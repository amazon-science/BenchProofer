"""properties.py — G-PBT falsification battery for pydata__xarray-4695 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct`` obligation survives) and swaps in a candidate
implementation. It is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over one binder):

  labelSelect (key : List (String × Label))   ensures out = Except.ok key

The routine is asked to honour a per-dimension request mapping: a list of
``(dimension-name, requested-labels)`` pairs. The single load-bearing clause
``out = Except.ok key`` pins EVERY facet of the intended behaviour at once —
selection must SUCCEED (``Except.ok``, never an error), and it must carry back
EXACTLY the mapping it was given: every entry present (none dropped), in order
(none reordered), unmodified, REGARDLESS of the textual dimension names — in
particular a dimension whose name coincides with an option of the selection
routine must NOT be diverted away from the dimension request.

CARRIER NOTE — everything here is decidable. There are NO opaque callees: the
spec is stated over ``List (String × Label)`` with concrete string/list
literals, so every reject witness lives at a concrete input that reduces under
kernel ``decide``. No conditioning on the carrier is needed, and no reject case
was dropped for being non-discriminable.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling writes back
    into a half-permission input (``names`` / ``values``) to prove the read-only
    frame holds. Lean and Velvet are referentially transparent and this method
    declares NO ``mut`` binder, so there is no read-only input to overwrite and
    no substitute probe to build. Reported N/A in the footer, not fabricated.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line a single ``return`` over immutable values, no loop
    and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A. The postcondition equates the result to the
    method's own input ``key`` (a structural predicate on the actual carrier),
    not to an opaque answer-key; there is nothing for a wrong impl to echo.
  * ROUTING / CONTENT / ORDER / SUCCESS — the main class. Each rival attacks a
    distinct facet of ``out = Except.ok key`` (drops a name-colliding entry;
    injects a spurious error on a collision; rejects unconditionally; drops an
    entry by position; reorders; rewrites a dimension name; truncates the
    requested label list), each refuted at a distinct concrete ``key`` point.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery
(``extract_program_for`` / ``derive_tester_for``): ``labelSelectTester key =
false`` says the extracted program's result violates the postcondition at that
concrete input. It is checked in a file whose ``prove_correct`` block has been
stripped, so no tactic script can mask the verdict.
``prove_postcondition_decidable_for`` needs equality of the report carrier
``Except String (List (String × Label))`` to be decidable, so the preamble
derives that instance first — an instance, not an assumption (no ``axiom`` /
``sorry`` / ``native_decide``), and the frozen solution rejects every witness
all the same (on each witness point the frozen impl SATISFIES the
postcondition, so its tester returns ``true`` and ``= false`` fails against gold
— the discriminator).

WITNESS PLACEMENT. The single binder ``key`` is moved across the seven reject
witnesses so the battery probes seven distinct input points rather than pinning
the binder:
  * ``[("method",["a"]),("dim1",["x"])]``  — collides, 2 entries, colliding first
  * ``[("method",["a"])]``                 — collides, 1 entry
  * ``[("dim1",["x"])]``                   — no collision, 1 entry
  * ``[("dim1",["x"]),("dim2",["y"])]``    — no collision, 2 entries
  * ``[("time",["t0","t1"])]``             — no collision, multi-label
  * ``[("dim2",["b"]),("method",["a"])]``  — collides, colliding entry LAST
  * ``[("dim1",["x","y"])]``               — no collision, 2 labels on one dim
The witnesses vary the presence of a name-colliding entry, its POSITION in the
mapping, the entry count, the order, and the LENGTH OF THE LABEL LIST per
dimension — the facets the seven rivals abuse — so no rival that mishandled only
one of those would slip through. pts=7.

The last three points close gaps the audit found in the original four: every
original witness carried a single-element label list, so a rival that mangled the
per-dimension label list (rather than the entry set) was unattacked; every
collision witness put the colliding entry FIRST; and no witness lived at a point
where the rival errs with no collision present at all.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the selection
engine is modelled deeply as the identity carry-through and validated by
G-CONF). The gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-4695"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the frozen impl block, verbatim (inside -- impl-start / -- impl-end).
# ---- Every variant swaps THIS whole block; a positive that reshapes into a
# ---- branch also retunes the (elided) proof body. Both anchors lie wholly
# ---- inside regions the spec view elides and are unique (asserted at load).
_GOLD_IMPL = (
    "    -- impl-start\n"
    "    -- Apply the whole mapping as the dimension/label request, as a unit.\n"
    "    return Except.ok key\n"
    "    -- impl-end"
)
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block drifted from Solution.lean"

_GOLD_PROVE = "prove_correct labelSelect by\n  loom_solve"
assert _BASE.count(_GOLD_PROVE) == 1, "frozen proof block drifted from Solution.lean"


# ---- witness preamble: reach the method contract through Velvet's tester.
# ---- Except-carrier equality is DERIVED as an instance (not assumed). ----
_PREAMBLE = (
    "deriving instance DecidableEq for Except\n\n"
    "extract_program_for labelSelect\n"
    "prove_precondition_decidable_for labelSelect\n"
    "prove_postcondition_decidable_for labelSelect\n"
    "derive_tester_for labelSelect\n\n"
)


def _wit(example):
    return _PREAMBLE + example


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. If a faithful correct impl cannot verify, the spec is
# SPEC-TOO-STRONG. Each keeps the obligation and reshapes only the executable
# surface + its (elided) proof body.
# ===========================================================================

# Local-staging reshape: bind the mapping to a local before returning it. Same
# carry-through as gold on every input; the frozen `loom_solve` still closes.
_POS_LOCAL_IMPL = (
    "    -- impl-start\n"
    "    -- Same whole-mapping carry-through, staged through a local binding.\n"
    "    let applied := key\n"
    "    return Except.ok applied\n"
    "    -- impl-end"
)

# Name-agnostic branch: classify whether some dimension name coincides with a
# routine option, then carry the whole mapping through on BOTH sides — so no
# entry is ever diverted by its name. Structurally a routing decision (mirroring
# the shape a name-keyed rival would take) whose two arms produce the SAME
# result, so it is correct on every input; the two arms fold back with `rfl`.
_POS_BRANCH_IMPL = (
    "    -- impl-start\n"
    "    -- Name-agnostic routing: classify whether a dimension name coincides\n"
    "    -- with a routine option, but carry the whole mapping through on BOTH\n"
    "    -- branches, so no entry is diverted by its name.\n"
    "    let collides := key.any (fun p =>\n"
    "      decide (p.1 = \"method\" ∨ p.1 = \"tolerance\" ∨ "
    "p.1 = \"drop\" ∨ p.1 = \"indexers\"))\n"
    "    if collides then\n"
    "      return Except.ok key\n"
    "    else\n"
    "      return Except.ok key\n"
    "    -- impl-end"
)
_POS_BRANCH_PROVE = "prove_correct labelSelect by\n  loom_solve\n  all_goals rfl"


# ===========================================================================
# ADMISSIBILITY (re-aimed) — this method has NO `require` clause, so the nagini
# "a normal / colliding F2P-shaped input satisfies the precondition" probe is
# VACUOUS: nothing could exclude an in-domain input. Re-aimed at the residual
# risk on a total domain — that the post-image is UNSATISFIABLE / DEGENERATE at
# the interesting point (a spec no impl can meet reads exactly like a spec every
# impl meets). The case discharges a live in-region assert that the post-image
# genuinely DEPENDS on the request at an F2P-shaped point: a name-colliding
# mapping must be carried through as a SUCCESS (never the rejection the pre-fix
# routing produces) and distinct requests demand distinct results. The impl is
# kept as a carry-through, so the method's own obligation still discharges; the
# assert is live (a false claim leaves an unsolved goal).
#
# AUDIT REPAIR. The original assert here was stated over CLOSED LITERALS only
# (`Except.ok [("method",["a"])] ≠ Except.ok []`) — two ground disequalities that
# `decide` closes without ever mentioning the method's binder, so it attested to
# nothing about THIS post-image and would have discharged against any spec over
# this carrier. Restated over `key` itself, so the claim is about the post-image
# at the method's own universally-quantified request: the intended result at an
# ARBITRARY request is a success, and prefixing a name-colliding entry onto that
# request changes the demanded result (so the obligation is request-DEPENDENT,
# not a constant any impl meets). Liveness re-measured by the audit: flipping the
# second conjunct to an equality leaves `unsolved goals ⊢ False` (exit 1).
# ===========================================================================
_ADMISS_IMPL = (
    "    -- impl-start\n"
    "    -- Admissibility: the intended result is non-degenerate at an\n"
    "    -- F2P-shaped input — a mapping whose dimension name coincides with a\n"
    "    -- routine option must be carried through as a SUCCESS (not the\n"
    "    -- rejection the diverting routing produces), and distinct requests\n"
    "    -- demand distinct results, so the obligation is satisfiable but not\n"
    "    -- vacuously constant. Stated over the method's OWN binder `key`, so\n"
    "    -- the claim is about this post-image and not a ground literal fact.\n"
    "    assert (with_name_prefix `assert\n"
    "      (((Except.ok key : Except String (List (String × Label)))\n"
    "          ≠ Except.error \"Invalid fill method\") ∧\n"
    "       ((Except.ok ((\"method\", [\"a\"]) :: key) :\n"
    "          Except String (List (String × Label)))\n"
    "          ≠ Except.ok key)))\n"
    "    return Except.ok key\n"
    "    -- impl-end"
)
_ADMISS_PROVE = (
    "prove_correct labelSelect by\n"
    "  loom_solve\n"
    "  all_goals first\n"
    "    | exact ⟨by simp, by simp⟩\n"
    "    | simp\n"
    "    | rfl"
)


# ===========================================================================
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected, each with a machine-checked refutation witness at a distinct
# decidable input and the argument that its faithful real counterpart would NOT
# resolve the failing test.
# ===========================================================================

# R1: drop every name-colliding entry (the pre-fix name-keyed routing, filtering
# variant). Correct on any mapping with no colliding name; on a colliding input
# the colliding entry is silently absent from the applied mapping.
_R1_DROP_COLLIDING = (
    "    -- impl-start\n"
    "    -- Divert away (DROP) any entry whose dimension name coincides with a\n"
    "    -- routine option — the pre-fix name-keyed routing.\n"
    "    return Except.ok (key.filter (fun p =>\n"
    "      decide (p.1 ≠ \"method\" ∧ p.1 ≠ \"tolerance\" ∧ "
    "p.1 ≠ \"drop\" ∧ p.1 ≠ \"indexers\")))\n"
    "    -- impl-end"
)

# R2: reject the whole selection with an error whenever a colliding name is
# present. This is the pre-fix crash path: a colliding entry is fed to an option
# that rejects its value.
_R2_ERROR_ON_COLLISION = (
    "    -- impl-start\n"
    "    -- Reject the selection when a dimension name coincides with a routine\n"
    "    -- option (the pre-fix crash path: the entry is fed to the option, whose\n"
    "    -- value is not a valid setting for it).\n"
    "    let methodHit := key.any (fun p => decide (p.1 = \"method\"))\n"
    "    if methodHit then\n"
    "      return Except.error \"Invalid fill method\"\n"
    "    else\n"
    "      return Except.ok key\n"
    "    -- impl-end"
)

# R3: drop the LAST entry (positional off-by-one). Correct on the empty mapping;
# wrong on every non-empty one.
_R3_DROP_LAST = (
    "    -- impl-start\n"
    "    -- Off-by-one: forward every entry EXCEPT the last.\n"
    "    return Except.ok key.dropLast\n"
    "    -- impl-end"
)

# R4: reverse the mapping (order-scrambling). Correct only on lists of length
# <=1; wrong whenever two entries appear in a fixed order.
_R4_REVERSE = (
    "    -- impl-start\n"
    "    -- Order-scrambling: apply the entries in reverse order.\n"
    "    return Except.ok key.reverse\n"
    "    -- impl-end"
)

# ---- AUDIT-ADDED rivals (R5-R7): facets the original four left unattacked. ----

# R5: reject EVERY request, collision or not. The four original rivals all agree
# with gold on some non-colliding input, so none of them attacked the bare
# SUCCESS facet at a point with no collision in play; this one does.
_R5_ERROR_ALWAYS = (
    "    -- impl-start\n"
    "    -- Refuse every selection request outright, whatever was asked for.\n"
    "    return Except.error \"Invalid fill method\"\n"
    "    -- impl-end"
)

# R6: rewrite ("sanitize") a colliding dimension name rather than applying the
# entry under the name requested. Distinct from R1/R2: the entry is neither
# dropped nor rejected — it is applied to a DIFFERENT dimension, which the
# `out = Except.ok key` clause forbids just as squarely. Its witness also places
# the colliding entry LAST, a position no original witness probed.
_R6_RENAME_COLLIDING = (
    "    -- impl-start\n"
    "    -- Rewrite a dimension name that coincides with a routine option instead\n"
    "    -- of applying the entry under the name that was requested.\n"
    "    return Except.ok (key.map (fun p =>\n"
    "      (if p.1 = \"method\" then p.1 ++ \"_dim\" else p.1, p.2)))\n"
    "    -- impl-end"
)

# R7: keep only the FIRST requested label along each dimension. Every original
# witness carried singleton label lists, on which this rival is INDISTINGUISHABLE
# from gold — so the per-dimension label CONTENT (the second projection, the
# `Label` carrier itself) was entirely unprobed. Correct on scalar-label requests,
# wrong on any list-valued one.
_R7_TRUNCATE_LABELS = (
    "    -- impl-start\n"
    "    -- Keep only the FIRST requested label along each dimension.\n"
    "    return Except.ok (key.map (fun p => (p.1, p.2.take 1)))\n"
    "    -- impl-end"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS
    # =====================================================================
    {
        "id": "pos-local-staging",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_LOCAL_IMPL),
        "rationale": "staging the mapping through a local binding before returning "
                     "it carries back exactly `key` on every input, so "
                     "`out = Except.ok key` holds and the frozen `loom_solve` still "
                     "closes. A correct reshape must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-name-agnostic-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _GOLD_IMPL, _POS_BRANCH_IMPL),
                        _GOLD_PROVE, _POS_BRANCH_PROVE),
        "rationale": "classifying whether a dimension name coincides with a routine "
                     "option and then carrying the whole mapping through on BOTH "
                     "branches produces the SAME result as gold on every input "
                     "(no entry diverted by its name), so `out = Except.ok key` "
                     "still holds; the two arms fold back with `rfl`. This defends "
                     "the 'regardless of names' intent directly. A correct reshape "
                     "must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY (re-aimed)
    # =====================================================================
    {
        "id": "admiss-collision-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL),
                        _GOLD_PROVE, _ADMISS_PROVE),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: a name-colliding mapping must be carried "
                     "through as a SUCCESS (never the rejection a diverting routing "
                     "produces) and distinct requests demand distinct results. The "
                     "in-region assert must discharge (else the obligation is "
                     "unsatisfiable / constant at the interesting point); the impl "
                     "is kept as a carry-through so `out = Except.ok key` discharges "
                     "as well. Re-aimed from the nagini precondition-admits probe, "
                     "vacuous here (no `require` clause).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals
    # =====================================================================
    {
        "id": "weak-drop-colliding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R1_DROP_COLLIDING),
        "refinement": "this IS the pre-fix name-keyed routing: an entry whose "
                      "dimension name coincides with a selection-routine option is "
                      "diverted out of the dimension request and DROPPED from the "
                      "applied mapping. The failing test drives exactly a "
                      "name-colliding request and asserts the colliding dimension "
                      "is still selected; a faithful counterpart drops it and does "
                      "NOT resolve.",
        "rationale": "REJECT from `out = Except.ok key`: on a mapping containing a "
                     "colliding name the rival returns the mapping with that entry "
                     "removed, which != Except.ok key. Refuted at "
                     "[(\"method\",[\"a\"]),(\"dim1\",[\"x\"])] — colliding entry "
                     "first, so its removal changes the list.",
        "witness": _wit(
            "example : labelSelectTester [(\"method\", [\"a\"]), "
            "(\"dim1\", [\"x\"])] = false := by\n  decide\n"),
    },
    {
        "id": "weak-error-on-collision",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R2_ERROR_ON_COLLISION),
        "refinement": "this is the pre-fix crash path: a dimension name coinciding "
                      "with a routine option feeds its label list to that option, "
                      "whose value is not a valid setting for it, so the whole "
                      "selection is rejected with an error. The failing test drives "
                      "that exact request and asserts a SUCCESSFUL selection; a "
                      "faithful counterpart raises instead and does NOT resolve.",
        "rationale": "REJECT from `out = Except.ok key`: on a colliding mapping the "
                     "rival returns Except.error, but the spec demands a successful "
                     "Except.ok carrying the whole mapping. Refuted at "
                     "[(\"method\",[\"a\"])] — a single colliding entry, the "
                     "minimal error-trigger.",
        "witness": _wit(
            "example : labelSelectTester [(\"method\", [\"a\"])] = false "
            ":= by\n  decide\n"),
    },
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R3_DROP_LAST),
        "refinement": "a counterpart that forwarded every entry EXCEPT the last "
                      "would drop a dimension from EVERY non-empty selection "
                      "request — the last requested dimension is never applied. "
                      "Broad selection tests (and the F2P) observe the missing "
                      "dimension, so a faithful counterpart does NOT resolve.",
        "rationale": "REJECT from `out = Except.ok key`: for any non-empty mapping "
                     "the rival returns key.dropLast, which != key. Refuted at a "
                     "non-colliding singleton [(\"dim1\",[\"x\"])] — so the failure "
                     "is the positional drop alone, distinguishing it from the "
                     "name-keyed rivals; here dropLast yields [].",
        "witness": _wit(
            "example : labelSelectTester [(\"dim1\", [\"x\"])] = false "
            ":= by\n  decide\n"),
    },
    {
        "id": "weak-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R4_REVERSE),
        "refinement": "a counterpart that applied the requested dimensions in "
                      "reverse order would bind each label list to the wrong "
                      "dimension whenever two or more dimensions are requested — a "
                      "corrupted selection. Selection tests over multi-dimension "
                      "requests observe the mismatched axes, so a faithful "
                      "counterpart does NOT resolve.",
        "rationale": "REJECT from `out = Except.ok key`: for a mapping of length "
                     ">=2 the rival returns key.reverse, which != key. Refuted at "
                     "[(\"dim1\",[\"x\"]),(\"dim2\",[\"y\"])] — two non-colliding "
                     "entries whose order the reversal swaps; this is the only "
                     "reject witness that fails purely on ORDER, moving the binder "
                     "onto a 2-entry non-colliding mapping.",
        "witness": _wit(
            "example : labelSelectTester [(\"dim1\", [\"x\"]), "
            "(\"dim2\", [\"y\"])] = false := by\n  decide\n"),
    },

    # ---- AUDIT-ADDED (R5-R7) ------------------------------------------------
    {
        "id": "weak-error-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R5_ERROR_ALWAYS),
        "refinement": "a counterpart that refused every request would reject even "
                      "the plainest single-dimension selection, so it fails the F2P "
                      "AND essentially every broad selection test in the suite — it "
                      "cannot resolve. Added by the audit because all four original "
                      "rivals agreed with the intended behaviour on SOME "
                      "non-colliding request, leaving the bare SUCCESS facet "
                      "unattacked away from a name collision.",
        "rationale": "REJECT from `out = Except.ok key`: the rival returns "
                     "Except.error unconditionally, while the spec demands a "
                     "successful Except.ok carrying the mapping at EVERY input. "
                     "Refuted at [(\"time\",[\"t0\",\"t1\"])] — no colliding name "
                     "anywhere, so the failure is attributable to the success "
                     "requirement alone and to no name-routing facet.",
        "witness": _wit(
            "example : labelSelectTester [(\"time\", [\"t0\", \"t1\"])] = false "
            ":= by\n  decide\n"),
    },
    {
        "id": "weak-rename-colliding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R6_RENAME_COLLIDING),
        "refinement": "a counterpart that renamed a colliding dimension instead of "
                      "applying the entry under the name requested would select "
                      "along an axis the caller never named — for the F2P request it "
                      "raises on the unknown rewritten dimension rather than "
                      "returning the requested sub-array, so it does NOT resolve. "
                      "Distinct from the drop and the error rivals: the entry "
                      "survives, but bound to the wrong dimension.",
        "rationale": "REJECT from `out = Except.ok key`: the applied mapping carries "
                     "a rewritten dimension name, so it != key. Refuted at "
                     "[(\"dim2\",[\"b\"]),(\"method\",[\"a\"])] — a collision in "
                     "FINAL position, the placement no other witness probes, "
                     "checking that the clause is not defended only for a leading "
                     "colliding entry.",
        "witness": _wit(
            "example : labelSelectTester [(\"dim2\", [\"b\"]), "
            "(\"method\", [\"a\"])] = false := by\n  decide\n"),
    },
    {
        "id": "weak-truncate-labels",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R7_TRUNCATE_LABELS),
        "refinement": "a counterpart that kept only the first label along each "
                      "dimension would return a narrower sub-array than requested "
                      "whenever more than one tick label is asked for on a "
                      "dimension. The failing test requests a multi-label selection "
                      "along one dimension and compares the full selected block, so "
                      "a faithful counterpart returns the wrong shape and does NOT "
                      "resolve.",
        "rationale": "REJECT from `out = Except.ok key`: the rival truncates the "
                     "second projection, so the applied mapping != key. Refuted at "
                     "[(\"dim1\",[\"x\",\"y\"])] — the only witness with TWO labels "
                     "on one dimension. Added by the audit: every original witness "
                     "used singleton label lists, on which this rival is "
                     "indistinguishable from the frozen impl, so the `Label` "
                     "carrier itself (the per-dimension label CONTENT, as opposed "
                     "to the entry set) was unprobed.",
        "witness": _wit(
            "example : labelSelectTester [(\"dim1\", [\"x\", \"y\"])] = false "
            ":= by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases over TWO
# contracted functions (forward_axis_names + bound_reserved_option): 2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 4 partial-domain /
# oracle-echo rivals. This bundle models the SAME behaviour — the whole indexer
# mapping is honoured as the (dimension, labels) request, regardless of names —
# as ONE method `labelSelect` with ONE obligation `out = Except.ok key`. That
# single clause fuses the sibling's two load-bearing postconditions:
# "the whole mapping is forwarded" (forward_axis_names' ToSeq(Result)==ToSeq
# (names)) and "no colliding entry leaks / is diverted" (bound_reserved_option's
# Result()==DEFAULT_OPTION). Carrier narrowing collapses the two functions into
# one; parity is NOT the target.
#
#   sibling case                          -> here
#   ---------------------------------------------------------------------
#   pos-control-forward-localreshape      -> pos-local-staging            PORTED
#   pos-control-option-direct             -> pos-name-agnostic-branch     PORTED
#   admiss-colliding-input                -> admiss-collision-nondegenerate RE-AIMED
#   frame-mutation-names-append           -> (none)                       VACUOUS
#   frame-mutation-values-write           -> (none)                       VACUOUS
#   partial-domain-drop-colliding         -> weak-drop-colliding          PORTED
#   partial-domain-drop-last              -> weak-drop-last               PORTED
#   oracle-echo-option-namekeyed          -> weak-error-on-collision      PORTED
#   partial-domain-option-conditional     -> weak-error-on-collision      MERGED
#   (added for ORDER-facet coverage)      -> weak-reverse-order           ADDED
#   (audit: SUCCESS facet off-collision)  -> weak-error-always            ADDED
#   (audit: wrong-dimension binding)      -> weak-rename-colliding        ADDED
#   (audit: label-CONTENT facet)          -> weak-truncate-labels         ADDED
#
# PORTED (positives): the sibling's two positives (a local-reshape forward copy
#   and a direct option return) become pos-local-staging (stage the mapping
#   through a local) and pos-name-agnostic-branch (a routing decision that
#   carries the whole mapping through on both arms — the structural analogue of
#   "the reserved option is never fed from the mapping"). Both verify.
# PORTED (rivals): partial-domain-drop-colliding IS the pre-fix name-keyed
#   routing that DROPS a colliding dimension -> weak-drop-colliding, the G-DIFF
#   discriminator; partial-domain-drop-last -> weak-drop-last (positional
#   off-by-one).
# PORTED + MERGED (site-B option rivals): the sibling's two bound_reserved_option
#   rivals (oracle-echo-option-namekeyed and partial-domain-option-conditional)
#   both encode "a colliding dimension is bound to a routine option instead of
#   being applied as a dimension". On this carrier that option-binding is not a
#   separate returned scalar — there is no reserved-option slot in the model — it
#   manifests as the selection being REJECTED (the option rejects the label
#   value: the "Invalid fill method" crash the issue reports). Both sibling
#   rivals therefore map to the SAME observable failure here, captured once by
#   weak-error-on-collision. The conditional variant's "correct off the collision"
#   subtlety is already covered: weak-error-on-collision is itself correct on
#   every non-colliding mapping and wrong only on the collision.
# ADDED (1): weak-reverse-order. The `out = Except.ok key` clause pins ORDER as
#   well as membership; no sibling rival attacks order (nagini's ToSeq==ToSeq is
#   defended by front-prefix invariants, and order-scrambling was not a modeled
#   failure there). Added so the ORDER facet of the fused clause is attacked and
#   the `key` binder is probed at a 2-entry non-colliding point.
# ADDED BY THE AUDIT (3): the fused clause has facets the ported four left open,
#   each closed by a rival whose two builds were run:
#   * weak-error-always — every one of the original four rivals AGREES with the
#     intended behaviour on some non-colliding request, so the bare SUCCESS
#     requirement was only ever attacked in the presence of a name collision
#     (weak-error-on-collision errs only when one is there). This rival errs
#     everywhere and is refuted at a collision-free point.
#   * weak-rename-colliding — the ported rivals dispose of a colliding entry by
#     DROPPING it or REJECTING the request. Neither covers "the entry is applied,
#     but to a different dimension than the one named", which the clause forbids
#     just as squarely; and its witness puts the collision LAST, a position no
#     ported witness used.
#   * weak-truncate-labels — every ported witness used SINGLETON label lists, on
#     which a rival that mangles the second projection is indistinguishable from
#     the frozen impl. So `Label` (the per-dimension label CONTENT, as opposed to
#     the entry set) was unprobed by the whole battery, even though the fused
#     clause pins it and the failing test requests a multi-label selection.
# VACUOUS (frame-mutation x2): the sibling writes back to a half-permission input
#   to prove the read-only frame holds. This backend is referentially transparent
#   and `labelSelect` declares NO `mut` binder (`key` is read-only by
#   construction), so there is no read-only input to overwrite and no substitute
#   probe to build. Not fabricated.
#
# WITNESS DISTINCTNESS. Seven distinct input points, probing the sole binder
#   `key` on presence-of-collision, collision POSITION, entry count, order, and
#   per-dimension label-list length:
#   [("method",["a"]),("dim1",["x"])]  weak-drop-colliding   (colliding entry dropped)
#   [("method",["a"])]                 weak-error-on-collision (collision -> error)
#   [("dim1",["x"])]                   weak-drop-last          (positional drop)
#   [("dim1",["x"]),("dim2",["y"])]    weak-reverse-order      (order scrambled)
#   [("time",["t0","t1"])]             weak-error-always       (success denied, no collision)
#   [("dim2",["b"]),("method",["a"])]  weak-rename-colliding   (bound to wrong dimension)
#   [("dim1",["x","y"])]               weak-truncate-labels    (label content dropped)
# Each rival fails for a DIFFERENT reason (drop-by-name / error-on-collision /
# drop-by-position / reorder / unconditional error / rename / label truncation) at
# a DIFFERENT point, so they are seven distinct predicates. pts=7.
# Every case was validated with two real builds (rival succeeds, gold fails), and
# every gold-side failure was read to confirm it is a SEMANTIC refutation —
# `decide` proved the claim false — and not a missing identifier, type error or
# stuck reduction.
#
# DIVERGENCE lane - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line a single ``return`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and is skipped for this
# instance (meta.json axioms == []; the selection engine is modelled deeply and
# differential-tested by G-CONF, not axiomatized).
AXIOM_TESTS = []
