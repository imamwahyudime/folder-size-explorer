# config.py
import os
from pathlib import Path
import platform

# --- Application Configuration ---
APP_TITLE = "Folder Size Explorer"
APP_VERSION = "0.0.5" # Incremented version for change
AUTHOR_NAME = "Imam Wahyudi"
GITHUB_URL = "https://github.com/imamwahyudime"
LINKEDIN_URL = "https://www.linkedin.com/in/imam-wahyudi/"

# --- Initial Settings ---
try:
    INITIAL_DIR = str(Path.home())
    if not os.path.isdir(INITIAL_DIR):
        INITIAL_DIR = '/' if platform.system() != "Windows" else 'C:\\'
except Exception:
    INITIAL_DIR = '/' if platform.system() != "Windows" else 'C:\\'

# --- Treeview Configuration ---
# Columns for Details view (** Added 'name' column **)
# Note: #0 is the hidden internal tree column when show="headings".
# We are adding an *explicit* visible 'name' column here.
TREEVIEW_COLUMNS_DETAILS = ("name", "size", "type", "modified")
# Columns for List view (** Added 'name' column **)
TREEVIEW_COLUMNS_LIST = ("name", "size")

# Column display properties for Details View (** Added 'name' **)
DETAILS_HEADINGS = {"name": "Name", "size": "Size", "type": "Type", "modified": "Date Modified"}
DETAILS_ANCHORS = {"name": "w", "size": "e", "type": "w", "modified": "w"} # Use "w" or "e"
DETAILS_WIDTHS = {"name": 250, "size": 100, "type": 80, "modified": 140} # Adjusted name width
DETAILS_STRETCH = {"name": True, "size": False, "type": False, "modified": False} # Allow Name to stretch

# Column display properties for List View (** Added 'name' **)
LIST_HEADINGS = {"name": "Name", "size": "Size"}
LIST_ANCHORS = {"name": "w", "size": "e"}
LIST_WIDTHS = {"name": 400, "size": 100} # Adjusted name width
LIST_STRETCH = {"name": True, "size": False} # Allow Name to stretch


# --- Formatting ---
SIZE_UNITS = ["B", "KB", "MB", "GB", "TB"]
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# --- UI Text ---
# (Keep existing UI text constants unchanged)
DUMMY_NODE_TEXT = "..."
STATUS_READY = "Ready"
STATUS_LOADING = "Loading {name}..."
STATUS_CALCULATING = "Calculating {count} folder size{plural}..."
STATUS_PERM_ERROR = "Ready (permission denied for some items)"
STATUS_ACCESS_ERROR = "Ready (error accessing some items)"
STATUS_BOTH_ERROR = "Ready (permission/access errors for some items)"
STATUS_ERROR = "Error"
ERROR_ACCESS_PATH_TITLE = "Error Accessing Path"
ERROR_ACCESS_PATH_MSG = "Could not access the path:\n{path}\n\nError: {error}"
ERROR_INVALID_PATH_TITLE = "Invalid Path"
ERROR_INVALID_PATH_MSG = "The path entered is not a valid directory:\n{path}"
ERROR_LISTING_TITLE = "Directory Listing Error"
ERROR_LISTING_MSG = "Could not list contents of:\n{path}\n\nError: {error}"
ERROR_OPEN_FILE_TITLE = "Error Opening File"
ERROR_OPEN_FILE_MSG = "Could not open the file:\n{path}\n\nError: {error}"
WARN_NAV_TITLE = "Navigation Error"
WARN_NAV_PARENT_MSG = "Could not navigate to the parent directory."
WARN_BROKEN_LINK_TITLE = "Broken Link"
WARN_BROKEN_LINK_MSG = "Could not resolve symbolic link target:\n{path}"
INFO_SYMLINK_TITLE = "Symbolic Link Target"
INFO_SYMLINK_MSG = "Target:\n{target_path}"
