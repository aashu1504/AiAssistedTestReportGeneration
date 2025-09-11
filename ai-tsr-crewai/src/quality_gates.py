"""Quality Gates evaluation module for TSR generation."""

import os
from typing import Dict, Any, Tuple
import logging
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)

class QualityGateEvaluator:
    """Evaluates test results against configurable quality gates."""
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        Initialize the quality gate evaluator.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager or ConfigManager()
        self.quality_gates = self.config_manager.get_quality_gate_config()
    
    
    def evaluate_release_recommendation(self, 
                                      pass_rate: float, 
                                      critical_defects: int, 
                                      major_defects: int,
                                      quality_gate: str = "default") -> Tuple[str, Dict[str, Any]]:
        """
        Evaluate release recommendation based on quality gate criteria.
        
        Args:
            pass_rate: Test pass rate percentage
            critical_defects: Number of open critical defects
            major_defects: Number of open major defects
            quality_gate: Quality gate to use (default, strict, lenient, custom)
            
        Returns:
            Tuple of (recommendation, evaluation_details)
        """
        if quality_gate not in self.quality_gates:
            logger.warning(f"Quality gate '{quality_gate}' not found, using 'default'")
            quality_gate = "default"
        
        gate_config = self.quality_gates[quality_gate]
        release_thresholds = gate_config.get("release_thresholds", {})
        
        # Check approved criteria
        approved_criteria = release_thresholds.get("approved", {})
        if (pass_rate >= approved_criteria.get("min_pass_rate", 0) and
            critical_defects <= approved_criteria.get("max_critical_defects", 999) and
            major_defects <= approved_criteria.get("max_major_defects", 999)):
            recommendation = "APPROVED"
            reason = f"Pass rate {pass_rate:.1f}% >= {approved_criteria.get('min_pass_rate', 0)}%, " \
                    f"Critical defects {critical_defects} <= {approved_criteria.get('max_critical_defects', 999)}, " \
                    f"Major defects {major_defects} <= {approved_criteria.get('max_major_defects', 999)}"
        
        # Check conditional criteria
        elif (pass_rate >= release_thresholds.get("conditional", {}).get("min_pass_rate", 0) and
              critical_defects <= release_thresholds.get("conditional", {}).get("max_critical_defects", 999) and
              major_defects <= release_thresholds.get("conditional", {}).get("max_major_defects", 999)):
            recommendation = "CONDITIONAL"
            conditional_criteria = release_thresholds.get("conditional", {})
            reason = f"Pass rate {pass_rate:.1f}% >= {conditional_criteria.get('min_pass_rate', 0)}%, " \
                    f"Critical defects {critical_defects} <= {conditional_criteria.get('max_critical_defects', 999)}, " \
                    f"Major defects {major_defects} <= {conditional_criteria.get('max_major_defects', 999)}"
        
        # Otherwise rejected
        else:
            recommendation = "REJECTED"
            failed_criteria = []
            conditional_criteria = release_thresholds.get("conditional", {})
            if pass_rate < conditional_criteria.get("min_pass_rate", 0):
                failed_criteria.append(f"Pass rate {pass_rate:.1f}% < {conditional_criteria.get('min_pass_rate', 0)}%")
            if critical_defects > conditional_criteria.get("max_critical_defects", 999):
                failed_criteria.append(f"Critical defects {critical_defects} > {conditional_criteria.get('max_critical_defects', 999)}")
            if major_defects > conditional_criteria.get("max_major_defects", 999):
                failed_criteria.append(f"Major defects {major_defects} > {conditional_criteria.get('max_major_defects', 999)}")
            reason = "; ".join(failed_criteria)
        
        evaluation_details = {
            "quality_gate_used": quality_gate,
            "gate_name": gate_config.get("name", quality_gate),
            "pass_rate": pass_rate,
            "critical_defects": critical_defects,
            "major_defects": major_defects,
            "criteria_met": recommendation != "REJECTED",
            "reason": reason,
            "release_thresholds": release_thresholds,
            "additional_criteria": gate_config.get("additional_criteria", {})
        }
        
        logger.info(f"Release recommendation: {recommendation} (Quality Gate: {quality_gate})")
        return recommendation, evaluation_details
    
    def get_available_quality_gates(self) -> Dict[str, str]:
        """Get list of available quality gates with their descriptions."""
        return self.config_manager.get_available_quality_gates()
    
    def get_quality_gate_criteria(self, quality_gate: str = "default") -> Dict[str, Any]:
        """Get criteria for a specific quality gate."""
        return self.config_manager.get_quality_gate_criteria(quality_gate)