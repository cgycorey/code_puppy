import threading
from typing import Any, Dict, List
from datetime import datetime
import psutil
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from code_puppy.process_dispatcher import SubAgent

# Legacy global state - maintained for backward compatibility
_message_history: List[Any] = []
_compacted_message_hashes = set()

# Agent process state management
agent_states: Dict[str, Dict[str, Any]] = {}
_agent_states_lock = threading.Lock()

# Flag to control whether to use agent-specific history (True) or global history (False)
_use_agent_specific_history = True
_tui_mode: bool = False
_tui_app_instance: Any = None


def add_agent_state(agent_id: str, pid: int, visible: bool, model: str | None = None) -> None:
    """Add a new agent state entry with thread-safe access.
    
    Args:
        agent_id: Unique identifier for the agent
        pid: Process ID of the agent
        visible: Whether the agent is running in visible mode
        model: Optional model name the agent is using
    """
    with _agent_states_lock:
        agent_states[agent_id] = {
            "pid": pid,
            "status": "running",
            "last_reasoning": None,
            "result": None,
            "start_time": datetime.now(),
            "visible": visible,
            "session_info": None,
            "model": model,
        }


def update_agent_status(agent_id: str, status: str, last_reasoning: str | None = None, result: str | None = None) -> None:
    """Update an agent's status with thread-safe access.
    
    Args:
        agent_id: Unique identifier for the agent
        status: New status of the agent
        last_reasoning: Optional reasoning message
        result: Optional result message
    
    Raises:
        KeyError: If agent_id doesn't exist in agent_states
    """
    with _agent_states_lock:
        if agent_id not in agent_states:
            raise KeyError(f"Agent {agent_id} not found in agent states")
        
        agent_states[agent_id]["status"] = status
        if last_reasoning is not None:
            agent_states[agent_id]["last_reasoning"] = last_reasoning
        if result is not None:
            agent_states[agent_id]["result"] = result


def get_agent_state(agent_id: str) -> Dict[str, Any]:
    """Get an agent's state with thread-safe access.
    
    Args:
        agent_id: Unique identifier for the agent
    
    Returns:
        Dictionary containing the agent's state
    
    Raises:
        KeyError: If agent_id doesn't exist in agent_states
    """
    with _agent_states_lock:
        if agent_id not in agent_states:
            raise KeyError(f"Agent {agent_id} not found in agent states")
        return agent_states[agent_id].copy()


def remove_agent_state(agent_id: str) -> None:
    """Remove an agent's state entry with thread-safe access.
    
    Args:
        agent_id: Unique identifier for the agent
    """
    with _agent_states_lock:
        if agent_id in agent_states:
            del agent_states[agent_id]


def poll_agent_processes() -> None:
    """Poll all tracked agent processes to detect unexpected exits.
    
    Updates agent status to 'terminated' if the process is no longer running.
    """
    with _agent_states_lock:
        for agent_id, state in list(agent_states.items()):
            pid = state["pid"]
            try:
                # Check if process is still running
                if not psutil.pid_exists(pid):
                    if state["status"] not in ["completed", "errored", "terminated"]:
                        agent_states[agent_id]["status"] = "terminated"
                        agent_states[agent_id]["result"] = "Process unexpectedly terminated"
                else:
                    # Additional check to see if process is actually alive
                    process = psutil.Process(pid)
                    if process.status() == psutil.STATUS_ZOMBIE:
                        agent_states[agent_id]["status"] = "terminated"
                        agent_states[agent_id]["result"] = "Process became a zombie"
            except psutil.NoSuchProcess:
                # Process no longer exists
                if state["status"] not in ["completed", "errored", "terminated"]:
                    agent_states[agent_id]["status"] = "terminated"
                    agent_states[agent_id]["result"] = "Process no longer exists"
            except Exception:
                # Handle any other exceptions silently to avoid breaking the polling
                pass


def add_compacted_message_hash(message_hash: str) -> None:
    """Add a message hash to the set of compacted message hashes."""
    if _use_agent_specific_history:
        try:
            from code_puppy.agents.agent_manager import (
                add_current_agent_compacted_message_hash,
            )

            add_current_agent_compacted_message_hash(message_hash)
            return
        except Exception:
            # Fallback to global if agent system fails
            pass
    _compacted_message_hashes.add(message_hash)


