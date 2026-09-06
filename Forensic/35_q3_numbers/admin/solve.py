#!/usr/bin/env python3
"""q3_numbers — reference solve.

Simulates the documented solve path: parse the OOXML package, find the
veryHidden sheet via workbook.xml, resolve the stale Recon_FYI defined name,
and read the flag out of that sheet.

    python3 admin/solve.py handout/Q3_numbers.xlsx
"""

import re
import sys
import zipfile

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def solve(path: str) -> str:
    z = zipfile.ZipFile(path)
    wb = z.read("xl/workbook.xml").decode()

    sheets = re.findall(r'<sheet name="([^"]+)"[^>]*state="([^"]+)"', wb) + [
        (m, "visible")
        for m in re.findall(r'<sheet name="([^"]+)"(?![^>]*state=)[^>]*>', wb)
    ]
    hidden = [(n, s) for n, s in sheets if s != "visible"]
    print("sheets:", sheets)
    if not hidden:
        raise SystemExit("no hidden sheets found")

    import html
    names = {k: html.unescape(v) for k, v in
             re.findall(r'<definedName name="([^"]+)">(.*?)</definedName>', wb)}
    print("defined names:", names)
    target = re.search(r"'?old_recon'?!\$C\$3", names.get("Recon_FYI", ""))
    if not target:
        raise SystemExit("Recon_FYI does not point at old_recon!$C$3")

    # rId -> sheet part
    rels = z.read("xl/_rels/workbook.xml.rels").decode()
    rid = re.search(r'<sheet name="old_recon"[^>]*r:id="(rId\d+)"', wb).group(1)
    part = re.search(rf'Id="{rid}"[^>]*Target="([^"]+)"', rels).group(1)
    part = "xl/" + part.lstrip("/xl/")

    sheet = z.read(part).decode()
    c3 = re.search(r'<c r="C3"[^>]*t="s"[^>]*><v>(\d+)</v>', sheet)
    sst = z.read("xl/sharedStrings.xml").decode()
    strings = ["".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S))
               for si in re.findall(r"<si>.*?</si>", sst, re.S)]
    flag = strings[int(c3.group(1))]
    print(f"old_recon!C3 = {flag}")
    return flag


if __name__ == "__main__":
    print(solve(sys.argv[1] if len(sys.argv) > 1 else "handout/Q3_numbers.xlsx"))
