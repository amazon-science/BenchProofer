"""properties.py — G-PBT falsification battery for django__django-11433 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models a SINGLE per-element decision function over four read-only boolean input
lists (``selected/has_default/omitted/value_empty``) returning a ``bool`` per
index. This Lean bundle models the SAME core decision, but on a RICHER carrier:
one total function that walks a list of per-field observable records, decides
per record whether to emit an assignment, and returns the exact ordered sequence
of emitted ``(name, value)`` pairs — with the two-pass (non-file then file)
ordering pinned. So the nagini per-index boolean pin becomes, here, a pin of the
whole output LIST equal to a grounded computation over the inputs. The nagini
cases carry over as attacks on the individual conjuncts of the per-record
decision plus the list-shape clauses this richer carrier adds; the mapping of
each nagini case to its Lean counterpart (or its principled omission) is in the
module ``assessment`` at the bottom.

DEFENDED SURFACE (one modeled behavior). The single obligation pins ``result``
equal to a grounded computation: keep exactly the records that pass the full
per-record decision (editable ∧ not-auto ∧ has-a-resolved-value ∧ passes an
optional name restriction ∧ not in a non-empty skip set ∧ NOT
(has-default ∧ omitted ∧ resolved-value-empty)), emit each kept record's
``(name, value)``, and order them non-file-first then file-deferred. The
independent top-level structure the postcondition therefore pins:

  * the per-record KEEP decision — a five-way conjunction of guards, each of
    which a rival can drop or corrupt;
  * the CHANGED conjunct (the behavioural discriminator / the F2P): a record
    that carries a default and was omitted from the payload is left at its
    default ONLY when its resolved value is itself empty. A defaulted, omitted
    field whose resolved value is NON-empty must now be emitted, where the
    pre-patch guard left it at the default;
  * the two-pass ORDERING: kept non-file records first, then kept file records,
    each in field order.

BEHAVIOURAL DISCRIMINATOR (the fix). A defaulted, omitted field whose resolved
value is non-empty was previously discarded in favour of the default; it must
now be emitted with that resolved value. The ``reject-prepatch`` rival below IS
that pre-fix behaviour (its guard omits the resolved-value-empty conjunct), and
its witness is exactly the F2P-shaped input.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input list carries no heap permission, there is no read-only half-permission
    to overwrite and no aliasing to exploit. The nagini frame-mutation rival
    (store ``True`` into the read-only input ``selected[i]`` held at 1/2
    permission) has no expressible instance here — a Lean ``for f in fields``
    binds each ``f`` immutably and cannot write back into ``fields``. No
    substitute is fabricated. (nagini REJECT 4.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to a term built only from the inputs (``assignmentsFor``),
    with no opaque callee anywhere in the spec. There is no answer key an
    implementation could echo instead of doing the work — echoing the grounded
    computation IS the work. In its place the battery carries honest
    cheapest-implementation POSITIVE CONTROLS that must verify. (nagini
    ``pos-control-echo-inline``.)

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where a specific conjunct or the ordering bites: dropping the
    resolved-value-empty conjunct (the fix), dropping the editable gate, dropping
    the skip-set gate, dropping the name-restriction gate, and dropping the
    file-deferral ordering.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input and refuting it. The carrier is FULLY TRANSPARENT (every field is
a concrete ``Bool``/``String``, no ``opaque`` callee), so each witness closes by
plain ``decide`` after unfolding the grounded predicate. Each was checked to HOLD
of its rival (the file elaborates) and to FAIL on the frozen solution (``decide``
reports the proposition is false), so it discriminates rather than asserting a
tautology.

BINDER / POINT SPREAD. The frozen ``problem_spec_bindFields`` binds three inputs
— ``nameFilter : Option (List String)``, ``skipNames : List String``, and
``fields : List FieldInput`` (each record carrying nine sub-fields) — plus the
result. The reject witnesses move all three: ``nameFilter`` takes both ``none``
and ``some [...]`` (the name-restriction rival); ``skipNames`` takes both ``[]``
and a non-empty list (the skip-gate rival); and ``fields`` ranges over records
that exercise each per-record sub-field independently — the defaulted/omitted/
non-empty combination (the fix), a non-editable record, a skipped record, a
name-filtered record, and a file/non-file pair that exposes the two-pass order.
No two rivals share a refutation point; the five reject witnesses probe five
distinct inputs.

AXIOM lane: EMPTY here. The bundle consumes no ``axiom`` and declares no
``opaque`` callee — every per-field predicate is supplied as a boolean field of
the input record. The nagini ``AXIOM_TESTS`` were also empty; dropped.
"""
from pathlib import Path

