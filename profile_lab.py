"""Generate the self-running RK4 experiment shown on the profile README."""

import argparse
import math
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "assets" / "rk4-four-futures.svg"

POPULATION = 1000.0
BASE_BETA = 0.28
SIGMA = 1 / 5
GAMMA = 1 / 10
SIMULATION_DAYS = 60
DOT_COUNT = 180

SCENARIOS = (
    {"key": "base", "label": "0% REDUCTION", "factor": 1.00, "curve": "curve-base"},
    {"key": "cut25", "label": "25% REDUCTION", "factor": 0.75, "curve": "curve-25"},
    {"key": "cut50", "label": "50% REDUCTION", "factor": 0.50, "curve": "curve-50"},
    {"key": "cut75", "label": "75% REDUCTION", "factor": 0.25, "curve": "curve-75"},
)


def derivatives(values, beta):
    """Return dS/dt, dE/dt, dI/dt, and dR/dt."""

    susceptible, exposed, infected, removed = values
    new_exposed = beta * susceptible * infected / POPULATION
    new_infected = SIGMA * exposed
    new_removed = GAMMA * infected
    return (
        -new_exposed,
        new_exposed - new_infected,
        new_infected - new_removed,
        new_removed,
    )


def add_scaled(values, slopes, scale):
    return tuple(value + scale * slope for value, slope in zip(values, slopes))


def rk4_step(values, beta):
    """Advance one day with the fourth-order Runge-Kutta method."""

    k1 = derivatives(values, beta)
    k2 = derivatives(add_scaled(values, k1, 0.5), beta)
    k3 = derivatives(add_scaled(values, k2, 0.5), beta)
    k4 = derivatives(add_scaled(values, k3, 1.0), beta)
    return tuple(
        max(value + (s1 + 2 * s2 + 2 * s3 + s4) / 6, 0.0)
        for value, s1, s2, s3, s4 in zip(values, k1, k2, k3, k4)
    )


def simulate(beta):
    values = (970.0, 18.0, 10.0, 2.0)
    states = [values]
    for _ in range(SIMULATION_DAYS):
        values = rk4_step(values, beta)
        states.append(values)
    return states


def allocate_dots(values):
    raw = [value / POPULATION * DOT_COUNT for value in values]
    counts = [math.floor(value) for value in raw]
    remaining = DOT_COUNT - sum(counts)
    order = sorted(range(4), key=lambda index: raw[index] - counts[index], reverse=True)
    for index in order[:remaining]:
        counts[index] += 1
    return counts


def render_population(values, scenario_index):
    counts = allocate_dots(values)
    statuses = (
        ["susceptible"] * counts[0]
        + ["exposed"] * counts[1]
        + ["infected"] * counts[2]
        + ["removed"] * counts[3]
    )
    random.Random(700 + scenario_index).shuffle(statuses)

    circles = []
    for index, status in enumerate(statuses):
        row, column = divmod(index, 18)
        x = 56 + column * 28
        y = 210 + row * 23
        radius = 6 if status != "infected" else 7
        circles.append(f'<circle class="person {status}" cx="{x}" cy="{y}" r="{radius}"/>')
    return "".join(circles)


def curve_points(states, maximum):
    left, right = 660.0, 1144.0
    top, bottom = 205.0, 408.0
    points = []
    for day, state in enumerate(states):
        x = left + day / SIMULATION_DAYS * (right - left)
        y = bottom - state[2] / maximum * (bottom - top)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def format_number(value):
    return f"{value:,.0f}"


