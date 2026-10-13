# P2 adversarial audit — pytest-dev__pytest-7521

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1_cr.py`, `probe_2_crlf.py`, `probe_3_verbatim.py`, `probe_4_lf.py`, `probe_5_utf8replace.py`, `probe_6_mode_writethrough.py`, `probe_7_suspend_resume.py`, `probe_8_binary.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_cr.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_cr.py` → holds on the patched tree (good)

```python
# Requirement 1.1 / 1.4 (POSITIVE CONTROL): a trailing '\r' written to a
# captured fd must be returned verbatim (not rewritten to '\n').
import os, tempfile
import _pytest.capture as cap

# use a scratch OS file descriptor as the capture target
scratch = tempfile.TemporaryFile()
targetfd = scratch.fileno()

c = cap.FDCapture(targetfd)
c.start()
os.write(targetfd, b"line\r")
os.fsync(targetfd) if False else None
got = c.snap()
c.done()
scratch.close()

print("wrote=%r got=%r" % ("line\r", got))
ok = got == "line\r"
if not ok:
    print("VIOLATION: expected trailing CR preserved, got %r" % got)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2_crlf.py` → holds on the patched tree (good)

```python
# Requirement 1.2: trailing '\r\n' preserved verbatim (both chars, in order).
import os, tempfile
import _pytest.capture as cap
scratch = tempfile.TemporaryFile(); fd = scratch.fileno()
c = cap.FDCapture(fd); c.start()
os.write(fd, b"line\r\n")
got = c.snap(); c.done(); scratch.close()
print("wrote=%r got=%r" % ("line\r\n", got))
ok = got == "line\r\n"
if not ok: print("VIOLATION: CRLF not preserved, got %r" % got)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3_verbatim.py` → holds on the patched tree (good)

```python
# Requirement 1.3: same code points, same order, no drop/insert/merge/rewrite.
import os, tempfile
import _pytest.capture as cap
s = "a\rb\r\nc\r\rd\ne\r"
data = s.encode("utf-8")
scratch = tempfile.TemporaryFile(); fd = scratch.fileno()
c = cap.FDCapture(fd); c.start()
os.write(fd, data)
got = c.snap(); c.done(); scratch.close()
print("wrote=%r got=%r" % (s, got))
ok = got == s
if not ok: print("VIOLATION: readback not verbatim")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4_lf.py` → holds on the patched tree (good)

```python
# Requirement 2.1 (SHALL keep): bare '\n' returned unchanged.
import os, tempfile
import _pytest.capture as cap
scratch = tempfile.TemporaryFile(); fd = scratch.fileno()
c = cap.FDCapture(fd); c.start()
os.write(fd, b"hello\nworld\n")
got = c.snap(); c.done(); scratch.close()
print("got=%r" % got)
ok = got == "hello\nworld\n"
if not ok: print("VIOLATION: bare LF not preserved")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5_utf8replace.py` → holds on the patched tree (good)

```python
# Requirement 2.2 (SHALL keep): decode as UTF-8, replace invalid bytes, no raise.
import os, tempfile
import _pytest.capture as cap
scratch = tempfile.TemporaryFile(); fd = scratch.fileno()
c = cap.FDCapture(fd); c.start()
os.write(fd, b"x\xff\xfey")  # invalid utf-8
try:
    got = c.snap()
except Exception as e:
    print("VIOLATION: raised %r" % e); c.done(); scratch.close(); raise SystemExit(1)
