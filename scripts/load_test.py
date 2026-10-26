"""BL-29 / MPMS-NF-001 load test: common actions must respond within 2 s for
95% of requests with up to 50 concurrent users.

Uses only the Python standard library. Start the app first (python run.py),
then in a second window:

    python scripts/load_test.py                 # 50 users, 3 rounds, realistic
    python scripts/load_test.py --burst         # worst case: no pauses at all

Realistic mode (default): like real people, each user starts within the first
5 s and pauses 1-3 s ("think time") between clicks. Burst mode removes all
pauses, so every user hits the server at the same instant (stress test).

Setup (not timed): one PM registers, creates a project, and registers + adds
N team members, each with one task. Timed actions per user, all users in
parallel: log in, open the project list, update the status of their own task.
Prints p50 / p95 / max per action and PASS/FAIL against the 2 s target.
"""
import argparse
import http.cookiejar
import random
import re
import statistics
import sys
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

PASSWORD = "LoadTest123"
TARGET_SECONDS = 2.0


class Client:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def request(self, path, data=None):
        body = urllib.parse.urlencode(data).encode() if data is not None else None
        start = time.perf_counter()
        with self.opener.open(self.base + path, data=body, timeout=60) as resp:
            html = resp.read().decode("utf-8", "replace")
            url = resp.geturl()
        return time.perf_counter() - start, html, url


def register(base, name, email, role):
    Client(base).request("/register", {"name": name, "email": email,
                                       "password": PASSWORD, "role": role})


def percentile(values, pct):
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round(pct / 100 * len(ordered)) - 1))
    return ordered[index]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:5000")
    ap.add_argument("--users", type=int, default=50)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--burst", action="store_true",
                    help="no ramp-up and no think time (worst-case stress)")
    args = ap.parse_args()
    run_id = str(int(time.time()))

    # ---------- setup (not timed) ----------
    print(f"Setting up {args.users} users on {args.base_url} ...")
    try:
        Client(args.base_url).request("/login")
    except OSError:
        sys.exit(f"Cannot reach {args.base_url} - start the app first "
                 "with: python run.py")
    pm_email = f"pm{run_id}@load.test"
    register(args.base_url, "Load PM", pm_email, "PM")
    pm = Client(args.base_url)
    pm.request("/login", {"email": pm_email, "password": PASSWORD})
    _, _, url = pm.request("/projects/new", {
        "name": f"Load test {run_id}", "start_date": "", "end_date": ""})
    project_id = int(re.search(r"/projects/(\d+)", url).group(1))

    members = [(f"Member {i}", f"m{i}_{run_id}@load.test") for i in range(args.users)]
    with ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(lambda m: register(args.base_url, m[0], m[1], "Team Member"),
                      members))
    for _, email in members:
        pm.request(f"/projects/{project_id}/members", {"email": email})
    _, html, _ = pm.request(f"/projects/{project_id}")
    ids = dict((name, uid) for uid, name in re.findall(
        r'<option value="(\d+)">(Member \d+)</option>', html))
    for name, _ in members:
        pm.request(f"/projects/{project_id}/tasks",
                   {"title": f"Task for {name}", "priority": "Medium",
                    "due_date": "", "assignee_id": ids.get(name, "")})
    _, html, _ = pm.request(f"/projects/{project_id}")
    task_ids = re.findall(r'/tasks/(\d+)/status', html)
    if len(task_ids) < args.users:
        sys.exit(f"Setup failed: expected {args.users} tasks, found {len(task_ids)}")

    # ---------- timed run ----------
    timings = {"login": [], "project list": [], "task status update": []}
    errors = []
    lock = threading.Lock()
    statuses = ["In Progress", "In Review", "Done", "To Do"]

    def think(low, high):
        if not args.burst:
            time.sleep(random.uniform(low, high))   # not included in timings

    def virtual_user(i):
        _, email = members[i]
        client = Client(args.base_url)
        think(0, 5)                                  # ramp-up
        for r in range(args.rounds):
            try:
                t_login, _, url = client.request(
                    "/login", {"email": email, "password": PASSWORD})
                if "/login" in url:
                    raise RuntimeError(f"login failed for {email}")
                think(1, 3)
                t_list, _, _ = client.request("/projects")
                think(1, 3)
                t_status, _, _ = client.request(
                    f"/tasks/{task_ids[i]}/status",
                    {"status": statuses[r % 4], "next": "/my-tasks"})
                with lock:
                    timings["login"].append(t_login)
                    timings["project list"].append(t_list)
                    timings["task status update"].append(t_status)
                think(1, 3)
            except Exception as exc:  # record and keep going
                with lock:
                    errors.append(str(exc))

    mode = "BURST (no pauses)" if args.burst else "REALISTIC (1-3 s think time)"
    print(f"Running: {args.users} concurrent users x {args.rounds} rounds, {mode} ...")
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.users) as pool:
        list(pool.map(virtual_user, range(args.users)))
    total = time.perf_counter() - start

    # ---------- report ----------
    all_times = [t for v in timings.values() for t in v]
    print()
    print(f"BL-29 load test - {time.strftime('%Y-%m-%d %H:%M')} - mode: {mode}")
    print(f"Users: {args.users} concurrent, rounds: {args.rounds}, "
          f"requests timed: {len(all_times)}, errors: {len(errors)}, "
          f"wall time: {total:.1f} s")
    print(f"{'Action':<22}{'count':>7}{'p50 (s)':>10}{'p95 (s)':>10}{'max (s)':>10}")
    for action, values in timings.items():
        if values:
            print(f"{action:<22}{len(values):>7}{statistics.median(values):>10.3f}"
                  f"{percentile(values, 95):>10.3f}{max(values):>10.3f}")
    if not all_times:
        sys.exit("No successful requests - is the app running?")
    p95 = percentile(all_times, 95)
    ok = p95 <= TARGET_SECONDS and not errors
    print(f"{'ALL':<22}{len(all_times):>7}{statistics.median(all_times):>10.3f}"
          f"{p95:>10.3f}{max(all_times):>10.3f}")
    print()
    print(f"Target: 95th percentile <= {TARGET_SECONDS} s  ->  "
          f"{'PASS' if ok else 'FAIL'}")
    for e in errors[:5]:
        print("error:", e)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
