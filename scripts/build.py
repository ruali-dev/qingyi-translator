from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def build_connector() -> Path:
    output = DIST / "paper-translator-zotero.xpi"
    connector = ROOT / "zotero-connector"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in connector.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(connector).as_posix())
    return output


def build_desktop() -> Path:
    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
            "--onefile", "--windowed", "--name", "PaperTranslator",
            "--workpath", str(ROOT / ".codex-tmp" / "pyinstaller"),
            "--specpath", str(ROOT / ".codex-tmp"),
            str(ROOT / "app.py")
        ],
        cwd=ROOT,
        check=True,
    )
    return DIST / "PaperTranslator.exe"


def main() -> None:
    DIST.mkdir(exist_ok=True)
    connector = build_connector()
    desktop = build_desktop()
    shutil.rmtree(ROOT / ".codex-tmp" / "pyinstaller", ignore_errors=True)
    spec = ROOT / ".codex-tmp" / "PaperTranslator.spec"
    if spec.exists():
        spec.unlink()
    print(f"Built {desktop}")
    print(f"Built {connector}")


if __name__ == "__main__":
    main()
