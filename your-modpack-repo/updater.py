import os
import hashlib
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import urllib.request
import platform

def get_config_dir():
    system = platform.system()
    if system == "Windows":
        return os.path.join(os.environ['APPDATA'], "ModpackUpdaterConfig")
    elif system == "Darwin":  # macOS
        return os.path.expanduser("~/Library/Application Support/ModpackUpdaterConfig")
    else:  # Linux and other UNIX-like systems
        return os.path.expanduser("~/.config/ModpackUpdaterConfig")

CONFIG_PATH = os.path.join(get_config_dir(), "updater_config.json")
MANIFEST_URL = "https://raw.githubusercontent.com/you-cant-run/minecraft-modpack-updater/main/manifest.json"
BASE_MOD_URL = "https://raw.githubusercontent.com/you-cant-run/minecraft-modpack-updater/main/"

def load_config():
    # Create config directory if it doesn't exist
    os.makedirs(get_config_dir(), exist_ok=True)
    
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    return {}

def save_config(config):
    # Ensure config directory exists before saving
    os.makedirs(get_config_dir(), exist_ok=True)
    
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f)
    except Exception as e:
        print(f"Error saving config: {e}")

def calculate_sha256(filepath):
    if not os.path.exists(filepath):
        return None
    
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def download_file(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(dest, 'wb') as out_file:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            out_file.write(chunk)

def update_mods(mod_folder, log_callback, remove_files=True):
    log_callback("Fetching manifest...")
    
    req = urllib.request.Request(MANIFEST_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        manifest = json.loads(response.read())
    
    log_callback("Manifest loaded. Checking mods...")
    
    mods = manifest["modpack"]["mods"]
    log_callback(f"Found {len(mods)} mods in manifest")
    
    os.makedirs(mod_folder, exist_ok=True)
    
    existing_files = [f for f in os.listdir(mod_folder) if os.path.isfile(os.path.join(mod_folder, f))]
    log_callback(f"Found {len(existing_files)} existing files in mod folder")
    
    files_in_manifest = set()
    
    for mod in mods:
        filename = mod["name"]
        sha256_hash = mod["sha256"]
        files_in_manifest.add(filename)
        
        # Determine URL
        if "url" in mod:
            target_url = mod["url"]
        elif "file" in mod:
            target_url = BASE_MOD_URL + mod["file"]
        else:
            target_url = BASE_MOD_URL + "your-modpack-repo/mods/" + filename
        
        filepath = os.path.join(mod_folder, filename)
        should_download = False
        
        if not os.path.exists(filepath):
            should_download = True
            log_callback(f"Missing: {filename}. Will download.")
        else:
            local_hash = calculate_sha256(filepath)
            if local_hash != sha256_hash:
                should_download = True
                log_callback(f"Outdated: {filename}. Will download.")
            else:
                log_callback(f"Up to date: {filename}")
        
        if should_download:
            log_callback(f"Downloading: {filename} from {target_url}")
            try:
                download_file(target_url, filepath)
                new_hash = calculate_sha256(filepath)
                
                if new_hash == sha256_hash:
                    log_callback(f"Download successful: {filename}")
                else:
                    log_callback(f"Hash mismatch after download: {filename}")
            except Exception as e:
                log_callback(f"Download failed for {filename}: {e}")
    
    # Remove files not in manifest
    if remove_files:
        log_callback("Checking for files to remove...")
        removed_count = 0
        
        for file in existing_files:
            if file not in files_in_manifest:
                try:
                    os.remove(os.path.join(mod_folder, file))
                    log_callback(f"Removed: {file}")
                    removed_count += 1
                except:
                    log_callback(f"Failed to remove: {file}")
        
        if removed_count > 0:
            log_callback(f"Removed {removed_count} file(s)")
        else:
            log_callback("No files needed removal")

class ModUpdaterGUI:
    def __init__(self):
        self.config = load_config()
        self.root = tk.Tk()
        self.root.title("Minecraft Mod Updater")
        self.root.geometry("700x450")
        
        # Log frame
        log_frame = ttk.Frame(self.root, padding="10")
        log_frame.pack(fill="both", expand=True)
        
        self.log_box = tk.Text(log_frame, wrap="word", state="disabled", height=15, width=80)
        self.log_box.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_box.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_box.config(yscrollcommand=scrollbar.set)
        
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        self.log_box.config(bg="#2b2b2b", fg="#a9b7c6", insertbackground="#bbbbbb")
        
        # Button frame
        button_frame = ttk.Frame(self.root, padding=(10, 5, 10, 10))
        button_frame.pack(fill="x")
        
        ttk.Button(button_frame, text="Run Update", command=self.run_update).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Set Mod Folder", command=self.set_mod_folder).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Exit", command=self.root.quit).pack(side="right", padx=5)
        
        self.remove_files_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(button_frame, text="Remove Outdated Mods", variable=self.remove_files_var).pack(side="left", padx=10)
        
        self.log("Updater initialized.")
        self.log(f"Manifest URL: {MANIFEST_URL}")
        
        mod_folder = self.config.get("mod_folder")
        if mod_folder:
            self.log(f"Current mod folder: {mod_folder}")
        else:
            self.log("Mod folder not set. Please set it first.")
        
        self.root.mainloop()
    
    def set_mod_folder(self):
        folder = filedialog.askdirectory(title="Select your Minecraft Mod Folder", 
                                        initialdir=self.config.get("mod_folder"))
        if folder:
            self.config["mod_folder"] = folder
            save_config(self.config)
            self.log(f"Mod folder set to: {folder}")
    
    def run_update(self):
        mod_folder = self.config.get("mod_folder")
        if not mod_folder:
            messagebox.showerror("Error", "Mod folder not set.")
            return
        
        self.log("-" * 20)
        self.log(f"Starting update for: {mod_folder}")
        
        try:
            update_mods(mod_folder, self.log, self.remove_files_var.get())
            self.log("-" * 20)
            self.log("Update complete!")
        except Exception as e:
            self.log(f"Error: {e}")
            messagebox.showerror("Update Error", f"An error occurred: {e}")
    
    def log(self, msg):
        try:
            self.log_box.config(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.config(state="disabled")
            self.root.update_idletasks()
        except:
            print(f"Log: {msg}")

if __name__ == "__main__":
    ModUpdaterGUI()
