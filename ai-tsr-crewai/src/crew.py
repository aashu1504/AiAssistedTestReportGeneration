"""CrewAI crew orchestration for TSR generation with sequential task flow."""

import os
import logging
import tempfile
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
CREWAI_VERBOSE = os.getenv("CREWAI_VERBOSE", "false").lower() == "true"
CREWAI_DEBUG = os.getenv("CREWAI_DEBUG", "false").lower() == "true"

# Configure logging level based on environment
if CREWAI_DEBUG:
    logging.getLogger().setLevel(logging.DEBUG)
elif CREWAI_VERBOSE:
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.getLogger().setLevel(logging.WARNING)

logger.info(f"Crew module loaded - CREWAI_VERBOSE: {CREWAI_VERBOSE}, CREWAI_DEBUG: {CREWAI_DEBUG}")


class CrewExecutionError(Exception):
    """Custom exception for crew execution errors."""
    pass


def build_crew() -> Dict[str, Any]:
    """
    Build and configure the TSR generation crew with sequential task flow.
    
    This function creates a crew configuration that orchestrates three tasks:
    1. Ingestion Task: Processes test execution files and normalizes data
    2. Analysis Task: Computes comprehensive test execution metrics
    3. Report Task: Generates structured TSR content
    
    Returns:
        Dictionary containing:
        - agents: Dictionary of configured agents
        - tasks: Dictionary of task functions
        - crew_config: Crew configuration metadata
        - flow: Sequential task flow definition
        
    Raises:
        CrewExecutionError: If crew building fails
    """
    logger.info("Building TSR generation crew...")
    
    try:
        # Import required modules
        from .agents import create_all_agents
        from .tasks import create_all_tasks
        
        # Create agents
        logger.debug("Creating agents...")
        agents = create_all_agents()
        
        if not agents:
            raise CrewExecutionError("Failed to create any agents")
        
        logger.info(f"Created {len(agents)} agents: {list(agents.keys())}")
        
        # Create tasks
        logger.debug("Creating tasks...")
        tasks = create_all_tasks(agents)
        
        if not tasks:
            raise CrewExecutionError("Failed to create any tasks")
        
        logger.info(f"Created {len(tasks)} tasks: {list(tasks.keys())}")
        
        # Define sequential flow
        flow = [
            {
                "step": 1,
                "name": "ingestion",
                "task": "ingestion_task",
                "description": "Process test execution file and normalize data",
                "required": True
            },
            {
                "step": 2,
                "name": "analysis", 
                "task": "analysis_task",
                "description": "Compute comprehensive test execution metrics",
                "required": True
            },
            {
                "step": 3,
                "name": "report",
                "task": "report_task", 
                "description": "Generate structured TSR content",
                "required": True
            }
        ]
        
        # Build crew configuration
        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "flow": flow,
            "metadata": {
                "version": "1.0.0",
                "description": "TSR Generation Crew with Sequential Task Flow",
                "created_at": "2024-01-01T00:00:00Z",
                "verbose": CREWAI_VERBOSE,
                "debug": CREWAI_DEBUG
            }
        }
        
        logger.info("Crew built successfully")
        return crew_config
        
    except Exception as e:
        logger.error(f"Failed to build crew: {str(e)}")
        raise CrewExecutionError(f"Crew building failed: {str(e)}")


