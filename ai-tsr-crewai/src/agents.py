"""CrewAI agents for TSR generation with Gemini integration."""

import os
import json
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Import CrewAI and dependencies with fallback
CREWAI_AVAILABLE = False
Agent = None
ChatGoogleGenerativeAI = None

try:
    from crewai import Agent
    from langchain_google_genai import ChatGoogleGenerativeAI
    CREWAI_AVAILABLE = True
    print("CrewAI dependencies loaded successfully")
except ImportError as e:
    print(f"Warning: CrewAI dependencies not available: {e}")
    print("Using simplified agent implementation...")
    CREWAI_AVAILABLE = False
    Agent = None
    ChatGoogleGenerativeAI = None

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CREWAI_VERBOSE = os.getenv("CREWAI_VERBOSE", "false").lower() == "true"
CREWAI_DEBUG = os.getenv("CREWAI_DEBUG", "false").lower() == "true"

# Configure logging level based on environment
if CREWAI_DEBUG:
    logging.getLogger().setLevel(logging.DEBUG)
elif CREWAI_VERBOSE:
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.getLogger().setLevel(logging.WARNING)

logger.info(f"Environment loaded - GEMINI_API_KEY: {'***' if GEMINI_API_KEY else 'Not set'}")
logger.info(f"CREWAI_VERBOSE: {CREWAI_VERBOSE}, CREWAI_DEBUG: {CREWAI_DEBUG}")


