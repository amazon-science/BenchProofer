"""properties.py — PBT falsification manifest for django__django-16667 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Every case is built by region surgery on an anchor
that lies entirely INSIDE the implementation region (and, for one positive, the
proof body), so the spec view is byte-identical, `variant_scope.same_spec` holds
by construction, and any rejection is attributable to the postcondition rather
than to a tampered spec.

DEFENDED SURFACE
----------------
The modeled function reduces a tripartite date entry to the single textual value
that is handed on for later field-level parsing:

    implementation_coerceDateEntry
        (c : DateEntry) (rendered y m d : String) : Option String

pinned by a postcondition of THREE independent top-level clauses, one per
outcome of the attempt to read the three components as a calendar date:

    (c = DateEntry.valid           → result = some rendered)
  ∧ (c = DateEntry.malformed       → result = some (pseudoIso y m d))
  ∧ (c = DateEntry.unrepresentable → result = some "0-0-0")

Two facts are pinned in every clause and both are load-bearing:

  * TOTALITY — the outcome is `some …`, i.e. a value IS handed on. `none` (no
    value produced) is forbidden in every case, including the third. That is the
    discriminating half: the pre-change behavior produced no value for an entry
    whose magnitude cannot be accommodated.
  * CONTENT — exactly WHICH text is handed on: the canonical rendering supplied
    for a representable date, the pseudo-ISO fallback assembled from the raw
    components for a well-formed-but-not-a-date entry, and the all-zero sentinel
    `"0-0-0"` for an entry whose magnitude cannot be accommodated.

The carrier is FULLY TRANSPARENT: `DateEntry` is a three-constructor inductive
with `DecidableEq`, `pseudoIso` is a plain `String` helper, and there is no
`opaque` callee anywhere in the spec. So every rival is refutable by `decide` at
concrete string literals — no carrier conditioning is needed, and consequently
no witness below binds a hypothesis (there is nothing that could be
inconsistent).

`pseudoIso` gives clause 2 sub-structure that is worth attacking in its own
right: the per-component zero-fill for an empty component, and the order in
which the three components are joined. See `verbatim-empty-component` and
`reversed-components`.

PORTING NOTES (which nagini cases port, which are omitted and why)
-----------------------------------------------------------------
The nagini sibling contracts `value_from_components(all_blank, all_present,
kind)` — the WHOLE reduction, outer guards included. This bundle models only the
inner classification dispatch (mapping.md: the outer all-blank and
not-all-present guards precede the modeled block and are not part of the modeled
function), so the nagini cases attached to those guards have no counterpart here.
That is carrier narrowing, not a thinner battery.

  * `pos-reorder` -> `pos-if-cascade` — a correct impl whose branch cascade is
    reordered (the unaccommodatable outcome tested FIRST, via `if` guards rather
    than a `match`). Verifies, or the postcondition is over-fit to one branch
    order (SPEC-TOO-STRONG).
  * added `pos-pure-functional` — the same dispatch as a pure functional `def`
    with no imperative do-block. A second correct impl SHAPE, closing with the
    frozen tactic script.
  * added `pos-derived-sentinel` — a correct impl that INLINES the fallback
    assembly and obtains the all-zero sentinel by assembling it from three empty
    components instead of writing the literal. It pins that the spec accepts the
    sentinel however it is PRODUCED (there is no literal-echo requirement), and
    is the one positive whose proof body needed re-closing.
  * `reject-drop-overflow-handler` -> `no-value-unrep` — the pre-change shape:
    the unaccommodatable outcome is left unhandled, so no value is produced. On
    nagini this landed as an escaping-exception violation of an implicit
    no-raise contract; here the `Option` carrier makes it an explicit clause
    violation (`none` where `some "0-0-0"` is pinned), which is a STRONGER and
    more direct attribution.
  * `reject-echo-success-on-kind2` -> `echo-rendered-unrep` — hands on the
    canonical rendering for the unaccommodatable outcome (cross-clause echo).
  * `reject-wrong-sentinel-content` -> `near-miss-sentinel` — a near-miss
    sentinel differing in one character; attacks the exact-content half of
    clause 3 while satisfying totality.
  * `reject-empty-on-kind2` SPLITS IN TWO on this carrier. Nagini modeled text
    as a code-point sequence, so "absent" and "empty text" were the same value
    (the empty sequence). Here `Option String` separates them, so the case ports
    as `no-value-unrep` (no value produced) AND `empty-text-unrep` (a value is
    produced but it is the empty text). Both are shipped.
  * `reject-swap-text-on-kind0` -> `fallback-on-valid` — hands on the pseudo-ISO
    fallback for a representable date; the only rival attacking clause 1.
  * added `echo-fallback-unrep` — hands on the pseudo-ISO fallback for the
    unaccommodatable outcome. This is the near-miss most likely to look right
    (it is the neighboring clause's own grounded text, non-empty and derived
    from the real components), and nagini could not state it as a distinct case
    because its fallback oracle was an abstract non-empty callee.
  * added `verbatim-empty-component` and `reversed-components` — nagini pinned
    the fallback rendering to an abstract `out_of_range_text()` constrained only
    to be non-empty, so the SUB-STRUCTURE of that text was unattackable there.
    Here `pseudoIso` is transparent, so the per-component zero-fill and the
    component ORDER are both attackable, and these two rivals are the only ones
    that move the `y`/`m`/`d` binders in a way clause 2 observes. Without them a
    rival that mishandled only the fallback assembly would verify.
  * `reject-nonempty-not-all-present`, `reject-empty-literal-not-all-present`,
    `reject-nonempty-all-blank` are OMITTED — no counterpart. All three attack
    the OUTER guards (an entirely blank entry yields no value; a partially
    submitted entry echoes the bare raw retrieval). Those guards are unchanged by
    the fix, precede the modeled block, and are not part of this bundle's modeled
    function — there is no clause here for such a rival to violate and no witness
    could discriminate one. Omitted for absence of surface, not for difficulty.
  * `admiss-f2p` PORTS as `admiss-f2p-input` — it is NOT vacuous, and an earlier
    revision of this manifest wrongly recorded it as such on the ground that the
    obligation carries "no precondition hypothesis, so nothing can be
    over-strong". That reasoning is wrong on a TOTAL carrier: the analogue of
    PRECOND-TOO-STRONG here is the obligation being UNSATISFIABLE at exactly an
    F2P-shaped input — a spec whose three clauses could not jointly hold at the
    entry the F2P exercises would be vacuously unprovable there, and no reject
    case detects that (every reject case shows some OTHER impl fails, which is
    equally true of an unsatisfiable clause). The positive discharges the
    obligation at the concrete F2P-shaped input by EVALUATION, as a `have`, and
    then closes the frozen obligation verbatim, so it is a direct test that the
    pinned clause is satisfiable at that point rather than merely unfalsified.
  * FRAME / PERMISSION-MUTATION: vacuous here. Lean is referentially
    transparent, so there is no read-only-input predicate a variant could
    overwrite. The nagini sibling already recorded this class as structurally
    N/A on its own carrier (its three inputs are primitive values passed by
    value), so nothing is lost in the port.
  * DIVERGENCE / NON-TERMINATION: a KNOWN HOLE, not a vacuous class. An earlier
    revision of this manifest recorded it as vacuous on the ground that "a
    diverging implementation cannot be written at all" over a three-constructor
    inductive. That is false and was measured false: rewriting the impl as a
    self-recursive `partial def` whose body is `implementation_coerceDateEntry c
    rendered y m d` is admissible under `variant_scope` (no new axiom, no new
    theorem, statement byte-identical) and elaborates. `partial` supplies a
    total-looking constant with NO decreasing measure and NO defining equation
    available to the kernel, so:
      - the frozen obligation cannot be closed for it (the frozen tactic script
        leaves `implementation_coerceDateEntry … = some rendered` unsolved), i.e.
        the case WOULD record `rejected`; but
      - no witness can attribute that rejection to the spec. Measured: a witness
        stating the refutation at a literal input fails against the rival too
        (exit 1 both sides — the term does not reduce, so `decide` cannot compute
        either side), and a hypothesis-conditioned witness of the shape
        `(h : implementation… ≠ some "0-0-0") → ¬ problem_spec …` ELABORATES
        against gold as well (exit 0 both sides), so it discriminates nothing.
        The opaque-carrier technique does not rescue this case: the hypothesis is
        satisfiable (the gate's consistency probe cannot derive `False` from it —
        measured exit 1) precisely BECAUSE the term is irreducible, and that same
        irreducibility is what makes the statement hold of the frozen impl.
    So the class is shippable neither as a reject case (unattributable) nor as a
    positive. It is recorded here as a hole in what this battery can certify: a
    rival that replaces the dispatch with a non-reducing constant is rejected for
    a reason this battery cannot distinguish from a tactic mismatch. Note this
    bundle sets no `set_option loom.semantics.termination`, so it is not the
    `"total"` situation in which such a rival is genuinely refuted by a
    termination obligation.
  * `AXIOM_TESTS` dropped: the axiom lane is G-AX's job and this gate ignores
    it. (This bundle's axioms region is empty in any case — the classification
    enters as an input rather than an axiomatized callee, so G-AX skips.)

WITNESSES
---------
Every reject case carries a `witness`: a Lean snippet negating the spec
predicate at ONE concrete input, checked in a file from which the frozen
obligation has been removed. Each must (1) ELABORATE against the rival and
(2) FAIL against the frozen solution, so it is a real discriminator and not a
tautology. All eleven were built BOTH ways with `scripts/lean_verify.sh`: rival
exit 0, gold exit 1 with `decide` proving the negated proposition FALSE (i.e.
gold satisfies the clause at that input). The eleven witnesses probe eleven
DISTINCT input points, covering all three `DateEntry` constructors and moving
`rendered`, `y`, `m` and `d` independently.

Every gold-side failure is in the PLAIN-EVALUATION class: `decide` reduced the
proposition and reported it false, rather than failing for a missing identifier,
a type error, an unfolding failure or a timeout. That distinction was checked
directly, not inferred, with the flipped-claim experiment: for each of the eight
original witnesses, a second file differing ONLY in dropping the leading `¬` was
built against both sides, and the exit codes INVERTED in every case (flipped
claim: gold exit 0, rival exit 1). So gold's exit code tracks what the witness
CLAIMS and carries information about the claim — the witnesses are genuine
discriminators and not artifacts of a build that would have failed whatever was
asserted. No witness here binds a hypothesis, so the gate's consistency probe is
not reached (`consistency_probe` returns None) and there are no assumptions that
could be inconsistent.
"""
from pathlib import Path

