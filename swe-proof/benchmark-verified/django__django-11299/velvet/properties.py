"""properties.py — G-PBT (spec-lane) falsification battery for
django__django-11299, PORTED from the nagini bundle's design doc to the velvet
(Lean 4 + Velvet) carrier. NOT a Velvet module: a record of adversarial,
instance-specific cases. The runner writes each `module` to a temp file,
verifies it, and checks markers.same_spec against the frozen Solution.lean.
Every case edits ONLY text inside the `-- impl-start` / `-- impl-end` region
(and, for the reshapes, nothing else — the `prove_correct` block here closes
by `loom_solve` regardless of impl shape, so the reshapes keep it verbatim), so
the frozen spec (the `ensures`, the pure model, the obligation) is provably
untouched and `markers.same_spec` holds by construction.

DEFENDED SURFACE (from Solution.lean + mapping.md + instance.json):
  method assignColumnForms (bare : Bool) (conds : List Cond)
      return (result : List ResolvedCond)
    ensures result = columnForms bare conds

There is ONE contracted method and ONE load-bearing `ensures` clause. It pins
the ENTIRE output at once: the grouping STRUCTURE is preserved, and every leaf
at every nesting depth receives the column form `formOf bare`, where descent
into a nested `.group` threads the SAME selector `bare` unchanged. `columnForms`
is a total, fully-unfolded DEEP model of the method's own inputs (the `axioms`
region is empty — no opaque answer key). It composes three independently-
attackable sub-behaviors:
  * the leaf's column form is `formOf bare` — NOT a constant (attacked by R2);
  * the selector is threaded UNCHANGED into a nested group — NOT reset to a
    default (attacked by R1, the literal pre-fix defect);
  * a nested group's leaves are PRESERVED, not dropped (attacked by R3);
  * a nested group stays its own NODE — its members are not spliced into the
    enclosing level (attacked by R4).

The two INPUT binders are both free and the post-image must hold for EVERY
value of each:
  * `bare : Bool`       — the column-form selector threaded through the walk;
  * `conds : List Cond` — the condition forest (atoms and nested groups).

ADVERSARIAL READ of the nagini classes:
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling's
    two mandatory frame-mutation rivals write back into a read-only tree/list
    input carrying only a fractional heap permission (`Acc(q_pred(head),1/2)` /
    `Acc(list_pred(src),1/2)`) and are rejected for INSUFFICIENT PERMISSION.
    Lean and Velvet are referentially transparent: `bare` and `conds` are
    immutable values, this bundle declares no `mut` binder, there is no heap and
    no aliasing. There is no read-only input to overwrite and no permission
    system to trip, so the class is vacuous. No substitute is fabricated (per
    the porting map, this class is legitimately dropped rather than replaced).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to
    `columnForms bare conds`, computed entirely from the method's own arguments
    by a concrete `def` in the `pure` region; the `axioms` region is empty. An
    impl that "echoes the oracle" IS the correct impl; the honest controls are
    the structurally-different reshapes (V1/V2/V3).
  * CONTROL-FLOW / SIDE-EFFECT — N/A. The method returns a pure value; there is
    no raise / side-effect distinction invisible to the value abstraction.
  * PARTIAL-DOMAIN / VALUE — heavily exercised. A rival can be correct on the
    flat / group-free / bare=true sub-domain yet diverge once a nested group or
    the other selector value appears: the pre-fix descent-resets-selector defect
    (R1), a leaf that ignores the selector (R2), a group whose leaves are
    dropped (R3), and a group whose members are spliced into the enclosing
    level (R4).

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is RECURSIVE (a
`termination_by` / `decreasing_by` walk), so its extracted program
(`assignColumnFormsExec`) is defined by well-founded recursion, which the kernel
will NOT reduce under `decide` — and `ResolvedCond` carries no `DecidableEq`
(a nested inductive, so the derive handler does not apply), so the tester-
equality route used by the straight-line bundles is unavailable here. Each
reject witness therefore states the refutation as a DISEQUALITY on the extracted
program at one concrete input:

    example : assignColumnFormsExec <in> ≠ DivM.res (columnForms <in>) := by
      unfold assignColumnFormsExec
      simp only [assignColumnForms, columnForms, columnForm, formOf]
      intro h; injection h with h; simp at h

`simp only [assignColumnForms, …]` unfolds BOTH the (equational) extracted
program AND the deep model on the concrete input (both reduce fully — the
recursion is over a finite literal forest); `injection` peels the `DivM.res`
constructor and `simp` decides the residual constructor (dis)equality via
`ResolvedCond`'s structural injectivity lemmas. Against a rival the residual is
a FALSE equation, so `simp at h` closes the goal (`False` from a contradictory
hypothesis) and the witness ELABORATES. Against the frozen solution the residual
is TRUE (gold satisfies the spec at every input), so `h` is consistent, `simp`
cannot derive `False`, and the goal `⊢ False` is left unsolved — the build
FAILS. That is exactly the discrimination the gate requires. No witness binds
any hypothesis (all inputs are concrete literals), so there is no consistency
obligation. No `sorry` / `admit` / `native_decide` is used.

All FOUR witnesses were checked out-of-band with `scripts/lean_verify.sh`:
each ELABORATES against its rival (exit 0) and FAILS against the frozen solution
(exit 1), so each rejection is a genuine spec refutation and not mechanical
tactic breakage.

WHY THE GOLD-SIDE FAILURE IS SEMANTIC AND NOT A TACTIC MISMATCH. Gold fails each
witness with `unsolved goals / h : True / ⊢ False`, which is not self-evidently a
refutation — an error that would appear for ANY claim carries no information about
THIS claim. It was therefore established by experiment rather than by reading,
twice over, per reject case:
  * TYPE-REVEALING probe. Append `exact (h : Nat)` after `simp at h`, forcing Lean
    to print `h`'s real type. Against gold: `Type mismatch / h has type True` —
    `simp` PROVED the residual equation, i.e. gold satisfies the post-image at
    that input, so `h` collapsed to `True` and `False` is correctly unreachable.
    Against each rival: `No goals to be solved` — `simp` derived `False` from the
    residual and CLOSED the goal before the probe ran. Opposite outcomes on the
    two sides, so the exit code tracks the claim.
  * FLIPPED-CLAIM probe. Assert the OPPOSITE (`=` for `≠`) and read the residual
    goal on each side. It differs per side and per input, naming the actual
    values: gold `[group [atom bare]] = [group [atom bare]]` (a true equation),
    rival R1 `[group [atom qualified]] = [group [atom bare]]`, R2
    `[atom bare] = [atom qualified]`, R3 `[group []] = [group [atom bare]]`,
    R4 `[atom bare, atom bare] = [group [atom bare], atom bare]`. The error text
    CHANGES with the claim and with the impl, which is what distinguishes a real
    refutation from a signature that would appear regardless.

NOTE on the earlier verify-only ship. A previous port shipped this battery
verify-only (NO-REJECT-LANE), on the grounds that no reject witness could be
built here. That diagnosis was caused by a gate-tooling bug: the frozen
`prove_correct assignColumnForms` block continues with `termination_by` /
`decreasing_by` / `by` at COLUMN 0 (Lean permits it — all one command), and the
witness-file preprocessor stopped at the first column-0 line, orphaning those
clauses so the witness file failed to PARSE for both builds. That preprocessor
(`pbt_witness._strip_prove_correct`) now consumes the continuation clauses with
the block they belong to, so the witness files build cleanly and R1/R2/R3/R4 are
landed below with the disequality witnesses above.

AXIOM lane: EMPTY by design. `columnForms` / `formOf` is an A-REFERENCE deep
model validated `== _get_col` (the real, unchanged column-reference operation)
by G-AX / axiom_check.py, NOT this gate's job. The nagini
`axref-leaf_modes-vs-build_where` probe belongs to that lane. `AXIOM_TESTS = []`.
"""
from pathlib import Path

