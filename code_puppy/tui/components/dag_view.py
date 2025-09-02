from datetime import datetime, timedelta
from typing import Dict, List, Optional

from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.widgets import Label, Static


class DAGNode:
    """Represents a single node in the DAG."""

    def __init__(
        self,
        node_id: str,
        name: str,
        node_type: str = "task",
        status: str = "pending",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict] = None,
    ):
        self.node_id = node_id
        self.name = name
        self.node_type = node_type  # 'task', 'tool', 'agent', 'decision'
        self.status = status  # 'pending', 'running', 'completed', 'failed'
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
        self.children: List[str] = []  # Node IDs this node connects to
        self.parents: List[str] = []  # Node IDs that connect to this node


class DAGView(Container):
    """Visual component for displaying the agentic execution DAG."""

    DEFAULT_CSS = """
    DAGView {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }

    .dag-container {
        height: 1fr;
    }

    .dag-node {
        margin: 1 0;
        padding: 0 1;
        border: solid $accent;
        background: $surface;
    }

    .dag-node-pending {
        border: solid #6b7280;
        color: #9ca3af;
    }

    .dag-node-running {
        border: solid #fbbf24;
        color: #fbbf24;
        text-style: bold;
    }

    .dag-node-completed {
        border: solid #34d399;
        color: #34d399;
    }

    .dag-node-failed {
        border: solid #ef4444;
        color: #ef4444;
    }

    .dag-connection {
        color: #6b7280;
        text-style: dim;
    }

    .dag-empty {
        color: #6b7280;
        text-style: italic;
        text-align: center;
        padding: 2;
    }

    .dag-header {
        color: #60a5fa;
        text-style: bold;
        text-align: center;
        padding: 0 1;
        background: $surface;
        border-bottom: solid $accent;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nodes: Dict[str, DAGNode] = {}
        self.execution_order: List[str] = []  # Track execution order

        # Add some hardcoded demo nodes for immediate visualization
        self._add_demo_nodes()

    def compose(self) -> ComposeResult:
        """Create the DAG visualization layout."""
        yield Static("🔀 Execution Flow (Demo Data)", classes="dag-header")
        with ScrollableContainer(classes="dag-container"):
            yield Label(
                "Loading execution data...", classes="dag-empty", id="dag-content"
            )

    def on_mount(self) -> None:
        """Refresh display when component is mounted."""
        self._refresh_display()

    def add_node(self, node: DAGNode) -> None:
        """Add a new node to the DAG."""
        self.nodes[node.node_id] = node
        if node.node_id not in self.execution_order:
            self.execution_order.append(node.node_id)
        self._refresh_display()

    def update_node_status(
        self, node_id: str, status: str, metadata: Optional[Dict] = None
    ) -> None:
        """Update the status of an existing node."""
        if node_id in self.nodes:
            self.nodes[node_id].status = status
            self.nodes[node_id].timestamp = datetime.now()
            if metadata:
                self.nodes[node_id].metadata.update(metadata)
            self._refresh_display()

    def add_connection(self, parent_id: str, child_id: str) -> None:
        """Add a connection between two nodes."""
        if parent_id in self.nodes and child_id in self.nodes:
            self.nodes[parent_id].children.append(child_id)
            self.nodes[child_id].parents.append(parent_id)
            self._refresh_display()

    def clear_dag(self) -> None:
        """Clear all nodes and connections, but keep demo nodes."""
        self.nodes.clear()
        self.execution_order.clear()
        # Re-add demo nodes after clearing
        self._add_demo_nodes()
        self._refresh_display()

    def clear_demo_mode(self) -> None:
        """Clear everything including demo nodes for real usage."""
        self.nodes.clear()
        self.execution_order.clear()
        self._refresh_display()

    def _add_demo_nodes(self) -> None:
        """Add some hardcoded demo nodes for immediate visualization."""
        from datetime import datetime

        # Create demo nodes with different statuses and types
        base_time = datetime.now()

        demo_nodes = [
            DAGNode(
                node_id="demo_1",
                name="📋 Understand user request: 'Add DAG sidebar'",
                node_type="agent",
                status="completed",
                timestamp=base_time - timedelta(seconds=45),
                metadata={"reasoning": "Planning implementation approach"},
            ),
            DAGNode(
                node_id="demo_2",
                name="🔧 list_files(directory='code_puppy/tui')",
                node_type="tool",
                status="completed",
                timestamp=base_time - timedelta(seconds=40),
                metadata={"tool_name": "list_files", "files_found": 15},
            ),
            DAGNode(
                node_id="demo_3",
                name="🤖 Analyze existing sidebar structure",
                node_type="agent",
                status="completed",
                timestamp=base_time - timedelta(seconds=35),
                metadata={"analysis": "Found TabbedContent pattern"},
            ),
            DAGNode(
                node_id="demo_4",
                name="❓ Choose: Extend sidebar vs new component?",
                node_type="decision",
                status="completed",
                timestamp=base_time - timedelta(seconds=30),
                metadata={"decision": "Extend existing sidebar"},
            ),
            DAGNode(
                node_id="demo_5",
                name="🔧 edit_file(dag_view.py) - Create component",
                node_type="tool",
                status="completed",
                timestamp=base_time - timedelta(seconds=25),
                metadata={"lines_added": 200},
            ),
            DAGNode(
                node_id="demo_6",
                name="🔧 edit_file(sidebar.py) - Add DAG tab",
                node_type="tool",
                status="completed",
                timestamp=base_time - timedelta(seconds=20),
                metadata={"integration": "TabPane added"},
            ),
            DAGNode(
                node_id="demo_7",
                name="🔧 edit_file(message_queue.py) - Add messaging",
                node_type="tool",
                status="running",
                timestamp=base_time - timedelta(seconds=15),
                metadata={"function": "emit_sidebar_message"},
            ),
            DAGNode(
                node_id="demo_8",
                name="🤖 Generate final response with docs",
                node_type="agent",
                status="pending",
                timestamp=base_time - timedelta(seconds=10),
                metadata={"output_type": "markdown"},
            ),
            DAGNode(
                node_id="demo_9",
                name="📋 Validation: Check all tests pass",
                node_type="task",
                status="failed",
                timestamp=base_time - timedelta(seconds=5),
                metadata={"error": "Network connectivity issues"},
            ),
        ]

        # Add demo nodes
        for node in demo_nodes:
            self.nodes[node.node_id] = node
            self.execution_order.append(node.node_id)

    def _refresh_display(self) -> None:
        """Refresh the visual display of the DAG."""
        container = self.query_one(".dag-container", ScrollableContainer)
        container.remove_children()

        if not self.nodes:
            container.mount(
                Label("No execution data yet", classes="dag-empty", id="dag-content")
            )
            return

        # Clear the initial loading message if it exists
        try:
            initial_label = self.query_one("#dag-content", Label)
            if initial_label:
                initial_label.remove()
        except Exception:
            pass

        # Display nodes in execution order
        for i, node_id in enumerate(self.execution_order):
            if node_id not in self.nodes:
                continue

            node = self.nodes[node_id]

            # Create node display
            node_classes = f"dag-node dag-node-{node.status}"

            # Format node content
            timestamp_str = (
                node.timestamp.strftime("%H:%M:%S") if node.timestamp else ""
            )
            node_content = f"[{timestamp_str}] {node.name}"

            # Add type indicator
            type_indicators = {
                "task": "📋",
                "tool": "🔧",
                "agent": "🤖",
                "decision": "❓",
            }
            icon = type_indicators.get(node.node_type, "•")
            node_content = f"{icon} {node_content}"

            # Add status indicator
            status_indicators = {
                "pending": "⏳",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌",
            }
            status_icon = status_indicators.get(node.status, "")
            if status_icon:
                node_content = f"{status_icon} {node_content}"

            node_widget = Static(node_content, classes=node_classes)
            container.mount(node_widget)

            # Add connection lines if this isn't the last node
            if i < len(self.execution_order) - 1:
                connection = Static("│", classes="dag-connection")
                container.mount(connection)

    def process_dag_message(self, content: str, metadata: Dict) -> None:
        """Process a DAG update message from the messaging system."""
        sidebar_type = metadata.get("sidebar_type", "")

        if sidebar_type != "dag":
            return

        # Parse different types of DAG messages
        message_type = metadata.get("dag_action", "node_update")

        if message_type == "add_node":
            node_data = metadata.get("node_data", {})
            node = DAGNode(
                node_id=node_data.get("id", ""),
                name=node_data.get("name", "Unknown"),
                node_type=node_data.get("type", "task"),
                status=node_data.get("status", "pending"),
                metadata=node_data.get("metadata", {}),
            )
            self.add_node(node)

        elif message_type == "update_status":
            node_id = metadata.get("node_id", "")
            status = metadata.get("status", "pending")
            node_metadata = metadata.get("node_metadata", {})
            self.update_node_status(node_id, status, node_metadata)

        elif message_type == "add_connection":
            parent_id = metadata.get("parent_id", "")
            child_id = metadata.get("child_id", "")
            self.add_connection(parent_id, child_id)

        elif message_type == "clear":
            self.clear_dag()

        elif message_type == "clear_demo":
            # Clear everything including demo nodes
            self.nodes.clear()
            self.execution_order.clear()
            self._refresh_display()

        elif message_type == "restore_demo":
            # Restore demo nodes
            self.nodes.clear()
            self.execution_order.clear()
            self._add_demo_nodes()
            self._refresh_display()
