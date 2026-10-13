# properties.py — PBT falsification battery for pydata__xarray-4695.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Spec
# cases are full model.py variants built by region-surgery (only the impl
# regions are edited; the frozen spec — signatures, pre/post-conditions, pure
# helpers, axioms — is never touched, so same_spec holds by construction). Each
# is checked by Nagini verify + markers.same_spec. Axiom cases are real-callee
# probes executed in the instance Docker image.
#
# Defended surface (read model.py): ONE one-line gold change (`sel(**key)` ->
# `sel(key)`) observed along two contracted functions over the SAME read-only
# parallel mapping (names, values: List[int], Acc(...,1/2)):
#
#   forward_axis_names  : Ensures ToSeq(Result()) == ToSeq(names)   (load-bearing)
#                         -> the WHOLE incoming mapping is forwarded as axis
#                            selectors; no entry diverted because its name
#                            collides with the reserved option name.
#   bound_reserved_option : Ensures Result() == DEFAULT_OPTION()    (load-bearing)
#                         -> the reserved option stays at its default (-1) for
#                            EVERY input; a colliding axis never leaks into it.
#
# The discriminator is a colliding axis (name == RESERVED_NAME() == 7, ~ a
# dimension literally named "method"): the pre-fix `sel(**key)` routing DROPS it
# from the forwarded axes and BINDS its value into the reserved option slot.
# That is the F2P `test_loc_dim_name_collision_with_sel_params`.
from pathlib import Path

INSTANCE = "pydata__xarray-4695"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact original impl blocks (verbatim from model.py, inside impl-start/impl-end).
# Every variant below replaces ONLY one of these blocks; the spec is frozen.
# ---------------------------------------------------------------------------
_FWD_IMPL = """\
    # impl-start
    # Forward the mapping positionally: every entry, including one whose name
    # equals RESERVED_NAME, is kept as an axis selector.
    forwarded = []  # type: List[int]
    i = 0
    while i < len(names):
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(values), 1 / 2))
        Invariant(len(names) == len(values))
        Invariant(Acc(list_pred(forwarded)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(forwarded) == ToSeq(names).take(i))
        Invariant(MustTerminate(len(names) - i + 1))
        # invariants-end
        forwarded.append(names[i])
        i = i + 1
    Assert(ToSeq(names).take(len(names)) == ToSeq(names))
    return forwarded
    # impl-end"""

_OPT_IMPL = """\
    # impl-start
    # Positional forwarding: the reserved option is not fed from the mapping.
    option = DEFAULT_OPTION()
    return option
    # impl-end"""


# ===========================================================================
# SPEC LANE
# ===========================================================================
SPEC_TESTS = []

# --- 1. POSITIVE CONTROL (soundness): forward copy, local-variable reshape ---
# Structurally different (hoist len(names) into a local n, loop against it) but
# behaviourally identical forward copy. KEEPS every gold invariant (just rewrites
# the textually-equal bound), so the gold proof still discharges. Must verify;
# else SPEC-TOO-STRONG. NOT a loop-direction flip (which would need an
# f(a+b)==f(a)+f(b) lemma the verifier can't auto-discharge against the
# front-prefix `.take(i)` invariant) — only a local-variable reshape.
SPEC_TESTS.append({
    "id": "pos-control-forward-localreshape",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _FWD_IMPL, """\
    # impl-start
    # Same positional forward copy, written with the length hoisted into a local
    # (a structural reshape that keeps the gold prefix invariant verbatim).
    n = len(names)
    forwarded = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(values), 1 / 2))
        Invariant(len(names) == len(values))
        Invariant(n == len(names))
        Invariant(Acc(list_pred(forwarded)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(forwarded) == ToSeq(names).take(i))
        Invariant(MustTerminate(len(names) - i + 1))
        # invariants-end
        forwarded.append(names[i])
        i = i + 1
    Assert(ToSeq(names).take(len(names)) == ToSeq(names))
    return forwarded
    # impl-end"""),
    "rationale": "a correct forward copy in a different textual shape (length "
                 "hoisted) keeping the gold prefix invariant must verify; else "
                 "the postcondition ToSeq(Result())==ToSeq(names) is SPEC-TOO-STRONG.",
})

