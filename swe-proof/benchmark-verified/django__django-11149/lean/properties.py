# properties.py — G-PBT falsification battery for django__django-11149 (lean lane).
# PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over and
# the mechanics re-expressed against this backend's carrier. Each SPEC case is a
# FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive legitimately reproves, the proof body — is
# edited), checked by variant_scope + the Lean verifier. Every expect="reject"
# case carries a refutation `witness`: a self-contained snippet that ELABORATES
# against the rival and FAILS on the frozen solution, so the rejection is
# attributable to the spec and not to a frozen tactic script that merely stopped
# matching a reshaped impl.
#
# ============================  DEFENDED SURFACE  =============================
#
# FIVE modeled functions over a fully TRANSPARENT carrier (String / List / Bool);
# the auto-created intermediary case of an object editor's four action decisions,
# plus the shared target-permission helper they delegate to:
#
#   hasAnyPermsForTargetModel selfApp selfModel parentId fields userPerms actions
#       result = anyPermForTarget …       -- resolve target, THEN "holds any action"
#   hasAddPermission    autoCreated … superResult
#   hasChangePermission autoCreated … superResult
#   hasDeletePermission autoCreated … superResult
#       (autoCreated → result = anyPermForTarget … ["change"]) ∧
#       (¬autoCreated → result = superResult)
#   hasViewPermission   autoCreated … superResult
#       (autoCreated → result = anyPermForTarget … ["view","change"]) ∧
#       (¬autoCreated → result = superResult)
#
# LOAD-BEARING clauses:
#   * The THREE editing decisions (add/change/delete) pin the auto-created arm to
#     the ["change"] action set — the BUG FIX. The pre-change behaviour delegated
#     to the view rule (["view","change"]); a rival using ["view","change"] for
#     any of the three is exactly the regression — correct when the change
#     permission is held, WRONG on the view-only sub-domain (holds only the view
#     action: it returns True, the spec demands False). This is precisely what the
#     two FAIL_TO_PASS tests assert (a view-only actor must NOT be able to
#     add/change an auto-created intermediary row).
#   * The view decision keeps the ["view","change"] disjunction (unchanged — a
#     pure refactor). A rival dropping the change disjunct denies a
#     change-permitted actor the view.
#   * hasAnyPermsForTargetModel pins BOTH the target RESOLUTION (first field
#     pointing at a related model other than the parent; else the self labels)
#     AND the existential "holds ANY of the listed actions" over the WHOLE action
#     list. A rival consulting only the first action, or ignoring the resolved
#     target, drops one of these.
#   * Each wrapper's SECOND clause pins the non-auto-created arm to the
#     caller-supplied `superResult` passthrough. A rival that ignores the
#     autoCreated flag substitutes the target-model check for that passthrough.
#
# ==========================  NAGINI → LEAN PORT  =============================
#
# The nagini sibling contracts a NARROWER abstraction: five decisions over a
# single read-only permission set `held : PSet[int]`, with target resolution and
# the permission-string format elided. This backend models the FULL surface — the
# target-resolution loop over `fields`, the concrete permission-string format
# (`permString`), and the auto-created/super-delegation split — so more clauses
# are attackable here (target resolution and the superResult passthrough have no
# nagini counterpart; see the accounting block at the bottom).
#
# LANES THAT DO NOT PORT:
#   * FRAME / PERMISSION-MUTATION (nagini's MANDATORY class: `held` is held at
#     Acc(set_pred,1/2) and the rival demands full write permission). Lean is
#     referentially transparent — every input is an immutable value, no `mut`
#     binder escapes the impl, no aliasing, no fractional permission — so a
#     "write to a read-only input" rival is not expressible and the whole lane is
#     VACUOUS here (porting map). Not fabricated; see `assessment`.
#   * DIVERGENCE / NON-TERMINATION. On lean this is genuinely vacuous:
#     `implementation_*` is a TOTAL Lean `def`, so a diverging impl cannot be
#     written at all. (The nagini sibling carries none regardless.)
#   * ADMISSIBILITY: PORTED, not dropped. The lean obligations are `∀ …,
#     problem_spec … (implementation …)` with NO precondition hypothesis, so
#     PRECOND-TOO-STRONG cannot arrive as "the Requires is contradictory" — but
#     that is NOT a reason to drop the lane, and an earlier revision of this file
#     wrongly recorded it as N/A on exactly that argument. On a TOTAL carrier the
#     analogue is the obligation being UNSATISFIABLE at exactly an F2P-shaped
#     input: a spec whose clauses over-constrained the auto-created arm would
#     admit no result value there, and the frozen ∀-obligation would then be
#     closable only vacuously. `admiss-obligation-at-f2p-input` tests that
#     directly — it discharges the obligation BY EVALUATION at two concrete
#     F2P-shaped inputs as `have`s before closing the frozen obligations
#     verbatim. See that case for the vacuity evidence.
#   * AXIOM_TESTS. meta.json axioms == [] and deep_model_references == []; the
#     permission lookup is the transparent `userPerms.contains` and the codename
#     format is modeled deeply as `permString`, so there is no opaque oracle to
#     probe. The axiom lane is G-AX's job; this gate ignores AXIOM_TESTS anyway.
import re as _re
from pathlib import Path

