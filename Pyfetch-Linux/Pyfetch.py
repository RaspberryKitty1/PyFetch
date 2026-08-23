from datetime import datetime
import locale
import os
import platform
import socket
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import psutil

console = Console()

# --- Optional GPU Drivers ---
try:
    import pynvml
    pynvml.nvmlInit()
    HAS_NVML = True
except Exception:
    HAS_NVML = False

try:
    import pyamdgpuinfo
    HAS_AMDGPU = True
except Exception:
    HAS_AMDGPU = False


def get_hardware_metrics():
    """Reads Linux core temperatures and fans via psutil sensors."""
    metrics = {"temp": None, "fan": None}

    # Temperature
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for key in ["coretemp", "cpu_thermal", "k10temp", "zenpower"]:
                if key in temps and temps[key]:
                    metrics["temp"] = round(temps[key][0].current, 1)
                    break
            if metrics["temp"] is None:
                first_key = next(iter(temps))
                if temps[first_key]:
                    metrics["temp"] = round(temps[first_key][0].current, 1)
    except Exception:
        pass

    # Fans
    try:
        fans = psutil.sensors_fans()
        if fans:
            for entries in fans.values():
                for entry in entries:
                    if entry.current > 0:
                        metrics["fan"] = int(entry.current)
                        break
    except Exception:
        pass

    return metrics


def get_gpu_info():
    """Queries NVIDIA and AMD GPUs natively on Linux."""
    gpus = []

    # NVIDIA GPUs
    if HAS_NVML:
        try:
            for i in range(pynvml.nvmlDeviceGetCount()):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode("utf-8")

                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                power = pynvml.nvmlDeviceGetPowerUsage(handle) // 1000
                clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

                try:
                    fan_rpm = pynvml.nvmlDeviceGetFanSpeedRPM(handle)
                except Exception:
                    fan_rpm = None

                gpus.append({
                    "name": name,
                    "temp": temp,
                    "power": power,
                    "clock": clock,
                    "util": util,
                    "fan_rpm": fan_rpm,
                    "mem_used": mem_info.used / (1024**3),
                    "mem_total": mem_info.total / (1024**3),
                    "mem_pct": (mem_info.used / mem_info.total) * 100,
                })
        except Exception:
            pass

    # AMD GPUs
    if HAS_AMDGPU:
        try:
            for i in range(pyamdgpuinfo.detect_gpus()):
                gpu = pyamdgpuinfo.get_gpu(i)
                mem_used = gpu.query_vram_usage() / (1024**3)
                mem_total = gpu.memory_info["vram_size"] / (1024**3)

                gpus.append({
                    "name": gpu.name,
                    "temp": gpu.query_temperature(),
                    "power": round(gpu.query_power(), 1),
                    "clock": gpu.query_sclk(),
                    "util": int(gpu.query_load() * 100),
                    "fan_rpm": gpu.query_fan_speed(),
                    "mem_used": mem_used,
                    "mem_total": mem_total,
                    "mem_pct": (mem_used / mem_total * 100) if mem_total else 0,
                })
        except Exception:
            pass

    return gpus


def make_mini_bar(pct, width=12):
    pct = max(0.0, min(100.0, float(pct)))
    filled = int(width * (pct / 100))
    bar = "█" * filled + "░" * (width - filled)
    color = "bright_red" if pct > 85 else ("bright_yellow" if pct > 65 else "bright_green")
    return f"[{color}]{bar}[/{color}] {pct:.1f}%"


def get_color_palette():
    colors = [
        "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
        "bright_black", "bright_red", "bright_green", "bright_yellow",
        "bright_blue", "bright_magenta", "bright_cyan", "bright_white"
    ]
    return "".join([f"[{c}]███[/{c}]" for c in colors[:8]]) + "\n" + "".join([f"[{c}]███[/{c}]" for c in colors[8:]])


def get_uptime():
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{uptime.days}d {hours}h {minutes}m"


def get_network_info():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"

    iface_name = "eth0"
    for name, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.address == ip:
                iface_name = name
                break
    return f"{iface_name} ({ip})"


def get_cpu_model():
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":")[1].strip()
    except Exception:
        pass
    return platform.processor() or "Linux Processor"