c.done(); scratch.close()
print("got=%r" % got)
# must not raise, must contain replacement char, and keep valid chars
ok = got.startswith("x") and got.endswith("y") and "�" in got
if not ok: print("VIOLATION: unexpected decode %r" % got)
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6_mode_writethrough.py` → holds on the patched tree (good)

```python
# Requirement 2.5 (SHALL keep): text wrapper reports mode without 'b', and
# write_through flushes immediately to underlying buffer.
import os, tempfile
import _pytest.capture as cap
scratch = tempfile.TemporaryFile(); fd = scratch.fileno()
c = cap.FDCapture(fd); c.start()
tw = c.tmpfile  # the TextIOWrapper/EncodedFile
mode = tw.mode
print("mode=%r" % mode)
# write via the text wrapper and confirm it's flushed through to buffer immediately (no explicit flush)
tw.write("abc\r")
raw = tw.buffer  # underlying binary buffer
pos = raw.tell()  # if write_through, data already in buffer
tw.seek(0); tw.buffer.seek(0)
onbuf = tw.buffer.read()
print("mode=%r buffer_after_write=%r bufpos=%d" % (mode, onbuf, pos))
c.done(); scratch.close()
ok = ("b" not in mode) and (b"abc\r" in onbuf)
if not ok: print("VIOLATION: mode or write-through incorrect")
raise SystemExit(0 if ok else 1)
```

Attack 7 — `probe_7_suspend_resume.py` → holds on the patched tree (good)

```python
# Requirement 2.4 (SHALL keep): suspend/resume and repeated snaps preserve content.
import os, tempfile
import _pytest.capture as cap
scratch = tempfile.TemporaryFile(); fd = scratch.fileno()
c = cap.FDCapture(fd); c.start()
os.write(fd, b"first\r")
got1 = c.snap()
c.suspend()
c.resume()
os.write(fd, b"second\r\n")
got2 = c.snap()
c.done(); scratch.close()
print("got1=%r got2=%r" % (got1, got2))
ok = got1 == "first\r" and got2 == "second\r\n"
if not ok: print("VIOLATION: suspend/resume/repeated snap lost or corrupted content")
raise SystemExit(0 if ok else 1)
```

Attack 8 — `probe_8_binary.py` → holds on the patched tree (good)

```python
# Requirement 2.3 (SHALL keep): FDCaptureBinary returns raw bytes verbatim.
import os, tempfile
import _pytest.capture as cap
scratch = tempfile.TemporaryFile(); fd = scratch.fileno()
c = cap.FDCaptureBinary(fd); c.start()
os.write(fd, b"bin\r\ndata\r")
got = c.snap(); c.done(); scratch.close()
print("got=%r type=%s" % (got, type(got).__name__))
ok = isinstance(got, bytes) and got == b"bin\r\ndata\r"
if not ok: print("VIOLATION: binary capture not verbatim bytes")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_cr.py`

```python
# Requirement 1.1 / 1.4 (POSITIVE CONTROL): a trailing '\r' written to a
# captured fd must be returned verbatim (not rewritten to '\n').
import os, tempfile
import _pytest.capture as cap

# use a scratch OS file descriptor as the capture target
scratch = tempfile.TemporaryFile()
targetfd = scratch.fileno()

c = cap.FDCapture(targetfd)
c.start()
os.write(targetfd, b"line\r")
os.fsync(targetfd) if False else None
got = c.snap()
c.done()
scratch.close()

print("wrote=%r got=%r" % ("line\r", got))
ok = got == "line\r"
if not ok:
    print("VIOLATION: expected trailing CR preserved, got %r" % got)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-7521: gold fix adds newline="" to the io.TextIOWrapper built in FDCaptureBinary.__init__, disabling universal-newline translation on readback of fd-captured output. Probes drive FDCapture / FDCaptureBinary directly on a scratch OS fd (no pytest needed): start() -> os.write(targetfd, ...) -> snap().

