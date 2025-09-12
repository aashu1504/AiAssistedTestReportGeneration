#!/usr/bin/env python3
"""
CLI orchestrator for AI-powered Test Summary Report (TSR) generation.

This module provides the main entry point for generating comprehensive test reports
using the CrewAI framework with data processing, visualization, and templating.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv

# Import our modules
from .tools import (
    read_execution_file,
    normalize_columns,
    compute_metrics,
    save_charts,
    render_report
)
from .crew import build_crew, run_crew
from .quality_gates import QualityGateEvaluator


def generate_dynamic_lessons_learned(metrics: Dict[str, Any], summary: Dict[str, Any], modules_covered: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate dynamic lessons learned based on actual test execution data.
    
    Args:
        metrics: Test execution metrics
        summary: Summary statistics
        modules_covered: Module-level statistics
        
    Returns:
        Dictionary with positive, negative, and improvement lessons
    """
    positive = []
    negative = []
    improvements = []
    
    # Extract key metrics
    pass_rate = summary.get('pass_pct', 0)
    executed_tests = summary.get('executed', 0)
    total_tests = summary.get('total', 0)
    failed_tests = summary.get('failed', 0)
    blocked_tests = summary.get('blocked', 0)
    critical_defects = metrics.get('defects_by_severity', {}).get('Critical', 0)
    major_defects = metrics.get('defects_by_severity', {}).get('Major', 0)
    flaky_tests = metrics.get('flaky', [])
    defect_density = metrics.get('density', {})
    
    # Positive lessons based on actual performance
    if executed_tests > 0:
        execution_rate = (executed_tests / total_tests * 100) if total_tests > 0 else 0
        if execution_rate >= 95:
            positive.append(f"Excellent test execution rate of {execution_rate:.1f}% ({executed_tests}/{total_tests} tests)")
        elif execution_rate >= 85:
            positive.append(f"Good test execution rate of {execution_rate:.1f}% ({executed_tests}/{total_tests} tests)")
    
    if pass_rate >= 90:
        positive.append(f"Outstanding pass rate of {pass_rate:.1f}% indicates high quality")
    elif pass_rate >= 80:
        positive.append(f"Good pass rate of {pass_rate:.1f}% shows solid quality")
    elif pass_rate >= 70:
        positive.append(f"Acceptable pass rate of {pass_rate:.1f}% with room for improvement")
    
    if critical_defects == 0:
        positive.append("No critical defects identified - core functionality is stable")
    
    if blocked_tests == 0:
        positive.append("No blocked tests - test environment was stable")
    elif blocked_tests <= 2:
        positive.append(f"Minimal blocked tests ({blocked_tests}) - good environment stability")
    
    if not flaky_tests:
        positive.append("No flaky tests identified - test reliability is good")
    
    # Negative lessons based on actual issues
    if pass_rate < 70:
        negative.append(f"Low pass rate of {pass_rate:.1f}% indicates quality concerns")
    
    if critical_defects > 0:
        negative.append(f"{critical_defects} critical defect(s) require immediate attention")
    
    if major_defects > 2:
        negative.append(f"High number of major defects ({major_defects}) indicates quality issues")
    
    if blocked_tests > 5:
        negative.append(f"High number of blocked tests ({blocked_tests}) indicates environment issues")
    
    if len(flaky_tests) > 0:
        negative.append(f"{len(flaky_tests)} flaky test(s) identified: {', '.join(flaky_tests[:3])}{'...' if len(flaky_tests) > 3 else ''}")
    
    # Module-specific analysis
    high_defect_modules = []
    low_pass_rate_modules = []
    
    for module, data in modules_covered.items():
        module_total = data.get('total', 0)
        module_passed = data.get('passed', 0)
        module_failed = data.get('failed', 0)
        
        if module_total > 0:
            module_pass_rate = (module_passed / module_total * 100)
            
            # Check defect density
            module_defects_data = defect_density.get(module, {})
            module_defects = module_defects_data.get('total', 0) if isinstance(module_defects_data, dict) else module_defects_data
            if module_defects > 0:
                defect_density_ratio = module_defects / module_total
                if defect_density_ratio > 0.3:  # More than 30% of tests have defects
                    high_defect_modules.append(f"{module} ({module_defects} defects)")
            
            # Check pass rate
            if module_pass_rate < 60:
                low_pass_rate_modules.append(f"{module} ({module_pass_rate:.1f}%)")
    
    if high_defect_modules:
        negative.append(f"High defect density in modules: {', '.join(high_defect_modules)}")
    
    if low_pass_rate_modules:
        negative.append(f"Low pass rates in modules: {', '.join(low_pass_rate_modules)}")
    
    # Improvement recommendations based on actual data
    if pass_rate < 80:
        improvements.append("Implement stricter quality gates and code review processes")
        improvements.append("Focus on root cause analysis for failing test cases")
    
    if critical_defects > 0:
        improvements.append("Establish critical defect resolution process with immediate escalation")
        improvements.append("Implement automated testing for critical paths to prevent regression")
    
    if major_defects > 2:
        improvements.append("Increase test coverage for major functionality areas")
        improvements.append("Implement continuous integration with automated testing")
    
    if len(flaky_tests) > 0:
        improvements.append("Investigate and fix flaky tests to improve reliability")
        improvements.append("Implement better test data management and environment stability")
    
    if blocked_tests > 2:
        improvements.append("Improve test environment stability and setup processes")
        improvements.append("Implement better test data management and cleanup")
    
    if high_defect_modules:
        improvements.append("Prioritize high-defect modules for additional testing and development focus")
    
    if low_pass_rate_modules:
        improvements.append("Review and improve test cases for low-performing modules")
    
    # General improvements
    improvements.append("Establish regular test execution schedules and monitoring")
    improvements.append("Implement comprehensive test data management processes")
    improvements.append("Create robust defect tracking and resolution workflows")
    
    # Fallback if no specific lessons
    if not positive and executed_tests > 0:
        positive.append("Test execution completed successfully")
    
    if not negative and executed_tests > 0:
        negative.append("No significant issues identified in this test cycle")
    
    if not improvements:
        improvements.append("Continue current testing practices and monitor for trends")
    
    return {
        'positive': positive,
        'negative': negative,
        'improvements': improvements
    }


