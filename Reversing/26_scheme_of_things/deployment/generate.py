#!/usr/bin/env python3
"""Scheme of Things — ordinary engineering, slot 26 (Reversing, H0).

Deterministic generator for a medium reverse-engineering challenge.

Design (v2.1 — softened):
  * The passphrase must itself parse as an s-expression (real grammar:
    parens, symbols [a-z0-9_-], integers). Grammar constraints
    ((length) (depth) (width)) are part of the hidden program.
  * A let-bound state chain s0..sN couples every byte: the chain is
    anchored at both ends (s0 = INIT, sN = FINAL), so bytes cannot be
    solved independently — but each step uses a simple bijective mix.
  * Most bytes carry unique pins (affine mod 257 / xor). A few (3-5)
    carry weak pins — mul by 2 mod 256, single-zero-bit band masks,
    div by 2 — leaving 2 candidates each, resolved by adjacent pair-sum
    checksums mod 257. A short backtracking DFS finishes the job.
  * Decoys are mostly classic dead branches ((if #f fake #t),
    (if #t #t fake)) prunable by inspection, plus two live ones that
    read real input-dependent values.
  * Opcode IDs are static per seed (h16(name)); once the blob is
    decoded, IDs map to operators via the visible domain string.
  * The flag is stream-XOR sealed behind FNV-1a(input) ^ salt and only
    decrypts when the hidden expression accepts the exact passphrase.

The generator searches internal variants (seed#0, seed#1, ...) until the
reference DFS solver confirms the puzzle has exactly one solution.
"""
import argparse
import base64
import json
import os
import random
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

SPECIAL_OPS = ["let", "if", "land", "lor"]
EAGER_OPS = ["length", "char", "head", "depth", "width",
             "add", "sub", "mul", "div", "mod", "xor", "rol8", "band", "eq", "lnot"]
ALL_OPS = SPECIAL_OPS + EAGER_OPS

SYMBOL_BYTES = set(b"abcdefghijklmnopqrstuvwxyz0123456789_-")
STRUCTURAL = set(b"() \t")


def rol8(v, r):
    r &= 7
    return ((v << r) | (v >> (8 - r))) & 0xff if r else v & 0xff


def fnv1a64(data: bytes) -> int:
    h = 0xcbf29ce484222325
    for b in data:
        h ^= b
        h = (h * 0x100000001b3) & 0xffffffffffffffff
    return h


def h16(dom: str, variant: int, name: str) -> int:
    return fnv1a64(f"oe:{variant}:{dom}:{name}".encode()) & 0xFFFF


def xorshift64star(x: int) -> int:
    x ^= (x >> 12) & 0xffffffffffffffff
    x ^= (x << 25) & 0xffffffffffffffff
    x ^= (x >> 27) & 0xffffffffffffffff
    return x & 0xffffffffffffffff


def crypt_flag(flag: bytes, password: bytes, salt: int) -> bytes:
    state = fnv1a64(password) ^ salt
    out = bytearray()
    for b in flag:
        state = xorshift64star(state)
        z = (state * 0x2545F4914F6CDD1D) & 0xffffffffffffffff
        out.append(b ^ ((z >> 56) & 0xff))
    return bytes(out)


# AST constructors ---------------------------------------------------------
def I(n): return ("int", int(n))
def B(v): return ("bool", bool(v))
def S(name): return ("sym", name)
def C(name, *args): return ("list", [S(name), *args])
def L(*items): return ("list", list(items))


# Passphrase grammar (mirrors the C parser) --------------------------------
def parse_check(pw: bytes):
    """Returns (ok, depth, width, head_word) mirroring the binary's parser."""
    n = len(pw)
    pos = 0
    state = {"maxdepth": 0, "width": 0}

    def ws():
        nonlocal pos
        while pos < n and pw[pos] in b" \t":
            pos += 1

    def atom():
        nonlocal pos
        start = pos
        while pos < n and pw[pos] not in b" \t()":
            pos += 1
        ln = pos - start
        if ln == 0 or ln > 31:
            return None
        chunk = pw[start:pos]
        body = chunk[1:] if chunk[:1] == b"-" else chunk
        if body.isdigit():
            if chunk[:1] == b"-" and ln == 1:
                return None
            state["width"] += 1
            return ("int", int(chunk))
        if any(b not in SYMBOL_BYTES for b in chunk):
            return None
        state["width"] += 1
        return ("sym", chunk.decode())

    def expr(depth):
        nonlocal pos
        if depth > 16:
            return None
        ws()
        if pos >= n:
            return None
        if pw[pos] == b"("[0]:
            pos += 1
            state["maxdepth"] = max(state["maxdepth"], depth + 1)
            items = []
            while True:
                ws()
                if pos >= n:
                    return None
                if pw[pos] == b")"[0]:
                    pos += 1
                    break
                if len(items) >= 64:
                    return None
                ch = expr(depth + 1)
                if ch is None:
                    return None
                items.append(ch)
            return ("list", items)
        if pw[pos] == b")"[0]:
            return None
        return atom()

    root = expr(0)
    if root is None:
        return None
    ws()
    if pos != n:
        return None
    if root[0] != "list" or not root[1]:
        return None
    head = root[1][0][1] if root[1][0][0] == "sym" else None
    if head is None or len(head) > 31:
        return None
    return {"depth": state["maxdepth"], "width": state["width"], "head": head}


