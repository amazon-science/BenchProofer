"""properties.py — G-PBT falsification battery for django__django-14140 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC_TESTS case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct deconstructNode`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method, three input binders):

  deconstructNode (children : List Child) (connector : Connector) (negated : Bool)
      return (out : Except DeconErr Decon)
    ensures out = deconstructed children connector negated   -- THE only clause

with ``deconstructed`` a fully-unfolded ``def`` in the ``pure`` region returning
``Except.ok`` unconditionally. The single clause therefore pins FIVE independent
components of the returned reconstructable form, one per field plus totality:

  * TOTALITY  — decomposition always succeeds (``Except.ok``, never
    ``Except.error``), for EVERY ``children`` including the empty list and
    including a lone child of any of the three observable shapes;
  * ARGS      — ``args = children`` verbatim: every child is positional, in
    order, uniformly in the number of children;
  * PAIRKW    — ``pairKw = none`` always: no child is ever relocated into a
    keyword recording;
  * CONNKW    — ``connKw = some connector`` iff ``connector ≠ Connector.conj``,
    else ``none`` (a grounded relation on the ``connector`` binder);
  * NEGKW     — ``negKw = negated`` (a grounded read of the ``negated`` binder).

``deconstructed`` is GROUNDED in the three inputs (a total ``def`` over them, no
opaque callee anywhere in the carrier); the ``axioms`` region is empty
(``deconstructed`` is a deep A-reference validated == the real node decomposition
by conformance_check.py, NOT a consumed answer key), so there is no wrong echo to
build and the ungrounded-oracle probe is replaced by honest positive controls.
The INPUT BINDERS are exactly ``children``, ``connector``, ``negated``; every one
of the three is VARIED across the reject witnesses below (see the coverage note at
the foot of this file).

THE CARRIER IS FULLY TRANSPARENT AND DECIDABLE. ``Child`` / ``Connector`` /
``DeconErr`` / ``Decon`` all derive ``DecidableEq`` and carry only concrete
payloads, so a witness reaches the ``method`` CONTRACT through Velvet's own
tester machinery (``extract_program_for`` + the two decidability derivations +
``derive_tester_for`` give ``deconstructNodeTester children connector negated``)
and states ``... = false`` at a concrete input, with ``decide`` closing the
residual literal. No opaque leaf, so NO witness binds a hypothesis and there is
no joint-satisfiability obligation for any case here. Both halves of ALL EIGHT
reject cases were rebuilt out-of-band with ``scripts/lean_verify.sh``: each
witness elaborates against its rival (exit 0) and fails on the frozen solution
(exit 1). The gold-side failure is in every case the SEMANTIC one —
``Tactic `decide` proved that the proposition deconstructNodeTester <input> =
false is false`` — i.e. the kernel evaluated the claim and found gold's tester
TRUE at exactly the probed point, so gold satisfies the postcondition there. That
is the discrimination the gate requires, and it is specifically NOT a stuck
reduction, an unknown identifier, a type error or a timeout: none of the eight
needs a ``witness_reference``, and none is at risk of the ``witness-undecided``
failure mode (the frozen impl is loop-free, so no ``Classical.choice`` blocks
``decide``).

ADVERSARIAL READ of the sibling battery's classes on this carrier:

  * PARTIAL-DOMAIN / VALUE — APPLIES; the heart of the port. Each sibling
    partial-domain rival re-expresses directly onto one component of
    ``deconstructed``, plus two ADDED rivals for components this bundle's richer
    carrier exposes and the sibling's carrier could not (TOTALITY, PAIRKW —
    the sibling models a total value computation with no error outcome and no
    keyword-recording field, so its clause (1) folds both into one list
    equality).

  * FRAME / PERMISSION-MUTATION — the REJECTION MECHANISM is vacuous, the
    PROPERTY is not, and it IS expressible here. The sibling carries THREE such
    rivals as its mandatory class (overwrite each of the three inputs, which are
    held read-only at half permission, to satisfy a clause vacuously). Lean and
    Velvet are referentially transparent: ``children``/``connector``/``negated``
    are immutable values, this bundle declares NO ``mut`` binder over any input,
    and there is no heap, no aliasing and no permission system — so nothing here
    is rejected for INSUFFICIENT PERMISSION, and that half of the sibling's class
    genuinely does not port.

    But the property those rivals defend does. What the sibling's write buys is
    that the clause be read against the SUBSTITUTED input rather than the caller's
    — and the carrier's transliteration of "overwrite the input" is to SHADOW the
    binder with a local of the same name and satisfy the clause against the
    shadow. That is expressible, and it is a live hazard rather than a formality:
    the impl region may bind any local it likes, so nothing syntactic stops a
    rival from rebinding ``children`` and reporting the decomposition of the
    shadow. What forbids it is that ``out = deconstructed children connector
    negated`` is anchored to the METHOD's binder, so the residual goal is
    ``children = []`` over the caller's list — unprovable. Shipped below as
    ``frame-shadow-children-binder``, with a witness that discriminates (built
    out-of-band: exit 0 against the rival, exit 1 against the frozen solution,
    which fails by ``decide`` proving the tester TRUE at the probed input).

  * DIVERGENCE / NON-TERMINATION: INAPPLICABLE HERE, and NOT a spec hole. Two
    independent reasons, in order of force. First, the frozen impl contains no
    loop and no recursion at all (``deconstructed`` is a total ``def`` applied
    once), so there is no repetition site a diverging rival could occupy without
    replacing the implementation wholesale rather than perturbing it, and the
    sibling carries no ``diverge-*``/``nonterm-*`` case either, so nothing is
    dropped in the port. Second, and this is what an earlier revision of this
    bullet got backwards: the semantics would refuse such a rival anyway. That
    revision claimed the bundle sets ``loom.semantics.termination "partial"``,
    under which a non-terminating impl satisfies every ``ensures`` clause
    VACUOUSLY and VERIFIES. The frozen file sets ``"total"`` (line 4) and opens
    ``TotalCorrectness`` (line 7), as do all 500 velvet bundles, and under
    ``total`` a postcondition is claimed of ALL runs, so the verifier demands a
    decreasing measure on every loop and discharges its descent. Measured by
    splicing a loop into this file's impl region: one that CARRIES a measure which
    increases (``let mut k : Nat := 0; while true / invariant True / decreasing k
    do k := k + 1``) is REJECTED at exit 1 on the measure's own goal,
    ``case «decreasing_1: k»``, residual ``⊢ k + 1 < k``. So the disposition is
    "no loop to attack, and the semantics would reject one anyway", not "the spec
    admits this". No reject case is shipped, and none is needed.

  * UNGROUNDED-ORACLE ECHO — N/A. ``deconstructed`` is a total ``def`` over the
    method's own three inputs; there is no answer key to echo. Replaced by the
    honest positive controls below.

  * CONTROL-FLOW-EFFECT — N/A, as in the sibling. The operation is a total pure
    value computation; the only non-value outcome the carrier can express (the
    error branch) is already pinned by TOTALITY, which the added
    ``weak-*-unreadable`` rivals attack directly.

AXIOM lane: EMPTY (``meta.json`` declares no consumed ``axiom``; ``deconstructed``
is a deep A-reference validated == the real decomposition by
conformance_check.py — that is G-CONF/G-AX's job, and this gate ignores
``AXIOM_TESTS`` regardless).
"""
from pathlib import Path

