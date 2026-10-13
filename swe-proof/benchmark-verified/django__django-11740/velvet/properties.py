"""properties.py — G-PBT falsification battery for django__django-11740 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
Every case's statement was diffed against the frozen file outside the impl
region and is byte-identical; two cases (``pos-decomposed-append`` and the
admissibility case) additionally retune the elided TACTIC BODY, which leaves the
``prove_correct`` header and the ``ensures`` clause untouched.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over a fully TRANSPARENT carrier). The
routine computes the ordering dependencies attached to the operation that
reshapes one model field into its new form:

  alteredFieldDependencies (isReferential : Bool) (f : RelField)
      return (out : List Dep)
    ensures out = (if isReferential then relationDeps f else [])

The postcondition is a two-arm conditional over the referential flag, and its
referential arm is pinned EXACTLY to ``relationDeps f`` — a concrete, transparent
function of the field's referential configuration:

  * ``relationDeps f`` = always the base dependency on the model the field points
    at, PLUS an extra dependency on the intermediary model when the relation is
    routed through one (``f.through = some (..)``);
  * ``baseDep f`` = the swappable-setting sentinel when the target is swappable
    (``f.swappable = some s``), otherwise the target model itself.

There is NO opaque answer key to echo: ``relationDeps``/``baseDep``/``mkDep`` are
concrete defs and the result is grounded in the actual input carrier ``f``
(directive 8), so the carrier COMPUTES and every witness settles by ``decide`` at
literal inputs. The behaviour pinned is that a field which now references another
model records EXACTLY the dependencies that reference induces (so the change is
sequenced after the models it refers to), and a field that references no model
records NONE.

BINDER STRUCTURE (read this before judging binder coverage). The postcondition
depends on BOTH inputs and, through ``f``, on three sub-configurations:

  * ``isReferential : Bool`` — selects the arm. The whole bug is the referential
    arm returning ``[]`` (no dependency) instead of ``relationDeps f``.
  * ``f.targetApp`` / ``f.targetObj`` — the identity of the referenced model,
    surfaced in ``baseDep`` on the non-swappable path.
  * ``f.through : Option (String × String)`` — present ⇒ ``relationDeps`` emits a
    SECOND dependency on the intermediary model.
  * ``f.swappable : Option String`` — present ⇒ ``baseDep`` swaps to the setting
    sentinel instead of the target model.

The reject witnesses below move all of these: ``isReferential`` across
{true, false}; ``f.through`` across {none, some}; ``f.swappable`` across
{none, some}; and the referenced-model identity is attacked by a wrong-constant
rival. Every top-level arm of the postcondition and every sub-arm of the pinned
``relationDeps`` is attacked by some rival. Moving each sub-arm binder ALONE is
not sufficient, because a rival can be right on each sub-arm in isolation and
wrong where they meet: ``swappable-shadows-through`` is refuted at the one input
where ``f.through`` and ``f.swappable`` are BOTH ``some``, the interaction point
the two single-sub-arm rivals each hold at ``none``.

ADMISSIBILITY is present (``admiss-f2p-obligation-satisfiable``) even though the
frozen method has no ``require`` clause. The absence of a precondition is NOT a
reason to drop the lane: on a total carrier the PRECOND-TOO-STRONG analogue is
the obligation being unsatisfiable or degenerate at an F2P-shaped input, which
that case tests by evaluation at the concrete F2P configuration. See the
accounting block at the bottom.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS. The nagini sibling carries this MANDATORY because
    its ``new_field`` input is held at a fractional heap permission
    (``Acc(.,1/2)``) an impl can illegally overwrite (forcing the referential
    flag false to make the relational clause vacuous). Lean/Velvet are
    referentially transparent: ``isReferential`` and ``f`` are immutable values,
    there is no ``mut`` binder, no heap and no aliasing — so there is no
    read-only field to mutate and no substitute probe to build. Not fabricated
    (per the porting map: this class is vacuous here).
  * UNGROUNDED-ORACLE ECHO — N/A here. The nagini sibling axiomatised
    ``fk_dependencies`` as an opaque ``@ContractOnly`` oracle and pinned the
    relational arm by EXACT equality to it, so a wrong non-empty echo could not
    be shown equal. This bundle models that computation DEEPLY (``relationDeps``,
    an A-reference validated == the real callee by G-AX; mapping.md §3.1), so the
    arm is pinned to a TRANSPARENT term and the analogous attacks (wrong constant,
    dropped through, ignored swappable) are refutable by ``decide`` at literal
    inputs rather than by an opacity argument. The ``axioms`` region declares no
    ``axiom``.

WITNESS PLACEMENT. Each reject rival is refuted at a concrete input reaching the
postcondition through Velvet's own tester machinery
(``alteredFieldDependenciesTester isReferential f = false`` says the extracted
program's result violates the postcondition there). There are no ``require``
clauses, so every input reaches the postcondition (nothing is vacuously
excluded). No two rivals are refuted at the same input tuple.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the delegated
per-field computation is modeled deeply as an A-reference, not a consumed
oracle). The gate ignores ``AXIOM_TESTS`` regardless; see the accounting block
at the bottom for the nagini→velvet correspondence.
"""
from pathlib import Path

