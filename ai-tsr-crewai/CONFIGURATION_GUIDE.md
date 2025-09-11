# Configuration Management Guide

## Overview

The TSR generation system now follows **industry best practices** for configuration management with a **configuration hierarchy**:

1. **Environment Variables** (highest priority)
2. **YAML Configuration Files** (medium priority)  
3. **Default Values** (lowest priority)

## Configuration Hierarchy

### 1. Environment Variables (Highest Priority)
Environment variables can override any configuration value at runtime:

```bash
# Override lenient quality gate pass rate
export TSR_LENIENT_PASS_RATE=40

# Override strict quality gate critical defects limit
export TSR_STRICT_CRITICAL_DEFECTS=1

# Run TSR with overridden values
python -m src.main --quality-gate lenient [other options...]
```

### 2. YAML Configuration Files (Medium Priority)
Configuration files provide structured, version-controlled settings:

```yaml
# config/quality_gates.yaml
quality_gates:
  lenient:
    criteria:
      min_pass_rate: 50  # Can be overridden by TSR_LENIENT_PASS_RATE
      max_critical_defects: 1
```

### 3. Default Values (Lowest Priority)
Hardcoded defaults as fallback when no configuration is available.

## Available Environment Variables

### Global Quality Gate Overrides
```bash
TSR_QUALITY_GATE=default                    # Override default quality gate
TSR_DEFAULT_PASS_RATE=75                   # Override default pass rate
TSR_DEFAULT_CRITICAL_DEFECTS=0             # Override default critical defects limit
TSR_DEFAULT_MAJOR_DEFECTS=2                # Override default major defects limit
```

### Strict Quality Gate Overrides
```bash
TSR_STRICT_PASS_RATE=95                    # Override strict pass rate
TSR_STRICT_CRITICAL_DEFECTS=0              # Override strict critical defects limit
TSR_STRICT_MAJOR_DEFECTS=0                 # Override strict major defects limit
```

### Lenient Quality Gate Overrides
```bash
TSR_LENIENT_PASS_RATE=50                   # Override lenient pass rate
TSR_LENIENT_CRITICAL_DEFECTS=1             # Override lenient critical defects limit
TSR_LENIENT_MAJOR_DEFECTS=5                # Override lenient major defects limit
```

### Custom Quality Gate Overrides
```bash
TSR_CUSTOM_PASS_RATE=50                    # Override custom pass rate
TSR_CUSTOM_CRITICAL_DEFECTS=1              # Override custom critical defects limit
TSR_CUSTOM_MAJOR_DEFECTS=3                 # Override custom major defects limit
```

## Usage Examples

### 1. Using Environment Variables

#### Set Environment Variables and Run
```bash
# Set environment variables
export TSR_LENIENT_PASS_RATE=30
export TSR_LENIENT_CRITICAL_DEFECTS=5

# Run TSR with overridden values
python -m src.main \
  --file data/tc_execution_report.xlsx \
  --project "TestProject" \
  --release "v1.0" \
  --environment "Test" \
  --scope "Test" \
  --objectives "Test" \
  --linked_plan "TP-001" \
  --quality-gate lenient
```

#### Inline Environment Variables
```bash
TSR_LENIENT_PASS_RATE=30 TSR_LENIENT_CRITICAL_DEFECTS=5 python -m src.main \
  --file data/tc_execution_report.xlsx \
  --project "TestProject" \
  --release "v1.0" \
  --environment "Test" \
  --scope "Test" \
  --objectives "Test" \
  --linked_plan "TP-001" \
  --quality-gate lenient
```

### 2. Using Configuration Files

#### Edit Configuration File
```yaml
# config/quality_gates.yaml
quality_gates:
  lenient:
    name: "Lenient Quality Gate"
    description: "Relaxed criteria for early releases"
    criteria:
      min_pass_rate: 30  # Changed from 50
      max_critical_defects: 5  # Changed from 1
      max_major_defects: 8  # Changed from 5
```

#### Run with Configuration File
```bash
python -m src.main \
  --file data/tc_execution_report.xlsx \
  --project "TestProject" \
  --release "v1.0" \
  --environment "Test" \
  --scope "Test" \
  --objectives "Test" \
  --linked_plan "TP-001" \
  --quality-gate lenient
```

### 3. CI/CD Integration

