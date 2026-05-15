# WINDOWS_SETUP_AND_ERRORS.md

## 1. Overview

### Purpose of This Document
This document provides a complete guide for Windows users who encounter issues when running the Blokus GUI using:

python -m blokus gui


It summarizes all errors discovered during troubleshooting, explains why they occur, and provides clear, Windows‑specific solutions. This is intended to save developers time and prevent repeated debugging across different machines.

### Summary of GUI Requirements
The Blokus GUI requires:

- Python 3.14+
- A correctly configured PATH environment
- GTK runtime **with librsvg** (for SVG → PNG conversion)
- `rsvg-convert` available in PATH
- A properly activated virtual environment
- The project installed in editable mode (`pip install -e .`)
- The correct Python interpreter selected in the terminal or IDE

---

## 2. Full List of Errors Encountered

### Error 1 — Python 3.14 Installed but NOT Added to PATH

**Why it happens:**  
Windows does not automatically add Python installed via the Microsoft Store or the embeddable installer to PATH.

**How to diagnose:**  
Running:
python --version

returns Python 3.10 instead of 3.14.

**How to fix:**  
Add these paths manually:

example:

C:\Users\user\AppData\Local\Python\pythoncore-3.14-64\
C:\Users\user\AppData\Local\Python\pythoncore-3.14-64\Scripts\


**Windows-specific notes:**  
PATH issues are extremely common on Windows and rarely occur on Linux/macOS.

---

### Error 2 — GTK Installed Without librsvg (`rsvg-convert` Missing)

**Why it happens:**  
The GTK Windows installer does **not** include librsvg, unlike Linux distributions.

**How to diagnose:**  
The GUI crashes when rendering SVG assets.  
Running:

rsvg-convert --version

returns “command not found”.

**How to fix:**  
Install MSYS2 and librsvg:

pacman -S mingw-w64-x86_64-librsvg


**Windows-specific notes:**  
Linux users never experience this issue because librsvg is installed automatically with GTK.

---

### Error 3 — `rsvg-convert` Not Found in PATH

**Why it happens:**  
Even after installing librsvg, Windows cannot find the executable unless its directory is added to PATH.

**How to diagnose:**  
Running:
rsvg-convert --version

fails.

**How to fix:**  
Add this to PATH:

C:\msys64\mingw64\bin


**Windows-specific notes:**  
MSYS2 installs binaries in a separate environment that must be manually exposed to Windows.

---

### Error 4 — No Virtual Environment (venv) Was Being Used

**Why it happens:**  
Python was executed globally, mixing system packages with project dependencies.

**How to diagnose:**  
The terminal prompt does **not** show:

(.venv)


**How to fix:**  
Create a venv:

py -3.14 -m venv .venv


Activate it:

.\.venv\Scripts\activate



**Windows-specific notes:**  
PowerShell requires `.\` before script paths.

---

### Error 5 — The `blokus` Module Was Not Installed Inside the venv

**Why it happens:**  
A new venv starts empty. Python cannot import the project unless it is installed.

**How to diagnose:**  
Running the GUI results in:

No module named blokus


**How to fix:**  
Install the project in editable mode:

pip install -e .


**Windows-specific notes:**  
Editable installs work identically across platforms.

---

### Error 6 — Wrong Python Interpreter Was Being Used

**Why it happens:**  
VS Code or the terminal was using the global Python instead of the venv Python.

**How to diagnose:**  
Running:
python --version

returns a version different from the one inside `.venv`.

**How to fix:**  
Always activate the venv before running the GUI:

.\.venv\Scripts\activate


**Windows-specific notes:**  
VS Code often defaults to the system interpreter unless manually changed.

---

## 3. Windows Setup Guide

### Install Python 3.14 Correctly
Download from python.org (not Microsoft Store).  
During installation, enable:

- “Add Python to PATH”
- “Install for all users” (optional)

### Add Python to PATH Manually
If needed, add:

example:

C:\Users\<your-user>\AppData\Local\Python\pythoncore-3.14-64\
C:\Users\<your-user>\AppData\Local\Python\pythoncore-3.14-64\Scripts\

### Install MSYS2
Download from: https://www.msys2.org  
Run the installer and update packages:
pacman -Syu

### Install librsvg
pacman -S mingw-w64-x86_64-librsvg


### Add MSYS2 to PATH
Add: 

C:\msys64\mingw64\bin



### Verify `rsvg-convert`
rsvg-convert --version


---

## 4. Virtual Environment Guide

### Create a venv
py -3.14 -m venv .venv


### Activate the venv
.\.venv\Scripts\activate


### Verify Python Version
python --version


### Why Each Project Needs Its Own venv
- Prevents dependency conflicts  
- Keeps environments isolated  
- Ensures reproducibility  
- Avoids global package pollution  

---

## 5. Installing the Project

### Install in Editable Mode
pip install -e .


### Verify Installation
python -c "import blokus; print(blokus.file)"


---

## 6. Running the GUI

### Correct Command
python -m blokus gui


### Common Mistakes
- Forgetting to activate the venv  
- Missing `rsvg-convert`  
- Wrong Python interpreter  
- Project not installed (`pip install -e .`)  

---

## 7. Final Recommendations

### Best Practices for Windows Users
- Always use PowerShell instead of CMD  
- Keep MSYS2 updated  
- Use `.venv` as the standard environment name  
- Add required paths only once and verify them  

### Maintain a Clean Environment
- Avoid installing packages globally  
- Use one venv per project  
- Regenerate the venv when dependencies break  

### Regenerate the venv if Needed
rm -r .venv
py -3.14 -m venv .venv
.\.venv\Scripts\activate
pip install -e .