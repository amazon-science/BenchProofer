# properties.py — G-PBT falsification battery for sympy__sympy-14531 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — never the spec, never a proof-obligation statement — is edited),
# checked by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival and
# FAILS on the frozen solution, so the rejection is attributable to the spec and not
# to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   printRelational (render : Settings → Expr → String) (settings _default : Settings)
#                   (relName : String) (lhs rhs : Expr) : String
#   printLimit      (render : Settings → Expr → String) (settings _default : Settings)
#                   (dirIsDefault : Bool) (e z z0 dir : Expr) : String
#   A container-style renderer splices nested subexpression fragments into a constant
#   textual template. `Settings`, `Expr` are ABSTRACT type variables and `render` is a
#   universally-quantified subexpression renderer, so the modeled behaviour is purely
#   WHICH formatting profile is handed to `render` for the nested positions, plus the
#   frame (template text, operand order, branch selection). Two postconditions:
#
#     (R) result = relName ++ "(" ++ render settings lhs ++ ", " ++ render settings rhs ++ ")"
#     (L) result = if dirIsDefault
#                   then "Limit(" ++ render settings e ++ ", " ++ ... ++ render settings z0 ++ ")"
#                   else "Limit(" ++ ... ++ render settings z0 ++ ", dir='" ++ render settings dir ++ "')"
#
#   Independent obligations pinned by these clauses:
#     (C1) PROFILE PROPAGATION — every nested position is rendered at the ACTIVE
#          profile `settings`, NOT at the fixed `_defaultSettings` a bare textual
#          conversion would use. This is the load-bearing clause (the modeled bug:
#          the pre-patch renderer handed `_defaultSettings` to the nested calls, so
#          any non-default display option was lost in the operand positions).
#     (C2) OPERAND FRAME / ORDER — the operator tag and literal punctuation are
#          constant and the nested positions appear in a fixed order (lhs before rhs;
#          e, z, z0[, dir]); no output component is left free.
#     (C3) BRANCH SELECTION — for the limit, `dirIsDefault` selects between the
#          two textual shapes (the `dir='…'` suffix is present iff the direction is
#          non-default).
#
#   Because `render`, `Settings`, `Expr` are all universally quantified, a witness may
#   instantiate them at CONCRETE first-order data (`Bool` for both type variables and a
#   two-valued `render`) and `decide` the disequality directly — there is no opaque
#   carrier to condition on here. A `render` that reads its FIRST argument
#   (`fun s _ => if s then … else …`) exposes clause C1 (active vs default profile); a
#   `render` that reads its SECOND argument (`fun _ x => if x then … else …`) exposes
#   clauses C2/C3 (operand identity / branch shape).
#
# CARRIER NARROWING vs nagini. The nagini sibling modeled the SAME fix over a
# byte-sequence carrier: it spelled out `render_rational(wrap,p,q)` (the `S(…)`
# wrapper toggled by the boolean `wrap`) and attacked the two halves of the `wrap`
# domain (drop-wrap / always-wrap) at the leaf plus two compound sites, with a
# supporting num/denom transposition. This backend abstracts the whole rendering
# profile into an opaque `Settings` type and the whole subexpression printer into a
# universally-quantified `render`, so the observable is no longer a concrete `S(…)`
# byte pattern but simply "which profile reaches `render`". Consequently:
#   * nagini's drop-wrap AND always-wrap collapse into a SINGLE modeled fault here —
#     "the nested call is handed the wrong profile" — because `Settings` is abstract
#     and the two profiles are just two distinct values `settings` / `_defaultSettings`
#     with no wrap-true/wrap-false polarity to mirror. That single fault IS the
#     pre-patch bug and is attacked at BOTH modeled sites (rel-prepatch, lim-prepatch).
#   * nagini's num/denom transposition ports to an operand transposition, which the
#     abstract carrier still sees sharply (rel-swap-operands, lim-swap-z-z0).
#   * The limit's `dirIsDefault` branch is a structural clause nagini's single-shape
#     `limit_text` did not carry; it is ADDITIONALLY attacked here (lim-ignore-dir).
# So the port is NARROWER where the two wrap-halves fuse and BROADER on the branch
# structure the Lean carrier exposes.
#
# LANES THAT DO NOT PORT:
#   * GROUNDED-ORACLE positive control (nagini `pos-control-equation-cheapest`). The
#     nagini spec pinned the result to a @Pure `eq_text(...)` grounded in the args, so
#     the cheapest correct impl just materialised it. Here the spec RHS is itself the
#     grounded template `relName ++ "(" ++ render settings … ++ ")"`; the analogue of
#     the cheapest-impl control is `pos-relational-pure` below (a direct pure `def`
#     whose body is definitionally the spec RHS). There is no separate opaque oracle
#     to echo, so no distinct WRONG-echo lane exists — as in nagini.
#   * ADMISSIBILITY (nagini `admiss-f2p-shape`, which discharged a half-permission
#     Requires via a self-call). The lean obligations are `∀ …, problem_spec … (impl …)`
#     with NO precondition hypothesis, so nothing could be PRECOND-TOO-STRONG in the
#     literal sense. The load-bearing RESIDUE of the sibling's case is non-vacuity —
#     it asserted, inside the routine, that the assembled text is non-degenerate at a
#     normal in-domain input — and that DOES port: `admiss-ground-instance` below
#     discharges BOTH obligations at a concrete task-shaped instantiation as a `have`
#     inside the existing tactic body, before the frozen proof closes them verbatim.
#     (An earlier revision of this manifest wrote the lane off as N/A; that was an
#     under-port, since a spec satisfiable only vacuously would pass a battery of
#     positives that never evaluate it at a literal input.)
#   * FRAME-MUTATION (nagini's #1 class). Every input is a `bool`/`String`/abstract
#     `Expr`, all passed by value; Lean is referentially transparent (no aliasing, no
#     fractional permission), so a "store into a read-only input" rival is not
#     expressible. The frame obligation instead lives in clause C2 (the template text
#     and operand order are pinned) and is attacked structurally by the swap rivals.
#   * DIVERGENCE / NON-TERMINATION. On lean `implementation_*` is a total Lean `def`;
#     a non-terminating implementation cannot be written at all, so the class is
#     genuinely VACUOUS here (the lean disposition, NOT the velvet-partial
#     known-spec-hole one). The nagini sibling carries no divergence case either.
#   * AXIOM_TESTS (nagini's ax-render-sound / ax-domain-containment). The axiom lane is
#     G-AX's job; this gate ignores them. `render` is a universally-quantified
#     parameter (an A-reference, per mapping.md), NOT an axiomatized callee, so there
#     is no constraining axiom for this spec lane to test anyway.
#
# NAGINI -> LEAN CASE ACCOUNTING (8 spec cases + 2 axiom cases in the sibling).
#   pos-control-operand-reshape   -> RE-EXPRESSED as pos-relational-pure and
#                                    pos-limit-letbind (two reshapes, one per obligation:
#                                    a pure `def` and a let-bound branch body), PLUS
#                                    pos-relational-reassoc and pos-limit-factored-tail.
#                                    (AUDIT ADDITION. The first two are definitionally the
#                                    frozen impl — the frozen `rfl`/`cases … <;> rfl` closes
#                                    them unchanged — so they exercise Lean's defeq rather
#                                    than the spec's tolerance for a different shape. The
#                                    added pair re-associates the concatenation and factors
#                                    the branch into the tail; the frozen tactic FAILS on
#                                    both, so each genuinely re-discharges the obligation
#                                    over a restructured term.)
#   pos-control-equation-cheapest -> FUSED into pos-relational-pure (see
#                                    GROUNDED-ORACLE above: the spec RHS is already the
#                                    grounded template, so "cheapest impl" and "reshaped
#                                    impl" are the same artifact here).
#   admiss-f2p-shape              -> RE-EXPRESSED as admiss-ground-instance (residue:
#                                    non-vacuity, not precondition admissibility).
#   partial-domain-drop-wrap      -> RE-EXPRESSED as rel-prepatch-default-profile and
#                                    lim-prepatch-default-profile.
#   partial-domain-always-wrap    -> RE-EXPRESSED as rel-extra-wrapper-template.
#                                    (AUDIT CORRECTION. An earlier revision of this
#                                    manifest recorded the mirror half as INEXPRESSIBLE
#                                    here, on the argument that "a rival cannot reach
#                                    inside `render` to over-apply a wrapper; there is no
#                                    wrapper". That argument is wrong, and was retracted
#                                    against real builds. The sibling's wrapper was never
#                                    INSIDE its leaf renderer either — it was TEMPLATE
#                                    text spliced around the rendered operand — and
#                                    template text is exactly what clause C2 pins on this
#                                    carrier. So the mirror ports directly: a rival that
#                                    renders both operands at the correct active profile
#                                    and then splices a CONSTANT decoration around one of
#                                    them commits the sibling's over-application fault,
#                                    is observably distinct from the frozen impl, and is
#                                    refuted by C2 rather than by C1. It is a genuinely
#                                    new probe point: every other rival either mis-routes
#                                    a profile or permutes/replaces existing template
#                                    text, and none ADDS any.)
#   compound-bug-equation         -> RE-EXPRESSED as rel-one-operand-default (a partial
#                                    propagation, i.e. the sibling's compound site
#                                    narrowed to ONE slot) and rel-constant-tag.
#   compound-bug-limit            -> RE-EXPRESSED as lim-one-shape-default and
#                                    lim-direction-component-default.
#   value-swap-num-denom          -> RE-EXPRESSED as rel-swap-operands and lim-swap-z-z0.
#   ax-render-sound /
#   ax-domain-containment         -> DROPPED (G-AX's lane; see above).
#   ADDED with no sibling: lim-ignore-dir — the `dirIsDefault` branch clause is
#                                    structure this carrier exposes and the sibling's
#                                    single-shape limit text did not have.
#
# POINT SPREAD (what each reject witness varies, so no binder is held fixed across the
# whole battery — a binder every witness pins at one value is a binder no rival was
# built to abuse):
#   printRelational: `settings` active=true (rel-prepatch, rel-one-operand) and
#     false (rel-swap, rel-constant-tag); `relName` four distinct values
#     ("Eq"/"Ne"/"Lt"/"Ge"); `lhs`/`rhs` both orderings of the distinct pair and the
#     equal pair; `render` both a profile-sensitive and an expr-sensitive instantiation.
#   printLimit: `dirIsDefault` true (lim-prepatch, lim-swap-z-z0) and false
#     (lim-ignore-dir, lim-one-shape, lim-direction-component); `settings` both values;
#     `e`/`z`/`z0` equal and distinct, in both orders; `dir` distinguished from the other
#     components in lim-direction-component (the only witness that varies it alone);
#     `render` both instantiations.
#   Both `render` and both abstract type binders are instantiated at Bool throughout;
#   they are the carrier the witnesses are stated over, so they are exercised by every
#   case rather than varied.
from pathlib import Path

