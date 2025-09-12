"""Tools for TSR generation - file processing, metrics computation, and report rendering."""

import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Canonical column mappings (case-insensitive)
CANONICAL_COLUMNS = {
    'module': 'Module',
    'testcaseid': 'TestCaseID', 
    'test_case_id': 'TestCaseID',
    'testcase': 'TestCaseID',
    'tc_id': 'TestCaseID',
    'tcid': 'TestCaseID',
    'description': 'Description',
    'desc': 'Description',
    'run': 'Run',
    'result': 'Result',
    'status': 'Result',
    'outcome': 'Result',
    'bugid': 'BugID',
    'bug_id': 'BugID',
    'defect_id': 'BugID',
    'priority': 'Priority',
    'severity': 'Severity',
    'duration': 'Duration',
    'tester': 'Tester',
    'executed_by': 'Tester'
}

# Standard result mappings
RESULT_MAPPINGS = {
    'pass': 'Pass',
    'passed': 'Pass',
    'p': 'Pass',
    'fail': 'Fail',
    'failed': 'Fail',
    'f': 'Fail',
    'blocked': 'Blocked',
    'block': 'Blocked',
    'b': 'Blocked',
    'skip': 'Skipped',
    'skipped': 'Skipped',
    's': 'Skipped',
    'not executed': 'Not Executed',
    'not_executed': 'Not Executed',
    'pending': 'Not Executed',
    '': 'Not Executed'
}

# Severity mappings
SEVERITY_MAPPINGS = {
    'critical': 'Critical',
    'crit': 'Critical',
    '1': 'Critical',
    'major': 'Major',
    'maj': 'Major',
    '2': 'Major',
    'medium': 'Medium',
    'med': 'Medium',
    '3': 'Medium',
    'minor': 'Minor',
    'min': 'Minor',
    '4': 'Minor'
}

# Priority mappings
PRIORITY_MAPPINGS = {
    'highest': 'Highest',
    'high': 'High',
    'medium': 'Medium',
    'low': 'Low',
    '1': 'Highest',
    '2': 'High',
    '3': 'Medium',
    '4': 'Low'
}


