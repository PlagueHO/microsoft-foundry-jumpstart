"""
Fallacy detection tool for logical error identification.

This module provides the detect_fallacies function and supporting helpers
for identifying common logical fallacies in argumentative text.
"""
import json
import logging
import re
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


def detect_fallacies(text: str) -> str:
    """
    Identify logical fallacies in argumentative text.

    This function analyzes text to identify common logical fallacies and
    reasoning errors, providing detailed analysis and suggestions for
    improvement.

    Args:
        text: Text containing argument to analyze for fallacies

    Returns:
        JSON string containing detailed fallacy analysis including:
        - fallacies_detected: list of identified fallacy types
        - analysis: explanation of identified fallacies
        - confidence: confidence score (0.0 to 1.0) for detection accuracy
        - suggestions: recommendations for improving the argument
        - text_analyzed: the original text that was analyzed
    """
    try:
        analysis_result: Dict[str, Any] = {
            "text_analyzed": text,
            "fallacies_detected": [],
            "analysis": "",
            "confidence": 0.0,
            "suggestions": []
        }

        if not text or not text.strip():
            analysis_result["analysis"] = "No text provided for analysis."
            analysis_result["suggestions"].append("Provide argumentative text to analyze for logical fallacies.")
            return json.dumps(analysis_result, indent=2)

        text_lower = text.lower()
        fallacies_found: List[Dict[str, Any]] = []
        confidence_scores: List[float] = []

        # Check for each type of fallacy
        fallacy_checks = [
            _check_ad_hominem,
            _check_straw_man,
            _check_false_dichotomy,
            _check_hasty_generalization,
            _check_appeal_to_authority,
            _check_slippery_slope,
            _check_circular_reasoning,
            _check_red_herring,
            _check_bandwagon,
            _check_appeal_to_emotion
        ]

        for check_function in fallacy_checks:
            detected, confidence, description = check_function(text, text_lower)
            if detected:
                fallacies_found.append({
                    "type": detected,
                    "confidence": confidence,
                    "description": description
                })
                confidence_scores.append(confidence)

        # Populate results
        analysis_result["fallacies_detected"] = [f["type"] for f in fallacies_found]

        if fallacies_found:
            # Calculate overall confidence as average of individual confidences
            analysis_result["confidence"] = sum(confidence_scores) / len(confidence_scores)

            # Build detailed analysis
            fallacy_descriptions = [f["description"] for f in fallacies_found]
            analysis_result["analysis"] = (
                f"Analysis identified {len(fallacies_found)} logical fallac"
                f"{'y' if len(fallacies_found) == 1 else 'ies'}: "
                f"{', '.join(fallacy_descriptions)}"
            )

            # Generate suggestions based on detected fallacies
            analysis_result["suggestions"] = _generate_suggestions(fallacies_found)
        else:
            analysis_result["analysis"] = (
                "No obvious logical fallacies detected in the provided text. "
                "The argument structure appears logically sound, though this "
                "does not guarantee the truth of the premises or conclusion."
            )
            analysis_result["confidence"] = 0.8
            analysis_result["suggestions"] = [
                "Consider examining the evidence supporting your premises",
                "Look for potential counterarguments or alternative perspectives",
                "Verify that your conclusion logically follows from your premises"
            ]

        return json.dumps(analysis_result, indent=2)

    except Exception as e:
        logger.error("Error in detect_fallacies: %s", e)
        error_result: Dict[str, Any] = {
            "text_analyzed": text,
            "fallacies_detected": [],
            "analysis": f"Error occurred during fallacy analysis: {str(e)}",
            "confidence": 0.0,
            "suggestions": ["Please try again with different text"],
            "error": "analysis_error"
        }
        return json.dumps(error_result, indent=2)


def _check_ad_hominem(text: str, text_lower: str) -> Tuple[str, float, str]:
    """Check for ad hominem attacks."""
    ad_hominem_patterns = [
        r"you(?:'re| are) (?:stupid|dumb|ignorant|naive|biased|wrong|crazy)",
        r"(?:he|she|they) (?:is|are|'s) (?:stupid|dumb|ignorant|naive|biased|wrong|crazy)",
        r"that's (?:stupid|dumb|ignorant|ridiculous)",
        r"(?:shut up|you don't know)",
        r"(?:idiot|moron|fool)",
        r"you (?:clearly|obviously) don't understand"
    ]

    for pattern in ad_hominem_patterns:
        if re.search(pattern, text_lower):
            return (
                "ad_hominem",
                0.85,
                "Contains personal attacks rather than addressing the argument itself"
            )

    return "", 0.0, ""


