#!/data/data/com.termux/files/usr/bin/env python
import os
import re
import json
import time
import random
import asyncio
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

REPO_DIR = os.path.expanduser("~/elu-live")
lock = threading.Lock()
state = {
    "connected": False,
    "username": "",
    "error": "",
    "events": [],
    "next_id": 1
}

def trigger_box(box_num, user_label):
    with lock:
        state["events"].append({
            "id": state["next_id"],
            "box": box_num,
            "user": user_label
        })
        state["next_id"] += 1
        if len(state["events"]) > 25:
            state["events"].pop(0)
    print(f"{GREEN}[🎁] {user_label} -> ሳጥን #{box_num} ተከፈተ!{RESET}")

class MemeHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=REPO_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            with lock:
                payload = json.dumps(state)
            self.wfile.write(payload.encode("utf-8"))
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass

class ReusableServer(ThreadingHTTPServer):
    allow_reuse_address = True

async def connect_tiktok(username):
    try:
        from TikTokLive import TikTokLiveClient
        from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent
    except ImportError:
        msg = "TikTokLive ላይብረሪ አልተጫነም (pip install TikTokLive)"
        with lock:
            state["error"] = msg
        print(f"{RED}[!] {msg}{RESET}")
        while True:
            await asyncio.sleep(5)

    clean = username.lstrip("@").strip()
    client = TikTokLiveClient(unique_id=f"@{clean}")

    @client.on(ConnectEvent)
    async def on_connect(event: ConnectEvent):
        with lock:
            state["connected"] = True
            state["username"] = clean
            state["error"] = ""
        print(f"{GREEN}[✔] ቀጥታ ከ @{clean} TikTok Live ጋር ተገናኝቷል!{RESET}")

    @client.on(CommentEvent)
    async def on_comment(event: CommentEvent):
        txt = event.comment.strip()
        match = re.search(r"\b([1-6])\b", txt)
        if match:
            box_num = int(match.group(1))
            trigger_box(box_num, event.user.nickname)

    @client.on(GiftEvent)
    async def on_gift(event: GiftEvent):
        if event.gift.streakable and event.streaking:
            return
        box_num = random.randint(1, 6)
        trigger_box(box_num, f"{event.user.nickname} 🎁 {event.gift.name}")

    try:
        await client.start()
    except Exception as e:
        with lock:
            state["error"] = f"Live አልተገኘም (@{clean} Live ላይ ላይሆኑ ይችላሉ)"
        print(f"{YELLOW}[!] መገናኘት አልተቻለም: {e}{RESET}")
        while True:
            await asyncio.sleep(5)

def main():
    os.system("clear")
    print(f"{CYAN}=== Elu 🧊 Direct TikTok LIVE Meme Server ==={RESET}\n")
    target = input("አሁን Live ላይ ያለውን Username አስገባ (ለምሳሌ elu...): ").strip()

    server = ReusableServer(("127.0.0.1", 8080), MemeHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    print(f"\n{GREEN}[+] Chrome ላይ ይህን ሊንክ ክፈት:{RESET} {CYAN}http://127.0.0.1:8080{RESET}")
    print(f"{RED}[*] ለማቆም CTRL + C ተጫን።{RESET}\n")

    try:
        if target:
            asyncio.run(connect_tiktok(target))
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        server.server_close()
        print("\n[!] ቆሟል።")

if __name__ == "__main__":
    main()
