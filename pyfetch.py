from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from datetime import datetime
import wmi
import psutil
import os
import sys
import socket
import locale

console = Console()

# --- NVML Setup ---
try:
    # try nvidia_smi / pynvml alias under nvidia-ml-py
    import pynvml
    pynvml.nvmlInit()
    HAS_NVML = True
except Exception:
    HAS_NVML = False


def get_openhardwaremonitor_metrics():
    """Reads CPU Temp, CPU Wattage, and Fan Speeds directly from Open Hardware Monitor's WMI engine."""
    metrics = {"temp": None, "power": None, "fan": None}

    try:
        # OpenHardwareMonitor exposes sensors under 'root\OpenHardwareMonitor'
        ohm = wmi.WMI(namespace=r"root\OpenHardwareMonitor")
        sensors = ohm.Sensor()

        for sensor in sensors:
            # Check for CPU Temperature
            if sensor.SensorType == "Temperature" and "CPU" in sensor.Name:
                # Core Average, Package, or first Core temp fallback
                if "Package" in sensor.Name or "Core #1" in sensor.Name or "CPU Core" in sensor.Name:
                    metrics["temp"] = round(sensor.Value, 1)

            # Check for CPU Power / Wattage
            elif sensor.SensorType == "Power" and "CPU" in sensor.Name:
                if "Package" in sensor.Name or "Total" in sensor.Name or "CPU Cores" in sensor.Name:
                    metrics["power"] = round(sensor.Value, 1)

            # Check for Fan Speeds
            elif sensor.SensorType == "Fan":
                if sensor.Value and sensor.Value > 0:
                    metrics["fan"] = int(sensor.Value)

    except Exception:
        # Fails silently if OpenHardwareMonitor isn't running or WMI namespace isn't accessible
        pass

    return metrics


def make_mini_bar(pct, width=12):
    """Creates a sleek inline progress bar string with dynamic threshold colors."""
    pct = max(0.0, min(100.0, float(pct)))
    filled = int(width * (pct / 100))
    bar = "█" * filled + "░" * (width - filled)

    if pct > 85:
        color = "bright_red"
    elif pct > 65:
        color = "bright_yellow"
    else:
        color = "bright_green"

    return f"[{color}]{bar}[/{color}] {pct:.1f}%"


def get_color_palette():
    """Generates Fastfetch-style color blocks."""
    colors = [
        "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
        "bright_black", "bright_red", "bright_green", "bright_yellow",
        "bright_blue", "bright_magenta", "bright_cyan", "bright_white"
    ]

    top_row = "".join([f"[{c}]███[/{c}]" for c in colors[:8]])
    bottom_row = "".join([f"[{c}]███[/{c}]" for c in colors[8:]])
    return f"{top_row}\n{bottom_row}"


def get_uptime():
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m"


def get_network_info():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"

    iface_name = "Ethernet"
    for name, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.address == ip:
                iface_name = name
                break

    return f"{iface_name} ({ip})"


def get_display_info(c):
    try:
        monitors = c.Win32_VideoController()
        if monitors:
            m = monitors[0]
            res_x = getattr(m, "CurrentHorizontalResolution", None)
            res_y = getattr(m, "CurrentVerticalResolution", None)
            hz = getattr(m, "CurrentRefreshRate", None)
            if res_x and res_y:
                hz_str = f" @ {hz}Hz" if hz else ""
                return f"{res_x}x{res_y}{hz_str}"
    except Exception:
        pass
    return "1920x1080 @ 60Hz"


def get_locale_safe():
    try:
        loc = locale.getlocale()[0]
        if loc:
            return loc
    except Exception:
        pass
    return os.environ.get("LANG", "en_US")


def get_disk_types(c):
    """Maps logical drive letters (e.g., C:) to media types (NVMe, SSD, HDD)."""
    drive_type_map = {}
    try:
        c_storage = wmi.WMI(namespace="root\\Microsoft\\Windows\\Storage")
        physical_disks = c_storage.MSFT_PhysicalDisk()

        disk_media_map = {}
        for pd in physical_disks:
            media_type_code = getattr(pd, "MediaType", 0)
            bus_type_code = getattr(pd, "BusType", 0)

            if bus_type_code == 17 or "NVME" in getattr(pd, "Model", "").upper():
                dtype = "NVMe"
            elif media_type_code == 4:
                dtype = "SSD"
            elif media_type_code == 3:
                dtype = "HDD"
            else:
                dtype = "Storage"

            disk_media_map[pd.DeviceId] = dtype

        for partition in c.Win32_LogicalDiskToPartition():
            drive_letter = partition.Dependent.DeviceId
            disk_index = partition.Antecedent.DeviceId.split(
                ",")[0].replace("Disk #", "").strip()

            if disk_index in disk_media_map:
                drive_type_map[drive_letter +
                               "\\"] = disk_media_map[disk_index]
    except Exception:
        pass

    return drive_type_map


