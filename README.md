# metar-taf-parser

A pure-Python library (no dependencies) that parses METAR aviation weather
reports into typed, immutable Python objects. TAF support is planned.

[![CI](https://github.com/Darkroos888/metar-taf-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/Darkroos888/metar-taf-parser/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> 🚧 **Alpha.** METAR parsing works end to end; TAF is not implemented yet and
> the package is not on PyPI. The import path will get shorter once the
> public API (`parse_metar()`) lands — see [Roadmap](#roadmap).

```text
METAR LEBL 161430Z 18012G22KT 150V210 6000 +TSRA FEW020CB BKN040 24/20 Q1009 NOSIG
```

becomes

```python
Metar(
    station_id="LEBL",
    observation_time=datetime(2026, 9, 16, 14, 30, tzinfo=timezone.utc),
    conditions=WeatherConditions(
        wind=Wind(direction=180, speed=12, gust=22, unit=WindUnit.KT, variable_range=(150, 210)),
        visibility=Visibility(distance=6000, unit=VisibilityUnit.METERS),
        sky=SkyCondition(clouds=(
            CloudLayer(amount=CloudAmount.FEW, height_ft=2000, convective_type="CB"),
            CloudLayer(amount=CloudAmount.BKN, height_ft=4000),
        )),
        weather=(PresentWeather(
            intensity=WeatherIntensity.HEAVY,
            descriptors=(WeatherDescriptor.THUNDERSTORM,),
            phenomena=(WeatherPhenomenon.RAIN,),
        ),),
    ),
    temperature=Temperature(air=24, dew_point=20),
    pressure=Pressure(value=1009.0, unit=PressureUnit.HPA),
    ...
)
```

## Installation

From GitHub (requires Python 3.10+):

```bash
pip install git+https://github.com/Darkroos888/metar-taf-parser.git
# or
uv add git+https://github.com/Darkroos888/metar-taf-parser.git
```

## Usage

```python
from metar_taf_parser.parsers.metar import MetarParser

parser = MetarParser()
metar = parser.parse("METAR LEMD 161200Z 24010G20KT 9999 FEW020 18/12 Q1015 NOSIG")

metar.station_id                     # 'LEMD'
metar.observation_time               # datetime(..., 16, 12, 0, tzinfo=timezone.utc)
metar.conditions.wind.direction      # 240
metar.conditions.wind.gust           # 20
metar.conditions.wind.unit           # WindUnit.KT
metar.conditions.visibility.distance # 9999
metar.conditions.sky.clouds[0]       # CloudLayer(amount=CloudAmount.FEW, height_ft=2000)
metar.temperature.air                # 18
metar.pressure.value                 # 1015.0
```

A `MetarParser` holds no per-report state, so one instance can parse any
number of reports.

### Observation time

A METAR timestamp (`161200Z`) only carries day, hour and minute. The year and
month are taken from `reference` (default: the current UTC time). If the
report's day is later than the reference day, the report is assumed to be from
the previous month:

```python
from datetime import datetime, timezone

metar = parser.parse(
    "METAR LEMD 302330Z 24010KT CAVOK 18/12 Q1015",
    reference=datetime(2026, 10, 1, 0, 30, tzinfo=timezone.utc),
)
metar.observation_time  # 2026-09-30 23:30 UTC
```

Pass a `reference` when parsing historical reports, so they aren't dated
relative to today.

### Errors

Every error derives from `ParseError`:

| Exception | Raised when |
|---|---|
| `UnknownTokenError` | A group isn't recognised by any parser (e.g. `XYZ123`) |
| `InvalidReportError` | The report is structurally broken: missing station, timestamp, wind, temperature or pressure; impossible time; a `dddVddd` group with no wind before it |

```python
from metar_taf_parser.exceptions import ParseError

try:
    metar = parser.parse(raw)
except ParseError as error:
    print(f"Could not parse {raw!r}: {error}")
```

### Example scripts

The [`examples/`](./examples) folder has two small programs:

```bash
# Decode some sample reports, or one passed as an argument
uv run python examples/decode_metar.py
uv run python examples/decode_metar.py "METAR LEMD 161200Z 24010KT CAVOK 18/12 Q1015"

# Interactive prompt: paste a report, see it decoded
uv run python examples/interactive_metar.py
```

## What is supported

| Group | Examples | Result |
|---|---|---|
| Header | `METAR`/`SPECI`, `LEMD`, `161200Z`, `AUTO`, `COR` | `station_id`, `observation_time`, `auto`, `corrected` |
| Wind | `24010KT`, `24010G20KT`, `VRB03KT`, `00000KT`, `01006MPS` + `150V210` | `Wind` |
| Visibility | `9999`, `0800`, `10SM`, `1/2SM`, `1 1/2SM`, `M1/4SM` | `Visibility` |
| `CAVOK` | `CAVOK` | `conditions.cavok = True`, `visibility`/`sky` left as `None` |
| Present weather | `-SN`, `+TSRA`, `VCSH`, `FZFG`, `BR` | `PresentWeather` (one per group) |
| Clouds | `FEW020`, `BKN040CB`, `SCT030TCU`, `SKC`, `CLR`, `NSC` | `CloudLayer`s in `SkyCondition` |
| Vertical visibility | `VV001`, `VV///` | `VerticalVisibility` in `SkyCondition` |
| Temperature | `18/12`, `M01/M03`, `20/` | `Temperature` (°C) |
| Pressure | `Q1015`, `A2992` | `Pressure` (hPa or inHg) |
| Ignored | `NOSIG`, trailing `=`, everything after `RMK` | — |

### Known limitations

These real-world groups are **not** supported yet and make `parse()` raise:

- `NCD` (no cloud detected, from automated stations)
- Directional visibility: `0150 0100SW`
- Runway visual range: `R28/0700`, `R25/0400D`
- Runway state: `R06R/CLRD62`, `R14R/0///95`
- Reports from automated stations that omit the wind or temperature group
  (sensor outage)
- Trend forecasts (`BECMG`, `TEMPO`), recent weather (`RERA`), wind shear (`WS`)

Remarks (`RMK ...`) are dropped, not decoded.

## Data model

All models are frozen dataclasses (`metar_taf_parser.models`). Collections are
tuples, so a parsed report is fully immutable and can be compared with `==`.
Coded values are enums (`metar_taf_parser.enums`).

```text
Metar
├── raw_text, station_id, observation_time (UTC), auto, corrected
├── conditions: WeatherConditions
│   ├── wind: Wind               direction | None (VRB), speed, gust, unit, variable, variable_range
│   ├── cavok: bool
│   ├── visibility: Visibility | None
│   ├── sky: SkyCondition | None clouds: tuple[CloudLayer], vertical_visibility
│   └── weather: tuple[PresentWeather]
├── temperature: Temperature     air, dew_point | None
└── pressure: Pressure           value, unit
```

Units are kept as reported. The library does not convert knots to m/s or inHg
to hPa.

## How it works

```text
raw text ──▶ Tokenizer ──▶ header ──▶ group parsers ──▶ assemble ──▶ Metar
             (drops RMK)   (station,   (one token at a   (folds 150V210
                            time…)      time, first       into Wind, builds
                                        match wins)       SkyCondition…)
```

- **`groups/`**: one parser per group (wind, visibility, clouds, …), each with
  `matches(token)` and `parse(token)`. Shared by METAR and TAF.
- **`parsers/`**: `MetarParser` (and later `TafParser`) run the pipeline above.
  The shared steps live in `AbstractReportParser`. Each report type only
  implements how to read its header and how to assemble the result.

## Development

Requires [`uv`](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Darkroos888/metar-taf-parser.git
cd metar-taf-parser
uv sync --extra dev
```

| Task | Command |
|---|---|
| Run tests (with coverage) | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Auto-fix lint | `uv run ruff check --fix .` |
| Format | `uv run ruff format .` |
| What CI runs | `uv run ruff check . && uv run pytest` |
| Browse docs (live reload) | `uv run pdoc metar_taf_parser --docformat google` |
| Build static docs | `uv run pdoc metar_taf_parser --docformat google -o docs/_build` |

CI runs ruff and pytest on Python 3.10, 3.11 and 3.12 on every push.

### Contributing

The project is built test-first, one group at a time:

1. Branch from `dev`: `feat/<name>` for parsing logic; `fix/`, `refactor/`,
   `chore/` or `docs/` for everything else.
2. Commit the failing tests first (`test: ...`).
3. Make them pass (`feat: ...`), then optionally clean up (`refactor: ...`).
4. Open a pull request into `dev`. CI must be green. Merge without squashing,
   so the red → green history stays visible.

`dev` is merged into `main` once it is green.

## Roadmap

- [x] Domain model, enums, exceptions
- [x] `Tokenizer`
- [x] Group parsers: wind, visibility, clouds, vertical visibility,
      temperature, pressure, present weather
- [x] `MetarParser`
- [ ] Public API: `from metar_taf_parser import parse_metar, parse_taf`
- [ ] The [known limitations](#known-limitations) above
- [ ] `TafParser` and TAF change groups (`FM`/`BECMG`/`TEMPO`/`PROB30`/`PROB40`)
- [ ] PyPI release

## License

MIT — see [`LICENSE`](./LICENSE).
