"""Tests for agent tools functionality."""

from unittest.mock import MagicMock
from code_puppy.tools.agent_tools import (
    register_list_agents, 
    register_invoke_agent,
    AgentInvocation
)


class TestAgentTools:
    """Test suite for agent tools."""

    def test_list_agents_tool(self):
        """Test that list_agents tool registers correctly."""
        # Create a mock agent to register tools to
        mock_agent = MagicMock()

        # Register the tool - this should not raise an exception
        register_list_agents(mock_agent)

    def test_invoke_agent_tool(self):
        """Test that invoke_agent tool registers correctly."""
        # Create a mock agent to register tools to
        mock_agent = MagicMock()

        # Register the tool - this should not raise an exception
        register_invoke_agent(mock_agent)

    def test_agent_invocation_model(self):
        """Test that AgentInvocation model works correctly."""
        # Create an AgentInvocation instance
        invocation = AgentInvocation(agent_name="test-agent", prompt="test prompt")
        
        # Verify the attributes
        assert invocation.agent_name == "test-agent"
        assert invocation.prompt == "test prompt"

    def test_agent_invocation_from_string(self):
        """Test that AgentInvocation can be created from JSON string."""
        # This would test the string parsing functionality if we had a way to mock the context
        pass