def render_svg(output_path):
    results = []
    for scenario in SCENARIOS:
        beta = BASE_BETA * scenario["factor"]
        states = simulate(beta)
        results.append({**scenario, "beta": beta, "states": states, "final": states[-1]})

    maximum_infected = max(state[2] for result in results for state in result["states"]) * 1.10
    baseline_cumulative = POPULATION - results[0]["final"][0]

    population_layers = []
    active_summaries = []
    curves = []
    endpoint_circles = []
    bottom_summaries = []

    for index, result in enumerate(results):
        cycle_class = f"cycle-{index}"
        susceptible, exposed, infected, removed = result["final"]
        effective_r = result["beta"] / GAMMA * susceptible / POPULATION
        cumulative = POPULATION - susceptible
        decrease = 0 if index == 0 else (baseline_cumulative - cumulative) / baseline_cumulative * 100

        population_layers.append(
            f'<g class="scenario-layer {cycle_class}">{render_population(result["final"], index)}</g>'
        )
        active_summaries.append(
            f'''<g class="scenario-layer {cycle_class}">
  <rect class="{result['curve']}" x="48" y="147" width="8" height="30"/>
  <text class="ink mono" x="70" y="160" font-size="13">CURRENT POPULATION: {result['label']}</text>
  <text class="muted mono" x="70" y="179" font-size="12">BETA {result['beta']:.3f} / Re DAY 60 {effective_r:.2f} / S {format_number(susceptible)} / E {format_number(exposed)} / I {format_number(infected)} / R {format_number(removed)}</text>
</g>'''
        )

        points = curve_points(result["states"], maximum_infected)
        curves.append(
            f'<polyline class="scenario-curve {result["curve"]}" points="{points}"/>'
        )
        last_x, last_y = points.split()[-1].split(",")
        endpoint_circles.append(
            f'<circle class="{result["curve"]}" cx="{last_x}" cy="{last_y}" r="5"/>'
        )

        x = 42 + index * 290
        decrease_text = "BASELINE" if index == 0 else f"{decrease:.1f}% BELOW BASE"
        bottom_summaries.append(
            f'''<g>
  <circle class="{result['curve']}" cx="{x + 6}" cy="500" r="6"/>
  <text class="muted mono" x="{x + 20}" y="505" font-size="12">{result['label']}</text>
  <text class="ink sans" x="{x}" y="540" font-size="27" font-weight="750">{format_number(cumulative)}</text>
  <text class="muted mono" x="{x}" y="561" font-size="11">CUMULATIVE INFECTED / {decrease_text}</text>
</g>'''
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="590" viewBox="0 0 1200 590" role="img" aria-labelledby="title description">
  <title id="title">Four SEIR futures solved with RK4</title>
  <desc id="description">A self-running comparison of four transmission scenarios. The population view automatically cycles while all infection curves remain visible.</desc>
  <style>
    .canvas {{ fill: #ffffff; }}
    .ink {{ fill: #1f2328; }}
    .muted {{ fill: #59636e; }}
    .rule {{ stroke: #d1d9e0; }}
    .band {{ fill: #f6f8fa; }}
    .susceptible {{ fill: #7d8590; }}
    .exposed {{ fill: #bf8700; }}
    .infected {{ fill: #cf222e; }}
    .removed {{ fill: #1a7f37; }}
    .curve-base {{ fill: #cf222e; stroke: #cf222e; }}
    .curve-25 {{ fill: #bc6b00; stroke: #bc6b00; }}
    .curve-50 {{ fill: #0969da; stroke: #0969da; }}
    .curve-75 {{ fill: #1a7f37; stroke: #1a7f37; }}
    .scenario-curve {{ fill: none !important; stroke-width: 3.5; stroke-linecap: round; stroke-linejoin: round; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; letter-spacing: 0; }}
    .sans {{ font-family: Inter, Arial, Helvetica, sans-serif; letter-spacing: 0; }}
    .person.infected {{ animation: breathe 1.7s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
    .scenario-layer {{ opacity: 0; }}
    .cycle-0 {{ animation: show-0 16s step-end infinite; }}
    .cycle-1 {{ animation: show-1 16s step-end infinite; }}
    .cycle-2 {{ animation: show-2 16s step-end infinite; }}
    .cycle-3 {{ animation: show-3 16s step-end infinite; }}
    @keyframes show-0 {{ 0%, 24.99% {{ opacity: 1; }} 25%, 100% {{ opacity: 0; }} }}
    @keyframes show-1 {{ 0%, 24.99% {{ opacity: 0; }} 25%, 49.99% {{ opacity: 1; }} 50%, 100% {{ opacity: 0; }} }}
    @keyframes show-2 {{ 0%, 49.99% {{ opacity: 0; }} 50%, 74.99% {{ opacity: 1; }} 75%, 100% {{ opacity: 0; }} }}
    @keyframes show-3 {{ 0%, 74.99% {{ opacity: 0; }} 75%, 100% {{ opacity: 1; }} }}
    @keyframes breathe {{ 0%, 100% {{ transform: scale(0.82); opacity: 0.72; }} 50% {{ transform: scale(1.18); opacity: 1; }} }}
    @media (prefers-color-scheme: dark) {{
      .canvas {{ fill: #0d1117; }}
      .ink {{ fill: #f0f6fc; }}
      .muted {{ fill: #8b949e; }}
      .rule {{ stroke: #30363d; }}
      .band {{ fill: #161b22; }}
      .susceptible {{ fill: #8c959f; }}
      .exposed {{ fill: #d29922; }}
      .infected {{ fill: #f85149; }}
      .removed {{ fill: #3fb950; }}
      .curve-base {{ fill: #f85149; stroke: #f85149; }}
      .curve-25 {{ fill: #d29922; stroke: #d29922; }}
      .curve-50 {{ fill: #58a6ff; stroke: #58a6ff; }}
      .curve-75 {{ fill: #3fb950; stroke: #3fb950; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .person.infected {{ animation: none; }}
      .scenario-layer {{ animation: none; opacity: 0; }}
      .cycle-0 {{ opacity: 1; }}
    }}
  </style>

  <rect class="canvas" width="1200" height="590"/>
  <text class="muted mono" x="48" y="33" font-size="13">AASHISH THAKURI / EXECUTABLE PROFILE 001</text>
  <text class="muted mono" x="1152" y="33" text-anchor="end" font-size="13">NO SERVER / NO DATABASE / PURE SVG</text>
  <line class="rule" x1="48" y1="49" x2="1152" y2="49"/>

  <text class="ink sans" x="48" y="96" font-size="42" font-weight="850">One equation. Four futures.</text>
  <text class="muted sans" x="48" y="125" font-size="16">The same initial SEIR state branches into four beta scenarios, each solved one day at a time with RK4.</text>

  {''.join(active_summaries)}
  <text class="muted mono" x="648" y="160" font-size="13">ACTIVE INFECTION / ALL FUTURES</text>
  <text class="muted mono" x="1144" y="160" text-anchor="end" font-size="11">DAY 0 TO DAY {SIMULATION_DAYS}</text>
  <line class="rule" x1="615" y1="145" x2="615" y2="430"/>

  {''.join(population_layers)}

  <line class="rule" x1="660" y1="408" x2="1144" y2="408"/>
  <line class="rule" x1="660" y1="205" x2="660" y2="408"/>
  <line class="rule" x1="660" y1="306.5" x2="1144" y2="306.5" opacity="0.55"/>
  <text class="muted mono" x="648" y="209" text-anchor="end" font-size="11">{maximum_infected:.0f}</text>
  <text class="muted mono" x="648" y="310" text-anchor="end" font-size="11">{maximum_infected / 2:.0f}</text>
  <text class="muted mono" x="648" y="412" text-anchor="end" font-size="11">0</text>
  {''.join(curves)}
  {''.join(endpoint_circles)}
  <text class="muted mono" x="660" y="427" font-size="11">DAY 0</text>
  <text class="muted mono" x="1144" y="427" text-anchor="end" font-size="11">DAY {SIMULATION_DAYS}</text>

  <circle class="susceptible" cx="48" cy="452" r="5"/><text class="muted mono" x="60" y="456" font-size="11">S SUSCEPTIBLE</text>
  <circle class="exposed" cx="176" cy="452" r="5"/><text class="muted mono" x="188" y="456" font-size="11">E EXPOSED</text>
  <circle class="infected" cx="284" cy="452" r="5"/><text class="muted mono" x="296" y="456" font-size="11">I INFECTIOUS</text>
  <circle class="removed" cx="414" cy="452" r="5"/><text class="muted mono" x="426" y="456" font-size="11">R REMOVED</text>
  <text class="muted mono" x="1152" y="456" text-anchor="end" font-size="11">DISPLAY SWITCHES EVERY 4 SECONDS</text>

  <rect class="band" x="0" y="477" width="1200" height="113"/>
  <line class="rule" x1="0" y1="477" x2="1200" y2="477"/>
  <line class="rule" x1="300" y1="493" x2="300" y2="574"/>
  <line class="rule" x1="590" y1="493" x2="590" y2="574"/>
  <line class="rule" x1="880" y1="493" x2="880" y2="574"/>
  {''.join(bottom_summaries)}
</svg>
'''

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    results = render_svg(args.output)
    for result in results:
        susceptible, exposed, infected, removed = result["final"]
        print(
            f"{result['label']}: beta={result['beta']:.3f}, "
            f"S={susceptible:.1f}, E={exposed:.1f}, I={infected:.1f}, R={removed:.1f}"
        )


if __name__ == "__main__":
    main()
