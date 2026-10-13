# P2 adversarial audit — django__django-16527

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control / Req1.2: lacking add permission => show_save_as_new False,
even with change permission. Holds patched, fails at base (base gated on change perm)."""
import sys
from django.contrib.admin.templatetags.admin_modify import submit_row

ctx = {
    "add": False, "change": True, "is_popup": False, "save_as": True,
    "has_add_permission": False, "has_change_permission": True,
    "has_view_permission": True, "has_editable_inline_admin_formsets": False,
    "has_delete_permission": True,
}
out = submit_row(dict(ctx))
val = out["show_save_as_new"]
print("show_save_as_new (no add perm, has change perm):", val)
sys.exit(0 if val is False else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.1 & 1.3: show_save_as_new True iff not popup & add perm & change & save_as,
independent of has_change_permission. Test with change perm False."""
import sys
from django.contrib.admin.templatetags.admin_modify import submit_row

base = {
    "add": False, "change": True, "is_popup": False, "save_as": True,
    "has_add_permission": True, "has_change_permission": False,
    "has_view_permission": True, "has_editable_inline_admin_formsets": False,
    "has_delete_permission": True,
}
ok = True
# has add, not popup, change, save_as, no change perm => True
v = submit_row(dict(base))["show_save_as_new"]
print("add perm, no change perm:", v); ok &= (v is True)
# flip change perm to True => still True (independence)
b2 = dict(base); b2["has_change_permission"] = True
v2 = submit_row(b2)["show_save_as_new"]
print("add perm, change perm True:", v2); ok &= (v2 is True)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.4 & 1.5: popup, or not change, or not save_as => show_save_as_new False."""
import sys
from django.contrib.admin.templatetags.admin_modify import submit_row

base = {
    "add": False, "change": True, "is_popup": False, "save_as": True,
    "has_add_permission": True, "has_change_permission": True,
    "has_view_permission": True, "has_editable_inline_admin_formsets": False,
    "has_delete_permission": True,
}
ok = True
for k in ["is_popup"]:
    b = dict(base); b[k] = True
    v = submit_row(b)["show_save_as_new"]; print(f"{k}=True:", v); ok &= (v is False)
for k in ["change", "save_as"]:
    b = dict(base); b[k] = False
    v = submit_row(b)["show_save_as_new"]; print(f"{k}=False:", v); ok &= (v is False)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2: regression flags unchanged. can_save, show_save, show_close,
show_save_and_add_another, show_save_and_continue, can_change, show_delete_link."""
import sys
from django.contrib.admin.templatetags.admin_modify import submit_row

def can_save(c):
    return ((c["has_change_permission"] and c["change"])
            or (c["has_add_permission"] and c["add"])
            or c["has_editable_inline_admin_formsets"])

ok = True
cases = [
    {"add":False,"change":True,"is_popup":False,"save_as":True,"has_add_permission":True,
     "has_change_permission":True,"has_view_permission":True,
     "has_editable_inline_admin_formsets":False,"has_delete_permission":True},
    {"add":True,"change":False,"is_popup":False,"save_as":False,"has_add_permission":True,
     "has_change_permission":False,"has_view_permission":True,
     "has_editable_inline_admin_formsets":True,"has_delete_permission":False},
    {"add":False,"change":True,"is_popup":True,"save_as":False,"has_add_permission":False,
     "has_change_permission":True,"has_view_permission":False,
     "has_editable_inline_admin_formsets":False,"has_delete_permission":True},
]
for i, c in enumerate(cases):
    out = submit_row(dict(c))
    cs = can_save(c)
    exp_show_save = (c.get("show_save",True) and cs)
    exp_close = not exp_show_save
    exp_saa = (c["has_add_permission"] and not c["is_popup"]
               and (not c["save_as"] or c["add"]) and cs and c.get("show_save_and_add_another",True))
    exp_sac = (not c["is_popup"] and cs and c["has_view_permission"] and c.get("show_save_and_continue",True))
    exp_can_change = c["has_change_permission"] or c["has_editable_inline_admin_formsets"]
    exp_del = (not c["is_popup"] and c["has_delete_permission"] and c["change"] and c.get("show_delete",True))
    checks = {
        "show_save": (out["show_save"], exp_show_save),
        "show_close": (out["show_close"], exp_close),
        "show_save_and_add_another": (out["show_save_and_add_another"], exp_saa),
        "show_save_and_continue": (out["show_save_and_continue"], exp_sac),
        "can_change": (out["can_change"], exp_can_change),
        "show_delete_link": (out["show_delete_link"], exp_del),
    }
    for name,(got,exp) in checks.items():
        good = bool(got)==bool(exp)
        ok &= good
        if not good:
            print(f"case{i} {name}: got={got} exp={exp} MISMATCH")
        else:
            print(f"case{i} {name}: {got} OK")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req2.8 & Req3: context preserved, and defaults for optional toggles.
