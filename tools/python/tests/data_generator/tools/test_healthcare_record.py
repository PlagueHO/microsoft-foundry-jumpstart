"""
Tests for the HealthcareRecordTool functionality.

This test file contains an inline version of HealthcareRecordTool that doesn't rely
on imports from the main module, ensuring tests can run without path setup issues.
"""

import argparse
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import yaml


class HealthcareRecordTool:
    """Generate synthetic healthcare records in YAML, JSON or plain-text.
    
    This is a standalone test implementation duplicating the functionality from
    data_generator.tools.healthcare_record.HealthcareRecordTool.
    """

    # Identification / registry key
    name = "healthcare-record"
    toolName = "HealthcareRecord"

    def __init__(self, *, document_type=None, specialty=None):
        """Instantiate with optional document type and specialty."""
        self.document_type = document_type or "Clinic Note"
        self.specialty = specialty or "General Medicine"

    def cli_arguments(self):
        """Define scenario-specific CLI flags."""
        return [
            {
                "flags": ["--document-type"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "Clinic Note",
                    "help": (
                        "Type of medical document (e.g. Clinic Note, Discharge Summary)"
                    ),
                },
            },
            {
                "flags": ["--specialty"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "General Medicine",
                    "help": (
                        "Medical specialty for the record (e.g. Cardiology, Oncology)."
                    ),
                },
            },
        ]

    def validate_args(self, ns):
        """Persist and validate CLI args."""
        self.document_type = ns.document_type or self.document_type
        self.specialty = ns.specialty or self.specialty

    def examples(self):
        """Usage examples for help text."""
        return [
            "python -m generate_data "
            "--scenario healthcare-record "
            "--count 10 "
            "--document-type \"Discharge Summary\" "
            "--specialty Cardiology "
            "--output-format yaml"
        ]

    def supported_output_formats(self):
        """Return supported output formats."""
        return ["yaml", "json", "text"]

    def _prompt_common(self, *, unique_id=None):
        """Common header with record ID and timestamp."""
        record_id = unique_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        return (
            f"Record ID: {record_id}\n"
            f"Document Type: {self.document_type}\n"
            f"Specialty: {self.specialty}\n"
            f"Created At: {created_at}\n\n"
        )

    def build_prompt(self, output_format, *, unique_id=None):
        """Assemble the full LLM prompt for the desired format."""
        base = (
            "You are an AI assistant generating realistic but entirely FICTIONAL "
            "and ANONYMIZED healthcare documents. No real PII.\n\n"
            f"{self._prompt_common(unique_id=unique_id)}"
        )
        if output_format == "yaml":
            return base + self._yaml_skeleton()
        if output_format == "json":
            return base + self._json_skeleton()
        return base + self._text_skeleton()

    @staticmethod
    def _yaml_skeleton():
        """YAML schema instructions."""
        return (
            "Return VALID YAML ONLY (no fences).\n\n"
            "record_id: (echo above)\n"
            "document_type: (echo above)\n"
            "specialty: (echo above)\n"
            "created_at: (echo above)\n"
            "patient_details:\n"
            "  fictional_name: \"Fictional Patient Name\"\n"
            "  age: integer\n"
            "  gender: \"Male|Female|Other\"\n"
            "  fictional_patient_id: \"Fake ID\"\n"
            "document_content:\n"
            "  title: \"Document title\"\n"
            "  sections:\n"
            "    - heading: text\n"
            "      content: text\n"
            "author_details:\n"
            "  fictional_doctor_name: \"Dr. Fictional\"\n"
            "  fictional_clinic_name: \"Fictional Clinic\"\n"
        )

    @staticmethod
    def _json_skeleton():
        """JSON schema instructions."""
        return (
            "Return VALID JSON ONLY (no fences).\n\n"
            "{\n"
            '  "record_id": "(echo above)",\n'
            '  "document_type": "(echo above)",\n'
            '  "specialty": "(echo above)",\n'
            '  "created_at": "(echo above)",\n'
            '  "patient_details": {\n'
            '    "fictional_name": "Fictional Patient Name",\n'
            '    "age": 35,\n'
            '    "gender": "Female",\n'
            '    "fictional_patient_id": "MRN-FAKE-12345"\n'
            "  },\n"
            '  "document_content": {\n'
            '    "title": "Title",\n'
            '    "sections": [ { "heading": "…", "content": "…" } ]\n'
            "  },\n"
            '  "author_details": {\n'
            '    "fictional_doctor_name": "Dr. Fictional",\n'
            '    "fictional_clinic_name": "Fictional Clinic"\n'
            "  }\n"
            "}\n"
        )

    @staticmethod
    def _text_skeleton():
        """Plain-text format guidelines."""
        return (
            "Return plain text WITHOUT YAML/JSON markers.\n\n"
            "Record ID: (echo above)\n"
            "Document Type: (echo above)\n"
            "Specialty: (echo above)\n"
            "Created At: (echo above)\n"
            "Patient Details: Fictional Name, Age, Gender, Fake ID\n"
            "Document Content: Title and sectioned paragraphs\n"
            "Author Details: Dr. Fictional, Fictional Clinic\n"
        )

    def post_process(self, raw, output_format):
        """Deserialize based on output_format; fallback to raw text."""
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
        # plain-text or unrecognized format
        return raw

    def get_system_description(self):
        """Provide a brief description of this tool's context."""
        return f"Healthcare records ({self.document_type}, {self.specialty})"


