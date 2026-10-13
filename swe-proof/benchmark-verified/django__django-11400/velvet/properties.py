"""properties.py — G-PBT falsification battery for django__django-11400 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and every ``prove_correct`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (two contracted methods, sharing one ordering kernel):

  orderedChoices (defaultOrdering requested : List String)
      return (out : List String)
    ensures out = effectiveOrdering defaultOrdering requested

  restrictedChoices (defaultOrdering adminOrdering : List String)
      return (out : List String)
    ensures out = effectiveOrdering defaultOrdering adminOrdering

An ordering specification is a sequence of ordering keys; the empty sequence
means "no explicit request". The pure kernel pins the whole outcome as a total
function of the two input sequences:

  effectiveOrdering defaultOrdering requested
    = if requested.isEmpty then defaultOrdering else requested

``restrictedChoices`` is the value-restricted call site: it routes its
configured ordering through the SAME kernel (``orderedChoices``) as an explicit
request, and its proof is discharged by the generated ``orderedChoices``
obligation (callee-under-spec), not an axiom.

What the spec defends, and the attacks it must survive:

  * The DISCRIMINATING clause is the EMPTY case: when the explicit request is
    empty (``requested.isEmpty``), the result MUST be the intrinsic default
    ordering, NOT the empty request itself. The behaviour this bundle corrects
    applied the request UNCONDITIONALLY, so an empty request collapsed the
    default to "no ordering at all" — the exact regression the failing tests
    pin (a collection with a non-trivial intrinsic default ordering, queried
    with an empty explicit request, must come back in that default order). A
    rival that routes the empty case through the request violates this clause
    (``rival-prepatch``, ``rival-restricted-uncond``). The clause demands the
    default back VERBATIM, not merely "something derived from it", so it is also
    attacked by a rival that preserves only a PREFIX of a multi-key default
    (``rival-default-first-key-only``) — the sub-domain every other rival misses,
    since each of those is refuted at a single-key default where a
    prefix-truncating fallback is indistinguishable from the frozen impl.

  * The REORDER case: when the explicit request is NON-empty, the result MUST be
    the request verbatim — the default must NOT be allowed to override it.
    Grounded entirely in the two inputs: ``effectiveOrdering`` is a concrete
    ``def`` over the method's own arguments (the ``axioms`` region is empty; no
    opaque answer-key to echo), so the unique satisfier IS the grounded
    selection and there is no wrong echo to build. A rival that keeps the
    default on a non-empty request violates this clause
    (``rival-invert``, ``rival-partial-len1``, ``rival-always-default``).

  * The value-restricted site must ROUTE its configured ordering to the kernel:
    discarding it loses the guarantee that the restricted choices honor the
    configured ordering exactly as the unrestricted choices do
    (``rival-restricted-drops-admin``).

Both input binders of each method are free (no ``require`` clause) and the
post-image must hold for EVERY value of each:
  * ``defaultOrdering`` — the collection's intrinsic default ordering; governs
    the empty-request case.
  * ``requested`` / ``adminOrdering`` — the explicitly requested ordering;
    governs the non-empty case and its emptiness selects the branch.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling's MANDATORY
    frame-mutation rivals (``frame-mutate-base`` / ``frame-mutate-ordering``)
    keep the gold body verbatim then write back into a read-only sequence input
    carrying only a fractional heap permission (``Acc(list_pred(.),1/2)``) and
    are rejected for INSUFFICIENT PERMISSION. Lean and Velvet are referentially
    transparent: every parameter is an immutable value, neither method declares
    a ``mut`` binder over an input, there is no heap and no aliasing. There is
    no read-only input to overwrite and no permission system to trip, so the
    class is vacuous here. No substitute is fabricated.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``let`` / ``if`` over
    immutable values, no loop and no recursion), so there is no control flow
    here to make diverge: a diverging rival cannot be obtained by mutating this
    body, it has to bring a loop of its own. When it does, the semantics refuse
    it. This bundle sets ``loom.semantics.termination "total"`` AND carries
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
  * UNGROUNDED-ORACLE ECHO — N/A. ``effectiveOrdering`` is a concrete ``def``
    computing the outcome from the method's own arguments; the ``axioms`` region
    is empty (there is no opaque callee — the downstream materialization that
    turns the selected ordering specification into an ordered sequence is an
    UNCHANGED shared continuation, reached identically on both branches, so
    nothing about it is assumed or modeled, see mapping.md §3). There is no
    answer-key to echo; the positives are honest cheapest reshapes.

WITNESS MECHANICS. Both frozen impls reduce fully under ``decide`` at concrete
``List String`` inputs. Each reject rival carries a machine-checked refutation
``witness`` — a Velvet tester statement ``<method>Tester <args> = false`` at ONE
concrete input, checked in a file whose ``prove_correct`` blocks have been
stripped so no tactic script can mask the verdict. Both halves were checked
out-of-band with ``scripts/lean_verify.sh``: every witness ELABORATES against
its rival (exit 0) and FAILS against the frozen solution (``decide`` proves the
proposition false, exit 1), so each rejection is a genuine spec refutation and
not mechanical tactic breakage. No witness binds a hypothesis (every refutation
is at literal inputs), so there is no consistency-probe surface.

AXIOM lane: EMPTY. This bundle declares no ``axiom`` and no deep-model
reference; ``effectiveOrdering`` is an I/R-op modeled directly and checked by
``conformance_check.py`` (G-CONF), not axiomatized. The nagini sibling's
``AXIOM_TESTS`` (probes of the real ordering-materialization callee) are
dropped: they belong to a bundle that axiomatizes that callee, whereas this
bundle models the pure selection kernel deeply and axiomatizes nothing (the
materialization is an unchanged shared continuation, neither consumed nor
modeled; mapping.md §3), so the axiom lane has nothing to probe here, and this
gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11400"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- frozen region anchors (each strictly inside one impl / proof region and
# --- unique in Solution.lean; both facts asserted at load by _swap). ---------

# orderedChoices — the whole impl body (markers included).
_OC_IMPL = (
    "    -- impl-start\n"
    "    -- Start from the collection's intrinsic default ordering; apply the explicit\n"
    "    -- request only when one was actually given (a non-empty sequence). An empty\n"
    "    -- request leaves the default ordering in place.\n"
    "    let mut ordering := defaultOrdering\n"
    "    ordering := if requested.isEmpty then ordering else requested\n"
    "    return ordering\n"
    "    -- impl-end"
)
assert _BASE.count(_OC_IMPL) == 1, "orderedChoices impl region drifted"

# orderedChoices — the frozen proof (retuned only by correct reshapes).
_OC_PROOF = ("prove_correct orderedChoices by\n"
             "  loom_solve\n"
             "  simp_all [effectiveOrdering]")
assert _BASE.count(_OC_PROOF) == 1, "orderedChoices proof region drifted"

# restrictedChoices — the whole impl body (markers included).
_RC_IMPL = (
    "    -- impl-start\n"
    "    -- Route the administrator-configured ordering through the shared ordering\n"
    "    -- kernel; it is treated exactly as an explicit request, so a configured\n"
    "    -- ordering governs and an absent one falls back to the default.\n"
    "    let out ← orderedChoices defaultOrdering adminOrdering\n"
    "    return out\n"
    "    -- impl-end"
)
assert _BASE.count(_RC_IMPL) == 1, "restrictedChoices impl region drifted"

# restrictedChoices — the frozen proof.
_RC_PROOF = "prove_correct restrictedChoices by\n  loom_solve"
assert _BASE.count(_RC_PROOF) == 1, "restrictedChoices proof region drifted"


def _oc(body, proof=None):
    """orderedChoices impl body replaced; optionally retune its proof."""
    src = _swap(_BASE, _OC_IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")
    if proof is not None:
        src = _swap(src, _OC_PROOF, proof)
    return src


def _rc(body, proof=None):
    """restrictedChoices impl body replaced; optionally retune its proof."""
    src = _swap(_BASE, _RC_IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")
    if proof is not None:
        src = _swap(src, _RC_PROOF, proof)
    return src


# --- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# --- so a witness reaches it through Velvet's tester machinery:
# --- `<method>Tester <args> = false` says the extracted program's result
# --- violates the postcondition at that concrete input. Checked in a file whose
# --- `prove_correct` blocks are stripped. Inputs are literal `List String`, so
# --- `decide` reduces the tester fully; no hypothesis is bound. ----------------
def _wit(tester_method, call):
    return (f"extract_program_for {tester_method}\n"
            f"prove_precondition_decidable_for {tester_method}\n"
            f"prove_postcondition_decidable_for {tester_method}\n"
            f"derive_tester_for {tester_method}\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the selected value identical and only
    # reshapes the executable surface; the reproof stays close to the frozen
    # script.
    # =====================================================================
    {
        "id": "pos-explicit-else",
        "kind": "soundness",
        "expect": "verify",
        # Reshape orderedChoices: collapse the two-statement `let mut` staging
        # into a single `let`-bound if/else selection. Same value on every
        # input; the frozen proof still closes.
        "module": _oc(
            "    let out : List String := if requested.isEmpty then defaultOrdering else requested\n"
            "    return out"),
        "rationale": "collapsing the mutable-staging shape into a single "
                     "`let`-bound if/else computes the SAME selection on every "
                     "input (empty request => default, non-empty => request), so "
                     "`out = effectiveOrdering defaultOrdering requested` still "
                     "holds; a correct reshape must verify, else SPEC-TOO-STRONG "
                     "on the impl's statement form. This is also the cheapest "
                     "HONEST impl — the non-empty case still returns the request "
                     "itself (no oracle to echo).",
    },
    {
        "id": "pos-match-shape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape orderedChoices: decide the branch by pattern-matching the
        # request's emptiness (`[]` vs `_`) rather than testing `.isEmpty`. Same
        # outcome; proof retuned to case-split the match.
        "module": _oc(
            "    let out : List String :=\n"
            "      match requested with\n"
            "      | [] => defaultOrdering\n"
            "      | _  => requested\n"
            "    return out",
            "prove_correct orderedChoices by\n"
            "  loom_solve <;> (cases requested <;> simp_all [effectiveOrdering])"),
        "rationale": "deciding the branch by matching the request's emptiness "
                     "(`[]` vs a non-empty list) instead of `.isEmpty` selects "
                     "the SAME value on every input, so the ensures is unchanged; "
                     "a correct reshape must verify, else SPEC-TOO-STRONG on the "
                     "emptiness-test spelling.",
    },
    {
        "id": "pos-restricted-inline",
        "kind": "soundness",
        "expect": "verify",
        # Reshape restrictedChoices: inline the selection instead of delegating
        # to the shared kernel. Same value; the configured ordering still
        # governs when present and falls back to the default when absent. Proof
        # retuned (the delegation-generated obligation no longer applies).
        "module": _rc(
            "    let out : List String := if adminOrdering.isEmpty then defaultOrdering else adminOrdering\n"
            "    return out",
            "prove_correct restrictedChoices by\n"
            "  loom_solve\n"
            "  simp_all [effectiveOrdering]"),
        "rationale": "inlining the value-restricted site's selection instead of "
                     "delegating to the shared kernel computes the SAME result "
                     "(configured ordering governs when present, default when "
                     "absent), so `out = effectiveOrdering defaultOrdering "
                     "adminOrdering` still holds; a correct reshape must verify, "
                     "else SPEC-TOO-STRONG on the delegation form. Independently "
                     "defends the restrictedChoices obligation.",
    },

    # =====================================================================
    # ADMISSIBILITY — neither method carries a `require` clause, so the nagini
    # sibling's "a normal input satisfies the precondition" probe is degenerate
    # here (every input is in-domain). The residual admissibility risk on a
    # total-domain spec is that the selection is DEGENERATE — a kernel that
    # never actually separated the empty case from the non-empty case would read
    # like a live one. This case discharges an in-region assert pinning that the
    # kernel genuinely forks: an empty request preserves the default, a non-empty
    # request overrides it. The impl is kept verbatim so the method's own
    # obligation still discharges; the proof is retuned to also close the assert.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _oc(
            "    assert (with_name_prefix `assert\n"
            "      (effectiveOrdering [\"a\"] ([] : List String) = [\"a\"] ∧\n"
            "       effectiveOrdering [\"a\"] [\"b\"] = [\"b\"]))\n"
            "    let mut ordering := defaultOrdering\n"
            "    ordering := if requested.isEmpty then ordering else requested\n"
            "    return ordering",
            "prove_correct orderedChoices by\n"
            "  loom_solve <;> simp_all [effectiveOrdering]"),
        "rationale": "the selection is satisfiable AND non-degenerate: on an "
                     "empty request the kernel preserves the default "
                     "(`effectiveOrdering [\"a\"] [] = [\"a\"]`) and on a "
                     "non-empty request it overrides with the request "
                     "(`effectiveOrdering [\"a\"] [\"b\"] = [\"b\"]`), so the two "
                     "branches really do fork. The in-region assert must "
                     "discharge (else a degenerate kernel would read as a live "
                     "one); the impl is kept verbatim so the ensures still "
                     "discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries a machine-checked refutation witness at
    # a concrete input that FAILS on the frozen solution, and the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "rival-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-change behaviour: apply the explicit request UNCONDITIONALLY,
        # so an empty request collapses the default to "no ordering at all".
        "module": _oc("    return requested"),
        "refinement": "applying the explicit request unconditionally is exactly "
                      "the pre-change behaviour: an empty request is used "
                      "verbatim, clearing the collection's intrinsic default "
                      "ordering instead of preserving it. Its faithful real "
                      "counterpart is the unchanged repo, which is precisely what "
                      "FAILS the F2P tests that query a collection with a "
                      "non-trivial default ordering under an empty explicit "
                      "request and require the default order back. It would NOT "
                      "resolve — the exact defect the change corrects.",
        "rationale": "REJECT from `out = effectiveOrdering defaultOrdering "
                     "requested` on the EMPTY case: when `requested.isEmpty` the "
                     "post-image demands the default `defaultOrdering`, but the "
                     "rival returns the empty request. Refuted at a non-empty "
                     "default with an EMPTY request — the sub-domain the "
                     "empty-case clause pins. If it verified => SPEC-TOO-WEAK "
                     "(admits the very bug).",
        "witness": _wit("orderedChoices",
                        'orderedChoicesTester ["a"] ([] : List String)'),
    },
    {
        "id": "rival-invert",
        "kind": "uniqueness",
        "expect": "reject",
        # Guard inverted: keep the request when empty, fall back to the default
        # when non-empty — wrong on BOTH cases.
        "module": _oc(
            "    let out : List String := if requested.isEmpty then requested else defaultOrdering\n"
            "    return out"),
        "refinement": "inverting the branch keeps the (empty) request on the "
                      "empty case — clearing the default, the exact bug — AND "
                      "drops a non-empty explicit request in favour of the "
                      "default. A faithful counterpart fails BOTH the "
                      "empty-request F2P (default cleared) and the "
                      "explicit-ordering paths (request ignored). It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = effectiveOrdering defaultOrdering "
                     "requested` on the REORDER case: for a NON-empty request the "
                     "post-image demands the request, but the inverted rival "
                     "returns the default. Refuted at a non-empty request "
                     "(`[\"y\"]`) with a differing default (`[\"x\"]`) — the "
                     "sub-domain where the request must govern. If it verified => "
                     "SPEC-TOO-WEAK (the branch direction is unconstrained).",
        "witness": _wit("orderedChoices",
                        'orderedChoicesTester ["x"] (["y"] : List String)'),
    },
    {
        "id": "rival-partial-len1",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: correct on empty and on multi-key requests, but a
        # SINGLE-key request (length 1) is routed to the default instead of the
        # request.
        "module": _oc(
            "    let out : List String := if requested.length ≤ 1 then defaultOrdering else requested\n"
            "    return out"),
        "refinement": "treating a single-key request as if it were absent skips "
                      "the override for exactly the single-field orderings the "
                      "call sites most commonly supply, leaving those choices in "
                      "the default order rather than the requested one. It fails "
                      "the explicit-ordering F2P/P2P inputs (a single requested "
                      "key), so it would NOT resolve — a genuine PARTIAL-DOMAIN "
                      "break on the length-1 sub-domain.",
        "rationale": "REJECT from `out = effectiveOrdering defaultOrdering "
                     "requested` on the REORDER case, length-1 sub-domain: the "
                     "post-image demands the request for EVERY non-empty request "
                     "including a single key, but the rival returns the default "
                     "there. Refuted at a single-key request (`[\"a\"]`) with a "
                     "differing default (`[\"d\"]`) — the point the two "
                     "boundary rivals above do not reach. If it verified => "
                     "SPEC-TOO-WEAK (domain-incomplete on the override case).",
        "witness": _wit("orderedChoices",
                        'orderedChoicesTester ["d"] (["a"] : List String)'),
    },
    {
        "id": "rival-always-default",
        "kind": "uniqueness",
        "expect": "reject",
        # Never overrides: always return the default, ignoring any explicit
        # request. Correct on the empty case, wrong on every non-empty request.
        "module": _oc("    return defaultOrdering"),
        "refinement": "always returning the default is what a real patch that "
                      "never wired the explicit request through would do — the "
                      "collection is left in its default order even when an "
                      "explicit ordering is supplied, failing every "
                      "explicit-ordering F2P/P2P. It would NOT resolve.",
        "rationale": "REJECT from `out = effectiveOrdering defaultOrdering "
                     "requested` on the REORDER case: for a non-empty request the "
                     "post-image demands the request, but the rival always "
                     "returns the default. Refuted at a MULTI-key request "
                     "(`[\"q\", \"r\"]`) with a differing default (`[\"p\"]`), "
                     "varying the request-length binder against the length-1 "
                     "rival. If it verified => SPEC-TOO-WEAK (the override is "
                     "hollow).",
        "witness": _wit("orderedChoices",
                        'orderedChoicesTester ["p"] (["q", "r"] : List String)'),
    },
    {
        "id": "rival-default-first-key-only",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on the OTHER binder. The empty-request branch preserves
        # only the FIRST key of the intrinsic default ordering instead of the
        # whole sequence. Correct on every SINGLE-key default (which is where the
        # other five rivals are all refuted) and correct on every non-empty
        # request; wrong only at a MULTI-key default under an empty request.
        "module": _oc(
            "    let out : List String := if requested.isEmpty then defaultOrdering.take 1 else requested\n"
            "    return out"),
        "refinement": "truncating the preserved default to its leading key keeps "
                      "the fallback only partly intact: a collection whose "
                      "intrinsic default ordering ranks by more than one key comes "
                      "back ordered by the first key alone, so rows tied on that "
                      "key are left in an arbitrary order instead of the "
                      "tie-broken one the default ordering specifies. A faithful "
                      "counterpart FAILS the F2P inputs whose intrinsic default "
                      "ordering carries a secondary key, so it would NOT resolve.",
        "rationale": "REJECT from `out = effectiveOrdering defaultOrdering "
                     "requested` on the EMPTY case, MULTI-key-default sub-domain: "
                     "the post-image demands the default sequence VERBATIM, but the "
                     "rival returns a proper prefix of it. Refuted at a two-key "
                     "default (`[\"m\", \"n\"]`) under an empty request — the point "
                     "no other rival reaches, since every one of them is refuted at "
                     "a SINGLE-key default, where this rival is indistinguishable "
                     "from the frozen impl. It varies the `defaultOrdering` binder "
                     "by LENGTH rather than by spelling. If it verified => "
                     "SPEC-TOO-WEAK (the fallback would be pinned only up to its "
                     "first key).",
        "witness": _wit("orderedChoices",
                        'orderedChoicesTester ["m", "n"] ([] : List String)'),
    },
    {
        "id": "rival-restricted-drops-admin",
        "kind": "uniqueness",
        "expect": "reject",
        # The value-restricted site DISCARDS its configured ordering, passing an
        # empty request to the shared kernel — so the configured ordering never
        # reaches the kernel and the restricted choices come back in the default
        # order regardless.
        "module": _rc(
            "    let out ← orderedChoices defaultOrdering []\n"
            "    return out"),
        "refinement": "passing an empty request to the kernel is exactly the "
                      "pre-change value-restricted site, which omitted the "
                      "configured ordering entirely: the restricted choices were "
                      "never ordered by the configured ordering. Its faithful "
                      "counterpart FAILS the F2P tests that assert the "
                      "value-restricted filter honors the configured / model "
                      "ordering. It would NOT resolve.",
        "rationale": "REJECT from `out = effectiveOrdering defaultOrdering "
                     "adminOrdering` (restrictedChoices): with a NON-empty "
                     "configured ordering the post-image demands that ordering, "
                     "but the rival hands the kernel an empty request and gets "
                     "the default back. Refuted at a non-empty configured "
                     "ordering (`[\"a\"]`) with a differing default (`[\"d\"]`). "
                     "If it verified => SPEC-TOO-WEAK (the configured ordering "
                     "need not reach the kernel).",
        "witness": _wit("restrictedChoices",
                        'restrictedChoicesTester ["d"] (["a"] : List String)'),
    },
    {
        "id": "rival-restricted-uncond",
        "kind": "uniqueness",
        "expect": "reject",
        # The value-restricted site applies its configured ordering
        # UNCONDITIONALLY (returns it verbatim), so an EMPTY configured ordering
        # clears the default — the pre-change bug at the restricted site.
        "module": _rc("    return adminOrdering"),
        "refinement": "returning the configured ordering verbatim collapses an "
                      "EMPTY configured ordering to 'no ordering at all', "
                      "clearing the collection's intrinsic default at the "
                      "value-restricted site — the same empty-case defect the "
                      "change corrects, now at the restricted call site. Its "
                      "faithful counterpart FAILS the F2P test that queries the "
                      "value-restricted filter with no configured ordering and "
                      "requires the Meta default order. It would NOT resolve.",
        "rationale": "REJECT from `out = effectiveOrdering defaultOrdering "
                     "adminOrdering` (restrictedChoices) on the EMPTY case: with "
                     "an empty configured ordering the post-image demands the "
                     "default, but the rival returns the empty ordering. Refuted "
                     "at an EMPTY configured ordering with a non-empty default "
                     "(`[\"e\"]`), varying the default binder against the "
                     "drops-admin rival. If it verified => SPEC-TOO-WEAK (the "
                     "empty-case clause is unenforced at the restricted site).",
        "witness": _wit("restrictedChoices",
                        'restrictedChoicesTester ["e"] ([] : List String)'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals; AXIOM_TESTS = 4 axiom-lane
# probes) over TWO byte-identical functions, each contracting a READ-ONLY base
# sequence and ordering sequence under fractional heap permission, with the
# reorder/materialization callee axiomatized. This bundle models the same fix as
# the pure ordering-selection KERNEL it introduces (`effectiveOrdering`) surfaced
# at two call sites (`orderedChoices` = the shared selection kernel;
# `restrictedChoices` = the value-restricted site routing through it). The
# decision surface — empty request preserves the default, non-empty request
# governs — carries across intact; the permission surface and the axiomatized
# callee do NOT exist here (the callee that materializes the selected ordering
# is an unchanged shared continuation, neither consumed nor deep-modeled;
# mapping.md §3), and this bundle instead models a SECOND call site the nagini
# sibling folds into its two identical functions.
#
#   nagini case                  -> here                          disposition
#   -----------------------------------------------------------------------
#   pos-control-explicit-else    -> pos-explicit-else             PORTED
#   pos-control-single-return    -> pos-match-shape               RE-SHAPED
#   admiss-self-call             -> admiss-nondegenerate          RE-AIMED
#   frame-mutate-base            -> (none)                        VACUOUS
#   frame-mutate-ordering        -> (none)                        VACUOUS
#   rival-prepatch-unconditional -> rival-prepatch                PORTED
#   rival-invert-guard           -> rival-invert                  PORTED
#   rival-partial-domain-len1    -> rival-partial-len1            PORTED
#   rival-drop-reorder           -> rival-always-default          PORTED
#   (no nagini)                  -> pos-restricted-inline         ADDED (2nd site
#                                                                  positive)
#   (no nagini)                  -> rival-restricted-drops-admin  ADDED (2nd site
#                                                                  attack)
#   (no nagini)                  -> rival-restricted-uncond       ADDED (2nd site
#                                                                  empty-case)
#   (no nagini)                  -> rival-default-first-key-only  ADDED (audit:
#                                                                  multi-key
#                                                                  default)
#   AXIOM_TESTS (4)              -> (dropped)                     G-AX's lane
#
# 5 ported, 1 re-shaped, 1 re-aimed, 2 vacuous; 3 second-site cases added, plus
# 1 audit-added rival (rival-default-first-key-only, the multi-key-default point)
# (1 positive + 2 rivals) because this bundle models the value-restricted call
# site as its own obligation, which the nagini sibling does not separate out.
#
# VACUOUS (frame-mutate-base / frame-mutate-ordering): the nagini sibling's
#   MANDATORY frame-mutation rivals keep the gold body verbatim then store back
#   into a read-only sequence input granted only at half permission, and must be
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: every parameter is an immutable value, neither method declares a
#   `mut` binder over an input, there is no heap, no aliasing, no permission
#   system. There is no read-only input to overwrite and nothing to trip, so the
#   class is vacuous. No substitute is fabricated.
# RE-AIMED (admiss-self-call -> admiss-nondegenerate): the nagini admissibility
#   control self-calls on F2P-shaped inputs to show the half-permission
#   precondition is establishable. This backend's methods have NO precondition
#   and no permission surface, so that probe is degenerate (every input is
#   in-domain). It is re-aimed at the residual total-domain risk — that the
#   kernel is DEGENERATE (never actually forks) — via an in-region assert that an
#   empty request preserves the default AND a non-empty request overrides it.
# RE-SHAPED (pos-control-single-return -> pos-match-shape): the nagini positive
#   computes into a single `out` local and returns once. This backend's frozen
#   impl already uses a mutable-staging shape; the structurally-different correct
#   reshape carried here is the emptiness pattern-match (`[]` vs `_`), a distinct
#   code shape over the same selection.
# PORTED (5): the two positives' spirit and the four decision rivals carry across
#   intact — the carrier changes from a returned list under fractional permission
#   to a returned `List String` value. rival-prepatch-unconditional (the
#   pre-patch unconditional reorder) becomes rival-prepatch (return the request
#   unconditionally), rejected on the empty case. rival-invert-guard becomes
#   rival-invert. rival-partial-domain-len1 becomes rival-partial-len1.
#   rival-drop-reorder (non-empty branch returns base order) becomes
#   rival-always-default. Each carries its nagini refinement argument.
# ADDED (3, no nagini counterpart): this bundle contracts the value-restricted
#   call site (`restrictedChoices`) as an independent obligation the nagini
#   sibling does not separate. pos-restricted-inline defends it (inline the
#   selection vs delegating to the kernel). rival-restricted-drops-admin attacks
#   the ROUTING clause (discard the configured ordering, pass empty to the
#   kernel). rival-restricted-uncond attacks the empty-case at that site (apply
#   the configured ordering unconditionally). All three have machine-checked
#   witnesses, not fabricated wrongness.
# AXIOM_TESTS dropped: the nagini sibling axiomatizes the reorder/materialization
#   callee and probes it against the real library routine. This bundle declares
#   NO axiom (the materialization is an unchanged shared continuation, neither
#   consumed nor modeled; mapping.md §3),
#   so there is no axiom-soundness obligation to probe. G-AX is skipped for this
#   bundle (no axiom_check.py), and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE / POINT COVERAGE.
#   orderedChoices(defaultOrdering, requested): 5 reject witnesses at 5 distinct
#     points. defaultOrdering varied [\"a\"]/[\"x\"]/[\"d\"]/[\"p\"]/[\"m\",\"n\"];
#     requested varied []/[\"y\"]/[\"a\"]/[\"q\",\"r\"] (empty, single-key,
#     multi-key) — neither binder held fixed. Both top-level cases of the
#     selection attacked: the empty case (rival-prepatch /
#     rival-default-first-key-only) and the non-empty override case
#     (rival-invert / rival-partial-len1 / rival-always-default), the last two
#     separating the single-key vs multi-key sub-domains.
#     NOTE on the defaultOrdering binder: the four request-side rivals are each
#     refuted at a SINGLE-key default, so their variation of defaultOrdering is
#     four SPELLINGS of one point (length 1) rather than four sub-domains. The
#     empty-case clause demands the default back VERBATIM, and a rival that
#     preserves only a PREFIX of it is therefore invisible to all of them.
#     rival-default-first-key-only closes that: it varies defaultOrdering by
#     LENGTH (a two-key default), the one point at which a prefix-truncating
#     fallback is observably wrong. Added by adversarial audit, which built the
#     rival and confirmed the gap with the real verifier before landing it.
#   restrictedChoices(defaultOrdering, adminOrdering): 2 reject witnesses at 2
#     distinct points. defaultOrdering varied [\"d\"]/[\"e\"]; adminOrdering
#     varied [\"a\"]/[] (non-empty and empty) — neither held fixed. The routing
#     clause (drops-admin) and the empty case (uncond) both attacked.
#   Each obligation is DEFENDED (orderedChoices by pos-explicit-else /
#     pos-match-shape / admiss-nondegenerate; restrictedChoices by
#     pos-restricted-inline) and ATTACKED (>=1 reject each). No reject witness
#     binds a hypothesis, so there is no consistency-probe surface.
AXIOM_TESTS = []
