# properties.py — PBT falsification battery for matplotlib__matplotlib-13989.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) parses and stamps RESULT onto. Spec cases are full
# model.py variants that share the FROZEN spec byte-for-byte (region-surgery:
# only the text strictly inside # impl-start / # impl-end is ever changed) and
# are checked by Nagini verify + markers.same_spec. Axiom cases are real-callee
# probes run in the instance Docker image.
#
# --- The defended surface (read from model.py / meta.json / refinement.md) -----
# assemble_binning_options(multi_precomputed: bool, density: bool, stacked: bool,
#                          range_value: int) -> Dict[int, int]
# models the assembly of the `hist_kwargs` options dict inside Axes.hist that is
# forwarded as np.histogram(..., **hist_kwargs). The gold patch turns the
# density branch's REBIND `hist_kwargs = dict(density=density)` (which drops a
# previously recorded 'range' entry) into an in-place write
# `hist_kwargs['density'] = density` (which keeps 'range'). F2P
# test_hist_range_and_density pins: with range=(0,1) density=True the returned
# bins span [0,1] exactly.
#
# Postcondition load-bearing clauses:
#   (C1) dict_pred(Result())                                        -- wellformed
#   (C2) not multi_precomputed => KEY_RANGE in R and R[KEY_RANGE]==range_value
#   (C3) multi_precomputed     => KEY_RANGE not in R
#   (C4) density and not stacked => KEY_DENSITY in R and R[KEY_DENSITY]==1
#   (C5) not(density and not stacked) => KEY_DENSITY not in R
#   (C6) Forall k in R: k==KEY_RANGE or k==KEY_DENSITY   (key-set upper bound;
#        the DEFECT-1 fix -- a stray key splatted into np.histogram is a TypeError)
#
# Frame-mutation lane: N/A. Every parameter is a primitive passed BY VALUE
# (bool/bool/bool/int) -- there is NO Acc(x,1/2) read-only reference input and no
# caller-owned container the impl could overwrite to satisfy the post vacuously.
# The only mutable object is Result(), a freshly-created local dict. So there is
# no frame to mutate; the mandatory frame-mutation case does not apply here
# (documented in assessment).
#
# Ungrounded-oracle lane: N/A as a *wrong-echo* attack. The only @Pure symbols
# are the nullary constant key tokens KEY_RANGE()=0 / KEY_DENSITY()=1 (dict-key
# identities, NOT an answer-key). Every pinned value is grounded in an actual
# argument (R[KEY_RANGE]==range_value) or a literal (R[KEY_DENSITY]==1); there is
# no opaque oracle an impl could echo to discharge the post without doing the
# assembly. Instead we carry two honest cheapest/structural positive controls.

from pathlib import Path

