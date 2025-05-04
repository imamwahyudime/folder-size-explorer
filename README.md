# Folder Size Explorer

A cross-platform desktop application built with Python and Tkinter to explore folder contents, view item details, and calculate folder sizes efficiently.

![image](https://github.com/user-attachments/assets/19ebbb8c-4ee2-4806-b0c0-08c8ce213dfe)

Folder Size Explorer provides a two-pane interface similar to traditional file explorers:
* **Left Pane:** A navigation tree showing the directory structure, allowing you to browse drives (Windows) or key locations (~ Home, /, /media, /mnt on Linux/macOS).
* **Right Pane:** Displays the contents of the selected directory from the navigation tree. It offers two view modes:
    * **Details View:** Shows Name, Size, Type, and Date Modified for each file and folder. Folder sizes are calculated asynchronously in the background to keep the UI responsive.
    * **List View:** A simpler view showing just Name and Size.

The application uses threading for non-blocking folder size calculations and aims for a native look and feel using Tkinter's themed widgets (ttk).

## Features:

* **Dual-Pane Layout:** Familiar navigation tree and content display.
* **Asynchronous Folder Size Calculation:** Calculates folder sizes in the background without freezing the UI (Details view).
* **Multiple View Modes:** Choose between detailed or list views.
* **Navigation Controls:** Back, Up, and direct path entry.
* **Sorting:** Click column headers in the content view to sort by Name, Size, Type, or Date Modified.
* **Cross-Platform:** Designed to run on Windows, macOS, and Linux.
* **File/Folder Interaction:** Double-click folders to navigate, files to open them with the default system application, and symlinks to view their target.
* **Basic Error Handling:** Gracefully handles permission errors and inaccessible items during scanning.
* **Modular Code Structure:** Organized into separate files for configuration, utilities, UI components, and main application logic.

## Requirements:

* **Python:** 3.6 or higher recommended (uses f-strings, `pathlib`, `os.scandir`).
* **Tkinter:** Usually included with standard Python distributions. If not, you may need to install it separately (e.g., `sudo apt-get install python3-tk` on Debian/Ubuntu).
* **Operating System:** Windows, macOS, or Linux.

## Usage

* Ensure all the Python files (`main.py`, `app.py`, `config.py`, `utils.py`, `about_window.py`) are in the same directory.
* Navigate to the project directory in your terminal or command prompt and run:
   ```bash
    python main.py
    ```
or
* You can also run main.py directly by double click it.

## File Structure
The project is organized into the following files:
* **main.py:** The main entry point of the application. Initializes Tkinter and starts the app.
* **app.py:** Contains the main FolderExplorerApp class, handling the GUI layout, event binding, navigation logic, and content display orchestration.
* **config.py:** Stores all configuration constants like application title, version, initial directory, column definitions, UI text strings, etc.
* **utils.py:** Holds helper functions for tasks like formatting file sizes, calculating folder sizes iteratively, and getting modification times.
* **about_window.py:** Defines the function to create and display the "About" window.
