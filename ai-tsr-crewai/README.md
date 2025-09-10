# AI TSR CrewAI

An AI-powered Test Summary Report (TSR) generation tool using CrewAI framework.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

3. Place your test execution file:
   - Copy your Excel test execution file to `data/sample_tc_execution.xlsx`
   - The file should contain columns: Test Case, Test Suite, Status, Error Message, Skip Reason

4. Environment variables are already configured in `.env` file

## Usage

Run the TSR generation tool:

```bash
python -m src.main --file data/sample_tc_execution.xlsx --project "SampleProject" --release "R1.0.3" --environment "Windows 11, Chrome 126" --scope "Login, Checkout, Profile, Orders" --objectives "Functional + Regression" --linked_plan "TP-001"
```

### Arguments:
- `--file`: Path to the test execution Excel file
- `--project`: Project name
- `--release`: Release version
- `--environment`: Test environment details
- `--scope`: Test scope description
- `--objectives`: Test objectives
- `--linked_plan`: Linked test plan ID

## Running Tests

The project includes comprehensive unit tests using pytest:

```bash
# Install pytest if not already installed
pip install pytest

# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_tools.py

# Run tests with coverage
pytest --cov=src tests/
```

### Test Coverage

The test suite covers:
- **Data Reading**: Excel, CSV, JSON, and XML file parsing
- **Data Normalization**: Column mapping and standardization
- **Metrics Computation**: Summary statistics, defect analysis, flaky test detection
- **Chart Generation**: Visualization creation and file handling
- **Report Rendering**: Template processing and output generation

## Project Structure

- `data/`: Contains test execution data files
- `templates/`: Jinja2 templates for TSR generation
- `src/`: Source code
  - `agents.py`: CrewAI agents
  - `tasks.py`: CrewAI tasks
  - `tools.py`: Custom tools
  - `crew.py`: Crew configuration
  - `main.py`: Main entry point
- `reports/`: Generated TSR reports
- `tests/`: Unit tests
  - `test_tools.py`: Comprehensive tests for data processing functions