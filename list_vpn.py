import os
import base64
import requests
import subprocess
import time
from typing import List

class VPNGateManager:
    def __init__(self, data_file="vpns.txt", config_file="config.txt"):
        self.api_url = "http://www.vpngate.net/api/iphone/"
        self.data_file = data_file
        self.ovpn_dir = "ovpn_configs"
        self.config_file = config_file
        self.load_config()
        os.makedirs(self.ovpn_dir, exist_ok=True)

    def load_config(self):
        self.refresh_interval = 600
        self.dont_change = False
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                for line in f:
                    if line.startswith("refresh_interval"):
                        self.refresh_interval = int(line.split("=")[1].strip())
                    elif line.startswith("dont_change"):
                        self.dont_change = line.split("=")[1].strip().lower() == "true"

    def fetch_vpn_data(self):
        print("[*] Fetching VPN data...")
        res = requests.get(self.api_url)
        lines = res.text.strip().split("\n")[2:]
        usable_lines = [line.split(',')[14] for line in lines if ',' in line]
        with open(self.data_file, "w") as f:
            f.write("\n".join(usable_lines))
        print(f"[+] Saved {len(usable_lines)} VPN entries.")

    def parse_and_save_ovpn(self) -> str:
        with open(self.data_file, "r") as f:
            lines = f.readlines()
        if not lines:
            print("[!] No VPN entries available.")
            return ""
        current = lines[0]
        with open(self.data_file, "w") as f:
            f.writelines(lines[1:])  # Remove used entry
        parts = current.strip().split(',')
        b64 = parts[-1]
        ovpn_content = base64.b64decode(b64).decode("utf-8")
        filepath = os.path.join(self.ovpn_dir, "current.ovpn")
        with open(filepath, "w") as f:
            f.write(ovpn_content)
        return filepath

    def connect_vpn(self, ovpn_path: str):
        print(f"[*] Connecting to VPN using {ovpn_path}")
        subprocess.Popen(["openvpn", "--config", ovpn_path])
        print("[+] VPN connection started.")

    def start_proxy(self):
        print("[*] Starting proxy server on port 1080 (SOCKS5)")
        subprocess.Popen(["ssh", "-D", "0.0.0.0:1080", "-N", "-f", "localhost"])
        print("[+] Access your proxy at socks5://<container_ip>:1080")

    def run(self):
        if not os.path.exists(self.data_file):
            self.fetch_vpn_data()
        while True:
            if not self.dont_change:
                if sum(1 for _ in open(self.data_file)) < 5:
                    self.fetch_vpn_data()
                ovpn_path = self.parse_and_save_ovpn()
                if ovpn_path:
                    self.connect_vpn(ovpn_path)
            # self.start_proxy()
            print(f"[*] Sleeping for {self.refresh_interval} seconds...")
            time.sleep(self.refresh_interval)


if __name__ == "__main__":
    manager = VPNGateManager()
    manager.run()
    
    # manager.run()
