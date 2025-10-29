"""
Demo Scenario Generator
Uses AI to generate customized dbt demo scenarios
"""

from typing import Optional, List
from pydantic import BaseModel, Field
import json
import re
from pathlib import Path

from .providers import AIProvider, get_ai_provider


# Data models for the demo scenario
class DataSource(BaseModel):
    """Source table definition"""
    name: str
    description: str
    columns: List[str]


class StagingModel(BaseModel):
    """Staging model definition"""
    name: str
    description: str
    source_table: str


class IntermediateModel(BaseModel):
    """Intermediate model definition"""
    name: str
    description: str
    depends_on: List[str]


class MartModel(BaseModel):
    """Mart model definition"""
    name: str
    description: str
    depends_on: List[str]
    is_incremental: bool = False


class Metric(BaseModel):
    """Business metric definition"""
    name: str
    description: str
    calculation: str


class DemoScenario(BaseModel):
    """Complete demo scenario"""
    demo_overview: str = Field(description="High-level demo summary")
    business_context: str = Field(description="Business problem being solved")
    data_sources: List[DataSource] = Field(description="Source tables")
    staging_models: List[StagingModel] = Field(description="Staging layer models")
    intermediate_models: List[IntermediateModel] = Field(description="Intermediate layer models")
    marts_models: List[MartModel] = Field(description="Marts layer models")
    key_metrics: List[Metric] = Field(description="Business metrics to showcase")
    talking_points: List[str] = Field(description="Key demo talking points")

    # Metadata
    company_name: Optional[str] = None
    industry: Optional[str] = None


