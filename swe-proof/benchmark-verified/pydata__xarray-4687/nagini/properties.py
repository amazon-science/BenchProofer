# properties.py — PBT manifest for pydata__xarray-4687. NOT a Nagini module; a
# record of adversarial cases the runner (swebench_nagini.pbt) parses + executes.
#
# Spec cases are full model.py variants that share the FROZEN spec exactly
# (every variant is built by region-surgery: _swap edits ONLY text strictly
# inside the # impl-start / # impl-end region, so same_spec is guaranteed) and
# are checked by Nagini verify + markers.same_spec. Axiom cases are real-callee
# probes checked in the instance Docker image.
#
# Defended surface of select_payload(attrs: List[List[int]], mode: int):
#   * attrs and attrs[1] are READ-ONLY: Requires/Ensures/Invariant all hold
#     Acc(list_pred(attrs), 1/2) and Acc(list_pred(attrs[1]), 1/2). Half
#     permission => the verified body may READ them but may NOT write them.
#   * Result carries full permission: Ensures(Acc(list_pred(Result()))).
#   * Load-bearing postcondition clauses:
#       mode == 0 (DEFAULT/unspecified) => ToSeq(Result()) == empty_payload()
#       mode == 1 (PRESERVE)            => ToSeq(Result()) == ToSeq(attrs[1])
#     i.e. PRESERVE keeps the FIRST-CHOICE operand at positional index 1 (x),
#     never index 0 (cond) nor index 2 (y), and never empty when index 1 is
#     non-empty; DEFAULT drops everything.
#   * default_mode_drops() is a @Pure @ContractOnly axiom Ensures(Result()==True)
#     used only as an in-body guard; empty_payload() is a @Pure helper grounded
#     to the empty sequence (PSeq(0).take(0)). Neither is an answer-key oracle:
#     the PRESERVE clause is grounded in the input (attrs[1]) and the DEFAULT
#     clause is grounded to a constant empty payload — so there is no "echo a
#     @Pure marker that lets a wrong output verify" attack here (see assessment).
from pathlib import Path

INSTANCE = "pydata__xarray-4687"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Every edit below is applied to text that lives STRICTLY between
# # impl-start (line 77) and # impl-end (line 99) of model.py, so the frozen
# spec view (axioms/pure/pre/post + signatures, invariants are part of impl and
# also elided) is never touched and same_spec holds.
# ---------------------------------------------------------------------------

# The full original impl region body (between the markers, exclusive).
_IMPL = """    result = []  # type: List[int]
    if mode == 0 and default_mode_drops():
        return result
    # PRESERVE (or a non-dropping default): copy the first-choice operand's
    # payload (positional index 1) element by element into the result.
    src = attrs[1]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(attrs), 1 / 2))
        Invariant(len(attrs) == 3)
        Invariant(Acc(list_pred(attrs[1]), 1 / 2))
        Invariant(src is attrs[1])
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        result.append(src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    return result"""

assert _IMPL in _BASE, "impl anchor drifted from model.py"


def _with_impl(new_impl):
    """Replace the whole impl-region body, leaving the markers + spec intact."""
    return _swap(_BASE, _IMPL, new_impl)


# ===========================================================================
# SPEC LANE
# ===========================================================================

# --- (5) POSITIVE CONTROL: structurally different but correct -------------
# Branch on `mode` first (PRESERVE branch, then DEFAULT), instead of the
# original "build empty then early-return on the drop guard" shape. The
# index-1 forward-append copy loop is kept verbatim (same direction, same
# take(i) invariant) so the gold proof still discharges — only the control
# flow around it is reshaped. DEFAULT returns a freshly-built empty list whose
# ToSeq is the empty payload by construction.
_POS_CONTROL = """    if mode == 1:
        # PRESERVE: copy the first-choice operand's payload (positional index 1).
        src = attrs[1]
        result = []  # type: List[int]
        i = 0
        while i < len(src):
            # invariants-start
            Invariant(Acc(list_pred(attrs), 1 / 2))
            Invariant(len(attrs) == 3)
            Invariant(Acc(list_pred(attrs[1]), 1 / 2))
            Invariant(src is attrs[1])
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(src))
            Invariant(ToSeq(result) == ToSeq(src).take(i))
            # invariants-end
            result.append(src[i])
            i = i + 1
        Assert(ToSeq(src).take(len(src)) == ToSeq(src))
        return result
    # DEFAULT (mode == 0): the unchanged option reader drops to the empty payload.
    Assert(default_mode_drops())
    empty = []  # type: List[int]
    return empty"""

