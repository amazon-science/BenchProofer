"""properties.py — G-PBT falsification battery for django__django-16899 (lean).

NOT a Lean module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``-- proof-start`` / ``-- proof-end``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``theorem correct_checkReadonlyFieldsItem``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation. It is checked by the real verifier: ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates — the witness must
ELABORATE against the rival and FAIL against the frozen solution).

This battery is a PORT of the nagini sibling (`../nagini/properties.py`); that
file is the design document. The nagini rivals are re-expressed against this
backend's carrier and each reject rival is given a machine-checked witness (the
part with no nagini counterpart).

DEFENDED SURFACE. One obligation over the modeled function
``implementation_checkReadonlyFieldsItem``, which validates one configured
display value and returns either no diagnostic or a single diagnostic message:

  problem_spec_checkReadonlyFieldsItem obj fieldName label
      isCallable hasAttrObj hasAttrModel fieldExists result :=
    if isCallable ∨ hasAttrObj ∨ hasAttrModel ∨ fieldExists then
      result = []                                                     -- EMPTY branch
    else
      result = [errorMessage label fieldName obj.className obj.modelLabel]  -- MESSAGE branch

The postcondition has two arms of one if/else (no top-level ∧). The load-bearing
content of the change is the MESSAGE-branch text: the diagnostic now names the
offending value (``fieldName``) as its own quoted segment immediately after the
position label, via the deeply-modeled ``errorMessage``:

  "The value of '" ++ label ++ "' refers to '" ++ fieldName ++
  "', which is not a callable, an attribute of '" ++ className ++
  "', or an attribute of '" ++ modelLabel ++ "'."

The spec pins this three ways, mirroring the nagini refinement:
  * the value is PRESENT and named (nagini CLAUSE-3, whole-message equality);
  * the value occupies ITS OWN slot, distinct from the class/model slots
    (nagini CLAUSE-4, value-position);
  * a resolved reference yields the EMPTY result and an unresolved one yields
    exactly one message (nagini CLAUSE-2, the emptiness discriminator).

CARRIER-NARROWING / -WIDENING vs nagini. Nagini models a single boolean
``resolves``; this lean bundle splits it into the FOUR independent resolution
outcomes (``isCallable``, ``hasAttrObj``, ``hasAttrModel``, ``fieldExists``)
whose disjunction is ``resolves``. So nagini's single discriminator-flip rival
becomes FOUR rivals here — one per disjunct — because each check independently
gates the empty-result branch and the spec's disjunction pins all four. The
message-branch rivals (drop / omit / transpose the value) port one-to-one.

ADVERSARIAL READ of the nagini weakness classes on THIS carrier:
  * FRAME-MUTATION (nagini's #1 mandatory probe) — VACUOUS. That class exists on
    nagini because a read-only input carries a fractional heap permission an
    impl can overwrite. Lean is referentially transparent: ``fieldName``,
    ``label`` and the ``AdminObj`` fields are immutable ``String`` values, there
    is no heap and no aliasing, so there is no read-only input to mutate and no
    substitute probe to build. Reported vacuous, not fabricated. Its SPIRIT (an
    output component left unconstrained) is covered positively: the spec pins
    the whole result list and the message rivals prove each part load-bearing.
  * UNGROUNDED-ORACLE ECHO — N/A. ``errorMessage`` is a deeply-modeled total
    function OF the inputs (a flat ``++`` chain of five constant prose pieces
    spliced with the four carriers), NOT an opaque answer key. There is nothing
    to echo; any impl satisfying the MESSAGE branch must build the real message
    from the real carriers. The reshape positives stand in for the nagini
    ``pos-master-assert`` no-echo control.
  * CONTROL-FLOW-EFFECT — captured by the value abstraction. The one observable
    effect is the returned ``List String`` (empty vs the one-message list); the
    resolve/error split is fully pinned by the if/else, so a wrong control-flow
    choice manifests as an emptiness/value difference the spec already catches.
    The flip rivals below exercise exactly that split.
  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE (not vacuous; measured, see the
    accounting block). A diverging impl CAN be written on this carrier — a
    ``partial def`` helper that recurses unconditionally, returned on the
    message path — and it IS rejected (the frozen ``rfl`` cannot equate the
    opaque term with the spec's message). But a ``partial def`` is opaque to the
    kernel, so ``decide`` cannot reduce the claim and NO discriminating witness
    can be built against it: the rejection would attest to a tactic mismatch,
    not to the spec. So the class is not shippable here and is recorded as a
    hole in the spec rather than as a complete lane.
  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals right on part of the input space
    but wrong on a sub-domain (the pre-patch message, an empty value, a
    transposed value, a spurious diagnostic on one resolve path). Each is
    refuted at a concrete assignment by a ``decide`` witness.

WITNESS. Every reject case carries a Lean ``example`` stating
``¬ problem_spec_checkReadonlyFieldsItem <inputs> (implementation_... <inputs>)``
at a concrete input and closing by ``decide``. The carrier is fully transparent
(``String`` literals + ``Bool`` literals + a concrete ``AdminObj``), so no
head binder is introduced and no conditioning-on-the-carrier is needed. Each
witness is checked in a file whose ``-- proof-start``/``-- proof-end`` region has
been stripped (so the frozen tactic script cannot mask the verdict): it must
elaborate against the rival and FAIL against the frozen solution. Each point is
chosen so the rival's returned list differs from the spec's there, attributing
the ``¬`` to the modeled behavior.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the diagnostic
text is modeled deeply as concrete string concatenation). The gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16899"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen impl anchors. Each lies wholly inside the one `-- impl-start` /
# `-- impl-end` region and is unique in Solution.lean (both asserted by _swap at
# build time, so the manifest breaks loudly on any spec drift). The four
# short-circuit acceptance branches differ only by the resolution flag they read,
# which makes each two-line block unique.
# ---------------------------------------------------------------------------
_BR_CALLABLE = "    if isCallable then\n      return []\n"
_BR_ATTROBJ = "    if hasAttrObj then\n      return []\n"
_BR_ATTRMODEL = "    if hasAttrModel then\n      return []\n"
_BR_FIELDEXISTS = "    if fieldExists then\n      return []\n"
_RET_ERROR = (
    "    return [errorMessage label fieldName obj.className obj.modelLabel]\n")

# The whole imperative body (for the single-expression reshape positive).
_IMPL_DO = ("  Id.run do\n" + _BR_CALLABLE + _BR_ATTROBJ + _BR_ATTRMODEL
            + _BR_FIELDEXISTS + _RET_ERROR)

# The four acceptance branches as one block (for the reorder reshape positive).
_FOUR_BRANCHES = _BR_CALLABLE + _BR_ATTROBJ + _BR_ATTRMODEL + _BR_FIELDEXISTS

# The frozen proof's `intro` line — the anchor inside the `-- proof-start` /
# `-- proof-end` tactic body that the admissibility positive prepends a ground
# `have` to. Also elided from the consumer spec view, so `same_spec` holds.
_P_INTRO = ("  intro obj fieldName label isCallable hasAttrObj hasAttrModel "
            "fieldExists\n")

for _a in (_BR_CALLABLE, _BR_ATTROBJ, _BR_ATTRMODEL, _BR_FIELDEXISTS,
           _RET_ERROR, _IMPL_DO, _FOUR_BRANCHES, _P_INTRO):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"

# The pre-change message shape: the value is never named (only the position
# label, the admin class, and the bound-model label appear).
_MSG_PREPATCH = (
    '"The value of \'" ++ label ++ "\' is not a callable, an attribute of \'" '
    '++ obj.className ++ "\', or an attribute of \'" ++ obj.modelLabel ++ "\'."')


# ---------------------------------------------------------------------------
# Witness construction. A witness states `¬ problem_spec_... <in> (impl <in>)`
# at a concrete input and closes by `decide`. The point is chosen so the rival's
# returned list differs from the spec's there.
# ---------------------------------------------------------------------------
_OBJ_SONG = '{ className := "SongAdmin", modelLabel := "admin_checks.Song" }'
_OBJ_CITY = '{ className := "CityInline", modelLabel := "admin_checks.City" }'


def _witness(obj, field_name, label, ic, ho, hm, fe):
    args = (f"    {obj}\n"
            f"    {field_name} {label}\n"
            f"    {ic} {ho} {hm} {fe}")
    return (
        "example : ¬ problem_spec_checkReadonlyFieldsItem\n"
        f"{args}\n"
        "    (implementation_checkReadonlyFieldsItem\n"
        f"{args}) := by\n"
        "  unfold problem_spec_checkReadonlyFieldsItem "
        "implementation_checkReadonlyFieldsItem\n"
        "  decide\n")


# The F2P-shaped points (test_nonexistent_field / _on_inline). All four checks
# false => the reference does not resolve => the MESSAGE branch fires.
def _w_song(ic="false", ho="false", hm="false", fe="false"):
    return _witness(_OBJ_SONG, '"nonexistent"', '"readonly_fields[1]"',
                    ic, ho, hm, fe)


def _w_city(ic="false", ho="false", hm="false", fe="false"):
    return _witness(_OBJ_CITY, '"i_dont_exist"', '"readonly_fields[0]"',
                    ic, ho, hm, fe)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify with a proof that actually closes (the frozen
    # `cases … <;> rfl` bundle still discharges both shapes). Neither weakens the
    # obligation; the theorem statement stays byte-identical. If a logically-equal
    # impl could not verify, the exact-equality post-image would be
    # SPEC-TOO-STRONG on impl shape.
    # =====================================================================
    {
        "id": "pos-single-expression",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the four short-circuit early-returns + final return are
        # collapsed into one if/else expression over the disjunction — the same
        # value on every input, no `Id.run do`.
        "module": _swap(
            _BASE, _IMPL_DO,
            "  if isCallable ∨ hasAttrObj ∨ hasAttrModel ∨ fieldExists then []\n"
            "  else [errorMessage label fieldName obj.className obj.modelLabel]\n"),
        "rationale": (
            "a correct reshape — the imperative chain of four short-circuit "
            "acceptances is rewritten as ONE if/else over the same disjunction — "
            "computes the identical result on every input, so the frozen "
            "`cases … <;> rfl` proof still closes (both branches reduce "
            "definitionally to the spec's two arms). Defends BOTH arms of the "
            "if/else postcondition. If it failed to verify, the post-image would "
            "be over-fit to the imperative shape => SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-reorder-checks",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the four acceptance branches are reordered (fieldExists,
        # hasAttrModel, hasAttrObj, isCallable). Since every branch returns the
        # SAME empty list and they are mutually compatible (any one true => empty),
        # the order is irrelevant to the value; the frozen proof still closes.
        "module": _swap(
            _BASE, _FOUR_BRANCHES,
            _BR_FIELDEXISTS + _BR_ATTRMODEL + _BR_ATTROBJ + _BR_CALLABLE),
        "rationale": (
            "a correct reshape — the four short-circuit acceptance branches are "
            "reordered — computes the identical result on every input (each branch "
            "returns the same empty list and the guards are independent), so it "
            "MUST verify; the frozen `cases … <;> rfl` proof still discharges the "
            "EMPTY arm regardless of branch order. A correct reshape that could "
            "not verify would be SPEC-TOO-STRONG."),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at exactly an
    # F2P-shaped input. The frozen obligation carries NO precondition hypothesis
    # (the domain is total), so nagini's precondition-admission self-call
    # re-expresses on this carrier as: discharge the spec predicate BY EVALUATION
    # at the concrete F2P-shaped assignment as a `have`, then close the frozen
    # obligation verbatim. That is the real analogue of PRECOND-TOO-STRONG here —
    # "the modeled behavior is unsatisfiable at exactly a normal input" — and it
    # is NOT implied by the ∀-quantified soundness positives: those are proved by
    # a uniform `cases … <;> rfl` that never evaluates the message at a ground
    # point, so an unsatisfiable-at-ground-instance spec would still pass them.
    # Nothing is assumed: no new declaration, statement byte-identical, the
    # ground instance is a `have` prepended to the existing tactic body.
    # =====================================================================
    {
        "id": "admiss-ground-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_checkReadonlyFieldsItem\n"
            f"      {_OBJ_SONG}\n"
            '      "nonexistent" "readonly_fields[1]" false false false false\n'
            "      (implementation_checkReadonlyFieldsItem\n"
            f"        {_OBJ_SONG}\n"
            '        "nonexistent" "readonly_fields[1]" false false false false)'
            " := by\n"
            "    unfold problem_spec_checkReadonlyFieldsItem "
            "implementation_checkReadonlyFieldsItem\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": (
            "the obligation is discharged at the F2P-shaped input (an unresolved "
            "reference on a normal admin shape: all four resolution checks false, "
            "so the MESSAGE arm fires) by `decide` — full kernel evaluation of "
            "both the impl and the spec's message — as a `have`, then the frozen "
            "obligation is closed verbatim. It MUST verify: if the spec predicate "
            "were unsatisfiable at exactly that concrete normal input, this would "
            "fail => PRECOND-TOO-STRONG (the total-carrier analogue). Ports "
            "nagini's admiss-fshape, which the carrier does NOT make vacuous: the "
            "soundness positives close by a uniform `cases … <;> rfl` that never "
            "evaluates the message at a ground point, so they do not subsume "
            "this. Nothing is assumed — no new declaration, statement "
            "byte-identical, ground instance is a `have` in the existing tactic "
            "body."),
    },

    # =====================================================================
    # MESSAGE-BRANCH rivals (port nagini drop-value / omit-value / swap). All
    # four checks false, so the message branch fires; each corrupts the message
    # a different way. Refuted at an F2P-shaped point.
    # =====================================================================
    {
        "id": "drop-value-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change bug: emit the message that never names the offending
        # value (only position label + class + model label).
        "module": _swap(
            _BASE, _RET_ERROR,
            "    return [" + _MSG_PREPATCH + "]\n"),
        "refinement": (
            "the faithful real counterpart is the pre-change message that names "
            "only the position and the two class labels, never the offending "
            "value. The failing test constructs an unresolved reference on a "
            "normal form and asserts the emitted diagnostic quotes that value; "
            "the pre-change message omits it => FAIL_TO_PASS NOT resolved. This "
            "is exactly the bug the change fixes."),
        "rationale": (
            "REJECT from the MESSAGE arm `result = [errorMessage label fieldName "
            "obj.className obj.modelLabel]`: with all four checks false the spec "
            "demands the message that NAMES the value, but this rival emits the "
            "value-less message. Refuted at the F2P point where the reference "
            "does not resolve. If it verified => SPEC-TOO-WEAK (the un-fixed "
            "message would be admitted)."),
        "witness": _w_song(),
    },
    {
        "id": "omit-value-keep-prose",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the full post-change prose but interpolate an EMPTY value: the
        # message reads "…refers to '', which is not…".
        "module": _swap(
            _BASE, _RET_ERROR,
            '    return [errorMessage label "" obj.className obj.modelLabel]\n'),
        "refinement": (
            "the faithful real counterpart interpolates an EMPTY string at the "
            "new value slot, so the diagnostic reads \"refers to ''\" and still "
            "does not name the offending value. The failing test asserts the "
            "value itself appears quoted; an empty slot still misses it => NOT "
            "resolved. Targets the value-position guarantee specifically (the "
            "prose is present but the value is not named)."),
        "rationale": (
            "REJECT from the MESSAGE arm: the value's own slot must hold the "
            "actual `fieldName`, but this rival leaves it empty, so the result "
            "differs from the spec's message. Refuted at a DISTINCT F2P point "
            "(the inline test shape) — a different obj/value/label than the "
            "drop-value rival, so it moves those three binders. If it verified => "
            "SPEC-TOO-WEAK (the value-position pin would be hollow)."),
        "witness": _w_city(),
    },
    {
        "id": "swap-value-class",
        "kind": "uniqueness",
        "expect": "reject",
        # Transpose the value and class slots: the value IS named, but at the
        # class's interpolation point and vice-versa.
        "module": _swap(
            _BASE, _RET_ERROR,
            '    return [errorMessage label obj.className fieldName '
            'obj.modelLabel]\n'),
        "refinement": (
            "the faithful real counterpart transposes the value and admin-class "
            "arguments, so the diagnostic names the value at the class's slot and "
            "the class where the value belongs. The failing test asserts the "
            "value appears at ITS position (immediately after the position "
            "label); a transposed message fails that assertion => NOT resolved. "
            "Defeats a naive value-PRESENCE check by putting the value somewhere "
            "wrong."),
        "rationale": (
            "REJECT from the MESSAGE arm: the value must occupy the slot right "
            "after the position label, but this rival puts the class there and "
            "the value at the class's slot, so the result string differs from the "
            "spec's. Refuted at the F2P point (where value and class are distinct "
            "so the transposition is observable). If it verified => "
            "SPEC-TOO-WEAK (the value-position would be unpinned)."),
        "witness": _w_song(),
    },

    # =====================================================================
    # EMPTINESS-DISCRIMINATOR rivals (port nagini discriminator-flip, ONE per
    # resolution disjunct — carrier-widening: nagini's single `resolves` toggle
    # is four booleans here). Each emits a spurious diagnostic on the resolve
    # path gated by ONE check, moving that boolean binder off `false`.
    # =====================================================================
    {
        "id": "flip-callable-emit",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the diagnostic on the callable-resolve path instead of returning
        # empty (a spurious diagnostic for a value that resolves via callability).
        "module": _swap(
            _BASE, _BR_CALLABLE,
            "    if isCallable then\n"
            "      return [errorMessage label fieldName obj.className "
            "obj.modelLabel]\n"),
        "refinement": (
            "the faithful real counterpart emits the diagnostic even when the "
            "value resolves as a callable — a spurious error for a valid entry. "
            "A previously-passing config whose readonly entry is a callable would "
            "then report a spurious error and its zero-error assertion regresses "
            "=> NOT resolved (a passing test regresses)."),
        "rationale": (
            "REJECT from the EMPTY arm `result = []` (guard `isCallable ∨ …`): "
            "with isCallable=true the spec demands the empty list but this rival "
            "emits a diagnostic. Refuted at (isCallable=true, others false) — the "
            "only witness that moves the callable binder off false."),
        "witness": _w_song(ic="true"),
    },
    {
        "id": "flip-attrobj-emit",
        "kind": "uniqueness",
        "expect": "reject",
        # Spurious diagnostic on the admin-object-attribute resolve path.
        "module": _swap(
            _BASE, _BR_ATTROBJ,
            "    if hasAttrObj then\n"
            "      return [errorMessage label fieldName obj.className "
            "obj.modelLabel]\n"),
        "refinement": (
            "the faithful real counterpart emits the diagnostic even when the "
            "value resolves as an attribute of the admin object. A "
            "previously-passing config whose readonly entry is such an attribute "
            "would report a spurious error and regress its zero-error assertion "
            "=> NOT resolved (a passing test regresses)."),
        "rationale": (
            "REJECT from the EMPTY arm (guard disjunct `hasAttrObj`): with "
            "hasAttrObj=true the spec demands the empty list but this rival emits "
            "a diagnostic. Refuted at (hasAttrObj=true, others false) — the only "
            "witness that moves the admin-attribute binder off false."),
        "witness": _w_song(ho="true"),
    },
    {
        "id": "flip-attrmodel-emit",
        "kind": "uniqueness",
        "expect": "reject",
        # Spurious diagnostic on the bound-model-attribute resolve path.
        "module": _swap(
            _BASE, _BR_ATTRMODEL,
            "    if hasAttrModel then\n"
            "      return [errorMessage label fieldName obj.className "
            "obj.modelLabel]\n"),
        "refinement": (
            "the faithful real counterpart emits the diagnostic even when the "
            "value resolves as an attribute of the bound model. A "
            "previously-passing config whose readonly entry is such an attribute "
            "would report a spurious error and regress its zero-error assertion "
            "=> NOT resolved (a passing test regresses)."),
        "rationale": (
            "REJECT from the EMPTY arm (guard disjunct `hasAttrModel`): with "
            "hasAttrModel=true the spec demands the empty list but this rival "
            "emits a diagnostic. Refuted at (hasAttrModel=true, others false) — "
            "the only witness that moves the model-attribute binder off false."),
        "witness": _w_song(hm="true"),
    },
    {
        "id": "flip-fieldexists-emit",
        "kind": "uniqueness",
        "expect": "reject",
        # Spurious diagnostic on the declared-model-field resolve path.
        "module": _swap(
            _BASE, _BR_FIELDEXISTS,
            "    if fieldExists then\n"
            "      return [errorMessage label fieldName obj.className "
            "obj.modelLabel]\n"),
        "refinement": (
            "the faithful real counterpart emits the diagnostic even when the "
            "value resolves as a declared model field. A previously-passing "
            "config whose readonly entry is a real model field would report a "
            "spurious error and regress its zero-error assertion => NOT resolved "
            "(a passing test regresses)."),
        "rationale": (
            "REJECT from the EMPTY arm (guard disjunct `fieldExists`): with "
            "fieldExists=true the spec demands the empty list but this rival "
            "emits a diagnostic. Refuted at (fieldExists=true, others false) — "
            "the only witness that moves the declared-field binder off false."),
        "witness": _w_song(fe="true"),
    },
]


# ===========================================================================
# Nagini -> lean accounting (see docstring for the full carrier discussion).
#
#   nagini case                 -> here
#   -----------------------------------------------------------------------
#   pos-one-expr (5a)           -> pos-single-expression        RE-EXPRESSED
#   pos-master-assert (5b/2)    -> (folded into positives)      N/A (no echo)
#   admiss-fshape (6)           -> admiss-ground-f2p            PORTED
#   frame-mutate-value (1)      -> (none)                       VACUOUS
#   drop-value (2)              -> drop-value-prepatch          PORTED
#   omit-value-keep-prose (3)   -> omit-value-keep-prose        PORTED
#   swap-value-cls (4)          -> swap-value-class             PORTED
#   discriminator-flip (5)      -> flip-{callable,attrobj,      PORTED x4
#                                       attrmodel,fieldexists}-emit  (widened)
#   AXIOM_TESTS                 -> dropped (G-AX's lane; no axiom declared)
#
# PORTED. The three message-branch rivals port one-to-one (drop the value, keep
#   the prose but empty the value, transpose value/class). The single nagini
#   discriminator-flip becomes FOUR flip rivals because this carrier splits the
#   nagini `resolves` boolean into the four independent resolution outcomes; each
#   is refuted on the sub-domain where that one check resolves.
#
# RE-EXPRESSED (soundness). pos-single-expression collapses the imperative body
#   into one if/else (nagini's "one combined expression" positive). pos-reorder-
#   checks additionally reorders the four acceptance branches — a second correct
#   reshape defending the EMPTY arm. Both keep the byte-identical obligation and
#   close with the frozen proof.
#
# pos-master-assert — N/A here. `errorMessage` is a deeply-modeled total function
#   grounded in the inputs (no opaque oracle), so there is no WRONG oracle-echo
#   to guard against; the reshape positives already show a correct impl verifies.
#
# admiss-fshape — PORTED as admiss-ground-f2p. The lean obligation carries NO
#   precondition hypothesis (the domain is total), but that does NOT make the lane
#   vacuous: the analogue on a total carrier is the obligation being unsatisfiable
#   at exactly an F2P-shaped input, which a positive that discharges the spec
#   predicate AT that concrete input — by `decide`, as a `have`, before closing the
#   frozen obligation verbatim — tests directly. Nor do the soundness positives
#   subsume it: both close by a uniform `cases … <;> rfl` over the four booleans,
#   which never forces the message to be EVALUATED at a ground point, so a spec
#   unsatisfiable at a ground instance would still pass them.
#
# frame-mutate-value — VACUOUS. Referential transparency: `fieldName`, `label`
#   and the `AdminObj` fields are immutable `String` values, no heap, no
#   fractional permission, nothing to overwrite. Reported, not fabricated. Its
#   spirit (an unconstrained output) is covered positively — the spec pins the
#   whole result list and the message rivals prove each part load-bearing.
#
# DIVERGENCE / NON-TERMINATION — KNOWN HOLE, measured with real builds (not
#   vacuous, and the earlier "cannot be written" reading was wrong). A diverging
#   rival IS expressible: a `partial def spin (n : Nat) : List String := spin
#   (n + 1)` helper in the impl region, returned on the message path. It stays in
#   variant scope (same_spec True, no new theorem/axiom) and it IS rejected —
#   the frozen `rfl` reports the `if … then [] else spin 0` term is not
#   definitionally equal to the spec's message. But no WITNESS can discriminate
#   it: `partial def` is opaque to the kernel, so `decide` fails with
#   "Tactic `decide` failed for proposition ¬if false = true ∨ …" — it never
#   evaluates, so its exit code would carry no information about the claim and
#   the rejection would attest to a tactic mismatch. Not shippable; recorded as a
#   hole in the spec (the spec does not pin termination) rather than as a
#   complete or vacuous lane.
#
# BINDER COVERAGE. The seven input binders are all moved by the reject witnesses:
#   obj / fieldName / label  <- drop-value-prepatch & swap (SongAdmin, "nonexistent",
#                                "readonly_fields[1]") vs omit-value (CityInline,
#                                "i_dont_exist", "readonly_fields[0]");
#   isCallable   <- flip-callable-emit (true);
#   hasAttrObj   <- flip-attrobj-emit (true);
#   hasAttrModel <- flip-attrmodel-emit (true);
#   fieldExists  <- flip-fieldexists-emit (true).
# Both if/else arms are attacked: the MESSAGE arm by the three message rivals,
# the EMPTY arm by the four flip rivals; both arms are defended by the reshape
# positives, and the MESSAGE arm is additionally shown SATISFIABLE at a ground
# F2P point by admiss-ground-f2p (evaluation, not a uniform case-split).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom, so there is nothing to probe.
AXIOM_TESTS = []
