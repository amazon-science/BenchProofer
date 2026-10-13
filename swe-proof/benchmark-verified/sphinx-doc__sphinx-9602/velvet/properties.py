"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9602 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct literalTypeNodes`` obligation survives with a
byte-identical header) and swaps in a candidate implementation. It is checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a rendered-annotation carrier,
``List DocNode`` where a ``DocNode`` is one of text / cross-reference / punct):

  literalTypeNodes (head : List Char) (values : List LitVal)
      return (out : List DocNode)
    require head = "Literal".toList ∨ head = "typing.Literal".toList
    require values ≠ []
    require values.all okLit
    ensures out = expandLiteral head values

The method builds the inline children rendered for a parametrised type whose
arguments are constant values, on the subdomain this signature uses. TWO input
binders: ``head`` (the parametrised type's name, pinned by the first ``require``
to one of two literals) and ``values`` (a non-empty list of in-domain constant
values — boolean, non-negative integer, or "simple" string, i.e. printable ASCII
excluding the apostrophe and the backslash, per ``okLit``).

``expandLiteral head values`` is a total, fully-unfolded pure ``def`` over the
method's OWN inputs (``wrap head (valSeq DocNode.text reprVal values)``), living
in the ``pure`` region. The ``axioms`` region is EMPTY — there is NO opaque
answer key to echo (spec_guide directive 8: the post-image is grounded in the
actual input carrier, so building the result IS doing the work), and nothing in
the postcondition is stated over an ``opaque`` term. That is why every witness
below can be a plain ``decide`` at literal inputs and none of them needs to
CONDITION on the carrier; consequently no witness binds a hypothesis, so no
joint-satisfiability probe applies.

The single load-bearing ``ensures`` clause decomposes, through the three pure
``def``s it is built from, into six INDEPENDENTLY-ATTACKABLE structural
sub-behaviours of the returned node list. Each reject rival below attacks exactly
one (two of them, ``head-text-constant`` and ``open-frame-wrong-glyph``, were
added by the audit lane, which found the head node's TEXT and the opening frame
node's GLYPH unattacked — see the footer's AUDIT ADDITIONS note):

  * HEAD-KIND  — node 0 is a ``DocNode.xref`` (a navigable cross-reference to the
                 parametrised type itself), NOT inert display text, and it carries
                 the CALLER's ``head`` rather than a constant name;
  * VAL-KIND   — every constant argument's node is a ``DocNode.text`` (PLAIN
                 display text), NEVER a ``DocNode.xref`` — the load-bearing
                 discriminator of the fix: a constant value is not a class, so it
                 must carry no navigable reference;
  * VAL-DELIM  — a string-valued argument's display text carries the source
                 delimiters on BOTH sides (``reprVal (.str s) = '\\'' :: s ++
                 ['\\'']``), so a one-sided delimiter is refuted;
  * VAL-DOMAIN — the delimiters are applied ONLY to a string value: a boolean or
                 integer argument's display text is bare (``True`` / ``False`` /
                 the decimal digits), never delimited;
  * VAL-GLYPH  — the string delimiter is the apostrophe, not some other quote
                 glyph;
  * SEP/FRAME  — the inner nodes are separated by a ``", "`` punctuation node and
                 the whole sequence is framed by ``"["`` … ``"]"`` punctuation
                 nodes — the opening one's GLYPH and the closing one's PRESENCE
                 both pinned.

The discriminating F2P behaviour (tests/test_domain_py.py::
test_parse_annotation_Literal, the single FAIL_TO_PASS) observes both halves at
once: for a two-boolean and a three-value (integer/integer/string) annotation it
asserts the head IS a cross-reference, the brackets and commas ARE punctuation,
and each argument is a PLAIN string — ``"True"``, ``"False"``, ``"0"``, ``"1"``
and ``"'abc'"`` (that last one WITH its apostrophes, and the numerics WITHOUT
any). Every rival below flips exactly one of those observations, which is why
each ``refinement`` can point at the concrete assertion its faithful real
counterpart would fail. ``Solution_prepatch_2.lean`` routes the values through
the cross-reference path (VAL-KIND) and ``Solution_prepatch.lean`` emits a string
value with no delimiters (VAL-DELIM); both fail ``prove_correct`` (G-DIFF), and
the two rivals ``values-as-xref`` / ``string-one-sided-delimiter`` below are the
battery's re-statements of exactly those two pre-images.

ADVERSARIAL READ of the nagini classes on this carrier (case-by-case accounting
in the footer):
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO MANDATORY
    frame rivals (``frame-mutation-write-value``, ``frame-mutation-write-kinds``)
    that write back into a read-only input held at half permission and are
    rejected for INSUFFICIENT PERMISSION even though the written value is
    unchanged. Lean and Velvet are referentially transparent: ``head`` and
    ``values`` are immutable values, this bundle declares no ``mut`` binder, and
    there is no heap, aliasing, or permission system to subvert. There is no
    read-only input to overwrite, so the class is vacuous here. No substitute
    probe is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack, for the reason above (empty
    ``axioms`` region; the post-image is a transparent ``def`` of the inputs).
    The honest cheapest CORRECT impl that inlines those ``def``s directly is
    carried as a POSITIVE control instead, which doubles as evidence the spec is
    not echo-vulnerable: any WRONG node fails the pin.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface: ten rivals against the
    one ``ensures`` clause, covering all six sub-behaviours above.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
    recursion), so there is no control flow here to make diverge: a diverging
    rival cannot be obtained by mutating this body, it has to bring a loop of
    its own. When it does, the semantics refuse it. This bundle sets
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
    REJECTED on the measure's own ``decreasing_1`` goal. Dropping the clause
    rather than faking it is refused even earlier, by the elaborator's own
    check (``Decreasing annotations are required in total correctness
    semantics``). So divergence neither applies to this impl nor discharges the
    ``ensures`` clauses vacuously if a rival introduces it.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is LOOP-FREE (three pure
``def``s composed, no ``while``), so its extracted tester reduces under
``decide`` — the loop-free tester pattern. Every rival is likewise a loop-free
expression (the two that reshape the traversal do so with one front ``match``,
not a loop), so each rival's tester also reduces. Each reject case therefore
carries a machine-checked refutation ``witness``: a Velvet tester statement
``literalTypeNodesTester <head> <values> = false`` at ONE concrete input, checked
in a file whose ``prove_correct`` block has been stripped so no tactic script can
mask the verdict. Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival (exit 0 —
the tester ``decide``s to ``false``, i.e. the rival's output violates the
postcondition there) and FAILS against the frozen solution (exit 1 with "Tactic
`decide` proved that the proposition … is false", i.e. gold's tester is ``true``
at that input). So each rejection is a genuine spec refutation, not the
mechanical ``rfl`` breakage that reshaping any impl produces by default. Every
witness input satisfies all three ``require`` clauses (an in-set head, a non-empty
value list, every value ``okLit``), so none is vacuously excluded by a false
precondition. No witness binds a hypothesis. No banned token
(sorry/admit/native_decide/axiom/opaque).

