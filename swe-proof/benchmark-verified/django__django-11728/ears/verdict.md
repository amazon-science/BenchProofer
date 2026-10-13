# P2 adversarial audit — django__django-11728

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""R1.1 (positive control): a named capture group closed by the FINAL char
of the pattern must be replaced with <groupname>."""
import sys
from django.contrib.admindocs.utils import replace_named_groups

pat = r'entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)'
out = replace_named_groups(pat)
expected = r'entries/<pk>/relationships/<related_field>'
print("input   :", pat)
print("output  :", out)
print("expected:", expected)
sys.exit(0 if out == expected else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R2.1 & R2.2: a trailing unnamed group (incl. nested) at the end of the
pattern must be replaced with a single <var>. NOTE: unnamed_group_matcher
matches any '(', so we use patterns with NO named group (this helper is
designed to run after replace_named_groups, as simplify_regex does)."""
import sys
from django.contrib.admindocs.utils import replace_unnamed_groups

cases = [
    (r'^a/b/(\w+)', r'^a/b/<var>'),            # R2.1 trailing unnamed
    (r'^b/((x|y)\w+)', r'^b/<var>'),           # R2.2 nested trailing, single <var>
]
ok = True
for pat, exp in cases:
    out = replace_unnamed_groups(pat)
    print(f"input={pat!r} output={out!r} expected={exp!r}")
    if out != exp:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.2: multiple named groups, the last one trailing — all replaced, incl.
the final one. Also R1.3: the trailing group's closing paren must be consumed
(no stray ')' left)."""
import sys
from django.contrib.admindocs.utils import replace_named_groups

pat = r'^(?P<a>\w+)/b/(?P<c>\w+)'
out = replace_named_groups(pat)
expected = r'^<a>/b/<c>'
print("input   :", pat)
print("output  :", out)
print("expected:", expected)
sys.exit(0 if out == expected else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3 (regression): groups followed by other characters keep working, nested
groups matched at depth-balanced close, escaped parens treated as literal,
trailing literal text retained. Unnamed cases use patterns with no named group
(the helper is used post-replace_named_groups)."""
import sys
from django.contrib.admindocs.utils import replace_named_groups, replace_unnamed_groups

named = [
    (r'^(?P<a>\w+)/b/(?P<c>\w+)/$', r'^<a>/b/<c>/$'),        # R3.1 followed by /$
    (r'^(?P<a>(x|y))/b', r'^<a>/b'),                         # R3.4 nested named
    (r'^(?P<a>(x|y)(\(|\)))/b', r'^<a>/b'),                  # R3.5 escaped parens literal
    (r'(?P<c>\w+)ab', r'<c>ab'),                             # R3.3 trailing literal text
]
unnamed = [
    (r'^a/b/(\w+)$', r'^a/b/<var>$'),                        # R3.2 unnamed followed by $
    (r'^b/((x|y)\w+)$', r'^b/<var>$'),                       # nested unnamed followed by $
    (r'^b/((x|y)\w+)ab', r'^b/<var>ab'),                     # R3.3 trailing literal after unnamed
]
ok = True
for pat, exp in named:
    out = replace_named_groups(pat)
    print(f"named   input={pat!r} out={out!r} exp={exp!r}")
    if out != exp:
        ok = False
for pat, exp in unnamed:
    out = replace_unnamed_groups(pat)
    print(f"unnamed input={pat!r} out={out!r} exp={exp!r}")
    if out != exp:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R4: end-to-end simplify_regex — trailing groups render as placeholders,
metacharacters stripped, leading '/', and trailing-slash patterns unchanged.
Mirrors the official F2P test table."""
import sys
from django.contrib.admindocs.views import simplify_regex

cases = [
    (r'^(?P<a>\w+)/b/(?P<c>\w+)/$', '/<a>/b/<c>/'),
    (r'^(?P<a>\w+)/b/(?P<c>\w+)$', '/<a>/b/<c>'),
    (r'^(?P<a>\w+)/b/(?P<c>\w+)', '/<a>/b/<c>'),         # R4.1 trailing named
    (r'^(?P<a>\w+)/b/(\w+)$', '/<a>/b/<var>'),
    (r'^(?P<a>\w+)/b/(\w+)', '/<a>/b/<var>'),            # R4.1 trailing unnamed
    (r'^(?P<a>\w+)/b/((x|y)\w+)$', '/<a>/b/<var>'),
    (r'^(?P<a>\w+)/b/((x|y)\w+)', '/<a>/b/<var>'),
    (r'^(?P<a>(x|y))/b/(?P<c>\w+)$', '/<a>/b/<c>'),
    (r'^(?P<a>(x|y))/b/(?P<c>\w+)', '/<a>/b/<c>'),
    (r'^(?P<a>(x|y))/b/(?P<c>\w+)ab', '/<a>/b/<c>ab'),
    (r'^(?P<a>(x|y)(\(|\)))/b/(?P<c>\w+)ab', '/<a>/b/<c>ab'),
    (r'^a/?$', '/a/'),
    (r'^a', '/a'),
]
ok = True
for pat, exp in cases:
    out = simplify_regex(pat)
    print(f"input={pat!r} out={out!r} exp={exp!r}")
    if out != exp:
        ok = False
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1 (positive control): a named capture group closed by the FINAL char
of the pattern must be replaced with <groupname>."""
import sys
from django.contrib.admindocs.utils import replace_named_groups

