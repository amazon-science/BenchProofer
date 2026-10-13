"""properties.py — G-PBT falsification battery for django__django-16429 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` / ``-- impl-end``
— and, for a case that legitimately re-proves or adds a ground instance, inside
``-- proof-start`` / ``-- proof-end`` — is changed, so ``markers.same_spec`` holds
and the ``theorem correct_<name>`` STATEMENT stays byte-identical).
``expect="verify"`` passes iff (in scope AND the file elaborates with the
obligation closed); ``expect="reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

This is a PORT of the nagini sibling's battery, re-expressed against this
backend's carrier. The nagini surface contracts a routine that assembles a
reference instant and then hands it to a deep datetime-subtraction reference; the
lean bundle models only the purely-functional core — the field-by-field assembly
of that reference instant — as one total function ``implementation_anchor`` with
one obligation ``correct_anchor``. So the nagini cases attached to the subtraction
call or to fractional-permission framing have no counterpart here (see below); the
cases attached to the assembled fields port directly.

DEFENDED SURFACE (one total function, one obligation):

  ``anchor (d : Instant) (years months : Int) : Instant`` builds the reference
  instant that lies ``years`` years and ``months`` months after ``d``. The
  postcondition pins EVERY output component to its input (frame discipline —
  referential transparency means an unpinned component is the analogue of the
  nagini full-permission hole):

    * ``result.year``  — ``d.year`` advanced by ``years`` (+1 when the month rolls
      past December);
    * ``result.month`` — ``d.month + months`` (−12 on roll);
    * ``result.day``   — ``d.day`` clamped down to ``monthLength result.month`` (so
      a 31st never lands in a shorter month);
    * ``result.hour`` / ``result.minute`` / ``result.second`` — copied from ``d``;
    * ``result.offset`` — copied from ``d``, so the reference carries the SAME
      timezone designation as the starting instant and is comparable with the
      instants it is measured against.

  The load-bearing clause for the underlying defect is ``result.offset =
  d.offset``: a naive reference against an aware peer is the crash the fix
  removes. The remaining clauses are the frame pins that make ``verify ⟹
  resolve`` (a reference at the wrong calendar position, wrong clock, or unclamped
  day renders the wrong span or violates a P2P edge test).

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION (nagini ``frame-mut-write-d-clock`` /
    ``frame-mut-write-d-tz``) — the PERMISSION MECHANIC is vacuous here, but the
    class's OBSERVABLE CONTENT is expressible and is now attacked. The nagini
    sibling holds every input field at fractional (read-only) permission, so a
    rival that WRITES the source to satisfy a clause is rejected for insufficient
    permission. Lean is referentially transparent, so there is no half-permission
    to violate and no aliasing to exploit, and no rival can be rejected FOR a
    permission error. What survives translation is the question the permission
    rule was protecting: does the answer come from the ACTUAL input, or from a
    doctored stand-in? That is expressible — shadow ``d`` with a corrupted copy
    (``let d := { d with offset := some 0 }``) and answer from the copy — and it is
    refutable at a concrete aware source. Ported as ``weak-rebind-source-offset``.
    (An earlier revision of this battery recorded the whole class as having "NO
    expressible instance"; that conflated the mechanic with the content. The audit
    landed the rival: rival exit 0, gold exit 1 with ``decide`` reporting the
    negation ``is false``.)

  * PARTIAL-DOMAIN: naive reference (nagini ``partial-naive-pivot``) — APPLIES and
    is the load-bearing rival. Building the reference with ``offset := none`` drops
    the source's timezone designation. Correct only when the source is naive;
    violates ``result.offset = d.offset`` on every aware source — the F2P
    sub-domain. Ported as ``weak-naive-offset``.

  * PARTIAL-DOMAIN: un-advanced reference (nagini ``partial-unadvanced-pivot``) —
    APPLIES. Assembling the reference at the SOURCE calendar position instead of
    the advanced one carries the designation correctly but pins the wrong span.
    Ported as ``weak-unadvanced-anchor``.

  * PARTIAL-DOMAIN: zeroed clock (nagini ``partial-zeroed-clock``) — APPLIES.
    Dropping the copied clock fields is correct only on the midnight sub-domain.
    Ported as ``weak-zeroed-clock``.

  * CLOCK sub-clause isolation — added by audit, no nagini counterpart. The nagini
    ``partial-zeroed-clock`` breaks the three clock fields as a block; on this
    carrier each is a separate spec clause, so ``weak-zeroed-second-only`` attacks
    ``result.second = d.second`` alone.

  * DAY-CLAMP drop — a modeled-surface clause with no separate nagini case (the
    nagini model supplied the clamped day as an input rather than computing it).
    This bundle computes ``result.day = min (monthLength result.month) d.day``
    inside the modeled function, so that clause needs its own attacker for clause
    coverage. Ported-in as ``weak-drop-day-clamp``.

  * SOUNDNESS POSITIVES (nagini ``posctl-drop-diff-call`` / ``posctl-local-reshape``)
    — APPLY. On lean the modeled function has no discardable side-effecting call to
    drop; the faithful analogue of "structurally different but CORRECT" is a
    functional (non-``Id.run``) reshape that must still verify, plus a local-binding
    reshape that keeps the ``Id.run`` form. Ported as ``pos-functional-shape`` and
    ``pos-local-reshape``. Each re-proves the byte-identical obligation for its new
    shape with no new lemma/axiom/assumption token.

  * ADMISSIBILITY (nagini ``admiss-disposition-witness``) — APPLIES in narrowed
    form. The frozen obligation carries only calendar-range preconditions (no
    disposition guard, since the subtraction is out of the modeled function), so
    the honest analogue discharges the spec predicate at BOTH an aware ground input
    and a naive ground input inside the proof region, alongside the frozen
    obligation. Ported as ``admiss-aware-and-naive-ground``.

  * DIVERGENCE / NON-TERMINATION — nagini carries no such case, and on lean the
    class is genuinely vacuous: ``implementation_anchor`` is a total Lean ``def``,
    so a diverging implementation cannot be written at all.

  * AXIOM lane — DROPPED. mapping.md records no consumed callee axiom and no
    deep-model reference (the assembly is pure structure + a constant table +
    integer ``min``/arithmetic), so there is no in-model axiom obligation; the
    nagini ``AXIOM_TESTS`` belong to G-AX, which this gate ignores. ``AXIOM_TESTS``
    is empty.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation, so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at a concrete ``decide``-able input; each was checked by hand
(``scripts/lean_verify.sh``) to HOLD of its rival and to FAIL on the frozen
solution, so it discriminates rather than asserting a tautology. No witness binds
a hypothesis (all inputs are concrete literals), so none needs the consistency
probe.

BINDER COVERAGE. The spec's input binders are ``d`` (the source instant),
``years`` and ``months``. Across the six reject witnesses:
  * ``d`` varies at every witness (distinct records; ``offset`` takes ``some 0``,
    ``some 5`` and ``some 330``, and ``d.second`` takes both 0 and 37);
  * ``years`` takes 1, 3, 0, 0, 0, 1;
  * ``months`` takes 2, 2, 5, 1, 1, 2;
so no binder is pinned to a single value across the lane. ``pts`` = 6 distinct
input points.

CLAUSE ISOLATION, not just clause mention. Every top-level postcondition clause
(year, month, day, hour, minute, second, offset) is violated by some rival AT ITS
OWN WITNESS POINT — which is the checkable property, and a stronger one than being
merely NAMED by a rationale. Two notes the audit had to fix:
  * ``weak-zeroed-clock`` originally stated its refutation at a source with
    ``second := 0``. Its rival zeroes the second, so at that point the ``second``
    clause was SATISFIED and the case attested only to hour/minute while its
    rationale named three clauses. The witness source now carries ``second := 37``.
  * No rival isolated the ``second`` clause on its own (every clock rival broke
    hour/minute/second as a block, so a spec pinning only hour and minute would
    reject them identically). ``weak-zeroed-second-only`` closes that: it is the
    sole clause it violates.
"""
from pathlib import Path

