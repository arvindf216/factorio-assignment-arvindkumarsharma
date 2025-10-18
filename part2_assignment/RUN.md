
# Run sample tests
python run_samples.py "python factory/main.py" "python belts/main.py"

# Run pytest
FACTORY_CMD="python factory/main.py" BELTS_CMD="python belts/main.py" pytest -q

# Factory CLI command
python3 factory/main.py < input.json > output.json

# Belts CLI command
python3 belts/main.py < belts_input.json > belts_output.json