INSTANCE = "django__django-11299"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors (each unique inside the single impl region) --------------------

_EMPTY = "    | [] => return []"

_ATOM = (
    "    | .atom :: rest =>\n"
    "      let tailR ← assignColumnForms bare rest\n"
    "      return (ResolvedCond.atom (formOf bare)) :: tailR"
)

_GROUP = (
    "    | .group inner :: rest =>\n"
    "      let innerR ← assignColumnForms bare inner\n"
    "      let tailR ← assignColumnForms bare rest\n"
    "      return (ResolvedCond.group innerR) :: tailR"
)

# Sub-anchors inside the group branch (each unique in the file), used to inject
# the two group-branch defects without disturbing the surrounding lines.
_GROUP_INNER_CALL = "      let innerR ← assignColumnForms bare inner\n"
_GROUP_ATOM_FORM = "      return (ResolvedCond.atom (formOf bare)) :: tailR"


# ---------------------------------------------------------------------------
# Witness builder. A reject witness reaches the sole `ensures` clause through
# Velvet's extracted program (`extract_program_for` -> `assignColumnFormsExec`),
# stated as a DISEQUALITY against the deep model at one concrete input, checked
# in a file whose `prove_correct` block has been stripped so no tactic script
# can mask the verdict. Because both the extracted program and the deep model
# reduce fully on a finite literal forest, `simp only [assignColumnForms, …]`
# unfolds both; `injection` + `simp` then decides the residual constructor
# (dis)equality via `ResolvedCond`'s structural injectivity. Elaborates against
# a rival (residual false -> `simp` derives `False`); fails against gold
# (residual true -> `⊢ False` unsolved). No hypotheses are bound, so the witness
# is unconditional and carries no consistency obligation.
# ---------------------------------------------------------------------------
def _witness(inp):
    return (
        "extract_program_for assignColumnForms\n\n"
        f"example : assignColumnFormsExec {inp}\n"
        f"    ≠ DivM.res (columnForms {inp}) := by\n"
        "  unfold assignColumnFormsExec\n"
        "  simp only [assignColumnForms, columnForms, columnForm, formOf]\n"
        "  intro h\n"
        "  injection h with h\n"
        "  simp at h\n"
    )