def get_sys_info():
    c = wmi.WMI()

    os_info = c.Win32_OperatingSystem()[0]
    os_name = f"{os_info.Caption} ({os_info.OSArchitecture})"
    kernel = f"WIN32_NT {os_info.Version}"

    uptime = get_uptime()

    # Dynamic Shell Detection
    try:
        curr_proc = psutil.Process(os.getpid())
        parent_proc = curr_proc.parent()

        while parent_proc and parent_proc.name().lower() in ("python.exe", "pythonw.exe", "uv.exe"):
            parent_proc = parent_proc.parent()

        if parent_proc:
            shell_name = parent_proc.name().lower()
            if "pwsh" in shell_name:
                shell = "PowerShell 7 (pwsh)"
            elif "powershell" in shell_name:
                shell = "Windows PowerShell"
            elif "cmd" in shell_name:
                shell = "cmd.exe"
            elif "bash" in shell_name or "zsh" in shell_name:
                shell = parent_proc.name()
            else:
                shell = parent_proc.name()
        else:
            shell = os.environ.get("ComSpec", "cmd.exe").split("\\")[-1]
    except Exception:
        shell = os.environ.get("ComSpec", "cmd.exe").split("\\")[-1]

    terminal = os.environ.get("WT_SESSION") and "Windows Terminal" or "Console"
    sys_locale = get_locale_safe()

    cpu_name = c.Win32_Processor()[0].Name.strip()
    cpu_usage = psutil.cpu_percent(interval=None)

    # Query OpenHardwareMonitor WMI namespace
    cpu_hw = get_openhardwaremonitor_metrics()

    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    gpu_info = []
    if HAS_NVML:
        device_count = pynvml.nvmlDeviceGetCount()
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode("utf-8")

            temp = pynvml.nvmlDeviceGetTemperature(
                handle, pynvml.NVML_TEMPERATURE_GPU)
            power = pynvml.nvmlDeviceGetPowerUsage(handle) // 1000
            clock = pynvml.nvmlDeviceGetClockInfo(
                handle, pynvml.NVML_CLOCK_GRAPHICS)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu

            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_mem_used = mem_info.used / (1024**3)
            gpu_mem_total = mem_info.total / (1024**3)
            gpu_mem_pct = (mem_info.used / mem_info.total) * 100

            gpu_info.append({
                "name": name,
                "temp": temp,
                "power": power,
                "clock": clock,
                "util": util,
                "mem_used": gpu_mem_used,
                "mem_total": gpu_mem_total,
                "mem_pct": gpu_mem_pct,
            })

    disk_types = get_disk_types(c)

    disks = []
    for part in psutil.disk_partitions(all=False):
        if "fixed" in part.opts or part.fstype:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                media_type = disk_types.get(part.mountpoint, "Disk")
                disks.append({
                    "drive": part.mountpoint.replace("\\", ""),
                    "used": usage.used / (1024**3),
                    "total": usage.total / (1024**3),
                    "pct": usage.percent,
                    "fstype": part.fstype,
                    "type": media_type,
                })
            except PermissionError:
                continue

    return {
        "os": os_name,
        "kernel": kernel,
        "uptime": uptime,
        "shell": shell,
        "terminal": terminal,
        "cpu": cpu_name,
        "cpu_usage": cpu_usage,
        "cpu_temp": cpu_hw["temp"],
        "cpu_power": cpu_hw["power"],
        "cpu_fan": cpu_hw["fan"],
        "mem_used": mem.used / (1024**3),
        "mem_total": mem.total / (1024**3),
        "mem_pct": mem.percent,
        "swap_used": swap.used / (1024**3),
        "swap_total": swap.total / (1024**3),
        "swap_pct": swap.percent,
        "display": get_display_info(c),
        "wm": "Desktop Window Manager",
        "network": get_network_info(),
        "locale": sys_locale,
        "gpus": gpu_info,
        "disks": disks,
    }


