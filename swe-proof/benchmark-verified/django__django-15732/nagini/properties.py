"""PBT manifest for django__django-15732 (NOT a Nagini module; a record of
adversarial cases the runner swebench_nagini.pbt executes + stamps RESULT).

Defended surface (frozen spec in model.py; see refinement.md / mapping.md):

  select_constraint_to_remove(candidates: List[int], default_name: int,
                              unique: bool, feature_on: bool) -> int
    Requires: Acc(list_pred(candidates), 1/2)     -- candidates is READ-ONLY
    Ensures (frame):  Acc(list_pred(candidates), 1/2)
    Ensures (NORMAL-RETURN DOMAIN, load-bearing -- the batch08 G-EQ fix):
        (disambiguates(unique, feature_on, len(candidates))
          and default_name in ToSeq(candidates))
        or len(candidates) == 1
      -- a normal return is PERMITTED only when the discovered set reduces to
         exactly one candidate; otherwise the operation MUST raise (refusal is
         REQUIRED, closing the silent-arbitrary-deletion hole).
    Ensures (DISAMBIGUATION SELECTION):
        Implies(disambiguates(...) and default_name in ToSeq(candidates),
                Result() == default_name)
        Implies(disambiguates(...) and default_name in ToSeq(candidates),
                Result() in ToSeq(candidates))
    Ensures (SOLE-CANDIDATE SELECTION):
        Implies(len(candidates) == 1, Result() == candidates[0])
    Ensures (MEMBERSHIP):  Result() in ToSeq(candidates)
    Exsures(AmbiguousConstraintSelection,
            Acc(list_pred(candidates),1/2) and len(candidates) != 1
            and not (disambiguates(...) and default_name in ToSeq(candidates)))

  disambiguates(unique, feature_on, n) = unique and feature_on and n >= 1
    -- a @Pure helper, FULLY GROUNDED in the inputs (no opaque answer-key).

This models the gold _delete_composed_index constraint-name selection: optional
narrowing to the composed rule's own default name on a uniqueness removal that
permits coexisting constraints, then the exactly-one-candidate count check.
Constraint names abstracted to distinct int ids (only equality/membership/length
are observable, never characters). The discriminating observable is purely WHICH
name is selected, or that selection refuses (raises).

GROUNDED-ORACLE NOTE: the postcondition is pinned to `disambiguates(...)` (a
@Pure boolean fully computable from the inputs) plus structural predicates over
the actual carrier -- `default_name in ToSeq(candidates)`, `len(candidates)==1`,
`Result() in ToSeq(candidates)`. There is NO opaque answer-key / exact-marker an
impl could echo without doing the work: the answer is a branch over the inputs,
not a value handed to the function. So there is no *wrong echo* to build; the
uniqueness lane instead attacks (a) frame mutation of the read-only input and
(b) partial-domain rivals that are correct on the resolvable sub-domain but
diverge on a discriminating sub-domain (the F2P multi-candidate-incl-default
case; the should-refuse multi-candidate non-member case). The honest cheapest
impl is exercised by the structurally-different positive controls below.

CONTROL-FLOW-EFFECT NOTE: N/A. The only observable difference between branches is
WHICH name is returned vs. that selection RAISES, and that is already captured by
the value abstraction (Ensures/normal-return-domain vs. Exsures). There is no
hidden side-effect / capability channel invisible to the value model. Both raise
directions are defended: should-return-but-raises is the G-DIFF witness
(model_prepatch.py); should-raise-but-returns is rival weak-arbitrary-on-multi
below (the atk7 hole the G-EQ fix closed).

AXIOM LANE: there is NO @ContractOnly axiom in this bundle (axioms region empty).
The changed selection is modelled DEEPLY (the impl region) and validated == the
real gold _delete_composed_index selection algorithm out-of-band by
axiom_check.py (G-AX, an A-reference; the selection needs no DB -- stdlib only).
We re-run that real-vs-model equivalence (axiom_check.py verbatim, read on the
HOST and embedded into a self-contained probe) as an axiom-soundness probe: if
the deep model ever disagrees with the gold algorithm, the A-reference is
unsound. A containment probe is N/A (there is no axiom Requires domain for a
caller-reachable input to fall outside of).

REGION-SURGERY: every spec variant is built by _swap on _BASE editing ONLY text
inside # impl-start/# impl-end. The frozen spec (module-level class /
axioms/pure/pre/post-conditions/signatures) is never touched, so same_spec holds.
"""
from pathlib import Path

