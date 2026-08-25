from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "assets" / "icon"


def test_windows_icon_contains_expected_sizes() -> None:
    with Image.open(ICON_DIR / "qingyi.ico") as icon:
        assert icon.format == "ICO"
        assert {(16, 16), (32, 32), (48, 48), (256, 256)} <= icon.ico.sizes()


def test_icon_has_editable_svg_source() -> None:
    svg = (ICON_DIR / "qingyi-icon.svg").read_text(encoding="utf-8")

    assert "viewBox=\"0 0 1024 1024\"" in svg
    assert "<title" in svg
    assert "<desc" in svg
    assert "<script" not in svg
    assert "foreignObject" not in svg