INSTANCE = "sympy__sympy-14531"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# Each anchor lies ENTIRELY inside one impl region of Solution.lean and is unique.

# The relational impl's `Id.run do` tail (inside printRelational's impl region).
_REL_BODY = (
    " : String := Id.run do\n"
    '  return relName ++ "(" ++ render settings lhs ++ ", " ++ render settings rhs ++ ")"'
)
assert _BASE.count(_REL_BODY) == 1, "rel impl anchor drifted"

# The whole limit impl body (inside printLimit's impl region).
_LIM_BODY = (
    "  if dirIsDefault then\n"
    '    return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "\n'
    '      ++ render settings z0 ++ ")"\n'
    "  else\n"
    '    return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "\n'
    '      ++ render settings z0 ++ ", dir=\'" ++ render settings dir ++ "\')"'
)
assert _BASE.count(_LIM_BODY) == 1, "lim impl anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-relational-pure: a structurally different CORRECT impl of the relational
# renderer written as a pure `def` (no `Id.run do`, no early return) whose body is
# byte-for-byte the spec RHS. Semantics identical on every input. The theorem
# STATEMENT is byte-identical and the FROZEN proof body (`unfold …; rfl`) still closes
# — `Id.run` of a pure `return v` reduces to `v`, so the pure form is definitionally
# the same value. No reproof, no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG
# (the postcondition is over-fit to the monadic `Id.run do` impl shape).
_POS_REL_PURE = _swap(
    _BASE,
    _REL_BODY,
    " : String :=\n"
    '  relName ++ "(" ++ render settings lhs ++ ", " ++ render settings rhs ++ ")"',
)