INSTANCE = "django__django-11433"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----

# The full frozen impl def body (from the `def` line through the last line
# before `-- impl-end`). Used by the soundness positives that replace the whole
# imperative body with a structurally different but definitionally-equal form.
_IMPL_FULL = _BASE[_BASE.index("def implementation_bindFields"):
                   _BASE.index("-- impl-end")]

# The frozen proof body (proof region tactic script). The soundness positives
# reprove here; kept inside proof-start/proof-end so same_spec holds.
_PROOF_FULL = (
    "  intro nameFilter skipNames fields\n"
    "  unfold problem_spec_bindFields assignmentsFor\n"
    "  rw [impl_as_foldl, FoldInv_final]"
)

# Individual impl-region guard anchors (each entirely inside the impl loop).
_A_GATE = (
    "    if !f.editable || f.isAuto || !f.inResolved then\n"
    "      continue"
)
_A_NAME = (
    "      if !names.contains f.name then\n"
    "        continue"
)
_A_SKIP = (
    "    if !skipNames.isEmpty && skipNames.contains f.name then\n"
    "      continue"
)
_A_EMPTY = (
    "    if f.hasDefault && f.omitted && f.resolvedEmpty then\n"
    "      continue"
)
_A_FILE = (
    "    if f.isFile then\n"
    "      fileFields := fileFields ++ [(f.name, f.resolvedValue)]\n"
    "    else\n"
    "      assigned := assigned ++ [(f.name, f.resolvedValue)]"
)


# ---- soundness-positive builders (replace impl body AND reprove with `rfl`) ----
# A structurally different impl that is DEFINITIONALLY equal to `assignmentsFor`
# lets the obligation close by `intro …; rfl`. This keeps the theorem STATEMENT
# byte-identical, introduces no new declaration / axiom / assumption token, and
# does not weaken the obligation.
#
# The frozen proof region carries several bridge lemmas (`step`, `impl_as_foldl`,
# `FoldInv_final`, …) whose STATEMENTS mention the frozen imperative `Id.run do`
# form of the implementation; once the impl is reshaped those lemmas no longer
# typecheck. Since a functional reshape closes the obligation directly by `rfl`,
# these bridge lemmas are no longer needed, so the whole proof region is replaced
# with just the (byte-identical-statement) `correct_bindFields` closed by `rfl`.
# Removing frozen helper declarations is scope-legal — the scope check flags only
# NEW declarations and only requires the `correct_bindFields` STATEMENT to
# survive; no new axiom/assumption token is introduced.

# The entire frozen proof region body (between the region markers).
_PROOF_REGION = _BASE[_BASE.index("-- proof-start\n") + len("-- proof-start\n"):
                      _BASE.index("-- proof-end")]

# The reshaped proof region: only the correctness theorem, closed by `rfl`.
_RFL_PROOF_REGION = (
    "theorem correct_bindFields :\n"
    "    ∀ (nameFilter : Option (List String)) (skipNames : List String)\n"
    "      (fields : List FieldInput),\n"
    "      problem_spec_bindFields nameFilter skipNames fields\n"
    "        (implementation_bindFields nameFilter skipNames fields) := by\n"
    "  intro nameFilter skipNames fields\n"
    "  rfl\n"
)


def _reshape(new_impl_body):
    src = _swap(_BASE, _IMPL_FULL, new_impl_body)
    return _swap(src, _PROOF_REGION, _RFL_PROOF_REGION)

