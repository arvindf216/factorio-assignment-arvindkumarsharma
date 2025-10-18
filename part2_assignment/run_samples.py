import sys
import os
import json
import subprocess
import shlex

def compare_json(obj1, obj2, tol=1e-6):
    """Recursively compare two JSON objects, with a tolerance for floats."""
    if type(obj1) != type(obj2):
        return False
    if isinstance(obj1, dict):
        if set(obj1.keys()) != set(obj2.keys()):
            return False
        for key in obj1:
            if not compare_json(obj1[key], obj2[key], tol):
                return False
    elif isinstance(obj1, list):
        if len(obj1) != len(obj2):
            return False
        for item1, item2 in zip(obj1, obj2):
            if not compare_json(item1, item2, tol):
                return False
    elif isinstance(obj1, float):
        if abs(obj1 - obj2) > tol:
            return False
    else:
        if obj1 != obj2:
            return False
    return True

def run_test(name, command, input_path, expected_output_path):
    """Run a single test case."""
    print(f"--- Running test: {name} ---")
    try:
        with open(input_path, 'r') as f_in:
            input_data = f_in.read()

        with open(expected_output_path, 'r') as f_exp:
            expected_json = json.load(f_exp)

        process = subprocess.run(
            shlex.split(command),
            input=input_data,
            capture_output=True,
            text=True,
            check=True
        )

        actual_json = json.loads(process.stdout)

        if compare_json(expected_json, actual_json):
            print(f"PASS: {name}")
            return True
        else:
            print(f"FAIL: {name}")
            print("Expected:", json.dumps(expected_json, indent=2))
            print("Actual:", json.dumps(actual_json, indent=2))
            return False

    except Exception as e:
        print(f"ERROR running {name}: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python run_samples.py <factory_cmd> <belts_cmd>")
        sys.exit(1)

    factory_cmd = sys.argv[1]
    belts_cmd = sys.argv[2]

    base_path = os.path.dirname(__file__)

    test_cases = [
        {
            "name": "Factory Sample",
            "command": factory_cmd,
            "input_path": os.path.join(base_path, "tests/input.json"),
            "expected_output_path": os.path.join(base_path, "tests/expected_factory_output.json")
        },
        {
            "name": "Belts Sample",
            "command": belts_cmd,
            "input_path": os.path.join(base_path, "tests/belts_input.json"),
            "expected_output_path": os.path.join(base_path, "tests/expected_belts_output.json")
        }
    ]

    results = [run_test(**case) for case in test_cases]

    if all(results):
        print("\nAll sample tests passed!")
        sys.exit(0)
    else:
        print("\nSome sample tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()