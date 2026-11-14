from src.board_svg import render_board

class FakeBoard:
    side = 19
    def get(self, row, col):
        return {(3, 3): "b", (15, 15): "w"}.get((row, col))

def test_svg_board_has_grid_and_stones():
    svg = render_board(FakeBoard(), last_move=(3, 3))
    assert svg.startswith("<svg")
    assert svg.count("<line ") == 38
    assert 'aria-label="Go board"' in svg
    assert '#202020' in svg and '#f8f6f0' in svg
    assert svg.endswith("</svg>")


def test_ai_suggestion_and_actual_move_are_distinct_markers():
    svg = render_board(FakeBoard(), last_move=(3, 3), ai_suggestion="F5")
    assert 'stroke="#2563eb"' in svg
    assert 'stroke="#f97316"' in svg
    assert 'aria-label="AI recommended point"' in svg
    assert 'aria-label="Played point"' in svg


def test_invalid_ai_point_is_ignored():
    svg = render_board(FakeBoard(), ai_suggestion="pass")
    assert 'AI recommended point' not in svg