# --- (6) ADMISSIBILITY: the precondition is usable + non-vacuous -----------
# Inside select_payload's OWN impl region (so same_spec holds — we never add a
# top-level def), assert that each precondition fact is actually usable for a
# normal F2P-shaped input and that both a PRESERVE return and a DEFAULT return
# are reachable. If the Requires (len==3, mode in {0,1}, the two half-permission
# predicates) could not be established/used for a legitimate input these asserts
# would fail => PRECOND-TOO-STRONG. The gold control flow + index-1 copy loop
# are kept verbatim after the probes so the model still verifies.
_ADMISS_BODY = """    # admissibility: the precondition facts are usable and non-vacuous.
    Assert(len(attrs) == 3)            # from Requires len(attrs) == 3
    Assert(mode == 0 or mode == 1)     # from Requires mode in {0, 1}
    Assert(Acc(list_pred(attrs), 1 / 2))      # read-only operand list is held
    Assert(Acc(list_pred(attrs[1]), 1 / 2))   # read-only index-1 payload is held
    # a normal (non-raising) return is reachable for an in-domain input:
    result = []  # type: List[int]
    if mode == 0 and default_mode_drops():
        return result
    src = attrs[1]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(attrs), 1 / 2))
        Invariant(len(attrs) == 3)
        Invariant(Acc(list_pred(attrs[1]), 1 / 2))
        Invariant(src is attrs[1])
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        result.append(src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    return result"""

# --- (1) FRAME-MUTATION (MANDATORY): write the read-only operand ----------
# PRESERVE can be "satisfied" vacuously by overwriting attrs[1] in place and
# returning it — ToSeq(Result()) == ToSeq(attrs[1]) trivially holds because the
# result IS the (mutated) attrs[1]. But attrs[1] is held at Acc(...,1/2): the
# append is an INSUFFICIENT-PERMISSION write and must be rejected by the
# permission system, NOT by the value postcondition.
_FRAME_MUT = """    if mode == 0 and default_mode_drops():
        empty = []  # type: List[int]
        return empty
    src = attrs[1]
    # ILLEGAL: writing through a read-only (half-permission) input.
    src.append(0)
    return src"""

# A second frame-mutation flavour: clear-then-return the read-only operand to
# force ToSeq(Result())==ToSeq(attrs[1]) by reference identity. The .clear()
# (modeled via repeated mutation) likewise needs full permission on attrs[1].
_FRAME_MUT2 = """    if mode == 0 and default_mode_drops():
        empty = []  # type: List[int]
        return empty
    src = attrs[1]
    j = 0
    while j < len(src):
        # ILLEGAL in-place mutation of the read-only operand to make it self-equal
        src[j] = src[j]
        j = j + 1
    return src"""

# --- (3) MODE-CONFUSION: PRESERVE returns the WRONG operand ----------------
# Return the predicate operand (index 0 = cond) under PRESERVE. The forward copy
# loop is kept; only the source slot is changed from attrs[1] to attrs[0]. This
# violates Ensures(Implies(mode==1, ToSeq(Result())==ToSeq(attrs[1]))) unless the
# verifier can equate attrs[0] with attrs[1], which it cannot.
_WRONG_COND = _swap(_IMPL, "    src = attrs[1]\n", "    src = attrs[0]\n")
# NOTE: this _swap is on _IMPL (impl-region text only); reapplied to _BASE below.

