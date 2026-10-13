# properties.py — PBT falsification battery for django__django-11179, PORTED from
# the nagini sibling to the lean bundle. NOT a Lean source file; a record of
# adversarial cases the runner executes and stamps with RESULT. Each SPEC_TESTS
# case is a full Solution.lean variant that shares the FROZEN spec exactly
# (markers.same_spec) and edits ONLY the impl region (and, where a positive
# needs it, the proof body); the runner re-runs the Lean verifier and checks the
# verify/reject outcome against `expect`. Every reject case additionally carries
# a `witness` that has been SEEN to discriminate (elaborates against the rival,
# fails against the frozen solution).
#
# ---------------------------------------------------------------------------
# Defended surface on THIS carrier (read Solution.lean + mapping.md).
# ---------------------------------------------------------------------------
# One modeled function, `delete`, over a purely functional core:
#
#   problem_spec_delete (data) (directlyDeletable) (directCount generalTotal)
#                       (result : (List RecGroup) × Int) : Prop :=
#     result.1 = clearAllPks data                                      -- (A)
#     ∧ result.2 = (if isSingleFast data directlyDeletable            -- (B)
#                   then directCount else generalTotal)
#
# obligation: theorem correct_delete, universally quantified over all four
# inputs, NO precondition.
#
# Two independent, load-bearing clauses:
#   (A) group structure — EVERY removed record's key is cleared, on either path
#       (`clearAllPks data`). This is the single added fact of the fix: the sole
#       F2P observes exactly this on the fast single-record path. Leaving a
#       record's key intact violates (A).
#   (B) count — the reported tally is the branch-selected one: the direct tally
#       on the smallest job, the general tally otherwise. A fabricated literal,
#       or the wrong tally, or the wrong branch selection, all violate (B).
#
# Four input binders: `data`, `directlyDeletable`, `directCount`, `generalTotal`.
# All are TRANSPARENT here (the two counts are free `Int` parameters, the
# branch predicate a free `Instance → Bool`), so every refutation is stated at
# concrete literals and closed by `decide` — no conditioning on an opaque
# carrier is needed.
#
# ---------------------------------------------------------------------------
# Port notes — which nagini cases carried over, and how the carrier reshaped them.
# ---------------------------------------------------------------------------
# The nagini surface is `remove_single_independent(instance, using) -> int`: a
# single scalar count return plus a written-back `instance.pk`. The lean bundle
# models the WHOLE `delete` core — both the fast and general paths, the grouped
# record structure, and the branch-selected count — so its carrier is wider on
# the structure axis and narrower on the oracle axis. Because clause (A) pins the
# WHOLE returned structure (every group's label, presence and order, and every
# record in it), the lean carrier additionally admits the frame attacks §0.5 asks
# for — relabelling, reordering, dropping an empty group, clearing one record per
# group — none of which the scalar nagini surface could state:
#
#   * nagini clause (2) `instance.pk is None`  ->  lean clause (A) over the whole
#     grouped structure (`clearAllPks data`). nagini's `uniq-drop-clear` (THE
#     bug) ports directly, and the lean model ADDITIONALLY exposes the general
#     path, so a second structure attack (`uniq-general-unclear`) exists that
#     nagini could not state.
#   * nagini clause (1) `Result() == removed_row_count(Old(pk))` pins the count
#     to an OPAQUE @Pure oracle. On this carrier the count is not an oracle but a
#     branch selection between two free `Int` parameters. So the nagini "opaque
#     oracle echo" framing is gone; the count is attacked instead by fabricating
#     a literal (`uniq-fabricate-count`, `-zero`), by returning the wrong tally
#     (`uniq-wrong-tally`, the analogue of nagini's `uniq-wrong-identifier`), and
#     by selecting the wrong BRANCH (`uniq-ignore-deletable`, which the scalar
#     nagini surface had no branch to attack).
#   * nagini `uniq-count-after-clear` (order-of-operations: read pk for the count
#     AFTER clearing it) DOES have a counterpart — see `uniq-order-after-clear`
#     below. The earlier port note claimed this was inexpressible because "the
#     lean count is an abstract parameter, not computed from the record's key, so
#     there is no capture-order to disturb". That is false: the tally parameters
#     are abstract, but WHICH of the two is reported is a decision, and an impl
#     can be written to take that decision by inspecting the record's key AFTER
#     clearing it — at which point the information the decision needs has been
#     destroyed and the wrong tally is reported. The capture-order IS disturbable;
#     the case is landed, not omitted.
#   * nagini admissibility (`admiss-f2p-shaped-input`) asserts the Requires is
#     establishable for an F2P-shaped input. An earlier port note recorded this as
#     inexpressible because "the lean obligation has NO precondition, so
#     PRECOND-TOO-STRONG is unreachable". That reason is wrong: the analogue on a
#     total carrier is not a precondition at all but the OBLIGATION being
#     unsatisfiable at exactly an F2P-shaped input, which a positive that
#     discharges the obligation at that concrete input — by evaluation, as a
#     `have`, before closing the frozen obligation verbatim — tests directly. The
#     case is LANDED as `admiss-ground-smallest-job` below, not omitted.
#   * Frame/permission-mutation rivals: nagini-specific fractional permissions.
#     Lean is referentially transparent, so this class is VACUOUS. Nothing to
#     port; no substitute fabricated.
#   * Divergence / non-termination rivals: nothing to ship. The termination-
#     semantics spec hole is a velvet-only finding recorded in
#     the corpus-wide termination-semantics finding, which measures lean as unaffected; it is not
#     re-derived or re-reported here.
#   * Intra-group record ORDER is NOT attackable, and this is a carrier collapse
#     rather than a gap. An impl that clears every key correctly but reverses the
#     records WITHIN each group verifies against the frozen spec — correctly so:
#     `Instance` carries exactly one field, so once every record in a group has
#     had its key cleared they are all the identical value `{ pk := none }` and any
#     permutation of them is the SAME list. Machine-checked, not argued: the
#     reversing impl and the frozen impl were proven equal at every input. So the
#     rival is a correct reshape, not a wrong impl, and no case is owed. Group
#     order, by contrast, IS observable (labels distinguish groups) and is
#     attacked by `uniq-general-reorder`.
#   * AXIOM_TESTS: dropped (G-AX's lane, not this gate's). The lean bundle
#     consumes no callee axiom anyway (mapping.md: "None consumed").
#
# No leakage: describe behavior abstractly, never the patched file/symbol.
from pathlib import Path