pat = r'entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)'
out = replace_named_groups(pat)
expected = r'entries/<pk>/relationships/<related_field>'
print("input   :", pat)
print("output  :", out)
print("expected:", expected)
sys.exit(0 if out == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover the admindocs trailing-capture-group fix in django/contrib/admindocs/utils.py (replace_named_groups, replace_unnamed_groups) and views.simplify_regex.

Probes (each standalone python, exit 0 iff criterion holds; all RUN in the instance docker image):
- probe_1.py (R1.1, POSITIVE CONTROL): trailing named group entries/(?P<pk>...)/relationships/(?P<related_field>\w+) -> entries/<pk>/relationships/<related_field>. HOLDS patched; VIOLATED at base (base leaves (?P<related_field>\w+) unreplaced) => discriminating power confirmed.
- probe_2.py (R2.1, R2.2): trailing unnamed group '^a/b/(\w+)'->'^a/b/<var>' and nested '^b/((x|y)\w+)'->'^b/<var>' (single <var>). HOLDS patched. NOTE: unnamed_group_matcher is bare '\(' matching ANY paren, so this helper is designed to run post-replace_named_groups; probes feed it patterns with no named group (as simplify_regex composes them). Initial versions that fed named groups directly produced doubled output — an artifact of misuse, not a defect; corrected.
- probe_3.py (R1.2, R1.3): two named groups, last trailing '^(?P<a>\w+)/b/(?P<c>\w+)'->'^<a>/b/<c>' (closing paren consumed, no stray ')'). HOLDS patched.
- probe_4.py (R3.1-R3.5 regression): named followed by /$, nested named, escaped-paren literals, trailing literal 'ab'; unnamed followed by $, nested unnamed, unnamed+trailing literal. All HOLD patched.
- probe_5.py (R4.1-R4.3 e2e simplify_regex): full official F2P table incl. trailing named/unnamed, metachar stripping, leading '/', trailing-slash-unchanged. HOLDS patched.

Candidate wrong-fix (weak.diff): the partial 'named-only' fix — repairs replace_named_groups exactly as gold but leaves replace_unnamed_groups' bug-order intact (this is the lazy reading permitted if one only reads the issue's headline about replace_named_groups). Under this patch: probe_1/3/4 HOLD but probe_2 REJECTS it ('^a/b/(\w+)'->'^a/b/(\w+)' unreplaced; nested '^b/(<var>\w+)') and probe_5 REJECTS it (e2e table fails). This demonstrates the suite discriminates a requirements-incomplete implementation — the too-weak candidate is caught, so no TOO-WEAK finding.