INSTANCE = "django__django-11149"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each is a COMPLETE `def implementation_*` block lying entirely
# inside `-- impl-start`/`-- impl-end`, and unique in the file (the shared
# `["change"]` delegation line occurs in three blocks, so we anchor on the whole
# block, never on that line alone). same_spec is preserved by construction.
# ---------------------------------------------------------------------------

_ANY = (
    "def implementation_hasAnyPermsForTargetModel\n"
    "    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)\n"
    "    (userPerms actions : List String) : Bool := Id.run do\n"
    "  let mut appLabel := selfAppLabel\n"
    "  let mut modelName := selfModelName\n"
    "  for f in fields do\n"
    "    if f.hasRemote && f.remoteModelId != parentModelId then\n"
    "      appLabel := f.remoteAppLabel\n"
    "      modelName := f.remoteModelName\n"
    "      break\n"
    "  for a in actions do\n"
    "    if userPerms.contains (permString appLabel modelName a) then\n"
    "      return true\n"
    "  return false"
)


def _wrapper(name, actions):
    """The frozen `def implementation_<name>` block for an action wrapper."""
    return (
        f"def implementation_{name} (autoCreated : Bool)\n"
        "    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)\n"
        "    (userPerms : List String) (superResult : Bool) : Bool := Id.run do\n"
        "  if autoCreated then\n"
        f"    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms {actions}\n"
        "  return superResult"
    )


def _wrapper_func(name, actions):
    """A structurally-different but observationally-identical wrapper: the
    `Id.run do`/early-return scaffold dropped for a direct `if … then … else`.
    Definitionally equal to the frozen block, so the frozen proof still closes."""
    return (
        f"def implementation_{name} (autoCreated : Bool)\n"
        "    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)\n"
        "    (userPerms : List String) (superResult : Bool) : Bool :=\n"
        "  if autoCreated then\n"
        f"    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms {actions}\n"
        "  else superResult"
    )


def _wrapper_ignoreflag(name, actions):
    """WRONG: drops the autoCreated guard, always applying the target check and
    discarding the caller-supplied `superResult` passthrough."""
    return (
        f"def implementation_{name} (autoCreated : Bool)\n"
        "    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)\n"
        "    (userPerms : List String) (superResult : Bool) : Bool := Id.run do\n"
        f"  return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms {actions}"
    )


_ADD = _wrapper("hasAddPermission", '["change"]')
_CHG = _wrapper("hasChangePermission", '["change"]')
_DEL = _wrapper("hasDeletePermission", '["change"]')
_VIEW = _wrapper("hasViewPermission", '["view", "change"]')

# WRONG helper: consult only the FIRST listed action (drops the existential over
# the rest of the action list).
_ANY_FIRST = _ANY.replace("  for a in actions do\n",
                          "  for a in actions.take 1 do\n")
# WRONG helper: ignore the field list entirely and use the SELF labels as the
# target (never resolves the related target model).
_ANY_IGNFIELDS = (
    "def implementation_hasAnyPermsForTargetModel\n"
    "    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)\n"
    "    (userPerms actions : List String) : Bool := Id.run do\n"
    "  for a in actions do\n"
    "    if userPerms.contains (permString selfAppLabel selfModelName a) then\n"
    "      return true\n"
    "  return false"
)

# WRONG helper: keeps the parent-model skip but DROPS the `hasRemote` conjunct of
# the resolution guard, so a field that refers to no related model at all is
# nonetheless treated as the target and its (vacuous) labels are used. Isolates
# the `hasRemote` half of the guard, which no other rival separates: the
# ignore-target rival discards the whole field scan, and the view-rule rivals do
# not touch resolution at all.
_ANY_NOHASREMOTE = _ANY.replace(
    "    if f.hasRemote && f.remoteModelId != parentModelId then\n",
    "    if f.remoteModelId != parentModelId then\n")

assert _BASE.count(_ANY) == 1, "helper anchor drifted"
assert _ANY_NOHASREMOTE != _ANY, "hasRemote conjunct anchor drifted"
for _blk in (_ADD, _CHG, _DEL, _VIEW):
    assert _BASE.count(_blk) == 1, "wrapper anchor drifted"

# ---------------------------------------------------------------------------
# ADMISSIBILITY. Inserted ahead of the frozen `intro` of correct_hasAddPermission,
# so every frozen proof step after it is byte-identical and the case is a pure
# ADDITION of proof obligations: two `have`s that discharge the spec predicate BY
# EVALUATION at concrete F2P-shaped inputs (an auto-created link model whose field
# list resolves a related target, once for an actor holding only the view action —
# the discriminating point — and once for an actor holding the change action).
# ---------------------------------------------------------------------------

_ADD_INTRO = ("  intro autoCreated selfAppLabel selfModelName parentModelId "
              "fields userPerms superResult\n  constructor\n")
assert _BASE.count(_ADD_INTRO) == 1, "add-proof intro anchor drifted"


def _admiss_have(name, perms):
    """`have`: the spec predicate holds, by evaluation, at one ground input."""
    field = ('[{ hasRemote := true, remoteModelId := "tgt", '
             'remoteAppLabel := "app",\n'
             '         remoteModelName := "target" }]')
    args = f'true "app" "link" "parent"\n      {field} [{perms}] false'
    return (
        f"  have {name} : problem_spec_hasAddPermission {args}\n"
        f"      (implementation_hasAddPermission {args}) := by\n"
        "    unfold problem_spec_hasAddPermission implementation_hasAddPermission\n"
        "    decide\n")


