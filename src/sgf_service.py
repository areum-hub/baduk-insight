"""Parse and replay the main variation of a Go SGF file."""
from dataclasses import dataclass
from sgfmill import sgf, sgf_moves

@dataclass
class GameRecord:
    size: int
    black_player: str
    white_player: str
    date: str
    event: str
    result: str
    setup_board: object
    moves: list
    place: str = ""  # SGF PC: recorded location; absent values stay empty.

    @property
    def move_count(self) -> int:
        return len(self.moves)

def load_sgf(raw: bytes) -> GameRecord:
    game = sgf.Sgf_game.from_bytes(raw)
    board, moves = sgf_moves.get_setup_and_moves(game)
    root = game.get_root()
    def prop(name: str) -> str:
        if not root.has_property(name):
            return ""
        value = root.get(name)
        return str(value) if value is not None else ""
    return GameRecord(
        size=game.get_size(), black_player=prop("PB"), white_player=prop("PW"),
        date=prop("DT"), event=prop("EV"), result=prop("RE"),
        setup_board=board, moves=moves, place=prop("PC")
    )

def replay(record: GameRecord, move_index: int):
    if not 0 <= move_index <= record.move_count:
        raise ValueError("Invalid move number")
    board = record.setup_board.copy()
    last = None
    for colour, point in record.moves[:move_index]:
        last = point
        if point is not None:
            board.play(point[0], point[1], colour)
    return board, last
