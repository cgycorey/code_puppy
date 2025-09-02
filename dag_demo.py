#!/usr/bin/env python3
"""
Demo script to test the DAG visualization in the TUI sidebar.

This script demonstrates how to use the emit_sidebar_message function
to send DAG updates to the TUI sidebar for visualization.
"""

import time

from code_puppy.messaging import emit_sidebar_message


def demo_dag_workflow():
    """Demonstrate a typical agentic workflow with DAG visualization."""

    print(
        "🐶 Starting DAG Demo! Switch to the 'Execution DAG' tab in the sidebar to see the magic!"
    )
    time.sleep(2)

    # Step 1: Add initial task node
    emit_sidebar_message(
        "Adding initial task",
        sidebar_type="dag",
        dag_action="add_node",
        node_data={
            "id": "task_1",
            "name": "Analyze user request",
            "type": "agent",
            "status": "running",
            "metadata": {"priority": "high"},
        },
    )

    time.sleep(2)

    # Step 2: Complete the first task and add tool usage
    emit_sidebar_message(
        "Task completed, starting tool execution",
        sidebar_type="dag",
        dag_action="update_status",
        node_id="task_1",
        status="completed",
    )

    emit_sidebar_message(
        "Adding tool execution",
        sidebar_type="dag",
        dag_action="add_node",
        node_data={
            "id": "tool_1",
            "name": "list_files(.)",
            "type": "tool",
            "status": "running",
            "metadata": {"tool_name": "list_files"},
        },
    )

    time.sleep(2)

    # Step 3: Complete tool and add decision point
    emit_sidebar_message(
        "Tool completed",
        sidebar_type="dag",
        dag_action="update_status",
        node_id="tool_1",
        status="completed",
    )

    emit_sidebar_message(
        "Adding decision point",
        sidebar_type="dag",
        dag_action="add_node",
        node_data={
            "id": "decision_1",
            "name": "Choose next action",
            "type": "decision",
            "status": "running",
        },
    )

    time.sleep(2)

    # Step 4: Add multiple parallel tasks
    emit_sidebar_message(
        "Decision completed, executing parallel tasks",
        sidebar_type="dag",
        dag_action="update_status",
        node_id="decision_1",
        status="completed",
    )

    emit_sidebar_message(
        "Adding parallel task A",
        sidebar_type="dag",
        dag_action="add_node",
        node_data={
            "id": "task_2a",
            "name": "Read configuration files",
            "type": "tool",
            "status": "running",
        },
    )

    emit_sidebar_message(
        "Adding parallel task B",
        sidebar_type="dag",
        dag_action="add_node",
        node_data={
            "id": "task_2b",
            "name": "Analyze code structure",
            "type": "agent",
            "status": "running",
        },
    )

    time.sleep(3)

    # Step 5: Complete parallel tasks
    emit_sidebar_message(
        "Parallel task A completed",
        sidebar_type="dag",
        dag_action="update_status",
        node_id="task_2a",
        status="completed",
    )

    emit_sidebar_message(
        "Parallel task B completed",
        sidebar_type="dag",
        dag_action="update_status",
        node_id="task_2b",
        status="completed",
    )

    time.sleep(2)

    # Step 6: Add final synthesis task
    emit_sidebar_message(
        "Adding final synthesis",
        sidebar_type="dag",
        dag_action="add_node",
        node_data={
            "id": "task_final",
            "name": "Generate final response",
            "type": "agent",
            "status": "running",
        },
    )

    time.sleep(3)

    emit_sidebar_message(
        "Workflow completed!",
        sidebar_type="dag",
        dag_action="update_status",
        node_id="task_final",
        status="completed",
    )

    print(
        "\n✅ DAG Demo completed! Check out the beautiful execution flow in the sidebar! 🎉"
    )
    print(
        "\n💡 This demonstrates how agentic tools can visualize their execution in real-time."
    )
    print("\nTry running this command in the TUI to see the demo:")
    print("python dag_demo.py")


if __name__ == "__main__":
    demo_dag_workflow()
