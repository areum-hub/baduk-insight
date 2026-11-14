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
