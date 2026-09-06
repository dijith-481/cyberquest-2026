# packet_loss — solution

**Flag:** `cyber_quest{dn5_3xf1l_r34ds_l1k3_h4rm0n_l3tt3rs_2c9a71}`
**Difficulty:** medium

## The setup

`office_capture_0318.pcap` is a clean, checksum-valid capture of one morning
on 10.14.0.0/16: NTP syncs, intranet DNS, ICMP monitoring probes, and three
plain-HTTP intranet fetches. The lore is load-bearing:

- the intranet notes `printer-dock-4` is "out of toner (day 41)" with
  "kevin's workaround standing";
- the third HTTP fetch — `/intranet/q3-deck-draft` — comes from
  **10.14.7.23**, and the page's own text says that page is finance-only.

So the kiosk was where the Q3 numbers leaked from, and the answer is what
10.14.7.23 did *next*.

## Step 1 — profile the noisy host

```bash
tshark -r office_capture_0318.pcap -q -z conv,ip
# or filter directly:
tshark -r office_capture_0318.pcap -Y 'ip.src==10.14.7.23 && dns.flags.response==0'
```

The ICMP probes to the gateway are a red herring — they carry boring JSON
monitoring payloads (`{"probe":"dock4","rssi":-41,"ok":1}`), which is
precisely why they were included: "weird payloads over ICMP" should now look
*normal* on this network.

## Step 2 — the DNS that isn't DNS

Buried mid-capture, 10.14.7.23 sends a series of **TXT** lookups:

```
mn4wezlsl5yxkzlt.assets-sync.oe-cdn-demo.net
or5wi3rvl4zxqzrr.assets-sync.oe-cdn-demo.net
nrpxemzumrzv63br.assets-sync.oe-cdn-demo.net
nmzv62buojwta3s7.assets-sync.oe-cdn-demo.net   (NXDOMAIN, then retried as …s7-2)
nqzxi5btojzv6mtd.assets-sync.oe-cdn-demo.net
hfqtoml5.assets-sync.oe-cdn-demo.net
```

`oe-cdn-demo.net` is not a company domain. Each first label is a fixed-width
chunk of an alphabet of 32 characters — base32. One lookup trips the
resolver's NXDOMAIN and is retried with a `-2` suffix on the *same* label:
a retransmission, not new data, so it must not be counted twice.

## Step 3 — reassemble

Take the labels in query order (transaction IDs run 0x5100+ and never repeat),
strip the `-2` retry suffix, concatenate, base32-decode:

```python
import base64
chunks = ["mn4wezlsl5yxkzlt", "or5wi3rvl4zxqzrr", "nrpxemzumrzv63br",
          "nmzv62buojwta3s7", "nqzxi5btojzv6mtd", "hfqtoml5"]
b32 = "".join(chunks)
print(base64.b32decode(b32 + "=" * (-len(b32) % 8), casefold=True).decode())
```

```
cyber_quest{dn5_3xf1l_r34ds_l1k3_h4rm0n_l3tt3rs_2c9a71}
```

(The labels are lowercase because DNS names fold case — `casefold=True`, or
just uppercase them first.)

## Step 4 — submit

The kiosk has been told to stop syncing assets. The kiosk does not know what
assets are.
