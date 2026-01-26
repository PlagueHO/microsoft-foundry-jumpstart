"""
Initiative Analyzer - AI-powered backlog item analysis and initiative association.

This application analyzes CSV backlog items against organizational initiatives
using Microsoft Foundry's language models to generate comprehensive markdown reports
organized by initiative.

Features:
- CSV-based backlog and initiative processing
- AI-powered semantic analysis and initiative matching
- Confidence threshold filtering for high-quality associations
- Initiative-centric markdown report generation
- Detailed impact analysis and strategic recommendations
- Configurable logging levels for debugging and monitoring
"""

import argparse
import csv
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
from pydantic import BaseModel

# Configure logging for debugging and monitoring (default configuration)
# This will be updated by configure_logging() function based on verbose setting
logger = logging.getLogger(__name__)


def chunk_backlog_items(backlog_items: List['BacklogItem'], chunk_size: int = 20) -> List[List['BacklogItem']]:
    """
    Split backlog items into chunks of specified size for batch processing.

    Args:
        backlog_items: List of BacklogItem objects to chunk
        chunk_size: Maximum number of items per chunk (default: 20)

    Returns:
        List of chunks, each containing up to chunk_size BacklogItem objects

    Raises:
        ValueError: If chunk_size is less than 1
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be at least 1")

    if not backlog_items:
        return []

    chunks: List[List[BacklogItem]] = []
    for i in range(0, len(backlog_items), chunk_size):
        chunk = backlog_items[i:i + chunk_size]
        chunks.append(chunk)

    logger.debug("Split %d backlog items into %d chunks of size %d",
                len(backlog_items), len(chunks), chunk_size)

    return chunks


@dataclass
class BacklogItem:
    """Represents a single backlog item with its metadata."""

    category: str
    initiative: str
    title: str
    goal: str
    stream: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert backlog item to dictionary format."""
        return {
            'category': self.category,
            'initiative': self.initiative,
            'title': self.title,
            'goal': self.goal,
            'stream': self.stream
        }


@dataclass
class Initiative:
    """Represents an organizational initiative."""

    area: str
    title: str
    details: str
    description: str
    kpi: str
    current_state: str
    solutions: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert initiative to dictionary format."""
        return {
            'area': self.area,
            'title': self.title,
            'details': self.details,
            'description': self.description,
            'kpi': self.kpi,
            'current_state': self.current_state,
            'solutions': self.solutions
        }


@dataclass
class BacklogItemAssociation:
    """Represents a backlog item associated with an initiative."""

    backlog_item: BacklogItem
    confidence: int
    impact_analysis: str


@dataclass
class InitiativeReport:
    """Represents a complete initiative report with associated backlog items."""

    initiative: Initiative
    associated_items: List[BacklogItemAssociation]
    confidence_threshold: int
    collective_impact: str
    strategic_recommendations: str


@dataclass
class EnrichedBacklogItem:
    """Represents a backlog item enriched with AI analysis."""

    original_item: BacklogItem
    matched_initiative: Optional[str]
    secondary_initiatives: List[str]
    category_confidence: int
    initiative_confidence: int
    impact_analysis: str
    detailed_analysis: str
    resource_implications: str
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert enriched backlog item to dictionary format for CSV output."""
        result = self.original_item.to_dict()
        result.update({
            'initiative': self.matched_initiative or self.original_item.initiative,
            'impact': self.impact_analysis,
            'analysis': self.detailed_analysis,
            'category_confidence': self.category_confidence,
            'initiative_confidence': self.initiative_confidence,
            'initiative_details': self.matched_initiative or '',
            'resource_implications': self.resource_implications,
            'recommendations': '; '.join(self.recommendations)
        })
        return result


@dataclass
class InitiativeBacklogAssociation:
    """Represents the result of analyzing backlog items for a specific initiative."""

    backlog_item_title: str
    initiative_title: str  # Add initiative title to track which initiative this association belongs to
    relevance_score: int
    impact_analysis: str
    strategic_value: str
    implementation_synergies: str
    confidence_reasoning: str

    def to_backlog_item_association(self, backlog_item: BacklogItem) -> 'BacklogItemAssociation':
        """Convert to BacklogItemAssociation for compatibility with existing code."""
        return BacklogItemAssociation(
            backlog_item=backlog_item,
            confidence=self.relevance_score,
            impact_analysis=self.impact_analysis
        )


# Pydantic models for structured outputs
class BacklogAnalysisResult(BaseModel):
    """Structured output model for backlog item analysis."""
    primary_initiative: Optional[str]
    secondary_initiatives: List[str]
    category_confidence: int
    initiative_confidence: int
    impact_analysis: str
    detailed_analysis: str
    resource_implications: str
    recommendations: List[str]


class InitiativeRelevanceItem(BaseModel):
    """Model for a single relevant backlog item in initiative analysis."""
    backlog_item_title: str
    relevance_score: int
    impact_analysis: str
    strategic_value: str
    implementation_synergies: str
    confidence_reasoning: str


class InitiativeRelevanceResult(BaseModel):
    """Structured output model for initiative relevance analysis."""
    relevant_items: List[InitiativeRelevanceItem]


