#!/usr/bin/env python3
"""q3_numbers — deterministic handout generator.

Regenerates ../handout/Q3_numbers.xlsx. The workbook is hand-built (no
openpyxl in the build environment): it is a plain zip of OOXML parts, which
is also exactly what makes it a forensics exercise — every "deleted" thing
is still sitting in the archive.

Nothing here is secret; the solve path is documented in admin/solution.md.
"""

import os
import zipfile
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")

FLAG = "cyber_quest{h1dd3n_r0ws_c4nt_h1d3_f0r3v3r_b7f2e9}"

CT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
<Override PartName="/xl/comments1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.comments+xml"/>
<Override PartName="/xl/drawings/vmlDrawing1.vml" ContentType="application/vnd.openxmlformats-officedocument.vmlDrawing"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""

# sheet1 = Q3 (visible), sheet2 = old_recon (veryHidden)
WORKBOOK = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets>
<sheet name="Q3" sheetId="1" r:id="rId1"/>
<sheet name="old_recon" sheetId="2" state="veryHidden" r:id="rId2"/>
</sheets>
<definedNames>
<definedName name="Recon_FYI">&apos;old_recon&apos;!$C$3</definedName>
<definedName name="Archived_FYI">#REF!.$A$1</definedName>
<definedName name="Q3_Total">Q3!$C$41</definedName>
</definedNames>
</workbook>
"""

WB_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
</Relationships>
"""

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="1"><fill><patternFill patternType="none"/></fill></fills>
<borders count="1"><border/></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
</styleSheet>
"""

CORE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:title>Q3 numbers (draft v7)</dc:title>
<dc:creator>k.okafor</dc:creator>
<cp:lastModifiedBy>k.okafor</cp:lastModifiedBy>
<dcterms:created xsi:type="dcterms:W3CDTF">2026-08-30T17:12:00Z</dcterms:created>
<dcterms:modified xsi:type="dcterms:W3CDTF">2026-09-02T09:41:00Z</dcterms:modified>
</cp:coreProperties>
"""

