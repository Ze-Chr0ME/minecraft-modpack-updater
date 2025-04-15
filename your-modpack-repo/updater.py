import os
import hashlib
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import urllib.request

CONFIG_FILE = "updater_config.json"
MANIFEST_URL = "https://raw.githubusercontent.com/you-cant-run/minecraft-modpack-updater/main/manifest.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def calculate_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def download_file(url, dest):
    urllib.request.urlretrieve(url, dest)

def update_mods(mod_folder, log_callback):
    response = urllib.request.urlopen(MANIFEST_URL)
    manifest = json.load(response)

    os.makedirs(mod_folder, exist_ok=True)

    for filename, info in manifest.items():
        filepath = os.path.join(mod_folder, filename)
        if not os.path.exists(filepath) or calculate_sha256(filepath) != info["sha256"]:
            log_callback(f"Downloading: {filename}")
            download_file(info["url"], filepath)
        else:
            log_callback(f"Up to date: {filename}")

class ModUpdaterGUI:
    def __init__(self):
        self.config = load_config()
        self.root = tk.Tk()
        self.root.title("Minecraft Mod Updater")
        self.root.geometry("600x400")

        self.log_box = tk.Text(self.root, wrap="word", state="disabled", bg="#1e1e1e", fg="#d4d4d4")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

        bottom = tk.Frame(self.root)
        bottom.pack(pady=5)

        tk.Button(bottom, text="Run Update", command=self.run_update).pack(side="left", padx=5)
        tk.Button(bottom, text="Set Mod Folder", command=self.set_mod_folder).pack(side="left", padx=5)
        tk.Button(bottom, text="Exit", command=self.root.quit).pack(side="left", padx=5)

        self.root.mainloop()

    def set_mod_folder(self):
        folder = filedialog.askdirectory(title="Select your mod folder")
        if folder:
            self.config["mod_folder"] = folder
            save_config(self.config)
            self.log("Mod folder set to: " + folder)

    def run_update(self):
        mod_folder = self.config.get("mod_folder")
        if not mod_folder:
            messagebox.showerror("Error", "Please set your mod folder first.")
            return
        self.log("Starting update...")
        try:
            update_mods(mod_folder, self.log)
            self.log("Update complete.")
        except Exception as e:
            self.log("Error: " + str(e))

    def log(self, msg):
        self.log_box.config(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

if __name__ == "__main__":
    ModUpdaterGUI()
