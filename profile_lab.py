"""Generate the visitor-controlled SEIR laboratory shown on the profile README."""

import argparse
import html
import json
import math
import random
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_STATE_PATH = ROOT / "lab" / "state.json"
DEFAULT_SVG_PATH = ROOT / "assets" / "live-seir-lab.svg"
DEFAULT_README_PATH = ROOT / "README.md"

POPULATION = 1000.0
BASE_BETA = 0.28
SIGMA = 1 / 5
GAMMA = 1 / 10
DOT_COUNT = 180
MAX_DAYS = 120

ACTIONS = {
    "continue": ("No reduction", 1.00),
    "reduce-25": ("Reduce beta by 25%", 0.75),
    "reduce-50": ("Reduce beta by 50%", 0.50),
    "reduce-75": ("Reduce beta by 75%", 0.25),
}


def derivatives(values, beta):
    """Return daily SEIR change rates for S, E, I, and R."""

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
    """Create the temporary RK4 state values + scale * slopes."""

    return tuple(value + scale * slope for value, slope in zip(values, slopes))


def rk4_step(values, beta):
    """Advance the SEIR initial-value problem by one day with RK4."""

    k1 = derivatives(values, beta)
    k2 = derivatives(add_scaled(values, k1, 0.5), beta)
    k3 = derivatives(add_scaled(values, k2, 0.5), beta)
    k4 = derivatives(add_scaled(values, k3, 1.0), beta)

    next_values = tuple(
        value + (s1 + 2 * s2 + 2 * s3 + s4) / 6
        for value, s1, s2, s3, s4 in zip(values, k1, k2, k3, k4)
    )
    return tuple(max(value, 0.0) for value in next_values)


def initial_state():
    """Create a short baseline so the first rendered graph already has a shape."""

    values = (970.0, 18.0, 10.0, 2.0)
    history = [{"day": 0, "infected": values[2], "beta": BASE_BETA}]

    for day in range(1, 13):
        values = rk4_step(values, BASE_BETA)
        history.append({"day": day, "infected": values[2], "beta": BASE_BETA})

    return {
        "run": 1,
        "day": 12,
        "susceptible": values[0],
        "exposed": values[1],
        "infected": values[2],
        "removed": values[3],
        "history": history,
        "last_action": "Baseline transmission",
        "last_actor": "AashishThakuri",
        "total_actions": 0,
    }


def load_state(path):
    if not path.exists():
        return initial_state()
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def clean_actor(actor):
    cleaned = re.sub(r"[^A-Za-z0-9-]", "", actor or "visitor")
    return cleaned[:39] or "visitor"


def advance_state(state, action, actor):
    """Apply one visitor decision and advance exactly one model day."""

    if action not in ACTIONS:
        raise ValueError(f"Unknown action: {action}")

    if state["day"] >= MAX_DAYS or state["exposed"] + state["infected"] < 0.1:
        new_state = initial_state()
        new_state["run"] = int(state.get("run", 1)) + 1
        state = new_state

    label, beta_factor = ACTIONS[action]
    beta = BASE_BETA * beta_factor
    values = (
        state["susceptible"],
        state["exposed"],
        state["infected"],
        state["removed"],
    )
    values = rk4_step(values, beta)

    state["day"] += 1
    state["susceptible"], state["exposed"], state["infected"], state["removed"] = values
    state["last_action"] = label
    state["last_actor"] = clean_actor(actor)
    state["total_actions"] = int(state.get("total_actions", 0)) + 1
    state["history"].append(
        {"day": state["day"], "infected": state["infected"], "beta": beta}
    )
    state["history"] = state["history"][-MAX_DAYS:]
    return state


def allocate_dots(state):
    """Convert the four model proportions into exactly DOT_COUNT visible dots."""

    values = [
        state["susceptible"],
        state["exposed"],
        state["infected"],
        state["removed"],
    ]
    raw_counts = [value / POPULATION * DOT_COUNT for value in values]
    counts = [math.floor(value) for value in raw_counts]
    remainder = DOT_COUNT - sum(counts)
    fractions = sorted(
        range(4), key=lambda index: raw_counts[index] - counts[index], reverse=True
    )
    for index in fractions[:remainder]:
        counts[index] += 1
    return counts


def graph_points(history):
    left, right = 662.0, 1140.0
    top, bottom = 181.0, 365.0
    infected_values = [float(item["infected"]) for item in history]
    maximum = max(max(infected_values), 25.0) * 1.10

    points = []
    for index, infected in enumerate(infected_values):
        x = left if len(history) == 1 else left + index / (len(history) - 1) * (right - left)
        y = bottom - infected / maximum * (bottom - top)
        points.append((x, y))
    return points, maximum


def format_number(value):
    return f"{value:,.0f}"