# pos-limit-letbind: a structurally different CORRECT impl of the limit renderer that
# binds each nested render to a typed local BEFORE the branch and splices the locals
# into the two templates, instead of re-spelling `render settings …` inside each
# branch. Output equals the frozen impl's on every input (the direction position `dir`
# is still rendered inline in the non-default branch). The theorem STATEMENT is
# byte-identical and the FROZEN proof body (`cases dirIsDefault <;> rfl`) still closes.
# No reproof, no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG.
_POS_LIM_LETBIND = _swap(
    _BASE,
    _LIM_BODY,
    "  let re := render settings e\n"
    "  let rz := render settings z\n"
    "  let rz0 := render settings z0\n"
    "  if dirIsDefault then\n"
    '    return "Limit(" ++ re ++ ", " ++ rz ++ ", " ++ rz0 ++ ")"\n'
    "  else\n"
    '    return "Limit(" ++ re ++ ", " ++ rz ++ ", " ++ rz0 ++ ", dir=\'"'
    ' ++ render settings dir ++ "\')"',
)


# AUDIT ADDITION. The two positives above are honest but WEAK, and the audit measured why:
# each passes with the frozen tactic body byte-for-byte UNCHANGED, because `Id.run (pure v)`
# and a `let`-bound nested render are both DEFINITIONALLY the frozen impl — `rfl` closes
# them for the same reason it closes gold. A positive the frozen `rfl` still closes cannot
# distinguish a spec that is over-fit to the frozen impl's shape from one that is not; it
# certifies only that Lean's defeq is reflexive. The two positives below are reshapes whose
# proofs the frozen tactic does NOT close (measured: `Tactic 'rfl' failed` on both when the
# proof region is left frozen), so they demand the postcondition be discharged over a
# genuinely different term structure and reproven within the admitted variant scope
# (tactic body only — statement byte-identical, no new axiom/lemma/sorry).

# pos-relational-reassoc: CORRECT relational impl that re-associates the concatenation —
# `((tag ++ "(") ++ lhs') ++ ((", " ++ rhs') ++ ")")` instead of the frozen right-nested
# chain. `String.append` is associative but NOT definitionally so at this shape, so the
# frozen `rfl` fails and the proof must appeal to associativity. Same string on every
# input. If it FAILS => SPEC-TOO-STRONG (the postcondition is over-fit to one particular
# parenthesisation of the template concatenation).
_POS_REL_REASSOC = _swap(
    _swap(
        _BASE,
        _REL_BODY,
        " : String := Id.run do\n"
        '  return ((relName ++ "(") ++ render settings lhs)'
        ' ++ ((", " ++ render settings rhs) ++ ")")',
    ),
    "  unfold problem_spec_printRelational implementation_printRelational\n  rfl",
    "  unfold problem_spec_printRelational implementation_printRelational\n"
    "  simp [String.append_assoc]",
)