def _check_straw_man(text: str, text_lower: str) -> Tuple[str, float, str]:
    """Check for straw man fallacy."""
    straw_man_indicators = [
        "so you're saying",
        "what you really mean is",
        "in other words",
        "you think that",
        "your position is basically"
    ]

    misrepresentation_words = [
        "extreme", "radical", "absurd", "ridiculous", "completely",
        "totally", "absolutely", "never", "always", "everyone", "no one"
    ]

    straw_man_score = 0.0
    for indicator in straw_man_indicators:
        if indicator in text_lower:
            straw_man_score += 0.3

    for word in misrepresentation_words:
        if word in text_lower:
            straw_man_score += 0.1

    if straw_man_score >= 0.4:
        return (
            "straw_man",
            min(straw_man_score, 0.9),
            "May be misrepresenting or oversimplifying the opposing position"
        )

    return "", 0.0, ""


def _check_false_dichotomy(text: str, text_lower: str) -> Tuple[str, float, str]:
    """Check for false dichotomy/false dilemma."""
    dichotomy_patterns = [
        r"(?:either|you (?:either|must)) .+ or .+",
        r"(?:only two|two choices|two options)",
        r"(?:you're either|it's either) .+ or .+",
        r"(?:if not .+, then|unless .+, then)"
    ]

    absolute_words = ["only", "must", "have to", "no choice", "no alternative"]

    for pattern in dichotomy_patterns:
        if re.search(pattern, text_lower):
            # Check for absolute language to increase confidence
            confidence = 0.7
            if any(word in text_lower for word in absolute_words):
                confidence = 0.85
            return (
                "false_dichotomy",
                confidence,
                "Presents only two options when more alternatives may exist"
            )

    return "", 0.0, ""


def _check_hasty_generalization(text: str, text_lower: str) -> Tuple[str, float, str]:
    """Check for hasty generalization."""
    generalization_words = [
        "all", "every", "everyone", "nobody", "no one", "never",
        "always", "everything", "nothing", "everywhere", "nowhere"
    ]

    # Look for sweeping statements
    hasty_indicators = [
        "all .+ are",
        "every .+ is",
        "no .+ ever",
        ".+ always .+",
        ".+ never .+"
    ]

    confidence = 0.0
    for word in generalization_words:
        if word in text_lower:
            confidence += 0.2

    for pattern in hasty_indicators:
        if re.search(pattern, text_lower):
            confidence += 0.4

    # Check if there's evidence or qualifying language
    evidence_words = [
        "studies show", "research indicates", "data suggests", "statistics",
        "most", "many", "some", "typically", "generally", "usually", "often"
    ]

    has_evidence = any(word in text_lower for word in evidence_words)

    if confidence >= 0.6 and not has_evidence:
        return (
            "hasty_generalization",
            min(confidence, 0.9),
            "Makes broad generalizations without sufficient evidence or qualifying language"
        )

    return "", 0.0, ""


def _check_appeal_to_authority(text: str, text_lower: str) -> Tuple[str, float, str]:
    """Check for inappropriate appeal to authority."""
    authority_patterns = [
        r"(?:expert|authority|scientist|doctor|professor) says?",
        r"according to (?:experts|authorities|scientists|doctors)",
        r"(?:famous|well-known|respected) .+ (?:says|believes|thinks)",
        r"(?:celebrity|actor|politician) .+ (?:endorses|supports|says)"
    ]

    weak_authority_indicators = [
        "celebrity", "actor", "politician", "famous person",
        "my friend", "someone told me", "i heard"
    ]

    for pattern in authority_patterns:
        if re.search(pattern, text_lower):
            confidence = 0.6
            # Higher confidence if it's clearly a weak authority
            if any(indicator in text_lower for indicator in weak_authority_indicators):
                confidence = 0.85
            return (
                "appeal_to_authority",
                confidence,
                "Relies on authority rather than evidence, or cites inappropriate authority"
            )

    return "", 0.0, ""


def _check_slippery_slope(text: str, text_lower: str) -> Tuple[str, float, str]:
    """Check for slippery slope fallacy."""
    slope_patterns = [
        r"if .+ then .+ will .+ and then",
        r"this will lead to .+ which will lead to",
        r"next thing you know",
        r"before you know it",
        r"this is just the (?:beginning|start|first step)",
        r"where will it end"
    ]

    chain_indicators = ["then", "which will", "leading to", "resulting in", "causing"]

    for pattern in slope_patterns:
        if re.search(pattern, text_lower):
            # Check for chain of consequences
            chain_count = sum(1 for indicator in chain_indicators if indicator in text_lower)
            confidence = 0.7 + min(chain_count * 0.1, 0.2)
            return (
                "slippery_slope",
                confidence,
                "Argues that one event will lead to a chain of negative consequences without evidence"
            )

    return "", 0.0, ""


