"""properties.py — G-PBT falsification battery for django__django-16255 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models a single read-only reduction over a per-entry stamp list held at half
permission (``latest_stamp(stamps) -> Optional[int]``): every nagini rival
attacks that ONE reduction. This Lean bundle models a WIDER purely-functional
core — a total decision over two configuration booleans, the list of per-item
timestamps, and a single constant timestamp, returning an optional timestamp.
The nagini reduction is exactly this bundle's per-item branch; the nagini rivals
carry over as attacks on that branch, and the two extra top-level clauses this
carrier exposes (the no-source clause and the single-constant clause) get their
own rivals so every clause and every binder is exercised. The per-case mapping
(port vs principled omission) is in the module ``assessment`` below.

DEFENDED SURFACE (one modeled behavior). The report is TOTAL — it always
produces an answer — and its optional-timestamp value is pinned to a single
grounded case split over the inputs. The independent top-level clauses, selected
by the inputs:

  * NO-SOURCE clause: when no timestamp source is defined, the report is "no
    latest timestamp";
  * PER-ITEM clause (the CHANGED one): when the timestamp is computed per item,
    the report is the greatest of the per-item timestamps — and "no latest
    timestamp" exactly when the collection is EMPTY (no greatest element),
    rather than a failure;
  * CONSTANT clause: otherwise the report is exactly the single constant
    timestamp (which may itself be absent).

The BEHAVIOURAL DISCRIMINATOR (the fix): the per-item branch over an EMPTY
collection reports "no latest timestamp" (a clean absent marker) instead of
failing. The pre-fix behavior fails on that sub-domain; the ``empty-break`` rival
below IS that pre-fix behavior. The per-item branch's value obligations —
membership (the report is one of the per-item timestamps) and dominance (it is
the greatest) — are attacked by the remaining reduction rivals.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini frame-mutation rival (write
    the running max back into the read-only stamp list) has no expressible
    instance here; no substitute is fabricated. (nagini case ``frame-write``.)
    DEMONSTRATED, not asserted: the nearest expressible analogue — an impl that
    builds a "normalised" copy of the per-item timestamps (each entry clamped up
    to the running greatest) alongside the correct report — was constructed and
    VERIFIES against the frozen obligation, because the copy is unobservable in
    the returned value. That is the carrier collapsing the distinction: here the
    write is not a rejectable defect but a no-op, so there is no wrong impl to
    land, rather than a witness that could not be built.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to a term built only from the inputs (the ``max?`` of the
    supplied list, the constant, or the absent marker). There is no opaque
    answer key an implementation could echo — the carrier is fully transparent,
    with no ``opaque`` callee or consumed ``axiom``. In its place the battery
    carries an honest cheapest-implementation POSITIVE CONTROL that must verify
    (nagini's ``pos-reshape``).

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: reporting a concrete stamp for an empty
    collection; skipping the first per-item stamp; a synthesised dominator that
    is not a member; the first member instead of the greatest; and the two
    extra clauses (no-source, constant) that this carrier models but the
    narrower nagini reduction never had.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``cases … <;> rfl`` is tuned to the
frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at one concrete input and refuting it. The carrier is fully
concrete (finite booleans, ``List Int`` literals, ``Option Int`` — no opaque
term), so every witness discharges by ``decide`` after unfolding, with no need
to condition on the carrier and hence NO witness hypotheses to be mutually
consistent. Each witness was checked with real builds to HOLD of its rival and
to FAIL on the frozen solution, so it discriminates rather than asserting a
tautology.

BINDER / POINT SPREAD. The reject witnesses move every input binder of the spec
rather than fixing them at one convenient point: ``hasM`` takes both settings
(``false`` at the no-source rival); ``callM`` takes both settings (``false`` at
the constant/no-source rivals); ``vals`` ranges over empty, singleton, and
length-≥2 lists whose first element is / is not the maximum; and ``constM`` takes
both ``none`` and ``some`` AS THE REFUTATION POINT (not merely as a value carried
along at an input where the report never reads it). No two rivals share a
refutation point — the seven reject witnesses probe seven distinct inputs.

POSITIVE-CONTROL DEPTH. Two soundness controls, deliberately at different
depths, because a reshape that the FROZEN tactic body still closes cannot have
re-proven anything: ``pos-single-return`` keeps the greatest-of-a-list term
verbatim and only moves the branch cascade, so it exercises the case split;
``pos-foldl-max`` recomputes that term by an explicit accumulator fold, is NOT
definitionally equal to it, and therefore carries its own inductive proof — the
control that actually re-establishes the per-item VALUE clause (the clause the
modeled change lives in, and the one every reject rival attacks) for a new impl
shape.

AXIOM lane: EMPTY here. The bundle consumes no ``axiom`` and declares no
``opaque`` (the greatest-of-a-list operation is the Mathlib builtin ``List.max?``
and a timestamp is a comparable ``Int``). The nagini ``AXIOM_TESTS`` were also
empty; dropped.
"""
from pathlib import Path

