import pytest
import time
import subprocess
from unittest.mock import patch, MagicMock
import psutil

from code_puppy.process_dispatcher import ProcessDispatcher, ProcessInfo
from code_puppy.state_management import agent_states


class TestProcessDispatcher:
    """Test the ProcessDispatcher class."""
    
    def setup_method(self):
        """Clear agent states before each test."""
        agent_states.clear()
        
    @patch('psutil.pid_exists')
    @patch('psutil.Process')
    def test_poll_processes_with_running_process(self, mock_process_class, mock_pid_exists):
        """Test that poll_processes correctly identifies running processes."""
        # Mock psutil to return True for pid existence check
        mock_pid_exists.return_value = True
        
        # Mock psutil.Process to avoid STATUS_ZOMBIE check
        mock_psutil_process = MagicMock()
        mock_psutil_process.status.return_value = "running"  # Any status other than STATUS_ZOMBIE
        mock_process_class.return_value = mock_psutil_process
        
        # Create a process dispatcher
        dispatcher = ProcessDispatcher()
        
        # Create a mock process that is still running
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is still running
        
        # Add a process to the dispatcher
        agent_id = "test-agent-123"
        process_info = ProcessInfo(mock_process, time.time())
        dispatcher.processes[agent_id] = process_info
        
        # Add agent state manually (since we're not actually spawning)
        from code_puppy.state_management import add_agent_state
        add_agent_state(agent_id=agent_id, pid=mock_process.pid, visible=False)
        
        # Poll processes
        dispatcher.poll_processes()
        
        # Since our mock process is still running, it should remain in both
        # processes dict and agent_states as 'running' status
        assert agent_id in dispatcher.processes
        assert agent_id in agent_states
        assert agent_states[agent_id]["status"] == "running"
        
    def test_poll_processes_with_terminated_process(self):
        """Test that poll_processes correctly identifies terminated processes."""
        # Create a process dispatcher
        dispatcher = ProcessDispatcher()
        
        # Create a mock process that has terminated
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Process has terminated with exit code 1
        
        # Add a process to the dispatcher
        agent_id = "test-agent-456"
        process_info = ProcessInfo(mock_process, time.time())
        dispatcher.processes[agent_id] = process_info
        
        # Add agent state manually (since we're not actually spawning)
        from code_puppy.state_management import add_agent_state
        pid = 12346  # Mock PID
        add_agent_state(agent_id=agent_id, pid=pid, visible=False)
        
        # Poll processes
        dispatcher.poll_processes()
        
        # Since the process has terminated, it should be removed from processes dict
        assert agent_id not in dispatcher.processes
        
        # But the agent should still exist in agent_states with its final status
        assert agent_id in agent_states
        
    @patch('psutil.pid_exists')
    def test_poll_processes_with_nonexistent_pid(self, mock_pid_exists):
        """Test that poll_processes correctly identifies processes that no longer exist."""
        # Mock psutil to return False for pid existence check
        mock_pid_exists.return_value = False
        
        # Create a process dispatcher
        dispatcher = ProcessDispatcher()
        
        # Create a mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process claims to still be running
        
        # Add a process to the dispatcher
        agent_id = "test-agent-789"
        process_info = ProcessInfo(mock_process, time.time())
        dispatcher.processes[agent_id] = process_info
        
        # Add agent state manually (since we're not actually spawning)
        from code_puppy.state_management import add_agent_state
        add_agent_state(agent_id=agent_id, pid=mock_process.pid, visible=False)
        
        # Poll processes
        dispatcher.poll_processes()
        
        # Since the PID no longer exists, the agent status should be updated to 'terminated'
        assert agent_id in agent_states
        assert agent_states[agent_id]["status"] == "terminated"
        assert agent_states[agent_id]["result"] == "Process unexpectedly terminated"
        
    @patch('psutil.Process')
    @patch('psutil.pid_exists')
    def test_poll_processes_with_zombie_process(self, mock_pid_exists, mock_process_class):
        """Test that poll_processes correctly identifies zombie processes."""
        # Mock psutil to return True for pid existence but STATUS_ZOMBIE for status
        mock_pid_exists.return_value = True
        mock_psutil_process = MagicMock()
        mock_psutil_process.status.return_value = psutil.STATUS_ZOMBIE
        mock_process_class.return_value = mock_psutil_process
        
        # Create a process dispatcher
        dispatcher = ProcessDispatcher()
        
        # Create a mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process claims to still be running
        
        # Add a process to the dispatcher
        agent_id = "test-agent-999"
        process_info = ProcessInfo(mock_process, time.time())
        dispatcher.processes[agent_id] = process_info
        
        # Add agent state manually (since we're not actually spawning)
        from code_puppy.state_management import add_agent_state
        add_agent_state(agent_id=agent_id, pid=mock_process.pid, visible=False)
        
        # Poll processes
        dispatcher.poll_processes()
        
        # Since the process is a zombie, the agent status should be updated to 'terminated'
        assert agent_id in agent_states
        assert agent_states[agent_id]["status"] == "terminated"
        assert agent_states[agent_id]["result"] == "Process became a zombie"
        
    @patch('psutil.Process')
    @patch('psutil.pid_exists')
    def test_poll_processes_with_exception(self, mock_pid_exists, mock_process_class):
        """Test that poll_processes handles exceptions gracefully."""
        # Mock psutil to raise an exception
        mock_pid_exists.side_effect = Exception("Mock psutil error")
        
        # Create a process dispatcher
        dispatcher = ProcessDispatcher()
        
        # Create a mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process claims to still be running
        
        # Add a process to the dispatcher
        agent_id = "test-agent-111"
        process_info = ProcessInfo(mock_process, time.time())
        dispatcher.processes[agent_id] = process_info
        
        # Add agent state manually (since we're not actually spawning)
        from code_puppy.state_management import add_agent_state
        add_agent_state(agent_id=agent_id, pid=mock_process.pid, visible=False)
        
        # Poll processes - should not raise an exception
        dispatcher.poll_processes()
        
        # The agent should still exist in agent_states, but status should remain unchanged
        assert agent_id in agent_states
        assert agent_states[agent_id]["status"] == "running"
