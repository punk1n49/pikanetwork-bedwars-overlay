import os
import requests
import tkinter as tk
from tkinter import ttk
import keyboard
import threading 

LOG_PATH = r"C:\Users\sushr\AppData\Roaming\.minecraft\logs\blclient\minecraft\latest.log"

def read_recent_chat_lines(n=21):
    with open(LOG_PATH, "r", encoding="latin-1") as f:
        lines = f.readlines()
    return [line for line in lines[-n:] if "[CHAT]" in line]

def extract_usernames_from_logs(chat_lines):
    for line in reversed(chat_lines):
        content = line.split("[CHAT] ", 1)[-1]
        if not content.startswith("BedWars ?") and content.count(",") >= 2:
            return [name.strip() for name in content.split(",")]
    return []

def get_stats(username):
    url = f"https://stats.pika-network.net/api/profile/{username}/leaderboard?type=bedwars&interval=total&mode=ALL_MODES"
    response = requests.get(url)
    if response.status_code == 200:
        stats = response.json()
        user_stats = {"username": username}
        for stat, details in stats.items():
            entries = details.get("entries", [])
            user_stats[stat] = entries[0]["value"] if entries else "No data"
        return user_stats
    return {"username": username, "Error": "Not found"}

def gather_all_stats():
    chat_lines = read_recent_chat_lines()
    usernames = extract_usernames_from_logs(chat_lines)

    if not usernames:
        print("❌ No valid player list found in logs.")
        return []

    print("👥 Players Detected:", ", ".join(usernames))
    stats_list = []
    for name in usernames:
        clean_username = name.strip().replace(",", "").split()[0]
        stats = get_stats(clean_username)
        stats_list.append(stats)
    return stats_list

def create_overlay(stats_list):
    root = tk.Tk()
    root.title("📊 Bedwars Stats Overlay")

    # 🪟 Always on top + Translucent + No maximize
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.7)  # Translucent
    root.resizable(True, True)

    root.geometry("1200x600+100+100")

    # 🧱 Table setup
    frame = ttk.Frame(root)
    frame.pack(expand=True, fill="both", padx=10, pady=10)

    # Extract all stat keys from first user (assumes uniform structure)
    if not stats_list:
        print("❌ No stats to display.")
        return

    columns = list(stats_list[0].keys())
    tree = ttk.Treeview(frame, columns=columns, show="headings")

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor="center")

    for user_data in stats_list:
        row = [user_data.get(col, "") for col in columns]
        tree.insert("", "end", values=row)

    # Add vertical scrollbar
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(expand=True, fill="both")

    # Start hotkey listener in background
    threading.Thread(target=start_hotkey_listener, args=(tree, columns), daemon=True).start()

    root.mainloop()

def start_hotkey_listener(tree, columns):
    def on_backslash():
        print("🔁 Updating stats...")
        stats = gather_all_stats()
        if stats:
            update_overlay(tree, columns, stats)

    keyboard.add_hotkey('\\', on_backslash)
    print("🎯 Press '\\' to refresh stats")
    keyboard.wait()  # Keeps the listener running

def update_overlay(tree, columns, stats_list):
    for item in tree.get_children():
        tree.delete(item)

    for user_data in stats_list:
        row = [user_data.get(col, "") for col in columns]
        tree.insert("", "end", values=row)

if __name__ == "__main__":
    stats_list = gather_all_stats()
    if stats_list:
        create_overlay(stats_list)