INSTANCE = "django__django-16429"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every replacement
# lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_anchor\n"
    "    (d : Instant) (years months : Int) : Instant := Id.run do\n"
    "  let mut anchorYear := d.year + years\n"
    "  let mut anchorMonth := d.month + months\n"
    "  if anchorMonth > 12 then\n"
    "    anchorMonth := anchorMonth - 12\n"
    "    anchorYear := anchorYear + 1\n"
    "  return {\n"
    "    year := anchorYear,\n"
    "    month := anchorMonth,\n"
    "    day := min (monthLength anchorMonth) d.day,\n"
    "    hour := d.hour,\n"
    "    minute := d.minute,\n"
    "    second := d.second,\n"
    "    offset := d.offset\n"
    "  }"
)

_PROOF_GOLD = (
    "  intro d years months _ _ _ _\n"
    "  unfold problem_spec_anchor implementation_anchor\n"
    "  simp only [Id.run, bind, pure]\n"
    "  by_cases h : d.month + months > 12\n"
    "  · simp only [h, if_true]; trivial\n"
    "  · simp only [h, if_false]; trivial"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_GOLD) == 1, "proof region drifted; update _PROOF_GOLD"


def _with_impl(new_impl):
    return _swap(_BASE, _IMPL_GOLD, new_impl)