INSTANCE = "django__django-14140"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (the method's
# impl body between -- impl-start / -- impl-end, or the prove_correct tactic
# body) and is unique in Solution.lean; both facts are asserted at load by
# _swap. Editing only these keeps markers.same_spec True and the
# `prove_correct deconstructNode` header byte-identical.
# ---------------------------------------------------------------------------

# The frozen impl body, verbatim — everything strictly BETWEEN the method's
# `-- impl-start` / `-- impl-end` (marker lines included).
_IMPL = (
    "    -- impl-start\n"
    "    -- Place every child positionally, uniformly (no single-child special case);\n"
    "    -- record the combinator only when non-default and the negation when present.\n"
    "    let args := children\n"
    "    let mut connKw : Option Connector := none\n"
    "    if connector ≠ Connector.conj then\n"
    "      connKw := some connector\n"
    "    let mut negKw : Bool := false\n"
    "    if negated then\n"
    "      negKw := true\n"
    "    return Except.ok { args := args, pairKw := none, connKw := connKw, negKw := negKw }\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct deconstructNode by\n  loom_solve <;> simp_all [deconstructed]"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `deconstructNodeTester <children> <connector> <negated> = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block is stripped (so no
# ---- tactic script can mask the verdict). The `Except DeconErr Decon` return
# ---- carrier needs a decidable-equality instance for the tester derivation; it
# ---- is DERIVED, not assumed — no `axiom`/`sorry`/`native_decide` is involved,
# ---- and the frozen solution rejects every witness below all the same.
_DEC = "deriving instance DecidableEq for Except\n\n"
_TESTER = (_DEC +
           "extract_program_for deconstructNode\n"
           "prove_precondition_decidable_for deconstructNode\n"
           "prove_postcondition_decidable_for deconstructNode\n"
           "derive_tester_for deconstructNode\n\n")


def _witness(children, connector, negated):
    """A refutation at ONE concrete (children, connector, negated) point.

    No binder is bound (every input is a literal), so `consistency_probe`
    returns None for each of these and there are no assumptions that could be
    jointly unsatisfiable.
    """
    return _TESTER + (
        f"example : deconstructNodeTester {children} {connector} {negated}"
        " = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the single
    # postcondition clause is SPEC-TOO-STRONG. Both keep the decomposition's
    # value identical on every input and reshape only the executable surface;
    # each was built and verified out-of-band.
    #
    # These port the sibling's two positive controls: its `pos-reorder-kwargs`
    # (hoist the two state-marker computations ahead of the positional copy) and
    # its `pos-inline-flags` (drop the temporaries and build the result inline).
    # =====================================================================
    {
        "id": "pos-flags-first",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: compute the two recorded markers BEFORE binding the positional
        # children. Both markers are functions of `connector`/`negated` only and
        # the positional copy is a function of `children` only, so the three are
        # mutually independent and the order between them is behaviourally
        # irrelevant. The impl's statement SHAPE is unchanged (same two guarded
        # mutations, same record literal), so the frozen proof script closes with
        # no retune.
        "module": _impl_reproved(
            "    let mut connKw : Option Connector := none\n"
            "    if connector ≠ Connector.conj then\n"
            "      connKw := some connector\n"
            "    let mut negKw : Bool := false\n"
            "    if negated then\n"
            "      negKw := true\n"
            "    let args := children\n"
            "    return Except.ok { args := args, pairKw := none, connKw := connKw, negKw := negKw }",
            _PROOF),
        "rationale": "structurally different CORRECT reshape: the two recorded "
                     "markers are computed BEFORE the positional copy. The markers "
                     "read only `connector`/`negated` and the copy reads only "
                     "`children`, so the three computations are mutually "
                     "independent and their order cannot change any of the five "
                     "components `out = deconstructed children connector negated` "
                     "pins (TOTALITY / ARGS / PAIRKW / CONNKW / NEGKW). A faithful "
                     "correct reshape MUST verify, else the clause is over-fit to "
                     "the ORDER in which the independent components are computed "
                     "=> SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-inline-match",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop BOTH mutable temporaries. The combinator record becomes an
        # exhaustive `match` on the combinator (the default arm records nothing,
        # the sole non-default arm records that value) instead of an inequality
        # guard on a `mut` local, and the negation is read straight into the
        # record literal. Same value on every input; the proof is retuned by the
        # case split the `match` introduces (the frozen script's `simp_all` cannot
        # see through an unreduced `match` on a variable).
        "module": _impl_reproved(
            "    let connKw : Option Connector :=\n"
            "      match connector with\n"
            "      | Connector.conj => none\n"
            "      | Connector.disj => some Connector.disj\n"
            "    return Except.ok { args := children, pairKw := none,\n"
            "                       connKw := connKw, negKw := negated }",
            "prove_correct deconstructNode by\n"
            "  loom_solve <;> cases connector <;> simp_all [deconstructed]"),
        "rationale": "structurally different CORRECT reshape: both mutable "
                     "temporaries are gone — the combinator record is an "
                     "exhaustive `match` on `connector` (default arm records "
                     "nothing; the sole non-default arm records that value, which "
                     "is exactly the `connector ≠ Connector.conj` relation spelled "
                     "case-wise) and the negation is read directly into the record "
                     "literal. Every component of `deconstructed` is unchanged on "
                     "every input. The obligation is reproven for the new shape by "
                     "the case split the `match` introduces (`cases connector`), "
                     "with the frozen statement byte-identical and no helper lemma. "
                     "A faithful correct reshape MUST verify, else the clause is "
                     "over-fit to the guard-and-mutate FORM => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is empty), so the sibling's `admiss-single-child-node` probe ("the
    # five half-permission accesses are establishable for a lone-child input") is
    # degenerate here: every input is in-domain by construction and there is no
    # permission system to satisfy. What the sibling's case actually DEFENDS,
    # though, ports: that the desired behaviour is live and non-degenerate at the
    # lone-child input shape, which is the shape the failing tests exercise. A
    # spec that happened to be degenerate there (e.g. one whose post-image
    # collapsed the lone-child case) would read like a live one. This case
    # discharges an in-region assert pinning that the post-image places a LONE
    # child positionally and records nothing as a keyword, for BOTH of the lone
    # child shapes that the decomposition could otherwise treat differently (an
    # embedded boolean expression, which has no key/value reading, and a
    # key/value condition pair, which has one). The rest of the impl is verbatim
    # so the method's own obligation still discharges.
    # =====================================================================
    {
        "id": "admiss-lone-child-shapes-live",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `assert\n"
            "      (deconstructed [Child.expr] Connector.conj false =\n"
            "         Except.ok { args := [Child.expr], pairKw := none, connKw := none, negKw := false } ∧\n"
            "       deconstructed [Child.pair \"x\" 1] Connector.conj false =\n"
            "         Except.ok { args := [Child.pair \"x\" 1], pairKw := none, connKw := none, negKw := false }))\n"
            "    let args := children\n"
            "    let mut connKw : Option Connector := none\n"
            "    if connector ≠ Connector.conj then\n"
            "      connKw := some connector\n"
            "    let mut negKw : Bool := false\n"
            "    if negated then\n"
            "      negKw := true\n"
            "    return Except.ok { args := args, pairKw := none, connKw := connKw, negKw := negKw }",
            _PROOF),
        "rationale": "the modeled domain ADMITS the lone-child input shape and the "
                     "post-image is non-degenerate there. The in-region assert "
                     "(elided from the spec view, so same_spec holds) pins that "
                     "`deconstructed` on a ONE-child list SUCCEEDS, places that "
                     "child positionally in `args`, and records nothing as a "
                     "keyword (`pairKw = none`) — for BOTH lone shapes the "
                     "decomposition could otherwise separate: an embedded boolean "
                     "expression (no key/value reading available) and a key/value "
                     "condition pair (one available). The impl is kept verbatim so "
                     "the `ensures` still discharges. If the lone-child input were "
                     "outside the admissible domain, or the post-image collapsed "
                     "it, the assert would not discharge => PRECOND-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete input by a witness that ELABORATES against
    # the rival and FAILS on the frozen solution (both halves built out-of-band),
    # and carries the refinement argument that its faithful real counterpart
    # would NOT resolve the failing tests.
    # =====================================================================

    # ---- ARGS + PAIRKW: relocate a lone readable child into the keyword record.
    # ---- This is the PRE-IMAGE behaviour (= Solution_prepatch.lean, which G-DIFF
    # ---- already confirms the spec senses). Correct on every multi-child node and
    # ---- on a lone nested node; diverges exactly on the lone-child sub-domain.
    {
        "id": "weak-lone-child-as-keyword",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let result : Except DeconErr Decon :=\n"
            "      match children with\n"
            "      | [c] =>\n"
            "        match c with\n"
            "        | .node =>\n"
            "          Except.ok { args := children, pairKw := none,\n"
            "                      connKw := (if connector ≠ Connector.conj then some connector else none),\n"
            "                      negKw := negated }\n"
            "        | .pair k v =>\n"
            "          Except.ok { args := [], pairKw := some (k, v), connKw := none, negKw := negated }\n"
            "        | .expr =>\n"
            "          Except.error DeconErr.notPair\n"
            "      | _ =>\n"
            "        Except.ok { args := children, pairKw := none,\n"
            "                    connKw := (if connector ≠ Connector.conj then some connector else none),\n"
            "                    negKw := negated }\n"
            "    return result"),
        "refinement": "this IS the pre-image behaviour, which special-cases a node "
                      "holding exactly one child that is not itself a nested node: "
                      "the lone child is read as a key/value pair and recorded as a "
                      "keyword instead of positionally. Its faithful real "
                      "counterpart is the unchanged repo. The failing tests now "
                      "assert that a lone child arrives POSITIONALLY with an empty "
                      "keyword record — both for a lone key/value condition and for "
                      "a lone embedded boolean expression, on which the keyword "
                      "reading is not even available and the operation aborts "
                      "instead of returning a form (the abort the issue reports). "
                      "It would NOT resolve — the precise change the spec senses.",
        "rationale": "REJECT from `out = deconstructed children connector negated` "
                     "on TWO components at once (ARGS and PAIRKW): at a lone "
                     "key/value child the post-image demands `args = children` and "
                     "`pairKw = none`, but the rival returns `args = []` with the "
                     "child relocated into `pairKw`. Refuted at "
                     "`([Child.pair \"x\" 1], conj, false)` — a lone readable child, "
                     "the sub-domain where this rival is wrong while it is CORRECT "
                     "on every multi-child input. Varies `children` to a "
                     "single-element pair list.",
        "witness": _witness('[Child.pair "x" 1]', "Connector.conj", "false"),
    },

    # ---- TOTALITY: a lone child with no key/value reading aborts instead of
    # ---- being carried positionally. The near-miss half of the pre-image rival,
    # ---- isolated: it agrees with gold everywhere the rival above disagrees
    # ---- EXCEPT the one shape with no pair reading, so it gets its own witness at
    # ---- that shape (and at the non-default combinator, which the rival above
    # ---- never probes).
    {
        "id": "weak-lone-nonpair-unreadable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let result : Except DeconErr Decon :=\n"
            "      match children with\n"
            "      | [Child.expr] => Except.error DeconErr.notPair\n"
            "      | _ =>\n"
            "        Except.ok { args := children, pairKw := none,\n"
            "                    connKw := (if connector ≠ Connector.conj then some connector else none),\n"
            "                    negKw := negated }\n"
            "    return result"),
        "refinement": "this is the backward-compatible half-measure the issue "
                      "itself floats: keep the lone-child special case but guard it "
                      "so a child with no key/value reading is not forced through "
                      "one — here the guard aborts instead of falling through to "
                      "the positional form. Its faithful real counterpart still "
                      "does not produce a reconstructable form for a node holding a "
                      "lone embedded boolean expression, so the failing tests that "
                      "assert such a node decomposes with that expression as its "
                      "sole positional component (and the one that filters with "
                      "such a node combined against an empty node) still fail. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = deconstructed children connector negated` "
                     "on TOTALITY: the post-image is `Except.ok` for EVERY input, "
                     "but the rival returns `Except.error DeconErr.notPair` at a "
                     "lone child with no key/value reading. Refuted at "
                     "`([Child.expr], disj, false)` — a NEAR-MISS distinguished from "
                     "the pre-image rival above, which it agrees with gold against "
                     "on every readable lone child; this is the one input shape "
                     "where it is wrong. Varies `children` to a single-element "
                     "expression list AND `connector` to its non-default value.",
        "witness": _witness("[Child.expr]", "Connector.disj", "false"),
    },

    # ---- ARGS: off-by-one, drop the final positional child. Correct on the empty
    # ---- node, wrong on every non-empty one.
    {
        "id": "weak-drop-final-child",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    return Except.ok { args := children.dropLast, pairKw := none,\n"
            "                       connKw := (if connector ≠ Connector.conj then some connector else none),\n"
            "                       negKw := negated }"),
        "refinement": "building the positional components from all but the last "
                      "child drops a condition from the reconstructable form. The "
                      "round-trip tests rebuild a node from its decomposition and "
                      "require it to equal the original, and the tests that read "
                      "the positional components of a multi-child node observe all "
                      "of them; a counterpart that lost the final child would "
                      "reconstruct a strictly weaker node. It would NOT resolve.",
        "rationale": "REJECT from `out = deconstructed children connector negated` "
                     "on ARGS: the post-image demands `args = children` verbatim, "
                     "but the rival returns a proper prefix for every non-empty "
                     "input (partial-domain: correct only on the empty node). "
                     "Refuted at `([Child.node, Child.expr], conj, true)`. Varies "
                     "`children` to a TWO-element list of mixed shapes — the only "
                     "witness here that probes a multi-child input, so it is also "
                     "what shows the spec's dependence on `children` beyond length "
                     "one — AND `negated` to true.",
        "witness": _witness("[Child.node, Child.expr]", "Connector.conj", "true"),
    },

    # ---- CONNKW: never record the combinator (constant `none`).
    {
        "id": "weak-combinator-never-recorded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    return Except.ok { args := children, pairKw := none,\n"
            "                       connKw := none, negKw := negated }"),
        "refinement": "never recording the combinator means a node joined by the "
                      "non-default combinator decomposes without it, so rebuilding "
                      "from the decomposition yields a node joined by the DEFAULT "
                      "combinator instead — a different filter. The tests that read "
                      "the recorded combinator of a non-default node, and those "
                      "that round-trip such a node and require equality with the "
                      "original, both fail. It would NOT resolve.",
        "rationale": "REJECT from `out = deconstructed children connector negated` "
                     "on CONNKW: the post-image demands `connKw = some connector` "
                     "whenever `connector ≠ Connector.conj`, which a constant "
                     "`none` cannot satisfy. Refuted at "
                     "`([Child.node], disj, false)` — varies `connector` to its "
                     "non-default value, the sub-domain where this rival is wrong "
                     "while it is CORRECT on every default-combinator input.",
        "witness": _witness("[Child.node]", "Connector.disj", "false"),
    },

    # ---- CONNKW: invert the relation (record iff the combinator IS the default).
    # ---- A supporting near-miss for the same component, wrong on the OPPOSITE
    # ---- sub-domain from the rival above — hence its own witness at the default
    # ---- combinator, which that rival handles correctly.
    {
        "id": "weak-combinator-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    return Except.ok { args := children, pairKw := none,\n"
            "                       connKw := (if connector = Connector.conj then some connector else none),\n"
            "                       negKw := negated }"),
        "refinement": "inverting the recording relation attaches the combinator "
                      "record to DEFAULT nodes and drops it from non-default ones: "
                      "exactly backwards. The tests that observe an empty keyword "
                      "record for a default node and a populated one for a "
                      "non-default node fail in both directions, and the round-trip "
                      "tests rebuild the wrong combinator. It would NOT resolve. "
                      "Supporting near-miss for the combinator component.",
        "rationale": "REJECT from `out = deconstructed children connector negated` "
                     "on CONNKW: `connector = Connector.conj` is the NEGATION of "
                     "the required relation, so the two disagree at every input. "
                     "Refuted at `([Child.node], conj, false)` — the DEFAULT "
                     "combinator, the opposite sub-domain from "
                     "`weak-combinator-never-recorded`, which is correct there; "
                     "sharing a witness between the two would let each claim a "
                     "sub-domain it was never demonstrated on. Varies `connector` "
                     "back to its default value.",
        "witness": _witness("[Child.node]", "Connector.conj", "false"),
    },

    # ---- NEGKW: never record the negation (constant false).
    {
        "id": "weak-negation-never-recorded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    return Except.ok { args := children, pairKw := none,\n"
            "                       connKw := (if connector ≠ Connector.conj then some connector else none),\n"
            "                       negKw := false }"),
        "refinement": "never recording the negation means a negated node "
                      "decomposes as though it were not negated, so rebuilding from "
                      "the decomposition drops the negation and yields the "
                      "complementary filter. The tests that read the recorded "
                      "negation of a negated node, and those that round-trip one "
                      "and require equality with the original, both fail. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = deconstructed children connector negated` "
                     "on NEGKW: the post-image demands `negKw = negated`, which a "
                     "constant `false` cannot satisfy on a negated input. Refuted "
                     "at `([Child.pair \"y\" 2], conj, true)` — varies `negated` to "
                     "true, the sub-domain where this rival is wrong while it is "
                     "CORRECT on every non-negated input, and varies the pair "
                     "child's payload away from the one "
                     "`weak-lone-child-as-keyword` probes.",
        "witness": _witness('[Child.pair "y" 2]', "Connector.conj", "true"),
    },

    # ---- FRAME: satisfy the clause against a SHADOWED input binder. The
    # ---- carrier's transliteration of the sibling's mandatory
    # ---- overwrite-a-read-only-input class (see the docstring): with no heap and
    # ---- no permissions there is nothing to WRITE, but the impl region can
    # ---- rebind `children` to a local and report the decomposition of THAT.
    # ---- Rejected because the clause is anchored to the METHOD's binder, not to
    # ---- whatever `children` names at the return.
    {
        "id": "frame-shadow-children-binder",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let children : List Child := []\n"
            "    return Except.ok { args := children, pairKw := none,\n"
            "                       connKw := (if connector ≠ Connector.conj then some connector else none),\n"
            "                       negKw := negated }"),
        "refinement": "reporting the decomposition of a SUBSTITUTED (here empty) "
                      "child sequence instead of the node's own is not a "
                      "reconstructable form of that node at all: rebuilding from it "
                      "yields a childless node whatever the original held. The tests "
                      "that read the positional components of a node and those that "
                      "rebuild a node from its decomposition and require equality "
                      "with the original both fail on every non-empty node — "
                      "including the lone-child shapes the failing tests exercise. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = deconstructed children connector negated` on "
                     "ARGS, via the FRAME hazard the sibling's read-only-input class "
                     "defends: the rival shadows the input binder `children` with a "
                     "local and satisfies the clause against the SHADOW. It is "
                     "rejected because the post-image is anchored to the METHOD's "
                     "binder — the residual goal is `children = []` over the CALLER's "
                     "list, which is unprovable — so a substituted input cannot "
                     "discharge the clause vacuously. Refuted at "
                     "`([Child.pair \"z\" 3, Child.node], disj, true)`: a multi-child "
                     "node of mixed shapes at the NON-DEFAULT combinator and NEGATED, "
                     "the only witness here that varies all three binders away from "
                     "their default at once, and a distinct input point from all "
                     "seven others.",
        "witness": _witness('[Child.pair "z" 3, Child.node]', "Connector.disj",
                            "true"),
    },

    # ---- TOTALITY at the other end of the `children` domain: abort on a node
    # ---- holding no children at all. Isolates the length-zero input, which no
    # ---- other witness here probes.
    {
        "id": "weak-empty-node-unreadable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let result : Except DeconErr Decon :=\n"
            "      match children with\n"
            "      | [] => Except.error DeconErr.notPair\n"
            "      | _ =>\n"
            "        Except.ok { args := children, pairKw := none,\n"
            "                    connKw := (if connector ≠ Connector.conj then some connector else none),\n"
            "                    negKw := negated }\n"
            "    return result"),
        "refinement": "a node holding no children is decomposed on a live path: "
                      "combining any node with an EMPTY one short-circuits by "
                      "decomposing one of the two operands and rebuilding from the "
                      "result, and when both operands are empty the node decomposed "
                      "is itself empty. A counterpart that failed to produce a form "
                      "for the childless node would abort that short-circuit, "
                      "breaking the currently-passing tests that combine two empty "
                      "nodes and require the result to equal an empty node. "
                      "Resolution requires those to keep passing, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = deconstructed children connector negated` "
                     "on TOTALITY at the length-ZERO input: the post-image is "
                     "`Except.ok` for every input including `[]`, but the rival "
                     "returns `Except.error DeconErr.notPair` there. Refuted at "
                     "`(([] : List Child), conj, false)` — varies `children` to the "
                     "empty list, the one input point no other witness in this "
                     "battery probes, and the one on which `weak-drop-final-child` "
                     "is CORRECT.",
        "witness": _witness("([] : List Child)", "Connector.conj", "false"),
    },
]