def read_execution_file(path: str) -> pd.DataFrame:
    """
    Read test execution data from various file formats.
    
    Supports .xlsx, .csv, .json, and TestNG-style .xml files.
    
    Args:
        path: Path to the execution file
        
    Returns:
        DataFrame with raw execution data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported or data is invalid
    """
    logger.info(f"Reading execution file: {path}")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    file_ext = Path(path).suffix.lower()
    
    try:
        if file_ext == '.xlsx':
            logger.info("Reading Excel file with openpyxl engine")
            df = pd.read_excel(path, engine='openpyxl')
            
        elif file_ext == '.csv':
            logger.info("Reading CSV file")
            df = pd.read_csv(path)
            
        elif file_ext == '.json':
            logger.info("Reading JSON file")
            with open(path, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            
        elif file_ext == '.xml':
            logger.info("Reading TestNG XML file")
            df = _parse_testng_xml(path)
            
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
            
        logger.info(f"Successfully loaded {len(df)} rows from {path}")
        return df
        
    except Exception as e:
        logger.error(f"Error reading file {path}: {str(e)}")
        raise ValueError(f"Failed to read file {path}: {str(e)}")


def _parse_testng_xml(path: str) -> pd.DataFrame:
    """
    Parse TestNG XML file and convert to DataFrame.
    
    Args:
        path: Path to TestNG XML file
        
    Returns:
        DataFrame with test execution data
    """
    logger.info("Parsing TestNG XML file")
    
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        
        test_data = []
        
        # Find all test methods
        for test_method in root.findall('.//test-method'):
            data = {
                'TestCaseID': test_method.get('name', ''),
                'Description': test_method.get('description', ''),
                'Result': test_method.get('status', 'Not Executed'),
                'Duration': test_method.get('duration-ms', '0'),
                'Module': test_method.get('class', '').split('.')[-1] if test_method.get('class') else '',
                'Run': '1',
                'Tester': 'TestNG',
                'BugID': '',
                'Priority': '',
                'Severity': ''
            }
            
            # Look for parameters
            params = test_method.find('params')
            if params is not None:
                for param in params.findall('param'):
                    name = param.get('name', '').lower()
                    value = param.get('value', '')
                    
                    if name in ['module', 'class']:
                        data['Module'] = value
                    elif name in ['tester', 'executed_by']:
                        data['Tester'] = value
                    elif name in ['bugid', 'bug_id']:
                        data['BugID'] = value
                    elif name == 'priority':
                        data['Priority'] = value
                    elif name == 'severity':
                        data['Severity'] = value
            
            test_data.append(data)
        
        df = pd.DataFrame(test_data)
        logger.info(f"Parsed {len(df)} test methods from TestNG XML")
        return df
        
    except ET.ParseError as e:
        logger.error(f"XML parsing error: {str(e)}")
        raise ValueError(f"Invalid XML file: {str(e)}")
    except Exception as e:
        logger.error(f"Error parsing TestNG XML: {str(e)}")
        raise ValueError(f"Failed to parse TestNG XML: {str(e)}")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names and standardize data values.
    
    Maps common column name variants to canonical names and fills defaults.
    
    Args:
        df: Input DataFrame with raw execution data
        
    Returns:
        Cleaned DataFrame with normalized columns and standardized values
    """
    logger.info("Normalizing columns and standardizing data")
    
    if df.empty:
        logger.warning("Empty DataFrame provided")
        # Still need to add canonical columns for empty DataFrame
        df_clean = df.copy()
    else:
        # Create a copy to avoid modifying original
        df_clean = df.copy()
    
    # Normalize column names (case-insensitive)
    column_mapping = {}
    for col in df_clean.columns:
        col_lower = col.lower().strip()
        if col_lower in CANONICAL_COLUMNS:
            column_mapping[col] = CANONICAL_COLUMNS[col_lower]
            logger.debug(f"Mapped column '{col}' to '{CANONICAL_COLUMNS[col_lower]}'")
    
    df_clean = df_clean.rename(columns=column_mapping)
    
    # Fill missing columns with defaults
    for canonical_col in CANONICAL_COLUMNS.values():
        if canonical_col not in df_clean.columns:
            df_clean[canonical_col] = ''
            logger.debug(f"Added missing column: {canonical_col}")
    
    # Standardize Run column (default to 1 if missing or empty)
    if 'Run' in df_clean.columns:
        df_clean['Run'] = df_clean['Run'].fillna(1)
        df_clean['Run'] = pd.to_numeric(df_clean['Run'], errors='coerce').fillna(1)
        logger.debug("Standardized Run column")
    
    # Standardize Result column
    if 'Result' in df_clean.columns:
        # Fill empty results with 'Not Executed'
        df_clean['Result'] = df_clean['Result'].fillna('Not Executed')
        
        # Map to standard result values
        df_clean['Result'] = df_clean['Result'].astype(str).str.lower().str.strip()
        df_clean['Result'] = df_clean['Result'].map(RESULT_MAPPINGS).fillna('Not Executed')
        logger.debug("Standardized Result column")
    
    # Standardize Severity column
    if 'Severity' in df_clean.columns:
        df_clean['Severity'] = df_clean['Severity'].astype(str).str.lower().str.strip()
        df_clean['Severity'] = df_clean['Severity'].map(SEVERITY_MAPPINGS).fillna('')
        logger.debug("Standardized Severity column")
    
    # Standardize Priority column
    if 'Priority' in df_clean.columns:
        df_clean['Priority'] = df_clean['Priority'].astype(str).str.lower().str.strip()
        df_clean['Priority'] = df_clean['Priority'].map(PRIORITY_MAPPINGS).fillna('')
        logger.debug("Standardized Priority column")
    
    # Clean up string columns
    string_columns = ['TestCaseID', 'Description', 'Module', 'Tester', 'BugID']
    for col in string_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()
    
    logger.info(f"Normalized {len(df_clean)} rows with {len(df_clean.columns)} columns")
    return df_clean


def compute_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute comprehensive test execution metrics.
    
    Args:
        df: Normalized DataFrame with test execution data
        
    Returns:
        Dictionary containing various metrics and analysis results
    """
    logger.info("Computing test execution metrics")
    
    if df.empty:
        logger.warning("Empty DataFrame provided for metrics computation")
        return {
            'summary': {'total': 0, 'executed': 0, 'passed': 0, 'failed': 0, 
                       'blocked': 0, 'skipped': 0, 'pass_pct': 0.0},
            'fail_by_module': {},
            'defects_by_severity': {'Critical': 0, 'Major': 0, 'Medium': 0, 'Minor': 0},
            'defects_by_priority': {'Highest': 0, 'High': 0, 'Medium': 0, 'Low': 0},
            'density': {},
            'flaky': [],
            'key_bugs': []
        }
    
    metrics = {}
    
    # Basic summary metrics
    total_tests = len(df)
    executed_tests = len(df[df['Result'].isin(['Pass', 'Fail', 'Blocked'])])
    passed_tests = len(df[df['Result'] == 'Pass'])
    failed_tests = len(df[df['Result'] == 'Fail'])
    blocked_tests = len(df[df['Result'] == 'Blocked'])
    skipped_tests = len(df[df['Result'] == 'Skipped'])
    pass_pct = (passed_tests / executed_tests * 100) if executed_tests > 0 else 0.0
    
    metrics['summary'] = {
        'total': total_tests,
        'executed': executed_tests,
        'passed': passed_tests,
        'failed': failed_tests,
        'blocked': blocked_tests,
        'skipped': skipped_tests,
        'pass_pct': round(pass_pct, 2)
    }
    
    logger.info(f"Summary: {executed_tests}/{total_tests} executed, {pass_pct:.1f}% pass rate")
    
    # Failures by module
    if 'Module' in df.columns and 'Result' in df.columns:
        fail_by_module = df[df['Result'] == 'Fail']['Module'].value_counts().to_dict()
        metrics['fail_by_module'] = fail_by_module
        logger.debug(f"Failures by module: {fail_by_module}")
    
    # Defects by severity
    if 'Severity' in df.columns and 'BugID' in df.columns:
        # Only count rows with both Severity and BugID
        defect_df = df[(df['Severity'].notna()) & (df['Severity'] != '') & 
                      (df['BugID'].notna()) & (df['BugID'] != '')]
        defects_by_severity = defect_df['Severity'].value_counts().to_dict()
        # Ensure all severity levels are present
        for severity in ['Critical', 'Major', 'Medium', 'Minor']:
            if severity not in defects_by_severity:
                defects_by_severity[severity] = 0
        metrics['defects_by_severity'] = defects_by_severity
        logger.debug(f"Defects by severity: {defects_by_severity}")
    
    # Defects by priority
    if 'Priority' in df.columns and 'BugID' in df.columns:
        # Only count rows with both Priority and BugID
        defect_df = df[(df['Priority'].notna()) & (df['Priority'] != '') & 
                      (df['BugID'].notna()) & (df['BugID'] != '')]
        defects_by_priority = defect_df['Priority'].value_counts().to_dict()
        # Ensure all priority levels are present
        for priority in ['Highest', 'High', 'Medium', 'Low']:
            if priority not in defects_by_priority:
                defects_by_priority[priority] = 0
        metrics['defects_by_priority'] = defects_by_priority
        logger.debug(f"Defects by priority: {defects_by_priority}")
    
    # Priority-to-severity fallback: If no severity data but priority data exists, map priority to severity
    if ('Severity' not in df.columns or df['Severity'].isna().all() or (df['Severity'] == '').all()) and \
       ('Priority' in df.columns and not df['Priority'].isna().all() and (df['Priority'] != '').any()):
        
        logger.info("No severity data found, mapping priority to severity for quality gates")
        
        # Create priority to severity mapping
        priority_to_severity = {
            'Highest': 'Critical',
            'High': 'Major', 
            'Medium': 'Medium',
            'Low': 'Minor'
        }
        
        # Map priority values to severity
        df['Severity'] = df['Priority'].map(priority_to_severity).fillna('')
        
        # Recompute defects by severity using the mapped values
        defect_df = df[(df['Severity'].notna()) & (df['Severity'] != '') & 
                      (df['BugID'].notna()) & (df['BugID'] != '')]
        defects_by_severity = defect_df['Severity'].value_counts().to_dict()
        
        # Ensure all severity levels are present
        for severity in ['Critical', 'Major', 'Medium', 'Minor']:
            if severity not in defects_by_severity:
                defects_by_severity[severity] = 0
        metrics['defects_by_severity'] = defects_by_severity
        logger.debug(f"Defects by severity (mapped from priority): {defects_by_severity}")
    
    # Defect density by module with enhanced analysis
    if 'Module' in df.columns and 'BugID' in df.columns:
        defect_density = {}
        for module in df['Module'].unique():
            if pd.notna(module) and module != '':
                module_data = df[df['Module'] == module]
                module_total_tests = len(module_data)
                module_bugs = module_data[(module_data['BugID'].notna()) & (module_data['BugID'] != '')]['BugID'].nunique()
                
                # Calculate defect density ratio (defects per test)
                density_ratio = module_bugs / module_total_tests if module_total_tests > 0 else 0
                
                # Get severity breakdown for this module
                module_defects = module_data[(module_data['BugID'].notna()) & (module_data['BugID'] != '')]
                severity_breakdown = {}
                if 'Severity' in module_defects.columns:
                    severity_counts = module_defects['Severity'].value_counts().to_dict()
                    for severity in ['Critical', 'Major', 'Medium', 'Minor']:
                        severity_breakdown[severity.lower()] = severity_counts.get(severity, 0)
                else:
                    # If no severity, use priority mapping
                    if 'Priority' in module_defects.columns:
                        priority_counts = module_defects['Priority'].value_counts().to_dict()
                        severity_breakdown = {
                            'critical': priority_counts.get('Highest', 0),
                            'major': priority_counts.get('High', 0),
                            'medium': priority_counts.get('Medium', 0),
                            'minor': priority_counts.get('Low', 0)
                        }
                    else:
                        severity_breakdown = {'critical': 0, 'major': 0, 'medium': module_bugs, 'minor': 0}
                
                defect_density[module] = {
                    'total': module_bugs,
                    'density': round(density_ratio, 3),
                    'density_percentage': round(density_ratio * 100, 1),
                    'total_tests': module_total_tests,
                    'critical': severity_breakdown.get('critical', 0),
                    'major': severity_breakdown.get('major', 0),
                    'medium': severity_breakdown.get('medium', 0),
                    'minor': severity_breakdown.get('minor', 0),
                    'risk_level': 'High' if density_ratio > 0.3 else 'Medium' if density_ratio > 0.1 else 'Low'
                }
        metrics['density'] = defect_density
        logger.debug(f"Enhanced defect density by module: {defect_density}")
    
    # Identify flaky tests (tests with both pass and fail results)
    if 'TestCaseID' in df.columns and 'Result' in df.columns:
        flaky_tests = []
        for test_id in df['TestCaseID'].unique():
            if pd.notna(test_id) and test_id != '':
                test_results = df[df['TestCaseID'] == test_id]['Result'].unique()
                if 'Pass' in test_results and 'Fail' in test_results:
                    flaky_tests.append(test_id)
        metrics['flaky'] = flaky_tests
        logger.debug(f"Found {len(flaky_tests)} flaky tests")
    
    # Extract unique bug IDs with module information
    if 'BugID' in df.columns and 'Module' in df.columns:
        bug_df = df[df['BugID'].notna() & (df['BugID'] != '') & 
                   df['Module'].notna() & (df['Module'] != '')]
        key_bugs = []
        for _, row in bug_df.iterrows():
            bug_info = {
                'id': row['BugID'],
                'module': row['Module'],
                'severity': row.get('Severity', 'Medium') if pd.notna(row.get('Severity')) else 'Medium',
                'priority': row.get('Priority', 'Medium') if pd.notna(row.get('Priority')) else 'Medium',
                'status': 'Open',
                'assigned_to': row.get('Tester', 'N/A') if pd.notna(row.get('Tester')) else 'N/A'
            }
            # Only add if not already present (avoid duplicates)
            if not any(bug['id'] == bug_info['id'] for bug in key_bugs):
                key_bugs.append(bug_info)
        metrics['key_bugs'] = key_bugs
        logger.debug(f"Found {len(key_bugs)} unique bug IDs with module info")
    elif 'BugID' in df.columns:
        # Fallback to simple bug IDs if no module info
        key_bugs = df[df['BugID'].notna() & (df['BugID'] != '')]['BugID'].unique().tolist()
        metrics['key_bugs'] = [{'id': bug_id, 'module': 'N/A', 'severity': 'Medium', 'priority': 'Medium', 'status': 'Open', 'assigned_to': 'N/A'} for bug_id in key_bugs]
        logger.debug(f"Found {len(key_bugs)} unique bug IDs (no module info)")
    
    logger.info("Metrics computation completed")
    return metrics


def save_charts(metrics: Dict[str, Any], out_dir: str) -> Dict[str, str]:
    """
    Generate and save charts based on computed metrics.
    
    Args:
        metrics: Dictionary containing computed metrics
        out_dir: Output directory for chart files
        
    Returns:
        Dictionary mapping chart keys to relative filenames
    """
    logger.info(f"Generating charts in directory: {out_dir}")
    
    # Create output directory if it doesn't exist
    os.makedirs(out_dir, exist_ok=True)
    
    chart_files = {}
    
    try:
        # Set up matplotlib style with modern, professional look
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 12
        plt.rcParams['axes.labelsize'] = 13
        plt.rcParams['axes.titlesize'] = 16
        plt.rcParams['xtick.labelsize'] = 11
        plt.rcParams['ytick.labelsize'] = 11
        plt.rcParams['legend.fontsize'] = 11
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['axes.edgecolor'] = '#E0E0E0'
        plt.rcParams['axes.linewidth'] = 1.2
        plt.rcParams['grid.alpha'] = 0.3
        
        # 1. Pass/Fail Bar Chart
        if 'summary' in metrics:
            summary = metrics['summary']
            fig, ax = plt.subplots(figsize=(12, 8))
            
            categories = ['Passed', 'Failed', 'Blocked', 'Skipped']
            values = [summary['passed'], summary['failed'], 
                     summary['blocked'], summary['skipped']]
            
            # Modern, professional color palette
            colors = ['#2ECC71', '#E74C3C', '#9B59B6', '#F39C12']
            
            # Create bars with better styling
            bars = ax.bar(categories, values, color=colors, alpha=0.8, 
                         edgecolor='white', linewidth=2, width=0.6)
            
            # Customize the chart
            ax.set_title('Test Results Summary', fontsize=18, fontweight='bold', 
                        color='#2C3E50', pad=20)
            ax.set_ylabel('Number of Tests', fontsize=14, fontweight='bold', color='#34495E')
            ax.set_xlabel('Test Status', fontsize=14, fontweight='bold', color='#34495E')
            
            # Style the axes
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#BDC3C7')
            ax.spines['bottom'].set_color('#BDC3C7')
            ax.tick_params(colors='#34495E', labelsize=12)
            
            # Add value labels on bars with better positioning
            for bar, value in zip(bars, values):
                if value > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2, height + 0.05,
                           f'{int(value)}', ha='center', va='bottom', 
                           fontweight='bold', fontsize=13, color='#2C3E50')
            
            # Add percentage labels
            total = sum(values)
            if total > 0:
                for bar, value in zip(bars, values):
                    if value > 0:
                        height = bar.get_height()
                        percentage = (value / total) * 100
                        ax.text(bar.get_x() + bar.get_width()/2, height/2,
                               f'{percentage:.1f}%', ha='center', va='center', 
                               fontweight='bold', fontsize=11, color='white')
            
            plt.tight_layout()
            chart_path = os.path.join(out_dir, 'pass_fail.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            chart_files['pass_fail'] = 'assets/pass_fail.png'
            logger.info("Generated pass/fail chart")
        
        # 2. Failures by Module
        if 'fail_by_module' in metrics and metrics['fail_by_module']:
            fig, ax = plt.subplots(figsize=(14, 8))
            
            modules = list(metrics['fail_by_module'].keys())
            failures = list(metrics['fail_by_module'].values())
            
            # Create gradient colors for modules
            colors = plt.cm.Reds(np.linspace(0.4, 0.9, len(modules)))
            
            bars = ax.bar(modules, failures, color=colors, alpha=0.8, 
                         edgecolor='white', linewidth=2, width=0.6)
            
            ax.set_title('Test Failures by Module', fontsize=18, fontweight='bold', 
                        color='#2C3E50', pad=20)
            ax.set_ylabel('Number of Failures', fontsize=14, fontweight='bold', color='#34495E')
            ax.set_xlabel('Module', fontsize=14, fontweight='bold', color='#34495E')
            
            # Style the axes
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#BDC3C7')
            ax.spines['bottom'].set_color('#BDC3C7')
            ax.tick_params(colors='#34495E', labelsize=12)
            
            # Rotate x-axis labels if needed
            if len(modules) > 4:
                plt.xticks(rotation=45, ha='right')
            
            # Add value labels on bars
            for bar, value in zip(bars, failures):
                if value > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2, height + 0.05,
                           f'{int(value)}', ha='center', va='bottom', 
                           fontweight='bold', fontsize=13, color='#2C3E50')
            
            plt.tight_layout()
            chart_path = os.path.join(out_dir, 'fail_by_module.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            chart_files['fail_by_module'] = 'assets/fail_by_module.png'
            logger.info("Generated failures by module chart")
        
        # 3. Defects by Severity
        if 'defects_by_severity' in metrics and any(metrics['defects_by_severity'].values()):
            fig, ax = plt.subplots(figsize=(12, 8))
            
            severities = ['Critical', 'Major', 'Medium', 'Minor']
            counts = [metrics['defects_by_severity'].get(s, 0) for s in severities]
            
            # Professional severity color palette
            colors = ['#E74C3C', '#F39C12', '#F1C40F', '#95A5A6']
            
            bars = ax.bar(severities, counts, color=colors, alpha=0.8, 
                         edgecolor='white', linewidth=2, width=0.6)
            
            ax.set_title('Defects by Severity', fontsize=18, fontweight='bold', 
                        color='#2C3E50', pad=20)
            ax.set_ylabel('Number of Defects', fontsize=14, fontweight='bold', color='#34495E')
            ax.set_xlabel('Severity Level', fontsize=14, fontweight='bold', color='#34495E')
            
            # Style the axes
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#BDC3C7')
            ax.spines['bottom'].set_color('#BDC3C7')
            ax.tick_params(colors='#34495E', labelsize=12)
            
            # Add value labels on bars
            for bar, value in zip(bars, counts):
                if value > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2, height + 0.05,
                           f'{int(value)}', ha='center', va='bottom', 
                           fontweight='bold', fontsize=13, color='#2C3E50')
            
            # Add percentage labels
            total = sum(counts)
            if total > 0:
                for bar, value in zip(bars, counts):
                    if value > 0:
                        height = bar.get_height()
                        percentage = (value / total) * 100
                        ax.text(bar.get_x() + bar.get_width()/2, height/2,
                               f'{percentage:.1f}%', ha='center', va='center', 
                               fontweight='bold', fontsize=11, color='white')
            
            plt.tight_layout()
            chart_path = os.path.join(out_dir, 'defects_by_severity.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            chart_files['defects_by_severity'] = 'assets/defects_by_severity.png'
            logger.info("Generated defects by severity chart")
        
        # 4. Defects by Priority
        if 'defects_by_priority' in metrics and any(metrics['defects_by_priority'].values()):
            fig, ax = plt.subplots(figsize=(12, 8))
            
            priorities = ['Highest', 'High', 'Medium', 'Low']
            counts = [metrics['defects_by_priority'].get(p, 0) for p in priorities]
            
            # Professional priority color palette
            colors = ['#8E44AD', '#9B59B6', '#3498DB', '#85C1E9']
            
            bars = ax.bar(priorities, counts, color=colors, alpha=0.8, 
                         edgecolor='white', linewidth=2, width=0.6)
            
            ax.set_title('Defects by Priority', fontsize=18, fontweight='bold', 
                        color='#2C3E50', pad=20)
            ax.set_ylabel('Number of Defects', fontsize=14, fontweight='bold', color='#34495E')
            ax.set_xlabel('Priority Level', fontsize=14, fontweight='bold', color='#34495E')
            
            # Style the axes
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#BDC3C7')
            ax.spines['bottom'].set_color('#BDC3C7')
            ax.tick_params(colors='#34495E', labelsize=12)
            
            # Add value labels on bars
            for bar, value in zip(bars, counts):
                if value > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2, height + 0.05,
                           f'{int(value)}', ha='center', va='bottom', 
                           fontweight='bold', fontsize=13, color='#2C3E50')
            
            # Add percentage labels
            total = sum(counts)
            if total > 0:
                for bar, value in zip(bars, counts):
                    if value > 0:
                        height = bar.get_height()
                        percentage = (value / total) * 100
                        ax.text(bar.get_x() + bar.get_width()/2, height/2,
                               f'{percentage:.1f}%', ha='center', va='center', 
                               fontweight='bold', fontsize=11, color='white')
            
            plt.tight_layout()
            chart_path = os.path.join(out_dir, 'defects_by_priority.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            chart_files['defects_by_priority'] = 'assets/defects_by_priority.png'
            logger.info("Generated defects by priority chart")
        
        logger.info(f"Generated {len(chart_files)} charts successfully")
        return chart_files
        
    except Exception as e:
        logger.error(f"Error generating charts: {str(e)}")
        raise ValueError(f"Failed to generate charts: {str(e)}")


def render_report(context: Dict[str, Any], template_dir: str, out_dir: str, base_name: str) -> Tuple[str, str]:
    """
    Render TSR reports using Jinja2 templates.
    
    Args:
        context: Dictionary containing data for template rendering
        template_dir: Directory containing Jinja2 templates
        out_dir: Output directory for generated reports
        base_name: Base name for output files (without extension)
        
    Returns:
        Tuple of (markdown_path, html_path) for generated files
        
    Raises:
        FileNotFoundError: If templates are not found
        ValueError: If rendering fails
    """
    logger.info(f"Rendering TSR reports with base name: {base_name}")
    
    # Create output directory if it doesn't exist
    os.makedirs(out_dir, exist_ok=True)
    
    try:
        # Set up Jinja2 environment
        env = Environment(loader=FileSystemLoader(template_dir))
        
        # Render Markdown report
        try:
            md_template = env.get_template('tsr_md.j2')
            md_content = md_template.render(**context)
            md_path = os.path.join(out_dir, f"{base_name}.md")
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            logger.info(f"Generated Markdown report: {md_path}")
            
        except TemplateNotFound:
            logger.error("Markdown template not found: tsr_md.j2")
            raise FileNotFoundError("Markdown template tsr_md.j2 not found")
        
        # Render HTML report
        try:
            html_template = env.get_template('tsr_html.j2')
            html_content = html_template.render(**context)
            html_path = os.path.join(out_dir, f"{base_name}.html")
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Generated HTML report: {html_path}")
            
        except TemplateNotFound:
            logger.error("HTML template not found: tsr_html.j2")
            raise FileNotFoundError("HTML template tsr_html.j2 not found")
        
        logger.info("Report rendering completed successfully")
        return md_path, html_path
        
    except Exception as e:
        logger.error(f"Error rendering reports: {str(e)}")
        raise ValueError(f"Failed to render reports: {str(e)}")


def process_execution_file(file_path: str, output_dir: str = 'reports') -> Dict[str, Any]:
    """
    Complete pipeline to process execution file and generate TSR.
    
    Args:
        file_path: Path to execution file
        output_dir: Output directory for reports and charts
        
    Returns:
        Dictionary with processing results and file paths
    """
    logger.info(f"Starting complete TSR processing pipeline for: {file_path}")
    
    try:
        # Step 1: Read execution file
        df = read_execution_file(file_path)
        
        # Step 2: Normalize columns
        df_clean = normalize_columns(df)
        
        # Step 3: Compute metrics
        metrics = compute_metrics(df_clean)
        
        # Step 4: Generate charts
        charts_dir = os.path.join(output_dir, 'assets')
        chart_files = save_charts(metrics, charts_dir)
        
        # Step 5: Prepare context for templates
        context = {
            'project': 'Sample Project',
            'release': '1.0.0',
            'environment': 'Test Environment',
            'scope': 'Full Test Suite',
            'objectives': 'Quality Assurance',
            'linked_plan': 'TP-001',
            'total_tests': metrics['summary']['total'],
            'executed_tests': metrics['summary']['executed'],
            'passed_tests': metrics['summary']['passed'],
            'failed_tests': metrics['summary']['failed'],
            'blocked_tests': metrics['summary']['blocked'],
            'skipped_tests': metrics['summary']['skipped'],
            'pass_rate': metrics['summary']['pass_pct'],
            'modules_covered': {module: {'total': 0, 'passed': 0, 'failed': 0, 
                                       'pass_rate': 0, 'status': 'N/A'} 
                              for module in df_clean['Module'].unique() if pd.notna(module)},
            'defects': {
                'critical': {'open': metrics['defects_by_severity'].get('Critical', 0), 
                           'closed': 0, 'deferred': 0},
                'major': {'open': metrics['defects_by_severity'].get('Major', 0), 
                         'closed': 0, 'deferred': 0},
                'medium': {'open': metrics['defects_by_severity'].get('Medium', 0), 
                          'closed': 0, 'deferred': 0},
                'minor': {'open': metrics['defects_by_severity'].get('Minor', 0), 
                         'closed': 0, 'deferred': 0}
            },
            'key_bugs': [{'id': bug_id, 'severity': 'Medium', 'priority': 'Medium', 
                         'status': 'Open', 'description': f'Bug {bug_id}', 'module': 'Unknown'}
                        for bug_id in metrics['key_bugs']],
            'defect_density': metrics['density'],
            'chart_files': chart_files
        }
        
        # Step 6: Render reports
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        base_name = f"TSR_{context['project']}_{context['release']}"
        md_path, html_path = render_report(context, template_dir, output_dir, base_name)
        
        result = {
            'success': True,
            'dataframe': df_clean,
            'metrics': metrics,
            'charts': chart_files,
            'markdown_path': md_path,
            'html_path': html_path
        }
        
        logger.info("TSR processing pipeline completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"TSR processing pipeline failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'dataframe': None,
            'metrics': None,
            'charts': {},
            'markdown_path': None,
            'html_path': None
        }