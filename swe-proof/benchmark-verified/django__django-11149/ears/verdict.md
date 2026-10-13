# P2 adversarial audit — django__django-11149

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
"""Probe for Req 1 crit 4 (POSITIVE CONTROL): a user holding only the target's
VIEW permission (not change) must get add/change/delete == False on an
auto-created M2M through inline.

At base this FAILS (add/change/delete reuse the view decision -> True).
Patched: all three are False. Discriminating.
"""
import sys


def build_inline():
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    import django
    django.setup()
    from django.contrib.admin.options import InlineModelAdmin

    class TMeta:
        app_label = "app"
        model_name = "target"

    class Target:
        _meta = TMeta()

    class Parent:
        pass

    class RF:
        def __init__(self, model):
            self.model = model

    class F:
        def __init__(self, rf):
            self.remote_field = rf

    class ThroughMeta:
        auto_created = True
        fields = [F(None), F(RF(Parent)), F(RF(Target))]

    inline = InlineModelAdmin.__new__(InlineModelAdmin)
    inline.parent_model = Parent
    inline.opts = ThroughMeta()
    return inline, Target._meta


class User:
    def __init__(self, held):
        self._held = set(held)

    def has_perm(self, p):
        return p in self._held


class Req:
    def __init__(self, held):
        self.user = User(held)


def main():
    from django.contrib.auth import get_permission_codename
    inline, tmeta = build_inline()
    view_perm = "%s.%s" % (tmeta.app_label, get_permission_codename("view", tmeta))
    req = Req([view_perm])  # view only, NOT change

    add = inline.has_add_permission(req, None)
    change = inline.has_change_permission(req, None)
    delete = inline.has_delete_permission(req, None)
    view = inline.has_view_permission(req, None)
    print("view-only user: add=%r change=%r delete=%r view=%r" % (add, change, delete, view))
    ok = (add is False and change is False and delete is False and view is True)
    if not ok:
        print("VIOLATION: view-only should give add/change/delete=False, view=True")
        return 1
    print("OK: view-only -> no edit, but can view")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Probe for Req 1 crits 1-3 & Req 4 crit 3: holding the target's CHANGE
permission makes add/change/delete (and view) all True. Also the "iff":
holding change but NOT view still yields add/change/delete=True.
"""
import sys


def build_inline():
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    import django
    django.setup()
    from django.contrib.admin.options import InlineModelAdmin

    class TMeta:
        app_label = "app"
        model_name = "target"

    class Target:
        _meta = TMeta()

    class Parent:
        pass

    class RF:
        def __init__(self, model):
            self.model = model

    class F:
        def __init__(self, rf):
            self.remote_field = rf

    class ThroughMeta:
        auto_created = True
        fields = [F(None), F(RF(Parent)), F(RF(Target))]

    inline = InlineModelAdmin.__new__(InlineModelAdmin)
    inline.parent_model = Parent
    inline.opts = ThroughMeta()
    return inline, Target._meta


class User:
    def __init__(self, held):
        self._held = set(held)

    def has_perm(self, p):
        return p in self._held


class Req:
    def __init__(self, held):
        self.user = User(held)


def main():
    from django.contrib.auth import get_permission_codename
    inline, tmeta = build_inline()
    change_perm = "%s.%s" % (tmeta.app_label, get_permission_codename("change", tmeta))
    req = Req([change_perm])  # change only, no explicit view

    add = inline.has_add_permission(req, None)
    change = inline.has_change_permission(req, None)
    delete = inline.has_delete_permission(req, None)
    view = inline.has_view_permission(req, None)
    print("change-only user: add=%r change=%r delete=%r view=%r" % (add, change, delete, view))
    ok = (add is True and change is True and delete is True and view is True)
    if not ok:
        print("VIOLATION: change perm should grant all four decisions True")
        return 1
    print("OK: change -> all four True")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Probe for Req 1 crit 1-3 "only if" direction & Req 2 crit 3: a user holding
NEITHER view nor change on the target (only unrelated perms, e.g. 'add' and
'delete' on the target) gets ALL FOUR decisions False.

This pins that add is derived from the target's CHANGE perm specifically, not
the target's ADD perm; and view requires view-or-change.
"""
import sys


def build_inline():
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    import django
    django.setup()
    from django.contrib.admin.options import InlineModelAdmin

    class TMeta:
        app_label = "app"
        model_name = "target"

    class Target:
        _meta = TMeta()

    class Parent:
        pass

    class RF:
        def __init__(self, model):
            self.model = model

    class F:
        def __init__(self, rf):
            self.remote_field = rf

    class ThroughMeta:
        auto_created = True
        fields = [F(None), F(RF(Parent)), F(RF(Target))]

    inline = InlineModelAdmin.__new__(InlineModelAdmin)
    inline.parent_model = Parent
    inline.opts = ThroughMeta()
    return inline, Target._meta


