mkdir build
cd build

echo "Building Windows executable..."
flet pack ../beebrain/main.py --icon ../beebrain/assets/avatar.png
echo "Done!"