"""Sudoku Studio — generate, solve and play Sudoku in the terminal.

Standard library only. Run `python sudoku.py` for the menu or
`python sudoku.py --self-check` to run the built-in tests.
"""
import itertools
import random
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


DIGITS = frozenset(range(1, 10))


def _search(g, rng=None):
    """Yield every solution of g. Each step fills naked singles (cells with
    one candidate) until stuck, then branches on the cell with the fewest
    candidates (MRV). rng shuffles branch order for random grids."""
    g = list(g)
    while True:
        best, changed = None, False
        for i in range(81):
            if g[i]:
                continue
            cs = DIGITS - {g[p] for p in PEERS[i]}
            if not cs:
                return  # contradiction
            if len(cs) == 1:
                g[i] = next(iter(cs))
                changed = True
            elif best is None or len(cs) < len(best[1]):
                best = (i, cs)
        if not changed:
            break
    if best is None:
        yield g
        return
    i, cs = best
    order = sorted(cs)
    if rng:
        rng.shuffle(order)
    for v in order:
        g[i] = v
        yield from _search(g, rng)


def solve(grid, rng=None):
    """Returns a solved copy, or None if invalid/unsolvable."""
    if not is_valid(grid):
        return None
    return next(_search(grid, rng), None)


def count_solutions(grid, limit=2):
    """Number of solutions, stopping early at limit (2 = 'is it unique?')."""
    if not is_valid(grid):
        return 0
    return sum(1 for _ in itertools.islice(_search(grid), limit))


# Target clue counts. Removal stops early if uniqueness would break.
DIFFICULTY = {"easy": 40, "medium": 32, "hard": 26}


def generate(difficulty="medium", rng=None):
    """Return (puzzle, solution) with a unique solution."""
    rng = rng or random.Random()
    solution = solve([0] * 81, rng)
    puzzle = list(solution)
    target = DIFFICULTY[difficulty]
    cells = list(range(81))
    rng.shuffle(cells)
    clues = 81
    for i in cells:
        if clues <= target:
            break
        v, puzzle[i] = puzzle[i], 0
        if count_solutions(puzzle) == 1:
            clues -= 1
        else:
            puzzle[i] = v
    return puzzle, solution


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


def generate_and_show():
    try:
        d = input("Difficulty (easy/medium/hard) [medium]: ").strip().lower() or "medium"
    except EOFError:
        return
    if d not in DIFFICULTY:
        print("Unknown difficulty.")
        return
    puzzle, solution = generate(d)
    clues = sum(1 for v in puzzle if v)
    print(f"\n{d.title()} puzzle ({clues} clues):\n" + render(puzzle))
    print("\nString: " + to_string(puzzle))
    try:
        if input("\nShow solution? (y/N) ").strip().lower() == "y":
            print(render(solution))
    except EOFError:
        pass


def menu():
    while True:
        print("\n=== Sudoku Studio ===")
        print("1) Solve the built-in sample puzzle")
        print("2) Solve a puzzle you paste in")
        print("3) Generate a new puzzle")
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
        elif choice == "3":
            generate_and_show()
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
    assert count_solutions(g) == 1
    assert count_solutions([0] * 81) == 2, "empty grid has many solutions"
    assert count_solutions(bad) == 0
    # A known 17-clue puzzle: propagation + MRV must handle minimal puzzles.
    hard = parse("000000010400000000020000000000050407008000300001090000300400200050100000000806000")
    hs = solve(hard)
    assert hs and is_solved(hs) and all(h in (0, s) for h, s in zip(hard, hs))
    rng = random.Random(7)
    for d in DIFFICULTY:
        p, s = generate(d, rng)
        assert is_solved(s) and all(v in (0, sv) for v, sv in zip(p, s))
        assert count_solutions(p) == 1, f"{d} puzzle not unique"
        assert sum(1 for v in p if v) >= DIFFICULTY[d]
    print("self-check passed")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        self_check()
    else:
        menu()