INSTANCE = "django__django-11179"
FLOAT_ENCODING = None

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors — each lies ENTIRELY inside the impl region and is unique in the file.
# ---------------------------------------------------------------------------
# The fast-path early return (clears the one record's key, reports the direct
# tally).
_FAST_RET = "      return ([(label, [{ inst with pk := none }])], directCount)"
assert _BASE.count(_FAST_RET) == 1

# The general-path return (clears every record's key, reports the general tally).
_GEN_RET = "  return (clearAllPks data, generalTotal)"
assert _BASE.count(_GEN_RET) == 1

# The whole fast-path branch guard + body (used by the branch-selection attack).
_IF_BLOCK = """    if directlyDeletable inst then
      -- Remove the one record directly, clear its now-stale key, and return early.
      return ([(label, [{ inst with pk := none }])], directCount)"""
assert _BASE.count(_IF_BLOCK) == 1

# The head of the branch-shape match (used by the branch-SHAPE attacks, which
# widen the fast path to inputs that are not the smallest job).
_MATCH_HEAD = """  match data with
  | [(label, [inst])] =>
    if directlyDeletable inst then"""
assert _BASE.count(_MATCH_HEAD) == 1

# The frozen proof body — a positive that is not definitionally equal to the
# frozen impl must reprove the SAME statement, so it replaces this body.
_PROOF_BODY = """  intro data directlyDeletable directCount generalTotal
  unfold implementation_delete problem_spec_delete isSingleFast
  match data with
  | [(label, [inst])] =>
    by_cases h : directlyDeletable inst <;> simp [clearAllPks, h]
  | [] => simp [clearAllPks]
  | (label, []) :: rest => simp [clearAllPks]
  | (label, inst1 :: inst2 :: more) :: rest => simp [clearAllPks]
  | g1 :: g2 :: rest => simp [clearAllPks]"""
assert _BASE.count(_PROOF_BODY) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness / verify) — structurally-different but CORRECT
# impls that MUST verify with the frozen obligation (else SPEC-TOO-STRONG). The
# frozen proof body closes both (confirmed by build); the theorem STATEMENT is
# byte-identical.
# ===========================================================================

# pos-clearall-fast: on the fast path, produce the cleared structure by the SAME
# expression the general path uses (`clearAllPks data`) rather than the inlined
# singleton `[(label, [{ inst with pk := none }])]`. On a single-group /
# single-record input those two expressions are equal, so clause (A) still holds
# and the direct tally is still reported. A different structural shape for the
# identical behavior; must verify.
_POS_CLEARALL_FAST = _swap(
    _BASE, _FAST_RET, "      return (clearAllPks data, directCount)")

