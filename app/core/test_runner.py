import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple, List

def run_skill_unit_test(code: str, function_name: str, test_call_code: str) -> Tuple[bool, str]:
    """
    Executes newly synthesized Python code in an isolated subprocess runner.
    Ensures that the skill not only passes AST checks, but actually executes and returns valid data.
    """
    harness_code = f"""
{code}

# Test execution assertion
try:
    result = {test_call_code}
    print("SUCCESS_OUTPUT::" + str(result))
except Exception as e:
    import traceback
    print("FAILURE_TRACE::" + traceback.format_exc())
    sys.exit(1)
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
        tf.write(harness_code)
        temp_path = tf.name

    try:
        proc = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=5.0
        )
        Path(temp_path).unlink(missing_ok=True)
        if proc.returncode == 0 and "SUCCESS_OUTPUT::" in proc.stdout:
            out = proc.stdout.split("SUCCESS_OUTPUT::")[-1].strip()
            return True, out
        else:
            err = proc.stderr or proc.stdout
            return False, f"Unit test failed: {err}"
    except subprocess.TimeoutExpired:
        Path(temp_path).unlink(missing_ok=True)
        return False, "Execution timed out (infinite loop detected)."
    except Exception as e:
        Path(temp_path).unlink(missing_ok=True)
        return False, f"Runner execution error: {str(e)}"
