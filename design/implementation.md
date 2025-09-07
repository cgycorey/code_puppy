# Code Puppy Multi-Agent Implementation Plan

## Overview
This document details the concrete implementation steps for the multi-agent system described in `multi_agent.md`. We'll build a system where the main Code Puppy instance can dispatch tasks to sub-agents running in separate processes, with optional visibility in terminal windows.

All functionality will be implemented as agentic tools that can be called by agents through the tool registry. This means we'll be adding tool functions that are self-contained and can be invoked by any agent with appropriate permissions.

## 1. Process Dispatcher Module

### File: `code_puppy/process_dispatcher.py` (~200 lines)

This module handles spawning and managing sub-agent processes. It serves as the core engine for our multi-agent system.

### Implementation Steps:

1. Create the basic dispatcher class with methods for spawning agents
2. Implement subprocess management using `subprocess.Popen`
3. Add unique agent ID generation (UUID4 recommended)
4. Create command building logic that includes:
   - `--child-mode` flag
   - `--task-id` parameter
   - `--prompt` parameter
   - `--model` parameter (when specified)
5. Add process monitoring functionality:
   - Store PIDs in state manager
   - Handle process exit codes
   - Capture stdout/stderr for result processing
6. Implement timeout handling:
   - Configurable timeout (default 5 minutes)
   - Graceful termination of hanging processes
7. Add error handling for process spawn failures

### Integration Points:
- Uses existing `invoke_agent` functionality for actual agent execution
- Interfaces with `state_management.py` to store and update agent states
- Leverages `model_factory.py` to handle model selection when specified
- Integrates with `visibility_handlers.py` for platform-specific terminal operations

### Result Processing:
- Captures final output from sub-agent processes via stdout
- Stores error messages from stderr when processes fail
- Updates state manager with completion status and results

### Key Internal Functions:
- `spawn_agent(agent_name: str, prompt: str, background: bool = True, visible: bool = False, model: str | None = None) -> str`
  - Returns the agent_id of the spawned process
- `build_agent_command(agent_name: str, task_id: str, prompt: str, model: str | None = None) -> List[str]`
  - Constructs the command to run the sub-agent
- `monitor_agent_process(agent_id: str, process: subprocess.Popen) -> None`
  - Handles process communication and status updates
- `terminate_hanging_processes() -> None`
  - Checks for and terminates processes that exceed timeout

Note: These are internal functions used by our agentic tools, not directly callable by agents.

## 2. State Management Extension

### File: `code_puppy/state_management.py` (existing, will be extended)

We'll extend the existing state management to track sub-agent processes.

### Implementation Steps:

1. Add a new shared state dictionary for agent processes
2. Implement thread-safe access using locks
3. Add functions to manage agent state entries:
   - `add_agent_state(agent_id: str, pid: int, visible: bool, model: str | None = None) -> None`
   - `update_agent_status(agent_id: str, status: str, last_reasoning: str | None = None, result: str | None = None) -> None`
   - `get_agent_state(agent_id: str) -> Dict[str, Any]`
   - `remove_agent_state(agent_id: str) -> None`
4. Add process polling to detect unexpected exits:
   - Integration with `psutil` to check if process is still running
   - Periodic polling function to update statuses
5. Implement state serialization for optional persistence (SQLite later if needed)

### Data Structure:
```python
agent_states: Dict[str, Dict[str, Any]] = {
    "agent_id_123": {
        "pid": 4567,  # Process ID for killing/polling
        "status": "running|idle|completed|errored|terminated",
        "last_reasoning": "Woof, refactoring now...",  # From share_your_reasoning
        "result": "Task done!" | None,  # Final output
        "start_time": timestamp,  # For timeouts
        "visible": True | False,  # If in a new terminal window
        "session_info": "Terminal tab ID or name"  # For visible mode
        "model": "gpt-4" | None,  # Pinned model if specified
    }
}
```

### Thread Safety Implementation:
- Use `threading.Lock()` to protect access to the shared state dictionary
- Implement atomic operations for state updates
- Consider using `threading.local()` for thread-specific data if needed

