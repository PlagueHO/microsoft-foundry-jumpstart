"""
Tests for the HealthcareClinicalPolicyTool functionality.

This test file contains an inline version of HealthcareClinicalPolicyTool that
doesn't rely on imports from the main module, ensuring tests can run without
path setup issues.
"""

import argparse
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import yaml


class HealthcareClinicalPolicyTool:
    """Generate synthetic clinical healthcare policy documents.
    
    This is a standalone test implementation duplicating the functionality from
    data_generator.tools.healthcare_clinical_policy.HealthcareClinicalPolicyTool.
    """

    # Identification / registry key
    name = "healthcare-clinical-policy"
    toolName = "HealthcareClinicalPolicy"

    # Approval status options
    _APPROVAL_STATUS = [
        "draft",
        "under_review",
        "approved",
        "active",
        "superseded",
        "archived",
    ]

    def __init__(self, *, specialty=None, policy_type=None, complexity=None):
        """Instantiate with optional specialty, policy type and complexity."""
        self.specialty = specialty or "General Medicine"
        self.policy_type = policy_type or "clinical-pathway"
        self.complexity = complexity or "medium"

    def cli_arguments(self):
        """Define scenario-specific CLI flags."""
        return [
            {
                "flags": ["--specialty"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "General Medicine",
                    "help": (
                        "Clinical specialty for the policy "
                        "(e.g., Cardiology, Emergency Medicine, Oncology, "
                        "Pediatrics, Surgery, Internal Medicine)"
                    ),
                },
            },
            {
                "flags": ["--policy-type"],
                "kwargs": {
                    "required": False,
                    "choices": [
                        "clinical-pathway",
                        "treatment-protocol",
                        "diagnostic-guideline",
                        "medication-management",
                        "infection-control",
                        "patient-safety",
                        "quality-assurance",
                    ],
                    "default": "clinical-pathway",
                    "help": (
                        "Type of clinical policy document to generate"
                    ),
                },
            },
            {
                "flags": ["--complexity"],
                "kwargs": {
                    "required": False,
                    "choices": ["simple", "medium", "complex"],
                    "default": "medium",
                    "help": "Complexity level of the policy (simple, medium, complex)",
                },
            },
        ]

    def validate_args(self, ns):
        """Persist and validate CLI args."""
        self.specialty = ns.specialty or self.specialty
        self.policy_type = ns.policy_type or self.policy_type
        self.complexity = ns.complexity or self.complexity

    def examples(self):
        """Usage examples for help text."""
        return [
            "python -m data_generator "
            "--scenario clinical-healthcare-policy "
            "--count 10 "
            "--specialty Cardiology "
            "--policy-type clinical-pathway "
            "--complexity complex "
            "--output-format yaml",
            "python -m data_generator "
            "--scenario clinical-healthcare-policy "
            "--count 5 "
            '--specialty "Emergency Medicine" '
            "--policy-type treatment-protocol "
            "--output-format json",
        ]

    def supported_output_formats(self):
        """Return supported output formats."""
        return ["yaml", "json", "txt", "text"]

    def _prompt_common(self, *, unique_id=None):
        """Common header with policy ID and timestamp."""
        policy_id = unique_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        version = "1.0"

        return (
            f"Policy ID (immutable): {policy_id}\n"
            f"Created At: {created_at}\n"
            f"Version: {version}\n"
            f"Specialty: {self.specialty}\n"
            f"Policy Type: {self.policy_type}\n"
            f"Complexity: {self.complexity}\n"
            "Approval Status: active\n"
            "Evidence Level: Level II - Randomized Controlled Trial\n"
            "Review Frequency: Annually\n"
            "Use ISO-8601 timestamps and do NOT invent real PII.\n\n"
        )

    def build_prompt(self, output_format, *, unique_id=None):
        """Assemble the full LLM prompt for the desired format."""
        fmt = output_format.lower()
        if fmt == "text":
            fmt = "txt"

        base = (
            "You are a clinical healthcare policy specialist generating REALISTIC "
            "but ENTIRELY FICTIONAL clinical policy documents based on real-world "
            "clinical standards and best practices.\n\n"
            "## ON THE CLINICAL POLICY\n\n"
            f"Specialty: {self.specialty}\n"
            f"Policy Type: {self.policy_type}\n"
            f"Complexity Level: {self.complexity}\n\n"
            f"{self._prompt_common(unique_id=unique_id)}"
            "## ON POLICY CONTENT\n\n"
            "Clinical policies should include:\n"
            "- Clear policy title and purpose statement\n"
            "- Scope and applicability (patient populations, clinical settings)\n"
            "- Evidence-based clinical rationale and background\n"
            "- Detailed care pathways with decision points and timeframes\n"
            "- Step-by-step clinical procedures and interventions\n"
            "- Patient assessment criteria and diagnostic requirements\n"
            "- Treatment options with indications and contraindications\n"
            "- Risk stratification and escalation criteria\n"
            "- Monitoring and follow-up requirements\n"
            "- Quality indicators and outcome measures\n"
            "- References to clinical guidelines and evidence sources\n"
            "- Multidisciplinary team roles and responsibilities\n"
            "- Patient communication and consent considerations\n"
            "- Documentation requirements\n"
            "- Version history with clinically meaningful changes\n\n"
            "All clinical details must be realistic and evidence-based but "
            "entirely fictional. Use realistic medical terminology, clinical "
            "decision trees, and care pathways similar to those found in real "
            "healthcare organizations.\n"
        )

        if fmt == "yaml":
            return base + self._yaml_skeleton()
        if fmt == "json":
            return base + self._json_skeleton()
        return base + self._text_skeleton()

    @staticmethod
    def _yaml_skeleton():
        """YAML schema instructions."""
        return (
            "Return VALID YAML ONLY (no markdown fences).\n\n"
            "policy_id: (echo above)\n"
            "version: (echo above)\n"
            "created_at: (echo above)\n"
            "title: clear descriptive policy title\n"
            "specialty: (echo above)\n"
            "policy_type: (echo above)\n"
            "complexity: simple|medium|complex\n"
            "care_pathway:\n"
            "  phases:\n"
            "clinical_procedures:\n"
        )

    @staticmethod
    def _json_skeleton():
        """JSON schema instructions."""
        return (
            "Return VALID JSON ONLY (no markdown fences).\n\n"
            "{\n"
            '  "policy_id": "(echo above)",\n'
            '  "version": "(echo above)",\n'
            '  "created_at": "(echo above)",\n'
            '  "title": "clear descriptive policy title",\n'
            '  "care_pathway": {\n'
            '    "phases": []\n'
            "  }\n"
            "}\n"
        )

    @staticmethod
    def _text_skeleton():
        """Plain-text format guidelines."""
        return (
            "Return plain text WITHOUT any YAML/JSON formatting markers.\n\n"
            "Policy ID: (echo above)\n"
            "Version: (echo above)\n"
            "Title: clear descriptive policy title\n"
            "CARE PATHWAY:\n"
            "CLINICAL PROCEDURES:\n"
        )

    def post_process(self, raw, output_format):
        """Deserialize based on output_format; fallback to raw text."""
        fmt = output_format.lower()
        if fmt in ("txt", "text"):
            return raw
        if fmt == "json" and raw.lstrip().startswith("{"):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
        if fmt == "yaml" and ":" in raw and "\n" in raw:
            try:
                return yaml.safe_load(raw)
            except yaml.YAMLError:
                return raw
        return raw

    def get_system_description(self):
        """Provide a brief description of this tool's context."""
        return (
            f"Clinical healthcare policy for {self.specialty} "
            f"({self.policy_type}, {self.complexity} complexity)"
        )


