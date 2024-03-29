### Setting Up a Python Virtual Environment with requirements.txt

#### Step 1: Setting Up the Virtual Environment

1. Open your terminal or command prompt.
2. Navigate to your project directory using the `cd` command:
   ```bash
   cd path/to/your/project/directory
   ```
3. Create a new virtual environment named `venv`:
   ```bash
   python -m venv venv
   ```

#### Step 2: Activating the Virtual Environment

4. Activate the virtual environment:
   - **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - **macOS and Linux**:
     ```bash
     source venv/bin/activate
     ```
     You should see `(venv)` prefix in your terminal prompt, indicating the virtual environment is active.

#### Step 3: Installing Dependencies

5. Install project dependencies listed in the `requirements.txt` file:
   ```bash
   pip install -r requirements.txt
   ```

#### Step 4: Deactivating the Virtual Environment

6. To deactivate the virtual environment, run:
   ```bash
   deactivate
   ```

### Sharing the Environment

7. Share the entire project directory with your team, including the `venv` directory and the `requirements.txt` file. Team members can follow the same steps to set up the environment on their machines.

### Important Note:

- Keep the `requirements.txt` file updated whenever you install new packages or update existing ones in your project:
  ```bash
  pip freeze > requirements.txt
  ```
- Include only necessary dependencies in the `requirements.txt` file to keep the environment lightweight and avoid potential conflicts.

By following these steps, your team members should be able to set up a consistent development environment for the project.

### Setting Up Environment Variables

Before running the application, you'll need to set up your environment variables. Follow these steps:

1. **Create a `.env` file**: In the root directory of your project, create a file named `.env`.

2. **Add environment variables**: Open the `.env` file in a text editor and add the following environment variable:

   ```plaintext
   SECRET_KEY='replace_with_MySQL_password'
   ```

## Using the Start Script

This script will activate the virtual environment, set environment variables, and start the Flask server.

### Windows

To start the application on Windows, you can use the `startScript.ps1` PowerShell script. Open PowerShell and navigate to the scripts directory of your project. Then, enter the following command:

```powershell
.\startScript.ps1`
```

### Unix/Linux/MacOS

To start the application on Unix/Linux/MacOS, you can use the `startScript.sh` shell script. Open a terminal and navigate to the root directory of your project. Then, enter the following command:

```bash
chmod +x startScript.sh # Make the script executable (if needed)
source startScript.sh
```
