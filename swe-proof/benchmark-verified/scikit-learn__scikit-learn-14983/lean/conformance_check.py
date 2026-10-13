#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-14983.

The bundle models ONE routine: the constructor-style summary builder `_build_repr`
(mapping.md), whose observable is the final repr STRING (the F2P test compares it
byte-for-byte). `_build_repr` resolves each constructor parameter's value and then
delegates the LAYOUT of the rendered parameters to `_pprint`.

ORACLE PROVENANCE — the real callee, not a replica.
--------------------------------------------------
This script imports and calls the REAL `sklearn.model_selection._split._build_repr`
from the patched tree (G-CONF runs with the gold patch applied), on synthesized
objects whose constructor signature is the modeled `argNames`, whose attribute dict
is the modeled `attrs`, and which carry the modeled auxiliary map when `hasExtra`.
So the whole resolution AND the whole `_pprint` layout — the `, `-continuation, the
>=75-char wrap to `',\\n' + (1 + offset//2)*' '`, and the >500-char entry elision —
are exercised by the genuine repo code rather than restated here.

An earlier revision of this script hand-wrote the oracle as a one-line `, `-join.
That replica agreed with the shadow by construction and therefore never exercised
`_pprint`'s wrapping branch, so the gate could not see that the modeled layout
disagreed with the real one on any input long enough to wrap. Deriving the oracle
from the real callee is what makes this gate able to refute the layout legs at all.

The SHADOW is the op-for-op transliteration of `implementation_reprString`
(Solution.lean impl region), per refinement.md — including `elideEntry`,
`lineSep`, `placeEntry` and `layoutEntries`.

This genuinely tests the soundness-critical clause: a parameter held only in the
auxiliary map (e.g. `n_splits` for RepeatedKFold) must render with its real value
(`n_splits=2`), not the null sentinel (`n_splits=None`) — matching the F2P
expectation `RepeatedKFold(n_repeats=6, n_splits=2, random_state=None)`.

Modeling scope (mapping.md): a value is an int / None / an escape-free short-ish
text value, and `argNames` is the SORTED constructor-parameter name list (that
sort is done by the unchanged introspection prologue, and `_pprint` sorts again,
so the two agree exactly on sorted input). The float branch of `_pprint`
(`type(v) is float` uses `str`) is outside the modeled value carrier and is not
fuzzed. Text values are drawn escape-free so that `repr(s) == "'" + s + "'"`,
which is the modeled `pyRepr .str`. The layout regime is NOT restricted: the
fuzzer deliberately reaches wrapping and elision.

