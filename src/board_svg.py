"""Render a basic SVG Go board."""
from html import escape

def _stars(size: int):
    axis = {19: (3, 9, 15), 13: (3, 6, 9), 9: (2, 4, 6)}.get(size, ())
    return [(r, c) for r in axis for c in axis]

def render_board(board, last_move=None) -> str:
    size = board.side
    square = 28 if size == 19 else 37
    pad = 32
    total = 2 * pad + (size - 1) * square
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total} {total}" '
        'style="display:block;width:100%;height:auto;max-width:620px" role="img" aria-label="Go board">',
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
    lines.append("</svg>")
    return "\n".join(lines)
