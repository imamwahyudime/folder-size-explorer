# main.py
import tkinter as tk
from tkinter import font
from app import FolderExplorerApp # Import the main application class
# import config # Only import if needed for main setup (e.g., initial font size)

if __name__ == "__main__":
    # Create the main application window
    root = tk.Tk()

    # --- Optional: Adjust default font size (like in the original script) ---
    try:
        default_font = font.nametofont("TkDefaultFont")
        # Set a base font size (adjust 10 as needed)
        default_font.configure(size=10)
        root.option_add("*Font", default_font)
        # You could make the font size configurable in config.py if desired
    except Exception as e:
        print(f"Could not configure default font: {e}")
        # Application will still run with the system's default font settings

    # Create an instance of the application class, passing the root window
    app_instance = FolderExplorerApp(root)

    # Start the Tkinter event loop to run the application
    root.mainloop()
