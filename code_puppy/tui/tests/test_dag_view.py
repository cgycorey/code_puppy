"""
Tests for the DAG view component.
"""

import pytest
from textual.app import App

from ..components.dag_view import DAGNode, DAGView


class DAGTestApp(App):
    """Test app for DAG view."""

    def compose(self):
        yield DAGView(id="dag-view")


@pytest.fixture
def dag_view():
    """Create a DAG view for testing."""
    return DAGView()


def test_dag_node_creation():
    """Test creating a DAG node."""
    node = DAGNode(
        node_id="test_1", name="Test Task", node_type="task", status="pending"
    )

    assert node.node_id == "test_1"
    assert node.name == "Test Task"
    assert node.node_type == "task"
    assert node.status == "pending"
    assert node.children == []
    assert node.parents == []


@pytest.mark.asyncio
async def test_dag_view_basic_functionality():
    """Test basic DAG view functionality."""
    async with DAGTestApp().run_test() as pilot:
        dag_view = pilot.app.query_one("#dag-view", DAGView)

        # Initially should be empty
        assert len(dag_view.nodes) == 0
        assert len(dag_view.execution_order) == 0

        # Add a node
        node = DAGNode(
            node_id="task_1", name="First Task", node_type="agent", status="running"
        )
        dag_view.add_node(node)

        # Check node was added
        assert len(dag_view.nodes) == 1
        assert "task_1" in dag_view.nodes
        assert dag_view.execution_order == ["task_1"]

        # Update node status
        dag_view.update_node_status("task_1", "completed")
        assert dag_view.nodes["task_1"].status == "completed"

        # Clear DAG
        dag_view.clear_dag()
        assert len(dag_view.nodes) == 0
        assert len(dag_view.execution_order) == 0


@pytest.mark.asyncio
async def test_dag_message_processing():
    """Test DAG message processing."""
    async with DAGTestApp().run_test() as pilot:
        dag_view = pilot.app.query_one("#dag-view", DAGView)

        # Test add_node message
        dag_view.process_dag_message(
            "Adding node",
            {
                "sidebar_type": "dag",
                "dag_action": "add_node",
                "node_data": {
                    "id": "test_node",
                    "name": "Test Node",
                    "type": "tool",
                    "status": "pending",
                },
            },
        )

        assert "test_node" in dag_view.nodes
        assert dag_view.nodes["test_node"].name == "Test Node"
        assert dag_view.nodes["test_node"].node_type == "tool"

        # Test update_status message
        dag_view.process_dag_message(
            "Updating status",
            {
                "sidebar_type": "dag",
                "dag_action": "update_status",
                "node_id": "test_node",
                "status": "completed",
            },
        )

        assert dag_view.nodes["test_node"].status == "completed"

        # Test clear message
        dag_view.process_dag_message(
            "Clearing DAG", {"sidebar_type": "dag", "dag_action": "clear"}
        )

        assert len(dag_view.nodes) == 0


def test_dag_connections():
    """Test DAG node connections."""
    dag_view = DAGView()

    # Add two nodes
    node1 = DAGNode("node1", "First Node")
    node2 = DAGNode("node2", "Second Node")

    dag_view.add_node(node1)
    dag_view.add_node(node2)

    # Add connection
    dag_view.add_connection("node1", "node2")

    assert "node2" in dag_view.nodes["node1"].children
    assert "node1" in dag_view.nodes["node2"].parents
