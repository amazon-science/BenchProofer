# P2 adversarial audit — sphinx-doc__sphinx-8621

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1_dash_standalone.py`, `probe_2_alt_caret.py`, `probe_3_shift_plus.py`, `probe_4_regression_controlx.py`, `probe_5_single_space.py`, `probe_6_whitespace_seq.py`, `probe_7_leading_sep.py`, `probe_8_trailing_sep.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_dash_standalone.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_dash_standalone.py` → holds on the patched tree (good)

```python
"""POSITIVE CONTROL. Req 1.1/1.2/1.3: standalone `-` renders as ONE kbd, text '-',
no nested <kbd>, no empty keystroke element.
Patched: HOLDS. Base: FAILS (splits into empty kbds around a separator)."""
import sys, warnings
warnings.filterwarnings('ignore')
from docutils import nodes, utils, frontend
from sphinx.builders.html.transforms import KeyboardTransform


def run_kbd(text):
    settings = frontend.OptionParser(components=()).get_default_values()
    doc = utils.new_document('t', settings)
    lit = nodes.literal('', text, classes=['kbd'])
    p = nodes.paragraph('', ''); p += lit; doc += p
    KeyboardTransform(doc).run()
    return lit


lit = run_kbd('-')
inner = [c for c in lit.children if isinstance(c, nodes.literal)]
empty = [c for c in inner if c.astext() == '']
print('astext=%r classes=%r n_inner_kbd=%d n_empty_kbd=%d children=%r'
      % (lit.astext(), lit.get('classes'), len(inner), len(empty),
         [ (type(c).__name__, c.astext()) for c in lit.children ]))

ok = (lit.astext() == '-'
      and 'compound' not in lit.get('classes', [])
      and len(inner) == 0
      and len(empty) == 0)
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_alt_caret.py` → holds on the patched tree (good)

```python
"""Req 2.4 / 2.1 / hidden F2P: `Alt+^` -> outer compound kbd with inner [Alt] '+' [^],
final keystroke '^', NO empty trailing kbd element.
Patched: HOLDS. Base: FAILS (trailing empty kbd because final ^ treated as sep)."""
import sys, warnings
warnings.filterwarnings('ignore')
from docutils import nodes, utils, frontend
from sphinx.builders.html.transforms import KeyboardTransform


def run_kbd(text):
    settings = frontend.OptionParser(components=()).get_default_values()
    doc = utils.new_document('t', settings)
    lit = nodes.literal('', text, classes=['kbd'])
    p = nodes.paragraph('', ''); p += lit; doc += p
    KeyboardTransform(doc).run()
    return lit


lit = run_kbd('Alt+^')
seq = [(type(c).__name__, c.astext()) for c in lit.children]
inner = [c.astext() for c in lit.children if isinstance(c, nodes.literal)]
seps = [str(c) for c in lit.children if isinstance(c, nodes.Text)]
empty = [c for c in lit.children if isinstance(c, nodes.literal) and c.astext() == '']
print('seq=%r inner=%r seps=%r n_empty=%d compound=%s'
      % (seq, inner, seps, len(empty), 'compound' in lit.get('classes', [])))

ok = (inner == ['Alt', '^']
      and seps == ['+']
      and len(empty) == 0
      and seq == [('literal', 'Alt'), ('Text', '+'), ('literal', '^')])
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_shift_plus.py` → holds on the patched tree (good)

```python
"""Req 2.4 (public example `Shift-+`): compound whose final key is '+'.
Expect inner [Shift, +], sep ['-'], no empty trailing element.
Patched HOLDS; base FAILS (splits at both '-' and trailing '+', empty last kbd)."""
import sys, warnings
warnings.filterwarnings('ignore')
from docutils import nodes, utils, frontend
from sphinx.builders.html.transforms import KeyboardTransform


def run_kbd(text):
    settings = frontend.OptionParser(components=()).get_default_values()
    doc = utils.new_document('t', settings)
    lit = nodes.literal('', text, classes=['kbd'])
    p = nodes.paragraph('', ''); p += lit; doc += p
    KeyboardTransform(doc).run()
    return lit


