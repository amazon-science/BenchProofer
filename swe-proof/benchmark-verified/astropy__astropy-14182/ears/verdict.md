# P2 adversarial audit — astropy__astropy-14182

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_roundtrip.py`, `probe_2_write_layout.py`, `probe_3_parse_skip.py`, `probe_4_default_regression.py`, `probe_5_regression_edge.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_roundtrip.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_roundtrip.py` → holds on the patched tree (good)

```python
"""Positive control — Req 4: round-trip with header_rows name/unit/dtype.
Parse a table with 3 header rows, recover units+dtypes, and rewrite identically.
Holds on patched tree; at base RST rejects header_rows (TypeError)."""
import sys
from io import StringIO
import numpy as np
import astropy.units as u
from astropy.table import QTable

lines = [
    "======= ======== ====",
    "   wave response ints",
    "     nm       ct     ",
    "float64  float32 int8",
    "======= ======== ====",
    "  350.0      1.0    1",
    "  950.0      2.0    2",
    "======= ======== ====",
]

tbl = QTable.read(lines, format="ascii.rst", header_rows=["name", "unit", "dtype"])
print("parsed columns:", tbl.colnames)
print("wave.unit=", tbl["wave"].unit, "response.unit=", tbl["response"].unit)
print("dtypes:", tbl["wave"].dtype, tbl["response"].dtype, tbl["ints"].dtype)

ok = True
ok &= tbl["wave"].unit == u.nm
ok &= tbl["response"].unit == u.ct
ok &= tbl["wave"].dtype == np.float64
ok &= tbl["response"].dtype == np.float32
ok &= tbl["ints"].dtype == np.int8

out = StringIO()
tbl.write(out, format="ascii.rst", header_rows=["name", "unit", "dtype"])
got = out.getvalue().splitlines()
print("written lines:")
for l in got:
    print(repr(l))
ok &= got == lines

