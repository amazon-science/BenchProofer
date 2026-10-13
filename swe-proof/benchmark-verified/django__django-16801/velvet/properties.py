"""properties.py — G-PBT falsification battery for django__django-16801 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes and stamps with a
verdict. Each SPEC case is a full ``Solution.lean`` variant that shares the
FROZEN spec byte-for-byte (region surgery: only text inside a method's
``-- impl-start`` / ``-- impl-end`` region — which the consumer spec view elides
— is changed, and for one reproved soundness positive the elided
``prove_correct`` tactic body, so ``markers.same_spec`` holds and every
``prove_correct <name>`` obligation survives with a byte-identical STATEMENT) and
swaps in a candidate implementation, checked by the real verifier.
``expect="verify"`` passes iff (in scope AND verifies); ``expect="reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (two contracted methods, both pure over free Bool inputs):

  registerInitHandler (isAbstract hasWidthField hasHeightField : Bool)
      return (out : Bool)
    ensures out = shouldRegister isAbstract hasWidthField hasHeightField    [G1]

      shouldRegister a w h  =  !a && (w || h)

  dimensionWrites (deferred force hasFile hasWidthField widthFilled
                   hasHeightField heightFilled : Bool)
      return (out : DimWrites)
    ensures out = dimUpdate deferred force hasFile hasWidthField widthFilled
                            hasHeightField heightFilled                     [D1]

      dimUpdate ...  =  let dimFilled := !((hasWidthField && !widthFilled)
                                            || (hasHeightField && !heightFilled))
                        let proceed   := !deferred && (hasFile || force)
                                                   && (!dimFilled || force)
                        { writeWidth  := hasWidthField && proceed,
                          writeHeight := hasHeightField && proceed }

registerInitHandler decides whether a post-initialization dimension-sync handler
is attached for a model class: exactly when the model is concrete AND declares at
least one companion dimension field. This is the behaviour the F2P observes — a
concrete model that declares no companion field must have no handler registered
for its class. dimensionWrites models which companion fields one sync pass writes
back: a pass reaches the assignment stage only when the value is not deferred,
either a file is present or the pass is forced, and the fields are not already
populated (unless forced); a declared field is then written, an undeclared one
never is. Both postconditions are GROUNDED in the method's own inputs
(``shouldRegister`` and ``dimUpdate`` are plain ``def``s over ``Bool``s; the
``axioms`` region is empty), so no wrong impl can verify by echoing an opaque
answer-key — it must reproduce the decision.

WHICH CLAUSE CONSTRAINS EACH IMPL.
  * G1 pins the whole registration decision at every (isAbstract, hasWidthField,
    hasHeightField) point. It senses every wrong registration: registering when
    it should not (concrete/no-field, or abstract), and failing to register when
    it should (a single declared field).
  * D1 pins the whole ``DimWrites`` at every input. It senses a wrong proceed
    gate (a dropped deferred/file/already-populated guard, or a force override
    dropped) AND a wrong field selection (writing a field that is not declared,
    or not writing a declared one). Both fields of the result and every gate
    binder are pinned by the single whole-result equality.

CARRIER WIDENING (this bundle vs the nagini sibling). The nagini sibling models
ONLY the registration decision (site 1), as
``attach_post_init_hook(receivers, owner_id, is_abstract, width_target,
height_target)`` whose load-bearing postcondition is a REGISTRATION BICONDITIONAL
over a mutated receiver list held at FULL permission, with the companion-target
names held read-only at half permission. Its ``should_register`` is exactly this
bundle's ``shouldRegister``; its ``configured(name)`` truthiness collapses to the
``hasWidthField`` / ``hasHeightField`` Bools per mapping.md §2. So every nagini
registration case has a counterpart here on ``registerInitHandler``:

    nagini case                     -> here (registerInitHandler)
    ----------------------------------------------------------------------
    always-register-prepatch-bug    -> reg-always-register        PORTED
    and-instead-of-or               -> reg-and-instead-of-or       PORTED
    partial-domain-width-only       -> reg-partial-domain-width    PORTED
    ignore-abstract                 -> reg-ignore-abstract         PORTED
    never-register                  -> reg-never-register          PORTED
    wrong-token                     -> (none)                      NO COUNTERPART
    pos-control-helper              -> pos-reg-decision-local      RE-SHAPED
    pos-control-demorgan            -> pos-reg-demorgan            PORTED (proof retuned)
    admiss-readperm                 -> admiss-gold-total           RE-AIMED
    frame-mutation-width            -> (none)                      VACUOUS

But this bundle ALSO models a SECOND function nagini never contracts: the
synchronization pass ``dimensionWrites`` (site 2), pinned by D1. That obligation
has its own defended-and-attacked surface (positives ``pos-dw-*`` and rivals
``dw-*`` below) with no nagini sibling — this is carrier WIDENING, not fabricated
wrongness: every ``dw-*`` rival is a real divergence with a machine-checked
witness and a faithful-patch refinement argument. (mapping.md §3.1 notes site 2
is a coupled behaviour-preserving refactor whose no-field configuration stays a
no-op — the rivals below attack the OTHER configurations, where dropping a guard
or mis-selecting a field is observable.)

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. Lean and Velvet are referentially
    transparent: there is no heap, no aliasing, no fractional permission. The
    nagini frame-mutation-width rival wrote to the read-only companion-target
    NAME carrier and was rejected for insufficient permission + a read-only pin.
    Here every parameter is an immutable by-value ``Bool``: there is no
    companion-target list to mutate, no aliasing, and no permission system.
    (``dimensionWrites`` does declare a ``let mut proceed`` LOCAL, but a local
    is not caller-visible state — writing it is ordinary computation, not a
    frame violation, and no read-only pin can be attached to it.) The nagini
    WRITE it attacked simply cannot be expressed. No substitute probe is
    fabricated.
  * WRONG-TOKEN — NO COUNTERPART. The nagini rival appended the WRONG identity
    token (owner_id + 1) to the receiver list; the receiver list itself is not
    modeled here (the registration decision is folded to a single ``Bool``
    out — whether the connect happens — per mapping.md §2, not to which token
    was appended). There is no token binder to corrupt, so the rival has nothing
    to land on. Reported as an omission, not faked.
  * UNGROUNDED-ORACLE ECHO — N/A: both postconditions are transparent total
    functions of the method's own arguments (``shouldRegister`` / ``dimUpdate``);
    the ``axioms`` region is empty. There is no answer key to echo; the cheapest
    correct reshapes are carried as positive controls.

CARRIER NOTE — why this port refutes at CONCRETE literals (no conditioning).
Every input is ``Bool``; ``shouldRegister`` returns ``Bool`` and ``dimUpdate``
returns ``DimWrites`` (a two-field structure deriving ``DecidableEq``). The
whole carrier is finite and transparent, so each reject witness reaches the
method's contract through Velvet's own tester machinery
(``registerInitHandlerTester`` / ``dimensionWritesTester``) at a concrete
literal tuple and closes by ``decide`` — no hypothesis about an opaque term is
needed, so no witness binds anything and the gate's consistency probe has
nothing to check. The frozen impls are straight-line and reduce under ``decide``
too; each witness fails against gold purely because gold SATISFIES the spec at
that input (the tester returns ``true``, so ``... = false`` is provably false —
the verifier reports ``decide proved ... is false``). Checked in a file whose
``prove_correct`` blocks are stripped, so no tactic script can mask the verdict.
Every reject witness below was run against the rival (elaborates, exit 0) and
the frozen solution (fails, exit 1) with two real builds.

DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
SEMANTICS against any rival that manufactures it. Every frozen impl region is
LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop and no
recursion), so there is no control flow here to make diverge: a diverging rival
cannot be obtained by mutating this body, it has to bring a loop of its own.
When it does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries an
axiom-soundness/containment pair over the real ``ImageField.contribute_to_class``
registration decision; that is G-AX's job (axiom_check.py / mapping.md §3 — this
bundle declares no axiom and no deep-model reference; the observations are free
Bool inputs) and the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16801"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors: the WHOLE frozen impl body of each method (text
# ---- strictly between that method's `-- impl-start` / `-- impl-end`, comments
# ---- included). Each lies wholly inside one impl region and is unique in
# ---- Solution.lean (both facts asserted at load by _swap), so every variant's
# ---- edit is confined to the elided impl region and same_spec holds by
# ---- construction.
_REG_IMPL = (
    "    let doRegister ← if (!isAbstract && (hasWidthField || hasHeightField)) then\n"
    "        pure true\n"
    "      else\n"
    "        pure false\n"
    "    return doRegister"
)

_DW_IMPL = (
    "    let mut proceed : Bool := true\n"
    "    -- a deferred value: nothing to synchronize\n"
    "    if deferred then\n"
    "      proceed := false\n"
    "    else\n"
    "      proceed := proceed\n"
    "    -- no file present and not forced: nothing to synchronize\n"
    "    if (!hasFile && !force) then\n"
    "      proceed := false\n"
    "    else\n"
    "      proceed := proceed\n"
    "    -- companion fields already populated and not forced: nothing to synchronize\n"
    "    let dimFilled := !((hasWidthField && !widthFilled) || (hasHeightField && !heightFilled))\n"
    "    if (dimFilled && !force) then\n"
    "      proceed := false\n"
    "    else\n"
    "      proceed := proceed\n"
    "    return { writeWidth := hasWidthField && proceed,\n"
    "             writeHeight := hasHeightField && proceed }"
)

assert _BASE.count(_REG_IMPL) == 1, "registerInitHandler impl region drifted"
assert _BASE.count(_DW_IMPL) == 1, "dimensionWrites impl region drifted"

# ---- the frozen registration proof, verbatim. Generic over impl shape enough to
# ---- close the value-preserving reshapes below unchanged; the De Morgan
# ---- positive leaves a residual disjunction the frozen `simp_all` does not close
# ---- alone, so THAT positive (and only it) retunes the elided tactic body (a
# ---- change confined to the proof region, obligation STATEMENT byte-identical).
_REG_PROOF = (
    "prove_correct registerInitHandler by\n"
    "  loom_solve <;> simp_all [shouldRegister]"
)

assert _BASE.count(_REG_PROOF) == 1, "registerInitHandler proof region drifted"


def _reg(new_body):
    """Full Solution.lean variant with ONLY registerInitHandler's impl body
    replaced (spec view and both frozen proofs untouched)."""
    return _swap(_BASE, _REG_IMPL, new_body)


def _reg_reproved(new_body, new_proof):
    """registerInitHandler impl body replaced AND its elided proof tactic retuned
    (obligation STATEMENT byte-identical). For a correct reshape whose residual
    goal the frozen tactic no longer closes."""
    return _swap(_reg(new_body), _REG_PROOF, new_proof)


def _dw(new_body):
    """Full Solution.lean variant with ONLY dimensionWrites' impl body replaced
    (spec view and both frozen proofs untouched)."""
    return _swap(_BASE, _DW_IMPL, new_body)


# ---- witness builders. Both postconditions are decidable (no opaque callee), so
# ---- the tester path is live: `<name>Tester <args> = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Neither method carries a `require` clause, so the
# ---- precondition-decidability directive is omitted. Checked in a file whose
# ---- `prove_correct` blocks are stripped; closes by `decide` on the transparent
# ---- finite carrier. Binds nothing (literal inputs), so the gate's consistency
# ---- probe is a no-op.
def _wit_reg(args):
    return (
        "extract_program_for registerInitHandler\n"
        "prove_postcondition_decidable_for registerInitHandler\n"
        "derive_tester_for registerInitHandler\n\n"
        f"example : registerInitHandlerTester {args} = false := by\n"
        "  decide\n"
    )


def _wit_dw(args):
    return (
        "extract_program_for dimensionWrites\n"
        "prove_postcondition_decidable_for dimensionWrites\n"
        "derive_tester_for dimensionWrites\n\n"
        f"example : dimensionWritesTester {args} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the obligation is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-reg-decision-inline",
        "kind": "soundness",
        "expect": "verify",
        # Reshape registerInitHandler: return the guard boolean directly instead of
        # branching to `pure true`/`pure false` in a monadic `let`. Same decision,
        # a straight-line boolean form; the frozen proof closes unchanged.
        "module": _reg("    return (!isAbstract && (hasWidthField || hasHeightField))"),
        "rationale": (
            "a correct impl of registerInitHandler with a DIFFERENT shape (return "
            "the guard boolean directly rather than branching into a monadic "
            "`let`); the returned value is unchanged so G1 still discharges under "
            "the frozen proof. Ports the nagini pos-control-helper's intent (bind "
            "the should_register decision, then return it) as the cheapest "
            "straight-line reshape on this carrier. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-reg-decision-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: stage the decision boolean in a typed local, then return it —
        # the direct analogue of the nagini pos-control-helper (bind should_register
        # into a typed local `do_register`, then branch/return on it).
        "module": _reg(
            "    let decision : Bool := !isAbstract && (hasWidthField || hasHeightField)\n"
            "    return decision"),
        "rationale": (
            "staging the registration decision in a typed local before returning "
            "it leaves the returned value unchanged, so G1 discharges under the "
            "frozen proof. Direct port of the nagini pos-control-helper (typed "
            "`do_register` local). If it fails => SPEC-TOO-STRONG (over-fit to the "
            "monadic-branch spelling)."
        ),
    },
    {
        "id": "pos-reg-demorgan",
        "kind": "soundness",
        "expect": "verify",
        # Reshape via De Morgan / branch reorder: skip (return false) on
        # `abstract or no-field`, else register. Same decision, opposite control
        # shape. The residual disjunction goal the frozen `simp_all` leaves is
        # closed by `grind`, so the elided proof tactic is retuned — obligation
        # STATEMENT byte-identical.
        "module": _reg_reproved(
            "    if isAbstract || !(hasWidthField || hasHeightField) then\n"
            "      return false\n"
            "    else\n"
            "      return true",
            "prove_correct registerInitHandler by\n"
            "  loom_solve <;> simp_all [shouldRegister] <;> grind"),
        "rationale": (
            "De Morgan of the guard (skip on `abstract or no-field`, else "
            "register): same decision over every (isAbstract, hasWidthField, "
            "hasHeightField) point, different control shape. Ports the nagini "
            "pos-control-demorgan. The polarity flip leaves a residual disjunction "
            "the frozen `simp_all` alone does not close, so the elided proof body "
            "is retuned (`<;> grind`), obligation statement unchanged. Must verify, "
            "else G1 is over-fit to one branch order => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-dw-direct-form",
        "kind": "soundness",
        "expect": "verify",
        # Reshape dimensionWrites: compute `proceed` as one boolean expression (the
        # exact `dimUpdate` shape) instead of threading a `mut` local through three
        # guarded assignments. Same value for every input; the frozen proof closes.
        "module": _dw(
            "    let dimFilled := !((hasWidthField && !widthFilled) || (hasHeightField && !heightFilled))\n"
            "    let proceed := !deferred && (hasFile || force) && (!dimFilled || force)\n"
            "    return { writeWidth := hasWidthField && proceed,\n"
            "             writeHeight := hasHeightField && proceed }"),
        "rationale": (
            "a correct impl of dimensionWrites with a DIFFERENT shape (compute the "
            "proceed gate as one boolean expression rather than threading a `mut` "
            "local through three guarded assignments); the returned DimWrites is "
            "unchanged for every input so D1 discharges under the frozen proof. No "
            "nagini counterpart (nagini does not model site 2); a soundness control "
            "for the widened surface. If it fails => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-readperm. That case
    # established the precondition's read permission suffices to evaluate the
    # decision on a normal F2P-shaped input. Neither method here carries a
    # `require` clause (both total over their Bool inputs), so the classic
    # "a normal input is admitted" probe is vacuous. Re-aimed at the residual
    # total-domain risk: that the two post-images (G1 and D1) are jointly
    # SATISFIABLE by a gold-shaped computation. The frozen impls discharging both
    # ensures IS that witness. MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impls; same_spec trivially, must verify
        "rationale": (
            "neither method carries a `require`, so both are total over their Bool "
            "inputs; the gold impls discharging G1 and D1 are the admissibility "
            "witness that both post-images are satisfiable across the whole input "
            "domain. Re-aimed from the nagini admiss-readperm, whose "
            "precondition-admits-a-normal-input half has no counterpart on this "
            "referentially-transparent carrier with no require clause. Else "
            "SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals on registerInitHandler (G1) — the ported
    # nagini registration rivals. Each is a wrong impl sharing the frozen spec that
    # MUST be rejected, with a machine-checked refutation witness at a concrete
    # (isAbstract, hasWidthField, hasHeightField) point and the refinement argument
    # for why its faithful real patch would NOT resolve the F2P/P2P tests. The
    # three binders are varied across the witnesses: isAbstract ∈ {false, true},
    # hasWidthField ∈ {false, true}, hasHeightField ∈ {false, true}.
    # =====================================================================
    {
        "id": "reg-always-register",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug: register for every concrete class, ignoring the
        # companion fields entirely (the pre-patch guard `if not abstract:`).
        "module": _reg("    return (!isAbstract)"),
        "refinement": (
            "this is the pre-change decision (register whenever the model is "
            "concrete, disregarding the companion fields). Its faithful real patch "
            "is the unpatched repo: a concrete model that declares no companion "
            "field STILL has the post-init handler registered for its class — "
            "exactly what the failing test asserts must NOT happen. This is the "
            "exact defect the fix corrects, so the faithful patch does NOT resolve."
        ),
        "rationale": (
            "REJECT from G1 (out = shouldRegister …) at (isAbstract=false, "
            "hasWidthField=false, hasHeightField=false): gold demands false (no "
            "field ⇒ no handler) but the rival returns true. Ports the nagini "
            "always-register-prepatch-bug. Refuted at `false false false`. If it "
            "verified => SPEC-TOO-WEAK (admits the very bug the patch fixes)."
        ),
        "witness": _wit_reg("false false false"),
    },
    {
        "id": "reg-and-instead-of-or",
        "kind": "uniqueness",
        "expect": "reject",
        # Register only when BOTH companion fields are declared (AND for OR).
        "module": _reg("    return (!isAbstract && (hasWidthField && hasHeightField))"),
        "refinement": (
            "requires BOTH companion fields to be declared. A faithful real patch "
            "of this shape would not register the handler for a single-field "
            "(width-only or height-only) concrete model, so its dimension-sync "
            "hook never connects and the stored dimensions go stale — the P2P "
            "dimension-update tests for single-field models fail. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from G1 at (isAbstract=false, hasWidthField=true, "
            "hasHeightField=false): gold demands true (a declared width field ⇒ "
            "register) but the AND rival returns false. Ports the nagini "
            "and-instead-of-or. Refuted at `false true false` — varies hasWidthField "
            "to true. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _wit_reg("false true false"),
    },
    {
        "id": "reg-partial-domain-width",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: key the decision on the width field alone, dropping the
        # height field. Correct except on a height-only concrete model.
        "module": _reg("    return (!isAbstract && hasWidthField)"),
        "refinement": (
            "keys the registration on the width field alone, dropping the height "
            "field from the decision. A faithful real patch of this shape would "
            "not register the handler for a height-only concrete model, whose "
            "dimension-sync hook then never fires, leaving its height dimension "
            "stale — the P2P dimension-update tests for a height-only model fail. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECT from G1 at (isAbstract=false, hasWidthField=false, "
            "hasHeightField=true): gold demands true (a declared height field ⇒ "
            "register) but the width-only rival returns false. Ports the nagini "
            "partial-domain-width-only. Refuted at `false false true` — the only "
            "reject point that varies hasHeightField to true while holding "
            "hasWidthField false, so the height field is exercised as the SOLE "
            "reason to register. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _wit_reg("false false true"),
    },
    {
        "id": "reg-ignore-abstract",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `!isAbstract` conjunct: register whenever a field is declared,
        # even for abstract base classes.
        "module": _reg("    return (hasWidthField || hasHeightField)"),
        "refinement": (
            "drops the concreteness conjunct: registers the handler for abstract "
            "base classes that declare a companion field. A faithful real patch of "
            "this shape would attach the post-init handler to abstract models — "
            "which have no instances and were never intended to register — "
            "regressing the P2P abstract-model expectations (no handler on abstract "
            "bases). Does NOT resolve."
        ),
        "rationale": (
            "REJECT from G1 at (isAbstract=true, hasWidthField=true, "
            "hasHeightField=false): gold demands false (abstract ⇒ no handler) but "
            "the rival returns true. Ports the nagini ignore-abstract. Refuted at "
            "`true true false` — the ONLY reject point that varies isAbstract to "
            "true, so that binder is exercised. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _wit_reg("true true false"),
    },
    {
        "id": "reg-never-register",
        "kind": "uniqueness",
        "expect": "reject",
        # No-op decision: never register. Trivially wrong on every should-register
        # input. Cheap supporting near-miss.
        "module": _reg("    return false"),
        "refinement": (
            "never registers the handler for any model. A faithful real patch that "
            "removed the connect call entirely would leave NO model recomputing its "
            "companion dimensions on init, breaking every P2P dimension-update test. "
            "Does NOT resolve. Cheap supporting near-miss."
        ),
        "rationale": (
            "REJECT from G1 at (isAbstract=false, hasWidthField=true, "
            "hasHeightField=true): gold demands true (a declared field ⇒ register) "
            "but the constant rival returns false. Ports the nagini never-register. "
            "Refuted at `false true true` — a DISTINCT point (both fields declared) "
            "from the other reject witnesses. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _wit_reg("false true true"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals on dimensionWrites (D1) — the WIDENED
    # surface with no nagini counterpart (nagini does not contract site 2). Each is
    # a real divergence of the synchronization-pass decision with a machine-checked
    # witness and a faithful-patch refinement argument. Together they attack every
    # gate of `dimUpdate` (deferred / file-or-force / already-populated-unless-
    # forced) and its field-selection, and vary all seven binders.
    # =====================================================================
    {
        "id": "dw-drop-deferred-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the deferred guard: sync even a deferred value.
        "module": _dw(
            "    let mut proceed : Bool := true\n"
            "    if (!hasFile && !force) then\n"
            "      proceed := false\n"
            "    else\n"
            "      proceed := proceed\n"
            "    let dimFilled := !((hasWidthField && !widthFilled) || (hasHeightField && !heightFilled))\n"
            "    if (dimFilled && !force) then\n"
            "      proceed := false\n"
            "    else\n"
            "      proceed := proceed\n"
            "    return { writeWidth := hasWidthField && proceed,\n"
            "             writeHeight := hasHeightField && proceed }"),
        "refinement": (
            "drops the deferred-value guard: a pass on a value not yet loaded would "
            "still write back companion fields. A faithful real patch that removed "
            "the deferred short-circuit would touch a deferred attribute during "
            "sync, forcing a database load (or writing a stale value) exactly where "
            "the code deliberately does nothing — the P2P defer test "
            "(ImageFieldTests.test_defer) fails. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from D1 at (deferred=true, force=false, hasFile=true, "
            "hasWidthField=true, widthFilled=false, hasHeightField=false, "
            "heightFilled=false): gold's proceed is false (deferred) so writeWidth "
            "= false, but the rival proceeds and writes width. Refuted at "
            "`true false true true false false false`. If it verified => "
            "SPEC-TOO-WEAK (the deferred gate unconstrained)."
        ),
        "witness": _wit_dw("true false true true false false false"),
    },
    {
        "id": "dw-drop-file-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the file-present/force guard: sync with no file and not forced.
        "module": _dw(
            "    let mut proceed : Bool := true\n"
            "    if deferred then\n"
            "      proceed := false\n"
            "    else\n"
            "      proceed := proceed\n"
            "    let dimFilled := !((hasWidthField && !widthFilled) || (hasHeightField && !heightFilled))\n"
            "    if (dimFilled && !force) then\n"
            "      proceed := false\n"
            "    else\n"
            "      proceed := proceed\n"
            "    return { writeWidth := hasWidthField && proceed,\n"
            "             writeHeight := hasHeightField && proceed }"),
        "refinement": (
            "drops the file-present-or-forced guard: a pass with no bound file and "
            "no force would still write companion fields. A faithful real patch of "
            "this shape would compute dimensions off an absent file (clearing or "
            "erroring) where the code must leave the fields untouched — the P2P "
            "'assigning ImageField to None clears dimensions' / no-file-in-"
            "constructor tests fail. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from D1 at (deferred=false, force=false, hasFile=false, "
            "hasWidthField=true, widthFilled=false, hasHeightField=false, "
            "heightFilled=false): gold's proceed is false (no file, not forced) so "
            "writeWidth = false, but the rival proceeds and writes width. Refuted "
            "at `false false false true false false false` — varies hasFile to "
            "false. If it verified => SPEC-TOO-WEAK (the file/force gate "
            "unconstrained)."
        ),
        "witness": _wit_dw("false false false true false false false"),
    },
    {
        "id": "dw-drop-populated-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the already-populated guard: re-sync fields that are already filled
        # even when not forced. Attacked on a HEIGHT-filled config (varies the
        # height binders).
        "module": _dw(
            "    let mut proceed : Bool := true\n"
            "    if deferred then\n"
            "      proceed := false\n"
            "    else\n"
            "      proceed := proceed\n"
            "    if (!hasFile && !force) then\n"
            "      proceed := false\n"
            "    else\n"
            "      proceed := proceed\n"
            "    return { writeWidth := hasWidthField && proceed,\n"
            "             writeHeight := hasHeightField && proceed }"),
        "refinement": (
            "drops the already-populated guard: a non-forced pass would overwrite "
            "companion fields that already hold a value. A faithful real patch that "
            "removed this short-circuit would recompute and re-write dimensions on "
            "every ordinary post-init even when they are already set, resurrecting "
            "the very redundant work whose no-op the P2P dimension-update tests "
            "assert (fields already populated stay untouched unless forced). Does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from D1 at (deferred=false, force=false, hasFile=true, "
            "hasWidthField=false, widthFilled=false, hasHeightField=true, "
            "heightFilled=true): dimFilled is true (the sole declared field is "
            "already filled) and not forced, so gold's proceed is false and "
            "writeHeight = false, but the rival proceeds and writes height. Refuted "
            "at `false false true false false true true` — the point that varies "
            "hasHeightField and heightFilled to true. If it verified => "
            "SPEC-TOO-WEAK (the already-populated gate unconstrained)."
        ),
        "witness": _wit_dw("false false true false false true true"),
    },
    {
        "id": "dw-force-not-overriding-populated",
        "kind": "uniqueness",
        "expect": "reject",
        # The already-populated guard fires even under force (drops the `|| force`
        # override): a forced pass on already-filled fields would wrongly skip.
        "module": _dw(
            "    let mut proceed : Bool := true\n"
            "    if deferred then\n"
            "      proceed := false\n"
            "    else\n"
            "      proceed := proceed\n"
            "    if (!hasFile && !force) then\n"
            "      proceed := false\n"
            "    else\n"
            "      proceed := proceed\n"
            "    let dimFilled := !((hasWidthField && !widthFilled) || (hasHeightField && !heightFilled))\n"
            "    if dimFilled then\n"
            "      proceed := false\n"
            "    else\n"
            "      proceed := proceed\n"
            "    return { writeWidth := hasWidthField && proceed,\n"
            "             writeHeight := hasHeightField && proceed }"),
        "refinement": (
            "makes the already-populated guard fire even under force (drops the "
            "force override on that guard). A faithful real patch of this shape "
            "would skip the write on a FORCED pass whose fields happen to be "
            "populated — but a forced pass is exactly how a value assignment "
            "refreshes dimensions, so the recomputed dimensions never land — the "
            "P2P assignment/dimension-update tests (force=True refresh) fail. Does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from D1 at (deferred=false, force=true, hasFile=false, "
            "hasWidthField=true, widthFilled=true, hasHeightField=false, "
            "heightFilled=false): the field is populated but force is set, so "
            "gold's proceed is true and writeWidth = true, but the rival's guard "
            "fires and writeWidth = false. Refuted at "
            "`false true false true true false false` — varies force and "
            "widthFilled to true. If it verified => SPEC-TOO-WEAK (the force "
            "override on the populated gate unconstrained)."
        ),
        "witness": _wit_dw("false true false true true false false"),
    },
    {
        "id": "dw-write-ignores-field-declared",
        "kind": "uniqueness",
        "expect": "reject",
        # Field-selection attack: write the width slot from `proceed` alone,
        # ignoring whether a width field is declared.
        "module": _dw(
            "    let mut proceed : Bool := true\n"
            "    if deferred then\n"
            "      proceed := false\n"
            "    else\n"
            "      proceed := proceed\n"
            "    if (!hasFile && !force) then\n"
            "      proceed := false\n"
            "    else\n"
            "      proceed := proceed\n"
            "    let dimFilled := !((hasWidthField && !widthFilled) || (hasHeightField && !heightFilled))\n"
            "    if (dimFilled && !force) then\n"
            "      proceed := false\n"
            "    else\n"
            "      proceed := proceed\n"
            "    return { writeWidth := proceed,\n"
            "             writeHeight := hasHeightField && proceed }"),
        "refinement": (
            "writes the width slot whenever the pass proceeds, regardless of "
            "whether a width field is declared. A faithful real patch of this shape "
            "would setattr a width attribute that the model does not define, "
            "raising AttributeError during ordinary init of a height-only model — "
            "the P2P constructor/assignment tests for a single-field model fail. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECT from D1 at (deferred=false, force=false, hasFile=true, "
            "hasWidthField=false, widthFilled=false, hasHeightField=true, "
            "heightFilled=false): the pass proceeds and gold's writeWidth = "
            "hasWidthField && proceed = false (no width field declared), but the "
            "rival's writeWidth = proceed = true. Refuted at "
            "`false false true false false true false`. If it verified => "
            "SPEC-TOO-WEAK (the field-selection dependence on hasWidthField "
            "unconstrained)."
        ),
        "witness": _wit_dw("false false true false false true false"),
    },
    {
        "id": "dw-dimfilled-ignores-declared",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Every other dw-* rival drops or re-polarises a WHOLE
        # gate; none perturbs the INTERNAL composition of `dimFilled`, so the
        # spec's "already populated" = "every DECLARED companion field holds a
        # value" reading was unattacked. This rival computes it as `widthFilled
        # && heightFilled` — requiring BOTH slots filled regardless of which
        # fields are declared. A near-miss: it agrees with gold at 126 of the 128
        # input points, diverging only where exactly one field is declared AND
        # its slot is filled.
        "module": _dw(
            "    let mut proceed : Bool := true\n"
            "    if deferred then\n"
            "      proceed := false\n"
            "    else\n"
            "      proceed := proceed\n"
            "    if (!hasFile && !force) then\n"
            "      proceed := false\n"
            "    else\n"
            "      proceed := proceed\n"
            "    let dimFilled := widthFilled && heightFilled\n"
            "    if (dimFilled && !force) then\n"
            "      proceed := false\n"
            "    else\n"
            "      proceed := proceed\n"
            "    return { writeWidth := hasWidthField && proceed,\n"
            "             writeHeight := hasHeightField && proceed }"),
        "refinement": (
            "reads 'already populated' off BOTH companion slots rather than off "
            "the DECLARED ones. A faithful real patch of this shape would keep "
            "re-deriving dimensions for a single-field model whose one declared "
            "field is already set — because the other, undeclared slot reads as "
            "unfilled — so an ordinary post-init on a width-only model repeats "
            "the work the short-circuit exists to skip, and it opens the file to "
            "do it. The P2P dimension-update tests for single-field models "
            "observe that a populated single-field model is a no-op unless "
            "forced. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from D1 at (deferred=false, force=false, hasFile=true, "
            "hasWidthField=true, widthFilled=true, hasHeightField=false, "
            "heightFilled=false): the sole DECLARED field (width) is filled, so "
            "gold's dimFilled is true, proceed is false and writeWidth = false; "
            "the rival's dimFilled is `widthFilled && heightFilled` = false (the "
            "UNDECLARED height slot is empty), so it proceeds and writeWidth = "
            "true. Attacks the one D1 sub-clause the other dw-* rivals leave "
            "untouched — how dimFilled QUANTIFIES over declared fields, rather "
            "than whether the gate it feeds exists. Refuted at "
            "`false false true true true false false`, a point no other witness "
            "uses. If it verified => SPEC-TOO-WEAK (dimFilled's dependence on "
            "hasWidthField/hasHeightField unconstrained)."
        ),
        "witness": _wit_dw("false false true true true false false"),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING. The nagini sibling has 10 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals, 1 mandatory frame-mutation, 1
# extra never-register near-miss) plus a 2-entry AXIOM lane, over ONE modeled
# function (site 1, the registration decision), whose load-bearing postcondition
# is a REGISTRATION BICONDITIONAL over a mutated receiver list (FULL permission)
# with read-only companion-target names (half permission). THIS bundle models the
# SAME registration decision as `registerInitHandler` (its `shouldRegister` ==
# the nagini `should_register`; the receiver list folds to a single `out : Bool`
# — whether the connect happens — and the target-name truthiness folds to the
# `hasWidthField`/`hasHeightField` Bools, mapping.md §2) AND, additionally, a
# SECOND function nagini never contracts: the synchronization pass
# `dimensionWrites` (site 2), pinned by D1.
#
#   nagini case                    -> here
#   -----------------------------------------------------------------------
#   pos-control-helper             -> pos-reg-decision-local        RE-SHAPED (direct port)
#   pos-control-demorgan           -> pos-reg-demorgan              PORTED (proof retuned)
#   admiss-readperm                -> admiss-gold-total             RE-AIMED
#   always-register-prepatch-bug   -> reg-always-register          PORTED (THE bug-delta)
#   and-instead-of-or              -> reg-and-instead-of-or         PORTED
#   partial-domain-width-only      -> reg-partial-domain-width      PORTED
#   ignore-abstract                -> reg-ignore-abstract           PORTED
#   never-register                 -> reg-never-register            PORTED
#   wrong-token                    -> (none)                        NO COUNTERPART
#   frame-mutation-width           -> (none)                        VACUOUS
#   (new, no sibling)              -> pos-reg-decision-inline       ADDED (reshape)
#   (new, no sibling)              -> pos-dw-direct-form            ADDED (site 2 defend)
#   (new, no sibling)              -> dw-drop-deferred-guard        ADDED (site 2, D1)
#   (new, no sibling)              -> dw-drop-file-guard            ADDED (site 2, D1)
#   (new, no sibling)              -> dw-drop-populated-guard       ADDED (site 2, D1)
#   (new, no sibling)              -> dw-force-not-overriding-populated  ADDED (site 2, D1)
#   (new, no sibling)              -> dw-write-ignores-field-declared    ADDED (site 2, D1)
#   (new, no sibling)              -> dw-dimfilled-ignores-declared  ADDED BY AUDIT (site 2, D1)
#   AXIOM_TESTS (2)                -> (none)                        DROPPED (G-AX lane)
#
# 16 velvet SPEC cases: 4 soundness, 1 admissibility, 11 uniqueness. Both modeled
# obligations are DEFENDED and ATTACKED: registerInitHandler (G1) by
# pos-reg-decision-inline / pos-reg-decision-local / pos-reg-demorgan and the five
# reg-* rivals; dimensionWrites (D1) by pos-dw-direct-form and the six dw-* rivals.
#
# PORTED (5 rivals + 2 positives, registerInitHandler / site 1): every nagini
#   registration case attacking a modeled facet of the biconditional carries
#   across; only the carrier changes (a mutated receiver list + read-only target
#   names folds to a single returned Bool decision over three Bool inputs).
#   reg-always-register (the pre-patch bug; G1), reg-and-instead-of-or (single-
#   field models drop out; G1), reg-partial-domain-width (height-only drops out;
#   G1), reg-ignore-abstract (abstract registers; G1), reg-never-register (cheap
#   near-miss; G1). Each keeps its nagini refinement argument, now backed by a
#   machine-checked witness. The two positives port the nagini soundness controls;
#   the De Morgan positive retunes the elided proof tactic (`<;> grind`) with a
#   byte-identical obligation statement.
# RE-AIMED (admiss-readperm -> admiss-gold-total): the nagini case established the
#   read permission suffices to evaluate the decision on a normal input. Neither
#   method here carries a `require`, so that probe is vacuous; re-aimed at the
#   residual total-domain risk (G1 and D1 jointly satisfiable), witnessed by the
#   frozen impls.
# NO COUNTERPART (wrong-token): the nagini rival appended the WRONG identity token
#   (owner_id + 1) to the receiver list. The receiver list is not modeled here —
#   the registration decision folds to a single Bool (whether the connect happens),
#   not to which token was appended (mapping.md §2) — so there is no token binder
#   to corrupt. Omitted because the modeled surface does not include it, NOT
#   because it was hard to prove.
# VACUOUS (frame-mutation-width): the nagini rival wrote to the read-only
#   companion-target NAME carrier (rejected for insufficient permission + a
#   read-only pin). Lean/Velvet are referentially transparent: no heap, no
#   aliasing, no permission system, and every parameter is an immutable
#   by-value Bool — the nagini WRITE cannot be expressed. (The `let mut proceed`
#   local in dimensionWrites is not caller-visible state, so writing it is
#   ordinary computation, not a frame violation.) No substitute fabricated.
# ADDED — SITE 2 (pos-dw-direct-form + 6 dw-* rivals): this bundle contracts a
#   SECOND function (dimensionWrites) that nagini never models. It gets its own
#   defended (pos-dw-direct-form) and attacked (dw-*) surface. The dw-* rivals each
#   drop or mis-wire one gate of `dimUpdate` — the deferred guard, the
#   file-or-force guard, the already-populated guard, the force override on that
#   guard, the field-selection dependence on hasWidthField, and (added by audit)
#   dimFilled's quantification over the DECLARED fields — and each is a real
#   divergence with a machine-checked witness and a faithful-patch refinement
#   argument grounded in the P2P dimension-update / defer / no-file tests. Carrier
#   WIDENING, not fabricated wrongness. (mapping.md §3.1: the no-declared-field
#   configuration of site 2 is a coupled behaviour-preserving no-op, so no rival
#   attacks THAT configuration — the rivals attack the configurations where a
#   dropped guard or mis-selected field IS observable.)
# ADDED — SITE 1 (pos-reg-decision-inline): a second cheapest correct reshape
#   (return the guard boolean directly) alongside the typed-local port, defending
#   G1 against over-fit to the monadic-branch spelling.
# DROPPED (AXIOM_TESTS, 2): the nagini file's axiom-soundness/containment probes
#   over the real ImageField.contribute_to_class registration decision are G-AX's
#   job (axiom_check.py / mapping.md §3 — this bundle declares no axiom and no
#   deep-model reference); the G-PBT gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE.
#   * G1 (registerInitHandler) attacked at `false false false` (always-register),
#     `false true false` (and), `false false true` (partial-width), `true true
#     false` (ignore-abstract), `false true true` (never). All three binders vary:
#     isAbstract ∈ {false, true}, hasWidthField ∈ {false, true}, hasHeightField ∈
#     {false, true}. 5 distinct points.
#   * D1 (dimensionWrites) attacked at `true false true true false false false`
#     (deferred), `false false false true false false false` (file/force),
#     `false false true false false true true` (populated), `false true false true
#     true false false` (force override), `false false true false false true false`
#     (field-selection), `false false true true true false false` (dimFilled's
#     quantification over declared fields — ADDED BY AUDIT). All seven binders vary
#     across these points: deferred, force, hasFile, hasWidthField, widthFilled,
#     hasHeightField, heightFilled each take both true and false. 6 distinct points.
#   * Total reject points: 11 distinct (pts=11); no binder of either method is held
#     fixed by every witness.
#   * CLAUSE depth on D1: five rivals attack whether a GATE exists or is correctly
#     polarised; dw-dimfilled-ignores-declared attacks the internal composition of
#     `dimFilled` (that "already populated" quantifies over the DECLARED fields),
#     which no whole-gate rival senses.
# FRAME-MUTATION: VACUOUS (see above). Referentially-transparent backend, no `mut`
#   binder, no heap, no permission system. Nagini's mandatory frame case has no
#   expressible substitute.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
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
# WITNESS MECHANICS: both postconditions are decidable (Bool inputs; shouldRegister
#   returns Bool, dimUpdate returns DimWrites deriving DecidableEq; no opaque
#   callee), so every witness reaches the contract through Velvet's tester
#   machinery (`registerInitHandlerTester` / `dimensionWritesTester`) at a concrete
#   literal tuple and closes by `decide`. No witness binds a hypothesis, so the
#   gate's consistency probe is a no-op. The frozen impls are straight-line and
#   reduce under `decide` too; each witness fails against gold because gold
#   SATISFIES the spec at that input (tester returns true, so `... = false` is
#   provably false). All eleven checked with scripts/lean_verify.sh: rival build
#   exit 0 (elaborates), gold build exit 1 (`decide proved ... is false`) — every
#   gold-side failure read and confirmed to be that SEMANTIC message, not a
#   missing identifier, type error, stuck reduction, or timeout.
#
# AUDIT RECORD (independent re-derivation, not the port's self-report). Attack A:
#   every case's module diffed against the frozen file — all deltas confined to an
#   impl region, plus pos-reg-demorgan's elided prove_correct tactic body; no
#   `ensures` line altered anywhere. Attack B: all reject witnesses rebuilt on both
#   sides (exits above). Attack C: a full truth-table sweep (8 points for G1, 128
#   for D1) confirms every rival diverges from gold observably and that each
#   witness point lies inside its own rival's divergence set — no vacuous case.
#   Attack D: five NEW wrong impls beyond the battery (registration on XOR of the
#   two fields; `||` for `&&` on the concreteness conjunct; the two write slots
#   swapped; file-AND-force for file-OR-force; dimFilled off both slots) were all
#   REJECTED, so no SPEC-TOO-WEAK hole; the last was retained as
#   dw-dimfilled-ignores-declared. Attack E: four NEW correct reshapes (a `match`
#   on the three-Bool tuple; a nested-if ladder; dimensionWrites returning
#   `dimUpdate` applied directly; a De Morgan'd dimFilled; a single-guard early
#   return) all VERIFY — the `match` needs the same `<;> grind` retune
#   pos-reg-demorgan already uses, which is a tactic artifact confined to the
#   elided proof region, not a spec rejection. So D1/G1 are neither too weak nor
#   too strong on the surfaces probed.
AXIOM_TESTS = []