class User:
    def __init__(self, held):
        self._held = set(held)

    def has_perm(self, p):
        return p in self._held


class Req:
    def __init__(self, held):
        self.user = User(held)


def main():
    from django.contrib.auth import get_permission_codename
    inline, tmeta = build_inline()
    # hold target's add + delete perms, but NOT view or change
    add_perm = "%s.%s" % (tmeta.app_label, get_permission_codename("add", tmeta))
    del_perm = "%s.%s" % (tmeta.app_label, get_permission_codename("delete", tmeta))
    req = Req([add_perm, del_perm])

    add = inline.has_add_permission(req, None)
    change = inline.has_change_permission(req, None)
    delete = inline.has_delete_permission(req, None)
    view = inline.has_view_permission(req, None)
    print("add+delete-only (no view/change): add=%r change=%r delete=%r view=%r"
          % (add, change, delete, view))
    ok = (add is False and change is False and delete is False and view is False)
    if not ok:
        print("VIOLATION: without target view/change all four must be False; "
              "add must NOT be derived from target's add perm")
        return 1
    print("OK: neither view nor change -> all False")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Probe for Req 2 crit 1 & 2: has_view_permission returns True when the user
holds EITHER the target's view perm OR the target's change perm (change implies
view). Checks both directions independently.
"""
import sys


def build_inline():
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    import django
    django.setup()
    from django.contrib.admin.options import InlineModelAdmin

    class TMeta:
        app_label = "app"
        model_name = "target"

    class Target:
        _meta = TMeta()

    class Parent:
        pass

    class RF:
        def __init__(self, model):
            self.model = model

    class F:
        def __init__(self, rf):
            self.remote_field = rf

    class ThroughMeta:
        auto_created = True
        fields = [F(None), F(RF(Parent)), F(RF(Target))]

    inline = InlineModelAdmin.__new__(InlineModelAdmin)
    inline.parent_model = Parent
    inline.opts = ThroughMeta()
    return inline, Target._meta


class User:
    def __init__(self, held):
        self._held = set(held)

    def has_perm(self, p):
        return p in self._held


class Req:
    def __init__(self, held):
        self.user = User(held)


def main():
    from django.contrib.auth import get_permission_codename
    inline, tmeta = build_inline()
    view_perm = "%s.%s" % (tmeta.app_label, get_permission_codename("view", tmeta))
    change_perm = "%s.%s" % (tmeta.app_label, get_permission_codename("change", tmeta))

    v_only = inline.has_view_permission(Req([view_perm]), None)
    c_only = inline.has_view_permission(Req([change_perm]), None)
    print("has_view: view-only=%r change-only=%r" % (v_only, c_only))
    if v_only is not True:
        print("VIOLATION: view perm should grant has_view_permission True")
        return 1
    if c_only is not True:
        print("VIOLATION: change perm should grant has_view_permission True (change implies view)")
        return 1
    print("OK: both view and change grant has_view_permission")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Probe for Req 3 crits 1-3 (SHALL keep / regression): a NON-auto-created
inline defers to the standard ModelAdmin per-model logic. A user holding the
inline model's OWN 'add' perm (but not 'change') must get add=True and
change=False, using the inline's own model — unaffected by the M2M change.
"""
import sys


def build_inline():
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    import django
    django.setup()
    from django.contrib.admin.options import InlineModelAdmin

    class OwnMeta:
        app_label = "app"
        model_name = "inner"
        auto_created = False  # NOT a through model

    inline = InlineModelAdmin.__new__(InlineModelAdmin)
    inline.opts = OwnMeta()
    # For non-auto-created path, admin_site/other attrs aren't used by the
    # superclass perm methods (they only use self.opts + request.user).
    return inline, OwnMeta


class User:
    def __init__(self, held):
        self._held = set(held)

    def has_perm(self, p):
        return p in self._held


class Req:
    def __init__(self, held):
        self.user = User(held)