# pos-loop-clear: the general path builds the cleared structure with an explicit
# accumulator loop (append one cleared group per iteration) instead of calling
# `clearAllPks`. The frozen proof body does NOT close this — the loop's `forIn`
# form is not the `.map` form clause (A) is stated over — so the case carries its
# own proof of the SAME (byte-identical) statement, which is what a positive is
# allowed to do. This is the strongest available soundness probe: measured NOT
# definitionally equal to the frozen impl (a `rfl` between the two impls fails),
# so it really does force clause (A) to be re-established for a new impl shape
# rather than re-asserted for the frozen one.
_POS_LOOP_CLEAR = _swap(
    _swap(_BASE, _GEN_RET,
          "  let mut out : List RecGroup := []\n"
          "  for g in data do\n"
          "    out := out ++ [(g.1, g.2.map (fun i => { i with pk := none }))]\n"
          "  return (out, generalTotal)"),
    _PROOF_BODY,
    """  intro data directlyDeletable directCount generalTotal
  have fl : ∀ (l : List RecGroup),
      (l.map (fun x => [(x.1, List.replicate x.2.length ({ pk := none } : Instance))])).flatten
        = l.map (fun g => (g.1, List.replicate g.2.length ({ pk := none } : Instance))) := by
    intro l
    induction l with
    | nil => simp
    | cons hd tl ih => simp [ih]
  have loop : ∀ (l : List RecGroup) (acc : List RecGroup),
      (Id.run (do
        let mut out := acc
        for g in l do
          out := out ++ [(g.1, g.2.map (fun i => { i with pk := none }))]
        return out)) = acc ++ clearAllPks l := by
    intro l
    induction l with
    | nil => intro acc; simp [clearAllPks]
    | cons hd tl ih => intro acc; simp [clearAllPks, fl]
  unfold implementation_delete problem_spec_delete isSingleFast
  match data with
  | [(label, [inst])] =>
    by_cases h : directlyDeletable inst <;> simp_all [clearAllPks]
  | [] => simp_all [clearAllPks]
  | (label, []) :: rest => simp_all [clearAllPks]
  | (label, inst1 :: inst2 :: more) :: rest => simp_all [clearAllPks]
  | g1 :: g2 :: rest => simp_all [clearAllPks]""")

# pos-pred-guard: drop the structural pattern match entirely and branch on the
# spec-level eligibility predicate (`isSingleFast data directlyDeletable`),
# producing the cleared structure the same way on both arms. Behaviorally
# identical — the match and the predicate agree by construction — but measured
# NOT definitionally equal to the frozen impl, so it too reproves the identical
# statement rather than inheriting it.
_POS_PRED_GUARD = _swap(
    _swap(_BASE,
          """  -- Optimize for the case with a single collected record and no dependents.
  match data with
  | [(label, [inst])] =>
    if directlyDeletable inst then
      -- Remove the one record directly, clear its now-stale key, and return early.
      return ([(label, [{ inst with pk := none }])], directCount)
  | _ => pure ()
  -- General path: after removal, clear every collected record's key.
  return (clearAllPks data, generalTotal)""",
          """  -- Optimize for the case with a single collected record and no dependents.
  if isSingleFast data directlyDeletable then
    return (clearAllPks data, directCount)
  -- General path: after removal, clear every collected record's key.
  return (clearAllPks data, generalTotal)"""),
    _PROOF_BODY,
    """  intro data directlyDeletable directCount generalTotal
  unfold implementation_delete problem_spec_delete
  by_cases h : isSingleFast data directlyDeletable = true <;> simp [h]""")


# ===========================================================================
# UNIQUENESS / partial-domain (reject) — rivals sharing the spec exactly,
# editing only the impl. Each MUST be rejected; a verifying rival is a real
# verify-but-not-resolve break (SPEC-TOO-WEAK). Each ships a witness SEEN to
# discriminate.
# ===========================================================================

# uniq-drop-clear: THE BUG. On the fast single-record path, return the record
# with its key INTACT instead of cleared. Violates clause (A) on that path — the
# exact pre-patch behavior the sole F2P observes.
_UNIQ_DROP_CLEAR = _swap(
    _BASE, _FAST_RET, "      return ([(label, [inst])], directCount)")

# uniq-general-unclear: the structure attack the scalar nagini surface could not
# state — on the GENERAL path, return the input groups UNCHANGED (keys intact)
# instead of `clearAllPks data`. Violates clause (A) on the general path.
_UNIQ_GENERAL_UNCLEAR = _swap(
    _BASE, _GEN_RET, "  return (data, generalTotal)")

# uniq-fabricate-count: report a hard-coded literal 1 for the fast-path count
# instead of the direct tally parameter. Violates clause (B): 1 is not the
# branch-selected `directCount`.
_UNIQ_FABRICATE_COUNT = _swap(
    _BASE, _FAST_RET, "      return ([(label, [{ inst with pk := none }])], 1)")

# uniq-fabricate-zero: supporting near-miss — report a hard-coded 0. Same defect
# on clause (B).
_UNIQ_FABRICATE_ZERO = _swap(
    _BASE, _FAST_RET, "      return ([(label, [{ inst with pk := none }])], 0)")

# uniq-wrong-tally: the analogue of nagini's wrong-identifier — on the fast path
# report the GENERAL tally (`generalTotal`) where the direct tally (`directCount`)
# is required. Violates clause (B) whenever the two tallies differ.
_UNIQ_WRONG_TALLY = _swap(
    _BASE, _FAST_RET,
    "      return ([(label, [{ inst with pk := none }])], generalTotal)")

