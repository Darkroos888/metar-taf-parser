"""Decode METAR reports into a human-readable summary.

Usage:
    uv run python examples/decode_metar.py                      # decode the built-in samples
    uv run python examples/decode_metar.py "METAR LEMD 161200Z 24010KT CAVOK 18/12 Q1015"
    echo "LEBL 161430Z 18012KT 9999 FEW020 24/20 Q1009" | uv run python examples/decode_metar.py -
"""

import sys

from metar_taf_parser.enums import PressureUnit, VisibilityUnit
from metar_taf_parser.exceptions import ParseError
from metar_taf_parser.models import Metar, PresentWeather, Wind
from metar_taf_parser.parsers.metar import MetarParser

SAMPLES = [
    "METAR LEMD 161200Z 24010KT CAVOK 18/12 Q1015 NOSIG=",
    "METAR KJFK 161151Z 24010G18KT 10SM FEW050 SCT250 22/14 A2992 RMK AO2 SLP132",
    "METAR LEVD 160600Z 00000KT 0100 FG VV001 M01/M01 Q1022",
    "METAR EFHK 160920Z AUTO 35015G25KT 3000 -SN BKN008 OVC015 M05/M07 Q0998",
    "METAR LEBL 161430Z 18012KT 150V210 6000 +TSRA FEW020CB BKN040 24/20 Q1009",
    "METAR COR KORD 160356Z VRB03KT 1 1/2SM BR OVC004 M02/M03 A3012",
    "METAR LEMD 161200Z 24010KT XYZ123 18/12 Q1015",  # invalid on purpose
]


def describe_wind(wind: Wind) -> str:
    """Return a one-line description of the wind."""
    unit = wind.unit.value
    if wind.speed == 0:
        return "calm"
    direction = "variable" if wind.variable else f"{wind.direction:03d}°"
    text = f"{direction} at {wind.speed} {unit}"
    if wind.gust is not None:
        text += f", gusting {wind.gust} {unit}"
    if wind.variable_range is not None:
        low, high = wind.variable_range
        text += f" (varying {low:03d}°-{high:03d}°)"
    return text


def describe_weather(weather: PresentWeather) -> str:
    """Return a description such as `heavy thunderstorm rain`."""
    words = [] if weather.intensity.value == "" else [weather.intensity.name.lower()]
    words += [descriptor.name.lower() for descriptor in weather.descriptors]
    words += [phenomenon.name.lower() for phenomenon in weather.phenomena]
    return " ".join(words).replace("_", " ")


def describe(metar: Metar) -> str:
    """Return a multi-line, human-readable summary of a parsed METAR."""
    conditions = metar.conditions
    flags = [name for name, on in (("AUTO", metar.auto), ("COR", metar.corrected)) if on]

    lines = [
        f"Station:      {metar.station_id}" + (f"  [{' '.join(flags)}]" if flags else ""),
        f"Observed:     {metar.observation_time:%Y-%m-%d %H:%M} UTC",
        f"Wind:         {describe_wind(conditions.wind)}",
    ]

    if conditions.cavok:
        lines.append("Visibility:   CAVOK (≥10 km, no significant cloud or weather)")
    elif conditions.visibility is not None:
        visibility = conditions.visibility
        if visibility.unit is VisibilityUnit.METERS:
            lines.append(f"Visibility:   {visibility.distance:g} m")
        else:
            lines.append(f"Visibility:   {visibility.distance:g} statute miles")

    if conditions.weather:
        lines.append(f"Weather:      {', '.join(describe_weather(w) for w in conditions.weather)}")

    if conditions.sky is not None:
        for layer in conditions.sky.clouds:
            convective = f" {layer.convective_type}" if layer.convective_type else ""
            lines.append(f"Clouds:       {layer.amount.value} at {layer.height_ft} ft{convective}")
        vertical = conditions.sky.vertical_visibility
        if vertical is not None:
            height = "unknown" if vertical.height_ft is None else f"{vertical.height_ft} ft"
            lines.append(f"Vertical vis: {height} (sky obscured)")

    temperature = metar.temperature
    dew_point = "n/a" if temperature.dew_point is None else f"{temperature.dew_point} °C"
    lines.append(f"Temperature:  {temperature.air} °C, dew point {dew_point}")

    pressure = metar.pressure
    unit = "hPa" if pressure.unit is PressureUnit.HPA else "inHg"
    lines.append(f"Pressure:     {pressure.value:g} {unit}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    """Decode the reports given on the command line, on stdin (`-`), or the samples."""
    if argv == ["-"]:
        reports = [line.strip() for line in sys.stdin if line.strip()]
    elif argv:
        reports = [" ".join(argv)]
    else:
        reports = SAMPLES

    parser = MetarParser()
    failures = 0

    for raw in reports:
        print(raw)
        try:
            print(describe(parser.parse(raw)))
        except ParseError as error:
            failures += 1
            print(f"  ✗ {type(error).__name__}: {error}")
        print()

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