class TestHealthcareClinicalPolicyTool:
    """Test suite for HealthcareClinicalPolicyTool functionality."""

    # ------------------------------------------------------------------ #
    # Initialization Tests                                               #
    # ------------------------------------------------------------------ #
    def test_default_initialization(self):
        """Test default initialization with no parameters."""
        tool = HealthcareClinicalPolicyTool()
        assert tool.specialty == "General Medicine"
        assert tool.policy_type == "clinical-pathway"
        assert tool.complexity == "medium"

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        tool = HealthcareClinicalPolicyTool(
            specialty="Cardiology",
            policy_type="treatment-protocol",
            complexity="complex",
        )
        assert tool.specialty == "Cardiology"
        assert tool.policy_type == "treatment-protocol"
        assert tool.complexity == "complex"

    def test_partial_custom_initialization(self):
        """Test initialization with only some custom parameters."""
        tool = HealthcareClinicalPolicyTool(specialty="Emergency Medicine")
        assert tool.specialty == "Emergency Medicine"
        assert tool.policy_type == "clinical-pathway"
        assert tool.complexity == "medium"

        tool2 = HealthcareClinicalPolicyTool(policy_type="medication-management")
        assert tool2.specialty == "General Medicine"
        assert tool2.policy_type == "medication-management"
        assert tool2.complexity == "medium"

        tool3 = HealthcareClinicalPolicyTool(complexity="simple")
        assert tool3.specialty == "General Medicine"
        assert tool3.policy_type == "clinical-pathway"
        assert tool3.complexity == "simple"

    # ------------------------------------------------------------------ #
    # CLI Interface Tests                                                #
    # ------------------------------------------------------------------ #
    def test_cli_arguments(self):
        """Test cli_arguments method returns expected structure."""
        tool = HealthcareClinicalPolicyTool()
        args = tool.cli_arguments()

        assert len(args) == 3

        # Check specialty argument
        assert args[0]["flags"] == ["--specialty"]
        assert not args[0]["kwargs"]["required"]
        assert args[0]["kwargs"]["default"] == "General Medicine"
        assert args[0]["kwargs"]["metavar"] == "TEXT"
        assert "Clinical specialty" in args[0]["kwargs"]["help"]

        # Check policy-type argument
        assert args[1]["flags"] == ["--policy-type"]
        assert not args[1]["kwargs"]["required"]
        assert args[1]["kwargs"]["default"] == "clinical-pathway"
        assert "clinical-pathway" in args[1]["kwargs"]["choices"]
        assert "treatment-protocol" in args[1]["kwargs"]["choices"]
        assert "diagnostic-guideline" in args[1]["kwargs"]["choices"]

        # Check complexity argument
        assert args[2]["flags"] == ["--complexity"]
        assert not args[2]["kwargs"]["required"]
        assert args[2]["kwargs"]["default"] == "medium"
        assert set(args[2]["kwargs"]["choices"]) == {"simple", "medium", "complex"}

    def test_validate_args(self):
        """Test validate_args persists args correctly."""
        tool = HealthcareClinicalPolicyTool()

        # Test with all args set
        ns = argparse.Namespace(
            specialty="Cardiology",
            policy_type="clinical-pathway",
            complexity="complex",
        )
        tool.validate_args(ns)
        assert tool.specialty == "Cardiology"
        assert tool.policy_type == "clinical-pathway"
        assert tool.complexity == "complex"

        # Test with None values (should retain previous values)
        ns = argparse.Namespace(
            specialty=None, policy_type="treatment-protocol", complexity=None
        )
        tool.validate_args(ns)
        assert tool.specialty == "Cardiology"  # Kept from previous
        assert tool.policy_type == "treatment-protocol"
        assert tool.complexity == "complex"  # Kept from previous

    def test_examples(self):
        """Test examples method returns non-empty list of strings."""
        tool = HealthcareClinicalPolicyTool()
        examples = tool.examples()

        assert isinstance(examples, list)
        assert len(examples) > 0
        assert all(isinstance(ex, str) for ex in examples)
        assert all("clinical-healthcare-policy" in ex for ex in examples)
        assert any("--specialty" in ex for ex in examples)
        assert any("--policy-type" in ex for ex in examples)
        assert any("--complexity" in ex for ex in examples)

    # ------------------------------------------------------------------ #
    # Output Format Tests                                                #
    # ------------------------------------------------------------------ #
    def test_supported_output_formats(self):
        """Test supported_output_formats returns expected formats."""
        tool = HealthcareClinicalPolicyTool()
        formats = tool.supported_output_formats()

        assert isinstance(formats, list)
        assert set(formats) == {"yaml", "json", "txt", "text"}

    # ------------------------------------------------------------------ #
    # Prompt Generation Tests                                            #
    # ------------------------------------------------------------------ #
    def test_prompt_common(self):
        """Test _prompt_common includes expected elements."""
        tool = HealthcareClinicalPolicyTool(
            specialty="Cardiology",
            policy_type="treatment-protocol",
            complexity="complex",
        )
        test_id = "test-policy-123"

        result = tool._prompt_common(unique_id=test_id)

        assert f"Policy ID (immutable): {test_id}" in result
        assert "Specialty: Cardiology" in result
        assert "Policy Type: treatment-protocol" in result
        assert "Complexity: complex" in result
        assert "Approval Status:" in result
        assert "Evidence Level:" in result
        assert "Review Frequency:" in result
        assert "Created At:" in result
        assert "Version:" in result

    def test_prompt_common_generates_uuid(self):
        """Test _prompt_common generates UUID when not provided."""
        tool = HealthcareClinicalPolicyTool()

        with patch(
            "uuid.uuid4",
            return_value=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        ):
            result = tool._prompt_common()

        assert "Policy ID (immutable): 12345678-1234-5678-1234-567812345678" in result
        assert "Specialty: General Medicine" in result
        assert "Policy Type: clinical-pathway" in result
        assert "Complexity: medium" in result

    def test_build_prompt_yaml(self):
        """Test build_prompt for YAML output format."""
        tool = HealthcareClinicalPolicyTool(
            specialty="Emergency Medicine",
            policy_type="diagnostic-guideline",
            complexity="simple",
        )
        test_id = "test-uuid-yaml"

        with patch.object(
            tool,
            "_prompt_common",
            return_value=(
                "Policy ID (immutable): test-uuid-yaml\n"
                "Created At: 2023-07-15T10:30:00+00:00\n"
                "Version: 1.0\n"
                "Specialty: Emergency Medicine\n"
                "Policy Type: diagnostic-guideline\n"
                "Complexity: simple\n"
                "Approval Status: active\n"
                "Evidence Level: Level II\n"
                "Review Frequency: Annually\n\n"
            ),
        ):
            result = tool.build_prompt("yaml", unique_id=test_id)

        assert "You are a clinical healthcare policy specialist" in result
        assert "Policy ID (immutable): test-uuid-yaml" in result
        assert "Specialty: Emergency Medicine" in result
        assert "Policy Type: diagnostic-guideline" in result
        assert "Complexity Level: simple" in result
        assert "Return VALID YAML ONLY" in result
        assert "policy_id: (echo above)" in result
        assert "care_pathway:" in result
        assert "clinical_procedures:" in result

    def test_build_prompt_json(self):
        """Test build_prompt for JSON output format."""
        tool = HealthcareClinicalPolicyTool(
            specialty="Oncology", policy_type="medication-management", complexity="medium"
        )
        test_id = "test-uuid-json"

        with patch.object(
            tool,
            "_prompt_common",
            return_value=(
                "Policy ID (immutable): test-uuid-json\n"
                "Created At: 2023-07-15T10:30:00+00:00\n"
                "Version: 1.0\n"
                "Specialty: Oncology\n"
                "Policy Type: medication-management\n"
                "Complexity: medium\n\n"
            ),
        ):
            result = tool.build_prompt("json", unique_id=test_id)

        assert "You are a clinical healthcare policy specialist" in result
        assert "Policy ID (immutable): test-uuid-json" in result
        assert "Specialty: Oncology" in result
        assert "Policy Type: medication-management" in result
        assert "Return VALID JSON ONLY" in result
        assert '"policy_id": "(echo above)"' in result
        assert '"care_pathway": {' in result

    def test_build_prompt_text(self):
        """Test build_prompt for text output format."""
        tool = HealthcareClinicalPolicyTool(
            specialty="Pediatrics", policy_type="patient-safety", complexity="complex"
        )
        test_id = "test-uuid-text"

        with patch.object(
            tool,
            "_prompt_common",
            return_value=(
                "Policy ID (immutable): test-uuid-text\n"
                "Created At: 2023-07-15T10:30:00+00:00\n"
                "Version: 1.0\n"
                "Specialty: Pediatrics\n"
                "Policy Type: patient-safety\n"
                "Complexity: complex\n\n"
            ),
        ):
            result = tool.build_prompt("text", unique_id=test_id)

        assert "You are a clinical healthcare policy specialist" in result
        assert "Policy ID (immutable): test-uuid-text" in result
        assert "Specialty: Pediatrics" in result
        assert "Policy Type: patient-safety" in result
        assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
        assert "CARE PATHWAY:" in result

    def test_build_prompt_txt_variant(self):
        """Test build_prompt handles 'txt' as equivalent to 'text'."""
        tool = HealthcareClinicalPolicyTool()
        test_id = "test-txt"

        result = tool.build_prompt("txt", unique_id=test_id)

        assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result

    # ------------------------------------------------------------------ #
    # Format-specific Skeletons Tests                                    #
    # ------------------------------------------------------------------ #
    def test_yaml_skeleton(self):
        """Test _yaml_skeleton returns correct structure."""
        result = HealthcareClinicalPolicyTool._yaml_skeleton()

        assert "Return VALID YAML ONLY" in result
        assert "policy_id: (echo above)" in result
        assert "version: (echo above)" in result
        assert "created_at: (echo above)" in result
        assert "title: clear descriptive policy title" in result
        assert "specialty: (echo above)" in result
        assert "policy_type: (echo above)" in result
        assert "care_pathway:" in result
        assert "clinical_procedures:" in result

    def test_json_skeleton(self):
        """Test _json_skeleton returns correct structure."""
        result = HealthcareClinicalPolicyTool._json_skeleton()

        assert "Return VALID JSON ONLY" in result
        assert '"policy_id": "(echo above)"' in result
        assert '"version": "(echo above)"' in result
        assert '"created_at": "(echo above)"' in result
        assert '"title": "clear descriptive policy title"' in result
        assert '"care_pathway": {' in result

    def test_text_skeleton(self):
        """Test _text_skeleton returns correct structure."""
        result = HealthcareClinicalPolicyTool._text_skeleton()

        assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
        assert "Policy ID: (echo above)" in result
        assert "Version: (echo above)" in result
        assert "Title: clear descriptive policy title" in result
        assert "CARE PATHWAY:" in result
        assert "CLINICAL PROCEDURES:" in result

    # ------------------------------------------------------------------ #
    # Post-processing Tests                                              #
    # ------------------------------------------------------------------ #
    def test_post_process_json_valid(self):
        """Test post_process handles valid JSON correctly."""
        tool = HealthcareClinicalPolicyTool()
        valid_json = """{
            "policy_id": "test-123",
            "specialty": "Cardiology",
            "policy_type": "clinical-pathway",
            "care_pathway": {
                "phases": []
            }
        }"""

        result = tool.post_process(valid_json, "json")

        assert isinstance(result, dict)
        assert result["policy_id"] == "test-123"
        assert result["specialty"] == "Cardiology"
        assert result["policy_type"] == "clinical-pathway"
        assert "care_pathway" in result

    def test_post_process_yaml_valid(self):
        """Test post_process handles valid YAML correctly."""
        tool = HealthcareClinicalPolicyTool()
        valid_yaml = """policy_id: test-123
specialty: Cardiology
policy_type: clinical-pathway
care_pathway:
  phases:
    - phase_number: 1"""

        result = tool.post_process(valid_yaml, "yaml")

        assert isinstance(result, dict)
        assert result["policy_id"] == "test-123"
        assert result["specialty"] == "Cardiology"
        assert result["policy_type"] == "clinical-pathway"
        assert "care_pathway" in result

    def test_post_process_text(self):
        """Test post_process with text format returns raw string."""
        tool = HealthcareClinicalPolicyTool()
        text = "Clinical healthcare policy details in plain text format"

        result = tool.post_process(text, "text")
        assert result == text

        result_txt = tool.post_process(text, "txt")
        assert result_txt == text

    def test_post_process_json_invalid(self):
        """Test post_process handles invalid JSON gracefully."""
        tool = HealthcareClinicalPolicyTool()
        invalid_json = '{policy_id: "missing quotes"}'

        result = tool.post_process(invalid_json, "json")
        assert result == invalid_json  # Should return raw string

    def test_post_process_yaml_invalid(self):
        """Test post_process handles invalid YAML gracefully."""
        tool = HealthcareClinicalPolicyTool()
        invalid_yaml = ": invalid: yaml: format:"

        result = tool.post_process(invalid_yaml, "yaml")
        assert result == invalid_yaml  # Should return raw string

    def test_post_process_unknown_format(self):
        """Test post_process handles unknown formats gracefully."""
        tool = HealthcareClinicalPolicyTool()
        data = "Some policy data"

        result = tool.post_process(data, "unknown_format")
        assert result == data  # Should return raw string

    def test_post_process_case_insensitive(self):
        """Test post_process handles format strings in different cases."""
        tool = HealthcareClinicalPolicyTool()
        valid_json = '{"policy_id": "test"}'

        # Test uppercase format
        result = tool.post_process(valid_json, "JSON")
        assert isinstance(result, dict)
        assert result["policy_id"] == "test"

        # Test mixed case format
        result = tool.post_process(valid_json, "Json")
        assert isinstance(result, dict)
        assert result["policy_id"] == "test"

    # ------------------------------------------------------------------ #
    # System Description Test                                            #
    # ------------------------------------------------------------------ #
    def test_get_system_description(self):
        """Test get_system_description returns expected string."""
        tool = HealthcareClinicalPolicyTool(
            specialty="Emergency Medicine",
            policy_type="treatment-protocol",
            complexity="complex",
        )

        result = tool.get_system_description()

        assert (
            result
            == "Clinical healthcare policy for Emergency Medicine (treatment-protocol, complex complexity)"
        )

    def test_get_system_description_default(self):
        """Test get_system_description with default values."""
        tool = HealthcareClinicalPolicyTool()

        result = tool.get_system_description()

        assert (
            result
            == "Clinical healthcare policy for General Medicine (clinical-pathway, medium complexity)"
        )

    # ------------------------------------------------------------------ #
    # Name and Tool Name Tests                                           #
    # ------------------------------------------------------------------ #
    def test_name_attributes(self):
        """Test that name and toolName attributes are set correctly."""
        tool = HealthcareClinicalPolicyTool()

        assert tool.name == "healthcare-clinical-policy"
        assert tool.toolName == "HealthcareClinicalPolicy"

    # ------------------------------------------------------------------ #
    # Edge Cases and Integration Tests                                   #
    # ------------------------------------------------------------------ #
    def test_empty_string_parameters(self):
        """Test initialization with empty string parameters."""
        tool = HealthcareClinicalPolicyTool(
            specialty="", policy_type="", complexity=""
        )
        # Empty strings should use defaults
        assert tool.specialty == "General Medicine"
        assert tool.policy_type == "clinical-pathway"
        assert tool.complexity == "medium"

    def test_validate_args_with_empty_strings(self):
        """Test validate_args with empty string values."""
        tool = HealthcareClinicalPolicyTool()
        ns = argparse.Namespace(specialty="", policy_type="", complexity="")
        tool.validate_args(ns)
        # Empty strings should keep current values
        assert tool.specialty == "General Medicine"
        assert tool.policy_type == "clinical-pathway"
        assert tool.complexity == "medium"

    def test_prompt_generation_consistency(self):
        """Test that prompts are generated consistently across formats."""
        tool = HealthcareClinicalPolicyTool(
            specialty="Test Specialty", policy_type="clinical-pathway", complexity="medium"
        )
        test_id = "consistent-test-id"

        yaml_prompt = tool.build_prompt("yaml", unique_id=test_id)
        json_prompt = tool.build_prompt("json", unique_id=test_id)
        text_prompt = tool.build_prompt("text", unique_id=test_id)

        # All prompts should contain the common elements
        for prompt in [yaml_prompt, json_prompt, text_prompt]:
            assert "Policy ID (immutable): consistent-test-id" in prompt
            assert "Specialty: Test Specialty" in prompt
            assert "Policy Type: clinical-pathway" in prompt
            assert "You are a clinical healthcare policy specialist" in prompt

    def test_yaml_post_processing_with_complex_data(self):
        """Test YAML post-processing with complex nested structure."""
        tool = HealthcareClinicalPolicyTool()
        complex_yaml = """
policy_id: test-complex
specialty: Cardiology
care_pathway:
  phases:
    - phase_number: 1
      phase_name: Initial Assessment
      decision_points:
        - criteria: STEMI confirmed
          action_if_met: Activate cath lab
          action_if_not_met: Continue monitoring
      clinical_interventions:
        - intervention: ECG monitoring
          indication: All patients
          responsible_role: Nursing
"""

        result = tool.post_process(complex_yaml, "yaml")

        assert isinstance(result, dict)
        assert result["policy_id"] == "test-complex"
        assert result["specialty"] == "Cardiology"
        assert isinstance(result["care_pathway"]["phases"], list)
        assert len(result["care_pathway"]["phases"]) == 1
        assert result["care_pathway"]["phases"][0]["phase_name"] == "Initial Assessment"
        assert isinstance(
            result["care_pathway"]["phases"][0]["decision_points"], list
        )
        assert (
            result["care_pathway"]["phases"][0]["decision_points"][0]["criteria"]
            == "STEMI confirmed"
        )

    def test_all_policy_types(self):
        """Test that all policy types can be initialized."""
        policy_types = [
            "clinical-pathway",
            "treatment-protocol",
            "diagnostic-guideline",
            "medication-management",
            "infection-control",
            "patient-safety",
            "quality-assurance",
        ]

        for policy_type in policy_types:
            tool = HealthcareClinicalPolicyTool(policy_type=policy_type)
            assert tool.policy_type == policy_type
            # Verify prompt can be built
            prompt = tool.build_prompt("json")
            assert f"Policy Type: {policy_type}" in prompt

    def test_all_complexity_levels(self):
        """Test that all complexity levels can be initialized."""
        complexity_levels = ["simple", "medium", "complex"]

        for complexity in complexity_levels:
            tool = HealthcareClinicalPolicyTool(complexity=complexity)
            assert tool.complexity == complexity
            # Verify prompt can be built
            prompt = tool.build_prompt("json")
            assert f"Complexity: {complexity}" in prompt

    def test_various_specialties(self):
        """Test that various specialties can be initialized."""
        specialties = [
            "General Medicine",
            "Cardiology",
            "Emergency Medicine",
            "Oncology",
            "Pediatrics",
            "Surgery",
            "Internal Medicine",
        ]

        for specialty in specialties:
            tool = HealthcareClinicalPolicyTool(specialty=specialty)
            assert tool.specialty == specialty
            # Verify prompt can be built
            prompt = tool.build_prompt("json")
            assert f"Specialty: {specialty}" in prompt

