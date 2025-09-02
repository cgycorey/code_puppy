# DAG Sidebar Implementation 🔀

This document outlines the implementation of the DAG (Directed Acyclic Graph) visualization sidebar for the Code Puppy TUI, which provides real-time visualization of agentic execution flows.

## 🎯 Overview

The DAG sidebar allows agents and tools to visualize their execution flow in real-time, showing:
- Task execution order
- Tool invocations
- Decision points
- Status updates (pending ⏳, running 🔄, completed ✅, failed ❌)
- Node types (task 📋, tool 🔧, agent 🤖, decision ❓)

## 🛠️ Components Implemented

### 1. Message System Enhancement

#### New Message Type
- Added `SIDEBAR_DAG_UPDATE` to `MessageType` enum in both:
  - `code_puppy/messaging/message_queue.py`
  - `code_puppy/tui/models/enums.py`

#### New Messaging Function
- **`emit_sidebar_message(content, sidebar_type="dag", **metadata)`**
  - Sends DAG updates to the sidebar
  - Located in `code_puppy/messaging/message_queue.py`
  - Exported through `code_puppy/messaging/__init__.py`

### 2. DAG Visualization Component

#### DAGNode Class
```python
class DAGNode:
    def __init__(self, node_id, name, node_type="task", status="pending",
                 timestamp=None, metadata=None)
```
- Represents individual nodes in the execution graph
- Supports different types: `task`, `tool`, `agent`, `decision`
- Tracks status: `pending`, `running`, `completed`, `failed`
- Maintains parent/child relationships

#### DAGView Component
- **File**: `code_puppy/tui/components/dag_view.py`
- Visual component for rendering the DAG
- Scrollable container with real-time updates
- Rich styling with status-based colors
- Methods:
  - `add_node(node)` - Add new execution node
  - `update_node_status(node_id, status)` - Update node status
  - `add_connection(parent_id, child_id)` - Link nodes
  - `clear_dag()` - Reset the visualization
  - `process_dag_message(content, metadata)` - Handle incoming messages

### 3. Sidebar Integration

#### Enhanced Sidebar Component
- **File**: `code_puppy/tui/components/sidebar.py`
- Added new tab: "🔀 Execution DAG"
- Integrated DAGView component
- Added `process_dag_message()` method
- Added `get_dag_view()` accessor method

#### TUI App Integration
- **File**: `code_puppy/tui/app.py`
- Added `update_sidebar_dag(content, metadata)` method
- Connects messaging system to sidebar

#### Message Renderer Enhancement
- **File**: `code_puppy/messaging/renderers.py`
- Added DAG message handling in `TUIRenderer`
- Routes `SIDEBAR_DAG_UPDATE` messages to TUI app

## 📝 Usage Examples

### Basic DAG Node Creation
```python
from code_puppy.messaging import emit_sidebar_message

# Add a new task node
emit_sidebar_message(
    "Starting analysis",
    sidebar_type="dag",
    dag_action="add_node",
    node_data={
        "id": "task_1",
        "name": "Analyze user request",
        "type": "agent",
        "status": "running"
    }
)
```

### Update Node Status
```python
# Update task status to completed
emit_sidebar_message(
    "Task completed",
    sidebar_type="dag",
    dag_action="update_status",
    node_id="task_1",
    status="completed"
)
```

### Add Tool Execution
```python
# Add tool execution node
emit_sidebar_message(
    "Executing file operations",
    sidebar_type="dag",
    dag_action="add_node",
    node_data={
        "id": "tool_list_files",
        "name": "list_files(.)",
        "type": "tool",
        "status": "running",
        "metadata": {"tool_name": "list_files"}
    }
)
```

### Clear DAG
```python
# Clear the entire DAG visualization
emit_sidebar_message(
    "Clearing execution history",
    sidebar_type="dag",
    dag_action="clear"
)
```

## 🎨 Visual Design

