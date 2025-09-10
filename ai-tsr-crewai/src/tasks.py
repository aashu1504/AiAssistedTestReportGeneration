"""CrewAI tasks for TSR generation with JSON validation and data flow."""

import os
import json
import logging
import tempfile
import pandas as pd
from typing import Dict, Any, Optional, Union
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

logger.info(f"Tasks module loaded - CREWAI_VERBOSE: {CREWAI_VERBOSE}, CREWAI_DEBUG: {CREWAI_DEBUG}")


class TaskValidationError(Exception):
    """Custom exception for task validation errors."""
    pass


class TaskExecutionError(Exception):
    """Custom exception for task execution errors."""
    pass


def validate_ingestion_response(response: Dict[str, Any]) -> None:
    """
    Validate ingestion agent response JSON structure.
    
    Expected structure:
    {
        "file_type": "xlsx|csv|json|xml",
        "canonical_columns": ["Module", "TestCaseID", "Description", "Run", "Result", "BugID", "Priority", "Severity", "Duration", "Tester"],
        "issues": ["list", "of", "data", "quality", "issues"],
        "readiness_note": "assessment of data readiness for analysis"
    }
    
    Args:
        response: JSON response from ingestion agent
        
    Raises:
        TaskValidationError: If required keys are missing or invalid
    """
    required_keys = ["file_type", "canonical_columns", "issues", "readiness_note"]
    
    for key in required_keys:
        if key not in response:
            raise TaskValidationError(f"Missing required key '{key}' in ingestion response")
    
    if not isinstance(response["canonical_columns"], list):
        raise TaskValidationError("'canonical_columns' must be a list")
    
    if not isinstance(response["issues"], list):
        raise TaskValidationError("'issues' must be a list")
    
    logger.debug("Ingestion response validation passed")


def validate_analysis_response(response: Dict[str, Any]) -> None:
    """
    Validate analysis agent response JSON structure.
    
    Expected structure:
    {
        "summary": {
            "total": number,
            "executed": number,
            "passed": number,
            "failed": number,
            "blocked": number,
            "skipped": number,
            "pass_pct": percentage
        },
        "fail_by_module": {"module_name": failure_count},
        "defects_by_severity": {"Critical": count, "Major": count, "Medium": count, "Minor": count},
        "defects_by_priority": {"Highest": count, "High": count, "Medium": count, "Low": count},
        "density": {"module_name": defect_count},
        "flaky": ["TestCaseID1", "TestCaseID2"],
        "key_bugs": ["BUG-001", "BUG-002"],
        "likely_causes": {"module_name": "Product/Automation/Environment - reason"}
    }
    
    Args:
        response: JSON response from analysis agent
        
    Raises:
        TaskValidationError: If required keys are missing or invalid
    """
    required_keys = ["summary", "fail_by_module", "defects_by_severity", "defects_by_priority", 
                    "density", "flaky", "key_bugs", "likely_causes"]
    
    for key in required_keys:
        if key not in response:
            raise TaskValidationError(f"Missing required key '{key}' in analysis response")
    
    # Validate summary structure
    summary_keys = ["total", "executed", "passed", "failed", "blocked", "skipped", "pass_pct"]
    for key in summary_keys:
        if key not in response["summary"]:
            raise TaskValidationError(f"Missing required key '{key}' in summary")
    
    # Validate data types
    if not isinstance(response["fail_by_module"], dict):
        raise TaskValidationError("'fail_by_module' must be a dictionary")
    
    if not isinstance(response["flaky"], list):
        raise TaskValidationError("'flaky' must be a list")
    
    if not isinstance(response["key_bugs"], list):
        raise TaskValidationError("'key_bugs' must be a list")
    
    logger.debug("Analysis response validation passed")


