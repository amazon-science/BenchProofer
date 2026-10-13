# properties.py — G-PBT falsification battery for django__django-11603 (lean lane).
# NOT a Lean module: a manifest of adversarial cases the gate elaborates against
# the frozen spec. Ported from the nagini sibling's properties.py and re-expressed
# against this backend's carrier.
#
# DEFENDED SURFACE (read off Solution.lean)
#
#   problem_spec_construct (kind : AggKind) (distinct : Bool)
#                          (filter : Option String)
#                          (result : Except AggError AggState) : Prop
#
#   One obligation, `theorem correct_construct`, over THREE input binders. The
#   spec is a single if-then-else with two independent arms:
#
#     (C1) distinct = true ∧ permitsDistinct kind = false
#            → result = Except.error AggError.distinctNotAllowed
#          — the construction must FAIL on exactly the request the per-kind
#            policy forbids.
#     (C2) otherwise
#            → result = Except.ok { kind := kind, distinct := distinct,
#                                   filter := filter }
#          — it must SUCCEED and record all three inputs unchanged. Three
#            independent record-fidelity sub-clauses live here (kind, distinct,
#            filter), each separately attackable.
#
#   `permitsDistinct` sits in the `pure` region (spec view) and is the DESIRED
#   per-kind policy: true for the averaging/counting/summation kinds, false for
#   the two extremum kinds and the two statistical-dispersion kinds. The
#   implementation performs its own per-kind lookup inside the impl region, so a
#   rival may encode any policy it likes there without touching the spec — which
#   is what makes the policy table the primary attack surface on this carrier.
#
# CARRIER NARROWING vs the nagini sibling
#
# The nagini model contracted THREE functions over plain booleans —
# `construct_dedup(allow_dedup, dedup)` plus a `build_mean`/`build_total` pair
# that each delegate to it with the capability hard-wired. This bundle collapses
# all of that into ONE relation whose first binder is the aggregate KIND, and
# whose policy lookup is a total function of that kind. Consequences:
#
#   * nagini's `allow_dedup` parameter is not an input here. Where nagini passed
#     the capability explicitly (and could therefore be attacked by passing the
#     wrong one), this carrier DERIVES it from `kind`. So nagini's two
#     `*-prepatch` rivals — `build_mean`/`build_total` routing through the
#     disabled capability — become single-entry edits to the impl's policy table
#     (weak-prepatch-avg / weak-prepatch-sum). The argument ports exactly; only
#     the mechanics change.
#   * nagini's `build_mean`/`build_total` pair, being two functions that differ
#     only in which family they name, collapse into two POINTS of one binder
#     (`kind = avg`, `kind = sum`) rather than two obligations. Every nagini case
#     that existed only because there were two delegating wrappers therefore has
#     a single counterpart here, not two.
#   * The raise/return distinction nagini expressed with `Exsures` is a VALUE
#     distinction here (`Except.error` vs `Except.ok`), so nagini's
#     control-flow-effect rival (`weak-construct-over-refuse`) ports as an
#     ordinary value-level rival with a `decide`-able witness — it needs no
#     special machinery on this carrier.
#   * Two binders have NO nagini counterpart at all: the `filter` payload (nagini
#     modeled no filter) and the `kind` field of the recorded result. Both are
#     record-fidelity sub-clauses of C2 that nagini's boolean carrier could not
#     express, so rivals attacking them are new work added here to keep every
#     input binder exercised by some reject witness.
#
# CLASSES DELIBERATELY NOT PORTED (stated, not silently dropped)
#
#   * FRAME / PERMISSION-MUTATION — VACUOUS here. The nagini file already records
#     this class as inapplicable (its inputs are immutable scalars, no heap
#     permissions). Lean is referentially transparent: there is no aliasable
#     read-only input a variant could overwrite. Nothing to port, and nothing
#     fabricated in its place.
#   * DIVERGENCE / NON-TERMINATION — the nagini sibling DOES carry one
#     (`weak-mean-diverge`, an `Invariant(True)` spin loop that satisfied every
#     postcondition vacuously until a termination obligation was added). On this
#     carrier the class is genuinely VACUOUS, not a spec hole:
#     `implementation_construct` is a total Lean `def`, so a diverging
#     implementation cannot be written at all and there is no rival to ship.
#     This is specifically NOT the velvet situation, where under
#     `loom.semantics.termination "partial"` a non-terminating implementation
#     satisfies every clause vacuously and VERIFIES while its faithful patch
#     hangs the graded test — a known spec hole rather than an empty class
#     (the corpus-wide termination-semantics finding). On lean the totality of `def` closes it.
#   * UNGROUNDED-ORACLE — N/A for the same reason the nagini file gives: C2 pins
#     the result to the INPUTS (`distinct := distinct`, `filter := filter`), not
#     to an opaque answer key, so there is no wrong echo to build. The honest
#     substitute is the positive control pos-policy-complement below, which shows
#     the policy is pinned to its VALUE and not to a syntactic echo of the
#     spec's own `permitsDistinct` table.
#   * AXIOM lane — DROPPED. meta.json `axioms == []` and
#     `deep_model_references == []`; there is no `opaque` callee anywhere on this
#     path, the policy lookup and the field stores being modeled with concrete
#     operations. The axiom lane is G-AX's job and this gate ignores it.
#     AXIOM_TESTS = [].
#
# A NOTE ON REFINEMENT ARGUMENTS, AND TWO RIVALS DROPPED BECAUSE OF THEM
#
# The graded test set for this instance is drawn ENTIRELY from one suite
# (aggregation.tests.AggregateTestCase). It contains no test that asserts a
# forbidden kind refuses a distinct request, and no test that exercises the
# filter payload. That materially constrains which rivals have an honest
# `refinement`, and two otherwise-attractive rivals were dropped rather than
# shipped with an argument the graded set does not support — see `assessment`
# in the port report. Each rival below states which graded observable its
# faithful patch actually breaks, and rivals whose break is visible only in the
# modeled relation say so plainly instead of claiming a graded failure.

