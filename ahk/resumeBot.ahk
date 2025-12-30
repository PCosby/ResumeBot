#Requires AutoHotkey v2.0
#SingleInstance Force

^+p:: {
    projectPath  := projectPath := RegExReplace(A_ScriptDir, "\\ahk$", "") . "\"
    filePath     := projectPath . "out\selected.txt"
    pythonExe    := "python" ; or full path to python.exe
    pythonScript := projectPath . "src\run_resume_bot.py"

    ; copy + save
    Send("^c")
    Sleep(120)
    try FileDelete(filePath)
    FileAppend(A_Clipboard "`r`n", filePath, "UTF-8")

    ; open a terminal and run python, keeping the window open
    cmd := A_ComSpec . ' /c ""' . pythonExe . '" "' . pythonScript . '""'
    Run(cmd)
}