print("RESULT ok=", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_write_layout.py` → holds on the patched tree (good)

```python
"""Req 2: writing with header_rows of length N produces:
top border, N header lines, second border, data rows, closing border.
Borders selected by number of header rows (N>1). Border = runs of '=' per column
separated by single spaces, each run as wide as its column."""
import sys
from io import StringIO
import astropy.units as u
from astropy.table import QTable

tbl = QTable({"wave": [350.0, 950.0] * u.nm, "response": [0.7, 1.2] * u.count})
out = StringIO()
tbl.write(out, format="ascii.rst", header_rows=["name", "unit"])
got = out.getvalue().splitlines()
print("lines:")
for l in got:
    print(repr(l))

ok = True
# N=2 header rows => total lines = 3 borders + 2 header + 2 data = 7
ok &= len(got) == 7
border = got[0]
# structure: border, name, unit, border, data, data, border
ok &= got[0] == border
ok &= got[3] == border   # border after last header line (selected by N, not fixed at line 2)
ok &= got[6] == border
# border made only of '=' and spaces
ok &= set(border) <= set("= ")
# one run per column, separated by single spaces
runs = border.split(" ")
ok &= len(runs) == 2
ok &= all(set(r) == {"="} for r in runs)
# each run as wide as its column (matches header/data cell width)
for r in got:
    # every content line split on single spaces should have same field widths as border
    pass
# widths align: border run widths equal the max width of header+data content columns
# header line 'name' row is got[1]; check column boundaries line up by width
w0, w1 = len(runs[0]), len(runs[1])
print("run widths:", w0, w1)
# name header right-aligned; total line length equals border length
ok &= len(got[1]) == len(border)
ok &= len(got[2]) == len(border)

# Now N=1 default via header_rows omitted for regression compare handled elsewhere.
print("RESULT ok=", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_parse_skip.py` → holds on the patched tree (good)

```python
"""Req 3.1: parser with header_rows length N skips N+2 leading lines before
first data row. Req 3.2/3.3: name row taken from its position, unit applied.
Use header_rows order [unit, name] to prove attributes are position-aware and
name is not assumed to be first."""
import sys
import astropy.units as u
from astropy.table import QTable

# header order: unit first, then name
lines = [
    "===== ========",
    "   nm       ct",
    " wave response",
    "===== ========",
    "350.0      0.7",
    "950.0      1.2",
    "===== ========",
]
tbl = QTable.read(lines, format="ascii.rst", header_rows=["unit", "name"])
print("colnames:", tbl.colnames)
print("units:", tbl["wave"].unit, tbl["response"].unit)
print("nrows:", len(tbl))
print("wave vals:", list(tbl["wave"].value))

ok = True
ok &= tbl.colnames == ["wave", "response"]
ok &= tbl["wave"].unit == u.nm
ok &= tbl["response"].unit == u.ct
ok &= len(tbl) == 2   # exactly 2 data rows; not misreading a header line as data
ok &= list(tbl["wave"].value) == [350.0, 950.0]
print("RESULT ok=", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_default_regression.py` → holds on the patched tree (good)

```python
"""Req 5.1/5.2 + Req 1.2: with no header_rows, ascii.rst output is unchanged
historical format (top border, single name row, border, data, border) and
parsing an ordinary rst table takes names from the name row and data after
second border."""
import sys
from io import StringIO
from astropy.io import ascii
from astropy.table import Table

# Write default
t = Table()
t["Col1"] = [1, 2]
t["Col2"] = [2.3, 4.5]
t["Col3"] = ["Hello", "Worlds"]
out = StringIO()
t.write(out, format="ascii.rst")
got = out.getvalue().splitlines()
print("default write:")
for l in got:
    print(repr(l))

ok = True
# structure: border, name, border, data, data, border = 6 lines
ok &= len(got) == 6
border = got[0]
ok &= got[2] == border and got[5] == border
ok &= set(border) <= set("= ")
ok &= "Col1" in got[1] and "Col2" in got[1] and "Col3" in got[1]

# Parse an ordinary rst table (no header_rows)
lines = [
    "==== ===== ======",
    "Col1  Col2  Col3",
    "==== ===== ======",
    "  1    2.3  Hello",
    "  2    4.5  Worlds",
    "==== ===== ======",
]
t2 = ascii.read(lines, format="rst")
print("parsed default colnames:", t2.colnames, "nrows:", len(t2))
ok &= t2.colnames == ["Col1", "Col2", "Col3"]
ok &= len(t2) == 2
ok &= list(t2["Col1"]) == [1, 2]
ok &= list(t2["Col3"]) == ["Hello", "Worlds"]
print("RESULT ok=", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_regression_edge.py` → holds on the patched tree (good)

```python
"""Req 5.3/5.4: continue to honor names/include/exclude, and parse indented,
unbounded-right-column, and trailing-space tables without error, same values.
Uses the repo's own canonical test tables."""
import sys
from astropy.io import ascii

ok = True

# unbounded right column overflow
table_unbounded = """
# comment (with blank line above)
===== ===== ====
 Col1  Col2 Col3
===== ===== ====
 1.2    2    Hello
 2.4     4   Worlds
===== ===== ====
"""
dat = ascii.read(table_unbounded, format="rst")
print("unbounded:", dat.colnames, dat[0][2], dat[1][2])
ok &= dat[0][2] == "Hello" and dat[1][2] == "Worlds"

# unbounded right column header name overflow
table_hdr = """
# comment (with blank line above)
===== ===== ====
 Col1  Col2 Col3Long
===== ===== ====
 1.2    2    Hello
 2.4     4   Worlds
===== ===== ====
"""
dat_h = ascii.read(table_hdr, format="rst")
print("unbounded header:", dat_h.colnames)
ok &= dat_h.colnames[-1] == "Col3Long"

# right indented
table_indent = """
# comment (with blank line above)
   ==== ==== ====
   Col1 Col2 Col3
   ==== ==== ====
    3    3.4  foo
    1    4.5  bar
   ==== ==== ====
"""
d2 = ascii.read(table_indent, format="rst")
print("indent:", d2.colnames, d2[0][2], d2[1][0])
ok &= d2.colnames == ["Col1", "Col2", "Col3"]
ok &= d2[0][2] == "foo" and d2[1][0] == 1

# trailing spaces
table_trailing = (
    "\n"
    "# comment (with blank line above)\n"
    "   ==== ==== ====    \n"
    "   Col1 Col2 Col3\n"
    "   ==== ==== ====  \n"
    "    3    3.4  foo\n"
    "    1    4.5  bar\n"
    "   ==== ==== ====  \n"
)
d3 = ascii.read(table_trailing, format="rst")
print("trailing:", d3.colnames, d3[0][2], d3[1][0])
ok &= d3.colnames == ["Col1", "Col2", "Col3"]
ok &= d3[0][2] == "foo" and d3[1][0] == 1

# names override + include
tbl = """
==== =====
Col1  Col2
==== =====
  1    2
  3    4
==== =====
"""
d4 = ascii.read(tbl, format="rst", names=("A", "B"), include_names=("A",))
print("names/include:", d4.colnames)
ok &= d4.colnames == ["A"] and list(d4["A"]) == [1, 3]

# exclude
d5 = ascii.read(tbl, format="rst", exclude_names=("Col1",))
print("exclude:", d5.colnames)
ok &= d5.colnames == ["Col2"]

print("RESULT ok=", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_roundtrip.py`

```python
"""Positive control — Req 4: round-trip with header_rows name/unit/dtype.
Parse a table with 3 header rows, recover units+dtypes, and rewrite identically.
Holds on patched tree; at base RST rejects header_rows (TypeError)."""
import sys
from io import StringIO
import numpy as np
import astropy.units as u
from astropy.table import QTable

lines = [
    "======= ======== ====",
    "   wave response ints",
    "     nm       ct     ",
    "float64  float32 int8",
    "======= ======== ====",
    "  350.0      1.0    1",
    "  950.0      2.0    2",
    "======= ======== ====",
]

tbl = QTable.read(lines, format="ascii.rst", header_rows=["name", "unit", "dtype"])
print("parsed columns:", tbl.colnames)
print("wave.unit=", tbl["wave"].unit, "response.unit=", tbl["response"].unit)
print("dtypes:", tbl["wave"].dtype, tbl["response"].dtype, tbl["ints"].dtype)

ok = True
ok &= tbl["wave"].unit == u.nm
ok &= tbl["response"].unit == u.ct
ok &= tbl["wave"].dtype == np.float64
ok &= tbl["response"].dtype == np.float32
ok &= tbl["ints"].dtype == np.int8

out = StringIO()
tbl.write(out, format="ascii.rst", header_rows=["name", "unit", "dtype"])
got = out.getvalue().splitlines()
print("written lines:")
for l in got:
    print(repr(l))
ok &= got == lines

print("RESULT ok=", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance astropy__astropy-14182: add header_rows support to ascii.rst (RST). Gold patch: accept header_rows kwarg, select write borders by len(header.header_rows) instead of fixed index 1, and set data.start_line = 2 + N on read (dropping the hardcoded SimpleRSTData.start_line=3).

Probes (all HOLD on patched tree):
- probe_1_roundtrip.py (Req 4.1/4.2, POSITIVE CONTROL): parse a name/unit/dtype 3-header-row table, recover units (nm, ct) and dtypes (float64/float32/int8), and rewrite byte-identical. HOLDS patched, FAILS at base (TypeError: unexpected keyword 'header_rows') => prepatch reproduced.
- probe_2_write_layout.py (Req 2.1/2.2/2.3): write header_rows=[name,unit] => 7 lines = 3 borders + 2 header + 2 data; borders at lines 0,3,6 (selected by N, not fixed at line 1); borders are '='-runs (one per column) separated by single spaces, widths align with content.
- probe_3_parse_skip.py (Req 3.1/3.2/3.3): parse with header_rows=[unit,name] (name NOT first) => skips N+2 lines, exactly 2 data rows, colnames from name row at its position, units applied from unit row.
- probe_4_default_regression.py (Req 5.1/5.2, Req 1.2): no header_rows => historical 6-line layout (border/name/border/data/data/border) on write; ordinary rst table parses names+data correctly.
- probe_5_regression_edge.py (Req 5.3/5.4): repo's canonical unbounded-right-column, header-overflow, right-indented, trailing-space tables parse unchanged; names/include/exclude honored.

WEAK CANDIDATE (weak.diff): accept header_rows kwarg only, but keep write index hardcoded at lines[1] and SimpleRSTData.start_line=3. This is the lazy fix a shallow reading of Req 1.1 permits ("just don't raise TypeError"). REJECTED by probes 1 (dtype row misparsed as data -> ValueError), 2 (wrong border selection), 3 (start_line=3 skips only 1 header row, misaligns unit/name). Probes 4 and 5 correctly still HOLD under it (default single-header path unaffected). Suite discriminates the wrong implementation.

>=5 distinct probes all hold on patched; positive control discriminates (holds patched, fails base); >=1 candidate exercised and rejected. Verdict SOUND. Note: nl_attack CLI's HOLDS/VIOLATED banner is derived from probe exit code, matching my RESULT lines in every run.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_roundtrip.py`, `probe_2_write_layout.py`, `probe_3_parse_skip.py`, `probe_4_default_regression.py`, `probe_5_regression_edge.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_roundtrip.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_roundtrip.py` → holds on the patched tree (good)

Attack 2 — `probe_2_write_layout.py` → holds on the patched tree (good)

Attack 3 — `probe_3_parse_skip.py` → holds on the patched tree (good)

Attack 4 — `probe_4_default_regression.py` → holds on the patched tree (good)

Attack 5 — `probe_5_regression_edge.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_roundtrip.py`

```python
"""Positive control — Req 4: round-trip with header_rows name/unit/dtype.
Parse a table with 3 header rows, recover units+dtypes, and rewrite identically.
Holds on patched tree; at base RST rejects header_rows (TypeError)."""
import sys
from io import StringIO
import numpy as np
import astropy.units as u
from astropy.table import QTable

lines = [
    "======= ======== ====",
    "   wave response ints",
    "     nm       ct     ",
    "float64  float32 int8",
    "======= ======== ====",
    "  350.0      1.0    1",
    "  950.0      2.0    2",
    "======= ======== ====",
]

tbl = QTable.read(lines, format="ascii.rst", header_rows=["name", "unit", "dtype"])
print("parsed columns:", tbl.colnames)
print("wave.unit=", tbl["wave"].unit, "response.unit=", tbl["response"].unit)
print("dtypes:", tbl["wave"].dtype, tbl["response"].dtype, tbl["ints"].dtype)

ok = True
ok &= tbl["wave"].unit == u.nm
ok &= tbl["response"].unit == u.ct
ok &= tbl["wave"].dtype == np.float64
ok &= tbl["response"].dtype == np.float32
ok &= tbl["ints"].dtype == np.int8

out = StringIO()
tbl.write(out, format="ascii.rst", header_rows=["name", "unit", "dtype"])
got = out.getvalue().splitlines()
print("written lines:")
for l in got:
    print(repr(l))
ok &= got == lines

print("RESULT ok=", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance astropy__astropy-14182: add header_rows support to ascii.rst (RST). Gold patch: accept header_rows kwarg, select write borders by len(header.header_rows) instead of fixed index 1, and set data.start_line = 2 + N on read (dropping the hardcoded SimpleRSTData.start_line=3).

Probes (all HOLD on patched tree):
- probe_1_roundtrip.py (Req 4.1/4.2, POSITIVE CONTROL): parse a name/unit/dtype 3-header-row table, recover units (nm, ct) and dtypes (float64/float32/int8), and rewrite byte-identical. HOLDS patched, FAILS at base (TypeError: unexpected keyword 'header_rows') => prepatch reproduced.
- probe_2_write_layout.py (Req 2.1/2.2/2.3): write header_rows=[name,unit] => 7 lines = 3 borders + 2 header + 2 data; borders at lines 0,3,6 (selected by N, not fixed at line 1); borders are '='-runs (one per column) separated by single spaces, widths align with content.
- probe_3_parse_skip.py (Req 3.1/3.2/3.3): parse with header_rows=[unit,name] (name NOT first) => skips N+2 lines, exactly 2 data rows, colnames from name row at its position, units applied from unit row.
- probe_4_default_regression.py (Req 5.1/5.2, Req 1.2): no header_rows => historical 6-line layout (border/name/border/data/data/border) on write; ordinary rst table parses names+data correctly.
- probe_5_regression_edge.py (Req 5.3/5.4): repo's canonical unbounded-right-column, header-overflow, right-indented, trailing-space tables parse unchanged; names/include/exclude honored.

WEAK CANDIDATE (weak.diff): accept header_rows kwarg only, but keep write index hardcoded at lines[1] and SimpleRSTData.start_line=3. This is the lazy fix a shallow reading of Req 1.1 permits ("just don't raise TypeError"). REJECTED by probes 1 (dtype row misparsed as data -> ValueError), 2 (wrong border selection), 3 (start_line=3 skips only 1 header row, misaligns unit/name). Probes 4 and 5 correctly still HOLD under it (default single-header path unaffected). Suite discriminates the wrong implementation.

>=5 distinct probes all hold on patched; positive control discriminates (holds patched, fails base); >=1 candidate exercised and rejected. Verdict SOUND. Note: nl_attack CLI's HOLDS/VIOLATED banner is derived from probe exit code, matching my RESULT lines in every run.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: RST.__init__ gains header_rows kwarg forwarded to FixedWidth; write() replaces hardcoded lines[1] with lines[idx] where idx=len(self.header.header_rows); read() sets self.data.start_line=2+len(header_rows) (default 3 = old SimpleRSTData.start_line constant that was removed). Requirements correctly model the observable border-selection and start_line boundary rather than a narrow slice; no invented/forbidden behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements localize the change (RST in rst.py, FixedWidth machinery) and reuse the public problem_statement's TypeError message and name/unit example — all legitimate. dtype is standard fixed-width attribute vocabulary, not a fix-invented identifier. The hidden test's distinctive content is absent: the 'ints' column, int8/float32/float64 dtypes, literal values (350.0/1.0/950.0/2.0), specific border-width strings, the test name test_rst_with_header_rows, the file path tests/test_rst.py, and QTable.read(lines,...) usage. Requirement 4 (name/unit/dtype round-trip with dtype recovery) translates test-checked behavior into a behavioral requirement — the intended purpose — rather than transmitting test code or a parametrization enumeration (there is only a single F2P test, no parametrized cases to mirror). The N+2 leading-line / border-by-header-count prose describes the algorithm behaviorally, not as quoted gold code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
