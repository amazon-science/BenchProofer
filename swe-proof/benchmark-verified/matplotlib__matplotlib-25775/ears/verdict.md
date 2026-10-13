# P2 adversarial audit — matplotlib__matplotlib-25775

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1_setget.py`, `probe_2_stale.py`, `probe_3_default_rc.py`, `probe_4_ctor_kw.py`, `probe_5_annotation.py`, `probe_6_update_from.py`, `probe_7_draw_honors.py`, `probe_8_gc_exposes.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_7_draw_honors.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_setget.py` → holds on the patched tree (good)

```python
# Req1: get/set roundtrip, boolean report, latest-wins, .1..5
import matplotlib.pyplot as plt
fig = plt.figure()
t = fig.text(0.5, 0.5, "hello")
# assign True
t.set_antialiased(True)
v1 = t.get_antialiased()
# assign False
t.set_antialiased(False)
v2 = t.get_antialiased()
# assign again True (latest wins)
t.set_antialiased(True)
v3 = t.get_antialiased()
print("after True:", v1, "after False:", v2, "after True again:", v3)
ok = (v1 is True or v1 == True) and (v2 is False or v2 == False) and (v3 == True)
ok = ok and isinstance(v2, (bool,)) and isinstance(v3, (bool,))
assert ok, "get/set roundtrip failed"
print("PASS")
```

Attack 2 — `probe_2_stale.py` → holds on the patched tree (good)

```python
# Req1.6: changing antialiased marks stale
import matplotlib.pyplot as plt
fig = plt.figure()
fig.canvas.draw()  # clear stale
t = fig.text(0.5, 0.5, "hello")
t.stale = False
t.set_antialiased(not t.get_antialiased())
print("stale after set:", t.stale)
assert t.stale is True, "not marked stale"
print("PASS")
```

Attack 3 — `probe_3_default_rc.py` → holds on the patched tree (good)

```python
# Req2.1/2.5: default equals rcParams, not forced to fixed boolean, for both rc values
import matplotlib as mpl
import matplotlib.pyplot as plt
for val in (True, False):
    mpl.rcParams["text.antialiased"] = val
    fig = plt.figure()
    t = fig.text(0.5, 0.5, "x")
    got = t.get_antialiased()
    print("rc=", val, "-> get_antialiased=", got)
    assert got == val, f"default did not track rcParams (rc={val}, got={got})"
    plt.close(fig)
print("PASS")
```

Attack 4 — `probe_4_ctor_kw.py` → holds on the patched tree (good)

```python
# Req2.2/2.3/2.4/2.6: constructor keyword overrides global; latest assignment wins
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.text import Text
# set global to opposite of what we request to prove override
mpl.rcParams["text.antialiased"] = True
t = Text(0.5, 0.5, "x", antialiased=False)
print("ctor False, rc True ->", t.get_antialiased())
assert t.get_antialiased() == False
mpl.rcParams["text.antialiased"] = False
t2 = Text(0.5, 0.5, "x", antialiased=True)
print("ctor True, rc False ->", t2.get_antialiased())
assert t2.get_antialiased() == True
# later assignment overrides ctor value
t2.set_antialiased(False)
assert t2.get_antialiased() == False
print("PASS")
```

Attack 5 — `probe_5_annotation.py` → holds on the patched tree (good)

```python
# Req3: Annotation supports the keyword with same semantics
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.text import Annotation
mpl.rcParams["text.antialiased"] = True
a = Annotation("txt", (0.5,0.5), antialiased=False)
print("ann ctor False rc True ->", a.get_antialiased())
assert a.get_antialiased() == False
a2 = Annotation("txt", (0.5,0.5), antialiased=True)
assert a2.get_antialiased() == True
# default tracks rc
mpl.rcParams["text.antialiased"] = False
a3 = Annotation("txt", (0.5,0.5))
print("ann default rc False ->", a3.get_antialiased())
assert a3.get_antialiased() == False
# reassign
a.set_antialiased(True)
assert a.get_antialiased() == True
print("PASS")
```

Attack 6 — `probe_6_update_from.py` → holds on the patched tree (good)

```python
# Req5.1: update_from copies antialiased
import matplotlib.pyplot as plt
from matplotlib.text import Text
src = Text(0,0,"s", antialiased=False)
dst = Text(0,0,"d", antialiased=True)
assert dst.get_antialiased() == True
dst.update_from(src)
print("dst after update_from(src False) ->", dst.get_antialiased())
assert dst.get_antialiased() == False, "update_from did not copy antialiased"
print("PASS")
```

Attack 7 — `probe_7_draw_honors.py` → holds on the patched tree (good)

```python
# Req4.1/4.2/4.3/4.5 POSITIVE CONTROL: drawing honors per-object antialiased.
# Rendering with antialiased=False must produce output IDENTICAL to global rc False,
# and DIFFERENT from antialiased=True. Base lacks per-object control -> fails.
import io
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

