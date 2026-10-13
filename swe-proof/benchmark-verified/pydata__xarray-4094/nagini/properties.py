"""PBT manifest for pydata__xarray-4094 -- adversarial falsification battery.

NOT a Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
executes and stamps with RESULT. Spec cases are full model.py variants that share
the FROZEN spec byte-for-byte (region-surgery: only the text strictly inside the
`# impl-start` / `# impl-end` region -- which here also encloses the loop
`# invariants-start`/`# invariants-end` block -- is edited) and swap the
implementation; they are checked by Nagini verify + markers.same_spec. Axiom cases
are real-callee probes run in the instance Docker image.

Defended surface (read from model.py / refinement.md / mapping.md / meta.json):

  One modeled function `to_unstacked(n, data, resid) -> List[int]` (the stacked-
  collection reconstruction = DataArray.to_unstacked_dataset; the gold one-line
  patch adds `drop=True` to the per-member `.sel`). Inputs:
    * `data`  : Acc(list_pred(data), 1/2)  -> READ-ONLY (the per-member values)
    * `resid` : Acc(list_pred(resid), 1/2) -> READ-ONLY (the per-member positions)
  BOTH inputs are read-only => the FRAME-MUTATION probe is MANDATORY on each.

  Load-bearing postcondition clauses (post-conditions region):
    P1  len(Result()) == n
    P2  ToSeq(Result()) == ToSeq(data)               (verbatim roundtrip identity)
    P3  combined_collection(Result(), ToSeq(resid))   (the CAPABILITY TOKEN)
  P3 is the decisive strengthening (the 2nd-pass G-EQ fix, re-keyed after the
  3rd-pass audit). The per-member values are identical whether or not the merge
  ran (the bug is "raises vs returns", not "wrong value"), so NO value-level
  clause (P1/P2) can separate gold from a merge-skipping impl. P3 is an abstract
  @ContractOnly @Predicate token, keyed by the result OBJECT (a List[int]
  reference, not a value sequence -- a Viper predicate is value-keyed over its
  arguments, so a ToSeq key could be laundered by a value-equal list minted via
  a side call to assemble; the reference key closes that), that ONLY
  `assemble`'s postcondition grants on its own output and that the impl cannot
  fabricate (Nagini rejects Fold of an abstract predicate). It forces the result through the merge
  -- i.e. it discriminates the otherwise value-invisible control-flow/raise
  difference (MergeError vs Dataset). So the CONTROL-FLOW-EFFECT lane is realised
  by the token-bypass / token-laundering attacks below, not a separate token.

  UNGROUNDED-ORACLE-ECHO: N/A in the "wrong echo" sense -- P3 carries NO value the
  impl can echo (it is a capability, not an answer-key oracle). Its analog here is
  the token-BYPASS attack (build the verbatim values, skip `assemble`) and the
  token-LAUNDER attack (call `assemble`, then return a fresh equal copy): both must
  be rejected for insufficient permission to P3. These are the load-bearing rivals.

  The merge guard: `assemble` Requires distinct_residuals(resid) AND
  all_equal(carried_seq(discard, resid)). With the single knob `discard=True`
  every slice carries shared_value() so the guard holds (lemma_carried_all_equal);
  with `discard=False` distinct positions are NOT all-equal -> the guard fails
  (the prepatch MergeError). A fabricated all-equal position list fails
  distinct_residuals. These give the partial-domain / wrong-discard rivals.

Axiom lane: four A-consumed @ContractOnly axioms about UNCHANGED xarray callees
  (carried, shared_value, assemble, combined_collection). axiom_check.py validates
  them on the real .sel(drop=...).squeeze + the Dataset constructor/merge in the
  pinned eval image. We (a) re-run that gold-grounded soundness check in-container,
  and (b) check containment: the model calls `assemble` ONLY with discard=True and
  with resid satisfying distinct_residuals + (via the lemma) all_equal -- every
  callee-reachable input is inside the axiom's Requires domain.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-4094"
FLOAT_ENCODING = None  # meta.json float_encoding is null (int carrier; precision-independent)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors -- all strictly INSIDE the impl region (lines 212-249), which
# also encloses the loop invariants block. Editing them keeps the frozen spec.
# ---------------------------------------------------------------------------

# the loop body that takes member i-1's slice and prepends it (front build).
_LOOP_BODY = ("        selected = data[i - 1]\n"
              "        data_dict = [selected] + data_dict\n"
              "        i = i - 1")

# the selection knob.
_DISCARD = "    discard = True\n"

# the post-loop combine + return (assemble grants the token; we return its output).
_COMBINE = ("    result = assemble(data_dict, resid, discard)\n"
            "    return result")


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): local-variable reshape -----------------
    # Same backward prepend loop, same direction; only introduces an explicit
    # index local `idx`. Keeps EVERY gold invariant and post-loop Assert/lemma
    # verbatim, so the gold proof obligations (the ToSeq(data_dict)==ToSeq(data)
    # .drop(i) invariant, lemma_carried_all_equal) are untouched -- avoids the
    # front-recursive-fold induction trap (no loop-direction flip). MUST verify
    # else SPEC-TOO-STRONG.
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _LOOP_BODY,
            "        idx = i - 1\n"
            "        selected = data[idx]\n"
            "        data_dict = [selected] + data_dict\n"
            "        i = i - 1"),
        "rationale": "a behaviourally-identical reshape (hoist i-1 into a local "
                     "`idx`) keeps the same backward build and every gold "
                     "invariant/lemma; it must verify (else SPEC-TOO-STRONG).",
    },

    # -- POSITIVE CONTROL (soundness): single-element-list local --------------
    # Build the prepend via an explicit one-element list local instead of the
    # inline `[selected]`. Same value, same shape, gold proof intact. MUST verify.
    {
        "id": "pos-singleton-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _LOOP_BODY,
            "        selected = data[i - 1]\n"
            "        one = [selected]  # type: List[int]\n"
            "        data_dict = one + data_dict\n"
            "        i = i - 1"),
        "rationale": "materialising the singleton in a typed local before the "
                     "prepend is behaviourally identical (the prepended sequence "
                     "is unchanged); must verify (else SPEC-TOO-STRONG).",
    },

    # -- ADMISSIBILITY: precondition admits a normal F2P-shaped input ---------
    # Before the gold body, Assert the precondition facts in scope for a normal
    # input (n>=2, the lengths, distinct positions). If the Requires could not be
    # established for a legitimate F2P-shaped input these asserts would fail =>
    # PRECOND-TOO-STRONG. It verifies, so the precondition is satisfiable.
    {
        "id": "admiss-precond-holds",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _DISCARD,
            "    Assert(n >= 2)\n"
            "    Assert(len(data) == n)\n"
            "    Assert(len(resid) == n)\n"
            "    Assert(distinct_residuals(ToSeq(resid)))\n"
            "    discard = True\n"),
        "rationale": "the precondition (n>=2, len(data)==len(resid)==n, "
                     "distinct_residuals, and the 1/2 list_pred permissions) is "
                     "established for a normal F2P-shaped input and the body still "
                     "verifies (else PRECOND-TOO-STRONG).",
    },

    # -- FRAME-MUTATION (uniqueness): write the read-only `data` --------------
    # MANDATORY: data is Acc(list_pred(data),1/2) read-only. This rival writes
    # back to data[i-1] inside the loop. Index-assignment requires the FULL
    # list_pred(data) permission but only 1/2 is held => INSUFFICIENT PERMISSION.
    # Every gold invariant/assert is kept verbatim so the rejection is
    # attributable to the write, not a proof gap.
    {
        "id": "frame-mutate-data",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _LOOP_BODY,
            "        selected = data[i - 1]\n"
            "        data[i - 1] = selected\n"
            "        data_dict = [selected] + data_dict\n"
            "        i = i - 1"),
        "refinement": "the faithful real patch writes back into the caller's "
                      "stacked DataArray's underlying buffer while reconstructing "
                      "it; to_unstacked_dataset must NOT mutate `self` (the F2P "
                      "asserts assert_identical(unstacked, data) and reuses the "
                      "same stacked array), so a mutating impl corrupts shared "
                      "state and does not resolve.",
        "rationale": "rejected by the permission system: `data` is held at "
                     "Acc(list_pred(data),1/2); index-assignment needs the full "
                     "predicate, so the write is INSUFFICIENT-PERMISSION. If it "
                     "verified, the read-only frame is unguarded (SPEC-TOO-WEAK).",
    },

    # -- FRAME-MUTATION supporting case: write the read-only `resid` ----------
    {
        "id": "frame-mutate-resid",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _LOOP_BODY,
            "        selected = data[i - 1]\n"
            "        resid[i - 1] = 0\n"
            "        data_dict = [selected] + data_dict\n"
            "        i = i - 1"),
        "refinement": "overwriting the per-member position labels mid-loop mutates "
                      "the caller's residual coordinate (shared with the input "
                      "stacked array); the real selection never rewrites `self`'s "
                      "coordinates, so a mutating impl diverges and the F2P fails.",
        "rationale": "rejected for INSUFFICIENT PERMISSION on `resid` (held at "
                     "Acc(list_pred(resid),1/2)). Frame integrity of the read-only "
                     "position vector.",
    },

    # -- TOKEN-BYPASS (uniqueness): build verbatim values, skip `assemble` ----
    # THE re-audit's named counterexample (atk_7) and the load-bearing rival. The
    # value-only postconditions P1/P2 ARE satisfiable without the merge (the values
    # are discard-independent). This rival builds the verbatim values and returns
    # them WITHOUT calling assemble. It must be REJECTED by P3
    # `combined_collection(Result(), ToSeq(resid))` -- the abstract token
    # only assemble grants and the impl cannot Fold.
    {
        "id": "atk-bypass-assemble",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _COMBINE,
            "    return data_dict"),
        "refinement": "the faithful real patch is `return data_dict` (a plain dict "
                      "of per-member slices) instead of `return Dataset(data_dict)`; "
                      "a dict is NOT a Dataset and is NOT assert_identical to the "
                      "original Dataset, so test_to_stacked_array_to_unstacked_"
                      "dataset fails -- and, fatally, it would NEVER raise the "
                      "MergeError the merge raises on the buggy drop, so it does not "
                      "exercise the fix at all.",
        "rationale": "rejected by P3 combined_collection: that abstract @ContractOnly "
                     "@Predicate token is granted ONLY by assemble's postcondition "
                     "and is unforgeable (Nagini rejects Fold of an abstract "
                     "predicate); a result not produced by assemble lacks the "
                     "token's permission. If it verified, the merge would be "
                     "OPTIONAL on the result path (SPEC-TOO-WEAK).",
    },

    # -- TOKEN-LAUNDER (uniqueness): call assemble, return a FRESH copy --------
    # atk_fresh: obtain the token by calling assemble, then return a fresh,
    # value-equal list. The token sits on assemble's OUTPUT, not the fresh copy, so
    # P3 fails on the laundered result.
    {
        "id": "atk-launder-fresh-copy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _COMBINE,
            "    result = assemble(data_dict, resid, discard)\n"
            "    fresh = []  # type: List[int]\n"
            "    j = 0\n"
            "    while j < len(result):\n"
            "        Invariant(Acc(list_pred(result), 1 / 2))\n"
            "        Invariant(Acc(list_pred(fresh)))\n"
            "        Invariant(0 <= j and j <= len(result))\n"
            "        Invariant(len(fresh) == j)\n"
            "        fresh = fresh + [result[j]]\n"
            "        j = j + 1\n"
            "    return fresh"),
        "refinement": "re-materialising the merge output into a fresh object (e.g. "
                      "`return Dataset(dict(merged))` or rebuilding it element-wise) "
                      "drops the identity that came through the merge; while it may "
                      "be value-equal, it has NOT itself gone through the Dataset "
                      "merge, so it does not faithfully realise the gold "
                      "`return Dataset(data_dict)` and cannot be relied on to "
                      "carry the merge's behaviour.",
        "rationale": "rejected by P3 combined_collection: the token is on assemble's "
                     "Result, not on the freshly-built `fresh` list, so the returned "
                     "value lacks the token. The capability cannot be laundered "
                     "through a copy. If it verified, the token would be forgeable "
                     "(SPEC-TOO-WEAK).",
    },

    # -- WRONG-DISCARD (uniqueness): discard=False = the prepatch BUG ----------
    # Set the single knob to False (= the default drop omitted). assemble Requires
    # all_equal(carried_seq(discard, resid)); with discard=False each slice carries
    # its own DISTINCT position, so the annotations are NOT all-equal -> the merge
    # guard is violated (the issue's MergeError). The lemma proves the True case
    # only, so the Assert(all_equal(...)) / the assemble precondition fails.
    {
        "id": "atk-discard-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DISCARD,
            "    discard = False\n"),
        "refinement": "this IS the pre-patch bug: `self.sel({variable_dim: k})` with "
                      "drop defaulting to False keeps the residual 'y' coordinate on "
                      "each slice; the slices carry distinct positions, Dataset("
                      "data_dict) raises MergeError: conflicting values for variable "
                      "'y' -- exactly the F2P failure (model_prepatch.py reproduces "
                      "this).",
        "rationale": "rejected by assemble's Requires all_equal(carried_seq(False, "
                     "ToSeq(resid))) (and the in-impl Assert): with distinct_residuals "
                     "and n>=2 the slices carry distinct positions -> NOT all-equal. "
                     "The merge guard fails (where the bug lives).",
    },

    # -- FABRICATE-ALL-EQUAL (uniqueness): slip past the guard with a fake list --
    # Try to satisfy assemble's all_equal guard under discard=False by passing a
    # fabricated all-equal position list (all zeros) instead of the real `resid`.
    # all_equal(carried_seq(False, zeros)) would hold, BUT assemble also Requires
    # distinct_residuals(its resid arg), which a zero list violates; and the result
    # token would be over the fabricated positions, not `resid`, failing P3.
    {
        "id": "atk-fabricate-allequal-resid",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _COMBINE,
            "    fake = []  # type: List[int]\n"
            "    j = 0\n"
            "    while j < n:\n"
            "        Invariant(Acc(list_pred(fake)))\n"
            "        Invariant(0 <= j and j <= n)\n"
            "        Invariant(len(fake) == j)\n"
            "        fake = fake + [0]\n"
            "        j = j + 1\n"
            "    result = assemble(data_dict, fake, False)\n"
            "    return result"),
        "refinement": "fabricating an all-equal coordinate set to feed the merge has "
                      "no counterpart in to_unstacked_dataset (it selects with one "
                      "real `drop` and merges the real per-member slices); a real "
                      "patch cannot invent a degenerate coordinate, so this is not a "
                      "faithful implementation and would not resolve.",
        "rationale": "rejected by assemble's Requires distinct_residuals(fake): a "
                     "constant-0 list is not pairwise distinct. Even were the guard "
                     "bypassed, the granted token would be over `fake`, not `resid`, "
                     "so P3 combined_collection(.., ToSeq(resid)) would still fail.",
    },

    # -- PARTIAL-DOMAIN (uniqueness): wrong roundtrip data --------------------
    # atk_4: assemble the POSITION labels (resid) rather than the member values.
    # Correct cardinality and (if positions were all-equal) the token, but the
    # roundtrip P2 ToSeq(Result())==ToSeq(data) fails since resid != data in general.
    {
        "id": "atk-wrong-roundtrip-data",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _COMBINE,
            "    result = assemble(resid, resid, discard)\n"
            "    return result"),
        "refinement": "returning the position labels instead of the recovered "
                      "per-member values means the reconstruction does not recover "
                      "the original data (unstacked != data), so assert_identical "
                      "fails -- the roundtrip is broken even if it doesn't raise.",
        "rationale": "rejected by P2 ToSeq(Result())==ToSeq(data): assemble returns "
                     "its first arg verbatim (ToSeq(Result())==ToSeq(slices)); with "
                     "slices==resid the result is ToSeq(resid), not provably "
                     "ToSeq(data). Partial-domain (correct shape, wrong values).",
    },

    # -- PARTIAL-DOMAIN supporting case: drop the last member -----------------
    # Build only n-1 members (skip the last prepend) then call assemble. Fails
    # assemble's Requires len(resid)==len(slices) (and P1 len(Result())==n).
    {
        "id": "atk-drop-last-member",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _LOOP_BODY,
            "        selected = data[i - 1]\n"
            "        if i > 1:\n"
            "            data_dict = [selected] + data_dict\n"
            "        i = i - 1"),
        "refinement": "dropping a member from the reconstruction yields a Dataset "
                      "missing a variable -> unstacked != data, assert_identical "
                      "fails.",
        "rationale": "the loop invariant len(data_dict)==n-i is broken (so the "
                     "module fails before assemble) and, were it reached, assemble's "
                     "Requires len(resid)==len(slices) and P1 len(Result())==n fail. "
                     "Partial-domain (missing last element).",
    },

    # -- EMPTY supporting case (uniqueness): return empty ---------------------
    {
        "id": "atk-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _COMBINE,
            "    empty = []  # type: List[int]\n"
            "    return empty"),
        "refinement": "returning an empty collection recovers nothing -> "
                      "unstacked != data, the F2P fails (and it never goes through "
                      "the merge).",
        "rationale": "rejected by P1 len(Result())==n (n>=2>0) and by P3 "
                     "combined_collection (no assemble call grants the token on "
                     "`empty`). Cheap near-miss supporting the token + cardinality "
                     "clauses.",
    },
]


# ===========================================================================
# AXIOM LANE  (four A-consumed @ContractOnly axioms about UNCHANGED callees:
# carried, shared_value, assemble, combined_collection)
# ===========================================================================
#
# The runner mounts ONLY the probe script at /work; axiom_check.py / model.py are
# NOT in-container. The soundness probe therefore EMBEDS axiom_check.py's source
# (read on the HOST at manifest-load time, utf-8-safe) and EXECUTES the REAL xarray
# callees (.sel(drop=...).squeeze + the Dataset constructor/merge) on the issue's
# single-position-axis stacked array -- it never scrapes source. The containment
# probe is static (stdlib ast over the embedded model source); utf-8-safe; reads
# nothing from disk in-container.

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")
_MODEL_SRC = (Path(__file__).parent / "model.py").read_text(encoding="utf-8")

# axiom-soundness: run the real callees via the persisted, gold-grounded
# axiom_check.py. It validates carried(False,.)=distinct position / carried(True,.)
# =no surviving residual (shared_value), the Dataset merge rejecting the conflicting
# kept residual (discard=False) and recovering verbatim (discard=True), and the
# combined_collection token soundness (the un-merged dict is not the Dataset and is
# not identical to the original). exit 0 iff every obligation holds. apply_gold=True
# (the axioms describe the post-gold composition, though axiom_check.py only calls
# UNCHANGED callees, never to_unstacked_dataset).
_AX_SOUND_PROBE = _AXIOM_CHECK_SRC + """