from pathlib import Path

INSTANCE = "django__django-11603"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- Frozen regions, extracted verbatim so the manifest breaks loudly if the
# frozen solution ever changes. The impl region body and the proof TACTIC body
# are the only regions a variant may edit; the spec view, the signature and the
# byte-identical `theorem correct_construct` statement are never touched, so
# `same_spec` and the obligation-preservation rule hold by construction.

_IMPL_OLD = """\
def implementation_construct (kind : AggKind) (distinct : Bool) (filter : Option String) :
    Except AggError AggState := Id.run do
  let permitted : Bool := match kind with
    | .avg => true
    | .count => true
    | .sum => true
    | _ => false
  if distinct && !permitted then
    return Except.error AggError.distinctNotAllowed
  let mut st : AggState := { kind := kind, distinct := false, filter := none }
  st := { st with distinct := distinct }
  st := { st with filter := filter }
  return Except.ok st"""

assert _BASE.count(_IMPL_OLD) == 1, "impl region drifted from expected text"

_PROOF_OLD = """\
  intro kind distinct filter
  unfold problem_spec_construct implementation_construct permitsDistinct
  cases kind <;> cases distinct <;> rfl"""

assert _BASE.count(_PROOF_OLD) == 1, "proof region drifted from expected text"


def _impl(new_impl, new_proof=None):
    """Build a full Solution.lean variant: replace the impl body and, when a
    reshaped positive needs it, the proof tactic body. Nothing else moves."""
    out = _swap(_BASE, _IMPL_OLD, new_impl)
    if new_proof is not None:
        out = _swap(out, _PROOF_OLD, new_proof)
    return out


# The frozen impl's shape, parameterized so a rival can edit exactly one of the
# two halves (the per-kind policy table, or the guard-and-store tail) and leave
# the other byte-identical to gold. Keeping the untouched half verbatim is what
# makes each rival a single-fault variant rather than a rewrite.
_TAIL_FROZEN = """\
  if distinct && !permitted then
    return Except.error AggError.distinctNotAllowed
  let mut st : AggState := { kind := kind, distinct := false, filter := none }
  st := { st with distinct := distinct }
  st := { st with filter := filter }
  return Except.ok st"""

_POLICY_GOLD = ["    | .avg => true", "    | .count => true",
                "    | .sum => true", "    | _ => false"]


def _variant(policy=None, tail=_TAIL_FROZEN):
    return ("def implementation_construct (kind : AggKind) (distinct : Bool) "
            "(filter : Option String) :\n"
            "    Except AggError AggState := Id.run do\n"
            "  let permitted : Bool := match kind with\n"
            + "\n".join(_POLICY_GOLD if policy is None else policy) + "\n"
            + tail)


# ---------------------------------------------------------------------------
# WITNESSES. Each states the spec predicate directly at one concrete, fully
# decidable input triple. `decide` cannot be used here: the `Decidable` instance
# does not reduce through the `Id.run do` block's `__do_jp` join points (measured
# — it reports `failed to synthesize Decidable` on the unreduced term), so the
# witnesses hand the three definitions to `simp`, which reduces the monadic
# scaffold and closes the disequality. No opaque term appears anywhere in this
# carrier, so no witness needs to condition on a hypothesis; every one is stated
# at literal inputs and binds nothing, which is also why none of them can be
# `witness-inconsistent`.
# ---------------------------------------------------------------------------

def _witness(kind, distinct, filt):
    args = f"AggKind.{kind} {distinct} {filt}"
    return f"""\
example : ¬ problem_spec_construct {args}
    (implementation_construct {args}) := by
  simp [problem_spec_construct, implementation_construct, permitsDistinct]"""


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG. Each is a
# structurally different but behaviourally identical correct implementation. The
# `theorem correct_construct` statement is byte-identical throughout; where a
# reshaped implementation needs a different script the tactic body is reproven
# honestly. No new lemma, no new axiom, no `sorry`, no `native_decide`.
# ===========================================================================

# pos-guard-reorder — ports nagini `pos-construct-reorder`: handle the permitted
# case first and fall through to the failure, instead of guarding the failure up
# front. De Morgan turns `distinct && !permitted` into `!distinct || permitted`,
# so the branch order is inverted while the behaviour is identical. The frozen
# `cases kind <;> cases distinct <;> rfl` script still closes because every one
# of the 14 kind×distinct combinations still reduces definitionally.
_POS_REORDER = """\
def implementation_construct (kind : AggKind) (distinct : Bool) (filter : Option String) :
    Except AggError AggState := Id.run do
  let permitted : Bool := match kind with
    | .avg => true
    | .count => true
    | .sum => true
    | _ => false
  if !distinct || permitted then
    let mut st : AggState := { kind := kind, distinct := false, filter := none }
    st := { st with distinct := distinct }
    st := { st with filter := filter }
    return Except.ok st
  return Except.error AggError.distinctNotAllowed"""