# uniq-ignore-deletable: the BRANCH-selection attack — ignore the direct-removal
# eligibility predicate and always take the fast path for a single-record group.
# When the record is NOT eligible, gold takes the general path (reporting the
# general tally), but this rival reports the direct tally. Violates clause (B)
# via a wrong branch selection; exercises the `directlyDeletable` binder that the
# other fast-path rivals hold at `true`.
_UNIQ_IGNORE_DELETABLE = _swap(
    _BASE, _IF_BLOCK,
    "    return ([(label, [{ inst with pk := none }])], directCount)")

# uniq-fast-multigroup: branch-SHAPE attack — take the fast path whenever the
# FIRST group holds a single eligible record, however many groups were collected.
# The smallest job is one group holding one record; widening the fast path to a
# multi-group job both reports the direct tally where the general tally is
# required (clause (B)) and returns only the first group, losing every other
# collected record's cleared entry (clause (A)).
_UNIQ_FAST_MULTIGROUP = _swap(
    _BASE, _MATCH_HEAD,
    """  match data with
  | (label, [inst]) :: _ =>
    if directlyDeletable inst then""")

# uniq-fast-multirecord: the companion branch-SHAPE attack on the other axis —
# take the fast path on the HEAD record of a single group holding SEVERAL
# records. Reports the direct tally where the general tally is required (clause
# (B)) and returns only the head record, so the group's remaining records never
# get their keys cleared (clause (A)).
_UNIQ_FAST_MULTIRECORD = _swap(
    _BASE, _MATCH_HEAD,
    """  match data with
  | [(label, inst :: _)] =>
    if directlyDeletable inst then""")

# uniq-fast-relabel: frame attack on the group label. The fast path clears the
# key correctly and reports the right tally, but substitutes a fabricated group
# label for the input one. Clause (A) pins the WHOLE structure to clearAllPks
# data, which preserves every group's label; only the key field may change.
_UNIQ_FAST_RELABEL = _swap(
    _BASE, _FAST_RET,
    "      return ([(0, [{ inst with pk := none }])], directCount)")

# uniq-general-headonly: partial-clearing near-miss on the general path — clear
# only the FIRST record of each group instead of every record. Violates clause
# (A) for any group holding two or more records with present keys: the guarantee
# is that EVERY removed record's key is cleared, not just the first of each group.
_UNIQ_GENERAL_HEADONLY = _swap(
    _BASE, _GEN_RET,
    "  return (data.map (fun g => (g.1, match g.2 with\n"
    "    | [] => []\n"
    "    | i :: rest => { i with pk := none } :: rest)), generalTotal)")

# uniq-general-reorder: frame attack on group ORDER — clear every key correctly
# but return the groups reversed. Clause (A) pins the structure to clearAllPks
# data, which is order-preserving (`.map`), so a permutation violates it.
_UNIQ_GENERAL_REORDER = _swap(
    _BASE, _GEN_RET, "  return ((clearAllPks data).reverse, generalTotal)")

# uniq-general-dropempty: frame attack on group PRESENCE — clear every key
# correctly but silently drop the groups that hold no records. clearAllPks
# preserves every group entry (label and shape), including the empty ones, so
# dropping any of them violates clause (A).
_UNIQ_GENERAL_DROPEMPTY = _swap(
    _BASE, _GEN_RET,
    "  return ((clearAllPks data).filter (fun g => !g.2.isEmpty), generalTotal)")

# uniq-pk-guard: the branch predicate is decided from the record's OWN key
# instead of by consulting the eligibility predicate. Every other fast-path rival
# holds `directlyDeletable` at a constant (`fun _ => true` / `fun _ => false`), so
# none of them can tell the parameter from any other decision procedure; this one
# is refuted at a predicate that genuinely DEPENDS on the record, which is the
# only way that binder is observably exercised. A record with a present key that
# the eligibility predicate rejects takes the general path in gold, but this rival
# reads the key, finds it present, and takes the fast path — reporting the direct
# tally where the general tally is required (clause (B)).
_UNIQ_PK_GUARD = _swap(
    _BASE, _IF_BLOCK,
    """    if inst.pk.isSome then
      return ([(label, [{ inst with pk := none }])], directCount)""")