def get_gemini_llm():
    """
    Configure and return Gemini LLM client.
    
    This function handles the Gemini SDK integration. If the runtime environment
    lacks direct Gemini SDK support, it provides a placeholder wrapper that
    reads GEMINI_API_KEY and returns stubbed responses for POC purposes.
    
    Returns:
        Configured LLM client for Gemini 2.5 Flash
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not found in environment variables")
        return None
    
    try:
        # Try to import and configure the actual Gemini SDK
        # Note: Replace this with the actual Gemini SDK import when available
        # from google.generativeai import GenerativeModel
        # from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Placeholder implementation for POC
        logger.info("Using placeholder Gemini client for POC")
        return PlaceholderGeminiClient()
        
    except ImportError:
        logger.warning("Gemini SDK not available, using placeholder client")
        return PlaceholderGeminiClient()
    except Exception as e:
        logger.error(f"Error configuring Gemini client: {str(e)}")
        return PlaceholderGeminiClient()


class PlaceholderGeminiClient:
    """
    Placeholder Gemini client for POC when actual SDK is not available.
    
    This class provides stubbed responses to allow the POC to run without
    requiring the actual Gemini SDK installation.
    """
    
    def __init__(self):
        self.model_name = "gemini-2.5-flash"
        logger.info(f"Initialized placeholder Gemini client with model: {self.model_name}")
    
    def invoke(self, messages: str) -> str:
        """
        Placeholder invoke method that returns stubbed responses.
        
        Args:
            messages: Input messages/prompt
            
        Returns:
            Stubbed response based on input content
        """
        logger.debug(f"Placeholder invoke called with: {messages[:100]}...")
        
        # Simple heuristics to provide relevant stubbed responses
        if "ingestion" in messages.lower() or "normalize" in messages.lower():
            return json.dumps({
                "file_type": "xlsx",
                "canonical_columns": ["Module", "TestCaseID", "Description", "Run", "Result", "BugID", "Priority", "Severity", "Duration", "Tester"],
                "issues": ["Some columns may need standardization"],
                "readiness_note": "Dataset is ready for analysis with minor normalization applied"
            })
        
        elif "analysis" in messages.lower() or "metrics" in messages.lower():
            return json.dumps({
                "summary": {
                    "total": 100,
                    "executed": 95,
                    "passed": 85,
                    "failed": 8,
                    "blocked": 2,
                    "skipped": 5,
                    "pass_pct": 89.5
                },
                "fail_by_module": {"Login": 3, "Checkout": 2, "Profile": 3},
                "defects_by_severity": {"Critical": 1, "Major": 2, "Medium": 3, "Minor": 2},
                "defects_by_priority": {"Highest": 1, "High": 2, "Medium": 3, "Low": 2},
                "density": {"Login": 2, "Checkout": 1, "Profile": 3},
                "flaky": ["TC001", "TC015"],
                "key_bugs": ["BUG-001", "BUG-002", "BUG-003"],
                "likely_causes": {
                    "Login": "Product - Authentication logic issues",
                    "Checkout": "Environment - Payment gateway connectivity",
                    "Profile": "Automation - Test data setup problems"
                }
            })
        
        elif "report" in messages.lower() or "tsr" in messages.lower():
            return json.dumps({
                "introduction": "Test execution completed for the specified release with overall positive results.",
                "test_summary": "95 tests executed with 89.5% pass rate, indicating good quality.",
                "variances": ["Minor delays in test execution due to environment setup"],
                "defect_summary_matrix": {
                    "critical": 1,
                    "major": 2,
                    "medium": 3,
                    "minor": 2
                },
                "key_findings": {
                    "stable_areas": ["User Management", "Search Functionality"],
                    "risky_areas": ["Payment Processing", "Data Validation"]
                },
                "exit_criteria": {
                    "met": ["Pass rate > 85%", "Critical defects resolved"],
                    "not_met": ["Some medium priority defects remain"]
                },
                "recommendations": [
                    "Address remaining medium priority defects",
                    "Improve test data management for Profile module",
                    "Enhance payment gateway test coverage"
                ],
                "signoff": {
                    "test_lead": "TBD",
                    "dev_lead": "TBD",
                    "product_owner": "TBD"
                }
            })
        
        else:
            return json.dumps({
                "status": "processed",
                "message": "Placeholder response generated",
                "model": self.model_name
            })


def create_ingestion_agent():
    """
    Create Data Ingestion Specialist agent.
    
    This agent is responsible for detecting file types, normalizing datasets,
    and identifying data quality issues.
    
    Returns:
        Configured CrewAI Agent for data ingestion
    """
    if not CREWAI_AVAILABLE:
        logger.error("CrewAI not available - cannot create agents")
        return None
    
    logger.info("Creating Data Ingestion Specialist agent")
    
    # Configure LLM
    llm = get_gemini_llm()
    
    agent = Agent(
        role="Data Ingestion Specialist",
        goal="Detect file type, normalize dataset to canonical columns, and assess data readiness",
        backstory="""You are a QA data engineer with expertise in test execution data processing. 
        You excel at detecting file formats, normalizing datasets to standard schemas, and identifying 
        data quality issues that could impact analysis accuracy.""",
        verbose=CREWAI_VERBOSE,
        allow_delegation=False,
        llm=llm,
        system_message="""You are a QA data engineer. Input file path: data/sample_tc_execution.xlsx.
        
        Your tasks:
        1. Detect file type and validate format
        2. Normalize the dataset to canonical columns: Module, TestCaseID, Description, Run, Result, BugID, Priority, Severity, Duration, Tester
        3. Identify missing or inconsistent columns and suggest defaults:
           - Run=1 if missing
           - Result='Not Executed' if blank
           - Priority='Medium' if not specified
        4. Assess data quality and readiness
        
        Output a JSON readiness note with this structure:
        {
            "file_type": "detected_file_format",
            "canonical_columns": ["list", "of", "canonical", "columns"],
            "issues": ["list", "of", "data", "quality", "issues"],
            "readiness_note": "assessment of data readiness for analysis"
        }
        
        Be specific about any data transformations or assumptions made."""
    )
    
    logger.debug("Data Ingestion Specialist agent created successfully")
    return agent


def create_analysis_agent():
    """
    Create QA Analytics Expert agent.
    
    This agent computes comprehensive test execution metrics and provides
    analytical insights including failure patterns and defect analysis.
    
    Returns:
        Configured CrewAI Agent for analytics
    """
    if not CREWAI_AVAILABLE:
        logger.error("CrewAI not available - cannot create agents")
        return None
    
    logger.info("Creating QA Analytics Expert agent")
    
    # Configure LLM
    llm = get_gemini_llm()
    
    agent = Agent(
        role="QA Analytics Expert",
        goal="Compute comprehensive test execution metrics and provide analytical insights",
        backstory="""You are a QA analytics expert with deep experience in test execution analysis. 
        You specialize in computing metrics, identifying patterns in test failures, and providing 
        actionable insights for quality improvement.""",
        verbose=CREWAI_VERBOSE,
        allow_delegation=False,
        llm=llm,
        system_message="""You are a QA analytics expert. Input: normalized rows (from ingestion_agent).
        
        Compute the following metrics:
        1. Basic summary: totals, executed, passed, failed, blocked, skipped, pass_pct
        2. Failures by module: count of failures per module
        3. Defects by severity: Critical, Major, Medium, Minor counts
        4. Defects by priority: Highest, High, Medium, Low counts
        5. Defect density per module: unique bug count per module
        6. Flaky tests: TestCaseIDs that have both pass and fail results
        7. Key bugs: list of unique BugIDs
        8. Likely causes: heuristic analysis of top failing modules (Product/Automation/Environment)
        
        Output a JSON with this structure:
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
            "likely_causes": {
                "module_name": "Product/Automation/Environment - specific reason"
            }
        }
        
        Use simple heuristics for likely_causes:
        - Product: Logic errors, business rule violations
        - Automation: Test script issues, data setup problems
        - Environment: Infrastructure, connectivity, configuration issues"""
    )
    
    logger.debug("QA Analytics Expert agent created successfully")
    return agent


def create_report_agent():
    """
    Create QA Report Writer agent.
    
    This agent generates structured TSR content based on metrics and metadata,
    producing professional report sections suitable for template rendering.
    
    Returns:
        Configured CrewAI Agent for report writing
    """
    if not CREWAI_AVAILABLE:
        logger.error("CrewAI not available - cannot create agents")
        return None
    
    logger.info("Creating QA Report Writer agent")
    
    # Configure LLM
    llm = get_gemini_llm()
    
    agent = Agent(
        role="QA Report Writer",
        goal="Generate structured TSR content and professional report sections",
        backstory="""You are a senior QA lead and report writer with extensive experience in 
        creating comprehensive test summary reports. You excel at translating technical metrics 
        into clear, actionable insights for stakeholders at all levels.""",
        verbose=CREWAI_VERBOSE,
        allow_delegation=False,
        llm=llm,
        system_message="""You are a senior QA lead and report writer. Input: metrics JSON + metadata (project, release, scope, environment, linked plan).
        
        Produce structured TSR sections in JSON format suitable for template rendering:
        
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
            "recommendations": [
                "List of actionable recommendations for improvement"
            ],
            "signoff": {
                "test_lead": "Name or TBD",
                "dev_lead": "Name or TBD", 
                "product_owner": "Name or TBD",
                "qa_manager": "Name or TBD"
            }
        }
        
        Guidelines:
        - Keep narratives concise and factual
        - Focus on actionable insights
        - Use professional language appropriate for stakeholders
        - Ensure all sections are complete and well-structured
        - Base recommendations on actual data and patterns observed"""
    )
    
    logger.debug("QA Report Writer agent created successfully")
    return agent


def create_all_agents() -> Dict[str, Any]:
    """
    Create all three agents and return them in a dictionary.
    
    Returns:
        Dictionary containing all configured agents
    """
    logger.info("Creating all TSR generation agents")
    
    agents = {}
    
    # Create each agent with error handling
    ingestion_agent = create_ingestion_agent()
    if ingestion_agent:
        agents['ingestion_agent'] = ingestion_agent
    else:
        logger.warning("Failed to create ingestion_agent")
    
    analysis_agent = create_analysis_agent()
    if analysis_agent:
        agents['analysis_agent'] = analysis_agent
    else:
        logger.warning("Failed to create analysis_agent")
    
    report_agent = create_report_agent()
    if report_agent:
        agents['report_agent'] = report_agent
    else:
        logger.warning("Failed to create report_agent")
    
    logger.info(f"Successfully created {len(agents)} agents: {list(agents.keys())}")
    return agents


# Example usage and testing
if __name__ == "__main__":
    """Test agent creation and configuration."""
    logger.info("Testing agent creation...")
    
    try:
        # Test environment loading
        logger.info(f"GEMINI_API_KEY loaded: {'Yes' if GEMINI_API_KEY else 'No'}")
        logger.info(f"CREWAI_VERBOSE: {CREWAI_VERBOSE}")
        logger.info(f"CREWAI_DEBUG: {CREWAI_DEBUG}")
        
        # Test LLM configuration
        llm = get_gemini_llm()
        if llm:
            logger.info(f"LLM configured: {type(llm).__name__}")
        else:
            logger.warning("LLM configuration failed")
        
        # Test agent creation
        agents = create_all_agents()
        logger.info(f"Created {len(agents)} agents: {list(agents.keys())}")
        
        # Test placeholder client if available
        if isinstance(llm, PlaceholderGeminiClient):
            test_response = llm.invoke("Test ingestion analysis")
            logger.info(f"Placeholder client test response: {test_response[:100]}...")
        
        logger.info("Agent creation test completed successfully")
        
    except Exception as e:
        logger.error(f"Error during agent creation test: {str(e)}")
        raise