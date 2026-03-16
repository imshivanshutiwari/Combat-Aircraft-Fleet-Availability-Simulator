import os
import sys

# THE BRIDGE: Automatically redirect Streamlit Cloud to the new Premium Dashboard.
# This fixes the issue where the Streamlit Cloud UI hides the "Main file path" setting.

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NEW_APP_PATH = os.path.join(PROJECT_ROOT, 'fleet-dashboard', 'app.py')

if __name__ == "__main__":
    # Change the current working directory to the new folder to ensure imports work correctly
    os.chdir(os.path.dirname(NEW_APP_PATH))
    
    # Execute the new app
    with open(NEW_APP_PATH, "rb") as f:
        code = compile(f.read(), NEW_APP_PATH, "exec")
        exec(code, {"__name__": "__main__"})
