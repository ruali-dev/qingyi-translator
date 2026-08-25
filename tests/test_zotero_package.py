import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "zotero-connector" / "manifest.json"
UPDATES = ROOT / "updates.json"


def test_manifest_has_zotero_install_metadata() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    zotero = payload["applications"]["zotero"]

    assert re.fullmatch(r"[a-z0-9._-]+@[a-z0-9._-]+", zotero["id"], re.IGNORECASE)
    assert zotero["update_url"].startswith("https://")
    assert zotero["strict_min_version"]
    assert zotero["strict_max_version"]


def test_update_manifest_matches_connector() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    updates = json.loads(UPDATES.read_text(encoding="utf-8"))
    plugin_id = manifest["applications"]["zotero"]["id"]
    release = updates["addons"][plugin_id]["updates"][0]

    assert release["version"] == manifest["version"]
    assert release["update_link"].startswith(
        "https://github.com/ruali-dev/qingyi-translator/releases/download/"
    )
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", release["update_hash"])
