#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15973.

The bundle models the dependency list `_get_dependencies_for_foreign_key`
returns for a relational field (autodetector.py). The modeled value is a pure
function of five observables (mapping.md):

    targetRef          : model reference (str | concrete) for the relation TARGET
    throughRef         : optional model reference for the intermediary model
    swappableSetting   : optional str (field.swappable_setting)
    scopeApp           : str (owning model's app_label)
    scopeName          : str (owning model's model_name)

ORACLE — the EXACT patched logic (autodetector.py:1409-1427), using the REAL
patched through reference (`field.remote_field.through`) and the real
`resolve_relation` semantics:

    if swappable_setting is not None:
        first = ("__setting__", swappable_setting)
    else:
        first = resolve_relation(target_ref, scope_app, scope_name)
    deps = [first]
    if through_ref is not None:
        deps.append(resolve_relation(through_ref, scope_app, scope_name))   # FIX
    return deps

SHADOW — op-for-op transliteration of implementation_relationDependencies
(Solution.lean), via the modelRefToPair replica.

The `(None, True)` tail of each real 4-tuple is a constant projected out
(mapping.md frame note); both legs compare the `(app_label, object_name)` heads.

Interpretation note: the Lean model leaves the object-name case normalization
ABSTRACT (`opaque lower : String → String`, mapping.md); both the oracle and
the shadow below interpret it as the REAL Python `str.lower` (the binding G-AX
validates), so the comparison exercises the dependency-construction rule under
the true fold.

stdlib-only. Pinned seed: 15973 (also in mapping.md).
"""
import random
import sys

SEED = 15973
N = 150_000


# --- resolve_relation semantics (shared; this is the deep-modeled A-reference,
#     and matches the real callee — independently checked by axiom_check.py) ---
def _resolve(ref, scope_app, scope_name):
    # ref is ("str", s) or ("concrete", app, name)
    kind = ref[0]
    if kind == "concrete":
        return (ref[1], ref[2])
    s = ref[1]
    if s == "self":
        return (scope_app, scope_name)
    if "." in s:
        a, n = s.split(".", 1)
        return (a, n.lower())
    return (scope_app, s.lower())


# --- ORACLE: the patched decision (uses through_ref for the 2nd dep) ----------
def oracle(target_ref, through_ref, swappable, scope_app, scope_name):
    if swappable is not None:
        first = ("__setting__", swappable)
    else:
        first = _resolve(target_ref, scope_app, scope_name)
    deps = [first]
    if through_ref is not None:
        deps.append(_resolve(through_ref, scope_app, scope_name))   # the fix
    return deps


# --- SHADOW of implementation_relationDependencies ----------------------------
def _model_ref_to_pair(ref, scope_app, scope_name):
    # transliteration of modelRefToPair
    if ref[0] == "concrete":
        return (ref[1], ref[2])
    s = ref[1]
    if s == "self":
        return (scope_app, scope_name)
    if "." in s:                       # splitFirstDot
        a, n = s.split(".", 1)
        return (a, n.lower())
    return (scope_app, s.lower())


def shadow(target_ref, through_ref, swappable, scope_app, scope_name):
    if swappable is not None:
        first = ("__setting__", swappable)
    else:
        first = _model_ref_to_pair(target_ref, scope_app, scope_name)
    deps = [first]
    if through_ref is not None:
        deps.append(_model_ref_to_pair(through_ref, scope_app, scope_name))
    return deps


def disagree(tr, thr, sw, sa, sn):
    got = oracle(tr, thr, sw, sa, sn)
    want = shadow(tr, thr, sw, sa, sn)
    if got != want:
        return ((tr, thr, sw, sa, sn), got, want)
    return None


WORDS = ["Author", "Publisher", "Contract", "Model", "self", "X", "MiXeD",
         "a.b", "UPPER"]
APPS = ["authors", "testapp", "contract", "fonte", "variavel", "self"]


def _rand_ref(rng):
    form = rng.randint(0, 3)
    if form == 0:
        return ("str", "self")
    if form == 1:
        return ("str", f"{rng.choice(APPS)}.{rng.choice(WORDS)}")
    if form == 2:
        return ("str", rng.choice(WORDS))
    return ("concrete", rng.choice(APPS), rng.choice(WORDS).lower())


def _edges():
    cases = []
    tgt = ("str", "testapp.Publisher")
    thr = ("str", "contract.Contract")
    # the F2P shape: through in a DIFFERENT app from target
    cases.append((tgt, thr, None, "authors", "author"))
    # no through model -> single dependency
    cases.append((tgt, None, None, "authors", "author"))
    # swappable target + through
    cases.append((tgt, thr, "AUTH_USER_MODEL", "authors", "author"))
    # through SAME app/name as target (degenerate; both legs identical)
    cases.append((tgt, tgt, None, "authors", "author"))
    # bare refs scoped to owner
    cases.append((("str", "Publisher"), ("str", "Contract"), None, "testapp", "author"))
    # self markers
    cases.append((("str", "self"), ("str", "self"), None, "authors", "author"))
    # concrete model refs
    cases.append((("concrete", "testapp", "publisher"),
                  ("concrete", "contract", "contract"), None, "authors", "author"))
    return cases


def main() -> int:
    checked = 0
    for tr, thr, sw, sa, sn in _edges():
        d = disagree(tr, thr, sw, sa, sn)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        tr = _rand_ref(rng)
        thr = _rand_ref(rng) if rng.random() < 0.6 else None
        sw = rng.choice([None, None, None, "AUTH_USER_MODEL", "MY_SETTING"])
        sa = rng.choice(APPS)
        sn = rng.choice(WORDS).lower()
        d = disagree(tr, thr, sw, sa, sn)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
