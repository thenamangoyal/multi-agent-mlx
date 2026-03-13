"""Base agent wrapping Agno with OpenAILike for local MLX server."""

from __future__ import annotations

from agno.agent import Agent
from agno.models.openai import OpenAILike

from factory.config import Config


def create_agent(
    name: str,
    instructions: list[str],
    tools: list,
    config: Config,
) -> Agent:
    """Create an Agno agent pointed at the local mlx_lm server."""
    model = OpenAILike(
        id=config.server.model,  # must match what mlx_lm.server reports at /v1/models
        base_url=f"http://{config.server.host}:{config.server.port}/v1",
        api_key="not-needed",
        max_tokens=config.agent.max_tokens_per_turn,
    )
    return Agent(
        name=name,
        model=model,
        instructions=instructions,
        tools=tools,
        markdown=True,
    )