#### Docker Environment
```dockerfile
# Dockerfile
FROM python:3.10
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

# Set environment variables
ENV TSR_STRICT_PASS_RATE=95
ENV TSR_STRICT_CRITICAL_DEFECTS=0
ENV TSR_STRICT_MAJOR_DEFECTS=0

CMD ["python", "-m", "src.main", "--quality-gate", "strict"]
```

#### Kubernetes ConfigMap
```yaml
# k8s-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tsr-config
data:
  TSR_LENIENT_PASS_RATE: "40"
  TSR_LENIENT_CRITICAL_DEFECTS: "2"
  TSR_LENIENT_MAJOR_DEFECTS: "8"
```

#### GitHub Actions
```yaml
# .github/workflows/tsr.yml
name: Generate TSR
on: [push, pull_request]

jobs:
  tsr:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Generate TSR with environment variables
        env:
          TSR_STRICT_PASS_RATE: 95
          TSR_STRICT_CRITICAL_DEFECTS: 0
          TSR_STRICT_MAJOR_DEFECTS: 0
        run: |
          python -m src.main \
            --file test_results.xlsx \
            --project "${{ github.event.repository.name }}" \
            --release "${{ github.ref_name }}" \
            --environment "CI" \
            --scope "Automated Tests" \
            --objectives "Quality Validation" \
            --linked_plan "CI-${{ github.run_number }}" \
            --quality-gate strict
```

## Configuration File Structure

### Quality Gates Configuration
```yaml
# config/quality_gates.yaml
quality_gates:
  default:
    name: "Standard Quality Gate"
    description: "Standard quality criteria for most projects"
    criteria:
      min_pass_rate: 75
      max_critical_defects: 0
      max_major_defects: 2
      min_execution_rate: 90
      max_blocked_rate: 10
    release_recommendations:
      approved:
        min_pass_rate: 90
        max_critical_defects: 0
        max_major_defects: 0
      conditional:
        min_pass_rate: 75
        max_critical_defects: 0
        max_major_defects: 2
      rejected:
        min_pass_rate: 0
        max_critical_defects: 999
        max_major_defects: 999
```

## Best Practices

### 1. Environment-Specific Configuration
```bash
# Development environment
export TSR_LENIENT_PASS_RATE=40
export TSR_LENIENT_CRITICAL_DEFECTS=2

# Production environment  
export TSR_STRICT_PASS_RATE=98
export TSR_STRICT_CRITICAL_DEFECTS=0
```

### 2. Configuration Validation
```bash
# Validate configuration
python -c "
from src.config_manager import ConfigManager
cm = ConfigManager()
print('Configuration valid:', cm.validate_config())
"
```

### 3. Configuration Testing
```bash
# Test different configurations
for pass_rate in 50 60 70 80 90; do
  echo "Testing pass rate: $pass_rate%"
  TSR_LENIENT_PASS_RATE=$pass_rate python -m src.main \
    --list-quality-gates | grep -A 5 "LENIENT"
done
```

## Troubleshooting

### Configuration Not Applied
1. Check environment variable names (case-sensitive)
2. Verify YAML syntax in configuration files
3. Check file paths and permissions

### Environment Variables Not Working
1. Ensure variables are exported: `export TSR_LENIENT_PASS_RATE=30`
2. Check variable names match exactly
3. Verify no typos in variable names

### Configuration File Issues
1. Validate YAML syntax
2. Check file permissions
3. Ensure file is in correct location (`config/quality_gates.yaml`)

## Migration from Hardcoded Values

### Before (Hardcoded)
```python
# Old hardcoded approach
if pass_rate >= 90:
    recommendation = "APPROVED"
elif pass_rate >= 75:
    recommendation = "CONDITIONAL"
else:
    recommendation = "REJECTED"
```

### After (Configuration-Driven)
```python
# New configuration-driven approach
evaluator = QualityGateEvaluator()
recommendation, details = evaluator.evaluate_release_recommendation(
    pass_rate=pass_rate,
    critical_defects=critical_defects,
    major_defects=major_defects,
    quality_gate=args.quality_gate
)
```

## Benefits

1. **Flexibility**: Easy to change criteria without code changes
2. **Environment-Specific**: Different settings for dev/staging/prod
3. **Version Control**: Configuration files can be versioned
4. **CI/CD Integration**: Easy integration with deployment pipelines
5. **Runtime Overrides**: Environment variables for quick adjustments
6. **Maintainability**: Centralized configuration management
7. **Testing**: Easy to test different configurations
8. **Documentation**: Configuration files serve as documentation

This approach follows industry best practices and makes the TSR generation system highly configurable and maintainable! 🎉