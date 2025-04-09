import getpass
from model import ConfigManager, ProxmoxManager

def settings_menu(config):
    cm = ConfigManager()
    while True:
        print("\nSettings Menu\n-------------")
        print(f"[1] List servers")
        print(f"[2] Add server")
        print(f"[3] Edit server")
        print(f"[4] Delete server")
        print(f"[5] Change CPU thresholds (yellow: {config['cpu_load_yellow']} / red: {config['cpu_load_red']})")
        print(f"[6] Change language (currently: {config['language']})")
        print(f"[7] Toggle color (currently: {config['use_color']})")
        print(f"[8] Set task list limit (currently: {config.get('task_limit', 15)})")
        print("[0] Save and return")

        choice = input("Choice: ").strip()
        if choice == "1":
            for idx, srv in enumerate(config["servers"]):
                print(f"{idx}: {srv['name']} ({srv['host']})")
        elif choice == "2":
            name = input("Name: ")
            host = input("Host: ")
            username = input("Username: ")
            password = getpass.getpass("Password: ")
            test_server = {"host": host, "username": username, "password": password}
            try:
                ProxmoxManager({"servers": [test_server]})
                config["servers"].append({"name": name, **test_server})
                print("Server added.")
            except:
                print("Connection failed.")
        elif choice == "3":
            idx = int(input("Edit server index: "))
            if 0 <= idx < len(config["servers"]):
                srv = config["servers"][idx]
                srv["name"] = input(f"Name [{srv['name']}]: ") or srv["name"]
                srv["host"] = input(f"Host [{srv['host']}]: ") or srv["host"]
                srv["username"] = input(f"Username [{srv['username']}]: ") or srv["username"]
                pw = getpass.getpass("Password (leave blank to keep): ")
                if pw:
                    srv["password"] = pw
                try:
                    ProxmoxManager({"servers": [srv]})
                    print("Updated and verified.")
                except:
                    print("Update failed.")
        elif choice == "4":
            idx = int(input("Delete server index: "))
            if 0 <= idx < len(config["servers"]):
                del config["servers"][idx]
                print("Server deleted.")
        elif choice == "5":
            config["cpu_load_yellow"] = int(input("CPU Load YELLOW: "))
            config["cpu_load_red"] = int(input("CPU Load RED: "))
        elif choice == "6":
            config["language"] = input("Language code (en/de): ")
        elif choice == "7":
            config["use_color"] = not config["use_color"]
        elif choice == "8":
            config["task_limit"] = int(input("Number of tasks to show: "))
        elif choice == "0":
            cm.save(config)
            print("Saved.")
            break
        else:
            print("Invalid input.")
