"""Configuration manager for TSR generation with environment variable support."""

import os
import yaml
import json
from typing import Dict, Any, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration with environment variable override support."""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        
        self.config_dir = Path(config_dir)
        self._config_cache = {}
        self._env_mappings = {}
    
    def load_config(self, config_file: str, use_env_overrides: bool = True) -> Dict[str, Any]:
        """
        Load configuration from file with optional environment variable overrides.
        
        Args:
            config_file: Configuration file name (e.g., 'quality_gates.yaml')
            use_env_overrides: Whether to apply environment variable overrides
            
        Returns:
            Configuration dictionary with overrides applied
        """
        config_path = self.config_dir / config_file
        
        if not config_path.exists():
            # Use warning for optional mapping files, error for required config files
            if config_file.endswith('_mappings.yaml'):
                logger.warning(f"Optional configuration file not found: {config_path}")
            else:
                logger.error(f"Configuration file not found: {config_path}")
            return {}
        
        # Load base configuration
        config = self._load_config_file(config_path)
        if not config:
            return {}
        
        # Apply environment variable overrides if requested
        if use_env_overrides:
            config = self._apply_env_overrides(config, config_file)
        
        return config
    
    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file."""
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif config_path.suffix.lower() == '.json':
                    return json.load(f) or {}
                else:
                    logger.error(f"Unsupported config file format: {config_path.suffix}")
                    return {}
        except Exception as e:
            logger.error(f"Error loading config file {config_path}: {e}")
            return {}
    
    def _apply_env_overrides(self, config: Dict[str, Any], config_file: str) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        # Load environment mappings
        env_mappings = self._get_env_mappings(config_file)
        
        # Create a deep copy to avoid modifying original
        config = self._deep_copy_dict(config)
        
        # Apply environment variable overrides
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    # Convert string value to appropriate type
                    converted_value = self._convert_env_value(env_value)
                    
                    # Set the value in the config using dot notation path
                    self._set_nested_value(config, config_path, converted_value)
                    
                    logger.debug(f"Applied environment override: {env_var}={env_value} -> {config_path}")
                except Exception as e:
                    logger.warning(f"Failed to apply environment override {env_var}={env_value}: {e}")
        
        return config
    
    def _get_env_mappings(self, config_file: str) -> Dict[str, str]:
        """Get environment variable mappings for a config file."""
        if config_file in self._env_mappings:
            return self._env_mappings[config_file]
        
        # Load mappings from config file
        mappings_config = self.load_config(f"{config_file.replace('.yaml', '')}_mappings.yaml", use_env_overrides=False)
        if mappings_config and 'env_mappings' in mappings_config:
            self._env_mappings[config_file] = mappings_config['env_mappings']
        else:
            # Fallback to default mappings
            self._env_mappings[config_file] = self._get_default_env_mappings()
        
        return self._env_mappings[config_file]
    
    def _get_default_env_mappings(self) -> Dict[str, str]:
        """Get default environment variable mappings."""
        return {
            # Global overrides
            'TSR_QUALITY_GATE': 'quality_gate_override',
            
            # Default gate overrides - Release Thresholds
            'TSR_DEFAULT_APPROVED_PASS_RATE': 'quality_gates.default.release_thresholds.approved.min_pass_rate',
            'TSR_DEFAULT_CONDITIONAL_PASS_RATE': 'quality_gates.default.release_thresholds.conditional.min_pass_rate',
            'TSR_DEFAULT_APPROVED_CRITICAL_DEFECTS': 'quality_gates.default.release_thresholds.approved.max_critical_defects',
            'TSR_DEFAULT_CONDITIONAL_CRITICAL_DEFECTS': 'quality_gates.default.release_thresholds.conditional.max_critical_defects',
            'TSR_DEFAULT_APPROVED_MAJOR_DEFECTS': 'quality_gates.default.release_thresholds.approved.max_major_defects',
            'TSR_DEFAULT_CONDITIONAL_MAJOR_DEFECTS': 'quality_gates.default.release_thresholds.conditional.max_major_defects',
            
            # Strict gate overrides - Release Thresholds
            'TSR_STRICT_APPROVED_PASS_RATE': 'quality_gates.strict.release_thresholds.approved.min_pass_rate',
            'TSR_STRICT_CONDITIONAL_PASS_RATE': 'quality_gates.strict.release_thresholds.conditional.min_pass_rate',
            'TSR_STRICT_APPROVED_CRITICAL_DEFECTS': 'quality_gates.strict.release_thresholds.approved.max_critical_defects',
            'TSR_STRICT_CONDITIONAL_CRITICAL_DEFECTS': 'quality_gates.strict.release_thresholds.conditional.max_critical_defects',
            'TSR_STRICT_APPROVED_MAJOR_DEFECTS': 'quality_gates.strict.release_thresholds.approved.max_major_defects',
            'TSR_STRICT_CONDITIONAL_MAJOR_DEFECTS': 'quality_gates.strict.release_thresholds.conditional.max_major_defects',
            
            # Lenient gate overrides - Release Thresholds
            'TSR_LENIENT_APPROVED_PASS_RATE': 'quality_gates.lenient.release_thresholds.approved.min_pass_rate',
            'TSR_LENIENT_CONDITIONAL_PASS_RATE': 'quality_gates.lenient.release_thresholds.conditional.min_pass_rate',
            'TSR_LENIENT_APPROVED_CRITICAL_DEFECTS': 'quality_gates.lenient.release_thresholds.approved.max_critical_defects',
            'TSR_LENIENT_CONDITIONAL_CRITICAL_DEFECTS': 'quality_gates.lenient.release_thresholds.conditional.max_critical_defects',
            'TSR_LENIENT_APPROVED_MAJOR_DEFECTS': 'quality_gates.lenient.release_thresholds.approved.max_major_defects',
            'TSR_LENIENT_CONDITIONAL_MAJOR_DEFECTS': 'quality_gates.lenient.release_thresholds.conditional.max_major_defects',
            
            # Custom gate overrides - Release Thresholds
            'TSR_CUSTOM_APPROVED_PASS_RATE': 'quality_gates.custom.release_thresholds.approved.min_pass_rate',
            'TSR_CUSTOM_CONDITIONAL_PASS_RATE': 'quality_gates.custom.release_thresholds.conditional.min_pass_rate',
            'TSR_CUSTOM_APPROVED_CRITICAL_DEFECTS': 'quality_gates.custom.release_thresholds.approved.max_critical_defects',
            'TSR_CUSTOM_CONDITIONAL_CRITICAL_DEFECTS': 'quality_gates.custom.release_thresholds.conditional.max_critical_defects',
            'TSR_CUSTOM_APPROVED_MAJOR_DEFECTS': 'quality_gates.custom.release_thresholds.approved.max_major_defects',
            'TSR_CUSTOM_CONDITIONAL_MAJOR_DEFECTS': 'quality_gates.custom.release_thresholds.conditional.max_major_defects',
        }
    
    def _convert_env_value(self, value: str) -> Union[int, float, str, bool]:
        """Convert environment variable string to appropriate type."""
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Try boolean
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        
        # Return as string
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any) -> None:
        """Set a value in nested dictionary using dot notation path."""
        keys = path.split('.')
        current = config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def _deep_copy_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deep copy of a dictionary."""
        import copy
        return copy.deepcopy(d)
    
    def get_quality_gate_config(self, gate_name: str = None) -> Dict[str, Any]:
        """
        Get quality gate configuration with environment overrides.
        
        Args:
            gate_name: Specific quality gate name, or None for all gates
            
        Returns:
            Quality gate configuration dictionary
        """
        config = self.load_config('quality_gates.yaml')
        
        if gate_name:
            return config.get('quality_gates', {}).get(gate_name, {})
        
        return config.get('quality_gates', {})
    
    def get_available_quality_gates(self) -> Dict[str, str]:
        """Get list of available quality gates with their names."""
        config = self.get_quality_gate_config()
        return {
            gate_id: gate_config.get('name', gate_id)
            for gate_id, gate_config in config.items()
        }
    
    def get_quality_gate_criteria(self, gate_name: str) -> Dict[str, Any]:
        """Get criteria for a specific quality gate."""
        gate_config = self.get_quality_gate_config(gate_name)
        # Return both release thresholds and additional criteria
        return {
            'release_thresholds': gate_config.get('release_thresholds', {}),
            'additional_criteria': gate_config.get('additional_criteria', {})
        }
    
    def get_quality_gate_info(self, gate_name: str) -> Dict[str, Any]:
        """Get complete information for a specific quality gate."""
        return self.get_quality_gate_config(gate_name)
    
    def get_quality_gate_recommendations(self, gate_name: str) -> Dict[str, Any]:
        """Get release recommendations for a specific quality gate."""
        gate_config = self.get_quality_gate_config(gate_name)
        return gate_config.get('release_recommendations', {})
    
    def validate_config(self) -> bool:
        """Validate that all required configuration is present."""
        try:
            config = self.get_quality_gate_config()
            
            required_gates = ['default', 'strict', 'lenient', 'custom']
            for gate in required_gates:
                if gate not in config:
                    logger.error(f"Missing required quality gate: {gate}")
                    return False
                
                gate_config = config[gate]
                required_fields = ['name', 'criteria', 'release_recommendations']
                for field in required_fields:
                    if field not in gate_config:
                        logger.error(f"Missing required field '{field}' in quality gate '{gate}'")
                        return False
            
            return True
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def load_sign_off_config(self) -> Dict[str, Any]:
        """
        Load sign-off configuration with environment variable overrides.
        
        Returns:
            Sign-off configuration dictionary with overrides applied
        """
        config = self.load_config('sign_off.yaml')
        
        if not config:
            # Return default values if config file not found
            default_config = {
                'test_lead': 'TBD',
                'test_engineer': 'TBD',
                'dev_lead': 'TBD',
                'product_owner': 'TBD',
                'qa_manager': 'TBD',
                'date_format': '%Y-%m-%d'
            }
        else:
            default_config = config.get('sign_off', {})
        
        # Apply environment variable overrides
        env_overrides = {
            'test_lead': os.getenv('TSR_TEST_LEAD'),
            'test_engineer': os.getenv('TSR_TEST_ENGINEER'),
            'dev_lead': os.getenv('TSR_DEV_LEAD'),
            'product_owner': os.getenv('TSR_PRODUCT_OWNER'),
            'qa_manager': os.getenv('TSR_QA_MANAGER'),
            'date_format': os.getenv('TSR_DATE_FORMAT')
        }
        
        # Apply overrides where environment variables are set
        for key, value in env_overrides.items():
            if value is not None:
                default_config[key] = value
        
        return default_config
    
    def load_test_environment_config(self) -> Dict[str, Any]:
        """
        Load test environment configuration with environment variable overrides.
        
        Returns:
            Test environment configuration dictionary with overrides applied
        """
        config = self.load_config('sign_off.yaml')
        
        if not config:
            # Return default values if config file not found
            default_config = {
                'environment_name': 'Staging',
                'software_version': 'v1.0.0',
                'software_details': 'Application v1.0.0',
                'browsers': 'Chrome, Firefox, Safari, Edge',
                'database_type': 'PostgreSQL',
                'database_version': '14.0',
                'database_details': 'PostgreSQL 14.0',
                'deployment_type': 'Docker',
                'load_balancer': 'NGINX',
                'monitoring': 'Prometheus',
                'logging': 'ELK Stack'
            }
        else:
            default_config = config.get('test_environment', {})
        
        # Apply environment variable overrides
        env_overrides = {
            'environment_name': os.getenv('TSR_ENVIRONMENT_NAME'),
            'software_version': os.getenv('TSR_SOFTWARE_VERSION'),
            'software_details': os.getenv('TSR_SOFTWARE_DETAILS'),
            'browsers': os.getenv('TSR_BROWSERS'),
            'database_type': os.getenv('TSR_DATABASE_TYPE'),
            'database_version': os.getenv('TSR_DATABASE_VERSION'),
            'database_details': os.getenv('TSR_DATABASE_DETAILS'),
            'deployment_type': os.getenv('TSR_DEPLOYMENT_TYPE'),
            'load_balancer': os.getenv('TSR_LOAD_BALANCER'),
            'monitoring': os.getenv('TSR_MONITORING'),
            'logging': os.getenv('TSR_LOGGING')
        }
        
        # Apply overrides where environment variables are set
        for key, value in env_overrides.items():
            if value is not None:
                default_config[key] = value
        
        return default_config