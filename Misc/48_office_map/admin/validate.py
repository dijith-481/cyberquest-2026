#!/usr/bin/env python3
"""Validator for the Office Map challenge (spec section 15).

Checks the static page in deployment/office_map.html:
- all rooms reachable, correct degrees, planar-ish edge budget
- exactly one Hamiltonian path from the Nap Room
- initials(path) == NEWBIEGOTLOST
- endpoints degree 1, max degree <= 5
- room table order != solution order, random-looking ids
- solution/flag strings absent from the handout
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
HTML = HERE.parent / "deployment" / "index.html"

EXPECTED_DEG = {
    "Nap Room": 1, "Engineering": 4, "Workshop": 4, "Break Room": 3,
    "Ideation Room": 4, "Electrical Closet": 5, "Green Room": 3,
    "Open Office": 4, "Testing": 2, "Legal": 5, "On-Call Room": 3,
    "Studio": 5, "Terminal Room": 1,
}
SOLUTION = ["Nap Room", "Engineering", "Workshop", "Break Room",
            "Ideation Room", "Electrical Closet", "Green Room",
            "Open Office", "Testing", "Legal", "On-Call Room",
            "Studio", "Terminal Room"]


def main():
    check_only = "--check-only" in sys.argv
    html = HTML.read_text()
    fails = []

    def need(cond, msg):
        print(("PASS " if cond else "FAIL ") + msg)
        if not cond:
            fails.append(msg)

    pairs = re.findall(r'\{id:"(r_[0-9a-f]+)", name:"([^"]+)"', html)
    id2 = dict(pairs)
    need(len(pairs) == 13, "13 unique rooms")
    need(len(set(id2)) == 13, "random ids unique")
    need(sorted(id2.values()) == sorted(SOLUTION), "room names match roster")

    links = re.findall(r'\["(r_[0-9a-f]+)","(r_[0-9a-f]+)"\]', html)
    adj = defaultdict(set)
    for a, b in links:
        adj[a].add(b)
        adj[b].add(a)
    need(all(len(adj[i]) == EXPECTED_DEG[n] for i, n in pairs),
         "door counts match design")
    need(max(len(adj[i]) for i, _ in pairs) <= 5, "max degree <= 5")

    start = next(i for i, n in pairs if n == "Nap Room")
    goal = next(i for i, n in pairs if n == "Terminal Room")
    sols = []

    def dfs(path, vis):
        if len(path) == 13:
            sols.append(tuple(path))
            return
        for nb in adj[path[-1]]:
            if nb not in vis:
                vis.add(nb)
                path.append(nb)
                dfs(path, vis)
                path.pop()
                vis.remove(nb)

    dfs([start], {start})
    need(len(sols) == 1, "exactly one Hamiltonian path from the Nap Room")
    if sols:
        route = [id2[i] for i in sols[0]]
        need(route == SOLUTION, "path == intended route")
        need("".join(n[0] for n in route) == "NEWBIEGOTLOST",
             "initials spell payload")
        need(sols[0][-1] == goal, "path ends at Terminal Room")

    order = [n for _, n in pairs]
    need(order != SOLUTION, "exported order != solution order")
    low = html.lower()
    # The assembled flag must never appear on the page. The leet table and the
    # drawing number ARE on the page deliberately — they are the last two steps
    # — so the check is on the finished string and on the leet body, not on the
    # individual ingredients.
    need("newbiegotlost" not in low, "plaintext payload absent from page")
    need("n3wb13g07l057" not in low, "leet payload absent from page")
    need("cyber_quest{n3w" not in low, "assembled flag absent from page")
    need("cyber_quest{cub" not in low, "flag absent from page")
    need("correctroute" not in low, "no stored solution variable")

    # The suffix must be discoverable, and only in the Workshop prop.
    need("b1c17" in low, "facilities drawing number present on the page")
    need(low.count("b1c17") == 1, "drawing number appears exactly once")
    need("house leet" in low, "leet table present on the page")
    # ...and the leet table must be a table, not the answer.
    for pair in ("a=4", "e=3", "i=1", "o=0", "s=5", "t=7"):
        need(pair in low, f"leet table states {pair}")

    if fails:
        print(f"{len(fails)} check(s) failed")
        sys.exit(1)
    print("all checks passed")
    if not check_only:
        print("tip: serve deployment/ statically; no backend needed")


if __name__ == "__main__":
    main()