# Return the second-choice operand (index 2 = y) under PRESERVE.
_WRONG_Y = _swap(_IMPL, "    src = attrs[1]\n", "    src = attrs[2]\n")

# But the loop invariant `Invariant(src is attrs[1])` would now be a proof gap
# rather than a postcondition violation (src is attrs[0] breaks the invariant).
# To make the rejection attributable to the VALUE postcondition (not a stale
# invariant), also relax that invariant to the new source. We must keep this
# inside impl (invariants are part of the elided impl region), so same_spec holds.
_WRONG_COND_CLEAN = _swap(_WRONG_COND, "        Invariant(src is attrs[1])\n",
                          "        Invariant(src is attrs[0])\n")
_WRONG_Y_CLEAN = _swap(_WRONG_Y, "        Invariant(src is attrs[1])\n",
                       "        Invariant(src is attrs[2])\n")

# --- (3') PARTIAL-DOMAIN: PRESERVE drops the FIRST attribute ---------------
# Start the copy at index 1 instead of 0: it drops attrs[1][0], so
# ToSeq(Result()) == ToSeq(attrs[1]) missing element 0 != ToSeq(attrs[1])
# whenever the payload is non-empty. Correct on the empty sub-domain, wrong
# everywhere else (the F2P operand carries exactly one attr, so it fails).
def _build_partial_drop_first():
    body = _IMPL
    # Begin the index from 1 (skip the first element). Keep the invariant lower
    # bound consistent so the rejection is the VALUE postcondition, not an
    # arithmetic invariant gap: 0 <= i becomes 1 <= i, and the take(i) relation
    # is left referencing src so the residual ToSeq(result)==take(i) cannot
    # reach take(len(src)) == ToSeq(src) (it misses element 0).
    body = _swap(body, "    src = attrs[1]\n    i = 0\n",
                 "    src = attrs[1]\n    i = 1\n")
    body = _swap(body, "        Invariant(0 <= i and i <= len(src))\n",
                 "        Invariant(1 <= i and i <= len(src))\n")
    return body


_PARTIAL_FIRST = _build_partial_drop_first()


