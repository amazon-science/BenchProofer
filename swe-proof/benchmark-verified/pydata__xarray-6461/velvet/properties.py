"""properties.py — G-PBT falsification battery for pydata__xarray-6461 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the single ``-- impl-start`` /
``-- impl-end`` region, which the consumer spec view elides, is changed — so
``markers.same_spec`` holds and the ``prove_correct attrsToKeep`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method, ``attrsToKeep``):

  attrsToKeep (present : List Int) (xAttrs : Int) (xPos : Int) return (out : Int)
    require xPos = -1 ∨ (0 ≤ xPos ∧ xPos < present.length)
    require ∀ k : Nat, (xPos = (k : Int) ∧ k < present.length) → present[k]! = xAttrs
    require xPos = -1 → xAttrs = 0
    ensures out = xAttrs                                   <-- LOAD-BEARING

A conditional-selection routine must preserve the attribute mapping that BELONGS
TO its second positional argument. Mappings are opaque ``Int`` identities (the
empty mapping — also what a bare scalar carries — is ``0``). ``present`` is the
list of identities of exactly the arguments that carry a mapping, in order;
``xAttrs`` is the second argument's OWN mapping identity; ``xPos`` locates it in
``present`` (``-1`` when the second argument is a scalar, so absent from the
list). The lone postcondition pins the result to ``xAttrs`` — the second
argument's own mapping — regardless of where (or whether) it sits in ``present``.

GROUNDED, NOT AN ORACLE ECHO. ``out = xAttrs`` is pinned directly to an INPUT
BINDER (``xAttrs``), fully unfolded — there is no opaque answer key to echo, and
the cheapest honest impl IS ``return xAttrs``. The ungrounded-oracle echo class
is therefore N/A; the positive control is a branch reshape that stays correct.

BINDER COVERAGE. The three inputs ``present`` / ``xAttrs`` / ``xPos`` are the
only binders of the spec predicate, and the three reject witnesses move all of
them: ``xPos`` ranges over ``-1`` (scalar), ``0`` and ``1`` (in-list, distinct
positions); ``xAttrs`` over ``0`` and a nonzero identity; ``present`` over lists
of length 1 and 2 with differing contents. So no rival mishandles a binder every
witness holds fixed. The single postcondition clause is attacked by every reject
rival and defended by both ``expect:"verify"`` cases.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling attacks a
    read-only input held at a fractional heap permission by WRITING back into it.
    Lean and Velvet are referentially transparent: every parameter is an
    immutable value (this bundle declares no ``mut`` binder), there is no heap
    and no aliasing, so there is no read-only input to overwrite and no
    substitute probe to build. Reported as an omission, not fabricated.
  * PARTIAL-DOMAIN / VALUE — APPLIES. The sibling's bounds-guarded and unguarded
    constant-offset rivals MERGE here: Lean list indexing is TOTAL (an
    out-of-range read yields the default identity ``0``, never a raise), so the
    "raise face" of the sibling bug has no counterpart on this carrier and the
    two sibling rivals collapse to one wrong-VALUE rival. Two further
    partial-domain rivals (a different constant offset; a constant scalar-marker
    return) round out the binder coverage.
  * UNGROUNDED-ORACLE ECHO — N/A (see above): the post-image is a total function
    of an input binder, with no opaque answer key to echo.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-6461"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the ONE impl-region anchor. It lies wholly inside the impl region and is
# ---- unique in Solution.lean; both facts are asserted at load by _swap. The
# ---- proof body is `loom_solve`, which discharges every candidate below with no
# ---- retuning, so no proof-body swap is needed. ----
_IMPL_GOLD = "    -- impl-start\n    return xAttrs\n    -- impl-end"
assert _IMPL_GOLD in _BASE, "impl anchor drift: gold impl region not verbatim"
assert _BASE.count(_IMPL_GOLD) == 1, "impl anchor not unique"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `attrsToKeepTester present xAttrs xPos = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input (the tester also checks the precondition holds there, else it
# ---- returns `true` vacuously — every witness point below satisfies all three
# ---- `require` clauses). Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can mask the verdict.
_TESTER = ("extract_program_for attrsToKeep\n"
           "prove_precondition_decidable_for attrsToKeep\n"
           "prove_postcondition_decidable_for attrsToKeep\n"
           "derive_tester_for attrsToKeep\n\n")


SPEC_TESTS = [
    # =====================================================================
    # (1) POSITIVE CONTROL (soundness) — structurally different but CORRECT.
    # Branch on `xPos` and route through a typed local `keep`; BOTH branches
    # return the same value `xAttrs`. Point-wise over immutable values, so no
    # induction: `loom_solve` closes it unchanged. If a faithful correct impl
    # could NOT verify => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-branch-typed-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    -- impl-start\n"
            "    let keep : Int := xAttrs\n"
            "    if xPos = -1 then\n"
            "      return keep\n"
            "    else\n"
            "      return keep\n"
            "    -- impl-end"),
        "rationale": "Structurally different but correct: branch on `xPos` and "
                     "route through a typed local `keep`; both branches return "
                     "`xAttrs`, so `out = xAttrs` holds on every input. No "
                     "loop / fold. Must verify, else SPEC-TOO-STRONG (a faithful "
                     "correct impl rejected). Defends the lone postcondition.",
    },

    # =====================================================================
    # (2) ADMISSIBILITY — the preconditions admit BOTH F2P-shaped configs and
    # are usable (non-vacuous). On the in-list branch this impl reads the entry
    # at `xPos` and returns it; verification succeeds ONLY because the structural
    # precondition `∀ k, (xPos = k ∧ k < len) → present[k]! = xAttrs` forces that
    # entry to equal `xAttrs`. On the scalar branch (`xPos = -1`) it returns
    # `xAttrs` directly. If that require clause were vacuous / unsatisfiable at
    # the interesting point the impl could not discharge `present[xPos]! = xAttrs`
    # and it would reject => PRECOND-TOO-STRONG / degenerate precondition.
    # Exercises both configurations the spec must admit.
    # =====================================================================
    {
        "id": "admiss-reads-present-both-configs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    -- impl-start\n"
            "    if xPos = -1 then\n"
            "      return xAttrs\n"
            "    else\n"
            "      return present[xPos.toNat]!\n"
            "    -- impl-end"),
        "rationale": "Reads the in-list entry at `xPos` on the non-scalar branch "
                     "and returns `xAttrs` on the scalar branch. It verifies only "
                     "by CONSUMING the structural require clause "
                     "(`present[xPos]! = xAttrs` in range) and the scalar require "
                     "clause — so it attests that both are satisfiable and "
                     "load-bearing, covering the in-list and scalar F2P configs. "
                     "If a require clause were vacuous / over-strong the impl "
                     "could not both read `present` and return => "
                     "PRECOND-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS rivals (reject) — wrong impls sharing the frozen spec, each
    # with a machine-checked refutation witness at a concrete input, and the
    # refinement argument that its faithful real counterpart would NOT resolve
    # the failing test.
    # =====================================================================

    # (3) PARTIAL-DOMAIN — constant-offset read. This IS the semantic port of
    # the pre-image bug: preserve the entry at the CONSTANT offset 1 of the
    # present-mappings list rather than the second argument's own mapping.
    # Correct exactly when the second argument's mapping happens to sit at offset
    # 1; WRONG on the sub-domain where it does not — most importantly the scalar
    # second argument (`xPos = -1`, `xAttrs = 0`) when other mapping-carriers
    # make the list length >= 2: it then returns some other argument's mapping,
    # not the empty one. (The sibling's separate guarded/unguarded rivals MERGE
    # here: list indexing is total, so there is no distinct raise face.)
    {
        "id": "weak-constant-offset-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    -- impl-start\n    return present[1]!\n    -- impl-end"),
        "refinement": "a faithful counterpart that preserves whatever mapping "
                      "sits at the fixed offset 1 of the present-mappings list "
                      "preserves the WRONG mapping whenever the second argument's "
                      "own mapping is not at that offset — squarely the reported "
                      "scalar-second-argument scenario, where the second argument "
                      "contributes no entry and the list holds only other "
                      "arguments' mappings. The failing test that pins the kept "
                      "mapping to the empty one for that scenario still observes "
                      "the wrong mapping, so it would NOT resolve.",
        "rationale": "REJECT from `out = xAttrs`: on the scalar sub-domain "
                     "(`xPos = -1`, `xAttrs = 0`) with a length-2 list the impl "
                     "returns the offset-1 entry where the post-image demands the "
                     "empty identity. Refuted at `present = [7,9]`, `xAttrs = 0`, "
                     "`xPos = -1` — the scalar config.",
        "witness": _TESTER +
                   "example : attrsToKeepTester [7, 9] 0 (-1) = false := by\n"
                   "  decide\n",
    },

    # (4) PARTIAL-DOMAIN — a DIFFERENT constant offset (near-miss). Preserve the
    # entry at offset 0. Agrees with the frozen post-image whenever the second
    # argument's mapping sits at offset 0, but diverges when it sits elsewhere.
    # Built to move `xPos` to a non-scalar, non-zero position (1) and `present`
    # to a length-2 list whose two entries differ — the sub-domain the offset-1
    # rival above (refuted on the scalar config) never probes.
    {
        "id": "weak-constant-offset-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    -- impl-start\n    return present[0]!\n    -- impl-end"),
        "refinement": "a counterpart pinned to the leading list entry preserves "
                      "the wrong mapping whenever the second argument's mapping "
                      "is not the first carrier's — e.g. when a mapping-carrying "
                      "argument precedes the second one. The failing test that "
                      "pins the kept mapping to the second argument's own still "
                      "observes the leading argument's mapping, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = xAttrs`: with the second argument's "
                     "mapping at offset 1 (`xPos = 1`) and a distinct leading "
                     "entry the impl returns offset 0 where the post-image "
                     "demands `xAttrs`. Refuted at `present = [3,5]`, "
                     "`xAttrs = 5`, `xPos = 1` — moving `xPos` to 1 and using a "
                     "list whose entries differ, a point no other rival probes.",
        "witness": _TESTER +
                   "example : attrsToKeepTester [3, 5] 5 1 = false := by\n"
                   "  decide\n",
    },

    # (5) PARTIAL-DOMAIN — constant scalar-marker return. Return the empty
    # identity (0) unconditionally, i.e. always behave as if the second argument
    # were a scalar. Correct exactly on the sub-domain where the second argument
    # IS a scalar (`xAttrs = 0`), WRONG whenever it carries a real mapping. Built
    # to move `xAttrs` off 0 while `xPos` sits in range at offset 0 — the only
    # rival here refuted at a NONZERO own-mapping.
    {
        "id": "weak-constant-empty-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    -- impl-start\n    return 0\n    -- impl-end"),
        "refinement": "a counterpart that always preserves the empty mapping "
                      "drops the second argument's mapping whenever it carries a "
                      "real one, so the failing test that pins the kept mapping "
                      "to a non-empty mapping the second argument owns still "
                      "observes the empty one. It would NOT resolve.",
        "rationale": "REJECT from `out = xAttrs`: at a nonzero own-mapping "
                     "(`xAttrs = 5`) the impl returns the empty identity 0 where "
                     "the post-image demands 5. Refuted at `present = [5]`, "
                     "`xAttrs = 5`, `xPos = 0` — the only witness with a nonzero "
                     "`xAttrs`, so that binder is varied rather than pinned at 0.",
        "witness": _TESTER +
                   "example : attrsToKeepTester [5] 5 0 = false := by\n"
                   "  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 5 cases (1 soundness
# positive, 1 admissibility, 3 uniqueness rivals). This bundle models only the
# purely functional core — a single method with one postcondition — so the port
# narrows accordingly.
#
#   sibling case                              -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-typed-local            -> pos-control-branch-typed-local  PORTED
#   admissibility-readonly-present-both-configs -> admiss-reads-present-both-configs  RE-EXPRESSED
#   frame-mutation-write-present              -> (none)                          OMITTED (vacuous)
#   partial-domain-constant-offset-guarded    -> weak-constant-offset-one        PORTED
#   partial-domain-constant-offset-unguarded-raise -> weak-constant-offset-one   MERGED
#
# PORTED (pos-control): the branch + typed-local reshape carries over directly;
#   both branches return `xAttrs`, `loom_solve` closes it.
# RE-EXPRESSED (admissibility): the sibling re-derives its `Requires` facts as
#   Asserts inside the impl and reaches a normal return. Here the same argument
#   is expressed by an impl that READS `present[xPos]` on the in-list branch —
#   its proof succeeds only by consuming the structural require clause — and
#   returns `xAttrs` on the scalar branch, covering both F2P configs and
#   attesting the preconditions are satisfiable and load-bearing.
# MERGED (unguarded raise face): the sibling's unguarded `present[1]` rival
#   attacks the IndexError face of the bug. Lean list indexing is total (an
#   out-of-range read yields the default identity 0, never a raise), so there is
#   no distinct raise face on this carrier; the wrong-VALUE face is fully
#   carried by weak-constant-offset-one.
# OMITTED (frame-mutation): VACUOUS on this backend. The sibling's rival writes
#   back into a read-only input held at a fractional heap permission. This
#   backend is referentially transparent, has no heap or aliasing, and this
#   bundle declares no `mut` binder — there is no read-only input to overwrite
#   and no discriminating witness could exist. Not fabricated.
#
# ADDED (2, no sibling counterpart) — BINDER-COVERAGE rivals. The sibling's lone
#   partial-domain rival, ported as weak-constant-offset-one, is refuted only on
#   the scalar config (`xPos = -1`, `xAttrs = 0`, a length-2 list). A battery
#   with just that rival would hold `xPos` at -1 and `xAttrs` at 0 across every
#   witness and say nothing about the spec's dependence on the other binder
#   values:
#     weak-constant-offset-zero    — a different constant offset, refuted with
#         the second argument's mapping at offset 1 (`xPos = 1`) and a list whose
#         entries differ. Moves `xPos` to an in-list, non-zero position.
#     weak-constant-empty-marker   — a constant empty-marker return, refuted at a
#         NONZERO own-mapping (`xAttrs = 5`, `xPos = 0`). The only witness that
#         moves `xAttrs` off 0.
#   Together the three reject witnesses probe THREE distinct input points and
#   vary all three binders (`xPos` over -1/0/1, `xAttrs` over 0/nonzero,
#   `present` over differing length-1 and length-2 lists). Each is a real
#   divergence from the post-image with a machine-checked witness (elaborates
#   against the rival, fails against the frozen solution), not a fabricated
#   wrongness.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the `axioms` region is empty), and the gate ignores AXIOM_TESTS anyway.
AXIOM_TESTS = []