# pos-pure-functional — ports nagini `pos-mean-local` (the "same honest impl,
# different shape" control), pushed further: drop the imperative encoding
# entirely. No `Id.run`, no `let mut`, no incremental field stores — the result
# record is built in one go. Confirms the spec does not secretly depend on the
# monadic scaffolding or on the store-then-overwrite sequence the frozen impl
# uses. Verified with the frozen tactic body unchanged.
_POS_PURE = """\
def implementation_construct (kind : AggKind) (distinct : Bool) (filter : Option String) :
    Except AggError AggState :=
  let permitted : Bool := match kind with
    | .avg => true
    | .count => true
    | .sum => true
    | _ => false
  if distinct && !permitted then
    Except.error AggError.distinctNotAllowed
  else
    Except.ok { kind := kind, distinct := distinct, filter := filter }"""

# pos-policy-complement — the grounded-oracle control, adapted to this carrier.
# The frozen impl enumerates the PERMITTED kinds, which are exactly the kinds the
# spec's own `permitsDistinct` maps to `true`; this impl instead enumerates the
# COMPLEMENT (the forbidden kinds) and inverts the guard accordingly, so it never
# reproduces the spec table's shape. Verifying shows C1/C2 are pinned to the
# policy's VALUE at each kind rather than to a syntactic echo of the spec's own
# enumeration — the honest substitute for the ungrounded-oracle class the nagini
# file records as N/A.
_POS_COMPLEMENT = """\
def implementation_construct (kind : AggKind) (distinct : Bool) (filter : Option String) :
    Except AggError AggState := Id.run do
  let forbidden : Bool := match kind with
    | .max => true
    | .min => true
    | .stdDev => true
    | .variance => true
    | _ => false
  if distinct && forbidden then
    return Except.error AggError.distinctNotAllowed
  let mut st : AggState := { kind := kind, distinct := false, filter := none }
  st := { st with distinct := distinct }
  st := { st with filter := filter }
  return Except.ok st"""

# admiss-policy-points — ports nagini `admiss-mean-distinct`. Nagini asserted the
# discriminating input's admissibility with an in-body `Assert(...)`; the lean
# analogue is the same claims as in-body `have`s.
#
# AUDIT REPAIR. The first version of this case stated its `have`s over
# `permitsDistinct` ALONE (`permitsDistinct AggKind.avg = true`, etc.). That pins
# the policy table but never mentions `problem_spec_construct`, so it did not
# support the claim its own rationale made — that the OBLIGATION admits the
# discriminating inputs. Being a claim about a `pure`-region function only, it
# would have gone on verifying even if the obligation were unsatisfiable at those
# points, which is exactly the PRECOND-TOO-STRONG direction this lane exists to
# detect. The `have`s now discharge the obligation's own predicate, applied to
# concrete F2P-shaped argument triples AND the concrete result the spec demands
# there, before the frozen obligation is closed verbatim below. Measured: this
# form elaborates (exit 0), and the same form with `_ground_avg`'s result changed
# to a refusal FAILS (exit 1, `unsolved goals`), so the `have`s carry information
# about the obligation rather than restating a table.
_ADMISS = """\
def implementation_construct (kind : AggKind) (distinct : Bool) (filter : Option String) :
    Except AggError AggState := Id.run do
  have _ground_avg : problem_spec_construct AggKind.avg true none
      (Except.ok { kind := AggKind.avg, distinct := true, filter := none }) := by
    simp [problem_spec_construct, permitsDistinct]
  have _ground_sum : problem_spec_construct AggKind.sum true (some "r")
      (Except.ok { kind := AggKind.sum, distinct := true, filter := some "r" }) := by
    simp [problem_spec_construct, permitsDistinct]
  have _ground_count : problem_spec_construct AggKind.count true none
      (Except.ok { kind := AggKind.count, distinct := true, filter := none }) := by
    simp [problem_spec_construct, permitsDistinct]
  have _ground_refuse : problem_spec_construct AggKind.variance true none
      (Except.error AggError.distinctNotAllowed) := by
    simp [problem_spec_construct, permitsDistinct]
  let permitted : Bool := match kind with
    | .avg => true
    | .count => true
    | .sum => true
    | _ => false
  if distinct && !permitted then
    return Except.error AggError.distinctNotAllowed
  let mut st : AggState := { kind := kind, distinct := false, filter := none }
  st := { st with distinct := distinct }
  st := { st with filter := filter }
  return Except.ok st"""


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Every one edits only
# the impl region and ships a witness that has been SEEN to discriminate: it
# elaborates against the rival and fails against the frozen solution.
# ===========================================================================

# --- Attacks on the per-kind policy table (C1/C2 boundary) -----------------

# The two single-entry regressions: drop the averaging kind, or drop the
# summation kind, from the set the policy permits. These are the direct ports of
# nagini `weak-mean-prepatch` / `weak-total-prepatch`, whose rivals routed
# `build_mean`/`build_total` through the disabled capability.
_WEAK_PREPATCH_AVG = _variant(["    | .count => true", "    | .sum => true",
                               "    | _ => false"])
_WEAK_PREPATCH_SUM = _variant(["    | .avg => true", "    | .count => true",
                               "    | _ => false"])

