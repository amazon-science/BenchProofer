"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-23314 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with every obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE — a PROCEDURE, not a function. ``Axes3D.draw(self, renderer)``
returns ``None``; everything it does, it does by drawing onto the renderer it is
handed. So the modeled object is the ACTION it carries out:

  render (self : Drawable) : m Unit

  quantified over an ARBITRARY lawful monad ``m`` and an ARBITRARY action
  ``renderContents : m Unit`` standing for the whole pre-existing body of
  ``draw``. A ``Drawable`` is abstracted to the single field the behavior depends
  on: a boolean ``visible`` flag.

  Load-bearing postcondition clauses (all in ``problem_spec_render``):
    (C-hidden)  self.visible = false → result = pure () — a hidden component's
                action is doing NOTHING: not "undone afterwards", not "written to
                a surface that is then discarded", but never carried out.
    (C-shown)   self.visible = true  → result = renderContents — a shown
                component carries out its contents-rendering, exactly once.

  The BEHAVIOURAL DISCRIMINATOR: a component flagged not-shown must contribute
  nothing. The pre-existing behavior ran the whole rendering body regardless of
  the flag, so a hidden component still drew. (C-hidden) senses exactly that: an
  implementation that sequences ``renderContents`` on the hidden path owes
  ``renderContents >>= f = pure ()`` for an ARBITRARY action, which is false, and
  the abstract ``m`` hands it no other operation — no read-back of what has been
  drawn, no undo — with which to erase it. That is the modeling reason the
  carrier is an abstract monad rather than a list-shaped output surface: on a
  concrete surface an implementation can carry out the rendering and then rebuild
  the entry surface from it (``.take 0``, ``.drop length``, snapshot-and-restore
  through ``get``/``set``), which no renderer permits and which would satisfy an
  output-VALUE postcondition while drawing.

  WHY ``[LawfulMonad m]`` IS IN THE OBLIGATION. Without it the clauses would pin
  the SYNTAX of a program rather than the drawing it performs: a correct
  implementation that sequences the one action differently
  (``renderContents >>= pure``, ``pure () >>= fun _ => renderContents``) would be
  rejected. With it those are provably the same action and verify — carried below
  as ``pos-shown-discarded-result`` and ``pos-lawful-resequence``, which is how
  this battery keeps the obligation behavioral. The same laws are what let
  (C-hidden) see THROUGH a discard: ``renderContents >>= fun _ => pure ()`` is
  provably ``renderContents``, so "carry out the body and throw the result away"
  is not a way to satisfy "the action is ``pure ()``".

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and now vacuous for a second reason.
    Lean is referentially transparent: the inputs carry no heap permission, so
    there is no read-only half-permission to overwrite and no aliasing to
    exploit. Nagini's rival is VALUE-NEUTRAL (`self.content = self.content`) and
    is rejected purely on permission accounting; there is no such accounting
    here. What remains of the class, stated as measured rather than as an
    expressibility claim — because the rebind IS writable on this carrier and both
    halves were built:

      - the VALUE-NEUTRAL rebind (``let self : Drawable := { visible :=
        self.visible }`` before the guard, nagini's own ``self.content =
        self.content`` transposed) VERIFIES once the case reproves, and it should:
        it is definitionally the frozen component, so it is observably identical
        to gold and a reject case over it would be VACUOUS — rejected by a tactic
        mismatch and nothing else. Not carried, for that reason.
      - the CONSTANT-flag rebind (``{ visible := true }``) is expressible and is
        rejected, with the frozen tactic leaving ``renderContents = pure ()`` on
        the hidden branch — but that is the same action, at the same clause, at the
        same point as ``overshoot-render-while-hidden``, which is carried below.
        It is a respelling of that rival rather than a new one.

    So the class contributes nothing this battery does not already have, and
    nothing is fabricated in its place. What is NOT claimed is that it could not
    be written.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. Both clauses are grounded in the inputs:
    (C-hidden) pins the action to ``pure ()`` and (C-shown) pins it to
    ``renderContents``, the action the behavior was handed — not an opaque answer
    key an implementation could echo without branching correctly. In its place
    the battery carries honest cheapest-implementation POSITIVE CONTROLS
    (``pos-*``).

  * DIVERGENCE / NON-TERMINATION — SHIPPABLE-BUT-UNWITNESSABLE, recorded as a
    KNOWN HOLE rather than as a vacuous class. This bundle sets no
    ``loom.semantics.termination`` option: the carrier is plain Lean 4 + Mathlib,
    where a ``def`` must be shown terminating and the only way to write a
    diverging impl is ``partial def``. That variant IS in scope mechanically (it
    introduces no axiom, no ``sorry``, no new theorem, and keeps the
    ``correct_render`` statement byte-identical) and it IS rejected — but the
    rejection is a CARRIER artifact, not a spec verdict: a ``partial def`` is
    irreducible, so the frozen tactic fails at
    ``Tactic `unfold` failed to unfold `implementation_render``` before any clause
    is consulted, and no witness can close the gap either (the rival's own body
    never reduces, so a witness cannot derive the equation it needs to refute).
    That last half is MEASURED, not argued: three witness shapes were built
    against a ``partial def`` self-recursing rival and all three failed on the
    RIVAL side, which is the half a shippable case must pass. ``simp
    [implementation_render]`` leaves the hypothesis as
    ``implementation_render renderContents { visible := false } = pure ()``, so
    the refutation cannot be applied to it; ``rw [implementation_render]`` reports
    ``Expected an equality or iff proof or definition name``; and
    ``implementation_render.eq_def`` is not generated for a ``partial def``
    (``Unknown constant``). So there is nothing shippable here, and per the
    divergence-lane rule the honest disposition is that the SPEC does not
    constrain termination — a hole — not that the class is empty.

  * PARTIAL-DOMAIN / VALUE — APPLIES. This is the whole battery: rivals correct
    on part of the visibility domain but diverging elsewhere. Never carrying the
    body out violates (C-shown); carrying it out regardless of the flag violates
    (C-hidden); carrying it out twice when shown violates (C-shown) at a distinct
    point; and the three ERASURE rivals — carry the body out and then take the
    hidden branch, carry it out inside the hidden branch and drop its result, or
    carry it out inside the hidden branch and sequence its result away with ``*>``
    — violate (C-hidden) at the point that motivates this carrier, since on an
    output-VALUE model of this same behavior they were the shapes that verified
    while still drawing. The third is not a respelling of the second: the frozen
    tactic leaves ``renderContents *> pure () = pure ()`` rather than
    ``renderContents = pure ()``, so the operator survives the reduction and its
    witness has to cross it with ``seqRight_eq``. It is carried as the
    representative of the whole post-hoc erasure family (``<$>``-erasure, ``<*``,
    ``discard``, explicit ``bind ... (fun _ => pure ())``, ``*>``), each member of
    which was built and rejected with the goal left as its OWN equation against
    ``pure ()`` — so what is demonstrated is that the spec refuses the CLASS, not
    one syntactic member of it.

