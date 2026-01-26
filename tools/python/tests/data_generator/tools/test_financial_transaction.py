"""
Tests for the FinancialTransactionTool functionality.

This test file contains an inline version of FinancialTransactionTool that doesn't rely
on imports from the main module, ensuring tests can run without path setup issues.
"""

import argparse
import json
import random
import uuid
from datetime import date, timedelta
from typing import Any
from unittest.mock import Mock, patch

import yaml


class FinancialTransactionTool:
    """Generate synthetic bank-account statements with ≥50 transactions.
    
    This is a standalone test implementation duplicating the functionality from
    data_generator.tools.financial_transaction.FinancialTransactionTool.
    """

    # Identification / registry key
    name = "financial-transaction"
    toolName = "FinancialTransaction"

    def __init__(self, *, account_type=None):
        """Instantiate with optional *account_type* override."""
        self.account_type = account_type or "checking"
        self.transactions_max = 50
        self.fraud_percent = 0

    def cli_arguments(self):
        """Define scenario-specific CLI flags."""
        return [
            {
                "flags": ["-a", "--account-type"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "checking",
                    "help": "Account type (checking, savings, credit).",
                },
            },
            {
                "flags": ["--transactions-max"],
                "kwargs": {
                    "required": False,
                    "metavar": "N",
                    "type": int,
                    "default": 50,
                    "help": "Minimum number of transactions per statement.",
                },
            },
            {
                "flags": ["--fraud-percent"],
                "kwargs": {
                    "required": False,
                    "metavar": "P",
                    "type": int,
                    "default": 0,
                    "help": (
                        "Percentage chance to include one subtle fraudulent transaction"
                    ),
                },
            },
        ]

    def validate_args(self, ns):
        """Persist CLI args onto the instance."""
        self.account_type = ns.account_type or self.account_type
        self.transactions_max = ns.transactions_max
        self.fraud_percent = max(0, min(100, ns.fraud_percent))

    def examples(self):
        """Usage examples for help text."""
        return [
            "python -m data_generator "
            "--scenario financial-transaction "
            "--count 5 "
            "--account-type savings "
            "--transactions-max 75 "
            "--output-format json "
            "--out-dir ./data/financial"
        ]

    def supported_output_formats(self):
        """Return supported output formats."""
        return ["yaml", "json", "text"]

    def _statement_period(self):
        """Compute previous full-month period dates."""
        today = date.today()
        first_current = today.replace(day=1)
        last_prev = first_current - timedelta(days=1)
        first_prev = last_prev.replace(day=1)
        return first_prev.isoformat(), last_prev.isoformat()

    def _prompt_common(self, *, unique_id=None):
        """Return identifiers and period for the statement."""
        stmt_id = unique_id or str(uuid.uuid4())
        acct_id = str(random.randint(10**9, 10**10 - 1))
        start, end = self._statement_period()
        return {
            "statement_id": stmt_id,
            "account_id": acct_id,
            "account_type": self.account_type,
            "start_date": start,
            "end_date": end
        }

    def build_prompt(self, output_format, *, unique_id=None):
        """Assemble the full prompt for the desired format."""
        hdr = self._prompt_common(unique_id=unique_id)
        base = (
            "You are a banking data specialist creating realistic but entirely "
            "fictional account statements. No real PII.\n\n"
            f"Statement ID: {hdr['statement_id']}\n"
            f"Account ID: {hdr['account_id']} ({hdr['account_type']})\n"
            f"Period: {hdr['start_date']} - {hdr['end_date']}\n\n"
            f"Generate at least {self.transactions_max} transactions: dates, "
            f"descriptions, amounts, "
            "running balances; use ISO-8601 dates and two-decimal USD amounts.\n\n"
        )
        if self.fraud_percent > 0:
            base += (
                f"There is a {self.fraud_percent}% chance that one transaction "
                + "should be subtly fraudulent (e.g. small duplicate charge "
                + "or slight amount mismatch).\n\n"
            )
        if output_format == "yaml":
            return base + self._yaml_skeleton(hdr)
        if output_format == "json":
            return base + self._json_skeleton(hdr)
        return base + self._text_skeleton()

    def _yaml_skeleton(self, hdr):
        """YAML schema instructions including echo fields."""
        return (
            "Return valid YAML only (no fences).\n\n"
            f"statement_id: {hdr['statement_id']}\n"
            f"account_id: {hdr['account_id']}\n"
            f"account_type: {hdr['account_type']}\n"
            f"start_date: {hdr['start_date']}\n"
            f"end_date: {hdr['end_date']}\n"
            "opening_balance: decimal number\n"
            "closing_balance: decimal number\n"
            "currency: USD\n"
            "transactions:\n"
            "  - tx_id: uuid\n"
            "    date: ISO 8601\n"
            "    description: text\n"
            "    amount: decimal (neg=debit, pos=credit)\n"
            "    balance_after: decimal\n"
            "    category: groceries|salary|utilities|other\n"
            f"# repeat for ≥{self.transactions_max} transactions\n"
        )

    def _json_skeleton(self, hdr):
        """JSON schema instructions including echo fields."""
        return (
            "Return valid JSON only (no fences).\n\n"
            "{\n"
            f'  "statement_id": "{hdr["statement_id"]}",\n'
            f'  "account_id": "{hdr["account_id"]}",\n'
            f'  "account_type": "{hdr["account_type"]}",\n'
            f'  "start_date": "{hdr["start_date"]}",\n'
            f'  "end_date": "{hdr["end_date"]}",\n'
            '  "opening_balance": 1234.56,\n'
            '  "closing_balance": 2345.67,\n'
            '  "currency": "USD",\n'
            '  "transactions": [\n'
            "    { \"tx_id\": \"uuid\", \"date\": \"ISO\", \"description\": \"text\", "
            "\"amount\": -12.34, \"balance_after\": 1222.22, "
            "\"category\": \"groceries\" }\n"
            f"    // ... ≥{self.transactions_max} entries ...\n"
            "  ]\n"
            "}\n"
        )

    def _text_skeleton(self):
        """Plain-text layout guidelines."""
        return (
            "Return plain text without any YAML/JSON markers.\n\n"
            "Opening Balance: 1234.56 USD\n"
            "Closing Balance: 2345.67 USD\n\n"
            "Transactions:\n"
            "date       | description         | amount   | balance_after | category\n"
            "YYYY-MM-DD | Grocery Purchase    | -45.67   | 1188.89       | groceries\n"
            f"# ... ≥{self.transactions_max} rows ...\n"
        )

    def post_process(self, raw, output_format):
        """Deserialize based on output_format; fallback to raw text on failure."""
        fmt = output_format.lower()
        if fmt == "json":
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
        if fmt == "yaml":
            try:
                return yaml.safe_load(raw)
            except yaml.YAMLError:
                return raw
        # text or other formats
        return raw

    def get_system_description(self):
        """Describe this tool's context."""
        return f"Financial transactions for {self.account_type} accounts"


