"""
Clinical Healthcare Policy Document Generator.

This module provides a tool to generate synthetic clinical healthcare policy
documents for testing and development purposes. Supports various output formats
including JSON, YAML, and text.
"""

from __future__ import annotations

import argparse
import json
import random
import uuid
from datetime import datetime, timezone
from typing import Any

import yaml

from ..tool import DataGeneratorTool


class HealthcareClinicalPolicyTool(DataGeneratorTool):
    """Generate synthetic clinical healthcare policy documents."""

    # ------------------------------------------------------------------ #
    # Identification / registry key                                      #
    # ------------------------------------------------------------------ #
    name: str = "healthcare-clinical-policy"
    toolName: str = "HealthcareClinicalPolicy"

    # ------------------------------------------------------------------ #
    # CLI contract                                                       #
    # ------------------------------------------------------------------ #
    def __init__(
        self,
        *,
        specialty: str | None = None,
        policy_type: str | None = None,
        complexity: str | None = None,
    ) -> None:
        """Instantiate with optional specialty, policy type and complexity."""
        super().__init__()
        self.specialty = specialty or "General Medicine"
        self.policy_type = policy_type or "clinical-pathway"
        self.complexity = complexity or "medium"

    def cli_arguments(self) -> list[dict[str, Any]]:
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

    def validate_args(self, ns: argparse.Namespace) -> None:
        """Persist and validate CLI args."""
        self.specialty = ns.specialty or self.specialty
        self.policy_type = ns.policy_type or self.policy_type
        self.complexity = ns.complexity or self.complexity

    def examples(self) -> list[str]:
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
            "--specialty \"Emergency Medicine\" "
            "--policy-type treatment-protocol "
            "--output-format json",
        ]

    # ------------------------------------------------------------------ #
    # Output formats                                                     #
    # ------------------------------------------------------------------ #
    def supported_output_formats(self) -> list[str]:
        """Return supported output formats."""
        return ["yaml", "json", "txt", "text"]

    # ------------------------------------------------------------------ #
    # Prompt construction                                                #
    # ------------------------------------------------------------------ #
    _APPROVAL_STATUS: list[str] = [
        "draft",
        "under_review",
        "approved",
        "active",
        "superseded",
        "archived",
    ]
    _EVIDENCE_LEVELS: list[str] = [
        "Level I - Systematic Review",
        "Level II - Randomized Controlled Trial",
        "Level III - Cohort Study",
        "Level IV - Case Series",
        "Level V - Expert Opinion",
    ]
    _REVIEW_FREQUENCIES: list[str] = [
        "Annually",
        "Biannually",
        "Every 2 years",
        "Every 3 years",
        "As needed based on new evidence",
    ]

    def _random_attributes(self) -> tuple[str, str, str]:
        """Randomly choose approval status, evidence level, and review frequency."""
        return (
            random.choice(self._APPROVAL_STATUS),
            random.choice(self._EVIDENCE_LEVELS),
            random.choice(self._REVIEW_FREQUENCIES),
        )

    def _prompt_common(self, *, unique_id: str | None = None) -> str:
        """Common header with policy ID and timestamp."""
        approval_status, evidence_level, review_frequency = self._random_attributes()
        policy_id = unique_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        version = f"{random.randint(1, 5)}.{random.randint(0, 9)}"

        return (
            f"Policy ID (immutable): {policy_id}\n"
            f"Created At: {created_at}\n"
            f"Version: {version}\n"
            f"Specialty: {self.specialty}\n"
            f"Policy Type: {self.policy_type}\n"
            f"Complexity: {self.complexity}\n"
            f"Approval Status: {approval_status}\n"
            f"Evidence Level: {evidence_level}\n"
            f"Review Frequency: {review_frequency}\n"
            "Use ISO-8601 timestamps and do NOT invent real PII.\n\n"
        )

    def build_prompt(
        self, output_format: str, *, unique_id: str | None = None
    ) -> str:
        """
        Construct the full system-prompt string for the requested output format.
        All variable data is pre-baked so the kernel only receives the index
        placeholder.
        """
        # Normalize output format for text variations
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
        # Plain text is the default
        return base + self._text_skeleton()

    # ------------------------------------------------------------------ #
    # Static prompt fragments                                            #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _yaml_skeleton() -> str:
        """YAML response schema instructing the LLM on the exact shape."""
        return (
            "Return VALID YAML ONLY (no markdown fences).\n\n"
            "policy_id: (echo above)\n"
            "version: (echo above)\n"
            "created_at: (echo above)\n"
            "last_updated: ISO 8601\n"
            "title: clear descriptive policy title\n"
            "specialty: (echo above)\n"
            "policy_type: (echo above)\n"
            "complexity: simple|medium|complex\n"
            "approval_status: draft|under_review|approved|active|superseded|archived\n"
            "evidence_level: (echo above)\n"
            "review_frequency: (echo above)\n"
            "effective_date: ISO 8601\n"
            "next_review_date: ISO 8601\n"
            "author:\n"
            "  name: fictional name\n"
            "  title: clinical role\n"
            "  department: fictional department\n"
            "  email: realistic but fake email\n"
            "approvers:\n"
            "  - name: fictional name\n"
            "    title: clinical role\n"
            "    department: fictional department\n"
            "    approved_at: ISO 8601\n"
            "purpose: clear statement of policy purpose\n"
            "scope:\n"
            "  patient_populations:\n"
            "    - population description\n"
            "  clinical_settings:\n"
            "    - setting name\n"
            "  exclusion_criteria:\n"
            "    - exclusion description\n"
            "background:\n"
            "  clinical_rationale: detailed clinical justification\n"
            "  epidemiology: relevant statistics (fictional but realistic)\n"
            "  current_evidence_summary: summary of evidence base\n"
            "care_pathway:\n"
            "  phases:\n"
            "    - phase_number: 1\n"
            "      phase_name: text\n"
            "      description: text\n"
            "      timeframe: text\n"
            "      decision_points:\n"
            "        - criteria: text\n"
            "          action_if_met: text\n"
            "          action_if_not_met: text\n"
            "      clinical_interventions:\n"
            "        - intervention: text\n"
            "          indication: text\n"
            "          procedure: text\n"
            "          responsible_role: text\n"
            "clinical_procedures:\n"
            "  - procedure_name: text\n"
            "    indication: text\n"
            "    contraindications:\n"
            "      - contraindication\n"
            "    steps:\n"
            "      - step_number: 1\n"
            "        action: text\n"
            "        details: text\n"
            "        safety_considerations: text (optional)\n"
            "patient_assessment:\n"
            "  initial_assessment:\n"
            "    - assessment_area: text\n"
            "      criteria: text\n"
            "      tools: text\n"
            "  ongoing_monitoring:\n"
            "    - parameter: text\n"
            "      frequency: text\n"
            "      abnormal_value_action: text\n"
            "risk_stratification:\n"
            "  - risk_level: low|moderate|high|critical\n"
            "    criteria: text\n"
            "    management_approach: text\n"
            "    escalation_triggers: text\n"
            "treatment_options:\n"
            "  - option_name: text\n"
            "    indication: text\n"
            "    contraindications:\n"
            "      - contraindication\n"
            "    dosing_regimen: text (if applicable)\n"
            "    monitoring_requirements: text\n"
            "    expected_outcomes: text\n"
            "quality_indicators:\n"
            "  - indicator_name: text\n"
            "    measurement_method: text\n"
            "    target_value: text\n"
            "multidisciplinary_team:\n"
            "  - role: text\n"
            "    responsibilities:\n"
            "      - responsibility\n"
            "patient_communication:\n"
            "  information_to_provide:\n"
            "    - information item\n"
            "  consent_requirements: text\n"
            "  shared_decision_making: text\n"
            "documentation_requirements:\n"
            "  - document_type: text\n"
            "    required_elements:\n"
            "      - element\n"
            "    timing: text\n"
            "references:\n"
            "  - citation: text\n"
            "    evidence_level: text\n"
            "    url: fictional but realistic URL (optional)\n"
            "related_policies:\n"
            "  - policy_title: text\n"
            "    policy_id: fictional ID\n"
            "    relationship: text\n"
            "appendices:\n"
            "  - title: text\n"
            "    content: text\n"
            "version_history:\n"
            "  - version: text\n"
            "    date: ISO 8601\n"
            "    author: text\n"
            "    changes: text\n"
            "tags:\n"
            "  - tag text\n"
        )

    @staticmethod
    def _json_skeleton() -> str:
        """JSON response schema instructing the LLM on the exact shape."""
        return (
            "Return VALID JSON ONLY (no markdown fences).\n\n"
            "{\n"
            '  "policy_id": "(echo above)",\n'
            '  "version": "(echo above)",\n'
            '  "created_at": "(echo above)",\n'
            '  "last_updated": "ISO 8601",\n'
            '  "title": "clear descriptive policy title",\n'
            '  "specialty": "(echo above)",\n'
            '  "policy_type": "(echo above)",\n'
            '  "complexity": "simple|medium|complex",\n'
            '  "approval_status": "draft|under_review|approved|active|'
            'superseded|archived",\n'
            '  "evidence_level": "(echo above)",\n'
            '  "review_frequency": "(echo above)",\n'
            '  "effective_date": "ISO 8601",\n'
            '  "next_review_date": "ISO 8601",\n'
            '  "author": {\n'
            '    "name": "fictional name",\n'
            '    "title": "clinical role",\n'
            '    "department": "fictional department",\n'
            '    "email": "realistic but fake email"\n'
            '  },\n'
            '  "approvers": [\n'
            '    {\n'
            '      "name": "fictional name",\n'
            '      "title": "clinical role",\n'
            '      "department": "fictional department",\n'
            '      "approved_at": "ISO 8601"\n'
            '    }\n'
            '  ],\n'
            '  "purpose": "clear statement of policy purpose",\n'
            '  "scope": {\n'
            '    "patient_populations": ["population description"],\n'
            '    "clinical_settings": ["setting name"],\n'
            '    "exclusion_criteria": ["exclusion description"]\n'
            '  },\n'
            '  "background": {\n'
            '    "clinical_rationale": "detailed clinical justification",\n'
            '    "epidemiology": "relevant statistics (fictional but realistic)",\n'
            '    "current_evidence_summary": "summary of evidence base"\n'
            '  },\n'
            '  "care_pathway": {\n'
            '    "phases": [\n'
            '      {\n'
            '        "phase_number": 1,\n'
            '        "phase_name": "text",\n'
            '        "description": "text",\n'
            '        "timeframe": "text",\n'
            '        "decision_points": [\n'
            '          {\n'
            '            "criteria": "text",\n'
            '            "action_if_met": "text",\n'
            '            "action_if_not_met": "text"\n'
            '          }\n'
            '        ],\n'
            '        "clinical_interventions": [\n'
            '          {\n'
            '            "intervention": "text",\n'
            '            "indication": "text",\n'
            '            "procedure": "text",\n'
            '            "responsible_role": "text"\n'
            '          }\n'
            '        ]\n'
            '      }\n'
            '    ]\n'
            '  },\n'
            '  "clinical_procedures": [\n'
            '    {\n'
            '      "procedure_name": "text",\n'
            '      "indication": "text",\n'
            '      "contraindications": ["contraindication"],\n'
            '      "steps": [\n'
            '        {\n'
            '          "step_number": 1,\n'
            '          "action": "text",\n'
            '          "details": "text",\n'
            '          "safety_considerations": "text (optional)"\n'
            '        }\n'
            '      ]\n'
            '    }\n'
            '  ],\n'
            '  "patient_assessment": {\n'
            '    "initial_assessment": [\n'
            '      {\n'
            '        "assessment_area": "text",\n'
            '        "criteria": "text",\n'
            '        "tools": "text"\n'
            '      }\n'
            '    ],\n'
            '    "ongoing_monitoring": [\n'
            '      {\n'
            '        "parameter": "text",\n'
            '        "frequency": "text",\n'
            '        "abnormal_value_action": "text"\n'
            '      }\n'
            '    ]\n'
            '  },\n'
            '  "risk_stratification": [\n'
            '    {\n'
            '      "risk_level": "low|moderate|high|critical",\n'
            '      "criteria": "text",\n'
            '      "management_approach": "text",\n'
            '      "escalation_triggers": "text"\n'
            '    }\n'
            '  ],\n'
            '  "treatment_options": [\n'
            '    {\n'
            '      "option_name": "text",\n'
            '      "indication": "text",\n'
            '      "contraindications": ["contraindication"],\n'
            '      "dosing_regimen": "text (if applicable)",\n'
            '      "monitoring_requirements": "text",\n'
            '      "expected_outcomes": "text"\n'
            '    }\n'
            '  ],\n'
            '  "quality_indicators": [\n'
            '    {\n'
            '      "indicator_name": "text",\n'
            '      "measurement_method": "text",\n'
            '      "target_value": "text"\n'
            '    }\n'
            '  ],\n'
            '  "multidisciplinary_team": [\n'
            '    {\n'
            '      "role": "text",\n'
            '      "responsibilities": ["responsibility"]\n'
            '    }\n'
            '  ],\n'
            '  "patient_communication": {\n'
            '    "information_to_provide": ["information item"],\n'
            '    "consent_requirements": "text",\n'
            '    "shared_decision_making": "text"\n'
            '  },\n'
            '  "documentation_requirements": [\n'
            '    {\n'
            '      "document_type": "text",\n'
            '      "required_elements": ["element"],\n'
            '      "timing": "text"\n'
            '    }\n'
            '  ],\n'
            '  "references": [\n'
            '    {\n'
            '      "citation": "text",\n'
            '      "evidence_level": "text",\n'
            '      "url": "fictional but realistic URL (optional)"\n'
            '    }\n'
            '  ],\n'
            '  "related_policies": [\n'
            '    {\n'
            '      "policy_title": "text",\n'
            '      "policy_id": "fictional ID",\n'
            '      "relationship": "text"\n'
            '    }\n'
            '  ],\n'
            '  "appendices": [\n'
            '    {\n'
            '      "title": "text",\n'
            '      "content": "text"\n'
            '    }\n'
            '  ],\n'
            '  "version_history": [\n'
            '    {\n'
            '      "version": "text",\n'
            '      "date": "ISO 8601",\n'
            '      "author": "text",\n'
            '      "changes": "text"\n'
            '    }\n'
            '  ],\n'
            '  "tags": ["tag text"]\n'
            "}\n"
        )

    @staticmethod
    def _text_skeleton() -> str:
        """Plain-text layout for tools that prefer unstructured output."""
        return (
            "Return plain text WITHOUT any YAML/JSON formatting markers.\n\n"
            "Policy ID: (echo above)\n"
            "Version: (echo above)\n"
            "Created At: (echo above)\n"
            "Last Updated: ISO 8601\n"
            "Title: clear descriptive policy title\n"
            "Specialty: (echo above)\n"
            "Policy Type: (echo above)\n"
            "Complexity: simple|medium|complex\n"
            "Approval Status: draft|under_review|approved|active|superseded|archived\n"
            "Evidence Level: (echo above)\n"
            "Review Frequency: (echo above)\n"
            "Effective Date: ISO 8601\n"
            "Next Review Date: ISO 8601\n\n"
            "AUTHOR:\n"
            "Name: fictional name\n"
            "Title: clinical role\n"
            "Department: fictional department\n"
            "Email: realistic but fake email\n\n"
            "APPROVERS:\n"
            "- Name: fictional name | Title: clinical role | "
            "Department: fictional department | Approved At: ISO 8601\n\n"
            "PURPOSE:\n"
            "clear statement of policy purpose\n\n"
            "SCOPE:\n"
            "Patient Populations:\n"
            "- population description\n\n"
            "Clinical Settings:\n"
            "- setting name\n\n"
            "Exclusion Criteria:\n"
            "- exclusion description\n\n"
            "BACKGROUND:\n"
            "Clinical Rationale: detailed clinical justification\n"
            "Epidemiology: relevant statistics (fictional but realistic)\n"
            "Current Evidence Summary: summary of evidence base\n\n"
            "CARE PATHWAY:\n"
            "Phase 1: [phase_name] (timeframe)\n"
            "Description: text\n"
            "Decision Points:\n"
            "  - Criteria: text | Action if Met: text | Action if Not Met: text\n"
            "Clinical Interventions:\n"
            "  - Intervention: text | Indication: text | "
            "Procedure: text | Responsible Role: text\n\n"
            "CLINICAL PROCEDURES:\n"
            "Procedure: [procedure_name]\n"
            "Indication: text\n"
            "Contraindications:\n"
            "  - contraindication\n"
            "Steps:\n"
            "  1. Action: text\n"
            "     Details: text\n"
            "     Safety Considerations: text (optional)\n\n"
            "PATIENT ASSESSMENT:\n"
            "Initial Assessment:\n"
            "  - Assessment Area: text | Criteria: text | Tools: text\n"
            "Ongoing Monitoring:\n"
            "  - Parameter: text | Frequency: text | Abnormal Value Action: text\n\n"
            "RISK STRATIFICATION:\n"
            "- Risk Level: [level] | Criteria: text | "
            "Management Approach: text | Escalation Triggers: text\n\n"
            "TREATMENT OPTIONS:\n"
            "Option: [option_name]\n"
            "Indication: text\n"
            "Contraindications:\n"
            "  - contraindication\n"
            "Dosing Regimen: text (if applicable)\n"
            "Monitoring Requirements: text\n"
            "Expected Outcomes: text\n\n"
            "QUALITY INDICATORS:\n"
            "- Indicator: text | Measurement Method: text | Target Value: text\n\n"
            "MULTIDISCIPLINARY TEAM:\n"
            "- Role: text\n"
            "  Responsibilities:\n"
            "    - responsibility\n\n"
            "PATIENT COMMUNICATION:\n"
            "Information to Provide:\n"
            "  - information item\n"
            "Consent Requirements: text\n"
            "Shared Decision Making: text\n\n"
            "DOCUMENTATION REQUIREMENTS:\n"
            "- Document Type: text\n"
            "  Required Elements:\n"
            "    - element\n"
            "  Timing: text\n\n"
            "REFERENCES:\n"
            "- Citation: text | Evidence Level: text | URL: fictional but "
            "realistic URL (optional)\n\n"
            "RELATED POLICIES:\n"
            "- Policy Title: text | Policy ID: fictional ID | "
            "Relationship: text\n\n"
            "APPENDICES:\n"
            "- Title: text\n"
            "  Content: text\n\n"
            "VERSION HISTORY:\n"
            "Version: text | Date: ISO 8601 | Author: text | Changes: text\n\n"
            "TAGS: tag1, tag2, tag3\n"
        )

    # ------------------------------------------------------------------ #
    # Post-processing                                                    #
    # ------------------------------------------------------------------ #
    def post_process(self, raw: str, output_format: str) -> Any:  # noqa: ANN401
        """Deserialize based on output_format; fallback to raw string on failure."""
        fmt = output_format.lower()
        # Handle both 'txt' and 'text' variations
        if fmt in ("txt", "text"):
            return raw
        if fmt == "json" and raw.lstrip().startswith("{"):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
        if fmt == "yaml" and ":" in raw and "\n" in raw:  # naive YAML sniff
            try:
                return yaml.safe_load(raw)
            except yaml.YAMLError:
                return raw
        # plain-text or unrecognized format
        return raw

    # ------------------------------------------------------------------ #
    # Misc.                                                              #
    # ------------------------------------------------------------------ #
    def get_system_description(self) -> str:
        """Return the current system description string."""
        return (
            f"Clinical healthcare policy for {self.specialty} "
            f"({self.policy_type}, {self.complexity} complexity)"
        )