### Error Handling:
- Implement proper locking/unlocking even in error conditions
- Add validation for agent_id existence before state operations
- Handle edge cases like processes that disappear between polls

## 3. Tools Integration

### Files: 
- `code_puppy/tools/agent_management.py` (new)
- `code_puppy/tools/__init__.py` (modify to register new tools)
- `code_puppy/tools/common.py` (may need modifications for new tool categories)

We'll add new tools that can be invoked from the main agent to manage sub-agents. These will be registered in the tool registry and available to all agents.

### Implementation Steps:

1. Create new tool module `code_puppy/tools/agent_management.py` for agent management functions
2. Implement `dispatch_to_agent` tool:
   - Interface with the process dispatcher
   - Handle both background and synchronous execution
   - Store agent metadata in state manager
3. Implement `manage_agent_process` tool:
   - Support actions: status, kill, restart
   - Query the state manager for agent data
   - Perform actual process management operations
4. Create a simple alias `check_status` that calls `manage_agent_process` with "status" action
5. Register these tools in the tool registry by modifying `code_puppy/tools/__init__.py`

### Key Agentic Tool Functions:
- `dispatch_to_agent(agent_name: str, prompt: str, background: bool = True, visible: bool = False, model: str | None = None) -> str`
  - This tool will be available to agents for spawning sub-agents
  - Returns the agent_id of the spawned process
- `manage_agent_process(agent_id: str, action: str) -> Dict[str, Any]`
  - This tool will be available to agents for managing sub-agent processes
  - Supports actions: "status", "kill", "restart"
  - Returns detailed information about the agent process
- `check_status(agent_id: str) -> Dict[str, Any]`
  - Simple alias for `manage_agent_process(agent_id, "status")`
  - Available for quick status checks

## 4. Visibility Mode Implementation

### File: `code_puppy/visibility_handlers.py` (~150 lines)

Platform-specific handlers for launching agents in visible terminal windows.

### Implementation Steps:

1. Create a new module for visibility handlers
2. Implement OS detection using `platform.system()`
3. Add specific handlers for each OS:
   - **macOS**: Use `osascript` to open Terminal.app tabs/windows
   - **Linux**: Use `gnome-terminal` or fallback to `xterm`
   - **Windows**: Use `start cmd` to launch new command windows
4. Create fallback logic when primary terminal application isn't available
5. Implement PID capture mechanisms for visible processes
6. Add persistence to Unix terminals after execution completes

### Key Functions:
- `detect_os() -> str`
- `spawn_visible_agent_macos(command: List[str]) -> int`
- `spawn_visible_agent_linux(command: List[str]) -> int`
- `spawn_visible_agent_windows(command: List[str]) -> int`
- `get_visible_process_pid(session_info: str) -> int | None`

## 5. Sub-Agent Mode

### File: `code_puppy/main.py` (modify to support --child-mode)

The sub-agent mode is a special execution path that allows Code Puppy to run as a child process executing a single task.

### Implementation Steps:

1. Add CLI argument parsing for `--child-mode`, `--task-id`, `--prompt`, and `--model`
2. Create a separate execution path for child mode that:
   - Skips the normal CLI prompt loop
   - Executes the provided task directly
   - Returns result via stdout
   - Uses proper exit codes
3. Optimize child mode to be "lite" by skipping unnecessary CLI initialization
4. Implement proper IPC handling for `share_your_reasoning` output:
   - Direct stdout/stderr streaming
   - JSON-formatted communication for structured data

### Child Mode Execution Flow:
1. When launched with `--child-mode`, Code Puppy will:
   - Parse the task ID, prompt, and model from CLI arguments
   - Execute the prompt using the existing agent infrastructure
   - Stream `share_your_reasoning` outputs in a structured format
   - Output final results to stdout
   - Exit with appropriate code (0 for success, non-zero for errors)

## 6. Testing Plan

### Implementation Steps:

