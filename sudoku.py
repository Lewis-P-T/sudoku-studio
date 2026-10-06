"""Sudoku Studio — generate, solve and play Sudoku in the terminal.

Standard library only. Run `python sudoku.py` for the menu or
`python sudoku.py --self-check` to run the built-in tests.
"""
import sys

# A grid is a list of 81 ints, row-major, 0 = empty.
SAMPLE = (
    "530070000600195000098000060800060003400803001"
    "700020006060000280000419005000080079"
)
SAMPLE_SOLUTION = (
    "534678912672195348198342567859761423426853791"
    "713924856961537284287419635345286179"
)


def parse(text):
    """Parse an 81-cell puzzle. Digits 1-9 are clues; 0 or . are blanks.
    Whitespace and | - + separators are ignored."""
    cells = [c for c in text if c not in " \t\r\n|-+"]
    if len(cells) != 81:
        raise ValueError(f"expected 81 cells, got {len(cells)}")
    grid = []
    for c in cells:
        if c in "0.":
            grid.append(0)
        elif c in "123456789":
            grid.append(int(c))
        else:
            raise ValueError(f"invalid character {c!r}")
    return grid


def to_string(grid):
    return "".join(str(v) for v in grid)


def render(grid):
    lines = []
    for r in range(9):
        if r and r % 3 == 0:
            lines.append("------+-------+------")
        row = []
        for c in range(9):
            if c and c % 3 == 0:
                row.append("|")
            v = grid[r * 9 + c]
            row.append(str(v) if v else ".")
        lines.append(" ".join(row))
    return "\n".join(lines)


def peers(i):
    """Indices sharing a row, column or box with cell i (excluding i)."""
    r, c = divmod(i, 9)
    br, bc = r - r % 3, c - c % 3
    ps = {r * 9 + k for k in range(9)} | {k * 9 + c for k in range(9)}
    ps |= {(br + dr) * 9 + bc + dc for dr in range(3) for dc in range(3)}
    ps.discard(i)
    return ps


PEERS = [peers(i) for i in range(81)]


def can_place(grid, i, v):
    return all(grid[p] != v for p in PEERS[i])


def is_valid(grid):
    """True if no clue conflicts with another (blanks allowed)."""
    return all(v == 0 or can_place(grid, i, v) for i, v in enumerate(grid))


def is_solved(grid):
    return 0 not in grid and is_valid(grid)


def solve(grid):
    """Plain backtracking. Returns a solved copy, or None if unsolvable."""
    if not is_valid(grid):
        return None
    g = list(grid)

    def bt():
        try:
            i = g.index(0)
        except ValueError:
            return True
        for v in range(1, 10):
            if can_place(g, i, v):
                g[i] = v
                if bt():
                    return True
        g[i] = 0
        return False

    return g if bt() else None


# ---------------------------------------------------------------- CLI

def read_puzzle():
    print("Paste a puzzle (81 cells; 0 or . for blanks). Blank line to finish:")
    buf = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            if buf:
                break
            continue
        buf.append(line)
        if len([c for c in "".join(buf) if c not in " \t|-+"]) >= 81:
            break
    return parse("".join(buf))


def solve_and_show(grid):
    print("\nPuzzle:\n" + render(grid))
    sol = solve(grid)
    if sol is None:
        print("\nNo solution (puzzle is invalid or contradictory).")
    else:
        print("\nSolution:\n" + render(sol))


def menu():
    while True:
        print("\n=== Sudoku Studio ===")
        print("1) Solve the built-in sample puzzle")
        print("2) Solve a puzzle you paste in")
        print("q) Quit")
        try:
            choice = input("> ").strip().lower()
        except EOFError:
            return
        if choice == "1":
            solve_and_show(parse(SAMPLE))
        elif choice == "2":
            try:
                solve_and_show(read_puzzle())
            except ValueError as e:
                print(f"Could not read puzzle: {e}")
        elif choice in ("q", "quit", "exit"):
            return
        else:
            print("Unknown option.")


def self_check():
    g = parse(SAMPLE)
    assert len(g) == 81 and g[0] == 5 and g[2] == 0
    assert parse(render(g).replace("\n", "")) == g, "render/parse round-trip"
    assert len(PEERS[0]) == 20 and all(len(p) == 20 for p in PEERS)
    assert is_valid(g) and not is_solved(g)
    sol = solve(g)
    assert sol is not None and to_string(sol) == SAMPLE_SOLUTION
    assert is_solved(sol)
    bad = list(g)
    bad[1] = 5  # duplicate 5 in row 0
    assert not is_valid(bad) and solve(bad) is None
    for text in ("123", "x" * 81):
        try:
            parse(text)
            raise AssertionError("parse should fail")
        except ValueError:
            pass
    print("self-check passed")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        self_check()
    else:
        menu()