# S1: the impl IS the grounded computation `assignmentsFor` applied to the
# inputs — the cheapest correct implementation. Definitionally equal to the
# spec RHS, so `rfl` closes.
_POS_ASSIGNMENTSFOR = _reshape(
    "def implementation_bindFields (nameFilter : Option (List String))\n"
    "    (skipNames : List String) (fields : List FieldInput) :\n"
    "    List (String × String) :=\n"
    "  assignmentsFor nameFilter skipNames fields\n",
)

# S2: the impl inlines the two-pass filter/map body of `assignmentsFor`
# (structurally distinct from S1 — no call to the helper — and from the frozen
# imperative loop). Still definitionally equal, so `rfl` closes.
_POS_INLINE_TWOPASS = _reshape(
    "def implementation_bindFields (nameFilter : Option (List String))\n"
    "    (skipNames : List String) (fields : List FieldInput) :\n"
    "    List (String × String) :=\n"
    "  let kept := fields.filter (assignField nameFilter skipNames)\n"
    "  (kept.filter (fun f => !f.isFile)).map emit\n"
    "    ++ (kept.filter (fun f => f.isFile)).map emit\n",
)


# ---- admissibility positive (frozen proof + a ground F2P `have`) ----
# Discharge the obligation at the F2P-shaped input (a defaulted, omitted field
# whose resolved value is NON-empty ⇒ emitted) by `decide`, then close the
# frozen obligation verbatim. Nothing is assumed: no new declaration, the
# theorem statement is byte-identical, the ground instance is a `have` inside
# the existing tactic body.
_ADMISS = _swap(
    _BASE, _PROOF_FULL,
    "  have _ground : problem_spec_bindFields none []\n"
    "      [{ name := \"modefield\", editable := true, isAuto := false,\n"
    "         inResolved := true, hasDefault := true, omitted := true,\n"
    "         resolvedEmpty := false, isFile := false, resolvedValue := \"de\" }]\n"
    "      (implementation_bindFields none []\n"
    "      [{ name := \"modefield\", editable := true, isAuto := false,\n"
    "         inResolved := true, hasDefault := true, omitted := true,\n"
    "         resolvedEmpty := false, isFile := false, resolvedValue := \"de\" }]) := by\n"
    "    unfold problem_spec_bindFields\n"
    "    decide\n"
    + _PROOF_FULL,
)


# ---- reject-case impl builders (edit ONE guard inside the impl region) ----
def _rej(old, new):
    return _swap(_BASE, old, new)


# REJECT 1 (ports nagini REJECT 1, the prepatch rival): drop the added
# resolved-value-empty conjunct, leaving the pre-patch guard
# `hasDefault ∧ omitted`. Diverges exactly on the defaulted+omitted+NON-empty
# record — the F2P scenario.
_REJECT_PREPATCH = _rej(
    _A_EMPTY,
    "    if f.hasDefault && f.omitted then\n"
    "      continue",
)

# REJECT 2 (ports nagini REJECT 3, drop-the-candidacy-gate): drop the
# `editable` conjunct from the keep decision, so a non-editable record is
# emitted when the spec keeps it out.
_REJECT_EDITABLE = _rej(
    _A_GATE,
    "    if f.isAuto || !f.inResolved then\n"
    "      continue",
)

# REJECT 3 (ports nagini REJECT 3 family, a second candidacy gate): drop the
# skip-set gate entirely, so a record whose name is in a non-empty skip set is
# emitted when the spec keeps it out.
_REJECT_SKIP = _rej(
    _A_SKIP,
    "    if false then\n"
    "      continue",
)

# REJECT 4 (no direct nagini counterpart — this carrier adds the name-restriction
# input the nagini surface did not model): drop the explicit-name-restriction
# gate, so a record outside a `some [...]` restriction is emitted when the spec
# keeps it out. Attacks the `nameFilter` binder specifically.
_REJECT_NAMEFILTER = _rej(
    _A_NAME,
    "      if false then\n"
    "        continue",
)

