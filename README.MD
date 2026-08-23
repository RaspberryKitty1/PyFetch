# ⚡ PyFetch Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Managed with uv](https://img.shields.io/badge/managed%20with-uv-000000.svg?logo=python&logoColor=white)](https://github.com/astral-sh/uv)
[![Platforms](https://img.shields.io/badge/Platforms-Windows%20%7C%20Linux-brightgreen.svg)](#platform-support)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**PyFetch** is a modern, ultra-fast system information CLI dashboard inspired by Fastfetch and Neofetch. Built using `rich` for terminal visuals, it provides live hardware telemetry, system specifications, utilization bars, and color testing across both Windows and Linux environments.

---

## 📁 Repository Structure

To maintain optimal performance and native hardware integration without cross-platform bloat, PyFetch is split into dedicated platform packages:

```text
PyFetch/
├── 📄 LICENSE
├── 📄 README.md                
├── 📁 Pyfetch-win/            <-- Windows Implementation
│   ├── 🐍 Pyfetch.py
│   ├──  pyproject.toml
│   └── 󰪷 README.MD
└── 📁 Pyfetch-Linux/          <-- Linux Implementation
    ├── 🐍 Pyfetch.py
    ├──  pyproject.toml
    └── 󰪷 README.MD

```

---

## 💻 Platform Support & Sub-Projects

Choose your operating system below to navigate to the specific installation guide and documentation:

### 🪟 [PyFetch Windows](https://www.google.com/search?q=./Pyfetch-win/)

* **Backend:** Native Windows Management Instrumentation (WMI) + Open Hardware Monitor engine.
* **Features:**
* Dynamic shell detection (PowerShell 7, Windows PowerShell, CMD, Bash).
* Storage device type detection (**NVMe**, **SSD**, **HDD**).
* CPU temp, power draw, and fan speed tracking via OpenHardwareMonitor.
* NVIDIA GPU telemetry via NVML.

### 🐧 [PyFetch Linux](https://www.google.com/search?q=./Pyfetch-Linux/)

* **Backend:** Direct `/sys` and `/proc` filesystem interfaces + `psutil` sensors.
* **Features:**
* Window Manager & Desktop Environment detection via `$XDG`.
* CPU temperature and fan speeds via `lm-sensors`.
* Storage mount point telemetry (`/`, `/home`, etc.) and drive classification.
* **Dual GPU Support:** NVIDIA (via NVML) and AMD (via `pyamdgpuinfo`).

---

## 🚀 Quick Start (`uv`)

You can quickly run the respective version using [`uv`](https://github.com/astral-sh/uv) directly from the root directory:

### Running on Windows

```bash
cd Pyfetch-win
uv sync
# With NVIDIA GPU support
uv sync --extra nvidia

uv run pyfetch.py
```

### Running on Linux

```bash
cd Pyfetch-Linux
uv sync
# With NVIDIA GPU support
uv run --extra nvidia pyfetch.py
# With AMD GPU support
uv run --extra amd pyfetch.py
uv run pyfetch.py
```

## 📜 License

Licensed under the [MIT License](LICENSE)
