import sys, os, shutil
os.chdir(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.abspath(os.path.join('..', 'beebrain')))

if os.path.exists("project"):
    shutil.rmtree("project")

# Make project directory if it doesn't exist
if not os.path.exists("project"):
    os.makedirs("project")

# Copy main.py and tools folder with content to project folder
shutil.copy("../beebrain/main.py", "project")
shutil.copytree("../beebrain/tools", "project/tools")
shutil.copytree("../beebrain/assets", "project/assets")

# Copy all files from config folder except for "auth.yaml", rename "auth_template.yaml" to "auth.yaml"

shutil.copytree("../beebrain/config", "project/config")
shutil.copy("../beebrain/config/auth_template.yaml", "project/config/auth.yaml")
os.remove("project/config/auth_template.yaml")
shutil.rmtree("project/tools/__pycache__")

# Copy the requirements.txt file to project folder
shutil.copy("../requirements.txt", "project")

