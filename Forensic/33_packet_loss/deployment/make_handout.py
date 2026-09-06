#!/usr/bin/env python3
"""packet_loss — deterministic handout generator.

Regenerates ../handout/office_capture_0318.pcap: a morning of ordinary
office traffic on the 10.14.0.0/16 network, hand-assembled packet by
packet (no scapy in the build environment). Ethernet/IPv4/UDP/TCP/ICMP
checksums are all computed properly so the capture dissects cleanly.

Nothing here is secret; the solve path is documented in admin/solution.md.
"""

import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")

FLAG = "cyber_quest{dn5_3xf1l_r34ds_l1k3_h4rm0n_l3tt3rs_2c9a71}"

# ---------------------------------------------------------------- helpers

def cksum(data: bytes) -> int:
    if len(data) % 2:
        data += b"\x00"
    s = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    s = (s >> 16) + (s & 0xFFFF)
    s += s >> 16
    return (~s) & 0xFFFF


def mac(s: str) -> bytes:
    return bytes(int(x, 16) for x in s.split(":"))


def ip4(s: str) -> bytes:
    return bytes(int(x) for x in s.split("."))


class Cap:
    """Packet accumulator with a monotonic clock."""

    def __init__(self, start=1773818400):  # 2026-03-18 08:00:00 UTC
        self.pkts = []
        self.t = float(start)
        self.ipid = 0x1000

    def wait(self, seconds: float) -> None:
        self.t += seconds

    def _emit(self, src_mac, dst_mac, ip_pkt):
        self.ipid += 1
        eth = dst_mac + src_mac + b"\x08\x00"
        self.pkts.append((self.t, eth + ip_pkt))

    def emit(self, src_mac, dst_mac, src_ip, dst_ip, proto, transport: bytes,
             payload: bytes = b"") -> None:
        # transport must already carry its own checksum
        total = 20 + len(transport) + len(payload)
        ip = struct.pack("!BBHHHBBH", 0x45, 0, total, self.ipid, 0x4000, 64,
                         proto, 0) + src_ip + dst_ip
        ip = ip[:10] + struct.pack("!H", cksum(ip)) + ip[12:]
        if proto == 17:  # UDP checksum covers the pseudo-header
            ph = src_ip + dst_ip + b"\x00\x11" + struct.pack("!H", len(transport))
            upd = transport + payload
            c = cksum(ph + upd) or 0xFFFF
            upd = upd[:6] + struct.pack("!H", c) + upd[8:]
        elif proto == 6:  # TCP, same pseudo-header trick
            ph = src_ip + dst_ip + b"\x00\x06" + struct.pack("!H", len(transport))
            upd = transport + payload
            c = cksum(ph + upd) or 0xFFFF
            upd = upd[:16] + struct.pack("!H", c) + upd[18:]
        else:
            upd = transport + payload
        self._emit(src_mac, dst_mac, ip + upd)

    def udp(self, src_mac, dst_mac, src_ip, dst_ip, sport, dport, payload):
        self.emit(src_mac, dst_mac, src_ip, dst_ip, 17,
                  struct.pack("!HHHH", sport, dport, 8 + len(payload), 0),
                  payload)

    def tcp(self, src_mac, dst_mac, src_ip, dst_ip, sport, dport, seq, ack,
            flags, payload=b"", win=64240):
        self.emit(src_mac, dst_mac, src_ip, dst_ip, 6,
                  struct.pack("!HHIIBBHHH", sport, dport, seq, ack, 0x50,
                              flags, win, 0, 0) + payload, b"")

    def icmp_echo(self, src_mac, dst_mac, src_ip, dst_ip, ident, seq, data,
                  reply=False):
        typ = 0 if reply else 8
        hdr = struct.pack("!BBHHH", typ, 0, 0, ident, seq)
        c = cksum(hdr + data)
        self.emit(src_mac, dst_mac, src_ip, dst_ip, 1,
                  hdr[:2] + struct.pack("!H", c) + hdr[4:] + data, b"")

    def write(self, path: str) -> None:
        with open(path, "wb") as f:
            f.write(struct.pack("!IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))
            for t, pkt in self.pkts:
                sec = int(t)
                usec = int((t - sec) * 1_000_000)
                f.write(struct.pack("!IIII", sec, usec, len(pkt), len(pkt)))
                f.write(pkt)


# ---------------------------------------------------------------- traffic

GW, RESOL, WS = mac("02:1a:4f:00:00:01"), mac("02:1a:4f:01:00:53"), mac("02:1a:4f:07:00:23")
MAC_A = mac("02:1a:4f:03:00:41")   # finance-103
MAC_B = mac("02:1a:4f:05:00:07")   # printer-dock-4 (not the printer)
IP_GW, IP_RESOL = ip4("10.14.0.1"), ip4("10.14.1.53")
IP_A, IP_B, IP_X = ip4("10.14.3.103"), ip4("10.14.5.7"), ip4("10.14.7.23")
IP_EXT = ip4("198.51.100.7")       # upstream for the sync domain
MAC_GW = GW

NORMAL_DNS = [
    ("wiki.oe.internal", "10.14.2.10"),
    ("jira.oe.internal", "10.14.2.11"),
    ("time.oe.internal", "10.14.1.9"),
    ("confluence.oe.internal", "10.14.2.12"),
    ("printer-dock-4.oe.internal", "10.14.5.7"),
    ("wiki.oe.internal", "10.14.2.10"),
    ("snacks.oe.internal", "10.14.2.13"),
    ("jira.oe.internal", "10.14.2.11"),
]

EXFIL_DOMAIN = "assets-sync.oe-cdn-demo.net"
BASE32 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


def b32(s: str) -> str:
    bits = 0
    acc = 0
    out = []
    for ch in s.encode():
        acc = (acc << 8) | ch
        bits += 8
        while bits >= 5:
            bits -= 5
            out.append(BASE32[(acc >> bits) & 31])
    if bits:
        out.append(BASE32[(acc << (5 - bits)) & 31])
    return "".join(out)


def dns_query(name: str, qtype=1, qid=None) -> bytes:
    qid = qid or 0
    hdr = struct.pack("!HHHHHH", qid, 0x0100, 1, 0, 0, 0)
    q = b"".join(bytes([len(l)]) + l.encode() for l in name.split(".")) + b"\x00"
    return hdr + q + struct.pack("!HH", qtype, 1)


def dns_answer(name: str, addr=None, txt=None, qtype=1, qid=None, rcode=0):
    hdr = struct.pack("!HHHHHH", qid, 0x8180 | (rcode & 0xF), 1,
                      1 if (addr or txt) else 0, 0, 0)
    q = b"".join(bytes([len(l)]) + l.encode() for l in name.split(".")) + b"\x00"
    pkt = hdr + q + struct.pack("!HH", qtype, 1)
    if addr:
        pkt += b"\xc0\x0c" + struct.pack("!HHIH", 1, 1, 300, 4) + ip4(addr)
    elif txt:
        data = txt.encode()
        pkt += b"\xc0\x0c" + struct.pack("!HHHHB", 16, 1, 300, len(data) + 1,
                                         len(data)) + data
    return pkt


def http_txn(cap, sport, req, resp, seq=1000):
    cseq, sseq = seq, seq
    cap.tcp(MAC_A if sport == 49152 else WS, GW, IP_A if sport == 49152 else IP_X,
            IP_GW, sport, 80, cseq, sseq, 0x02)          # SYN
    cap.tcp(GW, MAC_A if sport == 49152 else WS, IP_GW,
            IP_A if sport == 49152 else IP_X, 80, sport, sseq, cseq + 1, 0x12)
    cseq += 1
    cap.tcp(MAC_A if sport == 49152 else WS, GW, IP_A if sport == 49152 else IP_X,
            IP_GW, sport, 80, cseq, sseq + 1, 0x10)
    cap.tcp(MAC_A if sport == 49152 else WS, GW, IP_A if sport == 49152 else IP_X,
            IP_GW, sport, 80, cseq, sseq + 1, 0x18, req.encode())
    sseq += 1
    cap.tcp(GW, MAC_A if sport == 49152 else WS, IP_GW,
            IP_A if sport == 49152 else IP_X, 80, sport, sseq, cseq + len(req), 0x18,
            resp.encode())
    cseq += len(req)
    cap.tcp(MAC_A if sport == 49152 else WS, GW, IP_A if sport == 49152 else IP_X,
            IP_GW, sport, 80, cseq, sseq + len(resp), 0x10)
    return cseq, sseq + len(resp)


HTTP_PAGES = [
    ("GET /intranet/standup HTTP/1.1\r\nHost: wiki.oe.internal\r\n\r\n",
     "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
     "standup moved to 10:15. bring your own chair. the good chairs are in lobby B.\n"),
    ("GET /intranet/printer HTTP/1.1\r\nHost: wiki.oe.internal\r\n\r\n",
     "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
     "printer-dock-4 status: out of toner (day 41). kevin's workaround stands.\n"),
    ("GET /intranet/q3-deck-draft HTTP/1.1\r\nHost: wiki.oe.internal\r\n\r\n",
     "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
     "Q3 deck draft v7 is FINANCE ONLY until Thursday. if you can read this page you are not finance. log out.\n"),
]


def main() -> None:
    os.makedirs(HANDOUT, exist_ok=True)
    out = os.path.join(HANDOUT, "office_capture_0318.pcap")
    cap = Cap()

    # ---- 08:59 — NTP-ish noise: a couple of time syncs to time.oe.internal
    for i, src in ((0, (MAC_A, IP_A)), (1, (WS, IP_X))):
        cap.udp(src[0], RESOL, src[1], IP_RESOL, 123 + i, 123, b"\x1b" + b"\x00" * 47)
    cap.wait(0.4)

    # ---- 09:00-09:05 — ordinary name lookups from ordinary workstations
    for i, (name, addr) in enumerate(NORMAL_DNS):
        cap.udp(MAC_A if i % 2 == 0 else WS, RESOL,
                IP_A if i % 2 == 0 else IP_X, IP_RESOL,
                40000 + i, 53, dns_query(name, 1, 0x2400 + i))
        cap.wait(0.11)
        cap.udp(RESOL, MAC_A if i % 2 == 0 else WS, IP_RESOL,
                IP_A if i % 2 == 0 else IP_X, 53, 40000 + i,
                dns_answer(name, addr=addr, qid=0x2400 + i))
        cap.wait(0.6)

    # ---- 09:03 — ICMP monitoring noise (the red herring)
    for seq in range(1, 5):
        cap.wait(1.0)
        cap.icmp_echo(WS, GW, IP_X, IP_GW, 0x1F4, seq,
                      b'{"probe":"dock4","rssi":-41,"ok":1}')
        cap.icmp_echo(GW, WS, IP_GW, IP_X, 0x1F4, seq,
                      b'{"probe":"dock4","rssi":-41,"ok":1}', reply=True)

    # ---- 09:06-09:09 — intranet browsing
    sport = 49152
    for req, resp in HTTP_PAGES:
        cap.wait(1.7)
        http_txn(cap, sport, req, resp)
        sport += 1

    # ---- 09:11-09:14 — the exfiltration, disguised as a poster-gen asset sync
    flag32 = b32(FLAG)
    chunks = [flag32[i:i + 16] for i in range(0, len(flag32), 16)]
    qid = 0x5100
    for i, chunk in enumerate(chunks):
        name = f"{chunk.lower()}.{EXFIL_DOMAIN}"
        cap.wait(2.3)
        cap.udp(WS, GW, IP_X, IP_RESOL, 41000 + i, 53, dns_query(name, 16, qid))
        cap.wait(0.4)
        if i == 3:  # one label trips the resolver's NXDOMAIN; retry with -2
            cap.udp(RESOL, WS, IP_RESOL, IP_X, 53, 41000 + i,
                    dns_answer(name, qtype=16, qid=qid, rcode=3))
            cap.wait(1.1)
            name = f"{chunk.lower()}-2.{EXFIL_DOMAIN}"
            cap.udp(WS, GW, IP_X, IP_RESOL, 41003, 53, dns_query(name, 16, qid))
            cap.wait(0.4)
            cap.udp(RESOL, WS, IP_RESOL, IP_X, 53, 41003,
                    dns_answer(name, txt="ok", qtype=16, qid=qid))
        else:
            cap.udp(RESOL, WS, IP_RESOL, IP_X, 53, 41000 + i,
                    dns_answer(name, txt="ok", qtype=16, qid=qid))
        qid += 1

    # ---- 09:15+ — more ordinary noise so the exfil block sits mid-stream
    for i, (name, addr) in enumerate(NORMAL_DNS[3:], start=8):
        cap.udp(MAC_A, RESOL, IP_A, IP_RESOL, 40000 + i, 53,
                dns_query(name, 1, 0x2400 + i))
        cap.wait(0.13)
        cap.udp(RESOL, MAC_A, IP_RESOL, IP_A, 53, 40000 + i,
                dns_answer(name, addr=addr, qid=0x2400 + i))
        cap.wait(0.7)
    cap.wait(1.2)
    cap.icmp_echo(WS, GW, IP_X, IP_GW, 0x1F5, 9,
                  b'{"probe":"dock4","rssi":-40,"ok":1}')

    cap.write(out)
    print(f"wrote {out}: {len(cap.pkts)} packets")


if __name__ == "__main__":
    main()
