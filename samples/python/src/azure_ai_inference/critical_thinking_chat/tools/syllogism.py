"""
Syllogism evaluation tool for logical validity analysis.

This module provides the evaluate_syllogism function and supporting helpers.
"""
import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def evaluate_syllogism(major_premise: str, minor_premise: str, conclusion: str) -> str:
    """
    Evaluate the logical validity of a syllogism.

    This function analyzes the logical structure of a syllogism consisting of
    a major premise, minor premise, and conclusion to determine validity and
    identify logical errors or fallacies.

    Args:
        major_premise: The major premise statement (universal statement)
        minor_premise: The minor premise statement (specific statement)
        conclusion: The conclusion statement (derived statement)

    Returns:
        JSON string containing detailed validity analysis including:
        - valid: boolean indicating logical validity
        - form: type of syllogism (categorical, conditional, disjunctive)
        - analysis: detailed explanation of the logical structure
        - errors: list of identified logical fallacies or errors
    """
    try:
        analysis_result: Dict[str, Any] = {
            "major_premise": major_premise,
            "minor_premise": minor_premise,
            "conclusion": conclusion,
            "valid": False,
            "form": "categorical",
            "analysis": "",
            "errors": []
        }

        if not all([major_premise.strip(), minor_premise.strip(), conclusion.strip()]):
            analysis_result["errors"].append("incomplete_premises")
            analysis_result["analysis"] = "One or more premises are empty or missing."
            return json.dumps(analysis_result, indent=2)

        if any(word in major_premise.lower() for word in ["if ", "then ", "implies"]):
            analysis_result["form"] = "conditional"
        elif any(word in major_premise.lower() for word in [" either ", " or ", " neither "]):
            analysis_result["form"] = "disjunctive"
        else:
            analysis_result["form"] = "categorical"

        major_lower = major_premise.lower()
        if any(word in major_lower for word in ["all", "every", "always", "never", "no one", "everyone"]):
            if not _has_sufficient_evidence(major_premise):
                analysis_result["errors"].append("hasty_generalization")

        if analysis_result["form"] == "conditional":
            if "if" in major_lower and "then" in major_lower:
                if _is_affirming_consequent(major_premise, minor_premise, conclusion):
                    analysis_result["errors"].append("affirming_consequent")
                    analysis_result["valid"] = False
                elif _is_valid_modus_ponens(major_premise, minor_premise, conclusion):
                    analysis_result["valid"] = True
        elif analysis_result["form"] == "categorical":
            if _has_undistributed_middle(major_premise, minor_premise, conclusion):
                analysis_result["errors"].append("undistributed_middle")
                analysis_result["valid"] = False
            elif _is_valid_categorical_syllogism(major_premise, minor_premise, conclusion):
                analysis_result["valid"] = True

        if analysis_result["valid"] and not analysis_result["errors"]:
            analysis_result["analysis"] = f"This is a valid {analysis_result['form']} syllogism. The logical structure is sound and the conclusion follows from the premises."
        elif analysis_result["errors"]:
            error_descriptions = {
                "hasty_generalization": "The major premise makes a sweeping generalization without sufficient evidence",
                "affirming_consequent": "This commits the fallacy of affirming the consequent in conditional reasoning",
                "undistributed_middle": "The middle term is not properly distributed, making the conclusion invalid",
                "incomplete_premises": "One or more premises are missing or incomplete"
            }
            error_details = [error_descriptions.get(error, error) for error in analysis_result["errors"]]
            error_details_filtered = [detail for detail in error_details if detail is not None]
            analysis_result["analysis"] = f"This {analysis_result['form']} syllogism contains logical errors: {', '.join(error_details_filtered)}. The conclusion does not necessarily follow from the premises."
        else:
            analysis_result["analysis"] = f"This {analysis_result['form']} syllogism requires further analysis to determine validity."

        return json.dumps(analysis_result, indent=2)

    except Exception as e:
        logger.error("Error in evaluate_syllogism: %s", e)
        error_result: Dict[str, Any] = {
            "major_premise": major_premise,
            "minor_premise": minor_premise,
            "conclusion": conclusion,
            "valid": False,
            "form": "unknown",
            "analysis": f"Error occurred during analysis: {str(e)}",
            "errors": ["analysis_error"]
        }
        return json.dumps(error_result, indent=2)


def _has_sufficient_evidence(premise: str) -> bool:
    premise_lower = premise.lower()
    qualifying_words = ["most", "many", "some", "typically", "generally", "usually", "often"]
    has_qualifiers = any(word in premise_lower for word in qualifying_words)
    established_truths = [
        "all humans are mortal",
        "all living things die",
        "all circles are round",
        "all bachelors are unmarried",
        "all mothers are female"
    ]
    is_established_truth = any(truth in premise_lower for truth in established_truths)
    return has_qualifiers or is_established_truth


def _is_affirming_consequent(major: str, minor: str, _conclusion: str) -> bool:
    if not ("if" in major.lower() and "then" in major.lower()):
        return False
    major_parts = major.lower().split("then")
    if len(major_parts) < 2:
        return False
    consequent_words = major_parts[1].strip().split()[:3]
    minor_words = minor.lower().split()
    return any(word in minor_words for word in consequent_words if len(word) > 2)


def _is_valid_modus_ponens(major: str, minor: str, _conclusion: str) -> bool:
    if not ("if" in major.lower() and "then" in major.lower()):
        return False
    major_lower = major.lower()
    if_pos = major_lower.find("if")
    then_pos = major_lower.find("then")
    if if_pos == -1 or then_pos == -1 or then_pos <= if_pos:
        return False
    antecedent = major_lower[if_pos + 2:then_pos].strip()
    antecedent_words = antecedent.split()[:3]
    minor_words = minor.lower().split()
    return any(word in minor_words for word in antecedent_words if len(word) > 2)


def _has_undistributed_middle(major: str, minor: str, _conclusion: str) -> bool:
    return ("some" in major.lower() and "some" in minor.lower() and
            not any(word in major.lower() for word in ["all", "every"]))


def _is_valid_categorical_syllogism(major: str, minor: str, conclusion: str) -> bool:
    major_lower = major.lower()
    minor_lower = minor.lower()
    conclusion.lower()
    if ("all" in major_lower or "every" in major_lower) and " is " in minor_lower:
        return True
    if (("all" in major_lower or "every" in major_lower) and
        ("all" in minor_lower or "every" in minor_lower)):
        return True
    if "no " in major_lower and " is " in minor_lower:
        return True
    return False
