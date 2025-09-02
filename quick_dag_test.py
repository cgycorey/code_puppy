#!/usr/bin/env python3
"""
Quick test to send some DAG messages to see the live updates.
Run this while the TUI is open to see real-time DAG updates!
"""

import time

from code_puppy.messaging import emit_sidebar_message


def quick_test():
    """Send a few quick DAG messages for testing."""
    print("🐶 Sending DAG test messages! Check the Execution DAG tab!")

    # Clear demo and add real data
    emit_sidebar_message(
        "Clearing demo data", sidebar_type="dag", dag_action="clear_demo"
    )

    time.sleep(1)

    # Add a real task
    emit_sidebar_message(
        "Starting real execution",
        sidebar_type="dag",
        dag_action="add_node",
        node_data={
            "id": "live_test_1",
            "name": "📋 Analyze user input for testing",
            "type": "agent",
            "status": "running",
        },
    )

    time.sleep(2)

    # Complete it
    emit_sidebar_message(
        "Test node completed!",
        sidebar_type="dag",
        dag_action="update_status",
        node_id="live_test_1",
        status="completed",
    )

    time.sleep(1)

    # Add tool execution
    emit_sidebar_message(
        "Executing tool for file listing",
        sidebar_type="dag",
        dag_action="add_node",
        node_data={
            "id": "live_test_2",
            "name": "🔧 list_files(directory='.')",
            "type": "tool",
            "status": "running",
        },
    )

    time.sleep(2)

    # Complete tool
    emit_sidebar_message(
        "File listing completed successfully",
        sidebar_type="dag",
        dag_action="update_status",
        node_id="live_test_2",
        status="completed",
        node_metadata={"files_found": 12, "execution_time": "0.45s"},
    )

    time.sleep(1)

    # Add decision node
    emit_sidebar_message(
        "Evaluating implementation choices",
        sidebar_type="dag",
        dag_action="add_node",
        node_data={
            "id": "live_test_3",
            "name": "❓ Choose between two implementation paths",
            "type": "decision",
            "status": "running",
        },
    )

    time.sleep(1)

    # Complete decision
    emit_sidebar_message(
        "Decision made: Proceed with optimal path",
        sidebar_type="dag",
        dag_action="update_status",
        node_id="live_test_3",
        status="completed",
    )

    print("✅ Test complete! The DAG should now show live execution data.")
    print("\nTo restore demo data, run:")
    print("emit_sidebar_message('', sidebar_type='dag', dag_action='restore_demo')")


if __name__ == "__main__":
    quick_test()
