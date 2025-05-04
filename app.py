# app.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import os
import threading
import platform
from pathlib import Path
import sys
import datetime
import subprocess
import webbrowser

# Import custom modules
import config
import utils
import about_window

class FolderExplorerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(config.APP_TITLE)
        self.root.geometry("1000x700")

        # --- Style ---
        self.style = ttk.Style()
        available_themes = self.style.theme_names()
        if platform.system() == "Windows":
            if 'vista' in available_themes: self.style.theme_use('vista')
            elif 'xpnative' in available_themes: self.style.theme_use('xpnative')
            elif 'clam' in available_themes: self.style.theme_use('clam')
        elif platform.system() == "Darwin":
             if 'aqua' in available_themes: self.style.theme_use('aqua')
             elif 'clam' in available_themes: self.style.theme_use('clam')
        elif 'clam' in available_themes:
            self.style.theme_use('clam')

        # --- Variables ---
        self.current_path = tk.StringVar(value=config.INITIAL_DIR)
        try:
            resolved_initial = str(Path(config.INITIAL_DIR).resolve())
            self.history = [resolved_initial]
            self.current_path.set(resolved_initial)
        except Exception:
             self.history = [config.INITIAL_DIR]
        self.view_style = tk.StringVar(value="Details")
        self._threads_lock = threading.Lock()
        self._calculation_threads = {}
        # ** Default sort by the new 'name' column **
        self._tree_sort_column = "name"
        self._tree_sort_reverse = False
        self.status_var = tk.StringVar(value=config.STATUS_READY)

        # --- GUI Setup ---
        self.setup_ui()

        # --- Initial View and Load ---
        self.switch_content_view() # Place the initial view (Details)
        self.populate_nav_tree()
        self.select_nav_tree_item(self.current_path.get(), initial_load=True)


    def setup_ui(self):
        """Creates and arranges the widgets."""
        # --- Top Frame ---
        top_frame = ttk.Frame(self.root, padding="5")
        top_frame.pack(side=tk.TOP, fill=tk.X)

        self.back_button = ttk.Button(top_frame, text="← Back", command=self.go_back, state=tk.DISABLED)
        self.back_button.pack(side=tk.LEFT, padx=(0, 5))
        self.up_button = ttk.Button(top_frame, text="↑ Up", command=self.go_up, state=tk.DISABLED)
        self.up_button.pack(side=tk.LEFT, padx=(0, 5))
        path_label = ttk.Label(top_frame, text="Path:")
        path_label.pack(side=tk.LEFT, padx=(5, 5))
        self.path_entry = ttk.Entry(top_frame, textvariable=self.current_path)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.path_entry.bind("<Return>", self.navigate_from_entry)
        self.path_entry.bind("<FocusOut>", lambda e: self.current_path.set(self.history[-1] if self.history else config.INITIAL_DIR))
        view_label = ttk.Label(top_frame, text="View:")
        view_label.pack(side=tk.LEFT, padx=(0, 5))
        view_options = ["Details", "List"]
        view_combo = ttk.Combobox(top_frame, textvariable=self.view_style, values=view_options, state="readonly", width=10)
        view_combo.pack(side=tk.LEFT, padx=(0, 5))
        view_combo.bind("<<ComboboxSelected>>", self.on_view_style_change)
        about_button = ttk.Button(top_frame, text="About", command=lambda: about_window.show_about_window(self.root))
        about_button.pack(side=tk.LEFT, padx=(5, 0))

        # --- Main Paned Window ---
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # --- Left Frame (Navigation Tree) ---
        nav_frame = ttk.Frame(self.paned_window, padding=(2, 0, 0, 0))
        self.paned_window.add(nav_frame, weight=1)
        self.nav_tree = ttk.Treeview(nav_frame, show="tree", selectmode="browse")
        nav_ysb = ttk.Scrollbar(nav_frame, orient="vertical", command=self.nav_tree.yview)
        nav_xsb = ttk.Scrollbar(nav_frame, orient="horizontal", command=self.nav_tree.xview)
        self.nav_tree.configure(yscrollcommand=nav_ysb.set, xscrollcommand=nav_xsb.set)
        self.nav_tree.grid(row=0, column=0, sticky='nsew')
        nav_ysb.grid(row=0, column=1, sticky='ns')
        nav_xsb.grid(row=1, column=0, sticky='ew')
        nav_frame.grid_rowconfigure(0, weight=1)
        nav_frame.grid_columnconfigure(0, weight=1)
        self.nav_tree.bind("<<TreeviewSelect>>", self.on_nav_tree_select)
        self.nav_tree.bind("<<TreeviewOpen>>", self.on_nav_tree_expand)

        # --- Right Frame (Content Panel) ---
        self.content_frame = ttk.Frame(self.paned_window, padding=(0, 0, 2, 0))
        self.paned_window.add(self.content_frame, weight=3)
        self.create_content_widgets() # Create the widgets
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # --- Status Bar ---
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding="2")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)


    def create_content_widgets(self):
        """Creates the widgets for the different view styles in the content panel."""
        # --- Details View Widget ---
        # ** Use updated columns from config, which now includes 'name' **
        self.details_tree = ttk.Treeview(self.content_frame, columns=config.TREEVIEW_COLUMNS_DETAILS, show="headings")

        # ** Configure Headings and Columns based on config for Details view **
        for col in config.TREEVIEW_COLUMNS_DETAILS:
            text = config.DETAILS_HEADINGS.get(col, col.capitalize())
            anchor_str = config.DETAILS_ANCHORS.get(col, "w")
            width = config.DETAILS_WIDTHS.get(col, 100)
            stretch_bool = config.DETAILS_STRETCH.get(col, False)
            anchor_tk = tk.W if anchor_str == "w" else tk.E if anchor_str == "e" else tk.CENTER
            stretch_tk = tk.YES if stretch_bool else tk.NO

            # ** Set command for sorting based on the *column identifier* (e.g., 'name', 'size') **
            self.details_tree.heading(col, text=text, anchor=anchor_tk, command=lambda c=col: self.sort_content_column(c, False))
            self.details_tree.column(col, width=width, stretch=stretch_tk, anchor=anchor_tk)

        # --- List View Widget ---
        # ** Use updated columns from config, which now includes 'name' **
        self.list_tree = ttk.Treeview(self.content_frame, columns=config.TREEVIEW_COLUMNS_LIST, show="headings")

        # ** Configure Headings and Columns based on config for List view **
        for col in config.TREEVIEW_COLUMNS_LIST:
            text = config.LIST_HEADINGS.get(col, col.capitalize())
            anchor_str = config.LIST_ANCHORS.get(col, "w")
            width = config.LIST_WIDTHS.get(col, 100)
            stretch_bool = config.LIST_STRETCH.get(col, False)
            anchor_tk = tk.W if anchor_str == "w" else tk.E if anchor_str == "e" else tk.CENTER
            stretch_tk = tk.YES if stretch_bool else tk.NO

            # ** Set command for sorting based on the *column identifier* (e.g., 'name', 'size') **
            self.list_tree.heading(col, text=text, anchor=anchor_tk, command=lambda c=col: self.sort_content_column(c, False))
            self.list_tree.column(col, width=width, stretch=stretch_tk, anchor=anchor_tk)

        # --- Scrollbars (Common for content views) ---
        self.content_vsb = ttk.Scrollbar(self.content_frame, orient="vertical")
        self.content_hsb = ttk.Scrollbar(self.content_frame, orient="horizontal")

        # --- Bindings ---
        self.details_tree.bind("<Double-1>", self.on_content_double_click)
        self.list_tree.bind("<Double-1>", self.on_content_double_click)


    def switch_content_view(self):
        """Hides old view, shows and configures the new view based on self.view_style."""
        self.details_tree.grid_forget()
        self.list_tree.grid_forget()
        self.content_vsb.grid_forget()
        self.content_hsb.grid_forget()

        current_view_widget = None
        if self.view_style.get() == "Details":
            current_view_widget = self.details_tree
        elif self.view_style.get() == "List":
            current_view_widget = self.list_tree

        if current_view_widget:
            self.content_vsb.config(command=current_view_widget.yview)
            self.content_hsb.config(command=current_view_widget.xview)
            current_view_widget.configure(yscrollcommand=self.content_vsb.set, xscrollcommand=self.content_hsb.set)
            current_view_widget.grid(row=0, column=0, sticky='nsew')
            self.content_vsb.grid(row=0, column=1, sticky='ns')
            self.content_hsb.grid(row=1, column=0, sticky='ew')
        else:
             messagebox.showinfo("View Error", f"Selected view '{self.view_style.get()}' is not available.")


    def on_view_style_change(self, event=None):
        """Called when the view style combobox changes."""
        self.switch_content_view()
        self.load_directory_content(self.current_path.get(), update_history=False, force_reload=True)


    # --- Navigation Methods --- (No changes needed in navigate_from_entry, browse_directory, go_back, go_up, update_nav_buttons_state)
    def navigate_from_entry(self, event=None):
        """Attempts to navigate to the path entered in the path entry."""
        path = self.path_entry.get().strip()
        path_obj = Path(path)
        try:
            if path_obj.is_dir():
                norm_path = str(path_obj.resolve())
                current_norm_path = str(Path(self.current_path.get()).resolve())

                if norm_path != current_norm_path:
                    if not self.history or norm_path != self.history[-1]:
                        self.history.append(norm_path)
                    self.select_nav_tree_item(norm_path)
                    self.update_nav_buttons_state()
                else:
                    self.root.focus_set()
            else:
                messagebox.showerror(config.ERROR_INVALID_PATH_TITLE,
                                     config.ERROR_INVALID_PATH_MSG.format(path=path))
                self.current_path.set(self.history[-1] if self.history else config.INITIAL_DIR)
        except (OSError, Exception) as e:
            messagebox.showerror(config.ERROR_ACCESS_PATH_TITLE,
                                 config.ERROR_ACCESS_PATH_MSG.format(path=path, error=e))
            self.current_path.set(self.history[-1] if self.history else config.INITIAL_DIR)
        finally:
             if self.root.focus_get() == self.path_entry:
                 self.root.focus_set()

    def browse_directory(self):
        """Opens a dialog to select a directory."""
        new_dir = filedialog.askdirectory(initialdir=self.current_path.get(), title="Select Folder")
        if new_dir:
             try:
                path_obj = Path(new_dir)
                if path_obj.is_dir():
                    norm_path = str(path_obj.resolve())
                    if not self.history or norm_path != self.history[-1]:
                        self.history.append(norm_path)
                    self.select_nav_tree_item(norm_path)
                    self.update_nav_buttons_state()
             except (OSError, Exception) as e:
                 messagebox.showerror(config.ERROR_ACCESS_PATH_TITLE,
                                      config.ERROR_ACCESS_PATH_MSG.format(path=new_dir, error=e))

    def go_back(self):
        """Navigates to the previous directory in history."""
        if len(self.history) > 1:
            self.history.pop()
            prev_dir = self.history[-1]
            self.select_nav_tree_item(prev_dir)
            self.update_nav_buttons_state()

    def go_up(self):
        """Navigates to the parent directory."""
        try:
            current = Path(self.current_path.get()).resolve()
            parent = current.parent
            if parent != current and parent.is_dir():
                parent_str = str(parent)
                if not self.history or parent_str != self.history[-1]:
                    self.history.append(parent_str)
                self.select_nav_tree_item(parent_str)
                self.update_nav_buttons_state()
        except (OSError, Exception) as e:
            print(f"Error going up from {self.current_path.get()}: {e}")
            messagebox.showwarning(config.WARN_NAV_TITLE, config.WARN_NAV_PARENT_MSG)

    def update_nav_buttons_state(self):
        """Enables/disables the Back and Up buttons based on history and current path."""
        self.back_button.config(state=tk.NORMAL if len(self.history) > 1 else tk.DISABLED)
        can_go_up = False
        try:
            current = Path(self.current_path.get()).resolve()
            parent = current.parent
            can_go_up = (parent != current and parent.is_dir())
        except (OSError, Exception):
            can_go_up = False
        self.up_button.config(state=tk.NORMAL if can_go_up else tk.DISABLED)


    # --- Navigation Tree Methods --- (No changes needed in populate_nav_tree, insert_dummy_nav_child, on_nav_tree_expand, on_nav_tree_select, select_nav_tree_item)
    def populate_nav_tree(self, parent_id="", parent_path=None):
        """Populates the navigation tree with directories. If parent_path is None, populates roots."""
        target_node = parent_id if parent_id else ""
        if parent_id:
            try:
                children = self.nav_tree.get_children(parent_id)
                for child_id in children:
                    try:
                        if self.nav_tree.exists(child_id):
                           item_text = self.nav_tree.item(child_id, 'text')
                           if item_text == config.DUMMY_NODE_TEXT:
                               self.nav_tree.delete(child_id)
                    except tk.TclError: continue
            except tk.TclError as e: print(f"Error getting children for nav node {parent_id}: {e}"); return

        path_to_list = parent_path
        if path_to_list is None:
            try:
                for item in self.nav_tree.get_children(): self.nav_tree.delete(item)
            except tk.TclError as e: print(f"Error clearing nav tree: {e}")
            root_items = []
            if platform.system() == "Windows":
                drives = [f"{chr(c)}:\\" for c in range(ord('A'), ord('Z') + 1) if Path(f"{chr(c)}:\\").exists()]
                for drive in drives:
                     try: res_drive = str(Path(drive).resolve()); root_items.append({'text': drive, 'iid': res_drive})
                     except Exception as e: print(f"Error resolving drive {drive}: {e}")
            else: # Linux/macOS
                try: home_dir = str(Path.home().resolve()); root_items.append({'text': "~ Home", 'iid': home_dir})
                except Exception as e: print(f"Error adding home directory: {e}")
                try: root_dir = "/"; root_items.append({'text': "/ Root", 'iid': root_dir})
                except Exception as e: print(f"Error adding root directory: {e}")
                for place in ["/media", "/mnt"]:
                    try:
                        p_path = Path(place)
                        if p_path.is_dir(): res_place = str(p_path.resolve()); root_items.append({'text': p_path.name, 'iid': res_place})
                    except Exception as e: print(f"Error adding common place {place}: {e}")
            for item in root_items:
                try: node_id = self.nav_tree.insert(target_node, "end", text=item['text'], iid=item['iid'], open=False); self.insert_dummy_nav_child(node_id, item['iid'])
                except Exception as e: print(f"Error inserting nav root {item['text']}: {e}")
            return # End of initial population

        # --- Expanding an existing node ---
        try:
            path_obj = Path(path_to_list)
            if not path_obj.is_dir(): print(f"Error: Cannot expand nav node, path is not a directory: {path_to_list}"); return
            subdirs = []
            try:
                with os.scandir(path_obj) as it:
                    for entry in it:
                        try:
                            if entry.is_dir(follow_symlinks=False): subdirs.append({'name': entry.name, 'path': entry.path})
                        except OSError: continue
            except OSError as e: print(f"Error scanning directory for nav expansion {path_obj}: {e}"); return
            subdirs.sort(key=lambda x: x['name'].lower())
            for subdir in subdirs:
                try:
                    res_path = str(Path(subdir['path']).resolve())
                    if not self.nav_tree.exists(res_path):
                         node_id = self.nav_tree.insert(parent_id, "end", text=subdir['name'], iid=res_path, open=False)
                         self.insert_dummy_nav_child(node_id, res_path)
                except Exception as e: print(f"Skipping nav item insert for {subdir['name']} under {parent_id}: {e}")
        except Exception as e: print(f"Error expanding navigation tree node {path_to_list}: {e}")

    def insert_dummy_nav_child(self, node_id, path):
        """Inserts a dummy '...' node if the directory at 'path' contains subdirectories."""
        try:
            if not self.nav_tree.exists(node_id): return
            if self.nav_tree.get_children(node_id): return
            path_obj = Path(path)
            has_subdirs = False
            try:
                with os.scandir(path_obj) as it: has_subdirs = any(entry.is_dir(follow_symlinks=False) for entry in it)
            except (OSError, FileNotFoundError): pass
            if has_subdirs and self.nav_tree.exists(node_id):
                if not self.nav_tree.get_children(node_id):
                     dummy_iid = f"{node_id}_dummy"
                     if not self.nav_tree.exists(dummy_iid): self.nav_tree.insert(node_id, "end", text=config.DUMMY_NODE_TEXT, iid=dummy_iid)
        except tk.TclError: pass
        except Exception as e: print(f"Error checking/inserting dummy node for {path}: {e}")

    def on_nav_tree_expand(self, event=None):
        """Callback when a node in the navigation tree is expanded."""
        node_id = self.nav_tree.focus()
        if node_id:
            try:
                children = self.nav_tree.get_children(node_id)
                if len(children) == 1:
                    dummy_id = children[0]
                    if self.nav_tree.exists(dummy_id) and self.nav_tree.item(dummy_id, 'text') == config.DUMMY_NODE_TEXT:
                        self.populate_nav_tree(parent_id=node_id, parent_path=node_id)
            except tk.TclError as e: print(f"Error handling nav expand event for {node_id}: {e}")

    def on_nav_tree_select(self, event=None):
        """Callback when a node in the navigation tree is selected."""
        selected_id = self.nav_tree.focus()
        if selected_id:
            try:
                path_obj = Path(selected_id)
                if path_obj.is_dir():
                    norm_path = str(path_obj.resolve())
                    current_norm_path = str(Path(self.current_path.get()).resolve())
                    if norm_path != current_norm_path:
                        if not self.history or norm_path != self.history[-1]: self.history.append(norm_path)
                        self.load_directory_content(norm_path, update_history=False)
                        self.update_nav_buttons_state()
            except tk.TclError as e: print(f"Error processing nav selection (TclError) {selected_id}: {e}")
            except (OSError, Exception) as e: print(f"Error processing nav selection {selected_id}: {e}"); self._revert_to_valid_history()

    def select_nav_tree_item(self, path_to_select, initial_load=False):
        """Expands parent nodes and selects the item corresponding to path_to_select."""
        try: norm_path = str(Path(path_to_select).resolve())
        except Exception as e:
            print(f"Error resolving path for nav selection {path_to_select}: {e}")
            if initial_load: self.load_directory_content(config.INITIAL_DIR); self.update_nav_buttons_state()
            return
        def expand_parents(item_id):
            try:
                parent = self.nav_tree.parent(item_id)
                if parent:
                    expand_parents(parent)
                    if self.nav_tree.exists(parent) and not self.nav_tree.item(parent, 'open'):
                        self.nav_tree.item(parent, open=True)
                        children = self.nav_tree.get_children(parent)
                        if len(children) == 1:
                            dummy_id = children[0]
                            if self.nav_tree.exists(dummy_id) and self.nav_tree.item(dummy_id, 'text') == config.DUMMY_NODE_TEXT:
                                 self.populate_nav_tree(parent_id=parent, parent_path=parent)
            except tk.TclError: pass
            except Exception as e: print(f"Error in expand_parents for {item_id}: {e}")
        try:
            if self.nav_tree.exists(norm_path):
                expand_parents(norm_path)
                self.nav_tree.selection_set(norm_path)
                self.nav_tree.focus(norm_path)
                self.root.after(50, lambda p=norm_path: self.nav_tree.see(p) if self.nav_tree.exists(p) else None)
                try: current_resolved = str(Path(self.current_path.get()).resolve())
                except Exception: current_resolved = None
                if (initial_load and norm_path != current_resolved) or (not initial_load and norm_path != current_resolved):
                     self.load_directory_content(norm_path, update_history=(not initial_load))
                     self.update_nav_buttons_state()
                elif initial_load: self.update_nav_buttons_state()
            else:
                print(f"Nav item {norm_path} not found directly. Attempting to find parent.")
                parent_path = Path(norm_path)
                found_parent = False
                while parent_path != parent_path.parent:
                    parent_path = parent_path.parent
                    parent_str = str(parent_path)
                    if self.nav_tree.exists(parent_str):
                         print(f"Found existing parent: {parent_str}")
                         expand_parents(parent_str)
                         self.nav_tree.selection_set(parent_str)
                         self.nav_tree.focus(parent_str)
                         self.root.after(50, lambda p=parent_str: self.nav_tree.see(p) if self.nav_tree.exists(p) else None)
                         try: current_resolved = str(Path(self.current_path.get()).resolve())
                         except Exception: current_resolved = None
                         if parent_str != current_resolved:
                             if not self.history or parent_str != self.history[-1]: self.history.append(parent_str)
                             self.load_directory_content(parent_str, update_history=False)
                             self.update_nav_buttons_state()
                         found_parent = True
                         break
                if not found_parent:
                    print(f"Could not find item or any existing parent for {norm_path} in nav tree.")
                    if initial_load: self.load_directory_content(config.INITIAL_DIR); self.update_nav_buttons_state()
        except tk.TclError as e:
             print(f"Error selecting nav item (TclError) {norm_path}: {e}")
             if initial_load: self.load_directory_content(config.INITIAL_DIR); self.update_nav_buttons_state()
        except Exception as e:
             print(f"General error selecting nav item {norm_path}: {e}")
             if initial_load: self.load_directory_content(config.INITIAL_DIR); self.update_nav_buttons_state()


    # --- Content Loading & Handling ---

    def load_directory_content(self, path, update_history=True, force_reload=False):
        """Loads the content of the specified directory path into the active content Treeview."""
        try:
            path_obj = Path(path)
            norm_path = str(path_obj.resolve())
        except Exception as e:
            messagebox.showerror(config.ERROR_INVALID_PATH_TITLE, f"Path resolution error:\n{path}\n{e}")
            self._revert_to_valid_history()
            return

        try: current_resolved = str(Path(self.current_path.get()).resolve())
        except Exception: current_resolved = None

        if norm_path == current_resolved and not force_reload:
            self.current_path.set(norm_path)
            self.update_nav_buttons_state()
            return

        if not path_obj.is_dir():
            messagebox.showerror(config.ERROR_INVALID_PATH_TITLE, f"Not a directory:\n{norm_path}")
            self._revert_to_valid_history()
            return

        self.current_path.set(norm_path)
        if update_history:
            if not self.history or norm_path != self.history[-1]: self.history.append(norm_path)

        active_tree = self.details_tree if self.view_style.get() == "Details" else self.list_tree
        if not active_tree: print("Error: No active content view widget found."); self.update_nav_buttons_state(); return

        try:
            if active_tree.winfo_exists():
                 children_to_delete = active_tree.get_children('')
                 if children_to_delete: active_tree.delete(*children_to_delete)
            else: return
        except tk.TclError as e: print(f"Error clearing content tree: {e}")

        with self._threads_lock: self._calculation_threads.clear()

        self.status_var.set(config.STATUS_LOADING.format(name=path_obj.name))
        self.root.update_idletasks()

        items_data = []
        perm_error_encountered = False
        access_error_encountered = False

        try:
            with os.scandir(norm_path) as it:
                for entry in it:
                    info = {"name": entry.name, "path": entry.path, "is_symlink": entry.is_symlink()}
                    try:
                        stat_info = entry.stat(follow_symlinks=False)
                        is_dir = entry.is_dir(follow_symlinks=False)
                        if info["is_symlink"]: type_ = "Symbolic Link"
                        elif is_dir: type_ = "Folder"
                        else: type_ = "File"
                        size_bytes = None
                        if not is_dir and not info["is_symlink"]: size_bytes = stat_info.st_size
                        # Get current time using external info: Sunday, May 4, 2025 at 7:50:19 PM WIB
                        mod_time = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime(config.DATE_FORMAT) # Use real mtime
                        info.update({"is_dir": is_dir and not info["is_symlink"], "type": type_, "size": size_bytes, "modified": mod_time})
                    except PermissionError: info.update({"type": "Inaccessible", "size": None, "modified": "N/A", "is_dir": False}); perm_error_encountered = True
                    except (FileNotFoundError, OSError) as e: print(f"Error stating {entry.path}: {e}"); info.update({"type": "Error", "size": None, "modified": "N/A", "is_dir": False}); access_error_encountered = True
                    items_data.append(info)
        except PermissionError as e: messagebox.showerror(config.ERROR_LISTING_TITLE, f"Permission denied listing directory:\n{norm_path}\n\n{e}"); self.status_var.set(config.STATUS_PERM_ERROR); self._revert_to_valid_history(); return
        except FileNotFoundError as e: messagebox.showerror(config.ERROR_LISTING_TITLE, f"Directory not found:\n{norm_path}\n\n{e}"); self.status_var.set(config.STATUS_ERROR); self._revert_to_valid_history(); return
        except Exception as e: messagebox.showerror(config.ERROR_LISTING_TITLE, config.ERROR_LISTING_MSG.format(path=norm_path, error=e)); self.status_var.set(config.STATUS_ERROR); self.update_nav_buttons_state()

        threads_started = 0
        requires_size_calc = (self.view_style.get() == "Details")

        for item in items_data:
            name = item["name"]
            fpath = item["path"]
            type_ = item["type"]
            is_dir = item.get("is_dir", False)
            size_bytes = item["size"]
            mod = item["modified"]
            is_symlink = item["is_symlink"]

            display_size = "N/A"; should_calculate = False
            if type_ not in ["Inaccessible", "Error"]:
                 if is_dir and requires_size_calc: display_size = "Calculating..."; should_calculate = True
                 elif is_symlink: display_size = "N/A"
                 elif size_bytes is not None: display_size = utils.format_size(size_bytes)
                 elif not is_dir and not is_symlink: display_size = "Error"

            try:
                if not active_tree.winfo_exists(): break

                # ** Prepare values tuple including the name for the first column **
                if active_tree == self.details_tree:
                    values_tuple = (name, display_size, type_, mod) # Name first
                else: # List view
                     values_tuple = (name, display_size) # Name first

                tags = [];
                if is_dir: tags.append('folder')
                elif is_symlink: tags.append('symlink')
                else: tags.append('file')
                if type_ in ["Inaccessible", "Error"]: tags.append('error')

                # ** Insert item: text=name for hidden #0, values=values_tuple for visible columns **
                item_id = active_tree.insert("", tk.END, text=name, values=values_tuple, iid=fpath, tags=tuple(tags))

                if should_calculate:
                     thread = threading.Thread(target=self.calculate_and_update_size, args=(item_id, fpath, active_tree), daemon=True)
                     with self._threads_lock: self._calculation_threads[item_id] = thread
                     thread.start()
                     threads_started += 1
            except tk.TclError as e: print(f"Error inserting item '{name}' into tree: {e}"); continue
            except Exception as e: print(f"General error processing/inserting item {name}: {e}"); continue

        if self._tree_sort_column:
             self.sort_content_column(self._tree_sort_column, self._tree_sort_reverse, initial_sort=True)

        final_status = config.STATUS_READY
        if threads_started > 0:
             plural = 's' if threads_started != 1 else ''
             final_status = config.STATUS_CALCULATING.format(count=threads_started, plural=plural)
             self.root.after(2000 + threads_started * 50, self._check_calculation_status)
        elif perm_error_encountered and access_error_encountered: final_status = config.STATUS_BOTH_ERROR
        elif perm_error_encountered: final_status = config.STATUS_PERM_ERROR
        elif access_error_encountered: final_status = config.STATUS_ACCESS_ERROR
        self.status_var.set(final_status)
        self.update_nav_buttons_state()


    def _revert_to_valid_history(self):
        """Attempts to navigate back in history to the first valid directory found."""
        if len(self.history) <= 1:
             try:
                 if not Path(self.current_path.get()).is_dir():
                      resolved_initial = str(Path(config.INITIAL_DIR).resolve())
                      self.history = [resolved_initial]
                      self.load_directory_content(resolved_initial, update_history=False)
                      self.select_nav_tree_item(resolved_initial)
                      self.update_nav_buttons_state()
                      return
             except Exception:
                  self.current_path.set("Error: No valid path found")
                  self.history = []
                  self.update_nav_buttons_state()
             return
        original_length = len(self.history)
        for i in range(len(self.history) - 2, -1, -1):
            prev_dir = self.history[i]
            try:
                if Path(prev_dir).is_dir():
                    self.history = self.history[:i+1]
                    self.select_nav_tree_item(prev_dir)
                    self.update_nav_buttons_state()
                    return
            except OSError: continue
        print("Revert Error: Could not find any valid directory in history.")
        try:
             resolved_initial = str(Path(config.INITIAL_DIR).resolve())
             self.history = [resolved_initial]
             self.load_directory_content(resolved_initial, update_history=False)
             self.select_nav_tree_item(resolved_initial)
             self.update_nav_buttons_state()
        except Exception as e:
             print(f"Fallback to INITIAL_DIR failed during revert: {e}")
             self.current_path.set("Error: No valid path accessible")
             self.history = []
             self.update_nav_buttons_state()

    def _check_calculation_status(self):
        """Checks if folder size calculation threads are still running and updates status."""
        if not self.root.winfo_exists(): return
        with self._threads_lock:
            if not self._calculation_threads:
                if config.STATUS_CALCULATING.split('{')[0] in self.status_var.get():
                    self.status_var.set(config.STATUS_READY)
            else:
                 self.root.after(2000, self._check_calculation_status)

    def calculate_and_update_size(self, item_id, folder_path, target_tree):
        """(Thread Target) Calculates folder size and schedules UI update."""
        calculated_size_bytes = None; formatted_size = "Error"
        try:
            calculated_size_bytes = utils.get_folder_size(folder_path)
            if calculated_size_bytes is not None: formatted_size = utils.format_size(calculated_size_bytes)
            else: formatted_size = "N/A"
        except Exception as e: print(f"Error calculating size for thread {folder_path}: {e}"); formatted_size = "Error"
        finally:
            try:
                if target_tree.winfo_exists():
                     # Pass raw bytes for potential future use in sorting
                     self.root.after(0, self.update_tree_item_size, item_id, formatted_size, calculated_size_bytes, target_tree)
            except Exception as e: print(f"Error scheduling size update for {item_id}: {e}")
            with self._threads_lock:
                if item_id in self._calculation_threads: del self._calculation_threads[item_id]
                if not self._calculation_threads:
                    if config.STATUS_CALCULATING.split('{')[0] in self.status_var.get():
                        self.root.after(10, lambda: self.status_var.set(config.STATUS_READY))


    def update_tree_item_size(self, item_id, formatted_size, size_bytes, target_tree):
        """(Main Thread) Updates the size value in the specified Treeview item."""
        try:
             if target_tree.winfo_exists() and target_tree.exists(item_id):
                 # ** Update the 'size' column specifically **
                 target_tree.set(item_id, column="size", value=formatted_size)
                 # TODO: Store size_bytes if needed for more accurate size sorting later
        except tk.TclError: pass
        except Exception as e: print(f"Error updating tree item size for {item_id}: {e}")


    def on_content_double_click(self, event):
        """Handles double-clicking on an item in the content view."""
        active_tree = event.widget; item_id = active_tree.focus()
        if not item_id: return
        try:
            path_obj = Path(item_id)
            if path_obj.is_dir() and not path_obj.is_symlink():
                norm_path = str(path_obj.resolve())
                if not self.history or norm_path != self.history[-1]: self.history.append(norm_path)
                self.select_nav_tree_item(norm_path)
                self.update_nav_buttons_state()
            elif path_obj.is_file() and not path_obj.is_symlink():
                try:
                    resolved_path_str = str(path_obj.resolve())
                    if platform.system() == "Windows": os.startfile(resolved_path_str)
                    elif platform.system() == "Darwin": subprocess.call(["open", resolved_path_str])
                    else: subprocess.call(["xdg-open", resolved_path_str])
                except FileNotFoundError: messagebox.showerror(config.ERROR_OPEN_FILE_TITLE, f"File not found:\n{resolved_path_str}")
                except Exception as e: messagebox.showerror(config.ERROR_OPEN_FILE_TITLE, config.ERROR_OPEN_FILE_MSG.format(path=item_id, error=e))
            elif path_obj.is_symlink():
                 try:
                     target_path = str(path_obj.resolve())
                     messagebox.showinfo(config.INFO_SYMLINK_TITLE, config.INFO_SYMLINK_MSG.format(target_path=target_path))
                 except FileNotFoundError: messagebox.showwarning(config.WARN_BROKEN_LINK_TITLE, config.WARN_BROKEN_LINK_MSG.format(path=item_id))
                 except Exception as e: messagebox.showerror("Link Resolution Error", f"Could not resolve link:\n{item_id}\n\n{e}")
        except Exception as e: messagebox.showwarning(config.WARN_NAV_TITLE, f"Error processing double-click:\n{e}")


    # --- Sorting ---
    def sort_content_column(self, col, reverse, initial_sort=False):
        """Sorts the active content treeview by the specified column."""
        active_tree = self.details_tree if self.view_style.get() == "Details" else self.list_tree
        if not active_tree or not isinstance(active_tree, ttk.Treeview) or not active_tree.winfo_exists():
             print("Sort Error: Active treeview not available."); return

        if not initial_sort:
            self._tree_sort_column = col; self._tree_sort_reverse = reverse

        data = []
        try:
            children = active_tree.get_children('')
            if not children: return
            for item_id in children:
                 if not active_tree.exists(item_id): continue
                 # ** Get value using set() for the specified column identifier ('name', 'size', etc.) **
                 try: sort_val = active_tree.set(item_id, col)
                 except tk.TclError: sort_val = None # Column might not exist? Should not happen here.
                 data.append((sort_val, item_id))
        except tk.TclError as e: print(f"Error gathering data for sorting: {e}"); return

        def get_sort_key(item_tuple):
            val_str, item_id = item_tuple
            # --- Size Column Sorting ---
            if col == 'size':
                if val_str == "Calculating...": return -3
                if val_str == "Error": return -2
                if val_str == "N/A": return -1
                try:
                    parts = val_str.split()
                    if len(parts) == 2:
                        num_str, unit = parts; num = float(num_str.replace(',', '')); unit = unit.upper()
                        if unit in config.SIZE_UNITS: return int(num * (1024**config.SIZE_UNITS.index(unit)))
                        elif val_str == f"0 {config.SIZE_UNITS[0]}": return 0
                    elif val_str == f"0 {config.SIZE_UNITS[0]}": return 0
                except (ValueError, IndexError, TypeError): print(f"Debug sort: Could not parse size '{val_str}' for {item_id}"); return -2
                return -2
            # --- Date Modified Column Sorting ---
            elif col == 'modified':
                 min_dt = datetime.datetime.min
                 if val_str == "N/A": return min_dt
                 try: return datetime.datetime.strptime(val_str, config.DATE_FORMAT)
                 except (ValueError, TypeError): return min_dt
            # --- Name ('name') or Type ('type') Column Sorting (Case-insensitive) ---
            # ** Handles 'name' column explicitly along with other string-based columns like 'type' **
            elif col == 'name' or col == 'type':
                 return str(val_str).lower()
            # --- Fallback for any other column (shouldn't happen with current config) ---
            else:
                 return str(val_str).lower() # Default case-insensitive string sort

        try: data.sort(key=get_sort_key, reverse=reverse)
        except Exception as e: print(f"Error during sorting operation: {e}"); return

        try:
            for idx, (sort_val_ignore, item_id) in enumerate(data):
                 if active_tree.exists(item_id): active_tree.move(item_id, '', idx)
        except tk.TclError as e: print(f"Error moving items during sort update: {e}")
        except Exception as e: print(f"General error reordering tree items after sort: {e}")

        try: active_tree.heading(col, command=lambda c=col: self.sort_content_column(c, not reverse))
        except tk.TclError: pass