### Color Coding
- **Pending**: Gray (#6b7280) with hourglass ⏳
- **Running**: Yellow (#fbbf24) with spinner 🔄 (bold text)
- **Completed**: Green (#34d399) with checkmark ✅
- **Failed**: Red (#ef4444) with X ❌

### Node Type Icons
- **Task**: 📋 (clipboard)
- **Tool**: 🔧 (wrench)
- **Agent**: 🤖 (robot)
- **Decision**: ❓ (question mark)

### Layout
- Vertical flow showing execution order
- Timestamps for each node
- Connection lines between sequential steps
- Scrollable container for long execution flows

## 🧪 Test Implementation

### Test Suite
- **File**: `code_puppy/tui/tests/test_dag_view.py`
- Tests node creation, status updates, message processing
- Async tests for TUI integration
- Connection testing for node relationships

### Demo Script
- **File**: `dag_demo.py`
- Interactive demonstration of DAG functionality
- Shows realistic agentic workflow
- Can be run to test the implementation

## 🎭 **Demo Mode - See It Now!**

The DAG sidebar now includes **hardcoded demo data** so you can see what it looks like immediately!

### What You'll See:
- 📋 **Agent Reasoning**: "Understand user request: 'Add DAG sidebar'"
- 🔧 **Tool Execution**: "list_files(directory='code_puppy/tui')"
- ❓ **Decision Points**: "Choose: Extend sidebar vs new component?"
- ✅ **Completed Tasks**: Multiple steps showing green checkmarks
- 🔄 **Running Task**: "edit_file(message_queue.py) - Add messaging"
- ⏳ **Pending Task**: "Generate final response with docs"
- ❌ **Failed Task**: "Validation: Check all tests pass" (with network error)

### Demo Controls:
```python
# Clear demo data for real usage
emit_sidebar_message("", sidebar_type="dag", dag_action="clear_demo")

# Restore demo data
emit_sidebar_message("", sidebar_type="dag", dag_action="restore_demo")
```

### Quick Test Script:
Run `python quick_dag_test.py` while TUI is open to see live updates!

## 🚀 Integration Points

### For Agent Implementations
Agents can now visualize their execution by calling:
```python
from code_puppy.messaging import emit_sidebar_message

# At start of reasoning
emit_sidebar_message(
    "Starting analysis",
    sidebar_type="dag",
    dag_action="add_node",
    node_data={"id": "reasoning_1", "name": "Analyze request", "type": "agent", "status": "running"}
)

# When complete
emit_sidebar_message(
    "Analysis complete",
    sidebar_type="dag",
    dag_action="update_status",
    node_id="reasoning_1",
    status="completed"
)
```

### For Tool Implementations
Tools can report their execution:
```python
# Before tool execution
emit_sidebar_message(
    f"Executing {tool_name}",
    sidebar_type="dag",
    dag_action="add_node",
    node_data={"id": f"tool_{tool_name}", "name": tool_name, "type": "tool", "status": "running"}
)
```

## 🕰️ Future Enhancements

1. **Connection Visualization**: Add visual lines between connected nodes
2. **Parallel Execution**: Better visualization of concurrent tasks
3. **Error Details**: Click-to-expand error information
4. **Export**: Save DAG as image or text
5. **Performance Metrics**: Add timing and resource usage data
6. **Interactive Navigation**: Click nodes to jump to related chat messages

## 💯 File Summary

### New Files
- `code_puppy/tui/components/dag_view.py` - DAG visualization component
- `code_puppy/tui/tests/test_dag_view.py` - Test suite
- `dag_demo.py` - Full demo script
- `quick_dag_test.py` - Quick test for live updates
- `DAG_SIDEBAR_IMPLEMENTATION.md` - This documentation

### Modified Files
- `code_puppy/messaging/message_queue.py` - Added DAG message type and emit function
- `code_puppy/messaging/__init__.py` - Export new emit function
- `code_puppy/messaging/renderers.py` - Handle DAG messages in TUI renderer
- `code_puppy/tui/models/enums.py` - Added DAG message type
- `code_puppy/tui/components/__init__.py` - Export DAGView component
- `code_puppy/tui/components/sidebar.py` - Added DAG tab and integration
- `code_puppy/tui/app.py` - Added DAG message handling method

---

🐶 **Woof!** The DAG sidebar is now ready to visualize some serious agentic execution flows! Users can switch to the "🔀 Execution DAG" tab in the sidebar to see their agent's thought process unfold in real-time. This makes debugging and understanding agent behavior much more intuitive and fun!