SPEC STRENGTH IS CATEGORICAL. ``problem_spec_render`` pins the action to a closed
term of the inputs on BOTH branches, so it determines the behavior UNIQUELY: any
two implementations satisfying it are equal at every input. Checked as a theorem
against the frozen file —

    (hf : ∀ s, problem_spec_render rc s (f s))
    (hg : ∀ s, problem_spec_render rc s (g s)) : ∀ s, f s = g s

elaborates by case-splitting the flag and rewriting with the clause each branch
supplies (measured against the frozen file, exit 0). Consequence: SPEC-TOO-WEAK
is unreachable BY PROOF for any wrong impl of the modeled type — a wrong impl
that verified would have to be equal to the gold impl, i.e. not wrong. The scope
of that guarantee is stated precisely, because it is not unconditional:

  - it quantifies over impls of the modeled type ``m Unit`` that satisfy the
    predicate at every input, so it says nothing about termination (see the
    divergence class above);
  - and it is a statement about ACTIONS, so it is only as strong as the claim
    that a Lean action ``m Unit`` faithfully denotes "what ``draw`` does to the
    renderer". That claim is the reason the monad is abstract, and the one place
    it leaks is recorded rather than hidden: an implementation may BIND the
    action as a value and never sequence it (``let _ := renderContents``), which
    verifies. It is not a break — the Python counterpart of naming an action
    without performing it is naming the bound method without calling it, which
    draws nothing and is exactly what the hidden case requires — but it is the
    residual, and it is stated here so the next reader does not have to
    rediscover it. Re-measured independently: ``let _ := renderContents`` inside
    the HIDDEN branch verifies (exit 0), so the residual is real and sits exactly
    where it is documented; and its sequencing counterpart ``let _ ←
    renderContents`` in the same position is REJECTED and is carried below as
    ``discard-render-on-hidden-branch``, so the boundary between the two is the
    one the prose describes and not a wider one. The reject side of that boundary
    was probed further and holds: binding without sequencing on the SHOWN branch
    (``let _ := renderContents; pure ()``, i.e. never drawing when shown) is
    rejected on (C-shown), which is the direction that would have made the
    residual load-bearing.

WITNESSES. Every reject case's refutation is CONDITIONED, and on the same single
hypothesis class: that the contents-rendering action is not the do-nothing action
(``renderContents ≠ pure ()``, or for one rival the discard form of it). Nothing
weaker can work and nothing stronger is needed — an abstract action has no value
a tactic can compute, and if the body really did nothing then a hidden component
that ran it would be observationally indistinguishable from one that did not, so
the hypothesis is precisely the assumption under which this cell's behavior is
observable at all. It is jointly satisfiable, and that is exhibited rather than
asserted: the admissibility case discharges both clauses at the concrete lawful
instance ``m := StateM (List Nat)`` with ``renderContents := modify (0 :: ·)``,
and proves on the spot all FOUR hypothesis forms the reject lane uses at that
instance — ``≠ pure ()``, the doubled action ``≠`` the single one, the discard
form ``≠ pure ()``, and the ``*>`` form ``≠ pure ()``. The last three are
separate propositions rather than consequences of the first (a state action can be
idempotent, or have a discard form equal to ``pure ()``, without being ``pure ()``
itself; and ``*>`` reaches the discard form only through ``seqRight_eq``), so
exhibiting only the first would have left the multiplicity and the two erasure
hypotheses satisfiable by argument alone; all four are now built. The gate's own
consistency probe is the independent check that no tactic derives ``False`` from
the hypotheses.