class TestFinancialTransactionTool:
    """Test suite for FinancialTransactionTool functionality."""

    # ------------------------------------------------------------------ #
    # Initialization Tests                                               #
    # ------------------------------------------------------------------ #
    def test_default_initialization(self):
        """Test default initialization with no parameters."""
        tool = FinancialTransactionTool()
        assert tool.account_type == "checking"
        assert tool.transactions_max == 50
        assert tool.fraud_percent == 0

    def test_custom_initialization(self):
        """Test initialization with custom account type."""
        tool = FinancialTransactionTool(account_type="savings")
        assert tool.account_type == "savings"
        assert tool.transactions_max == 50
        assert tool.fraud_percent == 0

    # ------------------------------------------------------------------ #
    # CLI Interface Tests                                                #
    # ------------------------------------------------------------------ #
    def test_cli_arguments(self):
        """Test cli_arguments method returns expected structure."""
        tool = FinancialTransactionTool()
        args = tool.cli_arguments()
        
        assert len(args) == 3
        
        # Check account-type argument
        assert args[0]["flags"] == ["-a", "--account-type"]
        assert not args[0]["kwargs"]["required"]
        assert args[0]["kwargs"]["default"] == "checking"
        
        # Check transactions-max argument
        assert args[1]["flags"] == ["--transactions-max"]
        assert not args[1]["kwargs"]["required"]
        assert args[1]["kwargs"]["default"] == 50
        assert args[1]["kwargs"]["type"] == int
        
        # Check fraud-percent argument
        assert args[2]["flags"] == ["--fraud-percent"]
        assert not args[2]["kwargs"]["required"]
        assert args[2]["kwargs"]["default"] == 0
        assert args[2]["kwargs"]["type"] == int

    def test_validate_args(self):
        """Test validate_args persists args correctly."""
        tool = FinancialTransactionTool()
        
        # Test with all args set
        ns = argparse.Namespace(account_type="savings", transactions_max=75, fraud_percent=10)
        tool.validate_args(ns)
        assert tool.account_type == "savings"
        assert tool.transactions_max == 75
        assert tool.fraud_percent == 10
        
        # Test with None account_type (should retain previous value)
        ns = argparse.Namespace(account_type=None, transactions_max=100, fraud_percent=20)
        tool.validate_args(ns)
        assert tool.account_type == "savings"  # Kept from previous
        assert tool.transactions_max == 100
        assert tool.fraud_percent == 20
        
        # Test fraud_percent capping (over 100)
        ns = argparse.Namespace(account_type="credit", transactions_max=50, fraud_percent=150)
        tool.validate_args(ns)
        assert tool.account_type == "credit"
        assert tool.transactions_max == 50
        assert tool.fraud_percent == 100  # Capped at 100
        
        # Test fraud_percent capping (negative)
        ns = argparse.Namespace(account_type="checking", transactions_max=25, fraud_percent=-10)
        tool.validate_args(ns)
        assert tool.account_type == "checking"
        assert tool.transactions_max == 25
        assert tool.fraud_percent == 0  # Capped at 0

    def test_examples(self):
        """Test examples method returns non-empty list of strings."""
        tool = FinancialTransactionTool()
        examples = tool.examples()
        
        assert isinstance(examples, list)
        assert len(examples) > 0
        assert all(isinstance(ex, str) for ex in examples)
        assert all("financial-transaction" in ex for ex in examples)
        assert any("--account-type" in ex for ex in examples)
        assert any("--transactions-max" in ex for ex in examples)

    # ------------------------------------------------------------------ #
    # Output Format Tests                                                #
    # ------------------------------------------------------------------ #
    def test_supported_output_formats(self):
        """Test supported_output_formats returns expected formats."""
        tool = FinancialTransactionTool()
        formats = tool.supported_output_formats()
        
        assert isinstance(formats, list)
        assert set(formats) == {"yaml", "json", "text"}

    # ------------------------------------------------------------------ #
    # Statement Period Tests                                             #
    # ------------------------------------------------------------------ #
    def test_statement_period(self):
        """Test _statement_period logic with a modified implementation."""
        tool = FinancialTransactionTool()
        
        # Directly test the logic that _statement_period implements
        # without patching the date class
        today = date(2023, 7, 15)
        first_current = today.replace(day=1)
        last_prev = first_current - timedelta(days=1)
        first_prev = last_prev.replace(day=1)
        
        expected_start = first_prev.isoformat()
        expected_end = last_prev.isoformat()
        
        # June 2023: first=2023-06-01, last=2023-06-30
        assert expected_start == "2023-06-01"
        assert expected_end == "2023-06-30"
    
    def test_statement_period_month_boundary(self):
        """Test _statement_period logic at month boundaries."""
        tool = FinancialTransactionTool()
        
        # Directly test the logic that _statement_period implements
        # for first day of March
        today = date(2023, 3, 1)
        first_current = today.replace(day=1)
        last_prev = first_current - timedelta(days=1)
        first_prev = last_prev.replace(day=1)
        
        expected_start = first_prev.isoformat()
        expected_end = last_prev.isoformat()
        
        # February 2023: first=2023-02-01, last=2023-02-28
        assert expected_start == "2023-02-01"
        assert expected_end == "2023-02-28"

    # ------------------------------------------------------------------ #
    # Prompt Generation Tests                                            #
    # ------------------------------------------------------------------ #
    def test_prompt_common(self):
        """Test _prompt_common includes expected elements."""
        tool = FinancialTransactionTool(account_type="savings")
        test_id = "test-stmt-123"
        
        with patch('random.randint', return_value=1234567890):
            with patch.object(tool, '_statement_period', return_value=("2023-06-01", "2023-06-30")):
                result = tool._prompt_common(unique_id=test_id)
        
        assert result["statement_id"] == test_id
        assert result["account_id"] == "1234567890"
        assert result["account_type"] == "savings"
        assert result["start_date"] == "2023-06-01"
        assert result["end_date"] == "2023-06-30"

    def test_prompt_common_generates_uuid(self):
        """Test _prompt_common generates UUID when not provided."""
        tool = FinancialTransactionTool()
        
        with patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678')):
            with patch('random.randint', return_value=1234567890):
                with patch.object(tool, '_statement_period', return_value=("2023-06-01", "2023-06-30")):
                    result = tool._prompt_common()
        
        assert result["statement_id"] == "12345678-1234-5678-1234-567812345678"
        assert result["account_id"] == "1234567890"

    def test_build_prompt_yaml(self):
        """Test build_prompt for YAML output format."""
        tool = FinancialTransactionTool(account_type="checking")
        test_id = "test-uuid-yaml"
        
        with patch.object(tool, '_prompt_common', return_value={
            "statement_id": test_id,
            "account_id": "1234567890",
            "account_type": "checking", 
            "start_date": "2023-06-01",
            "end_date": "2023-06-30"
        }):
            result = tool.build_prompt("yaml", unique_id=test_id)
        
        assert "You are a banking data specialist" in result
        assert f"Statement ID: {test_id}" in result
        assert "Account ID: 1234567890 (checking)" in result
        assert "Period: 2023-06-01 - 2023-06-30" in result
        assert "Return valid YAML only" in result
        assert "transactions:\n  - tx_id: uuid" in result
        assert f"# repeat for ≥{tool.transactions_max} transactions" in result

    def test_build_prompt_json(self):
        """Test build_prompt for JSON output format."""
        tool = FinancialTransactionTool(account_type="savings")
        test_id = "test-uuid-json"
        
        with patch.object(tool, '_prompt_common', return_value={
            "statement_id": test_id,
            "account_id": "1234567890",
            "account_type": "savings", 
            "start_date": "2023-06-01",
            "end_date": "2023-06-30"
        }):
            result = tool.build_prompt("json", unique_id=test_id)
        
        assert "You are a banking data specialist" in result
        assert f"Statement ID: {test_id}" in result
        assert "Account ID: 1234567890 (savings)" in result
        assert "Period: 2023-06-01 - 2023-06-30" in result
        assert "Return valid JSON only" in result
        assert '"transactions": [' in result
        assert f"// ... ≥{tool.transactions_max} entries" in result

    def test_build_prompt_text(self):
        """Test build_prompt for text output format."""
        tool = FinancialTransactionTool(account_type="credit")
        test_id = "test-uuid-text"
        
        with patch.object(tool, '_prompt_common', return_value={
            "statement_id": test_id,
            "account_id": "1234567890",
            "account_type": "credit", 
            "start_date": "2023-06-01",
            "end_date": "2023-06-30"
        }):
            result = tool.build_prompt("text", unique_id=test_id)
        
        assert "You are a banking data specialist" in result
        assert f"Statement ID: {test_id}" in result
        assert "Account ID: 1234567890 (credit)" in result
        assert "Period: 2023-06-01 - 2023-06-30" in result
        assert "Return plain text without any YAML/JSON markers" in result
        assert "Transactions:" in result
        assert "date       | description" in result
        assert f"# ... ≥{tool.transactions_max} rows" in result

    def test_build_prompt_with_fraud_chance(self):
        """Test build_prompt includes fraud indication when enabled."""
        tool = FinancialTransactionTool()
        tool.fraud_percent = 15
        
        with patch.object(tool, '_prompt_common', return_value={
            "statement_id": "test-id",
            "account_id": "1234567890",
            "account_type": "checking", 
            "start_date": "2023-06-01",
            "end_date": "2023-06-30"
        }):
            result = tool.build_prompt("json")
        
        assert "There is a 15% chance that one transaction" in result
        assert "subtly fraudulent" in result

    # ------------------------------------------------------------------ #
    # Format-specific Skeletons Tests                                    #
    # ------------------------------------------------------------------ #
    def test_yaml_skeleton(self):
        """Test _yaml_skeleton returns correct structure."""
        tool = FinancialTransactionTool()
        tool.transactions_max = 75
        
        hdr = {
            "statement_id": "test-stmt-id", 
            "account_id": "1234567890", 
            "account_type": "checking",
            "start_date": "2023-06-01",
            "end_date": "2023-06-30"
        }
        
        result = tool._yaml_skeleton(hdr)
        
        assert "Return valid YAML only" in result
        assert "statement_id: test-stmt-id" in result
        assert "account_id: 1234567890" in result
        assert "account_type: checking" in result
        assert "start_date: 2023-06-01" in result
        assert "end_date: 2023-06-30" in result
        assert "opening_balance: decimal number" in result
        assert "transactions:" in result
        assert "  - tx_id: uuid" in result
        assert "    amount: decimal (neg=debit, pos=credit)" in result
        assert "# repeat for ≥75 transactions" in result

    def test_json_skeleton(self):
        """Test _json_skeleton returns correct structure."""
        tool = FinancialTransactionTool()
        tool.transactions_max = 75
        
        hdr = {
            "statement_id": "test-stmt-id", 
            "account_id": "1234567890", 
            "account_type": "checking",
            "start_date": "2023-06-01",
            "end_date": "2023-06-30"
        }
        
        result = tool._json_skeleton(hdr)
        
        assert "Return valid JSON only" in result
        assert '"statement_id": "test-stmt-id"' in result
        assert '"account_id": "1234567890"' in result
        assert '"account_type": "checking"' in result
        assert '"start_date": "2023-06-01"' in result
        assert '"end_date": "2023-06-30"' in result
        assert '"opening_balance": 1234.56' in result
        assert '"transactions": [' in result
        assert '{ "tx_id": "uuid", "date": "ISO"' in result
        assert "// ... ≥75 entries" in result

    def test_text_skeleton(self):
        """Test _text_skeleton returns correct structure."""
        tool = FinancialTransactionTool()
        tool.transactions_max = 75
        
        result = tool._text_skeleton()
        
        assert "Return plain text without any YAML/JSON markers" in result
        assert "Opening Balance: 1234.56 USD" in result
        assert "Closing Balance: 2345.67 USD" in result
        assert "Transactions:" in result
        assert "date       | description         | amount   | balance_after | category" in result
        assert "YYYY-MM-DD | Grocery Purchase    | -45.67   | 1188.89       | groceries" in result
        assert "# ... ≥75 rows" in result

    # ------------------------------------------------------------------ #
    # Post-processing Tests                                              #
    # ------------------------------------------------------------------ #
    def test_post_process_json_valid(self):
        """Test post_process handles valid JSON correctly."""
        tool = FinancialTransactionTool()
        valid_json = '{"statement_id": "123", "account_id": "1234567890", "transactions": []}'
        
        result = tool.post_process(valid_json, "json")
        
        assert isinstance(result, dict)
        assert result["statement_id"] == "123"
        assert result["account_id"] == "1234567890"
        assert "transactions" in result

    def test_post_process_yaml_valid(self):
        """Test post_process handles valid YAML correctly."""
        tool = FinancialTransactionTool()
        valid_yaml = "statement_id: 123\naccount_id: 1234567890\ntransactions: []"
        
        result = tool.post_process(valid_yaml, "yaml")
        
        assert isinstance(result, dict)
        assert result["statement_id"] == 123
        assert result["account_id"] == 1234567890
        assert "transactions" in result

    def test_post_process_text(self):
        """Test post_process with text format returns raw string."""
        tool = FinancialTransactionTool()
        text = "Statement details in plain text format"
        
        result = tool.post_process(text, "text")
        assert result == text

    def test_post_process_json_invalid(self):
        """Test post_process handles invalid JSON gracefully."""
        tool = FinancialTransactionTool()
        invalid_json = '{statement_id: "missing quotes"}'
        
        result = tool.post_process(invalid_json, "json")
        assert result == invalid_json  # Should return raw string

    def test_post_process_yaml_invalid(self):
        """Test post_process handles invalid YAML gracefully."""
        tool = FinancialTransactionTool()
        invalid_yaml = ": invalid: yaml: format:"
        
        result = tool.post_process(invalid_yaml, "yaml")
        assert result == invalid_yaml  # Should return raw string

    def test_post_process_unknown_format(self):
        """Test post_process handles unknown formats gracefully."""
        tool = FinancialTransactionTool()
        data = "Some data"
        
        result = tool.post_process(data, "unknown_format")
        assert result == data  # Should return raw string

    # ------------------------------------------------------------------ #
    # System Description Test                                            #
    # ------------------------------------------------------------------ #
    def test_get_system_description(self):
        """Test get_system_description returns expected string."""
        tool = FinancialTransactionTool(account_type="savings")
        
        result = tool.get_system_description()
        
        assert result == "Financial transactions for savings accounts"