# ---------------------------------------------------------------------------
# Rival impls (each edits ONLY the returned record inside the impl region; the
# spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# NAIVE OFFSET: drop the source's timezone designation (offset := none). Correct
# only on a naive source; violates result.offset = d.offset on every aware one.
_NAIVE_OFFSET = _IMPL_GOLD.replace(
    "    offset := d.offset\n  }", "    offset := none\n  }")

# UN-ADVANCED: assemble at the SOURCE calendar position instead of the advanced
# one. Carries the designation correctly but pins the wrong year/month.
_UNADVANCED = _IMPL_GOLD.replace(
    "    year := anchorYear,\n"
    "    month := anchorMonth,\n"
    "    day := min (monthLength anchorMonth) d.day,\n",
    "    year := d.year,\n"
    "    month := d.month,\n"
    "    day := min (monthLength d.month) d.day,\n")

# ZEROED CLOCK: drop the copied clock fields. Correct only at midnight.
_ZEROED_CLOCK = _IMPL_GOLD.replace(
    "    hour := d.hour,\n"
    "    minute := d.minute,\n"
    "    second := d.second,\n",
    "    hour := 0,\n"
    "    minute := 0,\n"
    "    second := 0,\n")

# DROP DAY-CLAMP: copy the source day unclamped, so a 31st survives into a
# shorter resulting month. Violates result.day = min (monthLength result.month) d.day.
_DROP_CLAMP = _IMPL_GOLD.replace(
    "    day := min (monthLength anchorMonth) d.day,\n",
    "    day := d.day,\n")

# ZEROED SECOND ONLY: drop just the copied `second`, keeping hour and minute. The
# zeroed-clock rival breaks hour/minute/second together, so it cannot attest that
# `result.second = d.second` is independently load-bearing — a spec that pinned
# only hour and minute would reject that rival just the same. This isolates the
# `second` clause: it is the ONLY clause this rival violates.
_ZEROED_SECOND = _IMPL_GOLD.replace(
    "    second := d.second,\n", "    second := 0,\n")

# SOURCE-REBIND (the frame-mutation class, re-expressed): satisfy the designation
# clause by first REBINDING the source to a corrupted copy, then reading the
# designation off that copy. Lean has no permission mechanic to violate, but the
# OBSERVABLE content of the nagini frame class — a rival that gets its answer from
# a doctored source rather than the real one — is expressible and wrong: it pins
# the designation to `some 0` regardless of the true source designation.
_REBIND_SOURCE = _IMPL_GOLD.replace(
    "  let mut anchorYear := d.year + years\n",
    "  let d := { d with offset := some 0 }\n"
    "  let mut anchorYear := d.year + years\n")