def execute_ingestion_step(crew_config: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """
    Execute the ingestion step of the crew.
    
    Args:
        crew_config: Crew configuration dictionary
        file_path: Path to test execution file
        
    Returns:
        Dictionary containing ingestion results
        
    Raises:
        CrewExecutionError: If ingestion step fails
    """
    logger.info(f"Executing ingestion step for file: {file_path}")
    
    try:
        tasks = crew_config["tasks"]
        
        if "ingestion_task" not in tasks:
            raise CrewExecutionError("Ingestion task not available in crew")
        
        # Execute ingestion task
        ingestion_result = tasks["ingestion_task"](file_path)
        
        # Validate result structure
        required_keys = ["readiness_data", "normalized_data_path", "file_type", "canonical_columns"]
        for key in required_keys:
            if key not in ingestion_result:
                raise CrewExecutionError(f"Missing required key '{key}' in ingestion result")
        
        logger.info(f"Ingestion step completed - File type: {ingestion_result.get('file_type')}, "
                   f"Columns: {len(ingestion_result.get('canonical_columns', []))}")
        
        return ingestion_result
        
    except Exception as e:
        logger.error(f"Ingestion step failed: {str(e)}")
        raise CrewExecutionError(f"Ingestion step failed: {str(e)}")


def execute_analysis_step(crew_config: Dict[str, Any], ingestion_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the analysis step of the crew.
    
    Args:
        crew_config: Crew configuration dictionary
        ingestion_result: Results from ingestion step
        
    Returns:
        Dictionary containing analysis results
        
    Raises:
        CrewExecutionError: If analysis step fails
    """
    logger.info("Executing analysis step")
    
    try:
        tasks = crew_config["tasks"]
        
        if "analysis_task" not in tasks:
            raise CrewExecutionError("Analysis task not available in crew")
        
        # Get normalized data path from ingestion result
        normalized_data_path = ingestion_result.get("normalized_data_path")
        if not normalized_data_path:
            raise CrewExecutionError("No normalized data path from ingestion step")
        
        # Execute analysis task
        analysis_result = tasks["analysis_task"](normalized_data_path)
        
        # Validate result structure
        required_keys = ["metrics_data", "summary", "fail_by_module", "defects_by_severity"]
        for key in required_keys:
            if key not in analysis_result:
                raise CrewExecutionError(f"Missing required key '{key}' in analysis result")
        
        # Log summary metrics
        summary = analysis_result.get("summary", {})
        logger.info(f"Analysis step completed - Total: {summary.get('total', 0)}, "
                   f"Executed: {summary.get('executed', 0)}, "
                   f"Pass Rate: {summary.get('pass_pct', 0):.1f}%")
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Analysis step failed: {str(e)}")
        raise CrewExecutionError(f"Analysis step failed: {str(e)}")


def execute_report_step(crew_config: Dict[str, Any], analysis_result: Dict[str, Any], 
                       metadata: Dict[str, str]) -> Dict[str, Any]:
    """
    Execute the report step of the crew.
    
    Args:
        crew_config: Crew configuration dictionary
        analysis_result: Results from analysis step
        metadata: Project metadata for report generation
        
    Returns:
        Dictionary containing report results
        
    Raises:
        CrewExecutionError: If report step fails
    """
    logger.info("Executing report step")
    
    try:
        tasks = crew_config["tasks"]
        
        if "report_task" not in tasks:
            raise CrewExecutionError("Report task not available in crew")
        
        # Execute report task
        report_result = tasks["report_task"](analysis_result, metadata)
        
        # Validate result structure
        required_keys = ["report_data", "introduction", "test_summary", "key_findings"]
        for key in required_keys:
            if key not in report_result:
                raise CrewExecutionError(f"Missing required key '{key}' in report result")
        
        # Log report sections
        key_findings = report_result.get("key_findings", {})
        stable_areas = key_findings.get("stable_areas", [])
        risky_areas = key_findings.get("risky_areas", [])
        
        logger.info(f"Report step completed - Stable areas: {len(stable_areas)}, "
                   f"Risky areas: {len(risky_areas)}")
        
        return report_result
        
    except Exception as e:
        logger.error(f"Report step failed: {str(e)}")
        raise CrewExecutionError(f"Report step failed: {str(e)}")


def run_crew(file_path: str, metadata: Dict[str, str]) -> Dict[str, Any]:
    """
    Execute the complete TSR generation crew workflow.
    
    This function orchestrates the sequential execution of:
    1. Ingestion Task: Processes test execution file and normalizes data
    2. Analysis Task: Computes comprehensive test execution metrics  
    3. Report Task: Generates structured TSR content
    
    Args:
        file_path: Path to test execution file (e.g., 'data/sample_tc_execution.xlsx')
        metadata: Project metadata dictionary containing:
            - project: Project name
            - release: Release version
            - environment: Test environment details
            - scope: Test scope description
            - objectives: Test objectives
            - linked_plan: Linked test plan identifier
            
    Returns:
        Dictionary containing complete TSR context ready for templating:
        - ingestion_result: Results from ingestion step
        - analysis_result: Results from analysis step
        - report_result: Results from report step
        - execution_summary: Crew execution metadata
        - template_context: Combined context for template rendering
        
    Raises:
        CrewExecutionError: If crew execution fails at any step
        
    Example:
        >>> metadata = {
        ...     'project': 'SampleProject',
        ...     'release': 'R1.0.3',
        ...     'environment': 'Windows 11, Chrome 126',
        ...     'scope': 'Login, Checkout, Profile, Orders',
        ...     'objectives': 'Functional + Regression',
        ...     'linked_plan': 'TP-001'
        ... }
        >>> result = run_crew('data/sample_tc_execution.xlsx', metadata)
        >>> print(f"TSR generated with {len(result['template_context'])} context items")
    """
    logger.info("Starting TSR generation crew execution")
    logger.info(f"File: {file_path}")
    logger.info(f"Project: {metadata.get('project', 'N/A')} - {metadata.get('release', 'N/A')}")
    
    try:
        # Build crew configuration
        crew_config = build_crew()
        
        # Track execution steps
        execution_steps = []
        start_time = __import__('time').time()
        
        # Step 1: Ingestion
        logger.info("=" * 50)
        logger.info("STEP 1: INGESTION")
        logger.info("=" * 50)
        
        ingestion_result = execute_ingestion_step(crew_config, file_path)
        execution_steps.append({
            "step": 1,
            "name": "ingestion",
            "status": "completed",
            "result_keys": list(ingestion_result.keys())
        })
        
        # Step 2: Analysis
        logger.info("=" * 50)
        logger.info("STEP 2: ANALYSIS")
        logger.info("=" * 50)
        
        analysis_result = execute_analysis_step(crew_config, ingestion_result)
        execution_steps.append({
            "step": 2,
            "name": "analysis", 
            "status": "completed",
            "result_keys": list(analysis_result.keys())
        })
        
        # Step 3: Report
        logger.info("=" * 50)
        logger.info("STEP 3: REPORT")
        logger.info("=" * 50)
        
        report_result = execute_report_step(crew_config, analysis_result, metadata)
        execution_steps.append({
            "step": 3,
            "name": "report",
            "status": "completed", 
            "result_keys": list(report_result.keys())
        })
        
        # Calculate execution time
        end_time = __import__('time').time()
        execution_time = end_time - start_time
        
        # Build execution summary
        execution_summary = {
            "total_steps": len(execution_steps),
            "completed_steps": len([s for s in execution_steps if s["status"] == "completed"]),
            "execution_time_seconds": round(execution_time, 2),
            "steps": execution_steps,
            "crew_config": crew_config["metadata"],
            "file_processed": file_path,
            "project": metadata.get("project", "N/A"),
            "release": metadata.get("release", "N/A")
        }
        
        # Build template context
        template_context = {
            # Project metadata
            "project": metadata.get("project", "N/A"),
            "release": metadata.get("release", "N/A"),
            "environment": metadata.get("environment", "N/A"),
            "scope": metadata.get("scope", "N/A"),
            "objectives": metadata.get("objectives", "N/A"),
            "linked_plan": metadata.get("linked_plan", "N/A"),
            
            # Ingestion data
            "file_type": ingestion_result.get("file_type", "unknown"),
            "canonical_columns": ingestion_result.get("canonical_columns", []),
            "readiness_note": ingestion_result.get("readiness_note", ""),
            "data_issues": ingestion_result.get("issues", []),
            
            # Analysis metrics
            "summary": analysis_result.get("summary", {}),
            "fail_by_module": analysis_result.get("fail_by_module", {}),
            "defects_by_severity": analysis_result.get("defects_by_severity", {}),
            "defects_by_priority": analysis_result.get("defects_by_priority", {}),
            "density": analysis_result.get("density", {}),
            "flaky_tests": analysis_result.get("flaky_tests", []),
            "key_bugs": analysis_result.get("key_bugs", []),
            "likely_causes": analysis_result.get("likely_causes", {}),
            
            # Report content
            "introduction": report_result.get("introduction", ""),
            "test_summary": report_result.get("test_summary", ""),
            "variances": report_result.get("variances", []),
            "defect_summary_matrix": report_result.get("defect_summary_matrix", {}),
            "key_findings": report_result.get("key_findings", {}),
            "exit_criteria": report_result.get("exit_criteria", {}),
            "recommendations": report_result.get("recommendations", []),
            "signoff": report_result.get("signoff", {}),
            
            # Execution metadata
            "execution_summary": execution_summary,
            "generated_at": __import__('datetime').datetime.now().isoformat()
        }
        
        # Build final result
        result = {
            "ingestion_result": ingestion_result,
            "analysis_result": analysis_result,
            "report_result": report_result,
            "execution_summary": execution_summary,
            "template_context": template_context
        }
        
        logger.info("=" * 50)
        logger.info("CREW EXECUTION COMPLETED SUCCESSFULLY")
        logger.info("=" * 50)
        logger.info(f"Execution time: {execution_time:.2f} seconds")
        logger.info(f"Template context items: {len(template_context)}")
        logger.info(f"Ready for template rendering")
        
        return result
        
    except Exception as e:
        logger.error(f"Crew execution failed: {str(e)}")
        raise CrewExecutionError(f"Crew execution failed: {str(e)}")


def get_crew_status(crew_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get the current status of the crew configuration.
    
    Args:
        crew_config: Optional crew configuration (will build if not provided)
        
    Returns:
        Dictionary containing crew status information
    """
    if crew_config is None:
        try:
            crew_config = build_crew()
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to build crew: {str(e)}",
                "agents_available": 0,
                "tasks_available": 0
            }
    
    agents = crew_config.get("agents", {})
    tasks = crew_config.get("tasks", {})
    
    return {
        "status": "ready",
        "agents_available": len(agents),
        "tasks_available": len(tasks),
        "agent_names": list(agents.keys()),
        "task_names": list(tasks.keys()),
        "flow_steps": len(crew_config.get("flow", [])),
        "verbose": CREWAI_VERBOSE,
        "debug": CREWAI_DEBUG
    }


# Example usage and testing
if __name__ == "__main__":
    """Test crew building and execution."""
    logger.info("Testing TSR generation crew...")
    
    try:
        # Test crew building
        logger.info("Testing crew building...")
        crew_config = build_crew()
        logger.info(f"Crew built successfully with {len(crew_config['agents'])} agents and {len(crew_config['tasks'])} tasks")
        
        # Test crew status
        logger.info("Testing crew status...")
        status = get_crew_status(crew_config)
        logger.info(f"Crew status: {status}")
        
        # Test crew execution (with placeholder data)
        logger.info("Testing crew execution...")
        test_metadata = {
            "project": "TestProject",
            "release": "R1.0.0",
            "environment": "Test Environment",
            "scope": "Test Scope",
            "objectives": "Test Objectives",
            "linked_plan": "TP-001"
        }
        
        # Note: This would require actual file processing
        logger.info("Crew execution test ready (requires actual file)")
        logger.info("Example usage:")
        logger.info("  result = run_crew('data/sample_tc_execution.xlsx', test_metadata)")
        
        logger.info("Crew testing completed successfully")
        
    except Exception as e:
        logger.error(f"Error during crew testing: {str(e)}")
        raise