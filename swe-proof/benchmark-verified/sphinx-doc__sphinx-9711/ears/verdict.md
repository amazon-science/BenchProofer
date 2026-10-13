# P2 adversarial audit — sphinx-doc__sphinx-9711

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req1 (crit 3): min 0.6.0, loaded 0.10.0 -> fulfilled, no raise. Positive control."""
import sys
from sphinx.extension import Extension, verify_needs_extensions
from sphinx.errors import VersionRequirementError

class App:
    def __init__(self, exts):
        self.extensions = exts

class Cfg:
    pass

app = App({'test.extension': Extension('test.extension', 'test.extension', version='0.10.0')})
cfg = Cfg()
cfg.needs_extensions = {'test.extension': '0.6.0'}
try:
    verify_needs_extensions(app, cfg)
    print("OK: 0.10.0 >= 0.6.0 accepted, no error raised")
    sys.exit(0)
except VersionRequirementError as e:
    print("VIOLATION: raised for 0.10.0 vs required 0.6.0:", e)
    sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1 crit 4: multi-digit leading component (e.g. 10 vs 9) that sorts wrong under
lexicographic order is accepted when numerically >= required."""
import sys
from sphinx.extension import Extension, verify_needs_extensions
from sphinx.errors import VersionRequirementError

class App:
    def __init__(self, exts): self.extensions = exts
class Cfg: pass

# "10.0" < "9.0" lexicographically, but 10 >= 9 numerically
app = App({'e': Extension('e', 'e', version='10.0')})
cfg = Cfg(); cfg.needs_extensions = {'e': '9.0'}
try:
    verify_needs_extensions(app, cfg)
    print("OK: 10.0 accepted against required 9.0")
    sys.exit(0)
except VersionRequirementError as e:
    print("VIOLATION: raised for 10.0 vs 9.0:", e)
    sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1 crit 5: loaded numerically LESS than required -> raise VersionRequirementError."""
import sys
from sphinx.extension import Extension, verify_needs_extensions
from sphinx.errors import VersionRequirementError

class App:
    def __init__(self, exts): self.extensions = exts
class Cfg: pass

app = App({'e': Extension('e', 'e', version='3.10')})
cfg = Cfg(); cfg.needs_extensions = {'e': '3.11'}
try:
    verify_needs_extensions(app, cfg)
    print("VIOLATION: no error raised though 3.10 < 3.11")
    sys.exit(1)
except VersionRequirementError as e:
    print("OK: raised for 3.10 < 3.11:", e)
    sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req1 crit 6: trailing-zero equality. 0.6 vs 0.6.0 equal; 1 vs 1.0 equal. Both directions no raise."""
import sys
from sphinx.extension import Extension, verify_needs_extensions
from sphinx.errors import VersionRequirementError

class App:
    def __init__(self, exts): self.extensions = exts
class Cfg: pass