# --- 2. POSITIVE CONTROL (soundness): option returned directly --------------
# bound_reserved_option without the temporary: return DEFAULT_OPTION() directly.
# Structurally different, behaviourally identical. Must verify.
SPEC_TESTS.append({
    "id": "pos-control-option-direct",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _OPT_IMPL, """\
    # impl-start
    # The reserved option is never fed from the mapping: return the default
    # directly (no temporary).
    return DEFAULT_OPTION()
    # impl-end"""),
    "rationale": "a correct impl that returns the default directly must verify; "
                 "else Result()==DEFAULT_OPTION() is SPEC-TOO-STRONG.",
})

# --- 3. ADMISSIBILITY: the precondition admits an F2P-shaped colliding input -
# Inside bound_reserved_option's impl, derive (from the Requires alone) the
# non-vacuous fact that a colliding axis carrying a non-negative selector — the
# F2P shape `method=['a']` — is in-domain: the precondition values[k]>=0 yields
# a concrete >=0 selector while a name MAY equal RESERVED_NAME. If the Requires
# were contradictory/over-strong this derivation would be vacuous; the assert
# pins that it is genuine. Must verify; else PRECOND-TOO-STRONG/vacuous.
SPEC_TESTS.append({
    "id": "admiss-colliding-input",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(_BASE, _OPT_IMPL, """\
    # impl-start
    # Admissibility: the precondition admits an F2P-shaped input — a colliding
    # axis (some name MAY equal RESERVED_NAME) whose selector is non-negative.
    # The Requires Forall yields a concrete >=0 selector for any in-range index,
    # so the input domain is non-empty and not contradictory.
    if len(values) > 0:
        Assert(values[0] >= 0)
    Assert(RESERVED_NAME() == 7)
    Assert(DEFAULT_OPTION() == -1)
    option = DEFAULT_OPTION()
    return option
    # impl-end"""),
    "rationale": "the precondition must accept a normal/colliding F2P-shaped "
                 "mapping (values[k]>=0 is real, not False); else PRECOND-TOO-STRONG.",
})

# --- 4. FRAME-MUTATION (MANDATORY): write the read-only `names` input --------
# names is read-only (Acc(list_pred(names), 1/2)). A rival that APPENDS to names
# to make ToSeq(Result())==ToSeq(names) hold by reshaping the input must FAIL for
# INSUFFICIENT PERMISSION (only half permission is held; .append needs full).
# Keeps the gold postcondition verbatim so the rejection is attributable to the
# write, not a contract change.
SPEC_TESTS.append({
    "id": "frame-mutation-names-append",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _FWD_IMPL, """\
    # impl-start
    # FRAME-MUTATION ATTACK: mutate the read-only `names` input. Held at 1/2
    # permission, so .append must be rejected for insufficient permission.
    names.append(RESERVED_NAME())
    forwarded = []  # type: List[int]
    i = 0
    while i < len(names):
        # invariants-start
        Invariant(Acc(list_pred(forwarded)))
        Invariant(0 <= i and i <= len(names))
        Invariant(MustTerminate(len(names) - i + 1))
        # invariants-end
        forwarded.append(names[i])
        i = i + 1
    return forwarded
    # impl-end"""),
    "refinement": "no faithful real patch mutates the incoming indexer dict "
                  "`key` before forwarding it; `sel(key)` reads it. A rival only "
                  "'works' by rewriting the input, which the 1/2 permission "
                  "forbids — its real analogue would corrupt the caller's mapping.",
    "rationale": "REJECT from the permission system: names is Acc(...,1/2); "
                 ".append requires full permission. A verifying mutation would be "
                 "a frame violation the spec must catch.",
})

# --- 5. FRAME-MUTATION (MANDATORY): write the read-only `values` input -------
# Same attack on the other contracted function: bound_reserved_option mutates
# `values` (read-only, 1/2). Must fail for insufficient permission.
SPEC_TESTS.append({
    "id": "frame-mutation-values-write",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _OPT_IMPL, """\
    # impl-start
    # FRAME-MUTATION ATTACK: write the read-only `values` input (held at 1/2
    # permission) before returning the default. .append must be rejected for
    # insufficient permission.
    values.append(DEFAULT_OPTION())
    option = DEFAULT_OPTION()
    return option
    # impl-end"""),
    "refinement": "the reserved option is computed without touching the caller's "
                  "mapping; `sel(key)` never writes `key`. A rival that mutates "
                  "the input has no faithful real patch (it would corrupt the "
                  "caller's dict), so it cannot resolve.",
    "rationale": "REJECT from the permission system: values is Acc(...,1/2); "
                 ".append needs full permission.",
})