# Chain step forms -----------------------------------------------------------
def chain_step(s, c, f):
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


class Builder:
    def __init__(self, password: bytes, flag: str, rng: random.Random, variant: int):
        self.pw = password
        self.N = len(password)
        self.flag = flag
        self.rng = rng
        self.variant = variant

    # -- symbol ids (static per seed; no input keying) -------------------------
    def sym_id(self, name):
        dom = "op" if name in ALL_OPS else "sym"
        return h16(dom, self.variant, name)

    # -- serialization (same node tags as v1) ---------------------------------
    def serialize(self, node, kind_tags):
        kind = node[0]
        if kind == "int":
            return bytes([kind_tags["int"]]) + struct.pack("<i", node[1])
        if kind == "bool":
            return bytes([kind_tags["bool"], 1 if node[1] else 0])
        if kind == "sym":
            return bytes([kind_tags["sym"]]) + struct.pack("<H", self.sym_id(node[1]))
        if kind == "list":
            items = node[1]
            if len(items) > 255:
                raise ValueError("AST list too large")
            return bytes([kind_tags["list"], len(items)]) + b"".join(self.serialize(x, kind_tags) for x in items)
        raise ValueError(kind)

    # -- chain (simple bijective mixes only) -------------------------------------
    def chain_form(self, i):
        r = self.rng
        pick = r.choice(["rolxor", "muladd", "addmul"])
        if pick == "rolxor":
            return {"form": pick, "r": r.randint(1, 7)}
        if pick == "addmul":
            return {"form": pick, "m": r.randrange(1, 256, 2)}
        return {"form": pick, "m1": r.randrange(1, 256, 2)}

    def chain_expr(self, i, sname):
        f = self.chain[i]
        s = S(sname)
        c = C("char", I(i))
        if f["form"] == "rolxor":
            return C("xor", C("rol8", s, I(f["r"])), c)
        if f["form"] == "addmul":
            return C("mod", C("add", s, C("mul", c, I(f["m"]))), I(256))
        if f["form"] == "bandxor":
            return C("xor", s, C("band", c, I(f["mask"])))
        if f["form"] == "roldiv":
            return C("mod", C("add", C("rol8", s, I(f["r"])), C("div", C("add", c, I(f["d"])), I(2))), I(256))
        return C("mod", C("add", C("mul", s, I(f["m1"])), c), I(256))

    # -- pins (mostly unique; ~15% weak on mutable bytes) -------------------------
    def make_pin(self, i, force_unique=False):
        r = self.rng
        c = self.pw[i]
        ci = C("char", I(i))
        mutable = c in SYMBOL_BYTES
        kinds = ["uniq_affine", "uniq_xor"]
        if mutable and not force_unique and r.random() < 0.15:
            kinds = ["weak_mul2", "weak_mask", "weak_div"]
        kind = r.choice(kinds)
        if kind == "uniq_affine":
            b = r.randint(1, 250)
            t = (c + b) % 257
            cands = [(t - b) % 257]
        elif kind == "uniq_xor":
            x = r.randint(1, 255)
            t = c ^ x
            cands = [t ^ x]
        elif kind == "weak_mul2":
            y = (2 * c) & 0xff
            cands = [y // 2, y // 2 + 128]
        elif kind == "weak_mask":
            bit = 1 << r.randrange(8)
            m = 0xFF ^ bit
            cands = [c & m, (c & m) | bit]
        else:  # weak_div
            d = r.randint(0, 15)
            y = (c + d) // 2
            cands = [v for v in (2 * y - d, 2 * y - d + 1) if 0 <= v <= 255]
        if not (0 <= c <= 255 and c in cands) or any(not (0 <= x <= 255) for x in cands):
            raise RuntimeError("pin candidate construction failed")
        pin = {"i": i, "kind": kind, "cands": sorted(set(cands))}
        if kind == "uniq_affine":
            pin.update({"b": b, "t": t})
        elif kind == "uniq_xor":
            pin.update({"x": x, "t": t})
        elif kind == "weak_mul2":
            pin.update({"y": y})
        elif kind == "weak_mask":
            pin.update({"m": m, "y": c & m})
        else:
            pin.update({"d": d, "y": y})
        return pin

    def pin_expr(self, pin):
        i = pin["i"]
        ci = C("char", I(i))
        kind = pin["kind"]
        if kind == "uniq_affine":
            return C("eq", C("mod", C("add", ci, I(pin["b"])), I(257)), I(pin["t"]))
        if kind == "uniq_xor":
            return C("eq", C("xor", ci, I(pin["x"])), I(pin["t"]))
        if kind == "weak_mul2":
            return C("eq", C("mod", C("mul", ci, I(2)), I(256)), I(pin["y"]))
        if kind == "weak_mask":
            return C("eq", C("band", ci, I(pin["m"])), I(pin["y"]))
        return C("eq", C("div", C("add", ci, I(pin["d"])), I(2)), I(pin["y"]))

    # -- build the whole instance ----------------------------------------------
    def build(self):
        r = self.rng
        N = self.N

        # h16 collision / zero check across every name the blob references.
        names = ALL_OPS + [f"s{k}" for k in range(N + 1)]
        hvals = [h16("op", self.variant, nm) for nm in ALL_OPS]
        hvals += [h16("sym", self.variant, f"s{k}") for k in range(N + 1)]
        if len(set(hvals)) != len(hvals) or 0 in hvals:
            return None

        # Grammar facts (length/depth/width only — no hashed-head hunt).
        gram = parse_check(self.pw)
        if gram is None:
            raise SystemExit("password is not a valid s-expression for the evaluator grammar")

        # State chain from the true passphrase.
        self.chain = [self.chain_form(i) for i in range(N)]
        svals = [0x5A]  # placeholder, replaced by INIT below
        init = r.randint(0, 255)
        svals = [init]
        for i in range(N):
            svals.append(chain_step(svals[-1], self.pw[i], self.chain[i]))
        final = svals[N]

        # Pins: unique for structural bytes, ~15% weak for mutable bytes.
        self.pins = []
        weak_idx = []
        for i in range(N):
            pin = self.make_pin(i)
            self.pins.append(pin)
            if pin["kind"].startswith("weak_"):
                weak_idx.append(i)
        if not (2 <= len(weak_idx) <= 6):
            return None

        # Pair checksums disambiguate weak pins; adjacent pairs resolve
        # immediately (no deferred backtracking).
        pairs = []
        svals_by_byte = svals  # svals[k] = state after k bytes
        for i in weak_idx:
            adj = [j for j in range(N) if j != i and abs(i - j) <= 2]
            j = r.choice(adj)
            a, b = sorted((i, j))
            bias = r.randint(1, 250)
            pairs.append({"i": a, "j": b, "b": bias,
                          "t": (self.pw[a] + self.pw[b] + bias) % 257})

        # Scattered state checks prune the DFS.
        states = []
        for k in r.sample(range(4, N), min(6, N - 4)):
            m = r.choice([1, 3, 7, 12, 24, 48])
            states.append({"k": k, "m": m, "v": svals_by_byte[k] & m})

        # Decoys: mostly classic dead branches prunable by inspection,
        # plus two live ones that read real input-dependent values.
        mutable = [i for i in range(N) if self.pw[i] in SYMBOL_BYTES]
        decoys = []

        def dead_f():  # never-taken branch: plausible but unchecked math
            idx = r.randrange(N)
            return C("if", B(False),
                     C("eq", C("xor", C("char", I(idx)), I(r.randint(0, 255))), I(r.randint(0, 255))),
                     B(True))

        def dead_t():  # always-taken branch: consequence never evaluated
            idx = r.randrange(N)
            return C("if", B(True), B(True),
                     C("eq", C("xor", C("char", I(idx)), I(r.randint(0, 255))), I(r.randint(0, 255))))

        def dB():  # cond reads a live state bit; consequence pins a byte
            k = r.randrange(3, N)
            m = r.choice([1, 3, 7, 12])
            b = r.choice(mutable)
            return C("if",
                     C("eq", C("band", S(f"s{k}"), I(m)), I(svals_by_byte[k] & m)),
                     C("eq", C("char", I(b)), I(self.pw[b])), B(True))

        def dE():  # tautological cond once noticed; consequence pins a byte
            a, b = r.sample(mutable, 2)
            return C("if", C("eq", C("char", I(a)), C("char", I(a))),
                     C("eq", C("char", I(b)), I(self.pw[b])), B(True))

        for maker in (dead_f, dead_t, dead_f, dead_t, dB, dE):
            decoys.append(maker())

        # Assemble the hidden program.
        body = [self.pin_expr(p) for p in self.pins]
        body += [C("eq", C("mod", C("add", C("char", I(p["i"])), C("char", I(p["j"])), I(p["b"])), I(257)), I(p["t"]))
                 for p in pairs]
        body += [C("eq", C("band", S(f"s{st['k']}"), I(st["m"])), I(st["v"])) for st in states]
        body += decoys
        body.append(C("eq", S(f"s{N}"), I(final)))
        r.shuffle(body)

        bindings = L(L(S("s0"), I(init)))
        for i in range(N):
            bindings[1].append(L(S(f"s{i + 1}"), self.chain_expr(i, f"s{i}")))

        root = C("land",
                 C("eq", C("length"), I(N)),
                 C("eq", C("depth"), I(gram["depth"])),
                 C("eq", C("width"), I(gram["width"])),
                 C("let", bindings, C("land", *body)))

        puzzle = {"n": N, "init": init, "final": final,
                  "chain": self.chain, "pins": self.pins,
                  "pairs": pairs, "states": states,
                  "grammar": {"head": gram["head"], "depth": gram["depth"], "width": gram["width"]}}
        return {"root": root, "puzzle": puzzle,
                "states_full": svals_by_byte}


# Reference DFS solver (mirrored in admin/solve_reference.py) -----------------
def step(s, c, f):
    return chain_step(s, c, f)


def solve_puzzle(pz, node_budget=400000):
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


# C emission ------------------------------------------------------------------
def encode_blob(raw: bytes, a: int, b: int, c: int) -> bytes:
    out = bytearray()
    for i, x in enumerate(raw):
        t = ((i * a + b) & 0xff)
        u = rol8((i + c) & 0xff, 3)
        out.append(x ^ t ^ u)
    return bytes(out)


def c_array(data: bytes, width=12):
    parts = [f"0x{x:02x}" for x in data]
    return ",\n    ".join(", ".join(parts[i:i + width]) for i in range(0, len(parts), width))


C_TEMPLATE = r'''// Generated by deployment/generate.py (ordinary engineering, slot 26).
// Organizer source; distribute the binary, not this file.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TAG_INT  @TAG_INT@
#define TAG_BOOL @TAG_BOOL@
#define TAG_SYM  @TAG_SYM@
#define TAG_LIST @TAG_LIST@

#define ENC_A @ENC_A@
#define ENC_B @ENC_B@
#define ENC_C @ENC_C@
#define FLAG_SALT UINT64_C(0x@FLAG_SALT@)
#define DOM_OP  "@VARIANT@:op"
#define DOM_SYM "@VARIANT@:sym"

#define MAX_ATOMS 64
#define MAX_DEPTH 16
#define MAX_ENV 96

static const uint8_t program_blob[] = {
    @BLOB@
};
static const size_t program_blob_len = sizeof(program_blob);

static const uint8_t flag_cipher[] = {
    @FLAGC@
};
static const size_t flag_cipher_len = sizeof(flag_cipher);

// Deliberate semantic noise. These strings are not the hidden program.
__attribute__((used)) static const char *decoy_words[] = {
    "lambda", "quote", "cons", "car", "cdr", "strcmp", "debug_win", "flag.txt", "admin=true"
};

typedef enum { N_INT, N_BOOL, N_SYM, N_LIST } NodeKind;
typedef struct Node Node;
struct Node {
    NodeKind kind;
    int32_t iv;
    uint16_t sym;
    uint8_t count;
    Node **items;
    uint8_t textlen;
    char text[32];
};

typedef struct { size_t off; int failed; } Reader;

static uint8_t rol8(uint8_t x, unsigned r) {
    r &= 7;
    return r ? (uint8_t)((x << r) | (x >> (8 - r))) : x;
}

static uint8_t dec_at(size_t i) {
    uint8_t t = (uint8_t)(i * ENC_A + ENC_B);
    uint8_t u = rol8((uint8_t)(i + ENC_C), 3);
    return program_blob[i] ^ t ^ u;
}

static uint8_t rd8(Reader *r) {
    if (r->off >= program_blob_len) { r->failed = 1; return 0; }
    return dec_at(r->off++);
}
static uint16_t rd16(Reader *r) {
    uint16_t a = rd8(r), b = rd8(r);
    return (uint16_t)(a | (b << 8));
}
static int32_t rd32(Reader *r) {
    uint32_t v = 0;
    for (unsigned i = 0; i < 4; i++) v |= ((uint32_t)rd8(r)) << (8 * i);
    return (int32_t)v;
}

static Node *node_new(void) {
    Node *n = (Node*)calloc(1, sizeof(Node));
    if (!n) exit(2);
    return n;
}

// Parser for the hidden program blob.
static Node *parse_node(Reader *r, unsigned depth) {
    if (depth > 128 || r->failed) { r->failed = 1; return NULL; }
    uint8_t tag = rd8(r);
    Node *n = node_new();
    if (tag == TAG_INT) { n->kind = N_INT; n->iv = rd32(r); return n; }
    if (tag == TAG_BOOL) { n->kind = N_BOOL; n->iv = (rd8(r) != 0); return n; }
    if (tag == TAG_SYM) { n->kind = N_SYM; n->sym = rd16(r); return n; }
    if (tag == TAG_LIST) {
        n->kind = N_LIST;
        n->count = rd8(r);
        n->items = (Node**)calloc(n->count ? n->count : 1, sizeof(Node*));
        if (!n->items) exit(2);
        for (unsigned i = 0; i < n->count; i++) n->items[i] = parse_node(r, depth + 1);
        if (r->failed) return NULL;
        return n;
    }
    r->failed = 1;
    return NULL;
}

static void free_node(Node *n) {
    if (!n) return;
    if (n->kind == N_LIST) {
        for (unsigned i = 0; i < n->count; i++) free_node(n->items[i]);
        free(n->items);
    }
    free(n);
}

// Parser for the player's input: a real s-expression grammar.
//   expr   := atom | "(" ws* (expr ws*)* ")"
//   atom   := integer | symbol
//   symbol := [a-z0-9_-]+        integer := -?[0-9]+
typedef struct { const uint8_t *s; size_t n, pos; int failed; } P;

static void pws(P *p) {
    while (p->pos < p->n && (p->s[p->pos] == ' ' || p->s[p->pos] == '\t')) p->pos++;
}

static Node *parse_input(P *p, int depth, int *maxdepth, int *width) {
    if (p->failed) return NULL;
    if (depth > MAX_DEPTH) { p->failed = 1; return NULL; }
    pws(p);
    if (p->pos >= p->n) { p->failed = 1; return NULL; }
    uint8_t c = p->s[p->pos];
    if (c == ')') { p->failed = 1; return NULL; }
    if (c == '(') {
        p->pos++;
        if (depth + 1 > *maxdepth) *maxdepth = depth + 1;
        Node *items[MAX_ATOMS];
        unsigned cnt = 0;
        for (;;) {
            pws(p);
            if (p->pos >= p->n) { p->failed = 1; return NULL; }
            if (p->s[p->pos] == ')') { p->pos++; break; }
            if (cnt >= MAX_ATOMS) { p->failed = 1; return NULL; }
            Node *ch = parse_input(p, depth + 1, maxdepth, width);
            if (p->failed) return NULL;
            items[cnt++] = ch;
        }
        Node *nd = node_new();
        nd->kind = N_LIST;
        nd->count = (uint8_t)cnt;
        nd->items = (Node**)calloc(cnt ? cnt : 1, sizeof(Node*));
        if (!nd->items) exit(2);
        memcpy(nd->items, items, cnt * sizeof(Node*));
        return nd;
    }
    // Atom: consume until a delimiter.
    size_t start = p->pos;
    while (p->pos < p->n && p->s[p->pos] != ' ' && p->s[p->pos] != '\t' &&
           p->s[p->pos] != '(' && p->s[p->pos] != ')') p->pos++;
    size_t len = p->pos - start;
    if (len == 0 || len > 31) { p->failed = 1; return NULL; }
    Node *nd = node_new();
    size_t k = start;
    int neg = 0, isint = 0;
    if (p->s[k] == '-') { neg = 1; k++; }
    if (k < start + len) {
        int alldig = 1;
        for (size_t q = k; q < start + len; q++)
            if (p->s[q] < '0' || p->s[q] > '9') { alldig = 0; break; }
        if (alldig) {
            int64_t v = 0;
            for (size_t q = k; q < start + len; q++) v = v * 10 + (p->s[q] - '0');
            if (neg) v = -v;
            nd->kind = N_INT;
            nd->iv = (int32_t)v;
            isint = 1;
            (*width)++;
        }
    }
    if (!isint) {
        for (size_t q = start; q < start + len; q++) {
            uint8_t ch = p->s[q];
            int okc = (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9') || ch == '_' || ch == '-';
            if (!okc) { p->failed = 1; return NULL; }
        }
        nd->kind = N_SYM;
        nd->textlen = (uint8_t)len;
        memcpy(nd->text, p->s + start, len);
        nd->text[len] = '\0';
        (*width)++;
    }
    return nd;
}

static uint64_t fnv1a64(const uint8_t *p, size_t n) {
    uint64_t h = UINT64_C(0xcbf29ce484222325);
    for (size_t i = 0; i < n; i++) { h ^= p[i]; h *= UINT64_C(0x100000001b3); }
    return h;
}

// Static 16-bit name hash: h16(name), no input keying.
static uint16_t h16dom(const char *dom, const char *name) {
    uint8_t buf[96];
    size_t n = 0;
    const char *p = "oe:";
    while (*p) buf[n++] = (uint8_t)*p++;
    p = dom;
    while (*p) buf[n++] = (uint8_t)*p++;
    buf[n++] = ':';
    p = name;
    while (*p) buf[n++] = (uint8_t)*p++;
    return (uint16_t)(fnv1a64(buf, n) & 0xffff);
}

enum { P_LET, P_IF, P_LAND, P_LOR, P_LENGTH, P_CHAR, P_HEAD, P_DEPTH, P_WIDTH,
       P_ADD, P_SUB, P_MUL, P_DIV, P_MOD, P_XOR, P_ROL8, P_BAND, P_EQ, P_LNOT, P_COUNT };
static const char *OP_NAMES[P_COUNT] = {
    "let", "if", "land", "lor", "length", "char", "head", "depth", "width",
    "add", "sub", "mul", "div", "mod", "xor", "rol8", "band", "eq", "lnot"
};

typedef struct {
    const uint8_t *input;
    size_t len;
    int depth, width;
    uint16_t head_id;
    uint16_t op[P_COUNT];
} Ctx;

typedef struct { uint16_t id; int64_t val; } Binding;

static int64_t eval(Node *n, Ctx *ctx, const Binding *env, int nenv, int *ok);

static int64_t argn(Node *n, unsigned idx, Ctx *ctx, const Binding *env, int nenv, int *ok) {
    if (!n || n->kind != N_LIST || idx >= n->count) { *ok = 0; return 0; }
    return eval(n->items[idx], ctx, env, nenv, ok);
}

static int64_t eval(Node *n, Ctx *ctx, const Binding *env, int nenv, int *ok) {
    if (!n || !*ok) return 0;
    if (n->kind == N_INT || n->kind == N_BOOL) return n->iv;
    if (n->kind == N_SYM) {
        for (int i = 0; i < nenv; i++)
            if (env[i].id == n->sym) return env[i].val;
        *ok = 0;
        return 0;
    }
    if (n->count == 0 || n->items[0]->kind != N_SYM) { *ok = 0; return 0; }
    uint16_t op = n->items[0]->sym;

    if (op == ctx->op[P_LET]) {
        if (n->count != 3 || n->items[1]->kind != N_LIST ||
            nenv + (int)n->items[1]->count > MAX_ENV) { *ok = 0; return 0; }
        Binding frame[MAX_ENV];
        if (nenv) memcpy(frame, env, sizeof(Binding) * (size_t)nenv);
        int nf = nenv;
        Node *binds = n->items[1];
        for (unsigned i = 0; i < binds->count && *ok; i++) {
            Node *pr = binds->items[i];
            if (pr->kind != N_LIST || pr->count != 2 || pr->items[0]->kind != N_SYM) { *ok = 0; return 0; }
            int64_t v = eval(pr->items[1], ctx, frame, nf, ok);
            frame[nf].id = pr->items[0]->sym;
            frame[nf].val = v;
            nf++;
        }
        if (!*ok) return 0;
        return eval(n->items[2], ctx, frame, nf, ok);
    }
    if (op == ctx->op[P_IF]) {
        int64_t cond = argn(n, 1, ctx, env, nenv, ok);
        if (!*ok) return 0;
        return argn(n, cond ? 2 : 3, ctx, env, nenv, ok);
    }
    if (op == ctx->op[P_LAND]) {
        for (unsigned i = 1; i < n->count; i++) {
            if (!argn(n, i, ctx, env, nenv, ok)) return 0;
            if (!*ok) return 0;
        }
        return 1;
    }
    if (op == ctx->op[P_LOR]) {
        for (unsigned i = 1; i < n->count; i++) {
            int64_t v = argn(n, i, ctx, env, nenv, ok);
            if (!*ok) return 0;
            if (v) return 1;
        }
        return 0;
    }

    if (op == ctx->op[P_LENGTH]) return (int64_t)ctx->len;
    if (op == ctx->op[P_HEAD]) return ctx->head_id;
    if (op == ctx->op[P_DEPTH]) return ctx->depth;
    if (op == ctx->op[P_WIDTH]) return ctx->width;
    if (op == ctx->op[P_CHAR]) {
        int64_t i = argn(n, 1, ctx, env, nenv, ok);
        if (!*ok || i < 0 || (uint64_t)i >= ctx->len) { *ok = 0; return 0; }
        return ctx->input[i];
    }
    if (op == ctx->op[P_ADD]) {
        int64_t v = 0;
        for (unsigned i = 1; i < n->count; i++) v += argn(n, i, ctx, env, nenv, ok);
        return v;
    }
    if (op == ctx->op[P_SUB]) {
        if (n->count < 2) { *ok = 0; return 0; }
        int64_t v = argn(n, 1, ctx, env, nenv, ok);
        for (unsigned i = 2; i < n->count && *ok; i++) v -= argn(n, i, ctx, env, nenv, ok);
        return v;
    }
    if (op == ctx->op[P_MUL]) {
        int64_t v = 1;
        for (unsigned i = 1; i < n->count && *ok; i++) v *= argn(n, i, ctx, env, nenv, ok);
        return v;
    }
    if (op == ctx->op[P_DIV]) {
        int64_t a = argn(n, 1, ctx, env, nenv, ok), b = argn(n, 2, ctx, env, nenv, ok);
        if (!*ok || b == 0) { *ok = 0; return 0; }
        return a / b;
    }
    if (op == ctx->op[P_MOD]) {
        int64_t a = argn(n, 1, ctx, env, nenv, ok), b = argn(n, 2, ctx, env, nenv, ok);
        if (!*ok || b == 0) { *ok = 0; return 0; }
        int64_t z = a % b;
        return z < 0 ? z + b : z;
    }
    if (op == ctx->op[P_XOR]) return argn(n, 1, ctx, env, nenv, ok) ^ argn(n, 2, ctx, env, nenv, ok);
    if (op == ctx->op[P_ROL8]) return rol8((uint8_t)argn(n, 1, ctx, env, nenv, ok), (unsigned)argn(n, 2, ctx, env, nenv, ok));
    if (op == ctx->op[P_BAND]) return argn(n, 1, ctx, env, nenv, ok) & argn(n, 2, ctx, env, nenv, ok);
    if (op == ctx->op[P_EQ]) return argn(n, 1, ctx, env, nenv, ok) == argn(n, 2, ctx, env, nenv, ok);
    if (op == ctx->op[P_LNOT]) return !argn(n, 1, ctx, env, nenv, ok);
    *ok = 0;
    return 0;
}

static uint64_t xs64(uint64_t x) { x ^= x >> 12; x ^= x << 25; x ^= x >> 27; return x; }

static void reveal(const uint8_t *input, size_t n) {
    uint64_t st = fnv1a64(input, n) ^ FLAG_SALT;
    for (size_t i = 0; i < flag_cipher_len; i++) {
        st = xs64(st);
        uint64_t z = st * UINT64_C(0x2545F4914F6CDD1D);
        putchar((int)(flag_cipher[i] ^ (uint8_t)(z >> 56)));
    }
    putchar('\n');
}

int main(void) {
    char buf[256];
    puts("oe-evaluator // calibration build");
    puts("The evaluator does not ask what you typed. It asks what the expression becomes.");
    fputs("passphrase> ", stdout);
    fflush(stdout);
    if (!fgets(buf, sizeof(buf), stdin)) return 1;
    size_t n = strcspn(buf, "\r\n");
    buf[n] = '\0';

    P p = { (const uint8_t*)buf, n, 0, 0 };
    int maxdepth = 0, width = 0;
    Node *root = parse_input(&p, 0, &maxdepth, &width);
    pws(&p);
    if (!root || p.failed || p.pos != n || root->kind != N_LIST || root->count == 0) {
        puts("Input does not satisfy the current evaluation policy. Incident logged.");
        return 1;
    }

    Ctx ctx;
    memset(&ctx, 0, sizeof(ctx));
    ctx.input = (const uint8_t*)buf;
    ctx.len = n;
    ctx.depth = maxdepth;
    ctx.width = width;
    if (root->items[0]->kind == N_SYM)
        ctx.head_id = h16dom(DOM_SYM, root->items[0]->text);
    for (int i = 0; i < P_COUNT; i++)
        ctx.op[i] = h16dom(DOM_OP, OP_NAMES[i]);

    Reader r = { 0, 0 };
    Node *prog = parse_node(&r, 0);
    int ok = !r.failed && r.off == program_blob_len;
    int64_t accepted = ok ? eval(prog, &ctx, NULL, 0, &ok) : 0;
    if (ok && accepted) reveal((const uint8_t*)buf, n);
    else puts("Input does not satisfy the current evaluation policy. Incident logged.");
    free_node(root);
    free_node(prog);
    return 0;
}
'''


def emit_c(blob, flagc, kind_tags, a, b, c, salt, variant):
    src = C_TEMPLATE
    src = src.replace("@TAG_INT@", str(kind_tags["int"]))
    src = src.replace("@TAG_BOOL@", str(kind_tags["bool"]))
    src = src.replace("@TAG_SYM@", str(kind_tags["sym"]))
    src = src.replace("@TAG_LIST@", str(kind_tags["list"]))
    src = src.replace("@ENC_A@", str(a)).replace("@ENC_B@", str(b)).replace("@ENC_C@", str(c))
    src = src.replace("@FLAG_SALT@", f"{salt:016x}")
    src = src.replace("@VARIANT@", str(variant))
    src = src.replace("@BLOB@", c_array(blob))
    src = src.replace("@FLAGC@", c_array(flagc))
    return src


SOLVE_REFERENCE_TEMPLATE = '''#!/usr/bin/env python3
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
'''


def main():
    ap = argparse.ArgumentParser(description="Generate the Scheme of Things RE challenge (ordinary engineering, slot 26)")
    ap.add_argument("--seed", default="oe-scheme-of-things-26")
    ap.add_argument("--password", default="(chain the state and backtrack 26)")
    ap.add_argument("--flag", default="cyber_quest{ch41n3d_b4cktr4ck1ng_9d41f3}")
    ap.add_argument("--out", default="build_scheme_of_things")
    ap.add_argument("--no-build", action="store_true")
    args = ap.parse_args()

    password = args.password.encode()
    flag = args.flag.encode()
    if not (8 <= len(password) <= 80):
        raise SystemExit("password must be 8..80 bytes")
    if len(flag) > 200:
        raise SystemExit("flag too long")

    # Search internal variants until the puzzle has exactly one solution.
    chosen = None
    for variant in range(64):
        rng = random.Random(f"{args.seed}#{variant}")
        b = Builder(password, args.flag, rng, variant)
        built = b.build()
        if built is None:
            continue
        try:
            solutions, nodes = solve_puzzle(built["puzzle"])
        except RuntimeError:
            continue
        if solutions != [password]:
            continue
        chosen = (variant, b, built, nodes)
        break
    if chosen is None:
        raise SystemExit("no variant produced a uniquely solvable puzzle (try another seed)")
    variant, b, built, nodes = chosen
    rng = b.rng
    print(f"variant #{variant}: unique solution certified in {nodes} DFS nodes")

    out = Path(args.out).resolve()
    if out.exists():
        shutil.rmtree(out)
    player = out / "player"
    org = out / "organizer"
    player.mkdir(parents=True)
    org.mkdir(parents=True)

    kind_tags = dict(zip(["int", "bool", "sym", "list"], rng.sample(range(0x21, 0xF0), 4)))
    raw = b.serialize(built["root"], kind_tags)
    a = rng.randrange(1, 256, 2)
    bb = rng.randrange(0, 256)
    cc = rng.randrange(0, 256)
    encoded = encode_blob(raw, a, bb, cc)
    salt = rng.getrandbits(64)
    enc_flag = crypt_flag(flag, password, salt)

    csrc = emit_c(encoded, enc_flag, kind_tags, a, bb, cc, salt, variant)
    (org / "challenge.c").write_text(csrc)
    (org / "Makefile").write_text(
        "CC ?= gcc\nCFLAGS ?= -std=c11 -O1 -fno-inline -fno-ident -Wall -Wextra\n"
        "all: evaluator\nevaluator: challenge.c\n\t$(CC) $(CFLAGS) challenge.c -o evaluator\n"
        "strip:\n\tstrip evaluator\nclean:\n\trm -f evaluator\n")

    meta = {
        "seed": args.seed,
        "variant": variant,
        "password": args.password,
        "flag": args.flag,
        "kind_tags": kind_tags,
        "encoding": {"a": a, "b": bb, "c": cc},
        "puzzle": built["puzzle"],
        "ast_raw_b64": base64.b64encode(raw).decode(),
        "ast_encoded_b64": base64.b64encode(encoded).decode(),
        "flag_salt": f"0x{salt:016x}",
        "flag_cipher_hex": enc_flag.hex(),
    }
    (org / "metadata.json").write_text(json.dumps(meta, indent=2))
    (org / "solve_reference.py").write_text(SOLVE_REFERENCE_TEMPLATE)
    os.chmod(org / "solve_reference.py", 0o755)

    player_readme = '''oe-evaluator

Performance calibration season. The evaluation tool that arrived with
the Q3 import batch has rejected every passphrase IT Support has on
file, and it is the only thing standing between you and your review
file. The vendor documentation is one page and mostly warranty
disclaimers. The one sentence IT extracted from the vendor: the tool
expects "a statement in the approved grammar." No sample statements
were approved.

A note taped to the kiosk, in someone's handwriting:

    The evaluator does not ask what you typed.
    It asks what the expression becomes.

Recover the statement. The tool prints the rest once an evaluation
passes.
'''
    (player / "README.txt").write_text(player_readme)

    if not args.no_build:
        subprocess.run(["gcc", "-std=c11", "-O1", "-fno-inline", "-fno-ident",
                        "-Wall", "-Wextra", str(org / "challenge.c"), "-o", str(player / "evaluator")], check=True)
        if shutil.which("strip"):
            subprocess.run(["strip", str(player / "evaluator")], check=True)
        run = lambda data: subprocess.run([str(player / "evaluator")], input=data,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
        # 1. Correct passphrase reveals the flag.
        p = run(password + b"\n")
        if flag not in p:
            raise SystemExit("self-test failed: correct passphrase did not reveal flag")
        # 2. Plain wrong input rejected.
        p = run(b"completely wrong\n")
        if flag in p:
            raise SystemExit("self-test failed: wrong input revealed flag")
        # 3. Flip the ambiguous bit of the first weak pin (carried ambiguity
        #    must be caught by the pair checksum, not just the final anchor).
        weak = next(p_ for p_ in built["puzzle"]["pins"] if p_["kind"].startswith("weak_"))
        flip = built["puzzle"]["pins"] and (weak["cands"][0] ^ weak["cands"][1])
        mutant = bytearray(password)
        mutant[weak["i"]] ^= flip
        p = run(bytes(mutant) + b"\n")
        if flag in p:
            raise SystemExit("self-test failed: weak-bit mutant revealed flag")
        # 4. Grammar violations rejected: unbalanced, non-expression, bad charset.
        for bad in (b"(chain the state", b"chain the state and backtrack 26",
                    b"(chain the state; and backtrack 26)"):
            p = run(bad + b"\n")
            if flag in p:
                raise SystemExit(f"self-test failed: grammar violation accepted: {bad!r}")

    bundle = out / "26_scheme_of_things.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in player.iterdir():
            zf.write(p, arcname=p.name)

    print(f"Generated: {out}")
    print(f"Player bundle: {bundle}")
    print(f"Organizer source: {org / 'challenge.c'}")
    print(f"Reference solver: {org / 'solve_reference.py'}")


if __name__ == "__main__":
    main()
