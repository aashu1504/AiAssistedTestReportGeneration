# Quality Gates Configuration Guide

## Overview

The TSR generation system now supports **configurable quality gates** that allow you to customize the release recommendation criteria based on your project's specific needs.

## Quick Answers to Your Questions

### 1. **What is Plan TP-001?**

- **TP-001** is a **Test Plan ID** that you provide via the `--linked_plan` parameter
- It's used for **traceability** - linking the TSR back to the original test plan document
- You can use any ID format: `TP-001`, `TEST-123`, `REGRESSION-2024`, `FEATURE-456`, etc.
- This appears in the generated report to maintain audit trails

### 2. **How to Make TSR Generation Configurable?**

The system now supports **4 built-in quality gates** plus **custom configuration**:

## Available Quality Gates

### 🔹 **DEFAULT** (Standard Quality Gate)
- **Approved**: Pass rate ≥ 90%, Critical defects = 0, Major defects = 0
- **Conditional**: Pass rate ≥ 75%, Critical defects = 0, Major defects ≤ 2
- **Rejected**: Any other combination

### 🔹 **STRICT** (High Standards)
- **Approved**: Pass rate ≥ 95%, Critical defects = 0, Major defects = 0
- **Conditional**: Pass rate ≥ 90%, Critical defects = 0, Major defects ≤ 1
- **Rejected**: Any other combination

### 🔹 **LENIENT** (Early Release/Prototype)
- **Approved**: Pass rate ≥ 80%, Critical defects = 0, Major defects ≤ 2
- **Conditional**: Pass rate ≥ 60%, Critical defects = 0, Major defects ≤ 3
- **Rejected**: Any other combination

### 🔹 **CUSTOM** (User-Defined)
- **Approved**: Pass rate ≥ 85%, Critical defects = 0, Major defects ≤ 1
- **Conditional**: Pass rate ≥ 70%, Critical defects = 0, Major defects ≤ 2
- **Rejected**: Any other combination

## Usage Examples

### List Available Quality Gates
```bash
python -m src.main --list-quality-gates
```

### Generate TSR with Different Quality Gates

#### Standard Quality Gate (Default)
```bash
python -m src.main \
  --file data/tc_execution_report.xlsx \
  --project "MyProject" \
  --release "v2.1" \
  --environment "Production" \
  --scope "Regression Testing" \
  --objectives "Functional Validation" \
  --linked_plan "TP-001"
```

#### Strict Quality Gate (High Standards)
```bash
python -m src.main \
  --file data/tc_execution_report.xlsx \
  --project "CriticalApp" \
  --release "v1.0" \
  --environment "Production" \
  --scope "Full Regression" \
  --objectives "Release Validation" \
  --linked_plan "TP-002" \
  --quality-gate strict
```

#### Lenient Quality Gate (Early Release)
```bash
python -m src.main \
  --file data/tc_execution_report.xlsx \
  --project "PrototypeApp" \
  --release "alpha-0.1" \
  --environment "Development" \
  --scope "Core Features" \
  --objectives "Basic Functionality" \
  --linked_plan "TP-003" \
  --quality-gate lenient
```

## Creating Custom Quality Gates

### Method 1: Edit Configuration File

Edit `config/quality_gates.json` to add your custom gate:

```json
{
  "my_custom_gate": {
    "name": "My Custom Quality Gate",
    "description": "Custom criteria for my specific project needs",
    "criteria": {
      "min_pass_rate": 50,
      "max_critical_defects": 1,
      "max_major_defects": 5,
      "min_execution_rate": 80,
      "max_blocked_rate": 15
    },
    "release_recommendations": {
      "approved": {
        "min_pass_rate": 80,
        "max_critical_defects": 0,
        "max_major_defects": 2
      },
      "conditional": {
        "min_pass_rate": 60,
        "max_critical_defects": 0,
        "max_major_defects": 3
      },
      "rejected": {
        "min_pass_rate": 0,
        "max_critical_defects": 999,
        "max_major_defects": 999
      }
    }
  }
}
```

Then use it:
```bash
python -m src.main --quality-gate my_custom_gate [other options...]
```

### Method 2: Runtime Configuration

You can also modify the quality gate criteria programmatically by editing the `config/quality_gates.json` file before running the TSR generation.

## Real-World Scenarios

### Scenario 1: Production Release (Strict)
```bash
python -m src.main \
  --file production_tests.xlsx \
  --project "E-commerce Platform" \
  --release "v3.2.1" \
  --environment "Production" \
  --scope "Full Regression Suite" \
  --objectives "Release Validation" \
  --linked_plan "PROD-RELEASE-2024" \
  --quality-gate strict
```

### Scenario 2: Feature Branch (Lenient)
```bash
python -m src.main \
  --file feature_tests.xlsx \
  --project "New Feature" \
  --release "feature-123" \
  --environment "Development" \
  --scope "Feature Testing" \
  --objectives "Feature Validation" \
  --linked_plan "FEATURE-123" \
  --quality-gate lenient
```

### Scenario 3: Hotfix (Custom)
```bash
python -m src.main \
  --file hotfix_tests.xlsx \
  --project "Critical Fix" \
  --release "hotfix-001" \
  --environment "Staging" \
  --scope "Critical Path" \
  --objectives "Hotfix Validation" \
  --linked_plan "HOTFIX-001" \
  --quality-gate custom
```

## Quality Gate Evaluation Logic

The system evaluates release recommendations in this order:

1. **Check APPROVED criteria** - If all conditions are met, recommend "APPROVED"
2. **Check CONDITIONAL criteria** - If approved criteria not met but conditional criteria met, recommend "CONDITIONAL"
3. **Otherwise REJECTED** - If neither approved nor conditional criteria are met

## Integration with CI/CD

You can integrate this into your CI/CD pipeline:

```bash
# In your CI/CD script
QUALITY_GATE="strict"  # or "default", "lenient", "custom"
TSR_OUTPUT=$(python -m src.main --quality-gate $QUALITY_GATE [other options...])

# Check if release is approved
if grep -q "APPROVED" reports/TSR_*.html; then
    echo "✅ Release approved - proceeding with deployment"
    # Deploy to production
elif grep -q "CONDITIONAL" reports/TSR_*.html; then
    echo "⚠️  Release conditional - manual review required"
    # Send for manual review
else
    echo "❌ Release rejected - stopping deployment"
    # Stop deployment
    exit 1
fi
```

## Benefits

1. **Flexibility**: Different quality standards for different types of releases
2. **Consistency**: Standardized evaluation criteria across projects
3. **Traceability**: Clear linkage between test plans and reports
4. **Automation**: Easy integration with CI/CD pipelines
5. **Transparency**: Clear criteria and reasoning for release decisions

## Troubleshooting

### Quality Gate Not Found
- Check that the quality gate exists in `config/quality_gates.json`
- Use `--list-quality-gates` to see available options

### Custom Quality Gate Not Working
- Ensure JSON syntax is valid
- Check that all required fields are present
- Restart the application after modifying the config file

### Release Recommendation Not Expected
- Check the actual test metrics against your quality gate criteria
- Use verbose logging to see the evaluation details
- Verify that the quality gate is being used correctly