# ============================================================================
# SPEC_TESTS
# ============================================================================

SPEC_TESTS = []

# ---------------------------------------------------------------------------
# V1. POSITIVE CONTROL (soundness). Port of nagini pos-control-reorder-descents.
#     Reorder the two INDEPENDENT recursive descents in the group branch
#     (compute the tail before the inner forest); the returned value is
#     unchanged (innerR still names the inner resolution, tailR the tail). A
#     correct, structurally-different impl MUST verify — else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "pos-control-reorder-descents",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _BASE, _GROUP,
        "    | .group inner :: rest =>\n"
        "      let tailR ← assignColumnForms bare rest\n"
        "      let innerR ← assignColumnForms bare inner\n"
        "      return (ResolvedCond.group innerR) :: tailR"),
    "rationale": "Reordering the two independent recursive calls leaves the "
                 "returned value identical (same inner resolution, same tail), "
                 "so a correct impl of the modeled behavior must still verify; "
                 "if it could not, the spec would be SPEC-TOO-STRONG. "
                 "(soundness — the sole `ensures` clause)",
})

# ---------------------------------------------------------------------------
# V2. POSITIVE CONTROL (soundness) — leaf branch. Let-bind the leaf's column
#     form before constructing the resolved atom; semantics-preserving. Defends
#     the LEAF sub-behavior of the obligation (the one reject rival R2 attacks).
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "pos-control-leaf-letbind",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _BASE, _ATOM,
        "    | .atom :: rest =>\n"
        "      let f := formOf bare\n"
        "      let tailR ← assignColumnForms bare rest\n"
        "      return (ResolvedCond.atom f) :: tailR"),
    "rationale": "Naming the leaf column form `formOf bare` in a let does not "
                 "change the result; a correct impl of the leaf sub-behavior "
                 "must verify, else the spec would be SPEC-TOO-STRONG on the "
                 "leaf branch. (soundness)",
})

# ---------------------------------------------------------------------------
# V3. POSITIVE CONTROL (soundness) — group branch. Let-bind the resolved group
#     node before consing it onto the tail; semantics-preserving. Defends the
#     GROUP sub-behavior of the obligation (the reject rivals R1/R3 attack).
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "pos-control-group-letbind",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _BASE, _GROUP,
        "    | .group inner :: rest =>\n"
        "      let innerR ← assignColumnForms bare inner\n"
        "      let tailR ← assignColumnForms bare rest\n"
        "      let g := ResolvedCond.group innerR\n"
        "      return g :: tailR"),
    "rationale": "Naming the resolved group node does not change the result; a "
                 "correct impl of the group sub-behavior must verify, else the "
                 "spec would be SPEC-TOO-STRONG on the group branch. "
                 "(soundness)",
})