def _check_circular_reasoning(text: str, text_lower: str) -> Tuple[str, float, str]:
    """Check for circular reasoning."""
    circular_patterns = [
        r"because (?:it is|they are|that's) (?:true|right|correct|the way it is)",
        r"(?:the bible|god|tradition) says so",
        r"that's just how (?:it is|things are|the world works)",
        r"because i said so",
        r"it's (?:true|right) because it's (?:true|right)"
    ]

    for pattern in circular_patterns:
        if re.search(pattern, text_lower):
            return (
                "circular_reasoning",
                0.8,
                "The reasoning is circular - the conclusion is used to support the premise"
            )

    return "", 0.0, ""


def _check_red_herring(text: str, text_lower: str) -> Tuple[str, float, str]:
    """Check for red herring fallacy."""
    distraction_phrases = [
        "but what about",
        "speaking of",
        "that reminds me",
        "by the way",
        "off topic but",
        "not to change the subject but"
    ]

    topic_shifts = [
        "anyway", "meanwhile", "on another note", "while we're at it",
        "that's another issue", "different topic"
    ]

    distraction_score = 0.0
    for phrase in distraction_phrases:
        if phrase in text_lower:
            distraction_score += 0.4

    for phrase in topic_shifts:
        if phrase in text_lower:
            distraction_score += 0.2

    if distraction_score >= 0.5:
        return (
            "red_herring",
            min(distraction_score + 0.3, 0.9),
            "Introduces irrelevant information that distracts from the main argument"
        )

    return "", 0.0, ""


def _check_bandwagon(text: str, text_lower: str) -> Tuple[str, float, str]:
    """Check for bandwagon/appeal to popularity fallacy."""
    bandwagon_patterns = [
        r"everyone (?:else |)(?:is doing|does|believes|thinks)",
        r"most people (?:believe|think|do|say)",
        r"(?:popular|common) opinion",
        r"(?:majority of|most) people",
        r"everyone knows",
        r"it's (?:popular|trendy|fashionable|cool)",
        r"join the crowd",
        r"don't be (?:left out|different)"
    ]

    for pattern in bandwagon_patterns:
        if re.search(pattern, text_lower):
            return (
                "bandwagon",
                0.8,
                "Appeals to popularity or what most people do/believe rather than evidence"
            )

    return "", 0.0, ""


def _check_appeal_to_emotion(text: str, text_lower: str) -> Tuple[str, float, str]:
    """Check for appeal to emotion fallacy."""
    emotional_words = [
        "terrible", "horrible", "awful", "disgusting", "outrageous",
        "wonderful", "amazing", "fantastic", "incredible", "devastating",
        "heartbreaking", "tragic", "shocking", "appalling"
    ]

    emotional_appeals = [
        "think of the children",
        "for your family",
        "people will (?:die|suffer)",
        "innocent (?:people|children|victims)",
        "you should be (?:ashamed|angry|outraged|scared)"
    ]

    emotion_score = 0.0
    for word in emotional_words:
        if word in text_lower:
            emotion_score += 0.2

    for pattern in emotional_appeals:
        if re.search(pattern, text_lower):
            emotion_score += 0.4

    if emotion_score >= 0.6:
        return (
            "appeal_to_emotion",
            min(emotion_score + 0.2, 0.9),
            "Relies primarily on emotional manipulation rather than logical reasoning"
        )

    return "", 0.0, ""


def _generate_suggestions(fallacies_found: List[Dict[str, Any]]) -> List[str]:
    """Generate improvement suggestions based on detected fallacies."""
    suggestions: List[str] = []
    fallacy_types = [f["type"] for f in fallacies_found]

    suggestion_map = {
        "ad_hominem": "Focus on addressing the argument itself rather than attacking the person making it",
        "straw_man": "Represent opposing viewpoints accurately and address their strongest form",
        "false_dichotomy": "Consider additional alternatives and middle-ground positions",
        "hasty_generalization": "Provide more evidence and use qualifying language (e.g., 'many', 'some', 'often')",
        "appeal_to_authority": "Cite relevant experts and provide supporting evidence beyond authority",
        "slippery_slope": "Provide evidence for each step in your chain of reasoning",
        "circular_reasoning": "Ensure your premises provide independent support for your conclusion",
        "red_herring": "Stay focused on the main topic and address relevant points directly",
        "bandwagon": "Base your argument on evidence and merit rather than popularity",
        "appeal_to_emotion": "Balance emotional content with logical reasoning and factual evidence"
    }

    for fallacy_type in fallacy_types:
        if fallacy_type in suggestion_map:
            suggestions.append(suggestion_map[fallacy_type])

    # Add general suggestions
    if len(fallacies_found) > 1:
        suggestions.append("Review your argument structure to ensure logical consistency throughout")

    suggestions.append("Consider potential counterarguments and address them proactively")

    return suggestions