def configure_logging(verbose_level: str = 'ERROR') -> None:
    """
    Configure application logging based on verbosity level.

    Args:
        verbose_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Raises:
        ValueError: If invalid logging level provided
    """
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if verbose_level.upper() not in valid_levels:
        raise ValueError(f"Invalid logging level '{verbose_level}'. Valid options: {', '.join(valid_levels)}")

    log_level = getattr(logging, verbose_level.upper())
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True  # Override any existing configuration
    )

    # Set Azure SDK logging to WARNING to reduce noise unless DEBUG is selected
    if verbose_level.upper() != 'DEBUG':
        logging.getLogger('azure').setLevel(logging.WARNING)
        logging.getLogger('openai').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for the initiative analyzer."""
    parser = argparse.ArgumentParser(
        description="Initiative Analyzer - Analyze backlog items against organizational initiatives using AI",
        epilog="Example: python initiative_analyzer.py --backlog backlog.csv --initiatives initiatives.csv --output initiative_reports/",
    )
    parser.add_argument(
        "--backlog",
        type=str,
        required=True,
        help="Path to CSV file containing backlog items"
    )
    parser.add_argument(
        "--initiatives",
        type=str,
        required=True,
        help="Path to CSV file containing organizational initiatives"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output directory for initiative markdown reports"
    )
    parser.add_argument(
        "--confidence-threshold",
        type=int,
        default=80,
        help="Minimum confidence threshold for including backlog-initiative associations (default: 80)"
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        help="Override PROJECT_ENDPOINT environment variable"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Override MODEL_DEPLOYMENT_NAME environment variable"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default=None,
        help="Set logging verbosity level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: ERROR"
    )
    parser.add_argument(
        "--filter-backlog-title",
        type=str,
        help="Filter backlog items by title using a regex pattern (e.g., 'onboard.*' to match titles containing 'onboard')"
    )
    parser.add_argument(
        "--filter-initiatives-title",
        type=str,
        help="Filter initiatives by title using a regex pattern (e.g., 'security.*' to match titles containing 'security')"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=20,
        help="Number of backlog items to process per batch for initiative-centric analysis (default: 20)"
    )
    parser.add_argument(
        "--processing-mode",
        type=str,
        choices=['item-centric', 'initiative-centric'],
        default='initiative-centric',
        help="""Processing approach:
        - item-centric: Legacy mode that analyzes each backlog item individually (less efficient)
        - initiative-centric: Recommended mode that analyzes batches of items per initiative (80%% fewer API calls)
        Default: initiative-centric"""
    )
    parser.add_argument(
        "--additional-instructions",
        type=str,
        help="""Additional instructions to include in the AI analysis prompt.
        Example: 'Exclude backlog items that would require very detailed and specific engineering understanding of the code base to implement'"""
    )
    return parser.parse_args()


def load_environment() -> None:
    """Load environment variables from .env file if available."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
        logger.info("Environment variables loaded from .env file")
    except ImportError:
        logger.info("python-dotenv not available, using system environment variables")


def initialize_client(endpoint: Optional[str] = None) -> AzureOpenAI:
    """
    Initialize and test the Azure AI Projects client and get Azure OpenAI client.

    Args:
        endpoint: Optional override for PROJECT_ENDPOINT

    Returns:
        Azure OpenAI client from AI Projects SDK

    Raises:
        SystemExit: If connection fails or required environment variables are missing
    """
    # Get project endpoint from argument or environment
    project_endpoint = endpoint or os.environ.get("PROJECT_ENDPOINT")
    if not project_endpoint:
        logger.error(
            "PROJECT_ENDPOINT environment variable is required or must be provided via --endpoint argument"
        )
        print(
            "Error: PROJECT_ENDPOINT environment variable is required or must be provided via --endpoint argument"
        )
        sys.exit(1)

    # Configure authentication using DefaultAzureCredential
    credential = DefaultAzureCredential()

    try:
        # Create the Azure AI Projects client
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=credential
        )

        # Get Azure OpenAI client for inference operations (handle dynamic attribute for type checkers)
        inference_attr = getattr(project_client, "inference", None)
        if inference_attr is None:
            raise RuntimeError(
                "AIProjectClient does not expose 'inference' operations. Ensure the 'azure-ai-projects' package version supports inference."
            )
        inference_ops = cast(Any, inference_attr)
        client = inference_ops.get_azure_openai_client(api_version="2024-10-21")

        logger.info("Created Azure OpenAI client via AIProjectClient for endpoint: %s", project_endpoint)
        print(f"Connected to Microsoft Foundry project: {project_endpoint}")

        return client

    except Exception as e:
        logger.error("Failed to initialize client: %s", e)
        print(f"Connection failed: {e}")
        print("Please check your PROJECT_ENDPOINT and authentication.")
        sys.exit(1)