INSTANCE = "django__django-11740"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. Lies wholly inside the single impl region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap). The three
# ---- comment lines above the code are ALSO inside the impl region; anchoring on
# ---- the three code lines keeps the surgery within the elided region. ----
_IMPL = (
    "    let mut deps : List Dep := []\n"
    "    if isReferential then\n"
    "      deps := relationDeps f\n"
    "    return deps"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched).

    Cases built through THIS helper keep the frozen ``prove_correct
    alteredFieldDependencies by loom_solve`` script verbatim: those soundness
    reshapes collapse to the frozen conditional so ``loom_solve`` still closes
    them (verified out-of-band with real builds), and each reject rival is judged
    by its witness, not by whether the frozen script happens to break on the
    reshape. Two cases need the elided tactic body retuned instead and use
    ``_with_impl_and_proof``.
    """
    return _swap(_BASE, _IMPL, new_impl)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `alteredFieldDependenciesTester isReferential f = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict. `Dep`/`RelField` are transparent
# ---- structures over `String`/`Option`/`Bool`, so `decide` settles every input.
_TESTER = (
    "extract_program_for alteredFieldDependencies\n"
    "prove_precondition_decidable_for alteredFieldDependencies\n"
    "prove_postcondition_decidable_for alteredFieldDependencies\n"
    "derive_tester_for alteredFieldDependencies\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (as is the impl region), so retuning it keeps
# ---- `markers.same_spec` and leaves the obligation's STATEMENT byte-identical:
# ---- the header `prove_correct alteredFieldDependencies` and the `ensures`
# ---- clause it discharges are untouched. Needed by two cases below whose goal
# ---- the frozen one-liner cannot close for a purely tactical reason (a `match`
# ---- on `f.through` the frozen script never case-splits, and the extra
# ---- in-region `assert` goal an admissibility case introduces).
_PROOF = "prove_correct alteredFieldDependencies by\n  loom_solve"


def _with_impl_and_proof(new_impl: str, new_tactics: str) -> str:
    """Impl body AND `prove_correct` tactic body replaced; spec view untouched."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF,
                 "prove_correct alteredFieldDependencies by\n" + new_tactics)