# pos-limit-factored-tail: CORRECT limit impl that emits the shared prefix ONCE and
# branches only over the tail (`")"` vs the direction fragment), rather than spelling a
# whole template per branch. The branch is pushed inside the concatenation, so the frozen
# `cases dirIsDefault <;> rfl` no longer matches the term and the proof must reassociate.
# Output equals the frozen impl's on every input. If it FAILS => SPEC-TOO-STRONG (the
# postcondition is over-fit to a per-branch whole-template spelling).
_POS_LIM_FACTORED = _swap(
    _swap(
        _BASE,
        _LIM_BODY,
        '  return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "\n'
        "    ++ render settings z0\n"
        '    ++ (if dirIsDefault then ")" else ", dir=\'" ++ render settings dir ++ "\')")',
    ),
    "  unfold problem_spec_printLimit implementation_printLimit\n"
    "  cases dirIsDefault <;> rfl",
    "  unfold problem_spec_printLimit implementation_printLimit\n"
    "  cases dirIsDefault <;> simp [String.append_assoc]",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits only the impl region; the frozen proof body is left in place
# (it will not close for the reshaped impl, but the gate reads the WITNESS — checked in
# a file with the obligation removed — not the rival's own build).
# ===========================================================================

# rel-prepatch: THE MODELED BUG. The nested operands are rendered at the fixed
# `_defaultSettings` profile instead of the active `settings`, so any non-default
# display option is lost in both operand positions. Correct only where the active and
# default profiles agree; wrong wherever they differ. Attacks clause C1 at the
# relational site.
_RIV_REL_PREPATCH = _swap(
    _BASE,
    _REL_BODY,
    " : String := Id.run do\n"
    '  return relName ++ "(" ++ render _defaultSettings lhs ++ ", "'
    ' ++ render _defaultSettings rhs ++ ")"',
)

# rel-swap-operands: renders both operands at the correct active profile but EMITS
# THEM IN THE WRONG ORDER (rhs before lhs). Element-wise it uses the right profile, but
# violates the operand-order sub-clause of C2. Ports nagini's num/denom transposition.
_RIV_REL_SWAP = _swap(
    _BASE,
    _REL_BODY,
    " : String := Id.run do\n"
    '  return relName ++ "(" ++ render settings rhs ++ ", " ++ render settings lhs ++ ")"',
)

# lim-prepatch: the SAME propagation bug at the OTHER modeled site — every nested
# component of the limit is rendered at `_defaultSettings` in both branches. Attacks
# clause C1 at the limit site; confirms the symmetric routine is equally tight.
_RIV_LIM_PREPATCH = _swap(
    _BASE,
    _LIM_BODY,
    "  if dirIsDefault then\n"
    '    return "Limit(" ++ render _defaultSettings e ++ ", " ++ render _defaultSettings z ++ ", "\n'
    '      ++ render _defaultSettings z0 ++ ")"\n'
    "  else\n"
    '    return "Limit(" ++ render _defaultSettings e ++ ", " ++ render _defaultSettings z ++ ", "\n'
    '      ++ render _defaultSettings z0 ++ ", dir=\'" ++ render _defaultSettings dir ++ "\')"',
)

# lim-ignore-dir: renders every component at the correct active profile but ALWAYS
# emits the default (no-`dir='…'`) shape, dropping the direction suffix when the
# approach direction is non-default. Correct on the dirIsDefault=true half; wrong on
# the other half. Attacks clause C3 (branch selection) — a structural clause with no
# nagini counterpart.
_RIV_LIM_IGDIR = _swap(
    _BASE,
    _LIM_BODY,
    '  return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "\n'
    '    ++ render settings z0 ++ ")"',
)

# lim-swap-z-z0: renders every component at the correct active profile and selects the
# correct branch, but EMITS z and z0 in the wrong order. Violates the component-order
# sub-clause of C2 at the limit site. Distinct probe point from lim-prepatch/igdir.
_RIV_LIM_SWAPZ = _swap(
    _BASE,
    _LIM_BODY,
    "  if dirIsDefault then\n"
    '    return "Limit(" ++ render settings e ++ ", " ++ render settings z0 ++ ", "\n'
    '      ++ render settings z ++ ")"\n'
    "  else\n"
    '    return "Limit(" ++ render settings e ++ ", " ++ render settings z0 ++ ", "\n'
    '      ++ render settings z ++ ", dir=\'" ++ render settings dir ++ "\')"',
)


# --- NEAR-MISS rivals: a SINGLE mis-propagated position ----------------------------
# The two prepatch rivals above flip EVERY nested position at once. That leaves the
# spec's per-position and per-shape content untested: a routine that propagated the
# active profile everywhere EXCEPT one place would satisfy every clause these rivals
# violate, so the battery would never notice it. Each of the three rivals below leaves
# strictly more of the domain correct than its wholesale counterpart, so each carries
# its own witness at the input that distinguishes IT — never a shared one, or its
# rationale would claim a sub-domain the manifest never demonstrates.

# rel-one-operand-default: only the FIRST operand position leaks the fixed profile;
# the second is correct. Agrees with the frozen behaviour on every input whose first
# operand renders the same under both profiles — a strictly larger sub-domain than
# rel-prepatch. Attacks clause C1 at ONE position.
_RIV_REL_ONE_OPERAND = _swap(
    _BASE,
    _REL_BODY,
    " : String := Id.run do\n"
    '  return relName ++ "(" ++ render _defaultSettings lhs ++ ", "'
    ' ++ render settings rhs ++ ")"',
)

# rel-constant-tag: renders both operands at the correct active profile but HARDCODES
# the operator tag instead of taking it from the input `relName`. Correct only for the
# one operator it happens to name. Attacks the tag sub-clause of C2 — the only input
# the two profile rivals leave entirely unexercised.
_RIV_REL_CONST_TAG = _swap(
    _BASE,
    _REL_BODY,
    " : String := Id.run do\n"
    '  return "Eq(" ++ render settings lhs ++ ", " ++ render settings rhs ++ ")"',
)

# rel-extra-wrapper-template: the recovered MIRROR half of the sibling's wrap-domain pair
# (see the accounting note on partial-domain-always-wrap). Both operands are rendered at
# the CORRECT active profile — clause C1 is fully satisfied — but a constant decoration is
# spliced around the first rendered operand, unconditionally. This is the over-application
# fault: a routine that adds framing the template does not call for, rather than one that
# drops or mis-routes anything. Refuted by clause C2 (the surrounding template text is
# constant and pinned), and it is the ONLY rival in the battery that ADDS template text
# instead of permuting, replacing, or re-profiling what is already there.
_RIV_REL_EXTRA_WRAP = _swap(
    _BASE,
    _REL_BODY,
    " : String := Id.run do\n"
    '  return relName ++ "(" ++ "W(" ++ render settings lhs ++ ")" ++ ", "'
    ' ++ render settings rhs ++ ")"',
)

# The non-default-direction branch of the limit impl (inside its impl region), used by
# the two per-shape / per-component near-misses. Unique: the default branch closes
# after z0 instead of continuing with the direction fragment.
_LIM_ELSE = (
    '    return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "\n'
    '      ++ render settings z0 ++ ", dir=\'" ++ render settings dir ++ "\')"'
)
assert _BASE.count(_LIM_ELSE) == 1, "lim else-branch anchor drifted"

# lim-one-shape-default: the default-direction shape is FULLY correct; only the OTHER
# shape renders its components at the fixed profile. Agrees with the frozen behaviour
# across the ENTIRE dirIsDefault=true half of the domain, so it must be refuted on the
# other half. Attacks clause C1 within ONE branch.
_RIV_LIM_ONE_SHAPE = _swap(
    _BASE,
    _LIM_ELSE,
    '    return "Limit(" ++ render _defaultSettings e ++ ", "'
    ' ++ render _defaultSettings z ++ ", "\n'
    '      ++ render _defaultSettings z0 ++ ", dir=\'"'
    ' ++ render _defaultSettings dir ++ "\')"',
)

# lim-direction-component-default: nearest miss of all. Within the non-default-direction
# shape the three expression components are rendered at the ACTIVE profile and ONLY the
# direction component leaks the fixed one. Attacks clause C1 at a SINGLE component
# position — the residual-omission class the reported issue is really about, since the
# whole point is that EVERY nested position must render at the active profile.
_RIV_LIM_DIR_COMPONENT = _swap(
    _BASE,
    _LIM_ELSE,
    '    return "Limit(" ++ render settings e ++ ", " ++ render settings z ++ ", "\n'
    '      ++ render settings z0 ++ ", dir=\'"'
    ' ++ render _defaultSettings dir ++ "\')"',
)


# --- witnesses ---------------------------------------------------------------------
# `Settings := Bool`, `Expr := Bool`. A `render` reading its FIRST argument exposes the
# active-vs-default profile choice (clause C1); one reading its SECOND argument exposes
# operand identity / branch shape (clauses C2/C3). Each witness states the spec
# predicate is FALSE of the rival's output at one concrete input, unfolds spec + impl,
# and `decide`s the string disequality. It ELABORATES against the rival (which produces
# the wrong string there) and FAILS on gold (which satisfies the spec at every input).
# No hypotheses are assumed (all data is concrete), so there is no consistency question.

# C1 @ relational: active profile `settings=true` ≠ default `_default=false`, a
# profile-sensitive render (reads its FIRST arg). gold emits render true = "Sp" in
# both operand slots; the prepatch rival emits render false = "Pl". The operand
# values (lhs=false, rhs=true) are irrelevant to this render, so they are set to
# distinct values purely to VARY the lhs/rhs binders across the two relational
# witnesses (the swap witness pins the profile arg the other way). `decide` separates
# the two strings.
_WIT_REL_PREPATCH = (
    "example :\n"
    '  ¬ problem_spec_printRelational (fun (s : Bool) (_ : Bool) => if s then "Sp" else "Pl")'
    ' true "Eq" false true\n'
    '    (implementation_printRelational (fun (s : Bool) (_ : Bool) => if s then "Sp" else "Pl")'
    ' true false "Eq" false true) := by\n'
    "  unfold problem_spec_printRelational implementation_printRelational\n"
    "  decide"
)

# C2 @ relational (operand order): an expr-sensitive render (reads its SECOND arg:
# lhs=true -> "A", rhs=false -> "B"). gold emits "Ne(A, B)"; the swap rival emits
# "Ne(B, A)". The profile arg is set to `false` (and relName to "Ne") to vary the
# `settings`/`relName` binders vs the prepatch witness; the render ignores it.
_WIT_REL_SWAP = (
    "example :\n"
    '  ¬ problem_spec_printRelational (fun (_ : Bool) (x : Bool) => if x then "A" else "B")'
    ' false "Ne" true false\n'
    '    (implementation_printRelational (fun (_ : Bool) (x : Bool) => if x then "A" else "B")'
    ' false true "Ne" true false) := by\n'
    "  unfold problem_spec_printRelational implementation_printRelational\n"
    "  decide"
)

# C1 @ limit: profile-sensitive render, active `settings=true` ≠ default, dirIsDefault
# =true. gold emits render true in every component; the prepatch rival emits render
# false. Component values (e=false, z=false, z0=true, dir=false) are irrelevant to
# this render and set to vary the e/z/dir binders across the three limit witnesses.
_WIT_LIM_PREPATCH = (
    "example :\n"
    '  ¬ problem_spec_printLimit (fun (s : Bool) (_ : Bool) => if s then "Sp" else "Pl")'
    " true true false false true false\n"
    '    (implementation_printLimit (fun (s : Bool) (_ : Bool) => if s then "Sp" else "Pl")'
    " true false true false false true false) := by\n"
    "  unfold problem_spec_printLimit implementation_printLimit\n"
    "  decide"
)

# C3 @ limit (branch): dirIsDefault=FALSE, so the spec demands the `dir='…'` suffix.
# gold emits the suffixed shape; the ignore-dir rival emits the plain shape. An
# expr-sensitive render suffices (the shapes differ in structure, not just profile).
# Profile arg set to `false` to vary the `settings` binder vs the other limit
# witnesses; this is the only limit witness with dirIsDefault=false.
_WIT_LIM_IGDIR = (
    "example :\n"
    '  ¬ problem_spec_printLimit (fun (_ : Bool) (x : Bool) => if x then "A" else "B")'
    " false false true true true true\n"
    '    (implementation_printLimit (fun (_ : Bool) (x : Bool) => if x then "A" else "B")'
    " false true false true true true true) := by\n"
    "  unfold problem_spec_printLimit implementation_printLimit\n"
    "  decide"
)

# C2 @ limit (component order): expr-sensitive render, z=true -> "A", z0=false -> "B",
# dirIsDefault=true, e=false -> "B". gold emits "Limit(B, A, B)"; the swap rival emits
# "Limit(B, B, A)". Requires z ≠ z0 to be observable.
_WIT_LIM_SWAPZ = (
    "example :\n"
    '  ¬ problem_spec_printLimit (fun (_ : Bool) (x : Bool) => if x then "A" else "B")'
    " true true false true false false\n"
    '    (implementation_printLimit (fun (_ : Bool) (x : Bool) => if x then "A" else "B")'
    " true false true false true false false) := by\n"
    "  unfold problem_spec_printLimit implementation_printLimit\n"
    "  decide"
)


# C1 @ relational, ONE position: profile-sensitive render, active `settings=true` ≠
# default. gold emits render true = "Wr" in BOTH operand slots; the rival emits
# render false = "Bd" in the FIRST only, so the strings differ in that slot alone.
# Fresh relName ("Lt") and operand values vs the other relational witnesses, so this is
# a distinct probe point rather than a re-refutation of the wholesale rival's input.
_WIT_REL_ONE_OPERAND = (
    "example :\n"
    '  ¬ problem_spec_printRelational (fun (s : Bool) (_ : Bool) => if s then "Wr" else "Bd")'
    ' true "Lt" true false\n'
    '    (implementation_printRelational (fun (s : Bool) (_ : Bool) => if s then "Wr" else "Bd")'
    ' true false "Lt" true false) := by\n'
    "  unfold problem_spec_printRelational implementation_printRelational\n"
    "  decide"
)

# C2 @ relational (operator tag): an expr-sensitive render, so the profile plays no
# part — the disagreement is confined to the leading tag. gold emits "Ge(Q, P)"; the
# rival emits "Eq(Q, P)". Profile arg `false` and a fourth distinct relName.
_WIT_REL_CONST_TAG = (
    "example :\n"
    '  ¬ problem_spec_printRelational (fun (_ : Bool) (x : Bool) => if x then "P" else "Q")'
    ' false "Ge" false true\n'
    '    (implementation_printRelational (fun (_ : Bool) (x : Bool) => if x then "P" else "Q")'
    ' false true "Ge" false true) := by\n'
    "  unfold problem_spec_printRelational implementation_printRelational\n"
    "  decide"
)

# C1 @ limit, ONE shape: dirIsDefault=FALSE (the half this rival gets wrong — on the
# other half it is byte-identical to gold, which is exactly why it needs its own
# witness). Profile-sensitive render, active=true; gold emits "Ac" throughout the
# suffixed shape, the rival "Df".
_WIT_LIM_ONE_SHAPE = (
    "example :\n"
    '  ¬ problem_spec_printLimit (fun (s : Bool) (_ : Bool) => if s then "Ac" else "Df")'
    " true false true false true false\n"
    '    (implementation_printLimit (fun (s : Bool) (_ : Bool) => if s then "Ac" else "Df")'
    " true false false true false true false) := by\n"
    "  unfold problem_spec_printLimit implementation_printLimit\n"
    "  decide"
)

# C1 @ limit, ONE component: dirIsDefault=FALSE and a profile-sensitive render, so the
# three expression components agree with gold ("Nx") and ONLY the direction component
# differs (rival "Ol"). The narrowest divergence the spec still catches. Component
# values chosen distinct from the other limit witnesses (dir=true here).
_WIT_LIM_DIR_COMPONENT = (
    "example :\n"
    '  ¬ problem_spec_printLimit (fun (s : Bool) (_ : Bool) => if s then "Nx" else "Ol")'
    " true false false false false true\n"
    '    (implementation_printLimit (fun (s : Bool) (_ : Bool) => if s then "Nx" else "Ol")'
    " true false false false false false true) := by\n"
    "  unfold problem_spec_printLimit implementation_printLimit\n"
    "  decide"
)


# C2 @ relational (added template text): an expr-sensitive render, so the profile plays
# no part and the disagreement is confined to the decoration the rival splices around the
# first operand. gold emits "Eq(A, B)"; the rival emits "Eq(W(A), B)". Profile arg `true`
# with `lhs`/`rhs` distinct, so the point is distinct from rel-constant-tag (which varies
# the tag at settings=false) as well as from both profile witnesses.
_WIT_REL_EXTRA_WRAP = (
    "example :\n"
    '  ¬ problem_spec_printRelational (fun (_ : Bool) (x : Bool) => if x then "A" else "B")'
    ' true "Eq" true false\n'
    '    (implementation_printRelational (fun (_ : Bool) (x : Bool) => if x then "A" else "B")'
    ' true false "Eq" true false) := by\n'
    "  unfold problem_spec_printRelational implementation_printRelational\n"
    "  decide"
)


# ===========================================================================
# ADMISSIBILITY — the modeled behaviour must be SATISFIABLE at a normal input.
# ===========================================================================
# Both obligations are additionally discharged at a CONCRETE task-shaped
# instantiation (a profile-sensitive renderer with the active profile switched ON) as a
# `have` prepended to the existing tactic body; the frozen proof then closes the
# obligation verbatim. Nothing is assumed: no new declaration, both theorem STATEMENTS
# byte-identical, no assumption token. If the modeled behaviour were satisfiable only
# vacuously — never at a literal input of the shape the reported expectations exercise —
# this would fail, which is the analogue of PRECOND-TOO-STRONG on obligations that bind
# no precondition hypotheses. (Verified: real build.)
_ADM_RENDER = 'fun (s : Bool) (_ : Bool) => if s then "Wr" else "Bd"'
_REL_INTRO = ("  intro Settings Expr render settings defaultSettings "
              "relName lhs rhs")
_LIM_INTRO = ("  intro Settings Expr render settings defaultSettings "
              "dirIsDefault e z z0 dir")

_ADMISS = _swap(
    _swap(
        _BASE, _REL_INTRO,
        "  have _ground : problem_spec_printRelational\n"
        f"      ({_ADM_RENDER})\n"
        '      true "Eq" true false\n'
        "      (implementation_printRelational\n"
        f"        ({_ADM_RENDER})\n"
        '        true false "Eq" true false) := by\n'
        "    unfold problem_spec_printRelational implementation_printRelational\n"
        "    decide\n" + _REL_INTRO),
    _LIM_INTRO,
    "  have _ground : problem_spec_printLimit\n"
    f"      ({_ADM_RENDER})\n"
    "      true true false false true false\n"
    "      (implementation_printLimit\n"
    f"        ({_ADM_RENDER})\n"
    "        true false true false false true false) := by\n"
    "    unfold problem_spec_printLimit implementation_printLimit\n"
    "    decide\n" + _LIM_INTRO)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-relational-pure",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REL_PURE,
        "rationale": (
            "structurally-different but CORRECT relational impl written as a pure `def` "
            "(no `Id.run do`, no early return) whose body is byte-for-byte the spec RHS. "
            "Semantics identical on every input. The theorem STATEMENT is byte-identical "
            "and the FROZEN proof body (`unfold …; rfl`) still closes because `Id.run` of "
            "a pure `return v` reduces to `v`. No reproof, no new axiom/lemma/sorry. If it "
            "FAILS => SPEC-TOO-STRONG (postcondition over-fit to the monadic impl shape)."
        ),
    },
    {
        "id": "pos-limit-letbind",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LIM_LETBIND,
        "rationale": (
            "structurally-different but CORRECT limit impl: each nested render is bound to "
            "a typed local before the branch and the locals are spliced into the two "
            "templates, instead of re-spelling `render settings …` inside each branch. "
            "Output equals the frozen impl's on every input. The theorem STATEMENT is "
            "byte-identical and the FROZEN proof body (`cases dirIsDefault <;> rfl`) still "
            "closes. No reproof, no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG."
        ),
    },

    {
        "id": "pos-relational-reassoc",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REL_REASSOC,
        "rationale": (
            "CORRECT relational impl that RE-ASSOCIATES the template concatenation "
            "(`((tag ++ \"(\") ++ lhs') ++ ((\", \" ++ rhs') ++ \")\")`) instead of the "
            "frozen right-nested chain. Unlike pos-relational-pure, this is NOT "
            "definitionally the frozen impl: `String.append` is associative but not "
            "definitionally so at this shape, and the audit measured the frozen `rfl` "
            "FAILING on it, so the postcondition is genuinely re-discharged over a "
            "different term structure (tactic body only; STATEMENT byte-identical, no new "
            "axiom/lemma/sorry). Same output on every input. If it FAILS => "
            "SPEC-TOO-STRONG (postcondition over-fit to one parenthesisation)."
        ),
    },
    {
        "id": "pos-limit-factored-tail",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LIM_FACTORED,
        "rationale": (
            "CORRECT limit impl that emits the shared prefix ONCE and branches only over "
            "the TAIL, pushing the branch inside the concatenation instead of spelling a "
            "whole template per branch. Not definitionally the frozen impl: the audit "
            "measured the frozen `cases dirIsDefault <;> rfl` FAILING on it, so the "
            "obligation is re-discharged over a restructured term (tactic body only; "
            "STATEMENT byte-identical, no new axiom/lemma/sorry). Output equals the frozen "
            "impl's on every input. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit "
            "to a per-branch whole-template spelling)."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "rel-prepatch-default-profile",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REL_PREPATCH,
        "refinement": (
            "this IS the modeled bug: the relational renderer hands the nested operand "
            "calls the fixed default profile a bare textual conversion uses, instead of "
            "the printer's active profile. Its faithful real patch is the UNCHANGED "
            "renderer, under which a rational operand of a relational rendered with the "
            "non-default integer-wrapping option ON prints WITHOUT the wrapper "
            "(the exact behaviour the F2P test_Rational pins as WRONG, e.g. the operand "
            "coming out as the plain fraction rather than the wrapped form). The exact-"
            "output assertion FAILS, so it would NOT resolve — this is precisely the bug "
            "the patch fixes (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by clause C1 (profile propagation) at the relational site: the spec "
            "pins both operand positions to `render settings …`, but the rival renders at "
            "`_defaultSettings`. Witness instantiates `Settings := Expr := Bool` and a "
            "profile-sensitive `render` (reads its FIRST argument), so `render true ≠ "
            "render false` is a concrete string disequality `decide` closes. Varies the "
            "`settings`/`_default` binder pair (active ≠ default). If it VERIFIES => "
            "SPEC-TOO-WEAK (profile propagation unpinned)."
        ),
        "witness": _WIT_REL_PREPATCH,
    },
    {
        "id": "rel-swap-operands",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REL_SWAP,
        "refinement": (
            "renders both operands at the correct active profile but emits them in the "
            "WRONG ORDER (right operand before left). Its faithful real patch is a "
            "renderer that transposes the two operand slots of the relational template; a "
            "relation like `Eq(x, 2/3)` would render as `Eq(2/3, x)`, so every exact-"
            "output assertion over a relational (test_Rational, test_python_relational) "
            "FAILS. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (operand order) at the relational site: the spec fixes "
            "the order lhs THEN rhs. Witness uses an expr-sensitive `render` (reads its "
            "SECOND argument) with distinct lhs/rhs (`true`/`false` -> \"A\"/\"B\"), so "
            "gold's \"Eq(A, B)\" differs from the rival's \"Eq(B, A)\" by `decide`. Varies "
            "the `lhs`/`rhs` binders (distinct operands) — a distinct probe point from the "
            "prepatch witness (which holds both operands equal). If it VERIFIES => "
            "SPEC-TOO-WEAK (operand order unpinned)."
        ),
        "witness": _WIT_REL_SWAP,
    },
    {
        "id": "lim-prepatch-default-profile",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_LIM_PREPATCH,
        "refinement": (
            "the SAME propagation bug at the OTHER modeled site: every nested component of "
            "the limit is rendered at the fixed default profile instead of the active one. "
            "Its faithful real patch is the UNCHANGED limit renderer, under which the "
            "limit-point operand printed with the non-default integer-wrapping option ON "
            "loses the wrapper — the exact behaviour the F2P test_Rational pins as WRONG "
            "for a limit (the point coming out as the plain fraction rather than the "
            "wrapped form). It would NOT resolve; confirms the symmetric routine is "
            "equally tight."
        ),
        "rationale": (
            "REJECTED by clause C1 (profile propagation) at the limit site: the spec pins "
            "every component to `render settings …`, but the rival renders at "
            "`_defaultSettings`. Witness uses the profile-sensitive `render` at "
            "dirIsDefault=true; `render true ≠ render false` closes by `decide`. Varies "
            "the `settings`/`_default` binder pair at the limit site. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _WIT_LIM_PREPATCH,
    },
    {
        "id": "lim-ignore-dir",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_LIM_IGDIR,
        "refinement": (
            "renders every component at the correct active profile but ALWAYS emits the "
            "default-direction shape, dropping the `dir='…'` suffix when the approach "
            "direction is non-default. Its faithful real patch is a limit renderer that "
            "never appends the direction clause; a limit with a non-default direction "
            "would render without its `dir=` component, so the exact-output assertions "
            "over such a limit (test_Limit) FAIL. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C3 (branch selection): the spec demands the `dir='…'` "
            "suffix exactly when `dirIsDefault` is false. Witness sets dirIsDefault=FALSE, "
            "so the spec's suffixed shape differs STRUCTURALLY from the rival's plain "
            "shape; an expr-sensitive `render` and `decide` close it. Varies the "
            "`dirIsDefault` binder (false — the only witness that does), which every other "
            "limit witness holds at true. If it VERIFIES => SPEC-TOO-WEAK (branch "
            "selection unpinned)."
        ),
        "witness": _WIT_LIM_IGDIR,
    },
    {
        "id": "lim-swap-z-z0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_LIM_SWAPZ,
        "refinement": (
            "renders every component at the correct active profile and selects the correct "
            "branch, but emits the second and third limit components (`z` and `z0`) in the "
            "WRONG ORDER. Its faithful real patch transposes those two template slots; a "
            "limit `Limit(x, x, 1/2)` would render as `Limit(x, 1/2, x)`, so the exact-"
            "output assertions over a limit (test_Limit) FAIL. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (component order) at the limit site: the spec fixes the "
            "order e, z, z0. Witness uses an expr-sensitive `render` with distinct z/z0 "
            "(`true`/`false` -> \"A\"/\"B\") at dirIsDefault=true; gold's \"…, A, B)\" "
            "differs from the rival's \"…, B, A)\" by `decide`. Varies the `z`/`z0` binders "
            "(distinct components) — a distinct probe point from lim-prepatch (all "
            "components equal) and lim-ignore-dir. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_LIM_SWAPZ,
    },

    {
        "id": "rel-extra-wrapper-template",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REL_EXTRA_WRAP,
        "refinement": (
            "the recovered MIRROR of the sibling's wrap-domain pair: an OVER-application "
            "fault rather than an omission. Both operands are rendered at the correct "
            "active profile, but a constant decoration is spliced around the first "
            "rendered operand unconditionally. Its faithful real patch is a renderer whose "
            "relational template carries extra framing around an operand slot, so every "
            "relation — including the ones rendered under the default display options — "
            "comes out with framing the expected text does not have. Every exact-output "
            "assertion over a relational (test_Rational, test_python_relational) FAILS, so "
            "it would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (template composition): the spec pins the surrounding "
            "template text to a CONSTANT, and this rival adds to it. This is the only "
            "rival that ADDS template text — every other one mis-routes a profile or "
            "permutes/replaces text already present — so a spec that pinned the nested "
            "positions and the operand order but let the framing around a slot float would "
            "refute all of them and admit this one. Witness uses an expr-sensitive "
            "`render` at settings=true with distinct operands: gold's \"Eq(A, B)\" differs "
            "from the rival's decorated form by `decide`. If it VERIFIES => SPEC-TOO-WEAK "
            "(the constant framing around an operand slot is unpinned)."
        ),
        "witness": _WIT_REL_EXTRA_WRAP,
    },

    # ---- near-miss rivals: a SINGLE mis-propagated position (must REJECT) ----
    {
        "id": "rel-one-operand-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REL_ONE_OPERAND,
        "refinement": (
            "propagates the active rendering profile to the SECOND operand position only; "
            "the first still renders at the fixed default profile. Its faithful real patch "
            "is a partial propagation that reaches one nested slot of the relational "
            "template and misses the other. A relation whose left operand renders "
            "differently under the two profiles would emit that operand in the wrong form "
            "while the right operand is correct, so an exact-output assertion over such a "
            "relation (test_python_relational) FAILS. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 at the FIRST operand position specifically. This exists "
            "because rel-prepatch-default-profile flips BOTH positions at once: any spec "
            "that pinned only 'at least one operand uses the active profile' would refute "
            "that rival and admit this one. Witness uses a profile-sensitive `render` with "
            "settings=true, so gold emits the active form in both slots and the rival "
            "differs in the first alone; `decide` separates them. Varies `relName` (\"Lt\") "
            "and the operand pair vs every other relational witness — a distinct probe "
            "point. If it VERIFIES => SPEC-TOO-WEAK (the spec constrains the operand "
            "positions only jointly, not each one)."
        ),
        "witness": _WIT_REL_ONE_OPERAND,
    },
    {
        "id": "rel-constant-tag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REL_CONST_TAG,
        "refinement": (
            "renders both operands at the correct active profile but emits a FIXED operator "
            "tag instead of the one supplied for this relation. Its faithful real patch is a "
            "renderer whose template hardcodes one relation's name; every relation of a "
            "different kind would render under the wrong name, so the exact-output "
            "assertions over relations (test_python_relational) FAIL. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (template composition) at the operator-tag slot. This is "
            "the ONLY case that exercises the `relName` binder as load-bearing DATA rather "
            "than as a value carried along: both profile rivals reproduce `relName` "
            "faithfully, so a spec that dropped the tag from the required output (or fixed "
            "it to a constant) would still refute them. Witness uses an expr-sensitive "
            "`render` at settings=false, isolating the disagreement to the tag: gold's tag "
            "differs from the rival's constant by `decide`. Varies `settings`=false and a "
            "fourth distinct `relName`. If it VERIFIES => SPEC-TOO-WEAK (the relation name "
            "is not pinned to the input)."
        ),
        "witness": _WIT_REL_CONST_TAG,
    },
    {
        "id": "lim-one-shape-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_LIM_ONE_SHAPE,
        "refinement": (
            "propagates the active rendering profile correctly throughout the "
            "default-direction limit shape, but renders every component of the OTHER shape "
            "at the fixed default profile. Its faithful real patch is a propagation applied "
            "to one branch of a two-branch renderer and forgotten in the other; a limit "
            "with a non-default approach direction would render all of its components in "
            "the wrong form, so an exact-output assertion over such a limit (test_Limit) "
            "FAILS. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 restricted to the non-default-direction BRANCH. It is "
            "byte-identical to gold across the entire dirIsDefault=true half of the domain, "
            "which is precisely why lim-prepatch-default-profile cannot stand in for it: a "
            "spec that pinned the profile only in the branch every other limit witness "
            "exercises would admit this rival. Witness therefore sets dirIsDefault=FALSE "
            "with a profile-sensitive `render` at settings=true, and `decide` separates the "
            "active-form suffixed shape from the rival's default-form one. If it VERIFIES "
            "=> SPEC-TOO-WEAK (one branch's rendering profile is unconstrained)."
        ),
        "witness": _WIT_LIM_ONE_SHAPE,
    },
    {
        "id": "lim-direction-component-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_LIM_DIR_COMPONENT,
        "refinement": (
            "renders the three expression components of the non-default-direction limit "
            "shape at the correct active profile and leaks the fixed default profile in the "
            "DIRECTION component alone. Its faithful real patch is a propagation that "
            "reaches every nested slot of the template but one. A limit whose direction "
            "component renders differently under the two profiles would emit that one "
            "component in the wrong form, so an exact-output assertion over such a limit "
            "(test_Limit) FAILS. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 at a SINGLE component position — the narrowest "
            "divergence in the battery, correct on every input except those where one "
            "component's rendering is profile-sensitive. This is the residual-omission "
            "class the whole obligation is about (EVERY nested position renders at the "
            "active profile), and no other rival tests it: all the others get a whole "
            "template, a whole branch, or a whole operand pair wrong. Witness sets "
            "dirIsDefault=FALSE with a profile-sensitive `render` at settings=true, so the "
            "first three components agree with gold and only the fourth differs; `decide` "
            "closes it. Varies the `dir` binder (true — the only witness that does) against "
            "e=z=z0=false, so the divergence is attributable to that position alone. If it "
            "VERIFIES => SPEC-TOO-WEAK (a per-position obligation stated only in aggregate)."
        ),
        "witness": _WIT_LIM_DIR_COMPONENT,
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "NON-VACUITY at a concrete, task-shaped input. Both obligations are universally "
            "quantified over `Settings`, `Expr` and `render` and bind no precondition "
            "hypotheses, so there is no precondition to be too strong; the portable residue "
            "of the nagini admissibility lane is that the modeled behaviour must be "
            "SATISFIABLE at a literal input of the shape the reported expectations exercise, "
            "not merely at inputs where the two profiles coincide. Each obligation is "
            "additionally discharged as a `have` at Settings := Expr := Bool with a "
            "profile-sensitive renderer and the active profile switched ON (the "
            "configuration under which the two profiles genuinely differ), by `unfold` + "
            "`decide`; the frozen tactic body then closes the obligation verbatim. Both "
            "theorem STATEMENTS stay byte-identical, no declaration is added, and no "
            "assumption token is used, so nothing is weakened. If this REJECTS => the "
            "spec is unsatisfiable at a normal input, i.e. SPEC-TOO-STRONG (the "
            "obligation-level analogue of PRECOND-TOO-STRONG on a precondition-free spec)."
        ),
    },
]


# No @ContractOnly axioms are consumed by this spec: `render` is a universally-
# quantified parameter (mapping.md A-reference to the unchanged subexpression printer),
# NOT an axiomatized callee, so there is no constraining property for this spec lane to
# test. The axiom lane belongs to G-AX regardless.
AXIOM_TESTS = []