# ---------------------------------------------------------------------------
# A1. ADMISSIBILITY. Re-aim of nagini admiss-none-head-selfcall for a TOTAL
#     carrier. The analogue of PRECOND-TOO-STRONG on a carrier with no `require`
#     is the obligation being UNSATISFIABLE at exactly an F2P-shaped input: if
#     the post-image demanded something no value can meet there, every impl
#     would be rejected at that point and the whole battery's rejections would
#     be attesting to that instead of to the spec. So this case discharges the
#     obligation AT that concrete input, by evaluation, as an in-region `have`,
#     BEFORE closing the frozen obligation verbatim. The `have` pins two things
#     at the F2P shape (a group followed by a sibling leaf, under the selector
#     the entry point requests):
#       (a) the post-image at that input EVALUATES to a concrete, inhabited
#           value — so it is satisfiable, not vacuous;
#       (b) the two selector values give DIFFERENT post-images there — so the
#           obligation is non-degenerate at the point that matters, rather than
#           a clause both selectors satisfy trivially.
#     Both must discharge and the frozen ensures must still close. Negative
#     controls (out-of-band, `scripts/lean_verify.sh`): corrupting (a) to claim
#     the nested leaf gets the other column form -> exit 1; weakening (b) to `=`
#     -> exit 1. So the `have` is load-bearing, not decoration.
#
#     (The previous shipping version of this case let-bound `[]` in the empty
#     branch. That was hollow: `let e : List ResolvedCond := []; return e` is
#     definitionally the frozen `return []`, so it verified without asking any
#     admissibility question — the honest reading is that it tested nothing.)
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "admiss-f2p-shape-satisfiable",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(
        _BASE, "    match conds with\n" + _EMPTY,
        "    have _f2p :\n"
        "        columnForms true [Cond.group [Cond.atom], Cond.atom]\n"
        "          = [ResolvedCond.group [ResolvedCond.atom ColForm.bare],\n"
        "             ResolvedCond.atom ColForm.bare]\n"
        "        ∧ columnForms true [Cond.group [Cond.atom], Cond.atom]\n"
        "            ≠ columnForms false [Cond.group [Cond.atom], Cond.atom] := by\n"
        "      refine ⟨by simp [columnForms, columnForm, formOf], ?_⟩\n"
        "      simp [columnForms, columnForm, formOf]\n"
        "    match conds with\n" + _EMPTY),
    "rationale": "The method has no `require`, so the PRECOND-TOO-STRONG "
                 "analogue is the sole `ensures` being unsatisfiable or "
                 "degenerate at an F2P-shaped input. The in-region `have` "
                 "discharges the post-image AT that input by evaluation: it is "
                 "inhabited by a concrete value (satisfiable — the nested leaf "
                 "and the sibling leaf both receive the requested form), and the "
                 "two selector values disagree there (non-degenerate — the "
                 "clause is not one both selectors meet trivially). The frozen "
                 "obligation is then closed verbatim, so the case attests the "
                 "in-domain input is admitted AND that its clause is live. If "
                 "either half failed, the obligation would be too strong / "
                 "vacuous exactly where the battery aims. (admissibility)",
})