AXIOM lane: dropped. ``AXIOM_TESTS = []`` — as in the nagini sibling, which also
ships an empty axiom lane (``meta.json axioms == []``: both changed operations
are modeled DEEPLY, with no consumed ``axiom``). The deep-model references are
G-AX's / G-CONF's job (axiom_check.py, conformance_check.py, mapping.md §3), and
the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9602"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the three statements of the frozen impl body, lying
# ---- strictly BETWEEN the method's `-- impl-start` / `-- impl-end` markers (the
# ---- explanatory comment lines above them stay put; they too live inside the
# ---- elided impl region). Every variant replaces exactly this text, so each
# ---- edit lies wholly inside the one impl region and same_spec holds by
# ---- construction (both facts asserted at load by _swap).
_IMPL = (
    "    let inner := valSeq DocNode.text reprVal values\n"
    "    let result := wrap head inner\n"
    "    return result\n"
)

# ---- the frozen proof, verbatim. A correct reshape may retune THIS block (the
# ---- spec view elides it); rivals leave it alone, so the wrong impl leaves the
# ---- postcondition goal unsolved and the rival MODULE fails to build — which is
# ---- what expect="reject" requires. The witness, NOT the module build, is what
# ---- attributes the rejection to the spec.
_PROOF = "prove_correct literalTypeNodes by\n  loom_solve\n  rfl\n"

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for a correct reshape or an
    admissibility probe, whose residual goal set differs from the frozen one).
    The `prove_correct literalTypeNodes` header is preserved verbatim."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `literalTypeNodesTester head values = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. The tester
# ---- short-circuits to `true` when a `require` clause is false, so every witness
# ---- below uses an in-set head and a non-empty all-`okLit` value list. Checked
# ---- in a file whose `prove_correct` block is stripped, so no tactic script can
# ---- mask the verdict; the frozen impl and every rival are loop-free, so both
# ---- testers reduce.
def _witness(head, values):
    return ("extract_program_for literalTypeNodes\n"
            "prove_precondition_decidable_for literalTypeNodes\n"
            "prove_postcondition_decidable_for literalTypeNodes\n"
            "derive_tester_for literalTypeNodes\n\n"
            f'example : literalTypeNodesTester {head} {values} = false := by\n'
            "  decide\n")


