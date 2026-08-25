from pathlib import Path

from paper_translator.config import AppConfig, ConfigStore


def test_config_round_trip_encrypts_key(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    store = ConfigStore(path)
    config = AppConfig(api_key="sk-test", model="test-model")

    store.save(config)

    assert store.load() == config
    assert "sk-test" not in path.read_text(encoding="utf-8")


def test_invalid_config_falls_back_to_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text('{"base_url":"ftp://invalid"}', encoding="utf-8")

    assert ConfigStore(path).load() == AppConfig()