INSTANCE = "django__django-16667"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl/proof-region substring; assert
    it matched so silent drift (Solution.lean edited) fails loudly."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — each lies strictly INSIDE the impl region (`_GOLD_ARMS`,
# `_GOLD_SIG`) or the proof region (`_GOLD_PROOF`) of Solution.lean, and each is
# unique across the whole file.
# ---------------------------------------------------------------------------

_GOLD_ARMS = (
    "  match c with\n"
    "  | DateEntry.valid => return some rendered\n"
    "  | DateEntry.malformed => return some (pseudoIso y m d)\n"
    '  | DateEntry.unrepresentable => return some "0-0-0"\n'
)

_GOLD_SIG = (
    "    (c : DateEntry) (rendered y m d : String) : Option String := Id.run do\n"
)

_GOLD_PROOF = (
    "  cases c <;>\n"
    "    refine ⟨?_, ?_, ?_⟩ <;>\n"
    "    intro h <;>\n"
    "    simp_all [implementation_coerceDateEntry]\n"
)


def _arms(valid: str, malformed: str, unrepresentable: str) -> str:
    """A replacement dispatch block, one arm per outcome."""
    return ("  match c with\n"
            f"  | DateEntry.valid => {valid}\n"
            f"  | DateEntry.malformed => {malformed}\n"
            f"  | DateEntry.unrepresentable => {unrepresentable}\n")


