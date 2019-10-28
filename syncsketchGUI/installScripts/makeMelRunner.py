import sys
import os
path, filename = os.path.split(sys.argv[0])
pythonInstallerPath = os.path.join(path, "installGui.py")
lines = []
with open(pythonInstallerPath, "r") as f:
    lines = f.readlines()

lines.insert(0, "python(\"\n")
newText = ""
for line in lines:
    newText += line.strip("\n") + "\\n\\\n"
    print(line)

newText += "\");"
melInstallerPath = os.path.join(path, "installCrossPlatformGUI.mel")
with open(melInstallerPath, "w") as f:
    f.write(newText)
exit()