Preserve all incoming keys; missing show_save/show_save_and_add_another/
show_save_and_continue/show_delete default to True."""
import sys
from django.contrib.admin.templatetags.admin_modify import submit_row

ctx = {
    "add": False, "change": True, "is_popup": False, "save_as": False,
    "has_add_permission": True, "has_change_permission": True,
    "has_view_permission": True, "has_editable_inline_admin_formsets": False,
    "has_delete_permission": True,
    "custom_marker": "PRESERVE_ME",
}
out = submit_row(dict(ctx))
def get(o, k):
    try: return o[k]
    except Exception:
        return o.get(k)
ok = True
# context preservation: original custom key must survive
pres = get(out, "custom_marker")
print("custom_marker preserved:", pres); ok &= (pres == "PRESERVE_ME")
# defaults: none of the toggles present in ctx (all absent) => treated True
# show_save default True + can_save True => show_save True
v = out["show_save"]; print("show_save (default True path):", v); ok &= (v is True)
# show_delete_link default True path (not popup, delete perm, change) => True
v2 = out["show_delete_link"]; print("show_delete_link (default show_delete):", v2); ok &= (v2 is True)
# show_save_and_continue default True path
v3 = out["show_save_and_continue"]; print("show_save_and_continue default:", v3); ok &= (v3 is True)
# explicit show_delete=False overrides default
c2 = dict(ctx); c2["show_delete"] = False
v4 = submit_row(c2)["show_delete_link"]; print("show_delete=False:", v4); ok &= (v4 is False)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1.2: lacking add permission => show_save_as_new False,
even with change permission. Holds patched, fails at base (base gated on change perm)."""
import sys
from django.contrib.admin.templatetags.admin_modify import submit_row

ctx = {
    "add": False, "change": True, "is_popup": False, "save_as": True,
    "has_add_permission": False, "has_change_permission": True,
    "has_view_permission": True, "has_editable_inline_admin_formsets": False,
    "has_delete_permission": True,
}
out = submit_row(dict(ctx))
val = out["show_save_as_new"]
print("show_save_as_new (no add perm, has change perm):", val)
sys.exit(0 if val is False else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes cover Req1.1-1.5 (show_save_as_new = not is_popup and has_add_permission and change and save_as, independent of has_change_permission), Req2.1-2.8 (can_save + show_save/show_close/show_save_and_add_another/show_save_and_continue/can_change/show_delete_link recomputed vs oracle, context preservation of custom key), and Req3.1-3.4 (optional toggle defaults). All 5 HOLD on the gold-patched tree. Positive control probe_1 (no add perm + has change perm => show_save_as_new must be False) FAILS at base (base gates on change perm, yielding True) and HOLDS patched — discriminating power confirmed. Two wrong-fix candidates constructed and run under --patch: weak_and (gate on add AND change) is REJECTED by probe_2 (add perm without change perm wrongly hides the button); weak_or (add OR change) is REJECTED by probe_1 (no add perm but change perm wrongly shows it). Suite discriminates both wrong readings; no requirements-conforming candidate found that would fail hidden tests. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control / Req1.2: lacking add permission => show_save_as_new False,
even with change permission. Holds patched, fails at base (base gated on change perm)."""
import sys
from django.contrib.admin.templatetags.admin_modify import submit_row

ctx = {
    "add": False, "change": True, "is_popup": False, "save_as": True,
    "has_add_permission": False, "has_change_permission": True,
    "has_view_permission": True, "has_editable_inline_admin_formsets": False,
    "has_delete_permission": True,
}
out = submit_row(dict(ctx))
val = out["show_save_as_new"]
print("show_save_as_new (no add perm, has change perm):", val)
sys.exit(0 if val is False else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes cover Req1.1-1.5 (show_save_as_new = not is_popup and has_add_permission and change and save_as, independent of has_change_permission), Req2.1-2.8 (can_save + show_save/show_close/show_save_and_add_another/show_save_and_continue/can_change/show_delete_link recomputed vs oracle, context preservation of custom key), and Req3.1-3.4 (optional toggle defaults). All 5 HOLD on the gold-patched tree. Positive control probe_1 (no add perm + has change perm => show_save_as_new must be False) FAILS at base (base gates on change perm, yielding True) and HOLDS patched — discriminating power confirmed. Two wrong-fix candidates constructed and run under --patch: weak_and (gate on add AND change) is REJECTED by probe_2 (add perm without change perm wrongly hides the button); weak_or (add OR change) is REJECTED by probe_1 (no add perm but change perm wrongly shows it). Suite discriminates both wrong readings; no requirements-conforming candidate found that would fail hidden tests. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified by reading the full patched submit_row source in the instance image and by a 5-case probe (exit 0, ALL OK). The modeling boundary is correct: requirements pin the changed observable behavior of show_save_as_new rather than a narrow slice, and correctly hold the sibling flags unchanged. Req 2.4's phrasing 'either save-as is disabled or the form is in add mode' faithfully renders (not save_as or add). Req 2.8 matches ctx=Context(context); ctx.update(...); return ctx.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe submit_row behavior in admin_modify.py. The function/module/line, the variable has_add_permission, and the fix itself are ALL public in the problem_statement (which quotes the corrected code). The document names only pre-existing context keys (show_save, show_close, can_change, has_*_permission, etc.) that are visible in the public base-commit source — legitimate localization/behavioral translation. No test names, test file path (tests/admin_views/test_templatetags.py), test helper identifiers (get_perm, get_permission_codename, reverse node-ids, UserAdmin/save_as setup), or fix-invented identifiers appear. The hidden F2P test is a single non-parametrized method; the requirement enumerations decompose the boolean logic of the function, not the test's cases (the test only exercises two permission combos and cannot even distinguish criterion 1.3's independence-from-change-permission claim). No case enumeration mirrors test parametrization. Behavior translated to requirements is exactly the intended purpose.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