def load_backlog_items(file_path: str, title_filter: Optional[str] = None) -> List[BacklogItem]:
    """
    Load backlog items from CSV file.

    Args:
        file_path: Path to the backlog CSV file
        title_filter: Optional regex pattern to filter backlog items by title

    Returns:
        List of BacklogItem objects (filtered by title if pattern provided)

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If required columns are missing or regex pattern is invalid
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Backlog file not found: {file_path}")

    # Compile regex pattern if provided
    title_pattern = None
    if title_filter:
        try:
            title_pattern = re.compile(title_filter, re.IGNORECASE)
            logger.info("Using title filter pattern: %s", title_filter)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{title_filter}': {e}") from e

    required_columns = ['category', 'title', 'goal', 'stream']

    backlog_items: List[BacklogItem] = []
    filtered_count = 0

    with open(file_path, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        # Validate required columns (handle Optional fieldnames)
        fieldnames = list(reader.fieldnames or [])
        missing_columns = [col for col in required_columns if col not in fieldnames]
        if missing_columns:
            raise ValueError(f"Missing required columns in backlog CSV: {missing_columns}")

        for row_num, row in enumerate(reader, start=2):
            try:
                title = row['title'].strip()

                # Apply title filter if provided
                if title_pattern and not title_pattern.search(title):
                    filtered_count += 1
                    continue

                # Create backlog item
                item = BacklogItem(
                    category=row['category'].strip(),
                    initiative=row.get('initiative', '').strip(),
                    title=title,
                    goal=row['goal'].strip(),
                    stream=row['stream'].strip()
                )

                backlog_items.append(item)

            except Exception as e:
                logger.warning("Error processing row %d in backlog CSV: %s", row_num, e)
                continue

    total_items = len(backlog_items) + filtered_count
    if title_pattern:
        logger.info("Loaded %d backlog items from %s (filtered %d items out of %d total)",
                   len(backlog_items), file_path, filtered_count, total_items)
        print(f"Applied title filter '{title_filter}': {len(backlog_items)} items match (filtered out {filtered_count})")
    else:
        logger.info("Loaded %d backlog items from %s", len(backlog_items), file_path)

    return backlog_items


def load_initiatives(file_path: str, title_filter: Optional[str] = None) -> List[Initiative]:
    """
    Load initiatives from CSV file.

    Args:
        file_path: Path to the initiatives CSV file
        title_filter: Optional regex pattern to filter initiatives by title

    Returns:
        List of Initiative objects (filtered by title if pattern provided)

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If required columns are missing or regex pattern is invalid
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Initiatives file not found: {file_path}")

    # Compile regex pattern if provided
    title_pattern = None
    if title_filter:
        try:
            title_pattern = re.compile(title_filter, re.IGNORECASE)
            logger.info("Using initiatives title filter: %s", title_filter)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{title_filter}': {e}")

    required_columns = ['area', 'title', 'details', 'description', 'kpi', 'current_state', 'solutions']

    initiatives: List[Initiative] = []
    filtered_count = 0

    with open(file_path, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        # Validate required columns (handle Optional fieldnames)
        fieldnames = list(reader.fieldnames or [])
        missing_columns = [col for col in required_columns if col not in fieldnames]
        if missing_columns:
            raise ValueError(f"Missing required columns in initiatives CSV: {missing_columns}")

        for row_num, row in enumerate(reader, start=2):
            try:
                # Apply title filter if provided
                if title_pattern and not title_pattern.search(row['title']):
                    filtered_count += 1
                    continue

                initiative = Initiative(
                    area=row['area'].strip(),
                    title=row['title'].strip(),
                    details=row['details'].strip(),
                    description=row['description'].strip(),
                    kpi=row['kpi'].strip(),
                    current_state=row['current_state'].strip(),
                    solutions=row['solutions'].strip()
                )

                initiatives.append(initiative)

            except Exception as e:
                logger.warning("Error processing row %d in initiatives CSV: %s", row_num, e)
                continue

    total_initiatives = len(initiatives) + filtered_count
    if title_pattern:
        logger.info("Loaded %d initiatives from %s (filtered by title: kept %d, filtered out %d of %d total)",
                   len(initiatives), file_path, len(initiatives), filtered_count, total_initiatives)
        print(f"Applied initiatives title filter '{title_filter}': {len(initiatives)} initiatives match (filtered out {filtered_count})")
    else:
        logger.info("Loaded %d initiatives from %s", len(initiatives), file_path)
    return initiatives


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be used as a filename.

    Args:
        filename: The string to sanitize

    Returns:
        str: A sanitized filename
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')
    # Limit length to avoid filesystem issues
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    return sanitized


def generate_initiative_markdown_report(initiative_report: InitiativeReport) -> str:
    """
    Generate a markdown report for a single initiative.

    Args:
        initiative_report: The initiative report data

    Returns:
        str: The markdown content for the report
    """
    initiative = initiative_report.initiative
    items = initiative_report.associated_items

    # Generate frontmatter
    markdown = f"""---
area: {initiative.area}
title: {initiative.title}
confidence_threshold: {initiative_report.confidence_threshold}
total_associated_items: {len(items)}
---

# {initiative.title}

## Initiative Overview

**Area:** {initiative.area}
**Current Status:** {initiative.current_state}

{initiative.details}

{initiative.description}

## Key Performance Indicators

{initiative.kpi}

## Proposed Solutions

{initiative.solutions}

## Associated Backlog Items

The following backlog items have been associated with this initiative based on semantic analysis and goal alignment:

| Title | Goal | Category | Stream | Confidence | Impact Analysis |
|-------|------|----------|--------|------------|-----------------|
"""

    # Add table rows for each associated backlog item
    for association in items:
        item = association.backlog_item
        markdown += f"| {item.title} | {item.goal} | {item.category} | {item.stream} | {association.confidence}% | {association.impact_analysis} |\n"

    # Add collective impact assessment
    markdown += f"""
## Collective Impact Assessment

{initiative_report.collective_impact}

## Strategic Recommendations

{initiative_report.strategic_recommendations}
"""

    return markdown


def organize_backlog_by_initiative(
    enriched_items: List[EnrichedBacklogItem],
    initiatives: List[Initiative],
    confidence_threshold: int
) -> List[InitiativeReport]:
    """
    Organize enriched backlog items by initiative and generate reports.

    Args:
        enriched_items: List of enriched backlog items
        initiatives: List of all initiatives
        confidence_threshold: Minimum confidence for including associations

    Returns:
        List[InitiativeReport]: Reports for initiatives with associated items
    """
    # Create a mapping of initiative titles to initiative objects
    initiative_map = {init.title: init for init in initiatives}

    # Create a case-insensitive mapping for fuzzy matching
    initiative_map_lower = {init.title.lower().strip(): init for init in initiatives}

    logger.info("Created initiative map with %d initiatives: %s",
                len(initiative_map), list(initiative_map.keys()))

    # Group backlog items by their matched initiatives
    initiative_associations: Dict[str, List[BacklogItemAssociation]] = {}

    logger.info("Processing %d enriched items with confidence threshold %d",
                len(enriched_items), confidence_threshold)

    for enriched_item in enriched_items:
        logger.debug(
            "Processing enriched item: title='%s', matched_initiative='%s', confidence=%d",
            enriched_item.original_item.title,
            enriched_item.matched_initiative,
            enriched_item.initiative_confidence,
        )

        # Only include items that meet the confidence threshold
        if (
            enriched_item.matched_initiative
            and enriched_item.initiative_confidence >= confidence_threshold
        ):
            initiative_title = enriched_item.matched_initiative
            logger.debug(
                "Item '%s' meets threshold - matched to initiative: '%s'",
                enriched_item.original_item.title,
                initiative_title,
            )

            # Try exact match first
            matched_initiative = None
            if initiative_title in initiative_map:
                matched_initiative = initiative_map[initiative_title]
                logger.debug("EXACT match found for initiative: '%s'", initiative_title)
            else:
                # Try case-insensitive match
                title_lower = initiative_title.lower().strip()
                if title_lower in initiative_map_lower:
                    matched_initiative = initiative_map_lower[title_lower]
                    logger.info(
                        "FUZZY match found: '%s' -> '%s'",
                        initiative_title,
                        matched_initiative.title,
                    )
                else:
                    logger.warning(
                        "NO match found for initiative: '%s'. Available: %s",
                        initiative_title,
                        list(initiative_map.keys()),
                    )
                    continue

            # Use the canonical initiative title from the matched initiative
            canonical_title = matched_initiative.title

            if canonical_title not in initiative_associations:
                initiative_associations[canonical_title] = []

            association = BacklogItemAssociation(
                backlog_item=enriched_item.original_item,
                confidence=enriched_item.initiative_confidence,
                impact_analysis=enriched_item.impact_analysis,
            )

            initiative_associations[canonical_title].append(association)
            logger.debug(
                "Added association for initiative '%s' (total: %d)",
                canonical_title,
                len(initiative_associations[canonical_title]),
            )
        else:
            logger.debug(
                "Item '%s' does not meet threshold: matched='%s', confidence=%d, threshold=%d",
                enriched_item.original_item.title,
                enriched_item.matched_initiative,
                enriched_item.initiative_confidence,
                confidence_threshold,
            )

    logger.info("Grouped items into %d initiatives: %s",
                len(initiative_associations), list(initiative_associations.keys()))

    # Generate reports for initiatives with associated items
    reports = []

    for initiative_title, associations in initiative_associations.items():
        logger.info("Processing initiative '%s' with %d associations", initiative_title, len(associations))

        initiative = initiative_map[initiative_title]  # We know this exists now

        # Generate collective impact and recommendations using AI
        collective_impact = _generate_collective_impact_analysis(initiative, associations)
        strategic_recommendations = _generate_strategic_recommendations(initiative, associations)

        report = InitiativeReport(
            initiative=initiative,
            associated_items=associations,
            confidence_threshold=confidence_threshold,
            collective_impact=collective_impact,
            strategic_recommendations=strategic_recommendations
        )

        reports.append(report)
        logger.info("Generated report for initiative '%s' with %d items", initiative_title, len(associations))

    logger.info("Generated %d total reports", len(reports))
    return reports


def _generate_collective_impact_analysis(
    initiative: Initiative,
    associations: List[BacklogItemAssociation]
) -> str:
    """Generate collective impact analysis for multiple backlog items on an initiative."""
    if not associations:
        return "No associated backlog items meet the confidence threshold."

    # Basic analysis based on the number and types of items
    impact_text = (
        f"The {len(associations)} associated backlog items will collectively advance "
        f"this initiative through complementary approaches. "
    )

    # Analyze item categories
    categories = {assoc.backlog_item.category for assoc in associations}
    if len(categories) > 1:
        impact_text += (
            f"These items span {len(categories)} different categories "
            f"({', '.join(categories)}), providing a comprehensive approach to initiative advancement. "
        )

    # Analyze confidence levels
    avg_confidence = sum(assoc.confidence for assoc in associations) / len(associations)
    if avg_confidence > 75:
        impact_text += "The high confidence scores indicate strong strategic alignment across all items."
    elif avg_confidence > 60:
        impact_text += "The moderate to high confidence scores suggest good strategic fit for most items."
    else:
        impact_text += "The confidence scores suggest these items provide some strategic value but may need closer review."

    return impact_text


def _generate_strategic_recommendations(
    initiative: Initiative,
    associations: List[BacklogItemAssociation]
) -> str:
    """Generate strategic recommendations for implementing associated backlog items."""
    if not associations:
        return "Consider identifying backlog items that could support this initiative."

    recommendations = (
        f"To maximize the success of the '{initiative.title}' initiative:\n\n"
        f"1. **Prioritize high-confidence items**: Focus on items with confidence scores above 70% for immediate impact.\n"
        f"2. **Coordinate implementation**: Ensure the {len(associations)} associated backlog items are implemented in a coordinated manner.\n"
        f"3. **Track KPI alignment**: Monitor progress against the initiative's KPIs: {initiative.kpi}\n"
        f"4. **Resource allocation**: Ensure adequate resources are allocated across the {len(associations)} associated items.\n"
    )

    return recommendations


def save_initiative_reports(reports: List[InitiativeReport], output_dir: str) -> None:
    """
    Save initiative reports as markdown files.

    Args:
        reports: List of initiative reports to save
        output_dir: Directory to save the reports

    Raises:
        IOError: If unable to create directory or save files
    """
    if not reports:
        print("No initiative reports to save.")
        return

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    saved_count = 0

    for report in reports:
        try:
            # Generate filename from initiative title
            filename = sanitize_filename(f"{report.initiative.title}.md")
            file_path = output_path / filename

            # Generate markdown content
            markdown_content = generate_initiative_markdown_report(report)

            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            saved_count += 1
            logger.info("Saved initiative report: %s", file_path)

        except Exception as e:
            logger.error("Failed to save report for initiative '%s': %s",
                        report.initiative.title, e)
            continue

    print(f"✅ Saved {saved_count} initiative reports to {output_dir}")
    if saved_count < len(reports):
        print(f"⚠️  Failed to save {len(reports) - saved_count} reports")


def _analyze_item_centric(
    backlog_items: List[BacklogItem],
    initiatives: List[Initiative],
    client: AzureOpenAI,
    model_name: str,
    confidence_threshold: int = 60,
    additional_instructions: Optional[str] = None
) -> List[EnrichedBacklogItem]:
    """
    Legacy item-centric processing mode - analyze each backlog item individually.

    This approach is less efficient for large datasets but maintained for compatibility.
    Now uses structured outputs for more reliable parsing.

    Args:
        additional_instructions: Optional additional instructions to include in the prompt
    """
    logger.info("Starting legacy item-centric analysis for %d items using model: %s", len(backlog_items), model_name)

    enriched_items: List[EnrichedBacklogItem] = []

    # Prepare the initiative details for the LLM context
    initiative_context = "\n".join([
        f"- {initiative.title}: {initiative.description}"
        for initiative in initiatives
    ])

    for i, item in enumerate(backlog_items, 1):
        try:
            logger.info("Analyzing item %d/%d: %s", i, len(backlog_items), item.title)

            # Create the enhanced system prompt with additional instructions
            system_prompt = f"""You are an expert business analyst tasked with categorizing software project backlog items into business initiatives.

AVAILABLE INITIATIVES:
{initiative_context}

Your task is to analyze the given backlog item and determine:
1. Which initiative it best aligns with (primary_initiative) - use exact initiative title or null
2. Any secondary initiatives it might support (secondary_initiatives) - list of exact initiative titles
3. Your confidence level for the category match (0-100)
4. Your confidence level for the initiative match (0-100)
5. A brief analysis of the expected impact
6. Detailed analysis of strategic alignment and value
7. Resource implications and implementation considerations
8. Strategic recommendations for prioritization

ANALYSIS GUIDELINES:
- Base analysis on semantic alignment between backlog goals and initiative objectives
- Consider both direct and indirect impacts on strategic goals
- Evaluate category compatibility and resource requirements
- If no initiative fits well, set primary_initiative to null and confidence scores below 50"""

            # Add additional instructions if provided
            if additional_instructions:
                system_prompt += f"\n\nADDITIONAL INSTRUCTIONS:\n{additional_instructions}"

            system_prompt += "\n\nProvide your analysis in the structured format specified."

            user_prompt = f"""BACKLOG ITEM TO ANALYZE:
Title: {item.title}
Goal: {item.goal}
Category: {item.category}
Stream: {item.stream}"""

            # Use structured outputs with Pydantic model
            completion = client.beta.chat.completions.parse(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=BacklogAnalysisResult,
                temperature=0.1,
                max_tokens=1000
            )

            # Extract the parsed result
            analysis_result = completion.choices[0].message.parsed

            if analysis_result is None:
                logger.error("Failed to parse structured output for item '%s'", item.title)
                # Create a default analysis
                analysis_result = BacklogAnalysisResult(
                    primary_initiative=None,
                    secondary_initiatives=[],
                    category_confidence=0,
                    initiative_confidence=0,
                    impact_analysis="Failed to analyze due to parsing error",
                    detailed_analysis="Structured output parsing failed",
                    resource_implications="Not analyzed due to error",
                    recommendations=[]
                )

            # Create enriched backlog item
            enriched_item = EnrichedBacklogItem(
                original_item=item,
                matched_initiative=analysis_result.primary_initiative,
                secondary_initiatives=analysis_result.secondary_initiatives,
                category_confidence=analysis_result.category_confidence,
                initiative_confidence=analysis_result.initiative_confidence,
                impact_analysis=analysis_result.impact_analysis,
                detailed_analysis=analysis_result.detailed_analysis,
                resource_implications=analysis_result.resource_implications,
                recommendations=analysis_result.recommendations
            )

            enriched_items.append(enriched_item)

            # Log progress
            if i % 10 == 0:
                logger.info("Processed %d/%d items", i, len(backlog_items))

        except Exception as e:
            logger.error("Error analyzing item '%s': %s", item.title, e)
            # Create a default enriched item for failed analysis
            enriched_item = EnrichedBacklogItem(
                original_item=item,
                matched_initiative=None,
                secondary_initiatives=[],
                category_confidence=0,
                initiative_confidence=0,
                impact_analysis=f"Analysis failed: {str(e)}",
                detailed_analysis="Analysis failed",
                resource_implications="Not analyzed due to error",
                recommendations=[]
            )
            enriched_items.append(enriched_item)

    logger.info("Completed legacy item-centric analysis of %d backlog items", len(enriched_items))
    return enriched_items


def _convert_associations_to_enriched_items(
    all_associations: List[InitiativeBacklogAssociation],
    confidence_threshold: int,
    initiatives: List[Initiative],
    backlog_items: List[BacklogItem]
) -> List[EnrichedBacklogItem]:
    """
    Convert InitiativeBacklogAssociation objects to EnrichedBacklogItem objects.

    For items with multiple associations, keeps the highest relevance score match.
    """
    # Create lookup maps
    backlog_lookup = {item.title: item for item in backlog_items}

    # Group associations by backlog item title
    item_associations: Dict[str, List[InitiativeBacklogAssociation]] = {}

    for association in all_associations:
        if association.relevance_score >= confidence_threshold:
            item_title = association.backlog_item_title
            if item_title not in item_associations:
                item_associations[item_title] = []
            item_associations[item_title].append(association)

    # Convert to EnrichedBacklogItem objects
    enriched_items: List[EnrichedBacklogItem] = []

    logger.info("Converting %d unique backlog items with associations above threshold %d",
               len(item_associations), confidence_threshold)

    for item_title, associations in item_associations.items():
        # Sort by relevance score and take the highest
        associations.sort(key=lambda x: x.relevance_score, reverse=True)
        best_association = associations[0]

        # Find the actual backlog item
        backlog_item = backlog_lookup.get(item_title)
        if not backlog_item:
            logger.warning("Could not find backlog item '%s' in original data", item_title)
            continue

        # We have the initiative title from the association
        matched_initiative_title = best_association.initiative_title

        # Collect secondary initiatives from other high-confidence matches
        secondary_initiatives = []
        for assoc in associations[1:]:
            if assoc.relevance_score >= confidence_threshold * 0.8:  # 80% of threshold
                secondary_initiatives.append(assoc.initiative_title)

        # Create enriched item with proper initiative title
        enriched_item = EnrichedBacklogItem(
            original_item=backlog_item,
            matched_initiative=matched_initiative_title,
            secondary_initiatives=secondary_initiatives,
            category_confidence=best_association.relevance_score,
            initiative_confidence=best_association.relevance_score,
            impact_analysis=best_association.impact_analysis,
            detailed_analysis=best_association.strategic_value,
            resource_implications=best_association.implementation_synergies,
            recommendations=[]
        )

        enriched_items.append(enriched_item)
        logger.debug("Created enriched item for '%s' -> '%s' (confidence: %d)",
                    item_title, matched_initiative_title, best_association.relevance_score)

        # Additional debug logging to trace the issue
        if matched_initiative_title:
            logger.info("ENRICHED ITEM DEBUG: Item '%s' matched to initiative '%s' with confidence %d",
                       item_title, matched_initiative_title, best_association.relevance_score)
        else:
            logger.warning("ENRICHED ITEM DEBUG: Item '%s' has NO matched initiative", item_title)

    logger.info("Converted %d associations to %d enriched items", len(all_associations), len(enriched_items))
    return enriched_items


def _analyze_initiative_centric(
    backlog_items: List[BacklogItem],
    initiatives: List[Initiative],
    client: AzureOpenAI,
    model_name: str,
    chunk_size: int,
    confidence_threshold: int = 80
) -> List[EnrichedBacklogItem]:
    """
    Initiative-centric processing mode - analyze batches of items for each initiative.

    This approach is more efficient and provides better LLM context for large datasets.
    """
    logger.info("Starting initiative-centric analysis for %d items across %d initiatives using model: %s",
                len(backlog_items), len(initiatives), model_name)
    logger.info("Using chunk size: %d", chunk_size)

    # Process each initiative against chunks of backlog items
    all_associations: List[InitiativeBacklogAssociation] = []

    for initiative in initiatives:
        logger.info("Processing initiative: %s", initiative.title)

        # Chunk the backlog items for this initiative
        chunks = chunk_backlog_items(backlog_items, chunk_size)

        for chunk_idx, chunk in enumerate(chunks, 1):
            logger.info("Processing chunk %d/%d for initiative '%s' (%d items)",
                       chunk_idx, len(chunks), initiative.title, len(chunk))

            try:
                chunk_associations = process_initiative_chunk(client, initiative, chunk, model_name)
                all_associations.extend(chunk_associations)
                logger.info("Found %d relevant items in chunk %d", len(chunk_associations), chunk_idx)

            except Exception as e:
                logger.error("Error processing chunk %d for initiative '%s': %s",
                           chunk_idx, initiative.title, e)
                continue

    # Aggregate and deduplicate associations
    logger.info("Aggregating %d total associations", len(all_associations))
    enriched_items = _convert_associations_to_enriched_items(all_associations, confidence_threshold, initiatives, backlog_items)

    logger.info("Completed initiative-centric analysis: %d enriched items", len(enriched_items))
    return enriched_items


def analyze_initiative_associations(
    backlog_file: str,
    initiatives_file: str,
    output_dir: str,
    client: AzureOpenAI,
    model_name: str,
    confidence_threshold: int = 60,
    backlog_title_filter: Optional[str] = None,
    initiatives_title_filter: Optional[str] = None,
    args: Optional[argparse.Namespace] = None
) -> None:
    """
    Analyze backlog items against initiatives and generate initiative reports.

    Args:
        backlog_file: Path to backlog CSV file
        initiatives_file: Path to initiatives CSV file
        output_dir: Directory for output markdown reports
        client: Azure OpenAI client
        model_name: Model deployment name
        confidence_threshold: Minimum confidence for including associations
        backlog_title_filter: Optional regex pattern to filter backlog items by title
        initiatives_title_filter: Optional regex pattern to filter initiatives by title
        args: Command line arguments (optional, for processing mode)
    """
    try:
        # Load data
        print("Loading backlog items...")
        backlog_items = load_backlog_items(backlog_file, backlog_title_filter)

        print("Loading initiatives...")
        initiatives = load_initiatives(initiatives_file, initiatives_title_filter)

        if not backlog_items:
            print("No backlog items found. Please check your backlog CSV file.")
            return

        if not initiatives:
            print("No initiatives found. Please check your initiatives CSV file.")
            return

        print(f"Analyzing {len(backlog_items)} backlog items against {len(initiatives)} initiatives...")
        print(f"Using confidence threshold: {confidence_threshold}%")

        # Determine processing mode
        processing_mode = 'initiative-centric'  # Default
        if args and hasattr(args, 'processing_mode'):
            processing_mode = args.processing_mode
            print(f"Using processing mode: {processing_mode}")

        # Process items based on mode
        if processing_mode == 'item-centric':
            print("⚠️  Using legacy item-centric mode - less efficient for large datasets")
            additional_instructions = getattr(args, 'additional_instructions', None) if args else None
            enriched_items = _analyze_item_centric(backlog_items, initiatives, client, model_name, confidence_threshold, additional_instructions)
        else:
            chunk_size = 20  # Default
            if args and hasattr(args, 'chunk_size'):
                chunk_size = args.chunk_size
            print(f"Using initiative-centric mode with chunk size: {chunk_size}")
            enriched_items = _analyze_initiative_centric(backlog_items, initiatives, client, model_name, chunk_size, confidence_threshold)

        qualifying_items = 0
        qualifying_items_debug = []  # Track which items qualify for debugging
        for item in enriched_items:
            if (item.matched_initiative and
                item.initiative_confidence >= confidence_threshold):
                qualifying_items += 1
                qualifying_items_debug.append({
                    'title': item.original_item.title,
                    'matched_initiative': item.matched_initiative,
                    'confidence': item.initiative_confidence
                })

        # Debug logging to show what items qualify and their initiative titles
        logger.info("DEBUG: Qualifying items summary (showing first 5):")
        unique_initiatives = set()
        for debug_item in qualifying_items_debug[:5]:  # Show first 5 for debugging
            logger.info("  - Item '%s' -> Initiative '%s' (confidence: %d)",
                       debug_item['title'], debug_item['matched_initiative'], debug_item['confidence'])
            unique_initiatives.add(debug_item['matched_initiative'])

        logger.info("DEBUG: Unique AI-generated initiative titles: %s", list(unique_initiatives))

        print("\n📊 Analysis Summary:")
        print(f"   • Total items analyzed: {len(enriched_items)}")
        print(f"   • Items meeting threshold: {qualifying_items}")
        print(f"   • Confidence threshold: {confidence_threshold}%")

        # Generate initiative reports
        if enriched_items:
            print("\n📝 Generating initiative reports...")
            reports = organize_backlog_by_initiative(enriched_items, initiatives, confidence_threshold)

            if reports:
                print(f"Generated {len(reports)} initiative reports")
                save_initiative_reports(reports, output_dir)

                # Print summary of generated reports
                print("\n📋 Generated Reports:")
                for report in reports:
                    print(f"   • {report.initiative.title}: {len(report.associated_items)} items")
            else:
                print("❌ No initiative reports generated. Try lowering the confidence threshold.")
        else:
            print("❌ No items were successfully analyzed.")

    except Exception as e:
        logger.error("Error in initiative analysis: %s", e)
        print(f"Error processing analysis: {e}")
        sys.exit(1)


def get_backlog_analysis_system_prompt() -> str:
    """
    Get the system prompt for backlog analysis and initiative association.

    Returns:
        str: System prompt for the backlog analyzer
    """
    return """You are a Strategic Backlog Analyzer, designed to help organizations understand how their backlog items align with strategic initiatives. Your role is to:

**Core Responsibilities:**
1. Analyze backlog items for strategic alignment with organizational initiatives
2. Provide confidence scores for category classification and initiative matching
3. Generate actionable insights about impact and resource implications
4. Recommend priority and implementation approaches based on strategic fit

**Analysis Framework:**
- Use semantic analysis to match backlog goals with initiative objectives
- Evaluate category alignment between backlog items and initiative areas
- Assess timeline compatibility and resource requirements
- Consider both direct and indirect impacts on strategic goals

**Output Requirements:**
- Provide clear, actionable analysis for each backlog item
- Include specific confidence scores (0-100) for categorization and initiative matching
- Generate timeline alignment analysis and resource implications
- Offer strategic recommendations for prioritization and implementation
- Return results in JSON format with the exact structure specified

**Quality Standards:**
- Base analysis on factual alignment between goals and initiatives
- Provide transparent reasoning for all associations and confidence scores
- Consider organizational context and resource constraints
- Focus on maximizing strategic value through proper backlog prioritization

Remember: Your goal is to help organizations make data-driven decisions about backlog prioritization by clearly showing how each item contributes to strategic initiatives."""


def get_initiative_analysis_system_prompt() -> str:
    """
    Get the system prompt for initiative-centric backlog analysis.

    Returns:
        str: System prompt for the initiative-focused analyzer
    """
    return """You are an Initiative-Focused Strategic Analyzer, designed to help organizations identify which backlog items will most effectively advance specific organizational initiatives. Your role is to:

**Core Responsibilities:**
1. Analyze backlog items specifically for their relevance to a single, well-defined initiative
2. Provide accurate relevance scores (0-100) based on strategic alignment and impact potential
3. Generate detailed impact analysis showing how each item advances the initiative
4. Assess strategic value and implementation synergies within the initiative context
5. Provide clear reasoning for all relevance assessments

**Analysis Framework:**
- Focus analysis on the specific initiative context, goals, and success criteria
- Evaluate direct alignment between backlog item goals and initiative objectives
- Assess how backlog item completion advances the initiative's KPIs and proposed solutions
- Consider implementation timing, resource requirements, and synergies with other initiative work
- Prioritize items that provide measurable advancement toward initiative success

**Scoring Guidelines:**
- 90-100: Direct, high-impact advancement of core initiative objectives
- 80-89: Strong alignment with significant impact on initiative success
- 70-79: Good alignment with moderate impact on initiative goals
- 60-69: Some alignment with minor but measurable impact
- 40-59: Weak alignment with minimal impact
- Below 40: No meaningful contribution to initiative (exclude from results)

**Output Requirements:**
- Only include backlog items with relevance scores of 40 or higher
- Provide specific, actionable impact analysis for each relevant item
- Explain strategic value in the context of the initiative's goals and current state
- Identify implementation synergies and dependencies with other initiative work
- Include clear reasoning for all relevance scores
- Return results in the exact JSON format specified

**Quality Standards:**
- Base analysis on factual alignment between backlog goals and initiative objectives
- Consider the initiative's current state, proposed solutions, and success metrics
- Focus on measurable advancement and strategic value creation
- Provide transparent reasoning that stakeholders can understand and act upon

Remember: Your goal is to help organizations maximize initiative success by identifying the most strategically valuable backlog items for each initiative."""


def analyze_initiative_relevance(
    client: AzureOpenAI,
    initiative: Initiative,
    backlog_items: List[BacklogItem],
    model_name: str
) -> List[InitiativeBacklogAssociation]:
    """
    Analyze a chunk of backlog items for relevance to a specific initiative using structured outputs.

    Args:
        client: Azure OpenAI client
        initiative: The initiative to analyze against
        backlog_items: List of backlog items to evaluate
        model_name: Model deployment name

    Returns:
        List of InitiativeBacklogAssociation objects for relevant items

    Raises:
        RuntimeError: If the AI analysis fails
    """
    try:
        # Create system prompt for initiative-centric analysis
        system_prompt = get_initiative_analysis_system_prompt()

        # Format backlog items for analysis
        backlog_text = ""
        for i, item in enumerate(backlog_items, 1):
            backlog_text += f"""
Item {i}:
- Title: {item.title}
- Category: {item.category}
- Goal: {item.goal}
- Stream: {item.stream}
"""

        # Create user prompt for initiative-focused analysis
        user_prompt = f"""
Analyze these {len(backlog_items)} backlog items for their relevance to the following initiative:

INITIATIVE CONTEXT:
- Area: {initiative.area}
- Title: {initiative.title}
- Details: {initiative.details}
- Description: {initiative.description}
- KPIs: {initiative.kpi}
- Current State: {initiative.current_state}
- Proposed Solutions: {initiative.solutions}

BACKLOG ITEMS TO ANALYZE:
{backlog_text}

For each backlog item, determine its relevance to this specific initiative. Only include items with relevance scores of 40 or higher.

Focus on:
1. Direct alignment between backlog item goals and initiative objectives
2. How completion of the backlog item advances the initiative's KPIs
3. Strategic fit within the initiative's area and proposed solutions
4. Implementation timing and resource synergies
"""

        logger.info("Analyzing %d backlog items for initiative '%s' using model: %s with structured outputs",
                   len(backlog_items), initiative.title, model_name)

        # Use structured outputs with Pydantic model
        completion = client.beta.chat.completions.parse(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=InitiativeRelevanceResult,
            temperature=0.1,
            max_tokens=2000
        )

        # Extract the parsed result
        analysis_result = completion.choices[0].message.parsed

        if analysis_result is None:
            logger.error("Failed to parse structured output for initiative '%s'", initiative.title)
            return []

        # Convert to InitiativeBacklogAssociation objects
        associations = []

        for item_analysis in analysis_result.relevant_items:
            try:
                association = InitiativeBacklogAssociation(
                    backlog_item_title=item_analysis.backlog_item_title,
                    initiative_title=initiative.title,
                    relevance_score=item_analysis.relevance_score,
                    impact_analysis=item_analysis.impact_analysis,
                    strategic_value=item_analysis.strategic_value,
                    implementation_synergies=item_analysis.implementation_synergies,
                    confidence_reasoning=item_analysis.confidence_reasoning
                )
                associations.append(association)
            except (ValueError, TypeError) as e:
                logger.warning("Failed to parse item analysis for initiative '%s': %s", initiative.title, e)
                continue

        logger.info("Found %d relevant items for initiative '%s'", len(associations), initiative.title)
        return associations

    except Exception as e:
        logger.error("Failed to analyze initiative '%s': %s", initiative.title, e)
        raise RuntimeError(f"Unable to analyze initiative relevance: {e}") from e


def aggregate_initiative_associations(
    initiative: Initiative,
    association_batches: List[List[InitiativeBacklogAssociation]],
    backlog_items: List[BacklogItem],
    confidence_threshold: int = 60
) -> List[BacklogItemAssociation]:
    """
    Aggregate and deduplicate association results from multiple chunks.

    Args:
        initiative: The initiative being analyzed
        association_batches: List of association lists from different chunks
        backlog_items: Original backlog items for lookup
        confidence_threshold: Minimum confidence for inclusion

    Returns:
        List of BacklogItemAssociation objects above threshold
    """
    # Create lookup map for backlog items by title
    backlog_lookup = {item.title: item for item in backlog_items}

    # Collect all associations and deduplicate by title
    association_map: Dict[str, InitiativeBacklogAssociation] = {}

    for batch in association_batches:
        for association in batch:
            title = association.backlog_item_title

            # Keep highest scoring association if duplicates exist
            if title in association_map:
                if association.relevance_score > association_map[title].relevance_score:
                    association_map[title] = association
            else:
                association_map[title] = association

    # Filter by confidence threshold and convert to BacklogItemAssociation
    result_associations = []

    for title, association in association_map.items():
        if association.relevance_score >= confidence_threshold:
            # Find matching backlog item
            backlog_item = backlog_lookup.get(title)
            if backlog_item:
                backlog_association = association.to_backlog_item_association(backlog_item)
                result_associations.append(backlog_association)
            else:
                logger.warning("Could not find backlog item '%s' for initiative '%s'",
                             title, initiative.title)

    # Sort by confidence score descending
    result_associations.sort(key=lambda x: x.confidence, reverse=True)

    logger.info("Aggregated %d associations for initiative '%s' (threshold: %d)",
               len(result_associations), initiative.title, confidence_threshold)

    return result_associations


def process_initiative_chunk(
    client: AzureOpenAI,
    initiative: Initiative,
    backlog_chunk: List[BacklogItem],
    model_name: str
) -> List[InitiativeBacklogAssociation]:
    """
    Process a single chunk of backlog items for a specific initiative.

    This is a wrapper around analyze_initiative_relevance for single chunk processing.

    Args:
        client: Azure OpenAI client
        initiative: The initiative to analyze against
        backlog_chunk: Chunk of backlog items to process
        model_name: Model deployment name

    Returns:
        List of InitiativeBacklogAssociation objects for relevant items
    """
    try:
        associations = analyze_initiative_relevance(client, initiative, backlog_chunk, model_name)
        logger.debug("Processed chunk of %d items for initiative '%s', found %d associations",
                    len(backlog_chunk), initiative.title, len(associations))
        return associations
    except Exception as e:
        logger.error("Failed to process chunk for initiative '%s': %s", initiative.title, e)
        # Return empty list to allow processing to continue with other chunks
        return []


def analyze_backlog_item(
    client: AzureOpenAI,
    backlog_item: BacklogItem,
    initiatives: List[Initiative],
    model_name: str,
    additional_instructions: Optional[str] = None
) -> EnrichedBacklogItem:
    """
    Analyze a single backlog item against available initiatives using AI with structured outputs.

    Args:
        client: The Azure OpenAI client
        backlog_item: The backlog item to analyze
        initiatives: List of available initiatives
        model_name: The model deployment name
        additional_instructions: Optional additional instructions to include in the prompt

    Returns:
        EnrichedBacklogItem with AI analysis results

    Raises:
        RuntimeError: If the AI analysis fails
    """
    try:
        # Create enhanced system prompt with additional instructions
        system_prompt = get_backlog_analysis_system_prompt()

        # Add additional instructions if provided
        if additional_instructions:
            system_prompt += f"\n\nADDITIONAL INSTRUCTIONS:\n{additional_instructions}"

        # Format initiatives for analysis
        initiatives_text = ""
        for i, initiative in enumerate(initiatives, 1):
            initiatives_text += f"""
Initiative {i}:
- Area: {initiative.area}
- Title: {initiative.title}
- Details: {initiative.details}
- Description: {initiative.description}
- KPI: {initiative.kpi}
- Current State: {initiative.current_state}
- Solutions: {initiative.solutions}
"""

        # Create user prompt for analysis
        user_prompt = f"""
Analyze this backlog item against the provided initiatives:

BACKLOG ITEM:
- Category: {backlog_item.category}
- Title: {backlog_item.title}
- Goal: {backlog_item.goal}
- Stream: {backlog_item.stream}

AVAILABLE INITIATIVES:
{initiatives_text}

Focus on semantic alignment between the backlog item's goal and the initiative objectives. Consider:
1. How well the backlog goal aligns with initiative details and solutions
2. Category compatibility between backlog item and initiative area
3. Strategic impact and value creation
4. Resource considerations and implementation requirements

Provide confidence scores:
- category_confidence: 0-100 (how well the category aligns with initiative areas)
- initiative_confidence: 0-100 (strength of association with primary initiative)

Only suggest a primary_initiative if confidence is above 40. Use null if no good match exists.
"""
        logger.info("Analyzing backlog item '%s' using model: %s with structured outputs", backlog_item.title, model_name)

        # Use structured outputs with Pydantic model
        completion = client.beta.chat.completions.parse(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=BacklogAnalysisResult,
            temperature=0.1,
            max_tokens=1500
        )

        # Extract the parsed result
        analysis_result = completion.choices[0].message.parsed

        if analysis_result is None:
            logger.error("Failed to parse structured output for backlog item '%s'", backlog_item.title)
            # Create a default analysis
            analysis_result = BacklogAnalysisResult(
                primary_initiative=None,
                secondary_initiatives=[],
                category_confidence=0,
                initiative_confidence=0,
                impact_analysis="Failed to analyze due to parsing error",
                detailed_analysis="Structured output parsing failed",
                resource_implications="Not analyzed due to error",
                recommendations=[]
            )

        # Create enriched backlog item
        enriched_item = EnrichedBacklogItem(
            original_item=backlog_item,
            matched_initiative=analysis_result.primary_initiative,
            secondary_initiatives=analysis_result.secondary_initiatives,
            category_confidence=analysis_result.category_confidence,
            initiative_confidence=analysis_result.initiative_confidence,
            impact_analysis=analysis_result.impact_analysis,
            detailed_analysis=analysis_result.detailed_analysis,
            resource_implications=analysis_result.resource_implications,
            recommendations=analysis_result.recommendations
        )

        return enriched_item

    except Exception as e:
        logger.error("Failed to analyze backlog item '%s': %s", backlog_item.title, e)
        raise RuntimeError(f"Unable to analyze backlog item: {e}") from e


def main() -> None:
    """
    Main entry point for the Initiative Analyzer.
    """
    try:
        # Load environment variables from .env file first
        load_environment()

        # Parse command-line arguments
        args = parse_arguments()

        # Configure logging based on verbose flag and environment variable
        # Priority: command-line argument > environment variable > default (ERROR)
        verbose_level = args.verbose
        if verbose_level is None:
            verbose_level = os.environ.get('VERBOSE_LOGGING', 'ERROR').upper()

        try:
            configure_logging(verbose_level)
            logger.info("Logging configured at %s level", verbose_level)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

        # Get model deployment name from environment or command line
        model_deployment_name = args.model or os.environ.get(
            "MODEL_DEPLOYMENT_NAME", "gpt-4o"
        )

        print(f"Using model deployment: {model_deployment_name}")

        # Initialize the client
        client = initialize_client(endpoint=args.endpoint)

        # Perform initiative analysis and generate reports
        analyze_initiative_associations(
            args.backlog,
            args.initiatives,
            args.output,
            client,
            model_deployment_name,
            getattr(args, 'confidence_threshold', 80),
            getattr(args, 'filter_backlog_title', None),
            getattr(args, 'filter_initiatives_title', None),
            args
        )

    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error in main: %s", e)
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
