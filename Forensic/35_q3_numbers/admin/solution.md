# q3_numbers — solution

**Flag:** `cyber_quest{h1dd3n_r0ws_c4nt_h1d3_f0r3v3r_b7f2e9}`
**Difficulty:** easy-medium

## The setup

The handout is a single xlsx workbook, `Q3_numbers.xlsx`, presented as "draft v7"
of the Q3 finance numbers. The story says the audit recon tab was deleted. It
wasn't. The whole exercise is: don't trust the spreadsheet UI — trust the file.

## Step 1 — notice the workbook is a zip

An `.xlsx` is an OOXML package. Unzip it:

```bash
unzip Q3_numbers.xlsx -d q3
```

Everything the spreadsheet app was told to hide is now plain XML.

## Step 2 — the sheet list never forgets

`xl/workbook.xml` lists **every** sheet in the workbook, including the ones the
UI does not show:

```xml
<sheet name="Q3" sheetId="1" r:id="rId1"/>
<sheet name="old_recon" sheetId="2" state="veryHidden" r:id="rId2"/>
```

`old_recon` is not `hidden` — it is `veryHidden`. Excel's Unhide dialog does not
even list veryHidden sheets, so a player who only clicks around the UI will
never see it. `openpyxl` shows the same thing:

```python
import openpyxl
wb = openpyxl.load_workbook("Q3_numbers.xlsx")
wb.sheetnames                    # ['Q3', 'old_recon']
wb["old_recon"].sheet_state      # 'veryHidden'
```

## Step 3 — the stale named range confirms it

Still in `xl/workbook.xml`:

```xml
<definedName name="Recon_FYI">'old_recon'!$C$3</definedName>
```

The name manager was never cleaned up after "the incident" — `Recon_FYI` still
points into the "deleted" tab, at `$C$3` specifically. (`Archived_FYI` is a
`#REF!` decoy: a name that really did lose its sheet.) A hidden row on the
visible Q3 sheet (rows 26–28, `hidden="1"`) and two cell comments by `k.okafor`
breadcrumb the same conclusion for players who prefer clicking to unzipping.

## Step 4 — read the sheet

`r:id="rId2"` maps to `xl/worksheets/sheet2.xml` via `xl/_rels/workbook.xml.rels`.
Its strings live in `xl/sharedStrings.xml`; cell `C3` holds:

```
cyber_quest{h1dd3n_r0ws_c4nt_h1d3_f0r3v3r_b7f2e9}
```

(Shortcut path: `strings Q3_numbers.xlsx` also surfaces it — the package is
only deflate-compressed per part — but the intended solve is reading the
package structure, not grepping.)

## Step 5 — submit

Done.