cases = [('0.6.0', '0.6'), ('0.6', '0.6.0'), ('1.0', '1'), ('1', '1.0')]
for loaded, req in cases:
    app = App({'e': Extension('e', 'e', version=loaded)})
    cfg = Cfg(); cfg.needs_extensions = {'e': req}
    try:
        verify_needs_extensions(app, cfg)
        print(f"OK: loaded {loaded} required {req} treated as fulfilled")
    except VersionRequirementError as e:
        print(f"VIOLATION: raised for equal versions loaded={loaded} req={req}: {e}")
        sys.exit(1)
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3 crit 1+2: 'unknown version' -> raise regardless; message names ext, required, loaded.
Also Req4 crit 1 (None -> return) and crit 2 (empty -> ok) and crit 3 (missing ext -> warn, no raise)."""
import sys
from sphinx.extension import Extension, verify_needs_extensions
from sphinx.errors import VersionRequirementError

class App:
    def __init__(self, exts): self.extensions = exts
class Cfg: pass

ok = True

# unknown version always raises, even when required is tiny
app = App({'e': Extension('e', 'e', version='unknown version')})
cfg = Cfg(); cfg.needs_extensions = {'e': '0.0.1'}
try:
    verify_needs_extensions(app, cfg)
    print("VIOLATION: unknown version did not raise"); ok = False
except VersionRequirementError as e:
    msg = str(e)
    if 'e' in msg and '0.0.1' in msg and 'unknown version' in msg:
        print("OK: unknown version raised with proper message:", msg)
    else:
        print("VIOLATION: message missing components:", msg); ok = False

# None config -> no raise
cfg2 = Cfg(); cfg2.needs_extensions = None
try:
    verify_needs_extensions(App({}), cfg2)
    print("OK: None needs_extensions returned without raise")
except Exception as e:
    print("VIOLATION: None raised:", repr(e)); ok = False

# empty config -> no raise
cfg3 = Cfg(); cfg3.needs_extensions = {}
try:
    verify_needs_extensions(App({}), cfg3)
    print("OK: empty needs_extensions ok")
except Exception as e:
    print("VIOLATION: empty raised:", repr(e)); ok = False

# missing extension -> no raise (warning logged internally)
cfg4 = Cfg(); cfg4.needs_extensions = {'notloaded': '1.0'}
try:
    verify_needs_extensions(App({}), cfg4)
    print("OK: missing extension did not raise")
except Exception as e:
    print("VIOLATION: missing extension raised:", repr(e)); ok = False

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req2 crit 1/2/3: unparseable version -> string-comparison fallback, no crash.
Fallback: not fulfilled exactly when required > loaded lexicographically."""
import sys
from sphinx.extension import Extension, verify_needs_extensions
from sphinx.errors import VersionRequirementError
from packaging.version import Version, InvalidVersion

class App:
    def __init__(self, exts): self.extensions = exts
class Cfg: pass

ok = True

# Sanity: confirm these strings are unparseable so we exercise the fallback path.
for s in ('xyz', 'abc'):
    try:
        Version(s); print(f"NOTE: {s} unexpectedly parsed");
    except InvalidVersion:
        pass

# required 'xyz' > loaded 'abc' lexicographically -> should NOT be fulfilled -> raise
app = App({'e': Extension('e', 'e', version='abc')})
cfg = Cfg(); cfg.needs_extensions = {'e': 'xyz'}
try:
    verify_needs_extensions(app, cfg)
    print("VIOLATION: fallback did not raise though 'xyz' > 'abc'"); ok = False
except VersionRequirementError as e:
    print("OK: fallback raised for required 'xyz' > loaded 'abc'")
except InvalidVersion as e:
    print("VIOLATION: InvalidVersion propagated instead of fallback:", repr(e)); ok = False

# required 'abc' < loaded 'xyz' lexicographically -> fulfilled -> no raise
app2 = App({'e': Extension('e', 'e', version='xyz')})
cfg2 = Cfg(); cfg2.needs_extensions = {'e': 'abc'}
try:
    verify_needs_extensions(app2, cfg2)
    print("OK: fallback did not raise for required 'abc' <= loaded 'xyz'")
except VersionRequirementError as e:
    print("VIOLATION: fallback raised though 'abc' <= 'xyz':", e); ok = False
except InvalidVersion as e:
    print("VIOLATION: InvalidVersion propagated:", repr(e)); ok = False

sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req3 crit 3: evaluate each entry independently and raise on FIRST unfulfilled.
Also Req4 crit 4: verify_needs_extensions connected to config-inited event."""
import sys, inspect
from sphinx.extension import Extension, verify_needs_extensions
from sphinx.errors import VersionRequirementError

class App:
    def __init__(self, exts): self.extensions = exts
class Cfg: pass

ok = True

# two entries, first unfulfilled -> must raise (independent evaluation)
app = App({
    'a': Extension('a', 'a', version='1.0'),   # required 2.0 -> unfulfilled
    'b': Extension('b', 'b', version='5.0'),   # fulfilled
})
cfg = Cfg(); cfg.needs_extensions = {'a': '2.0', 'b': '1.0'}
try:
    verify_needs_extensions(app, cfg)
    print("VIOLATION: did not raise though ext 'a' unfulfilled"); ok = False
except VersionRequirementError as e:
    if 'a' in str(e):
        print("OK: raised naming the unfulfilled extension 'a'")
    else:
        print("VIOLATION: raised but message not about 'a':", e); ok = False

# Req4 crit 4: setup() connects verify_needs_extensions to config-inited
import sphinx.extension as extmod
src = inspect.getsource(extmod.setup)
if "config-inited" in src and "verify_needs_extensions" in src:
    print("OK: setup connects verify_needs_extensions to config-inited")
else:
    print("VIOLATION: config-inited connection missing in setup:", src); ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1 (crit 3): min 0.6.0, loaded 0.10.0 -> fulfilled, no raise. Positive control."""