APP = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
<Application>ordinary engineering finance build (kevin's copy)</Application>
<TitlesOfParts><vt:vector size="2" baseType="lpstr"><vt:lpstr>Q3</vt:lpstr><vt:lpstr>old_recon</vt:lpstr></vt:vector></TitlesOfParts>
</Properties>
"""


def col_letter(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


class SST:
    """Shared string table."""

    def __init__(self):
        self.strings = []
        self.index = {}

    def get(self, s: str) -> int:
        if s not in self.index:
            self.index[s] = len(self.strings)
            self.strings.append(s)
        return self.index[s]

    def xml(self) -> str:
        items = "".join(f"<si><t xml:space=\"preserve\">{escape(s)}</t></si>" for s in self.strings)
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(self.strings)}" uniqueCount="{len(self.strings)}">'
            f"{items}</sst>\n"
        )


def cell(ref: str, *, s=None, n=None, inline_comment_row=None) -> str:
    if s is not None:
        return f'<c r="{ref}" t="s"><v>{s}</v></c>'
    if n is not None:
        return f'<c r="{ref}"><v>{n}</v></c>'
    return f'<c r="{ref}"/>'


def make_q3_sheet(sst: SST):
    rows = {r: [] for r in range(1, 60)}

    def put(r, c, text=None, num=None):
        s = sst.get(text) if text is not None else None
        rows[r].append(cell(f"{col_letter(c)}{r}", s=s, n=num))

    put(1, 1, "ORDINARY ENGINEERING — Q3 NUMBERS (draft v7, do not circulate)")
    put(2, 1, "prepared by k.okafor, finance. yes, again.")
    put(3, 1, "line"); put(3, 2, "item"); put(3, 3, "amount (uu)")
    items = [
        ("imports — universe A", 412300), ("imports — universe B", 287650),
        ("imports — universe C (returned)", -19800), ("warehouse lease, dock 4", 61000),
        ("warehouse lease, dock 7 (disputed)", 61000), ("printer toner", 48912),
        ("printer toner (second try)", 48912), ("printer toner (third try)", 48912),
        ("onam logistics retainer", 95000), ("signage: 'the multiverse, probably'", 3100),
        ("all-hands catering", 8200), ("all-hands catering (no dessert)", 7400),
        ("kevin's expense line (ask finance)", 104), ("badge ceremony, deposit", 12000),
        ("desk plants (real)", 640), ("desk plants (fake)", 0),
        ("inter-universe shipping surcharge", 77510), ("qa error budget", 20000),
        ("support headcount backfill", 118000), ("depreciation, everything", 34000),
    ]
    r = 4
    for name, amt in items:
        put(r, 1, f"L{r - 3:02d}"); put(r, 2, name); put(r, 3, num=amt)
        r += 1

    # rows 26-28: hidden — kevin's private margin notes on the draft
    put(26, 1, "NOTE (row hidden so nobody panics during the readout):")
    put(26, 2, "the recon tab from the audit was never deleted. it was hidden. "
               "by kevin. during the audit. the tab is called old_recon and it "
               "is very much still in this file.")
    put(27, 1, "if legal asks: the named range Recon_FYI still points straight "
               "at it. nobody updated the name manager after 'the incident'.")
    put(28, 1, "kevin's bonus is the rounding error. that is a joke. mostly.")

    put(41, 2, "Q3 total (draft)"); put(41, 3, num=sum(a for _, a in items))
    put(42, 2, "source of truth"); put(42, 3, "=Recon_FYI (see name manager)")

    rows_xml = []
    for r in sorted(rows):
        hidden = ' hidden="1"' if r in (26, 27, 28) else ""
        cells = "".join(rows[r])
        rows_xml.append(f'<row r="{r}"{hidden}>{cells}</row>')
    body = "".join(rows_xml)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData>' + body + '</sheetData>'
        '<legacyDrawing r:id="rId1"/>'
        "</worksheet>\n"
    )


def make_recon_sheet(sst: SST):
    rows = []
    a1 = sst.get("Q3 RECON — the version finance actually used (draft v7 was for the deck)")
    b2 = sst.get("reconciled against the ledgers on 2026-09-01. total matches the draft "
                 "to the unit. the draft's rounding note was a joke. mostly.")
    c3 = sst.get(FLAG)
    c4 = sst.get("(if you are reading this, you are either an auditor or kevin's "
                 "replacement. hello either way. the flag is above, in C3.)")
    rows.append(f'<row r="1"><c r="A1" t="s"><v>{a1}</v></c></row>')
    rows.append(f'<row r="2"><c r="B2" t="s"><v>{b2}</v></c></row>')
    rows.append(f'<row r="3"><c r="C3" t="s"><v>{c3}</v></c></row>')
    rows.append(f'<row r="4"><c r="C4" t="s"><v>{c4}</v></c></row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData>' + "".join(rows) + '</sheetData>'
        "</worksheet>\n"
    )


# comments on the visible sheet — the breadcrumb trail for people who click around
def make_comments(sst: SST):
    author = "k.okafor"
    comments = [
        ("C41", "the number above matches old_recon to the unit. which old_recon, "
                "you ask. exactly. ask the name manager."),
        ("B42", "the stale Recon_FYI range is live, by the way. nobody updated it "
                "after the tab was 'deleted' during the audit. kevin typed those "
                "quotes out loud."),
    ]
    items = "".join(
        f'<comment ref="{ref}" authorId="0"><text><r><t>{escape(text)}</t></r></text></comment>'
        for ref, text in comments
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<comments xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<authors><author>{author}</author></authors>'
        f'<commentList>{items}</commentList></comments>\n'
    )


VML = """<xml xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
<o:shapelayout v:ext="edit"><o:idmap v:ext="edit" data="1"/></o:shapelayout>
<v:shapetype id="_x0000_t202" coordsize="21600,21600" o:spt="202" path="m,l,21600r21600,l21600,xe">
<v:stroke joinstyle="miter"/><v:path gradientshapeok="t" o:connecttype="rect"/>
</v:shapetype>
<v:shape id="_x0000_s1025" type="#_x0000_t202" style="position:absolute;margin-left:100pt;width:150pt;height:60pt;z-index:1" fillcolor="#ffffe1">
<v:fill o:detectmouseclick="t"/><v:shadow on="t"/>
</v:shape>
<v:shape id="_x0000_s1026" type="#_x0000_t202" style="position:absolute;margin-left:120pt;width:150pt;height:60pt;z-index:2" fillcolor="#ffffe1">
<v:fill o:detectmouseclick="t"/><v:shadow on="t"/>
</v:shape>
</xml>
"""

SHEET1_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/vmlDrawing" Target="../drawings/vmlDrawing1.vml"/>
</Relationships>
"""


def main() -> None:
    os.makedirs(HANDOUT, exist_ok=True)
    out = os.path.join(HANDOUT, "Q3_numbers.xlsx")

    sst = SST()
    sheet1 = make_q3_sheet(sst)
    sheet2 = make_recon_sheet(sst)

    parts = [
        ("[Content_Types].xml", CT),
        ("_rels/.rels", RELS),
        ("docProps/core.xml", CORE),
        ("docProps/app.xml", APP),
        ("xl/workbook.xml", WORKBOOK),
        ("xl/_rels/workbook.xml.rels", WB_RELS),
        ("xl/styles.xml", STYLES),
        ("xl/sharedStrings.xml", sst.xml()),
        ("xl/worksheets/sheet1.xml", sheet1),
        ("xl/worksheets/sheet2.xml", sheet2),
        ("xl/worksheets/_rels/sheet1.xml.rels", SHEET1_RELS),
        ("xl/comments1.xml", make_comments(sst)),
        ("xl/drawings/vmlDrawing1.vml", VML),
    ]

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in parts:
            z.writestr(name, data)
    print("wrote", os.path.normpath(out))


if __name__ == "__main__":
    main()