def render_svg(state, path):
    """Render the current population and active-infection history as one SVG."""

    dot_counts = allocate_dots(state)
    statuses = (
        ["susceptible"] * dot_counts[0]
        + ["exposed"] * dot_counts[1]
        + ["infected"] * dot_counts[2]
        + ["removed"] * dot_counts[3]
    )
    random.Random(state["run"] * 10_000 + state["day"]).shuffle(statuses)

    dots = []
    for index, status in enumerate(statuses):
        row, column = divmod(index, 18)
        x = 61 + column * 29
        y = 170 + row * 23
        radius = 6 if status != "infected" else 7
        dots.append(
            f'<circle class="person {status}" cx="{x}" cy="{y}" r="{radius}"/>'
        )

    points, graph_maximum = graph_points(state["history"])
    point_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    current_x, current_y = points[-1]
    actor = html.escape(state["last_actor"])
    action = html.escape(state["last_action"])
    current_beta = float(state["history"][-1]["beta"])
    r0 = current_beta / GAMMA
    effective_r = r0 * state["susceptible"] / POPULATION

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="560" viewBox="0 0 1200 560" role="img" aria-labelledby="title description">
  <title id="title">Aashish Thakuri visitor-controlled SEIR laboratory</title>
  <desc id="description">A live SEIR population and active-infection curve. GitHub visitors choose the transmission rate and RK4 advances the model.</desc>
  <style>
    .canvas {{ fill: #ffffff; }}
    .ink {{ fill: #1f2328; }}
    .muted {{ fill: #59636e; }}
    .rule {{ stroke: #d1d9e0; }}
    .panel {{ fill: #f6f8fa; }}
    .susceptible {{ fill: #7d8590; }}
    .exposed {{ fill: #bf8700; }}
    .infected {{ fill: #cf222e; }}
    .removed {{ fill: #1a7f37; }}
    .curve {{ fill: none; stroke: #cf222e; stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; letter-spacing: 0; }}
    .sans {{ font-family: Inter, Arial, Helvetica, sans-serif; letter-spacing: 0; }}
    .person {{ opacity: 0.94; }}
    .person.infected {{ animation: breathe 1.7s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
    .current {{ animation: blink 1.5s ease-in-out infinite; }}
    @keyframes breathe {{ 0%, 100% {{ transform: scale(0.82); opacity: 0.72; }} 50% {{ transform: scale(1.18); opacity: 1; }} }}
    @keyframes blink {{ 0%, 100% {{ opacity: 0.45; }} 50% {{ opacity: 1; }} }}
    @media (prefers-color-scheme: dark) {{
      .canvas {{ fill: #0d1117; }}
      .ink {{ fill: #f0f6fc; }}
      .muted {{ fill: #8b949e; }}
      .rule {{ stroke: #30363d; }}
      .panel {{ fill: #161b22; }}
      .susceptible {{ fill: #8c959f; }}
      .exposed {{ fill: #d29922; }}
      .infected {{ fill: #f85149; }}
      .removed {{ fill: #3fb950; }}
      .curve {{ stroke: #f85149; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .person.infected, .current {{ animation: none; }}
    }}
  </style>

  <rect class="canvas" width="1200" height="560"/>
  <text class="muted mono" x="48" y="34" font-size="14">AASHISH THAKURI / LIVE SYSTEM 001</text>
  <text class="muted mono" x="1152" y="34" text-anchor="end" font-size="14">RUN {state['run']:02d} / DAY {state['day']:03d}</text>
  <line class="rule" x1="48" y1="51" x2="1152" y2="51"/>

  <text class="ink sans" x="48" y="94" font-size="34" font-weight="800">This profile is running an epidemic model.</text>
  <text class="muted sans" x="48" y="122" font-size="16">Visitors change transmission. RK4 calculates the next day. GitHub commits the result.</text>

  <text class="muted mono" x="48" y="150" font-size="13">POPULATION SAMPLE / 180 PEOPLE</text>
  <text class="muted mono" x="648" y="150" font-size="13">ACTIVE INFECTION HISTORY</text>
  <line class="rule" x1="615" y1="142" x2="615" y2="388"/>

  {''.join(dots)}

  <line class="rule" x1="662" y1="365" x2="1140" y2="365"/>
  <line class="rule" x1="662" y1="181" x2="662" y2="365"/>
  <line class="rule" x1="662" y1="273" x2="1140" y2="273" opacity="0.55"/>
  <text class="muted mono" x="650" y="185" text-anchor="end" font-size="11">{graph_maximum:.0f}</text>
  <text class="muted mono" x="650" y="277" text-anchor="end" font-size="11">{graph_maximum / 2:.0f}</text>
  <text class="muted mono" x="650" y="369" text-anchor="end" font-size="11">0</text>
  <polyline class="curve" points="{point_text}"/>
  <circle class="infected current" cx="{current_x:.1f}" cy="{current_y:.1f}" r="7"/>
  <text class="muted mono" x="662" y="386" font-size="11">DAY {state['history'][0]['day']}</text>
  <text class="muted mono" x="1140" y="386" text-anchor="end" font-size="11">DAY {state['day']}</text>

  <rect class="panel" x="0" y="414" width="1200" height="112"/>
  <line class="rule" x1="0" y1="414" x2="1200" y2="414"/>
  <line class="rule" x1="240" y1="432" x2="240" y2="508"/>
  <line class="rule" x1="480" y1="432" x2="480" y2="508"/>
  <line class="rule" x1="720" y1="432" x2="720" y2="508"/>
  <line class="rule" x1="960" y1="432" x2="960" y2="508"/>

  <circle class="susceptible" cx="48" cy="450" r="6"/><text class="muted mono" x="63" y="455" font-size="13">SUSCEPTIBLE</text>
  <text class="ink sans" x="48" y="494" font-size="28" font-weight="750">{format_number(state['susceptible'])}</text>
  <circle class="exposed" cx="288" cy="450" r="6"/><text class="muted mono" x="303" y="455" font-size="13">EXPOSED</text>
  <text class="ink sans" x="288" y="494" font-size="28" font-weight="750">{format_number(state['exposed'])}</text>
  <circle class="infected" cx="528" cy="450" r="6"/><text class="muted mono" x="543" y="455" font-size="13">INFECTIOUS</text>
  <text class="ink sans" x="528" y="494" font-size="28" font-weight="750">{format_number(state['infected'])}</text>
  <circle class="removed" cx="768" cy="450" r="6"/><text class="muted mono" x="783" y="455" font-size="13">REMOVED</text>
  <text class="ink sans" x="768" y="494" font-size="28" font-weight="750">{format_number(state['removed'])}</text>
  <text class="muted mono" x="1008" y="455" font-size="13">BETA / Re</text>
  <text class="ink sans" x="1008" y="494" font-size="28" font-weight="750">{current_beta:.3f} / {effective_r:.2f}</text>

  <text class="muted mono" x="48" y="548" font-size="12">LAST COMMAND  {action.upper()}  /  @{actor}</text>
  <text class="muted mono" x="1152" y="548" text-anchor="end" font-size="12">SIGMA {SIGMA:.2f} / GAMMA {GAMMA:.2f} / R0 {r0:.2f}</text>
</svg>
'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def dynamic_readme_block(state):
    version = f"{state['run']}-{state['day']}-{state['total_actions']}"
    actor = state["last_actor"]
    actor_text = f"[@{actor}](https://github.com/{actor})"
    beta = float(state["history"][-1]["beta"])
    effective_r = beta / GAMMA * state["susceptible"] / POPULATION
    return f'''<!-- LAB_STATE:START -->
<p align="center">
  <img src="./assets/live-seir-lab.svg?v={version}" width="100%" alt="Visitor-controlled live SEIR simulation">
</p>

**Current state:** Day {state['day']} | S {format_number(state['susceptible'])} | E {format_number(state['exposed'])} | I {format_number(state['infected'])} | R {format_number(state['removed'])} | Effective reproduction number {effective_r:.2f}

Last command: **{state['last_action']}** by {actor_text}
<!-- LAB_STATE:END -->'''


def update_readme(path, state):
    text = path.read_text(encoding="utf-8")
    start_marker = "<!-- LAB_STATE:START -->"
    end_marker = "<!-- LAB_STATE:END -->"
    start = text.index(start_marker)
    end = text.index(end_marker, start) + len(end_marker)
    updated = text[:start] + dynamic_readme_block(state) + text[end:]
    path.write_text(updated, encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=sorted(ACTIONS))
    parser.add_argument("--actor", default="AashishThakuri")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--svg", type=Path, default=DEFAULT_SVG_PATH)
    parser.add_argument("--readme", type=Path, default=DEFAULT_README_PATH)
    return parser.parse_args()


def main():
    args = parse_args()
    state = initial_state() if args.reset else load_state(args.state)

    if args.action:
        state = advance_state(state, args.action, args.actor)
    elif not args.reset and not args.render_only:
        raise SystemExit("Use --action, --reset, or --render-only")

    save_state(args.state, state)
    render_svg(state, args.svg)
    update_readme(args.readme, state)
    print(
        f"Rendered run {state['run']}, day {state['day']}: "
        f"S={state['susceptible']:.1f}, E={state['exposed']:.1f}, "
        f"I={state['infected']:.1f}, R={state['removed']:.1f}"
    )


if __name__ == "__main__":
    main()