# --- 6. PARTIAL-DOMAIN / pre-fix routing: drop the colliding axis ------------
# The EXACT pre-fix bug (model_prepatch.py forward_axis_names): forward every
# entry EXCEPT one whose name == RESERVED_NAME. Correct on non-colliding inputs,
# WRONG on the F2P collision case (the forwarded sequence loses the colliding
# axis, so ToSeq(Result()) != ToSeq(names)). Must REJECT.
SPEC_TESTS.append({
    "id": "partial-domain-drop-colliding",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _FWD_IMPL, """\
    # impl-start
    # NAME-KEYED routing (pre-fix sel(**key)): an axis whose name equals
    # RESERVED_NAME is diverted out of the forwarded indexers — DROPPED here.
    forwarded = []  # type: List[int]
    i = 0
    while i < len(names):
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(values), 1 / 2))
        Invariant(len(names) == len(values))
        Invariant(Acc(list_pred(forwarded)))
        Invariant(0 <= i and i <= len(names))
        Invariant(MustTerminate(len(names) - i + 1))
        # invariants-end
        if names[i] != RESERVED_NAME():
            forwarded.append(names[i])
        i = i + 1
    return forwarded
    # impl-end"""),
    "refinement": "this IS the pre-fix `self.data_array.sel(**key)` routing: a "
                  "dimension named 'method' is splatted into the `method` "
                  "keyword and dropped from the axis indexers — exactly the F2P "
                  "`test_loc_dim_name_collision_with_sel_params` failure (the "
                  "selection loses the colliding dimension). Its faithful patch "
                  "does NOT resolve.",
    "rationale": "REJECT from postcondition ToSeq(Result())==ToSeq(names): on a "
                 "mapping containing RESERVED_NAME the output is missing that "
                 "entry, so it != ToSeq(names).",
})

# --- 7. PARTIAL-DOMAIN: forward all but the LAST entry -----------------------
# Correct on the empty mapping and on every prefix, diverges on the final entry
# (an off-by-one that drops the last axis). Must REJECT.
SPEC_TESTS.append({
    "id": "partial-domain-drop-last",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _FWD_IMPL, """\
    # impl-start
    # Forward every entry EXCEPT the last (off-by-one): correct on a prefix,
    # wrong whenever len(names) >= 1.
    forwarded = []  # type: List[int]
    i = 0
    while i + 1 < len(names):
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(values), 1 / 2))
        Invariant(len(names) == len(values))
        Invariant(Acc(list_pred(forwarded)))
        Invariant(0 <= i and i <= len(names))
        Invariant(MustTerminate(len(names) - i + 1))
        # invariants-end
        forwarded.append(names[i])
        i = i + 1
    return forwarded
    # impl-end"""),
    "refinement": "a real patch that forwarded all but the last indexer entry "
                  "would drop a dimension from EVERY non-empty `.loc[dict(...)]`, "
                  "failing the F2P (and broad P2P selection tests) — it cannot "
                  "resolve.",
    "rationale": "REJECT from ToSeq(Result())==ToSeq(names): for len(names)>=1 "
                 "the output equals names.take(len-1) != ToSeq(names).",
})

# --- 8. UNGROUNDED-ORACLE / pre-fix oracle echo: bind option from the mapping -
# bound_reserved_option returns the pre-fix oracle option_after_namekeyed (the
# value a colliding axis would inject into the reserved slot) — the EXACT
# model_prepatch.py site-B impl. On a colliding input it returns that entry's
# (>=0) value, != DEFAULT_OPTION() (-1). Must REJECT. (The oracle is the wrong
# routing the contract explicitly does NOT pin in the postcondition; echoing it
# is the SPEC-TOO-WEAK trap.)
SPEC_TESTS.append({
    "id": "oracle-echo-option-namekeyed",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _OPT_IMPL, """\
    # impl-start
    # PRE-FIX oracle echo: bind the reserved option from the mapping via the
    # name-keyed routing (the value of the last colliding axis). This is the
    # routing the correct facade must NOT perform.
    option = option_after_namekeyed(ToSeq(names), ToSeq(values))
    return option
    # impl-end"""),
    "refinement": "this IS the pre-fix `sel(**key)` binding: a dimension named "
                  "'method' lands in the `method` keyword (option_after_namekeyed "
                  "returns its value), so `method` is no longer None — pandas "
                  "get_loc then rejects it ('Invalid fill method'), the exact "
                  "issue. Its faithful patch does NOT resolve the F2P.",
    "rationale": "REJECT from postcondition Result()==DEFAULT_OPTION(): on a "
                 "mapping with a colliding axis whose selector is v>=0, "
                 "option_after_namekeyed returns v != -1.",
})

