#!/usr/bin/env python3
"""
Create Excel test file with priority-only data for testing priority-to-severity mapping.
"""

import pandas as pd
import sys
import os

# Add src to path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def create_excel_test_file():
    """Create Excel test file with priority-only data."""
    
    # Test data with only priority (no severity column)
    data = {
        'TestCaseID': ['TC001', 'TC002', 'TC003', 'TC004', 'TC005', 'TC006', 'TC007', 'TC008', 'TC009', 'TC010'],
        'Description': [
            'Login functionality test',
            'User registration test', 
            'Password reset test',
            'Profile update test',
            'Profile delete test',
            'Search functionality test',
            'Filter results test',
            'Export data test',
            'Generate report test',
            'Email notification test'
        ],
        'Module': [
            'Authentication',
            'Authentication', 
            'Authentication',
            'User Management',
            'User Management',
            'Search',
            'Search',
            'Reports',
            'Reports',
            'Notifications'
        ],
        'Result': ['Pass', 'Fail', 'Fail', 'Pass', 'Fail', 'Pass', 'Fail', 'Pass', 'Fail', 'Pass'],
        'BugID': ['', 'BUG-001', 'BUG-002', '', 'BUG-003', '', 'BUG-004', '', 'BUG-005', ''],
        'Priority': ['', 'High', 'Highest', '', 'Medium', '', 'High', '', 'Low', ''],
        'Tester': ['Tester1', 'Tester1', 'Tester2', 'Tester1', 'Tester2', 'Tester1', 'Tester2', 'Tester1', 'Tester2', 'Tester1'],
        'Duration': [30, 45, 25, 20, 35, 15, 40, 50, 60, 25]
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save as Excel file
    output_file = 'data/test_priority_only_report.xlsx'
    df.to_excel(output_file, index=False, sheet_name='TestExecution')
    
    print(f"✅ Created Excel test file: {output_file}")
    print(f"📊 Data shape: {df.shape}")
    print(f"📋 Columns: {list(df.columns)}")
    print(f"🐛 Defects by priority:")
    priority_counts = df[df['BugID'] != '']['Priority'].value_counts()
    for priority, count in priority_counts.items():
        print(f"   {priority}: {count}")
    
    return output_file

if __name__ == "__main__":
    create_excel_test_file()