Probe -> requirement -> result (PATCHED / BASE):
- probe_1_cr (POSITIVE CONTROL, Req 1.1/1.4): trailing '\r' preserved. PATCHED: got 'line\r' (HOLDS). BASE: got 'line\n' (FAILS) -> discriminates.
- probe_2_crlf (Req 1.2): trailing '\r\n' preserved verbatim. PATCHED HOLDS.
- probe_3_verbatim (Req 1.3): mixed 'a\rb\r\nc\r\rd\ne\r' round-trips code-point-identical. PATCHED HOLDS.
- probe_4_lf (Req 2.1): bare '\n' unchanged. PATCHED HOLDS.
- probe_5_utf8replace (Req 2.2): invalid UTF-8 (b'x\xff\xfey') decoded with replacement char, no raise. PATCHED HOLDS.
- probe_6_mode_writethrough (Req 2.5): text wrapper mode reports 'r+' (no 'b'); write_through flushes 'abc\r' to underlying buffer immediately. PATCHED HOLDS.
- probe_7_suspend_resume (Req 2.4): suspend()/resume() + repeated snap() preserve 'first\r' then 'second\r\n'. PATCHED HOLDS.
- probe_8_binary (Req 2.3): FDCaptureBinary returns raw bytes b'bin\r\ndata\r' verbatim. PATCHED HOLDS.

All 8 probes hold on the gold-patched tree; positive control fails at base and holds patched (prepatch reproduced).

Candidate patches:
- weakB_noop (comment-only, does NOT add newline=): REJECTED by probe_1/probe_2/probe_3 (still returns 'line\n'). Demonstrates the suite discriminates a non-fix.
- weakA_newline_lf (newline="\n" instead of ""): passes ALL 8 probes. This is NOT a genuine too-weak finding: per io.TextIOWrapper semantics, newline="\n" also disables universal-newline read translation, so it is an equivalent correct fix and would resolve the hidden tests (runner will confirm). Reported as a candidate for completeness of the discrimination leg.

Verdict SOUND: >=5 distinct probes covering behavioral SHALLs (1.1-1.4), regression SHALL-keeps (2.1-2.5), boundaries (lone CR, CRLF, interior CR, invalid UTF-8); positive control has discriminating power; one candidate (weakB) is rejected by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1_cr.py`, `probe_2_crlf.py`, `probe_3_verbatim.py`, `probe_4_lf.py`, `probe_5_utf8replace.py`, `probe_6_mode_writethrough.py`, `probe_7_suspend_resume.py`, `probe_8_binary.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_cr.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_cr.py` → holds on the patched tree (good)

Attack 2 — `probe_2_crlf.py` → holds on the patched tree (good)

Attack 3 — `probe_3_verbatim.py` → holds on the patched tree (good)

Attack 4 — `probe_4_lf.py` → holds on the patched tree (good)

Attack 5 — `probe_5_utf8replace.py` → holds on the patched tree (good)

Attack 6 — `probe_6_mode_writethrough.py` → holds on the patched tree (good)

Attack 7 — `probe_7_suspend_resume.py` → holds on the patched tree (good)

Attack 8 — `probe_8_binary.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_cr.py`

```python
# Requirement 1.1 / 1.4 (POSITIVE CONTROL): a trailing '\r' written to a
# captured fd must be returned verbatim (not rewritten to '\n').
import os, tempfile
import _pytest.capture as cap

# use a scratch OS file descriptor as the capture target
scratch = tempfile.TemporaryFile()
targetfd = scratch.fileno()

c = cap.FDCapture(targetfd)
c.start()
os.write(targetfd, b"line\r")
os.fsync(targetfd) if False else None
got = c.snap()
c.done()
scratch.close()

print("wrote=%r got=%r" % ("line\r", got))
ok = got == "line\r"
if not ok:
    print("VIOLATION: expected trailing CR preserved, got %r" % got)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-7521: gold fix adds newline="" to the io.TextIOWrapper built in FDCaptureBinary.__init__, disabling universal-newline translation on readback of fd-captured output. Probes drive FDCapture / FDCaptureBinary directly on a scratch OS fd (no pytest needed): start() -> os.write(targetfd, ...) -> snap().