def setup_logging(verbose: bool = False, debug: bool = False) -> None:
    """Configure logging based on environment variables."""
    level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def validate_environment() -> None:
    """Validate required environment variables are present."""
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not found in environment variables.")
        print("   Please set GEMINI_API_KEY in your .env file or environment.")
        print("   Example: GEMINI_API_KEY=your_api_key_here")
        sys.exit(1)


def validate_file(file_path: str) -> None:
    """Validate that the input file exists and is readable."""
    if not os.path.exists(file_path):
        print(f"❌ Error: Input file not found: {file_path}")
        print("   Please ensure the file exists and the path is correct.")
        sys.exit(1)
    
    if not os.access(file_path, os.R_OK):
        print(f"❌ Error: Cannot read file: {file_path}")
        print("   Please check file permissions.")
        sys.exit(1)


def generate_report_id(project: str, release: str) -> str:
    """Generate a unique report identifier."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"TSR_{project}_{release}_{timestamp}"


def attempt_pdf_generation(html_path: str, pdf_path: str) -> bool:
    """Attempt to generate PDF from HTML using ReportLab."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from bs4 import BeautifulSoup
        import re
        
        print("📄 Generating PDF report...")
        
        # Read HTML content
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, 
                              rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        # Build content
        story = []
        
        # Extract title
        title = soup.find('h1')
        if title:
            story.append(Paragraph(title.get_text(), title_style))
            story.append(Spacer(1, 12))
        
        # Extract main content
        main_content = soup.find('div', class_='container') or soup.find('body')
        if main_content:
            # Extract text content and convert to paragraphs
            for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div']):
                text = element.get_text().strip()
                if text:
                    if element.name in ['h1', 'h2', 'h3']:
                        story.append(Paragraph(text, styles['Heading2']))
                    else:
                        story.append(Paragraph(text, styles['Normal']))
                    story.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(story)
        print(f"✅ PDF report generated: {pdf_path}")
        return True
        
    except ImportError as e:
        print(f"⚠️  Required library not available: {str(e)}")
        print("   Install with: pip install reportlab beautifulsoup4")
        return False
        
    except Exception as e:
        print(f"⚠️  PDF generation failed: {str(e)}")
        return False


