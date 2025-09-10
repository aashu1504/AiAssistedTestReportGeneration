"""
Pytest tests for src.tools module.

Tests cover data reading, normalization, and metrics computation functionality.
All tests are designed to be fast, environment-independent, and focused.
"""

import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Import the functions to test
from src.tools import (
    read_execution_file,
    normalize_columns,
    compute_metrics,
    save_charts,
    render_report
)


class TestReadExecutionFile:
    """Test cases for read_execution_file function."""
    
    def test_read_xlsx(self):
        """Test reading Excel file returns DataFrame."""
        # Use the sample file in data directory
        file_path = "data/tc_execution_report.xlsx"
        
        # Ensure file exists
        assert os.path.exists(file_path), f"Test file {file_path} not found"
        
        # Read the file
        df = read_execution_file(file_path)
        
        # Assertions
        assert isinstance(df, pd.DataFrame), "Should return a pandas DataFrame"
        assert not df.empty, "DataFrame should not be empty"
        assert len(df) > 0, "Should have at least one row"
        
        # Check that we have some expected columns (after normalization)
        expected_columns = ['Module', 'TestCaseID', 'Description', 'Result']
        for col in expected_columns:
            assert col in df.columns, f"Expected column '{col}' not found in DataFrame"
    
    def test_read_csv(self):
        """Test reading CSV file returns DataFrame."""
        # Create a temporary CSV file
        test_data = {
            'Module': ['Login', 'Checkout'],
            'TestCaseID': ['TC001', 'TC002'],
            'Description': ['Test login', 'Test checkout'],
            'Result': ['Pass', 'Fail']
        }
        df_expected = pd.DataFrame(test_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df_expected.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            df = read_execution_file(temp_file)
            assert isinstance(df, pd.DataFrame), "Should return a pandas DataFrame"
            assert not df.empty, "DataFrame should not be empty"
            assert len(df) == 2, "Should have 2 rows"
        finally:
            os.unlink(temp_file)


class TestNormalizeColumns:
    """Test cases for normalize_columns function."""
    
    def test_normalize_columns_basic(self):
        """Test basic column name normalization."""
        # Create test data with varied headers
        test_data = {
            'tcid': ['TC001', 'TC002', 'TC003'],
            'Status': ['Pass', 'Fail', 'Pass'],
            'Priority': ['High', 'Medium', 'Low'],
            'Module': ['Login', 'Checkout', 'Profile'],
            'Description': ['Test 1', 'Test 2', 'Test 3']
        }
        df = pd.DataFrame(test_data)
        
        # Normalize columns
        normalized_df = normalize_columns(df)
        
        # Assertions
        assert isinstance(normalized_df, pd.DataFrame), "Should return a pandas DataFrame"
        assert len(normalized_df) == 3, "Should preserve all rows"
        
        # Check canonical column names
        expected_canonical = ['TestCaseID', 'Result', 'Priority', 'Module', 'Description']
        for col in expected_canonical:
            assert col in normalized_df.columns, f"Expected canonical column '{col}' not found"
        
        # Check that data is preserved
        assert normalized_df['TestCaseID'].tolist() == ['TC001', 'TC002', 'TC003']
        assert normalized_df['Result'].tolist() == ['Pass', 'Fail', 'Pass']
        assert normalized_df['Priority'].tolist() == ['High', 'Medium', 'Low']
    
    def test_normalize_columns_case_insensitive(self):
        """Test that column normalization is case-insensitive."""
        test_data = {
            'TCID': ['TC001', 'TC002'],
            'status': ['Pass', 'Fail'],
            'PRIORITY': ['High', 'Medium'],
            'module': ['Login', 'Checkout']
        }
        df = pd.DataFrame(test_data)
        
        normalized_df = normalize_columns(df)
        
        # Should map to canonical names regardless of case
        assert 'TestCaseID' in normalized_df.columns
        assert 'Result' in normalized_df.columns
        assert 'Priority' in normalized_df.columns
        assert 'Module' in normalized_df.columns
    
    def test_normalize_columns_missing_columns(self):
        """Test that missing columns are added with defaults."""
        test_data = {
            'TestCaseID': ['TC001', 'TC002'],
            'Result': ['Pass', 'Fail']
        }
        df = pd.DataFrame(test_data)
        
        normalized_df = normalize_columns(df)
        
        # Should add missing canonical columns
        expected_columns = ['TestCaseID', 'Result', 'Module', 'Description', 'Run', 'BugID', 'Severity', 'Duration', 'Tester']
        for col in expected_columns:
            assert col in normalized_df.columns, f"Missing column '{col}' should be added"
        
        # Check defaults
        assert normalized_df['Run'].tolist() == [1, 1]  # Default Run value
        assert normalized_df['Module'].isna().all() or normalized_df['Module'].eq('').all()  # Empty default
    
    def test_normalize_columns_empty_dataframe(self):
        """Test normalization with empty DataFrame."""
        df = pd.DataFrame()
        normalized_df = normalize_columns(df)
        
        assert isinstance(normalized_df, pd.DataFrame), "Should return a pandas DataFrame"
        assert normalized_df.empty, "Should remain empty"
        # Should still have canonical columns
        expected_columns = ['TestCaseID', 'Result', 'Module', 'Description', 'Run', 'BugID', 'Priority', 'Severity', 'Duration', 'Tester']
        for col in expected_columns:
            assert col in normalized_df.columns


class TestComputeMetrics:
    """Test cases for compute_metrics function."""
    
    def test_compute_metrics_basic(self):
        """Test basic metrics computation with passes and fails."""
        test_data = {
            'Module': ['Login', 'Login', 'Checkout', 'Checkout', 'Profile'],
            'TestCaseID': ['TC001', 'TC002', 'TC003', 'TC004', 'TC005'],
            'Result': ['Pass', 'Fail', 'Pass', 'Fail', 'Pass'],
            'BugID': ['', 'BUG001', '', 'BUG002', ''],
            'Severity': ['', 'Major', '', 'Critical', ''],
            'Priority': ['', 'High', '', 'Highest', '']
        }
        df = pd.DataFrame(test_data)
        
        metrics = compute_metrics(df)
        
        # Basic assertions
        assert isinstance(metrics, dict), "Should return a dictionary"
        
        # Test summary metrics
        assert 'summary' in metrics
        summary = metrics['summary']
        assert summary['total'] == 5, "Total tests should be 5"
        assert summary['executed'] == 5, "Executed tests should be 5"
        assert summary['passed'] == 3, "Passed tests should be 3"
        assert summary['failed'] == 2, "Failed tests should be 2"
        assert summary['pass_pct'] == 60.0, "Pass rate should be 60%"
    
    def test_compute_metrics_fail_by_module(self):
        """Test failures by module calculation."""
        test_data = {
            'Module': ['Login', 'Login', 'Checkout', 'Checkout', 'Profile'],
            'TestCaseID': ['TC001', 'TC002', 'TC003', 'TC004', 'TC005'],
            'Result': ['Pass', 'Fail', 'Pass', 'Fail', 'Pass']
        }
        df = pd.DataFrame(test_data)
        
        metrics = compute_metrics(df)
        
        # Test fail_by_module
        assert 'fail_by_module' in metrics
        fail_by_module = metrics['fail_by_module']
        assert fail_by_module['Login'] == 1, "Login should have 1 failure"
        assert fail_by_module['Checkout'] == 1, "Checkout should have 1 failure"
        assert 'Profile' not in fail_by_module or fail_by_module.get('Profile', 0) == 0, "Profile should have 0 failures"
    
    def test_compute_metrics_defects_by_severity(self):
        """Test defects by severity calculation."""
        test_data = {
            'Module': ['Login', 'Checkout', 'Profile'],
            'TestCaseID': ['TC001', 'TC002', 'TC003'],
            'Result': ['Fail', 'Fail', 'Fail'],
            'BugID': ['BUG001', 'BUG002', 'BUG003'],
            'Severity': ['Critical', 'Major', 'Medium']
        }
        df = pd.DataFrame(test_data)
        
        metrics = compute_metrics(df)
        
        # Test defects_by_severity
        assert 'defects_by_severity' in metrics
        defects = metrics['defects_by_severity']
        assert defects['Critical'] == 1, "Should have 1 Critical defect"
        assert defects['Major'] == 1, "Should have 1 Major defect"
        assert defects['Medium'] == 1, "Should have 1 Medium defect"
        assert defects['Minor'] == 0, "Should have 0 Minor defects"
    
    def test_compute_metrics_flaky_detection(self):
        """Test flaky test detection."""
        test_data = {
            'Module': ['Login', 'Login', 'Checkout', 'Checkout'],
            'TestCaseID': ['TC001', 'TC001', 'TC002', 'TC002'],  # Same test ID appears twice
            'Result': ['Pass', 'Fail', 'Pass', 'Pass']  # TC001 has both Pass and Fail
        }
        df = pd.DataFrame(test_data)
        
        metrics = compute_metrics(df)
        
        # Test flaky detection
        assert 'flaky' in metrics
        flaky_tests = metrics['flaky']
        assert 'TC001' in flaky_tests, "TC001 should be detected as flaky"
        assert 'TC002' not in flaky_tests, "TC002 should not be flaky"
    
    def test_compute_metrics_key_bugs(self):
        """Test key bugs extraction."""
        test_data = {
            'Module': ['Login', 'Checkout', 'Profile'],
            'TestCaseID': ['TC001', 'TC002', 'TC003'],
            'Result': ['Fail', 'Fail', 'Pass'],
            'BugID': ['BUG001', 'BUG002', '']  # Only first two have bugs
        }
        df = pd.DataFrame(test_data)
        
        metrics = compute_metrics(df)
        
        # Test key_bugs
        assert 'key_bugs' in metrics
        key_bugs = metrics['key_bugs']
        assert 'BUG001' in key_bugs, "BUG001 should be in key bugs"
        assert 'BUG002' in key_bugs, "BUG002 should be in key bugs"
        assert len(key_bugs) == 2, "Should have 2 unique bugs"
    
    def test_compute_metrics_empty_dataframe(self):
        """Test metrics computation with empty DataFrame."""
        df = pd.DataFrame()
        metrics = compute_metrics(df)
        
        # Should return empty metrics
        assert isinstance(metrics, dict)
        assert metrics['summary']['total'] == 0
        assert metrics['summary']['executed'] == 0
        assert metrics['summary']['passed'] == 0
        assert metrics['summary']['failed'] == 0
        assert metrics['summary']['pass_pct'] == 0.0
        assert metrics['fail_by_module'] == {}
        assert metrics['defects_by_severity'] == {'Critical': 0, 'Major': 0, 'Medium': 0, 'Minor': 0}
        assert metrics['key_bugs'] == []
        assert metrics['flaky'] == []


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])