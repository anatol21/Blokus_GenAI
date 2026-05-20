"""Command-line interface for the Blokus engine."""

from argparse import ArgumentParser, Namespace
from collections.abc import Mapping
import json
from pathlib import Path
import sys

from blokus.config import get_mode_config
from blokus.engine import apply_move, is_first_move, list_legal_moves, new_game, pass_turn, validate_loaded_state, validate_move
from blokus.evaluate import main as evaluate_main
from blokus.models import GameState, Move
from blokus.pieces import reference_cell, start_corner_cell
from blokus.players import choose_move
from blokus.render import render_state


def _load_state(path: str) -> GameState:
    """Load a serialized game state from JSON."""

    with Path(path).open("r", encoding="utf-8") as handle:
        state = GameState.from_dict(json.load(handle))
        return state


def _dump_json(payload: Mapping[str, object], output_path: str | None) -> None:
    """Write JSON either to a file or to standard output."""

    if output_path:
        with Path(output_path).open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        return
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def _parse_controllers(mode: str, value: str | None) -> dict[str, str]:
    """Parse the controller list for a mode into a player-to-controller mapping."""

    players = get_mode_config(mode).players
    if value is None:
        return {player: "human" for player in players}
    parsed = tuple(part.strip().lower() for part in value.split(",") if part.strip())
    if len(parsed) != len(players):
        raise ValueError(
            f"Mode '{mode}' expects {len(players)} controller types, got {len(parsed)}."
        )
    for controller in parsed:
        if controller not in {"human", "computer"}:
            raise ValueError("Controller types must be 'human' or 'computer'.")
    return {player: controller for player, controller in zip(players, parsed)}


def _engine_to_human(state: GameState, move: Move) -> tuple[int, int]:
    """Translate engine bounding-box coordinates to human-friendly coordinates.

    For first moves the displayed coordinate is the player's start corner.
    For subsequent moves it is the first occupied cell of the transformed piece.
    """

    if is_first_move(state, move.player):
        return state.start_corners[move.player]
    ref_dx, ref_dy = reference_cell(move.piece, move.rotation, move.flipped)
    return (move.x + ref_dx, move.y + ref_dy)


def _human_to_engine(
    state: GameState,
    player: str,
    piece: str,
    human_x: int,
    human_y: int,
    rotation: int,
    flipped: bool,
) -> tuple[int, int]:
    """Translate human-friendly coordinates to engine bounding-box coordinates.

    For first moves the coordinate is interpreted as the start corner.
    For subsequent moves it is the first occupied cell of the transformed piece.
    """

    if is_first_move(state, player):
        corner = state.start_corners[player]
        cell = start_corner_cell(piece, rotation, flipped, corner, state.board_size)
        if cell is None:
            raise ValueError(
                f"Piece '{piece}' with rotation={rotation} flipped={flipped} "
                f"cannot cover start corner {corner} within the board."
            )
        dx, dy = cell
        return (corner[0] - dx, corner[1] - dy)
    ref_dx, ref_dy = reference_cell(piece, rotation, flipped)
    return (human_x - ref_dx, human_y - ref_dy)


def _move_from_args(state: GameState, args: Namespace) -> Move:
    """Build a move object from parsed CLI arguments.

    Translates human-friendly coordinates to engine bounding-box
    coordinates before constructing the Move.
    """

    player = args.player or state.current_player
    engine_x, engine_y = _human_to_engine(
        state, player, args.piece, args.x, args.y,
        args.rotation, args.flipped,
    )
    return Move(
        player=player,
        piece=args.piece,
        x=engine_x,
        y=engine_y,
        rotation=args.rotation,
        flipped=args.flipped,
    )


def cmd_new(args: Namespace) -> int:
    """Create a fresh game state and emit it as JSON."""
    controllers = _parse_controllers(args.mode, args.players)
    state = new_game(mode=args.mode, controllers=controllers)
    _dump_json(state.to_dict(), args.output)
    return 0



def cmd_show(args: Namespace) -> int:
    """Render a saved game state in the terminal."""

    print(render_state(_load_state(args.state)))
    return 0


def cmd_validate(args: Namespace) -> int:
    """Validate one move against a saved state."""

    state = _load_state(args.state)
    result = validate_move(state, _move_from_args(state, args))
    print(result.reason)
    return 0 if result.ok else 1


def cmd_apply(args: Namespace) -> int:
    """Apply one legal move to a saved state and emit the new state."""

    state = _load_state(args.state)
    move = _move_from_args(state, args)
    result = validate_move(state, move)
    if not result.ok:
        print(result.reason)
        return 1
    new_state = apply_move(state, move)
    _dump_json(new_state.to_dict(), args.output)
    return 0