Probe -> requirement -> result (PATCHED / BASE):
- probe_1_cr (POSITIVE CONTROL, Req 1.1/1.4): trailing '\r' preserved. PATCHED: got 'line\r' (HOLDS). BASE: got 'line\n' (FAILS) -> discriminates.
- probe_2_crlf (Req 1.2): trailing '\r\n' preserved verbatim. PATCHED HOLDS.
- probe_3_verbatim (Req 1.3): mixed 'a\rb\r\nc\r\rd\ne\r' round-trips code-point-identical. PATCHED HOLDS.
- probe_4_lf (Req 2.1): bare '\n' unchanged. PATCHED HOLDS.
- probe_5_utf8replace (Req 2.2): invalid UTF-8 (b'x\xff\xfey') decoded with replacement char, no raise. PATCHED HOLDS.
- probe_6_mode_writethrough (Req 2.5): text wrapper mode reports 'r+' (no 'b'); write_through flushes 'abc\r' to underlying buffer immediately. PATCHED HOLDS.
- probe_7_suspend_resume (Req 2.4): suspend()/resume() + repeated snap() preserve 'first\r' then 'second\r\n'. PATCHED HOLDS.
- probe_8_binary (Req 2.3): FDCaptureBinary returns raw bytes b'bin\r\ndata\r' verbatim. PATCHED HOLDS.

All 8 probes hold on the gold-patched tree; positive control fails at base and holds patched (prepatch reproduced).

Candidate patches:
- weakB_noop (comment-only, does NOT add newline=): REJECTED by probe_1/probe_2/probe_3 (still returns 'line\n'). Demonstrates the suite discriminates a non-fix.
- weakA_newline_lf (newline="\n" instead of ""): passes ALL 8 probes. This is NOT a genuine too-weak finding: per io.TextIOWrapper semantics, newline="\n" also disables universal-newline read translation, so it is an equivalent correct fix and would resolve the hidden tests (runner will confirm). Reported as a candidate for completeness of the discrimination leg.

Verdict SOUND: >=5 distinct probes covering behavioral SHALLs (1.1-1.4), regression SHALL-keeps (2.1-2.5), boundaries (lone CR, CRLF, interior CR, invalid UTF-8); positive control has discriminating power; one candidate (weakB) is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds a single kwarg newline="" to the io.TextIOWrapper built in FDCaptureBinary.__init__ (src/_pytest/capture.py), disabling universal-newline translation on FD-capture readback while preserving encoding=utf-8, errors=replace, write_through=True. Probe results: PATCHED tree -> all 5 pass (CR 'x\r', CRLF 'y\r\n', LF 'z\n', capfdbinary b'a\r', invalid-UTF8 '�'+'\r'). BASE tree -> test_cr, test_crlf, test_invalid_utf8 FAIL (CR/CRLF rewritten to \n; matches issue reproducer and FAIL_TO_PASS test_cafd_preserves_newlines[\r]/[\r\n]); LF and binary pass on both. Requirement boundary is the full changed readback behavior; Req 2 correctly asserts preserved behaviors (bare LF unchanged 2.1, UTF-8 errors=replace no-raise 2.2, fixtures+binary variants 2.3, suspend/resume+repeated readouterr 2.4, mode/name+write_through 2.5) — all consistent with the patch and observed code. No requirement mandates absent behavior, forbids present behavior, invents behavior, or mis-pins the modeling boundary.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe FD-capture newline preservation behaviorally. The three newline forms enumerated (\n R1.1/R1.2 as \r and \r\n, R2.1 as \n) coincide with the test parametrization ('\n','\r\n','\r'), but {\n,\r,\r\n} is the inherent, complete set of sequences universal-newline translation rewrites, so enumerating them is describing the behavior, not mirroring test-only cases. The \r and \n cases plus readouterr()/capfd/capfdbinary and src/_pytest/capture.py are all present in the public problem_statement; the \r\n case is the natural CRLF behavioral extension, not derivable solely from tests. The gold's fix-invented token newline="" is never named — the doc states 'no universal-newline translation' (behavior, not code). Module/class names (EncodedFile, FDCaptureBinary, TextIOWrapper) are legitimate change localization, not test paths/names/ids. No quoted test code, no test function name/path/param-id, no verbatim gold lines.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