Every witness below was built twice: it ELABORATES against its rival and FAILS on
the frozen solution. The gold-side failure is SEMANTICALLY FORCED, and this is
stated as a MEASUREMENT rather than as an argument, because the argument alone is
exactly what the forgery test exists to distrust. Each witness's tactic reduces
the clause it invokes with a full ``simp`` before consuming it, so on gold the
hypothesis ``hb`` reduces to ``True`` — i.e. ``simp`` PROVED the equation the
witness assumes is violated — and the next step then fails on ``True``. That
reduct is the refutation, and it was confirmed by two controls per case rather
than read off the error text:

  * a REVEAL build (final step replaced by ``exact (hb : Nat)``, which makes Lean
    print ``hb``'s real type) prints ``has type True`` on gold and prints the
    CONCRETE unproved equation (``renderContents = pure ()``,
    ``pure () = renderContents``) on the rival;
  * a same-shape build whose only change is the CLAIM — the hypothesis weakened to
    one gold's own action satisfies — ELABORATES on gold (exit 0), so gold's exit
    code tracks what is claimed and is not a constant artifact of the shape.

An earlier revision of three of these witnesses used ``simp only
[implementation_render]``, which unfolds the impl without reducing the ``if``: on
gold that left ``hb`` as an equation about an unreduced ``if``-term and the
failure was a plain type mismatch — a ``shape``-tier signature, which is the tier
that CANNOT be told from a hollow tactic mismatch without exactly these builds.
The claim was true there and the builds confirm it, but the recorded evidence did
not show it; the witnesses now reduce, so the recorded signature exhibits the
``True`` reduct itself.

AXIOM lane: DROPPED, and there is nothing left for it to have judged: the frozen
file declares no ``axiom`` and no ``opaque`` at all (the contents-rendering action
is a universally quantified PARAMETER, which is why no property of it can be
smuggled in). meta.json records the A-reference deep model and G-AX handles it
separately.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-23314"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL body of the impl region: every impl reshape lands entirely inside it.
_IMPL = (
    "  if !self.visible then\n"
    "    return\n"
    "  renderContents"
)

# The opening two tactic lines of the frozen obligation — the injection point for
# the admissibility ground instances (a `have` prepended before the frozen body).
_PROOF_INTRO = (
    "  intro m _ _ renderContents self\n"
    "  unfold problem_spec_render implementation_render"
)


# === POSITIVE CONTROLS (soundness) — structurally different but CORRECT ======
# implementations that MUST verify. If a faithful correct implementation cannot
# satisfy the frozen obligation, the spec is SPEC-TOO-STRONG. Each keeps the
# `theorem correct_render` statement byte-identical; the frozen tactic body
# (`cases h : self.visible <;> simp`) closes every shape below, so no proof edit
# is needed and no helper/axiom/assumption is introduced.
#
# GRADED BY PROOF CONTENT, and the grading is measured rather than asserted. The
# discriminator used is the `[LawfulMonad m]` hypothesis of `correct_render`: each
# positive was ALSO built with that hypothesis deleted from the obligation (and
# the matching binder dropped from the tactic block's `intro`), which asks whether
# the shape is identified with the frozen action by REDUCTION alone or whether the
# monad laws have to be spent on it. Measured, one build per shape:
#   pos-positive-guard, pos-branchless-cond, pos-local-action — still close
#     without the laws: the two actions reduce to each other, so these certify
#     that the obligation is not over-fitted to the guard's SYNTAX and nothing
#     stronger.
#   pos-shown-discarded-result, pos-lawful-resequence — FAIL without the laws:
#     these are the shapes (C-shown) has to discharge as an obligation, and they
#     are what keeps the spec behavioral rather than syntactic.
# The frozen solution itself also FAILS with `[LawfulMonad m]` deleted, so the
# hypothesis is load-bearing for the shipped proof and not decoration. Each grade
# is recorded in the case's own rationale.

# --- pos-positive-guard: rewrite the negative early-return guard into positive
# form — carry out the rendering ONLY when shown, otherwise fall off the end
# having done nothing. Same action on both clauses.
_IMPL_POS = (
    "  if self.visible then\n"
    "    renderContents"
)
POS_GUARD = _swap(_BASE, _IMPL, _IMPL_POS)

# --- pos-branchless-cond: drop the branching construct entirely and select the
# action with the `cond` combinator. Not a reindentation of the guard: the action
# carried out is chosen by a total function of the flag.
_IMPL_POS2 = "  cond self.visible renderContents (pure ())"
POS_COND = _swap(_BASE, _IMPL, _IMPL_POS2)

# --- pos-local-action: bind the action to be carried out to a local and then
# carry THAT out. A guard-less control flow performing the same action on every
# input; it also pins that the spec constrains what is performed and not where
# the choice of it is written.
_IMPL_POS3 = (
    "  let act := if self.visible then renderContents else pure ()\n"
    "  act"
)
POS_LOCAL = _swap(_BASE, _IMPL, _IMPL_POS3)

# --- pos-shown-discarded-result: on the shown branch, carry out the rendering
# and explicitly discard its (unit) result. `renderContents >>= fun _ => pure ()`
# is the SAME ACTION as `renderContents` — provably, by the monad laws, not by
# reduction — so this MUST verify. It is the positive that pins (C-shown) to
# behavior rather than syntax, and it is the exact counterpart of the
# `discard-render-on-hidden-branch` rival: the same Lean phrase is correct on the
# shown branch and a violation on the hidden one, which is what "the action is
# what matters" means.
_IMPL_POS4 = (
    "  if !self.visible then\n"
    "    return\n"
    "  let _ ← renderContents\n"
    "  pure ()"
)
POS_DISCARD_SHOWN = _swap(_BASE, _IMPL, _IMPL_POS4)

# --- pos-lawful-resequence: sequence a do-nothing action before the real one on
# each branch (`pure () >>= …`). Equal to the frozen action only by the monad
# laws (`pure_bind`), so the clauses must discharge it rather than the kernel.
# Faithful: not one drawing operation is added, removed, or reordered.
_IMPL_POS5 = (
    "  if !self.visible then\n"
    "    pure ()\n"
    "    pure ()\n"
    "  else\n"
    "    pure ()\n"
    "    renderContents"
)
POS_RESEQUENCE = _swap(_BASE, _IMPL, _IMPL_POS5)


# === ADMISSIBILITY ===========================================================
# The frozen `correct_render` theorem carries NO precondition hypothesis (the
# behavior is total), so the nagini precondition-admission probe has no binder to
# attack. The honest analogue on an ABSTRACT carrier is stronger than a ground
# instance would be on a concrete one: discharge the spec predicate at a CONCRETE
# lawful instance of the quantified monad, with a contents-rendering action that
# is provably NOT the do-nothing action. That answers the two ways this spec could
# be unsatisfiable-in-substance rather than in form —
#   (a) the two clauses could be jointly unsatisfiable at any action that
#       actually draws (the analogue of PRECOND-TOO-STRONG: a spec reachable only
#       when the body does nothing would constrain nothing about drawing), and
#   (b) the hypothesis every reject witness conditions on
#       (`renderContents ≠ pure ()`) could be unsatisfiable, which would make the
#       whole reject lane vacuous.
# Both are discharged here, in the proof region, alongside the frozen obligation
# closed verbatim. Nothing is assumed: no new declaration, the `correct_` statement
# is byte-identical, and each instance is a `have` inside the tactic body.
_DRAWS = "(modify (fun l : List Nat => 0 :: l) : StateM (List Nat) Unit)"
_ADMISS_BLOCK = (
    "  -- ADMISSIBILITY at a CONCRETE instance of the quantified monad: state over\n"
    "  -- the log of drawing operations, with the contents-rendering action being\n"
    "  -- one that actually records something. First that this action is NOT the\n"
    "  -- do-nothing action -- the hypothesis the reject lane conditions on, shown\n"
    "  -- satisfiable rather than assumed -- then both clauses discharged at it.\n"
    f"  have _draws : {_DRAWS}\n"
    "      ≠ pure () := by\n"
    "    intro hEq\n"
    f"    have h2 : (({_DRAWS}.run []).2)\n"
    "        = (((pure () : StateM (List Nat) Unit).run []).2) := by rw [hEq]\n"
    "    simp at h2\n"
    "  -- ...and the same for the two DERIVED forms the reject lane conditions on,\n"
    "  -- which are separate propositions rather than consequences of the one above:\n"
    "  -- the DOUBLED action is not the single one (the multiplicity hypothesis), and\n"
    "  -- the DISCARD form is not the do-nothing action (the launder hypothesis).\n"
    "  -- Exhibited at the same instance, so no witness hypothesis in this battery\n"
    "  -- rests on satisfiability that is merely argued.\n"
    f"  have _draws_twice : ({_DRAWS} >>= fun _ => {_DRAWS})\n"
    f"      ≠ {_DRAWS} := by\n"
    "    intro hEq\n"
    f"    have h2 : ((({_DRAWS} >>= fun _ => {_DRAWS}).run []).2)\n"
    f"        = (({_DRAWS}.run []).2) := by rw [hEq]\n"
    "    simp at h2\n"
    "    exact absurd h2 (by decide)\n"
    f"  have _draws_discarded : ({_DRAWS} >>= fun _ => (pure () : StateM (List Nat) Unit))\n"
    "      ≠ pure () := by\n"
    "    intro hEq\n"
    f"    have h2 : ((({_DRAWS} >>= fun _ => (pure () : StateM (List Nat) Unit)).run []).2)\n"
    "        = (((pure () : StateM (List Nat) Unit).run []).2) := by rw [hEq]\n"
    "    simp at h2\n"
    "  -- ...and the SEQRIGHT form, which the erasure-family rival conditions on. A\n"
    "  -- FOURTH separate proposition: `*>` is identified with a discarding bind only\n"
    "  -- by `seqRight_eq`, so it does not follow from the form above without that\n"
    "  -- law, and a rival that assumes it is entitled to an instance of its own.\n"
    f"  have _draws_seqright : ({_DRAWS} *> (pure () : StateM (List Nat) Unit))\n"
    "      ≠ pure () := by\n"
    "    intro hEq\n"
    f"    have h2 : ((({_DRAWS} *> (pure () : StateM (List Nat) Unit)).run []).2)\n"
    "        = (((pure () : StateM (List Nat) Unit).run []).2) := by rw [hEq]\n"
    "    simp at h2\n"
    "  have _ground_shown :\n"
    f"      problem_spec_render {_DRAWS}\n"
    "        { visible := true }\n"
    f"        (implementation_render {_DRAWS}\n"
    "          { visible := true }) := by\n"
    "    unfold problem_spec_render implementation_render\n"
    "    refine ⟨?_, ?_⟩\n"
    "    · intro h; simp at h\n"
    "    · intro _; simp\n"
    "  have _ground_hidden :\n"
    f"      problem_spec_render {_DRAWS}\n"
    "        { visible := false }\n"
    f"        (implementation_render {_DRAWS}\n"
    "          { visible := false }) := by\n"
    "    unfold problem_spec_render implementation_render\n"
    "    refine ⟨?_, ?_⟩\n"
    "    · intro _; simp\n"
    "    · intro h; simp at h\n"
    + _PROOF_INTRO
)
ADMISS = _swap(_BASE, _PROOF_INTRO, _ADMISS_BLOCK)


# === UNIQUENESS / REJECT rivals ==============================================
# Wrong implementations sharing the frozen spec that MUST be rejected. Each
# carries (a) the refinement argument that its faithful real patch would NOT
# resolve the F2P — so a verifying rival would be a true
# verify-does-not-imply-resolve break, not an artifact — and (b) a refutation
# witness pinning the violation, checked to hold of the rival and to FAIL on the
# frozen solution.

# --- overshoot-render-while-hidden (the discriminator; the pre-existing
# behavior): drop the visibility guard and carry out the rendering
# unconditionally.
_IMPL_OVERSHOOT = "  renderContents"
RIVAL_OVERSHOOT = _swap(_BASE, _IMPL, _IMPL_OVERSHOOT)

# --- underdeliver-nothing-while-shown: never carry out the rendering. The mirror
# miss: correct while hidden, wrong while shown.
_IMPL_UNDER = "  pure ()"
RIVAL_UNDER = _swap(_BASE, _IMPL, _IMPL_UNDER)

# --- overdeliver-double-while-shown: when shown, carry out the rendering twice.
# An over-count of the drawing performed.
_IMPL_DOUBLE = (
    "  if !self.visible then\n"
    "    return\n"
    "  renderContents\n"
    "  renderContents"
)
RIVAL_DOUBLE = _swap(_BASE, _IMPL, _IMPL_DOUBLE)

# --- render-before-consulting-the-flag: carry out the contents-rendering FIRST,
# binding its result, and only then consult the visibility flag (and, being past
# the point of no return, render again on the shown path). This is the shape that
# motivates the whole carrier: on an output-VALUE model of this behavior the
# corresponding Lean text VERIFIED — a discarded pure `let` is definitionally the
# gold impl there, so no postcondition on the returned surface could see it — while
# its faithful Python calls the drawing body before the guard can stop it. Under
# the action model the hidden path owes `renderContents >>= fun _ => pure () =
# pure ()`, which the monad laws reduce to `renderContents = pure ()`: false for
# an arbitrary action.
_IMPL_EARLY = (
    "  let _ ← renderContents\n"
    "  if !self.visible then\n"
    "    return\n"
    "  renderContents"
)
RIVAL_EARLY = _swap(_BASE, _IMPL, _IMPL_EARLY)

# --- discard-render-on-hidden-branch: take the hidden branch, but carry out the
# rendering inside it and discard its result before returning. The second shape
# the output-VALUE model could not reject, and the more tempting one: it LOOKS
# like it honours the guard. Distinct from `render-before-consulting-the-flag` in
# where the drawing sits relative to the branch — here the flag IS consulted
# first and the branch taken is the right one — and refuted from a hypothesis
# stated on the discard form itself rather than on the bare action.
_IMPL_DISCARD_HIDDEN = (
    "  if !self.visible then\n"
    "    let _ ← renderContents\n"
    "    return\n"
    "  renderContents"
)
RIVAL_DISCARD_HIDDEN = _swap(_BASE, _IMPL, _IMPL_DISCARD_HIDDEN)

# --- launder-render-on-hidden-branch-via-seqRight: the same violation as
# `discard-render-on-hidden-branch` reached through the APPLICATIVE sequencing
# operator instead of a `do`-block bind. `renderContents *> pure ()` performs the
# rendering and then yields the do-nothing action's result, which is the most
# compact way to write "draw, then pretend you did not" — and the reason it is
# carried separately is that it lands the clause on a DIFFERENT TERM: the frozen
# tactic leaves `renderContents *> pure () = pure ()` rather than
# `renderContents = pure ()`, i.e. the laundering operator survives the reduction
# and has to be refuted through the `LawfulMonad` law that identifies `*>` with a
# discarding bind (`seqRight_eq`), rather than dissolved before the refutation
# starts. That makes it the case for the whole family of erasure spellings an
# implementation can reach for once it has already performed the action
# (`<$>`-erasure, `<*`, `discard`, an explicit `bind ... (fun _ => pure ())`):
# each one is a different surface term over the same performed action, and each is
# rejected at this same clause. Measured, one build per spelling: all rejected,
# with the goal left as that spelling's own equation against `pure ()`.
_IMPL_LAUNDER_SEQRIGHT = (
    "  if !self.visible then\n"
    "    let _ ← (renderContents *> (pure () : m Unit))\n"
    "    return\n"
    "  renderContents"
)
RIVAL_LAUNDER_SEQRIGHT = _swap(_BASE, _IMPL, _IMPL_LAUNDER_SEQRIGHT)


# ---- witnesses (each checked: elaborates vs rival, fails vs frozen) ----------
# Stated against the spec predicate, conditioning on the abstract action.
#
# WHY EVERY WITNESS IS CONDITIONED. `renderContents` is a universally quantified
# parameter of the spec: there is no value for a tactic to compute and no input
# at which the two sides differ by reduction. The refutations therefore state
# their point under the assumption that the contents-rendering is not the
# do-nothing action, which is the assumption under which this cell's behavior is
# observable at all (if the body drew nothing, a hidden component that ran it
# would be indistinguishable from one that did not, and there would be no bug to
# fix and no test to fail). The assumption is exhibited as satisfiable by the
# admissibility case at a concrete monad, and the gate's consistency probe checks
# independently that no tactic derives `False` from it.
#
# WHY NO WITNESS NAMES AN INPUT SHAPE. On the previous output-VALUE carrier the
# witnesses named surfaces (`op :: rest`, `[]`) and had to state `Nonempty` for the
# element type. There is no surface here: the monad is abstract, so the only
# "input" besides the flag is the action itself, and the flag is named at both of
# its values across the cases below. Nothing is lost — the shape-naming existed to
# probe a list-shaped output the spec no longer mentions — and nothing has to be
# assumed about inhabitation.

# hidden component, and the rival carries out the rendering anyway. Spec
# (C-hidden) = the action is `pure ()`.
_WIT_OVERSHOOT = (
    "example {m : Type → Type} [Monad m] [LawfulMonad m] (renderContents : m Unit)\n"
    "    (h : renderContents ≠ pure ()) :\n"
    "    ¬ problem_spec_render renderContents { visible := false }\n"
    "        (implementation_render renderContents { visible := false }) := by\n"
    "  intro hspec\n"
    "  have hb := hspec.1 rfl\n"
    "  simp [implementation_render] at hb\n"
    "  exact h hb\n"
)

# shown component, and the rival does nothing at all. Spec (C-shown) = the action
# is `renderContents`.
_WIT_UNDER = (
    "example {m : Type → Type} [Monad m] [LawfulMonad m] (renderContents : m Unit)\n"
    "    (h : renderContents ≠ pure ()) :\n"
    "    ¬ problem_spec_render renderContents { visible := true }\n"
    "        (implementation_render renderContents { visible := true }) := by\n"
    "  intro hspec\n"
    "  have hb := hspec.2 rfl\n"
    "  simp [implementation_render] at hb\n"
    "  exact h hb.symm\n"
)

# shown component, and the rival carries out the rendering twice. Spec (C-shown)
# = ONE pass. Conditioned on the second pass being observable — the hypothesis
# has to be about the doubled action, since a body that is idempotent as an
# ACTION (drawing the same thing twice with no accumulation) would make this
# rival genuinely equivalent to gold, and the rival must be refuted where it is
# not.
_WIT_DOUBLE = (
    "example {m : Type → Type} [Monad m] [LawfulMonad m] (renderContents : m Unit)\n"
    "    (h : (renderContents >>= fun _ => renderContents) ≠ renderContents) :\n"
    "    ¬ problem_spec_render renderContents { visible := true }\n"
    "        (implementation_render renderContents { visible := true }) := by\n"
    "  intro hspec\n"
    "  have hb := hspec.2 rfl\n"
    "  exact h (by simpa [implementation_render] using hb)\n"
)

# hidden component, and the rival has already carried out the rendering before it
# looks at the flag. Spec (C-hidden) = the action is `pure ()`; the rival's action
# on this branch is the rendering followed by a discard, which the monad laws
# identify with the rendering itself — so the SAME hypothesis that refutes the
# guard-less rival refutes this one, at the same clause but through a step the
# laws have to supply. That step is the whole point of the case: it is what an
# output-value postcondition could not take.
_WIT_EARLY = (
    "example {m : Type → Type} [Monad m] [LawfulMonad m] (renderContents : m Unit)\n"
    "    (h : renderContents ≠ pure ()) :\n"
    "    ¬ problem_spec_render renderContents { visible := false }\n"
    "        (implementation_render renderContents { visible := false }) := by\n"
    "  intro hspec\n"
    "  have hb := hspec.1 rfl\n"
    "  exact h (by simpa [implementation_render] using hb)\n"
)

# hidden component, branch correctly taken, and the rival draws inside it and
# drops the result. Stated on the DISCARD FORM directly (`the rendering followed
# by a discard is not the do-nothing action`), which is the claim this rival
# denies in its own terms and which needs no law to connect to the clause.
_WIT_DISCARD_HIDDEN = (
    "example {m : Type → Type} [Monad m] [LawfulMonad m] (renderContents : m Unit)\n"
    "    (h : (renderContents >>= fun _ => pure ()) ≠ pure ()) :\n"
    "    ¬ problem_spec_render renderContents { visible := false }\n"
    "        (implementation_render renderContents { visible := false }) := by\n"
    "  intro hspec\n"
    "  have hb := hspec.1 rfl\n"
    "  simp [implementation_render] at hb\n"
    "  exact h (by simpa using hb)\n"
)


# hidden component, branch correctly taken, and the rival performs the rendering
# inside it through the applicative sequencing operator. Conditioned on the
# SEQRIGHT form itself (`renderContents *> pure () ≠ pure ()`), which is the claim
# this spelling denies in its own terms — and which is the same proposition as the
# discard rival's hypothesis only via `seqRight_eq`, so the case genuinely rests on
# that law rather than on a restatement of the neighbouring case's assumption.
_WIT_LAUNDER_SEQRIGHT = (
    "example {m : Type → Type} [Monad m] [LawfulMonad m] (renderContents : m Unit)\n"
    "    (h : (renderContents *> (pure () : m Unit)) ≠ pure ()) :\n"
    "    ¬ problem_spec_render renderContents { visible := false }\n"
    "        (implementation_render renderContents { visible := false }) := by\n"
    "  intro hspec\n"
    "  have hb := hspec.1 rfl\n"
    "  simp [implementation_render] at hb\n"
    "  exact h (by simpa [seqRight_eq] using hb)\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness)
    # =====================================================================
    {
        "id": "pos-positive-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_GUARD,
        "rationale": "structurally different but CORRECT: the negative "
        "early-return guard is rewritten in positive form (carry out the "
        "rendering only when `self.visible = true`, otherwise fall off the end "
        "having performed nothing). Same action on both clauses — (C-hidden) the "
        "action is `pure ()` when hidden, (C-shown) it is `renderContents` when "
        "shown — so it MUST verify (else SPEC-TOO-STRONG). The frozen "
        "`cases h : self.visible <;> simp` closes both branches, so no proof edit "
        "is needed; the `correct_render` statement is byte-identical. WEAK BY "
        "CONSTRUCTION and recorded so: measured with `[LawfulMonad m]` deleted "
        "from the obligation, this shape still closes, i.e. the two actions reduce "
        "to each other and the laws were not spent. It certifies that "
        "the spec is not over-fitted to the guard's SYNTAX and nothing stronger; "
        "`pos-shown-discarded-result` and `pos-lawful-resequence` are what carry "
        "real proof content.",
    },
    {
        "id": "pos-branchless-cond",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_COND,
        "rationale": "second correct shape, with the branching construct removed "
        "entirely: the action carried out is selected by the `cond` combinator "
        "(`cond self.visible renderContents (pure ())`) rather than by an `if` or "
        "an early return. Same action on every input, so it MUST verify (else "
        "SPEC-TOO-STRONG). Confirms the spec constrains WHAT IS PERFORMED and does "
        "not require the flag to be consumed by a branch at all. Frozen proof "
        "unchanged, `correct_render` statement byte-identical.",
    },
    {
        "id": "pos-local-action",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_LOCAL,
        "rationale": "third correct shape: bind the action to be carried out to a "
        "local (`let act := if self.visible then renderContents else pure ()`) and "
        "then carry THAT out. A guard-less control flow performing the same action "
        "on every input; must verify (else SPEC-TOO-STRONG). It also pins a "
        "distinction the residual depends on and which this battery therefore has "
        "to get right in both directions: BINDING an action as a value is not "
        "performing it, and this positive is the case where the bound action IS "
        "subsequently performed, on the branch where performing it is correct. "
        "Frozen proof unchanged, `correct_render` statement byte-identical.",
    },
    {
        "id": "pos-shown-discarded-result",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_DISCARD_SHOWN,
        "rationale": "correct positive with REAL PROOF CONTENT, aimed at (C-shown) "
        "as an obligation rather than a definitional identity. The shown branch "
        "carries out the rendering and explicitly discards its unit result; "
        "`renderContents >>= fun _ => pure ()` is the same ACTION as "
        "`renderContents`, but only by the monad laws — measured: with "
        "`[LawfulMonad m]` deleted from the obligation this shape FAILS, unlike the "
        "control-flow reshapes above. So the clauses must actually discharge it, "
        "and the laws are what does it. Faithful: "
        "ignoring the `None` that `draw`'s body returns changes no drawing "
        "performed, so it MUST verify (else SPEC-TOO-STRONG — the spec would be "
        "demanding a particular way of WRITING the call rather than that the "
        "drawing be performed). It is the deliberate mirror of the "
        "`discard-render-on-hidden-branch` rival: the identical Lean phrase is "
        "correct here and a violation there, which is what it means for the "
        "obligation to be about the action and not the syntax. `correct_render` "
        "statement byte-identical, frozen proof unchanged.",
    },
    {
        "id": "pos-lawful-resequence",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_RESEQUENCE,
        "rationale": "second value-level positive, reaching the same point by a "
        "different route: a do-nothing action is sequenced before the real one on "
        "each branch, so each branch's action is equal to the frozen one only by "
        "`pure_bind` — and this shape too was measured to FAIL once "
        "`[LawfulMonad m]` is deleted from the obligation. "
        "Distinguishes 'performs this drawing' from 'is written exactly this way' "
        "— a distinction neither clause may make, since both branches perform the "
        "identical drawing. Must verify (else SPEC-TOO-STRONG). Frozen proof "
        "unchanged, `correct_render` statement byte-identical.",
    },

    # =====================================================================
    # ADMISSIBILITY
    # =====================================================================
    {
        "id": "admiss-concrete-drawing-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "the obligation is discharged at a CONCRETE instance of the "
        "quantified monad — state over a log of drawing operations, "
        "`m := StateM (List Nat)`, with `renderContents := modify (0 :: ·)`, an "
        "action that actually records something — for both values of the flag, and "
        "then the frozen obligation is closed verbatim. This is the analogue of the "
        "nagini precondition-admission probe on a spec with no precondition binder, "
        "and on an abstract carrier it is the stronger question: a spec quantified "
        "over all lawful monads could be satisfiable only where the body does "
        "nothing, which would make (C-hidden) trivially true and the cell empty. "
        "The instance is chosen so that cannot be the reading — the first `have` "
        "PROVES `modify (0 :: ·) ≠ pure ()`, so both clauses are discharged at an "
        "action that is observably not the do-nothing action. That same fact is "
        "what the reject lane conditions on, so this case doubles as the "
        "satisfiability exhibit for every witness hypothesis in the battery: if it "
        "could not be discharged, every rejection below would be resting on an "
        "assumption with no instance. ALL FOUR hypothesis forms the reject lane "
        "uses are exhibited here, not just the base one: `modify (0 :: ·) ≠ "
        "pure ()`, the DOUBLED action `≠` the single one (which "
        "`overdeliver-double-render-while-shown` conditions on), the DISCARD "
        "form `≠ pure ()` (which `discard-render-on-hidden-branch` conditions on), "
        "and the SEQRIGHT form `≠ pure ()` (which "
        "`launder-render-on-hidden-branch-via-seqRight` conditions on). "
        "The last three are independent propositions rather than consequences of the "
        "first — a state action can be idempotent, or can have a discard form equal "
        "to `pure ()`, without being `pure ()` itself, and `*>` reaches the discard "
        "form only through `seqRight_eq` — so exhibiting only the "
        "first would have left those three rivals' hypotheses satisfiable by argument "
        "alone. Nothing is assumed: no new declaration, the "
        "`correct_render` statement is byte-identical, and the ground instances "
        "live inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / REJECT rivals
    # =====================================================================
    {
        "id": "overshoot-render-while-hidden",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_OVERSHOOT,
        "refinement": "this IS the pre-existing behavior: the rendering body runs "
        "regardless of the visibility flag, so a component flagged not-shown still "
        "draws. The F2P compares a hidden 3D axes against an empty reference "
        "image; drawing makes the output non-empty and the comparison FAILS — the "
        "faithful (guard-less) patch does NOT resolve. This is exactly the failure "
        "the reported behavior consists of.",
        "rationale": "REJECT from (C-hidden): when `self.visible = false` the "
        "action must be `pure ()`, and this rival's action is `renderContents`. "
        "partial-domain — agrees with gold on the whole shown sub-domain, diverges "
        "on every hidden input. Attacks the `self.visible` binder at the value "
        "`false`.",
        "witness": _WIT_OVERSHOOT,
    },
    {
        "id": "underdeliver-nothing-while-shown",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_UNDER,
        "refinement": "a faithful patch that returned without drawing even when "
        "the component IS shown (an over-broad guard, or the condition inverted) "
        "would draw NOTHING for a normal shown component — every 3D rendering test "
        "would come back blank, so the patch would NOT resolve.",
        "rationale": "REJECT from (C-shown): when `self.visible = true` the action "
        "must be `renderContents`, and this rival's action is `pure ()`. "
        "partial-domain — agrees with gold on the whole hidden sub-domain, diverges "
        "on every shown input. Attacks the `self.visible` binder at the value "
        "`true`.",
        "witness": _WIT_UNDER,
    },
    {
        "id": "overdeliver-double-render-while-shown",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_DOUBLE,
        "refinement": "a faithful patch that ran the rendering body twice on a "
        "shown component would over-draw — every artist emitted twice — failing the "
        "image comparison against the single-pass reference; it would NOT resolve. "
        "Not an isolated shape either: over-drawing when shown is also half of what "
        "`render-before-consulting-the-flag` does, so this case isolates that half "
        "and refutes it on its own. Stated without a resolve count, because no "
        "oracle run of this rival's refined patch is on file for the current "
        "carrier; the argument is the image-comparison semantics of the P2P suite, "
        "and what is machine-checked is the spec's rejection, via the witness.",
        "rationale": "REJECT from (C-shown): the action must be ONE "
        "`renderContents`, and this rival's is "
        "`renderContents >>= fun _ => renderContents`. A near-miss of the "
        "underdeliver rival that agrees with gold wherever a second pass is "
        "unobservable, so it is refuted at its OWN distinguishing point — via a "
        "hypothesis about the doubled action rather than the bare one. Attacks the "
        "`self.visible` binder at `true` and the multiplicity of the action, which "
        "no other rival varies.",
        "witness": _WIT_DOUBLE,
    },
    {
        "id": "render-before-consulting-the-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_EARLY,
        "refinement": "the faithful patch runs the drawing body BEFORE the guard "
        "can stop it, so it draws on BOTH branches: a hidden component draws at all "
        "(the F2P renders against an empty reference, which then fails) and a shown "
        "component draws twice (the image comparisons run against single-pass "
        "references, which a doubled emission does not match). So the patch does NOT "
        "resolve, and it is the shape whose rejection is load-bearing here: it is "
        "the one that reads the flag too late to matter rather than not at all. "
        "PROVENANCE, stated at the strength the bundle record actually supports — no "
        "oracle run of THIS rival's own refined patch is on file for the current "
        "carrier, so no resolve counts are cited for it. What IS on file is the "
        "reason this rival exists: the bundle record documents that an earlier "
        "OUTPUT-VALUE revision of this spec admitted the corresponding text (bind "
        "the emitter on the hidden path, then rebuild the entry surface from it) as "
        "VERIFYING, and that a faithful refinement of one such shape was measured "
        "non-resolving — which is what motivated the change to the action carrier. "
        "Under this carrier that whole family is rejected instead, which is what "
        "this case pins. The claim here is therefore about what the SPEC does to "
        "the shape, which is machine-checked by the witness below, and not a "
        "harness measurement of this variant.",
        "rationale": "REJECT from (C-hidden): the rival's action when hidden is "
        "the rendering followed by a discard, and the monad laws identify that with "
        "the rendering itself, so the clause demands `renderContents = pure ()`. "
        "This case exists because an output-VALUE model of the same behavior could "
        "NOT reject it — a discarded pure `let` is definitionally the gold impl "
        "there, so the postcondition on the returned surface saw nothing wrong "
        "while the Python it refines to draws before the flag is read. What makes "
        "the action model refuse it is that there is nothing to discard INTO: the "
        "monad is abstract, so an action once sequenced is in the action, and the "
        "laws propagate it to the clause. Attacks the ORDER of the flag read "
        "relative to the drawing — a position no other rival varies. Note what the "
        "carrier change does to that old text: it SPLITS it. `let _ := "
        "renderContents` (bind the action, never sequence it) and `let _ ← "
        "renderContents` (sequence it) were the same program when the model was a "
        "function of an output surface, and they are two different programs here — "
        "the first draws nothing and verifies, the second draws and is this rival. "
        "The shape the bundle record documents as verifying-but-non-resolving on "
        "the superseded output-value carrier refines the second, which is why the "
        "split is a repair and not a relabeling — and on THIS carrier the second is "
        "rejected, which is the machine-checked half of that claim.",
        "witness": _WIT_EARLY,
    },
    {
        "id": "discard-render-on-hidden-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_DISCARD_HIDDEN,
        "refinement": "a faithful patch that took the hidden branch but drew "
        "inside it before returning — reading the flag, entering the not-shown "
        "case, and still calling the body — leaves a hidden component drawn, so the "
        "F2P image comparison against an empty reference FAILS and the patch does "
        "NOT resolve. Worse than the guard-less rival in one respect: it reads the "
        "flag and branches correctly, so a review that checks 'is the guard there' "
        "passes it.",
        "rationale": "REJECT from (C-hidden): the action on the taken branch is "
        "`renderContents >>= fun _ => pure ()`, which is not `pure ()`. The second "
        "shape an output-VALUE model of this behavior could not reject, and the "
        "distinct one: `render-before-consulting-the-flag` never lets the guard "
        "decide anything, while this rival lets it decide and then ignores what it "
        "decided. Refuted from a hypothesis stated on the DISCARD FORM itself, "
        "which is the claim the rival denies in its own terms — that carrying out "
        "the drawing and throwing away its result is still carrying it out.",
        "witness": _WIT_DISCARD_HIDDEN,
    },
    {
        "id": "launder-render-on-hidden-branch-via-seqRight",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_LAUNDER_SEQRIGHT,
        "refinement": "a faithful patch that entered the not-shown case and still "
        "invoked the body there, written so the body's result is sequenced away "
        "rather than named, leaves a hidden component drawn: the F2P image "
        "comparison against an empty reference FAILS and the patch does NOT resolve. "
        "It is the most compact way to write the mistake — the erasure of the "
        "result reads like the erasure of the drawing, and it is not — so it is the "
        "spelling most likely to survive review.",
        "rationale": "REJECT from (C-hidden): the action on the taken branch is "
        "`renderContents *> pure ()`, which is not `pure ()`. Carried in addition "
        "to `discard-render-on-hidden-branch` because it lands the clause on a "
        "DIFFERENT TERM rather than restating that case: the frozen tactic leaves "
        "`renderContents *> pure () = pure ()`, so the applicative operator "
        "survives the reduction and the refutation has to cross it via `seqRight_eq` "
        "instead of finding a bind already dissolved. Measured, and this is why the "
        "case is here rather than assumed to be a duplicate: the whole family of "
        "post-hoc erasure spellings an implementation can reach for after it has "
        "already performed the action — `<$>`-erasure, `<*`, `discard`, an explicit "
        "`bind ... (fun _ => pure ())`, and this `*>` — was built one spelling per "
        "build, and every one is rejected with the goal left as its OWN equation "
        "against `pure ()`. So the spec refuses the class, not one syntactic member "
        "of it, and this case is the class's representative in the battery. Attacks "
        "the `self.visible` binder at `false`, at the point where the drawing has "
        "already happened and only its result is being hidden.",
        "witness": _WIT_LAUNDER_SEQRIGHT,
    },
]
