
import sys
import os
import json
from subprocess import Popen, PIPE

def run_command(command, input_data):
    process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)
    stdout, stderr = process.communicate(input=json.dumps(input_data))
    if process.returncode != 0:
        raise Exception(f"Error running command: {command}\n{stderr}")
    return json.loads(stdout)

def main():
    if len(sys.argv) != 3:
        print("Usage: python run_samples.py <factory_cmd> <belts_cmd>")
        sys.exit(1)

    factory_cmd = sys.argv[1]
    belts_cmd = sys.argv[2]

    # Add sample running logic here

if __name__ == "__main__":
    main()
