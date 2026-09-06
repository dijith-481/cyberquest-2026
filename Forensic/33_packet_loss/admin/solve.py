#!/usr/bin/env python3
"""packet_loss — reference solve.

Simulates the documented solve path: read the pcap, collect the TXT
queries the reception kiosk (10.14.7.23) sent to the asset-sync domain,
reassemble the base32 labels in query order (dropping the -2 retry
suffix), and decode.

    python3 admin/solve.py handout/office_capture_0318.pcap
"""

import base64
import struct
import sys

EXFIL_SUFFIX = ".assets-sync.oe-cdn-demo.net"


def read_pcap(path):
    data = open(path, "rb").read()
    magic = struct.unpack("!I", data[:4])[0]
    if magic == 0xA1B2C3D4:
        endian = "!"
    elif magic == 0xD4C3B2A1:
        endian = "<"
    else:
        raise SystemExit("not a classic pcap file")
    off, pkts = 24, []
    while off < len(data):
        ts, us, cl, _ = struct.unpack(endian + "IIII", data[off:off + 16])
        off += 16
        pkts.append(data[off:off + cl])
        off += cl
    return pkts


def udp_payloads(pkts):
    for pkt in pkts:
        if pkt[12:14] != b"\x08\x00":
            continue
        ip = pkt[14:]
        ihl = (ip[0] & 0xF) * 4
        proto = ip[9]
        src = ".".join(str(b) for b in ip[12:16])
        dst = ".".join(str(b) for b in ip[16:20])
        if proto != 17:
            continue
        udp = ip[ihl:]
        sport, dport = struct.unpack("!HH", udp[:4])
        yield src, dst, sport, dport, udp[8:]


def parse_qname(payload, off=12):
    labels = []
    while payload[off]:
        n = payload[off]
        labels.append(payload[off + 1:off + 1 + n].decode())
        off += 1 + n
    return labels, off + 1


def solve(path: str) -> str:
    pkts = read_pcap(path)
    labels, qids = [], []
    seen_queries = 0
    for src, dst, sport, dport, payload in udp_payloads(pkts):
        if dport != 53:
            continue
        qid, flags, qd, an, ns, ar = struct.unpack("!HHHHHH", payload[:12])
        labels_only, qend = parse_qname(payload)
        qtype = struct.unpack("!H", payload[qend:qend + 2])[0]
        name = ".".join(labels_only)
        if not name.endswith(EXFIL_SUFFIX):
            continue
        seen_queries += 1
        chunk = name[:-len(EXFIL_SUFFIX)].split(".")[0]
        chunk = chunk.removesuffix("-2")  # the NXDOMAIN retry
        if qid in qids:
            print(f"  query #{qid:5d}  TXT  {name}  -> retry of #{qid}, skipped")
            continue
        qids.append(qid)
        labels.append((qid, chunk))
        print(f"  query #{qid:5d}  TXT  {name}  -> chunk {chunk!r}")

    if len(labels) < 5:
        raise SystemExit("did not find enough exfil labels")

    # queries all share one transaction id family; order = reassembly order
    labels.sort(key=lambda t: t[0])
    b32 = "".join(c for _, c in labels)
    flag = base64.b32decode(b32 + "=" * ((8 - len(b32) % 8) % 8),
                            casefold=True).decode()
    print(f"reassembled {len(b32)} base32 chars from {seen_queries} queries")
    print("flag:", flag)
    return flag


if __name__ == "__main__":
    print(solve(sys.argv[1] if len(sys.argv) > 1 else "handout/office_capture_0318.pcap"))
