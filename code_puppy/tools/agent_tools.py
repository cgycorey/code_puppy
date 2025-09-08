# agent_tools.py

from typing import List
from pydantic import BaseModel
from pydantic_ai import RunContext

from code_puppy.messaging import (
    emit_info,
    emit_divider,
    emit_system_message,
    emit_error,
)
from code_puppy.tools.common import generate_group_id
from code_puppy.agents.agent_manager import get_available_agents, load_agent_config

# Import Agent from pydantic_ai to create temporary agents for invocation
from pydantic_ai import Agent
from code_puppy.model_factory import ModelFactory
from code_puppy.config import get_model_name
from code_puppy.process_dispatcher import ProcessDispatcher
from code_puppy.state_management import get_agent_state, agent_states, _agent_states_lock


class AgentInfo(BaseModel):
    """Information about an available agent."""
    name: str
    display_name: str


class ListAgentsOutput(BaseModel):
    """Output for the list_agents tool."""
    agents: List[AgentInfo]
    error: str | None = None


class AgentInvokeOutput(BaseModel):
    """Output for the invoke_agent tool."""
    response: str | None
    agent_name: str
    error: str | None = None


class SpawnAgentOutput(BaseModel):
    """Output for the spawn_agent tool."""
    agent_id: str
    agent_name: str
    error: str | None = None


class AgentStatusInfo(BaseModel):
    """Information about a running agent's status."""
    agent_id: str
    agent_name: str
    pid: int
    status: str
    start_time: str
    model: str | None = None


class CheckRunningAgentStatusOutput(BaseModel):
    """Output for the check_running_agent_status tool."""
    agent_id: str
    status: str | None = None
    pid: int | None = None
    error: str | None = None


class ListRunningAgentsOutput(BaseModel):
    """Output for the list_running_agents tool."""
    agents: List[AgentStatusInfo]
    error: str | None = None


def _list_agents(context: RunContext) -> ListAgentsOutput:
    """List all available sub-agents that can be invoked.
    
    Returns:
        ListAgentsOutput: A list of available agents with their names and display names.
    """
    group_id = generate_group_id("list_agents")
    
    emit_info(
        "\n[bold white on blue] LIST AGENTS [/bold white on blue]",
        message_group=group_id
    )
    emit_divider(message_group=group_id)
    
    try:
        # Get available agents from the agent manager
        agents_dict = get_available_agents()
        
        # Convert to list of AgentInfo objects
        agents = [
            AgentInfo(name=name, display_name=display_name)
            for name, display_name in agents_dict.items()
        ]
        
        # Display the agents in the console
        for agent in agents:
            emit_system_message(
                f"- [bold]{agent.name}[/bold]: {agent.display_name}", 
                message_group=group_id
            )
            
        emit_divider(message_group=group_id)
        return ListAgentsOutput(agents=agents)
        
    except Exception as e:
        error_msg = f"Error listing agents: {str(e)}"
        emit_error(error_msg, message_group=group_id)
        emit_divider(message_group=group_id)
        return ListAgentsOutput(agents=[], error=error_msg)


def _invoke_agent(context: RunContext, agent_name: str, prompt: str) -> AgentInvokeOutput:
    """Invoke a specific sub-agent with a given prompt.
    
    Args:
        agent_name: The name of the agent to invoke
        prompt: The prompt to send to the agent
        
    Returns:
        AgentInvokeOutput: The agent's response to the prompt
    """
    group_id = generate_group_id("invoke_agent", agent_name)
    
    emit_info(
        f"\n[bold white on blue] INVOKE AGENT [/bold white on blue] {agent_name}",
        message_group=group_id
    )
    emit_divider(message_group=group_id)
    emit_system_message(f"Prompt: {prompt}", message_group=group_id)
    emit_divider(message_group=group_id)
    
    try:
        # Load the specified agent config
        agent_config = load_agent_config(agent_name)
        
        # Get the current model for creating a temporary agent
        model_name = get_model_name()
        models_config = ModelFactory.load_config()
        model = ModelFactory.get_model(model_name, models_config)
        
        # Create a temporary agent instance to avoid interfering with current agent state
        instructions = agent_config.get_system_prompt()
        temp_agent = Agent(
            model=model,
            instructions=instructions,
            output_type=str,
            retries=3,
        )
        
        # Register the tools that the agent needs
        from code_puppy.tools import register_tools_for_agent
        agent_tools = agent_config.get_available_tools()
        
        # Avoid recursive tool registration - if the agent has the same tools
        # as the current agent, skip registration to prevent conflicts
        current_agent_tools = ["list_agents", "invoke_agent"]
        if set(agent_tools) != set(current_agent_tools):
            register_tools_for_agent(temp_agent, agent_tools)
        
        # Run the temporary agent with the provided prompt
        result = temp_agent.run_sync(prompt)
        
        # Extract the response from the result
        response = result.output
        
        emit_system_message(f"Response: {response}", message_group=group_id)
        emit_divider(message_group=group_id)
        
        return AgentInvokeOutput(response=response, agent_name=agent_name)
        
    except Exception as e:
        error_msg = f"Error invoking agent '{agent_name}': {str(e)}"
        emit_error(error_msg, message_group=group_id)
        emit_divider(message_group=group_id)
        return AgentInvokeOutput(response=None, agent_name=agent_name, error=error_msg)


