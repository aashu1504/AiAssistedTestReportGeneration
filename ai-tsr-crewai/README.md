# AI-Assisted Test Summary Report (TSR) Generation

An intelligent Test Summary Report generation system that uses AI agents to analyze test execution data and create comprehensive reports. The system supports multiple input formats including CSV, Excel, JSON, and TestNG XML files.

## 🚀 Features

### Core Capabilities
- **Multi-Format Support**: Process CSV, Excel (.xlsx), JSON, and TestNG XML files
- **AI-Powered Analysis**: Uses Google Gemini 2.5 Flash for intelligent data analysis
- **Automated Report Generation**: Creates HTML, PDF, and Markdown reports
- **Visual Analytics**: Generates charts and visualizations for test metrics
- **Quality Gate Evaluation**: Automated release recommendation based on configurable quality gates
- **Modular Architecture**: Clean separation of concerns with agents, tasks, and tools

### AI Agents
1. **Ingestion Agent**: Analyzes test execution files and normalizes data
2. **Analysis Agent**: Computes comprehensive test execution metrics
3. **Report Agent**: Generates structured TSR content and insights

### Supported Input Formats
- **CSV Files**: Standard test execution results
- **Excel Files**: .xlsx format with test data
- **JSON Files**: Structured test execution data
- **TestNG XML**: Selenium TestNG automation results

## 📋 Prerequisites

- Python 3.10+
- Virtual environment (venv310)
- Google Gemini API key

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AiAssistedTestReportGeneration/ai-tsr-crewai
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv310
   source venv310/bin/activate  # On Windows: venv310\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env file and add your GEMINI_API_KEY
   ```

## 🔧 Configuration

### Environment Variables (.env file)
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
TSR_DEFAULT_FILE=data/selenium_testng_execution_results.csv
TSR_QUALITY_GATE=strict
CREWAI_VERBOSE=true
CREWAI_DEBUG=false
TSR_PROJECT_NAME=E-Commerce Platform
TSR_RELEASE_VERSION=v2.6.0
TSR_ENVIRONMENT=QA
TSR_SCOPE=Functional Testing, Regression Testing, Integration Testing
TSR_OBJECTIVES=Verify system functionality, Ensure quality standards, Validate release readiness
TSR_LINKED_PLAN=TP-DEFAULT-001
```

### Quality Gates
The system supports multiple quality gate configurations:
- **default**: Standard quality thresholds
- **strict**: Higher quality requirements
- **lenient**: Lower quality thresholds
- **custom**: User-defined thresholds

## 🚀 Usage

### Basic Commands

#### Data Analysis Only (No AI)
```bash
# Activate virtual environment and run with data analysis only
source venv310/bin/activate && python -m src.main --project "E-Commerce Platform" --release "v2.6.10" --skip-crew
```

#### Full AI Processing (With LLM)
```bash
# Activate virtual environment and run with AI crew processing
source venv310/bin/activate && python -m src.main --project "E-Commerce Platform" --release "v2.6.10"
```

### File-Specific Commands

#### Using TestNG XML File
```bash
# With TestNG XML (no AI)
source venv310/bin/activate && python -m src.main --file data/testng-results.xml --project "E-Commerce Platform" --release "v2.6.10" --skip-crew

# With TestNG XML (with AI)
source venv310/bin/activate && python -m src.main --file data/testng-results.xml --project "E-Commerce Platform" --release "v2.6.10"
```

#### Using CSV File
```bash
# With CSV (no AI)
source venv310/bin/activate && python -m src.main --file data/selenium_testng_execution_results.csv --project "E-Commerce Platform" --release "v2.6.10" --skip-crew

# With CSV (with AI)
source venv310/bin/activate && python -m src.main --file data/selenium_testng_execution_results.csv --project "E-Commerce Platform" --release "v2.6.10"
```

### Advanced Commands

#### Full Command with All Parameters
```bash
source venv310/bin/activate && python -m src.main \
  --file data/testng-results.xml \
  --project "My Application" \
  --release "v1.2.3" \
  --environment "QA Windows/Chrome" \
  --scope "Login, Checkout, Orders" \
  --objectives "Functional Regression" \
  --linked_plan "TP-001" \
  --outdir reports \
  --quality-gate strict
```

#### Quick Test Command
```bash
# Quick test with default settings
cd /Users/ashish/Documents/GitHub/AiAssistedTestReportGeneration/ai-tsr-crewai && source venv310/bin/activate && python -m src.main --project "Test Project" --release "v1.0.0" --skip-crew
```

### Utility Commands

#### Help Command
```bash
# See all available options
source venv310/bin/activate && python -m src.main --help
```

#### List Quality Gates
```bash
# List available quality gates
source venv310/bin/activate && python -m src.main --list-quality-gates
```

## 📊 Command Line Arguments

| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| `--file` | Path to test execution file (.xlsx, .csv, .json, .xml) | No | From .env TSR_DEFAULT_FILE |
| `--project` | Project name | Yes | - |
| `--release` | Release version | Yes | - |
| `--environment` | Test environment | No | From .env |
| `--scope` | Test scope | No | From .env |
| `--objectives` | Test objectives | No | From .env |
| `--linked_plan` | Linked test plan ID | No | From .env |
| `--outdir` | Output directory for reports | No | reports |
| `--quality-gate` | Quality gate to use | No | default |
| `--skip-crew` | Skip AI crew processing | No | false |
| `--verbose` | Enable verbose logging | No | false |
| `--debug` | Enable debug logging | No | false |

## 📁 Project Structure

```
ai-tsr-crewai/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── agents.py            # AI agents configuration
│   ├── tasks.py             # Task definitions
│   ├── crew.py              # Crew orchestration
│   ├── tools.py             # File processing and utilities
│   ├── config_manager.py    # Configuration management
│   └── quality_gates.py     # Quality gate evaluation
├── templates/
│   ├── tsr_html_tabbed.j2   # HTML report template
│   ├── tsr_html.j2          # Alternative HTML template
│   └── tsr_md.j2            # Markdown template
├── data/
│   ├── selenium_testng_execution_results.csv  # Sample CSV data
│   └── testng-results.xml                     # Sample TestNG XML
├── reports/                 # Generated reports output
├── config/
│   └── quality_gates.yaml   # Quality gate configurations
├── tests/
│   └── test_tools.py        # Unit tests
├── requirements.txt         # Python dependencies
├── env.example             # Environment variables template
└── README.md               # This file
```

## 🔍 Supported Data Formats

### CSV Format
Expected columns (case-insensitive):
- Test Case ID, Test Name, Module, Priority, Status
- Execution Time, Tester, Environment, Browser, OS
- Error Message, Severity, Bug ID, Test Suite, Execution Date

### TestNG XML Format
Standard TestNG results XML with:
- `<test-method>` elements with status, duration, parameters
- Module, priority, severity, and bug ID in parameters
- Exception details for failed tests

### Excel Format
Standard Excel files with test execution data in any supported column format.

## 📈 Generated Reports

The system generates multiple report formats:

### HTML Report (Tabbed Interface)
- **Overview Tab**: Executive summary, key metrics, test execution summary
- **Test Execution Tab**: Charts, test execution summary by module
- **Defects Tab**: Defect analytics and summary
- **Sign-off Tab**: Release decision and sign-off information

### PDF Report
- Professional PDF version of the HTML report
- Includes all charts and visualizations

### Markdown Report
- Text-based report for documentation
- Compatible with GitHub and other platforms

### Metrics JSON
- Raw metrics data in JSON format
- Suitable for integration with other tools

## 🤖 AI Features

### Intelligent Analysis
- **Pattern Recognition**: Identifies failure patterns and trends
- **Root Cause Analysis**: Suggests likely causes of test failures
- **Risk Assessment**: Evaluates release readiness
- **Recommendations**: Provides actionable improvement suggestions

### Dynamic Content Generation
- **Executive Summaries**: AI-generated high-level insights
- **Key Findings**: Identifies stable and risky areas
- **Lessons Learned**: Dynamic lessons based on actual test data
- **Release Recommendations**: AI-powered release decisions

## 🔧 Configuration Files

### Quality Gates (config/quality_gates.yaml)
```yaml
default:
  description: "Standard quality thresholds"
  release_thresholds:
    approved:
      min_pass_rate: 90
      max_critical_defects: 0
      max_major_defects: 2
    conditional:
      min_pass_rate: 80
      max_critical_defects: 1
      max_major_defects: 5
```

### Sign-off Configuration
The system supports configurable sign-off information through YAML files.

## 🧪 Testing

Run the test suite:
```bash
source venv310/bin/activate && python -m pytest tests/
```

## 📝 Sample Data

The project includes sample data files:
- `data/selenium_testng_execution_results.csv`: Sample CSV with 45 test cases
- `data/testng-results.xml`: Sample TestNG XML with same data

## 🚨 Troubleshooting

### Common Issues

1. **Virtual Environment Not Activated**
   ```bash
   source venv310/bin/activate
   ```

2. **Missing API Key**
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

3. **File Not Found**
   - Ensure file path is correct
   - Check file permissions

4. **Import Errors**
   ```bash
   pip install -r requirements.txt
   ```

### Debug Mode
```bash
source venv310/bin/activate && python -m src.main --project "Test" --release "v1.0" --debug
```

## 🔄 Recent Updates

### v2.6.10 Features
- ✅ Fixed sign-off date fields in HTML template
- ✅ Reorganized tab content (moved module summary to Test Execution tab)
- ✅ Added TestNG XML support verification
- ✅ Enhanced error handling and logging
- ✅ Improved template rendering

### Tab Reorganization
- **Overview Tab**: Now contains Test Execution Summary
- **Test Execution Tab**: Now contains Test Execution Summary by Module
- Better logical flow and user experience

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs with `--debug` flag
3. Create an issue in the repository

## 🎯 Roadmap

- [ ] Additional input format support
- [ ] Enhanced visualization options
- [ ] Integration with CI/CD pipelines
- [ ] Custom template support
- [ ] Advanced analytics and reporting
- [ ] Multi-language support

---

**Generated with ❤️ using AI-Assisted Test Summary Report Generation System**