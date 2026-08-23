# PyFetch Dashboard (Linux)

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Managed with uv](https://img.shields.io/badge/managed%20with-uv-000000.svg?logo=python&logoColor=white)](https://github.com/astral-sh/uv)
[![Platform](https://img.shields.io/badge/Platform-Linux-FCC624.svg?logo=linux&logoColor=black)](https://www.kernel.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A modern, fast, Python-based system information tool inspired by Fastfetch and Neofetch. Built with `rich` and native Linux APIs, **PyFetch** delivers a clean, terminal-native dashboard packed with host specs, dynamic utilization metrics, and hardware telemetry.

---

## Features

* **System & Host Details:** Linux distribution release, kernel version, system uptime, shell detection (`bash`, `zsh`, `fish`), active terminal emulator, desktop environment / window manager (`XDG`), and local network IP/interface.
* **CPU Telemetry:** Live load percentage with color-coded progress bars, core temperatures (`sysfs`), and system fan speeds (`lm-sensors`).
* **Multi-GPU Monitoring (Optional):**
  * **NVIDIA:** Queries NVML for clock speeds, GPU utilization, VRAM usage, temperature, power draw, and fan RPM.
  * **AMD:** Queries `pyamdgpuinfo` for core clocks, VRAM usage, temperature, power, and fan RPM.
* **Storage Telemetry:** Tracks mount points (`/`, `/home`, etc.), filesystem types, partition capacity, and storage types (**NVMe** vs. **SSD/HDD**).
* **Dynamic Visuals:** Fastfetch-style color palette tester and threshold-based progress bars that shift from green to yellow to red under load.

---

## Prerequisites

* **Linux OS:** Native support via `/proc`, `/sys`, and system APIs.
* **[`uv`](https://github.com/astral-sh/uv):** Fast Python package and project manager.
* **`lm-sensors`** *(Optional)*: Recommended for detailed motherboard and CPU temperature metrics.
* **GPU Drivers & Tools** *(Optional)*:
  * NVIDIA GPU: Drivers with NVML support.
  * AMD GPU: `pyamdgpuinfo` support.

---

## Getting Started

### Installation

Clone the repository and navigate to the project directory:

```bash
git clone [https://github.com/your-username/pyfetch.git](https://github.com/your-username/pyfetch.git)
cd pyfetch

```

#### Standard Installation (Base Metrics)

Installs core system and hardware monitoring dependencies:

```bash
uv sync

```

#### Optional GPU Installations

Install support for NVIDIA GPUs, AMD GPUs, or both:

```bash
# NVIDIA support
uv sync --extra nvidia

# AMD support
uv sync --extra amd

```

---

### Usage

Run the dashboard inside your project environment:

```bash
uv run pyfetch_linux.py

```

> **Standalone Execution:** Run directly with `uv` without cloning the repository:
>
> ```bash
> # Standard
> uv run --with rich --with psutil pyfetch_linux.py
> 
> # With GPU support
> uv run --with rich --with psutil --with nvidia-ml-py --with pyamdgpuinfo pyfetch_linux.py
> 
> ```
>
>

---

## Configuration & Troubleshooting

* **Missing CPU Temps or Fans:** Ensure `lm-sensors` is installed on your Linux distribution (`sudo apt install lm-sensors` or `sudo pacman -S lm-sensors`) and run `sudo sensors-detect` to configure system hardware monitoring modules.
* **Disk Permissions:** Some mount points or drive types require appropriate read permissions for `/dev` nodes to accurately report device types.

---

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request to enhance hardware telemetry, display configurations, or terminal graphics.

## 📜 License

Licensed under the [MIT License](../LICENSE)