_ADMISS_MODULE = _swap(
    _BASE, _ADD_INTRO,
    _ADD_INTRO.replace("\n  constructor\n", "\n")
    + _admiss_have("_viewOnlyActor", '"app.view_target"')
    + _admiss_have("_changeHeldActor", '"app.change_target"')
    + "  constructor\n")


# ---------------------------------------------------------------------------
# REPROVING positive controls. The three `_wrapper_func` positives below are
# DEFINITIONALLY equal to the frozen blocks (the `Id.run do`/early-return
# scaffold elaborates to the same term as the direct `if … then … else`), which
# is why the frozen proof region carries them unchanged. That makes them cheap
# but WEAK: a positive whose impl is definitionally the frozen one exercises no
# proof obligation the frozen file did not already discharge, and neither the
# helper nor the view decision had a positive at all. The two cases below close
# that: each is a correct impl whose shape is NOT definitionally the frozen one
# (the frozen tactic script does not close it — confirmed: the frozen proof body
# fails on both with `Tactic 'rfl' failed` / unsolved `pure x = x` goals), so
# each must be REPROVEN against the same byte-identical obligation statement.
# ---------------------------------------------------------------------------

# A point-free correct helper: target resolution as `List.find?` and the action
# scan as `List.any` — i.e. the same values the two frozen for-loops compute,
# but with no `Id.run` monadic scaffold at all. Because this shape lands exactly
# on the spec's own `resolveTarget`/`List.any` form, every obligation closes by
# `rfl` once the flag is substituted, so the whole proof region is rewritten to
# that (no aux lemma survives — all the frozen loop-bridging lemmas are about a
# loop this impl does not contain).
_ANY_POINTFREE = (
    "def implementation_hasAnyPermsForTargetModel\n"
    "    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)\n"
    "    (userPerms actions : List String) : Bool :=\n"
    "  let t := match fields.find? (fun f => f.hasRemote && f.remoteModelId != parentModelId) with\n"
    "    | some f => (f.remoteAppLabel, f.remoteModelName)\n"
    "    | none => (selfAppLabel, selfModelName)\n"
    "  actions.any (fun a => userPerms.contains (permString t.1 t.2 a))"
)

# The frozen obligation STATEMENTS, lifted verbatim out of the frozen proof
# region (everything up to the proof-introducing `:=`). Reusing the frozen text
# rather than retyping it is what keeps `variant_scope`'s statement-identity
# check honest: a reproving positive may change the tactic body freely but the
# statement must stay byte-identical, and copying it cannot drift.
def _frozen_stmt(name):
    i = _BASE.index("theorem " + name)
    j = _BASE.index(":=", i)
    return _BASE[i:j].rstrip()


_PROOF_START = _BASE.index("-- proof-start")
_PROOF_END = _BASE.index("-- proof-end") + len("-- proof-end")
_FROZEN_PROOF = _BASE[_PROOF_START:_PROOF_END]

_OBLIGATIONS = ("correct_hasAnyPermsForTargetModel", "correct_hasAddPermission",
                "correct_hasChangePermission", "correct_hasDeletePermission",
                "correct_hasViewPermission")

# Proof region for the point-free helper: the helper is now syntactically the
# spec's own form, so each obligation is closed by `rfl` (after `subst`ing the
# autoCreated flag in the four wrappers).
_PROOF_POINTFREE = "-- proof-start\n" + (
    _frozen_stmt("correct_hasAnyPermsForTargetModel") + " := by\n"
    "  intro selfAppLabel selfModelName parentModelId fields userPerms actions\n"
    "  rfl\n\n"
) + "".join(
    _frozen_stmt(n) + " := by\n"
    "  intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult\n"
    "  refine ⟨?_, ?_⟩ <;> intro h <;> subst h <;> rfl\n\n"
    for n in _OBLIGATIONS[1:]
) + "-- proof-end"

_ANY_POINTFREE_MODULE = _swap(
    _BASE[:_PROOF_START] + _PROOF_POINTFREE + _BASE[_PROOF_END:],
    _ANY, _ANY_POINTFREE)

# A correct VIEW wrapper spelled as an explicit disjunction of two single-action
# helper calls instead of one two-action call. Observationally identical (the
# action-list existential distributes over the concatenation), but NOT
# definitionally so: `anyPerms(["view"]) || anyPerms(["change"])` and
# `anyPerms(["view","change"])` are different terms, so this genuinely reproves
# the view obligation from `anyPerms_impl_eq_spec` plus `List.any` on a two-
# element list.
_VIEW_DISJ = (
    "def implementation_hasViewPermission (autoCreated : Bool)\n"
    "    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)\n"
    "    (userPerms : List String) (superResult : Bool) : Bool :=\n"
    "  if autoCreated then\n"
    "    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms [\"view\"]\n"
    "      || implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms [\"change\"]\n"
    "  else superResult"
)

