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


# ---------------------------------------------------------------- hints

UNITS = (
    [("row", r + 1, [r * 9 + c for c in range(9)]) for r in range(9)]
    + [("column", c + 1, [r * 9 + c for r in range(9)]) for c in range(9)]
    + [("box", b + 1, [(b // 3 * 3 + dr) * 9 + b % 3 * 3 + dc
                       for dr in range(3) for dc in range(3)]) for b in range(9)]
)


def candidates(grid, i):
    return DIGITS - {grid[p] for p in PEERS[i]}


def cell_name(i):
    return f"r{i // 9 + 1}c{i % 9 + 1}"


def find_hint(grid):
    """Next logical move as (index, digit, explanation), or None if no
    naked/hidden single exists. Assumes the filled cells are correct."""
    for i in range(81):
        if not grid[i]:
            cs = candidates(grid, i)
            if len(cs) == 1:
                v = next(iter(cs))
                return i, v, f"Naked single: {cell_name(i)} can only be {v} - every other digit is already in its row, column or box."
    for kind, n, cells in UNITS:
        present = {grid[i] for i in cells}
        for v in DIGITS - present:
            spots = [i for i in cells if not grid[i] and v in candidates(grid, i)]
            if len(spots) == 1:
                i = spots[0]
                return i, v, f"Hidden single: in {kind} {n}, {v} fits only at {cell_name(i)}."
    return None


def mistakes(grid, solution):
    return [i for i in range(81) if grid[i] and grid[i] != solution[i]]


def conflicts(grid):
    """Filled cells that clash with a peer holding the same digit."""
    return sorted(i for i in range(81) if grid[i] and not can_place(grid, i, grid[i]))


# ---------------------------------------------------------------- play

PLAY_HELP = """Commands (rows/cols 1-9):
  r c v      place digit v at row r, column c   (e.g. 3 5 7)
  r c 0      erase that cell
  n r c v    toggle pencil mark v on a cell
  notes      list pencil marks
  hint       reveal one logical move, with the reasoning
  check      mark wrong entries against the solution
  help       show this help     q  quit"""


def new_game(puzzle, solution=None):
    return {
        "givens": list(puzzle),
        "grid": list(puzzle),
        "solution": solution or solve(puzzle),
        "notes": {},  # index -> set of pencil marks
    }


def render_play(game):
    """Board with row/column numbers; '!' marks entries clashing with a peer."""
    grid, givens = game["grid"], game["givens"]
    bad = {i for i in conflicts(grid) if not givens[i]}
    lines = ["    1 2 3   4 5 6   7 8 9"]
    for r in range(9):
        if r and r % 3 == 0:
            lines.append("   -------+-------+------")
        row = [f"{r + 1} "]
        for c in range(9):
            if c and c % 3 == 0:
                row.append("|")
            i = r * 9 + c
            v = grid[i]
            row.append("!" if i in bad else str(v) if v else "," if game["notes"].get(i) else ".")
        lines.append(" ".join(row))
    lines.append("('.' empty, ',' has pencil marks, '!' conflicting entry)")
    return "\n".join(lines)


def apply_command(game, line):
    """Apply one play command. Returns a message for the player."""
    parts = line.split()
    if not parts:
        return ""
    cmd = parts[0].lower()
    grid, givens, notes = game["grid"], game["givens"], game["notes"]
    if cmd == "help":
        return PLAY_HELP
    if cmd == "hint":
        wrong = mistakes(grid, game["solution"])
        if wrong:
            return "Fix your mistakes first: " + ", ".join(cell_name(i) for i in wrong)
        h = find_hint(grid)
        if h is None:
            if 0 not in grid:
                return "The puzzle is already complete."
            i = grid.index(0)
            h = (i, game["solution"][i], f"No single available - revealed {cell_name(i)} from the solution.")
        i, v, why = h
        grid[i] = v
        notes.pop(i, None)
        return why
    if cmd == "check":
        wrong = mistakes(grid, game["solution"])
        if not wrong:
            return "No mistakes so far."
        return f"{len(wrong)} wrong: " + ", ".join(cell_name(i) for i in wrong)
    if cmd == "notes":
        if not notes:
            return "No pencil marks."
        return "\n".join(f"{cell_name(i)}: {' '.join(map(str, sorted(s)))}"
                         for i, s in sorted(notes.items()))
    nums = parts[1:] if cmd == "n" else parts
    if len(nums) != 3 or not all(p.isdigit() and len(p) == 1 for p in nums):
        return "Unknown command - type 'help'."
    r, c, v = map(int, nums)
    if not (1 <= r <= 9 and 1 <= c <= 9) or (cmd == "n" and v == 0):
        return "Rows/cols are 1-9, digits 1-9."
    i = (r - 1) * 9 + c - 1
    if givens[i]:
        return f"{cell_name(i)} is a given clue."
    if cmd == "n":
        if grid[i]:
            return f"{cell_name(i)} is filled; erase it first."
        marks = notes.setdefault(i, set())
        marks ^= {v}
        if not marks:
            del notes[i]
        return f"{cell_name(i)} marks: {' '.join(map(str, sorted(marks))) or '(none)'}"
    grid[i] = v
    if v == 0:
        return f"Erased {cell_name(i)}."
    notes.pop(i, None)
    for p in PEERS[i]:  # placing a digit clears it from peers' pencil marks
        if v in notes.get(p, ()):
            notes[p].discard(v)
            if not notes[p]:
                del notes[p]
    if not can_place(grid, i, v):
        return f"Placed {v} at {cell_name(i)} - conflicts with a peer!"
    return f"Placed {v} at {cell_name(i)}."


def play(game):
    print(PLAY_HELP)
    while True:
        print("\n" + render_play(game))
        if is_solved(game["grid"]):
            print("\nSolved! Well done.")
            return
        try:
            line = input("play> ").strip()
        except EOFError:
            return
        if line.lower() in ("q", "quit", "exit"):
            return
        msg = apply_command(game, line)
        if msg:
            print(msg)


def play_menu():
    try:
        d = input("Play which? (easy/medium/hard/sample) [medium]: ").strip().lower() or "medium"
    except EOFError:
        return
    if d == "sample":
        play(new_game(parse(SAMPLE), parse(SAMPLE_SOLUTION)))
    elif d in DIFFICULTY:
        play(new_game(*generate(d)))
    else:
        print("Unknown choice.")


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
        print("4) Play a puzzle")
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
        elif choice == "4":
            play_menu()
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
    # Play mode + hints.
    game = new_game(g, sol)
    assert "given" in apply_command(game, "1 1 9")
    assert apply_command(game, "n 1 3 4").endswith("4")
    apply_command(game, "n 1 3 2")
    apply_command(game, "n 1 4 4")
    assert apply_command(game, "1 3 4") == "Placed 4 at r1c3."
    assert 2 not in game["notes"] and 3 not in game["notes"], "placing clears own and peer marks"
    assert "conflicts" in apply_command(game, "1 4 5")  # 5 already in row 1
    assert conflicts(game["grid"]) and "!" in render_play(game)
    assert "r1c4" in apply_command(game, "check")
    assert "Fix your mistakes" in apply_command(game, "hint")
    assert apply_command(game, "1 4 0") == "Erased r1c4."
    assert apply_command(game, "check") == "No mistakes so far."
    assert "Unknown" in apply_command(game, "foo")
    for _ in range(81):
        if is_solved(game["grid"]):
            break
        msg = apply_command(game, "hint")
        assert "single" in msg or "revealed" in msg, msg
    assert game["grid"] == sol, "hints must solve the sample correctly"
    h = find_hint(g)
    assert h and sol[h[0]] == h[1]
    # Hidden single: row 1 lacks 1, 2, 3 in c1-c3; 1s in columns 2 and 3 leave
    # r1c1 as the only spot for 1, though every cell has 2+ candidates.
    hs_grid = [0] * 81
    hs_grid[3:9] = [4, 5, 6, 7, 8, 9]
    hs_grid[4 * 9 + 1] = hs_grid[7 * 9 + 2] = 1
    kind_hint = find_hint(hs_grid)
    assert kind_hint[:2] == (0, 1) and kind_hint[2].startswith("Hidden single"), kind_hint
    print("self-check passed")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        self_check()
    else:
        menu()
