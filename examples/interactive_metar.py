"""Interactive METAR decoder: type a report, get it decoded, repeat.

Usage:
    uv run python examples/interactive_metar.py           # human-readable summary
    uv run python examples/interactive_metar.py --raw     # also print the `Metar` object

Type an empty line, `exit` or press Ctrl+D to quit.
"""

import sys
from pprint import pprint

from metar_taf_parser.exceptions import ParseError
from metar_taf_parser.parsers.metar import MetarParser

PROMPT = "METAR> "
EXIT_COMMANDS = frozenset({"", "exit", "quit"})


def main(argv: list[str]) -> int:
    """Read reports from the keyboard until the user quits."""
    show_raw = "--raw" in argv
    metar_p = MetarParser()

    print("Paste a METAR report (empty line or `exit` to quit).")
    while True:
        try:
            raw = input(PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if raw.lower() in EXIT_COMMANDS:
            break

        try:
            metar = metar_p.parse(raw)
        except ParseError as error:
            print(f"  ✗ {type(error).__name__}: {error}\n")
            continue

        # print(describe(metar))
        pprint(metar)
        if show_raw:
            pprint(metar)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