# Keep the frozen aux machinery up to the three view-shape-specific lemmas
# (`view_wrapper_reduce` / `view_true_branch` / `view_false_branch` are all
# statements about the frozen `Id.run` view block, so they no longer elaborate),
# re-carry the four untouched obligations verbatim, then reprove the view one.
def _frozen_obligation_block(name):
    i = _FROZEN_PROOF.index("theorem " + name)
    m = _re.search(r"\n(?=(?:theorem|def|-- proof))", _FROZEN_PROOF[i + 8:])
    return (_FROZEN_PROOF[i:i + 8 + m.start()] if m
            else _FROZEN_PROOF[i:]).rstrip() + "\n\n"


_PROOF_VIEW_DISJ = (
    _FROZEN_PROOF[:_FROZEN_PROOF.index("theorem view_wrapper_reduce")]
    + "".join(_frozen_obligation_block(n) for n in _OBLIGATIONS[:4])
    + _frozen_stmt("correct_hasViewPermission") + " := by\n"
    "  intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult\n"
    "  refine ⟨?_, ?_⟩\n"
    "  · intro h\n"
    "    subst h\n"
    "    show (implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms [\"view\"]\n"
    "        || implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms [\"change\"])\n"
    "      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms [\"view\", \"change\"]\n"
    "    rw [anyPerms_impl_eq_spec, anyPerms_impl_eq_spec]\n"
    "    simp [anyPermForTarget]\n"
    "  · intro h\n"
    "    subst h\n"
    "    rfl\n\n-- proof-end")

_VIEW_DISJ_MODULE = _swap(
    _BASE[:_PROOF_START] + _PROOF_VIEW_DISJ + _BASE[_PROOF_END:],
    _VIEW, _VIEW_DISJ)


# ---------------------------------------------------------------------------
# Witness scaffold. The carrier is fully transparent (String / List / Bool all
# derive DecidableEq), so each witness states the spec predicate at CONCRETE
# ground literals and closes by `decide` after unfolding. Checked in a file whose
# frozen obligations are elided by the gate, so no tactic script can mask the
# verdict. Against gold the same `decide` faces `<held> = <held>` and fails.
# No witness binds a hypothesis (every input is a literal), so the consistency
# probe is a no-op — there are no assumptions that could be inconsistent.
# ---------------------------------------------------------------------------

def _field(mid, app, model):
    return ("{ hasRemote := true, remoteModelId := %r, remoteAppLabel := %r, "
            "remoteModelName := %r }" % (mid, app, model)).replace("'", '"')


def _wit_any(args):
    return (
        f"example : ¬ problem_spec_hasAnyPermsForTargetModel {args}\n"
        f"    (implementation_hasAnyPermsForTargetModel {args}) := by\n"
        "  unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel\n"
        "  decide"
    )