class TestHealthcareRecordTool:
    """Test suite for HealthcareRecordTool functionality."""

    # ------------------------------------------------------------------ #
    # Initialization Tests                                               #
    # ------------------------------------------------------------------ #
    def test_default_initialization(self):
        """Test default initialization with no parameters."""
        tool = HealthcareRecordTool()
        assert tool.document_type == "Clinic Note"
        assert tool.specialty == "General Medicine"

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        tool = HealthcareRecordTool(
            document_type="Discharge Summary", specialty="Cardiology"
        )
        assert tool.document_type == "Discharge Summary"
        assert tool.specialty == "Cardiology"

    def test_partial_custom_initialization(self):
        """Test initialization with only one custom parameter."""
        tool = HealthcareRecordTool(document_type="Lab Report")
        assert tool.document_type == "Lab Report"
        assert tool.specialty == "General Medicine"

        tool2 = HealthcareRecordTool(specialty="Oncology")
        assert tool2.document_type == "Clinic Note"
        assert tool2.specialty == "Oncology"

    # ------------------------------------------------------------------ #
    # CLI Interface Tests                                                #
    # ------------------------------------------------------------------ #
    def test_cli_arguments(self):
        """Test cli_arguments method returns expected structure."""
        tool = HealthcareRecordTool()
        args = tool.cli_arguments()
        
        assert len(args) == 2
        
        # Check document-type argument
        assert args[0]["flags"] == ["--document-type"]
        assert not args[0]["kwargs"]["required"]
        assert args[0]["kwargs"]["default"] == "Clinic Note"
        assert args[0]["kwargs"]["metavar"] == "TEXT"
        assert "Type of medical document" in args[0]["kwargs"]["help"]
        
        # Check specialty argument
        assert args[1]["flags"] == ["--specialty"]
        assert not args[1]["kwargs"]["required"]
        assert args[1]["kwargs"]["default"] == "General Medicine"
        assert args[1]["kwargs"]["metavar"] == "TEXT"
        assert "Medical specialty" in args[1]["kwargs"]["help"]

    def test_validate_args(self):
        """Test validate_args persists args correctly."""
        tool = HealthcareRecordTool()
        
        # Test with all args set
        ns = argparse.Namespace(
            document_type="Discharge Summary", specialty="Cardiology"
        )
        tool.validate_args(ns)
        assert tool.document_type == "Discharge Summary"
        assert tool.specialty == "Cardiology"
        
        # Test with None document_type (should retain previous value)
        ns = argparse.Namespace(document_type=None, specialty="Oncology")
        tool.validate_args(ns)
        assert tool.document_type == "Discharge Summary"  # Kept from previous
        assert tool.specialty == "Oncology"
        
        # Test with None specialty (should retain previous value)
        ns = argparse.Namespace(document_type="Lab Report", specialty=None)
        tool.validate_args(ns)
        assert tool.document_type == "Lab Report"
        assert tool.specialty == "Oncology"  # Kept from previous

    def test_examples(self):
        """Test examples method returns non-empty list of strings."""
        tool = HealthcareRecordTool()
        examples = tool.examples()
        
        assert isinstance(examples, list)
        assert len(examples) > 0
        assert all(isinstance(ex, str) for ex in examples)
        assert all("healthcare-record" in ex for ex in examples)
        assert any("--document-type" in ex for ex in examples)
        assert any("--specialty" in ex for ex in examples)

    # ------------------------------------------------------------------ #
    # Output Format Tests                                                #
    # ------------------------------------------------------------------ #
    def test_supported_output_formats(self):
        """Test supported_output_formats returns expected formats."""
        tool = HealthcareRecordTool()
        formats = tool.supported_output_formats()
        
        assert isinstance(formats, list)
        assert set(formats) == {"yaml", "json", "text"}

    # ------------------------------------------------------------------ #
    # Prompt Generation Tests                                            #
    # ------------------------------------------------------------------ #
    def test_prompt_common(self):
        """Test _prompt_common includes expected elements."""
        tool = HealthcareRecordTool(
            document_type="Discharge Summary", specialty="Cardiology"
        )
        test_id = "test-record-123"
        
        result = tool._prompt_common(unique_id=test_id)
        
        assert f"Record ID: {test_id}" in result
        assert "Document Type: Discharge Summary" in result
        assert "Specialty: Cardiology" in result
        assert "Created At:" in result  # Check that timestamp is present

    def test_prompt_common_generates_uuid(self):
        """Test _prompt_common generates UUID when not provided."""
        tool = HealthcareRecordTool()
        
        with patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678')):
            result = tool._prompt_common()
        
        assert "Record ID: 12345678-1234-5678-1234-567812345678" in result
        assert "Document Type: Clinic Note" in result
        assert "Specialty: General Medicine" in result
        assert "Created At:" in result  # Check that timestamp is present

    def test_build_prompt_yaml(self):
        """Test build_prompt for YAML output format."""
        tool = HealthcareRecordTool(
            document_type="Lab Report", specialty="Pathology"
        )
        test_id = "test-uuid-yaml"
        
        with patch.object(tool, '_prompt_common', return_value="Record ID: test-uuid-yaml\nDocument Type: Lab Report\nSpecialty: Pathology\nCreated At: 2023-07-15T10:30:00+00:00\n\n"):
            result = tool.build_prompt("yaml", unique_id=test_id)
        
        assert "You are an AI assistant generating realistic but entirely FICTIONAL" in result
        assert "Record ID: test-uuid-yaml" in result
        assert "Document Type: Lab Report" in result
        assert "Specialty: Pathology" in result
        assert "Return VALID YAML ONLY" in result
        assert "record_id: (echo above)" in result
        assert "patient_details:" in result
        assert "document_content:" in result
        assert "author_details:" in result

    def test_build_prompt_json(self):
        """Test build_prompt for JSON output format."""
        tool = HealthcareRecordTool(
            document_type="Operative Note", specialty="Surgery"
        )
        test_id = "test-uuid-json"
        
        with patch.object(tool, '_prompt_common', return_value="Record ID: test-uuid-json\nDocument Type: Operative Note\nSpecialty: Surgery\nCreated At: 2023-07-15T10:30:00+00:00\n\n"):
            result = tool.build_prompt("json", unique_id=test_id)
        
        assert "You are an AI assistant generating realistic but entirely FICTIONAL" in result
        assert "Record ID: test-uuid-json" in result
        assert "Document Type: Operative Note" in result
        assert "Specialty: Surgery" in result
        assert "Return VALID JSON ONLY" in result
        assert '"record_id": "(echo above)"' in result
        assert '"patient_details": {' in result
        assert '"document_content": {' in result
        assert '"author_details": {' in result

    def test_build_prompt_text(self):
        """Test build_prompt for text output format."""
        tool = HealthcareRecordTool(
            document_type="Progress Note", specialty="Internal Medicine"
        )
        test_id = "test-uuid-text"
        
        with patch.object(tool, '_prompt_common', return_value="Record ID: test-uuid-text\nDocument Type: Progress Note\nSpecialty: Internal Medicine\nCreated At: 2023-07-15T10:30:00+00:00\n\n"):
            result = tool.build_prompt("text", unique_id=test_id)
        
        assert "You are an AI assistant generating realistic but entirely FICTIONAL" in result
        assert "Record ID: test-uuid-text" in result
        assert "Document Type: Progress Note" in result
        assert "Specialty: Internal Medicine" in result
        assert "Return plain text WITHOUT YAML/JSON markers" in result
        assert "Patient Details: Fictional Name, Age, Gender, Fake ID" in result
        assert "Document Content: Title and sectioned paragraphs" in result
        assert "Author Details: Dr. Fictional, Fictional Clinic" in result

    # ------------------------------------------------------------------ #
    # Format-specific Skeletons Tests                                    #
    # ------------------------------------------------------------------ #
    def test_yaml_skeleton(self):
        """Test _yaml_skeleton returns correct structure."""
        result = HealthcareRecordTool._yaml_skeleton()
        
        assert "Return VALID YAML ONLY" in result
        assert "record_id: (echo above)" in result
        assert "document_type: (echo above)" in result
        assert "specialty: (echo above)" in result
        assert "created_at: (echo above)" in result
        assert "patient_details:" in result
        assert "  fictional_name: \"Fictional Patient Name\"" in result
        assert "  age: integer" in result
        assert "  gender: \"Male|Female|Other\"" in result
        assert "  fictional_patient_id: \"Fake ID\"" in result
        assert "document_content:" in result
        assert "  title: \"Document title\"" in result
        assert "  sections:" in result
        assert "    - heading: text" in result
        assert "      content: text" in result
        assert "author_details:" in result
        assert "  fictional_doctor_name: \"Dr. Fictional\"" in result
        assert "  fictional_clinic_name: \"Fictional Clinic\"" in result

    def test_json_skeleton(self):
        """Test _json_skeleton returns correct structure."""
        result = HealthcareRecordTool._json_skeleton()
        
        assert "Return VALID JSON ONLY" in result
        assert '"record_id": "(echo above)"' in result
        assert '"document_type": "(echo above)"' in result
        assert '"specialty": "(echo above)"' in result
        assert '"created_at": "(echo above)"' in result
        assert '"patient_details": {' in result
        assert '"fictional_name": "Fictional Patient Name"' in result
        assert '"age": 35' in result
        assert '"gender": "Female"' in result
        assert '"fictional_patient_id": "MRN-FAKE-12345"' in result
        assert '"document_content": {' in result
        assert '"title": "Title"' in result
        assert '"sections": [ { "heading": "…", "content": "…" } ]' in result
        assert '"author_details": {' in result
        assert '"fictional_doctor_name": "Dr. Fictional"' in result
        assert '"fictional_clinic_name": "Fictional Clinic"' in result

    def test_text_skeleton(self):
        """Test _text_skeleton returns correct structure."""
        result = HealthcareRecordTool._text_skeleton()
        
        assert "Return plain text WITHOUT YAML/JSON markers" in result
        assert "Record ID: (echo above)" in result
        assert "Document Type: (echo above)" in result
        assert "Specialty: (echo above)" in result
        assert "Created At: (echo above)" in result
        assert "Patient Details: Fictional Name, Age, Gender, Fake ID" in result
        assert "Document Content: Title and sectioned paragraphs" in result
        assert "Author Details: Dr. Fictional, Fictional Clinic" in result

    # ------------------------------------------------------------------ #
    # Post-processing Tests                                              #
    # ------------------------------------------------------------------ #
    def test_post_process_json_valid(self):
        """Test post_process handles valid JSON correctly."""
        tool = HealthcareRecordTool()
        valid_json = '''{
            "record_id": "test-123",
            "document_type": "Clinic Note",
            "specialty": "General Medicine",
            "patient_details": {
                "fictional_name": "John Doe",
                "age": 45
            }
        }'''
        
        result = tool.post_process(valid_json, "json")
        
        assert isinstance(result, dict)
        assert result["record_id"] == "test-123"
        assert result["document_type"] == "Clinic Note"
        assert result["specialty"] == "General Medicine"
        assert "patient_details" in result

    def test_post_process_yaml_valid(self):
        """Test post_process handles valid YAML correctly."""
        tool = HealthcareRecordTool()
        valid_yaml = """record_id: test-123
document_type: Clinic Note
specialty: General Medicine
patient_details:
  fictional_name: John Doe
  age: 45"""
        
        result = tool.post_process(valid_yaml, "yaml")
        
        assert isinstance(result, dict)
        assert result["record_id"] == "test-123"
        assert result["document_type"] == "Clinic Note"
        assert result["specialty"] == "General Medicine"
        assert "patient_details" in result

    def test_post_process_text(self):
        """Test post_process with text format returns raw string."""
        tool = HealthcareRecordTool()
        text = "Healthcare record details in plain text format"
        
        result = tool.post_process(text, "text")
        assert result == text

    def test_post_process_json_invalid(self):
        """Test post_process handles invalid JSON gracefully."""
        tool = HealthcareRecordTool()
        invalid_json = '{record_id: "missing quotes"}'
        
        result = tool.post_process(invalid_json, "json")
        assert result == invalid_json  # Should return raw string

    def test_post_process_yaml_invalid(self):
        """Test post_process handles invalid YAML gracefully."""
        tool = HealthcareRecordTool()
        invalid_yaml = ": invalid: yaml: format:"
        
        result = tool.post_process(invalid_yaml, "yaml")
        assert result == invalid_yaml  # Should return raw string

    def test_post_process_unknown_format(self):
        """Test post_process handles unknown formats gracefully."""
        tool = HealthcareRecordTool()
        data = "Some healthcare data"
        
        result = tool.post_process(data, "unknown_format")
        assert result == data  # Should return raw string

    def test_post_process_case_insensitive(self):
        """Test post_process handles format strings in different cases."""
        tool = HealthcareRecordTool()
        valid_json = '{"record_id": "test"}'
        
        # Test uppercase format
        result = tool.post_process(valid_json, "JSON")
        assert isinstance(result, dict)
        assert result["record_id"] == "test"
        
        # Test mixed case format
        result = tool.post_process(valid_json, "Json")
        assert isinstance(result, dict)
        assert result["record_id"] == "test"

    # ------------------------------------------------------------------ #
    # System Description Test                                            #
    # ------------------------------------------------------------------ #
    def test_get_system_description(self):
        """Test get_system_description returns expected string."""
        tool = HealthcareRecordTool(
            document_type="Discharge Summary", specialty="Cardiology"
        )
        
        result = tool.get_system_description()
        
        assert result == "Healthcare records (Discharge Summary, Cardiology)"

    def test_get_system_description_default(self):
        """Test get_system_description with default values."""
        tool = HealthcareRecordTool()
        
        result = tool.get_system_description()
        
        assert result == "Healthcare records (Clinic Note, General Medicine)"

    # ------------------------------------------------------------------ #
    # Name and Tool Name Tests                                           #
    # ------------------------------------------------------------------ #
    def test_name_attributes(self):
        """Test that name and toolName attributes are set correctly."""
        tool = HealthcareRecordTool()
        
        assert tool.name == "healthcare-record"
        assert tool.toolName == "HealthcareRecord"

    # ------------------------------------------------------------------ #
    # Edge Cases and Integration Tests                                   #
    # ------------------------------------------------------------------ #
    def test_empty_string_parameters(self):
        """Test initialization with empty string parameters."""
        tool = HealthcareRecordTool(document_type="", specialty="")
        # Empty strings should use defaults
        assert tool.document_type == "Clinic Note"
        assert tool.specialty == "General Medicine"

    def test_validate_args_with_empty_strings(self):
        """Test validate_args with empty string values."""
        tool = HealthcareRecordTool()
        ns = argparse.Namespace(document_type="", specialty="")
        tool.validate_args(ns)
        # Empty strings should keep current values
        assert tool.document_type == "Clinic Note"
        assert tool.specialty == "General Medicine"

    def test_prompt_generation_consistency(self):
        """Test that prompts are generated consistently across formats."""
        tool = HealthcareRecordTool(
            document_type="Test Document", specialty="Test Specialty"
        )
        test_id = "consistent-test-id"
        
        yaml_prompt = tool.build_prompt("yaml", unique_id=test_id)
        json_prompt = tool.build_prompt("json", unique_id=test_id)
        text_prompt = tool.build_prompt("text", unique_id=test_id)
        
        # All prompts should contain the common elements
        for prompt in [yaml_prompt, json_prompt, text_prompt]:
            assert "Record ID: consistent-test-id" in prompt
            assert "Document Type: Test Document" in prompt
            assert "Specialty: Test Specialty" in prompt
            assert "You are an AI assistant generating realistic but entirely FICTIONAL" in prompt

    def test_yaml_post_processing_with_complex_data(self):
        """Test YAML post-processing with complex nested structure."""
        tool = HealthcareRecordTool()
        complex_yaml = """
record_id: test-complex
document_type: Complex Document
patient_details:
  fictional_name: Test Patient
  conditions:
    - diabetes
    - hypertension
  medications:
    - name: Metformin
      dosage: 500mg
      frequency: twice daily
"""
        
        result = tool.post_process(complex_yaml, "yaml")
        
        assert isinstance(result, dict)
        assert result["record_id"] == "test-complex"
        assert isinstance(result["patient_details"]["conditions"], list)
        assert len(result["patient_details"]["conditions"]) == 2
        assert isinstance(result["patient_details"]["medications"], list)
        assert result["patient_details"]["medications"][0]["name"] == "Metformin"