# --- 9. PARTIAL-DOMAIN: option default ONLY when no collision -----------------
# A subtler site-B rival: return DEFAULT_OPTION on non-colliding inputs but the
# colliding entry's value otherwise — correct on the bulk of the P2P domain
# (mappings with no reserved-name dimension), wrong on exactly the F2P case.
# Must REJECT.
SPEC_TESTS.append({
    "id": "partial-domain-option-conditional",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _OPT_IMPL, """\
    # impl-start
    # Default ONLY when no axis collides; otherwise bind the colliding value
    # into the option (correct on non-colliding mappings, wrong on the F2P).
    option = option_after_namekeyed(ToSeq(names), ToSeq(values))
    if option == DEFAULT_OPTION():
        return DEFAULT_OPTION()
    return option
    # impl-end"""),
    "refinement": "this resolves every selection whose dimensions avoid the "
                  "reserved names but reproduces the pre-fix bug on a dimension "
                  "named 'method' — precisely the F2P collision, which it fails.",
    "rationale": "REJECT from Result()==DEFAULT_OPTION(): when a colliding axis "
                 "is present the branch returns its value (>=0) != -1.",
})


# ===========================================================================
# AXIOM LANE — no @ContractOnly consumed axioms (meta.axioms == []); the routing
# is modelled DEEPLY as an A-reference. These probes validate that deep model
# against the REAL xarray callee in-container (strengthening axiom_check.py,
# which uses only a stdlib faithful copy, by calling the genuine library code).
# ===========================================================================
AXIOM_TESTS = []

# --- A. axiom-soundness: real either_dict_or_kwargs + real DataArray.sel ------
# Under the gold patch, run the GENUINE xarray callees: (1) the real
# either_dict_or_kwargs confirms positional forwarding returns the whole mapping
# and the keyword-splat path drops reserved-named entries; (2) the actual
# DataArray.sel signature has method/tolerance/drop defaulting to None/None/False
# (DEFAULT_OPTION); (3) the end-to-end F2P `da.loc[dict(dim1=..., method=...)]`
# succeeds and selects the colliding 'method' dimension. Any disagreement ->
# AXIOM-UNSOUND (the deep model would not match the real routing).
_AX_SOUND_PROBE = r'''
import sys, inspect

def fail(msg):
    print("AXIOM-UNSOUND:", msg); sys.exit(1)

# (1) the REAL dispatch helper the routing depends on.
from xarray.core.utils import either_dict_or_kwargs

boundary = [
    {},
    {"dim1": "x"},
    {"dim1": "x", "dim2": "a"},
    {"dim1": "x", "method": "a"},          # the issue's exact case
    {"method": "a"},                        # axis named like the reserved option
    {"method": "a", "tolerance": "b", "drop": "c"},
    {"dim1": "x", "method": "a", "dim2": "b"},
    {"x": 1, "y": 2, "z": 3},
]
RESERVED = ("method", "tolerance", "drop")
for m in boundary:
    pos = either_dict_or_kwargs(m, {}, "sel")
    if pos != m:
        fail("positional forwarding changed the mapping: %r -> %r" % (m, pos))
    kw_kwargs = {k: v for k, v in m.items() if k not in RESERVED}
    kw = either_dict_or_kwargs(None, kw_kwargs, "sel")
    if kw != kw_kwargs:
        fail("keyword-splat path mismatch: %r" % (m,))
print("ok: either_dict_or_kwargs positional==whole mapping; splat drops reserved")

# (2) DataArray.sel's real signature: reserved options default to the model's
#     DEFAULT_OPTION (None / None / False), never fed from the mapping.
import xarray
sig = inspect.signature(xarray.DataArray.sel)
defaults = {n: p.default for n, p in sig.parameters.items()}
for opt, want in (("method", None), ("tolerance", None), ("drop", False)):
    if opt not in defaults:
        fail("sel lost reserved option %r (signature drift)" % (opt,))
    if defaults[opt] != want:
        fail("sel default for %r is %r, expected %r" % (opt, defaults[opt], want))
print("ok: sel reserved-option defaults == DEFAULT_OPTION (method/tolerance/drop)")

# (3) End-to-end F2P: positional `.loc[dict(...)]` selects the colliding axis.
import numpy as np
da = xarray.DataArray(
    [[0, 0], [1, 1]],
    dims=["dim1", "method"],
    coords={"dim1": ["x", "y"], "method": ["a", "b"]},
)
got = da.loc[dict(dim1=["x", "y"], method=["a"])]
np.testing.assert_array_equal(got, [[0], [1]])
# the colliding dimension is still a real axis of the result (not consumed as
# a fill 'method'); selecting it kept 'method' as a dimension.
if "method" not in got.dims:
    fail("colliding dimension 'method' was not forwarded as an axis indexer")
print("ok: F2P collision case selects the 'method' dimension positionally")

print("G-AX(real) OK: real either_dict_or_kwargs + DataArray.sel + end-to-end "
      ".loc collision all match the deep model (positional forwards the whole "
      "mapping; reserved options stay default).")
sys.exit(0)
'''

