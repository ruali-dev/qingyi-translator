import json
import queue
import threading
import urllib.request

from paper_translator.server import ConnectorServer
from paper_translator.translator import TranslationResult


def test_started_event_precedes_slow_translation_result() -> None:
    events: queue.Queue[tuple[str, object]] = queue.Queue()
    release_translation = threading.Event()

    def translate(text: str) -> TranslationResult:
        assert text == "selected sentence"
        assert release_translation.wait(timeout=2)
        return TranslationResult(text, "译文", "test-model")

    server = ConnectorServer("127.0.0.1", 0, translate, events)
    server.start()
    request_finished = threading.Event()

    def send_request() -> None:
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.port}/translate",
            data=json.dumps({"text": "selected sentence"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            assert response.status == 200
        request_finished.set()

    request_thread = threading.Thread(target=send_request, daemon=True)
    request_thread.start()
    try:
        event, payload = events.get(timeout=1)
        assert (event, payload) == ("translation_started", "selected sentence")
        assert not request_finished.is_set()

        release_translation.set()
        event, payload = events.get(timeout=1)
        assert event == "translation"
        assert isinstance(payload, TranslationResult)
        assert request_finished.wait(timeout=1)
    finally:
        release_translation.set()
        server.stop()