lit = run_kbd('Shift-+')
seq = [(type(c).__name__, c.astext()) for c in lit.children]
inner = [c.astext() for c in lit.children if isinstance(c, nodes.literal)]
seps = [str(c) for c in lit.children if isinstance(c, nodes.Text)]
empty = [c for c in lit.children if isinstance(c, nodes.literal) and c.astext() == '']
print('seq=%r inner=%r seps=%r n_empty=%d' % (seq, inner, seps, len(empty)))

ok = (inner == ['Shift', '+'] and seps == ['-'] and len(empty) == 0)
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_regression_controlx.py` → holds on the patched tree (good)

```python
"""Req 4.1/4.5 regression: ordinary compound `Control+X` -> outer kbd
containing inner [Control] '+' [X], with the `kbd` CSS class preserved on
each inner keystroke element (Req 4.5), in original left-to-right order."""
import sys, warnings
warnings.filterwarnings('ignore')
from docutils import nodes, utils, frontend
from sphinx.builders.html.transforms import KeyboardTransform


def run_kbd(text):
    settings = frontend.OptionParser(components=()).get_default_values()
    doc = utils.new_document('t', settings)
    lit = nodes.literal('', text, classes=['kbd'])
    p = nodes.paragraph('', ''); p += lit; doc += p
    KeyboardTransform(doc).run()
    return lit


lit = run_kbd('Control+X')
inner = [(c.astext(), list(c.get('classes', []))) for c in lit.children if isinstance(c, nodes.literal)]
seps = [str(c) for c in lit.children if isinstance(c, nodes.Text)]
seq = [(type(c).__name__, c.astext()) for c in lit.children]
print('inner=%r seps=%r seq=%r' % (inner, seps, seq))

ok = ([i[0] for i in inner] == ['Control', 'X']
      and seps == ['+']
      and all('kbd' in c[1] for c in inner)
      and seq == [('literal', 'Control'), ('Text', '+'), ('literal', 'X')])
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_single_space.py` → holds on the patched tree (good)

```python
"""Req 4.2: single ordinary keystroke `space` (no separator) -> single keystroke,
text unchanged, NO nested kbd, not compound."""
import sys, warnings
warnings.filterwarnings('ignore')
from docutils import nodes, utils, frontend
from sphinx.builders.html.transforms import KeyboardTransform


def run_kbd(text):
    settings = frontend.OptionParser(components=()).get_default_values()
    doc = utils.new_document('t', settings)
    lit = nodes.literal('', text, classes=['kbd'])
    p = nodes.paragraph('', ''); p += lit; doc += p
    KeyboardTransform(doc).run()
    return lit


lit = run_kbd('space')
inner = [c for c in lit.children if isinstance(c, nodes.literal)]
print('astext=%r compound=%s n_inner=%d' % (lit.astext(), 'compound' in lit.get('classes', []), len(inner)))
ok = (lit.astext() == 'space' and 'compound' not in lit.get('classes', []) and len(inner) == 0)
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_whitespace_seq.py` → holds on the patched tree (good)

```python
"""Req 3.1 / 4.3: whitespace-joined `M-x  M-s` keeps splitting into constituent
keystrokes with whitespace kept as plain-text separator. Expect inner
[M, x, M, s], seps ['-', '  ', '-'] in order."""
import sys, warnings
warnings.filterwarnings('ignore')
from docutils import nodes, utils, frontend
from sphinx.builders.html.transforms import KeyboardTransform


def run_kbd(text):
    settings = frontend.OptionParser(components=()).get_default_values()
    doc = utils.new_document('t', settings)
    lit = nodes.literal('', text, classes=['kbd'])
    p = nodes.paragraph('', ''); p += lit; doc += p
    KeyboardTransform(doc).run()
    return lit