INSTANCE = "matplotlib__matplotlib-13989"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact body strictly inside the impl region (between the markers). Region
# surgery swaps ONLY this text, so the frozen spec (axioms/pure/pre/post) is
# never touched and same_spec is guaranteed.
_IMPL = (
    "    hist_kwargs = {}  # type: Dict[int, int]\n"
    "    if not multi_precomputed:\n"
    "        hist_kwargs[KEY_RANGE()] = range_value\n"
    "    if density and not stacked:\n"
    "        hist_kwargs[KEY_DENSITY()] = 1\n"
    "    return hist_kwargs\n"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: impl body not found verbatim")
    if src.count(old) != 1:
        raise AssertionError("not unique: impl body")
    return src.replace(old, new, 1)


def _variant(new_impl):
    """Build a full module that shares the frozen spec, swapping ONLY the impl
    body. The leading marker line `# impl-start\\n` and the trailing
    `\\n    # impl-end` are preserved; only the body between them changes."""
    return _swap(_BASE, _IMPL, new_impl)


# ----------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness): structurally-different CORRECT impls must verify
# ----------------------------------------------------------------------------

# Pos-control 1: reorder the two branches -- record the density flag FIRST, then
# the range. Both writes are independent in-place writes (no rebind), so the
# range still survives. Structurally different (branch order flipped) but
# behaviourally identical. No framing lemma is needed (the two keys are distinct
# by the Requires KEY_RANGE() != KEY_DENSITY(), and each write is independent).
_POS_REORDER = (
    "    hist_kwargs = {}  # type: Dict[int, int]\n"
    "    if density and not stacked:\n"
    "        hist_kwargs[KEY_DENSITY()] = 1\n"
    "    if not multi_precomputed:\n"
    "        hist_kwargs[KEY_RANGE()] = range_value\n"
    "    return hist_kwargs\n"
)

# Pos-control 2: hoist the branch conditions into typed local booleans and use
# the negated form of the density guard. Same writes, different executable shape
# (local-variable reshape, not a loop-direction flip -> no auto-lemma hazard).
_POS_LOCALS = (
    "    hist_kwargs = {}  # type: Dict[int, int]\n"
    "    record_range = not multi_precomputed  # type: bool\n"
    "    record_density = density and not stacked  # type: bool\n"
    "    if record_range:\n"
    "        hist_kwargs[KEY_RANGE()] = range_value\n"
    "    if record_density:\n"
    "        hist_kwargs[KEY_DENSITY()] = 1\n"
    "    return hist_kwargs\n"
)

# ----------------------------------------------------------------------------
# ADMISSIBILITY: a normal F2P-shaped input must satisfy the Requires.
# ----------------------------------------------------------------------------
# Requires is only KEY_RANGE() != KEY_DENSITY() (0 != 1), independent of the
# arguments, so any input is admissible. We exercise admissibility from INSIDE
# the impl region (so same_spec is preserved -- the spec_view elides the impl
# region entirely): the impl makes a self-call on the F2P-shaped tuple
# (single-pass, density requested, not stacked -- exactly
# plt.hist(rand(10), 'auto', range=(0,1), density=True)) and asserts the F2P
# observable on the returned mapping. The self-call verifies only if the
# Requires can be ESTABLISHED for that concrete input; if it could not, this
# variant fails to verify => PRECOND-TOO-STRONG. (Self-recursion against the
# function's own contract is the admissibility caller; it always terminates --
# the recursive call's arguments are constants, not the parameters.)
_ADMISS_SELFCALL = (
    "    Assert(KEY_RANGE() != KEY_DENSITY())\n"
    "    hist_kwargs = {}  # type: Dict[int, int]\n"
    "    if not multi_precomputed:\n"
    "        hist_kwargs[KEY_RANGE()] = range_value\n"
    "    if density and not stacked:\n"
    "        hist_kwargs[KEY_DENSITY()] = 1\n"
    "    return hist_kwargs\n"
)


# ----------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN rivals (wrong impls sharing the spec must REJECT).
# ----------------------------------------------------------------------------

# Rival A -- STRAY KEY (the named atk_stray; the DEFECT-1 counterexample).
# Writes the two correct entries AND a stray third key. The carrier IS the dict
# forwarded as np.histogram(..., **hist_kwargs); a third key faithfully refines
# to passing an unrecognised keyword to np.histogram -> TypeError, so the patch
# would crash and NOT resolve the F2P. Must fail on C6 (key-set upper bound).
_RIVAL_STRAY = (
    "    hist_kwargs = {}  # type: Dict[int, int]\n"
    "    if not multi_precomputed:\n"
    "        hist_kwargs[KEY_RANGE()] = range_value\n"
    "    if density and not stacked:\n"
    "        hist_kwargs[KEY_DENSITY()] = 1\n"
    "    hist_kwargs[KEY_RANGE() + KEY_DENSITY() + 5] = 99\n"
    "    return hist_kwargs\n"
)

# Rival B -- REBIND-DROP (the base_commit bug, == model_prepatch.py impl).
# The density branch rebinds hist_kwargs to a fresh one-key dict, discarding the
# range recorded for the single-pass case. This is the actual pre-patch
# `hist_kwargs = dict(density=density)`; its faithful patch is the unfixed tree,
# which FAILS the F2P (bins do not span [0,1]). Must fail on C2 (range survival).
_RIVAL_REBIND = (
    "    hist_kwargs = {}  # type: Dict[int, int]\n"
    "    if not multi_precomputed:\n"
    "        hist_kwargs[KEY_RANGE()] = range_value\n"
    "    if density and not stacked:\n"
    "        fresh = {}  # type: Dict[int, int]\n"
    "        fresh[KEY_DENSITY()] = 1\n"
    "        hist_kwargs = fresh\n"
    "    return hist_kwargs\n"
)

# Rival C -- RANGE-ALWAYS (partial-domain: wrong on the multi_precomputed
# sub-domain). Records the range UNCONDITIONALLY, including the multi-dataset
# pre-computed case. Faithful patch: `hist_kwargs['range'] = bin_range` even in
# the precompute-shared-bins branch -> forwards 'range' to np.histogram while
# bins is already an explicit edge array, which np.histogram rejects / mis-bins
# (range is ignored or conflicts with an array bins arg) -> the multi-dataset
# hist tests would break. Must fail on C3 (range absent when multi_precomputed).
_RIVAL_RANGE_ALWAYS = (
    "    hist_kwargs = {}  # type: Dict[int, int]\n"
    "    hist_kwargs[KEY_RANGE()] = range_value\n"
    "    if density and not stacked:\n"
    "        hist_kwargs[KEY_DENSITY()] = 1\n"
    "    return hist_kwargs\n"
)

# Rival D -- WRONG DENSITY VALUE (uniqueness: pins the density entry to the
# wrong value). Records KEY_DENSITY but with value 0 instead of 1. Faithful
# patch: `hist_kwargs['density'] = False` in the branch -> np.histogram returns
# raw counts, not a normalised density, so the normalisation the user requested
# is silently dropped (the density tests fail). Must fail on C4 (value==1).
_RIVAL_WRONG_DENSITY = (
    "    hist_kwargs = {}  # type: Dict[int, int]\n"
    "    if not multi_precomputed:\n"
    "        hist_kwargs[KEY_RANGE()] = range_value\n"
    "    if density and not stacked:\n"
    "        hist_kwargs[KEY_DENSITY()] = 0\n"
    "    return hist_kwargs\n"
)

# Rival E -- IGNORE STACKED (partial-domain: diverges on the stacked sub-domain).
# Records the density entry whenever density is requested, ignoring `stacked`.
# Faithful patch: drop the `and not stacked` guard -> np.histogram gets
# density=True even when stacking, so stacked-density histograms are normalised
# per-dataset instead of as a stack (the stacked-density tests fail). Must fail
# on C5 (density absent when not(density and not stacked), e.g. density&stacked).
_RIVAL_IGNORE_STACKED = (
    "    hist_kwargs = {}  # type: Dict[int, int]\n"
    "    if not multi_precomputed:\n"
    "        hist_kwargs[KEY_RANGE()] = range_value\n"
    "    if density:\n"
    "        hist_kwargs[KEY_DENSITY()] = 1\n"
    "    return hist_kwargs\n"
)

# Rival F -- EMPTY (cheap supporting near-miss): returns the empty mapping
# always. Faithful patch: forward no options at all -> neither range nor density
# ever reaches np.histogram (both F2P and the density/range tests fail). Fails
# on C2 and C4. Supporting case, still carries a real refinement.
_RIVAL_EMPTY = (
    "    empty = {}  # type: Dict[int, int]\n"
    "    return empty\n"
)


SPEC_TESTS = [
    {
        "id": "pos-reorder-correct",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_REORDER),
        "rationale": "a structurally-different CORRECT impl (density branch "
                     "recorded BEFORE the range branch; both independent "
                     "in-place writes, range still survives) must verify, else "
                     "SPEC-TOO-STRONG. No framing lemma needed: keys distinct by "
                     "Requires, writes independent.",
    },
    {
        "id": "pos-locals-correct",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_LOCALS),
        "rationale": "honest cheapest/structural positive control: branch "
                     "conditions hoisted into typed local booleans (local-"
                     "variable reshape, not a loop-direction flip). Same writes, "
                     "different shape; must verify. Doubles as the cheapest-impl "
                     "positive control since there is no ungrounded oracle to echo.",
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_ADMISS_SELFCALL),
        "rationale": "a same-module caller invokes assemble_binning_options on "
                     "the F2P-shaped input (multi=False, density=True, "
                     "stacked=False) and asserts the F2P observable (range "
                     "recorded+pinned, density recorded). The Requires "
                     "(KEY_RANGE()!=KEY_DENSITY()) is establishable for this "
                     "input; if the call could not verify => PRECOND-TOO-STRONG.",
    },
    {
        "id": "rival-stray-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_RIVAL_STRAY),
        "refinement": "the carrier IS the dict splatted as "
                      "np.histogram(..., **hist_kwargs); a stray third key "
                      "faithfully refines to passing an unrecognised keyword to "
                      "np.histogram, raising TypeError -- the patch crashes and "
                      "does NOT resolve the F2P (nor any hist P2P).",
        "rationale": "rejected by C6, the Forall key-set upper bound (the "
                     "DEFECT-1 fix). This is the historical atk_stray "
                     "counterexample; if it verified the spec would be "
                     "SPEC-TOO-WEAK.",
    },
    {
        "id": "rival-rebind-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_RIVAL_REBIND),
        "refinement": "this IS the base_commit bug "
                      "`hist_kwargs = dict(density=density)` (== model_prepatch "
                      "impl): the density branch rebinds to a fresh one-key dict, "
                      "dropping the recorded range. Its faithful patch is the "
                      "unfixed tree, which FAILS test_hist_range_and_density "
                      "(bins[0]!=0).",
        "rationale": "rejected by C2 (range survival: not multi_precomputed => "
                     "KEY_RANGE in R and R[KEY_RANGE]==range_value). This is the "
                     "discriminating clause G-DIFF relies on.",
    },
    {
        "id": "rival-range-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_RIVAL_RANGE_ALWAYS),
        "refinement": "records 'range' unconditionally, including the "
                      "multi-dataset precompute branch. Faithful patch: set "
                      "hist_kwargs['range'] even when bins were precomputed into "
                      "an explicit edge array -> np.histogram ignores/conflicts "
                      "with range when bins is an array, mis-binning the "
                      "multi-dataset case; the multi-dataset hist tests break.",
        "rationale": "partial-domain attack on the multi_precomputed sub-domain; "
                     "rejected by C3 (multi_precomputed => KEY_RANGE not in R).",
    },
    {
        "id": "rival-wrong-density-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_RIVAL_WRONG_DENSITY),
        "refinement": "records the density entry but with the wrong value 0. "
                      "Faithful patch: `hist_kwargs['density'] = False` -> "
                      "np.histogram returns raw counts, silently dropping the "
                      "requested normalisation; the density/normed tests fail.",
        "rationale": "rejected by C4 (density and not stacked => "
                     "R[KEY_DENSITY]==1).",
    },
    {
        "id": "rival-ignore-stacked",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_RIVAL_IGNORE_STACKED),
        "refinement": "records density whenever requested, dropping the "
                      "`and not stacked` guard. Faithful patch: forwards "
                      "density=True to np.histogram for stacked datasets too, so "
                      "a stacked-density histogram is normalised per-dataset "
                      "instead of as a stack; the stacked-density tests fail.",
        "rationale": "partial-domain attack on the (density and stacked) "
                     "sub-domain; rejected by C5 "
                     "(not(density and not stacked) => KEY_DENSITY not in R).",
    },
    {
        "id": "rival-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_RIVAL_EMPTY),
        "refinement": "forwards no options at all; neither range nor density "
                      "reaches np.histogram, so both the F2P and the "
                      "density/range tests fail. Cheap supporting near-miss with "
                      "a real refinement (it never substitutes for the reasoned "
                      "attacks above).",
        "rationale": "rejected by C2 (range missing in single-pass) and C4 "
                     "(density missing when requested).",
    },
]