# POSITIVE (soundness): a structurally different but CORRECT impl — a direct
# functional expression (no Id.run / let mut), spelling the roll decision as the
# spec's own if/then/else. Same value on every input; the frozen script is tuned
# to the Id.run shape, so the obligation is re-proved (statement byte-identical).
_POS_FUNCTIONAL = (
    "def implementation_anchor\n"
    "    (d : Instant) (years months : Int) : Instant :=\n"
    "  let rawMonth := d.month + months\n"
    "  if rawMonth > 12 then\n"
    "    { year := d.year + years + 1,\n"
    "      month := rawMonth - 12,\n"
    "      day := min (monthLength (rawMonth - 12)) d.day,\n"
    "      hour := d.hour,\n"
    "      minute := d.minute,\n"
    "      second := d.second,\n"
    "      offset := d.offset }\n"
    "  else\n"
    "    { year := d.year + years,\n"
    "      month := rawMonth,\n"
    "      day := min (monthLength rawMonth) d.day,\n"
    "      hour := d.hour,\n"
    "      minute := d.minute,\n"
    "      second := d.second,\n"
    "      offset := d.offset }"
)
_POS_FUNCTIONAL_PROOF = (
    "  intro d years months _ _ _ _\n"
    "  unfold problem_spec_anchor implementation_anchor\n"
    "  by_cases h : d.month + months > 12\n"
    "  · simp only [h, if_true]; trivial\n"
    "  · simp only [h, if_false]; trivial"
)

# POSITIVE (soundness): local-binding reshape — bind the assembled fields into
# locals first, then construct from them. Keeps the Id.run form, so the frozen
# proof still closes it verbatim.
_POS_LOCAL = (
    "def implementation_anchor\n"
    "    (d : Instant) (years months : Int) : Instant := Id.run do\n"
    "  let mut anchorYear := d.year + years\n"
    "  let mut anchorMonth := d.month + months\n"
    "  if anchorMonth > 12 then\n"
    "    anchorMonth := anchorMonth - 12\n"
    "    anchorYear := anchorYear + 1\n"
    "  let dd := min (monthLength anchorMonth) d.day\n"
    "  let hh := d.hour\n"
    "  let mm := d.minute\n"
    "  let ss := d.second\n"
    "  let zz := d.offset\n"
    "  return {\n"
    "    year := anchorYear,\n"
    "    month := anchorMonth,\n"
    "    day := dd,\n"
    "    hour := hh,\n"
    "    minute := mm,\n"
    "    second := ss,\n"
    "    offset := zz\n"
    "  }"
)

# ADMISSIBILITY: discharge the spec predicate at an AWARE ground input and a NAIVE
# ground input inside the proof region, then close the frozen obligation verbatim.
_ADMISS_PROOF = (
    "  have _ground_aware : problem_spec_anchor\n"
    "      { year := 2007, month := 8, day := 14, hour := 13, minute := 46, second := 0, offset := some 330 } 10 0\n"
    "      (implementation_anchor\n"
    "        { year := 2007, month := 8, day := 14, hour := 13, minute := 46, second := 0, offset := some 330 } 10 0) := by\n"
    "    unfold problem_spec_anchor implementation_anchor\n"
    "    simp only [Id.run, bind, pure]\n"
    "    decide\n"
    "  have _ground_naive : problem_spec_anchor\n"
    "      { year := 2007, month := 8, day := 14, hour := 13, minute := 46, second := 0, offset := none } 10 0\n"
    "      (implementation_anchor\n"
    "        { year := 2007, month := 8, day := 14, hour := 13, minute := 46, second := 0, offset := none } 10 0) := by\n"
    "    unfold problem_spec_anchor implementation_anchor\n"
    "    simp only [Id.run, bind, pure]\n"
    "    decide\n"
    + _PROOF_GOLD
)