lit = run_kbd('M-x  M-s')
inner = [c.astext() for c in lit.children if isinstance(c, nodes.literal)]
seps = [str(c) for c in lit.children if isinstance(c, nodes.Text)]
empty = [c for c in lit.children if isinstance(c, nodes.literal) and c.astext() == '']
print('inner=%r seps=%r n_empty=%d compound=%s' % (inner, seps, len(empty), 'compound' in lit.get('classes', [])))
ok = (inner == ['M', 'x', 'M', 's'] and seps == ['-', '  ', '-'] and len(empty) == 0)
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7_leading_sep.py` → holds on the patched tree (good)

```python
"""Req 2.2: a separator char at the very START (no char before) is NOT a separator.
`+x` -> single keystroke '+x', no split. Base FAILS (splits into ['','x'] -> empty kbd)."""
import sys, warnings
warnings.filterwarnings('ignore')
from docutils import nodes, utils, frontend
from sphinx.builders.html.transforms import KeyboardTransform


def run_kbd(text):
    settings = frontend.OptionParser(components=()).get_default_values()
    doc = utils.new_document('t', settings)
    lit = nodes.literal('', text, classes=['kbd'])
    p = nodes.paragraph('', ''); p += lit; doc += p
    KeyboardTransform(doc).run()
    return lit


lit = run_kbd('+x')
inner = [c for c in lit.children if isinstance(c, nodes.literal)]
empty = [c for c in inner if c.astext() == '']
print('astext=%r compound=%s n_inner=%d n_empty=%d' % (lit.astext(), 'compound' in lit.get('classes', []), len(inner), len(empty)))
ok = (lit.astext() == '+x' and 'compound' not in lit.get('classes', []) and len(inner) == 0 and len(empty) == 0)
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
```

Attack 8 — `probe_8_trailing_sep.py` → holds on the patched tree (good)

```python
"""Req 2.3: a separator char at the very END (no char after) is NOT a separator.
`x-` -> single keystroke 'x-', no split, no empty trailing kbd.
Base FAILS (splits into ['x',''] -> empty trailing kbd)."""
import sys, warnings
warnings.filterwarnings('ignore')
from docutils import nodes, utils, frontend
from sphinx.builders.html.transforms import KeyboardTransform


def run_kbd(text):
    settings = frontend.OptionParser(components=()).get_default_values()
    doc = utils.new_document('t', settings)
    lit = nodes.literal('', text, classes=['kbd'])
    p = nodes.paragraph('', ''); p += lit; doc += p
    KeyboardTransform(doc).run()
    return lit


lit = run_kbd('x-')
inner = [c for c in lit.children if isinstance(c, nodes.literal)]
empty = [c for c in inner if c.astext() == '']
print('astext=%r compound=%s n_inner=%d n_empty=%d' % (lit.astext(), 'compound' in lit.get('classes', []), len(inner), len(empty)))
ok = (lit.astext() == 'x-' and 'compound' not in lit.get('classes', []) and len(inner) == 0 and len(empty) == 0)
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_dash_standalone.py`

```python
"""POSITIVE CONTROL. Req 1.1/1.2/1.3: standalone `-` renders as ONE kbd, text '-',
no nested <kbd>, no empty keystroke element.
Patched: HOLDS. Base: FAILS (splits into empty kbds around a separator)."""
import sys, warnings
warnings.filterwarnings('ignore')
from docutils import nodes, utils, frontend
from sphinx.builders.html.transforms import KeyboardTransform


def run_kbd(text):
    settings = frontend.OptionParser(components=()).get_default_values()
    doc = utils.new_document('t', settings)
    lit = nodes.literal('', text, classes=['kbd'])
    p = nodes.paragraph('', ''); p += lit; doc += p
    KeyboardTransform(doc).run()
    return lit


lit = run_kbd('-')
inner = [c for c in lit.children if isinstance(c, nodes.literal)]
empty = [c for c in inner if c.astext() == '']
print('astext=%r classes=%r n_inner_kbd=%d n_empty_kbd=%d children=%r'
      % (lit.astext(), lit.get('classes'), len(inner), len(empty),
         [ (type(c).__name__, c.astext()) for c in lit.children ]))

ok = (lit.astext() == '-'
      and 'compound' not in lit.get('classes', [])
      and len(inner) == 0
      and len(empty) == 0)
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

KeyboardTransform in the instance image uses builders=('html',) and does NOT append a 'compound' class (older than), so probe_4 checks the split structure + inner 'kbd' class preservation rather than a compound class.