INSTANCE = "django__django-15732"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_DIR = Path(__file__).parent
_BASE = (_DIR / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors inside the impl region (each present exactly once in _BASE).
# ---------------------------------------------------------------------------
_NARROW_INIT = "    narrowed_to_default = False\n"
_IF_DISAMB = (
    "    if disambiguates(unique, feature_on, len(candidates)):\n"
    "        if default_name in ToSeq(candidates):\n"
    "            narrowed_to_default = True\n"
)
_RET_DEFAULT = (
    "    if narrowed_to_default:\n"
    "        return default_name\n"
)
_RET_SOLE = (
    "    if len(candidates) == 1:\n"
    "        return candidates[0]\n"
)
_RAISE = "    raise AmbiguousConstraintSelection()\n"

for _a in (_NARROW_INIT, _IF_DISAMB, _RET_DEFAULT, _RET_SOLE, _RAISE):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (5a) POSITIVE CONTROL -- return-order reshuffle. The two return checks are
# swapped so the sole-candidate check runs BEFORE the narrowed-to-default check.
# This stays faithful: when len(candidates)==1 AND narrowing applied, the sole
# element IS default_name (default_name in a one-element list), so returning
# candidates[0] == returning default_name; when len>1 the narrowed path is still
# the one taken. The narrowing computation (which fixes narrowed_to_default ==
# disambiguates && default in cand) is kept verbatim, so every postcondition
# clause stays provable. MUST verify; else the postcondition is over-fit to the
# narrowed-first branch ORDER => SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE,
    _RET_DEFAULT + _RET_SOLE,
    _RET_SOLE + _RET_DEFAULT,
)

# (5b) POSITIVE CONTROL -- local-variable reshape. Instead of two early returns,
# compute the selected name into a single local and return once. Semantically
# identical to gold (narrowed -> default_name; else sole -> candidates[0]; else
# raise). The narrowing computation is kept verbatim. MUST verify; else the
# postcondition is over-fit to the two-early-return SHAPE => SPEC-TOO-STRONG.
_POS_SINGLE_RETURN = _swap(
    _BASE,
    _RET_DEFAULT + _RET_SOLE + _RAISE,
    "    if narrowed_to_default:\n"
    "        selected = default_name\n"
    "    elif len(candidates) == 1:\n"
    "        selected = candidates[0]\n"
    "    else:\n"
    "        raise AmbiguousConstraintSelection()\n"
    "    return selected\n",
)

