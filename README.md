# metar-taf-parser

A Python library for parsing METAR and TAF aviation weather reports into
typed, immutable Python objects.

[![CI](https://github.com/Darkroos888/metar-taf-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/Darkroos888/metar-taf-parser/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> 🚧 **Status: early development.** This project is being built test-first,
> one weather group at a time. See [Roadmap](#roadmap) for what's implemented
> today. Not yet published to PyPI.

## Why this library

METAR and TAF reports pack a lot of information into a dense, fixed-format
string (`METAR LEMD 161200Z 24010G20KT 9999 FEW020 18/12 Q1015 NOSIG`).
`metar-taf-parser` turns that string into typed dataclasses — wind, visibility,
sky condition, temperature, pressure, present weather — so you can work with
structured data instead of parsing regular expressions yourself.

## Installation

Not yet published to PyPI. Once released:

```bash
pip install metar-taf-parser
```

For now, install directly from GitHub:

```bash
pip install git+https://github.com/Darkroos888/metar-taf-parser.git
```

## Usage

```python
from metar_taf_parser import parse_metar

metar = parse_metar("METAR LEMD 161200Z 24010G20KT 9999 FEW020 18/12 Q1015 NOSIG")

metar.station_id                 # "LEMD"
metar.conditions.wind.direction  # 240
metar.conditions.wind.speed      # 10
metar.conditions.wind.gust       # 20
metar.conditions.wind.unit       # WindUnit.KT
metar.temperature.air            # 18
metar.pressure.value             # 1015.0
```

> The top-level `parse_metar()` entry point is part of the target API and not
> implemented yet — see [Roadmap](#roadmap). Individual group parsers
> (e.g. wind) are being built and tested first.

## Development setup

Requires Python 3.10+ and [`uv`](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Darkroos888/metar-taf-parser.git
cd metar-taf-parser
uv sync --extra dev
```

Run the test suite:

```bash
uv run pytest
```

Run the linter:

```bash
uv run ruff check .
```

Auto-fix what ruff can fix on its own (import order, safe rewrites):

```bash
uv run ruff check --fix .
```

Run everything CI runs, in one line:

```bash
uv run ruff check . && uv run pytest
```

Build the documentation:

```bash
uv run pdoc --html --output-dir docs src/metar_taf_parser
```

## Project architecture

The library is organized in three layers:

- **`models.py`** — immutable value objects (`Wind`, `Visibility`,
  `CloudLayer`, `SkyCondition`, `Temperature`, `Pressure`, `Metar`, `Taf`...)
- **`groups/`** — one parser per METAR/TAF group (wind, visibility, clouds,
  temperature, pressure, present weather...), each implementing a shared
  `matches()` / `parse()` contract
- **`parsers/`** — orchestrators (`MetarParser`, `TafParser`) that tokenize a
  raw report and delegate each token to the right group parser

Full class diagrams, design rationale, and naming conventions are documented
in [`CONTEXT.md`](./CONTEXT.md).

## Methodology

Built test-first: for each weather group, behavioral tests are written
before any parsing logic exists (and are expected to fail), then the logic
is implemented until they pass, then refactored. Each group is developed on
its own branch and merged via pull request once CI is green. The commit
history within each branch intentionally keeps `test:` and `feat:` commits
separate, so the red → green cycle is visible.

## Contributing

1. Branch from `main`: `feat/<group-name>` for new parsing logic,
   `fix/`, `refactor/`, `chore/`, `docs/` for everything else
2. Write failing tests first, commit as `test: ...`
3. Implement until tests pass, commit as `feat: ...`
4. Open a pull request — CI must pass (ruff + pytest on Python 3.10–3.12)
   before merging

See [`CONTEXT.md`](./CONTEXT.md) for the full architecture and conventions.

## Roadmap

- [x] Domain model (value objects, enums)
- [ ] `Tokenizer`
- [ ] Group parsers: wind, visibility, clouds, vertical visibility,
      temperature, pressure, present weather
- [ ] `MetarParser` orchestration
- [ ] `TafParser` and TAF change groups (`FM`/`BECMG`/`TEMPO`/`PROBxx`)
- [ ] PyPI release

## License

MIT — see [`LICENSE`](./LICENSE).