INSTANCE = "django__django-16255"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the admissibility
# case that re-proves, the proof region) so same_spec stays byte-identical.

# The whole no-source + per-item head of the impl (used by the positive
# reshape, which rewrites the whole branch cascade into one grounded `let`).
_I_CASCADE = (
    "  if hasM = false then\n"
    "    return some none\n"
    "  if callM then\n"
    "    -- greatest of the per-item timestamps; an empty collection has no greatest\n"
    "    -- element, so the report is \"no latest timestamp\".\n"
    "    return some vals.max?\n"
    "  else\n"
    "    return some constM"
)

# The per-item (CHANGED) branch of the impl — the nagini reduction's counterpart.
_I_PERITEM = (
    "  if callM then\n"
    "    -- greatest of the per-item timestamps; an empty collection has no greatest\n"
    "    -- element, so the report is \"no latest timestamp\".\n"
    "    return some vals.max?"
)

# The no-source branch of the impl.
_I_NOSOURCE = "  if hasM = false then\n    return some none"

# The constant branch of the impl.
_I_CONSTANT = "  else\n    return some constM"

# The frozen proof body (proof region).
_P_FROZEN = (
    "  intro hasM callM vals constM\n"
    "  unfold problem_spec_latestLastmod implementation_latestLastmod\n"
    "  cases hasM <;> cases callM <;> rfl"
)

# An INDEPENDENT re-derivation of the greatest-of-a-list operation: an explicit
# left fold over the per-item timestamps carrying the running greatest in an
# `Option Int` accumulator (absent until the first item is seen). Used by the
# `pos-foldl-max` soundness control. This is NOT definitionally equal to
# `vals.max?` — `rfl` does not close it and the frozen tactic body fails on it —
# so the case needs, and carries, a real inductive proof.
_I_FOLDL = (
    "  if hasM = false then\n"
    "    return some none\n"
    "  if callM then\n"
    "    return some (vals.foldl (fun acc v =>\n"
    "      match acc with\n"
    "      | none   => some v\n"
    "      | some x => some (max x v)) none)\n"
    "  else\n"
    "    return some constM"
)

