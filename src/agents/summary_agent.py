from langchain.agents import create_agent
from src.model import bedrock_model

SUMMARIZATION_PROMPT = """
You are summarizing a technical conversation. Create a concise bullet-point summary that:
- Focuses on code changes, architectural decisions, and technical solutions
- Preserves specific function names, file paths, and configuration details
- Omits conversational elements and focuses on actionable information
- Uses technical terminology appropriate for software development

Format as bullet points without conversational language.
"""


def custom_summarization_agent():
    """Returns a summarization agent that summarizes messages in an easy-to-understand format."""
    try:
        return create_agent(
            model=bedrock_model,
            tools=[],
            system_prompt=SUMMARIZATION_PROMPT,
        )
    except Exception as e:
        raise RuntimeError(f"Error creating summarization agent: {e}")