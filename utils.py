# utils.py
import os
import datetime
from pathlib import Path
import config # Import the configuration constants

def format_size(size_bytes):
    """Formats a size in bytes into a human-readable string (KB, MB, GB)."""
    if size_bytes is None or not isinstance(size_bytes, (int, float)) or size_bytes < 0:
        return "N/A" # Handle invalid or unavailable sizes
    if size_bytes == 0:
        return f"0 {config.SIZE_UNITS[0]}" # Use "B" from config

    i = 0
    # Determine the appropriate unit
    while size_bytes >= 1024 and i < len(config.SIZE_UNITS) - 1:
        size_bytes /= 1024.0
        i += 1

    # Format to 2 decimal places, removing trailing zeros if they are .00
    formatted_size = f"{size_bytes:.2f}".rstrip('0').rstrip('.')
    return f"{formatted_size} {config.SIZE_UNITS[i]}"

def get_folder_size(folder_path):
    """
    Calculates the total size of a folder iteratively (avoids deep recursion).
    Returns size in bytes or None if the top-level folder is inaccessible.
    Handles permission errors on sub-items gracefully by skipping them.
    """
    total_size = 0
    try:
        start_path = Path(folder_path)
        # Initial check if the starting path is actually a directory we can potentially scan
        if not start_path.is_dir():
             # If it's a file, return its size. If it doesn't exist or isn't a dir, return None.
             try:
                 if start_path.is_file(follow_symlinks=False):
                     return start_path.stat(follow_symlinks=False).st_size
                 else:
                     return None # Not a file or dir we can handle initially
             except OSError:
                 return None # Cannot stat the initial path

        stack = [start_path] # Use Path objects
        visited = set() # Keep track of visited inodes to prevent cycles with symlinks

        while stack:
            current_path = stack.pop()

            try:
                # Re-check if path exists and is a directory before proceeding (could change)
                if not current_path.is_dir():
                    # print(f"Debug: Path {current_path} is no longer a directory or doesn't exist.")
                    continue

                # Check for symlink loops using inode numbers
                try:
                    inode = current_path.stat(follow_symlinks=False).st_ino
                    if inode in visited:
                        # print(f"Warning: Symlink cycle detected or directory visited again: {current_path}")
                        continue
                    visited.add(inode)
                except OSError as e:
                    # print(f"Warning: Could not get inode for {current_path}: {e}")
                    continue # Skip if inode check fails

                # Use scandir for potentially better performance
                with os.scandir(current_path) as it:
                    for entry in it:
                        try:
                            entry_path = Path(entry.path) # Work with Path object
                            # Important: Use follow_symlinks=False for size calculation consistency
                            # Treat symlinks themselves as having size 0 in this context, don't follow them for size.
                            if entry.is_file(follow_symlinks=False):
                                total_size += entry.stat(follow_symlinks=False).st_size
                            elif entry.is_dir(follow_symlinks=False):
                                # Avoid adding symlinks pointing to directories to the stack unless explicitly desired
                                if not entry.is_symlink():
                                     stack.append(entry_path) # Add subdirectory Path object to the stack
                            # else: it's a symlink (to file or dir), socket, etc. - ignore its size here.

                        except OSError as e:
                            # Skip files/dirs we can't access or that disappear during scan
                            # print(f"Warning: Cannot access item {entry.path} during scan: {e}")
                            continue # Continue scanning the rest of the current directory
            except PermissionError:
                # If we can't scan the current_path itself
                # print(f"Warning: Permission denied accessing {current_path}.")
                continue
            except FileNotFoundError:
                # If the directory disappears between popping and scanning
                # print(f"Warning: Directory not found during scan: {current_path}")
                continue
            except OSError as e:
                # Catch other potential OS errors during scandir or stat
                # print(f"Warning: OS error processing {current_path}: {e}")
                continue

        return total_size

    except PermissionError:
        # print(f"Warning: Permission denied accessing the initial folder {folder_path}.")
        return None # Indicate inaccessible top-level folder
    except FileNotFoundError:
        # print(f"Warning: Initial folder not found: {folder_path}")
        return None # Indicate non-existent top-level folder
    except Exception as e:
        # Catch any other unexpected error during initial setup
        # print(f"Error calculating size for {folder_path}: {e}")
        return None


def get_modification_time(path):
    """Gets the last modification time of a file/folder."""
    try:
        # Use Path object for consistency and follow_symlinks=False
        path_obj = Path(path)
        timestamp = path_obj.stat(follow_symlinks=False).st_mtime
        return datetime.datetime.fromtimestamp(timestamp).strftime(config.DATE_FORMAT)
    except (OSError, FileNotFoundError):
        # Handle cases where the file doesn't exist or permissions fail
        return "N/A"