def main():
    from django.contrib.auth import get_permission_codename
    inline, ometa = build_inline()
    add_perm = "%s.%s" % (ometa.app_label, get_permission_codename("add", ometa))
    change_perm = "%s.%s" % (ometa.app_label, get_permission_codename("change", ometa))
    view_perm = "%s.%s" % (ometa.app_label, get_permission_codename("view", ometa))
    delete_perm = "%s.%s" % (ometa.app_label, get_permission_codename("delete", ometa))

    # user has add on the inline's own model only
    req = Req([add_perm])
    add = inline.has_add_permission(req, None)
    change = inline.has_change_permission(req)
    print("own add-perm only: add=%r change=%r" % (add, change))
    if add is not True:
        print("VIOLATION: non-auto-created inline should grant add via own add perm")
        return 1
    if change is not False:
        print("VIOLATION: non-auto-created change should be False without own change perm")
        return 1

    # sanity: own change perm grants change, own delete grants delete, view grants view
    if inline.has_change_permission(Req([change_perm])) is not True:
        print("VIOLATION: own change perm should grant change")
        return 1
    if inline.has_delete_permission(Req([delete_perm])) is not True:
        print("VIOLATION: own delete perm should grant delete")
        return 1
    if inline.has_view_permission(Req([view_perm])) is not True:
        print("VIOLATION: own view perm should grant view")
        return 1
    # and add perm alone must NOT grant delete/view
    if inline.has_add_permission(Req([add_perm]), None) is not True:
        print("VIOLATION: own add perm should grant add (recheck)")
        return 1
    if inline.has_delete_permission(Req([add_perm])) is not False:
        print("VIOLATION: own add perm must not grant delete on non-through inline")
        return 1
    print("OK: non-auto-created inline follows standard per-own-model rules")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Probe for Req 1 crit 4 (POSITIVE CONTROL): a user holding only the target's
VIEW permission (not change) must get add/change/delete == False on an
auto-created M2M through inline.

At base this FAILS (add/change/delete reuse the view decision -> True).
Patched: all three are False. Discriminating.
"""
import sys


def build_inline():
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    import django
    django.setup()
    from django.contrib.admin.options import InlineModelAdmin

    class TMeta:
        app_label = "app"
        model_name = "target"

    class Target:
        _meta = TMeta()

    class Parent:
        pass

    class RF:
        def __init__(self, model):
            self.model = model

    class F:
        def __init__(self, rf):
            self.remote_field = rf

    class ThroughMeta:
        auto_created = True
        fields = [F(None), F(RF(Parent)), F(RF(Target))]

    inline = InlineModelAdmin.__new__(InlineModelAdmin)
    inline.parent_model = Parent
    inline.opts = ThroughMeta()
    return inline, Target._meta


class User:
    def __init__(self, held):
        self._held = set(held)

    def has_perm(self, p):
        return p in self._held


class Req:
    def __init__(self, held):
        self.user = User(held)


def main():
    from django.contrib.auth import get_permission_codename
    inline, tmeta = build_inline()
    view_perm = "%s.%s" % (tmeta.app_label, get_permission_codename("view", tmeta))
    req = Req([view_perm])  # view only, NOT change

    add = inline.has_add_permission(req, None)
    change = inline.has_change_permission(req, None)
    delete = inline.has_delete_permission(req, None)
    view = inline.has_view_permission(req, None)
    print("view-only user: add=%r change=%r delete=%r view=%r" % (add, change, delete, view))
    ok = (add is False and change is False and delete is False and view is True)
    if not ok:
        print("VIOLATION: view-only should give add/change/delete=False, view=True")
        return 1
    print("OK: view-only -> no edit, but can view")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Prepatch bug re-encoded as an attack: `True`.

Requirements target InlineModelAdmin auto-created-M2M permission derivation (django/contrib/admin/options.py). 5 probes, all HOLD on gold-patched tree; each drives the real patched InlineModelAdmin methods via stub through/target meta + a set-membership has_perm user (same construction as the conformance shadow).

Probe->criterion mapping:
- probe_1 (POSITIVE CONTROL): Req1 crit4 — view-only target perm => add/change/delete=False, view=True. FAILS at base (base reuses view decision => add=change=delete=True) and HOLDS patched. Discriminating.
- probe_2: Req1 crits1-3 & Req4 crit3 — target CHANGE perm alone => all four True (change implies view; no explicit view needed).
- probe_3: Req1 'only-if' & Req2 crit3 — target add+delete perms but no view/change => all four False (pins add derives from target CHANGE, not target add).
- probe_4: Req2 crits1-2 — has_view True for view-only AND for change-only (change implies view).
- probe_5: Req3 crits1-3 (SHALL keep / regression) — non-auto-created inline defers to superclass per-own-model logic: own add perm => add True, change False; own change/delete/view perms grant their own decisions; add perm alone does not grant delete.

CANDIDATE (required floor): weak_addfromadd.diff — the gold patch but with has_add_permission deriving from the target's ['add'] perm instead of ['change']. A plausible weak reading ('add on the inline needs add on the target'). REJECTED by probe_2 (change-only user gets add=False, should be True) and probe_3 (target-add-only user gets add=True, should be False). Confirms the suite discriminates wrong implementations. probes 1/4/5 correctly still hold under it (they don't exercise the add-from-add distinction), so no false rejection.

All needed runs completed cleanly (patch applied cleanly each time).

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
"""Probe for Req 1 crit 4 (POSITIVE CONTROL): a user holding only the target's
VIEW permission (not change) must get add/change/delete == False on an
auto-created M2M through inline.

