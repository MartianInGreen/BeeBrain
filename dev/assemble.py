import sys, os, shutil
os.chdir(os.path.dirname(os.path.abspath(__file__)))

if os.path.exists("assembled"):
    shutil.rmtree("assembled")

# Make project directory if it doesn't exist
if not os.path.exists("assembled"):
    os.makedirs("assembled")

# Zip the folder project and name it BeeBrain.zip
shutil.make_archive("assembled/BeeBrain_python", "zip", "project")

# Zip the executable and name it BeeBrain_windows.zip
shutil.make_archive("assembled/BeeBrain_windows", "zip", "dist/BeeBrain")