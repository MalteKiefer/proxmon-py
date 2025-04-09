from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text
from util import format_uptime, format_unix_timestamp

console = Console()

def prompt_command():
    cmd = input(":").strip()
    if not cmd.startswith(":"):
        cmd = f":{cmd}"
    return cmd

def display_help():
    print("""
:q                  → quit
:r                  → refresh VM list
:restart <ID>       → restart VM/LXC
:start <ID>         → start VM/LXC
:shutdown <ID>      → shutdown VM/LXC
:stop <ID>          → stop VM/LXC
:reset <ID>         → reset VM/LXC
:hardreset <ID>     → stop + start
:delete <ID>        → permanently delete VM/LXC
:node-restart <NODE>→ reboot full Proxmox node
:tasks <NODE>       → show recent tasks (limit from config)
:settings           → open settings menu
:nodes              → show node overview
:?                  → show this help
""")

def display_vm_table(vms, use_color=False, config=None):
    y_thresh = config.get("cpu_load_yellow", 80)
    r_thresh = config.get("cpu_load_red", 90)

    table = Table(title="Proxmon VM Übersicht", box=box.SQUARE_DOUBLE_HEAD, expand=True)

    table.add_column("ID", style="bold")
    table.add_column("Type")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Uptime")
    table.add_column("CPU%")
    table.add_column("RAM (GB)")
    table.add_column("Disk (GB)")
    table.add_column("Node")

    for vm in vms:
        vmid = str(vm["vmid"])
        name = vm.get("name", "-")
        vm_type = "LXC" if vm["type"] == "lxc" else "VM"
        node = vm["node"]
        status = vm["status"]

        # Status mit Farbe
        status_text = Text(status)
        if use_color:
            status_text.stylize("green" if status == "running" else "red")

        # CPU %
        cpu = round(vm.get("cpu", 0) * 100, 1)
        cpu_text = Text(str(cpu))
        if use_color:
            if cpu >= r_thresh:
                cpu_text.stylize("bold red")
            elif cpu >= y_thresh:
                cpu_text.stylize("yellow")
            else:
                cpu_text.stylize("green")

        # RAM
        mem_used = int(vm.get("mem", 0))
        mem_total = int(vm.get("maxmem", 0)) or 1
        mem_used_gb = round(mem_used / 1024 / 1024 / 1024, 1)
        mem_total_gb = round(mem_total / 1024 / 1024 / 1024, 1)
        ram_text = f"{mem_used_gb:.1f}/{mem_total_gb:.1f}"

        # Disk
        disk = round(int(vm.get("disk", 0)) / 1024 / 1024 / 1024, 1)
        
        #Uptime
        uptime = int(vm.get("uptime"))
        uptime_text = format_uptime(uptime)

        table.add_row(
            vmid,
            vm_type,
            name,
            status_text,
            uptime_text,
            cpu_text,
            ram_text,
            f"{disk:.1f}",
            node
        )

    console.print(table)

def display_tasks(tasks):
    table = Table(title="Tasks", box=box.SQUARE_DOUBLE_HEAD, expand=True)
    table.add_column("Upid", style="bold")
    table.add_column("Status")
    table.add_column("StartTime")
    table.add_column("EndTime")
    table.add_column("Type")
    table.add_column("User")

    for task in tasks:
        table.add_row(
            str(task.get('upid', '')),
            str(task.get('status', '')),
            str(format_unix_timestamp(task.get("starttime", 0))),
            str(format_unix_timestamp(task.get("endtime", 0))),
            str(task.get('type', '')),
            str(task.get('user', ''))
        )

    console.print(table)

def display_node_table(nodes, use_color=False):
    table = Table(title="Proxmon Node Übersicht", box=box.SQUARE_DOUBLE_HEAD, expand=True)

    table.add_column("Node", style="bold")
    table.add_column("Status")
    table.add_column("Version")
    table.add_column("DNS (IP)") 
    table.add_column("Updates")

    for node in nodes:
        name = node["node"]
        status = node.get("status", "unknown")
        version = node.get("pveversion", "-")
        dns_ips = node.get("dns_ips", "-")
        updates = node.get("updates", {}).get("upgradable", 0)

        # Farbiger Status
        status_text = Text(status)
        if use_color:
            status_text.stylize("green" if status == "online" else "red")

        update_text = Text(str(updates))
        if use_color:
            if updates > 10:
                update_text.stylize("bold red")
            elif updates > 0:
                update_text.stylize("yellow")
            else:
                update_text.stylize("green")

        table.add_row(
            name,
            status_text,
            version,
            dns_ips,
            update_text
        )

    console.print(table)