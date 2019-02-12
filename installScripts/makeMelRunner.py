lines = []
with open("installGui.py", "r") as f:
    lines = f.readlines()

lines.insert(0, "python(\"\n")
newText = ""
for line in lines:
    newText += line.strip("\n") + "\\n\\\n"
    print(line)

newText += "\");"
with open("installCrossPlatformGUI.mel", "w") as f:
    f.write(newText)
exit()