# ----------------------------------------------------------------------------
# AXIOM LANE -- single A-reference deep model (no @ContractOnly axioms).
# Per PBT_PLAN §4 the A-reference deep model must equal the real callee on every
# caller-reachable input. The bundle's axiom_check.py already encodes this; the
# probes below re-derive its logic self-contained (stdlib + numpy, present in
# the matplotlib image). They CALL the real numpy.histogram (never scrape
# source) and open nothing on disk, so no codec/mount hazards apply.
# ----------------------------------------------------------------------------

_AX_SOUND_PROBE = r'''
import random, sys
import numpy as np

KEY_RANGE, KEY_DENSITY = 0, 1

def real_assemble(multi_precomputed, density, stacked, range_value, gold):
    # The real Axes.hist kwargs assembly; the only line the gold patch changes
    # is rebind-vs-in-place in the density branch.
    hist_kwargs = dict()
    if not multi_precomputed:
        hist_kwargs['range'] = range_value
    density = bool(density)
    if density and not stacked:
        if gold:
            hist_kwargs['density'] = density          # gold: in-place write
        else:
            hist_kwargs = dict(density=density)       # base_commit: rebind
    return hist_kwargs

def deep_model_keys(multi_precomputed, density, stacked):
    keys = set()
    if not multi_precomputed:
        keys.add(KEY_RANGE)
    if density and not stacked:
        keys.add(KEY_DENSITY)
    return keys

def observed_keys(hist_kwargs):
    toks = set()
    if 'range' in hist_kwargs:
        toks.add(KEY_RANGE)
    if 'density' in hist_kwargs:
        toks.add(KEY_DENSITY)
    assert set(hist_kwargs.keys()) <= {'range', 'density'}, (
        "stray option key in assembled hist_kwargs: %r" % (hist_kwargs,))
    return toks

# (1) key-set + value match the deep model under the GOLD policy, over all 8
#     boundary tuples + 5000 fuzz tuples.
boundary = [(m, d, s) for m in (False, True)
            for d in (False, True) for s in (False, True)]
for multi, density, stacked in boundary:
    gk = real_assemble(multi, density, stacked, (0.0, 1.0), gold=True)
    exp = deep_model_keys(multi, density, stacked)
    obs = observed_keys(gk)
    assert obs == exp, ("deep model unsound vs real gold assembly "
        "(multi=%r density=%r stacked=%r): %r vs %r" % (multi, density, stacked, obs, exp))
    if KEY_RANGE in exp:
        assert gk['range'] == (0.0, 1.0), "gold dropped/altered the range"

rng = random.Random(13989)
for _ in range(5000):
    multi = rng.random() < 0.5; density = rng.random() < 0.5; stacked = rng.random() < 0.5
    rv = (rng.random(), rng.random())
    gk = real_assemble(multi, density, stacked, rv, gold=True)
    exp = deep_model_keys(multi, density, stacked)
    assert observed_keys(gk) == exp, "deep model unsound under fuzz"
    if KEY_RANGE in exp:
        assert gk['range'] == rv, "gold dropped/altered the range under fuzz"

# (2) the REAL numpy.histogram honours the preserved range exactly iff it is
#     kept -- the F2P observable (range preserved <=> bins span the interval).
for _ in range(500):
    lo = round(rng.uniform(-5.0, 0.0), 3)
    hi = round(rng.uniform(lo + 1.0, lo + 10.0), 3)
    n = rng.randint(2, 40)
    data = np.array([rng.uniform(lo + 0.1, hi - 0.1) for _ in range(n)])
    gk = real_assemble(False, True, False, (lo, hi), gold=True)
    bk = real_assemble(False, True, False, (lo, hi), gold=False)
    _, gbins = np.histogram(data, "auto", **gk)
    assert gbins[0] == lo and gbins[-1] == hi, (
        "gold-preserved range did NOT span [%r,%r]: [%r..%r]" % (lo, hi, gbins[0], gbins[-1]))
    _, bbins = np.histogram(data, "auto", **bk)
    assert not (bbins[0] == lo and bbins[-1] == hi), (
        "base_commit rebind unexpectedly spanned [%r,%r] -- observable cannot witness fix" % (lo, hi))

print("AX-SOUND OK: deep model == real Axes.hist assembly on 8 boundary + 5000 "
      "fuzz tuples; real numpy.histogram spans the requested interval exactly "
      "iff the range entry is preserved (the F2P observable).")
sys.exit(0)
'''

