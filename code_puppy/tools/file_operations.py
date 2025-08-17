# file_operations.py

import os
from typing import Any, Dict, List

from pydantic import BaseModel, StrictStr, StrictInt
from pydantic_ai import RunContext

from code_puppy.tools.common import console

# ---------------------------------------------------------------------------
# Module-level helper functions (exposed for unit tests _and_ used as tools)
# ---------------------------------------------------------------------------
from code_puppy.tools.common import should_ignore_path


class ListedFile(BaseModel):
    path: str | None = None
    type: str | None = None
    size: int = 0
    full_path: str | None = None
    depth: int | None = None
    error: str | None = None


class ListFileOutput(BaseModel):
    files: List[ListedFile]


def _list_files(
    context: RunContext, directory: str = ".", recursive: bool = True
) -> ListFileOutput:
    results = []
    directory = os.path.abspath(directory)
    console.print("\n[bold white on blue] DIRECTORY LISTING [/bold white on blue]")
    console.print(
        f"\U0001f4c2 [bold cyan]{directory}[/bold cyan] [dim](recursive={recursive})[/dim]"
    )
    console.print("[dim]" + "-" * 60 + "[/dim]")
    if not os.path.exists(directory):
        console.print(
            f"[bold red]Error:[/bold red] Directory '{directory}' does not exist"
        )
        console.print("[dim]" + "-" * 60 + "[/dim]\n")
        return ListFileOutput(files=[ListedFile(**{"error": f"Directory '{directory}' does not exist"})])
    if not os.path.isdir(directory):
        console.print(f"[bold red]Error:[/bold red] '{directory}' is not a directory")
        console.print("[dim]" + "-" * 60 + "[/dim]\n")
        return ListFileOutput(files=[ListedFile(**{"error": f"'{directory}' is not a directory"})])
    folder_structure = {}
    file_list = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not should_ignore_path(os.path.join(root, d))]
        rel_path = os.path.relpath(root, directory)
        depth = 0 if rel_path == "." else rel_path.count(os.sep) + 1
        if rel_path == ".":
            rel_path = ""
        if rel_path:
            dir_path = os.path.join(directory, rel_path)
            results.append(
                ListedFile(**{
                    "path": rel_path,
                    "type": "directory",
                    "size": 0,
                    "full_path": dir_path,
                    "depth": depth,
                })
            )
            folder_structure[rel_path] = {
                "path": rel_path,
                "depth": depth,
                "full_path": dir_path,
            }
        for file in files:
            file_path = os.path.join(root, file)
            if should_ignore_path(file_path):
                continue
            rel_file_path = os.path.join(rel_path, file) if rel_path else file
            try:
                size = os.path.getsize(file_path)
                file_info = {
                    "path": rel_file_path,
                    "type": "file",
                    "size": size,
                    "full_path": file_path,
                    "depth": depth,
                }
                results.append(ListedFile(**file_info))
                file_list.append(file_info)
            except (FileNotFoundError, PermissionError):
                continue
        if not recursive:
            break

    def format_size(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def get_file_icon(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".py", ".pyw"]:
            return "\U0001f40d"
        elif ext in [".js", ".jsx", ".ts", ".tsx"]:
            return "\U0001f4dc"
        elif ext in [".html", ".htm", ".xml"]:
            return "\U0001f310"
        elif ext in [".css", ".scss", ".sass"]:
            return "\U0001f3a8"
        elif ext in [".md", ".markdown", ".rst"]:
            return "\U0001f4dd"
        elif ext in [".json", ".yaml", ".yml", ".toml"]:
            return "\u2699\ufe0f"
        elif ext in [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"]:
            return "\U0001f5bc\ufe0f"
        elif ext in [".mp3", ".wav", ".ogg", ".flac"]:
            return "\U0001f3b5"
        elif ext in [".mp4", ".avi", ".mov", ".webm"]:
            return "\U0001f3ac"
        elif ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"]:
            return "\U0001f4c4"
        elif ext in [".zip", ".tar", ".gz", ".rar", ".7z"]:
            return "\U0001f4e6"
        elif ext in [".exe", ".dll", ".so", ".dylib"]:
            return "\u26a1"
        else:
            return "\U0001f4c4"

    if results:
        files = sorted(
            [f for f in results if f.type == "file"], key=lambda x: x.path
        )
        console.print(
            f"\U0001f4c1 [bold blue]{os.path.basename(directory) or directory}[/bold blue]"
        )
    all_items = sorted(results, key=lambda x: x.path)
    parent_dirs_with_content = set()
    for i, item in enumerate(all_items):
        if item.type == "directory" and not item.path:
            continue
        if os.sep in item.path:
            parent_path = os.path.dirname(item.path)
            parent_dirs_with_content.add(parent_path)
        depth = item.path.count(os.sep) + 1 if item.path else 0
        prefix = ""
        for d in range(depth):
            if d == depth - 1:
                prefix += "\u2514\u2500\u2500 "
            else:
                prefix += "    "
        name = os.path.basename(item.path) or item.path
        if item.type == "directory":
            console.print(f"{prefix}\U0001f4c1 [bold blue]{name}/[/bold blue]")
        else:
            icon = get_file_icon(item.path)
            size_str = format_size(item.size)
            console.print(
                f"{prefix}{icon} [green]{name}[/green] [dim]({size_str})[/dim]"
            )
    else:
        console.print("[yellow]Directory is empty[/yellow]")
    dir_count = sum(1 for item in results if item.type == "directory")
    file_count = sum(1 for item in results if item.type == "file")
    total_size = sum(item.size for item in results if item.type == "file")
    console.print("\n[bold cyan]Summary:[/bold cyan]")
    console.print(
        f"\U0001f4c1 [blue]{dir_count} directories[/blue], \U0001f4c4 [green]{file_count} files[/green] [dim]({format_size(total_size)} total)[/dim]"
    )
    console.print("[dim]" + "-" * 60 + "[/dim]\n")
    return ListFileOutput(files=results)


# Backward compatibility function for tests
def list_files(context: RunContext, directory: str = ".", recursive: bool = True):
    """Backward compatibility function for tests.""" 
    result = _list_files(context, directory, recursive)
    # Convert ListFileOutput to list of dictionaries for backward compatibility
    return [file.model_dump() for file in result.files]


class ReadFileOutput(BaseModel):
    content: str | None
    path: str | None = None
    total_lines: int | None = None
    error: str | None = None


def _read_file(context: RunContext, file_path: str, start_line: int | None = None, num_lines: int | None = None) -> ReadFileOutput:
    file_path = os.path.abspath(file_path)
    console.print(
        f"\n[bold white on blue] READ FILE [/bold white on blue] \U0001f4c2 [bold cyan]{file_path}[/bold cyan]"
    )
    console.print("[dim]" + "-" * 60 + "[/dim]")
    if not os.path.exists(file_path):
        return ReadFileOutput(content=f"File '{file_path}' does not exist", error=f"File '{file_path}' does not exist")
    if not os.path.isfile(file_path):
        return ReadFileOutput(content=f"'{file_path}' is not a file", error=f"'{file_path}' is not a file")
    
    # Check total file lines first
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            total_lines = sum(1 for _ in f)
    except Exception:
        return ReadFileOutput(content="Unable to determine file size", error="Unable to determine file size")
    
    # If no parameters provided, check if file is too large
    if start_line is None and num_lines is None:
        if total_lines > 600:
            error_msg = f"File '{file_path}' has {total_lines} lines, which exceeds the 600-line limit. Please specify start_line and num_lines parameters to read a portion of the file."
            return ReadFileOutput(content=error_msg, error=error_msg, path=file_path, total_lines=total_lines)
        
    # If num_lines is specified, validate it
    if num_lines is not None:
        if num_lines > 600:
            error_msg = f"Cannot read {num_lines} lines at once. Maximum allowed is 600 lines."
            return ReadFileOutput(content=error_msg, error=error_msg)
        if num_lines <= 0:
            error_msg = f"num_lines must be a positive integer."
            return ReadFileOutput(content=error_msg, error=error_msg)
    
    # If start_line is specified, validate it
    if start_line is not None:
        if start_line <= 0:
            error_msg = f"start_line must be a positive integer (1-indexed)."
            return ReadFileOutput(content=error_msg, error=error_msg)
        if start_line > total_lines:
            error_msg = f"start_line ({start_line}) exceeds the total number of lines in the file ({total_lines})."
            return ReadFileOutput(content=error_msg, error=error_msg)
        
    # Default values if only one parameter is provided
    if start_line is None:
        start_line = 1
    if num_lines is None:
        num_lines = total_lines
    
    # Read specified portion of the file
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Skip lines before start_line
            for _ in range(start_line - 1):
                next(f)
            # Read the specified number of lines
            lines = []
            for i in range(num_lines):
                try:
                    lines.append(f.readline())
                except StopIteration:
                    break
            content = ''.join(lines)
        return ReadFileOutput(content=content, path=file_path, total_lines=total_lines)
    except Exception as exc:
        return ReadFileOutput(content="FILE NOT FOUND", error="FILE NOT FOUND")


# Backward compatibility function for tests  
def read_file(context: RunContext, file_path: str = "", start_line: int | None = None, num_lines: int | None = None):
    """Backward compatibility function for tests."""
    result = _read_file(context, file_path, start_line, num_lines)
    # Convert ReadFileOutput to dictionary for backward compatibility
    result_dict = result.model_dump()
    
    # For backward compatibility with tests, remove error field if None
    if result_dict.get("error") is None:
        result_dict.pop("error", None)
    
    return result_dict


class MatchInfo(BaseModel):
    file_path: str | None
    line_number: int | None
    line_content: str | None

class GrepOutput(BaseModel):
    matches: List[MatchInfo]

def _grep(
    context: RunContext, search_string: str, directory: str = "."
) -> GrepOutput:
    matches: List[MatchInfo] = []
    directory = os.path.abspath(directory)
    console.print(
        f"\n[bold white on blue] GREP [/bold white on blue] \U0001f4c2 [bold cyan]{directory}[/bold cyan] [dim]for '{search_string}'[/dim]"
    )
    console.print("[dim]" + "-" * 60 + "[/dim]")

    for root, dirs, files in os.walk(directory, topdown=True):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if not should_ignore_path(os.path.join(root, d))]

        for f_name in files:
            file_path = os.path.join(root, f_name)

            if should_ignore_path(file_path):
                # console.print(f"[dim]Ignoring: {file_path}[/dim]") # Optional: for debugging ignored files
                continue

            try:
                # console.print(f"\U0001f4c2 [bold cyan]Searching: {file_path}[/bold cyan]") # Optional: for verbose searching log
                with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                    for line_number, line_content in enumerate(fh, 1):
                        if search_string in line_content:
                            match_info = MatchInfo(**{
                                "file_path": file_path,
                                "line_number": line_number,
                                "line_content": line_content.strip(),
                            })
                            matches.append(match_info)
                            # console.print(
                            #     f"[green]Match:[/green] {file_path}:{line_number} - {line_content.strip()}"
                            # ) # Optional: for verbose match logging
                            if len(matches) >= 200:
                                console.print(
                                    "[yellow]Limit of 200 matches reached. Stopping search.[/yellow]"
                                )
                                return GrepOutput(matches=matches)
            except FileNotFoundError:
                console.print(
                    f"[yellow]File not found (possibly a broken symlink): {file_path}[/yellow]"
                )
                continue
            except UnicodeDecodeError:
                console.print(
                    f"[yellow]Cannot decode file (likely binary): {file_path}[/yellow]"
                )
                continue
            except Exception as e:
                console.print(f"[red]Error processing file {file_path}: {e}[/red]")
                continue

    if not matches:
        console.print(
            f"[yellow]No matches found for '{search_string}' in {directory}[/yellow]"
        )
    else:
        console.print(
            f"[green]Found {len(matches)} match(es) for '{search_string}' in {directory}[/green]"
        )

    return GrepOutput(matches=matches)


# Backward compatibility function for tests
def grep(context: RunContext, search_string: str = "", directory: str = "."):
    """Backward compatibility function for tests."""
    result = _grep(context, search_string, directory)
    # Convert GrepOutput to list of dictionaries for backward compatibility
    return [match.model_dump() for match in result.matches]


def register_file_operations_tools(agent):
    @agent.tool
    def list_files(
        context: RunContext, directory: str = ".", recursive: bool = True
    ) -> ListFileOutput:
        return _list_files(context, directory, recursive)

    @agent.tool
    def read_file(context: RunContext, file_path: str = "", start_line: int | None = None, num_lines: int | None = None) -> ReadFileOutput:
        return _read_file(context, file_path, start_line, num_lines)

    @agent.tool
    def grep(
        context: RunContext, search_string: str = "", directory: str = "."
    ) -> GrepOutput:
        return _grep(context, search_string, directory)

    @agent.tool
    def should_ignore_path(context: RunContext, path: str) -> bool:
        """Check if a path should be ignored based on ignore patterns."""
        return should_ignore_path(path)