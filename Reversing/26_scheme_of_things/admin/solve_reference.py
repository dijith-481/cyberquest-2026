#!/usr/bin/env python3
# Organizer reference solve for Scheme of Things (slot 26).
# Runs the same backtracking DFS the generator used to certify uniqueness,
# driven entirely by deployment/organizer/metadata.json — no embedded answers.

import json
import sys


def rol8(v, r):
    r &= 7
    return ((v << r) | (v >> (8 - r))) & 0xff if r else v & 0xff


def step(s, c, f):
    if f["form"] == "rolxor":
        return rol8(s, f["r"]) ^ c
    if f["form"] == "addmul":
        return (s + c * f["m"]) & 0xff
    if f["form"] == "bandxor":
        return s ^ (c & f["mask"])
    if f["form"] == "roldiv":
        return (rol8(s, f["r"]) + (c + f["d"]) // 2) & 0xff
    if f["form"] == "muladd":
        return (s * f["m1"] + c) & 0xff
    raise ValueError(f["form"])


def solve(pz, node_budget=400000):
    n, init, final = pz["n"], pz["init"], pz["final"]
    chain, pins, pairs, states = pz["chain"], pz["pins"], pz["pairs"], pz["states"]
    cands = [p["cands"] for p in pins]
    pair_at = {}
    for pr in pairs:
        pair_at.setdefault(max(pr["i"], pr["j"]), []).append((min(pr["i"], pr["j"]), pr["b"], pr["t"]))
    state_at = {st["k"]: st for st in states}
    solutions = []
    nodes = 0
    assign = [0] * n

    def dfs(i, s):
        nonlocal nodes
        nodes += 1
        if nodes > node_budget:
            raise RuntimeError("search budget exceeded")
        if i == n:
            if s == final:
                solutions.append(bytes(assign))
            return
        for c in cands[i]:
            assign[i] = c
            s2 = step(s, c, chain[i])
            st = state_at.get(i + 1)
            if st and (s2 & st["m"]) != st["v"]:
                continue
            good = True
            for (j, b, t) in pair_at.get(i, []):
                if (assign[j] + c + b) % 257 != t:
                    good = False
                    break
            if good:
                dfs(i + 1, s2)

    dfs(0, init)
    return solutions, nodes


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "metadata.json"
    meta = json.load(open(path))
    solutions, nodes = solve(meta["puzzle"])
    print(f"search nodes: {nodes}", file=sys.stderr)
    if len(solutions) != 1:
        print(f"expected exactly 1 solution, found {len(solutions)}", file=sys.stderr)
        return 1
    print(solutions[0].decode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