# The counting kind is the one whose permissiveness this change does NOT
# introduce — it was already permitted. A rival that drops it regresses a
# behaviour the change was supposed to leave alone.
_WEAK_DROP_COUNT = _variant(["    | .avg => true", "    | .sum => true",
                             "    | _ => false"])

# Over-permission in the other direction: extend the policy to the extremum
# kinds, which must keep refusing.
_WEAK_PERMIT_EXTREMUM = _variant(
    ["    | .avg => true", "    | .count => true", "    | .sum => true",
     "    | .max => true", "    | .min => true", "    | _ => false"])

# The wholesale inversion: permit exactly the kinds that must refuse and refuse
# exactly the kinds that must permit.
_WEAK_POLICY_INVERTED = _variant(
    ["    | .max => true", "    | .min => true", "    | .stdDev => true",
     "    | .variance => true", "    | _ => false"])

# --- Attacks on the guard itself (C1) --------------------------------------

# Ports nagini `weak-construct-over-refuse`: refuse on every distinct request,
# ignoring the policy entirely. On nagini this was a control-flow-effect attack
# needing the `Exsures` domain to catch; on this carrier the difference is a
# plain value difference (`error` where `ok` is required).
_WEAK_OVER_REFUSE = """\
def implementation_construct (kind : AggKind) (distinct : Bool) (filter : Option String) :
    Except AggError AggState := Id.run do
  if distinct then
    return Except.error AggError.distinctNotAllowed
  let mut st : AggState := { kind := kind, distinct := false, filter := none }
  st := { st with distinct := distinct }
  st := { st with filter := filter }
  return Except.ok st"""

# Ports nagini `weak-construct-never-refuse`: drop the guard entirely and accept
# everything.
_WEAK_DROP_GUARD = """\
def implementation_construct (kind : AggKind) (distinct : Bool) (filter : Option String) :
    Except AggError AggState := Id.run do
  let mut st : AggState := { kind := kind, distinct := false, filter := none }
  st := { st with distinct := distinct }
  st := { st with filter := filter }
  return Except.ok st"""

# NO nagini counterpart. The guard's two conjuncts are swapped for a disjunction,
# so the construction fails whenever a distinct request is made OR the kind's
# policy forbids it — even with no distinct request at all. Every other guard
# rival above still fails only on inputs that DID request distinct operation;
# this is the only one that can fail on `distinct = false`, which is the sub-
# domain the whole C2 arm lives in.
_WEAK_REFUSE_FORBIDDEN_KIND = """\
def implementation_construct (kind : AggKind) (distinct : Bool) (filter : Option String) :
    Except AggError AggState := Id.run do
  let permitted : Bool := match kind with
    | .avg => true
    | .count => true
    | .sum => true
    | _ => false
  if distinct || !permitted then
    return Except.error AggError.distinctNotAllowed
  let mut st : AggState := { kind := kind, distinct := false, filter := none }
  st := { st with distinct := distinct }
  st := { st with filter := filter }
  return Except.ok st"""

# --- Attacks on record fidelity (the three C2 sub-clauses) -----------------

# Ports nagini `weak-construct-const-false` / `weak-mean-const-false`: construct
# successfully but never record the request, leaving the recorded flag at its
# initial value.
_WEAK_RECORD_CONST_FALSE = _variant(tail="""\
  if distinct && !permitted then
    return Except.error AggError.distinctNotAllowed
  let mut st : AggState := { kind := kind, distinct := false, filter := none }
  st := { st with filter := filter }
  return Except.ok st""")

# Ports nagini `weak-construct-negate`: record the negation of the request.
_WEAK_RECORD_NEGATE = _variant(tail="""\
  if distinct && !permitted then
    return Except.error AggError.distinctNotAllowed
  let mut st : AggState := { kind := kind, distinct := false, filter := none }
  st := { st with distinct := !distinct }
  st := { st with filter := filter }
  return Except.ok st""")

# NO nagini counterpart — the nagini carrier had no filter payload. Drop the
# filter store, leaving the recorded filter at its initial absent value.
_WEAK_DROP_FILTER = _variant(tail="""\
  if distinct && !permitted then
    return Except.error AggError.distinctNotAllowed
  let mut st : AggState := { kind := kind, distinct := false, filter := none }
  st := { st with distinct := distinct }
  return Except.ok st""")

# NO nagini counterpart. ADDED DURING AUDIT: every record-fidelity rival above is
# UNIFORM in `kind` — it mishandles the recorded flag the same way at all seven
# kinds — so all of them are refuted by a witness at any one kind, and none of
# them shows the recorded flag is pinned KIND-BY-KIND. This rival is correct at
# six of the seven kinds and drops the request at exactly one, so it can only be
# caught by a witness sited at that kind. The `kind == AggKind.count` test is
# written with the derived `DecidableEq` rather than a nested `match`, because a
# `match` on `kind` inside the `do` block blocks equation-theorem generation for
# `implementation_construct` and the witness then fails against the RIVAL too
# (measured: `failed to generate equational theorem`), which would make the case
# inconclusive rather than discriminating.
_WEAK_RECORD_FAULT_AT_COUNT = _variant(tail="""\
  if distinct && !permitted then
    return Except.error AggError.distinctNotAllowed
  let mut st : AggState := { kind := kind, distinct := false, filter := none }
  st := { st with distinct := (distinct && !(kind == AggKind.count)) }
  st := { st with filter := filter }
  return Except.ok st""")

