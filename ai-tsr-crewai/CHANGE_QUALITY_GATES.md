# How to Change Quality Gate Values

## **Method 1: Edit YAML Configuration File (Permanent Changes)**

### **File: `config/quality_gates.yaml`** (MAIN CONFIGURATION FILE)

Edit the values directly in the YAML file:

```yaml
quality_gates:
  lenient:
    name: "Lenient Quality Gate"
    description: "Relaxed criteria for early releases or prototypes"
    release_thresholds:
      approved:
        min_pass_rate: 80        # ← Change this value
        max_critical_defects: 0
        max_major_defects: 2
      conditional:
        min_pass_rate: 50        # ← Change this value
        max_critical_defects: 1
        max_major_defects: 5
      rejected:
        min_pass_rate: 0
        max_critical_defects: 999
        max_major_defects: 999
    additional_criteria:
      min_pass_rate: 50          # ← Change this value (for reporting only)
      max_critical_defects: 1
      max_major_defects: 5
```

### **Example: Make Lenient Even More Lenient**

```yaml
# Change lenient conditional threshold from 50% to 30%
lenient:
  release_thresholds:
    conditional:
      min_pass_rate: 30          # ← Changed from 50 to 30
      max_critical_defects: 2    # ← Changed from 1 to 2
      max_major_defects: 8       # ← Changed from 5 to 8
```

## **Method 2: Use Environment Variables (Runtime Overrides)**

### **File: `env.example`** (Template)

Copy `env.example` to `.env` and modify:

```bash
# Override lenient quality gate thresholds
TSR_LENIENT_CONDITIONAL_PASS_RATE=30
TSR_LENIENT_CONDITIONAL_CRITICAL_DEFECTS=2
TSR_LENIENT_CONDITIONAL_MAJOR_DEFECTS=8
```

### **Runtime Override (Temporary)**

```bash
# Set environment variables and run
export TSR_LENIENT_CONDITIONAL_PASS_RATE=30
export TSR_LENIENT_CONDITIONAL_CRITICAL_DEFECTS=2
python -m src.main --quality-gate lenient [options...]

# Or inline
TSR_LENIENT_CONDITIONAL_PASS_RATE=30 python -m src.main --quality-gate lenient [options...]
```

## **Which Method to Use?**

### **Use YAML File When:**
- ✅ You want **permanent changes**
- ✅ Changes apply to **all environments**
- ✅ You want to **version control** the changes
- ✅ Changes are **part of the project configuration**

### **Use Environment Variables When:**
- ✅ You want **temporary overrides**
- ✅ Different values for **different environments** (dev/staging/prod)
- ✅ **CI/CD pipeline** configuration
- ✅ **Runtime flexibility** without code changes

## **Examples**

### **Example 1: Make Lenient More Lenient (YAML)**
```yaml
# In config/quality_gates.yaml
lenient:
  release_thresholds:
    conditional:
      min_pass_rate: 30        # Was 50, now 30
      max_critical_defects: 2  # Was 1, now 2
```

### **Example 2: Override for Development (Environment Variables)**
```bash
# In .env file or export
TSR_LENIENT_CONDITIONAL_PASS_RATE=25
TSR_LENIENT_CONDITIONAL_CRITICAL_DEFECTS=3
```

### **Example 3: CI/CD Pipeline Override**
```yaml
# In GitHub Actions or similar
env:
  TSR_STRICT_CONDITIONAL_PASS_RATE: 95
  TSR_STRICT_CONDITIONAL_CRITICAL_DEFECTS: 0
```

## **Testing Your Changes**

After making changes, test them:

```bash
# List all quality gates to see current values
python -m src.main --list-quality-gates

# Test with specific quality gate
python -m src.main --quality-gate lenient [options...]
```

## **Summary**

- **`config/quality_gates.yaml`** = Main configuration file (permanent changes)
- **`env.example`** = Environment variable template (runtime overrides)
- **`.env`** = Actual environment file (automatically loaded)
- **Environment variables** = Override YAML values at runtime
- **YAML values** = Default values when no environment variables are set

## **Files Removed**

- **`config/quality_gates.json`** = ❌ DELETED (replaced by YAML system)