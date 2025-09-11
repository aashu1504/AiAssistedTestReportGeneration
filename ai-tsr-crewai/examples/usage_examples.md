# TSR Generation Usage Examples

## Basic Usage

### 1. Standard Quality Gate (Default)
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

### 2. Strict Quality Gate (High Standards)
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

### 3. Lenient Quality Gate (Early Release)
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

### 4. Custom Quality Gate (Your Own Criteria)
```bash
python -m src.main \
  --file data/tc_execution_report.xlsx \
  --project "CustomProject" \
  --release "v1.5" \
  --environment "Staging" \
  --scope "Feature Testing" \
  --objectives "New Feature Validation" \
  --linked_plan "TP-004" \
  --quality-gate custom
```

## List Available Quality Gates

```bash
python -m src.main --list-quality-gates
```

## Quality Gate Criteria

### Default Quality Gate
- **Approved**: Pass rate ≥ 90%, Critical defects = 0, Major defects = 0
- **Conditional**: Pass rate ≥ 75%, Critical defects = 0, Major defects ≤ 2
- **Rejected**: Any other combination

### Strict Quality Gate
- **Approved**: Pass rate ≥ 95%, Critical defects = 0, Major defects = 0
- **Conditional**: Pass rate ≥ 90%, Critical defects = 0, Major defects ≤ 1
- **Rejected**: Any other combination

### Lenient Quality Gate
- **Approved**: Pass rate ≥ 80%, Critical defects = 0, Major defects ≤ 2
- **Conditional**: Pass rate ≥ 60%, Critical defects = 0, Major defects ≤ 3
- **Rejected**: Any other combination

### Custom Quality Gate
- **Approved**: Pass rate ≥ 85%, Critical defects = 0, Major defects ≤ 1
- **Conditional**: Pass rate ≥ 70%, Critical defects = 0, Major defects ≤ 2
- **Rejected**: Any other combination

## Customizing Quality Gates

To create your own quality gate, edit `config/quality_gates.json`:

```json
{
  "my_custom_gate": {
    "name": "My Custom Quality Gate",
    "description": "Custom criteria for my project",
    "criteria": {
      "min_pass_rate": 60,
      "max_critical_defects": 1,
      "max_major_defects": 5
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

Then use it with:
```bash
python -m src.main --quality-gate my_custom_gate [other options...]
```

## Understanding Test Plan IDs

The `--linked_plan` parameter is used for traceability:

- **TP-001**: Test Plan 001 (standard format)
- **REGRESSION-2024**: Regression test plan for 2024
- **FEATURE-123**: Feature-specific test plan
- **RELEASE-v2.1**: Release-specific test plan

This ID appears in the generated report to link back to the original test plan document.