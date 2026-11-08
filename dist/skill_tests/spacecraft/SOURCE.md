# Spacecraft subsystem figure: evidence and limits

Checked 2026-11-07. This figure is a **domain adaptation** for a notional solar-powered, three-axis-stabilized satellite platform with propulsion. It is not the wiring diagram of a flown spacecraft and does not assign voltages, frequencies, thruster type, redundancy, or mission payload hardware.

## Functional evidence

- [NASA 2026 Small Spacecraft Platforms](https://www.nasa.gov/smallsat-institute/sst-soa/platforms/), §2.1: a bus supports payload power, thermal, attitude/navigation, communications, propulsion and C&DH; the exact platform depends on mission requirements. Propulsion is configuration-dependent in small buses.
- [NASA 2026 Small Spacecraft Avionics](https://www.nasa.gov/smallsat-institute/sst-soa/small-spacecraft-avionics/), §8.1: C&DH/flight software provide command, control, communications and data-management interfaces across subsystems.
- [NASA 2026 GNC](https://www.nasa.gov/smallsat-institute/sst-soa/guidance-navigation-and-control/), §§5.1–5.2: sensors feed attitude determination/control; actuators such as reaction wheels, magnetic torquers and thrusters change attitude or motion. The figure chooses sensors → controller → reaction wheel → attitude feedback as one illustrative path.
- [NASA 2026 Power](https://www.nasa.gov/smallsat-institute/sst-soa/power-subsystems/) and [NASA SSRI electrical power](https://s3vi.ndc.nasa.gov/ssri-kb/topics/30/): solar arrays, battery storage and power management/distribution are common elements of a solar-powered small-satellite EPS.
- [NASA Webb spacecraft bus](https://science.nasa.gov/mission/webb/spacecraft-bus/): communications handle commands and science/status data; C&DH controls payload interaction and storage; propulsion performs orbital correction; thermal control maintains bus temperature. These are functional analogues, not a claim that the diagram depicts Webb.
- [NASA 2026 Thermal Control](https://www.nasa.gov/smallsat-institute/sst-soa/thermal-control/): thermal management may combine passive heat rejection and active heater control depending on the design.

## Visual reference, separate from technical configuration

- NASA NTRS, [*Spacecraft Design Summary*, Figure 2-9, “Probe Bus and Orbiter Block Diagram”](https://ntrs.nasa.gov/api/citations/19740024191/downloads/19740024191.pdf), PDF p. 51. The local original `nasa_1974_design_summary.pdf` is hashed as a separate visual reference; `nasa_1974_figure_2_9_page.png` was used only for inspection. Its hardware and mission-specific numbers are **not** transferred. The reusable visual grammar is dashed subsystem boundaries, orthogonal routed wires, named interfaces and small component symbols.

The figure uses a simplified energy path, command/telemetry path, payload-data path, attitude feedback path, heat-rejection path and optional propulsion path. Lines crossing without a junction marker are distinct interfaces. Any actual mission needs its own ICD and electrical/thermal/attitude budgets before the drawing can become a design diagram.