def _rival(valid: str, malformed: str, unrepresentable: str) -> str:
    """Full Solution.lean with only the dispatch arms reshaped."""
    return _swap(_BASE, _GOLD_ARMS, _arms(valid, malformed, unrepresentable))


def _witness(c: str, rendered: str, y: str, m: str, d: str) -> str:
    """`¬ problem_spec … ` at one concrete input, decided outright.

    The carrier is transparent (a `DecidableEq` three-constructor inductive plus
    `String` literals), so the head binds NOTHING: there is no opaque term to
    condition on and therefore no hypothesis that could be inconsistent.
    """
    args = f"{c} {rendered} {y} {m} {d}"
    return ("example : ¬ problem_spec_coerceDateEntry\n"
            f"    {args}\n"
            f"    (implementation_coerceDateEntry {args}) := by\n"
            "  unfold problem_spec_coerceDateEntry implementation_coerceDateEntry\n"
            "  decide\n")


def _admiss_have(c: str, rendered: str, y: str, m: str, d: str) -> str:
    """A `have` discharging the frozen obligation at ONE concrete input.

    Inserted before the frozen tactic script and then `clear`ed, so the frozen
    obligation is still closed by the frozen script VERBATIM and the `have` can
    only add a requirement, never remove one. `decide` computes the three clauses
    at the literal input, so the case verifies exactly when the postcondition is
    SATISFIABLE there — which is what the admissibility lane tests on a total
    carrier (the analogue of a precondition refusing an F2P-shaped input).
    """
    args = f"{c} {rendered} {y} {m} {d}"
    return ("  have admissible_at_input : problem_spec_coerceDateEntry\n"
            f"      {args}\n"
            f"      (implementation_coerceDateEntry {args}) := by\n"
            "    unfold problem_spec_coerceDateEntry "
            "implementation_coerceDateEntry\n"
            "    decide\n"
            "  clear admissible_at_input\n")