def print_summary(metrics: Dict[str, Any], output_files: Dict[str, str]) -> None:
    """Print a summary of the generated report and metrics."""
    print("\n" + "="*60)
    print("📊 TSR GENERATION SUMMARY")
    print("="*60)
    
    # Report files
    print("\n📁 Generated Files:")
    for file_type, file_path in output_files.items():
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / 1024  # KB
            print(f"   {file_type.upper()}: {file_path} ({file_size:.1f} KB)")
    
    # Test metrics summary
    if 'summary' in metrics:
        summary = metrics['summary']
        print(f"\n📈 Test Execution Summary:")
        print(f"   Total Tests: {summary.get('total', 0)}")
        print(f"   Executed: {summary.get('executed', 0)}")
        print(f"   Passed: {summary.get('passed', 0)}")
        print(f"   Failed: {summary.get('failed', 0)}")
        print(f"   Pass Rate: {summary.get('pass_pct', 0):.1f}%")
    
    # Defect summary
    if 'defects_by_severity' in metrics:
        defects = metrics['defects_by_severity']
        total_defects = sum(defects.values())
        print(f"\n🐛 Defect Summary:")
        print(f"   Total Defects: {total_defects}")
        for severity, count in defects.items():
            if count > 0:
                print(f"   {severity}: {count}")
    
    print("\n✅ TSR generation completed successfully!")
    print("="*60)