# --- (4) DEFAULT-KEEPS: unspecified mode keeps instead of drops ------------
# Under mode == 0 return the index-1 payload (keep) instead of empty. This
# violates Ensures(Implies(mode==0, ToSeq(Result())==empty_payload())). It is
# the dual of the bug: it makes the historical drop behaviour wrong.
_DEFAULT_KEEPS = """    src = attrs[1]
    result = []  # type: List[int]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(attrs), 1 / 2))
        Invariant(len(attrs) == 3)
        Invariant(Acc(list_pred(attrs[1]), 1 / 2))
        Invariant(src is attrs[1])
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        result.append(src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    return result"""
# (_DEFAULT_KEEPS unconditionally copies index 1 for BOTH modes => mode==0 fails.)


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_CONTROL),
        "rationale": (
            "A structurally-different but CORRECT impl: branch on mode first "
            "(PRESERVE copy then DEFAULT empty) instead of the original "
            "early-return-on-guard shape. The index-1 forward-append loop and "
            "its take(i) invariant are kept verbatim so no new induction lemma "
            "is needed; DEFAULT returns a freshly-built empty list. Must verify "
            "(else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "admiss-precond-usable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISS_BODY),
        "rationale": (
            "Inside select_payload's own impl region, assert each Requires fact "
            "is usable + non-vacuous (len==3, mode in {0,1}, both half-permission "
            "predicates held) and that a normal non-raising return is reachable "
            "for an in-domain input. If the precondition over-constrained a "
            "legitimate F2P-shaped input these asserts could not be discharged "
            "=> PRECOND-TOO-STRONG. same_spec preserved (no new top-level def)."
        ),
    },
    {
        "id": "frame-mut-append-readonly",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_FRAME_MUT),
        "refinement": (
            "A real patch satisfying PRESERVE by mutating x.attrs IN PLACE "
            "(append to / overwrite the operand's own dict) and returning it "
            "would corrupt the first-choice operand's attributes as a side "
            "effect — gold builds a FRESH merged dict via merge_attrs and never "
            "writes back to x.attrs. Such a patch would fail test_where_attrs' "
            "assert_identical (which also pins cond/x/y identity and the "
            "untouched operand attrs) and break PASS_TO_PASS that rely on "
            "operand immutability."
        ),
        "rationale": (
            "attrs[1] is held at Acc(list_pred(attrs[1]), 1/2). The src.append "
            "is a write through a READ-ONLY half-permission input => must be "
            "rejected for INSUFFICIENT PERMISSION (the permission system), not "
            "by the value postcondition. #1 weakness class."
        ),
    },
    {
        "id": "frame-mut-overwrite-readonly",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_FRAME_MUT2),
        "refinement": (
            "Same frame-mutation defect via in-place element overwrite of the "
            "read-only operand to force result-is-attrs[1] by identity; a "
            "faithful real patch doing in-place writes to x.attrs would mutate "
            "shared operand state and fail assert_identical / operand-immutable "
            "PASS_TO_PASS."
        ),
        "rationale": (
            "src[j] = src[j] writes through Acc(list_pred(attrs[1]), 1/2): a "
            "store needs full permission; rejected for INSUFFICIENT PERMISSION."
        ),
    },
    {
        "id": "preserve-returns-cond-index0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _BASE.replace(_IMPL, _WRONG_COND_CLEAN, 1),
        "refinement": (
            "Returning the predicate operand's payload (cond, positional index "
            "0) under PRESERVE is exactly the wrong-operand bug. The real combine "
            "installs lambda attrs, context: attrs[1]; a patch using attrs[0] "
            "would yield cond's attrs and fail test_where_attrs (expects "
            "{'attr': 'x'}, gets {'attr': 'cond'})."
        ),
        "rationale": (
            "Violates Ensures(Implies(mode==1, ToSeq(Result())==ToSeq(attrs[1]))): "
            "the verifier cannot equate ToSeq(attrs[0]) with ToSeq(attrs[1]). "
            "The matching invariant is relaxed to `src is attrs[0]` (inside the "
            "elided impl region) so the rejection is the VALUE postcondition, "
            "not a stale invariant proof gap."
        ),
    },
    {
        "id": "preserve-returns-y-index2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _BASE.replace(_IMPL, _WRONG_Y_CLEAN, 1),
        "refinement": (
            "Returning the second-choice operand's payload (y, positional index "
            "2) under PRESERVE. A patch using attrs[2] yields y's attrs and "
            "fails test_where_attrs (expects x's {'attr': 'x'}, gets "
            "{'attr': 'y'}). The gold comment pins index 1 = x explicitly."
        ),
        "rationale": (
            "Violates Ensures(Implies(mode==1, ToSeq(Result())==ToSeq(attrs[1]))); "
            "ToSeq(attrs[2]) != ToSeq(attrs[1]) in general. Invariant relaxed to "
            "`src is attrs[2]` inside impl so the reject is the value clause."
        ),
    },
    {
        "id": "preserve-drops-first-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _BASE.replace(_IMPL, _PARTIAL_FIRST, 1),
        "refinement": (
            "PARTIAL-DOMAIN: correct on the empty index-1 payload (drop-first of "
            "[] is []) but on any non-empty payload it drops the first attribute "
            "key. A real patch that lost the first attribute would keep x's "
            "remaining attrs but fail test_where_attrs / any P2P comparing the "
            "FULL attrs dict whenever the surviving operand carries >=1 attr "
            "(the F2P operand carries {'attr':'x'}, a single key — dropping it "
            "yields {} and fails)."
        ),
        "rationale": (
            "Starts the copy at i=1 (skips element 0). With result=[] on entry "
            "the loop invariant ToSeq(result)==ToSeq(src).take(i) demands "
            "ToSeq([])==ToSeq(src).take(1), which is FALSE for any non-empty "
            "payload — so the rival cannot be proven (rejected) exactly on the "
            "non-empty sub-domain where it diverges (it would yield "
            "ToSeq(attrs[1]) missing element 0, failing the mode==1 value "
            "postcondition). It is only 'correct' on the empty payload. A "
            "verifying rival here would be a true SPEC-TOO-WEAK on partial "
            "domain. (The lower bound is moved to 1<=i inside the elided impl "
            "region, so same_spec holds.)"
        ),
    },
    {
        "id": "default-keeps-instead-of-drops",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_DEFAULT_KEEPS),
        "refinement": (
            "CONTROL-FLOW / dual-of-the-bug: drops the mode==0 guard entirely "
            "and copies index 1 unconditionally, so the UNSPECIFIED mode keeps "
            "x's attrs instead of dropping. A real patch that kept attrs by "
            "default would change historical where() semantics and fail "
            "PASS_TO_PASS / the documented drop behaviour for keep_attrs=None."
        ),
        "rationale": (
            "Violates Ensures(Implies(mode==0, ToSeq(Result())==empty_payload())): "
            "for mode==0 the result equals ToSeq(attrs[1]) which is not the empty "
            "payload when attrs[1] is non-empty. The default_mode_drops guard is "
            "removed so the empty-result obligation is unmet on mode 0."
        ),
    },
]