def cmd_pass_turn(args: Namespace) -> int:
    """Apply a legal pass for the current player."""

    state = _load_state(args.state)
    try:
        new_state = pass_turn(state, player=args.player or state.current_player)
    except ValueError as exc:
        print(str(exc))
        return 1
    _dump_json(new_state.to_dict(), args.output)
    return 0


def cmd_legal_moves(args: Namespace) -> int:
    """List legal moves in text or JSON form."""

    state = _load_state(args.state)
    moves = list_legal_moves(state, player=args.player, limit=args.limit)
    if args.json:
        # JSON output uses raw engine coordinates for programmatic consumers.
        _dump_json({"moves": [move.to_dict() for move in moves]}, args.output)
    else:
        for move in moves:
            hx, hy = _engine_to_human(state, move)
            print(
                f"{move.player}: {move.piece} @ ({hx}, {hy}) "
                f"rotation={move.rotation} flipped={move.flipped}"
            )
    return 0


def cmd_suggest(args: Namespace) -> int:
    """Pick one simple computer move for the requested player."""

    state = _load_state(args.state)
    player = args.player or state.current_player
    strategy = state.controller_strategies.get(player, "default")
    move = choose_move(state, player=player, strategy=strategy)
    if move is None:
        print(f"No legal move exists for {player}.")
        return 1
    if args.json:
        # JSON output uses raw engine coordinates for programmatic consumers.
        _dump_json(move.to_dict(), args.output)
    else:
        hx, hy = _engine_to_human(state, move)
        print(
            f"{move.player}: {move.piece} @ ({hx}, {hy}) "
            f"rotation={move.rotation} flipped={move.flipped}"
        )
    return 0