# ---- the F2P-shaped input: the referential arm at a plain cross-app reference
# ---- (no intermediary, non-swappable) — the configuration the new failing test
# ---- exercises. Used by the admissibility case below.
_F2P = ('{ targetApp := "testapp", targetObj := "Author", '
        'through := none, swappable := none }')


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify, else SPEC-TOO-STRONG. Both collapse to the
    # frozen conditional, so the byte-identical `loom_solve` obligation closes
    # with no retune (each verified out-of-band with a real build).
    # =====================================================================
    {
        "id": "pos-if-expression",
        "kind": "soundness",
        "expect": "verify",
        # A single `let` bound to the conditional expression, no mutable seed and
        # no imperative `if` statement. Same value on both arms as the frozen
        # skeleton; MUST verify.
        "module": _with_impl(
            "    let deps : List Dep := if isReferential then relationDeps f else []\n"
            "    return deps"),
        "rationale": "structurally different CORRECT reshape (pure conditional "
                     "expression, no mutable accumulator / imperative branch) with "
                     "the identical value on both arms of `out = if isReferential "
                     "then relationDeps f else []`. A faithful reshape MUST verify, "
                     "else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-match-on-flag",
        "kind": "soundness",
        "expect": "verify",
        # Dispatch the referential flag with a `match` rather than an `if`. Same
        # value on both arms; MUST verify.
        "module": _with_impl(
            "    let deps : List Dep :=\n"
            "      match isReferential with\n"
            "      | true  => relationDeps f\n"
            "      | false => []\n"
            "    return deps"),
        "rationale": "second CORRECT reshape dispatching the referential flag with "
                     "a `match` instead of an `if`; both arms match the pinned "
                     "conditional, so it MUST verify. A structural variation that "
                     "the spec accepts, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-decomposed-append",
        "kind": "soundness",
        "expect": "verify",
        # A THIRD correct reshape, and the only positive that does not name
        # `relationDeps` at all: it rebuilds the referential arm's value
        # compositionally as the base dependency APPENDED to the (possibly empty)
        # intermediary contribution. Unlike the two positives above — which return
        # the pinned term `relationDeps f` verbatim and so are definitionally the
        # frozen value on the nose — this one forces the checker to prove
        # `[baseDep f] ++ (match f.through with ..) = relationDeps f`, i.e. to
        # relate a decomposed construction to the pinned one across BOTH sub-arms
        # of `relationDeps`. That is the positive direction of the same sub-arm
        # structure the `drop-through-dependency` rival attacks negatively.
        #
        # The frozen `loom_solve` one-liner does NOT close this (it never
        # case-splits `f.through`), so the tactic body is retuned. Retuning is
        # in-scope: the tactic body is elided from the spec view, the
        # `prove_correct` header and the `ensures` clause are byte-identical, and
        # no assumption is introduced. Confirmed with a real build: the frozen
        # script leaves the unsolved goal above, and the retuned script closes it.
        "module": _with_impl_and_proof(
            "    let deps : List Dep :=\n"
            "      if isReferential then\n"
            "        [baseDep f] ++ (match f.through with\n"
            "                        | none => []\n"
            "                        | some (ta, to_) => [mkDep ta to_])\n"
            "      else []\n"
            "    return deps",
            "  loom_solve\n"
            "  simp only [relationDeps]\n"
            "  rcases f.through with _ | ⟨ta, to_⟩ <;> simp"),
        "rationale": "third CORRECT reshape, and the only positive that does not "
                     "return the pinned `relationDeps f` verbatim: it rebuilds the "
                     "referential value as `[baseDep f] ++ <intermediary "
                     "contribution>`, so the obligation must be discharged across "
                     "both sub-arms of `relationDeps` rather than by definitional "
                     "identity. A faithful decomposed construction MUST verify, else "
                     "SPEC-TOO-STRONG on the sub-arm structure. The rejection the "
                     "frozen tactic one-liner gives it is a TACTIC gap (unsolved "
                     "goal `[baseDep f] ++ (match f.through ..) = relationDeps f`, a "
                     "true equality it does not case-split), not a spec hole — which "
                     "is exactly why the tactic body is retuned here.",
    },

    # =====================================================================
    # ADMISSIBILITY — the frozen method has NO `require` clause (the
    # pre-conditions region is empty), so the literal "a normal input satisfies
    # the precondition" probe has nothing to admit. That does NOT make the lane
    # vacuous: the analogue on a total carrier is the obligation being
    # UNSATISFIABLE or DEGENERATE at exactly an F2P-shaped input — a spec no
    # impl can meet reads like a spec every impl meets, and a spec whose two
    # arms coincide at the interesting point cannot detect the bug at all.
    #
    # This case discharges two in-region `assert`s, by EVALUATION at the fully
    # concrete F2P-shaped input, BEFORE the frozen impl and obligation close
    # verbatim:
    #   (1) SATISFIABLE with the expected value: the post-image at the F2P input
    #       reduces to exactly one concrete dependency on the referenced model,
    #       so an impl meeting it exists and the obligation is not empty there.
    #   (2) NON-DEGENERATE: the referential arm's value at that input DIFFERS
    #       from the non-referential arm's, so the two arms genuinely separate at
    #       the F2P point. If they coincided, every rival that confuses the arms
    #       would satisfy the spec there and the whole battery's discrimination
    #       would be illusory.
    # Both asserts are LIVE, not decoration: confirmed with real builds that the
    # same claims stated FALSELY at the same point (expecting a wrong dependency,
    # or claiming the two arms are equal) leave an unsolved goal and the case
    # FAILS. The tactic body is retuned only to clear the extra assert goals by
    # `decide`; the impl and the `ensures` obligation are byte-identical.
    # =====================================================================
    {
        "id": "admiss-f2p-obligation-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl_and_proof(
            "    assert (with_name_prefix `admiss "
            f"((if true then relationDeps {_F2P} else []) "
            '= [mkDep "testapp" "Author"]))\n'
            "    assert (with_name_prefix `admiss "
            f"((if true then relationDeps {_F2P} else []) "
            f"≠ (if false then relationDeps {_F2P} else ([] : List Dep))))\n"
            + _IMPL,
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp_all"),
        "rationale": "PRECOND-TOO-STRONG lane on a carrier with no `require`: the "
                     "residual admissibility risk is the obligation being "
                     "unsatisfiable or degenerate at an F2P-shaped input. Both are "
                     "discharged by evaluation at the concrete F2P configuration (a "
                     "plain cross-app reference, no intermediary, non-swappable): the "
                     "post-image there reduces to exactly one dependency on the "
                     "referenced model (satisfiable, with the expected value), and it "
                     "DIFFERS from the non-referential arm's value at the same point "
                     "(non-degenerate, so the arms really separate where the fix "
                     "matters). The frozen impl and `ensures` obligation still close "
                     "verbatim. Live, not decorative: the same claims stated falsely "
                     "at the same point leave an unsolved goal.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input, and the refinement argument for why its faithful real
    # counterpart is a genuine wrong impl (not a mere reshape).
    # =====================================================================
    {
        "id": "always-empty-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating miss == pre-patch behaviour: record NO dependency,
        # ever. Correct on the non-referential arm, wrong on the referential arm.
        "module": _with_impl(
            "    let deps : List Dep := []\n"
            "    return deps"),
        "refinement": "this is the pre-patch behaviour: the reshape operation is "
                      "created with no ordering dependencies at all. When a field is "
                      "reshaped so that it now references another model, ZERO "
                      "dependencies are recorded, so the migration cannot be "
                      "sequenced after the referenced model — exactly the "
                      "unresolvable-migration failure the issue reports. The new "
                      "FAIL_TO_PASS test asserts the reshape records a dependency on "
                      "the referenced model and would observe none — it would NOT "
                      "resolve.",
        "rationale": "REJECT from the referential arm of `out = if isReferential "
                     "then relationDeps f else []`: the rival returns `[]` "
                     "unconditionally, differing from `relationDeps f` (a non-empty "
                     "list) whenever `isReferential` holds. Refuted at "
                     "`isReferential = true`.",
        "witness": _witness(
            "alteredFieldDependenciesTester true "
            "{ targetApp := \"testapp\", targetObj := \"Author\", "
            "through := none, swappable := none }"),
    },
    {
        "id": "nonreferential-pollution",
        "kind": "uniqueness",
        "expect": "reject",
        # Dual miss: correct on the referential arm, but records a dependency even
        # when the field references NO model. Wrong on the non-referential arm.
        "module": _with_impl(
            "    let deps : List Dep :=\n"
            "      if isReferential then relationDeps f else [mkDep f.targetApp f.targetObj]\n"
            "    return deps"),
        "refinement": "a real patch that attaches an ordering dependency to a "
                      "reshape whose new field references no model would demand an "
                      "unrelated model be created first for a plain (non-referential) "
                      "field change, misordering the migration and breaking the "
                      "PASS_TO_PASS reshape tests that expect NO dependency on such "
                      "an operation. It would NOT resolve.",
        "rationale": "REJECT from the non-referential arm: the spec demands `[]` "
                     "when `isReferential` is false, but the rival returns a "
                     "non-empty list there. Refuted at `isReferential = false`.",
        "witness": _witness(
            "alteredFieldDependenciesTester false "
            "{ targetApp := \"otherapp\", targetObj := \"Book\", "
            "through := none, swappable := none }"),
    },
    {
        "id": "wrong-referenced-model",
        "kind": "uniqueness",
        "expect": "reject",
        # Records SOME dependency on the referential arm (non-empty, so it would
        # satisfy a mere len>0 spec) but on the WRONG model — not the one the
        # field points at. Attacks the referenced-model identity (targetApp/
        # targetObj) surfaced by baseDep.
        "module": _with_impl(
            "    let deps : List Dep :=\n"
            "      if isReferential then [mkDep \"wrong\" \"Wrong\"] else []\n"
            "    return deps"),
        "refinement": "a real patch that records a non-empty but WRONG ordering "
                      "dependency (a placeholder, not the model the field now points "
                      "at) sequences the migration after the wrong / a non-existent "
                      "model. The FAIL_TO_PASS test asserts the EXACT dependency on "
                      "the referenced model and would read back a different one — it "
                      "would NOT resolve. This proves the referential arm pins the "
                      "referenced-model IDENTITY, not merely non-emptiness.",
        "rationale": "REJECT from the referential arm: the rival returns a fixed "
                     "`[mkDep \"wrong\" \"Wrong\"]`, which differs from "
                     "`relationDeps f` whenever `f.targetApp`/`f.targetObj` differ "
                     "from the literal. Refuted at a field pointing at "
                     "`otherapp/Publisher`; discrimination comes from the referenced "
                     "model identity, a near-miss the always-empty rival (wrong "
                     "presence) does not subsume.",
        "witness": _witness(
            "alteredFieldDependenciesTester true "
            "{ targetApp := \"otherapp\", targetObj := \"Publisher\", "
            "through := none, swappable := none }"),
    },
    {
        "id": "drop-through-dependency",
        "kind": "uniqueness",
        "expect": "reject",
        # Records only the base dependency, DROPPING the extra dependency a
        # relation routed through an intermediary model induces. Correct whenever
        # f.through = none, wrong when f.through = some. Attacks the `through` arm
        # of relationDeps — moves the `f.through` binder off `none`.
        "module": _with_impl(
            "    let deps : List Dep :=\n"
            "      if isReferential then [baseDep f] else []\n"
            "    return deps"),
        "refinement": "the modeled per-field dependency computation (an A-reference "
                      "validated == the real callee by G-AX) emits, for a relation "
                      "routed through an explicit intermediary model, a SECOND "
                      "ordering dependency on that intermediary. A real patch that "
                      "records only the base dependency omits it, leaving the "
                      "reshape unorderable relative to the intermediary — the same "
                      "class of missing-dependency bug the issue reports. The single "
                      "new FAIL_TO_PASS test uses a plain cross-app reference (no "
                      "intermediary), so this rival happens to satisfy THAT one "
                      "assertion; the spec nonetheless pins the full computation, so "
                      "an impl dropping the intermediary dependency is SPEC-TOO-WEAK "
                      "and would misorder through-routed reshapes.",
        "rationale": "REJECT from the referential arm: `relationDeps f` appends the "
                     "intermediary dependency when `f.through = some (..)`, so "
                     "`[baseDep f]` differs there. Refuted at a field with "
                     "`through := some (\"interapp\", \"Link\")`; this is the only "
                     "rival that moves the `f.through` binder off `none`.",
        "witness": _witness(
            "alteredFieldDependenciesTester true "
            "{ targetApp := \"app1\", targetObj := \"Src\", "
            "through := some (\"interapp\", \"Link\"), swappable := none }"),
    },
    {
        "id": "ignore-swappable-setting",
        "kind": "uniqueness",
        "expect": "reject",
        # Reimplements relationDeps but ALWAYS uses the target model for the base
        # dependency, ignoring the swappable-setting substitution. Correct when
        # f.swappable = none, wrong when f.swappable = some. Attacks the swappable
        # arm of baseDep — moves the `f.swappable` binder off `none`.
        "module": _with_impl(
            "    let deps : List Dep :=\n"
            "      if isReferential then\n"
            "        (match f.through with\n"
            "         | none => [mkDep f.targetApp f.targetObj]\n"
            "         | some (ta, to_) => [mkDep f.targetApp f.targetObj, mkDep ta to_])\n"
            "      else []\n"
            "    return deps"),
        "refinement": "when the referenced model is swappable, the modeled "
                      "computation records the base dependency against the swappable "
                      "SETTING sentinel rather than the concrete target model (so the "
                      "reshape tracks whatever the setting resolves to). A real patch "
                      "that always records the concrete target ignores the swappable "
                      "setting, recording a dependency on the wrong object for a "
                      "reshape into a swappable relation — SPEC-TOO-WEAK on the "
                      "swappable arm. The single new FAIL_TO_PASS test uses a "
                      "non-swappable reference, so this rival satisfies THAT "
                      "assertion; the spec pins the swappable substitution, which "
                      "this rival violates.",
        "rationale": "REJECT from the referential arm: `baseDep f` uses the "
                     "`__setting__` sentinel with the setting name when "
                     "`f.swappable = some s`, but the rival always uses "
                     "`f.targetApp`/`f.targetObj`. Refuted at a field with "
                     "`swappable := some \"AUTH_USER_MODEL\"`; this is the only "
                     "rival that moves the `f.swappable` binder off `none`.",
        "witness": _witness(
            "alteredFieldDependenciesTester true "
            "{ targetApp := \"app1\", targetObj := \"Src\", "
            "through := none, swappable := some \"AUTH_USER_MODEL\" }"),
    },
    {
        "id": "swappable-shadows-through",
        "kind": "uniqueness",
        "expect": "reject",
        # The INTERACTION rival. Handles each sub-arm of the pinned computation
        # correctly IN ISOLATION — it uses the setting sentinel when the target is
        # swappable, and it emits the intermediary dependency when the relation is
        # routed through one — but it treats the two as mutually exclusive: on the
        # swappable path it returns the sentinel dependency ALONE and drops the
        # intermediary. So it agrees with the spec at every input the five rivals
        # above are refuted at, and diverges only where BOTH `f.swappable = some`
        # AND `f.through = some` hold. That input tuple is reached by no other
        # witness in this battery: `drop-through-dependency` holds `swappable` at
        # `none` and `ignore-swappable-setting` holds `through` at `none`, so
        # neither moves the pair together and neither subsumes this miss.
        "module": _with_impl(
            "    let deps : List Dep :=\n"
            "      if isReferential then\n"
            "        (match f.swappable, f.through with\n"
            "         | some s, _ => [mkDep \"__setting__\" s]\n"
            "         | none, none => [mkDep f.targetApp f.targetObj]\n"
            "         | none, some (ta, to_) => "
            "[mkDep f.targetApp f.targetObj, mkDep ta to_])\n"
            "      else []\n"
            "    return deps"),
        "refinement": "the modeled per-field computation (an A-reference validated "
                      "== the real callee by G-AX) emits the intermediary-model "
                      "dependency INDEPENDENTLY of whether the referenced model is "
                      "swappable — the two contributions compose, they do not "
                      "displace one another. A real patch that treats the swappable "
                      "substitution as replacing the whole dependency set records the "
                      "setting sentinel but loses the intermediary, so a reshape into "
                      "a swappable relation routed through an explicit intermediary "
                      "is left unorderable relative to that intermediary — the same "
                      "missing-dependency class the issue reports, surviving on a "
                      "narrower sub-domain. The single new FAIL_TO_PASS test uses a "
                      "plain non-swappable reference with no intermediary, so this "
                      "rival satisfies THAT assertion; the spec pins the full "
                      "computation, so it is SPEC-TOO-WEAK on the interaction.",
        "rationale": "REJECT from the referential arm: `relationDeps f` appends the "
                     "intermediary dependency whenever `f.through = some (..)`, "
                     "including when `baseDep f` has taken the swappable sentinel, "
                     "but the rival returns the sentinel alone there. Refuted at the "
                     "ONLY input tuple in this battery where `f.swappable` and "
                     "`f.through` are BOTH `some` — the interaction point the two "
                     "single-sub-arm rivals each hold at `none` and therefore leave "
                     "unattacked.",
        "witness": _witness(
            "alteredFieldDependenciesTester true "
            "{ targetApp := \"app1\", targetObj := \"Src\", "
            "through := some (\"interapp\", \"Link\"), "
            "swappable := some \"AUTH_USER_MODEL\" }"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 3 SPEC soundness/
# admissibility positives, 1 frame-mutation reject, 3 partial-domain rejects,
# plus a 2-case AXIOM lane. Its carrier is different in two ways that reshape
# the port:
#
#   (a) FRACTIONAL PERMISSIONS. The sibling holds `new_field` at Acc(.,1/2) and
#       makes the frame-mutation reject MANDATORY (an impl that writes the
#       read-only input to make the relational clause vacuous). This backend is
#       referentially transparent: `isReferential`/`f` are immutable values, no
#       `mut` binder, no heap. The class is VACUOUS here (porting map) — not
#       fabricated, not substituted.
#   (b) OPAQUE ORACLE vs DEEP MODEL. The sibling axiomatises `fk_dependencies`
#       as `@ContractOnly` and pins the relational arm by EXACT equality to that
#       opaque oracle (its only weakness attack is "a wrong non-empty echo cannot
#       be proven equal"). This bundle models the same computation DEEPLY
#       (`relationDeps`/`baseDep`, an A-reference validated == the real callee by
#       G-AX), so the arm is pinned to a TRANSPARENT term. That REPLACES the one
#       opacity attack with three transparent value attacks (wrong constant,
#       dropped through, ignored swappable) that also cover the `f.through` and
#       `f.swappable` binders the opaque oracle hid.
#
#   sibling case                         -> here
#   -----------------------------------------------------------------------
#   pos-guard-early-return               -> pos-if-expression       RE-EXPRESSED
#   pos-cheapest-honest-echo             -> pos-match-on-flag        RE-EXPRESSED
#   admiss-fshaped-selfcall              -> admiss-f2p-obligation-satisfiable
#                                                                    RE-EXPRESSED
#   weak-frame-mutate-input              -> (none)                   VACUOUS (no heap)
#   weak-always-empty-prepatch           -> always-empty-prepatch    PORTED
#   weak-nonrelational-pollution         -> nonreferential-pollution PORTED
#   weak-relational-nonequal-nonempty    -> wrong-referenced-model   RE-EXPRESSED
#   (no sibling)                         -> drop-through-dependency   ADDED (binder)
#   (no sibling)                         -> ignore-swappable-setting  ADDED (binder)
#   (no sibling)                         -> swappable-shadows-through ADDED (interaction)
#   (no sibling)                         -> pos-decomposed-append     ADDED (soundness)
#   AXIOM_TESTS (2)                      -> (none)                   DROPPED (G-AX)
#
# RE-EXPRESSED (positives): the sibling's two positives are a branch-reordered
#   guard and a direct-oracle echo. On this carrier the arms collapse to a
#   transparent conditional, so the ports are a pure-conditional reshape and a
#   `match` reshape — both structurally different from the frozen mutable-seed
#   skeleton, both closing the frozen `loom_solve` obligation (verified with real
#   builds).
# RE-EXPRESSED (oracle-pin reject): the sibling's `weak-relational-nonequal-
#   nonempty` (a non-empty non-oracle sequence) attacked the EXACTNESS of the
#   opaque-oracle pin. With a transparent `relationDeps` there is no opacity to
#   lean on; the same "records a wrong dependency" argument ports as a concrete
#   wrong-constant rival refuted by `decide`.
# ADDED (binder coverage): `relationDeps`/`baseDep` expose two sub-arms the
#   sibling's opaque oracle folded away — the intermediary-model (`through`)
#   dependency and the swappable-setting substitution. Two rivals attack them so
#   the `f.through` and `f.swappable` binders are each moved off their default;
#   without them a rival mishandling only those arms would verify unnoticed.
# RE-EXPRESSED (admissibility): the sibling's admissibility positive self-calls
#   the method to show `Acc(new_field.is_relation,1/2)` ADMITS a freshly built
#   F2P-shaped field. There is no `require` clause here (the pre-conditions region
#   is empty), so nothing can exclude an input — but the LANE is not vacuous, and
#   recording it as such was a defect: on a total carrier the analogue is the
#   obligation being UNSATISFIABLE or DEGENERATE at an F2P-shaped input, which
#   `admiss-f2p-obligation-satisfiable` tests directly by discharging, at the
#   concrete F2P configuration and by evaluation, that the post-image there
#   reduces to the expected single dependency (satisfiable) AND differs from the
#   non-referential arm's value at the same point (non-degenerate, so the arms
#   really separate where the fix matters). Both asserts are live: stating either
#   claim falsely at the same point leaves an unsolved goal and the case fails.
# VACUOUS (frame-mutation only): see (a) above — no heap/`mut` to overwrite.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
#   consumed `axiom` (the delegated computation is a directive-7 deep-model
#   A-reference), so there is nothing to probe and the gate ignores AXIOM_TESTS.
#
#   The five reject witnesses probe five DISTINCT input tuples. Across them
#   `isReferential` takes {true, false}; `f.through` takes {none, some};
#   `f.swappable` takes {none, some}; and the referenced-model identity is
#   attacked directly by the wrong-constant rival. Both top-level arms of the
#   postcondition and both sub-arms of the pinned `relationDeps` are attacked.
AXIOM_TESTS = []