def get_compacted_message_hashes():
    """Get the set of compacted message hashes."""
    if _use_agent_specific_history:
        try:
            from code_puppy.agents.agent_manager import (
                get_current_agent_compacted_message_hashes,
            )

            return get_current_agent_compacted_message_hashes()
        except Exception:
            # Fallback to global if agent system fails
            pass
    return _compacted_message_hashes


def set_tui_mode(enabled: bool) -> None:
    """Set the global TUI mode state.

    Args:
        enabled: True if running in TUI mode, False otherwise
    """
    global _tui_mode
    _tui_mode = enabled


def is_tui_mode() -> bool:
    """Check if the application is running in TUI mode.

    Returns:
        True if running in TUI mode, False otherwise
    """
    return _tui_mode


def set_tui_app_instance(app_instance: Any) -> None:
    """Set the global TUI app instance reference.

    Args:
        app_instance: The TUI app instance
    """
    global _tui_app_instance
    _tui_app_instance = app_instance


def get_tui_app_instance() -> Any:
    """Get the current TUI app instance.

    Returns:
        The TUI app instance if available, None otherwise
    """
    return _tui_app_instance


def get_tui_mode() -> bool:
    """Get the current TUI mode state.

    Returns:
        True if running in TUI mode, False otherwise
    """
    return _tui_mode


def get_message_history() -> List[Any]:
    """Get message history - uses agent-specific history if enabled, otherwise global."""
    if _use_agent_specific_history:
        try:
            from code_puppy.agents.agent_manager import (
                get_current_agent_message_history,
            )

            return get_current_agent_message_history()
        except Exception:
            # Fallback to global if agent system fails
            return _message_history
    return _message_history


def set_message_history(history: List[Any]) -> None:
    """Set message history - uses agent-specific history if enabled, otherwise global."""
    if _use_agent_specific_history:
        try:
            from code_puppy.agents.agent_manager import (
                set_current_agent_message_history,
            )

            set_current_agent_message_history(history)
            return
        except Exception:
            # Fallback to global if agent system fails
            pass
    global _message_history
    _message_history = history


def clear_message_history() -> None:
    """Clear message history - uses agent-specific history if enabled, otherwise global."""
    if _use_agent_specific_history:
        try:
            from code_puppy.agents.agent_manager import (
                clear_current_agent_message_history,
            )

            clear_current_agent_message_history()
            return
        except Exception:
            # Fallback to global if agent system fails
            pass
    global _message_history
    _message_history = []


def append_to_message_history(message: Any) -> None:
    """Append to message history - uses agent-specific history if enabled, otherwise global."""
    if _use_agent_specific_history:
        try:
            from code_puppy.agents.agent_manager import (
                append_to_current_agent_message_history,
            )

            append_to_current_agent_message_history(message)
            return
        except Exception:
            # Fallback to global if agent system fails
            pass
    _message_history.append(message)


def extend_message_history(history: List[Any]) -> None:
    """Extend message history - uses agent-specific history if enabled, otherwise global."""
    if _use_agent_specific_history:
        try:
            from code_puppy.agents.agent_manager import (
                extend_current_agent_message_history,
            )

            extend_current_agent_message_history(history)
            return
        except Exception:
            # Fallback to global if agent system fails
            pass
    _message_history.extend(history)


def set_use_agent_specific_history(enabled: bool) -> None:
    """Enable or disable agent-specific message history.

    Args:
        enabled: True to use per-agent history, False to use global history.
    """
    global _use_agent_specific_history
    _use_agent_specific_history = enabled


def is_using_agent_specific_history() -> bool:
    """Check if agent-specific message history is enabled.

    Returns:
        True if using per-agent history, False if using global history.
    """
    return _use_agent_specific_history


def hash_message(message):
    hashable_entities = []
    for part in message.parts:
        if hasattr(part, "timestamp"):
            hashable_entities.append(part.timestamp.isoformat())
        elif hasattr(part, "tool_call_id"):
            hashable_entities.append(part.tool_call_id)
        else:
            hashable_entities.append(part.content)
    return hash(",".join(hashable_entities))