def get_sys_info():
    # Shell & WM
    try:
        curr_proc = psutil.Process(os.getpid())
        parent = curr_proc.parent()
        while parent and parent.name() in ("python", "python3", "uv"):
            parent = parent.parent()
        shell = parent.name() if parent else os.environ.get("SHELL", "bash")
    except Exception:
        shell = os.environ.get("SHELL", "bash")

    wm = (
        os.environ.get("XDG_CURRENT_DESKTOP")
        or os.environ.get("DESKTOP_SESSION")
        or os.environ.get("WINDOWMANAGER")
        or "Wayland/X11"
    )

    hw = get_hardware_metrics()
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Disks
    disks = []
    for part in psutil.disk_partitions(all=False):
        if part.fstype and not part.mountpoint.startswith("/dev"):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                dtype = "NVMe" if "nvme" in part.device else ("SSD/HDD" if "sd" in part.device else "Disk")
                disks.append({
                    "drive": part.mountpoint,
                    "used": usage.used / (1024**3),
                    "total": usage.total / (1024**3),
                    "pct": usage.percent,
                    "fstype": part.fstype,
                    "type": dtype,
                })
            except (PermissionError, OSError):
                continue

    return {
        "os": f"{platform.system()} {platform.release()}",
        "kernel": platform.version().split()[0],
        "uptime": get_uptime(),
        "shell": shell,
        "terminal": os.environ.get("TERM", "terminal"),
        "wm": wm,
        "network": get_network_info(),
        "locale": locale.getlocale()[0] or os.environ.get("LANG", "en_US"),
        "cpu": get_cpu_model(),
        "cpu_usage": psutil.cpu_percent(interval=None),
        "cpu_temp": hw["temp"],
        "cpu_fan": hw["fan"],
        "mem_used": mem.used / (1024**3),
        "mem_total": mem.total / (1024**3),
        "mem_pct": mem.percent,
        "swap_used": swap.used / (1024**3),
        "swap_total": swap.total / (1024**3),
        "swap_pct": swap.percent,
        "gpus": get_gpu_info(),
        "disks": disks,
    }


def render_fetch():
    data = get_sys_info()

    # System & Host Table
    sys_table = Table(show_header=False, box=None, padding=(0, 2))
    sys_table.add_column("Key", style="bold cyan", justify="right")
    sys_table.add_column("Value")

    sys_table.add_row("🐧 OS", data["os"])
    sys_table.add_row("⚙️ Kernel", data["kernel"])
    sys_table.add_row("⏱️ Uptime", data["uptime"])
    sys_table.add_row("🐚 Shell", data["shell"])
    sys_table.add_row("💻 Terminal", data["terminal"])
    sys_table.add_row("🖼️ WM", data["wm"])
    sys_table.add_row("🌐 Network", data["network"])
    sys_table.add_row("🌍 Locale", data["locale"])

    # Hardware & Storage Table
    hw_table = Table(show_header=False, box=None, padding=(0, 2))
    hw_table.add_column("Key", style="bold yellow", justify="right")
    hw_table.add_column("Value")

    cpu_details = f"{data['cpu']}\nLoad: {make_mini_bar(data['cpu_usage'])}"
    extra_stats = []
    if data["cpu_temp"]:
        extra_stats.append(f"🔥 [bold red]{data['cpu_temp']}°C[/bold red]")
    if data["cpu_fan"]:
        extra_stats.append(f"🌀 [bold cyan]{data['cpu_fan']} RPM[/bold cyan]")
    if extra_stats:
        cpu_details += f"  {'  '.join(extra_stats)}"

    hw_table.add_row("🧠 CPU", cpu_details)

    for idx, gpu in enumerate(data["gpus"]):
        gpu_title = f"🎮 GPU {idx + 1}"
        fan_text = f"🌀 [bold cyan]{gpu['fan_rpm']} RPM[/bold cyan]  " if gpu.get("fan_rpm") is not None else ""
        gpu_details = (
            f"[bold white]{gpu['name']}[/bold white] @ {gpu['clock']}MHz [{gpu['util']}%]\n"
            f"🔥 [bold red]{gpu['temp']}°C[/bold red]  ⚡ [bold green]{gpu['power']}W[/bold green]  {fan_text}"
            f"VRAM: {make_mini_bar(gpu['mem_pct'])} ({gpu['mem_used']:.1f}/{gpu['mem_total']:.1f} GiB)"
        )
        hw_table.add_row(gpu_title, gpu_details)

    hw_table.add_row("⚡ Memory", f"{make_mini_bar(data['mem_pct'])} ({data['mem_used']:.1f}/{data['mem_total']:.1f} GiB)")
    hw_table.add_row("🔄 Swap", f"{make_mini_bar(data['swap_pct'])} ({data['swap_used']:.1f}/{data['swap_total']:.1f} GiB)")

    for d in data["disks"]:
        hw_table.add_row(f"💾 Disk ({d['drive']})", f"{make_mini_bar(d['pct'], width=10)} ({d['used']:.0f}/{d['total']:.0f} GiB) [{d['type']} / {d['fstype']}]")

    palette_table = Table(show_header=False, box=None, padding=(0, 2))
    palette_table.add_column("Key", style="bold magenta", justify="right")
    palette_table.add_column("Value")
    palette_table.add_row("🎨 Colors", get_color_palette())

    vertical_grid = Table.grid(expand=True)
    vertical_grid.add_column()
    vertical_grid.add_row(Panel(sys_table, title="[bold magenta]System & Host[/bold magenta]", border_style="magenta"))
    vertical_grid.add_row(Panel(hw_table, title="[bold green]Hardware & Storage[/bold green]", border_style="green"))
    vertical_grid.add_row(Panel(palette_table, border_style="bright_magenta"))

    console.print(Panel(vertical_grid, title="[bold white]⚡ PYFETCH LINUX ⚡[/bold white]", border_style="bright_blue", expand=False))


if __name__ == "__main__":
    try:
        render_fetch()
    finally:
        if HAS_NVML:
            pynvml.nvmlShutdown()