def main() -> int:
    """Main CLI entry point for TSR generation."""
    parser = argparse.ArgumentParser(
        description="Generate AI-powered Test Summary Reports using CrewAI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main --file data/sample_tc_execution.xlsx --project "SampleProject" --release "R1.0.0" --environment "QA Windows/Chrome" --scope "Login, Checkout, Orders" --objectives "Functional Regression" --linked_plan "TP-001"
  
  python -m src.main --file data/test_results.csv --project "MyApp" --release "v2.1" --environment "Linux/Firefox" --scope "API Testing" --objectives "Performance" --linked_plan "TP-002" --outdir custom_reports/
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--file',
        default='data/sample_tc_execution.xlsx',
        help='Path to test execution file (.xlsx, .csv, .json, .xml) [default: data/sample_tc_execution.xlsx]'
    )
    parser.add_argument(
        '--project',
        help='Project name (e.g., "MyApplication")'
    )
    parser.add_argument(
        '--release',
        help='Release version (e.g., "R1.0.0", "v2.1.3")'
    )
    parser.add_argument(
        '--environment',
        help='Test environment (e.g., "QA Windows/Chrome", "Production")'
    )
    parser.add_argument(
        '--scope',
        help='Test scope (e.g., "Login, Checkout, Orders", "API Testing")'
    )
    parser.add_argument(
        '--objectives',
        help='Test objectives (e.g., "Functional Regression", "Performance")'
    )
    parser.add_argument(
        '--linked_plan',
        help='Linked test plan ID (e.g., "TP-001", "TEST-123")'
    )
    
    # Optional arguments
    parser.add_argument(
        '--outdir',
        default='reports',
        help='Output directory for reports [default: reports/]'
    )
    parser.add_argument(
        '--quality-gate',
        default='default',
        choices=['default', 'strict', 'lenient', 'custom'],
        help='Quality gate to use for release recommendation [default: default]'
    )
    parser.add_argument(
        '--list-quality-gates',
        action='store_true',
        help='List available quality gates and exit'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '--skip-crew',
        action='store_true',
        help='Skip AI crew processing (use only data analysis)'
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Override quality gate from environment variable if set
    if os.getenv('TSR_QUALITY_GATE'):
        args.quality_gate = os.getenv('TSR_QUALITY_GATE')
        logger = logging.getLogger(__name__)
        logger.info(f"Using quality gate from environment: {args.quality_gate}")
    
    # Setup logging
    verbose = args.verbose or os.getenv('CREWAI_VERBOSE', 'false').lower() == 'true'
    debug = args.debug or os.getenv('CREWAI_DEBUG', 'false').lower() == 'true'
    setup_logging(verbose, debug)
    
    logger = logging.getLogger(__name__)
    
    # Handle quality gates listing
    if args.list_quality_gates:
        evaluator = QualityGateEvaluator()
        gates = evaluator.get_available_quality_gates()
        print("\n📋 Available Quality Gates:")
        print("=" * 50)
        for gate_id, gate_name in gates.items():
            gate_info = evaluator.config_manager.get_quality_gate_info(gate_id)
            release_thresholds = gate_info.get('release_thresholds', {})
            additional_criteria = gate_info.get('additional_criteria', {})
            description = gate_info.get('description', 'No description available')
            print(f"\n🔹 {gate_id.upper()}: {gate_name}")
            print(f"   Description: {description}")
            print(f"   Release Thresholds:")
            print(f"     ✅ APPROVED:")
            approved = release_thresholds.get('approved', {})
            for key, value in approved.items():
                print(f"       • {key.replace('_', ' ').title()}: {value}")
            print(f"     ⚠️  CONDITIONAL:")
            conditional = release_thresholds.get('conditional', {})
            for key, value in conditional.items():
                print(f"       • {key.replace('_', ' ').title()}: {value}")
            print(f"     ❌ REJECTED:")
            print(f"       • Any values below conditional thresholds")
            print(f"   Additional Criteria (for reporting):")
            for key, value in additional_criteria.items():
                print(f"     • {key.replace('_', ' ').title()}: {value}")
        print("\n" + "=" * 50)
        print("Usage: --quality-gate <gate_id>")
        return 0
    
    # Validate required arguments for TSR generation
    required_args = ['project', 'release', 'environment', 'scope', 'objectives', 'linked_plan']
    missing_args = [arg for arg in required_args if not getattr(args, arg)]
    if missing_args:
        print(f"❌ Error: Missing required arguments: {', '.join(f'--{arg}' for arg in missing_args)}")
        print("Use --list-quality-gates to see available quality gates")
        return 1
    
    logger.info("Starting TSR generation process...")
    
    try:
        # Validate environment and inputs
        validate_environment()
        validate_file(args.file)
        
        # Create output directory
        output_dir = Path(args.outdir)
        output_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = output_dir / 'assets'
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🚀 Starting TSR generation for {args.project} {args.release}")
        print(f"📁 Input file: {args.file}")
        print(f"📁 Output directory: {output_dir}")
        
        # Step 1: Read and normalize data
        print("\n📊 Step 1: Reading and normalizing test execution data...")
        raw_data = read_execution_file(args.file)
        normalized_data = normalize_columns(raw_data)
        
        logger.info(f"Loaded {len(normalized_data)} test records")
        print(f"✅ Loaded {len(normalized_data)} test records")
        
        # Step 2: Optional AI crew processing
        crew_metadata = None
        if not args.skip_crew:
            print("\n🤖 Step 2: Running AI crew for data analysis...")
            try:
                crew = build_crew()
                if crew:
                    metadata = {
                        'project': args.project,
                        'release': args.release,
                        'environment': args.environment,
                        'scope': args.scope,
                        'objectives': args.objectives,
                        'linked_plan': args.linked_plan
                    }
                    crew_metadata = run_crew(args.file, metadata)
                    print("✅ AI crew processing completed")
                else:
                    print("⚠️  AI crew not available - continuing with data analysis only")
            except Exception as e:
                logger.warning(f"AI crew processing failed: {str(e)}")
                print(f"⚠️  AI crew processing failed: {str(e)}")
                print("   Continuing with data analysis only...")
        else:
            print("\n⏭️  Step 2: Skipping AI crew processing (--skip-crew)")
        
        # Step 3: Compute metrics
        print("\n📈 Step 3: Computing test metrics...")
        metrics = compute_metrics(normalized_data)
        print("✅ Metrics computed successfully")
        
        # Step 4: Generate charts
        print("\n📊 Step 4: Generating visualization charts...")
        chart_files = save_charts(metrics, str(assets_dir))
        print(f"✅ Generated {len(chart_files)} charts")
        
        # Step 5: Build context for templates
        print("\n📝 Step 5: Preparing report context...")
        report_id = generate_report_id(args.project, args.release)
        
        # Extract modules from data
        modules = sorted(normalized_data['Module'].unique().tolist()) if 'Module' in normalized_data.columns else []
        
        # Build comprehensive context for templates
        summary = metrics.get('summary', {})
        context = {
            # Report identification
            'report_id': report_id,
            'project': args.project,
            'release': args.release,
            'scope': args.scope,
            'objectives': args.objectives,
            'environment': args.environment,
            'linked_plan': args.linked_plan,
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            
            # Test summary data
            'total_tests': summary.get('total', 0),
            'executed_tests': summary.get('executed', 0),
            'passed_tests': summary.get('passed', 0),
            'failed_tests': summary.get('failed', 0),
            'blocked_tests': summary.get('blocked', 0),
            'skipped_tests': summary.get('skipped', 0),
            'pass_rate': summary.get('pass_pct', 0),
            
            # Modules covered
            'modules_covered': {
                module: {
                    'total': len(normalized_data[normalized_data['Module'] == module]),
                    'passed': len(normalized_data[(normalized_data['Module'] == module) & (normalized_data['Result'] == 'Pass')]),
                    'failed': len(normalized_data[(normalized_data['Module'] == module) & (normalized_data['Result'] == 'Fail')]),
                    'pass_rate': 0,  # Will be calculated in template
                    'status': 'N/A'
                }
                for module in modules
            },
            
            # Defect summary
            'defects': {
                'critical': {'open': metrics.get('defects_by_severity', {}).get('Critical', 0), 'closed': 0, 'deferred': 0},
                'major': {'open': metrics.get('defects_by_severity', {}).get('Major', 0), 'closed': 0, 'deferred': 0},
                'medium': {'open': metrics.get('defects_by_severity', {}).get('Medium', 0), 'closed': 0, 'deferred': 0},
                'minor': {'open': metrics.get('defects_by_severity', {}).get('Minor', 0), 'closed': 0, 'deferred': 0}
            },
            
            # Key bugs (now includes module information)
            'key_bugs': metrics.get('key_bugs', []),
            
            # Defect density (use enhanced data from metrics)
            'defect_density': metrics.get('density', {}),
            
            # Charts
            'charts': chart_files,
            
            # AI crew metadata (if available)
            'variances': crew_metadata.get('variances', []) if crew_metadata else [],
            'findings': crew_metadata.get('findings', {}) if crew_metadata else {},
            'exit_criteria': crew_metadata.get('exit_criteria', {}) if crew_metadata else {},
            
            # Additional template fields
            'report_version': '1.0',
            'hardware_info': 'Standard test hardware',
            'software_info': 'Test environment software stack',
            'os_version': 'N/A',
            'browser_version': 'N/A',
            'database_version': 'N/A',
            'test_data_info': 'Standard test data set',
            'configuration': 'Default configuration',
            'sign_off': {
                'test_lead': 'TBD',
                'test_engineer': 'TBD',
                'test_date': datetime.now().strftime("%Y-%m-%d"),
                'dev_lead': 'TBD',
                'dev_date': 'TBD',
                'product_lead': 'TBD',
                'product_date': 'TBD',
                'qa_lead': 'TBD',
                'qa_date': 'TBD'
            },
            'release_recommendation': 'APPROVED',  # Will be calculated below
            'release_comments': 'Based on test execution results and exit criteria evaluation',
            
            # Additional template fields
            'variances': crew_metadata.get('variances', []) if crew_metadata else [],
            'flaky_tests': metrics.get('flaky', [])
        }
        
        # Evaluate release recommendation using quality gates
        evaluator = QualityGateEvaluator()
        pass_rate = summary.get('pass_pct', 0)
        critical_defects = metrics.get('defects_by_severity', {}).get('Critical', 0)
        major_defects = metrics.get('defects_by_severity', {}).get('Major', 0)
        
        recommendation, evaluation_details = evaluator.evaluate_release_recommendation(
            pass_rate=pass_rate,
            critical_defects=critical_defects,
            major_defects=major_defects,
            quality_gate=args.quality_gate
        )
        
        # Update context with quality gate evaluation
        context['release_recommendation'] = recommendation
        context['quality_gate_evaluation'] = evaluation_details
        context['quality_gate_used'] = args.quality_gate
        
        # Generate dynamic lessons learned
        context['lessons_learned'] = generate_dynamic_lessons_learned(metrics, summary, context['modules_covered'])
        
        # Step 6: Render templates
        print("\n📄 Step 6: Rendering report templates...")
        base_name = f"TSR_{args.project}_{args.release}"
        md_path, html_path = render_report(
            context, 
            'templates', 
            str(output_dir), 
            base_name
        )
        print(f"✅ Templates rendered successfully")
        
        # Step 7: Attempt PDF generation
        pdf_path = None
        if html_path:
            pdf_path = str(output_dir / f"{base_name}.pdf")
            attempt_pdf_generation(html_path, pdf_path)
        
        # Step 8: Save metrics summary
        metrics_file = output_dir / f"{base_name}_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        
        # Prepare output files summary
        output_files = {
            'markdown': md_path,
            'html': html_path,
            'pdf': pdf_path if pdf_path and os.path.exists(pdf_path) else None,
            'metrics': str(metrics_file)
        }
        
        # Print summary
        print_summary(metrics, output_files)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"TSR generation failed: {str(e)}", exc_info=debug)
        print(f"\n❌ Error: {str(e)}")
        if debug:
            print(f"   Full traceback: {e.__class__.__name__}")
        return 1


if __name__ == "__main__":
    sys.exit(main())