8 probes, all HOLD on gold-patched tree:
- probe_1 (POSITIVE CONTROL, Req 1.1/1.2/1.3): standalone `-` -> single keystroke text '-', 0 inner <kbd>, 0 empty kbd. HOLDS patched, FAILS at base (base gives ['',...,''] with 2 empty kbds). Discriminates.
- probe_2 (Req 2.4/2.1, hidden F2P `Alt+^`): inner [Alt,^], sep ['+'], no empty trailing. HOLDS patched; FAILS base.
- probe_3 (Req 2.4 public example `Shift-+`): inner [Shift,+], sep ['-'], no empty. HOLDS patched; FAILS base.
- probe_4 (Req 4.1/4.5 regression `Control+X`): inner [Control,X] each with 'kbd' class, sep ['+'], LTR order. HOLDS patched AND base (regression preserved).
- probe_5 (Req 4.2 `space`): single keystroke unchanged, no split. HOLDS both.
- probe_6 (Req 3.1/4.3 `M-x  M-s`): inner [M,x,M,s], seps ['-','  ','-'], no empty. HOLDS both.
- probe_7 (Req 2.2 leading sep `+x`): no split, single keystroke '+x'. HOLDS patched; FAILS base (base -> empty leading kbd).
- probe_8 (Req 2.3 trailing sep `x-`): no split, single keystroke 'x-'. HOLDS patched; FAILS base.

Weak candidate exercised: naive_lookbehind_only replaces the gold `(?<=.)(...)(?=.)` with lookbehind-only `(?<=.)(...)` — a plausibly-wrong reading that only suppresses LEADING empty keystrokes but still splits on trailing separators. REJECTED by the suite: probe_2 (Alt+^ -> 2 empty kbds), probe_3 (Shift-+ -> 2 empty), probe_8 (x- -> empty trailing). This demonstrates the suite discriminates wrong implementations that satisfy a subset of the requirements. No requirements-conforming-but-wrong candidate found.

Verdict SOUND: >=5 distinct probes covering behavioral SHALLs, boundary cases (leading/trailing/standalone sep), and the 'SHALL keep' regressions (Control+X, space, M-x M-s); positive control discriminates base vs patched; the one weak candidate is rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1_dash_standalone.py`, `probe_2_alt_caret.py`, `probe_3_shift_plus.py`, `probe_4_regression_controlx.py`, `probe_5_single_space.py`, `probe_6_whitespace_seq.py`, `probe_7_leading_sep.py`, `probe_8_trailing_sep.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_dash_standalone.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_dash_standalone.py` → holds on the patched tree (good)

Attack 2 — `probe_2_alt_caret.py` → holds on the patched tree (good)

Attack 3 — `probe_3_shift_plus.py` → holds on the patched tree (good)

Attack 4 — `probe_4_regression_controlx.py` → holds on the patched tree (good)

Attack 5 — `probe_5_single_space.py` → holds on the patched tree (good)

Attack 6 — `probe_6_whitespace_seq.py` → holds on the patched tree (good)

Attack 7 — `probe_7_leading_sep.py` → holds on the patched tree (good)

Attack 8 — `probe_8_trailing_sep.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_dash_standalone.py`

```python
"""POSITIVE CONTROL. Req 1.1/1.2/1.3: standalone `-` renders as ONE kbd, text '-',
no nested <kbd>, no empty keystroke element.
Patched: HOLDS. Base: FAILS (splits into empty kbds around a separator)."""
import sys, warnings
warnings.filterwarnings('ignore')
from docutils import nodes, utils, frontend
from sphinx.builders.html.transforms import KeyboardTransform


def run_kbd(text):
    settings = frontend.OptionParser(components=()).get_default_values()
    doc = utils.new_document('t', settings)
    lit = nodes.literal('', text, classes=['kbd'])
    p = nodes.paragraph('', ''); p += lit; doc += p
    KeyboardTransform(doc).run()
    return lit