def register_list_agents(agent):
    """Register the list_agents tool with the provided agent.
    
    Args:
        agent: The agent to register the tool with
    """
    @agent.tool
    def list_agents(context: RunContext) -> ListAgentsOutput:
        """List all available sub-agents that can be invoked.
        
        Returns:
            ListAgentsOutput: A list of available agents with their names and display names.
        """
        # Generate a group ID for this tool execution
        group_id = generate_group_id("list_agents")
        
        emit_info(
            "\n[bold white on blue] LIST AGENTS [/bold white on blue]",
            message_group=group_id
        )
        emit_divider(message_group=group_id)
        
        try:
            # Get available agents from the agent manager
            agents_dict = get_available_agents()
            
            # Convert to list of AgentInfo objects
            agents = [
                AgentInfo(name=name, display_name=display_name)
                for name, display_name in agents_dict.items()
            ]
            
            # Display the agents in the console
            for agent_item in agents:
                emit_system_message(
                    f"- [bold]{agent_item.name}[/bold]: {agent_item.display_name}", 
                    message_group=group_id
                )
                
            emit_divider(message_group=group_id)
            return ListAgentsOutput(agents=agents)
            
        except Exception as e:
            error_msg = f"Error listing agents: {str(e)}"
            emit_error(error_msg, message_group=group_id)
            emit_divider(message_group=group_id)
            return ListAgentsOutput(agents=[], error=error_msg)
        
    return list_agents


def register_invoke_agent(agent):
    """Register the invoke_agent tool with the provided agent.
    
    Args:
        agent: The agent to register the tool with
    """
    @agent.tool
    def invoke_agent(context: RunContext, agent_name: str, prompt: str) -> AgentInvokeOutput:
        """Invoke a specific sub-agent with a given prompt.
        
        Args:
            agent_name: The name of the agent to invoke
            prompt: The prompt to send to the agent
            
        Returns:
            AgentInvokeOutput: The agent's response to the prompt
        """
        # Generate a group ID for this tool execution
        group_id = generate_group_id("invoke_agent", agent_name)
        
        emit_info(
            f"\n[bold white on blue] INVOKE AGENT [/bold white on blue] {agent_name}",
            message_group=group_id
        )
        emit_divider(message_group=group_id)
        emit_system_message(f"Prompt: {prompt}", message_group=group_id)
        emit_divider(message_group=group_id)
        
        try:
            # Load the specified agent config
            agent_config = load_agent_config(agent_name)
            
            # Get the current model for creating a temporary agent
            model_name = get_model_name()
            models_config = ModelFactory.load_config()

            # Only proceed if we have a valid model configuration
            if model_name not in models_config:
                raise ValueError(f"Model '{model_name}' not found in configuration")
                
            model = ModelFactory.get_model(model_name, models_config)
            
            # Create a temporary agent instance to avoid interfering with current agent state
            instructions = agent_config.get_system_prompt()
            temp_agent = Agent(
                model=model,
                instructions=instructions,
                output_type=str,
                retries=3,
            )
            
            # Register the tools that the agent needs
            from code_puppy.tools import register_tools_for_agent
            agent_tools = agent_config.get_available_tools()
            register_tools_for_agent(temp_agent, agent_tools)
            
            # Run the temporary agent with the provided prompt
            result = temp_agent.run_sync(prompt)
            
            # Extract the response from the result
            response = result.output
            
            emit_system_message(f"Response: {response}", message_group=group_id)
            emit_divider(message_group=group_id)
            
            return AgentInvokeOutput(response=response, agent_name=agent_name)
            
        except Exception as e:
            error_msg = f"Error invoking agent '{agent_name}': {str(e)}"
            emit_error(error_msg, message_group=group_id)
            emit_divider(message_group=group_id)
            return AgentInvokeOutput(response=None, agent_name=agent_name, error=error_msg)