# NO nagini counterpart — the nagini carrier had no recorded kind either. Record
# a fixed kind rather than the requested one.
_WEAK_RECORD_FIXED_KIND = _variant(tail="""\
  if distinct && !permitted then
    return Except.error AggError.distinctNotAllowed
  let mut st : AggState := { kind := AggKind.avg, distinct := false, filter := none }
  st := { st with distinct := distinct }
  st := { st with filter := filter }
  return Except.ok st""")


SPEC_TESTS = [
    # ---------------- soundness / admissibility positives ----------------
    {
        "id": "pos-guard-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "ports nagini pos-construct-reorder. Handles the permitted case "
            "first and falls through to the failure, instead of guarding the "
            "failure up front — the guard is De Morgan'd from "
            "`distinct && !permitted` to `!distinct || permitted`, so the "
            "control flow is inverted while the behaviour is identical on all "
            "14 kind×distinct combinations. Must satisfy both C1 and C2; the "
            "frozen `cases kind <;> cases distinct <;> rfl` script still closes "
            "because each combination reduces definitionally. If it fails => "
            "SPEC-TOO-STRONG (the spec would be constraining the branch ORDER, "
            "not the relation)."
        ),
    },
    {
        "id": "pos-pure-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_PURE),
        "rationale": (
            "ports nagini pos-mean-local (the reshape-the-honest-impl control), "
            "pushed further: the imperative encoding is dropped entirely — no "
            "Id.run, no let mut, and the result record is built in one "
            "expression instead of by three successive field stores. Confirms "
            "the spec does not secretly depend on the monadic scaffold or on "
            "the store-then-overwrite sequence the frozen impl happens to use. "
            "Verifies with the frozen tactic body unchanged. If it fails => "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-policy-complement",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_COMPLEMENT),
        "rationale": (
            "the grounded-oracle control adapted to this carrier (the nagini "
            "file records the ungrounded-oracle CLASS as N/A because C2 pins "
            "the result to the inputs; this is its honest substitute for the "
            "policy half). The frozen impl enumerates the permitted kinds — "
            "exactly the kinds the spec's own `permitsDistinct` sends to true — "
            "so it could in principle be passing by echoing the spec table's "
            "shape. This impl enumerates the COMPLEMENT (the forbidden kinds) "
            "and inverts the guard, never reproducing that shape. Verifying "
            "shows the C1/C2 boundary is pinned to the policy's VALUE at each "
            "kind. If it fails => SPEC-TOO-STRONG (the spec would demand the "
            "echo)."
        ),
    },
    {
        "id": "admiss-policy-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "ports nagini admiss-mean-distinct. Nagini asserted the "
            "discriminating input in-body with `Assert(...)`; the lean analogue "
            "is the same claims as in-body `have`s discharged by `decide`. It "
            "discharges the obligation's OWN predicate at concrete F2P-shaped "
            "argument triples — the three permitted kinds each asked for "
            "distinct operation, plus one dispersion kind that must refuse — "
            "each paired with the concrete result the spec demands there, as "
            "in-body `have`s, before closing the frozen obligation verbatim. "
            "`correct_construct` binds no precondition hypothesis (the relation "
            "is total over the three binders), so the analogue of "
            "PRECOND-TOO-STRONG on this total carrier is the obligation being "
            "UNSATISFIABLE at exactly an F2P-shaped input; a `have` that "
            "exhibits the satisfying result at that input tests it directly. "
            "The impl tail and the frozen proof script are otherwise verbatim, "
            "so the only thing this case can fail on is one of those points "
            "ceasing to be satisfiable. Repaired during audit: the earlier form "
            "stated its `have`s over the `pure`-region policy table alone, which "
            "never mentioned the obligation and so would have verified even if "
            "the obligation were unsatisfiable at those points. If it fails => "
            "PRECOND-TOO-STRONG."
        ),
    },

    # ---------------- policy-table rivals (C1/C2 boundary) ----------------
    {
        "id": "weak-prepatch-avg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPATCH_AVG),
        "witness": _witness("avg", "true", "none"),
        "refinement": (
            "this is the pre-change policy for the averaging kind, and it is "
            "exactly Solution_prepatch.lean's defect isolated to one kind. Its "
            "faithful real patch is the one that omits the averaging kind from "
            "the change, so constructing an averaging aggregate over distinct "
            "values still fails outright where the graded set requires it to "
            "succeed and produce the distinct-valued average. The F2P "
            "test_distinct_on_aggregate iterates over the averaging, counting "
            "and summation kinds and asserts each returns its distinct-valued "
            "result; the averaging subtest raises instead. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C2: at (avg, true, none) the policy permits distinct "
            "operation, so the construction must succeed and record the flag, "
            "but the rival's table omits the averaging kind and its guard fires, "
            "yielding Except.error. Witness at (avg, true, none) — the exact "
            "discriminating point of the change. If it verifies => SPEC-TOO-WEAK "
            "(the policy would be unpinned at the averaging kind)."
        ),
    },
    {
        "id": "weak-prepatch-sum",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPATCH_SUM),
        "witness": _witness("sum", "true", '(some "r")'),
        "refinement": (
            "the same single-entry regression at the summation kind — the second "
            "half of Solution_prepatch.lean's defect, and the port of the nagini "
            "sibling's second prepatch witness. Its faithful patch omits the "
            "summation kind, so the summation subtest of the F2P "
            "test_distinct_on_aggregate raises instead of returning the "
            "distinct-valued total. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C2 at (sum, true, some \"r\"): the policy permits "
            "distinct operation for the summation kind, so the construction must "
            "succeed and record all three inputs, but the rival's table omits it "
            "and the guard fires. Witnessed with a PRESENT filter rather than an "
            "absent one, so this case and weak-prepatch-avg probe genuinely "
            "different points of the input space instead of sharing one. If it "
            "verifies => SPEC-TOO-WEAK at the summation kind."
        ),
    },
    {
        "id": "weak-drop-count",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_COUNT),
        "witness": _witness("count", "true", "none"),
        "refinement": (
            "a REGRESSION rather than a missing improvement, and the reason it "
            "matters: the counting kind's permissiveness is not something this "
            "change introduces — it is pre-existing behaviour the change must "
            "leave alone. A real patch that made the two newly-permitted kinds "
            "work by REPLACING the permitted set rather than extending it would "
            "look like a fix and break the counting kind. The graded set "
            "exercises a distinct counting request in several places "
            "(test_count_distinct_expression asserts the distinct count, and "
            "the F2P test_distinct_on_aggregate covers the counting kind in its "
            "own subtest), all of which would then raise. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C2 at (count, true, none): the policy permits distinct "
            "operation for the counting kind, so construction must succeed, but "
            "the rival's table drops it and the guard fires. Attacks a different "
            "point of the `kind` binder than either prepatch rival — the one "
            "whose correct value the change does not alter — so it is the case "
            "that pins the policy as an EXTENSION rather than a replacement. If "
            "it verifies => SPEC-TOO-WEAK at the counting kind."
        ),
    },
    {
        "id": "weak-permit-extremum",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PERMIT_EXTREMUM),
        "witness": _witness("max", "true", "none"),
        "refinement": (
            "over-permission in the opposite direction from every rival above: "
            "the two extremum kinds are added to the permitted set. This is the "
            "one the public issue text actively invites — it muses that the "
            "change 'could also be applied to Min and Max (although pointless)' "
            "— and it is precisely NOT what the graded behaviour wants: those "
            "kinds must keep refusing. Its faithful patch marks two extra kinds "
            "permissive, so a distinct request on an extremum kind silently "
            "constructs and emits distinct-qualified SQL instead of refusing, "
            "changing the modeled failure observable on a domain the desired "
            "policy reserves for refusal. NOTE, stated rather than "
            "over-claimed: no test in this instance's graded set asserts that a "
            "forbidden kind refuses (the suite that does, "
            "aggregation_regress test_allow_distinct, is not in either graded "
            "list), so the honest claim is that this rival contradicts the "
            "modeled relation and the desired policy, not that it flips a "
            "graded test. It is shipped because C1 is a real half of the frozen "
            "spec and a battery that attacked only under-permission would leave "
            "it undefended."
        ),
        "rationale": (
            "rejected by C1 at (max, true, none): distinct is requested and the "
            "policy forbids it for the extremum kind, so the result must be "
            "Except.error, but the rival's table permits it and it constructs "
            "successfully. This is the ONLY direction of policy error that C1 "
            "rather than C2 catches — every other policy rival above is caught "
            "by C2 — so without it the C1 arm has no attacker at all. If it "
            "verifies => SPEC-TOO-WEAK (the refusal domain would be unpinned)."
        ),
    },
    {
        "id": "weak-policy-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_POLICY_INVERTED),
        "witness": _witness("max", "true", "none"),
        "refinement": (
            "the wholesale inversion: permit exactly the kinds that must refuse, "
            "refuse exactly the kinds that must permit. Its faithful patch marks "
            "the four dispersion/extremum kinds permissive and leaves the other "
            "three refusing, so the F2P test_distinct_on_aggregate raises on all "
            "three of its subtests. Does NOT resolve. Shipped alongside "
            "weak-permit-extremum rather than in place of it because it breaks "
            "BOTH arms at once and so could be rejected on the C2 arm alone; "
            "weak-permit-extremum is the strictly tighter case that isolates C1."
        ),
        "rationale": (
            "rejected by C1 at (max, true, none) — and also by C2 at every "
            "permitted kind, which is what makes it the looser of the two "
            "over-permission rivals. It shares weak-permit-extremum's witness "
            "point because the two really do fail there for the same reason (an "
            "extremum kind wrongly permitted); the tighter case carries the "
            "isolating argument, and this one exists to show a rival that gets "
            "the policy globally backwards is caught rather than accidentally "
            "agreeing with the spec on a symmetry. If it verifies => "
            "SPEC-TOO-WEAK."
        ),
    },

    # ---------------- guard rivals (C1) ----------------
    {
        "id": "weak-over-refuse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_OVER_REFUSE),
        "witness": _witness("sum", "true", "none"),
        "refinement": (
            "ports nagini weak-construct-over-refuse. Refuse on every distinct "
            "request, consulting no policy at all. Its faithful patch refuses a "
            "distinct request unconditionally, so all three subtests of the F2P "
            "test_distinct_on_aggregate raise, and the pre-existing distinct "
            "counting assertions in the graded set break too. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C2 at (sum, true, none): the policy permits distinct "
            "operation there so construction must succeed and record the flag, "
            "but the rival returns Except.error. On nagini this rival was a "
            "control-flow-EFFECT attack that needed the Exsures raise-domain to "
            "catch, because the value abstraction could not see a raise; on this "
            "carrier the failure is itself a value (Except.error vs Except.ok) so "
            "it is caught by the ordinary result equation and its witness is "
            "plainly decidable. Witnessed at the summation kind with an absent "
            "filter — a point no other rival's witness uses. If it verifies => "
            "SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-drop-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_GUARD),
        "witness": _witness("variance", "true", "none"),
        "refinement": (
            "ports nagini weak-construct-never-refuse. Drop the validation "
            "entirely and accept everything. This is the behaviour the codebase "
            "had before distinct-capability gating existed at all: every kind "
            "silently accepts a distinct request. Its faithful patch deletes the "
            "guard, so a dispersion kind asked for distinct operation constructs "
            "and emits distinct-qualified SQL instead of refusing — the same "
            "caveat as weak-permit-extremum applies and is stated rather than "
            "over-claimed: the graded set for this instance contains no test "
            "asserting a forbidden kind refuses, so the claim is that the rival "
            "contradicts the modeled relation, not that it flips a graded test. "
            "Shipped because deleting the guard is the single most likely "
            "over-broad 'fix' for this issue and C1 must be defended against it."
        ),
        "rationale": (
            "rejected by C1 at (variance, true, none): distinct is requested and "
            "the policy forbids it for a dispersion kind, so the result must be "
            "Except.error, but the guardless rival constructs successfully. "
            "Probes a dispersion kind, distinct from weak-permit-extremum's "
            "extremum kind, so the two do not collapse onto one point of the "
            "`kind` binder even though both attack C1. If it verifies => "
            "SPEC-TOO-WEAK (the refusal would be entirely unpinned)."
        ),
    },
    {
        "id": "weak-refuse-forbidden-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_REFUSE_FORBIDDEN_KIND),
        "witness": _witness("max", "false", "none"),
        "refinement": (
            "NO nagini counterpart. The guard's conjunction becomes a "
            "disjunction, so the construction fails whenever distinct operation "
            "is requested OR the kind's policy forbids it. Its faithful patch is "
            "the plausible typo of writing the validation with the wrong "
            "connective, and its effect is far broader than any other rival "
            "here: a kind whose policy forbids distinct operation can no longer "
            "be constructed AT ALL, even with no distinct request. Every graded "
            "test that builds an extremum or dispersion aggregate in the ordinary "
            "way then raises — test_aggregate_multi_join, test_even_more_"
            "aggregate, test_annotate_ordering and several more all construct "
            "such aggregates with no distinct request whatsoever. Does NOT "
            "resolve, and unlike the two C1 rivals above this one's graded "
            "breakage is direct and needs no caveat."
        ),
        "rationale": (
            "rejected by C2 at (max, false, none): NO distinct operation is "
            "requested, so the C1 antecedent is false and the spec requires a "
            "successful construction recording all three inputs — but the rival "
            "fails because the kind's policy happens to forbid distinct. This is "
            "the only rival in the battery whose witness holds `distinct = "
            "false`; every other reject witness above requests distinct "
            "operation, which would leave the `distinct` binder pinned at `true` "
            "across the whole reject lane and the entire C2 arm — the arm that "
            "governs ordinary construction — probed only on inputs that asked "
            "for distinct. If it verifies => SPEC-TOO-WEAK on the no-request "
            "sub-domain."
        ),
    },

    # ---------------- record-fidelity rivals (C2 sub-clauses) ----------------
    {
        "id": "weak-record-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_RECORD_CONST_FALSE),
        "witness": _witness("avg", "true", '(some "f")'),
        "refinement": (
            "ports nagini weak-construct-const-false / weak-mean-const-false. "
            "Construct successfully — never refusing — but drop the request on "
            "the floor, leaving the recorded flag at its initial value. This is "
            "the most dangerous shape of all because it is SILENT: nothing "
            "raises. Its faithful patch stores a constant instead of the "
            "requested flag, so the constructed aggregate does not carry the "
            "distinct request into the emitted SQL and the aggregate ranges over "
            "all rows. The F2P test_distinct_on_aggregate asserts the actual "
            "distinct-valued results for all three kinds and would receive the "
            "all-rows values instead. Does NOT resolve."
        ),
        "rationale": (
            "rejected by the recorded-flag sub-clause of C2 at "
            "(avg, true, some \"f\"): the result must record distinct := true, "
            "the rival records false. This is the read-back-fidelity attack the "
            "nagini file calls load-bearing, and it is orthogonal to every "
            "policy and guard rival above — all of those change WHETHER the "
            "construction succeeds, this one changes WHAT it records. If it "
            "verifies => SPEC-TOO-WEAK (the request could be dropped silently)."
        ),
    },
    {
        "id": "weak-record-negate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_RECORD_NEGATE),
        "witness": _witness("count", "false", "none"),
        "refinement": (
            "ports nagini weak-construct-negate: record the NEGATION of the "
            "request. Its faithful patch stores the inverted flag, so a distinct "
            "request produces an all-rows aggregate and — the half this witness "
            "probes — an ORDINARY request silently produces a distinct-valued "
            "one. Both directions corrupt results while raising nothing: the F2P "
            "test_distinct_on_aggregate gets all-rows values, and graded tests "
            "that aggregate without any distinct request (test_count's plain "
            "count of 6, among many) get distinct-valued results instead. Does "
            "NOT resolve."
        ),
        "rationale": (
            "rejected by the recorded-flag sub-clause of C2 at "
            "(count, false, none): the result must record distinct := false, the "
            "rival records true. Deliberately witnessed on the NO-request side "
            "rather than at (avg, true, ...) where weak-record-const-false "
            "already probes: a negation is wrong in both directions, and pinning "
            "it only where the const-false rival also fails would leave the "
            "claim that C2 constrains the flag at `distinct = false` "
            "undemonstrated. If it verifies => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-drop-filter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_FILTER),
        "witness": _witness("avg", "false", '(some "r")'),
        "refinement": (
            "NO nagini counterpart — the nagini carrier modeled no filter "
            "payload, so this whole C2 sub-clause is new attack surface on this "
            "backend. The rival drops the filter store, leaving the recorded "
            "filter absent. Its faithful patch omits the field assignment that "
            "carries the row filter onto the constructed aggregate, so a "
            "row-filtered aggregate silently loses its filter and ranges over "
            "every row. Stated rather than over-claimed: the graded set for this "
            "instance is drawn entirely from one suite that never passes a "
            "filter (the suite that does, FilteredAggregateTests, is in neither "
            "graded list), so this rival's break is against the modeled relation "
            "and the real construction's behaviour, not a graded assertion. "
            "Shipped because the filter is one of the three things C2 requires "
            "recorded unchanged, and leaving it unattacked would mean a rival "
            "that mishandled only the filter would verify."
        ),
        "rationale": (
            "rejected by the recorded-filter sub-clause of C2 at "
            "(avg, false, some \"r\"): the result must record "
            "filter := some \"r\", the rival records none. This is the only "
            "rival that varies the THIRD binder's value in its witness — every "
            "other reject witness leaves the filter at whichever value it was "
            "handed and would behave identically if the filter were ignored "
            "entirely, so without this case the `filter` binder is one no rival "
            "was built to abuse. If it verifies => SPEC-TOO-WEAK on the filter."
        ),
    },
    {
        "id": "weak-record-fault-at-count",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_RECORD_FAULT_AT_COUNT),
        "witness": _witness("count", "true", '(some "r")'),
        "refinement": (
            "NO nagini counterpart; added during audit. The rival records the "
            "requested flag correctly for six of the seven kinds and drops it "
            "for exactly one — the counting kind. Its faithful patch is the "
            "narrowest possible version of the record-fidelity fault: a "
            "construction that carries the distinct request onto the aggregate "
            "except on one code path, so a distinct counting request builds "
            "successfully and silently ranges over all rows. The counting "
            "subtest of the F2P test_distinct_on_aggregate asserts the "
            "distinct-valued count and would receive the all-rows count "
            "instead, and the graded test_count_distinct_expression asserts a "
            "distinct count too. Does NOT resolve."
        ),
        "rationale": (
            "rejected by the recorded-flag sub-clause of C2 at "
            "(count, true, some \"r\"). Its purpose is coverage the rest of the "
            "record-fidelity lane cannot give: weak-record-const-false and "
            "weak-record-negate are both UNIFORM in `kind`, so each is refuted "
            "by a witness at whichever single kind it is sited at, and neither "
            "demonstrates that C2 pins the recorded flag kind-by-kind. A rival "
            "faithful at six kinds and faulty at one can only be caught by a "
            "witness sited at that kind, so this case is what shows the "
            "recorded-flag clause is quantified over the `kind` binder rather "
            "than spot-checked at one point of it. If it verifies => "
            "SPEC-TOO-WEAK on the recorded flag away from the witnessed kind."
        ),
    },
    {
        "id": "weak-record-fixed-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_RECORD_FIXED_KIND),
        "witness": _witness("min", "false", "none"),
        "refinement": (
            "NO nagini counterpart — the nagini carrier had no recorded kind "
            "either. The rival records a FIXED kind instead of the requested "
            "one, so the constructed aggregate misreports which computation it "
            "is. Its faithful patch is a construction that hard-codes the "
            "identity of the thing it builds; every graded test that constructs "
            "a non-averaging aggregate and checks its result would compute the "
            "wrong function. Does NOT resolve. It is the third of C2's three "
            "record-fidelity sub-clauses and the last one that would otherwise "
            "be undefended: the frozen impl threads `kind` into the result, and "
            "nothing else in this battery checks that it arrives."
        ),
        "rationale": (
            "rejected by the recorded-kind sub-clause of C2 at "
            "(min, false, none): the result must record kind := min, the rival "
            "records the averaging kind. Note the rival is deliberately built to "
            "be correct wherever the substituted kind coincides with the "
            "requested one, so it agrees with gold on the entire averaging "
            "sub-domain — this witness sits outside it, at a kind whose policy "
            "also forbids distinct, which no other record-fidelity witness "
            "touches. If it verifies => SPEC-TOO-WEAK on the recorded kind."
        ),
    },
]

# ===========================================================================
# AXIOM TESTS — none. meta.json records `axioms == []` and
# `deep_model_references == []`: there is no `opaque` callee on this path, the
# per-kind policy lookup and the field stores being modeled with concrete
# operations. Nothing is assumed, so there is no axiom-soundness or
# axiom-containment obligation for this lane to execute, and the axiom lane is
# G-AX's job in any case.
# ===========================================================================
AXIOM_TESTS = []
