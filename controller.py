from model import ConfigManager, ProxmoxManager
from settings_controller import settings_menu
from view import display_help, display_vm_table, prompt_command, display_tasks, display_node_table
from util import ensure_config_dir, clear_screen
from settings_controller import settings_menu
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

class ProxmonController:
    def __init__(self):
        ensure_config_dir()
        self.config = ConfigManager().load()
        if not self.config["servers"]:
            print("No servers configured. Use :settings to add one.")
            exit()

        self.selected_server = self._choose_server(self.config["servers"])
        self.pm = ProxmoxManager({"servers": [self.selected_server]})
        self.current_vms = []

    def run(self):
        self._clear_and_refresh()
        print("Type :? for help.")

        while True:
            cmd = prompt_command()
            if cmd in (":q", "q"):
                break
            elif cmd in (":r", "r"):
                self._clear_and_refresh()
            elif cmd.startswith(":") and len(cmd.split()) > 1:
                action, arg = cmd.split(maxsplit=1)
                self._handle_vm_command(action, arg)
            elif cmd == ":tasks":
                print("Usage: :tasks <nodename>")
            elif cmd.startswith(":tasks "):
                self._show_tasks(cmd.split()[1])
            elif cmd == ":settings":
                clear_screen()
                settings_menu(self.config)
            elif cmd == ":?":
                clear_screen()
                display_help()
            elif cmd == ":nodes":
                clear_screen()
                self._show_nodes()
            else:
                print("Unknown command. Use :? for help.")

    def _handle_vm_command(self, action, arg):
        commands = {
            ":restart": self.pm.restart_vm,
            ":start": self.pm.start_vm,
            ":shutdown": self.pm.shutdown_vm,
            ":stop": self.pm.stop_vm,
            ":reset": self.pm.reset_vm,
            ":delete": self.pm.delete_vm,
        }

        if action in commands:
            commands[action](arg, self.current_vms)
            self._clear_and_refresh()
        elif action == ":hardreset":
            self.pm.stop_vm(arg, self.current_vms)
            self.pm.start_vm(arg, self.current_vms)
            self._clear_and_refresh()
        elif action == ":node-restart":
            self.pm.restart_node(arg)
            self._clear_and_refresh()
        else:
            print("Unknown command. Use :? for help.")

    def _show_tasks(self, node):
        clear_screen()
        limit = self.config.get("task_limit", 15)
        tasks = self.pm.list_tasks(node, limit)
        display_tasks(tasks)

    def _clear_and_refresh(self):
        clear_screen()
        self.refresh()

    def refresh(self):
        self.current_vms = self.pm.fetch_vms()
        display_vm_table(self.current_vms, self.config.get("use_color", False), config=self.config)

    def _choose_server(self, servers):
        while True:
            print("Wähle einen Server:")
            print("[0] Server hinzufügen")
            for i, s in enumerate(servers, start=1):
                print(f"[{i}] {s['name']} ({s['host']})")
            try:
                idx = int(input("Auswahl: "))
                if idx == 0:
                    clear_screen()
                    settings_menu(self.config)
                    clear_screen()
                    self.config = ConfigManager().load()
                    servers = self.config.get("servers", [])
                    if not servers:
                        print("❌ Kein Server konfiguriert. Beende...")
                        exit()
                    continue  # zurück zur Auswahl mit aktualisierter Liste
                elif 1 <= idx <= len(servers):
                    return servers[idx - 1]
                else:
                    print("Ungültige Auswahl.")
            except ValueError:
                print("Bitte eine Zahl eingeben.")
            
    def _show_nodes(self):
        clear_screen()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            transient=True
        ) as progress:
            task = progress.add_task(description="Lade Node-Daten...", total=None)

            try:
                results = self.pm.fetch_nodes()
            except Exception as e:
                progress.stop()
                print(f"Fehler beim Laden der Nodes: {e}")
                return

        display_node_table(results, use_color=self.config.get("use_color", False))