# ---------------------------------------------------------------------------
# R1. UNIQUENESS / PARTIAL-DOMAIN. Port of nagini partial-prepatch-descent-false
#     — the LITERAL pre-fix defect: descent into a nested group resets the
#     selector to the constant `false` instead of threading the caller's `bare`.
#     Correct on the flat / group-free sub-domain; diverges on any nested leaf
#     when bare=true. Attacks the selector-threading sub-behavior of the sole
#     ensures clause. Refuted at (bare=true, [group [atom]]): gold gives the
#     nested leaf `formOf true = bare`, the rival gives `formOf false =
#     qualified`.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "weak-prepatch-descent-const",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _GROUP_INNER_CALL,
        "      let innerR ← assignColumnForms false inner\n"),
    "refinement": "This is the literal pre-fix behaviour: the recursive descent "
                  "into a nested group omits the propagated selector and falls "
                  "back to its default value, so leaves nested inside a group "
                  "receive the table-qualified column form even when the "
                  "top-level walk requested the bare form. The failing test "
                  "constructs an OR of an AND-group and a leaf and asserts, via "
                  "the entry point that requests the bare form for the whole "
                  "tree, that the leaves nested INSIDE the group are bare; this "
                  "rival leaves them qualified there, so it would NOT resolve — "
                  "it is exactly the change the spec senses.",
    "rationale": "REJECT from the sole `ensures` (result = columnForms bare "
                 "conds) at the selector-threading sub-behavior: the group "
                 "clause demands `columnForms bare inner`, but the rival "
                 "produces `columnForms false inner`; for bare=true and a leaf "
                 "inside the group these disagree (bare != qualified). Refuted "
                 "at (bare=true, [group [atom]]).",
    "witness": _witness("true [Cond.group [Cond.atom]]"),
})

# ---------------------------------------------------------------------------
# R2. UNIQUENESS / PARTIAL-DOMAIN. Port of nagini partial-leaf-hardcode-true,
#     re-expressed for this carrier: the leaf emits the constant `ColForm.bare`
#     regardless of the selector (nagini's `formOf` returns a ColForm, not a
#     bool; "hardcode True" becomes "hardcode the bare form"). Correct only on
#     the bare=true sub-domain; wrong whenever bare=false. Attacks the leaf
#     sub-behavior. Refuted at (bare=false, [atom]): gold gives `formOf false =
#     qualified`, the rival gives `bare`.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "weak-leaf-hardcode-bare",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _GROUP_ATOM_FORM,
        "      return (ResolvedCond.atom ColForm.bare) :: tailR"),
    "refinement": "The real-patch counterpart always builds the bare column "
                  "form regardless of the selector. That breaks every ordinary "
                  "(non-check-constraint) query, which needs the table-qualified "
                  "column form; the PASS_TO_PASS query-construction tests build "
                  "with the default selector and assert the qualified form, so it "
                  "would NOT resolve.",
    "rationale": "REJECT from the sole `ensures` at the leaf sub-behavior: the "
                 "leaf clause is `formOf bare`, but the rival emits the constant "
                 "bare form, which differs from `formOf bare` when bare=false "
                 "(qualified). Refuted at (bare=false, [atom]) — moving the "
                 "`bare` binder to false, the value R1/R3 do not probe.",
    "witness": _witness("false [Cond.atom]"),
})

# ---------------------------------------------------------------------------
# R3. UNIQUENESS / PARTIAL-DOMAIN. Port of nagini partial-drop-group-leaves: a
#     nested group resolves to the EMPTY forest, dropping every leaf inside it.
#     Correct on group-free input; diverges (leaves missing) whenever a group is
#     present. Attacks the group-preservation sub-behavior. Refuted at
#     (bare=true, [group [atom]]): gold gives a one-leaf group, the rival gives
#     an empty group.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "weak-drop-group-leaves",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _GROUP,
        "    | .group inner :: rest =>\n"
        "      let tailR ← assignColumnForms bare rest\n"
        "      return (ResolvedCond.group []) :: tailR"),
    "refinement": "The real-patch counterpart would assemble a nested group but "
                  "never populate it with its child clauses, dropping the entire "
                  "nested sub-expression. The failing test's nested-group leaves "
                  "would be absent from the assembled tree, so its per-leaf "
                  "assertions fail — it would NOT resolve.",
    "rationale": "REJECT from the sole `ensures` at the group-preservation "
                 "sub-behavior: the group clause is `columnForms bare inner`, "
                 "but the rival produces the empty forest, which is shorter "
                 "whenever the group has >=1 member. Refuted at (bare=true, "
                 "[group [atom]]).",
    "witness": _witness("true [Cond.group [Cond.atom]]"),
})