import sys
from sphinx.extension import Extension, verify_needs_extensions
from sphinx.errors import VersionRequirementError

class App:
    def __init__(self, exts):
        self.extensions = exts

class Cfg:
    pass

app = App({'test.extension': Extension('test.extension', 'test.extension', version='0.10.0')})
cfg = Cfg()
cfg.needs_extensions = {'test.extension': '0.6.0'}
try:
    verify_needs_extensions(app, cfg)
    print("OK: 0.10.0 >= 0.6.0 accepted, no error raised")
    sys.exit(0)
except VersionRequirementError as e:
    print("VIOLATION: raised for 0.10.0 vs required 0.6.0:", e)
    sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9711: fix verify_needs_extensions to compare versions numerically (packaging.version.Version) with string fallback for unparseable versions.

Probes (all HOLD on gold-patched tree, exit 0):
- probe_1 (Req1 crit 3, POSITIVE CONTROL): min 0.6.0, loaded 0.10.0 -> no raise. HOLDS patched, FAILS at base (base uses string compare, wrongly raises). Discriminates.
- probe_2 (Req1 crit 4): loaded 10.0 vs required 9.0 (lexicographically 10.0<9.0) accepted. HOLDS patched, FAILS base.
- probe_3 (Req1 crit 5): loaded 3.10 < required 3.11 -> VersionRequirementError raised. HOLDS.
- probe_4 (Req1 crit 6): trailing-zero equality 0.6==0.6.0, 1==1.0 both directions -> no raise. HOLDS patched, FAILS base.
- probe_5 (Req3 crit1/2 + Req4 crit1/2/3): unknown version raises with message naming ext+required+loaded; None returns; empty ok; missing ext no raise. HOLDS.
- probe_6 (Req2 crit1/2/3): unparseable versions ('abc','xyz') fall back to string comparison without propagating InvalidVersion; not-fulfilled iff required > loaded lexicographically. HOLDS.
- probe_7 (Req3 crit3 + Req4 crit4): first unfulfilled entry raises naming that extension; setup() connects verify_needs_extensions to config-inited. HOLDS.

Positive control (probe_1): prepatch_reproduced=TRUE — raised at base, no raise on patched.