All 5 probes hold on the gold-patched tree; positive control fails at base and holds patched. No probe fails on the patched tree; no requirements-conforming alternative patch passes the suite. => SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1 (positive control): a named capture group closed by the FINAL char
of the pattern must be replaced with <groupname>."""
import sys
from django.contrib.admindocs.utils import replace_named_groups

pat = r'entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)'
out = replace_named_groups(pat)
expected = r'entries/<pk>/relationships/<related_field>'
print("input   :", pat)
print("output  :", out)
print("expected:", expected)
sys.exit(0 if out == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover the admindocs trailing-capture-group fix in django/contrib/admindocs/utils.py (replace_named_groups, replace_unnamed_groups) and views.simplify_regex.

Probes (each standalone python, exit 0 iff criterion holds; all RUN in the instance docker image):
- probe_1.py (R1.1, POSITIVE CONTROL): trailing named group entries/(?P<pk>...)/relationships/(?P<related_field>\w+) -> entries/<pk>/relationships/<related_field>. HOLDS patched; VIOLATED at base (base leaves (?P<related_field>\w+) unreplaced) => discriminating power confirmed.
- probe_2.py (R2.1, R2.2): trailing unnamed group '^a/b/(\w+)'->'^a/b/<var>' and nested '^b/((x|y)\w+)'->'^b/<var>' (single <var>). HOLDS patched. NOTE: unnamed_group_matcher is bare '\(' matching ANY paren, so this helper is designed to run post-replace_named_groups; probes feed it patterns with no named group (as simplify_regex composes them). Initial versions that fed named groups directly produced doubled output — an artifact of misuse, not a defect; corrected.
- probe_3.py (R1.2, R1.3): two named groups, last trailing '^(?P<a>\w+)/b/(?P<c>\w+)'->'^<a>/b/<c>' (closing paren consumed, no stray ')'). HOLDS patched.
- probe_4.py (R3.1-R3.5 regression): named followed by /$, nested named, escaped-paren literals, trailing literal 'ab'; unnamed followed by $, nested unnamed, unnamed+trailing literal. All HOLD patched.
- probe_5.py (R4.1-R4.3 e2e simplify_regex): full official F2P table incl. trailing named/unnamed, metachar stripping, leading '/', trailing-slash-unchanged. HOLDS patched.

Candidate wrong-fix (weak.diff): the partial 'named-only' fix — repairs replace_named_groups exactly as gold but leaves replace_unnamed_groups' bug-order intact (this is the lazy reading permitted if one only reads the issue's headline about replace_named_groups). Under this patch: probe_1/3/4 HOLD but probe_2 REJECTS it ('^a/b/(\w+)'->'^a/b/(\w+)' unreplaced; nested '^b/(<var>\w+)') and probe_5 REJECTS it (e2e table fails). This demonstrates the suite discriminates a requirements-incomplete implementation — the too-weak candidate is caught, so no TOO-WEAK finding.

All 5 probes hold on the gold-patched tree; positive control fails at base and holds patched. No probe fails on the patched tree; no requirements-conforming alternative patch passes the suite. => SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch moves the `unmatched_open_brackets == 0` check to AFTER the paren-count update in both helpers and adjusts the slice end (+idx+1 for named, +2+idx for unnamed) so a group whose closing paren is the final character is detected. Probed gold-patched behavior (all pass): R1.1 rn('^(?P<a>\w+)/b/(?P<c>\w+)')='^<a>/b/<c>'; R1.2 named trailing across multiple groups -> 'entries/<pk>/relationships/<related_field>'; R1/nested trailing '^(?P<a>(x|y))'->'^<a>'; R2.1 ru('b/(\w+)')='b/<var>'; R2.2 nested unnamed trailing 'b/((x|y)\w+)'->'b/<var>' (single <var>); R3.1/R3.2 followed groups preserved with trailing chars intact; R3.3 trailing literal '(?P<a>\w+)ab'->'<a>ab'; R3.4 nested/alternation depth-balanced close; R3.5 escaped parens (\( \)) treated as literals; R4.1 simplify_regex trailing named -> '/entries/<pk>/relationships/<related_field>' and unnamed '/b/<var>'; R4.3 slash-ended pattern unchanged '/<a>/b/<c>/'. Requirements correctly scope claims: R1/R3 to replace_named_groups (named-group matcher), R2 to replace_unnamed_groups (whose matcher is bare '\(', matching any paren — the requirements only assert unnamed-group inputs, consistent with its real use downstream of replace_named_groups). No unfaithful boundary, no invented behavior, no forbidden-but-present behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the trailing-capture-group fix behaviorally. The sole worked example (line 19) is copied from the PUBLIC problem_statement. Named identifiers (replace_named_groups/replace_unnamed_groups/simplify_regex, utils.py/views.py) are legitimate localization present in the module, not fix-invented. Illustrative fragments — `(?P<a>\w+)`, `<a>`/`<var>`, `((x|y)\w+)`, `(?P<a>(x|y))` — come from the pre-existing source docstrings/pre-existing (unchanged/context) test lines, and the escaped-paren (req 3.5) and trailing-literal `ab` (req 3.3) notes describe pre-existing code branches (prev_char != '\\', literal retention) that are regression-preservation requirements any author derives from reading utils.py. No test file paths, test function/class names, FAIL_TO_PASS ids, parametrization ids, or verbatim gold-patch internals (no `==>` docstring lines, no `end+idx+1`/`start+2+idx` indices) are transmitted. The requirement decomposition (trailing named / trailing unnamed / nested / preserve-followed) is the natural behavioral decomposition, not a mirror of the added test tuples. This is behavior translation, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