# ===========================================================================
# AXIOM lane — EMPTY. meta.json declares `axioms: []`: there is no consumed
# module-level `axiom` in this bundle. The decomposition is modeled DEEPLY in the
# `pure` region (`deconstructed`) as a deep A-reference, validated == the real
# node decomposition out-of-band by conformance_check.py (G-CONF: PASS, 0
# disagreements over 100018 inputs). The spec lane above consumes no axiom
# `ensures`, so there is no axiom-soundness or axiom-containment obligation to
# discharge here — and this gate ignores AXIOM_TESTS regardless (that is G-AX's
# lane, recorded `skip` for this bundle).
# ===========================================================================
AXIOM_TESTS = []


# ===========================================================================
# Sibling -> velvet accounting. The sibling battery has 11 SPEC cases (2
# soundness positives, 1 admissibility, 3 frame-mutation rivals, 5
# partial-domain rivals) plus an EMPTY axiom lane. This bundle models the SAME
# purely-functional core over a RICHER carrier: the sibling abstracts a child to
# an opaque `int` and the outcome to a total value, whereas here a child carries
# its three observable shapes and the outcome carries an error branch and a
# keyword-recording field. So the value rivals port near 1:1, the frame class is
# genuinely vacuous, the admissibility case is REDIRECTED (no precondition to
# admit; the non-degeneracy it defends is what ports), and TWO rivals are ADDED
# for components the sibling's carrier cannot express.
#
#   sibling case                    -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-reorder-kwargs              -> pos-flags-first                PORTED
#   pos-inline-flags                -> pos-inline-match               PORTED
#   admiss-single-child-node        -> admiss-lone-child-shapes-live  REDIRECTED
#   frame-mutate-children           -> frame-shadow-children-binder   REDIRECTED
#   frame-mutate-connector          -> (none)                         VACUOUS
#   frame-mutate-negated            -> (none)                         VACUOUS
#   uniq-single-child-special-case  -> weak-lone-child-as-keyword     PORTED
#   uniq-drop-last                  -> weak-drop-final-child          PORTED
#   uniq-connector-constant-false   -> weak-combinator-never-recorded PORTED
#   uniq-negated-constant-false     -> weak-negation-never-recorded   PORTED
#   uniq-connector-flip             -> weak-combinator-inverted       PORTED
#   (no sibling)                    -> weak-lone-nonpair-unreadable   ADDED
#   (no sibling)                    -> weak-empty-node-unreadable     ADDED
#   (no sibling, see docstring)     -> (none)                         NO LOOP
#   AXIOM_TESTS (0)                 -> (none)                         EMPTY
#
# The two frame rivals recorded VACUOUS above are so recorded for a narrower
# reason than the third, and the distinction is deliberate. Shadowing the
# `connector` binder to the default (`let connector := Connector.conj`) makes the
# guarded record constantly `none`, and shadowing `negated` to false makes the
# negation record constantly false — i.e. each is EXPRESSIBLE, but its value
# behaviour is DEFINITIONALLY EQUAL, on every input, to a rival this battery
# already ships (`weak-combinator-never-recorded` and
# `weak-negation-never-recorded` respectively). Shipping them would add two
# reject cases and zero discrimination, so they are folded rather than
# duplicated. Only the `children` shadow is behaviourally distinct from every
# shipped rival (it substitutes the whole positional sequence), which is why that
# one is carried as its own case.
#
# 7 ported, 2 added, 2 redirected, 2 folded = 11 SPEC cases (2 soundness,
# 1 admissibility, 8 uniqueness).
#
# COVERAGE of the single obligation `out = deconstructed children connector
# negated`. It is DEFENDED by 3 verify cases and ATTACKED by 8 rivals. All five
# independent components of the post-image are attacked:
#
#   TOTALITY -> weak-lone-nonpair-unreadable, weak-empty-node-unreadable
#   ARGS     -> weak-lone-child-as-keyword, weak-drop-final-child,
#               frame-shadow-children-binder
#   PAIRKW   -> weak-lone-child-as-keyword
#   CONNKW   -> weak-combinator-never-recorded, weak-combinator-inverted
#   NEGKW    -> weak-negation-never-recorded
#
# and all THREE input binders are varied by the reject witnesses — the failure
# mode the coverage checker exists to catch is a binder every witness holds at
# one value, so each is listed with the distinct values probed:
#
#   children  -> [] / [pair "x" 1] / [pair "y" 2] / [node] / [expr]
#                / [node, expr] / [pair "z" 3, node]
#                                      (6 shapes: empty, both lone-pair payloads,
#                                       lone node, lone expression, and two
#                                       DISTINCT multi-child sequences)
#   connector -> conj (default) AND disj (non-default)
#   negated   -> false AND true
#
# 8 reject cases at 8 DISTINCT input points (pts=8), so no rival's sub-domain
# claim rests on another's witness. `frame-shadow-children-binder` is the only
# point that moves all three binders off their default simultaneously
# (multi-child, non-default combinator, negated). The two pairs that attack a shared component
# are deliberately split across COMPLEMENTARY sub-domains rather than sharing a
# witness: never-recorded vs inverted are refuted at the non-default and the
# default combinator respectively (each is correct where the other is wrong),
# and lone-child-as-keyword vs lone-nonpair-unreadable at the readable and the
# unreadable lone child respectively.
# ===========================================================================