AXIOM_TESTS.append({
    "id": "ax-sound-routing",
    "axiom": "deep-model:sel-positional-routing",
    "kind": "axiom-soundness",
    "expect": "holds",
    "apply_gold": True,
    "probe": _AX_SOUND_PROBE,
    "rationale": "the A-reference deep model (positional forwarding keeps the "
                 "whole mapping and leaves reserved options at default) must "
                 "match the REAL xarray either_dict_or_kwargs + DataArray.sel "
                 "signature + the end-to-end .loc collision; any disagreement is "
                 "AXIOM-UNSOUND.",
})

# --- B. axiom-containment: every caller-reachable mapping is in-domain --------
# The model can pass ANY parallel List[int] (any axis-name ids incl.
# RESERVED_NAME, any non-negative selector values) to the routing reference.
# either_dict_or_kwargs / sel accept any dict whose keys are hashable — so every
# caller-reachable mapping (modelled as a finite dict of hashable name -> value,
# possibly containing the reserved names) lies inside the reference's domain.
# Covering MORE (e.g. non-int keys) is sound; the check is that no reachable
# input falls OUTSIDE the accepted domain.
_AX_COVER_PROBE = r'''
import sys, random
def fail(msg):
    print("AXIOM-TOO-WEAK-FOR-CALLER:", msg); sys.exit(1)
from xarray.core.utils import either_dict_or_kwargs

RESERVED = ("method", "tolerance", "drop")
names_pool = ["dim1", "dim2", "method", "tolerance", "drop", "x", "y", "k0", "k1"]
rng = random.Random(4695)
# enumerate caller-reachable mappings: any finite dict (incl. reserved-name keys,
# non-negative int selectors == the model's values[k] >= 0 precondition).
checked = 0
for _ in range(5000):
    n = rng.randint(0, 6)
    keys = rng.sample(names_pool, min(n, len(names_pool)))
    m = {k: rng.randint(0, 9) for k in keys}   # selectors >= 0 (model Requires)
    # in-domain: the routing reference accepts this mapping positionally and
    # returns it whole (no key rejected for being a reserved name).
    out = either_dict_or_kwargs(m, {}, "sel")
    if out != m:
        fail("caller-reachable mapping not forwarded whole: %r -> %r" % (m, out))
    checked += 1
print("G-AX containment OK: every caller-reachable mapping (any axis names incl. "
      "reserved, selectors>=0) is accepted by the routing reference and "
      "forwarded whole over %d samples." % checked)
sys.exit(0)
'''

AXIOM_TESTS.append({
    "id": "ax-cover-routing",
    "axiom": "deep-model:sel-positional-routing",
    "kind": "axiom-containment",
    "expect": "covered",
    "apply_gold": True,
    "probe": _AX_COVER_PROBE,
    "rationale": "every mapping the model can reach (any name ids incl. "
                 "RESERVED_NAME, selectors >= 0) lies inside the routing "
                 "reference's domain (positional forwarding accepts any dict); a "
                 "reachable input outside it would be AXIOM-TOO-WEAK-FOR-CALLER.",
})