# ---------------------------------------------------------------------------
# R4. UNIQUENESS / PARTIAL-DOMAIN. NOT in the nagini sibling — added by audit,
#     aimed at the one independent sub-behavior of the sole ensures that R1/R2/R3
#     all leave unattacked: the GROUPING STRUCTURE itself. R1 gets a nested
#     leaf's FORM wrong, R3 gets a group's LENGTH wrong (empties it); neither
#     senses a rival that resolves every leaf CORRECTLY, at the right form and
#     with none missing, but SPLICES the group's members into the parent level
#     instead of wrapping them in a group node. On this carrier that is
#     observable — `ResolvedCond.group [x]` and `x` are distinct constructors —
#     and the frozen post-image forbids it, but nothing in the shipped battery
#     probed it. Refuted at (bare=true, [group [atom], atom]): gold gives
#     `[group [atom bare], atom bare]`, the rival gives `[atom bare, atom bare]`
#     — same leaves, same forms, same count, one nesting level lost.
#     Also the battery's only THIRD input point (a group with a non-empty
#     sibling tail), so the `conds` binder now varies over three shapes rather
#     than two.
# ---------------------------------------------------------------------------
SPEC_TESTS.append({
    "id": "weak-flatten-group-node",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, "      return (ResolvedCond.group innerR) :: tailR",
        "      return innerR ++ tailR"),
    "refinement": "The real-patch counterpart would resolve a nested group's "
                  "children correctly and then merge them into the enclosing "
                  "condition level instead of keeping them as their own nested "
                  "sub-expression. Every leaf still gets the right column form, "
                  "so a check that only inspects leaf forms would pass — but the "
                  "assembled tree has lost a nesting level, which changes the "
                  "boolean grouping (an inner AND merged into an outer OR is a "
                  "different condition). The failing test reaches its nested "
                  "leaves by descending one level into the group; with the level "
                  "gone that descent finds nothing, and the query-construction "
                  "tests that assert the assembled tree's shape see the wrong "
                  "structure — so it would NOT resolve.",
    "rationale": "REJECT from the sole `ensures` at the grouping-structure "
                 "sub-behavior: the group clause demands the head be "
                 "`ResolvedCond.group (columnForms bare inner)`, a group NODE, "
                 "but the rival splices `columnForms bare inner` into the parent "
                 "list. Distinct constructors, so they disagree whenever a group "
                 "is present. Refuted at (bare=true, [group [atom], atom]) — a "
                 "group with a non-empty sibling tail, the input point R1/R2/R3 "
                 "do not reach.",
    "witness": _witness("true [Cond.group [Cond.atom], Cond.atom]"),
})


