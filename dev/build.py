import sys, os, shutil
os.chdir(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.abspath(os.path.join('..', 'beebrain')))

if os.path.exists("build"):
    shutil.rmtree("build")

# Make build directory if it doesn't exist
if not os.path.exists("build"):
    os.makedirs("build")

# Copy main.py and tools folder with content to build folder
shutil.copy("../beebrain/main.py", "build")
shutil.copytree("../beebrain/tools", "build/tools")
shutil.copytree("../beebrain/assets", "build/assets")

# Copy all files from config folder except for "auth.yaml", rename "auth_template.yaml" to "auth.yaml"

shutil.copytree("../beebrain/config", "build/config")
shutil.copy("../beebrain/config/auth_template.yaml", "build/config/auth.yaml")
os.remove("build/config/auth_template.yaml")
shutil.rmtree("build/tools/__pycache__")