def render(rc_aa, obj_aa):
    mpl.rcParams["text.antialiased"] = rc_aa
    fig = plt.figure(figsize=(2,1), dpi=100)
    kw = {} if obj_aa is None else {"antialiased": obj_aa}
    fig.text(0.1, 0.4, "Ag", size=20, **kw)
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    import matplotlib.image as mimg
    return mimg.imread(buf)

# per-object False, global True  vs  global False no per-object -> identical (Req4.2)
img_obj_false = render(True, False)
img_glob_false = render(False, None)
same_false = np.array_equal(img_obj_false, img_glob_false)

# per-object True vs per-object False -> different (drawing honors it)
img_true = render(False, True)
img_false = render(True, False)
differ = not np.array_equal(img_true, img_false)

print("per-object False == global False:", same_false)
print("per-object True != per-object False:", differ)
assert same_false, "Req4.2 violated: per-object False output != global False output"
assert differ, "drawing does not honor per-object antialiased (True==False)"
print("PASS")
```

Attack 8 — `probe_8_gc_exposes.py` → holds on the patched tree (good)

```python
# Req4.4: GraphicsContext exposes the antialiased state it was given (get_antialiased roundtrip)
from matplotlib.backend_bases import GraphicsContextBase
gc = GraphicsContextBase()
gc.set_antialiased(False)
print("gc after set False ->", gc.get_antialiased())
assert gc.get_antialiased() in (0, False), "gc did not expose False"
gc.set_antialiased(True)
print("gc after set True ->", gc.get_antialiased())
assert gc.get_antialiased() in (1, True), "gc did not expose True"
print("PASS")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_7_draw_honors.py`

```python
# Req4.1/4.2/4.3/4.5 POSITIVE CONTROL: drawing honors per-object antialiased.
# Rendering with antialiased=False must produce output IDENTICAL to global rc False,
# and DIFFERENT from antialiased=True. Base lacks per-object control -> fails.
import io
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

def render(rc_aa, obj_aa):
    mpl.rcParams["text.antialiased"] = rc_aa
    fig = plt.figure(figsize=(2,1), dpi=100)
    kw = {} if obj_aa is None else {"antialiased": obj_aa}
    fig.text(0.1, 0.4, "Ag", size=20, **kw)
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    import matplotlib.image as mimg
    return mimg.imread(buf)

# per-object False, global True  vs  global False no per-object -> identical (Req4.2)
img_obj_false = render(True, False)
img_glob_false = render(False, None)
same_false = np.array_equal(img_obj_false, img_glob_false)

# per-object True vs per-object False -> different (drawing honors it)
img_true = render(False, True)
img_false = render(True, False)
differ = not np.array_equal(img_true, img_false)