def clean_json_response(text: str) -> str:
    """
    Clean common JSON syntax errors from AI responses

    Args:
        text: Raw JSON text that may have syntax errors

    Returns:
        Cleaned JSON text
    """
    # Remove trailing commas before closing braces/brackets
    text = re.sub(r',(\s*[}\]])', r'\1', text)

    # Replace single quotes with double quotes (but be careful with apostrophes in text)
    # This is a simple approach - only replace single quotes that look like JSON delimiters
    text = re.sub(r"'([a-zA-Z_][a-zA-Z0-9_]*)'(\s*):", r'"\1"\2:', text)  # Keys

    # Remove comments (// or /* */)
    text = re.sub(r'//.*?\n', '\n', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    return text


def load_prompt_template(template_name: str) -> str:
    """
    Load a prompt template from the templates directory

    Args:
        template_name: Name of the template file (without .txt extension)

    Returns:
        Template content as string
    """
    template_path = Path(__file__).parent.parent.parent / "templates" / "prompts" / f"{template_name}.txt"
    with open(template_path, 'r') as f:
        return f.read()


def load_additional_prompt_guidance(exclude: Optional[List[str]] = None) -> str:
    """
    Aggregate any extra guidance files dropped into templates/prompts.

    Args:
        exclude: Optional list of template stems to ignore

    Returns:
        Combined guidance text or empty string if none found
    """
    exclude = set(exclude or [])
    prompts_dir = Path(__file__).parent.parent.parent / "templates" / "prompts"
    guidance_sections: List[str] = []

    for path in sorted(prompts_dir.glob("*.txt")):
        stem = path.stem
        if stem in exclude:
            continue
        try:
            content = path.read_text().strip()
        except Exception:
            continue
        if not content:
            continue
        section_title = stem.replace('_', ' ').title()
        guidance_sections.append(f"{section_title}:\n{content}")

    if not guidance_sections:
        return ""

    return "\n\n".join(guidance_sections)


def generate_demo_scenario(
    company_name: str,
    industry: str,
    ai_provider: AIProvider,
    discovery_notes: Optional[str] = None,
    pain_points: Optional[str] = None,
    include_semantic_layer: bool = False,
    regenerate_feedback: Optional[str] = None
) -> DemoScenario:
    """
    Generate a demo scenario using AI

    Args:
        company_name: Prospect company name
        industry: Industry/vertical
        ai_provider: Configured AI provider instance
        discovery_notes: Optional discovery call notes
        pain_points: Optional pain points
        include_semantic_layer: Whether to include Semantic Layer
        regenerate_feedback: Optional feedback for regeneration

    Returns:
        Generated DemoScenario instance

    Raises:
        ValueError: If AI response cannot be parsed
        Exception: If AI generation fails
    """
    # Load prompt templates
    system_prompt = load_prompt_template("demo_scenario_system")
    additional_guidance = load_additional_prompt_guidance(
        exclude=["demo_scenario_system", "demo_scenario_user"]
    )
    if additional_guidance:
        system_prompt = (
            f"{system_prompt}\n\n"
            f"Additional internal guidelines to follow:\n{additional_guidance}"
        )
    user_prompt_template = load_prompt_template("demo_scenario_user")

    # Build optional sections
    discovery_section = ""
    if discovery_notes:
        discovery_section = f"\n**Discovery Notes (READ CAREFULLY - This defines what the demo should be about):**\n{discovery_notes}\n"

    pain_points_section = ""
    if pain_points:
        pain_points_section = f"\n**Technical Pain Points:**\n{pain_points}\n"

    semantic_section = ""
    semantic_talking_points = ""
    if include_semantic_layer:
        semantic_section = "\n**Note:** This demo should include Semantic Layer examples (metrics and semantic models)."
        semantic_talking_points = '\n7. **Semantic Layer**: How to define metrics once and use everywhere'

    incremental_section = ""
    if not include_semantic_layer:  # Keep it simpler without semantic layer
        incremental_section = "   - At least ONE mart model should be incremental (for demonstrating incremental materialization)"

    # Add regeneration feedback if provided
    regenerate_section = ""
    if regenerate_feedback:
        regenerate_section = f"\n\n**FEEDBACK FROM PREVIOUS GENERATION:**\n{regenerate_feedback}\n\nPlease adjust the scenario based on this feedback.\n"

    # Format the user prompt
    user_prompt = user_prompt_template.format(
        company_name=company_name,
        industry=industry,
        discovery_notes_section=discovery_section,
        pain_points_section=pain_points_section,
        semantic_layer_section=semantic_section,
        semantic_layer_talking_points=semantic_talking_points,
        incremental_section=incremental_section
    ) + regenerate_section

    # Generate scenario using AI
    try:
        response = ai_provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt
        )

        # Parse JSON response
        # Try to extract JSON from markdown code blocks if present
        response_text = response.strip()
        if "```json" in response_text:
            # Extract JSON from code block
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            # Generic code block
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()

        # Clean common JSON syntax errors
        response_text = clean_json_response(response_text)

        # Try to parse JSON with multiple attempts
        scenario_data = None
        parse_error = None

        try:
            # First attempt: direct parsing
            scenario_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            parse_error = e
            # Second attempt: try to find the first { and last }
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_subset = response_text[start_idx:end_idx + 1]
                    json_subset = clean_json_response(json_subset)
                    scenario_data = json.loads(json_subset)
            except json.JSONDecodeError:
                pass

        if scenario_data is None:
            # If all parsing attempts failed, raise detailed error
            error_msg = f"Failed to parse AI response as JSON: {parse_error}"
            error_msg += f"\n\nCleaned response (first 1000 chars):\n{response_text[:1000]}"
            raise ValueError(error_msg)

        # Create DemoScenario instance
        scenario = DemoScenario(**scenario_data)

        # Add metadata
        scenario.company_name = company_name
        scenario.industry = industry

        return scenario

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse AI response as JSON: {e}\n\nResponse (first 500 chars): {response[:500]}")
    except Exception as e:
        raise Exception(f"Failed to generate demo scenario: {e}")


def regenerate_scenario(
    original_scenario: DemoScenario,
    feedback: str,
    ai_provider: AIProvider,
    discovery_notes: Optional[str] = None,
    pain_points: Optional[str] = None,
    include_semantic_layer: bool = False
) -> DemoScenario:
    """
    Regenerate a scenario with user feedback

    Args:
        original_scenario: The original scenario to modify
        feedback: User feedback for changes
        ai_provider: Configured AI provider instance
        discovery_notes: Optional discovery call notes
        pain_points: Optional pain points
        include_semantic_layer: Whether to include Semantic Layer

    Returns:
        Regenerated DemoScenario instance
    """
    return generate_demo_scenario(
        company_name=original_scenario.company_name,
        industry=original_scenario.industry,
        ai_provider=ai_provider,
        discovery_notes=discovery_notes,
        pain_points=pain_points,
        include_semantic_layer=include_semantic_layer,
        regenerate_feedback=feedback
    )
