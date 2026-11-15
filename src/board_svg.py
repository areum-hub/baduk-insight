"""Render a basic SVG Go board."""
from html import escape

def _stars(size: int):
    axis = {19: (3, 9, 15), 13: (3, 6, 9), 9: (2, 4, 6)}.get(size, ())
    return [(r, c) for r in axis for c in axis]

def _gtp_to_point(move, size):
    """Convert a KataGo GTP move (e.g. F5) to a board location."""
    columns = "ABCDEFGHJKLMNOPQRSTUVWXYZ"[:size]
    if not isinstance(move, str) or move.upper() in ("PASS", "RESIGN"):
        return None
    move = move.upper().strip()
    if len(move) < 2 or move[0] not in columns or not move[1:].isdigit():
        return None
    row = int(move[1:]) - 1
    if not 0 <= row < size:
        return None
    return (row, columns.index(move[0]))


def render_board(board, last_move=None, ai_suggestion=None) -> str:
    size = board.side
    square = 28 if size == 19 else 37
    pad = 32
    total = 2 * pad + (size - 1) * square
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total} {total}" '
        'style="display:block;width:100%;height:auto;max-width:720px;margin:0 auto" role="img" aria-label="Go board">',
        f'<rect width="{total}" height="{total}" rx="10" fill="#e2bc80"/>'
    ]
    end = pad + (size - 1) * square
    for n in range(size):
        p = pad + n * square
        lines.append(f'<line x1="{pad}" y1="{p}" x2="{end}" y2="{p}" stroke="#59412a"/>')
        lines.append(f'<line x1="{p}" y1="{pad}" x2="{p}" y2="{end}" stroke="#59412a"/>')
    for r, c in _stars(size):
        lines.append(f'<circle cx="{pad+c*square}" cy="{pad+(size-1-r)*square}" r="3" fill="#59412a"/>')
    columns = "ABCDEFGHJKLMNOPQRSTUVWXYZ"[:size]
    for col in range(size):
        lines.append(f'<text x="{pad+col*square}" y="18" font-size="12" text-anchor="middle">{escape(columns[col])}</text>')
    for row in range(size):
        lines.append(f'<text x="17" y="{pad+(size-1-row)*square+4}" font-size="12" text-anchor="middle">{row+1}</text>')
    for row in range(size):
        for col in range(size):
            colour = board.get(row, col)
            if colour not in ("b", "w"):
                continue
            x, y = pad+col*square, pad+(size-1-row)*square
            fill = "#202020" if colour == "b" else "#f8f6f0"
            lines.append(f'<circle cx="{x}" cy="{y}" r="{square*0.47:.1f}" fill="{fill}" stroke="#444" stroke-width="1"/>')
            if last_move == (row, col):
                mark = "#ffffff" if colour == "b" else "#b01924"
                lines.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{mark}"/>')
    # Blue ring = AI's first candidate. Orange ring = played move.
    # Draw suggestion after the stones, but don't obscure the underlying piece.
    suggestion = _gtp_to_point(ai_suggestion, size)
    if suggestion is not None:
        row, col = suggestion
        x, y = pad + col * square, pad + (size - 1 - row) * square
        lines.append(
            f'<circle cx="{x}" cy="{y}" r="{square * 0.42:.1f}" '
            'fill="none" stroke="#2563eb" stroke-width="4" '
            'aria-label="AI recommended point"/>'
        )
    if last_move is not None:
        row, col = last_move
        x, y = pad + col * square, pad + (size - 1 - row) * square
        lines.append(
            f'<circle cx="{x}" cy="{y}" r="{square * 0.33:.1f}" '
            'fill="none" stroke="#f97316" stroke-width="2.5" '
            'aria-label="Played point"/>'
        )
    lines.append("</svg>")
    return "\n".join(lines)