def render_fetch():
    data = get_sys_info()

    # System & Host Table
    sys_table = Table(show_header=False, box=None, padding=(0, 2))
    sys_table.add_column("Key", style="bold cyan", justify="right")
    sys_table.add_column("Value")

    sys_table.add_row("🪟 OS", data["os"])
    sys_table.add_row("⚙️ Kernel", data["kernel"])
    sys_table.add_row("⏱️ Uptime", data["uptime"])
    sys_table.add_row("🐚 Shell", data["shell"])
    sys_table.add_row("💻 Terminal", data["terminal"])
    sys_table.add_row("🖥️ Display", data["display"])
    sys_table.add_row("🪟 WM", data["wm"])
    sys_table.add_row("🌐 Network", data["network"])
    sys_table.add_row("🌍 Locale", data["locale"])

    # Hardware & Storage Table
    hw_table = Table(show_header=False, box=None, padding=(0, 2))
    hw_table.add_column("Key", style="bold yellow", justify="right")
    hw_table.add_column("Value")

    # CPU Formatting
    cpu_details = f"{data['cpu']}\n"
    cpu_details += f"Load: {make_mini_bar(data['cpu_usage'])}"

    extra_stats = []
    if data["cpu_temp"]:
        extra_stats.append(f"🔥 [bold red]{data['cpu_temp']}°C[/bold red]")
    if data["cpu_power"]:
        extra_stats.append(f"⚡ [bold green]{data['cpu_power']}W[/bold green]")
    if data["cpu_fan"]:
        extra_stats.append(f"🌀 [bold cyan]{data['cpu_fan']} RPM[/bold cyan]")

    if extra_stats:
        cpu_details += f"  {'  '.join(extra_stats)}"

    hw_table.add_row("🧠 CPU", cpu_details)

    # GPU Rows
    for idx, gpu in enumerate(data["gpus"]):
        gpu_title = f"🎮 GPU {idx + 1}"
        gpu_details = (
            f"[bold white]{gpu['name']}[/bold white] @ {gpu['clock']}MHz [{gpu['util']}%]\n"
            f"🔥 [bold red]{gpu['temp']}°C[/bold red]  ⚡ [bold green]{gpu['power']}W[/bold green]  "
            f"VRAM: {make_mini_bar(gpu['mem_pct'])} ({gpu['mem_used']:.1f}/{gpu['mem_total']:.1f} GiB)"
        )
        hw_table.add_row(gpu_title, gpu_details)

    # Memory & Swap
    hw_table.add_row(
        "⚡ Memory",
        f"{make_mini_bar(data['mem_pct'])} ({data['mem_used']:.1f}/{data['mem_total']:.1f} GiB)",
    )
    hw_table.add_row(
        "🔄 Swap",
        f"{make_mini_bar(data['swap_pct'])} ({data['swap_used']:.1f}/{data['swap_total']:.1f} GiB)",
    )

    # Disks with Media Type
    for d in data["disks"]:
        disk_label = f"💾 Disk ({d['drive']})"
        disk_stat = f"{make_mini_bar(d['pct'], width=10)} ({d['used']:.0f}/{d['total']:.0f} GiB) [{d['type']} / {d['fstype']}]"
        hw_table.add_row(disk_label, disk_stat)

    # Palette Row Inside System Panel
    palette_table = Table(show_header=False, box=None, padding=(0, 2))
    palette_table.add_column("Key", style="bold magenta", justify="right")
    palette_table.add_column("Value")
    palette_table.add_row("🎨 Colors", get_color_palette())

    # Vertical Master Layout
    vertical_grid = Table.grid(expand=True)
    vertical_grid.add_column()

    vertical_grid.add_row(
        Panel(
            sys_table, title="[bold magenta]System & Host[/bold magenta]", border_style="magenta")
    )
    vertical_grid.add_row(
        Panel(
            hw_table, title="[bold green]Hardware & Storage[/bold green]", border_style="green")
    )
    vertical_grid.add_row(
        Panel(palette_table, border_style="bright_magenta")
    )

    console.print(
        Panel(
            vertical_grid,
            title="[bold white]⚡ PYFETCH DASHBOARD ⚡[/bold white]",
            border_style="bright_blue",
            expand=False,
        )
    )


if __name__ == "__main__":
    try:
        render_fetch()
    finally:
        if HAS_NVML:
            pynvml.nvmlShutdown()
