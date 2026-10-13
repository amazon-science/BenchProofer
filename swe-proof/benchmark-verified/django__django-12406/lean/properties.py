"""properties.py — G-PBT falsification battery for django__django-12406 (lean).

NOT a Lean module: a manifest of adversarially-reasoned cases the G-PBT runner
executes against the frozen `Solution.lean`. PORTED from the nagini sibling —
the adversarial ARGUMENTS are carried over one-for-one; the mechanics are
re-expressed against this backend's carrier. Every case edits ONLY the
implementation region (and, for the soundness positives, the proof body), so
`variant_scope.same_spec` holds by construction, each `theorem correct_<name>`
keeps a byte-identical STATEMENT, and every rejection is attributable to the
postcondition rather than to a tampered spec.

DEFENDED SURFACE
----------------
TWO modeled behaviors, both pure decision logic, both with a fully TRANSPARENT
carrier (no `opaque` callee, no axiom, no answer-key oracle) — so every rival is
refutable at a concrete literal input and no witness needs to condition on the
carrier.

(1) `implementation_emptyOption (required initialPresent radioWidget
     blankAllowed : Bool) (defaultLabel : String) : Option String`

    Obligation `correct_emptyOption`, with NO precondition hypothesis
    (`∀ required initialPresent radioWidget blankAllowed defaultLabel, …`).
    The single load-bearing clause pins the result exactly:

        result = if (required ∧ initialPresent) ∨ (radioWidget ∧ ¬ blankAllowed)
                 then none else some defaultLabel

    Two independent facts live in that one equation, and the battery attacks
    both:
      * PRESENCE — `none` exactly when one of the two suppression situations
        holds. Attacked from all four directions a wrong decision can take:
        drop the second disjunct, drop the first, widen the second by ignoring
        its `¬ blankAllowed` half, and widen the FIRST by reading its `∧` as an
        `∨`. That last direction needs a witness at a point where `required` and
        `initialPresent` DISAGREE, which is a genuinely separate sub-domain: the
        other four behavior-1 witnesses all hold the two flags equal, so a rival
        that only mishandles the disagreeing half is invisible to every one of
        them (verified by rebuilding this case's witness against each of the
        other rivals).
      * LABEL IDENTITY — when the option IS offered, the payload is EXACTLY
        `defaultLabel`, not some other string. A rival can satisfy PRESENCE
        perfectly and still fail this; `weak-wrong-label` is that rival, and it
        is the only case that varies the `defaultLabel` binder.

(2) `implementation_formKwargs (base : Std.HashMap String KwargVal)
     (blankAllowed : Bool) : Std.HashMap String KwargVal`

    Obligation `correct_formKwargs`, again with no precondition. TWO
    independent top-level clauses, each attacked separately:
      * `result["blank"]? = some (KwargVal.flag blankAllowed)` — the dedicated
        key carries the flag, UNCONDITIONALLY (so it overrides whatever `base`
        already held there).
      * `∀ k, k ≠ "blank" → result[k]? = base[k]?` — the FRAME clause. Every
        other key equals its incoming value: nothing else may be altered,
        dropped, or added. This is directive 5's frame obligation made
        structural, and it is a genuine attack surface here, not a
        referential-transparency casualty (see LANES below).

The discriminating delta every reject rival attacks:
  * behavior 1: the SECOND suppression situation — a radio-style presentation
    over an attribute that forbids an empty value must suppress the leading
    empty option;
  * behavior 2: forwarding the attribute's empty-value flag under the dedicated
    key at all (and forwarding the RIGHT flag).

CARRIER NARROWING vs THE NAGINI SIBLING
---------------------------------------
The nagini sibling models behavior 1 as a MUTATION of a field object under full
write permission plus an `int` placeholder label, and behavior 2 as a `bool`
identity-forwarding function. This backend models behavior 1 as a pure
`Bool^4 × String → Option String` decision (the label is the real `String`
value, not an `int` stand-in) and behavior 2 as the whole keyword-argument MAP
transformation rather than the single forwarded flag. The map carrier is a
STRENGTHENING: nagini's site 2 pinned only the forwarded boolean, whereas the
frame clause here also pins every untouched key, which is why this port carries
two frame rivals nagini had no place for.

WHICH NAGINI CASES PORTED
-------------------------
  * `pos-control-demorgan-offered` -> `pos-demorgan-offered`. Same argument
    (compute the OFFERED flag first, by De Morgan, and reverse the branch
    order); proof honestly re-closed by exhaustive case analysis on the four
    Booleans.
  * `pos-control-forward-branch` -> `pos-flag-branch`. Same argument (forward
    the flag through an explicit two-armed branch instead of one unconditional
    write), re-expressed as two `insert`s of the literal flags.
  * `weak-drop-radio-clause` -> `weak-drop-radio-situation`.
  * `weak-drop-required-clause` -> `weak-drop-required-situation`.
  * `partial-domain-radio-ignores-blank` -> `weak-radio-ignores-blank`.
  * `weak-wrong-label` -> `weak-wrong-label`. Nagini carried `label + 1` over an
    `int` stand-in; here the label is a real `String`, so the rival appends to
    it — the same "offered under the right condition, carrying the wrong text"
    attack on the LABEL IDENTITY fact.
  * `support-always-offer` -> `weak-always-offer`, witnessed at an input no
    other witness probes: the first suppression situation holds while the second
    does NOT (a radio presentation that permits an empty value), so the witness
    pins the first disjunct's force independently of the second.
  * `weak-flip-blank` -> `weak-flip-flag`, witnessed on the flag value where it
    is NOT already covered by `weak-const-false-flag`, so each of the two
    rivals is refuted on the sub-domain its own rationale claims.
  * `weak-const-false` -> `weak-const-false-flag`. Nagini's pre-patch shape
    (the flag never forwarded, so the derived field fell back to the
    forbids-empty default) becomes "the key is always set to the `false` flag".
  * ADDED `pos-nested-branch-order` — a second behavior-1 positive in a
    genuinely different shape (nested `if`s, no mutable accumulator, the two
    suppression situations tested in the OPPOSITE order). Guards against a
    postcondition over-fit to one branch order.
  * ADDED `pos-erase-then-insert` — a second behavior-2 positive.
  * ADDED `weak-omit-forward` — the pre-patch shape of behavior 2 (the key is
    never written at all), witnessed at a `base` that ALREADY carries a
    contrary flag under that key, so the witness also pins the
    unconditional-override half of the first clause.
  * ADDED `weak-clobber-other-keys` and `weak-inject-extra-key` — the two ways
    to violate the FRAME clause (destroy the incoming entries; add an entry
    that was never there). Nagini's carrier had no counterpart: its site 2
    returned a bare boolean, so there were no sibling keys to frame.
  * AUDIT-ADDED `admiss-report-shaped-inputs` — the admissibility lane, which
    the port dropped as vacuous and a later audit re-derived as expressible
    (see the OMISSIONS section below for why the port's reason was wrong).
  * AUDIT-ADDED `weak-required-or-initial` — the fourth direction on behavior 1's
    PRESENCE fact: the `∧` inside the first disjunct read as an `∨`. Found by an
    independent audit as a genuine coverage gap, not a reshape of an existing
    case: this rival agrees with the frozen decision at all four points the other
    behavior-1 witnesses probe (each of which holds `required` and
    `initialPresent` equal), so it was invisible to the battery as ported. Its
    witness sits at the only point where those two flags disagree.

WHICH NAGINI CASES DID NOT PORT (and why)
-----------------------------------------
  * `admiss-site1-read-field` (nagini's only admissibility case) -> ported as
    `admiss-report-shaped-inputs`. The port as first written DROPPED this case,
    reasoning that nagini's precondition (write permission on the mutated field
    object) has no counterpart because both obligations here are
    `∀ <binders>, problem_spec_<name> … (implementation_<name> …)` with no
    precondition hypothesis, so nothing could be PRECOND-TOO-STRONG. An
    independent audit rejected that reasoning and landed the case: "the frozen
    obligation has no precondition" is NOT what makes this lane vacuous. The
    analogue of PRECOND-TOO-STRONG on a TOTAL carrier is the obligation being
    UNSATISFIABLE at exactly an F2P-shaped input — a postcondition can be
    over-constrained (mutually contradictory clauses, or a clause that pins an
    unreachable value) while still being stated with no hypothesis at all, and
    every uniqueness case would still reject, every soundness case would still
    fail, so neither of the other two lanes detects it. The ported case
    discharges both obligations' predicates at concrete report-shaped inputs
    BEFORE closing the frozen obligation verbatim, which tests exactly that.
  * FRAME / PERMISSION-MUTATION rivals — nagini's fractional-permission class
    (write through a `Acc(x,1/2)` read-only input) is not expressible here:
    Lean is referentially transparent, so there is no aliasing and no
    permission to abuse. The class is VACUOUS *as a permission* class. Note
    carefully that this does NOT leave the frame obligation untested: behavior
    2's spec makes the frame an OBSERVABLE component of the result
    (`∀ k ≠ "blank", result[k]? = base[k]?`), so `weak-clobber-other-keys` and
    `weak-inject-extra-key` attack it structurally. The nagini frame ARGUMENT
    therefore survives the port even though nagini's frame MECHANISM does not.
  * DIVERGENCE / NON-TERMINATION — genuinely vacuous on lean, and this is the
    one lane where that phrase is literally true rather than a euphemism: both
    `implementation_*` are total Lean `def`s (no `partial`, no
    `termination_by`), so a non-terminating implementation cannot be written at
    all and there is nothing for a spec to admit vacuously. This is NOT the
    velvet `loom.semantics.termination "partial"` known hole documented in
    `the corpus-wide termination-semantics finding` — that hole is a property of velvet's
    semantics option, and this backend has no such option to set. The nagini
    sibling carries no divergence case either (both its sites are loop-free).
  * `AXIOM_TESTS` (`ax-ref-placeholder`, `ax-ref-forwarding`,
    `ax-cover-boolean-domain`) — DROPPED. The axiom lane is G-AX's job and this
    gate ignores it. This bundle declares no axiom and no `opaque` callee
    anyway (`meta.json`: `axioms: []`, `opaque_callees: []`), so both behaviors
    are modeled deeply and there is no consumed contract to fuzz.

WITNESSES
---------
Every `expect="reject"` case carries a `witness`: a snippet negating the frozen
spec predicate at ONE concrete input, checked in a file with the frozen
obligations removed. Each was built BOTH ways with `scripts/lean_verify.sh`
before shipping — exit 0 against the rival, exit 1 against the frozen solution
— so each has been SEEN to discriminate. No witness binds a hypothesis (the
carrier is transparent, so there is nothing to condition on and no
joint-satisfiability question to get wrong), so no case needs the gate's
consistency probe.

Re-derived independently by a later audit, which rebuilt all of these both ways
and read the gold-side failure text rather than only its exit code. Each gold
build fails by a SEMANTIC refutation, not a syntactic accident: the behavior-1
witnesses report `decide` proved the negation false at the stated literals, and
the behavior-2 witnesses leave a bare `⊢ False` after `simp` has computed the
map lookups. No gold failure is an unknown identifier, a type error, a stuck
`Decidable` reduction, or a timeout — the four ways a witness can look like a
discriminator without being one.

Behavior 1's spec computes under `decide`. Behavior 2's does NOT: `decide`
reduces the `Decidable` instance and gets stuck on a `Std.HashMap` lookup
(`(…)["blank"]?.instDecidableEq … did not reduce`), which is a tactic limit and
not an undecidable input. `simp [Std.HashMap.getElem?_insert]` computes those
lookups, so behavior 2's witnesses use it.
"""
from pathlib import Path

