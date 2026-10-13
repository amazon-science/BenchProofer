# P2 adversarial audit — astropy__astropy-13453

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control: Req1.2 - format-spec string honored in HTML <td> cells.
Holds iff the formatted string '1.24' (from '{:.2f}' on 1.23456) appears in output
and the raw '1.23456' does not."""
import io
from astropy.table import Table

t = Table([[1.23456, 2.34567]], names=["a"])
buf = io.StringIO()
t.write(buf, format="html", formats={"a": "{:.2f}"})
out = buf.getvalue()
print(out)
ok = ("<td>1.23</td>" in out) and ("<td>2.35</td>" in out) and ("1.23456" not in out)
print("formatted-present:", "<td>1.23</td>" in out, "raw-absent:", "1.23456" not in out)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.3 - callable format honored in HTML <td> cells."""
import io
from astropy.table import Table

t = Table([[1.0, 2.0]], names=["a"])
buf = io.StringIO()
t.write(buf, format="html", formats={"a": lambda x: f"V={x:.1f}"})
out = buf.getvalue()
print(out)
ok = ("<td>V=1.0</td>" in out) and ("<td>V=2.0</td>" in out)
print("callable applied:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.4 - column not named in formats is unchanged; Req1.1 - only named col affected."""
import io
from astropy.table import Table

t = Table([[1.23456, 2.34567], [3.45678, 4.56789]], names=["a", "b"])
buf = io.StringIO()
t.write(buf, format="html", formats={"a": "{:.2f}"})
out = buf.getvalue()
print(out)
# a formatted
a_ok = "<td>1.23</td>" in out and "<td>2.35</td>" in out
# b unchanged: full-precision default repr present
b_ok = "3.45678" in out and "4.56789" in out
print("a formatted:", a_ok, "b unchanged:", b_ok)
raise SystemExit(0 if (a_ok and b_ok) else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req1.5 - HTML formatted values equal what CSV writer produces for same value+format."""
import io
from astropy.table import Table

t = Table([[1.23456, 2.99999]], names=["a"])

hbuf = io.StringIO()
t.write(hbuf, format="html", formats={"a": "{:.3f}"})
hout = hbuf.getvalue()

cbuf = io.StringIO()
t.write(cbuf, format="csv", formats={"a": "{:.3f}"})
cvals = [ln.strip() for ln in cbuf.getvalue().splitlines()[1:]]  # skip header
print("csv vals:", cvals)
print(hout)
ok = all(f"<td>{v}</td>" in hout for v in cvals)
print("html matches csv:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.1/3.2 - fill_values still applied together with formats (regression).
fill_values matches against the (formatted) string value; ensure both work together."""
import io
from astropy.table import Table

t = Table([[1.5, 2.5]], names=["a"])
buf = io.StringIO()
# format 1.5->'1.5','2.5'; then fill substitution replaces formatted '1.5' with 'ONE'
t.write(buf, format="html", formats={"a": "{:.1f}"}, fill_values=[("1.5", "ONE")])
out = buf.getvalue()
print(out)
fill_ok = "<td>ONE</td>" in out           # fill substitution happened on formatted value
fmt_ok = "<td>2.5</td>" in out            # other value formatted, not filled
print("fill applied:", fill_ok, "format applied:", fmt_ok)
raise SystemExit(0 if (fill_ok and fmt_ok) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req2.1/2.3 - structure preserved; no-formats output has full doc structure and raw values."""
import io
from astropy.table import Table

t = Table([[1.23456, 2.34567]], names=["a"])
buf = io.StringIO()
t.write(buf, format="html")
out = buf.getvalue()
print(out)
struct = all(tag in out for tag in ["<html", "<head>", "<body>", "<table", "<thead>", "<th>a</th>"])
raw = "1.23456" in out and "2.34567" in out
# two data rows
nrows = out.count("<tr>") == 3  # 1 header row + 2 data rows
print("struct:", struct, "raw values:", raw, "rows:", out.count("<tr>"))
raise SystemExit(0 if (struct and raw and nrows) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: Req1.2 - format-spec string honored in HTML <td> cells.
Holds iff the formatted string '1.24' (from '{:.2f}' on 1.23456) appears in output
and the raw '1.23456' does not."""
import io
from astropy.table import Table

t = Table([[1.23456, 2.34567]], names=["a"])
buf = io.StringIO()
t.write(buf, format="html", formats={"a": "{:.2f}"})
out = buf.getvalue()
print(out)
ok = ("<td>1.23</td>" in out) and ("<td>2.35</td>" in out) and ("1.23456" not in out)
print("formatted-present:", "<td>1.23</td>" in out, "raw-absent:", "1.23456" not in out)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: HTML writer must apply the supplied per-column `formats` mapping (astropy-13453). Gold patch adds `self.data.cols = cols` and `self.data._set_col_formats()` in HTML.write.

Probes (all run on patched tree; conda python from swebench-lean env):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): format-spec string '{:.2f}' on col a -> <td>1.23</td>/<td>2.35</td>, raw '1.23456' absent. HOLDS patched; FAILS at base (base emits raw 1.23456). Discriminates.
- probe_2 (Req1.3): callable format lambda x: f'V={x:.1f}' -> <td>V=1.0</td>. HOLDS patched.
- probe_3 (Req1.4/1.1): named col a formatted, unnamed col b keeps full-precision default (3.45678/4.56789 present). HOLDS patched.
- probe_4 (Req1.5): HTML formatted values byte-equal to CSV writer output for same value+format ('{:.3f}': 1.235/3.000). HOLDS patched.
- probe_5 (Req3.1/3.2): fill_values substitution ('1.5'->'ONE') applied on top of format '{:.1f}', other value ('2.5') formatted not filled. HOLDS patched. (Initial version was buggy - masked entries render as empty <td>, not '--'; corrected to match fill_values against formatted string.)
- probe_6 (Req2.1/2.3): no-formats output retains full <html>/<head>/<body>/<table>/<thead> structure, header cell <th>a</th>, 1 header + 2 data rows, raw values present. HOLDS patched.

Candidate wrong-fix patches (both REJECTED by suite):
- weak.diff: adds _set_col_formats() call but forgets `self.data.cols = cols` (the lazy 1-line fix). AttributeError: 'HTMLData' object has no attribute 'cols' -> crashes ALL 6 probes. REJECTED.
- weak2.diff: sets self.data.cols and honors only STRING format specs, ignoring callables (a plausible partial reading of Req1). probe_2 (callable) VIOLATED (exit 1); other probes hold. REJECTED by the callable-format probe.

Both candidates rejected => suite discriminates wrong implementations. All 6 probes hold on the gold-patched tree; positive control (probe_1) holds patched and fails at base (prepatch_reproduced=true). No violation or too-weak finding. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: Req1.2 - format-spec string honored in HTML <td> cells.
Holds iff the formatted string '1.24' (from '{:.2f}' on 1.23456) appears in output
and the raw '1.23456' does not."""
import io
from astropy.table import Table

t = Table([[1.23456, 2.34567]], names=["a"])
buf = io.StringIO()
t.write(buf, format="html", formats={"a": "{:.2f}"})
out = buf.getvalue()
print(out)
ok = ("<td>1.23</td>" in out) and ("<td>2.35</td>" in out) and ("1.23456" not in out)
print("formatted-present:", "<td>1.23</td>" in out, "raw-absent:", "1.23456" not in out)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: HTML writer must apply the supplied per-column `formats` mapping (astropy-13453). Gold patch adds `self.data.cols = cols` and `self.data._set_col_formats()` in HTML.write.

Probes (all run on patched tree; conda python from swebench-lean env):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): format-spec string '{:.2f}' on col a -> <td>1.23</td>/<td>2.35</td>, raw '1.23456' absent. HOLDS patched; FAILS at base (base emits raw 1.23456). Discriminates.
- probe_2 (Req1.3): callable format lambda x: f'V={x:.1f}' -> <td>V=1.0</td>. HOLDS patched.
- probe_3 (Req1.4/1.1): named col a formatted, unnamed col b keeps full-precision default (3.45678/4.56789 present). HOLDS patched.
- probe_4 (Req1.5): HTML formatted values byte-equal to CSV writer output for same value+format ('{:.3f}': 1.235/3.000). HOLDS patched.
- probe_5 (Req3.1/3.2): fill_values substitution ('1.5'->'ONE') applied on top of format '{:.1f}', other value ('2.5') formatted not filled. HOLDS patched. (Initial version was buggy - masked entries render as empty <td>, not '--'; corrected to match fill_values against formatted string.)
- probe_6 (Req2.1/2.3): no-formats output retains full <html>/<head>/<body>/<table>/<thead> structure, header cell <th>a</th>, 1 header + 2 data rows, raw values present. HOLDS patched.

Candidate wrong-fix patches (both REJECTED by suite):
- weak.diff: adds _set_col_formats() call but forgets `self.data.cols = cols` (the lazy 1-line fix). AttributeError: 'HTMLData' object has no attribute 'cols' -> crashes ALL 6 probes. REJECTED.
- weak2.diff: sets self.data.cols and honors only STRING format specs, ignoring callables (a plausible partial reading of Req1). probe_2 (callable) VIOLATED (exit 1); other probes hold. REJECTED by the callable-format probe.

Both candidates rejected => suite discriminates wrong implementations. All 6 probes hold on the gold-patched tree; positive control (probe_1) holds patched and fails at base (prepatch_reproduced=true). No violation or too-weak finding. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed on gold-patched image: (1) callable format {'a': lambda x: f'{x:.2e}'} yields <td>1.24e-24</td> (Req1.3); (2) string spec {'a':'.2e'} yields same (Req1.2); (3) unnamed column 'b' unchanged as <td>2</td> (Req1.4); (4) full <html>/<head>/<body>/<table>/<thead>/<th> structure preserved (Req2.1-2.2); (5) HTML format string matches CSV output '1.24e-24' (Req1.5); (6) formats + fill_values both applied together -> <td>MISSING</td> with '.1f' format (Req3.1-3.2). Base (unpatched) violates: 'callable format not applied' assertion fails, confirming boundary is on the changed behavior not a subset. Req3.3-3.5 (byte-identical without formats, multicol, other options, dimensionality reject) are regression-preservation claims consistent with the minimal 2-line patch that only adds format assignment before rendering.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix behaviorally: the HTML writer must honor the `formats` mapping (format-spec strings and callables) exactly like other ASCII writers, leave unnamed columns on their existing info.format, and preserve document structure and existing features. All of this is derivable from the PUBLIC problem_statement, which already exhibits the 'a'/'b' table, lambda callable format, and the CSV/RST parity behavior. 

No hidden-test content is transmitted: none of the test-specific identifiers (test_write_table_formatted_columns, column names 'C1'/'C2', the format specs '04d'/'.2e', the literal values 1.234567e-11 / -9.876543e11, or the expected `<td>0001</td>` / `<td>1.23e-11</td>` output) appear in requirements.md. The document never quotes the expected HTML string or gold values.

Naming `astropy/io/ascii/html.py`, the `HTML`/`HTMLData` classes, `info.format`, `fill_values`, and the `multicol` option is legitimate localization of the change — these are pre-existing public code entities, and Requirement 3's regression list (fill_values, masked, multicol, raw-HTML, CSS/JS/id/class) tracks existing writer features rather than reconstructing the FAIL_TO_PASS test. The gold-patch identifier `_set_col_formats` is NOT surfaced in the prose. Requirement 5's 'same string the other ASCII writers produce' restates the public issue's CSV/RST comparison, not a hidden gold value. No enumeration mirrors a test parametrization (the F2P test is a single non-parametrized case).


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