# The matching proof: the fold's accumulator, once primed with the head, agrees
# with `List.foldl max` — which is what `List.max?` is on a non-empty list.
_P_FOLDL = (
    "  intro hasM callM vals constM\n"
    "  unfold problem_spec_latestLastmod implementation_latestLastmod\n"
    "  have key : ∀ (l : List Int) (a : Int),\n"
    "      l.foldl (fun acc v => match acc with\n"
    "                            | none => some v\n"
    "                            | some x => some (max x v)) (some a)\n"
    "        = some (l.foldl max a) := by\n"
    "    intro l\n"
    "    induction l with\n"
    "    | nil => intro a; rfl\n"
    "    | cons b t ih => intro a; simpa using ih (max a b)\n"
    "  cases hasM <;> cases callM <;> simp_all [List.max?] <;>\n"
    "    cases vals with\n"
    "    | nil => rfl\n"
    "    | cons b t => simpa using key t b"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # implementation that MUST verify. If a faithful correct implementation of
    # this shape cannot satisfy the frozen obligation the spec is
    # SPEC-TOO-STRONG. Keeps the theorem statement byte-identical; the reshape
    # collapses the branch cascade into a single grounded `let` + one return,
    # matching the spec's own case-split shape, so the frozen `cases … <;> rfl`
    # still closes (no helper lemma, no axiom, no assumption token).
    #
    # Ports nagini's `pos-reshape` (a local-variable reshape of the reduction
    # keeping every value claim). Here the analogous reshape hoists the whole
    # decision into one `Option Int` local and returns `some` of it.
    # =====================================================================
    {
        "id": "pos-single-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _I_CASCADE,
            "  let inner : Option Int :=\n"
            "    if hasM = false then none\n"
            "    else if callM then vals.max?\n"
            "    else constM\n"
            "  return some inner",
        ),
        "rationale": "the branch cascade is reshaped into a single grounded "
                     "`let inner := if … else if … else …` followed by one "
                     "`return some inner`. The assembled value is identical on "
                     "every input, so `result = some (if … )` still holds. Must "
                     "verify, else the modeled decision is SPEC-TOO-STRONG. "
                     "Proof: the frozen tactic body is retained (the local "
                     "zeta-reduces and `cases hasM <;> cases callM <;> rfl` "
                     "closes). Ports nagini's `pos-reshape` local-variable "
                     "positive to this wider carrier.",
    },

    # =====================================================================
    # POSITIVE CONTROL #2 (soundness) — a genuinely INDEPENDENT re-derivation of
    # the greatest-of-a-list operation, not a syntactic reshuffle of it.
    #
    # AUDIT NOTE. `pos-single-return` above keeps `vals.max?` verbatim and only
    # moves the branch cascade around, so it is closed by the FROZEN tactic body
    # unchanged — which means it exercises the spec's case split but never its
    # per-item VALUE claim, the one clause the modeled change lives in. The
    # reject rivals all attack that clause, so nothing in the battery was
    # confirming a faithful re-implementation OF it can be proven. This case
    # closes that: the per-item branch is recomputed by an explicit left fold
    # with an `Option Int` running accumulator. It is not definitionally equal to
    # `vals.max?` (`rfl` fails; the frozen script does not close it), so it
    # carries its own inductive proof — a real re-proof of the value obligation
    # for a new impl shape rather than a restatement of it. If this cannot be
    # proven the spec pins an incidental spelling of the operation rather than
    # its meaning, i.e. SPEC-TOO-STRONG on the changed clause.
    # =====================================================================
    {
        "id": "pos-foldl-max",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _I_CASCADE, _I_FOLDL).replace(
            _P_FROZEN, _P_FOLDL, 1),
        "rationale": "the per-item branch recomputes the greatest timestamp by "
                     "an explicit left fold carrying the running greatest in an "
                     "`Option Int` accumulator (absent until the first item is "
                     "seen) instead of naming the builtin. This is a DIFFERENT "
                     "term, not a reshuffle: the frozen `cases … <;> rfl` does "
                     "NOT close it, so the case supplies a real inductive proof "
                     "(the primed accumulator agrees with `List.foldl max`, "
                     "which is the builtin on a non-empty list). Must verify, "
                     "else the spec pins one spelling of the greatest-of-a-list "
                     "operation rather than its meaning — SPEC-TOO-STRONG on "
                     "exactly the clause the modeled change lives in. Statement "
                     "byte-identical; no axiom, no assumption token, no new "
                     "declaration (the helper is a `have` inside the tactic "
                     "body).",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at exactly the F2P input rather than only in the
    # abstract. The frozen theorem carries NO precondition hypothesis (the
    # modeled behavior is total, so `∀` is unguarded), so the nagini
    # precondition-admission probe (`admiss-nonempty`) has no binder to attack;
    # the honest analogue is to discharge the spec predicate by `rfl` at the
    # exact F2P scenario — a per-item source over an EMPTY collection — inside
    # the tactic body, then close the frozen obligation verbatim. Nothing is
    # assumed: no new declaration, the statement is byte-identical.
    # =====================================================================
    {
        "id": "admiss-empty-peritem",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_FROZEN,
            "  have _ground : problem_spec_latestLastmod true true [] none\n"
            "      (implementation_latestLastmod true true [] none) := rfl\n"
            + _P_FROZEN,
        ),
        "rationale": "the obligation is discharged at the exact F2P input — a "
                     "per-item timestamp source (hasM, callM both true) over an "
                     "EMPTY collection, whose correct report is the absent "
                     "marker — by `rfl`, then the frozen obligation is closed "
                     "verbatim. Verifies (else the modeled behavior is "
                     "unsatisfiable at exactly the input the F2P exercises — the "
                     "analogue of PRECOND-TOO-STRONG). Nothing is assumed: the "
                     "ground instance is a `have` inside the existing tactic "
                     "body and the theorem statement is byte-identical. Ports "
                     "nagini's admissibility probe to the F2P-shaped input.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete input (HOLDS of the rival, FAILS on gold — both checked with real
    # builds).
    # =====================================================================

    # ---- the fix itself: report a concrete stamp on an empty collection ----
    {
        "id": "weak-empty-break",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_PERITEM,
            "  if callM then\n"
            "    return some (some (vals.max?.getD 0))",
        ),
        "refinement": "this IS the pre-fix behavior on the per-item branch: it "
                      "never falls back to the absent marker, so an EMPTY "
                      "collection reports a concrete timestamp (the value "
                      "abstraction of the real pre-fix path, which fails outright "
                      "on the empty per-item reduction). The F2P scenario asserts "
                      "that a per-item source over an empty collection reports "
                      "'no latest timestamp' (a clean absent marker), not a "
                      "concrete/failing value — so the faithful real patch would "
                      "NOT resolve; it is the very defect the fix removes.",
        "rationale": "REJECT from the per-item clause on the EMPTY sub-domain: "
                     "the spec pins the report to `vals.max?` which is the absent "
                     "marker for the empty list, while the rival reports a "
                     "present concrete stamp, so `result` differs. Partial-domain "
                     "(agrees with gold on every non-empty collection). Moves "
                     "vals to the empty list.",
        "witness": (
            "example : ¬ problem_spec_latestLastmod true true [] none\n"
            "    (implementation_latestLastmod true true [] none) := by\n"
            "  unfold problem_spec_latestLastmod implementation_latestLastmod\n"
            "  decide\n"
        ),
    },

    # ---- skip the first per-item stamp (nagini `w2-skip-first`) ----
    {
        "id": "weak-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_PERITEM,
            "  if callM then\n"
            "    return some vals.tail.max?",
        ),
        "refinement": "a faithful real patch reducing over `vals[1:]` (an "
                      "off-by-one slice of the per-item comprehension) reports an "
                      "older timestamp whenever the latest entry is the first "
                      "one — or the absent marker for a singleton collection. The "
                      "P2P behavior 'the report is the most recent per-item "
                      "timestamp' asserts the EXACT greatest value and would "
                      "FAIL; it would NOT resolve.",
        "rationale": "REJECT from the per-item clause's dominance/membership: "
                     "with the greatest stamp at index 0 the spec reports it and "
                     "the rival drops it, so `result` differs. Partial-domain "
                     "(first-element / singleton sub-domain). Moves vals to a "
                     "length-≥2 list whose HEAD is the maximum.",
        "witness": (
            "example : ¬ problem_spec_latestLastmod true true [5, 3] none\n"
            "    (implementation_latestLastmod true true [5, 3] none) := by\n"
            "  unfold problem_spec_latestLastmod implementation_latestLastmod\n"
            "  decide\n"
        ),
    },

    # ---- synthesised dominator that is not a member (nagini `w3`) ----
    {
        "id": "weak-nonmember-dominator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_PERITEM,
            "  if callM then\n"
            "    return some (vals.max?.map (· + 1))",
        ),
        "refinement": "a faithful real patch returning a timestamp strictly newer "
                      "than every per-item entry (e.g. the greatest plus one) "
                      "would report a value LATER than any real entry — the P2P "
                      "'the report is the most recent per-item timestamp' asserts "
                      "the exact real (member) value and would FAIL; it would NOT "
                      "resolve. (Still the absent marker on the empty collection, "
                      "so it is a value-only miss on the non-empty sub-domain.)",
        "rationale": "REJECT from the per-item clause's MEMBERSHIP: a "
                     "strictly-greater synthetic value dominates every stamp but "
                     "is not one of them, so `result` differs from `vals.max?`. "
                     "Moves vals to a singleton (isolating the value from any "
                     "index effect).",
        "witness": (
            "example : ¬ problem_spec_latestLastmod true true [5] none\n"
            "    (implementation_latestLastmod true true [5] none) := by\n"
            "  unfold problem_spec_latestLastmod implementation_latestLastmod\n"
            "  decide\n"
        ),
    },

    # ---- first member instead of the greatest (nagini `w4-first-member`) ----
    {
        "id": "weak-first-member",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_PERITEM,
            "  if callM then\n"
            "    return some vals.head?",
        ),
        "refinement": "a faithful real patch reporting the FIRST per-item "
                      "timestamp (a genuine member) instead of the greatest would "
                      "report an OLDER value than the collection's latest entry — "
                      "the P2P 'the report is the most recent per-item timestamp' "
                      "asserts the MAXIMUM and would FAIL; it would NOT resolve.",
        "rationale": "REJECT from the per-item clause's DOMINANCE: the first "
                     "collected stamp is a member but need not dominate a later, "
                     "newer entry, so `result` differs from `vals.max?`. "
                     "Partial-domain (agrees on empty, singletons, and "
                     "already-descending collections). Moves vals to a length-≥2 "
                     "list whose head is NOT the maximum.",
        "witness": (
            "example : ¬ problem_spec_latestLastmod true true [3, 5] none\n"
            "    (implementation_latestLastmod true true [3, 5] none) := by\n"
            "  unfold problem_spec_latestLastmod implementation_latestLastmod\n"
            "  decide\n"
        ),
    },

    # ---- the no-source clause (this carrier's extra clause; no nagini twin) --
    {
        "id": "weak-nosource-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_NOSOURCE,
            "  if hasM = false then\n    return some constM",
        ),
        "refinement": "a faithful real patch that, when no timestamp source is "
                      "defined, reported the constant attribute instead of 'no "
                      "latest timestamp' would emit a timestamp for a collection "
                      "that has no source at all — the P2P behavior 'no source ⇒ "
                      "no latest timestamp' (the Last-Modified header omitted) "
                      "asserts the absent marker and would FAIL; it would NOT "
                      "resolve.",
        "rationale": "REJECT from the NO-SOURCE clause: the spec pins the report "
                     "to the absent marker when hasM is false, while the rival "
                     "returns the constant, so at a no-source input with a "
                     "present constant `result` differs. Fully concrete, "
                     "decidable. The only rival moving the hasM binder to false, "
                     "so that clause is demonstrated live.",
        "witness": (
            "example : ¬ problem_spec_latestLastmod false false [] (some 7)\n"
            "    (implementation_latestLastmod false false [] (some 7)) := by\n"
            "  unfold problem_spec_latestLastmod implementation_latestLastmod\n"
            "  decide\n"
        ),
    },

    # ---- the constant clause (this carrier's extra clause; no nagini twin) ---
    {
        "id": "weak-constant-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_CONSTANT,
            "  else\n    return some none",
        ),
        "refinement": "a faithful real patch that, when the timestamp is a single "
                      "constant value (not per-item), reported 'no latest "
                      "timestamp' instead of that constant would drop the "
                      "collection's declared timestamp — the P2P behavior 'a "
                      "single constant lastmod is reported verbatim' asserts the "
                      "exact constant and would FAIL; it would NOT resolve.",
        "rationale": "REJECT from the CONSTANT clause: the spec pins the report "
                     "to the constant `constM` when a source is defined and it is "
                     "not per-item, while the rival returns the absent marker, so "
                     "at a present-constant input `result` differs. Fully "
                     "concrete, decidable. Moves callM to false with a present "
                     "constant — the sub-domain no reduction rival reaches.",
        "witness": (
            "example : ¬ problem_spec_latestLastmod true false [] (some 7)\n"
            "    (implementation_latestLastmod true false [] (some 7)) := by\n"
            "  unfold problem_spec_latestLastmod implementation_latestLastmod\n"
            "  decide\n"
        ),
    },

    # ---- the constant clause at an ABSENT constant -------------------------
    # AUDIT NOTE. Every rival above pins `constM` at `none` or at `some 7`, but
    # the two that read `constM` (`weak-nosource-wrong`, `weak-constant-wrong`)
    # both refute at `some 7` — so no witness in the battery discriminated at a
    # DEFINED-but-ABSENT constant, the sub-domain where the constant clause must
    # forward the absent marker rather than manufacture a value. A rival that
    # substitutes a concrete default for an absent constant therefore went
    # unattacked. This case adds that point.
    {
        "id": "weak-absent-constant-defaulted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_CONSTANT,
            "  else\n    return some (some (constM.getD 0))",
        ),
        "refinement": "a faithful real patch that, on the single-constant branch, "
                      "substituted a concrete fallback timestamp when the declared "
                      "constant is itself absent would emit a timestamp for a "
                      "collection that declares none — the P2P behavior 'a "
                      "collection whose constant timestamp is absent reports no "
                      "latest timestamp (the header is omitted)' asserts the "
                      "absent marker and would FAIL; it would NOT resolve. It also "
                      "agrees with the frozen report on every PRESENT constant, so "
                      "it is invisible to the existing constant-clause rival.",
        "rationale": "REJECT from the CONSTANT clause on the ABSENT sub-domain: "
                     "the spec pins the report to `constM` verbatim, so an absent "
                     "constant reports the absent marker, while the rival reports "
                     "a present concrete stamp. Partial-domain (agrees with gold "
                     "wherever the constant is present). Moves constM to `none` "
                     "with callM false — the seventh distinct refutation point, "
                     "and the only one exercising a defined-but-absent constant.",
        "witness": (
            "example : ¬ problem_spec_latestLastmod true false [] none\n"
            "    (implementation_latestLastmod true false [] none) := by\n"
            "  unfold problem_spec_latestLastmod implementation_latestLastmod\n"
            "  decide\n"
        ),
    },
]

# No AXIOM lane here: the bundle consumes no `axiom` and declares no `opaque`
# (the greatest-of-a-list operation is the Mathlib builtin `List.max?`, and a
# timestamp is a comparable `Int`). The nagini AXIOM_TESTS were also empty;
# dropped.
AXIOM_TESTS = []