def validate_report_response(response: Dict[str, Any]) -> None:
    """
    Validate report agent response JSON structure.
    
    Expected structure:
    {
        "introduction": "Executive summary of test execution and objectives",
        "test_summary": "High-level overview of test results and key metrics",
        "variances": ["List of any deviations from planned execution"],
        "defect_summary_matrix": {
            "critical": count,
            "major": count,
            "medium": count,
            "minor": count
        },
        "key_findings": {
            "stable_areas": ["List of well-performing modules/areas"],
            "risky_areas": ["List of problematic modules/areas requiring attention"]
        },
        "exit_criteria": {
            "met": ["List of criteria successfully met"],
            "not_met": ["List of criteria not met with impact assessment"]
        },
        "recommendations": ["List of actionable recommendations for improvement"],
        "signoff": {
            "test_lead": "Name or TBD",
            "dev_lead": "Name or TBD",
            "product_owner": "Name or TBD",
            "qa_manager": "Name or TBD"
        }
    }
    
    Args:
        response: JSON response from report agent
        
    Raises:
        TaskValidationError: If required keys are missing or invalid
    """
    required_keys = ["introduction", "test_summary", "variances", "defect_summary_matrix",
                    "key_findings", "exit_criteria", "recommendations", "signoff"]
    
    for key in required_keys:
        if key not in response:
            raise TaskValidationError(f"Missing required key '{key}' in report response")
    
    # Validate nested structures
    if not isinstance(response["variances"], list):
        raise TaskValidationError("'variances' must be a list")
    
    if not isinstance(response["recommendations"], list):
        raise TaskValidationError("'recommendations' must be a list")
    
    # Validate key_findings structure
    if not isinstance(response["key_findings"], dict):
        raise TaskValidationError("'key_findings' must be a dictionary")
    
    if "stable_areas" not in response["key_findings"] or "risky_areas" not in response["key_findings"]:
        raise TaskValidationError("'key_findings' must contain 'stable_areas' and 'risky_areas'")
    
    logger.debug("Report response validation passed")


def create_ingestion_task(agent, file_path: str = "data/sample_tc_execution.xlsx") -> Dict[str, Any]:
    """
    Create ingestion task that processes test execution file and normalizes data.
    
    This task:
    1. Reads the specified file using tools.py functions
    2. Invokes ingestion_agent with file path
    3. Validates the readiness JSON response
    4. Saves normalized DataFrame to temporary CSV for next step
    
    Args:
        agent: Configured ingestion agent
        file_path: Path to test execution file (default: data/sample_tc_execution.xlsx)
        
    Returns:
        Dictionary containing:
        - readiness_data: Validated JSON response from agent
        - normalized_data_path: Path to temporary CSV with normalized data
        - file_type: Detected file type
        - canonical_columns: List of canonical column names
        
    Raises:
        TaskExecutionError: If file processing or agent invocation fails
        TaskValidationError: If agent response validation fails
    """
    logger.info(f"Starting ingestion task for file: {file_path}")
    
    try:
        # Import tools for file processing
        from .tools import read_execution_file, normalize_columns
        
        # Read and normalize the file
        logger.debug(f"Reading execution file: {file_path}")
        raw_df = read_execution_file(file_path)
        logger.info(f"Raw data loaded: {len(raw_df)} rows, {len(raw_df.columns)} columns")
        
        # Normalize columns
        logger.debug("Normalizing columns to canonical format")
        normalized_df = normalize_columns(raw_df)
        logger.info(f"Data normalized: {len(normalized_df)} rows, {len(normalized_df.columns)} columns")
        
        # Create temporary CSV for next step
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        normalized_df.to_csv(temp_file.name, index=False)
        temp_file.close()
        logger.debug(f"Normalized data saved to: {temp_file.name}")
        
        # Prepare agent input
        agent_input = f"""
        Process the following test execution file:
        - File path: {file_path}
        - File type: {file_path.split('.')[-1].upper()}
        - Rows: {len(normalized_df)}
        - Columns: {list(normalized_df.columns)}
        
        Sample data (first 3 rows):
        {normalized_df.head(3).to_string()}
        
        Please analyze the data and provide readiness assessment.
        """
        
        # Invoke agent
        logger.debug("Invoking ingestion agent")
        if hasattr(agent, 'invoke') and callable(getattr(agent, 'invoke')):
            # Direct agent invocation
            response_text = agent.invoke(agent_input)
        elif hasattr(agent, 'execute_task') and callable(getattr(agent, 'execute_task')):
            # CrewAI agent execution
            response_text = agent.execute_task(agent_input)
        elif hasattr(agent, 'llm') and hasattr(agent.llm, 'invoke'):
            # Use agent's LLM directly
            response_text = agent.llm.invoke(agent_input)
        else:
            # Fallback - return placeholder response
            logger.warning("Using placeholder response for ingestion agent")
            response_text = {
                "file_type": "xlsx",
                "canonical_columns": ["Module", "TestCaseID", "Description", "Run", "Result", "BugID", "Priority", "Severity", "Duration", "Tester"],
                "issues": ["Using placeholder analysis - actual AI analysis not available"],
                "readiness_note": "Data normalized and ready for analysis (placeholder response)"
            }
        
        # Parse JSON response
        try:
            if isinstance(response_text, str):
                response_data = json.loads(response_text)
            else:
                response_data = response_text
        except json.JSONDecodeError as e:
            raise TaskExecutionError(f"Failed to parse agent response as JSON: {e}")
        
        # Validate response
        validate_ingestion_response(response_data)
        
        # Prepare result
        result = {
            "readiness_data": response_data,
            "normalized_data_path": temp_file.name,
            "file_type": response_data.get("file_type", "unknown"),
            "canonical_columns": response_data.get("canonical_columns", []),
            "issues": response_data.get("issues", []),
            "readiness_note": response_data.get("readiness_note", "")
        }
        
        logger.info("Ingestion task completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Ingestion task failed: {str(e)}")
        raise TaskExecutionError(f"Ingestion task failed: {str(e)}")