print("per-object False == global False:", same_false)
print("per-object True != per-object False:", differ)
assert same_false, "Req4.2 violated: per-object False output != global False output"
assert differ, "drawing does not honor per-object antialiased (True==False)"
print("PASS")
```

Prepatch bug re-encoded as an attack: `True`.

8 probes cover Reqs 1-6. All HOLD on gold-patched tree. Positive control = probe_7 (Req4.1/4.2/4.3/4.5, Agg/PNG drawing honors per-object antialiased: per-object False output identical to global-False, and per-object True != False); it FAILS at base ('Text' object has no property 'antialiased') and HOLDS patched -> discriminates.

Probe->criterion map:
- probe_1_setget: Req1.1-1.5 get/set roundtrip, boolean report, latest-wins.
- probe_2_stale: Req1.6 set marks stale.
- probe_3_default_rc: Req2.1/2.5 default tracks rcParams for both True/False (not forced constant).
- probe_4_ctor_kw: Req2.2/2.3/2.4/2.6 ctor keyword overrides global; later assignment wins.
- probe_5_annotation: Req3.1-3.5 Annotation keyword semantics + default + reassign.
- probe_6_update_from: Req5.1 update_from copies antialiased.
- probe_7_draw_honors: Req4.1/4.2/4.3/4.5 (PNG/Agg drawing).
- probe_8_gc_exposes: Req4.4 GraphicsContext exposes given antialiased (note: gc.get_antialiased already exists at base, so this probe holds at base too; it is a supporting regression probe, not discriminating).

Candidate patch 'partial_no_agg_fix' = gold patch MINUS the backend_agg.py one-line change (still consults rcParams['text.antialiased'] at glyph time). This is the lazy/partial fix a weak reading permits (full public API + cairo, no Agg raster wiring). Probes 1-6,8 HOLD under it but probe_7 REJECTS it (Req4.2 violated: per-object False PNG output != global-False output). This demonstrates the suite discriminates a wrong implementation on the raster-output requirement, and the requirements are not too weak on that axis. Verdict SOUND: >=5 probes hold on patched, positive control discriminates base vs patched, and a plausibly-wrong candidate is rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1_setget.py`, `probe_2_stale.py`, `probe_3_default_rc.py`, `probe_4_ctor_kw.py`, `probe_5_annotation.py`, `probe_6_update_from.py`, `probe_7_draw_honors.py`, `probe_8_gc_exposes.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_7_draw_honors.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_setget.py` → holds on the patched tree (good)

Attack 2 — `probe_2_stale.py` → holds on the patched tree (good)

Attack 3 — `probe_3_default_rc.py` → holds on the patched tree (good)

Attack 4 — `probe_4_ctor_kw.py` → holds on the patched tree (good)

Attack 5 — `probe_5_annotation.py` → holds on the patched tree (good)

Attack 6 — `probe_6_update_from.py` → holds on the patched tree (good)

Attack 7 — `probe_7_draw_honors.py` → holds on the patched tree (good)

Attack 8 — `probe_8_gc_exposes.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_7_draw_honors.py`

```python
# Req4.1/4.2/4.3/4.5 POSITIVE CONTROL: drawing honors per-object antialiased.
# Rendering with antialiased=False must produce output IDENTICAL to global rc False,
# and DIFFERENT from antialiased=True. Base lacks per-object control -> fails.
import io
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

def render(rc_aa, obj_aa):
    mpl.rcParams["text.antialiased"] = rc_aa
    fig = plt.figure(figsize=(2,1), dpi=100)
    kw = {} if obj_aa is None else {"antialiased": obj_aa}
    fig.text(0.1, 0.4, "Ag", size=20, **kw)
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    import matplotlib.image as mimg
    return mimg.imread(buf)

# per-object False, global True  vs  global False no per-object -> identical (Req4.2)
img_obj_false = render(True, False)
img_glob_false = render(False, None)
same_false = np.array_equal(img_obj_false, img_glob_false)

# per-object True vs per-object False -> different (drawing honors it)
img_true = render(False, True)
img_false = render(True, False)
differ = not np.array_equal(img_true, img_false)

print("per-object False == global False:", same_false)
print("per-object True != per-object False:", differ)
assert same_false, "Req4.2 violated: per-object False output != global False output"
assert differ, "drawing does not honor per-object antialiased (True==False)"
print("PASS")
```