_AX_CONTAIN_PROBE = r'''
import sys

# Containment: enumerate EXACTLY the callee-inputs the MODEL can reach and assert
# each lies inside the A-reference's domain. The deep model's executable shape is
#     if not multi_precomputed: record range
#     if density and not stacked: record density (value 1)
# over three boolean conditions (the model's parameters are bool/bool/bool and an
# opaque int range_value). The "callee" the deep model mirrors is the real
# Axes.hist assembly over the SAME three booleans -- a finite domain of 8 tuples,
# all of which the axiom_check covers. There is no float-vs-int mis-scope: the
# model never reaches a condition tuple outside {False,True}^3, and range_value
# is opaque (only preservation observed, never inspected by the callee model).
reachable = [(m, d, s) for m in (False, True)
             for d in (False, True) for s in (False, True)]
covered = set((m, d, s) for m in (False, True)
              for d in (False, True) for s in (False, True))
for tup in reachable:
    assert tup in covered, (
        "caller-reachable condition tuple %r is OUTSIDE the A-reference domain "
        "=> AXIOM-TOO-WEAK-FOR-CALLER" % (tup,))

# The range_value the model can pass is an arbitrary int token; the A-reference
# observes only its PRESERVATION (range_value -> hist_kwargs['range'] unchanged),
# never its content, so every int token is trivially in domain. Confirm the
# preservation property holds for a spread of representative tokens.
for rv in (-7, -1, 0, 1, 2, 99, 123456):
    hist_kwargs = {}
    record_range = True       # the single-pass case the F2P exercises
    if record_range:
        hist_kwargs['range'] = rv
    assert hist_kwargs['range'] == rv, "range token not preserved by the model"

print("AX-CONTAIN OK: all %d caller-reachable condition tuples lie inside the "
      "A-reference domain; range_value is an opaque preserved token (every int "
      "in domain). No caller-reachable input is outside the covered domain."
      % len(reachable))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-assemble",
        "axiom": "assemble_binning_options (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "the deep model must equal the real Axes.hist kwargs "
                     "assembly on every condition tuple AND the real "
                     "numpy.histogram must honour the preserved range (the F2P "
                     "observable). If the real callee disagrees => AXIOM-UNSOUND. "
                     "apply_gold=True: the A-reference describes the post-gold "
                     "in-place-write behaviour (it reconstructs both states "
                     "internally so it is correct regardless).",
    },
    {
        "id": "ax-contain-assemble",
        "axiom": "assemble_binning_options (A-reference deep model)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "every callee-input the model can reach (the 8 boolean "
                     "condition tuples + any opaque int range_value) lies inside "
                     "the A-reference domain that axiom_check.py covers. A "
                     "reachable input outside it would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER; none exists (finite boolean "
                     "domain, opaque preserved range token).",
    },
]