def _spawn_agent(context: RunContext, agent_name: str, prompt: str, background: bool = True, visible: bool = False) -> SpawnAgentOutput:
    """Spawn a sub-agent as a child process.
    
    Args:
        agent_name: Name of the agent to invoke
        prompt: Prompt to send to the agent
        background: Whether to run in background (default True)
        visible: Whether to show the process terminal (default False)
        
    Returns:
        SpawnAgentOutput: The agent_id of the spawned process
    """
    group_id = generate_group_id("spawn_agent", agent_name)
    
    emit_info(
        f"\n[bold white on blue] SPAWN AGENT [/bold white on blue] {agent_name}",
        message_group=group_id
    )
    emit_divider(message_group=group_id)
    emit_system_message(f"Prompt: {prompt}", message_group=group_id)
    emit_system_message(f"Background: {background}, Visible: {visible}", message_group=group_id)
    emit_divider(message_group=group_id)
    
    try:
        # Create a process dispatcher instance
        dispatcher = ProcessDispatcher()
        
        # Spawn the agent process
        agent_id = dispatcher.spawn_agent(agent_name, prompt, background, visible)
        
        emit_system_message(f"Spawned agent with ID: {agent_id}", message_group=group_id)
        emit_divider(message_group=group_id)
        
        return SpawnAgentOutput(agent_id=agent_id, agent_name=agent_name)
        
    except Exception as e:
        error_msg = f"Error spawning agent '{agent_name}': {str(e)}"
        emit_error(error_msg, message_group=group_id)
        emit_divider(message_group=group_id)
        return SpawnAgentOutput(agent_id="", agent_name=agent_name, error=error_msg)


def run_agent_in_child_mode_sync(agent_name: str, prompt: str) -> str:
    """Run an agent in child mode synchronously and return its response.
    
    Args:
        agent_name: Name of the agent to invoke
        prompt: Prompt to send to the agent
        
    Returns:
        str: The agent's response
    """
    try:
        # Load the specified agent config
        agent_config = load_agent_config(agent_name)
        
        # Get the current model for creating a temporary agent
        model_name = get_model_name()
        models_config = ModelFactory.load_config()
        
        # Only proceed if we have a valid model configuration
        if model_name not in models_config:
            raise ValueError(f"Model '{model_name}' not found in configuration")
            
        model = ModelFactory.get_model(model_name, models_config)
        
        # Create a temporary event loop for this execution
        import asyncio
        import threading
        
        def run_async_code():
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Create a temporary agent instance to avoid interfering with current agent state
            instructions = agent_config.get_system_prompt()
            temp_agent = Agent(
                model=model,
                instructions=instructions,
                output_type=str,
                retries=3,
            )
            
            # Register the tools that the agent needs
            from code_puppy.tools import register_tools_for_agent
            agent_tools = agent_config.get_available_tools()
            register_tools_for_agent(temp_agent, agent_tools)
            
            # Run the temporary agent with the provided prompt
            result = loop.run_until_complete(temp_agent.run(prompt))
            
            # Extract the response from the result
            return result.output
        
        # Run in a separate thread to avoid event loop conflicts
        thread = threading.Thread(target=run_async_code)
        thread.start()
        thread.join()
        
        # We need to actually run the code and get the result
        # Let's create a new event loop in a separate thread
        loop = asyncio.new_event_loop()
        
        def run_in_thread():
            asyncio.set_event_loop(loop)
            instructions = agent_config.get_system_prompt()
            temp_agent = Agent(
                model=model,
                instructions=instructions,
                output_type=str,
                retries=3,
            )
            
            # Register the tools that the agent needs
            from code_puppy.tools import register_tools_for_agent
            agent_tools = agent_config.get_available_tools()
            register_tools_for_agent(temp_agent, agent_tools)
            
            return loop.run_until_complete(temp_agent.run(prompt))
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            result = future.result()
        
        response = result.output
        
        return response
        
    except Exception as e:
        raise Exception(f"Error running agent '{agent_name}' in child mode: {str(e)}")