# ============================================================================
# Nagini -> velvet accounting.
# ============================================================================
# The nagini sibling has 7 SPEC cases (1 soundness positive, 1 admissibility, 5
# uniqueness — two of which are the mandatory frame-mutation rivals) plus 1
# AXIOM_TESTS entry. It models TWO functions (compile_children + append_all)
# over READ-ONLY tree/list inputs carrying fractional heap permissions, with the
# accumulation done by a verified `append_all` helper. This backend models the
# SAME core behaviour (thread a selector to every leaf at every depth) as a
# single recursive method over an immutable `List Cond`; the value surface
# carries across intact, the permission surface and the helper do not exist.
#
#   nagini case                       -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-control-reorder-descents       -> pos-control-reorder-descents  PORTED
#   admiss-none-head-selfcall          -> admiss-f2p-shape-satisfiable  RE-AIMED
#   frame-mut-head-field               -> (none)                        VACUOUS
#   frame-mut-src-append               -> (none)                        VACUOUS
#   partial-prepatch-descent-false     -> weak-prepatch-descent-const   PORTED
#   partial-leaf-hardcode-true         -> weak-leaf-hardcode-bare       PORTED (re-expressed)
#   partial-drop-group-leaves          -> weak-drop-group-leaves        PORTED
#   (none)                             -> pos-control-leaf-letbind      ADDED (2nd positive)
#   (none)                             -> pos-control-group-letbind     ADDED (3rd positive)
#   (none)                             -> weak-flatten-group-node       ADDED (4th rival, audit)
#   axref-leaf_modes-vs-build_where    -> (none)                        DROPPED (G-AX lane)
#
# 4 ported, 1 re-aimed, 2 vacuous; 2 extra positive controls and 1 extra rival
# added; 1 axiom-lane entry dropped.
#
# VACUOUS (frame-mut-head-field, frame-mut-src-append): the nagini sibling's two
#   MANDATORY frame-mutation rivals keep the gold body then write back into a
#   read-only input granted only at half permission, and must be rejected for
#   INSUFFICIENT PERMISSION. This backend is referentially transparent: `bare`
#   and `conds` are immutable values, the method declares no `mut` binder, there
#   is no heap and no aliasing. There is no read-only input to overwrite and no
#   permission system to trip, so the class is vacuous. No substitute fabricated.
# RE-AIMED (admissibility): the nagini case witnesses that the fractional
#   precondition on `head` admits head=None. This method has NO precondition
#   (total domain) and no permission surface, so a "the precondition admits this"
#   probe is degenerate here. It is re-aimed at the analogue that is NOT
#   degenerate on a total carrier: the obligation being unsatisfiable or
#   degenerate at an F2P-SHAPED input. A1 discharges the post-image at that
#   concrete input by evaluation, as an in-region `have`, before closing the
#   frozen obligation verbatim — pinning both that the clause is inhabited there
#   and that the two selector values disagree there. Negative controls confirm
#   the `have` is load-bearing (corrupt either conjunct -> the case fails).
# ADDED (pos-control-leaf-letbind, pos-control-group-letbind): two more
#   structurally-distinct correct reshapes, one per branch, so the single
#   obligation is defended at every branch the reject rivals attack.
# DROPPED (axiom lane): the nagini AXIOM_TESTS probe validates the deep model
#   against the real Django callee. That is G-AX / axiom_check.py's job; this
#   gate ignores AXIOM_TESTS. `columnForms` / `formOf` is an A-reference, not a
#   consumed axiom.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the two input binders of
#   the sole ensures (3 distinct input points):
#     bare  — TRUE (R1, R3, R4), FALSE (R2): both values exercised, and the
#             variation is MEANINGFUL rather than two spellings of one point —
#             the selector is exactly what the post-image branches on, so
#             flipping it changes the demanded column form (measured: the flipped
#             -claim residual reads `atom bare` on one value and
#             `atom qualified` on the other).
#     conds — [atom] (R2, a flat leaf), [group [atom]] (R1, R3, a nested group
#             with an empty tail), and [group [atom], atom] (R4, a nested group
#             with a non-empty sibling tail): the atom and group constructors,
#             both nesting depths, and both the empty and non-empty tail of the
#             list recursion.
#   Every independent sub-behavior of the sole post-image is attacked: the
#   selector-threading into a nested group (R1), the per-leaf column form (R2),
#   the group-member preservation (R3), and the group NODE itself (R4). Note R1
#   and R3 share the input (true, [group [atom]]) but fail there for DIFFERENT
#   reasons and are NOT near-misses of one another (R1 gets the leaf's FORM wrong
#   at the right position; R3 gets the group's LENGTH wrong — the leaf is
#   absent), so each witness genuinely discriminates its own rival (verified:
#   rival exit 0, gold exit 1, plus the type-revealing and flipped-claim probes
#   above, for all four).
#
# TOOLING NOTE (bundle-specific, not a spec claim). This bundle's `prove_correct`
#   writes its `termination_by` / `decreasing_by` / `by` clauses at COLUMN 0.
#   `markers._elide_prove_correct` elides a `prove_correct` body only up to the
#   next non-indented line, so on this file the tactic body is NOT elided and
#   lands inside the spec view — which means a variant here may NOT retune its
#   proof script (doing so trips `same_spec`), unlike the sibling velvet bundles
#   whose `prove_correct ... by` is single-line. Every case above therefore keeps
#   the proof block verbatim and is shaped so `loom_solve` still closes it. One
#   consequence is recorded honestly in the audit: a correct reshape that spells
#   the leaf's column form by its `if`-expansion instead of `formOf bare` needs a
#   one-tactic reproof and so cannot be carried as a case on THIS bundle, though
#   it does verify with that reproof (measured, exit 0) — so it is not a
#   SPEC-TOO-STRONG hole, it is a variant-scope interaction with the column-0
#   continuation.
#
# AXIOM_TESTS: dropped (see above).
AXIOM_TESTS = []