lit = run_kbd('-')
inner = [c for c in lit.children if isinstance(c, nodes.literal)]
empty = [c for c in inner if c.astext() == '']
print('astext=%r classes=%r n_inner_kbd=%d n_empty_kbd=%d children=%r'
      % (lit.astext(), lit.get('classes'), len(inner), len(empty),
         [ (type(c).__name__, c.astext()) for c in lit.children ]))

ok = (lit.astext() == '-'
      and 'compound' not in lit.get('classes', [])
      and len(inner) == 0
      and len(empty) == 0)
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

KeyboardTransform in the instance image uses builders=('html',) and does NOT append a 'compound' class (older than), so probe_4 checks the split structure + inner 'kbd' class preservation rather than a compound class.

8 probes, all HOLD on gold-patched tree:
- probe_1 (POSITIVE CONTROL, Req 1.1/1.2/1.3): standalone `-` -> single keystroke text '-', 0 inner <kbd>, 0 empty kbd. HOLDS patched, FAILS at base (base gives ['',...,''] with 2 empty kbds). Discriminates.
- probe_2 (Req 2.4/2.1, hidden F2P `Alt+^`): inner [Alt,^], sep ['+'], no empty trailing. HOLDS patched; FAILS base.
- probe_3 (Req 2.4 public example `Shift-+`): inner [Shift,+], sep ['-'], no empty. HOLDS patched; FAILS base.
- probe_4 (Req 4.1/4.5 regression `Control+X`): inner [Control,X] each with 'kbd' class, sep ['+'], LTR order. HOLDS patched AND base (regression preserved).
- probe_5 (Req 4.2 `space`): single keystroke unchanged, no split. HOLDS both.
- probe_6 (Req 3.1/4.3 `M-x  M-s`): inner [M,x,M,s], seps ['-','  ','-'], no empty. HOLDS both.
- probe_7 (Req 2.2 leading sep `+x`): no split, single keystroke '+x'. HOLDS patched; FAILS base (base -> empty leading kbd).
- probe_8 (Req 2.3 trailing sep `x-`): no split, single keystroke 'x-'. HOLDS patched; FAILS base.

Weak candidate exercised: naive_lookbehind_only replaces the gold `(?<=.)(...)(?=.)` with lookbehind-only `(?<=.)(...)` — a plausibly-wrong reading that only suppresses LEADING empty keystrokes but still splits on trailing separators. REJECTED by the suite: probe_2 (Alt+^ -> 2 empty kbds), probe_3 (Shift-+ -> 2 empty), probe_8 (x- -> empty trailing). This demonstrates the suite discriminates wrong implementations that satisfy a subset of the requirements. No requirements-conforming-but-wrong candidate found.

Verdict SOUND: >=5 distinct probes covering behavioral SHALLs, boundary cases (leading/trailing/standalone sep), and the 'SHALL keep' regressions (Control+X, space, M-x M-s); positive control discriminates base vs patched; the one weak candidate is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a one-line regex change adding lookbehind/lookahead so a separator only splits when it has a char on both sides. Requirements pin exactly this changed observable behavior (position-aware separator splitting), not a narrow branch/helper slice. The multiwords_keys logic is untouched by the patch and not the subject of the requirements. probe.py (split-based) ran green on the gold-patched image confirming all listed cases; a second full-render probe failed only due to docutils Transform.__init__ needing a real document object, unrelated to behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe the KeyboardTransform behavior generically. All separator chars (-, +, ^), the standalone-separator bug, blank-keystroke output, and the Shift-+ / trailing-separator-as-key case are explicit in the public problem_statement. Naming sphinx/builders/html/transforms.py and KeyboardTransform is legitimate localization. The hidden FAIL_TO_PASS `Alt+^` is only covered as the generic 'compound keystroke whose final keystroke is a separator char' behavior (Req 2.4) — no 'Alt' identifier, no test id, no case-list mirroring the parametrization. Example `M-x  M-y` differs from the actual test's `M-x  M-s`, and Control+X/space are pre-existing common regression examples, not copied test code. The 'both sides' positional rule is a behavioral restatement of the fix, not the verbatim gold regex `(?<=.)(...)(?=.)`. No test paths/names/ids, quoted test or gold code, or fix-invented identifiers present.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
