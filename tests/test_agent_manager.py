import pytest
from code_puppy.agents.agent_manager import get_available_agents, load_agent_config


def test_list_agents_includes_piglet():
    """Test that the piglet agent is included in the list of available agents."""
    agents = get_available_agents()
    agent_names = list(agents.keys())
    
    # Verify that piglet is in the list of available agents
    assert "piglet" in agent_names


def test_load_piglet_agent():
    """Test that we can load the piglet agent configuration."""
    # Load the piglet agent
    agent = load_agent_config("piglet")
    
    # Verify it's a valid agent
    assert agent is not None
    assert agent.name == "piglet"
    assert "oink" in agent.description.lower()
