<!-- LAB_STATE:START -->
<p align="center">
  <img src="./assets/live-seir-lab.svg?v=1-12-0" width="100%" alt="Visitor-controlled live SEIR simulation">
</p>

**Current state:** Day 12 | S 897 | E 35 | I 38 | R 30 | Effective reproduction number 2.51

Last command: **Baseline transmission** by [@AashishThakuri](https://github.com/AashishThakuri)
<!-- LAB_STATE:END -->

<div align="center">

### Choose what happens on the next day

Each control opens a prepared GitHub Issue. Submit it unchanged. The profile will calculate and redraw itself in about a minute.

<a href="https://github.com/AashishThakuri/AashishThakuri/issues/new?title=%5BLAB%5D%20continue&body=Submit%20this%20issue%20unchanged.%20It%20will%20advance%20the%20live%20SEIR%20model%20by%20one%20day%20with%20its%20baseline%20transmission%20rate."><kbd>NO REDUCTION</kbd></a>&nbsp;&nbsp;
<a href="https://github.com/AashishThakuri/AashishThakuri/issues/new?title=%5BLAB%5D%20reduce-25&body=Submit%20this%20issue%20unchanged.%20It%20will%20advance%20the%20live%20SEIR%20model%20by%20one%20day%20with%20beta%20reduced%20by%2025%20percent."><kbd>REDUCE BETA 25%</kbd></a>&nbsp;&nbsp;
<a href="https://github.com/AashishThakuri/AashishThakuri/issues/new?title=%5BLAB%5D%20reduce-50&body=Submit%20this%20issue%20unchanged.%20It%20will%20advance%20the%20live%20SEIR%20model%20by%20one%20day%20with%20beta%20reduced%20by%2050%20percent."><kbd>REDUCE BETA 50%</kbd></a>&nbsp;&nbsp;
<a href="https://github.com/AashishThakuri/AashishThakuri/issues/new?title=%5BLAB%5D%20reduce-75&body=Submit%20this%20issue%20unchanged.%20It%20will%20advance%20the%20live%20SEIR%20model%20by%20one%20day%20with%20beta%20reduced%20by%2075%20percent."><kbd>REDUCE BETA 75%</kbd></a>

</div>

<details>
<summary><strong>How can a GitHub profile run a simulation?</strong></summary>

1. A visitor selects an intervention and submits the prepared issue.
2. GitHub Actions reads the selected transmission reduction.
3. Python solves the next SEIR day as an initial-value problem using RK4.
4. The workflow saves the new state, regenerates the SVG, updates this README, and closes the issue.

There is no application server and no database. The repository is the state machine. [Read the simulation engine](./profile_lab.py).

</details>

## Aashish Thakuri

I build software that can be tested, inspected, and explained. My work moves between full-stack systems, data, numerical modelling, computer vision, and applied AI.

## Selected work

**[Covid-19-SEIR-Model](https://github.com/AashishThakuri/Covid-19-SEIR-Model)**
Two Nepal COVID-19 waves solved with RK4, ten fitted transmission segments per wave, validation against Johns Hopkins data, and intervention scenarios.

**[Hand Gesture Live Visuals](https://github.com/AashishThakuri/hand-gesture-live-visuals)**
A real-time OpenCV instrument with twelve visual effects controlled through MediaPipe hand tracking.

**[RiskLock](https://github.com/AashishThakuri/EsewaHackathon_TeamLyrical_ChallengeSix_Submission)**
Adaptive account recovery using device and behavior signals, Qwen3 with LoRA, FastAPI, React, Vite, and MySQL.

## Working set

`Python` `JavaScript` `TypeScript` `React` `FastAPI` `MySQL` `OpenCV` `MediaPipe` `NumPy` `Pandas` `SciPy`
