' Opens the Battle Cats save editor (BCSFE graphical interface) without a console window.
Option Explicit

Dim fso, sh, dir, script
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
script = fso.BuildPath(dir, "BCSFE Editor.pyw")
sh.CurrentDirectory = dir

On Error Resume Next
sh.Run "pyw -3 """ & script & """", 0, False
If Err.Number <> 0 Then
    Err.Clear
    sh.Run "pythonw """ & script & """", 0, False
    If Err.Number <> 0 Then
        MsgBox "Python was not found." & vbCrLf & vbCrLf & _
               "Install it from https://www.python.org/downloads/ (tick 'Add python.exe to PATH')" & vbCrLf & _
               "and then run in a terminal:  py -m pip install -r requirements.txt", _
               vbCritical, "Battle Cats Save Editor"
    End If
End If
