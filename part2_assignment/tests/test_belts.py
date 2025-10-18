import os
import json
import subprocess
import shlex
import pytest

# Helper function to compare JSON objects with float tolerance
def compare_json(obj1, obj2, tol=1e-6):
    if type(obj1) != type(obj2):
        return False
    if isinstance(obj1, dict):
        if set(obj1.keys()) != set(obj2.keys()):
            return False
        for key in sorted(obj1.keys()): # Sort keys for deterministic comparison
            if not compare_json(obj1[key], obj2[key], tol):
                return False
    elif isinstance(obj1, list):
        if len(obj1) != len(obj2):
            return False
        # Note: This assumes list order is deterministic
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

@pytest.mark.skipif(not os.environ.get("BELTS_CMD"), reason="BELTS_CMD environment variable not set")
def test_belts_sample():
    command = os.environ["BELTS_CMD"]
    base_path = os.path.dirname(os.path.dirname(__file__)) # Get the part2_assignment directory

    input_path = os.path.join(base_path, "tests/belts_input.json")
    expected_output_path = os.path.join(base_path, "tests/expected_belts_output.json")

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

    assert compare_json(expected_json, actual_json), "The actual output does not match the expected output."