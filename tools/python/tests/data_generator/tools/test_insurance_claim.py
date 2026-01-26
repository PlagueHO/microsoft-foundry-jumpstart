"""
Unit tests for the InsuranceClaimTool in data_generator.tools.insurance_claim module.
"""

import argparse
import json
import unittest
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
import yaml
from data_generator.tools.insurance_claim import InsuranceClaimTool


class TestInsuranceClaimToolInit(unittest.TestCase):
    """Test initialization of InsuranceClaimTool."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        tool = InsuranceClaimTool()
        self.assertEqual(tool.policy_type, "auto")
        self.assertEqual(tool.fraud_percent, 0)

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        tool = InsuranceClaimTool(policy_type="home", fraud_percent=10)
        self.assertEqual(tool.policy_type, "home")
        self.assertEqual(tool.fraud_percent, 10)

    def test_name_attributes(self):
        """Test the name attributes are set correctly."""
        tool = InsuranceClaimTool()
        self.assertEqual(tool.name, "insurance-claim")
        self.assertEqual(tool.toolName, "InsuranceClaim")


class TestInsuranceClaimToolCLI(unittest.TestCase):
    """Test CLI argument handling for InsuranceClaimTool."""

    def test_cli_arguments(self):
        """Test cli_arguments returns expected structure."""
        tool = InsuranceClaimTool()
        args = tool.cli_arguments()
        
        self.assertEqual(len(args), 2)
        
        # Check policy_type argument
        policy_arg = args[0]
        self.assertIn("-p", policy_arg["flags"])
        self.assertIn("--policy-type", policy_arg["flags"])
        self.assertEqual(policy_arg["kwargs"]["default"], "auto")
        self.assertFalse(policy_arg["kwargs"]["required"])
        
        # Check fraud_percent argument
        fraud_arg = args[1]
        self.assertIn("--fraud-percent", fraud_arg["flags"])
        self.assertEqual(fraud_arg["kwargs"]["default"], 0)
        self.assertEqual(fraud_arg["kwargs"]["type"], int)
        self.assertFalse(fraud_arg["kwargs"]["required"])

    def test_validate_args(self):
        """Test validate_args processes arguments correctly."""
        tool = InsuranceClaimTool()
        
        # Test with custom values
        ns = argparse.Namespace(policy_type="health", fraud_percent=25)
        tool.validate_args(ns)
        self.assertEqual(tool.policy_type, "health")
        self.assertEqual(tool.fraud_percent, 25)
        
        # Test with invalid fraud_percent (too high)
        ns = argparse.Namespace(policy_type="auto", fraud_percent=150)
        tool.validate_args(ns)
        self.assertEqual(tool.policy_type, "auto")
        # Should be clamped to max (100)
        self.assertEqual(tool.fraud_percent, 100)
        
        # Test with invalid fraud_percent (negative)
        ns = argparse.Namespace(policy_type="home", fraud_percent=-10)
        tool.validate_args(ns)
        self.assertEqual(tool.policy_type, "home")
        # Should be clamped to min (0)
        self.assertEqual(tool.fraud_percent, 0)


class TestInsuranceClaimToolOutputFormats(unittest.TestCase):
    """Test output format handling for InsuranceClaimTool."""

    def test_supported_output_formats(self):
        """Test supported_output_formats returns expected formats."""
        tool = InsuranceClaimTool()
        formats = tool.supported_output_formats()
        
        self.assertIn("json", formats)
        self.assertIn("yaml", formats)
        self.assertIn("txt", formats)
        self.assertEqual(len(formats), 3)

    def test_examples(self):
        """Test examples returns at least one example."""
        tool = InsuranceClaimTool()
        examples = tool.examples()
        
        self.assertGreater(len(examples), 0)
        self.assertIsInstance(examples[0], str)
        
        # Example should mention insurance-claim
        self.assertIn("insurance-claim", examples[0])


class TestInsuranceClaimToolPrompt(unittest.TestCase):
    """Test prompt building for InsuranceClaimTool."""

    @patch("uuid.uuid4")
    @patch("random.randint")
    @patch("random.choice")
    def test_build_prompt_json(self, mock_choice, mock_randint, mock_uuid4):
        """Test build_prompt for JSON output format."""
        # Setup mocks
        mock_uuid4.return_value = "test-uuid"
        mock_randint.return_value = 30  # Days ago
        mock_choice.return_value = "open"  # Status
        
        tool = InsuranceClaimTool(policy_type="auto", fraud_percent=0)
        prompt = tool.build_prompt("json")
        
        # Check that prompt contains expected elements
        self.assertIn("Claim ID: test-uuid", prompt)
        self.assertIn("Policy Type: auto", prompt)
        self.assertIn("Status: open", prompt)
        self.assertIn("Respond in JSON only", prompt)
        
        # Fraud flag should not be present with 0%
        self.assertNotIn("MAY BE FRAUDULENT", prompt)

    @patch("uuid.uuid4")
    @patch("random.randint")
    @patch("random.choice")
    @patch("random.random")
    def test_build_prompt_with_fraud(self, mock_random, mock_choice, mock_randint, mock_uuid4):
        """Test build_prompt with fraud flag."""
        # Setup mocks
        mock_uuid4.return_value = "test-uuid"
        mock_randint.return_value = 30
        mock_choice.return_value = "investigating"
        mock_random.return_value = 0.05  # Less than 10/100 to trigger fraud
        
        tool = InsuranceClaimTool(policy_type="home", fraud_percent=10)
        prompt = tool.build_prompt("yaml")
        
        # Check fraud flag is present
        self.assertIn("MAY BE FRAUDULENT", prompt)
        self.assertIn("Policy Type: home", prompt)
        self.assertIn("Respond in YAML only", prompt)

    @patch("uuid.uuid4")
    def test_build_prompt_custom_id(self, mock_uuid4):
        """Test build_prompt with custom unique_id."""
        # UUID should not be called if custom ID is provided
        custom_id = "custom-claim-id-123"
        
        tool = InsuranceClaimTool()
        prompt = tool.build_prompt("txt", unique_id=custom_id)
        
        self.assertIn(f"Claim ID: {custom_id}", prompt)
        mock_uuid4.assert_not_called()

    def test_random_incident(self):
        """Test _random_incident selects appropriate incident type."""
        # Test with auto policy
        tool = InsuranceClaimTool(policy_type="auto")
        with patch("random.choice") as mock_choice:
            mock_choice.return_value = "collision"
            incident = tool._random_incident()
            self.assertEqual(incident, "collision")
            mock_choice.assert_called_once_with(["collision", "theft", "windshield damage"])
        
        # Test with home policy
        tool = InsuranceClaimTool(policy_type="home")
        with patch("random.choice") as mock_choice:
            mock_choice.return_value = "fire"
            incident = tool._random_incident()
            self.assertEqual(incident, "fire")
            mock_choice.assert_called_once_with(["fire", "flood", "break-in"])
        
        # Test with health policy
        tool = InsuranceClaimTool(policy_type="health")
        with patch("random.choice") as mock_choice:
            mock_choice.return_value = "surgery"
            incident = tool._random_incident()
            self.assertEqual(incident, "surgery")
            mock_choice.assert_called_once_with(["surgery", "emergency room visit", "routine check-up"])
        
        # Test with unsupported policy type
        tool = InsuranceClaimTool(policy_type="unsupported")
        with patch("random.choice") as mock_choice:
            mock_choice.return_value = "other"
            incident = tool._random_incident()
            self.assertEqual(incident, "other")
            mock_choice.assert_called_once_with(["other"])


class TestInsuranceClaimToolPostProcessing(unittest.TestCase):
    """Test post-processing functionality for InsuranceClaimTool."""

    def test_post_process_valid_json(self):
        """Test post_process with valid JSON."""
        tool = InsuranceClaimTool()
        valid_json = '{"claim_id": "123", "policy_type": "auto"}'
        
        with patch("json.loads") as mock_loads:
            result = tool.post_process(valid_json, "json")
            mock_loads.assert_called_once_with(valid_json)
            self.assertEqual(result, valid_json)

    def test_post_process_valid_yaml(self):
        """Test post_process with valid YAML."""
        tool = InsuranceClaimTool()
        valid_yaml = "claim_id: '123'\npolicy_type: 'auto'"
        
        with patch("yaml.safe_load") as mock_safe_load:
            result = tool.post_process(valid_yaml, "yaml")
            mock_safe_load.assert_called_once_with(valid_yaml)
            self.assertEqual(result, valid_yaml)

    def test_post_process_txt(self):
        """Test post_process with text format."""
        tool = InsuranceClaimTool()
        text_content = "This is a plain text description."
        
        # No validation for txt format, should return as-is
        result = tool.post_process(text_content, "txt")
        self.assertEqual(result, text_content)

    def test_post_process_invalid_json(self):
        """Test post_process with invalid JSON."""
        tool = InsuranceClaimTool()
        invalid_json = "{'claim_id': '123'}"  # Single quotes invalid in JSON
        
        with patch("json.loads", side_effect=json.JSONDecodeError("Invalid JSON", doc="", pos=0)) as mock_loads:
            with patch("data_generator.tools.insurance_claim._logger") as mock_logger:
                result = tool.post_process(invalid_json, "json")
                
                mock_loads.assert_called_once()
                mock_logger.warning.assert_called_once()
                self.assertEqual(result, invalid_json)  # Original returned on error

    def test_post_process_invalid_yaml(self):
        """Test post_process with invalid YAML."""
        tool = InsuranceClaimTool()
        invalid_yaml = "claim_id: '123'\n  policy_type: 'auto'"  # Indentation error
        
        with patch("yaml.safe_load", side_effect=yaml.YAMLError("Invalid YAML")) as mock_safe_load:
            with patch("data_generator.tools.insurance_claim._logger") as mock_logger:
                result = tool.post_process(invalid_yaml, "yaml")
                
                mock_safe_load.assert_called_once()
                mock_logger.warning.assert_called_once()
                self.assertEqual(result, invalid_yaml)  # Original returned on error


class TestInsuranceClaimToolUtility(unittest.TestCase):
    """Test utility methods of InsuranceClaimTool."""

    def test_get_system_description(self):
        """Test get_system_description returns expected string."""
        tool = InsuranceClaimTool()
        description = tool.get_system_description()
        
        self.assertIsInstance(description, str)
        self.assertGreater(len(description), 0)
        
        # Description should mention insurance or claim
        self.assertTrue("insurance" in description.lower() or "claim" in description.lower())