def create_analysis_task(agent, normalized_data: Union[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Create analysis task that computes comprehensive test execution metrics.
    
    This task:
    1. Loads normalized data (from CSV path or DataFrame)
    2. Invokes analysis_agent with sample data
    3. Validates the metrics JSON response
    4. Returns computed metrics and insights
    
    Args:
        agent: Configured analysis agent
        normalized_data: Path to normalized CSV file or DataFrame
        
    Returns:
        Dictionary containing:
        - metrics_data: Validated JSON response from agent
        - summary: Basic test execution summary
        - fail_by_module: Failures grouped by module
        - defects_by_severity: Defects grouped by severity
        - defects_by_priority: Defects grouped by priority
        - density: Defect density per module
        - flaky_tests: List of flaky test case IDs
        - key_bugs: List of key bug IDs
        - likely_causes: Analysis of failure causes by module
        
    Raises:
        TaskExecutionError: If data processing or agent invocation fails
        TaskValidationError: If agent response validation fails
    """
    logger.info("Starting analysis task")
    
    try:
        # Load normalized data
        if isinstance(normalized_data, str):
            logger.debug(f"Loading normalized data from: {normalized_data}")
            try:
                df = pd.read_csv(normalized_data, encoding='utf-8')
            except UnicodeDecodeError:
                logger.warning("UTF-8 encoding failed, trying latin-1")
                df = pd.read_csv(normalized_data, encoding='latin-1')
        else:
            logger.debug("Using provided DataFrame")
            df = normalized_data.copy()
        
        logger.info(f"Analysis data loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Prepare sample data for agent (limit size for large datasets)
        if len(df) > 1000:
            sample_df = df.sample(n=1000, random_state=42)
            logger.info(f"Using sample of {len(sample_df)} rows for analysis")
        else:
            sample_df = df
        
        # Prepare agent input with sample data
        agent_input = f"""
        Analyze the following normalized test execution data:
        
        Dataset summary:
        - Total rows: {len(df)}
        - Sample rows for analysis: {len(sample_df)}
        - Columns: {list(df.columns)}
        
        Sample data (first 5 rows):
        {sample_df.head(5).to_string()}
        
        Column value counts:
        {sample_df['Result'].value_counts().to_string() if 'Result' in sample_df.columns else 'Result column not found'}
        
        Please compute comprehensive metrics and provide analytical insights.
        """
        
        # Invoke agent
        logger.debug("Invoking analysis agent")
        if hasattr(agent, 'invoke') and callable(getattr(agent, 'invoke')):
            # Direct agent invocation
            response_text = agent.invoke(agent_input)
        elif hasattr(agent, 'execute_task') and callable(getattr(agent, 'execute_task')):
            # CrewAI agent execution
            response_text = agent.execute_task(agent_input)
        elif hasattr(agent, 'llm') and hasattr(agent.llm, 'invoke'):
            # Use agent's LLM directly
            response_text = agent.llm.invoke(agent_input)
        else:
            # Fallback - return placeholder response
            logger.warning("Using placeholder response for analysis agent")
            response_text = {
                "summary": {"total": len(df), "executed": len(df), "passed": len(df[df['Result'] == 'Pass']), "failed": len(df[df['Result'] == 'Fail']), "blocked": 0, "skipped": 0, "pass_pct": (len(df[df['Result'] == 'Pass']) / len(df)) * 100},
                "fail_by_module": df[df['Result'] == 'Fail']['Module'].value_counts().to_dict(),
                "defects_by_severity": df[df['BugID'].notna()]['Severity'].value_counts().to_dict(),
                "defects_by_priority": df[df['BugID'].notna()]['Priority'].value_counts().to_dict(),
                "density": df[df['BugID'].notna()]['Module'].value_counts().to_dict(),
                "flaky_tests": [],
                "key_bugs": df[df['BugID'].notna()]['BugID'].unique().tolist(),
                "likely_causes": {"Product": "Potential product issues identified", "Automation": "Test automation stability concerns", "Environment": "Environment-related test failures"}
            }
        
        # Parse JSON response
        try:
            if isinstance(response_text, str):
                response_data = json.loads(response_text)
            else:
                response_data = response_text
        except json.JSONDecodeError as e:
            raise TaskExecutionError(f"Failed to parse agent response as JSON: {e}")
        
        # Validate response
        validate_analysis_response(response_data)
        
        # Prepare result
        result = {
            "metrics_data": response_data,
            "summary": response_data.get("summary", {}),
            "fail_by_module": response_data.get("fail_by_module", {}),
            "defects_by_severity": response_data.get("defects_by_severity", {}),
            "defects_by_priority": response_data.get("defects_by_priority", {}),
            "density": response_data.get("density", {}),
            "flaky_tests": response_data.get("flaky", []),
            "key_bugs": response_data.get("key_bugs", []),
            "likely_causes": response_data.get("likely_causes", {})
        }
        
        logger.info("Analysis task completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Analysis task failed: {str(e)}")
        raise TaskExecutionError(f"Analysis task failed: {str(e)}")


def create_report_task(agent, metrics_data: Dict[str, Any], metadata: Dict[str, str]) -> Dict[str, Any]:
    """
    Create report task that generates structured TSR content.
    
    This task:
    1. Combines metrics data with project metadata
    2. Invokes report_agent to generate narrative sections
    3. Validates the report JSON response
    4. Returns structured TSR content
    
    Args:
        agent: Configured report agent
        metrics_data: Metrics data from analysis task
        metadata: Project metadata (project, release, environment, scope, objectives, linked_plan)
        
    Returns:
        Dictionary containing:
        - report_data: Validated JSON response from agent
        - introduction: Executive summary
        - test_summary: High-level test results overview
        - variances: List of execution deviations
        - defect_summary_matrix: Defect counts by severity
        - key_findings: Stable and risky areas analysis
        - exit_criteria: Met and not met criteria
        - recommendations: Actionable improvement recommendations
        - signoff: Stakeholder sign-off information
        
    Raises:
        TaskExecutionError: If agent invocation fails
        TaskValidationError: If agent response validation fails
    """
    logger.info("Starting report task")
    
    try:
        # Prepare agent input with metrics and metadata
        agent_input = f"""
        Generate a comprehensive Test Summary Report based on the following data:
        
        Project Metadata:
        - Project: {metadata.get('project', 'N/A')}
        - Release: {metadata.get('release', 'N/A')}
        - Environment: {metadata.get('environment', 'N/A')}
        - Scope: {metadata.get('scope', 'N/A')}
        - Objectives: {metadata.get('objectives', 'N/A')}
        - Linked Plan: {metadata.get('linked_plan', 'N/A')}
        
        Test Execution Metrics:
        - Summary: {json.dumps(metrics_data.get('summary', {}), indent=2)}
        - Failures by Module: {json.dumps(metrics_data.get('fail_by_module', {}), indent=2)}
        - Defects by Severity: {json.dumps(metrics_data.get('defects_by_severity', {}), indent=2)}
        - Defects by Priority: {json.dumps(metrics_data.get('defects_by_priority', {}), indent=2)}
        - Defect Density: {json.dumps(metrics_data.get('density', {}), indent=2)}
        - Flaky Tests: {metrics_data.get('flaky_tests', [])}
        - Key Bugs: {metrics_data.get('key_bugs', [])}
        - Likely Causes: {json.dumps(metrics_data.get('likely_causes', {}), indent=2)}
        
        Please generate structured TSR content with professional narratives.
        """
        
        # Invoke agent
        logger.debug("Invoking report agent")
        if hasattr(agent, 'invoke') and callable(getattr(agent, 'invoke')):
            # Direct agent invocation
            response_text = agent.invoke(agent_input)
        elif hasattr(agent, 'execute_task') and callable(getattr(agent, 'execute_task')):
            # CrewAI agent execution
            response_text = agent.execute_task(agent_input)
        elif hasattr(agent, 'llm') and hasattr(agent.llm, 'invoke'):
            # Use agent's LLM directly
            response_text = agent.llm.invoke(agent_input)
        else:
            # Fallback - return placeholder response
            logger.warning("Using placeholder response for report agent")
            response_text = {
                "introduction": f"Test Summary Report for {metadata.get('project', 'Project')} {metadata.get('release', 'Release')}",
                "test_summary": "Comprehensive test execution analysis completed",
                "variances": ["Test execution completed as planned", "No significant deviations from test plan"],
                "defect_summary_matrix": "Defect analysis completed with severity and priority breakdown",
                "key_findings": {"Stable": "Core functionality working as expected", "Risky": "Some test failures require attention"},
                "exit_criteria": {"Met": True, "Details": "All critical test cases executed successfully"},
                "recommendations": ["Address identified defects", "Improve test coverage", "Enhance test automation"],
                "signoff": {"test_lead": "TBD", "test_engineer": "TBD", "dev_lead": "TBD", "product_lead": "TBD"}
            }
        
        # Parse JSON response
        try:
            if isinstance(response_text, str):
                response_data = json.loads(response_text)
            else:
                response_data = response_text
        except json.JSONDecodeError as e:
            raise TaskExecutionError(f"Failed to parse agent response as JSON: {e}")
        
        # Validate response
        validate_report_response(response_data)
        
        # Prepare result
        result = {
            "report_data": response_data,
            "introduction": response_data.get("introduction", ""),
            "test_summary": response_data.get("test_summary", ""),
            "variances": response_data.get("variances", []),
            "defect_summary_matrix": response_data.get("defect_summary_matrix", {}),
            "key_findings": response_data.get("key_findings", {}),
            "exit_criteria": response_data.get("exit_criteria", {}),
            "recommendations": response_data.get("recommendations", []),
            "signoff": response_data.get("signoff", {})
        }
        
        logger.info("Report task completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Report task failed: {str(e)}")
        raise TaskExecutionError(f"Report task failed: {str(e)}")


def create_all_tasks(agents: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create all three tasks with their respective agents.
    
    Args:
        agents: Dictionary containing configured agents
        
    Returns:
        Dictionary containing task functions
    """
    logger.info("Creating all TSR generation tasks")
    
    tasks = {}
    
    # Create ingestion task
    if 'ingestion_agent' in agents and agents['ingestion_agent']:
        tasks['ingestion_task'] = lambda file_path="data/sample_tc_execution.xlsx": create_ingestion_task(
            agents['ingestion_agent'], file_path
        )
        logger.debug("Ingestion task created")
    else:
        logger.warning("Ingestion agent not available, skipping ingestion task")
    
    # Create analysis task
    if 'analysis_agent' in agents and agents['analysis_agent']:
        tasks['analysis_task'] = lambda normalized_data: create_analysis_task(
            agents['analysis_agent'], normalized_data
        )
        logger.debug("Analysis task created")
    else:
        logger.warning("Analysis agent not available, skipping analysis task")
    
    # Create report task
    if 'report_agent' in agents and agents['report_agent']:
        tasks['report_task'] = lambda metrics_data, metadata: create_report_task(
            agents['report_agent'], metrics_data, metadata
        )
        logger.debug("Report task created")
    else:
        logger.warning("Report agent not available, skipping report task")
    
    logger.info(f"Successfully created {len(tasks)} tasks: {list(tasks.keys())}")
    return tasks


# Example usage and testing
if __name__ == "__main__":
    """Test task creation and execution."""
    logger.info("Testing task creation...")
    
    try:
        # Test with placeholder agents
        from .agents import create_all_agents
        
        # Create agents
        agents = create_all_agents()
        logger.info(f"Created {len(agents)} agents: {list(agents.keys())}")
        
        # Create tasks
        tasks = create_all_tasks(agents)
        logger.info(f"Created {len(tasks)} tasks: {list(tasks.keys())}")
        
        # Test task execution if agents are available
        if 'ingestion_task' in tasks:
            logger.info("Testing ingestion task...")
            # Note: This would require actual file processing
            logger.info("Ingestion task ready for execution")
        
        logger.info("Task creation test completed successfully")
        
    except Exception as e:
        logger.error(f"Error during task creation test: {str(e)}")
        raise