SPEC_TESTS = [

    # ---------------- ADMISSIBILITY ----------------

    # The obligation must be SATISFIABLE at the entry shape the F2P exercises —
    # the unaccommodatable outcome, at a component whose magnitude is above the
    # platform's integer-conversion limit. Discharged by EVALUATION at that
    # concrete input, as a `have`, before the frozen script closes the frozen
    # obligation verbatim.
    {
        "id": "admiss-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_PROOF,
            _admiss_have("DateEntry.unrepresentable", '"2010-01-31"',
                         '"9223372036854775808"', '"12"', '"1"') + _GOLD_PROOF),
        "rationale": "the postcondition must be SATISFIABLE at the entry shape "
                     "the F2P observes: the unaccommodatable outcome, at a "
                     "component whose magnitude exceeds what a calendar "
                     "component can accommodate. On a total carrier this is the "
                     "analogue of PRECOND-TOO-STRONG — there is no precondition "
                     "to refuse an input, so the failure mode is instead an "
                     "obligation that could not be DISCHARGED at that input "
                     "(mutually unsatisfiable clauses, or a clause pinning a "
                     "value the impl cannot produce there). The `have` computes "
                     "all three clauses at the literal input with `decide`, so "
                     "it verifies only if the pinned sentinel really is "
                     "obtainable at exactly that entry. No reject case tests "
                     "this: each of those shows some OTHER impl violates a "
                     "clause, which would be equally true of an unsatisfiable "
                     "one. The frozen obligation is still closed by the frozen "
                     "tactic script verbatim (the `have` is `clear`ed before "
                     "it), and the theorem STATEMENT is byte-identical, so the "
                     "case can only ADD a requirement.",
    },

    # ---------------- SOUNDNESS POSITIVES ----------------

    # Reordered cascade: the unaccommodatable outcome is decided FIRST, by `if`
    # guards instead of a `match`, and the representable outcome falls through as
    # the default. Same observable behavior, different control shape. The frozen
    # tactic script still closes it.
    {
        "id": "pos-if-cascade",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_ARMS,
            "  if c = DateEntry.unrepresentable then\n"
            '    return some "0-0-0"\n'
            "  if c = DateEntry.malformed then\n"
            "    return some (pseudoIso y m d)\n"
            "  return some rendered\n"),
        "rationale": "a CORRECT impl that decides the outcomes in the opposite "
                     "order, with equality guards rather than a constructor "
                     "match and the representable outcome as the fall-through "
                     "default, must verify. If it does not, the postcondition is "
                     "SPEC-TOO-STRONG — it would be pinning a branch ORDER "
                     "rather than the three clauses "
                     "(valid → some rendered, malformed → some (pseudoIso y m d), "
                     "unrepresentable → some \"0-0-0\"), which are mutually "
                     "exclusive and hence order-independent.",
    },

    # Pure functional form: no `Id.run do`, no `return`. Exercises that the spec
    # constrains the VALUE and not the monadic packaging of it.
    {
        "id": "pos-pure-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GOLD_SIG,
                  "    (c : DateEntry) (rendered y m d : String) : Option String :=\n"),
            _GOLD_ARMS,
            _arms("some rendered", "some (pseudoIso y m d)", 'some "0-0-0"')),
        "rationale": "the same dispatch written as a pure functional def (no "
                     "imperative do-block, no early return) is observationally "
                     "identical and must verify. A rejection here would mean the "
                     "obligation is discharged by the impl's monadic PACKAGING "
                     "rather than by the value it hands on — SPEC-TOO-STRONG "
                     "against a faithful structural variant.",
    },

    # The fallback assembly is inlined (the pure helper is not called), and the
    # all-zero sentinel is DERIVED by assembling three empty components rather
    # than written as a literal. Proof body re-closed (the helper must be
    # unfolded now that the impl no longer mentions it by name).
    {
        "id": "pos-derived-sentinel",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GOLD_ARMS,
                  "  match c with\n"
                  "  | DateEntry.valid => return some rendered\n"
                  "  | DateEntry.malformed =>\n"
                  '      return some ((if y = "" then "0" else y) ++ "-" ++\n'
                  '                   (if m = "" then "0" else m) ++ "-" ++\n'
                  '                   (if d = "" then "0" else d))\n'
                  '  | DateEntry.unrepresentable => return some (pseudoIso "" "" "")\n'),
            _GOLD_PROOF,
            "  cases c <;>\n"
            "    refine ⟨?_, ?_, ?_⟩ <;>\n"
            "    intro h <;>\n"
            "    simp_all [implementation_coerceDateEntry, pseudoIso]\n"),
        "rationale": "a CORRECT impl that inlines the fallback assembly and "
                     "OBTAINS the all-zero sentinel by assembling three empty "
                     "components (rather than writing the sentinel text) must "
                     "verify: the spec pins the VALUE handed on, not the "
                     "syntactic route to it. This is the positive that shows "
                     "clause 3 is not satisfiable only by echoing a literal, and "
                     "that clause 2 is a real per-component rule rather than an "
                     "opaque helper call. The proof body is re-closed for the new "
                     "shape (the helper is unfolded, since the impl no longer "
                     "names it); the theorem STATEMENT is byte-identical.",
    },

    # ---------------- UNIQUENESS RIVALS ----------------

    # The pre-change shape: nothing is handed on for the unaccommodatable
    # outcome.
    {
        "id": "no-value-unrep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("return some rendered",
                         "return some (pseudoIso y m d)",
                         "return none"),
        "rationale": "rejection comes from the TOTALITY half of clause 3 "
                     "(c = DateEntry.unrepresentable → result = some \"0-0-0\"): "
                     "this impl produces `none` for that outcome, reducing the "
                     "third conjunct to the underivable `none = some \"0-0-0\"`. "
                     "The other two clauses are untouched, so the rejection is "
                     "attributable to exactly the clause the fix defends. This is "
                     "also the G-DIFF discriminator: Solution_prepatch.lean fails "
                     "the same way.",
        "refinement": "this is the pre-change behavior: the outcome in which a "
                      "component's magnitude cannot be accommodated is not "
                      "handled at all, so the reduction is aborted instead of "
                      "handing a value on. Its faithful real patch is the "
                      "unpatched repo, on which the F2P inputs (a component far "
                      "above the platform's integer-conversion limit) abort the "
                      "request rather than yielding the all-zero sentinel: "
                      "test_value_from_datadict's added row does not produce the "
                      "expected value, and test_form_field never reaches the "
                      "invalid-entry error it asserts. Resolves NEITHER F2P, so a "
                      "verifying rival here would be a true "
                      "verify-does-not-imply-resolve break.",
        "witness": _witness("DateEntry.unrepresentable", '"2010-01-31"',
                            '"9223372036854775808"', '"12"', '"1"'),
    },

    # Cross-clause echo: hand on the canonical rendering for an outcome in which
    # no rendering was ever produced.
    {
        "id": "echo-rendered-unrep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("return some rendered",
                         "return some (pseudoIso y m d)",
                         "return some rendered"),
        "rationale": "rejection from the CONTENT half of clause 3: the impl hands "
                     "on the `rendered` input where `some \"0-0-0\"` is pinned. "
                     "`rendered` is a universally quantified String, so no value "
                     "of it can be proven equal to the sentinel; this is the "
                     "cross-clause echo attack — satisfying totality and "
                     "borrowing clause 1's own grounded text — and it is refuted "
                     "at a point where the two differ.",
        "refinement": "its faithful real patch hands on the canonical rendering "
                      "of a date for an entry whose magnitude could not be "
                      "accommodated — a date that was therefore never "
                      "constructed, so the real code either raises on the unbound "
                      "name or, if some earlier rendering is in scope, hands on "
                      "text that is not the all-zero sentinel. The F2P "
                      "test_value_from_datadict asserts that added row equals the "
                      "sentinel verbatim, so it FAILS. Does not resolve.",
        "witness": _witness("DateEntry.unrepresentable", '"31.12.2010"',
                            '"2010"', '"13"', '"40"'),
    },

    # Near-miss content: one character off.
    {
        "id": "near-miss-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("return some rendered",
                         "return some (pseudoIso y m d)",
                         'return some "0-0-1"'),
        "rationale": "rejection from the exact-content half of clause 3: the text "
                     "handed on differs from the pinned sentinel in a single "
                     "character. A supporting NEAR-MISS that satisfies totality "
                     "and every structural expectation (non-empty, same shape, "
                     "same length) and is caught only by the exact equality — so "
                     "it demonstrates that clause 3 pins content and not merely "
                     "the presence of a value. Probed at its own input point, "
                     "distinct from every other rival's.",
        "refinement": "its faithful real patch hands on a text one character off "
                      "from the all-zero sentinel. The F2P "
                      "test_value_from_datadict asserts the added row equals the "
                      "sentinel VERBATIM, so it FAILS regardless of how close the "
                      "text is. Does not resolve.",
        "witness": _witness("DateEntry.unrepresentable", '"r"',
                            '"1"', '"2"', '"3"'),
    },

    # A value IS handed on, but it is empty text.
    {
        "id": "empty-text-unrep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("return some rendered",
                         "return some (pseudoIso y m d)",
                         'return some ""'),
        "rationale": "rejection from the CONTENT half of clause 3 while TOTALITY "
                     "is satisfied: a value is handed on, but it is the empty "
                     "text rather than the pinned sentinel. This is the half of "
                     "nagini's collapsed absent-or-empty case that the `Option "
                     "String` carrier separates out — `none` is attacked by "
                     "`no-value-unrep`, and `some \"\"` is a genuinely different "
                     "wrong impl that only the content pin refutes.",
        "refinement": "its faithful real patch hands on empty text for the "
                      "unaccommodatable outcome. The F2P "
                      "test_value_from_datadict asserts the added row equals the "
                      "all-zero sentinel, so it FAILS; and an empty submitted "
                      "value makes the field report a MISSING entry rather than "
                      "the invalid-entry error test_form_field asserts, so that "
                      "F2P fails too. Resolves NEITHER.",
        "witness": _witness("DateEntry.unrepresentable", '"x"',
                            '"0"', '"5"', '"7"'),
    },

    # The most plausible near-miss: reuse the neighboring clause's own grounded
    # text for the unaccommodatable outcome.
    {
        "id": "echo-fallback-unrep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("return some rendered",
                         "return some (pseudoIso y m d)",
                         "return some (pseudoIso y m d)"),
        "rationale": "rejection from clause 3's content pin, attacked with clause "
                     "2's OWN grounded text: the impl collapses the two "
                     "non-representable outcomes onto the pseudo-ISO fallback. "
                     "This is the strongest near-miss on this carrier — the text "
                     "is non-empty, derived from the real components, and correct "
                     "for the neighboring outcome — so only the fact that clause "
                     "3 pins a DIFFERENT text refutes it. Refuted at a component "
                     "value for which the fallback and the sentinel differ.",
        "refinement": "its faithful real patch handles the unaccommodatable "
                      "outcome by falling through to the pseudo-ISO fallback, so "
                      "the value handed on echoes the oversized component (e.g. "
                      "a very long digit string joined to the other two "
                      "components) instead of the all-zero sentinel. The F2P "
                      "test_value_from_datadict asserts that row equals the "
                      "sentinel verbatim, so it FAILS. Does not resolve.",
        "witness": _witness("DateEntry.unrepresentable", '"q"',
                            '"18446744073709551616"', '"3"', '"4"'),
    },

    # Clause 1: the representable outcome hands on the wrong branch's text.
    {
        "id": "fallback-on-valid",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("return some (pseudoIso y m d)",
                         "return some (pseudoIso y m d)",
                         'return some "0-0-0"'),
        "rationale": "rejection from clause 1 "
                     "(c = DateEntry.valid → result = some rendered): the impl "
                     "hands on the pseudo-ISO fallback for a representable date. "
                     "The ONLY rival attacking clause 1, and the only one whose "
                     "witness sets `c` to DateEntry.valid — without it a rival "
                     "that mishandled just the representable outcome would never "
                     "be caught. `rendered` is a quantified input, so the "
                     "fallback text cannot be proven equal to it.",
        "refinement": "its faithful real patch hands on the pseudo-ISO fallback "
                      "even for an entry that DOES denote a representable "
                      "calendar date, so an ordinary valid entry no longer "
                      "reduces to its canonical rendering. The pre-existing rows "
                      "of the F2P test_value_from_datadict assert the canonical "
                      "rendering for such entries, so that F2P FAILS (as do the "
                      "date-field round-trip P2P tests). Does not resolve.",
        "witness": _witness("DateEntry.valid", '"2010-01-01"',
                            '"2010"', '"1"', '"1"'),
    },

    # Clause 2 sub-structure: the per-component zero-fill is dropped.
    {
        "id": "verbatim-empty-component",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("return some rendered",
                         'return some (y ++ "-" ++ m ++ "-" ++ d)',
                         'return some "0-0-0"'),
        "rationale": "rejection from clause 2 "
                     "(c = DateEntry.malformed → result = some (pseudoIso y m d)): "
                     "the impl joins the three components VERBATIM, dropping the "
                     "rule that an empty component is shown as a single zero. It "
                     "agrees with the spec on every entry whose components are "
                     "all non-empty, so it is refuted only at an input with an "
                     "empty component — which is exactly the sub-domain where the "
                     "zero-fill is observable, and the only witness here that "
                     "moves a component to the empty string.",
        "refinement": "its faithful real patch drops the zero-substitution for "
                      "unselected components, so a well-formed entry with one "
                      "component unselected reduces to a text with an empty slot "
                      "instead of a zero there. The F2P "
                      "test_value_from_datadict's pre-existing rows assert the "
                      "zero-filled fallback for exactly those entries, so it "
                      "FAILS. Does not resolve.",
        "witness": _witness("DateEntry.malformed", '"z"',
                            '"2000"', '""', '"1"'),
    },

    # Clause 2 sub-structure: the components are joined in the wrong order.
    {
        "id": "reversed-components",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("return some rendered",
                         "return some (pseudoIso d m y)",
                         'return some "0-0-0"'),
        "rationale": "rejection from clause 2's component ORDER: the impl "
                     "assembles the fallback from the same three components but "
                     "joined in reverse. Every component is still zero-filled and "
                     "the text is still non-empty, so only the positional "
                     "grounding of `pseudoIso y m d` in the spec refutes it. "
                     "Refuted at an input whose components are pairwise distinct "
                     "(a symmetric input would not discriminate), which is what "
                     "makes this rival probe the `y`/`d` binders independently.",
        "refinement": "its faithful real patch assembles the fallback text from "
                      "the three components in the opposite order, so a "
                      "well-formed non-date entry reduces to a transposed text. "
                      "The F2P test_value_from_datadict's pre-existing rows "
                      "assert the fallback with the components in their declared "
                      "order, so it FAILS. Does not resolve.",
        "witness": _witness("DateEntry.malformed", '"z"',
                            '"2017"', '"3"', '"23"'),
    },

    # Totality of clause 1 — the battery otherwise tests the `some …` half only
    # on clause 3.
    {
        "id": "no-value-valid",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("return none",
                         "return some (pseudoIso y m d)",
                         'return some "0-0-0"'),
        "rationale": "rejection from the TOTALITY half of clause 1 "
                     "(c = DateEntry.valid → result = some rendered): no value is "
                     "produced for a representable date, reducing the first "
                     "conjunct to the underivable `none = some rendered`. "
                     "Totality is pinned in ALL THREE clauses and every other "
                     "rival attacks it only in clause 3, so without this case a "
                     "rival that dropped the value on the representable outcome "
                     "would be caught by no witness here.",
        "refinement": "its faithful real patch produces no value at all for an "
                      "entry that DOES denote a representable calendar date, so "
                      "an ordinary valid entry aborts instead of reducing to its "
                      "canonical rendering. The pre-existing rows of the F2P "
                      "test_value_from_datadict assert the canonical rendering "
                      "for such entries, so that F2P FAILS (as do the date-field "
                      "round-trip P2P tests). Does not resolve.",
        "witness": _witness("DateEntry.valid", '"2010-06-15"',
                            '"2010"', '"6"', '"15"'),
    },

    # Totality of clause 2.
    {
        "id": "no-value-malformed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival("return some rendered",
                         "return none",
                         'return some "0-0-0"'),
        "rationale": "rejection from the TOTALITY half of clause 2 "
                     "(c = DateEntry.malformed → result = some (pseudoIso y m d)): "
                     "no value is produced for a well-formed entry that does not "
                     "denote a representable date. Completes the totality probe "
                     "across all three clauses — clause 3 is covered by "
                     "`no-value-unrep` and clause 1 by `no-value-valid`.",
        "refinement": "its faithful real patch stops handling the well-formed "
                      "but non-representable entry, so such an entry aborts "
                      "instead of reducing to the pseudo-ISO fallback. The "
                      "pre-existing rows of the F2P test_value_from_datadict "
                      "assert that fallback for exactly those entries, so it "
                      "FAILS. Does not resolve.",
        "witness": _witness("DateEntry.malformed", '"w"',
                            '"2017"', '"13"', '"23"'),
    },

    # Clause 2 sub-structure: the zero-fill fires on the WRONG CONDITION.
    {
        "id": "fill-wrong-condition",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "return some rendered",
            'return some ((if y = "0" then "0" else y) ++ "-" ++\n'
            '                   (if m = "0" then "0" else m) ++ "-" ++\n'
            '                   (if d = "0" then "0" else d))',
            'return some "0-0-0"'),
        "rationale": "rejection from clause 2's per-component rule, attacked at "
                     "its CONDITION rather than its result: this impl "
                     "substitutes a zero for a component already equal to \"0\" "
                     "(an identity, so a no-op) instead of for an EMPTY "
                     "component. It agrees with the spec on every entry with no "
                     "empty component, and differs from `verbatim-empty-"
                     "component` in shape rather than extension — that rival "
                     "drops the conditional entirely, this one keeps a "
                     "conditional of the same form with the test moved. It "
                     "checks that clause 2 pins WHICH component gets filled and "
                     "not merely that some conditional is present. Refuted at an "
                     "input with an empty component.",
        "refinement": "its faithful real patch tests each component against the "
                      "text \"0\" rather than against the unselected/empty case, "
                      "so a well-formed entry with one component unselected "
                      "reduces to a text with an empty slot instead of a zero "
                      "there. The pre-existing rows of the F2P "
                      "test_value_from_datadict assert the zero-filled fallback "
                      "for exactly those entries, so it FAILS. Does not resolve.",
        "witness": _witness("DateEntry.malformed", '"z"',
                            '"2000"', '""', '"1"'),
    },
]