SPEC_TESTS = [

    # =====================================================================
    # SOUNDNESS POSITIVES — structurally different but CORRECT impls that MUST
    # verify. If a faithful correct impl of the modeled behavior cannot satisfy
    # the frozen obligation, the spec is SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_anchor` STATEMENT byte-identical and re-proves the new
    # shape with no new declaration/axiom/assumption token.
    # =====================================================================
    {
        "id": "pos-functional-shape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_with_impl(_POS_FUNCTIONAL), _PROOF_GOLD,
                        _POS_FUNCTIONAL_PROOF),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` and "
            "spells the roll decision as one functional `if rawMonth > 12 then … "
            "else …` term must satisfy every pinned clause (`result.year`, "
            "`result.month`, `result.day`, `result.hour`, `result.minute`, "
            "`result.second`, `result.offset`) — the two branches are exactly the "
            "spec's two `rolled`/not-`rolled` arms. If it could not verify, the "
            "spec would be SPEC-TOO-STRONG for an equivalent shape. Proof: the "
            "frozen `simp only [Id.run …]` is tuned to the `Id.run` form, so the "
            "obligation is re-proved by `by_cases` on the same roll condition; no "
            "new lemma, axiom, or assumption token."
        ),
    },
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_LOCAL),
        "rationale": (
            "behaviourally identical to the frozen impl — each assembled field is "
            "named into a local first, then the record is built from the locals — "
            "so every pinned clause maps to the same value. A faithful refinement "
            "MUST verify; if it failed the spec would reject an equivalent shape. "
            "The `Id.run` form is preserved, so the frozen tactic body closes it "
            "verbatim (no proof change, no new declaration)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at the normal,
    # F2P-shaped inputs, not only provable in the abstract. The frozen obligation
    # carries only calendar-range preconditions, so nagini's disposition-admission
    # probe narrows to: discharge the spec predicate at an AWARE ground input and
    # a NAIVE ground input inside the proof region, alongside the frozen
    # obligation. If either ground instance could not be discharged, the modeled
    # behavior would be unsatisfiable at exactly the inputs the F2P classes
    # exercise (the analogue of PRECOND-TOO-STRONG).
    # =====================================================================
    {
        "id": "admiss-aware-and-naive-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_GOLD, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at an aware ground input "
            "(`offset := some 330`, the make-aware analogue) AND at a naive ground "
            "input (`offset := none`, the default configuration) by `decide`, then "
            "the frozen obligation is closed verbatim. Verifies (else the spec is "
            "unsatisfiable at a normal input). Nothing is assumed: the theorem "
            "STATEMENT is byte-identical, both ground instances are `have`s inside "
            "the existing tactic body, and no new declaration/axiom/`sorry` is "
            "introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries (a) the refinement argument that its faithful
    # real patch would NOT resolve the F2P (so a verifying rival would be a true
    # verify-does-not-imply-resolve break, not an artifact), and (b) a refutation
    # witness pinning the violation at one concrete input, checked to hold of the
    # rival and fail on gold.
    # =====================================================================
    {
        # THE load-bearing rival: the pre-fix behavior. Reference assembled without
        # the source's timezone designation.
        "id": "weak-naive-offset",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_NAIVE_OFFSET),
        "refinement": (
            "this is the pre-fix construction: the reference instant is assembled "
            "with no timezone designation (`offset := none`) regardless of the "
            "source. For an aware source the reference is naive while its peer is "
            "aware, so the downstream comparison against that peer is undefined and "
            "raises — the crash the F2P aware class observes. Its faithful real "
            "patch IS the pre-fix code, which does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result.offset = d.offset`: at an aware source "
            "(`offset := some 0`) the spec demands the reference carry `some 0`, "
            "but the rival returns `none`. Refuted on the aware sub-domain — the "
            "exact sub-domain the fix repairs."
        ),
        "witness": (
            "-- Refuted on an aware source: the reference must carry the source's\n"
            "-- timezone designation (some 0), but the naive rival drops it to none.\n"
            "example : ¬ problem_spec_anchor\n"
            "    { year := 2007, month := 8, day := 14, hour := 13, minute := 46, second := 0, offset := some 0 } 1 2\n"
            "    (implementation_anchor\n"
            "      { year := 2007, month := 8, day := 14, hour := 13, minute := 46, second := 0, offset := some 0 } 1 2) := by\n"
            "  unfold problem_spec_anchor implementation_anchor\n"
            "  simp only [Id.run, bind, pure]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-unadvanced-anchor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_UNADVANCED),
        "refinement": (
            "assembling the reference at the SOURCE calendar position "
            "(`result.year = d.year`, `result.month = d.month`) instead of the "
            "advanced one measures the WHOLE span rather than the leftover span "
            "beyond the advanced years/months. The rendered count would be wrong — "
            "e.g. the thousand-years-ago F2P expects the full-year count, whose "
            "leftover beyond the advanced years is ~0 — so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clauses `result.year = (if rolled then d.year + years "
            "+ 1 else d.year + years)` and `result.month = …`: with `years = 3`, "
            "`months = 2` the spec demands the advanced year, but the rival pins "
            "`result.year = d.year`. Varies `years` (3) and `d` off the other "
            "witnesses."
        ),
        "witness": (
            "-- Refuted where years/months are non-zero: the reference must be at\n"
            "-- the advanced calendar position, not the source position.\n"
            "example : ¬ problem_spec_anchor\n"
            "    { year := 2020, month := 8, day := 14, hour := 13, minute := 46, second := 0, offset := some 5 } 3 2\n"
            "    (implementation_anchor\n"
            "      { year := 2020, month := 8, day := 14, hour := 13, minute := 46, second := 0, offset := some 5 } 3 2) := by\n"
            "  unfold problem_spec_anchor implementation_anchor\n"
            "  simp only [Id.run, bind, pure]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-zeroed-clock",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_ZEROED_CLOCK),
        "refinement": (
            "zeroing the copied clock fields (`result.hour`/`result.minute`/"
            "`result.second` set to 0 instead of `d.hour`/`d.minute`/`d.second`) "
            "shifts the leftover span by up to ~24h for any non-midnight source. "
            "The sub-day components the depth/units F2P tests observe would differ, "
            "so it does NOT resolve; correct only on the midnight sub-domain."
        ),
        "rationale": (
            "REJECT from the clauses `result.hour = d.hour`, `result.minute = "
            "d.minute`, `result.second = d.second`: at `d.hour = 13`, "
            "`d.minute = 46`, `d.second = 37` the spec demands each of those "
            "values, but the rival returns 0 for all three. The witness source "
            "carries a NON-ZERO second precisely so the `result.second` clause is "
            "independently violated at the refuted point: with `d.second = 0` the "
            "rival's `second := 0` coincides with the spec's demand, and the case "
            "would attest only to the hour/minute clauses while its rationale "
            "named three. Varies `months` (5)."
        ),
        "witness": (
            "-- Refuted on a non-midnight source whose second is also non-zero, so\n"
            "-- that ALL THREE clock clauses (hour, minute, second) are violated at\n"
            "-- this one point rather than only hour and minute.\n"
            "example : ¬ problem_spec_anchor\n"
            "    { year := 2007, month := 8, day := 14, hour := 13, minute := 46, second := 37, offset := some 0 } 0 5\n"
            "    (implementation_anchor\n"
            "      { year := 2007, month := 8, day := 14, hour := 13, minute := 46, second := 37, offset := some 0 } 0 5) := by\n"
            "  unfold problem_spec_anchor implementation_anchor\n"
            "  simp only [Id.run, bind, pure]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-drop-day-clamp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_DROP_CLAMP),
        "refinement": (
            "copying the source day unclamped (`result.day = d.day` instead of "
            "`min (monthLength result.month) d.day`) lets a 31st survive into a "
            "shorter resulting month, which the pre-existing month-edge and "
            "leap-year P2P tests forbid. Breaking a PASS_TO_PASS test means the "
            "harness reports NOT resolved, so a faithful patch dropping the clamp "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result.day = min (monthLength result.month) "
            "d.day`: advancing Jan 31 by one month lands in a 28-day month, so the "
            "spec demands the day clamp `min (monthLength result.month) d.day = "
            "28`, but the rival returns the unclamped `31`. Varies `months` (1) and "
            "attacks the day clause no other rival touches."
        ),
        "witness": (
            "-- Refuted where the source day exceeds the resulting month's length:\n"
            "-- the day must be clamped down, but the rival copies it unclamped.\n"
            "example : ¬ problem_spec_anchor\n"
            "    { year := 2020, month := 1, day := 31, hour := 13, minute := 46, second := 0, offset := some 0 } 0 1\n"
            "    (implementation_anchor\n"
            "      { year := 2020, month := 1, day := 31, hour := 13, minute := 46, second := 0, offset := some 0 } 0 1) := by\n"
            "  unfold problem_spec_anchor implementation_anchor\n"
            "  simp only [Id.run, bind, pure]\n"
            "  decide\n"
        ),
    },
    {
        # ADDED BY AUDIT. Clause isolation: every other rival that touches the
        # clock breaks hour/minute/second as a block, so none of them attests that
        # `result.second = d.second` carries its own weight. This rival violates
        # that clause and NOTHING else.
        "id": "weak-zeroed-second-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_ZEROED_SECOND),
        "refinement": (
            "dropping only the copied `second` (`result.second := 0`, hour and "
            "minute still copied) shifts the reference by up to 59s for any source "
            "whose second is non-zero. The rendered residual seconds the depth/units "
            "tests observe would differ at second-granularity, so it does NOT "
            "resolve; correct only on the whole-minute sub-domain."
        ),
        "rationale": (
            "REJECT from the clause `result.second = d.second` ALONE: at "
            "`d.second = 37` the spec demands 37 and the rival returns 0, while "
            "every other clause (year, month, day, hour, minute, offset) is "
            "satisfied. This is the only case in the lane whose refutation isolates "
            "a single clock clause, so it is what attributes independent strength to "
            "`result.second = d.second` rather than to the clock block as a whole. "
            "Varies `months` (1) and `d.second` (37) off the other witnesses."
        ),
        "witness": (
            "-- Refuted at a source with a non-zero second: `second` is the sole\n"
            "-- clause violated here, so this pins that clause specifically.\n"
            "example : ¬ problem_spec_anchor\n"
            "    { year := 2007, month := 8, day := 14, hour := 13, minute := 46, second := 37, offset := some 0 } 0 1\n"
            "    (implementation_anchor\n"
            "      { year := 2007, month := 8, day := 14, hour := 13, minute := 46, second := 37, offset := some 0 } 0 1) := by\n"
            "  unfold problem_spec_anchor implementation_anchor\n"
            "  simp only [Id.run, bind, pure]\n"
            "  decide\n"
        ),
    },
    {
        # ADDED BY AUDIT. The port recorded the nagini FRAME/PERMISSION class as
        # having "NO expressible instance" on this carrier. That is right about the
        # permission MECHANIC and wrong about the class's observable content: a
        # rival that answers from a doctored copy of the source instead of the real
        # source is expressible here and is refutable at a concrete input. Landed
        # rather than left as an omission.
        "id": "weak-rebind-source-offset",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_REBIND_SOURCE),
        "refinement": (
            "rebinding the source to a copy whose designation is forced to `some 0` "
            "and then carrying THAT designation makes the reference agree with its "
            "peer only when the true source already sat at that offset. For a source "
            "at any other designation the reference is built at the wrong one, so the "
            "measured span is displaced by the offset difference and a naive source "
            "is silently made aware — the comparison the F2P aware class exercises is "
            "against the wrong designation. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result.offset = d.offset`: at a source carrying "
            "`some 330` the spec demands `some 330`, but the rival answers from its "
            "own doctored copy and returns `some 0`. This is the frame class's real "
            "content on a referentially-transparent carrier — the answer must come "
            "from the actual input, not from a locally substituted stand-in. Distinct "
            "from `weak-naive-offset`, which drops the designation entirely rather "
            "than replacing it with a wrong one; `some 0` vs `none` are different "
            "failures and this witness varies `d.offset` (some 330) off the lane."
        ),
        "witness": (
            "-- Refuted at an aware source NOT at offset 0: the designation must be\n"
            "-- the real source's (some 330), not the rebound stand-in's (some 0).\n"
            "example : ¬ problem_spec_anchor\n"
            "    { year := 2007, month := 8, day := 14, hour := 13, minute := 46, second := 37, offset := some 330 } 1 2\n"
            "    (implementation_anchor\n"
            "      { year := 2007, month := 8, day := 14, hour := 13, minute := 46, second := 37, offset := some 330 } 1 2) := by\n"
            "  unfold problem_spec_anchor implementation_anchor\n"
            "  simp only [Id.run, bind, pure]\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references (mapping.md): the assembly is
# pure structure + a constant table + integer min/arithmetic, so there is no
# in-model axiom obligation for the PBT axiom lane. The nagini AXIOM_TESTS belong
# to G-AX, which this gate ignores.
AXIOM_TESTS = []