# uniq-order-after-clear: the counterpart of nagini's order-of-operations attack,
# which the earlier port note wrongly recorded as inexpressible. The two tallies
# are abstract parameters, but WHICH one is reported is a decision, and this
# rival takes that decision by inspecting the record's key AFTER clearing it. The
# cleared key is always absent, so the branch always resolves the wrong way and
# the general tally is reported on the fast path. Same defect class as nagini's
# read-after-clear: the information the decision needs was destroyed before it
# was read. Violates clause (B).
_UNIQ_ORDER_AFTER_CLEAR = _swap(
    _BASE, _FAST_RET,
    "      let cleared := { inst with pk := none }\n"
    "      let tally := if cleared.pk.isSome then directCount else generalTotal\n"
    "      return ([(label, [cleared])], tally)")


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-clearall-fast",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CLEARALL_FAST,
        "rationale": "structurally-different CORRECT impl: on the smallest job, "
                     "build the cleared structure with the SAME expression the "
                     "general path uses (clearAllPks data) rather than the "
                     "inlined singleton. On a single-group/single-record input "
                     "the two are equal, so clause (A) result.1 = clearAllPks "
                     "data still holds and the direct tally is still reported "
                     "(clause (B)). Frozen proof body closes it (built). If a "
                     "faithful correct impl cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-loop-clear",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LOOP_CLEAR,
        "rationale": "the general path builds the cleared structure with an "
                     "explicit accumulator loop (append one cleared group per "
                     "iteration) instead of calling clearAllPks. Behaviorally "
                     "identical, but measured NOT definitionally equal to the "
                     "frozen impl (a rfl between the two impls fails), so "
                     "clause (A) must be RE-ESTABLISHED for a genuinely new "
                     "impl shape: the loop's forIn form is not the .map form "
                     "the clause is stated over, the frozen proof body does not "
                     "close it, and the case carries its own proof of the "
                     "byte-identical statement plus the loop/accumulator lemma "
                     "that proof needs. If a faithful correct impl cannot "
                     "verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-pred-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PRED_GUARD,
        "rationale": "drop the structural pattern match entirely and branch on "
                     "the spec-level eligibility predicate (isSingleFast data "
                     "directlyDeletable), producing the cleared structure the "
                     "same way on both arms. Behaviorally identical — the match "
                     "and the predicate agree by construction — but measured "
                     "NOT definitionally equal to the frozen impl, so it "
                     "reproves the identical statement rather than inheriting "
                     "it. If it cannot verify => SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    # The frozen obligation carries no `→` hypothesis, so the nagini-shaped
    # "the Requires admits this input" probe has no precondition to aim at. The
    # analogue on a total carrier is the OBLIGATION being unsatisfiable at exactly
    # an F2P-shaped input: the spec pins both output components to closed
    # expressions, and if those two demands could not be jointly met at a normal
    # smallest-job input the obligation would be vacuously unprovable there. This
    # case discharges the spec at that concrete input BY EVALUATION as a leading
    # `have`, then closes the frozen obligation with the unchanged frozen body.
    # Nothing is assumed: no new declaration, statement byte-identical, the ground
    # instance is a `have` prepended to the existing tactic body. The two tallies
    # are pinned DISTINCT (1 and 0) so the branch selection is load-bearing —
    # with equal tallies clause (B) would hold whichever way the branch went.
    {
        "id": "admiss-ground-smallest-job",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_BODY,
            "  have _ground : problem_spec_delete [(3, [{ pk := some 7 }])] "
            "(fun _ => true) 1 0\n"
            "      (implementation_delete [(3, [{ pk := some 7 }])] "
            "(fun _ => true) 1 0) := by\n"
            "    unfold problem_spec_delete implementation_delete clearAllPks "
            "isSingleFast\n"
            "    decide\n"
            + _PROOF_BODY),
        "rationale": "the obligation is discharged at an F2P-shaped input — the "
                     "smallest job, one group holding one record whose key is "
                     "present, eligible for direct removal — by evaluation as a "
                     "`have`, then the frozen obligation is closed verbatim. Both "
                     "clauses are met jointly at that input: the returned "
                     "structure is the input group with the key cleared, and the "
                     "reported count is the direct tally, pinned distinct from "
                     "the general one (1 vs 0) so the branch selection is "
                     "load-bearing. If this could NOT verify, the spec would be "
                     "unsatisfiable at exactly a normal input — the analogue of "
                     "PRECOND-TOO-STRONG on a total carrier. Ports nagini's "
                     "admiss-f2p-shaped-input, which an earlier port note wrongly "
                     "recorded as inexpressible here.",
    },

    # ---- uniqueness / partial-domain (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-drop-clear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_DROP_CLEAR,
        "refinement": "this IS the pre-patch behavior the sole F2P observes: on "
                      "the smallest single-record job the row is removed and the "
                      "count returned, but the removed record's in-memory key is "
                      "never cleared. The F2P creates a directly-removable "
                      "record, removes it, and asserts its key is now absent; "
                      "with the clearing dropped the key keeps its stale value "
                      "and the assertion fails. Its faithful real patch (the "
                      "un-fixed fast branch) is exactly what does NOT resolve.",
        "rationale": "rejected by clause (A) result.1 = clearAllPks data: on the "
                     "fast path the returned record retains its key, so the "
                     "structure differs from clearAllPks data.",
        "witness": """example : ¬ problem_spec_delete
    [(0, [{ pk := some 5 }])] (fun _ => true) 0 0
    (implementation_delete [(0, [{ pk := some 5 }])] (fun _ => true) 0 0) := by
  unfold problem_spec_delete implementation_delete clearAllPks isSingleFast
  decide""",
    },
    {
        "id": "uniq-general-unclear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_GENERAL_UNCLEAR,
        "refinement": "returning the collected groups unchanged on the general "
                      "path corresponds to a patch that removed the general-path "
                      "key-clearing loop: every record removed through the "
                      "general path would keep its stale in-memory key. The "
                      "key-clearing behavior the issue demands must hold for "
                      "EVERY removed record on EVERY path; a patch that cleared "
                      "keys on neither path (or only the fast one) does not "
                      "deliver the fixed behavior.",
        "rationale": "rejected by clause (A) result.1 = clearAllPks data: on the "
                     "general path the input groups are returned with keys "
                     "intact, which differs from clearAllPks data whenever any "
                     "record has a present key.",
        "witness": """example : ¬ problem_spec_delete
    [(0, [{ pk := some 5 }, { pk := some 6 }])] (fun _ => false) 0 0
    (implementation_delete [(0, [{ pk := some 5 }, { pk := some 6 }])] (fun _ => false) 0 0) := by
  unfold problem_spec_delete implementation_delete clearAllPks isSingleFast
  decide""",
    },
    {
        "id": "uniq-fabricate-count",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_FABRICATE_COUNT,
        "refinement": "reporting a hard-coded 1 fabricates the surfaced count. "
                      "The real removal primitive reports the actual number of "
                      "rows removed; count-observing tests read that value. A "
                      "faithful patch that returned a constant 1 would claim a "
                      "removal when the tally was anything else, and would not "
                      "resolve the count-observing tests.",
        "rationale": "rejected by clause (B): the fast-path count must be the "
                     "branch-selected directCount parameter; a literal 1 is not "
                     "that parameter (witness pins directCount = 0).",
        "witness": """example : ¬ problem_spec_delete
    [(1, [{ pk := some 2 }])] (fun _ => true) 0 0
    (implementation_delete [(1, [{ pk := some 2 }])] (fun _ => true) 0 0) := by
  unfold problem_spec_delete implementation_delete clearAllPks isSingleFast
  decide""",
    },
    {
        "id": "uniq-fabricate-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_FABRICATE_ZERO,
        "refinement": "reporting a hard-coded 0 always claims 'nothing removed'. "
                      "A faithful patch returning a constant 0 would tell caller "
                      "code nothing was removed even when a live row was, failing "
                      "the count-observing tests. Supporting near-miss for the "
                      "fabricated-count attack.",
        "rationale": "rejected by clause (B): a literal 0 is not the "
                     "branch-selected directCount parameter (witness pins "
                     "directCount = 7).",
        "witness": """example : ¬ problem_spec_delete
    [(1, [{ pk := some 2 }])] (fun _ => true) 7 7
    (implementation_delete [(1, [{ pk := some 2 }])] (fun _ => true) 7 7) := by
  unfold problem_spec_delete implementation_delete clearAllPks isSingleFast
  decide""",
    },
    {
        "id": "uniq-wrong-tally",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_WRONG_TALLY,
        "refinement": "on the fast path this reports the GENERAL tally where the "
                      "direct tally is required — the analogue of computing the "
                      "count from the wrong source. The two paths tally removals "
                      "differently; a patch that surfaced the general total on "
                      "the fast path would report the wrong count for a "
                      "directly-removed record and would not resolve the "
                      "count-observing tests.",
        "rationale": "rejected by clause (B): on the fast path the count must be "
                     "directCount, not generalTotal; witness pins them distinct "
                     "(directCount = 3, generalTotal = 9).",
        "witness": """example : ¬ problem_spec_delete
    [(0, [{ pk := some 3 }])] (fun _ => true) 3 9
    (implementation_delete [(0, [{ pk := some 3 }])] (fun _ => true) 3 9) := by
  unfold problem_spec_delete implementation_delete clearAllPks isSingleFast
  decide""",
    },
    {
        "id": "uniq-ignore-deletable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_IGNORE_DELETABLE,
        "refinement": "ignoring the direct-removal eligibility check and always "
                      "taking the fast path corresponds to a patch that dropped "
                      "the can-fast-delete guard. For a single-record group whose "
                      "record is NOT eligible, the general path (with its own "
                      "tally) is the correct behavior; taking the fast path "
                      "reports the wrong tally. A patch that removed the guard "
                      "would mis-count (and mis-route) exactly those records.",
        "rationale": "rejected by clause (B): with the branch predicate false on "
                     "a single-record group, isSingleFast is false so the count "
                     "must be generalTotal, but the rival reports directCount; "
                     "witness pins them distinct (directCount = 2, generalTotal "
                     "= 8) and holds directlyDeletable at false — the binder the "
                     "other fast-path rivals hold at true.",
        "witness": """example : ¬ problem_spec_delete
    [(0, [{ pk := some 4 }])] (fun _ => false) 2 8
    (implementation_delete [(0, [{ pk := some 4 }])] (fun _ => false) 2 8) := by
  unfold problem_spec_delete implementation_delete clearAllPks isSingleFast
  decide""",
    },
    {
        "id": "uniq-fast-multigroup",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_FAST_MULTIGROUP,
        "refinement": "the direct single-record removal is only valid for the "
                      "smallest possible job — ONE group holding ONE record. "
                      "Widening its guard to 'the first group holds one "
                      "eligible record' corresponds to a patch that dropped the "
                      "one-group half of the size test: a job that collected "
                      "several kinds of record would take the direct path, "
                      "removing (and reporting) only the first kind and leaving "
                      "every other collected record neither removed nor "
                      "key-cleared. That is a data-loss regression the "
                      "removal-behavior tests observe.",
        "rationale": "rejected on BOTH clauses at a two-group input: clause (A) "
                     "because only the first group is returned where "
                     "clearAllPks data returns both, and clause (B) because "
                     "isSingleFast is false for two groups so the count must be "
                     "generalTotal, not directCount (witness pins them distinct "
                     "at 2 and 8). Exercises the multi-group region of the data "
                     "binder that every other case holds at one group.",
        "witness": """example : ¬ problem_spec_delete
    [(0, [{ pk := some 5 }]), (1, [{ pk := some 6 }])] (fun _ => true) 2 8
    (implementation_delete [(0, [{ pk := some 5 }]), (1, [{ pk := some 6 }])] (fun _ => true) 2 8) := by
  unfold problem_spec_delete implementation_delete clearAllPks isSingleFast
  decide""",
    },
    {
        "id": "uniq-fast-multirecord",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_FAST_MULTIRECORD,
        "refinement": "the companion size-test failure on the other axis: "
                      "widening the guard to 'a single group whose FIRST record "
                      "is eligible' corresponds to a patch that dropped the "
                      "one-record half of the size test. A group holding several "
                      "records would take the direct path, removing and "
                      "reporting only its head record while the rest are left "
                      "unremoved and keep their stale keys — again observable as "
                      "both a wrong count and surviving stale keys.",
        "rationale": "rejected on BOTH clauses at a single group holding two "
                     "records: clause (A) because only the head record is "
                     "returned where clearAllPks data returns both cleared, and "
                     "clause (B) because isSingleFast is false for a "
                     "two-record group so the count must be generalTotal "
                     "(witness pins directCount = 2, generalTotal = 8). "
                     "Exercises the multi-record region of the data binder.",
        "witness": """example : ¬ problem_spec_delete
    [(0, [{ pk := some 5 }, { pk := some 6 }])] (fun _ => true) 2 8
    (implementation_delete [(0, [{ pk := some 5 }, { pk := some 6 }])] (fun _ => true) 2 8) := by
  unfold problem_spec_delete implementation_delete clearAllPks isSingleFast
  decide""",
    },
    {
        "id": "uniq-fast-relabel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_FAST_RELABEL,
        "refinement": "the frame probe SPEC_GUIDE §0.5 demands: the removal "
                      "changes exactly one observable per record — the "
                      "primary-key identity — and must leave everything else "
                      "alone. A patch that also rewrote the group's kind label "
                      "would misreport which kind of record was removed to every "
                      "caller that reads the per-kind breakdown, even though the "
                      "count and the key-clearing were both right.",
        "rationale": "rejected by clause (A) result.1 = clearAllPks data: "
                     "clearAllPks preserves each group's label (it maps only "
                     "over the record list), so substituting a fabricated label "
                     "for the input one differs from clearAllPks data. The "
                     "witness holds the input label at 7 so the fabricated 0 is "
                     "observably wrong; it also exercises the label component of "
                     "the data binder, which every other case holds at 0 or 1.",
        "witness": """example : ¬ problem_spec_delete
    [(7, [{ pk := some 5 }])] (fun _ => true) 2 8
    (implementation_delete [(7, [{ pk := some 5 }])] (fun _ => true) 2 8) := by
  unfold problem_spec_delete implementation_delete clearAllPks isSingleFast
  decide""",
    },
    {
        "id": "uniq-general-headonly",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_GENERAL_HEADONLY,
        "refinement": "the near-miss for uniq-general-unclear: clear the FIRST "
                      "record of each group rather than every record. This is "
                      "the off-by-one a patch makes when it clears the key once "
                      "per group instead of once per record — the group's "
                      "remaining removed records keep their stale keys. The "
                      "demanded behavior is that NO removed record retains a "
                      "key, so clearing one per group does not deliver it, and a "
                      "battery that only attacked 'clear nothing' would not "
                      "catch this.",
        "rationale": "rejected by clause (A) result.1 = clearAllPks data: for a "
                     "group holding two records with present keys, clearAllPks "
                     "clears both, but this rival clears only the head and "
                     "leaves the second record's key intact.",
        "witness": """example : ¬ problem_spec_delete
    [(0, [{ pk := some 5 }, { pk := some 6 }])] (fun _ => false) 2 8
    (implementation_delete [(0, [{ pk := some 5 }, { pk := some 6 }])] (fun _ => false) 2 8) := by
  unfold problem_spec_delete implementation_delete clearAllPks isSingleFast
  decide""",
    },
    {
        "id": "uniq-general-reorder",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_GENERAL_REORDER,
        "refinement": "frame attack on group ORDER: every key is cleared and the "
                      "tally is right, but the groups come back permuted. The "
                      "order the groups are reported in is caller-observable "
                      "(the collection order is the removal order), so a patch "
                      "that reversed it would change observable behavior while "
                      "getting the key-clearing fix itself right — exactly the "
                      "kind of unconstrained output component §0.5 warns a weak "
                      "spec would admit.",
        "rationale": "rejected by clause (A) result.1 = clearAllPks data: "
                     "clearAllPks is a .map and therefore order-preserving, so a "
                     "reversal of two distinguishable groups differs from it. "
                     "The witness uses two groups with distinct labels and keys "
                     "so the permutation is observable.",
        "witness": """example : ¬ problem_spec_delete
    [(0, [{ pk := some 5 }]), (1, [{ pk := some 6 }])] (fun _ => true) 2 8
    (implementation_delete [(0, [{ pk := some 5 }]), (1, [{ pk := some 6 }])] (fun _ => true) 2 8) := by
  unfold problem_spec_delete implementation_delete clearAllPks isSingleFast
  decide""",
    },
    {
        "id": "uniq-general-dropempty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_GENERAL_DROPEMPTY,
        "refinement": "frame attack on group PRESENCE: clear every key "
                      "correctly, then silently drop the groups that hold no "
                      "records. A patch that compacted the reported structure "
                      "this way would omit those kinds from the per-kind "
                      "breakdown callers read, changing observable behavior for "
                      "a job that collected a kind with nothing under it.",
        "rationale": "rejected by clause (A) result.1 = clearAllPks data: "
                     "clearAllPks preserves EVERY group entry, including one "
                     "whose record list is empty (it maps over the list and "
                     "never filters), so removing such an entry differs from it. "
                     "The witness pins an input whose first group is empty — the "
                     "empty-record-list region of the data binder no other case "
                     "reaches.",
        "witness": """example : ¬ problem_spec_delete
    [(0, ([] : List Instance)), (1, [{ pk := some 6 }])] (fun _ => true) 2 8
    (implementation_delete [(0, ([] : List Instance)), (1, [{ pk := some 6 }])] (fun _ => true) 2 8) := by
  unfold problem_spec_delete implementation_delete clearAllPks isSingleFast
  decide""",
    },
    {
        "id": "uniq-pk-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_PK_GUARD,
        "refinement": "deciding whether the direct single-record removal applies "
                      "by looking at the record's own stored identity, rather than "
                      "by asking the eligibility decision, corresponds to a patch "
                      "that replaced the can-fast-delete test with a "
                      "'does it look stored?' test. Those two questions are not "
                      "the same: eligibility depends on whether the record has "
                      "dependents, not on whether it currently has a key. A record "
                      "with dependents but a present key would be routed down the "
                      "direct path and its removal reported with the wrong tally, "
                      "so the count-observing tests would not resolve.",
        "rationale": "rejected by clause (B): at a record whose key is present but "
                     "which the eligibility predicate REJECTS, isSingleFast is "
                     "false so the count must be generalTotal, yet the rival reads "
                     "the present key and reports directCount (witness pins them "
                     "distinct at 2 and 8). This is the only case that holds "
                     "directlyDeletable at a predicate genuinely DEPENDING on the "
                     "record (fun i => i.pk == some 1) rather than at a constant, "
                     "which is the only way that binder is observably exercised: "
                     "against a constant predicate this rival could not be told "
                     "from any other decision procedure.",
        "witness": """example : ¬ problem_spec_delete
    [(0, [{ pk := some 5 }])] (fun i => i.pk == some 1) 2 8
    (implementation_delete [(0, [{ pk := some 5 }])] (fun i => i.pk == some 1) 2 8) := by
  unfold problem_spec_delete implementation_delete clearAllPks isSingleFast
  decide""",
    },
    {
        "id": "uniq-order-after-clear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_ORDER_AFTER_CLEAR,
        "refinement": "the order-of-operations defect: decide WHICH tally to "
                      "report by inspecting the record's key AFTER clearing it. "
                      "The cleared key is always absent, so the decision always "
                      "resolves the same (wrong) way. This is the read-after-"
                      "clear mistake a patch makes when it moves the "
                      "key-clearing above the code that still needs the stored "
                      "identity: the information the later step depends on has "
                      "already been destroyed, and the surfaced count is wrong "
                      "for every directly-removed record. It does not resolve "
                      "the count-observing tests.",
        "rationale": "rejected by clause (B): on the smallest job isSingleFast "
                     "is true so the count must be directCount, but the rival "
                     "reads the already-cleared key, finds it absent, and "
                     "reports generalTotal. Witness pins them distinct "
                     "(directCount = 2, generalTotal = 8) — with equal tallies "
                     "the defect would be invisible, which is why this case "
                     "cannot be folded into the equal-tally witnesses.",
        "witness": """example : ¬ problem_spec_delete
    [(0, [{ pk := some 5 }])] (fun _ => true) 2 8
    (implementation_delete [(0, [{ pk := some 5 }])] (fun _ => true) 2 8) := by
  unfold problem_spec_delete implementation_delete clearAllPks isSingleFast
  decide""",
    },
]