def _wit_wrap(name, args):
    return (
        f"example : ¬ problem_spec_{name} {args}\n"
        f"    (implementation_{name} {args}) := by\n"
        f"  unfold problem_spec_{name} implementation_{name}\n"
        "  decide"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — CORRECT impls that MUST verify, else
    # SPEC-TOO-STRONG. Two strengths, both shipped deliberately:
    #
    #   * the three `pos-*-functional` cases below drop the `Id.run do` /
    #     early-return scaffold for a direct `if … then … else`. These are
    #     DEFINITIONALLY equal to the frozen blocks, so the frozen proof region
    #     is carried byte-identically and still closes. Cheap, and honest about
    #     what they test: that the spec is not tied to the do-notation spelling.
    #     They do NOT exercise any obligation the frozen file did not already
    #     discharge — do not read them as evidence the spec admits a genuinely
    #     new proof.
    #   * `pos-any-pointfree` and `pos-view-disjunction` are the load-bearing
    #     ones: correct impls that are NOT definitionally the frozen impl, so the
    #     frozen tactic body FAILS on them and each must reprove the same
    #     byte-identical obligation statement from a new shape. They also cover
    #     the helper and the view decision, which had no positive control at all.
    #
    # In every case the frozen `theorem correct_<name>` STATEMENT stays
    # byte-identical (variant_scope enforces this); only the tactic body may
    # differ. No assumption token, no new axiom, no new theorem.
    # =====================================================================
    {
        "id": "pos-add-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _ADD, _wrapper_func("hasAddPermission", '["change"]')),
        "rationale": "correct reshape of the add decision: the mutable-do/early-return "
                     "scaffold is replaced by a direct `if autoCreated then … else "
                     "superResult`, computing the same value on every input. It must "
                     "satisfy both clauses of problem_spec_hasAddPermission — else "
                     "SPEC-TOO-STRONG. Proof: the frozen tactic body still closes "
                     "(the branches are definitionally the frozen ones).",
    },
    {
        "id": "pos-change-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _CHG, _wrapper_func("hasChangePermission", '["change"]')),
        "rationale": "correct reshape of the change decision into a direct "
                     "conditional; observationally identical to the frozen impl, so "
                     "it satisfies problem_spec_hasChangePermission and the carried "
                     "proof still closes. If a faithful correct impl could NOT verify "
                     "=> SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-delete-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _DEL, _wrapper_func("hasDeletePermission", '["change"]')),
        "rationale": "correct reshape of the delete decision into a direct "
                     "conditional; observationally identical to the frozen impl, so "
                     "it satisfies problem_spec_hasDeletePermission and the carried "
                     "proof still closes. If a faithful correct impl could NOT verify "
                     "=> SPEC-TOO-STRONG.",
    },
    # ---- REPROVING positives: correct impls that are NOT definitionally the
    # frozen one, so the frozen tactic body does NOT close them and each has to
    # discharge the byte-identical obligation from a genuinely new shape. These
    # are the load-bearing SPEC-TOO-STRONG controls; the three above are cheap
    # definitional reshapes that the frozen proof carries unchanged. They also
    # give the HELPER and the VIEW decision their first positive control.
    {
        "id": "pos-any-pointfree",
        "kind": "soundness",
        "expect": "verify",
        "module": _ANY_POINTFREE_MODULE,
        "rationale": "correct reshape of the target-permission HELPER with the monadic "
                     "scaffold removed entirely: target resolution becomes "
                     "`fields.find? (fun f => f.hasRemote && f.remoteModelId != "
                     "parentModelId)` and the action scan becomes `actions.any`. Same "
                     "value on every input, so it must satisfy "
                     "problem_spec_hasAnyPermsForTargetModel AND — since all four "
                     "wrappers delegate to it — all four wrapper obligations, else "
                     "SPEC-TOO-STRONG. NOT definitionally the frozen impl: the frozen "
                     "proof body fails on it (the loop-bridging aux lemmas are stated "
                     "about `Id.run` for-loops this impl does not contain), so the "
                     "proof region is rewritten and every obligation reproven. This is "
                     "the only positive control on the helper obligation.",
    },
    {
        "id": "pos-view-disjunction",
        "kind": "soundness",
        "expect": "verify",
        "module": _VIEW_DISJ_MODULE,
        "rationale": "correct reshape of the VIEW decision: instead of one helper call "
                     "on [\"view\", \"change\"], an explicit `||` of two single-action "
                     "helper calls. Observationally identical (the action-list "
                     "existential distributes over the two-element list) but NOT "
                     "definitionally so — the frozen `rfl`-based view proof fails on it "
                     "(`Tactic 'rfl' failed: … is not definitionally equal …`), so the "
                     "view obligation is reproven from anyPerms_impl_eq_spec plus "
                     "`List.any` on a two-element list while the statement stays "
                     "byte-identical. If the spec rejected this faithful shape => "
                     "SPEC-TOO-STRONG. This is the only positive control on the view "
                     "obligation, whose ['view','change'] disjunction the fix leaves "
                     "unchanged.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at an F2P-shaped input.
    # =====================================================================
    {
        "id": "admiss-obligation-at-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_MODULE,
        "rationale": "the frozen obligation carries no precondition hypothesis, so "
                     "PRECOND-TOO-STRONG cannot arrive as a contradictory Requires; "
                     "on this total carrier its analogue is the obligation being "
                     "UNSATISFIABLE at exactly an F2P-shaped input. This case "
                     "discharges problem_spec_hasAddPermission BY EVALUATION "
                     "(`decide`, no appeal to any frozen lemma) at two concrete "
                     "F2P-shaped inputs — an auto-created link model whose field "
                     "list resolves a related target, once for an actor holding "
                     "ONLY the view action (the discriminating point, where the "
                     "spec demands False) and once for an actor holding the change "
                     "action (where it demands True) — as `have`s inserted ahead of "
                     "the frozen `intro`, after which the frozen obligation is "
                     "closed byte-identically. If the auto-created arm's clauses "
                     "over-constrained the result, no value would satisfy them at "
                     "those points and this would fail => the total-carrier form of "
                     "PRECOND-TOO-STRONG. Measured NON-VACUOUS: the same `have` "
                     "shape with the claim NEGATED fails to elaborate (`decide` "
                     "refutes the negation), and the same shape asserting the "
                     "result literal `true` at the view-only point also fails, so "
                     "these `have`s are decided by evaluation of the concrete input "
                     "rather than closed by any tactic that would close anything. "
                     "Statement byte-identical; no new declaration, no assumption "
                     "token. Ports nagini's admiss-distinct-codes, whose "
                     "precondition-admission self-call has this as its counterpart "
                     "on a carrier with no precondition to admit.",
    },

    # =====================================================================
    # HELPER rivals (uniqueness) — attack hasAnyPermsForTargetModel's two pinned
    # behaviours: the existential over the WHOLE action list, and the target
    # RESOLUTION over `fields`. Two witnesses at distinct input points that
    # jointly vary selfAppLabel / selfModelName / parentModelId / fields /
    # userPerms / actions.
    # =====================================================================
    {
        "id": "uniq-any-first-action-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ANY, _ANY_FIRST),
        "refinement": "consulting only the FIRST listed action is correct only when "
                      "the first action decides. The view decision passes "
                      "[\"view\",\"change\"]; an actor holding only the change action "
                      "(the second) is correctly view-permitted (change subsumes "
                      "view), but this rival reports the view action's absence. A "
                      "faithful patch checking only the first requested permission "
                      "would deny a change-permitted actor the view — breaking the "
                      "documented 'change implies view' and the PASS_TO_PASS "
                      "change-permission assertions. Does NOT resolve.",
        "rationale": "REJECT from result = anyPermForTarget (the existential over the "
                     "WHOLE action list): with actions [\"view\",\"change\"] and only "
                     "the change action held, the whole-list existential is true but "
                     "the first-only rival returns false. Attacks the action-list "
                     "existential clause.",
        "witness": _wit_any(
            '"a" "m" "p" ([] : List LinkField) ["a.change_m"] ["view", "change"]'),
    },
    {
        "id": "uniq-any-ignore-target-resolution",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ANY, _ANY_IGNFIELDS),
        "refinement": "ignoring the field list and using the self labels as the "
                      "target never resolves the related target model; the permission "
                      "is then looked up on the WRONG model. A faithful patch that "
                      "skipped target resolution would test the intermediary's own "
                      "(nonexistent) permissions instead of the related model's, so a "
                      "user correctly granted the change permission on the target "
                      "would be denied — it does NOT resolve.",
        "rationale": "REJECT from result = anyPermForTarget with the target resolved "
                     "over `fields`: with a field pointing at a related model other "
                     "than the parent, the spec resolves the target to that model, "
                     "but the rival looks up the permission on the self labels. "
                     "Attacks the target-resolution binders (fields / parentModelId / "
                     "selfAppLabel / selfModelName).",
        "witness": _wit_any(
            '"s" "n" "q" [%s] ["t.change_tm"] ["change"]' % _field("r", "t", "tm")),
    },
    {
        "id": "uniq-any-drop-hasremote-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ANY, _ANY_NOHASREMOTE),
        "refinement": "the resolution guard is a CONJUNCTION — the field must refer "
                      "to a related model at all, AND that model must not be the "
                      "parent. This rival keeps the second conjunct and drops the "
                      "first, so a field that refers to no related model is "
                      "nonetheless accepted as the target and its vacuous labels are "
                      "used for the lookup. A faithful patch that tested only "
                      "'not the parent' would resolve the target to a non-relational "
                      "field on any link model that has one, looking the permission "
                      "up under labels that name no model, so a user correctly "
                      "granted the change permission on the real target would be "
                      "denied. Does NOT resolve.",
        "rationale": "REJECT from result = anyPermForTarget with the target resolved "
                     "over `fields`: with a single field whose hasRemote is FALSE, "
                     "the spec finds no qualifying field and falls back to the self "
                     "labels (finding the held permission), while the rival accepts "
                     "that field and looks the permission up under its labels. "
                     "Isolates the `hasRemote` conjunct of the guard, which the "
                     "ignore-target rival does not separate (it discards the whole "
                     "scan) — so the two halves of the conjunction are each "
                     "measured rather than only their combination.",
        "witness": _wit_any(
            '"a" "m" "p" [{ hasRemote := false, remoteModelId := "z", '
            'remoteAppLabel := "zz", remoteModelName := "zm" }] '
            '["a.change_m"] ["change"]'),
    },

    # =====================================================================
    # EDITING-DECISION rivals (uniqueness) — the pre-change VIEW-RULE regression
    # on add/change/delete, plus an ignore-flag rival per decision that attacks
    # the superResult passthrough. Each pair probes two distinct input points and
    # varies selfAppLabel / selfModelName / parentModelId / fields / autoCreated /
    # userPerms / superResult, so no binder is pinned across the pair.
    # =====================================================================
    {
        "id": "uniq-add-view-rule",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ADD, _wrapper("hasAddPermission", '["view", "change"]')),
        "refinement": "using [\"view\",\"change\"] for the ADD decision IS the "
                      "pre-change regression (the add decision delegated to the view "
                      "rule). An actor holding only the view action then gets add=True, "
                      "but the fix demands add=False. This is exactly the body of "
                      "FAIL_TO_PASS test_inline_add_m2m_view_only_perm (a view-only "
                      "user must NOT be able to add), so the faithful real patch does "
                      "NOT resolve.",
        "rationale": "REJECT from the autoCreated arm of problem_spec_hasAddPermission "
                     "(result = anyPermForTarget … [\"change\"]): on a view-only user "
                     "the view-rule impl returns True while the spec demands False.",
        "witness": _wit_wrap(
            "hasAddPermission",
            'true "a" "m" "p" ([] : List LinkField) ["a.view_m"] false'),
    },
    {
        "id": "uniq-add-ignore-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ADD, _wrapper_ignoreflag("hasAddPermission", '["change"]')),
        "refinement": "always applying the target-model check and discarding "
                      "`superResult` is what a patch that moved the check OUTSIDE the "
                      "auto-created guard would do. For a NON-auto-created inline the "
                      "correct decision is the caller-supplied `superResult`; "
                      "substituting the target check changes the decision for every "
                      "ordinary inline, breaking the PASS_TO_PASS permission-delegation "
                      "tests. Does NOT resolve.",
        "rationale": "REJECT from the non-auto-created arm (¬autoCreated → result = "
                     "superResult): with autoCreated=false and superResult=false, the "
                     "spec demands False, but the rival returns the target-model check "
                     "(True here). Attacks the superResult passthrough clause and the "
                     "autoCreated binder.",
        "witness": _wit_wrap(
            "hasAddPermission",
            'false "b" "n" "q" [%s] [] true' % _field("r", "c", "k")),
    },
    {
        "id": "uniq-change-view-rule",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CHG, _wrapper("hasChangePermission", '["view", "change"]')),
        "refinement": "using [\"view\",\"change\"] for the CHANGE decision IS the "
                      "pre-change regression. A view-only actor would be allowed to "
                      "change the auto-created intermediary — the precise behaviour "
                      "FAIL_TO_PASS test_inline_change_m2m_view_only_perm forbids "
                      "(change must be False for a view-only user). Does NOT resolve.",
        "rationale": "REJECT from the autoCreated arm of "
                     "problem_spec_hasChangePermission: on a view-only user the "
                     "view-rule impl returns True while the spec demands False.",
        "witness": _wit_wrap(
            "hasChangePermission",
            'true "a" "m" "p" ([] : List LinkField) ["a.view_m"] false'),
    },
    {
        "id": "uniq-change-ignore-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CHG, _wrapper_ignoreflag("hasChangePermission", '["change"]')),
        "refinement": "discarding `superResult` and always applying the target check "
                      "changes the decision for every NON-auto-created inline, whose "
                      "correct answer is the caller-supplied `superResult`. Breaks the "
                      "PASS_TO_PASS change-permission-delegation tests. Does NOT "
                      "resolve.",
        "rationale": "REJECT from the non-auto-created arm (¬autoCreated → result = "
                     "superResult): with autoCreated=false and superResult=false the "
                     "spec demands False; the rival returns the target check. Attacks "
                     "the superResult passthrough and the autoCreated binder.",
        "witness": _wit_wrap(
            "hasChangePermission",
            'false "b" "n" "q" [%s] [] true' % _field("r", "c", "k")),
    },
    {
        "id": "uniq-delete-view-rule",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _DEL, _wrapper("hasDeletePermission", '["view", "change"]')),
        "refinement": "using [\"view\",\"change\"] for the DELETE decision IS the "
                      "pre-change regression: a view-only actor would be allowed to "
                      "delete auto-created intermediary rows — the editability the "
                      "issue and the view-only tests forbid (delete must be False for "
                      "a view-only user). Does NOT resolve.",
        "rationale": "REJECT from the autoCreated arm of "
                     "problem_spec_hasDeletePermission: on a view-only user the "
                     "view-rule impl returns True while the spec demands False.",
        "witness": _wit_wrap(
            "hasDeletePermission",
            'true "a" "m" "p" ([] : List LinkField) ["a.view_m"] false'),
    },
    {
        "id": "uniq-delete-ignore-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _DEL, _wrapper_ignoreflag("hasDeletePermission", '["change"]')),
        "refinement": "discarding `superResult` and always applying the target check "
                      "changes the decision for every NON-auto-created inline, whose "
                      "correct answer is the caller-supplied `superResult`. Breaks the "
                      "PASS_TO_PASS delete-permission-delegation tests. Does NOT "
                      "resolve.",
        "rationale": "REJECT from the non-auto-created arm (¬autoCreated → result = "
                     "superResult): with autoCreated=false and superResult=false the "
                     "spec demands False; the rival returns the target check. Attacks "
                     "the superResult passthrough and the autoCreated binder.",
        "witness": _wit_wrap(
            "hasDeletePermission",
            'false "b" "n" "q" [%s] [] true' % _field("r", "c", "k")),
    },

    # =====================================================================
    # VIEW-DECISION rivals (uniqueness) — the view decision keeps the
    # ["view","change"] disjunction (a pure refactor). One rival drops the change
    # disjunct; one ignores the autoCreated flag (superResult passthrough).
    # =====================================================================
    {
        "id": "uniq-view-drop-change",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _VIEW, _wrapper("hasViewPermission", '["view"]')),
        "refinement": "dropping the change disjunct from the VIEW decision denies the "
                      "view to a change-permitted-but-not-view actor. Since the change "
                      "permission is documented to subsume view, a real patch narrowing "
                      "view to the view action alone would deny the inline to a "
                      "change-only actor — a behaviour every change-permission "
                      "PASS_TO_PASS test forbids. Does NOT resolve.",
        "rationale": "REJECT from the autoCreated arm of "
                     "problem_spec_hasViewPermission (result = anyPermForTarget … "
                     "[\"view\",\"change\"]): an actor holding only the change action "
                     "is view-permitted by the spec's disjunction but the "
                     "change-dropping rival returns False.",
        "witness": _wit_wrap(
            "hasViewPermission",
            'true "a" "m" "p" ([] : List LinkField) ["a.change_m"] false'),
    },
    {
        "id": "uniq-view-ignore-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _VIEW, _wrapper_ignoreflag("hasViewPermission", '["view", "change"]')),
        "refinement": "discarding `superResult` and always applying the target check "
                      "changes the VIEW decision for every NON-auto-created inline, "
                      "whose correct answer is the caller-supplied `superResult`. "
                      "Breaks the PASS_TO_PASS view-permission-delegation tests. Does "
                      "NOT resolve.",
        "rationale": "REJECT from the non-auto-created arm of "
                     "problem_spec_hasViewPermission (¬autoCreated → result = "
                     "superResult): with autoCreated=false and superResult=false the "
                     "spec demands False; the rival returns the target check (True "
                     "here). Attacks the superResult passthrough and the autoCreated "
                     "binder.",
        "witness": _wit_wrap(
            "hasViewPermission",
            'false "b" "n" "q" [%s] [] true' % _field("r", "c", "k")),
    },
]