Candidate wrong-fix (weak.diff): naive float() comparison instead of packaging.Version. Applies cleanly at base. REJECTED by probe_1 (float('0.10.0') -> ValueError -> string fallback -> wrongly rejects 0.10.0 vs 0.6.0) and probe_4 (float can't equate 0.6==0.6.0 after ValueError fallback). Demonstrates the suite discriminates a plausibly-wrong reading of Req1 (multi-component versions). probes 2/3/5/6/7 HOLD under it, so it is a genuine wrong fix caught only by 1 & 4.

All runs completed in the official image; every probe holds on patched and the positive control discriminates base vs patched. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1 (crit 3): min 0.6.0, loaded 0.10.0 -> fulfilled, no raise. Positive control."""
import sys
from sphinx.extension import Extension, verify_needs_extensions
from sphinx.errors import VersionRequirementError

class App:
    def __init__(self, exts):
        self.extensions = exts

class Cfg:
    pass

app = App({'test.extension': Extension('test.extension', 'test.extension', version='0.10.0')})
cfg = Cfg()
cfg.needs_extensions = {'test.extension': '0.6.0'}
try:
    verify_needs_extensions(app, cfg)
    print("OK: 0.10.0 >= 0.6.0 accepted, no error raised")
    sys.exit(0)
except VersionRequirementError as e:
    print("VIOLATION: raised for 0.10.0 vs required 0.6.0:", e)
    sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9711: fix verify_needs_extensions to compare versions numerically (packaging.version.Version) with string fallback for unparseable versions.

Probes (all HOLD on gold-patched tree, exit 0):
- probe_1 (Req1 crit 3, POSITIVE CONTROL): min 0.6.0, loaded 0.10.0 -> no raise. HOLDS patched, FAILS at base (base uses string compare, wrongly raises). Discriminates.
- probe_2 (Req1 crit 4): loaded 10.0 vs required 9.0 (lexicographically 10.0<9.0) accepted. HOLDS patched, FAILS base.
- probe_3 (Req1 crit 5): loaded 3.10 < required 3.11 -> VersionRequirementError raised. HOLDS.
- probe_4 (Req1 crit 6): trailing-zero equality 0.6==0.6.0, 1==1.0 both directions -> no raise. HOLDS patched, FAILS base.
- probe_5 (Req3 crit1/2 + Req4 crit1/2/3): unknown version raises with message naming ext+required+loaded; None returns; empty ok; missing ext no raise. HOLDS.
- probe_6 (Req2 crit1/2/3): unparseable versions ('abc','xyz') fall back to string comparison without propagating InvalidVersion; not-fulfilled iff required > loaded lexicographically. HOLDS.
- probe_7 (Req3 crit3 + Req4 crit4): first unfulfilled entry raises naming that extension; setup() connects verify_needs_extensions to config-inited. HOLDS.

Positive control (probe_1): prepatch_reproduced=TRUE — raised at base, no raise on patched.

Candidate wrong-fix (weak.diff): naive float() comparison instead of packaging.Version. Applies cleanly at base. REJECTED by probe_1 (float('0.10.0') -> ValueError -> string fallback -> wrongly rejects 0.10.0 vs 0.6.0) and probe_4 (float can't equate 0.6==0.6.0 after ValueError fallback). Demonstrates the suite discriminates a plausibly-wrong reading of Req1 (multi-component versions). probes 2/3/5/6/7 HOLD under it, so it is a genuine wrong fix caught only by 1 & 4.

All runs completed in the official image; every probe holds on patched and the positive control discriminates base vs patched. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirement 2.3 accurately captures the string-fallback semantics (required lexicographically greater than loaded → not fulfilled), matching `if reqversion > extension.version` inside the except branch. Error message/type and config/missing-extension handling (req3,4) are unchanged by the patch and correctly described. NOTE: this is strictly a faithfulness verdict — the separate G-PANEL-3 leakage concern (the 3.9/3.10/3.11 triples in req1.4/1.5 being derivable only from the hidden test, not the public problem statement) is out of scope for this gate and does not affect faithfulness.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change (module sphinx/extension.py, function verify_needs_extensions, Extension.version attribute, VersionRequirementError, config-inited event) — all legitimate localization, and all public/derivable from the problem statement or the source repo. The concrete example enumerated (min 0.6/0.6.0 vs loaded 0.10/0.10.0) is taken verbatim from the PUBLIC problem_statement (the sphinx-gallery 0.6.0 vs 0.10.0 reproduction). The hidden test's distinguishing artifacts are NOT present: no test path (tests/test_extension.py), no test function name (test_needs_extensions), no test-specific version values (3.9 / 3.10 / 3.11), no 'test.extension' identifier. The gold's implementation vocabulary (packaging.version.Version / InvalidVersion) is not quoted; Req 2's 'parse as numeric version' / 'invalid version error / string fallback' is a behavioral description of the required degradation, not a transcription of the try/except gold code. Req 1.6 (trailing-zero equality) and Req 1.4 (multi-digit leading component) are behavioral generalizations of numeric version semantics, not mirrors of test parametrization (the test has only one non-parametrized function with three inline asserts). Translating what the single F2P test checks into behavioral requirements is exactly the intended job; no hidden-test or gold-only content is transmitted.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
