# about_window.py
import tkinter as tk
from tkinter import ttk, font
import webbrowser
import datetime
import config # Import configuration constants

def show_about_window(parent_window):
    """
    Displays the modal About window.

    Args:
        parent_window: The parent tk.Tk or tk.Toplevel window.
    """
    about_win = tk.Toplevel(parent_window)
    about_win.title(f"About {config.APP_TITLE}")
    about_win.geometry("450x300") # Adjusted size for links
    about_win.resizable(False, False)

    # Make the window modal
    about_win.grab_set()
    about_win.transient(parent_window)

    frame = ttk.Frame(about_win, padding="15")
    frame.pack(expand=True, fill=tk.BOTH)

    # Title
    title_font = font.Font(family="TkDefaultFont", size=14, weight="bold")
    title_label = ttk.Label(frame, text=config.APP_TITLE, font=title_font, anchor=tk.CENTER)
    title_label.pack(pady=(0, 10), fill=tk.X)

    # Version
    version_label = ttk.Label(frame, text=f"Version: {config.APP_VERSION}", anchor=tk.CENTER)
    version_label.pack(pady=2, fill=tk.X)

    # Release Date (Current Date) - Use today's date
    # Getting current time based on external information: Sunday, May 4, 2025 at 7:43:14 PM WIB
    # Displaying only the date part as per original format seems more appropriate for a release date.
    release_date = datetime.date(2025, 5, 4).strftime("%Y-%m-%d, %A") # Using provided date
    date_label = ttk.Label(frame, text=f"Release Date: {release_date}", anchor=tk.CENTER)
    date_label.pack(pady=2, fill=tk.X)

    # Author
    author_label = ttk.Label(frame, text=f"Author: {config.AUTHOR_NAME}", anchor=tk.CENTER)
    author_label.pack(pady=(2, 10), fill=tk.X) # Added bottom padding

    # --- Links Frame ---
    links_frame = ttk.Frame(frame)
    links_frame.pack(pady=5, fill=tk.X)

    # GitHub Link
    github_label_text = ttk.Label(links_frame, text="GitHub:")
    github_label_text.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
    github_link_label = ttk.Label(links_frame, text=config.GITHUB_URL, foreground="blue", cursor="hand2")
    github_link_label.grid(row=0, column=1, sticky=tk.W)
    github_link_label.bind("<Button-1>", lambda e, link=config.GITHUB_URL: webbrowser.open_new(link))

    # LinkedIn Link
    linkedin_label_text = ttk.Label(links_frame, text="LinkedIn:")
    linkedin_label_text.grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5,0)) # Add top padding
    linkedin_link_label = ttk.Label(links_frame, text=config.LINKEDIN_URL, foreground="blue", cursor="hand2")
    linkedin_link_label.grid(row=1, column=1, sticky=tk.W, pady=(5,0)) # Add top padding
    linkedin_link_label.bind("<Button-1>", lambda e, link=config.LINKEDIN_URL: webbrowser.open_new(link))

    # Center the links within the links_frame (optional, adjust column weights if needed)
    # links_frame.grid_columnconfigure(0, weight=1) # Might push text left
    # links_frame.grid_columnconfigure(1, weight=1) # Might push links right

    # OK Button
    ok_button = ttk.Button(frame, text="OK", command=about_win.destroy, width=10)
    ok_button.pack(pady=(20, 0)) # Increased top padding

    # Center the About window relative to the parent window
    about_win.update_idletasks() # Ensure window dimensions are calculated
    parent_x = parent_window.winfo_x()
    parent_y = parent_window.winfo_y()
    parent_width = parent_window.winfo_width()
    parent_height = parent_window.winfo_height()
    about_width = about_win.winfo_width()
    about_height = about_win.winfo_height()

    x = parent_x + (parent_width // 2) - (about_width // 2)
    y = parent_y + (parent_height // 2) - (about_height // 2)
    about_win.geometry(f"+{x}+{y}")

    # Wait for the window to be closed before returning
    parent_window.wait_window(about_win)
