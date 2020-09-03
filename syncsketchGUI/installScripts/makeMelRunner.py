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
    '''
    The old way or alternative way is:
        newText += line.strip("\n") + "\\n\\\n"
    The last \\\n makes the final mel file more human readable but introduces 
    some issues, since Windows encodes this as CRLF (\r\n) which is not compatible on 
    Unix systems. 
    Removing the last \\\n makes it less readable but more compatible, which is preferred.
    '''
    newText += line.strip("\n") + "\\n"
    print(line)

newText += "\");"
melInstallerPath = os.path.join(path, "installCrossPlatformGUI.mel")
with open(melInstallerPath, "w") as f:
    f.write(newText)
exit()
