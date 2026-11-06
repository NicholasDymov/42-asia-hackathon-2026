import ast
from typing import Tuple, List

BANNED_IMPORTS = {
    "os.system", "shutil.rmtree", "subprocess", "socket", "pty",
    "ctypes", "multiprocessing", "builtins.__import__"
}

BANNED_CALLS = {
    "eval", "exec", "compile", "open", "fork", "kill"
}

class SecurityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.violations: List[str] = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in ["subprocess", "socket", "pty", "ctypes"]:
                self.violations.append(f"Forbidden import: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module in ["subprocess", "socket", "pty", "ctypes"]:
            self.violations.append(f"Forbidden from-import: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in BANNED_CALLS:
                self.violations.append(f"Forbidden function call: {node.func.id}()")
        elif isinstance(node.func, ast.Attribute):
            full_call = f"{getattr(node.func.value, 'id', '')}.{node.func.attr}"
            if full_call in BANNED_IMPORTS:
                self.violations.append(f"Forbidden method invocation: {full_call}()")
        self.generic_visit(node)

def validate_python_code_ast(code: str) -> Tuple[bool, List[str]]:
    """
    Statically analyzes newly generated Python skill code before registration.
    Ensures syntax is valid and prevents destructive system actions.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, [f"SyntaxError on line {e.lineno}: {e.msg}"]

    visitor = SecurityVisitor()
    visitor.visit(tree)

    if visitor.violations:
        return False, visitor.violations

    return True, []
