from paper_translator.ui import (
    RESULT_MIN_HEIGHT,
    RESULT_MIN_WIDTH,
    PaperTranslatorApp,
    constrained_result_size,
)


def test_result_resize_tracks_pointer_delta() -> None:
    assert constrained_result_size(520, 300, 140, 90, 1200, 800) == (660, 390)


def test_result_resize_respects_minimum_and_screen_bounds() -> None:
    assert constrained_result_size(520, 300, -1000, -1000, 1200, 800) == (
        RESULT_MIN_WIDTH,
        RESULT_MIN_HEIGHT,
    )
    assert constrained_result_size(520, 300, 2000, 2000, 760, 540) == (760, 540)


def test_rounded_card_points_follow_resized_bounds() -> None:
    points = PaperTranslatorApp._rounded_rect_points(5, 5, 707, 427, 22)

    assert min(points[0::2]) == 5
    assert max(points[0::2]) == 707
    assert min(points[1::2]) == 5
    assert max(points[1::2]) == 427