stdlib-only. Pinned seed: 14983 (also in mapping.md).
"""
import random
import sys

sys.path.insert(0, "/testbed")

from sklearn.model_selection._split import _build_repr  # the REAL callee

SEED = 14983
N = 120_000

NAME_POOL = ["n_splits", "n_repeats", "random_state", "shuffle", "alpha",
             "C", "gamma", "tol", "max_iter", "cv"]
# Escape-free text values, so repr(s) == "'" + s + "'" (the modeled pyRepr .str).
# Lengths deliberately span the regimes: short, wrap-inducing, and >500 so the
# per-entry elision branch fires.
STR_POOL = ["auto", "balanced", "l2", "rbf", "ovr", "lbfgs", "",
            "a" * 30, "b" * 60, "c" * 120, "d" * 480, "e" * 520, "f" * 900]

WRAP_THRESHOLD = 75
ELIDE_LIMIT = 500


# --- ORACLE: the REAL _build_repr, driven on a synthesized object -------------
def _to_py(val):
    tag = val[0]
    if tag == "int":
        return val[1]
    if tag == "null":
        return None
    if tag == "str":
        return val[1]
    raise AssertionError(tag)


def _make_obj(class_name, arg_names, attrs, extra, has_extra):
    """An object the real `_build_repr` introspects exactly as a real splitter.

    Its `__init__` signature is `arg_names` (so the unchanged introspection
    prologue yields those names, sorted), its instance dict is `attrs`, and it
    carries `cvargs` iff `has_extra` — the three observables mapping.md §2 binds.

    Both association lists are materialized FIRST-OCCURRENCE-WINS, because the
    modeled `lookupVal` is `List.find?` (it returns the first entry for a key).
    A Python attribute dict / `cvargs` dict has unique keys, so a list with a
    repeated key has no single canonical counterpart; consuming it in reverse
    order makes the last write land on the first occurrence and so makes the
    bridge total on repeated keys instead of leaving them untested. Without
    this, `dict(extra)` would keep the LAST entry while the shadow reads the
    first, and the gate would report a disagreement that is an artifact of the
    bridge rather than a divergence of the model from `_build_repr`.
    """
    params = ", ".join("%s=None" % a for a in arg_names)
    src = "class %s:\n    def __init__(self%s):\n        pass\n" % (
        class_name, (", " + params) if params else "")
    ns = {}
    exec(src, ns)
    obj = ns[class_name].__new__(ns[class_name])
    for key, val in reversed(attrs):
        setattr(obj, key, _to_py(val))
    if has_extra:
        obj.cvargs = dict((k, _to_py(v)) for k, v in reversed(extra))
    return obj


def oracle(inp):
    return _build_repr(_make_obj(inp["className"], inp["argNames"],
                                 inp["attrs"], inp["extra"], inp["hasExtra"]))


# --- SHADOW of implementation_reprString (the R legs) -------------------------
# Mirrors Solution.lean impl region exactly.
def py_repr_shadow(val):
    tag = val[0]
    if tag == "int":
        return str(val[1])
    if tag == "null":
        return "None"
    return "'" + val[1] + "'"


def lookup_val_shadow(assoc, key):
    for k, v in assoc:
        if k == key:
            return v
    return ("null",)


def elide_entry_shadow(e):
    """`elideEntry`: an entry over 500 chars keeps its first 300, '...', last 100."""
    if len(e) > ELIDE_LIMIT:
        return e[:300] + "..." + e[len(e) - 100:]
    return e


def line_sep_shadow(offset):
    """`lineSep`: ',\\n' then 1 + offset//2 spaces."""
    return ",\n" + (1 + offset // 2) * " "


def place_entry_shadow(offset, state, e):
    """`placeEntry`: (text, running line width, nothing-placed-yet)."""
    acc, ln, first = state
    if first:
        return (acc + e, ln + len(e), False)
    if ln + len(e) >= WRAP_THRESHOLD:
        sep = line_sep_shadow(offset)
        return (acc + sep + e, len(sep) + len(e), False)
    return (acc + ", " + e, ln + 2 + len(e), False)


def layout_entries_shadow(offset, entries):
    """`layoutEntries`: fold placeEntry from ("", offset, True)."""
    state = ("", offset, True)
    for e in entries:
        state = place_entry_shadow(offset, state, e)
    return state[0]


def shadow(inp):
    class_name = inp["className"]
    args = inp["argNames"]
    attrs = inp["attrs"]
    extra = inp["extra"]
    has_extra = inp["hasExtra"]

    parts = []
    for key in args:
        v0 = lookup_val_shadow(attrs, key)
        v = v0
        if v0 == ("null",) and has_extra:
            v = lookup_val_shadow(extra, key)
        parts.append(elide_entry_shadow(key + "=" + py_repr_shadow(v)))
    return (class_name + "("
            + layout_entries_shadow(len(class_name), parts) + ")")


def disagree(inp):
    got = oracle(inp)
    want = shadow(inp)
    if got != want:
        return (inp, got, want)
    return None


def _enumerate_edge():
    cases = []
    # F2P: RepeatedKFold — n_repeats direct=6, n_splits only-in-cvargs=2,
    # random_state direct=None. Expect n_splits=2 (NOT None).
    cases.append(dict(
        className="RepeatedKFold",
        argNames=["n_repeats", "n_splits", "random_state"],
        attrs=[("n_repeats", ("int", 6)), ("random_state", ("null",))],
        extra=[("n_splits", ("int", 2))],
        hasExtra=True))
    # F2P sibling: RepeatedStratifiedKFold, same shape.
    cases.append(dict(
        className="RepeatedStratifiedKFold",
        argNames=["n_repeats", "n_splits", "random_state"],
        attrs=[("n_repeats", ("int", 6)), ("random_state", ("null",))],
        extra=[("n_splits", ("int", 2))],
        hasExtra=True))
    # No auxiliary map present: a direct-None param stays None (no fallback).
    cases.append(dict(
        className="KFold",
        argNames=["n_splits", "random_state", "shuffle"],
        attrs=[("n_splits", ("int", 5)), ("random_state", ("null",)),
               ("shuffle", ("str", "auto"))],
        extra=[],
        hasExtra=False))
    # Auxiliary map present but the key is also absent there -> stays None.
    cases.append(dict(
        className="Foo",
        argNames=["C", "alpha"],
        attrs=[("alpha", ("null",))],
        extra=[("gamma", ("int", 3))],
        hasExtra=True))
    # Direct attribute non-None: auxiliary map is NOT consulted even if it has
    # a different value for that key (getattr wins).
    cases.append(dict(
        className="Bar",
        argNames=["n_splits"],
        attrs=[("n_splits", ("int", 10))],
        extra=[("n_splits", ("int", 99))],
        hasExtra=True))
    # Empty parameter list -> ClassName().
    cases.append(dict(className="Empty", argNames=[], attrs=[], extra=[],
                      hasExtra=False))
    # String value rendering.
    cases.append(dict(
        className="SVC",
        argNames=["gamma", "kernel"],
        attrs=[("gamma", ("str", "auto")), ("kernel", ("str", "rbf"))],
        extra=[],
        hasExtra=True))

    # ---- LAYOUT edge cases: the legs the previous replica-oracle never ran ----
    # The reviewer's witness (G-PANEL-2): 5 short text params under a 13-char
    # class name wrap after the 3rd — the input the flat one-line join got wrong.
    ks = ["alpha", "n_repeats", "n_splits", "random_state", "shuffle"]
    cases.append(dict(
        className="RepeatedKFold", argNames=ks,
        attrs=[(k, ("str", "balanced")) for k in ks],
        extra=[], hasExtra=False))
    # EXACTLY at the threshold: running width + entry width == 75, so the
    # `>= 75` branch must fire (a `> 75` renderer differs here and nowhere near).
    cases.append(dict(
        className="RepeatedKFold", argNames=["a", "b"],
        attrs=[("a", ("str", "z" * 55)), ("b", ("int", 7))],
        extra=[], hasExtra=False))
    # One below the threshold: stays on the line.
    cases.append(dict(
        className="RepeatedKFold", argNames=["a", "b"],
        attrs=[("a", ("str", "z" * 54)), ("b", ("int", 7))],
        extra=[], hasExtra=False))
    # Elision: a single entry over 500 chars.
    cases.append(dict(
        className="C", argNames=["a"],
        attrs=[("a", ("str", "z" * 520))], extra=[], hasExtra=False))
    # Elision boundary, both sides (entry length 500 vs 501).
    for n in (496, 497, 498, 499, 500):
        cases.append(dict(
            className="C", argNames=["a"],
            attrs=[("a", ("str", "z" * n))], extra=[], hasExtra=False))
    # Wrap + fallback together: the F2P resolution on a wrapping layout.
    cases.append(dict(
        className="RepeatedStratifiedKFold",
        argNames=["alpha", "n_repeats", "n_splits", "random_state"],
        attrs=[("n_repeats", ("int", 6)), ("random_state", ("null",)),
               ("alpha", ("str", "c" * 40))],
        extra=[("n_splits", ("int", 2))],
        hasExtra=True))
    # Odd/even class-name widths: the indent is 1 + offset//2, so the parity of
    # len(className) is observable on a wrapped layout.
    for cn in ["A", "AB", "ABC", "ABCD", "ABCDE"]:
        ks2 = sorted(["alpha", "beta", "delta", "epsilon", "gamma"])
        cases.append(dict(
            className=cn, argNames=ks2,
            attrs=[(k, ("str", "balanced")) for k in ks2],
            extra=[], hasExtra=False))
    # Several wrapped lines in one repr.
    ks3 = sorted(NAME_POOL)
    cases.append(dict(
        className="GradientBoostingClassifier", argNames=ks3,
        attrs=[(k, ("str", "b" * 30)) for k in ks3], extra=[], hasExtra=False))
    return cases


def _rand_value(rng):
    t = rng.random()
    if t < 0.4:
        return ("int", rng.randint(-3, 50))
    if t < 0.7:
        return ("null",)
    return ("str", rng.choice(STR_POOL))


def _rand_inp(rng):
    class_name = rng.choice(["RepeatedKFold", "RepeatedStratifiedKFold", "KFold",
                             "SVC", "Foo", "Bar", "A", "AB",
                             "GradientBoostingClassifier"])
    k = rng.randint(0, 8)
    # argNames is the SORTED ctor-parameter name list (mapping.md §2).
    args = sorted(rng.sample(NAME_POOL, k))
    has_extra = rng.random() < 0.6
    attrs = []
    extra = []
    for key in args:
        r = rng.random()
        # some keys are direct attributes (possibly None), some live only in the
        # auxiliary map, some are absent everywhere.
        if r < 0.5:
            attrs.append((key, _rand_value(rng)))
        elif r < 0.5 + (0.4 if has_extra else 0.0):
            attrs.append((key, ("null",)))   # direct attr is None -> fallback
            extra.append((key, _rand_value(rng)))
        else:
            # absent from attrs; maybe present in extra
            if has_extra and rng.random() < 0.5:
                extra.append((key, _rand_value(rng)))
    # add some unrelated extra entries / shuffle order
    if has_extra and rng.random() < 0.3:
        extra.append((rng.choice(NAME_POOL), _rand_value(rng)))
    rng.shuffle(attrs)
    rng.shuffle(extra)
    return dict(className=class_name, argNames=args, attrs=attrs, extra=extra,
                hasExtra=has_extra)


def main() -> int:
    checked = 0
    wrapped = 0
    elided = 0
    for inp in _enumerate_edge():
        d = disagree(inp)
        if d:
            print("DISAGREE edge: oracle=%r shadow=%r inp=%s" % (d[1], d[2], d[0]))
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        inp = _rand_inp(rng)
        d = disagree(inp)
        if d:
            print("DISAGREE fuzz: oracle=%r shadow=%r inp=%s" % (d[1], d[2], d[0]))
            print("status=fail")
            return 1
        out = shadow(inp)
        if "\n" in out:
            wrapped += 1
        if "..." in out:
            elided += 1
        checked += 1

    # Coverage of the two layout branches the replica oracle could never reach.
    # Report them so a future regression to a flat-join oracle is visible as a
    # coverage collapse rather than a silent pass.
    print("wrapped=%d elided=%d" % (wrapped, elided))
    if wrapped == 0 or elided == 0:
        print("status=fail (layout branches uncovered)")
        return 1
    print("checked=%d disagreements=0" % checked)
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
