import os
import json
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
import time
from proxmoxer import ProxmoxAPI
from util import CONFIG_PATH, clear_screen

class ConfigManager:
    def load(self):
        if not os.path.exists(CONFIG_PATH):
            return {
                "servers": [],
                "update_interval": 10,
                "cpu_load_yellow": 80,
                "cpu_load_red": 90,
                "use_color": False,
                "language": "en",
                "task_limit": 15
            }
        with open(CONFIG_PATH) as f:
            return json.load(f)

    def save(self, config):
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
class ProxmoxManager:
    def __init__(self, config):
        self.server = config["servers"][0]
        self.proxmox = ProxmoxAPI(
            self.server["host"].replace("https://", "").split(":")[0],
            user=self.server["username"],
            password=self.server["password"],
            verify_ssl=False
        )

    def fetch_vms(self):
        return self.proxmox.cluster.resources.get(type="vm")

    def find_vm(self, vmid, vms):
        return next((v for v in vms if str(v["vmid"]) == str(vmid)), None)

    def get_node_and_type(self, vm):
        return vm["node"], vm["type"]

    def _action(self, vmid, vms, action):
        vm = self.find_vm(vmid, vms)
        if not vm:
            print(f"VM/CT with ID {vmid} not found.")
            return
        node, vm_type = self.get_node_and_type(vm)
        obj = self.proxmox.nodes(node)
        target = obj.qemu if vm_type == "qemu" else obj.lxc
        try:
            getattr(target(vmid).status(), action).post()
            print(f"{action.capitalize()} {vm_type.upper()} {vmid} on {node}")
        except Exception as e:
            print(f"{action.capitalize()} failed: {e}")

    def restart_vm(self, vmid, vms):
        from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

        vm = self.find_vm(vmid, vms)
        if not vm:
            print(f"VM/CT with ID {vmid} not found.")
            return

        node, vm_type = self.get_node_and_type(vm)
        obj = self.proxmox.nodes(node)
        target = obj.qemu if vm_type == "qemu" else obj.lxc

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                transient=True
            ) as progress:
                progress.add_task(description=f"Stopping LXC {vmid}", total=None)
                target(vmid).status().stop.post()
                # Warte auf Stop
                for _ in range(30):
                    status = target(vmid).status.current.get()["status"]
                    if status == "stopped":
                        break
                    time.sleep(1)
                else:
                    print("Timeout waiting for container to stop.")
                    return

                progress.add_task(description=f"Starting LXC {vmid}", total=None)
                target(vmid).status().start.post()

            print(f"Restarted {vm_type.upper()} {vmid} on {node}")

        except Exception as e:
            print(f"Restart failed: {e}")

    def start_vm(self, vmid, vms): self._action(vmid, vms, "start")
    def shutdown_vm(self, vmid, vms): self._action(vmid, vms, "shutdown")
    def stop_vm(self, vmid, vms):
        from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

        vm = self.find_vm(vmid, vms)
        if not vm:
            print(f"VM/CT with ID {vmid} not found.")
            return

        node, vm_type = self.get_node_and_type(vm)
        obj = self.proxmox.nodes(node)
        target = obj.qemu if vm_type == "qemu" else obj.lxc

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                transient=True
            ) as progress:
                progress.add_task(description=f"Stopping LXC {vmid}", total=None)
                target(vmid).status().stop.post()
                # Warte auf Stop
                for _ in range(30):
                    status = target(vmid).status.current.get()["status"]
                    if status == "stopped":
                        break
                    time.sleep(5)
                else:
                    print("Timeout waiting for container to stop.")
                    return

        except Exception as e:
            print(f"Restart failed: {e}")
    def reset_vm(self, vmid, vms): self._action(vmid, vms, "reset")

    def delete_vm(self, vmid, vms):
        vm = self.find_vm(vmid, vms)
        if not vm:
            print(f"VM/CT with ID {vmid} not found.")
            return
        node, vm_type = self.get_node_and_type(vm)
        obj = self.proxmox.nodes(node)
        target = obj.qemu if vm_type == "qemu" else obj.lxc
        try:
            target(vmid).delete()
            print(f"Deleted {vm_type.upper()} {vmid} on {node}")
        except Exception as e:
            print(f"Delete failed: {e}")

    def restart_node(self, node):
        try:
            self.proxmox.nodes(node).status().reboot.post()
            print(f"Node {node} reboot triggered.")
        except Exception as e:
            print(f"Node reboot failed: {e}")

    def list_tasks(self, node, limit=15):
        try:
            return self.proxmox.nodes(node).tasks.get(limit=limit)
        except Exception as e:
            print(f"Failed to load tasks for node '{node}': {e}")
            return []

    def fetch_nodes(self):
        nodes = self.proxmox.nodes.get()
        result = []

        for node in nodes:
            name = node["node"]
            status = node.get("status", "unknown")
            try:
                version = self.proxmox.nodes(name).version.get()
                updates = self.proxmox.nodes(name).apt.update.get()
                dns_config = self.proxmox.nodes(name).dns.get()
            except Exception as e:
                print(f"Error fetching node data for {name}: {e}")
                version = {}
                updates = []
                dns_config = {}

            dns_ips = ", ".join(filter(None, [dns_config.get("dns1"), dns_config.get("dns2"), dns_config.get("dns3")]))

            result.append({
                "node": name,
                "status": status,
                "pveversion": version.get("version", "-"),
                "hostname": version.get("hostname", "-"),
                "dns_ips": dns_ips,
                "updates": {
                    "upgradable": len(updates)
                }
            })

        return result