async def run_agent_in_child_mode(agent_name: str, prompt: str) -> str:
    """Run an agent in child mode and return its response.
    
    Args:
        agent_name: Name of the agent to invoke
        prompt: Prompt to send to the agent
        
    Returns:
        str: The agent's response
    """
    try:
        # Load the specified agent config
        agent_config = load_agent_config(agent_name)
        
        # Get the current model for creating a temporary agent
        model_name = get_model_name()
        models_config = ModelFactory.load_config()
        
        # Only proceed if we have a valid model configuration
        if model_name not in models_config:
            raise ValueError(f"Model '{model_name}' not found in configuration")
            
        model = ModelFactory.get_model(model_name, models_config)
        
        # Create a temporary agent instance to avoid interfering with current agent state
        instructions = agent_config.get_system_prompt()
        temp_agent = Agent(
            model=model,
            instructions=instructions,
            output_type=str,
            retries=3,
        )
        
        # Register the tools that the agent needs
        from code_puppy.tools import register_tools_for_agent
        agent_tools = agent_config.get_available_tools()
        register_tools_for_agent(temp_agent, agent_tools)
        
        # Run the temporary agent with the provided prompt
        result = await temp_agent.run(prompt)
        
        # Extract the response from the result
        response = result.output
        
        return response
        
    except Exception as e:
        raise Exception(f"Error running agent '{agent_name}' in child mode: {str(e)}")
def _check_running_agent_status(context: RunContext, agent_id: str) -> CheckRunningAgentStatusOutput:
    """Check the status of a running agent process.
    
    Args:
        agent_id: The ID of the agent to check
        
    Returns:
        CheckRunningAgentStatusOutput: Status information for the agent
    """
    group_id = generate_group_id("check_running_agent_status", agent_id)
    
    emit_info(
        f"\n[bold white on blue] CHECK AGENT STATUS [/bold white on blue] {agent_id}",
        message_group=group_id
    )
    emit_divider(message_group=group_id)
    
    try:
        # Get the process status from agent states
        agent_state = get_agent_state(agent_id)
        pid = agent_state["pid"]
        status = agent_state["status"]
        
        emit_system_message(f"Agent ID: {agent_id}", message_group=group_id)
        emit_system_message(f"PID: {pid}", message_group=group_id)
        emit_system_message(f"Status: {status}", message_group=group_id)
        emit_divider(message_group=group_id)
        
        return CheckRunningAgentStatusOutput(agent_id=agent_id, status=status, pid=pid)
        
    except KeyError:
        error_msg = f"Agent with ID '{agent_id}' not found"
        emit_error(error_msg, message_group=group_id)
        emit_divider(message_group=group_id)
        return CheckRunningAgentStatusOutput(agent_id=agent_id, error=error_msg)
    except Exception as e:
        error_msg = f"Error checking agent status for '{agent_id}': {str(e)}"
        emit_error(error_msg, message_group=group_id)
        emit_divider(message_group=group_id)
        return CheckRunningAgentStatusOutput(agent_id=agent_id, error=error_msg)


def _list_running_agents(context: RunContext) -> ListRunningAgentsOutput:
    """List all currently running agents.
    
    Returns:
        ListRunningAgentsOutput: Information about all running agents
    """
    group_id = generate_group_id("list_running_agents")
    
    emit_info(
        "\n[bold white on blue] LIST RUNNING AGENTS [/bold white on blue]",
        message_group=group_id
    )
    emit_divider(message_group=group_id)
    
    try:
        # Get all agent states
        with _agent_states_lock:
            agents = []
            for agent_id, state in agent_states.items():
                # Only include agents that are running
                if state["status"] == "running":
                    agent_info = AgentStatusInfo(
                        agent_id=agent_id,
                        agent_name=state.get("agent_name", "Unknown"),
                        pid=state["pid"],
                        status=state["status"],
                        start_time=state["start_time"].isoformat() if hasattr(state["start_time"], 'isoformat') else str(state["start_time"]),
                        model=state.get("model")
                    )
                    agents.append(agent_info)
        
        # Display the running agents in the console
        if not agents:
            emit_system_message("No agents currently running", message_group=group_id)
        else:
            for agent in agents:
                emit_system_message(
                    f"- [bold]{agent.agent_id}[/bold]: {agent.agent_name} (PID: {agent.pid}, Model: {agent.model or 'default'})", 
                    message_group=group_id
                )
                
        emit_divider(message_group=group_id)
        return ListRunningAgentsOutput(agents=agents)
        
    except Exception as e:
        error_msg = f"Error listing running agents: {str(e)}"
        emit_error(error_msg, message_group=group_id)
        emit_divider(message_group=group_id)
        return ListRunningAgentsOutput(agents=[], error=error_msg)


def register_spawn_agent(agent):
    """Register the spawn_agent tool with the provided agent.
    
    Args:
        agent: The agent to register the tool with
    """
    agent.tool(_spawn_agent)


def register_check_running_agent_status(agent):
    """Register the check_running_agent_status tool with the provided agent.
    
    Args:
        agent: The agent to register the tool with
    """
    agent.tool(_check_running_agent_status)


def register_list_running_agents(agent):
    """Register the list_running_agents tool with the provided agent.
    
    Args:
        agent: The agent to register the tool with
    """
    agent.tool(_list_running_agents)