# (6) ADMISSIBILITY -- a self-call on a fresh, F2P-shaped input. A single
# discovered candidate [5] with default_name=5, a uniqueness removal on a feature-
# on backend: the fresh list literal carries FULL list_pred, so the call's
# Requires(Acc(list_pred(.),1/2)) is establishable; the result must be 5 (the sole
# = default candidate). Then the gold body runs on the actual `candidates`. MUST
# verify; else the precondition rejects a normal F2P-shaped input =>
# PRECOND-TOO-STRONG.
_POS_ADMISS = _swap(
    _BASE,
    _NARROW_INIT,
    "    probe = [5]  # type: List[int]\n"
    "    Assert(Acc(list_pred(probe), 1 / 2))\n"
    "    narrowed_to_default = False\n",
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (1) FRAME MUTATION -- MANDATORY (#1 weakness class). `candidates` is read-only
# at 1/2 permission. This rival WRITES `candidates[0] = default_name` (an index-
# safe store, guarded by len>=1) before the gold logic, attempting to normalize
# the discovered set so selection is vacuously satisfiable. Under
# Acc(list_pred(candidates),1/2) a store needs FULL permission, so it MUST be
# rejected for INSUFFICIENT PERMISSION (not a value mismatch). The gold logic
# (and every postcondition obligation) is kept verbatim AFTER the write, so the
# rejection is attributable solely to the store.
_RIVAL_FRAME = _swap(
    _BASE,
    _NARROW_INIT,
    "    if len(candidates) >= 1:\n"
    "        candidates[0] = default_name\n"
    "    narrowed_to_default = False\n",
)

# (3a) PARTIAL-DOMAIN -- the atk7 hole (silent arbitrary deletion). On the
# NON-resolvable multi-candidate path (not narrowed, len>=2) the rival returns
# candidates[0] instead of raising -- exactly the "remove an arbitrary
# constraint" behaviour the issue forbids. Index 0 is safe (len>=2 here), so the
# ONLY obstacle is the normal-return-domain Ensures: on this path neither
# (disambiguates && default in cand) nor len==1 holds, so a normal return
# VIOLATES that clause => rejected. (Membership clause is satisfied -- candidates[0]
# IS a member -- so the rejection is isolated to the normal-return-domain clause,
# the precise batch08 G-EQ fix.)
_RIVAL_ARBITRARY = _swap(
    _BASE,
    _RAISE,
    "    if len(candidates) >= 1:\n"
    "        return candidates[0]\n"
    "    raise AmbiguousConstraintSelection()\n",
)

# (3b) PARTIAL-DOMAIN -- wrong disambiguation pick. On the narrowed (disambiguation)
# path the rival returns candidates[0] instead of default_name. When the
# discovered set is e.g. [KEY, UNIQ] with default=UNIQ (the F2P: an independent
# single-column unique + the composed _uniq), candidates[0]==KEY != UNIQ, so the
# DISAMBIGUATION-SELECTION clause (Result()==default_name on the narrowed path)
# is VIOLATED. Correct on the sole-candidate-is-default sub-domain (len==1, where
# candidates[0]==default_name); wrong on the multi-candidate-incl-default
# sub-domain. The verifier cannot prove candidates[0]==default_name in general =>
# rejected at the disambiguation-selection clause.
_RIVAL_WRONG_NARROW = _swap(
    _BASE,
    _RET_DEFAULT,
    "    if narrowed_to_default:\n"
    "        return candidates[0]\n",
)

# (3c) PARTIAL-DOMAIN / INVENTED-VALUE -- on the sole-candidate path return
# default_name instead of candidates[0]. When the single discovered candidate is
# NOT the default (e.g. [KEY] with default=UNIQ -- a sole independent constraint),
# this returns a name that was NEVER discovered: the MEMBERSHIP clause
# (Result() in ToSeq(candidates)) is VIOLATED (UNIQ not in [KEY]) AND the
# sole-candidate clause (Result()==candidates[0]) is VIOLATED. Correct only when
# the sole candidate happens to equal the default. The verifier cannot prove
# default_name in ToSeq(candidates) on this path => rejected.
_RIVAL_INVENTED = _swap(
    _BASE,
    _RET_SOLE,
    "    if len(candidates) == 1:\n"
    "        return default_name\n",
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different (the sole-candidate return check runs "
                  "BEFORE the narrowed-to-default check) but CORRECT impl: when "
                  "len==1 and narrowing applied the sole element IS default_name, so "
                  "returning candidates[0] == returning default_name; otherwise the "
                  "narrowed path is unchanged. The narrowing computation (fixing "
                  "narrowed_to_default == disambiguates && default in cand) is kept "
                  "verbatim, so every Ensures clause stays provable. Must verify; "
                  "else the postcondition is over-fit to the branch ORDER => "
                  "SPEC-TOO-STRONG."},
    {"id": "pos-control-single-return", "kind": "soundness", "expect": "verify",
     "module": _POS_SINGLE_RETURN,
     "rationale": "local-variable reshape: the two early returns + raise are "
                  "rewritten as an if/elif/else assigning a single `selected` local "
                  "returned once. Semantically identical to gold; narrowing kept "
                  "verbatim. Must verify; else the postcondition is over-fit to the "
                  "two-early-return SHAPE => SPEC-TOO-STRONG."},
    {"id": "admiss-selfcall", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "a self-call on a fresh F2P-shaped input (a single discovered "
                  "candidate [5], default_name=5, unique=True, feature_on=True) must "
                  "establish the precondition Acc(list_pred(.),1/2) -- the fresh list "
                  "literal carries full list_pred -- and the result must be 5 (the "
                  "sole = default candidate; from the disambiguation/sole-candidate "
                  "clauses). If the precondition rejects this normal input => "
                  "PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-candidates", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: "
                   "_delete_composed_index only INSPECTS the discovered "
                   "constraint_names list (membership / length / [0]); it never "
                   "rewrites the candidate set returned by _constraint_names. The "
                   "rival exists solely to test whether the read-only (1/2) "
                   "precondition can be subverted by overwriting `candidates`. There "
                   "is no resolving patch that mutates its discovered set, so a "
                   "verifying rival here would be a pure verify-not-resolve artifact "
                   "(vacuous satisfaction via self-normalization of the input).",
     "rationale": "MANDATORY frame-mutation probe. `candidates[0] = default_name` "
                  "writes through a 1/2 (read-only) reference and MUST fail for "
                  "INSUFFICIENT PERMISSION (a store needs full Acc(list_pred(candidates))), "
                  "NOT a value mismatch; the store is index-safe (guarded by len>=1) "
                  "and the gold logic + obligations are kept verbatim after it, so "
                  "the rejection is attributable solely to the write. Rejection "
                  "source: the PERMISSION SYSTEM. If it verified => SPEC-TOO-WEAK "
                  "(frame protection hollow)."},
    {"id": "weak-arbitrary-on-multi", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ARBITRARY,
     "refinement": "this is the EXACT atk7 hole the issue forbids: on a "
                   "non-resolvable discovered set (several names, none of which is "
                   "the composed rule's default -- or two non-default names) it "
                   "silently returns candidates[0] and so DELETES an arbitrary "
                   "constraint instead of refusing. A faithful patch doing this would "
                   "drop a wrong/independent constraint and FAIL the migration tests "
                   "(the gold raises ValueError 'Found wrong number of constraints' "
                   "here); it does not resolve -- verify-not-resolve.",
     "rationale": "rejection source: the NORMAL-RETURN-DOMAIN Ensures "
                  "((disambiguates && default in cand) or len==1). On this path "
                  "(not narrowed, len>=2) neither disjunct holds, so a normal return "
                  "violates the clause. candidates[0] IS a member (membership clause "
                  "satisfied), so the rejection is isolated to the normal-return-domain "
                  "clause -- the precise batch08 G-EQ fix. If it verified => "
                  "SPEC-TOO-WEAK (silent-arbitrary-selection hole re-opened)."},
    {"id": "weak-wrong-disambig-pick", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_NARROW,
     "refinement": "on the disambiguation path this returns candidates[0] (the FIRST "
                   "discovered name) rather than the composed rule's default name. In "
                   "the F2P scenario the discovered set is [_key, _uniq] (an "
                   "independent single-column unique plus the composed _uniq), so it "
                   "would delete the INDEPENDENT _key constraint instead of the "
                   "composed-rule _uniq -- exactly the wrong constraint. A faithful "
                   "patch doing this FAILS test_remove_unique_together_on_unique_field "
                   "(the F2P): it removes the user's standalone unique constraint, not "
                   "the unique_together one -- verify-not-resolve.",
     "rationale": "rejection source: the DISAMBIGUATION-SELECTION Ensures "
                  "(Implies(disambiguates && default in cand, Result()==default_name)). "
                  "On the narrowed path narrowed_to_default holds, so the antecedent "
                  "is true and Result() must equal default_name; candidates[0] need "
                  "not equal default_name when len>1, so the verifier cannot close it. "
                  "Correct only on the sole-candidate-is-default sub-domain. If it "
                  "verified => SPEC-TOO-WEAK."},
    {"id": "weak-invented-name", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INVENTED,
     "refinement": "on the sole-candidate path this returns default_name instead of "
                   "the one discovered candidate. When the sole discovered constraint "
                   "is an independent one whose name is NOT the composed-rule default "
                   "(e.g. [_key] with default _uniq), it targets a name that was never "
                   "discovered for deletion -- a constraint that does not exist on "
                   "those columns. A faithful patch doing this would emit a DROP for a "
                   "non-existent / wrong constraint name and FAIL the migration tests "
                   "-- verify-not-resolve.",
     "rationale": "rejection source: the MEMBERSHIP Ensures (Result() in "
                  "ToSeq(candidates)) AND the SOLE-CANDIDATE Ensures "
                  "(Implies(len==1, Result()==candidates[0])). On the len==1 path the "
                  "antecedent holds so Result() must equal candidates[0]; returning "
                  "default_name (which need not be in candidates, let alone equal "
                  "candidates[0]) violates both clauses and the verifier cannot close "
                  "either. If it verified => SPEC-TOO-WEAK (a removal could target an "
                  "undiscovered name)."},
]


# ===========================================================================
# AXIOM LANE -- no @ContractOnly axiom is consumed (axioms region empty). The
# changed selection is an A-reference deep model validated == the real gold
# _delete_composed_index selection algorithm. We re-run that real-vs-model
# equivalence (axiom_check.py verbatim -- it transcribes the gold patch's
# selection and the model's verified impl as pure functions and asserts they are
# observationally equal on 72 boundary + 200000 fuzz inputs incl. the F2P/P2P
# scenarios; stdlib only, needs no DB) as an axiom-soundness probe: if the deep
# model ever disagrees with the gold algorithm, the A-reference is unsound. A
# containment probe is N/A (no axiom Requires domain to fall outside of).
# ===========================================================================

_AXIOM_CHECK_SRC = (_DIR / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-select-equals-gold",
        "axiom": "select_constraint_to_remove",  # A-reference deep model (no consumed axiom)
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the deep model select_constraint_to_remove (the impl region) is "
                     "an A-reference: it must equal the REAL gold _delete_composed_index "
                     "selection algorithm (narrow to [default_name] iff unique and "
                     "feature_on and len(candidates)>=1 and default_name in candidates; "
                     "then return the sole candidate or raise if not exactly one) on "
                     "every input. This probe (axiom_check.py verbatim, stdlib only) "
                     "transcribes the gold selection (gold_select) and the model impl "
                     "(model_select) and asserts observational equality (same selected "
                     "name, same raise) on 72 boundary inputs (incl. the F2P unique-field "
                     "and P2P pk-field scenarios) + 200000 randomized fuzz inputs. Exit 0 "
                     "iff every observation agrees; any disagreement => the A-reference "
                     "is UNSOUND.",
    },
]
