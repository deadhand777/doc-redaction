from unittest.mock import Mock

import pytest
from strands import Agent
from strands.models import BedrockModel
from strands.models.ollama import OllamaModel
from strands_tools import calculator, current_time, file_read, file_write

from doc_redaction.agent import bedrock_model, create_agent
from doc_redaction.utils import MissingArgumentError


class TestCreateAgent:
    """Test suite for the create_agent function."""

    def test_create_agent_with_default_model(self):
        """Test creating an agent with default model and system prompt."""
        system_prompt = "You are a helpful assistant."

        agent = create_agent(system_prompt=system_prompt)

        assert isinstance(agent, Agent)
        assert agent.system_prompt == system_prompt

    def test_create_agent_with_custom_bedrock_model(self):
        """Test creating an agent with a custom BedrockModel."""
        system_prompt = "You are a document analyzer."
        custom_model = BedrockModel(
            model_id="eu.anthropic.claude-sonnet-4-20250514-v1:0",
            region_name="eu-central-1",
            temperature=0.5,
        )

        agent = create_agent(system_prompt=system_prompt, model=custom_model)

        assert isinstance(agent, Agent)
        assert agent.system_prompt == system_prompt
        assert agent.model == custom_model

    def test_create_agent_with_ollama_model(self):
        """Test creating an agent with an OllamaModel."""
        system_prompt = "You are a data processor."
        ollama_model = OllamaModel(model_id="llama3.2", host="http://localhost:11434")

        agent = create_agent(system_prompt=system_prompt, model=ollama_model)

        assert isinstance(agent, Agent)
        assert agent.system_prompt == system_prompt
        assert agent.model == ollama_model

    def test_create_agent_with_tool_objects(self):
        """Test creating an agent with tool objects."""
        system_prompt = "You are a function-calling assistant."
        mock_tool = Mock()
        tools = [mock_tool]
        agent = create_agent(system_prompt=system_prompt, tools=tools)

        assert isinstance(agent, Agent)
        assert agent.system_prompt == system_prompt

    def test_create_agent_with_empty_tools_list(self):
        """Test creating an agent with an empty tools list."""
        system_prompt = "You are a basic assistant."
        tools = []
        agent = create_agent(system_prompt=system_prompt, tools=tools)

        assert isinstance(agent, Agent)
        assert agent.system_prompt == system_prompt

    def test_create_agent_with_none_tools(self):
        """Test creating an agent with tools=None."""
        system_prompt = "You are a simple assistant."
        agent = create_agent(system_prompt=system_prompt, tools=None)

        assert isinstance(agent, Agent)
        assert agent.system_prompt == system_prompt

    def test_create_agent_raises_error_for_missing_system_prompt(self):
        """Test that MissingArgumentError is raised when system_prompt is not provided."""
        with pytest.raises(MissingArgumentError, match="system_prompt must be provided"):
            create_agent(system_prompt="")

    def test_create_agent_uses_default_model_when_none_provided(self):
        """Test that the default bedrock_model is used when model is None."""
        system_prompt = "You are a default model assistant."
        agent = create_agent(system_prompt=system_prompt, model=None)

        assert isinstance(agent, Agent)
        assert agent.model == bedrock_model

    def test_create_agent_with_all_parameters(self):
        """Test creating an agent with all parameters specified."""
        system_prompt = "You are a fully configured assistant."
        custom_model = BedrockModel(
            model_id="eu.anthropic.claude-sonnet-4-20250514-v1:0",
            region_name="eu-central-1",
            temperature=0,
        )
        tools = [file_read, file_write, current_time]

        agent = create_agent(system_prompt=system_prompt, model=custom_model, tools=tools)

        assert isinstance(agent, Agent)
        assert agent.system_prompt == system_prompt
        assert agent.model == custom_model

    @pytest.mark.parametrize("invalid_prompt", ["", None])
    def test_create_agent_invalid_system_prompt_parametrized(self, invalid_prompt):
        """Parametrized test for invalid system prompts."""
        with pytest.raises(MissingArgumentError, match="system_prompt must be provided"):
            create_agent(system_prompt=invalid_prompt)

    def test_create_agent_type_annotations(self):
        """Test that the function accepts the expected types."""
        system_prompt = "You are a type-checked assistant."
        bedrock_model_instance = BedrockModel(model_id="eu.anthropic.claude-sonnet-4-20250514-v1:0", region_name="eu-central-1")
        ollama_model_instance = OllamaModel(model_id="llama3.2", host="http://localhost:11434")

        # Should work with BedrockModel
        agent1 = create_agent(system_prompt, bedrock_model_instance)
        assert isinstance(agent1, Agent)

        # Should work with OllamaModel
        agent2 = create_agent(system_prompt, ollama_model_instance)
        assert isinstance(agent2, Agent)

    def test_create_agent_returns_agent_instance(self):
        """Test that the function returns an Agent instance."""
        system_prompt = "You are a return value test assistant."
        result = create_agent(system_prompt=system_prompt)

        assert isinstance(result, Agent)
        assert hasattr(result, "system_prompt")
        assert hasattr(result, "model")
        assert result.system_prompt == system_prompt

    def test_create_agent_with_ollama_model_and_tools(self):
        """Test creating an agent with OllamaModel and tools."""
        system_prompt = "You are a tool-enabled assistant."
        ollama_model = OllamaModel(model_id="llama3.2", host="http://localhost:11434")
        tools = [file_read, calculator]
        agent = create_agent(system_prompt=system_prompt, model=ollama_model, tools=tools)

        assert isinstance(agent, Agent)
        assert agent.system_prompt == system_prompt
        assert agent.model == ollama_model