INSTANCE = "django__django-12406"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    """Replace exactly one occurrence, asserting the anchor is present and
    unique so drift in the frozen solution fails loudly instead of silently
    producing a variant that tests nothing."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies ENTIRELY inside ONE impl region (or, for the positives,
# one proof region) and is unique in the whole file, so every _swap keeps
# same_spec and the obligation statements byte-identical.
# ---------------------------------------------------------------------------

# --- behavior 1 -----------------------------------------------------------
# The full frozen decision body.
_B1_BODY = (
    "  let mut chosen : Option String := some defaultLabel\n"
    "  if (required && initialPresent) || (radioWidget && !blankAllowed) then\n"
    "    chosen := none\n"
    "  else\n"
    "    chosen := some defaultLabel\n"
    "  return chosen"
)
# Just the decision condition (unique: the spec states it with ∧/∨, not &&/||).
_B1_COND = "  if (required && initialPresent) || (radioWidget && !blankAllowed) then\n"
# Just the offered arm (the `let mut` line differs in indent and prefix).
_B1_OFFER = "    chosen := some defaultLabel\n"
# The frozen behavior-1 proof body.
_B1_PROOF = (
    "  unfold problem_spec_emptyOption implementation_emptyOption\n"
    "  simp only [Id.run, bind, pure]\n"
    "  split <;> simp_all"
)

# Just the accumulator seed line, for prepending an in-body `have` (the
# admissibility positive) without disturbing the decision itself.
_B1_SEED = "  let mut chosen : Option String := some defaultLabel\n"

# --- behavior 2 -----------------------------------------------------------
_B2_SEED = "  let mut d := base\n"
_B2_INSERT = '  d := d.insert "blank" (KwargVal.flag blankAllowed)\n'
# The frozen behavior-2 proof body.
_B2_PROOF = (
    "  unfold problem_spec_formKwargs implementation_formKwargs\n"
    "  simp only [Id.run, pure]\n"
    "  refine ⟨?_, ?_⟩\n"
    "  · rw [Std.HashMap.getElem?_insert]; simp\n"
    "  · intro k hk\n"
    "    rw [Std.HashMap.getElem?_insert]\n"
    "    simp only [beq_iff_eq]\n"
    "    rw [if_neg (fun h => hk h.symm)]"
)

for _a in (_B1_BODY, _B1_COND, _B1_OFFER, _B1_PROOF, _B1_SEED, _B2_SEED,
           _B2_INSERT, _B2_PROOF):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drifted or not unique: {_a!r}")


# ---------------------------------------------------------------------------
# Witness builders.
# ---------------------------------------------------------------------------

def _wit1(required, initial, radio, blank, label, note):
    """Behavior 1: negate the frozen spec at a concrete input, by `decide`.

    The whole carrier is transparent and finite here, so `decide` computes both
    sides. Elaborates iff the impl in the file disagrees with the frozen
    postcondition at exactly this point.
    """
    args = f'{required} {initial} {radio} {blank} "{label}"'
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_emptyOption {args}\n"
        f"    (implementation_emptyOption {args}) := by\n"
        f"  unfold problem_spec_emptyOption implementation_emptyOption\n"
        f"  decide"
    )


_EMPTY_MAP = "(∅ : Std.HashMap String KwargVal)"


def _wit2_flag(base, blank, note):
    """Behavior 2, FIRST clause: the dedicated key does not carry the flag.

    `decide` is stuck on HashMap lookups (a `Decidable`-instance reduction
    limit, not an undecidable input), so the lookups are computed by `simp` with
    the insert-lookup lemma.
    """
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_formKwargs {base} {blank}\n"
        f"    (implementation_formKwargs {base} {blank}) := by\n"
        f"  unfold problem_spec_formKwargs implementation_formKwargs\n"
        f"  simp [Std.HashMap.getElem?_insert]"
    )


def _wit2_frame(base, blank, key, note):
    """Behavior 2, SECOND (frame) clause: some key other than the dedicated one
    no longer equals its incoming value. Instantiates the ∀ at `key`."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_formKwargs {base} {blank}\n"
        f"    (implementation_formKwargs {base} {blank}) := by\n"
        f"  unfold problem_spec_formKwargs implementation_formKwargs\n"
        f"  intro h\n"
        f'  have h2 := h.2 "{key}" (by decide)\n'
        f"  simp [Std.HashMap.getElem?_insert] at h2"
    )


