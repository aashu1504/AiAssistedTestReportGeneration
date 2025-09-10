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
    """Attempt to generate PDF from HTML using WeasyPrint."""
    try:
        import weasyprint
        
        print("📄 Generating PDF report...")
        weasyprint.HTML(filename=html_path).write_pdf(pdf_path)
        print(f"✅ PDF report generated: {pdf_path}")
        return True
        
    except ImportError:
        print("⚠️  WeasyPrint not available - skipping PDF generation")
        print("   Install with: pip install weasyprint")
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
        required=True,
        help='Project name (e.g., "MyApplication")'
    )
    parser.add_argument(
        '--release',
        required=True,
        help='Release version (e.g., "R1.0.0", "v2.1.3")'
    )
    parser.add_argument(
        '--environment',
        required=True,
        help='Test environment (e.g., "QA Windows/Chrome", "Production")'
    )
    parser.add_argument(
        '--scope',
        required=True,
        help='Test scope (e.g., "Login, Checkout, Orders", "API Testing")'
    )
    parser.add_argument(
        '--objectives',
        required=True,
        help='Test objectives (e.g., "Functional Regression", "Performance")'
    )
    parser.add_argument(
        '--linked_plan',
        required=True,
        help='Linked test plan ID (e.g., "TP-001", "TEST-123")'
    )
    
    # Optional arguments
    parser.add_argument(
        '--outdir',
        default='reports',
        help='Output directory for reports [default: reports/]'
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
    
    # Setup logging
    verbose = args.verbose or os.getenv('CREWAI_VERBOSE', 'false').lower() == 'true'
    debug = args.debug or os.getenv('CREWAI_DEBUG', 'false').lower() == 'true'
    setup_logging(verbose, debug)
    
    logger = logging.getLogger(__name__)
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
            
            # Key bugs
            'key_bugs': [
                {'id': bug_id, 'severity': 'Medium', 'priority': 'Medium', 'description': f'Bug {bug_id}'}
                for bug_id in metrics.get('key_bugs', [])
            ],
            
            # Defect density (convert simple counts to complex objects for template)
            'defect_density': {
                module: {
                    'total': count,
                    'density': count / len(normalized_data[normalized_data['Module'] == module]) if len(normalized_data[normalized_data['Module'] == module]) > 0 else 0,
                    'critical': 0,  # Would need severity breakdown
                    'major': 0,
                    'medium': count,  # Assume all are medium for now
                    'minor': 0
                }
                for module, count in metrics.get('density', {}).items()
            },
            
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
            'release_recommendation': 'APPROVED' if summary.get('pass_pct', 0) >= 90 else 'CONDITIONAL' if summary.get('pass_pct', 0) >= 75 else 'REJECTED',
            'release_comments': 'Based on test execution results and exit criteria evaluation',
            
            # Additional template fields
            'variances': crew_metadata.get('variances', []) if crew_metadata else [],
            'lessons_learned': {
                'positive': ['Test execution completed successfully', 'All critical modules tested'],
                'negative': ['Some test failures identified', 'Defect density needs attention'],
                'improvements': ['Improve test data quality', 'Enhance test coverage']
            },
            'flaky_tests': metrics.get('flaky', [])
        }
        
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