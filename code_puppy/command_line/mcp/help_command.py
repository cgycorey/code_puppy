"""
MCP Help Command - Shows help for all MCP commands.
"""

import logging
from typing import List, Optional

from rich.text import Text

from code_puppy.messaging import emit_info

from .base import MCPCommandBase

# Configure logging
logger = logging.getLogger(__name__)


class HelpCommand(MCPCommandBase):
    """
    Command handler for showing MCP command help.

    Displays comprehensive help information for all available MCP commands.
    """

    def execute(self, args: List[str], group_id: Optional[str] = None) -> None:
        """
        Show help for MCP commands.

        Args:
            args: Command arguments (unused)
            group_id: Optional message group ID for grouping related messages
        """
        if group_id is None:
            group_id = self.generate_group_id()

        try:
            # Build help text programmatically to avoid markup conflicts
            help_lines = []

            # Title
            help_lines.append(
                Text("MCP Server Management Commands", style="bold magenta")
            )
            help_lines.append(Text(""))

            # Registry Commands
            help_lines.append(Text("Registry Commands:", style="bold cyan"))
            help_lines.append(
                Text("/_mcp search", style="cyan")
                + Text(" [query]     Search 30+ pre-configured servers")
            )
            help_lines.append(
                Text("/_mcp install", style="cyan")
                + Text(" <id>       Install server from registry")
            )
            help_lines.append(Text(""))

            # Core Commands
            help_lines.append(Text("Core Commands:", style="bold cyan"))
            help_lines.append(
                Text("/_mcp", style="cyan")
                + Text("                    Show server status dashboard")
            )
            help_lines.append(
                Text("/_mcp list", style="cyan")
                + Text("               List all registered servers")
            )
            help_lines.append(
                Text("/_mcp start", style="cyan")
                + Text(" <name>       Start a specific server")
            )
            help_lines.append(
                Text("/_mcp start-all", style="cyan")
                + Text("          Start all servers")
            )
            help_lines.append(
                Text("/_mcp stop", style="cyan")
                + Text(" <name>        Stop a specific server")
            )
            help_lines.append(
                Text("/_mcp stop-all", style="cyan")
                + Text(" [group_id]  Stop all running servers")
            )
            help_lines.append(
                Text("/_mcp restart", style="cyan")
                + Text(" <name>     Restart a specific server")
            )
            help_lines.append(Text(""))

            # Management Commands
            help_lines.append(Text("Management Commands:", style="bold cyan"))
            help_lines.append(
                Text("/_mcp status", style="cyan")
                + Text(" [name]      Show detailed status (all servers or specific)")
            )
            help_lines.append(
                Text("/_mcp test", style="cyan")
                + Text(" <name>        Test connectivity to a server")
            )
            help_lines.append(
                Text("/_mcp logs", style="cyan")
                + Text(" <name> [limit] Show recent events (default limit: 10)")
            )
            help_lines.append(
                Text("/_mcp add", style="cyan")
                + Text(" [json]         Add new server (JSON or wizard)")
            )
            help_lines.append(
                Text("/_mcp remove", style="cyan")
                + Text(" <name>      Remove/disable a server")
            )
            help_lines.append(
                Text("/_mcp help", style="cyan")
                + Text("               Show this help message")
            )
            help_lines.append(Text(""))

            # Status Indicators
            help_lines.append(Text("Status Indicators:", style="bold"))
            help_lines.append(
                Text("✓ Running    ✗ Stopped    ⚠ Error    ⏸ Quarantined    ⭐ Popular")
            )
            help_lines.append(Text(""))

            # Examples
            help_lines.append(Text("Examples:", style="bold"))
            examples_text = """/_mcp search database     # Find database servers
/_mcp install postgres    # Install PostgreSQL server
/_mcp start filesystem    # Start a specific server
/_mcp start-all           # Start all servers at once
/_mcp stop-all            # Stop all running servers
/_mcp add {"name": "test", "type": "stdio", "command": "echo"}"""
            help_lines.append(Text(examples_text, style="dim"))

            # Combine all lines
            final_text = Text()
            for i, line in enumerate(help_lines):
                if i > 0:
                    final_text.append("\n")
                final_text.append_text(line)

            emit_info(final_text, message_group=group_id)

        except Exception as e:
            logger.error(f"Error showing help: {e}")
            emit_info(f"[red]Error showing help: {e}[/red]", message_group=group_id)