def _handle_human_turn(state: GameState) -> GameState | None:
    """Run one interactive terminal turn for a human player."""

    print(render_state(state))
    print(
        "\nEnter one of: "
        "'move PIECE X Y ROTATION FLIPPED(0|1)'  (X,Y = occupied cell position), "
        "'legal [N]', 'pass', 'show', 'export', 'import', 'quit'."
    )
    while True:
        raw = input(f"{state.current_player}> ").strip()
        if not raw:
            continue
        if raw == "quit":
            return None
        if raw == "show":
            print(render_state(state))
            continue
        if raw.startswith("export"):
            # Support both `export` (interactive prompts) and `export <path>` convenience form.
            parts = raw.split(maxsplit=1)
            given = parts[1].strip() if len(parts) > 1 else None
            try:
                if given:
                    # Try immediate write; on failure fall through to interactive retry loop.
                    target = Path(given).expanduser()
                    if target.suffix.lower() != ".json":
                        target = target.with_suffix(target.suffix + ".json") if target.suffix else Path(str(target) + ".json")
                    # Attempt write using the established dump path. Overwriting is allowed.
                    try:
                        _dump_json(state.to_dict(), str(target))
                        print(f"Exported game state to {target}")
                        continue
                    except Exception as exc:
                        print(f"Export failed: {exc}")
                        # fall through to interactive retry below
                # Interactive retry loop: ask for filename then path, allow cancel.
                while True:
                    filename = input("Enter filename (or 'cancel' to abort): ").strip()
                    if filename.lower() == "cancel":
                        break
                    if not filename:
                        print("Invalid filename.")
                        continue
                    # append .json if missing
                    if not filename.lower().endswith(".json"):
                        filename = filename + ".json"
                    directory = input("Enter directory path (or 'cancel' to abort): ").strip()
                    if directory.lower() == "cancel":
                        break
                    if not directory:
                        print("Invalid path.")
                        continue
                    outdir = Path(directory).expanduser()
                    if not outdir.exists() or not outdir.is_dir():
                        print("Directory does not exist or is not a directory.")
                        continue
                    target = outdir / filename
                    try:
                        _dump_json(state.to_dict(), str(target))
                        print(f"Exported game state to {target}")
                        break
                    except Exception as exc:
                        print(f"Export failed: {exc}")
                        # retry the path/filename prompts
                continue
            except Exception:
                # Protect the outer loop from unrelated failures; re-raise unexpected errors.
                raise
        if raw.startswith("import"):
            # Support both `import` (interactive prompts) and `import <path>` convenience form.
            parts = raw.split(maxsplit=1)
            given = parts[1].strip() if len(parts) > 1 else None
            try:
                if given:
                    # Try immediate load; on failure fall through to interactive retry loop.
                    target = Path(given).expanduser()
                    if target.suffix.lower() != ".json":
                        target = target.with_suffix(target.suffix + ".json") if target.suffix else Path(str(target) + ".json")
                    try:
                        with open(target, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        loaded = GameState.from_dict(data)
                        validate_loaded_state(loaded)
                        state = loaded
                        print(f"Imported game state from {target}")
                        continue
                    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
                        print(f"Import failed: {exc}")
                        # fall through to interactive retry below
                # Interactive retry loop: ask for filename then path, allow cancel.
                while True:
                    filename = input("Enter filename (or 'cancel' to abort): ").strip()
                    if filename.lower() == "cancel":
                        break
                    if not filename:
                        print("Invalid filename.")
                        continue
                    # append .json if missing
                    if not filename.lower().endswith(".json"):
                        filename = filename + ".json"
                    directory = input("Enter directory path (or 'cancel' to abort): ").strip()
                    if directory.lower() == "cancel":
                        break
                    if not directory:
                        print("Invalid path.")
                        continue
                    indir = Path(directory).expanduser()
                    if not indir.exists() or not indir.is_dir():
                        print("Directory does not exist or is not a directory.")
                        continue
                    target = indir / filename
                    try:
                        with open(target, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        loaded = GameState.from_dict(data)
                        validate_loaded_state(loaded)
                        state = loaded
                        print(f"Imported game state from {target}")
                        break
                    except FileNotFoundError:
                        print(f"File not found: {target}")
                    except json.JSONDecodeError as e:
                        print(f"Invalid JSON: {e}")
                    except ValueError as e:
                        print(f"Import failed: {e}")
                    # retry the path/filename prompts
                continue
            except Exception:
                # Protect the outer loop from unrelated failures; re-raise unexpected errors.
                raise
        if raw.startswith("legal"):
            # Keep legal-move listing lightweight so a human can browse candidates quickly.
            parts = raw.split()
            limit = int(parts[1]) if len(parts) > 1 else 10
            moves = list_legal_moves(state, limit=limit)
            if not moves:
                print("No legal moves.")
            else:
                for move in moves:
                    hx, hy = _engine_to_human(state, move)
                    print(
                        f"{move.piece} @ ({hx}, {hy}) "
                        f"rotation={move.rotation} flipped={move.flipped}"
                    )
            continue
        if raw == "pass":
            try:
                return pass_turn(state)
            except ValueError as exc:
                print(str(exc))
                continue
        if raw.startswith("move "):
            parts = raw.split()
            if len(parts) != 6:
                print("Expected exactly: move PIECE X Y ROTATION FLIPPED")
                continue
            # Translate human-friendly coordinates to engine bounding-box origin.
            piece = parts[1]
            human_x = int(parts[2])
            human_y = int(parts[3])
            rotation = int(parts[4])
            flipped = bool(int(parts[5]))
            try:
                engine_x, engine_y = _human_to_engine(
                    state, state.current_player, piece,
                    human_x, human_y, rotation, flipped,
                )
            except ValueError as exc:
                print(str(exc))
                continue
            except KeyError:
                print(f"Unknown piece '{piece}'. Use 'legal' to see valid pieces.")
                continue
            move = Move(
                player=state.current_player,
                piece=piece,
                x=engine_x,
                y=engine_y,
                rotation=rotation,
                flipped=flipped,
            )
            result = validate_move(state, move)
            if not result.ok:
                print(result.reason)
                continue
            return apply_move(state, move)
        print("Unsupported command.")


def cmd_play(args: Namespace) -> int:
    """Play an interactive or computer-controlled game loop."""

    if args.state:
        state = _load_state(args.state)
    else:
        state = new_game(mode=args.mode, controllers=_parse_controllers(args.mode, args.players))

    max_turns = args.max_turns
    turns = 0
    while not state.finished and (max_turns is None or turns < max_turns):
        controller = state.controller_types.get(state.current_player, "human")
        if controller == "computer":
            strategy = state.controller_strategies.get(state.current_player, "default")
            move = choose_move(state, strategy=strategy)
            if move is None:
                # Computer players pass only when the engine reports no legal move.
                print(f"{state.current_player} passes.")
                state = pass_turn(state)
            else:
                hx, hy = _engine_to_human(state, move)
                print(
                    f"{state.current_player} plays {move.piece} at ({hx}, {hy}) "
                    f"rotation={move.rotation} flipped={move.flipped}"
                )
                state = apply_move(state, move)
        else:
            maybe_state = _handle_human_turn(state)
            if maybe_state is None:
                if args.output:
                    _dump_json(state.to_dict(), args.output)
                return 0
            state = maybe_state
        turns += 1

    print(render_state(state))
    if args.output:
        _dump_json(state.to_dict(), args.output)
    return 0


def cmd_evaluate(_: Namespace) -> int:
    """Delegate to the fixture-backed evaluation harness."""

    return evaluate_main()


def cmd_gui(_: Namespace) -> int:
    """Launch the Classic-mode Tkinter GUI."""

    from blokus.gui import launch_gui

    launch_gui()
    return 0


def build_parser() -> ArgumentParser:
    """Construct the full CLI parser and all subcommands."""

    parser = ArgumentParser(
        prog="blokus",
        description=(
            "Blokus CLI. Coordinates in human-readable output refer to an "
            "occupied cell of the piece being placed. JSON output uses "
            "internal bounding-box origin coordinates."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_parser = subparsers.add_parser("new", help="Create a new game state.")
    new_parser.add_argument("--mode", default="classic")
    new_parser.add_argument("--players", help="Comma-separated controllers, e.g. human,computer,computer,computer")
    new_parser.add_argument("--output", help="Write the JSON state to this path.")
    new_parser.set_defaults(func=cmd_new)

    show_parser = subparsers.add_parser("show", help="Render a saved game state.")
    show_parser.add_argument("--state", required=True)
    show_parser.set_defaults(func=cmd_show)

    validate_parser = subparsers.add_parser("validate", help="Validate a proposed move.")
    validate_parser.add_argument("--state", required=True)
    validate_parser.add_argument("--player")
    validate_parser.add_argument("--piece", required=True)
    validate_parser.add_argument("--x", required=True, type=int, help="Column of an occupied cell of the piece on the board.")
    validate_parser.add_argument("--y", required=True, type=int, help="Row of an occupied cell of the piece on the board.")
    validate_parser.add_argument("--rotation", type=int, default=0)
    validate_parser.add_argument("--flipped", action="store_true")
    validate_parser.set_defaults(func=cmd_validate)

    apply_parser = subparsers.add_parser("apply", help="Apply a legal move and print the new state.")
    apply_parser.add_argument("--state", required=True)
    apply_parser.add_argument("--player")
    apply_parser.add_argument("--piece", required=True)
    apply_parser.add_argument("--x", required=True, type=int, help="Column of an occupied cell of the piece on the board.")
    apply_parser.add_argument("--y", required=True, type=int, help="Row of an occupied cell of the piece on the board.")
    apply_parser.add_argument("--rotation", type=int, default=0)
    apply_parser.add_argument("--flipped", action="store_true")
    apply_parser.add_argument("--output", help="Write the JSON state to this path.")
    apply_parser.set_defaults(func=cmd_apply)

    pass_parser = subparsers.add_parser("pass-turn", help="Pass when no legal move exists.")
    pass_parser.add_argument("--state", required=True)
    pass_parser.add_argument("--player")
    pass_parser.add_argument("--output", help="Write the JSON state to this path.")
    pass_parser.set_defaults(func=cmd_pass_turn)

    legal_parser = subparsers.add_parser("legal-moves", help="List legal moves for a player.")
    legal_parser.add_argument("--state", required=True)
    legal_parser.add_argument("--player")
    legal_parser.add_argument("--limit", type=int)
    legal_parser.add_argument("--json", action="store_true")
    legal_parser.add_argument("--output", help="Write JSON output to this path.")
    legal_parser.set_defaults(func=cmd_legal_moves)

    suggest_parser = subparsers.add_parser("suggest", help="Choose a simple computer move.")
    suggest_parser.add_argument("--state", required=True)
    suggest_parser.add_argument("--player")
    suggest_parser.add_argument("--json", action="store_true")
    suggest_parser.add_argument("--output", help="Write JSON output to this path.")
    suggest_parser.set_defaults(func=cmd_suggest)

    play_parser = subparsers.add_parser("play", help="Play interactively or run computer-vs-computer turns.")
    play_parser.add_argument("--mode", default="classic")
    play_parser.add_argument("--players", help="Comma-separated controllers, e.g. human,computer,computer,computer")
    play_parser.add_argument("--state", help="Resume from an existing JSON state.")
    play_parser.add_argument("--max-turns", type=int)
    play_parser.add_argument("--output", help="Write the final state to this path.")
    play_parser.set_defaults(func=cmd_play)

    evaluate_parser = subparsers.add_parser("evaluate", help="Run the fixture-backed evaluation harness.")
    evaluate_parser.set_defaults(func=cmd_evaluate)

    gui_parser = subparsers.add_parser("gui", help="Launch the Classic-mode GUI.")
    gui_parser.set_defaults(func=cmd_gui)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point used by both `python -m blokus` and tests."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        print(str(exc))
        return 1

def run_cli(argv=None):
    """Compatibility wrapper for old tests."""
    return main(argv)