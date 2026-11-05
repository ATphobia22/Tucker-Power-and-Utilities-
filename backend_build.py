#!/usr/bin/env python3
"""Freeze PTDT v33 FastAPI backend into a standalone binary via PyInstaller."""
import subprocess
import sys


def build_backend() -> None:
    print("Building PTDT v33 Sovereign Backend Executable...")

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--console",  # keep console for sidecar logs; Electron captures stdout
        "--name=ptdt-backend",
        "--add-data=data;data",
        "--add-data=core;core",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "backend/main.py",
    ]

    subprocess.check_call(cmd)
    print("Backend executable successfully built in ./dist/ptdt-backend/")


if __name__ == "__main__":
    build_backend()