# ===========================================================================
# AXIOM LANE
# ===========================================================================
# default_mode_drops (A-consumed, @ContractOnly): Ensures(Result()==True) means
# "under the ambient default global option the unchanged reader resolves the
# unspecified mode to the dropping behaviour". flag_dependency: the proof's
# DEFAULT branch consumes this; provenance OPTIONS['keep_attrs']=='default'.
#   - axiom-soundness: run the real _get_keep_attrs(default=False) under the
#     default option; it must be False (which the combine step maps to 'drop'),
#     i.e. drops == True. Fuzz the boundary by also confirming the option is the
#     untouched 'default' sentinel (the only config the F2P/caller reaches).
#   - axiom-containment: the model reaches the axiom only on the single nullary
#     call default_mode_drops() inside the mode==0 guard; its (nullary) domain is
#     trivially covered, but the REAL callee is parameterised by default=False
#     and the global option. We enumerate the caller-reachable callee inputs
#     (default=False, option=='default') and assert they lie in the axiom's
#     intended domain (the default-option configuration).
# The PRESERVE deep model is an A-reference (merge_attrs with the index-1
# combiner) — checked the same way: the deep index-1 selection must equal the
# real merge_attrs(callable) on every payload list the caller can form.

_AX_SOUND_PROBE = r'''
import sys
try:
    from xarray.core.options import _get_keep_attrs, OPTIONS
except Exception as exc:
    print("AXIOM-PROBE ENV: xarray.core.options unavailable: %r" % (exc,))
    sys.exit(1)

# Caller's actual runtime config (provenance): the ambient global option is the
# untouched 'default' sentinel — the only configuration the F2P test reaches.
opt = OPTIONS["keep_attrs"]
print("OPTIONS['keep_attrs'] =", repr(opt))
if opt != "default":
    print("AXIOM-UNSOUND: ambient option is not the 'default' sentinel; the "
          "caller's DEFAULT branch resolves through a non-default config")
    sys.exit(1)

# default_mode_drops() == True  iff  the unchanged reader resolves the
# unspecified mode (keep_attrs=None -> default=False) to the dropping behaviour.
resolved = _get_keep_attrs(default=False)
print("_get_keep_attrs(default=False) =", repr(resolved))
# False is what the combine step (apply_ufunc keep_attrs False -> 'drop',
# merge_attrs 'drop' branch -> {}) maps to the EMPTY payload, i.e. drops == True.
if resolved is not False:
    print("AXIOM-UNSOUND: reader did not resolve to False (drop) under default")
    sys.exit(1)

print("AXIOM HOLDS: default_mode_drops Ensures(Result()==True) sound — the "
      "unchanged reader is False under the 'default' option, mapped to 'drop' "
      "(empty payload).")
sys.exit(0)
'''

