from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def test_fullstack_windows_installer_files_exist() -> None:
    ps1 = ROOT / "scripts" / "Install-ZEAZ-FullStack-Windows11.ps1"
    cmd = ROOT / "scripts" / "Install-ZEAZ-FullStack-Windows11.cmd"
    assert ps1.exists()
    assert cmd.exists()

def test_fullstack_installer_content() -> None:
    ps1_content = (ROOT / "scripts" / "Install-ZEAZ-FullStack-Windows11.ps1").read_text(encoding="utf-8")
    assert "Step 1: Checking System Prerequisites" in ps1_content
    assert "npm.cmd" in ps1_content or "npm.exe" in ps1_content
    assert "Turbo Build" in ps1_content
    assert "ZEAZ_HOME" in ps1_content