1. Unit tests for process dispatcher (mocking subprocess.Popen)
2. Tests for state management functions with thread safety checks
3. Tests for agent management tools with mocked agent responses
4. Integration tests for the full dispatch and management flow
5. Platform-specific tests for visibility handlers (where possible)
6. Test timeout and process termination scenarios

### Key Testing Areas:
- Process spawning and management
- State tracking accuracy
- Tool invocation and response handling
- Visibility mode functionality (manual testing where automation isn't feasible)
- Error handling in various failure modes
- Memory and resource usage of sub-agents

### Test Strategies:
- Mock subprocess operations to avoid actually spawning processes during unit tests
- Use threading tests to verify state management thread safety
- Create integration tests that verify the full flow from tool invocation to process completion
- Test both successful and failed agent execution scenarios
- Verify proper error messages are returned when agents fail

## 7. Best Practices and Code Quality

### Implementation Guidelines:

1. **SOLID/DRY Principles**:
   - Each module has a single responsibility
   - Reuse existing code-puppy components where possible
   - Avoid duplicating agent invocation logic

2. **Zen Principles**:
   - Keep files under 600 lines
   - Start simple with hidden mode, add visible mode as enhancement
   - Type hints on all functions and variables
   - Comprehensive error handling

3. **Dependencies**:
   - Minimal dependencies (psutil for process monitoring)
   - All new dependencies should be properly declared in pyproject.toml
   - No hard requirements on specific terminal applications

4. **Error Handling Strategies**:
   - Implement try/finally blocks for resource cleanup
   - Use specific exception types rather than generic exceptions
   - Log errors with appropriate context for debugging
   - Return structured error information to calling agents

5. **Git Workflow**:
   - Run `ruff check --fix` and `ruff format .` before commits
   - Follow existing code style and patterns
   - Never force push to main branch

## 8. Configuration Management

### Implementation Details:

1. Add configuration options to existing config system:
   - Default timeout for sub-agent processes
   - Enable/disable visibility mode by default
   - Logging verbosity for sub-agent processes
2. Configuration should be accessible both via CLI flags and config files
3. Add validation for configuration values
4. Implement configuration inheritance for sub-agents (they should inherit most settings from the controller)

## 9. Future Extensibility

### Implementation Considerations:

1. Config flags for various modes (e.g., `--distributed` for ZeroMQ)
2. Data structure designed for easy serialization/storage
3. Clean interfaces that can be replaced with distributed implementations
4. Separate visibility handlers to easily swap terminal handling logic

## Data Flow Between Components

The multi-agent system will have several key data flows:

1. **Controller to Dispatcher**:
   - Tool calls from agents pass parameters to the dispatcher
   - Dispatcher spawns sub-agent processes and returns agent_id

2. **Dispatcher to Sub-Agent**:
   - Dispatcher creates CLI command with task parameters
   - Sub-agent receives these via command-line arguments

3. **Sub-Agent to Controller**:
   - Sub-agent streams reasoning updates via stdout (in structured format)
   - Controller captures these and updates state manager
   - Sub-agent outputs final results via stdout
   - Controller captures results and updates state

4. **Controller to State Manager**:
   - Tools query agent states for status information
   - Periodic polling updates agent statuses
   - Management tools update agent states based on actions

5. **State Manager Internal Updates**:
   - Thread-safe access to shared state dictionary
   - Automatic cleanup of completed/terminated agents

## Estimated Implementation Order:

1. Process dispatcher core functionality (`code_puppy/process_dispatcher.py`)
2. State management extension (`code_puppy/state_management.py`)
3. Child mode execution in main.py (`code_puppy/main.py`)
4. Agent management tools (`code_puppy/tools/agent_management.py`)
5. Tool registration (`code_puppy/tools/__init__.py`)
6. Visibility handlers (`code_puppy/visibility_handlers.py`)
7. Configuration management (`code_puppy/config.py`)
8. Full integration testing
9. Documentation updates

This plan should keep us aligned with the vision while maintaining code quality and following our development principles.