echo "Copying project files"
python3 copy.py 
echo "Copying project files done"

flet pack project/main.py --name "BeeBrain" --icon "project/assets/avatar.png" --add-data "project/config;config" --onedir --hidden-import "replicate"

echo "Zipping project files"
python3 assemble.py
echo "Packaging done!"