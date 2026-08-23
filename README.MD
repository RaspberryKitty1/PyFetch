
# PyFetch Dashboard

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Managed with uv](https://img.shields.io/badge/managed%20with-uv-000000.svg?logo=python&logoColor=white)](https://github.com/astral-sh/uv)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg?logo=windows)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A modern, fast, Python-based system information tool inspired by Fastfetch and Neofetch. Built with `rich` and optimized for Windows environments, **PyFetch** delivers a clean, terminal-native dashboard packed with host specs, dynamic utilization metrics, and hardware telemetry.

---

## Features

* **System & Host Details:** Operating system architecture, kernel version, uptime, dynamic shell detection (PowerShell 7, Windows PowerShell, CMD, Bash), active terminal emulator, display resolution, and local IP/interface.
* **CPU Telemetry:** Live load percentage with color-coded progress bars, temperature, wattage, and fan speeds.
* **GPU Monitoring (Optional):** NVIDIA GPU status via NVML including core clock, utilization, VRAM usage, temperature, and power draw.
* **Smart Storage Detection:** Maps logical drive letters ($C:$, $D:$, etc.) to physical media types (**NVMe**, **SSD**, **HDD**) along with filesystem and partition capacity.
* **Dynamic Visuals:** Fastfetch-style color palette tester and threshold-based progress bars that shift from green to yellow to red under heavy load.

---

## Prerequisites

* **Windows OS:** Relies on Windows Management Instrumentation (WMI) and native Windows APIs.
* **[`uv`](https://github.com/astral-sh/uv):** Fast Python package and project manager.
* **[Open Hardware Monitor](https://openhardwaremonitor.org/)** *(Optional)*: Keep running in the background to supply CPU temperature, wattage, and fan speed metrics.
* **NVIDIA GPU** *(Optional)*: Utilizes `nvidia-ml-py` via the optional `Nvidia` extra if an NVIDIA GPU is present.

---

## Getting Started

### Installation

Clone the repository and install dependencies using `uv`:

```bash
# Clone the repository
git clone [https://github.com/your-username/pyfetch.git](https://github.com/your-username/pyfetch.git)
cd pyfetch

```

#### Standard Installation (Base Metrics)

Installs core system and hardware monitoring dependencies:

```bash
uv sync

```

#### Installation with NVIDIA GPU Metrics

Includes optional `nvidia-ml-py` support for GPU telemetry:

```bash
uv sync --extra Nvidia

```

---

### Usage

Run the dashboard inside your project environment:

```bash
uv run pyfetch.py

```

> **Standalone Execution:** If you have the script without cloning the full repository, you can run it directly with `uv`:
>
> ```bash
> # Standard
> uv run --with rich --with psutil --with wmi pyfetch.py
> 
> # With NVIDIA GPU support
> uv run --with rich --with psutil --with wmi --with nvidia-ml-py pyfetch.py
> 
> ```
>
>

---

## Configuration & Troubleshooting

* **Missing CPU Temps / Power / Fan Speeds:** Windows WMI does not natively expose raw motherboard sensor data. Open Hardware Monitor must be running in the background so PyFetch can query its `root\OpenHardwareMonitor` WMI namespace.
* **Storage Type Fallback:** Querying physical disk bus types (NVMe vs. SSD) requires access to `root\Microsoft\Windows\Storage`. If run in a restricted terminal, storage types may fall back to generic `"Disk"` or `"Storage"`. Launch your terminal as Administrator for accurate drive type reporting.

---

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request if you want to add support for additional hardware sensors, AMD/Intel GPU monitoring, or UI enhancements.

## 📜 License

Licensed under the [MIT License](LICENSE)