At base this FAILS (add/change/delete reuse the view decision -> True).
Patched: all three are False. Discriminating.
"""
import sys


def build_inline():
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    import django
    django.setup()
    from django.contrib.admin.options import InlineModelAdmin

    class TMeta:
        app_label = "app"
        model_name = "target"

    class Target:
        _meta = TMeta()

    class Parent:
        pass

    class RF:
        def __init__(self, model):
            self.model = model

    class F:
        def __init__(self, rf):
            self.remote_field = rf

    class ThroughMeta:
        auto_created = True
        fields = [F(None), F(RF(Parent)), F(RF(Target))]

    inline = InlineModelAdmin.__new__(InlineModelAdmin)
    inline.parent_model = Parent
    inline.opts = ThroughMeta()
    return inline, Target._meta


class User:
    def __init__(self, held):
        self._held = set(held)

    def has_perm(self, p):
        return p in self._held


class Req:
    def __init__(self, held):
        self.user = User(held)


def main():
    from django.contrib.auth import get_permission_codename
    inline, tmeta = build_inline()
    view_perm = "%s.%s" % (tmeta.app_label, get_permission_codename("view", tmeta))
    req = Req([view_perm])  # view only, NOT change

    add = inline.has_add_permission(req, None)
    change = inline.has_change_permission(req, None)
    delete = inline.has_delete_permission(req, None)
    view = inline.has_view_permission(req, None)
    print("view-only user: add=%r change=%r delete=%r view=%r" % (add, change, delete, view))
    ok = (add is False and change is False and delete is False and view is True)
    if not ok:
        print("VIOLATION: view-only should give add/change/delete=False, view=True")
        return 1
    print("OK: view-only -> no edit, but can view")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Prepatch bug re-encoded as an attack: `True`.

Requirements target InlineModelAdmin auto-created-M2M permission derivation (django/contrib/admin/options.py). 5 probes, all HOLD on gold-patched tree; each drives the real patched InlineModelAdmin methods via stub through/target meta + a set-membership has_perm user (same construction as the conformance shadow).

Probe->criterion mapping:
- probe_1 (POSITIVE CONTROL): Req1 crit4 — view-only target perm => add/change/delete=False, view=True. FAILS at base (base reuses view decision => add=change=delete=True) and HOLDS patched. Discriminating.
- probe_2: Req1 crits1-3 & Req4 crit3 — target CHANGE perm alone => all four True (change implies view; no explicit view needed).
- probe_3: Req1 'only-if' & Req2 crit3 — target add+delete perms but no view/change => all four False (pins add derives from target CHANGE, not target add).
- probe_4: Req2 crits1-2 — has_view True for view-only AND for change-only (change implies view).
- probe_5: Req3 crits1-3 (SHALL keep / regression) — non-auto-created inline defers to superclass per-own-model logic: own add perm => add True, change False; own change/delete/view perms grant their own decisions; add perm alone does not grant delete.

CANDIDATE (required floor): weak_addfromadd.diff — the gold patch but with has_add_permission deriving from the target's ['add'] perm instead of ['change']. A plausible weak reading ('add on the inline needs add on the target'). REJECTED by probe_2 (change-only user gets add=False, should be True) and probe_3 (target-add-only user gets add=True, should be False). Confirms the suite discriminates wrong implementations. probes 1/4/5 correctly still hold under it (they don't exercise the add-from-add distinction), so no false rejection.

All needed runs completed cleanly (patch applied cleanly each time).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Issue: view-only users could edit M2M inlines because add/change/delete reused has_view_permission. Fix requires the target model's change permission for edit decisions. Requirements 1-4 mirror the diff at the correct observable boundary (the four InlineModelAdmin permission methods for auto_created through models), including the change-implies-view semantics (R2.2) and the unchanged non-auto-created superclass deferral (R3). Probe HOLDS on patched tree; source and behavior both match.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior derivable from the public problem_statement (M2M auto-created through-model inline permissions bug) plus legitimate localization of the change (naming InlineModelAdmin, options.py, the four has_*_permission methods, get_permission_codename, has_perm). All of these are public API / pre-existing repo code visible in the base commit, not fix-invented. The gold patch's invented identifier `_has_any_perms_for_target_model` is NOT named. No test names (test_inline_add_m2m_view_only_perm etc.), no test file paths (tests/admin_inlines/tests.py), no model names from the test fixtures (Author/Book/Photo/Report), no rendered-HTML assertions, no parametrization ids appear. The target-model-finding description ('related model reached through the through model's fields, not the inline's parent model') mirrors the pre-existing public has_view_permission loop, not hidden material. Requirement 4's enumeration ({change} for add/change/delete; {view,change} for view) is a behavioral spec of the fix, not a mirror of the test parametrization (tests are keyed by add/view/change codenames, which the doc translates as behavior). This is behavioral translation, which is the intended task, not test/gold transmission.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