_AX_CONTAIN_PROBE = r'''
import sys
# Containment: enumerate EXACTLY the callee-inputs the model can reach.
#   * default_mode_drops() is invoked nullary, only inside `if mode == 0 ...`.
#     Its real-callee shadow is _get_keep_attrs(default=False) under the ambient
#     global option. The caller NEVER varies `default` (always False, from
#     keep_attrs is None -> _get_keep_attrs(default=False)) and NEVER mutates the
#     global option (no xr.set_options in the modeled path). So the single
#     reachable callee input is (default=False, OPTIONS['keep_attrs']=='default').
#   * The PRESERVE deep model reaches merge_attrs only with the installed
#     combiner `lambda attrs, context: attrs[1]` on a length-3 positional list.
# We assert each reachable input lies in the axiom/deep-model domain. Covering
# MORE (e.g. non-default options, other combiners) would be SOUND, not required.
try:
    from xarray.core.options import _get_keep_attrs, OPTIONS
    from xarray.core.merge import merge_attrs
except Exception as exc:
    print("AXIOM-PROBE ENV: xarray callees unavailable: %r" % (exc,))
    sys.exit(1)

reachable_defaults = [False]          # keep_attrs is None -> default=False only
reachable_option = OPTIONS["keep_attrs"]
print("reachable callee inputs: default in", reachable_defaults,
      "; option =", repr(reachable_option))

# The axiom's intended domain is the default-option configuration.
if reachable_option != "default":
    print("AXIOM-TOO-WEAK-FOR-CALLER: caller reaches option %r outside the "
          "default-configuration domain the axiom constrains" % (reachable_option,))
    sys.exit(1)
for d in reachable_defaults:
    # every reachable (default, option) pair must sit in-domain (resolves cleanly)
    val = _get_keep_attrs(default=d)
    print("  _get_keep_attrs(default=%r) = %r (in-domain)" % (d, val))

# Deep-model containment: every payload list the caller forms is length-3 and
# the combiner picks index 1; merge_attrs accepts any non-empty variable_attrs
# list with a callable combiner, so the length-3 caller inputs are in-domain.
combiner = lambda attrs, context: attrs[1]
for sample in ([[{}], [{"a": 1}], [{}]], [[{"k": 0}], [{"k": 9}], [{"k": 0}]]):
    out = merge_attrs(sample, combine_attrs=combiner)
    assert out is sample[1], "deep-model containment: merge_attrs != index 1"
    print("  merge_attrs(len-3, index-1 combiner) -> index 1 (in-domain)")

print("AXIOM COVERED: every caller-reachable callee input (default=False, "
      "option=='default'; length-3 positional list with the index-1 combiner) "
      "lies inside the axiom / deep-model domain.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-default-mode-drops",
        "axiom": "default_mode_drops",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "Runs the real unchanged reader _get_keep_attrs(default=False) under "
            "the caller's actual runtime config (OPTIONS['keep_attrs']=='default', "
            "per meta provenance). It must be False — which apply_ufunc maps to "
            "'drop' and merge_attrs's drop branch maps to {} (empty payload) — so "
            "the axiom's Ensures(Result()==True) (drops==True) is sound. If the "
            "real reader disagreed it would be AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-contain-default-and-deepmodel",
        "axiom": "default_mode_drops",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": (
            "Containment: the model reaches the unchanged reader only with "
            "default=False under the untouched 'default' global option (no "
            "set_options in the modeled path), and reaches merge_attrs only with "
            "the index-1 combiner on a length-3 positional list. Each reachable "
            "callee input lies inside the axiom / A-reference deep-model domain; "
            "a reachable input outside it would be AXIOM-TOO-WEAK-FOR-CALLER."
        ),
    },
]