# REJECT 5 (no direct nagini counterpart — this carrier adds the ordered output
# list and the file-deferral two-pass the nagini per-index surface did not
# model): drop the file deferral, emitting every kept record into the single
# pass in field order. Diverges on any input mixing kept file and non-file
# records where a file record precedes a non-file one.
_REJECT_ORDER = _rej(
    _A_FILE,
    "    assigned := assigned ++ [(f.name, f.resolvedValue)]",
)

# REJECT 6 (ports nagini REJECT 2, `reject-partial-first-element`): a
# POSITIONAL corruption that is orthogonal to every per-record guard — it is
# correct on every record EXCEPT the first one processed, which it always
# skips regardless of the decision. Introduces a loop index and `continue`s on
# index 0. Diverges from the spec on any input whose first record qualifies
# (e.g. a single eligible record: the spec emits it, the rival emits nothing).
# The nagini port claimed no counterpart for this class was carried; it is
# expressible here (verified: rival reshaped-out, witness holds of the rival,
# fails on gold by a `decide` refutation).
_A_LOOP_HEAD = (
    "  let mut fileFields : List (String × String) := []\n"
    "  for f in fields do\n"
)
_REJECT_FIRSTELEM = _rej(
    _A_LOOP_HEAD,
    "  let mut fileFields : List (String × String) := []\n"
    "  let mut idx : Nat := 0\n"
    "  for f in fields do\n"
    "    if idx == 0 then\n"
    "      idx := idx + 1\n"
    "      continue\n"
    "    idx := idx + 1\n",
)


# A per-record field literal helper for the witnesses (documentation aside — the
# witnesses embed the literals directly so the gate reads them verbatim).

SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem statement byte-identical and introduces no new
    # declaration / axiom / assumption token.
    #
    # Ports nagini `pos-control-helper` and `pos-control-echo-inline`: the two
    # nagini positives called the grounded @Pure helper and inlined its body.
    # Here the analogues call the grounded helper `assignmentsFor` and inline
    # its two-pass body — both definitionally equal to the spec RHS, so `rfl`
    # closes.
    # =====================================================================
    {
        "id": "pos-call-grounded-helper",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_ASSIGNMENTSFOR,
        "rationale": (
            "structurally-different CORRECT impl: the result IS the grounded "
            "computation applied to the inputs (the cheapest correct impl), "
            "instead of the imperative two-accumulator loop. Definitionally "
            "equal to the spec RHS, so the obligation `result = "
            "assignmentsFor …` closes by `intro …; rfl`. The theorem statement "
            "is byte-identical; no new declaration / axiom / assumption token. "
            "If this cannot verify => SPEC-TOO-STRONG. Ports nagini "
            "`pos-control-helper` (bind-the-@Pure-helper positive)."
        ),
    },
    {
        "id": "pos-inline-two-pass",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_INLINE_TWOPASS,
        "rationale": (
            "a second structurally-different CORRECT impl: inline the two-pass "
            "filter/map body (keep the records passing the decision, emit "
            "non-file first then file) WITHOUT calling the helper. Distinct in "
            "shape from both the frozen imperative loop and the "
            "call-the-helper positive, yet definitionally equal to the spec "
            "RHS, so `rfl` closes. Documents that the only available 'echo' is "
            "the truthful grounded computation itself — there is no wrong echo. "
            "Ports nagini `pos-control-echo-inline`."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the F2P-shaped input rather than only in the
    # abstract. The frozen theorem carries NO precondition hypothesis (the
    # modeled behavior is total, so `∀` is unguarded), so the nagini
    # precondition-admission probe (`admiss-f2p-shaped`) has no binder to attack;
    # the honest analogue is to discharge the spec predicate by evaluation at the
    # ground F2P-shaped input alongside the frozen obligation.
    # Ports nagini `admiss-f2p-shaped`.
    # =====================================================================
    {
        "id": "admiss-f2p-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the obligation is discharged at the F2P-shaped input (a single "
            "field carrying a default, omitted from the payload, whose resolved "
            "value is NON-empty ⇒ emitted with that resolved value) by "
            "`decide`, then the frozen obligation is closed verbatim. Verifies "
            "(else the modeled behavior is unsatisfiable at exactly the input "
            "the F2P exercises — the analogue of PRECOND-TOO-STRONG). Nothing is "
            "assumed: no new declaration, the theorem statement is "
            "byte-identical, and the ground instance is a `have` inside the "
            "existing tactic body. Ports nagini's F2P-shaped admissibility "
            "probe."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P (or would
    # regress P2P), so a verifying rival would be a true
    # verify-does-not-imply-resolve break rather than an artifact, and (b) a
    # refutation witness pinning the violation at one concrete input, checked to
    # hold of the rival and to FAIL on the frozen solution.
    # =====================================================================

    # ---- the fix itself: drop the resolved-value-empty conjunct (nagini REJECT 1) ----
    {
        "id": "reject-prepatch-drop-empty-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_PREPATCH,
        "refinement": (
            "this rival IS the pre-fix behaviour: it leaves a defaulted, "
            "omitted field at its default REGARDLESS of the resolved value, "
            "dropping the added conjunct that the resolved value must itself be "
            "empty. On the reported scenario (a field with a default whose "
            "value was omitted from the payload but whose resolved value is "
            "non-empty) it discards that resolved value in favour of the default "
            "— it emits NOTHING where the fix emits the resolved value. The F2P "
            "test asserts the resolved value is populated, so the faithful real "
            "patch would NOT resolve."
        ),
        "rationale": (
            "REJECT from the CHANGED conjunct of the per-record decision: on the "
            "defaulted+omitted+NON-empty record the spec keeps the record and "
            "emits its `(name, value)`, while the rival keeps it OUT, so "
            "`result` differs (the spec's non-empty list vs the rival's empty "
            "list). Binder spread: nameFilter=none, skipNames=[], a single "
            "record exercising exactly the fix's sub-domain. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted at the F2P-shaped record: default present, value omitted,\n"
            "-- resolved value NON-empty ⇒ the spec emits it, the rival drops it.\n"
            "-- Fully concrete carrier, closes by `decide`.\n"
            "example : ¬ problem_spec_bindFields none []\n"
            "    [{ name := \"f\", editable := true, isAuto := false, inResolved := true,\n"
            "       hasDefault := true, omitted := true, resolvedEmpty := false,\n"
            "       isFile := false, resolvedValue := \"v\" }]\n"
            "    (implementation_bindFields none []\n"
            "    [{ name := \"f\", editable := true, isAuto := false, inResolved := true,\n"
            "       hasDefault := true, omitted := true, resolvedEmpty := false,\n"
            "       isFile := false, resolvedValue := \"v\" }]) := by\n"
            "  unfold problem_spec_bindFields\n"
            "  decide\n"
        ),
    },

    # ---- drop the editable candidacy gate (ports nagini REJECT 3) ----
    {
        "id": "reject-drop-editable-gate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_EDITABLE,
        "refinement": (
            "a faithful real patch that dropped the editability gate would emit "
            "an assignment for a field that must never receive a form value "
            "(a non-editable field), corrupting the built instance and "
            "regressing the P2P suite (the non-editable-field behaviour); it "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from the editable conjunct of the per-record decision: a "
            "non-editable record must be kept OUT (emit nothing), but this rival "
            "emits it, so `result` differs. Binder spread: a single "
            "non-editable record; the only rival moving the `editable` "
            "sub-field. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- A non-editable record: spec keeps it out (empty result), the\n"
            "-- rival emits it. Concrete carrier, `decide`.\n"
            "example : ¬ problem_spec_bindFields none []\n"
            "    [{ name := \"f\", editable := false, isAuto := false, inResolved := true,\n"
            "       hasDefault := false, omitted := false, resolvedEmpty := false,\n"
            "       isFile := false, resolvedValue := \"v\" }]\n"
            "    (implementation_bindFields none []\n"
            "    [{ name := \"f\", editable := false, isAuto := false, inResolved := true,\n"
            "       hasDefault := false, omitted := false, resolvedEmpty := false,\n"
            "       isFile := false, resolvedValue := \"v\" }]) := by\n"
            "  unfold problem_spec_bindFields\n"
            "  decide\n"
        ),
    },

    # ---- drop the skip-set gate (ports nagini REJECT 3 family) ----
    {
        "id": "reject-drop-skip-gate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_SKIP,
        "refinement": (
            "a faithful real patch that ignored the caller's non-empty set of "
            "names to skip would emit assignments for explicitly-excluded "
            "fields, writing values the caller asked to withhold; it regresses "
            "the exclude-fields P2P behaviour and does NOT resolve."
        ),
        "rationale": (
            "REJECT from the skip-set conjunct of the per-record decision: with "
            "a non-empty skipNames containing the record's name the spec keeps "
            "the record OUT, but this rival emits it, so `result` differs. "
            "Binder spread: this is the ONLY rival moving the `skipNames` binder "
            "off `[]`. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- The record's name is in a non-empty skip set: spec keeps it out,\n"
            "-- rival emits it. Concrete carrier, `decide`. Moves skipNames.\n"
            "example : ¬ problem_spec_bindFields none [\"a\"]\n"
            "    [{ name := \"a\", editable := true, isAuto := false, inResolved := true,\n"
            "       hasDefault := false, omitted := false, resolvedEmpty := false,\n"
            "       isFile := false, resolvedValue := \"v\" }]\n"
            "    (implementation_bindFields none [\"a\"]\n"
            "    [{ name := \"a\", editable := true, isAuto := false, inResolved := true,\n"
            "       hasDefault := false, omitted := false, resolvedEmpty := false,\n"
            "       isFile := false, resolvedValue := \"v\" }]) := by\n"
            "  unfold problem_spec_bindFields\n"
            "  decide\n"
        ),
    },

    # ---- drop the explicit-name-restriction gate (carrier-specific) ----
    {
        "id": "reject-drop-name-restriction",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_NAMEFILTER,
        "refinement": (
            "a faithful real patch that ignored the caller's explicit set of "
            "field names to work on would emit assignments for fields outside "
            "that set, writing values for fields the caller restricted away; it "
            "regresses the restricted-fields P2P behaviour and does NOT resolve."
        ),
        "rationale": (
            "REJECT from the name-restriction conjunct of the per-record "
            "decision: with nameFilter = some [\"x\"] and a record named \"y\", "
            "the spec keeps the record OUT, but this rival emits it, so "
            "`result` differs. Binder spread: this is the ONLY rival moving "
            "`nameFilter` off `none`. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- A record outside the some-restriction: spec keeps it out, rival\n"
            "-- emits it. Concrete carrier, `decide`. Moves nameFilter to some.\n"
            "example : ¬ problem_spec_bindFields (some [\"x\"]) []\n"
            "    [{ name := \"y\", editable := true, isAuto := false, inResolved := true,\n"
            "       hasDefault := false, omitted := false, resolvedEmpty := false,\n"
            "       isFile := false, resolvedValue := \"v\" }]\n"
            "    (implementation_bindFields (some [\"x\"]) []\n"
            "    [{ name := \"y\", editable := true, isAuto := false, inResolved := true,\n"
            "       hasDefault := false, omitted := false, resolvedEmpty := false,\n"
            "       isFile := false, resolvedValue := \"v\" }]) := by\n"
            "  unfold problem_spec_bindFields\n"
            "  decide\n"
        ),
    },

    # ---- drop the file-deferral two-pass ordering (carrier-specific) ----
    {
        "id": "reject-drop-file-deferral-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_ORDER,
        "refinement": (
            "a faithful real patch that assigned file fields inline in field "
            "order (rather than deferring them to a second pass) would run a "
            "file field's assignment before a later non-file field's value is "
            "available — the deferral exists precisely so a callable upload "
            "target can read the other fields' values. It reorders the emitted "
            "assignment sequence and regresses the file-field ordering P2P "
            "behaviour; it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the two-pass ORDERING clause: on an input with a kept "
            "FILE record before a kept non-file record, the spec emits the "
            "non-file record first (file deferred), while this rival emits them "
            "in field order (file first), so the ordered `result` list differs "
            "even though the same pairs are present. Binder spread: a "
            "file/non-file record pair; the only rival exercising the `isFile` "
            "sub-field and the output ordering. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- A kept FILE record before a kept non-file record: the spec\n"
            "-- defers the file (non-file first), the rival keeps field order.\n"
            "-- Concrete carrier, `decide`.\n"
            "example : ¬ problem_spec_bindFields none []\n"
            "    [{ name := \"g\", editable := true, isAuto := false, inResolved := true,\n"
            "       hasDefault := false, omitted := false, resolvedEmpty := false,\n"
            "       isFile := true, resolvedValue := \"G\" },\n"
            "     { name := \"h\", editable := true, isAuto := false, inResolved := true,\n"
            "       hasDefault := false, omitted := false, resolvedEmpty := false,\n"
            "       isFile := false, resolvedValue := \"H\" }]\n"
            "    (implementation_bindFields none []\n"
            "    [{ name := \"g\", editable := true, isAuto := false, inResolved := true,\n"
            "       hasDefault := false, omitted := false, resolvedEmpty := false,\n"
            "       isFile := true, resolvedValue := \"G\" },\n"
            "     { name := \"h\", editable := true, isAuto := false, inResolved := true,\n"
            "       hasDefault := false, omitted := false, resolvedEmpty := false,\n"
            "       isFile := false, resolvedValue := \"H\" }]) := by\n"
            "  unfold problem_spec_bindFields\n"
            "  decide\n"
        ),
    },

    # ---- positional corruption: skip the first record processed (nagini REJECT 2) ----
    {
        "id": "reject-skip-first-record",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_FIRSTELEM,
        "refinement": (
            "a faithful real patch that special-cased the first iterated field "
            "to never receive its resolved value would, on a form whose first "
            "(or only) field qualifies — the F2P single-field form is exactly "
            "the 0th and only field — leave that field at its default and NOT "
            "resolve; it also regresses any P2P behaviour that assigns the first "
            "field. This class is ORTHOGONAL to the per-record guards: it "
            "corrupts by list position, not by any observable sub-field."
        ),
        "rationale": (
            "REJECT independent of every guard conjunct: the rival is correct on "
            "every record except the first one processed, which it drops "
            "unconditionally. On a single eligible record the spec emits its "
            "`(name, value)` while the rival emits nothing, so `result` differs. "
            "Binder spread: nameFilter=none, skipNames=[], a single eligible "
            "record — the same point the prepatch rival's F2P uses, but the "
            "divergence here is positional, not from the leave-default guard. If "
            "it verified => SPEC-TOO-WEAK. Ports nagini `reject-partial-first-"
            "element`, which the original port dropped without a counterpart."
        ),
        "witness": (
            "-- A single eligible record: the spec emits it, the rival (which\n"
            "-- skips whatever record is processed first) emits nothing.\n"
            "-- Concrete carrier, closes by `decide`.\n"
            "example : ¬ problem_spec_bindFields none []\n"
            "    [{ name := \"f\", editable := true, isAuto := false, inResolved := true,\n"
            "       hasDefault := false, omitted := false, resolvedEmpty := false,\n"
            "       isFile := false, resolvedValue := \"v\" }]\n"
            "    (implementation_bindFields none []\n"
            "    [{ name := \"f\", editable := true, isAuto := false, inResolved := true,\n"
            "       hasDefault := false, omitted := false, resolvedEmpty := false,\n"
            "       isFile := false, resolvedValue := \"v\" }]) := by\n"
            "  unfold problem_spec_bindFields\n"
            "  decide\n"
        ),
    },
]

# No AXIOM lane here: the bundle consumes no `axiom` and declares no `opaque`
# callee (every per-field predicate is a boolean field of the input record).
# The nagini AXIOM_TESTS were also empty; dropped.
AXIOM_TESTS = []
