@RD /S /Q ".\dist"
python -m PyInstaller --noconsole --icon icon.ico --onefile main.py

@RD /S /Q ".\dist\resources"
echo d | xcopy /s resources dist\resources

cd dist
tar -a -cf game.zip main.exe resources
echo f | xcopy game.zip ..\game.zip

cd..
@RD /S /Q ".\dist"