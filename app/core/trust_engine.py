import json
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional
from skills.core_tools import CORE_TOOL_FUNCTIONS
from core.audit import audit_ledger
from core.sandbox_runner import validate_python_code_ast

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "skills" / "registry.json"
DYNAMIC_SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills" / "dynamic"

class TrustEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TrustEngine, cls).__new__(cls)
            cls._instance.registry = {}
            cls._instance.dynamic_functions = {}
            cls._instance._load_registry()
            cls._instance._load_dynamic_modules()
        return cls._instance

    def _load_registry(self):
        if REGISTRY_PATH.exists():
            try:
                with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.registry = data.get("skills", {})
            except Exception as e:
                print(f"Error reading registry.json: {e}")
                self.registry = {}
        else:
            self.registry = {}

    def _save_registry(self):
        try:
            with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
                json.dump({"skills": self.registry}, f, indent=2)
        except Exception as e:
            print(f"Error saving registry.json: {e}")

    def _load_dynamic_modules(self):
        """Dynamically imports Python files from skills/dynamic/."""
        if not DYNAMIC_SKILLS_DIR.exists():
            DYNAMIC_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
            return

        for py_file in DYNAMIC_SKILLS_DIR.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            skill_name = py_file.stem
            try:
                spec = importlib.util.spec_from_file_location(skill_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, skill_name):
                        self.dynamic_functions[skill_name] = getattr(module, skill_name)
            except Exception as e:
                print(f"Failed to load dynamic skill {skill_name}: {e}")

    def get_tools_for_role(self, role: str) -> List[Dict[str, Any]]:
        """Returns Mistral tool schemas permitted for the given role."""
        tools = []
        for name, meta in self.registry.items():
            permitted = meta.get("roles_permitted", [])
            # Executive has access to everything
            if role == "Executive" or role in permitted or "SHARED" in meta.get("category", ""):
                # Quarantined tools are disabled
                if meta.get("status") != "QUARANTINED":
                    tools.append(meta["schema"])
        return tools

    def dispatch(self, tool_name: str, arguments: Dict[str, Any], caller_role: str) -> str:
        """Executes a tool with RBAC check and trust impact logging."""
        meta = self.registry.get(tool_name)
        if not meta:
            return f"Error: Tool '{tool_name}' not found in registry."

        # RBAC Check
        permitted = meta.get("roles_permitted", [])
        if caller_role != "Executive" and caller_role not in permitted and "SHARED" not in meta.get("category", ""):
            return f"Permission Denied: Role '{caller_role}' is not authorized to execute '{tool_name}'."

        # Fetch function pointer
        func = CORE_TOOL_FUNCTIONS.get(tool_name) or self.dynamic_functions.get(tool_name)
        if not func:
            return f"Error: Implementation function for '{tool_name}' is not loaded."

        try:
            result = func(**arguments)
            self._record_success(tool_name)
            return str(result)
        except Exception as e:
            self._record_failure(tool_name, str(e))
            return f"Runtime Execution Error in '{tool_name}': {str(e)}"

    def _record_success(self, tool_name: str):
        if tool_name in self.registry:
            meta = self.registry[tool_name]
            meta["success_count"] = meta.get("success_count", 0) + 1
            meta["trust_score"] = meta.get("trust_score", 1) + 1
            # Graduation threshold: 4 successful runs -> TRUSTED
            if meta.get("status") == "EXPERIMENTAL" and meta["success_count"] >= 4:
                meta["status"] = "TRUSTED"
                meta["requires_human_approval"] = False
                audit_ledger.record_event(
                    action="SKILL_GRADUATED",
                    actor="TrustEngine",
                    role="SYSTEM",
                    details={"skill_name": tool_name, "new_status": "TRUSTED", "trust_score": meta["trust_score"]},
                    trust_impact="PROMOTED_TO_TRUSTED"
                )
            self._save_registry()

    def _record_failure(self, tool_name: str, error_msg: str):
        if tool_name in self.registry:
            meta = self.registry[tool_name]
            meta["failure_count"] = meta.get("failure_count", 0) + 1
            meta["trust_score"] = max(0, meta.get("trust_score", 1) - 5)
            # Automatic quarantine on failure
            meta["status"] = "QUARANTINED"
            audit_ledger.record_event(
                action="SKILL_QUARANTINED",
                actor="TrustEngine",
                role="SYSTEM",
                details={"skill_name": tool_name, "error": error_msg},
                status="FAILED",
                trust_impact="DEMOTED_TO_QUARANTINED"
            )
            self._save_registry()

    def register_new_skill(
        self,
        name: str,
        code: str,
        description: str,
        schema: Dict[str, Any],
        category: str = "DEVOPS",
        roles_permitted: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Registers an AI-synthesized skill as EXPERIMENTAL after AST validation.
        """
        # 1. AST Security Analysis
        is_safe, violations = validate_python_code_ast(code)
        if not is_safe:
            return {"success": False, "error": f"Security validation failed: {', '.join(violations)}"}

        # 2. Write Python file to skills/dynamic/
        file_path = DYNAMIC_SKILLS_DIR / f"{name}.py"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            return {"success": False, "error": f"Failed to persist skill code: {str(e)}"}

        # 3. Dynamically load into Python runtime
        try:
            spec = importlib.util.spec_from_file_location(name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, name):
                    self.dynamic_functions[name] = getattr(module, name)
                else:
                    return {"success": False, "error": f"Function '{name}' not found inside generated module."}
        except Exception as e:
            return {"success": False, "error": f"Runtime compilation error: {str(e)}"}

        # 4. Add to registry as EXPERIMENTAL
        meta = {
            "name": name,
            "category": category,
            "type": "ACTION_TOOL",
            "status": "EXPERIMENTAL",
            "trust_score": 1,
            "success_count": 0,
            "failure_count": 0,
            "roles_permitted": roles_permitted or [category.capitalize(), "Executive"],
            "requires_human_approval": True,
            "description": description,
            "schema": schema
        }
        self.registry[name] = meta
        self._save_registry()

        audit_ledger.record_event(
            action="REGISTER_EXPERIMENTAL_SKILL",
            actor="CuratorAgent",
            role="SYSTEM",
            details={"skill_name": name, "category": category},
            trust_impact="INITIALIZED_AS_EXPERIMENTAL"
        )
        return {"success": True, "meta": meta}

# Singleton instance
trust_engine = TrustEngine()
