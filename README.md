# INSA_finial_project
This repo contains all the necessary files for my INSA graduation project
**Usage**
1. Edit the port number in the client.py file.
2. Compile client.py using nuitka. This is required to change the python code into an executable that can be used directly used by the stager (guide is below).
3. Convert the generated executable into a usable pe payload and name it exactly "shellc.bin". For this, I recommend using: https://github.com/hasherezade/pe_to_shellcode.
4. In a Linux environment, use builder.py to generate the stager.exe file. (guide also below)
5. Initiate a python http server in the directory which contains shellc.bin ( python -m http.server <PORT> )
6. Run server.py
7. Test by launching stager.exe
8. deliver a the stager to the target (Figure this out by your self). 

# Disclaimer: This material is to be used for only for educational and experimental purposes in well designed and controlled labs.


# Stager generation (in Linux)

1. Go to the project directory.
2. Use "Python3 builder.py -l "<IP>" -p "<PORT>" " to generate the stager.
3. Done


# Nuitka — Python to Executable Guide

A practical guide to compiling Python scripts into standalone Windows executables using Nuitka.

## 1. What Is Nuitka?

[Nuitka](https://nuitka.net/) is a Python compiler that translates Python code into C/C++ code and compiles it into an executable program.

It supports several compilation modes, including standalone executables that can run without a separately installed Python interpreter.

### Benefits
- Compile Python programs into executable files.
- Create standalone applications.
- Bundle Python dependencies when supported.
- Distribute applications to other Windows computers.
- Integrate compilation into build workflows.

## 2. Requirements

Before using Nuitka, install the following:

- Windows 10 or Windows 11.
- A supported Python version.
- Nuitka.
- A supported C compiler, such as Microsoft Visual C++ Build Tools.
- The dependencies required by your Python application.

Check your Python installation:

```powershell
python --version
```

Check pip:

```powershell
python -m pip --version
```

## 3. Install Nuitka

Install Nuitka using pip:

```powershell
python -m pip install -U nuitka
```

Verify the installation:

```powershell
python -m nuitka --version
```

To check whether Nuitka can find a suitable C compiler:

```powershell
python -m nuitka --version
```

Follow Nuitka's compiler setup instructions if a compiler is missing.

Official documentation: https://nuitka.net/doc/user-manual.html

## 4. Compile a Python Script

Suppose your project contains:

```text
MyProject/
├── main.py
└── requirements.txt
```

Open PowerShell in the project directory:

```powershell
cd C:\Path\To\MyProject
```

Compile the script:

```powershell
python -m nuitka main.py
```

Nuitka will compile the program and create the necessary build files.

The exact output depends on the selected compilation options.

## 5. Create a Standalone Application

To create an application that includes the Python runtime and required dependencies, use:

```powershell
python -m nuitka --mode=standalone main.py
```

Nuitka generates a standalone distribution directory containing the executable and required files.

Keep the generated directory structure intact when distributing the application.

## 6. Create a Single-File Executable

To package a standalone application into a single executable, use:

```powershell
python -m nuitka --mode=onefile main.py
```

The resulting executable can be easier to distribute.

However, one-file applications may extract bundled components temporarily when launched. Startup time and compatibility can vary depending on the application.

## 7. Include Package Dependencies

Install your application's dependencies before compilation.

For example:

```powershell
python -m pip install requests
```

Then compile:

```powershell
python -m nuitka --mode=standalone main.py
```

Nuitka analyzes imports and includes supported dependencies. Some packages may require additional configuration.

For applications using dynamically imported modules, plugins, or data files, consult the official documentation for the appropriate inclusion options.

## 8. Include Data Files

If your application needs external files, such as configuration files or templates, include them explicitly.

For example:

```powershell
python -m nuitka --mode=standalone --include-data-files=config.json=config.json main.py
```

The general syntax is:

```text
--include-data-files=SOURCE=DESTINATION
```

Here, `SOURCE` identifies the file on your development computer, while `DESTINATION` specifies its location inside the distribution.

Consult the documentation for directory inclusion and platform-specific path considerations.

## 9. Choose an Output Directory

To keep build files organized, specify a build directory:

```powershell
python -m nuitka --mode=standalone --output-dir=build main.py
```

For a single-file executable:

```powershell
python -m nuitka --mode=onefile --output-dir=build main.py
```

This helps separate generated files from source code.

## 10. Use Nuitka with a Virtual Environment

A virtual environment helps isolate your project's dependencies.

Create one:

```powershell
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation, you can invoke the environment's Python executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install nuitka
```

Install the dependencies your application requires:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Compile using that same Python environment:

```powershell
.\.venv\Scripts\python.exe -m nuitka --mode=standalone main.py
```

This helps ensure Nuitka uses the intended Python interpreter and installed packages.

## 11. Common Problems

### C Compiler Not Found

Nuitka needs a supported C compiler to compile your application.

Install or configure a supported compiler using the official Nuitka instructions.

### Missing Modules

If a module is imported dynamically, Nuitka might not detect it automatically.

Check the module's documentation and Nuitka's inclusion options.

### Missing Data Files

Files such as images, JSON files, templates, and certificates may need to be included explicitly.

### Executable Works on One Computer but Not Another

Test the compiled application on a clean Windows environment.

Check for missing DLLs, unsupported operating-system features, architecture differences, and external runtime dependencies.

### Antivirus Warnings

Compiled executables can sometimes trigger security software warnings. Investigate detections through legitimate security tools and review your program's behavior. Compilation does not guarantee that a program will be trusted by antivirus software.

## 12. Recommended Workflow

1. Write and test your Python program.
2. Create a virtual environment.
3. Install the application's dependencies.
4. Install Nuitka in the same environment.
5. Compile in standalone mode.
6. Test the generated application.
7. Include required data files and dependencies.
8. Test the distribution on another computer.
9. Package the application for distribution.

## 13. Useful Commands

| Task | Command |
|---|---|
| Check Python | `python --version` |
| Install Nuitka | `python -m pip install -U nuitka` |
| Check Nuitka | `python -m nuitka --version` |
| Compile a script | `python -m nuitka main.py` |
| Build standalone | `python -m nuitka --mode=standalone main.py` |
| Build one file | `python -m nuitka --mode=onefile main.py` |
| Specify output directory | `python -m nuitka --mode=standalone --output-dir=build main.py` |

## 14. Official Resources

- Nuitka website: https://nuitka.net/
- User manual: https://nuitka.net/doc/user-manual.html
- Nuitka downloads and releases: https://github.com/Nuitka/Nuitka/releases
- Python documentation: https://docs.python.org/3/

---

**Note:** Nuitka compiles Python applications, but it does not guarantee that the resulting executable will be completely self-contained, compatible with every computer, or impossible to reverse engineer. Always test the compiled application in its intended environment.