# ---- PBT axiom-soundness driver (appended) --------------------------------
import sys as _sys
print("PBT axiom-soundness: running real-callee obligations for carried / "
      "shared_value / assemble / combined_collection on the issue MCVE")
_rc = main()
_sys.exit(0 if _rc == 0 else 1)
"""

# axiom-containment: the model calls `assemble` only with the SAME `discard` it
# selects under and with the REAL `resid`. The single verifying choice is
# discard=True, for which the proof establishes assemble's Requires:
#   len(resid)==len(slices)             (loop invariant len(data_dict)==n-i, i==0)
#   distinct_residuals(ToSeq(resid))    (precondition, threaded as invariant)
#   all_equal(carried_seq(True, resid)) (lemma_carried_all_equal)
# carried/shared_value have no Requires beyond their bool/int arg types (total).
# So every callee-reachable input is inside each axiom's Requires domain. We make
# this concrete statically: assert the ONLY assemble call site in model.py is in
# to_unstacked, that the proof calls lemma_carried_all_equal + Asserts the three
# guards before it, and that distinct_residuals is a model precondition. A
# reachable assemble input outside the domain would be AXIOM-TOO-WEAK-FOR-CALLER.
_AX_COVER_PROBE = (
    "import sys, ast\n"
    "SRC = " + repr(_MODEL_SRC) + "\n"
    "tree = ast.parse(SRC)\n"
    "funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}\n"
    "# 1) every call to `assemble` lives in to_unstacked.\n"
    "assemble_callers = set()\n"
    "for fname, fnode in funcs.items():\n"
    "    for sub in ast.walk(fnode):\n"
    "        if isinstance(sub, ast.Call) and getattr(sub.func, 'id', None) == 'assemble':\n"
    "            assemble_callers.add(fname)\n"
    "print('assemble call sites (callers):', sorted(assemble_callers))\n"
    "if not assemble_callers:\n"
    "    print('NO assemble call site found'); sys.exit(1)\n"
    "if assemble_callers - {'to_unstacked'}:\n"
    "    print('UNEXPECTED caller of assemble:', assemble_callers); sys.exit(1)\n"
    "# 2) to_unstacked establishes assemble's three Requires before the gold call:\n"
    "#    distinct_residuals (a precondition), all_equal via lemma_carried_all_equal,\n"
    "#    and the lengths via the loop invariant. Check the proof text contains them.\n"
    "tu = funcs['to_unstacked']\n"
    "lo = tu.lineno - 1\n"
    "hi = getattr(tu, 'end_lineno', tu.lineno)\n"
    "body_src = '\\n'.join(SRC.splitlines()[lo:hi])\n"
    "checks = {\n"
    "    'distinct_residuals precondition': 'Requires(distinct_residuals(ToSeq(resid)))' in body_src,\n"
    "    'all_equal lemma invoked':         'lemma_carried_all_equal(ToSeq(resid))' in body_src,\n"
    "    'all_equal guard asserted':        'all_equal(carried_seq(discard, ToSeq(resid)))' in body_src,\n"
    "    'length guard asserted':           'len(resid) == len(data_dict)' in body_src,\n"
    "    'distinct guard asserted':         'distinct_residuals(ToSeq(resid)))' in body_src,\n"
    "}\n"
    "for name, ok in checks.items():\n"
    "    print(('  OK ' if ok else '  MISSING ') + name)\n"
    "if not all(checks.values()):\n"
    "    print('AXIOM-CONTAINMENT: a reachable assemble input may lie outside the "
    "Requires domain (guard not established in-proof)'); sys.exit(1)\n"
    "# 3) carried/shared_value are total over their (bool,int)/() arg domains -- no\n"
    "#    Requires to violate; the discard the model passes is the literal True\n"
    "#    (the single verifying choice), and resid entries are plain ints.\n"
    "print('AXIOM-CONTAINMENT OK: the only assemble call is in to_unstacked with the "
    "real resid; the proof establishes distinct_residuals + all_equal(carried_seq("
    "True, resid)) + matching lengths before it, so every caller-reachable assemble "
    "input is inside the axiom Requires domain. carried/shared_value are total. No "
    "caller-reachable input is outside any axiom domain.')\n"
    "sys.exit(0)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-sound-callees",
        "axiom": "carried+shared_value+assemble+combined_collection",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "runs the gold-grounded axiom_check.py against the REAL "
                     "unchanged xarray callees in the instance image: carried(False,.)"
                     "=distinct surviving residual, carried(True,.)=no surviving "
                     "residual (shared_value), the Dataset merge REJECTS the "
                     "conflicting kept residual (discard=False) and recovers verbatim "
                     "(discard=True), and the combined_collection token is genuinely "
                     "unobtainable by skipping the merge (the un-merged dict is not "
                     "the Dataset, not identical to the original). A real-callee "
                     "violation of any would be AXIOM-UNSOUND.",
    },
    {
        "id": "ax-cover-assemble",
        "axiom": "assemble+carried+shared_value",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": "the only assemble call is in to_unstacked with the real resid "
                     "and discard=True; the proof establishes assemble's three "
                     "Requires (distinct_residuals, all_equal(carried_seq(True, "
                     "resid)) via the lemma, matching lengths) before the call. "
                     "carried/shared_value are total. Every caller-reachable callee "
                     "input is inside the axiom domain (containment); a reachable "
                     "input outside it would be AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
