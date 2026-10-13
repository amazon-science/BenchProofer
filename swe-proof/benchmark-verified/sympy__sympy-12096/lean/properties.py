"""properties.py — G-PBT falsification battery for sympy__sympy-12096 (lean).

NOT a Lean file; a record of the adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_evalf``
STATEMENT stays byte-identical). ``expect="verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect="reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` HOLDS of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a single inductive input):

  evalf (e : Expr) : Option Int      with      result = evalSpec e

  ``Expr`` is the numeric-expression carrier with three constructors:
    * ``num n``     — a concrete numeric value ``n``;
    * ``atom``      — a bare symbol carrying NO numeric value;
    * ``app f args``— an application of a node whose numeric implementation is
                      ``f : List Int → Int`` to the argument subexpressions.

  ``evalSpec`` is the FULLY GROUNDED oracle (a structural recursion over the
  argument subexpressions, spelled out — not an opaque answer key):
    * ``num n``  ↦ ``some n``;
    * ``atom``   ↦ ``none``;
    * ``app f args`` ↦ ``(args.attach.mapM evalSpec).map f`` — a numeric value
      exactly when EVERY argument has one, obtained by evaluating each argument
      and then applying the node's implementation ``f`` to the evaluated list.

  The single top-level clause ``result = evalSpec e`` therefore pins THREE
  independent behaviors, one per constructor of the sole input binder ``e``:
    * the concrete-value leaf must reduce to itself (the ``num`` equation);
    * a bare symbol must have NO numeric value (the ``atom`` equation);
    * an application must evaluate each argument FIRST and then apply the
      node's implementation to the evaluated list (the ``app`` equation) — the
      load-bearing clause, since the modeled behavior's whole content is that a
      NESTED application argument is itself evaluated before the outer
      implementation runs.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY because its modeled list input is held at
    fractional (read-only) permission, so a rival that appends to / index-stores
    into it is rejected for insufficient permission. Lean is referentially
    transparent: the input is a plain immutable ``Expr`` value, there is no
    half-permission to violate and no aliasing to exploit, so BOTH nagini
    frame-mutation rivals (``frame-mutate-append`` / ``frame-mutate-index``)
    have NO expressible instance here. No substitute is fabricated for them.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on this backend. ``implementation_evalf``
    is a total Lean ``def`` (well-founded over the argument subexpressions), so a
    diverging implementation cannot be written at all; there is nothing to port.

  * UNGROUNDED-ORACLE ECHO — not applicable AS AN ATTACK, but it constrains the
    positives. ``evalSpec`` is a pure function of the input, fully unfolded (no
    ``opaque`` callee, no consumed axiom; meta.json axioms == [],
    deep_model_references == []), so returning it IS the cheapest CORRECT impl
    rather than a wrong echo — there is no rival to build here. The consequence
    for the other direction is that an impl which merely RESTATES the oracle's
    app equation is a degenerate soundness positive: it verifies, but its
    obligation is the oracle's own defining equation, so it exercises nothing.
    The soundness positive below is therefore required to differ from the oracle
    as well as from gold (see ``pos-reverse-accumulator``).

  * PARTIAL-DOMAIN uniqueness — APPLIES, and is the load-bearing class. The
    nagini partial-domain rivals (``partial-none-on-composition``,
    ``partial-offbyone-on-composition``, ``partial-wrong-bare-leaf``) each attack
    the value pin on a distinct sub-domain; here each maps to an ``Expr``
    constructor / recursion depth and is refuted with a concrete witness (see
    below). A fourth rival attacks the ``atom`` equation directly (a
    lean-carrier binder the nagini ``Optional[int]`` leaf modeled implicitly).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating ``problem_spec_evalf`` directly at a
concrete input; each was built (against the rival) and rebuilt (against the
frozen solution) to confirm it HOLDS of its rival and FAILS on gold (so it
discriminates rather than asserting a tautology). ``decide``/``rfl`` get stuck on
the well-founded recursion, so each witness unfolds ``evalSpec`` +
``implementation_evalf`` and the ``mapM``/``attach``/``Id.run`` machinery with a
fixed ``simp only`` set, then closes the residual concrete (in)equality with
``decide``. All witnesses probe literal inputs (no ``opaque`` term forces
conditioning), so none carries a hypothesis binder (no consistency obligation).

BINDER COVERAGE. The sole input binder ``e`` is varied across all THREE
constructors, across recursion depth, AND across argument-list arity by the
reject witnesses:
  * ``num 2``                       — the ``num`` (bare-leaf) equation;
  * ``atom``                        — the ``atom`` (symbolic) equation;
  * ``app f []``                    — the ``app`` equation, ZERO arguments;
  * ``app f [num 2]``               — the ``app`` equation, 1-layer;
  * ``app f [num 2, num 5]``        — the ``app`` equation, TWO arguments, with a
                                      position-sensitive node implementation, so
                                      arity and ORDER are observable;
  * ``app f [app f [num 2]]``       — the ``app`` equation, NESTED (the F2P shape).
``pts`` = 6 distinct input points, so the value pin's dependence on the
constructor, on recursion depth, and on the argument list is demonstrated, not
merely asserted. (The arity-0 and arity-2 points were added by the audit: at
arity <= 1 the evaluated-argument list is determined by its single element, so
the ``app`` equation's claim that the node implementation receives EVERY
argument IN ORDER was previously undemonstrated — two rivals that are correct at
every originally-probed input are now refuted there.)

OMITTED nagini cases (see assessment): the two frame/permission-mutation rivals
(VACUOUS on a referentially-transparent carrier) and the AXIOM_TESTS lane (this
bundle declares no axiom / deep-model reference — G-AX skips — and the axiom
lane is not this gate's job). The nagini ``pos-loop-rename`` and
``pos-cheapest-fold`` positives collapse to a SINGLE structural soundness
positive here; note that the ``pos-cheapest-fold`` analogue (return the oracle
fold directly) is NOT a meaningful positive on this carrier, because ``evalSpec``
is a spelled-out total function rather than nagini's ``@Pure`` fold, so "return
the fold" is literally the spec's own defining equation with one identifier
renamed. The surviving positive is the ``pos-loop-rename`` analogue instead: an
accumulator reshape that keeps the loop but changes its invariant.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-12096"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (each unique inside Solution.lean; verified at load). The FULL
# frozen impl-region body and the FULL frozen proof-region body, so every
# replacement lands entirely inside the region it means to edit.
# ---------------------------------------------------------------------------

_IMPL_GOLD = (
    "def implementation_evalf : Expr → Option Int\n"
    "  | .num n  => some n\n"
    "  | .atom   => none\n"
    "  | .app f args => Id.run do\n"
    "      let mut vals : List Int := []\n"
    "      for a in args.attach do\n"
    "        match implementation_evalf a.1 with\n"
    "        | some v => vals := vals ++ [v]\n"
    "        | none   => return none\n"
    "      return some (f vals)\n"
    "decreasing_by\n"
    "  have h := List.sizeOf_lt_of_mem a.2\n"
    "  simp only [Expr.app.sizeOf_spec]\n"
    "  omega"
)

# The frozen proof body from `intro e` onward — the app-branch loop lemmas above
# it (`loop_run`, `loop_eq_mapM`, `mapM_congr_eval`) are re-derivable but the
# structural positive replaces the WHOLE proof region, so this anchor is used
# only by the admissibility case, which keeps the frozen proof verbatim and
# injects a ground instance before it.
_PROOF_INTRO = (
    "theorem correct_evalf : ∀ (e : Expr),\n"
    "    problem_spec_evalf e (implementation_evalf e) := by\n"
    "  intro e\n"
    "  show implementation_evalf e = evalSpec e"
)

# The FULL frozen proof region body (used to reshape the proof for the
# structurally-different soundness positive).
_PROOF_GOLD = (
    "/-- Closed form for the app-branch imperative loop started with accumulator `acc`\n"
    "over the attached argument list `xs`: the `mapM` of `implementation_evalf` over the\n"
    "subexpressions, threaded through `acc`.  This is the value-level target the loop is\n"
    "proven equal to before the outer implementation function `f` is applied. -/\n"
    "def loop_run {p : Expr → Prop} (xs : List {x : Expr // p x}) (acc : List Int) :\n"
    "    Option (List Int) :=\n"
    "  Option.map (fun vs => acc ++ vs) (xs.mapM (fun a => implementation_evalf a.1))\n"
    "\n"
    "/-- The app-branch imperative `Id.run` for-loop (with early `none` short-circuit,\n"
    "started at accumulator `acc`, and final `some (f vals)`) equals the closed form\n"
    "`loop_run xs acc` post-composed with `f`. -/\n"
    "theorem loop_eq_mapM {p : Expr → Prop} (f : List Int → Int)\n"
    "    (xs : List {x : Expr // p x}) (acc : List Int) :\n"
    "    (Id.run do\n"
    "      let mut vals := acc\n"
    "      for a in xs do\n"
    "        match implementation_evalf a.1 with\n"
    "        | some v => vals := vals ++ [v]\n"
    "        | none   => return none\n"
    "      return some (f vals)) = (loop_run xs acc).map f := by\n"
    "  induction xs generalizing acc with\n"
    "  | nil => simp [loop_run, Id.run]; rfl\n"
    "  | cons a as ih =>\n"
    "      simp only [List.forIn_cons, loop_run, List.mapM_cons]\n"
    "      cases h : implementation_evalf a.1 with\n"
    "      | none => simp [Id.run]; rfl\n"
    "      | some v =>\n"
    "          have hih := ih (acc ++ [v])\n"
    "          simp only [loop_run, Id.run] at hih ⊢\n"
    "          simp at *\n"
    "          rw [hih]\n"
    "          cases List.mapM implementation_evalf as.unattach <;> simp\n"
    "\n"
    "/-- Under `mapM`, `implementation_evalf` may be swapped for `evalSpec` on the\n"
    "attached subexpressions using the pointwise induction hypothesis. -/\n"
    "theorem mapM_congr_eval {p : Expr → Prop} (xs : List {x : Expr // p x})\n"
    "    (h : ∀ a ∈ xs, implementation_evalf a.1 = evalSpec a.1) :\n"
    "    xs.mapM (fun a => implementation_evalf a.1)\n"
    "      = xs.mapM (fun a => evalSpec a.1) := by\n"
    "  induction xs with\n"
    "  | nil => rfl\n"
    "  | cons x xs ih =>\n"
    "    have hx : implementation_evalf x.1 = evalSpec x.1 := h x (by simp)\n"
    "    have hxs : ∀ a ∈ xs, implementation_evalf a.1 = evalSpec a.1 :=\n"
    "      fun a ha => h a (by simp [ha])\n"
    "    simp only [List.mapM_cons, hx, ih hxs]\n"
    "\n"
    "theorem correct_evalf : ∀ (e : Expr),\n"
    "    problem_spec_evalf e (implementation_evalf e) := by\n"
    "  intro e\n"
    "  show implementation_evalf e = evalSpec e\n"
    "  induction e using implementation_evalf.induct with\n"
    "  | case1 n => rw [implementation_evalf, evalSpec]\n"
    "  | case2 => rw [implementation_evalf, evalSpec]\n"
    "  | case3 f args ih =>\n"
    "    rw [implementation_evalf, evalSpec]\n"
    "    rw [loop_eq_mapM f args.attach []]\n"
    "    rw [loop_run]\n"
    "    rw [mapM_congr_eval args.attach (fun a _ => ih a)]\n"
    "    simp only [List.nil_append, Option.map_map]\n"
    "    rfl"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_INTRO) == 1, "proof intro drifted; update _PROOF_INTRO"
assert _BASE.count(_PROOF_GOLD) == 1, "proof region drifted; update _PROOF_GOLD"


# ---------------------------------------------------------------------------
# Rival / positive impl bodies (each a full impl region; only the impl — and,
# for the positive, the proof — changes, so the spec and the theorem STATEMENT
# stay byte-identical).
# ---------------------------------------------------------------------------

# STRUCTURAL POSITIVE: the arguments are accumulated in REVERSE order (`v ::
# vals` instead of `vals ++ [v]`) and the accumulator is re-reversed before the
# node implementation is applied. Behaviourally identical to gold at every
# input, but the intermediate accumulator disagrees with gold's at every step
# beyond the first, so closing the obligation requires a genuinely different
# loop lemma (`loop_eq_mapM`, whose closed form carries `acc.reverse ++ vs` rather
# than gold's `acc ++ vs`) — not a re-spelling of the oracle.
#
# AUDIT NOTE (why this replaced the previous positive). The earlier
# `pos-functional-mapM` impl was
#     | .app f args => (args.attach.mapM (fun a => implementation_evalf a.1)).map f
# which is the `evalSpec` app-equation VERBATIM with `evalSpec` renamed to
# `implementation_evalf`. Its obligation therefore reduced to the oracle's own
# defining equation, so it demonstrated only that the spec accepts a syntactic
# copy of itself — the honest-but-tests-nothing positive. It verified (real
# build, exit 0) and taught nothing. This reshape keeps the imperative loop (so
# it is not the oracle) while changing the accumulation order (so it is not
# gold), and was closed with a real build before being shipped here.
_IMPL_FUN = (
    "def implementation_evalf : Expr → Option Int\n"
    "  | .num n  => some n\n"
    "  | .atom   => none\n"
    "  | .app f args => Id.run do\n"
    "      let mut vals : List Int := []\n"
    "      for a in args.attach do\n"
    "        match implementation_evalf a.1 with\n"
    "        | some v => vals := v :: vals\n"
    "        | none   => return none\n"
    "      return some (f vals.reverse)\n"
    "decreasing_by\n"
    "  have h := List.sizeOf_lt_of_mem a.2\n"
    "  simp only [Expr.app.sizeOf_spec]\n"
    "  omega"
)
_PROOF_FUN = (
    "/-- Closed form for the REVERSE-accumulating app-branch loop started at `acc`:\n"
    "the `mapM` of `implementation_evalf` over the subexpressions, with the reversed\n"
    "accumulator prepended. Note `acc.reverse ++ vs` — gold's corresponding lemma\n"
    "carries `acc ++ vs`, so this is a genuinely different loop invariant, not a\n"
    "re-spelling of the frozen one. -/\n"
    "theorem loop_eq_mapM {q : Expr → Prop} (f : List Int → Int)\n"
    "    (xs : List {x : Expr // q x}) (acc : List Int) :\n"
    "    (Id.run do\n"
    "      let mut vals := acc\n"
    "      for a in xs do\n"
    "        match implementation_evalf a.1 with\n"
    "        | some v => vals := v :: vals\n"
    "        | none   => return none\n"
    "      return some (f vals.reverse))\n"
    "      = (xs.mapM (fun a => implementation_evalf a.1)).map\n"
    "          (fun vs => f (acc.reverse ++ vs)) := by\n"
    "  induction xs generalizing acc with\n"
    "  | nil => simp [Id.run]; rfl\n"
    "  | cons a as ih =>\n"
    "      simp only [List.forIn_cons, List.mapM_cons]\n"
    "      cases h : implementation_evalf a.1 with\n"
    "      | none => simp [Id.run]; rfl\n"
    "      | some v =>\n"
    "          have hih := ih (v :: acc)\n"
    "          simp only [Id.run] at hih ⊢\n"
    "          refine hih.trans ?_\n"
    "          cases List.mapM (fun a => implementation_evalf a.1) as <;>\n"
    "            simp [List.reverse_cons]\n"
    "\n"
    "/-- Under `mapM`, `implementation_evalf` may be swapped for `evalSpec` on the\n"
    "attached subexpressions using the pointwise induction hypothesis. -/\n"
    "theorem mapM_congr_eval {p : Expr → Prop} (xs : List {x : Expr // p x})\n"
    "    (h : ∀ a ∈ xs, implementation_evalf a.1 = evalSpec a.1) :\n"
    "    xs.mapM (fun a => implementation_evalf a.1)\n"
    "      = xs.mapM (fun a => evalSpec a.1) := by\n"
    "  induction xs with\n"
    "  | nil => rfl\n"
    "  | cons x xs ih =>\n"
    "    have hx : implementation_evalf x.1 = evalSpec x.1 := h x (by simp)\n"
    "    have hxs : ∀ a ∈ xs, implementation_evalf a.1 = evalSpec a.1 :=\n"
    "      fun a ha => h a (by simp [ha])\n"
    "    simp only [List.mapM_cons, hx, ih hxs]\n"
    "\n"
    "theorem correct_evalf : ∀ (e : Expr),\n"
    "    problem_spec_evalf e (implementation_evalf e) := by\n"
    "  intro e\n"
    "  show implementation_evalf e = evalSpec e\n"
    "  induction e using implementation_evalf.induct with\n"
    "  | case1 n => rw [implementation_evalf, evalSpec]\n"
    "  | case2 => rw [implementation_evalf, evalSpec]\n"
    "  | case3 f args ih =>\n"
    "    rw [implementation_evalf, evalSpec]\n"
    "    rw [loop_eq_mapM f args.attach []]\n"
    "    rw [mapM_congr_eval args.attach (fun a _ => ih a)]\n"
    "    cases List.mapM (fun a => evalSpec a.1) args.attach <;> simp"
)

# ADMISSIBILITY: the frozen impl + frozen proof, with a ground instance
# discharged at the F2P-shaped NESTED-application input BEFORE the frozen
# obligation — proving the modeled behavior is satisfiable at exactly the input
# the F2P exercises. `same_spec` elides the proof region, the theorem STATEMENT
# is byte-identical, and the `have` introduces no new named declaration/axiom.
#
# AUDIT NOTE (why this was strengthened). The previous form discharged
# `problem_spec_evalf` at the nested input by `simp only [...]; decide` — i.e. it
# proved `impl = evalSpec` HERE without ever naming the value either side takes.
# That is satisfiability, but the case's rationale claimed the stronger and more
# interesting fact that a strict `v ↦ v*v` applied to `f (f 2)` reaches 16, which
# the module never demonstrated: the literal `16` did not appear anywhere in it,
# so a reader could not tell whether both sides were `some 16` or both `none`
# (`none = none` would have satisfied the old script equally well, and `none` is
# exactly the pre-fix observation). The two `have`s below pin the ABSOLUTE value
# on each side independently, then close the ground instance by rewriting with
# them, so the prose and the machine-checked content now agree.
_ADMISS_INTRO = (
    "theorem correct_evalf : ∀ (e : Expr),\n"
    "    problem_spec_evalf e (implementation_evalf e) := by\n"
    "  have _spec_value : evalSpec\n"
    "      (.app (fun xs => xs.headD 0 * xs.headD 0) [.app (fun xs => xs.headD 0 * xs.headD 0) [.num 2]])\n"
    "      = some 16 := by\n"
    "    simp only [evalSpec, List.attach_cons, List.attach_nil, List.mapM_cons,\n"
    "      List.mapM_nil, List.map, Option.map, List.headD]\n"
    "    decide\n"
    "  have _impl_value : implementation_evalf\n"
    "      (.app (fun xs => xs.headD 0 * xs.headD 0) [.app (fun xs => xs.headD 0 * xs.headD 0) [.num 2]])\n"
    "      = some 16 := by\n"
    "    simp only [implementation_evalf, List.attach_cons, List.attach_nil,\n"
    "      Id.run, List.forIn_cons, List.forIn_nil, List.headD]\n"
    "    decide\n"
    "  have _ground : problem_spec_evalf\n"
    "      (.app (fun xs => xs.headD 0 * xs.headD 0) [.app (fun xs => xs.headD 0 * xs.headD 0) [.num 2]])\n"
    "      (implementation_evalf\n"
    "      (.app (fun xs => xs.headD 0 * xs.headD 0) [.app (fun xs => xs.headD 0 * xs.headD 0) [.num 2]])) := by\n"
    "    unfold problem_spec_evalf\n"
    "    rw [_spec_value, _impl_value]\n"
    "  intro e\n"
    "  show implementation_evalf e = evalSpec e"
)

# --- reject rivals (each a full impl region; the frozen proof region is kept
#     verbatim and legitimately fails to build against the reshaped impl — the
#     WITNESS is what attributes the rejection to the spec) ---

# PRE-PATCH: an application value is taken ONLY from arguments that are ALREADY
# concrete numbers; any argument that is itself an application aborts to `none`.
# Correct for a bare leaf and for a one-layer application over a numeric leaf,
# but leaves a NESTED application without a numeric value. Attacks the `app`
# equation on the nested sub-domain (the load-bearing bug).
_IMPL_PRE = (
    "def implementation_evalf : Expr → Option Int\n"
    "  | .num n  => some n\n"
    "  | .atom   => none\n"
    "  | .app f args => Id.run do\n"
    "      let mut vals : List Int := []\n"
    "      for a in args do\n"
    "        match a with\n"
    "        | .num v => vals := vals ++ [v]\n"
    "        | _      => return none\n"
    "      return some (f vals)"
)

# OFF-BY-ONE: evaluates each argument correctly (full recursion) but the node
# implementation is applied to a value one too large. Present (not none) but the
# WRONG number on every application. Attacks the apply-step of the `app`
# equation without touching the recursion.
_IMPL_OBO = (
    "def implementation_evalf : Expr → Option Int\n"
    "  | .num n  => some n\n"
    "  | .atom   => none\n"
    "  | .app f args => (args.attach.mapM (fun a => implementation_evalf a.1)).map (fun vs => f vs + 1)\n"
    "decreasing_by\n"
    "  have h := List.sizeOf_lt_of_mem a.2\n"
    "  simp only [Expr.app.sizeOf_spec]\n"
    "  omega"
)

# BARE-LEAF OFF-BY-ONE: mis-reduces a concrete numeric leaf by one; correct on
# every other constructor. Pins the `num` equation (the base case) that a
# composition-only attack would not touch.
_IMPL_NUM = (
    "def implementation_evalf : Expr → Option Int\n"
    "  | .num n  => some (n + 1)\n"
    "  | .atom   => none\n"
    "  | .app f args => Id.run do\n"
    "      let mut vals : List Int := []\n"
    "      for a in args.attach do\n"
    "        match implementation_evalf a.1 with\n"
    "        | some v => vals := vals ++ [v]\n"
    "        | none   => return none\n"
    "      return some (f vals)\n"
    "decreasing_by\n"
    "  have h := List.sizeOf_lt_of_mem a.2\n"
    "  simp only [Expr.app.sizeOf_spec]\n"
    "  omega"
)

# SYMBOLIC-LEAF: assigns a numeric value to a bare symbol that has none;
# correct on every other constructor. Pins the `atom` equation (a numeric value
# must NOT be invented for a symbol carrying none).
_IMPL_ATOM = (
    "def implementation_evalf : Expr → Option Int\n"
    "  | .num n  => some n\n"
    "  | .atom   => some 0\n"
    "  | .app f args => Id.run do\n"
    "      let mut vals : List Int := []\n"
    "      for a in args.attach do\n"
    "        match implementation_evalf a.1 with\n"
    "        | some v => vals := vals ++ [v]\n"
    "        | none   => return none\n"
    "      return some (f vals)\n"
    "decreasing_by\n"
    "  have h := List.sizeOf_lt_of_mem a.2\n"
    "  simp only [Expr.app.sizeOf_spec]\n"
    "  omega"
)

# AUDIT ADDITION — the two rivals below close the one dimension of the input the
# original battery never varied. Every pre-existing witness probes an application
# whose argument list has length 0 or 1 (`[.num 2]`, `[.app ...]`), and at length
# <= 1 the evaluated-argument LIST is determined by its single element: a rival
# may drop an argument, or mis-handle the empty list, and still agree with the
# spec at every point the battery looked at. So the `app` equation's claim about
# the LIST it hands to the node implementation (every argument, in order) was
# only demonstrated for a one-element list. Both are refuted at a 2-argument
# application with a POSITION-SENSITIVE node implementation (`10*x0 + x1`), which
# is what makes arity and order observable.

# ARITY / EMPTY-APPLICATION: correct at every application with at least one
# argument, but a no-argument application is reported as having no numeric value.
# The spec's `mapM` over an EMPTY argument list is `some []`, so a zero-argument
# node must still evaluate (to `f []`). Pins the empty-list end of the `app`
# equation, which every length>=1 witness leaves open.
_IMPL_EMPTY = (
    "def implementation_evalf : Expr → Option Int\n"
    "  | .num n  => some n\n"
    "  | .atom   => none\n"
    "  | .app f args => if args.isEmpty then none else\n"
    "      (args.attach.mapM (fun a => implementation_evalf a.1)).map f\n"
    "decreasing_by\n"
    "  have h := List.sizeOf_lt_of_mem a.2\n"
    "  simp only [Expr.app.sizeOf_spec]\n"
    "  omega"
)

# DROPPED-FIRST-ARGUMENT: evaluates the arguments correctly but hands the node
# implementation the TAIL of the evaluated list, silently discarding the first
# argument. Indistinguishable from gold on any single-argument application (the
# tail of a 1-element list feeds `f []`... only when the node ignores its input),
# so this is precisely the rival a length<=1 battery cannot see. Pins "the node
# implementation receives EVERY evaluated argument".
_IMPL_DROP1 = (
    "def implementation_evalf : Expr → Option Int\n"
    "  | .num n  => some n\n"
    "  | .atom   => none\n"
    "  | .app f args => (args.attach.tail.mapM (fun a => implementation_evalf a.1)).map f\n"
    "decreasing_by\n"
    "  have h := List.sizeOf_lt_of_mem a.2\n"
    "  simp only [Expr.app.sizeOf_spec]\n"
    "  omega"
)


# ---------------------------------------------------------------------------
# Witnesses. Each states `¬ problem_spec_evalf e (implementation_evalf e)` at a
# concrete input, unfolds the spec + impl + traversal machinery with a fixed
# `simp only` set, and closes the residual (in)equality with `decide`. Built
# against the rival (must succeed) and against gold (must fail).
# ---------------------------------------------------------------------------

# `mysqW` is the witness's own strict node implementation (v ↦ v*v). Declared
# inside the witness, so it is present in both the rival and gold builds.
_MYSQ = "def mysqW : List Int → Int := fun xs => xs.headD 0 * xs.headD 0\n\n"

_APP_SIMP = (
    "  simp only [evalSpec, implementation_evalf, List.attach_cons, List.attach_nil,\n"
    "    List.mapM_cons, List.mapM_nil, List.map, Option.map, mysqW, List.headD,\n"
    "    Id.run, List.forIn_cons, List.forIn_nil]\n"
    "  decide"
)
_LEAF_SIMP = (
    "  simp only [evalSpec, implementation_evalf]\n"
    "  decide"
)

# nested application f(f(2)): refutes the PRE-PATCH rival (which returns none).
_WIT_PRE = (
    _MYSQ
    + "example : ¬ problem_spec_evalf (.app mysqW [.app mysqW [.num 2]])\n"
    + "    (implementation_evalf (.app mysqW [.app mysqW [.num 2]])) := by\n"
    + "  unfold problem_spec_evalf\n"
    + _APP_SIMP
)

# one-layer application f(2): refutes the OFF-BY-ONE rival (returns 5, want 4).
_WIT_OBO = (
    _MYSQ
    + "example : ¬ problem_spec_evalf (.app mysqW [.num 2])\n"
    + "    (implementation_evalf (.app mysqW [.num 2])) := by\n"
    + "  unfold problem_spec_evalf\n"
    + _APP_SIMP
)

# bare numeric leaf: refutes the BARE-LEAF rival (returns 3, want 2).
_WIT_NUM = (
    "example : ¬ problem_spec_evalf (.num 2)\n"
    "    (implementation_evalf (.num 2)) := by\n"
    "  unfold problem_spec_evalf\n"
    + _LEAF_SIMP
)

# bare symbol: refutes the SYMBOLIC-LEAF rival (returns some 0, want none).
_WIT_ATOM = (
    "example : ¬ problem_spec_evalf (.atom)\n"
    "    (implementation_evalf (.atom)) := by\n"
    "  unfold problem_spec_evalf\n"
    + _LEAF_SIMP
)

# `mypairW` is a POSITION-SENSITIVE node implementation (x0, x1 ↦ 10*x0 + x1).
# Position sensitivity is what makes the argument list's arity and ORDER
# observable: with a symmetric node implementation (`v ↦ v*v` above) a rival that
# reorders or drops arguments could still agree with the spec, so the two
# argument-list rivals need their own node implementation rather than reusing
# `mysqW`. Declared inside the witness, so it exists in both builds.
_MYPAIR = ("def mypairW : List Int → Int :=\n"
           "  fun xs => xs.headD 0 * 10 + xs.tail.headD 0\n\n")

# The traversal-reduction set for a 2-argument application; `List.tail` and the
# append lemmas are needed on top of the 1-argument set because the evaluated
# list is genuinely built up here.
_PAIR_SIMP = (
    "  simp only [evalSpec, implementation_evalf, List.attach_cons, List.attach_nil,\n"
    "    List.mapM_cons, List.mapM_nil, List.map, Option.map, mypairW, List.headD,\n"
    "    List.tail, List.isEmpty, Id.run, List.forIn_cons, List.forIn_nil,\n"
    "    List.append, List.nil_append, List.cons_append]\n"
    "  decide"
)

# ZERO-argument application: the spec's `mapM` over `[]` is `some []`, so the
# node implementation still runs and the value is `f [] = 0*10 + 0 = 0`. Refutes
# the ARITY rival, which reports no numeric value there.
_WIT_EMPTY = (
    _MYPAIR
    + "example : ¬ problem_spec_evalf (.app mypairW [])\n"
    + "    (implementation_evalf (.app mypairW [])) := by\n"
    + "  unfold problem_spec_evalf\n"
    + _PAIR_SIMP
)

# TWO-argument application f(2, 5): the spec demands `some 25` (10*2 + 5), while
# a rival that discards the first argument computes `f [5] = 10*5 + 0 = 50`.
# Refutes the DROPPED-FIRST-ARGUMENT rival at the first arity where dropping is
# observable at all.
_WIT_DROP1 = (
    _MYPAIR
    + "example : ¬ problem_spec_evalf (.app mypairW [.num 2, .num 5])\n"
    + "    (implementation_evalf (.app mypairW [.num 2, .num 5])) := by\n"
    + "  unfold problem_spec_evalf\n"
    + _PAIR_SIMP
)


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS positive — a structurally different but CORRECT impl that MUST
    # verify. The arguments are accumulated in REVERSE order and the accumulator
    # is re-reversed before the node implementation is applied; behaviourally
    # identical at every input, but the loop's intermediate state differs from
    # gold's at every step past the first, so the obligation needs its own loop
    # lemma. The `theorem correct_evalf` STATEMENT is byte-identical, the proof
    # is retuned to the reshaped form, and no new axiom / `sorry` / assumption
    # token is introduced. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-reverse-accumulator",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL_GOLD, _IMPL_FUN),
                        _PROOF_GOLD, _PROOF_FUN),
        "rationale": (
            "a correct reshape that accumulates the evaluated arguments in "
            "REVERSE order (`v :: vals`) and re-reverses before applying the "
            "node implementation must satisfy `result = evalSpec e` at every "
            "input; if it cannot, a structurally different correct impl is "
            "rejected (SPEC-TOO-STRONG). This shape was chosen over a bare "
            "`mapM` reshape deliberately: the `mapM` form is the `evalSpec` app "
            "equation verbatim up to renaming, so its obligation collapses to "
            "the oracle's own defining equation and demonstrates only that the "
            "spec accepts a copy of itself. Here the loop is retained but its "
            "invariant genuinely differs — the closed form carries "
            "`acc.reverse ++ vs` where gold's carries `acc ++ vs` — so a real "
            "reshape is being admitted. Proof: a new `loop_eq_mapM` lemma plus the "
            "same pointwise `mapM` congruence; no new axiom or assumption "
            "token, and the theorem STATEMENT is byte-identical."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY positive — confirms the obligation is SATISFIABLE
    # (non-vacuous) at the F2P-shaped input. The frozen theorem carries NO
    # precondition hypothesis (the behavior is total, so `∀` is unguarded), so
    # nagini's precondition-admission probe has no binder to attack; the honest
    # analogue is to discharge the spec predicate at the F2P ground input (a
    # NESTED application over a numeric leaf) inside the proof region, alongside
    # the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-f2p-nested-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_INTRO, _ADMISS_INTRO),
        "rationale": (
            "the obligation is discharged at the F2P ground input (a nested "
            "application `f (f 2)` with the strict node implementation `v ↦ v*v`, "
            "so both layers must be evaluated to reach `16`) by `decide` over the "
            "reduced traversal, then the frozen obligation is closed verbatim. "
            "Verifies (else the spec is unsatisfiable at the normal input, the "
            "analogue of PRECOND-TOO-STRONG). Nothing is assumed: the theorem "
            "STATEMENT is byte-identical, the ground instance is a `have` inside "
            "the existing tactic body, and no new declaration/axiom/`sorry` is "
            "introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P/P2P suite, so a verifying
    # rival would be a true verify-does-not-imply-resolve break rather than an
    # artifact, and (b) a refutation witness pinning the violation at one
    # concrete input.
    # =====================================================================
    {
        "id": "weak-unevaluated-nested-arg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_PRE),
        "refinement": (
            "this IS the pre-fix behavior: an application takes a numeric value "
            "only from arguments that are ALREADY concrete numbers, so a nested "
            "application argument is left without a value and the whole "
            "expression stays symbolic. On the F2P observable — a strict node "
            "applied to a one-layer application of itself over the leaf 2, i.e. "
            "`f (f 2)` — it produces no number (the spec value is 16). It is "
            "EXACTLY the reported defect and does NOT resolve (the prepatch "
            "model fails here — G-DIFF)."
        ),
        "rationale": (
            "REJECT from the clause `result = evalSpec e`: at the nested "
            "application `.app f [.app f [.num 2]]` with `f = v ↦ v*v` the spec "
            "demands `some 16` (each layer is evaluated before the node "
            "implementation runs), but the rival aborts the outer application to "
            "`none` because its inner argument is not already a concrete number. "
            "Refuted on the nested-application sub-domain — the load-bearing `app` "
            "equation. If it verified, the spec would not force a nested argument "
            "to be evaluated first (SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_PRE,
    },
    {
        "id": "weak-offbyone-apply",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_OBO),
        "refinement": (
            "a patch that evaluates the arguments recursively but applies the "
            "node implementation to a value one too large (an off-by-one in the "
            "combination) computes a one-layer application `f 2` as 5 instead of "
            "4 and the nested `f (f 2)` as 17 instead of 16. The F2P assertion "
            "(`f (f 2)` numerically equals 16) and the single-argument numeric "
            "P2P paths fail, so such a patch does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = evalSpec e`: at the one-layer "
            "application `.app f [.num 2]` with `f = v ↦ v*v` the spec demands "
            "`some 4`, but the rival returns `some 5` (present, but the wrong "
            "number). Refuted on the apply-step of the `app` equation at a "
            "one-layer shape distinct from the nested witness — a pure value-pin "
            "violation. If it verified, the value produced by an application "
            "would be unpinned (SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_OBO,
    },
    {
        "id": "weak-bare-leaf-offbyone",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_NUM),
        "refinement": (
            "a patch that mis-reduces a bare concrete numeric leaf by one would "
            "report the leaf 2 as 3, breaking the no-argument / bare-numeric P2P "
            "paths (which evaluate plain numeric results) as well as every "
            "downstream application built on such a leaf; it would not resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = evalSpec e`: at the bare leaf "
            "`.num 2` the spec demands `some 2`, but the rival returns `some 3`. "
            "Refuted on the `num` equation (the base case) — the OTHER end of the "
            "domain from the application rivals, exercising the `num` constructor "
            "of the input binder. If it verified, the base case would be unpinned "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_NUM,
    },
    {
        "id": "weak-symbolic-leaf-invented",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ATOM),
        "refinement": (
            "a patch that invents a numeric value for a bare symbol carrying "
            "none would make a purely symbolic expression report a spurious "
            "number, breaking the symbolic-evaluation P2P paths (a symbol with no "
            "numeric implementation must stay symbolic); it would not resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = evalSpec e`: at the bare symbol "
            "`.atom` the spec demands `none` (a symbol has no numeric value), but "
            "the rival returns `some 0`. Refuted on the `atom` equation — the "
            "third constructor of the input binder, which the value-pin rivals "
            "do not touch. If it verified, the spec would not force a symbol to "
            "stay without a numeric value (SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_ATOM,
    },

    # =====================================================================
    # AUDIT ADDITIONS — the argument LIST itself. The four rivals above all probe
    # applications of arity <= 1, where the evaluated-argument list is pinned by
    # its single element. The `app` equation additionally claims that the node
    # implementation receives EVERY evaluated argument IN ORDER, and that claim
    # is only observable at arity 0 (does a no-argument node still evaluate?) and
    # arity >= 2 (are all the arguments there, in order?). Both rivals below are
    # correct at every input the original battery examined.
    # =====================================================================
    {
        "id": "weak-empty-application-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_EMPTY),
        "refinement": (
            "a patch that treats a no-argument application as having no numeric "
            "value would leave every zero-argument node with a numeric "
            "implementation unevaluated. The no-argument evaluation paths in the "
            "P2P suite (which evaluate such a node to its implementation's value) "
            "would report a symbolic result instead of a number, so it would not "
            "resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = evalSpec e`: at the zero-argument "
            "application `.app f []` the spec's argument traversal over the empty "
            "list is `some []`, so the node implementation still runs and the "
            "value is `some (f [])` — `some 0` for the witness's `10*x0 + x1`. "
            "The rival returns `none`. Refuted on the EMPTY-argument-list end of "
            "the `app` equation, which every arity>=1 witness leaves open. If it "
            "verified, the spec would permit a numeric node to stay unevaluated "
            "merely for taking no arguments (SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_EMPTY,
    },
    {
        "id": "weak-drops-first-argument",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_DROP1),
        "refinement": (
            "a patch that hands the node implementation only the tail of the "
            "evaluated argument list silently discards the first argument of "
            "every multi-argument application. Multi-argument evaluation paths in "
            "the P2P suite would compute from the wrong arguments (or raise on an "
            "arity mismatch), so it would not resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = evalSpec e`: at the two-argument "
            "application `.app f [.num 2, .num 5]` with the position-sensitive "
            "`f = x0, x1 ↦ 10*x0 + x1` the spec demands `some 25`, but the rival "
            "drops the leading argument and computes `f [5] = some 50`. Refuted "
            "on the ORDER-and-completeness content of the `app` equation at the "
            "first arity where dropping an argument is observable at all — the "
            "arity<=1 rivals above cannot distinguish this impl from the frozen "
            "one. If it verified, the spec would not force the node "
            "implementation to receive every evaluated argument (SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_DROP1,
    },
]


# No consumed axioms and no deep-model references: the numeric evaluation is
# modeled DEEPLY over the input (evalSpec is a spelled-out structural
# recursion), so there is no in-model axiom obligation for the PBT axiom lane to
# re-discharge. AXIOM_TESTS is empty.
AXIOM_TESTS = []