# Nagini → lean accounting:
#   nagini case                     -> here
#   -----------------------------------------------------------------------
#   pos-control-flag-accumulator    -> pos-any-pointfree                  RE-EXPRESSED
#     (nagini's whole-list accumulator reproves the existential from a shape the
#     gold proof does not carry; the faithful lean counterpart is the point-free
#     find?/any helper, which likewise forces a reproof. The three
#     pos-*-functional cases are the CHEAP end of the same lane — definitionally
#     equal to the frozen blocks, so the frozen proof carries them unchanged.)
#   pos-control-create-inline-...   -> pos-add/change/delete-functional   RE-EXPRESSED
#   admiss-distinct-codes           -> admiss-obligation-at-f2p-input     RE-EXPRESSED
#     (nagini asserts its own Requires facts before delegating; with no
#     precondition to admit here, the counterpart is discharging the obligation by
#     EVALUATION at concrete F2P-shaped inputs before closing the frozen
#     obligation verbatim. An earlier revision recorded this lane as N/A on the
#     grounds that the obligation has no precondition — that is not a sufficient
#     reason and the lane is now carried.)
#   frame-mut-write-perm            -> (none)                             VACUOUS (no heap)
#   uniq-first-required-only        -> uniq-any-first-action-only         PORTED
#   uniq-create-view-rule           -> uniq-add-view-rule                 PORTED
#   uniq-modify-view-rule           -> uniq-change-view-rule              PORTED
#   uniq-remove-view-rule           -> uniq-delete-view-rule              PORTED
#   AXIOM_TESTS (empty)             -> (none)                             DROPPED (G-AX)
#
# ADDED beyond the nagini set (surface this backend models but nagini elided):
#   * uniq-any-ignore-target-resolution — nagini abstracts the target away into
#     the single `held` set; this backend models the field-scan resolution, so a
#     rival that skips it is attackable here and nagini could not express it.
#   * uniq-{add,change,delete,view}-ignore-flag — nagini has no autoCreated /
#     super-delegation split (its five decisions are unconditional over `held`);
#     this backend pins the ¬autoCreated → superResult passthrough, so a rival
#     ignoring the flag is a genuine clause attack with no nagini counterpart.
#   * uniq-view-drop-change — attacks the view disjunction (unchanged by the fix,
#     but a load-bearing clause of the frozen spec).
#   * pos-view-disjunction — a correct VIEW reshape (|| of two single-action
#     helper calls). Nagini's view decision is `(ins in held) or (mod in held)`
#     already spelled as a disjunction, so there was no reshape to make there.
#
#   * uniq-any-drop-hasremote-guard — isolates the `hasRemote` conjunct of the
#     resolution guard. Nagini elides target resolution entirely, and no other
#     rival here separates the conjunction's two halves.
#
# SPEC-TOO-WEAK probes run during the audit and NOT shipped (each was rejected
# by the frozen spec, with a witness that held of the rival and failed
# semantically on gold — every one re-derived with real builds, rival exit 0 /
# gold exit 1 — so none is a spec hole):
# permission-string composed as "<app>.<model>_<action>" instead of
# "<app>.<action>_<model>"; target resolution taking the LAST matching field
# (break dropped) rather than the first; target resolution dropping the
# parent-model skip guard (first field with any related model wins);
# resolution taking the first field UNCONDITIONALLY (both guard conjuncts
# dropped); add/delete looking up their OWN action codename instead of change;
# the autoCreated branches swapped (flag POLARITY, on add and on delete); the
# view decision narrowed to ["change"] alone; and the helper demanding ALL listed
# actions instead of any. The action-set, resolution-order, parent-skip,
# hasRemote, composition-order, flag-polarity and any/all clauses are therefore
# each measured, not just argued.
#
# SPEC-TOO-STRONG probes run during the audit and not shipped (each VERIFIES, so
# the spec admits it and there is no soundness hole): the helper with the action
# scan as `List.foldl (· || ·)` and resolution as `(fields.filter …).head?`
# (reproven from a foldl/any bridge and a filter-head?/find? bridge); the view
# wrapper as a `match` on the flag; and the add wrapper with the guard NEGATED
# (`if !autoCreated then superResult else …`).
#
# The 11 reject witnesses probe distinct input points; across them autoCreated
# takes {true,false} and superResult {false,true} — the view-rule / drop-change /
# first-only / ignore-target rivals hold superResult at false on the auto-created
# arm (where the passthrough is dead), while each ignore-flag rival holds it at
# TRUE on the non-auto-created arm with no matching permission, so the spec demands
# the true passthrough and the rival returns the (false) target check. selfAppLabel
# {"a","s","b"}, selfModelName {"m","n"},
# parentModelId {"p","q"}, fields {[], [remote→…]}, userPerms across view/change on
# several targets, and actions {["change"],["view"],["view","change"]}. Each
# obligation is attacked at ≥2 distinct points, and every load-bearing clause
# (target resolution, the action-list existential, the ["change"]/["view","change"]
# action sets, and the superResult passthrough) is attacked by some rival.
AXIOM_TESTS = []
