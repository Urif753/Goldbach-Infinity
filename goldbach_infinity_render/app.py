import os, time, threading, sqlite3, math
from flask import Flask, jsonify, render_template

app = Flask(__name__)
DB_PATH = os.environ.get("DB_PATH", "/var/data/goldbach.db")
if not os.path.isdir(os.path.dirname(DB_PATH)):
    DB_PATH = os.environ.get("DB_PATH", "goldbach.db")

BLOCK_SIZE = int(os.environ.get("BLOCK_SIZE", "200000"))
PAUSE_SECONDS = float(os.environ.get("PAUSE_SECONDS", "0.05"))

lock = threading.Lock()
state = {
    "current": 4, "checked": 0, "started_at": time.time(),
    "last_batch_seconds": 0, "rate": 0, "status": "Arrancando",
    "counterexample": None, "milestone": 0
}

def db():
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("""CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY CHECK(id=1), current INTEGER, checked INTEGER,
        counterexample INTEGER, updated REAL)""")
    con.commit()
    return con

def load_progress():
    con = db()
    row = con.execute("SELECT current, checked, counterexample FROM progress WHERE id=1").fetchone()
    if row:
        state["current"], state["checked"], state["counterexample"] = row
    else:
        con.execute("INSERT OR REPLACE INTO progress VALUES (1, 4, 0, NULL, ?)", (time.time(),))
        con.commit()
    con.close()

def save_progress():
    con = db()
    con.execute("INSERT OR REPLACE INTO progress VALUES (1, ?, ?, ?, ?)",
                (state["current"], state["checked"], state["counterexample"], time.time()))
    con.commit()
    con.close()

def sieve(n):
    # bytearray sieve, efficient for each finite batch
    flags = bytearray(b"\x01") * (n + 1)
    flags[0:2] = b"\x00\x00"
    for p in range(2, math.isqrt(n) + 1):
        if flags[p]:
            start = p*p
            flags[start:n+1:p] = b"\x00" * (((n-start)//p)+1)
    return flags

def check_even(n, primes):
    # Find p <= n/2 such that both p and n-p are prime
    for p in range(2, n//2 + 1):
        if primes[p] and primes[n-p]:
            return True
    return False

def worker():
    load_progress()
    while True:
        start_time = time.time()
        start = max(4, int(state["current"]))
        if start % 2: start += 1
        end = start + BLOCK_SIZE - 2
        primes = sieve(end)
        found = None
        checked_here = 0
        for n in range(start, end + 1, 2):
            if not check_even(n, primes):
                found = n
                break
            checked_here += 1
        elapsed = max(0.001, time.time() - start_time)
        with lock:
            state["last_batch_seconds"] = round(elapsed, 3)
            state["rate"] = int(checked_here / elapsed)
            state["checked"] += checked_here
            state["current"] = found if found else end + 2
            state["status"] = "¡Contraejemplo encontrado!" if found else "Investigando"
            if found:
                state["counterexample"] = found
            state["milestone"] = state["current"] // 1000000
            save_progress()
        if found:
            # Stop on a possible counterexample; do not continue past it.
            return
        time.sleep(PAUSE_SECONDS)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def api_status():
    with lock:
        s = dict(state)
    s["uptime"] = int(time.time() - s["started_at"])
    s["target"] = "∞ (por bloques)"
    return jsonify(s)

def start_worker_once():
    if not getattr(app, "_worker_started", False):
        app._worker_started = True
        threading.Thread(target=worker, daemon=True, name="goldbach-worker").start()

@app.before_request
def ensure_worker():
    start_worker_once()

if __name__ == "__main__":
    start_worker_once()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
