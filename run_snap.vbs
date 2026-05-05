Option Explicit

Dim shell, fso, scriptDir, pythonwPath, command

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonwPath = "pythonw"

If fso.FileExists(scriptDir & "\.venv\Scripts\pythonw.exe") Then
    pythonwPath = """" & scriptDir & "\.venv\Scripts\pythonw.exe" & """"
End If

command = pythonwPath & " """ & scriptDir & "\snap.py"""

' 0 = hidden window, False = do not wait for completion
shell.Run command, 0, False