# ---- a per-value display-text policy spelled out inline, parameterised on the
# ---- string arm. Used by the three rivals that keep the node kinds and the
# ---- framing correct and corrupt ONLY the display text of a value.
def _render_impl(str_arm, bool_true='"True".toList',
                 bool_false='"False".toList', int_arm="(toString n).toList"):
    return ("    let render : LitVal → List Char := fun v =>\n"
            "      match v with\n"
            f"      | .bool true  => {bool_true}\n"
            f"      | .bool false => {bool_false}\n"
            f"      | .int n      => {int_arm}\n"
            f"      | .str s      => {str_arm}\n"
            "    let inner := valSeq DocNode.text render values\n"
            "    let result := wrap head inner\n"
            "    return result\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — INLINE THE FRAMING. A structurally
    # different but CORRECT impl that MUST verify, else SPEC-TOO-STRONG. Instead
    # of calling the framing `def`, it builds the head cross-reference, the
    # opening punctuation, the inner sequence and the closing punctuation
    # DIRECTLY in one expression, and binds no local at all. Same values, no
    # `wrap` call, no `let`. The frozen `loom_solve; rfl` still closes the
    # byte-identical obligation. Verified out-of-band with a real build.
    # Ports the shape of nagini pos-control-rlv-branch-reorder (a correct
    # structural variant of the whole impl body).
    # =====================================================================
    {
        "id": "pos-inline-framing",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    return (DocNode.xref head :: DocNode.punct \"[\".toList ::\n"
            "            (valSeq DocNode.text reprVal values"
            " ++ [DocNode.punct \"]\".toList]))\n"),
        "rationale": (
            "a structurally-different CORRECT impl: inline the framing (head "
            "cross-reference, opening punctuation, inner sequence, closing "
            "punctuation) into ONE expression instead of routing through the "
            "framing `def`, and bind no local. The single `ensures` clause `out = "
            "expandLiteral head values` is grounded in the input binders `head` "
            "and `values` (empty axioms region, no opaque answer key), so this is "
            "definitionally the same node sequence and MUST verify, else "
            "SPEC-TOO-STRONG (over-fit to the frozen call shape). Also the honest "
            "positive control for the no-ungrounded-oracle finding: there is no "
            "answer key to echo, and any WRONG node fails the pin. Ports nagini "
            "pos-control-rlv-branch-reorder."
        ),
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — LOCAL RESTAGING. Stage the closing
    # punctuation into its own local BEFORE the head/bracket prefix, i.e. build
    # the sequence in a different order through different intermediate locals.
    # Identical values, different local structure; the frozen proof closes as-is.
    # Verified out-of-band with a real build. Ports the shape of nagini
    # pos-control-rs-resolve-reorder (a correct restaging of the frozen
    # construction whose per-element result is unchanged).
    # =====================================================================
    {
        "id": "pos-local-restage",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let inner := valSeq DocNode.text reprVal values\n"
            "    let closed := inner ++ [DocNode.punct \"]\".toList]\n"
            "    let result := DocNode.xref head :: DocNode.punct \"[\".toList"
            " :: closed\n"
            "    return result\n"),
        "rationale": (
            "a correct impl with a DIFFERENT local structure: close the inner "
            "sequence with the trailing punctuation into its own local first, then "
            "prefix the head cross-reference and the opening punctuation, instead "
            "of framing in one call. Value flow is unchanged, so the single "
            "`ensures` still discharges and the frozen proof closes as-is. If it "
            "failed => SPEC-TOO-STRONG (over-fit to the exact frozen local-binding "
            "form). Ports nagini pos-control-rs-resolve-reorder."
        ),
    },
    # =====================================================================
    # POSITIVE CONTROL 3 (soundness) — INLINE THE VALUE-DISPLAY POLICY. Replace
    # the display-text `def` with the SAME policy spelled out as an inline
    # `match` on the value shape, and hand that to the traversal. Behaviourally
    # identical, syntactically a different function value, so `loom_solve; rfl`
    # is retuned to `loom_solve; simp [...]`-free `rfl` on the unfolded form —
    # here plain `rfl` still suffices (checked). Verified out-of-band.
    # This is the positive counterpart of the three VAL-* rivals below: they
    # differ from it in exactly one `match` arm, so it proves the rejections come
    # from the arm's VALUE and not from inlining the policy at all.
    # =====================================================================
    {
        "id": "pos-inline-value-policy",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_render_impl("'\\'' :: (s ++ ['\\''])")),
        "rationale": (
            "a correct impl that inlines the per-value display-text policy as a "
            "local `match` on the value shape (bare `True`/`False`, the decimal "
            "digits, the apostrophe-delimited string) instead of calling the pure "
            "`def`, then hands it to the same traversal. Behaviourally identical, "
            "so it MUST verify, else SPEC-TOO-STRONG. Load-bearing as the positive "
            "counterpart of the three VAL-* rivals (one-sided delimiter, delimited "
            "non-string, wrong glyph): each of those differs from THIS impl in "
            "exactly one `match` arm, so their rejections are attributable to the "
            "arm's value and not to inlining the policy."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY 1 — RE-AIMED from nagini admiss-rlv-quote-fact. That case
    # asserted, on the string path, the postcondition's own deep-model fact
    # before returning the gold value, to show the precondition ADMITS a normal
    # string input and pins it to the delimited form. Here the same argument is
    # made with one in-region `assert`: the F2P-shaped string value "abc" is
    # in-domain (`okLit` holds) AND its display text is the apostrophe-delimited
    # `'abc'`. If that could not discharge the precondition would be unusable =>
    # PRECOND-TOO-STRONG. The impl is kept verbatim so the method's own `ensures`
    # discharges too; the proof clears the extra goal per-goal (elided from the
    # spec view). Verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "admiss-string-value-delimited",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (okLit (LitVal.str \"abc\".toList) = true ∧\n"
            "       reprVal (LitVal.str \"abc\".toList) = \"'abc'\".toList))\n"
            + _IMPL,
            "prove_correct literalTypeNodes by\n  loom_solve\n"
            "  all_goals first | rfl | decide\n"),
        "rationale": (
            "the `require values.all okLit` clause ADMITS the F2P-shaped normal "
            "string value \"abc\", AND the post-image is non-degenerate there: its "
            "display text is the apostrophe-delimited `'abc'` (five code points, "
            "the delimiters included). If this in-region assert could not "
            "discharge, the in-domain predicate + the display-text `def` would be "
            "unusable => PRECOND-TOO-STRONG. The impl is kept verbatim so the "
            "method's own `ensures` discharges too. Ports nagini "
            "admiss-rlv-quote-fact."
        ),
    },
    # =====================================================================
    # ADMISSIBILITY 2 — RE-AIMED from nagini admiss-rs-pipeline-fact. That case
    # asserted the EXACT composed postcondition fact before the gold return, to
    # show the precondition admits a normal argument list and that the whole
    # pipeline fact discharges. Here: pin the full six-node post-image at the
    # F2P-shaped two-boolean input — head cross-reference, `[`, plain `True`,
    # `, `, plain `False`, `]` — so the obligation is neither unsatisfiable nor a
    # collapse. Impl verbatim; proof retuned per-goal. Verified out-of-band.
    # =====================================================================
    {
        "id": "admiss-full-post-image",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (expandLiteral \"Literal\".toList"
            " [LitVal.bool true, LitVal.bool false]\n"
            "        = [DocNode.xref \"Literal\".toList,"
            " DocNode.punct \"[\".toList,\n"
            "           DocNode.text \"True\".toList,"
            " DocNode.punct \", \".toList,\n"
            "           DocNode.text \"False\".toList,"
            " DocNode.punct \"]\".toList]))\n"
            + _IMPL,
            "prove_correct literalTypeNodes by\n  loom_solve\n  all_goals rfl\n"),
        "rationale": (
            "the composed postcondition fact itself must discharge at the "
            "F2P-shaped input (in-set head, two boolean values): the post-image is "
            "exactly the six-node sequence [xref head, punct \"[\", text \"True\", "
            "punct \", \", text \"False\", punct \"]\"] — every node kind and text "
            "pinned, the values PLAIN text. So the precondition admits a normal "
            "argument list and the obligation is neither unsatisfiable (else "
            "PRECOND-TOO-STRONG) nor a degenerate collapse. Ports nagini "
            "admiss-rs-pipeline-fact."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. Eight rivals cover all six
    # structural sub-behaviours of the single `ensures` clause. The `head` binder
    # is varied across BOTH admitted literals and the `values` binder across all
    # three value shapes at lengths 1, 2 and 3, so no binder is held at one value
    # by every witness.
    # =====================================================================
    {
        "id": "values-as-xref",
        "kind": "uniqueness",
        "expect": "reject",
        # THE bug of the issue: route every constant argument through the
        # cross-reference path, so each value becomes a navigable reference
        # instead of plain display text. Framing, punctuation and every display
        # TEXT are unchanged — only the value nodes' KIND flips.
        "module": _impl(
            "    let inner := valSeq DocNode.xref reprVal values\n"
            "    let result := wrap head inner\n"
            "    return result\n"),
        "refinement": (
            "this is the pre-image behaviour the issue reports: a constant value "
            "rendered as a navigable class reference rather than as plain display "
            "text, which is exactly what makes a strict build flag the value as a "
            "missing class. The failing test compares each child's NODE CLASS, "
            "asserting the bracketed arguments are plain strings and only the "
            "parametrised type's own name is a reference; a value emitted as a "
            "reference fails that comparison on the very first argument. A faithful "
            "real patch with this behaviour would leave the reported symptom in "
            "place, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the VAL-KIND sub-behaviour of `out = expandLiteral head "
            "values`: the traversal is pinned to build each value node with "
            "`DocNode.text`, but the rival builds them with `DocNode.xref`. Every "
            "display text and all punctuation still match, so only the value nodes' "
            "kind flag diverges — the inert-vs-navigable distinction a text-only "
            "proxy would miss, and the load-bearing discriminator of the fix. "
            "Refuted at head=\"Literal\", values=[bool true, bool false] (the F2P's "
            "first annotation). If it verified => SPEC-TOO-WEAK (the spec would "
            "admit the reported bug). Re-states Solution_prepatch_2.lean."
        ),
        "witness": _witness('"Literal".toList',
                            "[LitVal.bool true, LitVal.bool false]"),
    },
    {
        "id": "first-value-only-plain",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS of the rival above: the FIRST argument is emitted as plain
        # text (correctly), and only the remaining ones become cross-references.
        # It therefore agrees with gold on every single-value annotation and
        # diverges only from the second argument on — a sub-domain the
        # values-as-xref witness does not reach, so it gets its own input.
        "module": _impl(
            "    let inner := match values with\n"
            "      | []      => []\n"
            "      | [v]     => [DocNode.text (reprVal v)]\n"
            "      | v :: vs => DocNode.text (reprVal v) ::"
            " DocNode.punct \", \".toList ::\n"
            "                   valSeq DocNode.xref reprVal vs\n"
            "    let result := wrap head inner\n"
            "    return result\n"),
        "refinement": (
            "a faithful real patch that treated only the FIRST bracketed argument "
            "as plain display text and left the rest on the cross-reference path "
            "would still emit references for every argument after the first — so a "
            "strict build keeps flagging those values as missing classes, and the "
            "failing test's multi-argument annotation (whose second and third "
            "children after the first value must all be plain strings) still fails "
            "the node-class comparison. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the VAL-KIND sub-behaviour, on the TAIL sub-domain: the "
            "post-image pins EVERY value node to `DocNode.text`, but this rival "
            "only does so for the head of `values`. It is a NEAR-MISS of "
            "values-as-xref — it agrees with gold on every single-argument input, "
            "so it needs its OWN witness at a longer list. Refuted at "
            "head=\"typing.Literal\", values=[int 0, int 1, str \"abc\"] (the F2P's "
            "second annotation, three values, and the only witness that probes a "
            "length-3 list). If it verified => SPEC-TOO-WEAK: the spec would pin "
            "only the first argument's kind and a rival mishandling the rest would "
            "pass."
        ),
        "witness": _witness(
            '"typing.Literal".toList',
            '[LitVal.int 0, LitVal.int 1, LitVal.str "abc".toList]'),
    },
    {
        "id": "head-as-inert-text",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-correction in the opposite direction: make the parametrised type's
        # own name inert display text too, so NOTHING in the sequence is
        # navigable. All value nodes and all punctuation stay correct.
        "module": _impl(
            "    let inner := valSeq DocNode.text reprVal values\n"
            "    return (DocNode.text head :: DocNode.punct \"[\".toList ::\n"
            "            (inner ++ [DocNode.punct \"]\".toList]))\n"),
        "refinement": (
            "a faithful real patch that suppressed the reference on the "
            "parametrised type's own name — the plausible over-correction of the "
            "reported symptom, silencing the warning by making nothing navigable — "
            "would lose the type's own cross-reference. The failing test asserts "
            "the FIRST child is a reference node carrying the type name while the "
            "bracketed arguments are plain; an inert first child fails that "
            "assertion, and the surrounding annotation tests that require ordinary "
            "type names to stay navigable would break too. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the HEAD-KIND sub-behaviour: the framing `def` pins node 0 "
            "to `DocNode.xref head` (navigable), but the rival emits "
            "`DocNode.text head`. The head's TEXT still matches and every other "
            "node is untouched, so the rejection isolates node 0's kind — the "
            "opposite error from values-as-xref, and the reason the spec must pin "
            "BOTH kinds rather than 'plain everywhere'. Refuted at "
            "head=\"typing.Literal\", values=[bool true] — the dotted head, so this "
            "witness also moves the `head` binder off the bare literal the "
            "majority of witnesses use. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness('"typing.Literal".toList', "[LitVal.bool true]"),
    },
    {
        "id": "string-one-sided-delimiter",
        "kind": "uniqueness",
        "expect": "reject",
        # The display text of a string value carries only its LEADING delimiter.
        # Correct on every non-string value; diverges on every string.
        "module": _impl(_render_impl("'\\'' :: s")),
        "refinement": (
            "the source form of a short printable-ASCII string carries the "
            "apostrophe on BOTH sides. A faithful real patch emitting only the "
            "leading one would render the string argument one code point short; the "
            "failing test pins that child's text to the exactly-five-character "
            "delimited form, so a one-sided rendering fails the string comparison. "
            "It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the VAL-DELIM sub-behaviour: the display-text `def` pins a "
            "string value to `'\\'' :: s ++ ['\\'']` (delimiters on both sides), but "
            "the rival drops the trailing one. Node kinds, punctuation, and every "
            "non-string value are untouched, so the rejection isolates the string "
            "arm's shape. Refuted at head=\"Literal\", values=[str \"abc\"] — the "
            "F2P's string argument, and the only witness at a single string value. "
            "If it verified => SPEC-TOO-WEAK. Ports nagini "
            "partial-domain-rlv-one-sided-quote; re-states "
            "Solution_prepatch.lean's clause on a narrower sub-domain (that "
            "pre-image drops BOTH delimiters)."
        ),
        "witness": _witness('"Literal".toList', '[LitVal.str "abc".toList]'),
    },
    {
        "id": "delimit-non-string-value",
        "kind": "uniqueness",
        "expect": "reject",
        # The canonical over-application of the string-delimiting rule: EVERY
        # value shape gets the delimiters, so a boolean or an integer is rendered
        # as though it were a string. Correct on strings; diverges on all others.
        "module": _impl(_render_impl(
            "'\\'' :: (s ++ ['\\''])",
            bool_true="'\\'' :: (\"True\".toList ++ ['\\''])",
            bool_false="'\\'' :: (\"False\".toList ++ ['\\''])",
            int_arm="'\\'' :: ((toString n).toList ++ ['\\''])")),
        "refinement": (
            "the source form of a boolean or an integer carries NO delimiters — "
            "only a string does. A faithful real patch that applied the delimiting "
            "rule to every constant shape would render a boolean or numeric "
            "argument delimited; the failing test pins those children to the bare "
            "strings (the two booleans and the two single digits, no apostrophes), "
            "so a uniformly-delimited rendering fails every one of those "
            "comparisons. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the VAL-DOMAIN sub-behaviour: the display-text `def` "
            "delimits ONLY the string arm and leaves the boolean and integer arms "
            "bare, but the rival delimits all three. It is the exact converse of "
            "string-one-sided-delimiter (that one under-applies the rule on the "
            "string sub-domain; this one over-applies it off that sub-domain), so it "
            "needs its own non-string witness. Refuted at head=\"Literal\", "
            "values=[int 42] — the only witness at a single integer value, so it is "
            "also what moves the `values` binder onto the integer shape alone. If it "
            "verified => SPEC-TOO-WEAK. Ports nagini "
            "partial-domain-rlv-quote-nonstring."
        ),
        "witness": _witness('"Literal".toList', "[LitVal.int 42]"),
    },
    {
        "id": "wrong-delimiter-glyph",
        "kind": "uniqueness",
        "expect": "reject",
        # A plausible "delimit the string" slip with the WRONG glyph: the double
        # quote instead of the apostrophe. Both sides present, correct arm,
        # correct kinds — only the code point is wrong.
        "module": _impl(_render_impl("'\"' :: (s ++ ['\"'])")),
        "refinement": (
            "the source form of a short printable-ASCII string uses the APOSTROPHE "
            "as its delimiter, not the double quote. A faithful real patch framing "
            "the string argument in double quotes would render a child whose text "
            "differs from the delimited form the failing test pins exactly, so the "
            "string comparison fails on both delimiter positions. It would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the VAL-GLYPH sub-behaviour: the display-text `def` pins "
            "the string delimiter to the apostrophe, but the rival uses the "
            "double-quote code point. The delimiters are present on both sides and "
            "everything else is untouched, so the rejection isolates the glyph — a "
            "near-miss of string-one-sided-delimiter that agrees with gold on "
            "delimiter COUNT and differs only in identity, hence its own witness. "
            "Refuted at head=\"typing.Literal\", values=[str \"x y\"] — an in-domain "
            "string distinct from the F2P's (it contains a space, and `okLit` admits "
            "it), so this witness probes the string sub-domain at a second point. "
            "If it verified => SPEC-TOO-WEAK. Ports nagini "
            "uniqueness-rlv-wrong-quote-glyph."
        ),
        "witness": _witness('"typing.Literal".toList',
                            '[LitVal.str "x y".toList]'),
    },
    {
        "id": "separator-loses-space",
        "kind": "uniqueness",
        "expect": "reject",
        # The punctuation node between the first two arguments drops its trailing
        # space. Every node KIND and every value's display text are correct;
        # correct on any single-argument annotation.
        "module": _impl(
            "    let inner := match values with\n"
            "      | []      => []\n"
            "      | [v]     => [DocNode.text (reprVal v)]\n"
            "      | v :: vs => DocNode.text (reprVal v) ::"
            " DocNode.punct \",\".toList ::\n"
            "                   valSeq DocNode.text reprVal vs\n"
            "    let result := wrap head inner\n"
            "    return result\n"),
        "refinement": (
            "a faithful real patch whose argument separator lost its trailing space "
            "would render the arguments flush against the comma instead of spaced. "
            "The failing test pins each separator child's text to the two code "
            "points comma+space, so a one-character-short separator fails that "
            "comparison. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the SEP/FRAME sub-behaviour, separator half: the traversal "
            "pins the node between adjacent values to `DocNode.punct \", \"`, but "
            "the rival emits `\",\"`. The node's KIND is correct (punct) and every "
            "value node is correct, so the rejection isolates the separator's text. "
            "Refuted at head=\"Literal\", values=[bool false, int 5] — the only "
            "witness at a MIXED two-value list, which is also what makes the "
            "separator observable at all (a single-value input cannot distinguish "
            "this rival from gold). If it verified => SPEC-TOO-WEAK: nothing would "
            "pin the separator's text and a rival mangling it would pass."
        ),
        "witness": _witness('"Literal".toList',
                            "[LitVal.bool false, LitVal.int 5]"),
    },
    {
        "id": "closing-bracket-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # The framing loses its CLOSING punctuation node: the head reference, the
        # opening bracket and every value node are correct, but the sequence is
        # one node short.
        "module": _impl(
            "    let inner := valSeq DocNode.text reprVal values\n"
            "    return (DocNode.xref head :: DocNode.punct \"[\".toList"
            " :: inner)\n"),
        "refinement": (
            "a faithful real patch that appended the arguments but never the "
            "closing punctuation would render an unbalanced annotation. The failing "
            "test asserts the child sequence ends with a punctuation node carrying "
            "the closing bracket, and the assertion is positional over the whole "
            "sequence, so a sequence one node short fails on arity. It would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the SEP/FRAME sub-behaviour, framing half: the framing "
            "`def` appends `DocNode.punct \"]\"` after the inner sequence, but the "
            "rival omits it, so the result's LENGTH is wrong (and its last node is a "
            "value rather than punctuation). Everything else is byte-identical to "
            "gold, so the rejection isolates the closing frame — the structural "
            "clause no value-level rival touches. Refuted at head=\"Literal\", "
            "values=[bool false] — a single FALSE boolean, the one witness at that "
            "value shape. If it verified => SPEC-TOO-WEAK: the postcondition would "
            "not pin the output's arity."
        ),
        "witness": _witness('"Literal".toList', "[LitVal.bool false]"),
    },
    # =====================================================================
    # ADDED BY AUDIT — HEAD-TEXT. The rivals above attack the head node's
    # KIND (head-as-inert-text) but never its TEXT: every one of them passes
    # `head` through unchanged, so a rival that emits the correct node kind
    # carrying a CONSTANT head string was unattacked. That left the `head`
    # binder's variation decorative — both admitted literals appeared in some
    # witness, but no rival's verdict DEPENDED on which one, so the two
    # spellings were two points of the same behaviour rather than a probed
    # sub-domain. This rival's verdict does depend on it: it AGREES with gold
    # wherever head is the bare literal and diverges only on the dotted one
    # (both halves machine-checked out-of-band: the same tester claim FAILS
    # against this rival at head="Literal" and holds at head="typing.Literal").
    # =====================================================================
    {
        "id": "head-text-constant",
        "kind": "uniqueness",
        "expect": "reject",
        # The head node is the right KIND (a cross-reference) but carries a
        # hard-coded name instead of the `head` the caller passed. Every value
        # node, all punctuation and the arity are correct.
        "module": _impl(
            "    let inner := valSeq DocNode.text reprVal values\n"
            "    return (DocNode.xref \"Literal\".toList"
            " :: DocNode.punct \"[\".toList ::\n"
            "            (inner ++ [DocNode.punct \"]\".toList]))\n"),
        "refinement": (
            "a faithful real patch that emitted a constant name for the "
            "parametrised type instead of the one it was handed would render the "
            "dotted spelling of the annotation under the bare name — the "
            "reference would point at, and display, the wrong target. The failing "
            "test parses BOTH spellings and pins the first child's text to the "
            "spelling it passed in, so the dotted annotation's first child fails "
            "the comparison. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the HEAD-KIND sub-behaviour's TEXT half: the framing "
            "`def` pins node 0 to `DocNode.xref head` — the caller's own `head`, "
            "not a constant — but the rival ignores the binder and emits a fixed "
            "name. The node's KIND is correct (xref) and everything else is "
            "byte-identical to gold, so the rejection isolates the head's text. "
            "This is the rival that makes the `head` binder load-bearing: it "
            "AGREES with gold on the whole head=\"Literal\" sub-domain and is "
            "refutable ONLY at the dotted spelling. Refuted at "
            "head=\"typing.Literal\", values=[bool true, str \"abc\"]. If it "
            "verified => SPEC-TOO-WEAK: the postcondition would not tie the head "
            "node to the input."
        ),
        "witness": _witness(
            '"typing.Literal".toList',
            '[LitVal.bool true, LitVal.str "abc".toList]'),
    },
    # =====================================================================
    # ADDED BY AUDIT — OPENING-FRAME GLYPH. closing-bracket-dropped attacks the
    # frame by DELETING its closing node, and separator-loses-space attacks the
    # separator's text, but no rival attacked the text of the OPENING frame
    # node: every rival either kept `DocNode.punct "["` verbatim or removed a
    # node outright. So "the whole sequence is framed by `[` … `]`" was pinned
    # only on the closing side and on arity, never on the opening glyph.
    # =====================================================================
    {
        "id": "open-frame-wrong-glyph",
        "kind": "uniqueness",
        "expect": "reject",
        # The opening frame node is a punctuation node of the right KIND in the
        # right POSITION, carrying the wrong glyph (a parenthesis). Arity, the
        # head node, every value node and the closing frame are correct.
        "module": _impl(
            "    let inner := valSeq DocNode.text reprVal values\n"
            "    return (DocNode.xref head :: DocNode.punct \"(\".toList ::\n"
            "            (inner ++ [DocNode.punct \"]\".toList]))\n"),
        "refinement": (
            "a faithful real patch that opened the argument list with a "
            "parenthesis while closing it with a bracket would render a "
            "mismatched annotation — the subscript would not read as a subscript "
            "at all. The failing test pins the second child to a punctuation node "
            "carrying exactly the opening bracket, so that comparison fails. It "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from the SEP/FRAME sub-behaviour, OPENING-frame half: the "
            "framing `def` pins node 1 to `DocNode.punct \"[\"`, but the rival "
            "emits a parenthesis. The node's kind and position are correct and "
            "the arity is correct — the two other frame rivals get one of those "
            "wrong instead — so the rejection isolates the opening glyph. Refuted "
            "at head=\"Literal\", values=[bool true]. If it verified => "
            "SPEC-TOO-WEAK: the frame would be pinned only on its closing side."
        ),
        "witness": _witness('"Literal".toList', "[LitVal.bool true]"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING. The nagini sibling has 11 SPEC cases (2 soundness
# positives, 2 admissibility, 7 uniqueness rivals) plus an EMPTY axiom lane. It
# contracts TWO functions over a code-point / node-kind carrier (`List[int]`):
# a per-constant renderer, and a two-loop wrap-then-resolve pipeline over a body
# node-kind list. This velvet bundle contracts ONE method, `literalTypeNodes`,
# over the richer `List DocNode` carrier — which COLLAPSES that split: the
# per-constant display text is the pure `reprVal` and the wrap-then-resolve
# pipeline is subsumed by "each value node is `DocNode.text`, the head is
# `DocNode.xref`", both inside the single `ensures out = expandLiteral head
# values`. So the nagini pipeline rivals do not disappear — they RE-AIM onto the
# node-kind sub-behaviours of that one clause.
#
#   nagini case                          -> here                     disposition
#   -------------------------------------------------------------------------
#   pos-control-rlv-branch-reorder       -> pos-inline-framing       PORTED
#   pos-control-rs-resolve-reorder       -> pos-local-restage        PORTED
#   admiss-rlv-quote-fact                -> admiss-string-value-delimited  PORTED
#   admiss-rs-pipeline-fact              -> admiss-full-post-image    PORTED
#   frame-mutation-write-value  (W1)     -> (none)                    VACUOUS
#   frame-mutation-write-kinds  (W2)     -> (none)                    VACUOUS
#   partial-domain-never-wrap   (W3)     -> values-as-xref            PORTED (re-aimed)
#   partial-domain-lit-to-xref  (W4)     -> first-value-only-plain    PORTED (re-aimed)
#   partial-domain-name-not-xref(W5)     -> head-as-inert-text        PORTED (re-aimed)
#   partial-domain-rlv-one-sided-quote(W6)-> string-one-sided-delimiter PORTED
#   partial-domain-rlv-quote-nonstring(W7)-> delimit-non-string-value  PORTED
#   uniqueness-rlv-wrong-quote-glyph(W8) -> wrong-delimiter-glyph     PORTED
#   (no nagini counterpart)              -> pos-inline-value-policy   ADDED
#   (no nagini counterpart)              -> separator-loses-space     ADDED
#   (no nagini counterpart)              -> closing-bracket-dropped   ADDED
#   (no nagini counterpart)              -> head-text-constant        ADDED (audit)
#   (no nagini counterpart)              -> open-frame-wrong-glyph    ADDED (audit)
#   AXIOM_TESTS (empty in nagini too)    -> (none)                    DROPPED
#
# 15 velvet SPEC cases: 3 soundness, 2 admissibility, 10 uniqueness. Every nagini
# case that attacks a clause THIS bundle models is ported; the only omissions are
# the two frame rivals, and they are vacuous rather than hard.
#
# AUDIT ADDITIONS (head-text-constant, open-frame-wrong-glyph): found by the
#   independent audit lane, which wrote NEW wrong impls aimed at whatever the
#   ported rivals left unattacked and checked whether the frozen spec caught
#   them. Both are caught — the spec is not weak here — but neither was
#   DEMONSTRATED to be caught by any shipped case, and the footer claimed the
#   head node and the bracket frame were covered when only the head's KIND and
#   the frame's CLOSING half were. Each carries its own discriminating witness
#   (rival elaborates, gold refuted by `decide`); head-text-constant additionally
#   fixes a decorative binder, being the only rival whose verdict depends on
#   WHICH admitted head literal is passed.
#
# PORTED (positives): nagini's two positives are both correct STRUCTURAL variants
#   (reorder the two top-level branches of the renderer; reorder the two disjoint
#   arms of the resolve decision). Neither branch structure exists here — this
#   method has no conditional at all — so they are carried across as the two
#   correct structural variants that DO exist on this carrier: inline the framing
#   into one expression (pos-inline-framing), and restage the construction through
#   different intermediate locals (pos-local-restage). A THIRD positive was ADDED
#   with no nagini counterpart, pos-inline-value-policy: three of the ten rivals
#   corrupt one arm of an inlined display-text `match`, and without a correct
#   inlined-policy control their rejections could in principle be blamed on
#   inlining rather than on the arm. All three verified out-of-band with real
#   builds (the frozen `loom_solve; rfl` closes each unchanged).
# PORTED (admissibility): both nagini admissibility cases assert the
#   postcondition's own fact in-region before returning the gold value, to show
#   the precondition is USABLE. Carried across directly: one pins the F2P-shaped
#   string value as in-domain with its delimited display text; the other pins the
#   entire six-node post-image at the F2P-shaped two-boolean input. Both keep the
#   impl verbatim and retune only the elided proof body (per-goal `rfl`/`decide`),
#   so the `prove_correct literalTypeNodes` header is byte-identical. Verified
#   out-of-band.
# PORTED-RE-AIMED (the three pipeline rivals): nagini's W3/W4/W5 all attack the
#   same underlying question on its node-kind carrier — WHICH nodes end up
#   navigable. W3 never wraps, so an enumerated value becomes a reference; W4
#   resolves a wrapped value to a reference instead of plain text (the same
#   observable, introduced one stage later); W5 fails to make a NON-wrapped name a
#   reference, breaking the still-required behaviour for ordinary type names. This
#   bundle has no wrap/resolve staging to attack — the two stages are collapsed
#   into the node CONSTRUCTOR each element is built with — so the three re-aim
#   onto the three distinct kind errors that carrier admits: every value navigable
#   (values-as-xref, = W3/W4's shared observable, and Solution_prepatch_2's
#   behaviour), only the tail navigable (first-value-only-plain, the near-miss that
#   W4's "one stage later" flavour becomes here), and the head NOT navigable
#   (head-as-inert-text, = W5's "ordinary names must stay references" concern).
# PORTED (the three value rivals): W6/W7/W8 attack the per-constant display text
#   and port with only the carrier rewritten (`List[int]` code points -> the
#   `reprVal` arms): one-sided delimiter, delimiters on a non-string, wrong
#   delimiter glyph. Each keeps all node kinds and all punctuation correct, so
#   each isolates one property of the display text.
# ADDED (two rivals with no nagini counterpart): the velvet carrier models
#   structure nagini's does not — the `", "` separator between arguments and the
#   bracket FRAME are real `DocNode.punct` elements of the returned sequence,
#   where nagini's `List[int]` node-kind list has no separator or bracket
#   elements at all. Those are independent top-level components of the post-image,
#   so leaving them unattacked would leave part of the modeled surface untested:
#   separator-loses-space and closing-bracket-dropped close that gap (the latter
#   is the only rival that gets the output's LENGTH wrong).
# VACUOUS (W1 frame-mutation-write-value, W2 frame-mutation-write-kinds): both
#   nagini rivals write back into an input held at half permission — the SAME
#   value, so the computed output is byte-identical to gold and the rejection is
#   attributable to the write alone. Velvet is referentially transparent: `head`
#   and `values` are immutable values, no `mut` binder is declared, and there is
#   no heap, aliasing, or fractional-permission system. There is no read-only
#   input to overwrite and no permission obligation to violate, so the class is
#   vacuous here. No substitute probe is fabricated (porting map: vacuous).
# DROPPED (AXIOM_TESTS): empty in the nagini sibling too (`meta.json axioms ==
#   []` — both changed operations are modeled deeply, no consumed axiom). The
#   deep-model references are validated out-of-band by G-AX (axiom_check.py: the
#   display-text model over 17 boundary + 20000 fuzz constants; the head-node
#   carrier) and G-CONF (conformance_check.py: the whole model vs the real patched
#   callee on 100007 inputs, seed 9602). The G-PBT gate ignores AXIOM_TESTS
#   regardless.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
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
#   REJECTED on the measure's own ``decreasing_1`` goal. Dropping the clause
#   rather than faking it is refused even earlier, by the elaborator's own
#   check (``Decreasing annotations are required in total correctness
#   semantics``). So divergence neither applies to this impl nor discharges the
#   ``ensures`` clauses vacuously if a rival introduces it.
#
# CLAUSE / BINDER / POINT COVERAGE. The single load-bearing `ensures` clause is
#   attacked on ALL SIX of its structural sub-behaviours — HEAD-KIND
#   (head-as-inert-text for the kind, head-text-constant for the text), VAL-KIND
#   (values-as-xref and its tail near-miss first-value-only-plain), VAL-DELIM
#   (string-one-sided-delimiter), VAL-DOMAIN (delimit-non-string-value),
#   VAL-GLYPH (wrong-delimiter-glyph), SEP/FRAME (separator-loses-space for the
#   separator's text, open-frame-wrong-glyph for the opening glyph,
#   closing-bracket-dropped for the closing node's presence and the arity) — so
#   no top-level component of the post-image (head node kind AND text, value
#   nodes, their display texts, separators, both frame nodes, the output's arity)
#   is left unattacked. The head-TEXT and opening-GLYPH components were the two
#   the port left uncovered while claiming otherwise; both are now attacked by a
#   rival with its own machine-checked witness.
#   BINDER `head`: varied across BOTH admitted literals — "Literal" (6 witnesses)
#   and "typing.Literal" (4: first-value-only-plain, head-as-inert-text,
#   wrong-delimiter-glyph, head-text-constant). It is pinned by the precondition
#   to exactly those two, so this is total coverage of its admitted domain. Two
#   rivals attack the head's own node directly — head-as-inert-text its KIND and
#   head-text-constant its TEXT — so the binder is both varied and abused.
#   The variation is MEANINGFUL rather than two spellings of one point only
#   because of head-text-constant: it is the one rival whose verdict DEPENDS on
#   which literal is passed (it agrees with gold on the entire head="Literal"
#   sub-domain and is refutable only at the dotted spelling). Every other rival
#   is refutable at either head, so before that rival was added the two spellings
#   probed the same behaviour twice — the audit lane's finding, not the port's
#   claim.
#   BINDER `values`: varied across all three value shapes and three lengths —
#   [bool true, bool false] (len 2), [int 0, int 1, str "abc"] (len 3),
#   [bool true] (1), [str "abc"] (1), [int 42] (1), [str "x y"] (1),
#   [bool false, int 5] (mixed, len 2), [bool false] (1),
#   [bool true, str "abc"] (mixed, len 2). Every constructor of
#   `LitVal` is exercised, both boolean values appear, and both the singleton
#   short-circuit arm and the multi-element arm of the traversal are probed —
#   which matters because the separator and tail-kind sub-behaviours are
#   UNOBSERVABLE at length 1.
#   pts = 10 distinct (head, values) input points, one per rival; no two rivals
#   share a witness, so every rival's claimed sub-domain is demonstrated at an
#   input where it actually diverges. The two near-misses (first-value-only-plain
#   agrees with gold on every singleton; wrong-delimiter-glyph agrees with
#   string-one-sided-delimiter on delimiter count) each get their own
#   discriminating point rather than reusing a broader rival's.
#
# WITNESS MECHANICS: the frozen impl and all ten rivals are loop-free, so the
#   `derive_tester_for literalTypeNodes` + `decide` path is LIVE (both testers
#   reduce; the two rivals that reshape the traversal use one front `match`, not a
#   loop). Every witness states `literalTypeNodesTester <head> <values> = false`,
#   checked in a file whose `prove_correct` block is stripped so no tactic script
#   masks the verdict. All ten checked out-of-band with scripts/lean_verify.sh:
#   the RIVAL build elaborates (exit 0 — the tester decides to `false`) and the
#   GOLD build fails (exit 1, "Tactic `decide` proved that the proposition … is
#   false", i.e. gold's tester is `true` there). Since the postcondition is stated
#   over transparent `def`s of the inputs and never over an `opaque` term, no
#   witness needs to CONDITION on the carrier; none binds a hypothesis, so
#   `consistency_probe` is a no-op and the `witness-inconsistent` failure mode
#   cannot arise. No banned token appears in any witness.
AXIOM_TESTS = []