# ===========================================================================
# SPEC LANE
# ===========================================================================
SPEC_TESTS = [

    # ---------------------------------------------------------------- POSITIVES
    # Behavior 1, positive #1 — the nagini De Morgan reshape. Compute the
    # OFFERED flag first as the negation of the suppression disjunction, then
    # assign in the OPPOSITE branch order. Value-identical on all 2^4 Boolean
    # inputs and on every label. The frozen `split <;> simp_all` no longer
    # matches the reshaped branch tree, so the proof body is honestly re-closed
    # by exhaustive case analysis on the four Booleans — the theorem STATEMENT
    # is byte-identical and no axiom / lemma / sorry is introduced.
    {
        "id": "pos-demorgan-offered",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _B1_BODY,
                "  let offered : Bool :=\n"
                "    (!required || !initialPresent) && (!radioWidget || blankAllowed)\n"
                "  let mut chosen : Option String := none\n"
                "  if offered then\n"
                "    chosen := some defaultLabel\n"
                "  else\n"
                "    chosen := none\n"
                "  return chosen",
            ),
            _B1_PROOF,
            "  unfold problem_spec_emptyOption implementation_emptyOption\n"
            "  simp only [Id.run, bind, pure]\n"
            "  cases required <;> cases initialPresent <;> cases radioWidget <;>\n"
            "    cases blankAllowed <;> simp_all",
        ),
        "rationale": "SOUNDNESS positive for `correct_emptyOption`. A "
                     "structurally-different but CORRECT implementation: the "
                     "OFFERED flag is computed up front as the De Morgan dual "
                     "of the suppression disjunction, the accumulator is seeded "
                     "with the suppressed value instead of the offered one, and "
                     "the two branches are swapped. Value-equal to the frozen "
                     "decision at every one of the 16 Boolean points and at "
                     "every label, so BOTH facts in the clause (presence and "
                     "label identity) still hold. If this is REJECTED => "
                     "SPEC-TOO-STRONG: the postcondition would be over-fit to "
                     "one branch order rather than pinning the behavior.",
    },

    # Behavior 1, positive #2 — ADDED. A second correct shape with no mutable
    # accumulator at all: nested `if`s that test the two suppression situations
    # in the OPPOSITE order. A faithful patch could equally take this form.
    {
        "id": "pos-nested-branch-order",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _B1_BODY,
                "  if radioWidget && !blankAllowed then\n"
                "    return none\n"
                "  if required && initialPresent then\n"
                "    return none\n"
                "  return some defaultLabel",
            ),
            _B1_PROOF,
            "  unfold problem_spec_emptyOption implementation_emptyOption\n"
            "  simp only [Id.run, bind, pure]\n"
            "  cases required <;> cases initialPresent <;> cases radioWidget <;>\n"
            "    cases blankAllowed <;> simp_all",
        ),
        "rationale": "SOUNDNESS positive for `correct_emptyOption`, in a shape "
                     "further from the frozen one than pos-demorgan-offered: no "
                     "mutable accumulator, two early returns, and the two "
                     "suppression situations tested in the REVERSE order. The "
                     "disjunction is symmetric, so the verdict is identical on "
                     "every input. Rejection => SPEC-TOO-STRONG (the clause "
                     "would be pinning the ORDER in which the two situations "
                     "are examined, which the specified behavior does not fix).",
    },

    # Behavior 2, positive #1 — the nagini forward-branch reshape: route the
    # flag through an explicit two-armed branch writing the literal flags,
    # instead of one unconditional write of the flag value.
    {
        "id": "pos-flag-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _B2_INSERT,
                "  if blankAllowed then\n"
                '    d := d.insert "blank" (KwargVal.flag true)\n'
                "  else\n"
                '    d := d.insert "blank" (KwargVal.flag false)\n',
            ),
            _B2_PROOF,
            "  have hrun : implementation_formKwargs base blankAllowed\n"
            '      = base.insert "blank" (KwargVal.flag blankAllowed) := by\n'
            "    cases blankAllowed <;> rfl\n"
            "  unfold problem_spec_formKwargs\n"
            "  rw [hrun]\n"
            "  refine ⟨?_, ?_⟩\n"
            "  · rw [Std.HashMap.getElem?_insert]; simp\n"
            "  · intro k hk\n"
            "    rw [Std.HashMap.getElem?_insert]\n"
            "    simp only [beq_iff_eq]\n"
            "    rw [if_neg (fun h => hk h.symm)]",
        ),
        "rationale": "SOUNDNESS positive for `correct_formKwargs` — the port of "
                     "nagini's branch-shaped forwarding. Each arm writes the "
                     "literal flag its guard establishes, so the resulting map "
                     "is the same on both arms as the frozen unconditional "
                     "write; both clauses (the dedicated key carries the flag; "
                     "every other key is untouched) hold on each arm. The "
                     "frozen proof cannot see through the branch, so it is "
                     "honestly re-closed by first collapsing the branch to the "
                     "single insert (`cases blankAllowed <;> rfl`) — same "
                     "theorem statement, no new axiom/lemma/sorry. Rejection => "
                     "SPEC-TOO-STRONG.",
    },

    # Behavior 2, positive #2 — ADDED. Remove the key first, then write it.
    # Redundant but CORRECT: the erase only touches the one key the write then
    # overwrites, so the frame clause is untouched.
    {
        "id": "pos-erase-then-insert",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _B2_SEED,
                '  let mut d := base.erase "blank"\n',
            ),
            _B2_PROOF,
            "  unfold problem_spec_formKwargs implementation_formKwargs\n"
            "  simp only [Id.run, pure]\n"
            "  refine ⟨?_, ?_⟩\n"
            "  · rw [Std.HashMap.getElem?_insert]; simp\n"
            "  · intro k hk\n"
            "    rw [Std.HashMap.getElem?_insert]\n"
            "    simp only [beq_iff_eq]\n"
            "    rw [if_neg (fun h => hk h.symm)]\n"
            "    rw [Std.HashMap.getElem?_erase]\n"
            "    simp only [beq_iff_eq]\n"
            "    rw [if_neg (fun h => hk h.symm)]",
        ),
        "rationale": "SOUNDNESS positive for `correct_formKwargs`: clearing the "
                     "dedicated key before writing it is redundant but "
                     "value-equal, since the write immediately re-establishes "
                     "that key and the clear provably touches no OTHER key. "
                     "This is the positive control for the frame clause "
                     "specifically — it proves the frame clause is satisfiable "
                     "by an impl that does manipulate the map beyond a single "
                     "write, so the two frame rivals below are rejected for "
                     "changing OTHER keys and not merely for touching the map "
                     "twice. Rejection => SPEC-TOO-STRONG.",
    },

    # ---------------------------------------------------------- ADMISSIBILITY
    # AUDIT-ADDED. The port dropped nagini's admissibility case on the ground
    # that neither obligation carries a precondition. That is the wrong test:
    # on a TOTAL carrier the analogue of PRECOND-TOO-STRONG is the obligation
    # being UNSATISFIABLE at exactly an F2P-shaped input, which a hypothesis-free
    # `∀` statement can perfectly well be. Both frozen bodies AND both frozen
    # proofs are kept verbatim; the case only PREPENDS in-body `have`s that
    # discharge each postcondition predicate, by evaluation, at concrete
    # report-shaped inputs. If any of them could not be discharged the spec
    # would be over-constrained at the very points the reported failure is
    # about, and neither of the other two lanes would show it: a uniqueness
    # rival would still reject (from a contradiction) and a soundness positive
    # would still fail, so the battery would read as clean.
    {
        "id": "admiss-report-shaped-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _B1_SEED,
                # Behavior 1 at BOTH halves of the discriminating situation: a
                # radio-style presentation over an attribute that forbids an
                # empty value (must suppress) and one that permits it (must
                # offer). These are the two points the reported failure is
                # about, and the clause must be satisfiable at each.
                "  have _hSuppressAtReport :\n"
                '      problem_spec_emptyOption false false true false "---------"\n'
                "        none := by\n"
                "    unfold problem_spec_emptyOption\n"
                "    decide\n"
                "  have _hOfferAtReport :\n"
                '      problem_spec_emptyOption false false true true "---------"\n'
                '        (some "---------") := by\n'
                "    unfold problem_spec_emptyOption\n"
                "    decide\n"
                + _B1_SEED,
            ),
            _B2_SEED,
            # Behavior 2 at a report-shaped incoming map: a caller-assembled
            # argument already present, and the flag forwarded alongside it.
            # BOTH clauses must hold there jointly — the dedicated key carrying
            # the flag must be compatible with the frame clause preserving the
            # pre-existing entry, which is exactly the joint satisfiability an
            # over-constrained conjunction would break.
            _B2_SEED
            + "  have _hKwargsAtReport :\n"
              "      problem_spec_formKwargs\n"
              '        (((∅ : Std.HashMap String KwargVal)).insert "queryset" KwargVal.obj) true\n'
              '        ((((∅ : Std.HashMap String KwargVal)).insert "queryset" KwargVal.obj).insert\n'
              '          "blank" (KwargVal.flag true)) := by\n'
              "    unfold problem_spec_formKwargs\n"
              "    refine ⟨?_, ?_⟩\n"
              "    · rw [Std.HashMap.getElem?_insert]; simp\n"
              "    · intro k hk\n"
              "      rw [Std.HashMap.getElem?_insert]\n"
              "      simp only [beq_iff_eq]\n"
              "      rw [if_neg (fun h => hk h.symm)]\n",
        ),
        "rationale": "ADMISSIBILITY positive, the lane that detects "
                     "PRECOND-TOO-STRONG. Neither obligation carries a "
                     "precondition hypothesis, so the analogue on this total "
                     "carrier is SATISFIABILITY at a concrete report-shaped "
                     "input rather than vacuous truth: both frozen bodies and "
                     "both frozen proofs are kept verbatim and the variant only "
                     "adds in-body `have`s that DISCHARGE each postcondition "
                     "predicate at such inputs. Behavior 1 is discharged at "
                     "both halves of the discriminating situation — a "
                     "radio-style presentation over an attribute that forbids "
                     "an empty value (the predicate must admit `none`) and one "
                     "that permits it (the predicate must admit `some "
                     "defaultLabel`) — so neither half is an over-constrained "
                     "point. Behavior 2 is discharged at an incoming map that "
                     "already carries a caller-assembled argument, which "
                     "requires the two top-level clauses to hold JOINTLY there: "
                     "the dedicated key must carry the flag while the frame "
                     "clause preserves the pre-existing entry. If any `have` "
                     "could not be discharged => PRECOND-TOO-STRONG (the "
                     "obligation would be unsatisfiable at exactly the inputs "
                     "the reported failure concerns, and NEITHER other lane "
                     "would reveal it: uniqueness rivals would still reject, "
                     "from a contradiction rather than from the behavior, and "
                     "every soundness positive would fail too).",
    },

    # ------------------------------------------------ UNIQUENESS (behavior 1)
    # The pre-patch decision: only the required-with-initial situation
    # suppresses; the radio situation is absent.
    {
        "id": "weak-drop-radio-situation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _B1_COND, "  if required && initialPresent then\n"),
        "refinement": "this rival IS the behavior of the code before the change "
                      "(it is the shape of `Solution_prepatch_1.lean`): the "
                      "second suppression situation simply does not exist. Its "
                      "faithful real patch is therefore the UNCHANGED code, "
                      "which still presents the leading empty option for a "
                      "radio-style presentation over an attribute that forbids "
                      "an empty value — precisely the observation the "
                      "FAIL_TO_PASS tests make (the forbids-empty subcase of "
                      "the radio/empty-value test, and the non-emptyable "
                      "relational-attribute-with-radio test, which expect the "
                      "rendered option list to carry NO leading empty row). So "
                      "a rival that verified here would resolve nothing: a true "
                      "verify-does-not-imply-resolve break.",
        "rationale": "REJECT from the PRESENCE fact of the single clause: at "
                     "(required=false, initialPresent=false, radioWidget=true, "
                     "blankAllowed=false) the postcondition demands `none`, but "
                     "with the second disjunct gone the rival takes the else "
                     "arm and returns `some defaultLabel`. Attacks the "
                     "`radioWidget ∧ ¬ blankAllowed` disjunct; varies the "
                     "radioWidget binder to true against a false "
                     "required/initialPresent. If it VERIFIES => SPEC-TOO-WEAK.",
        "witness": _wit1("false", "false", "true", "false", "---------",
                         "radio presentation, empty value forbidden: the frozen "
                         "spec suppresses, the rival offers"),
    },

    # The mirror omission: keep only the radio situation.
    {
        "id": "weak-drop-required-situation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _B1_COND,
                        "  if radioWidget && !blankAllowed then\n"),
        "refinement": "dropping the required-with-initial suppression re-offers "
                      "the leading empty option for a mandatory field that "
                      "already carries a pre-filled value. That situation is "
                      "long-standing behavior at the base commit, NOT part of "
                      "the change, so a faithful real patch of this rival is a "
                      "REGRESSION: it would break the pre-existing "
                      "required-with-initial paths exercised across the "
                      "PASS_TO_PASS suite while leaving the newly required "
                      "radio behavior correct. It does not resolve — it trades "
                      "one failing set of tests for another.",
        "rationale": "REJECT from the PRESENCE fact: at (required=true, "
                     "initialPresent=true, radioWidget=false, "
                     "blankAllowed=false) the postcondition demands `none`, but "
                     "with the first disjunct gone the rival returns `some "
                     "defaultLabel`. Attacks the `required ∧ initialPresent` "
                     "disjunct at the point where that disjunct is the SOLE "
                     "reason to suppress: radioWidget=false makes the second "
                     "disjunct false, so no other clause can mask the omission. "
                     "(weak-always-offer also holds required and initialPresent "
                     "at true, but there radioWidget=true, so that witness does "
                     "not isolate this disjunct the way this one does.) If it "
                     "VERIFIES => SPEC-TOO-WEAK.",
        "witness": _wit1("true", "true", "false", "false", "---------",
                         "required with a present initial value, no radio: the "
                         "frozen spec suppresses, the rival offers"),
    },

    # Near-miss: suppress for EVERY radio presentation, ignoring whether an
    # empty value is permitted. Correct everywhere except (radio ∧ blank).
    {
        "id": "weak-radio-ignores-blank",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _B1_COND,
            "  if (required && initialPresent) || radioWidget then\n"),
        "refinement": "suppressing for EVERY radio-style presentation drops the "
                      "leading empty option even when the underlying attribute "
                      "DOES permit an empty value — an option that must remain "
                      "available, since an empty selection is a legitimate "
                      "choice there. Its faithful real patch fails the "
                      "permits-empty subcase of the radio/empty-value "
                      "FAIL_TO_PASS test and the emptyable-relational-attribute "
                      "test, both of which expect a leading empty row followed "
                      "by the real options. It over-applies the fix instead of "
                      "resolving it.",
        "rationale": "REJECT from the PRESENCE fact: at (required=false, "
                     "initialPresent=false, radioWidget=true, "
                     "blankAllowed=true) the postcondition demands `some "
                     "defaultLabel`, but the rival's widened disjunct fires and "
                     "returns `none`. This is a NEAR-MISS of the previous two "
                     "rivals — it agrees with the frozen decision at every "
                     "input except this one sub-domain — so it gets its own "
                     "witness at the point that distinguishes it: the only "
                     "behavior-1 witness holding blankAllowed at true while the "
                     "FIRST disjunct is false, which is what makes the "
                     "`¬ blankAllowed` conjunct the sole load-bearing term "
                     "there. (weak-always-offer also sets blankAllowed=true, "
                     "but its first disjunct fires, so it cannot isolate this "
                     "conjunct.) Attacks the `¬ blankAllowed` half of the "
                     "second disjunct. If it "
                     "VERIFIES => SPEC-TOO-WEAK (the `¬ blankAllowed` "
                     "conjunct would be doing no work).",
        "witness": _wit1("false", "false", "true", "true", "---------",
                         "radio presentation, empty value permitted: the frozen "
                         "spec offers, the rival suppresses"),
    },

    # Near-miss: read the FIRST situation's conjunction as a disjunction, so a
    # mandatory field with NO pre-filled value (or a pre-filled optional one)
    # also suppresses. AUDIT-ADDED: every other behavior-1 witness holds
    # `required` and `initialPresent` EQUAL, so this rival agrees with the frozen
    # decision at all four of their points and only the witness below catches it.
    {
        "id": "weak-required-or-initial",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _B1_COND,
            "  if (required || initialPresent) || (radioWidget && !blankAllowed) then\n"),
        "refinement": "reading the first situation's conjunction as a "
                      "disjunction suppresses the leading empty option for a "
                      "mandatory field that carries NO pre-filled value — the "
                      "commonest presentation there is, a blank required "
                      "selector, which must still offer the empty row so the "
                      "form has an unselected initial state to render. Its "
                      "faithful real patch would strip that row from ordinary "
                      "required selectors across the suite, so the PASS_TO_PASS "
                      "paths that render a fresh required selector and compare "
                      "the full option list break. It over-applies a "
                      "long-standing condition rather than resolving the "
                      "reported one.",
        "rationale": "REJECT from the PRESENCE fact, attacking the `∧` INSIDE "
                     "the first disjunct — the one sub-domain the rest of the "
                     "battery leaves open. At (required=true, "
                     "initialPresent=false, radioWidget=false, "
                     "blankAllowed=true) the postcondition demands `some "
                     "defaultLabel` (neither situation holds) but the widened "
                     "disjunct fires and the rival returns `none`. This is the "
                     "ONLY behavior-1 witness at which `required` and "
                     "`initialPresent` DISAGREE: the other four all hold them "
                     "equal, so each of them accepts this rival. If it VERIFIES "
                     "=> SPEC-TOO-WEAK (the clause would be pinning only that "
                     "SOME combination of the two flags suppresses, not their "
                     "conjunction).",
        "witness": _wit1("true", "false", "false", "true",
                         "---------",
                         "a mandatory field with no pre-filled value and no "
                         "radio presentation: the frozen spec offers, the rival "
                         "suppresses"),
    },

    # Attacks the OTHER fact in the clause: presence is perfect, payload wrong.
    {
        "id": "weak-wrong-label",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _B1_OFFER,
                        '    chosen := some (defaultLabel ++ "!")\n'),
        "refinement": "this rival decides PRESENCE exactly right on all 16 "
                      "Boolean inputs and errs only in the text it carries. Its "
                      "faithful real patch would render the leading empty row "
                      "with a caption other than the supplied one, so the "
                      "rendered option list diverges from the exact "
                      "label-bearing rows the FAIL_TO_PASS tests compare "
                      "against (they assert the full expected option list, "
                      "captions included, not merely that a leading empty row "
                      "exists). It does not resolve.",
        "rationale": "REJECT from the LABEL IDENTITY fact of the clause: when "
                     "the option is offered the postcondition pins the payload "
                     "to EXACTLY `some defaultLabel`, and the rival carries a "
                     "different string. This is the only case that attacks the "
                     "payload rather than the presence, and the only one that "
                     "varies the `defaultLabel` binder (witnessed at a short "
                     "label, not the default one) — without it a rival that "
                     "ignored or mangled `defaultLabel` while branching "
                     "correctly would verify. If it VERIFIES => SPEC-TOO-WEAK "
                     "(the clause would only be pinning presence).",
        "witness": _wit1("false", "false", "false", "false", "L",
                         "offered under the correct condition but carrying a "
                         "different label than the supplied one"),
    },

    # No suppression at all: reintroduces both situations' bugs at once.
    {
        "id": "weak-always-offer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _B1_BODY, "  return some defaultLabel"),
        "refinement": "offering unconditionally ignores BOTH suppression "
                      "situations at once: a mandatory pre-filled field and a "
                      "radio presentation over a non-emptyable attribute would "
                      "each wrongly show the leading empty option. Its faithful "
                      "real patch fails the non-emptyable "
                      "relational-attribute-with-radio FAIL_TO_PASS test AND "
                      "the pre-existing required-with-initial PASS_TO_PASS "
                      "paths. It resolves nothing and regresses besides.",
        "rationale": "REJECT from the PRESENCE fact at every suppressing input. "
                     "Witnessed at (required=true, initialPresent=true, "
                     "radioWidget=true, blankAllowed=true) — a point no other "
                     "witness probes, and deliberately one where the FIRST "
                     "situation alone forces suppression while the second does "
                     "NOT fire, so the witness pins the first disjunct's "
                     "independent force even in the presence of a radio widget "
                     "that permits an empty value. If it VERIFIES => "
                     "SPEC-TOO-WEAK.",
        "witness": _wit1("true", "true", "true", "true", "---------",
                         "required with a present initial value under a "
                         "radio presentation that permits an empty value: the "
                         "frozen spec still suppresses, the rival offers"),
    },

    # ------------------------------------------------ UNIQUENESS (behavior 2)
    # The pre-patch shape: the dedicated key is never written.
    {
        "id": "weak-omit-forward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _B2_INSERT, ""),
        "refinement": "this rival IS the behavior before the change (the shape "
                      "of `Solution_prepatch_2.lean`): the empty-value flag is "
                      "never plumbed into the generated field's keyword "
                      "arguments, so the consuming decision never receives it "
                      "and falls back to its own default. Its faithful real "
                      "patch is the UNCHANGED code, under which a radio "
                      "presentation over an attribute that DOES permit an empty "
                      "value loses its leading empty option — exactly what the "
                      "emptyable-relational-attribute-with-radio FAIL_TO_PASS "
                      "test asserts must not happen. Behavior 1's fix is "
                      "unreachable from a generated form without this "
                      "plumbing, so it resolves nothing.",
        "rationale": "REJECT from the FIRST clause "
                     "(`result[\"blank\"]? = some (KwargVal.flag "
                     "blankAllowed)`): with no write, the dedicated key retains "
                     "whatever `base` held, so the clause fails whenever that "
                     "differs from the flag. Witnessed at a `base` that already "
                     "carries the CONTRARY flag under that key, which makes the "
                     "witness pin the clause's unconditional-OVERRIDE force as "
                     "well as its presence — the incoming value must be "
                     "replaced, not deferred to. This is the only witness that "
                     "varies the `base` binder away from the empty map with a "
                     "pre-existing entry under the dedicated key. If it "
                     "VERIFIES => SPEC-TOO-WEAK.",
        "witness": _wit2_flag(
            f'({_EMPTY_MAP}.insert "blank" (KwargVal.flag false))', "true",
            "the incoming map already carries the contrary flag under the "
            "dedicated key: the frozen spec overrides it, the rival leaves it"),
    },

    # Near-miss: the key is always written with the forbids-empty flag.
    {
        "id": "weak-const-false-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _B2_INSERT,
                        '  d := d.insert "blank" (KwargVal.flag false)\n'),
        "refinement": "writing the dedicated key with a hard-coded "
                      "forbids-empty flag is the port of nagini's pre-patch "
                      "default: the key exists but never reflects the "
                      "attribute. Its faithful real patch makes every generated "
                      "field behave as though an empty value were forbidden, so "
                      "a radio presentation over an attribute that permits one "
                      "loses its leading empty option — the "
                      "emptyable-relational-attribute-with-radio FAIL_TO_PASS "
                      "test fails. It does not resolve.",
        "rationale": "REJECT from the FIRST clause. This is a NEAR-MISS: it "
                     "agrees with the frozen spec on the whole blankAllowed="
                     "false half of the domain, so it is witnessed at "
                     "blankAllowed=true, the sub-domain its rationale actually "
                     "claims — distinct from weak-flip-flag's witness below, "
                     "which sits at blankAllowed=false where THIS rival is "
                     "correct. If it VERIFIES => SPEC-TOO-WEAK (the clause "
                     "would not be pinning the flag to the input at all).",
        "witness": _wit2_flag(_EMPTY_MAP, "true",
                              "an attribute that permits an empty value: the "
                              "frozen spec forwards that, the rival hard-codes "
                              "the opposite"),
    },

    # Forward the negation.
    {
        "id": "weak-flip-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _B2_INSERT,
                        '  d := d.insert "blank" (KwargVal.flag (!blankAllowed))\n'),
        "refinement": "forwarding the negated flag inverts the consuming "
                      "decision on BOTH halves of the domain at once: an "
                      "attribute permitting an empty value would lose its "
                      "leading empty option and one forbidding it would gain "
                      "one. Its faithful real patch is the exact inverse of "
                      "both relational-attribute-with-radio FAIL_TO_PASS "
                      "expectations, so it resolves nothing.",
        "rationale": "REJECT from the FIRST clause. Witnessed at "
                     "blankAllowed=FALSE — the half where "
                     "weak-const-false-flag is correct — so the two rivals are "
                     "refuted at genuinely different points rather than sharing "
                     "one, and each rationale's claimed sub-domain is the one "
                     "its witness demonstrates. Together the pair varies the "
                     "blankAllowed binder across both values against the same "
                     "empty base. If it VERIFIES => SPEC-TOO-WEAK.",
        "witness": _wit2_flag(_EMPTY_MAP, "false",
                              "an attribute that forbids an empty value: the "
                              "frozen spec forwards that, the rival forwards "
                              "its negation"),
    },

    # FRAME attack #1: build the result from scratch, destroying every other key.
    {
        "id": "weak-clobber-other-keys",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _B2_SEED,
                        "  let mut d : Std.HashMap String KwargVal := ∅\n"),
        "refinement": "writing the dedicated key correctly but discarding every "
                      "OTHER incoming keyword argument means the generated "
                      "field is constructed without the arguments its caller "
                      "assembled. Its faithful real patch would build the "
                      "generated field from the empty-value flag alone, losing "
                      "the collection it draws its options from and every other "
                      "caller-supplied argument, so the generated field cannot "
                      "even produce an option list — the FAIL_TO_PASS tests "
                      "that read that list, and the PASS_TO_PASS suite around "
                      "them, all fail. It does not resolve.",
        "rationale": "REJECT from the SECOND (FRAME) clause "
                     "(`∀ k, k ≠ \"blank\" → result[k]? = base[k]?`), which no "
                     "behavior-2 rival above touches. The rival satisfies the "
                     "first clause perfectly, so this case is the only evidence "
                     "that the frame clause carries force — it is the "
                     "structural counterpart of the nagini sibling's "
                     "read-only-input discipline, which cannot be expressed as "
                     "a permission here but IS expressible as an observable "
                     "component of the result. The witness instantiates the ∀ "
                     "at a non-dedicated key present in `base`. If it VERIFIES "
                     "=> SPEC-TOO-WEAK (an impl could return anything for every "
                     "other key).",
        "witness": _wit2_frame(
            f'({_EMPTY_MAP}.insert "other" (KwargVal.flag true))', "true",
            "other",
            "an unrelated incoming key: the frozen spec preserves it, the "
            "rival drops it"),
    },

    # FRAME attack #2: preserve everything, but ADD a key that was never there.
    {
        "id": "weak-inject-extra-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _B2_INSERT,
            '  d := d.insert "blank" (KwargVal.flag blankAllowed)\n'
            '  d := d.insert "other" (KwargVal.name none)\n'),
        "refinement": "this rival destroys nothing — it writes the dedicated "
                      "key correctly and preserves every incoming entry — but "
                      "it also introduces an argument the caller never "
                      "supplied. Its faithful real patch would pass an extra "
                      "keyword argument down to the generated field's "
                      "constructor, overriding a caller default (or raising on "
                      "an unexpected argument) on EVERY generated field for "
                      "every relational attribute, so the PASS_TO_PASS suite "
                      "around the generated-field paths breaks while the "
                      "radio/empty-value behavior is at best incidentally "
                      "right. It does not resolve.",
        "rationale": "REJECT from the SECOND (FRAME) clause, in the direction "
                     "`weak-clobber-other-keys` does not reach: the frame "
                     "equation is `result[k]? = base[k]?`, an equality in BOTH "
                     "directions, so ADDING a key is as much a violation as "
                     "dropping one. Witnessed at a key ABSENT from `base` "
                     "(`base[k]? = none`, `result[k]? = some …`) — a third "
                     "distinct value of the `base` binder, and the ∀ binder `k` "
                     "is instantiated at the same name as in "
                     "weak-clobber-other-keys but on the opposite side of the "
                     "equation: there the key is present in `base` and missing "
                     "from the result, here it is missing from `base` and "
                     "present in the result. The two frame rivals therefore "
                     "share neither a `base` nor a direction of failure. If it "
                     "VERIFIES => SPEC-TOO-WEAK (the frame clause would only "
                     "forbid changing keys already present, permitting "
                     "arbitrary spurious ones).",
        "witness": _wit2_frame(
            f'({_EMPTY_MAP}.insert "queryset" KwargVal.obj)', "true", "other",
            "a key absent from the incoming map (which carries an unrelated "
            "entry under a different key): the frozen spec leaves the absent "
            "key absent, the rival injects it"),
    },
]


# The axiom lane belongs to G-AX and this gate ignores it. This bundle declares
# no axiom and no opaque callee (meta.json: axioms=[], opaque_callees=[]) —
# both behaviors are modeled deeply over transparent carriers — so there is no
# consumed contract to fuzz here in any case.
AXIOM_TESTS = []
