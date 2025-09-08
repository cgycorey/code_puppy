import subprocess
import uuid
import time
import sys
from typing import List, Dict, Optional, Any, Tuple
import psutil

from code_puppy.state_management import append_to_message_history, poll_agent_processes


class ProcessInfo:
    """Information about a running process."""
    
    def __init__(self, process: subprocess.Popen, start_time: float):
        self.process = process
        self.start_time = start_time


class ProcessDispatcher:
    """Handles spawning and managing sub-agent processes as child processes."""
    
    def __init__(self, timeout: int = 300):  # Default 5 minutes timeout
        """Initialize the process dispatcher.
        
        Args:
            timeout: Process timeout in seconds (default 300 seconds/5 minutes)
        """
        self.processes: Dict[str, ProcessInfo] = {}
        self.timeout = timeout
        
    def spawn_agent(
        self, 
        agent_name: str, 
        prompt: str, 
        background: bool = True, 
        visible: bool = False, 
        model: Optional[str] = None
    ) -> str:
        """Spawn a sub-agent as a child process.
        
        Args:
            agent_name: Name of the agent to invoke
            prompt: Prompt to send to the agent
            background: Whether to run in background (default True)
            visible: Whether to show the process terminal (default False)
            model: Optional model to use for the agent
            
        Returns:
            str: The agent_id of the spawned process
            
        Raises:
            Exception: If process spawning fails
        """
        # Generate a unique agent ID
        agent_id = str(uuid.uuid4())
        
        try:
            # Build the command to run the sub-agent
            command = self.build_agent_command(agent_name, agent_id, prompt, model)
            
            # Start the subprocess
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Store the process with its start time
            process_info = ProcessInfo(process, time.time())
            self.processes[agent_id] = process_info
            
            # Add agent state to global tracking
            from code_puppy.state_management import add_agent_state
            add_agent_state(agent_id=agent_id, pid=process.pid, visible=visible, model=model)
            
            # If not running in background, wait for completion
            if not background:
                self.monitor_agent_process(agent_id, process)
                
            return agent_id
            
        except Exception as e:
            # Handle process spawn failures
            raise Exception(f"Failed to spawn agent '{agent_name}': {str(e)}")
    
    def build_agent_command(
        self, 
        agent_name: str, 
        task_id: str, 
        prompt: str, 
        model: Optional[str] = None
    ) -> List[str]:
        """Build the command to run a sub-agent in child mode.
        
        Args:
            agent_name: Name of the agent to invoke
            task_id: Unique task ID for this agent invocation
            prompt: Prompt to send to the agent
            model: Optional model to use for the agent
            
        Returns:
            List[str]: Command parts as a list
        """
        # Get the Python executable
        python_executable = sys.executable
        
        # Build base command
        command = [python_executable, "-m", "code_puppy"]
        
        # Add child mode flag
        command.append("--child-mode")
        
        # Add task ID
        command.extend(["--task-id", task_id])
        
        # Add agent name
        command.extend(["--agent", agent_name])
        
        # Add prompt
        command.extend(["--prompt", prompt])
        
        # Add model if specified
        if model:
            command.extend(["--model", model])
            
        return command
    
    def monitor_agent_process(self, agent_id: str, process: subprocess.Popen) -> Dict[str, Any]:
        """Monitor a sub-agent process and capture its output.
        
        Args:
            agent_id: ID of the agent process
            process: The subprocess.Popen object to monitor
            
        Returns:
            Dict[str, Any]: Process result data including stdout, stderr, and exit code
        """
        # Wait for the process to complete
        stdout, stderr = process.communicate()
        
        # Check exit code
        exit_code = process.returncode
        
        # Store results
        result_data = {
            "agent_id": agent_id,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "completed_at": time.time()
        }
        
        # Add to message history
        append_to_message_history(result_data)
        
        return result_data
    
    def terminate_hanging_processes(self) -> List[str]:
        """Check for and terminate processes that exceed timeout.
        
        Returns:
            List[str]: List of terminated agent IDs
        """
        current_time = time.time()
        terminated_agents = []
        
        # Get list of processes to avoid modifying dict during iteration
        process_items = list(self.processes.items())
        
        for agent_id, process_info in process_items:
            # Check if process is still running
            if process_info.process.poll() is None:  # Process is still running
                # Check if it has exceeded timeout
                if current_time - process_info.start_time > self.timeout:
                    try:
                        process_info.process.terminate()
                        process_info.process.wait(timeout=5)  # Wait up to 5 seconds for graceful termination
                    except subprocess.TimeoutExpired:
                        process_info.process.kill()  # Force kill if graceful termination fails
                    
                    # Remove from processes dict
                    del self.processes[agent_id]
                    terminated_agents.append(agent_id)
        
        return terminated_agents
    
    def get_process_status(self, agent_id: str) -> Optional[Tuple[bool, int]]:
        """Get the status of a process.
        
        Args:
            agent_id: ID of the agent process
            
        Returns:
            Optional[Tuple[bool, int]]: (is_running, exit_code) or None if process not found
        """
        if agent_id not in self.processes:
            return None
            
        process_info = self.processes[agent_id]
        exit_code = process_info.process.poll()
        
        # If poll() returns None, the process is still running
        is_running = exit_code is None
        
        return (is_running, exit_code if not is_running else None)
    
    def poll_processes(self) -> None:
        """Poll all tracked processes to detect unexpected exits.
        
        Uses psutil to check if processes are still running and updates
        their status in the global agent state tracking.
        """
        # Check each process in our dispatcher
        for agent_id, process_info in list(self.processes.items()):
            process = process_info.process
            pid = process.pid
            
            # Check if the process has terminated normally
            exit_code = process.poll()
            if exit_code is not None:
                # Process has terminated, remove it from our tracking
                del self.processes[agent_id]
                # Update agent state to reflect normal termination
                try:
                    from code_puppy.state_management import update_agent_status
                    update_agent_status(agent_id, status="completed", result=f"Process terminated with exit code {exit_code}")
                except KeyError:
                    # Agent state doesn't exist, nothing to update
                    pass
                continue
            
            # If process claims to still be running, use psutil to verify
            try:
                if not psutil.pid_exists(pid):
                    # Process no longer exists (unexpected termination)
                    from code_puppy.state_management import update_agent_status
                    update_agent_status(agent_id, status="terminated", result="Process unexpectedly terminated")
                    del self.processes[agent_id]
                    continue
                    
                # Check if process is a zombie
                psutil_process = psutil.Process(pid)
                if psutil_process.status() == psutil.STATUS_ZOMBIE:
                    # Process became a zombie (unexpected termination)
                    from code_puppy.state_management import update_agent_status
                    update_agent_status(agent_id, status="terminated", result="Process became a zombie")
                    del self.processes[agent_id]
                    continue
                else:
                    # Process is still running, update its status
                    from code_puppy.state_management import update_agent_status
                    update_agent_status(agent_id, status="running")
            except Exception:
                # If we can't check the process status, just continue
                # This could happen if the process terminated between our checks
                pass
        
        # Also call the global polling function
        poll_agent_processes()
    
    def wait_for_process(self, agent_id: str, timeout: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Wait for a specific process to complete and return its results.
        
        Args:
            agent_id: ID of the agent process to wait for
            timeout: Optional timeout in seconds (uses dispatcher timeout if None)
            
        Returns:
            Optional[Dict[str, Any]]: Process result data or None if process not found
        """
        if agent_id not in self.processes:
            return None
            
        process_info = self.processes[agent_id]
        process = process_info.process
        
        try:
            # Wait for the process to complete with timeout
            stdout, stderr = process.communicate(timeout=timeout or self.timeout)
            
            # Check exit code
            exit_code = process.returncode
            
            # Remove from processes dict
            del self.processes[agent_id]
            
            # Store results
            result_data = {
                "agent_id": agent_id,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "completed_at": time.time()
            }
            
            return result_data
            
        except subprocess.TimeoutExpired:
            # Terminate the process if it timed out
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            # Remove from processes dict
            del self.processes[agent_id]
            
            return {
                "agent_id": agent_id,
                "stdout": "",
                "stderr": "Process timed out",
                "exit_code": -1,
                "completed_at": time.time()
            }
        
        except Exception as e:
            # Remove from processes dict
            del self.processes[agent_id]
            
            return {
                "agent_id": agent_id,
                "stdout": "",
                "stderr": f"Error waiting for process: {str(e)}",
                "exit_code": -1,
                "completed_at": time.time()
            }