# Helper script to run Poetry with correct Python path on Windows
# Usage: .\run-poetry.ps1 lock
# Usage: .\run-poetry.ps1 install
# Usage: .\run-poetry.ps1 add package-name

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Save current PATH
$oldPath = $env:Path

# Set PATH with real Python first, removing Microsoft Store alias
$env:Path = "C:\Users\val2\AppData\Local\Programs\Python\Python314;C:\Users\val2\AppData\Local\Programs\Python\Python314\Scripts;" + ($env:Path -replace [regex]::Escape("C:\Users\val2\AppData\Local\Microsoft\WindowsApps;"), "")

# Run Poetry with all arguments
& "C:\Users\val2\AppData\Local\Programs\Python\Python314\Scripts\poetry.exe" $Arguments

# Restore PATH
$env:Path = $oldPath