Prepatch bug re-encoded as an attack: `True`.

8 probes cover Reqs 1-6. All HOLD on gold-patched tree. Positive control = probe_7 (Req4.1/4.2/4.3/4.5, Agg/PNG drawing honors per-object antialiased: per-object False output identical to global-False, and per-object True != False); it FAILS at base ('Text' object has no property 'antialiased') and HOLDS patched -> discriminates.

Probe->criterion map:
- probe_1_setget: Req1.1-1.5 get/set roundtrip, boolean report, latest-wins.
- probe_2_stale: Req1.6 set marks stale.
- probe_3_default_rc: Req2.1/2.5 default tracks rcParams for both True/False (not forced constant).
- probe_4_ctor_kw: Req2.2/2.3/2.4/2.6 ctor keyword overrides global; later assignment wins.
- probe_5_annotation: Req3.1-3.5 Annotation keyword semantics + default + reassign.
- probe_6_update_from: Req5.1 update_from copies antialiased.
- probe_7_draw_honors: Req4.1/4.2/4.3/4.5 (PNG/Agg drawing).
- probe_8_gc_exposes: Req4.4 GraphicsContext exposes given antialiased (note: gc.get_antialiased already exists at base, so this probe holds at base too; it is a supporting regression probe, not discriminating).

Candidate patch 'partial_no_agg_fix' = gold patch MINUS the backend_agg.py one-line change (still consults rcParams['text.antialiased'] at glyph time). This is the lazy/partial fix a weak reading permits (full public API + cairo, no Agg raster wiring). Probes 1-6,8 HOLD under it but probe_7 REJECTS it (Req4.2 violated: per-object False PNG output != global-False output). This demonstrates the suite discriminates a wrong implementation on the raster-output requirement, and the requirements are not too weak on that axis. Verdict SOUND: >=5 probes hold on patched, positive control discriminates base vs patched, and a plausibly-wrong candidate is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds Text._antialiased (init to rcParams['text.antialiased']), set/get_antialiased with stale=True, antialiased ctor kwarg threaded via _reset_visual_defaults (only applied if not None -> unspecified follows global), update_from copies _antialiased, draw() calls gc.set_antialiased(self._antialiased); Agg draw_text uses gc.get_antialiased() instead of rcParams; Cairo adds GC get_antialiased and uses it. Requirements 1-6 map exactly onto these observable behaviors and the F2P tests (test_set/get_antialiased, test_annotation_antialiased, test_text_antialiased_{off,on}_default_vs_manual[png/pdf]). Boundary is the changed observable behavior (per-object aa read/set + drawing honoring it), not a narrow slice. Req4.5's PDF identity confirmed empirically even though patch touches only Agg/Cairo, because the identity is between two paths that render identically.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes per-object antialiasing behavior for Text/Annotation, the constructor keyword, default-from-rcParams fallback, drawing through the GraphicsContext, gc.get_antialiased(), update_from copy, and stale-on-change. All of this is either public in the problem_statement/hints (get/set_antialiased on Text, adjust Annotations, route through GraphicsContext, AGG+Cairo backends) or a legitimate localization/behavioral translation of the gold patch. No test names, no test file path, no parametrization ids, no test fixture literals ('foo\nbar', '6 inches x 2 inches'), no private-attr assertions, and no verbatim gold lines are transmitted. New identifiers named (get_antialiased/set_antialiased, antialiased kwarg) are directly implied by the public issue. Req 4.5's PNG/PDF mention tracks the check_figures_equal default extensions but is expressed as genuine raster/vector behavior, not a reconstruction of the [png]/[pdf] parametrization. Translating what tests check into behavioral requirements is the intended purpose; the defect (transmitting the tests themselves) is absent.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
