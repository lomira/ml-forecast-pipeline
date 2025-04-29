# Using VS Code with WSL (Without Docker Desktop as it is a paid subcription for large companies)

This guide explains how to set up your development environment using Visual Studio Code and Windows Subsystem for Linux (WSL) directly, without needing Docker Desktop. This provides many benefits similar to Dev Containers, like isolating your development environment.

**Steps:**

1. **Install Ubuntu in a WSL**
    * Instruction
2. **Install Docker Engine on Ubuntu (WSL)**
    * Instructions : https://docs.docker.com/engine/install/ubuntu/

3.  **Install Required VS Code Extensions:**
    *   Open VS Code.
    *   Go to the Extensions view (Ctrl+Shift+X).
    *   Search for and install the following extensions:
        *   **WSL** (ID: `ms-vscode-remote.remote-wsl`): Allows VS Code to connect to your WSL distribution.
        *   **(Recommended) Dev Containers** (ID: `ms-vscode-remote.remote-containers`): While you're not using Docker *containers*, this extension provides the core functionality for managing remote development environments, including WSL, and utilizes `.devcontainer` configurations.

2.  **Connect VS Code to WSL:**
    *   Open the Command Palette (Ctrl+Shift+P).
    *   Type `WSL: Connect to WSL` and select it.
    *   VS Code will open a new window connected directly to your default WSL distribution. The Remote Indicator will now show `WSL: <Your Distro Name>`.

3.  **Open Your Project Folder:**
    *   Inside the WSL-connected VS Code window, go to `File > Open Folder...`.
    *   Navigate to your project directory within the WSL filesystem.
        *   Your Windows drives are typically mounted under `/mnt/`. For example, your project might be at `/mnt/c/Users/PC/Documents/PyProject/ml-forecast-pipeline`.
        *   It's often better to clone or place your project directly within the WSL home directory (e.g., `/home/<your-wsl-username>/projects/ml-forecast-pipeline`) for better performance.
    *   Select your project folder and click `OK`.

4.  **Develop in WSL:**
    *   You are now running VS Code connected to your WSL environment.
    *   The integrated terminal (Ctrl+`) will open a shell within your WSL distribution.
    *   You can install programming languages (like Python via `apt`), tools (like `git`), and dependencies directly within WSL using its package manager (e.g., `apt update && apt install python3-pip git`). These will be isolated from your Windows environment.
    *   VS Code extensions you install might prompt you to install them in WSL as well – you generally should, so they run within the Linux environment.

5.  **(Optional) Use `.devcontainer/devcontainer.json` for Configuration:**
    *   Even without Docker, the Dev Containers extension can use a `devcontainer.json` file to configure the WSL environment when you open the folder.
    *   Create a `.devcontainer` folder in your project root.
    *   Inside `.devcontainer`, create a `devcontainer.json` file.
    *   This file can specify:
        *   VS Code extensions to automatically install in WSL for this project.
        *   Settings to apply within VS Code for this project when connected via WSL.
        *   Commands to run after the environment is set up (e.g., `pip install -r requirements.txt`).

    *   **Example `devcontainer.json` (for WSL, no Docker):**
        ```json
        // .devcontainer/devcontainer.json
        {
          "name": "Python 3 (WSL)",
          // Tells VS Code to use the existing WSL environment
          // No "dockerComposeFile" or "image" property needed.

          // Extensions to install in WSL for this project
          "customizations": {
            "vscode": {
              "extensions": [
                "ms-python.python",
                "ms-python.vscode-pylance",
                "ms-python.debugpy",
                "charliermarsh.ruff"
              ],
              "settings": {
                 "python.testing.pytestEnabled": true,
                 "python.testing.pytestArgs": ["tests"]
              }
            }
          },

          // Command to run after connecting (runs in WSL)
          // "postCreateCommand": "pip install -r requirements.txt"

          // Use 'forwardPorts' to make WSL ports available locally
          // "forwardPorts": [3000],

          // Use 'remoteUser' to connect as a specific user in WSL
          // "remoteUser": "vscode" // if you have a specific user setup
        }
        ```
    *   When you open the folder in WSL (or use `Dev Containers: Reopen in Container` which will detect WSL), VS Code will read this file and apply the configurations.

**Conclusion:**

By connecting VS Code directly to WSL using the WSL extension, you leverage your existing Linux environment for development. The Dev Containers extension enhances this by allowing configuration-as-code via `devcontainer.json`, automating setup and ensuring consistency without requiring Docker. Your WSL instance acts as the isolated "container".
