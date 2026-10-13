# properties.py — G-PBT falsification battery for sympy__sympy-15345 (lean).
#
# A record of adversarially-reasoned cases the G-PBT gate executes and stamps
# with a verdict. Each SPEC_TESTS case is a full Solution.lean variant built by
# region surgery: ONLY text inside the # impl-start / # impl-end region (and,
# where a positive legitimately reproves, the -- proof-start / -- proof-end
# tactic body) is swapped, so the frozen spec is byte-for-byte preserved and
# `markers.same_spec` holds by construction. Every `theorem correct_*` STATEMENT
# is byte-identical to the frozen one in every case; no case adds an axiom, a
# helper lemma, a `sorry`/`admit`, or a `native_decide`.
#
# Defended surface of this instance
# ---------------------------------
# implementation_printApplication
#     {Expr : Type} (render : Expr → String) (funcName : String)
#     (args : List Expr) : String
#
#   Obligation: `theorem correct_printApplication` — an UNCONDITIONED
#       ∀ over all three inputs (no precondition hypothesis, so no input is
#       excluded, including the empty argument list).
#
#   Load-bearing postcondition (a single top-level clause, an equation that
#   pins the whole output with no free component):
#       result = funcName ++ "[" ++ renderArgs render args ++ "]"
#     where renderArgs render args = String.intercalate ", " (args.map render).
#
#   Unfolding that one clause names four independently attackable ingredients,
#   and this battery attacks each:
#     (a) the CALL DELIMITERS — the opening and closing bracket literals;
#     (b) the SEPARATOR between adjacent rendered fragments: its exact CONTENT
#         (both by deletion and by a same-length permutation of its characters),
#         and the fact that it appears strictly BETWEEN them (no leading or
#         trailing occurrence);
#     (c) which fragments fill the list, in WHICH ORDER, and that ALL of them
#         appear;
#     (d) the LEADING textual name, and that it is the name rather than
#         anything else that precedes the bracketed list;
#     (e) that each fragment is `render` APPLIED TO THAT ARGUMENT — a claim about
#         the quantified function parameter rather than about a literal or a
#         position, so it survives every rival that only permutes or truncates
#         the fragment list and needs rivals of its own. It takes TWO, because
#         the clause makes two separable demands: that a fragment is a `render`
#         image at all (attacked by `weak-render-ignored`, whose fragments are
#         constants) and that fragment i is the image of the I-TH argument
#         (attacked by `weak-wrong-arg-per-position`, whose fragments are all
#         genuine `render` images of one and the same argument, so the first
#         rival's refutation says nothing about it).
#
# Carrier notes vs. the nagini sibling
# ------------------------------------
# The nagini model carries the text as `PSeq[int]` code points and re-implements
# the join as an explicit back-to-front fold with loop invariants; this backend
# carries it as Lean `String` with the join expressed as a total `String.intercalate`
# over `args.map render`. So the nagini rivals that attack the FOLD's bookkeeping
# and the nagini positives that reshape it lose their fold to attack, but each
# one's ARGUMENT (which ingredient of the rendered text it corrupts) ports
# directly onto the intercalate carrier, and that is what is carried over below.
#
# `render` is a UNIVERSALLY QUANTIFIED function parameter, not an `opaque`
# constant, so a witness may instantiate it with a concrete literal function and
# `decide` the resulting closed String equation. Eleven of the twelve rival witnesses
# do exactly that: they state the negated spec predicate at literal inputs and bind
# nothing, so none can be vacuous by contradictory hypotheses (the gate's
# consistency probe is `None` for them, there being no assumption to be
# inconsistent). `weak-nonterminating` is the one exception and needs a different
# technique, because its impl is a `partial def` whose value NO tactic can reduce;
# see that case.
#
# One nagini class has no counterpart here and is NOT substituted for:
#   * frame/permission mutation — Lean is referentially transparent; both inputs
#     are immutable values and there is no fractional-permission analogue. The
#     class is VACUOUS on this backend.
#
# The DIVERGENCE class, by contrast, IS shippable here and is now shipped
# (`weak-nonterminating`, the port of nagini's `weak-nonterminating`). An earlier
# revision of this manifest recorded it as unshippable on the stated ground that
# "Lean's own termination checker refuses a non-terminating impl, so the rival
# cannot be written past the elaborator". That ground is FALSE, and the falsity is
# machine-checked: it holds only for a plain `def` (a bare self-call fails with
# `fail to show termination for spin ... failed to infer structural recursion`),
# but `partial def` elaborates without complaint — Lean admits it by supplying an
# `Inhabited` default rather than a measure — and `variant_scope` does not ban
# `partial` in the impl region. So a diverging renderer is expressible, the frozen
# obligation rejects it, and its rejection is attributable by a witness. See the
# case's own comment for the witness technique the opaque carrier forces.
#
# This is a bundle-local disposition, not a claim about the class in general: the
# divergence lane IS a live spec hole on the velvet backend under
# `set_option loom.semantics.termination "partial"`, where a diverging impl
# verifies vacuously. That is measured and recorded in the corpus-wide termination-semantics finding
# (401 velvet bundles; lean and nagini unaffected), so it is cited rather than
# re-derived here. This frozen solution sets no `loom.semantics.termination`
# option at all — it is a lean bundle, whose `theorem correct_*` obligation is
# discharged by an explicit tactic script over a total carrier — so the diverging
# rival is genuinely REJECTED rather than vacuously admitted.
# The axiom lane is G-AX's job and is ignored by this gate, so AXIOM_TESTS = [].
from pathlib import Path

INSTANCE = "sympy__sympy-15345"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region-surgery anchors. Each lies ENTIRELY inside the region it edits and is
# unique in the frozen file, so drift in any other region breaks this manifest
# loudly rather than silently relocating an edit.
# ---------------------------------------------------------------------------

# The gold impl BODY (inside # impl-start / # impl-end). Anchor for every rival:
# they all keep the frozen declaration header and change only what it returns.
_GOLD_BODY = '  return funcName ++ "[" ++ renderArgs render args ++ "]"\n'

# The gold impl DECLARATION, header included. Anchor for the positives that
# reshape the declaration itself (dropping the monadic wrapper, accumulating
# imperatively, splitting on the argument list).
_GOLD_DECL = (
    "def implementation_printApplication\n"
    "    {Expr : Type}\n"
    "    (render : Expr → String) (funcName : String) (args : List Expr)"
    " : String := Id.run do\n"
    + _GOLD_BODY
)

# The frozen proof's closing tactic (inside -- proof-start / -- proof-end). Only
# the case whose impl shape needs a different closer touches this; the
# `theorem correct_printApplication` STATEMENT is never edited.
_GOLD_CLOSER = "  rfl\n"


def _rival(body: str) -> str:
    """A variant that changes ONLY the returned expression."""
    return _swap(_BASE, _GOLD_BODY, body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# Each carries a proof that actually closes for its own impl shape, with the
# obligation statement untouched. Confirmed by real builds.
#
# Not all positives are equal evidence, and the set is chosen so that at least one
# is not cheap: `pos-direct-template` and `pos-accumulate` are definitionally
# equal to the frozen body (the frozen `rfl` still closes them), so they test that
# the equation accepts a re-SPELLING, which is the weakest form of the
# SPEC-TOO-STRONG question. `pos-foldr-fragments` is the one that is NOT defeq —
# its equality to the template needs a bridging induction — and it is the case
# that would actually catch an equation too rigid to admit correct code written
# another way.
# ---------------------------------------------------------------------------

# pos-direct-template: the cheapest honest impl. Drops the monadic `Id.run do`
# wrapper and returns the template splice as a plain expression. This is not an
# ungrounded echo: the spec's right-hand side is fully a function of the three
# inputs (the separator and the delimiters are literals, and every fragment is
# `render` applied to an actual argument), so producing it IS doing the work. If
# this were rejected, the equation would be SPEC-TOO-STRONG — it would refuse a
# correct output. The frozen closer still discharges it.
_POS_DIRECT = (
    "def implementation_printApplication\n"
    "    {Expr : Type}\n"
    "    (render : Expr → String) (funcName : String) (args : List Expr)"
    " : String :=\n"
    '  funcName ++ "[" ++ renderArgs render args ++ "]"\n'
)

# pos-accumulate: a STRUCTURALLY DIFFERENT correct impl. Instead of one splice
# expression it builds the output by successive mutation of a local accumulator —
# name first, then the opening delimiter, then the fragment list, then the
# closing delimiter — mirroring an imperative renderer that emits the template
# piecewise. Same value, different shape; must verify or the equation is
# SPEC-TOO-STRONG. This is the port of nagini's `pos-branch-reorder` argument
# ("a faithful correct impl written another way must still verify"), re-expressed
# on a carrier that has no fold to reorder.
_POS_ACC = (
    "def implementation_printApplication\n"
    "    {Expr : Type}\n"
    "    (render : Expr → String) (funcName : String) (args : List Expr)"
    " : String := Id.run do\n"
    "  let inner := renderArgs render args\n"
    "  let mut out := funcName\n"
    '  out := out ++ "["\n'
    "  out := out ++ inner\n"
    '  out := out ++ "]"\n'
    "  return out\n"
)

# pos-foldr-fragments: the positive that carries the SPEC-TOO-STRONG weight, and
# the reason it is here rather than left to the two above. Both of those are
# DEFINITIONALLY equal to the frozen body — the frozen `rfl` discharges them
# unchanged, which is honest but means the equation was never asked to accept a
# value-equal impl it cannot see through. This one builds the fragment list by an
# explicit `List.foldr` instead of `List.map`, so the two sides are equal only up
# to a lemma: `rfl` does NOT close it (the analogous reverse-roundtrip reshape
# fails with "is not definitionally equal to the right-hand side" under the frozen
# closer), and the proof has to supply the bridging induction itself. A faithful
# correct impl whose equality to the template needs a proof rather than a
# reduction must still verify, else the equation is SPEC-TOO-STRONG in the way
# that actually bites: rejecting correct code for its shape.
_POS_FOLDR = (
    "def implementation_printApplication\n"
    "    {Expr : Type}\n"
    "    (render : Expr → String) (funcName : String) (args : List Expr)"
    " : String :=\n"
    '  funcName ++ "[" ++ String.intercalate ", "\n'
    "    (args.foldr (fun a acc => render a :: acc) []) ++ \"]\"\n"
)
_POS_FOLDR_CLOSER = (
    "  have key : ∀ (l : List Expr),\n"
    "      l.foldr (fun a acc => render a :: acc) [] = l.map render := by\n"
    "    intro l; induction l with\n"
    "    | nil => rfl\n"
    "    | cons a t ih => simp [ih]\n"
    "  simp [renderArgs, key]\n"
)

# admiss-empty-arg-list: an admissibility positive at the boundary input.
# The obligation here is UNCONDITIONED — unlike the nagini contract, it carries
# no "at least one argument" hypothesis — so the spec must be dischargeable on
# the empty argument list too, where the fragment list degenerates to the empty
# string and the output is the bare name plus an empty pair of delimiters. This
# impl splits the domain explicitly and handles that boundary in its own branch;
# the proof closes both arms by case analysis. If the empty-list arm could not be
# discharged, the obligation would be unsatisfiable on part of its own declared
# domain (the lean analogue of nagini's PRECOND-TOO-STRONG finding).
_ADMISS_EMPTY = (
    "def implementation_printApplication\n"
    "    {Expr : Type}\n"
    "    (render : Expr → String) (funcName : String) (args : List Expr)"
    " : String := Id.run do\n"
    "  match args with\n"
    '  | [] => return funcName ++ "[" ++ "" ++ "]"\n'
    '  | a :: rest => return funcName ++ "[" ++ renderArgs render (a :: rest)'
    ' ++ "]"\n'
)
_ADMISS_CLOSER = (
    "  cases args with\n"
    "  | nil => rfl\n"
    "  | cons a rest => rfl\n"
)

# admiss-f2p-satisfiable: the second admissibility direction, and the one an
# unconditioned obligation still needs. `admiss-empty-arg-list` shows the spec is
# dischargeable at the DEGENERATE end of its domain; this shows the obligation is
# SATISFIABLE — not vacuously true — at concrete inputs shaped like the ones the
# real oracle exercises (a three-argument and a two-argument application, the two
# arities that oracle pins).
#
# On a total carrier the PRECOND-TOO-STRONG analogue is not a rejected
# precondition — there is none to reject — but the obligation being unsatisfiable
# at exactly an F2P-shaped input: a postcondition no output could meet there would
# leave `correct_printApplication` provable only if the impl were also unrealisable,
# and the gate would never notice, because every positive it runs proves the
# ∀-statement rather than exhibiting a witness at a point. So this case discharges
# the spec predicate BY EVALUATION at those two concrete points, as `have`s naming
# the expected text OUTRIGHT, before closing the frozen obligation verbatim. The
# impl is untouched; only the proof adds the two boundary checks.
#
# The `have`s are load-bearing rather than decorative, and that is checkable: the
# same case with a deliberately wrong expected text at arity 3 FAILS, with
# `decide` reporting the concrete equation false. So each `have` pins the exact
# rendered text at its input, and a spec that could not deliver it there would
# fail this case rather than pass it.
_ADMISS_F2P_CLOSER = (
    "  have admissible_at_arity3 :\n"
    "      problem_spec_printApplication (fun (s : String) => s) \"Fn\"\n"
    "        [\"u\", \"v\", \"w\"] \"Fn[u, v, w]\" := by\n"
    "    unfold problem_spec_printApplication renderArgs\n"
    "    decide\n"
    "  have admissible_at_arity2 :\n"
    "      problem_spec_printApplication (fun (s : String) => \"<\" ++ s ++ \">\")\n"
    "        \"Gn\" [\"v\", \"w\"] \"Gn[<v>, <w>]\" := by\n"
    "    unfold problem_spec_printApplication renderArgs\n"
    "    decide\n"
    + _GOLD_CLOSER
)


def _positive(decl: str, closer: str | None = None) -> str:
    src = _swap(_BASE, _GOLD_DECL, decl)
    if closer is not None:
        src = _swap(src, _GOLD_CLOSER, closer)
    return src


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS (wrong impl sharing the frozen spec) — must REJECT.
#
# The publicly stated defect is that this application class was rendered with
# the GENERIC parenthesized call form instead of the target language's
# square-bracket call template, and the F2P test pins the exact rendered text of
# a two-factor product of two such applications. So every rival below is checked
# against the same bar: would its faithful real patch still produce that exact
# text? Each `refinement` answers no, and names the character of the output it
# corrupts.
#
# Each rival also ships a `witness`: a snippet stating the frozen spec predicate
# at ONE concrete input, negated. Verified by real builds to ELABORATE against
# the rival (so the rejection is attributable to the postcondition, not to the
# frozen tactic script failing to match a reshaped impl) and to FAIL against the
# frozen solution (so it discriminates rather than asserting a tautology). For the
# eleven rivals whose output is a closed String expression, gold fails with `decide`
# reporting the negation FALSE — i.e. gold satisfies the spec at exactly that
# input. `weak-nonterminating` is the exception: its output is irreducible, so its
# witness refutes by functional dependence and its gold-side failure is a
# `rewrite` failure — gold's two instantiations have DIFFERENT left-hand sides, so
# the pattern `hA` rewrites by does not occur in `hB`'s goal. Each of these
# gold-side failures was re-derived with the claim FLIPPED (assert the predicate
# rather than its negation): the exit codes invert, gold 0 / rival 1, so each
# gold-side exit code carries information about the claim rather than being a
# constant artifact of the surgery.
#
# The witnesses deliberately move all three input binders across the set, so no
# rival could hide in a binder the battery holds fixed: `render` takes an
# identity fragment renderer and two different decorating ones, `funcName` takes
# eight distinct names plus one point where it is left QUANTIFIED (the divergence
# witness, which needs two instantiations of it at once), and `args` takes lists
# of length 0, 1, 2 and 3 — the 0 case mattering because the obligation is
# unconditioned and so covers it. Twelve distinct input points in total.
#
# One of the four ingredients needs a rival that attacks the BINDER rather than
# the template, and it is `render`: ingredients (a), (b) and (d) are literals or
# positions, but "each fragment is `render` APPLIED TO THAT ARGUMENT" is a claim
# about a quantified function parameter. A rival that emits the right NUMBER of
# fragments, correctly separated, correctly delimited and correctly named, but
# does not pass the arguments through `render` at all, corrupts nothing the other
# rivals corrupt — so `weak-render-ignored` carries that lane. Likewise
# ingredient (b) is attacked by DELETION (`weak-separator-no-space`) and by
# MISPLACEMENT (`weak-trailing-separator`), but not by a same-length permutation
# of the separator's own characters; `weak-separator-transposed` closes that.
#
# Two further lanes are neither an ingredient of the template nor a binder, and
# each needs its own rival:
#   * the DEGENERATE ARITY. The obligation is unconditioned, so it covers the empty
#     argument list, but every template-ingredient rival is either correct there or
#     wrong across arities generally, so none attributes anything to that point.
#     `weak-nullary-bare-name` is wrong at exactly arity 0 and correct elsewhere,
#     making it the reject-lane mirror of `admiss-empty-arg-list`.
#   * DELIVERY of any output at all, as opposed to the content of the output
#     delivered. `weak-nonterminating` carries that lane; see its comment for why
#     it is expressible here and how its witness works on an irreducible carrier.
# ---------------------------------------------------------------------------

_WITNESS_TAIL = (
    "  unfold problem_spec_printApplication implementation_printApplication"
    " renderArgs\n"
    "  decide\n"
)


def _witness(render: str, name: str, args: str) -> str:
    """Negate the frozen spec predicate at one concrete, `decide`-able input.

    `render` is a quantified function parameter rather than an opaque constant,
    so instantiating it with a literal function closes the term completely and
    the resulting String equation decides.
    """
    return (
        "example : ¬ problem_spec_printApplication\n"
        f"    {render} {name} {args}\n"
        f"    (implementation_printApplication {render} {name} {args}) := by\n"
        + _WITNESS_TAIL
    )


_ID_RENDER = "(fun (s : String) => s)"
_ANGLE_RENDER = '(fun (s : String) => "<" ++ s ++ ">")'
_ROUND_RENDER = '(fun (s : String) => "(" ++ s ++ ")")'

# weak-generic-delimiters: the canonical discriminating delta (== the frozen
# Solution_prepatch impl). Same name, same fragment list, same separators —
# only the surrounding call delimiters become the generic rounded pair.
_WEAK_DELIMS = '  return funcName ++ "(" ++ renderArgs render args ++ ")"\n'

# weak-separator-no-space: the separator loses its trailing space, so adjacent
# fragments are divided by the bare punctuation mark alone.
_WEAK_SEP = ('  return funcName ++ "[" ++ String.intercalate ","'
             " (args.map render)"
             ' ++ "]"\n')

# weak-trailing-separator: a right fold that emits the separator AFTER every
# fragment rather than only between adjacent ones, so the list closes with a
# dangling separator (and a single-argument application gains one too).
_WEAK_TRAILING = ('  return funcName ++ "[" ++ (args.map render).foldr'
                  ' (fun s acc => s ++ ", " ++ acc) ""'
                  ' ++ "]"\n')

# weak-reversed-order: every fragment present and correctly separated, but the
# argument positions are emitted back to front.
_WEAK_REVERSE = '  return funcName ++ "[" ++ renderArgs render args.reverse ++ "]"\n'

# weak-drop-first-arg: the leading argument is omitted from the fragment list.
# A partial-domain attack, and a near-miss in that it still gets the delimiters,
# the separator placement and the order of everything it does emit right. It is
# wrong at every arity >= 1 for a renderer that separates the fragments it is
# given, but NOT for every (render, args) pair of that shape: under a renderer
# that collapses every argument to the same fragment the two outputs can coincide
# (measured at the witness's own arity, with the name CONCRETE — `"Fn" ++ "[" ++
# renderArgs (fun _ => "") (["a"].drop 1) ++ "]" = "Fn" ++ "[" ++ renderArgs
# (fun _ => "") ["a"] ++ "]"` closes by `decide`, while the same equation under
# the identity renderer is refuted by `decide`), which is why the witness below
# fixes a renderer that does not collapse. The name has to be a literal for that
# measurement: with `funcName` left free, `decide` does not report the equation
# either way but fails with `Expected type must not contain free variables`, so
# the collapse is a statement about concrete points, not a closed ∀.
_WEAK_DROP_FIRST = ('  return funcName ++ "[" ++ renderArgs render (args.drop 1)'
                    ' ++ "]"\n')

# weak-drop-name: the bracketed fragment list is correct in every detail but the
# leading textual name is not emitted at all — the frame-discipline attack on the
# one output component that is not part of the argument list.
_WEAK_NO_NAME = '  return "[" ++ renderArgs render args ++ "]"\n'

# weak-first-arg-only: renders just the leading argument and discards the rest,
# so the separator never appears. Distinguished from weak-drop-first-arg (which
# keeps the tail) by probing a three-argument application.
_WEAK_FIRST_ONLY = (
    "  match args with\n"
    '  | [] => return funcName ++ "[" ++ "" ++ "]"\n'
    '  | a :: _ => return funcName ++ "[" ++ render a ++ "]"\n'
)

# weak-render-ignored: the fragment list has the right LENGTH, the right
# separators and the right delimiters, and the name is right — but the arguments
# are never passed through the per-argument renderer at all; every fragment is a
# constant. The only rival that attacks the `render` BINDER rather than the
# template's literals or positions.
_WEAK_NO_RENDER = ('  return funcName ++ "[" ++ String.intercalate ", "'
                   ' (args.map (fun _ => "x"))'
                   ' ++ "]"\n')

# weak-wrong-arg-per-position: every fragment is `render` applied to the LAST
# argument, whatever position it occupies. This is the second lane on ingredient
# (e) and it is not the one `weak-render-ignored` covers. That rival emits a
# CONSTANT per argument, so it is refuted by "the fragments are not constants";
# this one genuinely calls `render`, on a genuine element of `args`, and emits the
# right number of correctly separated fragments under the right name inside the
# right delimiters — so every argument that refutes weak-render-ignored passes it.
# What it corrupts is the POSITIONAL pairing `args.map render` pins: fragment i
# must be `render` applied to the i-th argument, not to some argument. That is
# also distinct from weak-reversed-order and the two truncating rivals, which all
# preserve the pairing on the fragments they do emit and corrupt only which
# positions survive or in what order. Its faithful real counterpart renders one
# argument repeatedly instead of each in turn, so a multi-argument application
# comes out with the wrong fragments and the pinned text is not produced — it
# resolves nothing.
#
# This one swaps the DECLARATION rather than only the body, because its `match`
# arm needs a continuation line: inside the frozen `Id.run do` wrapper a wrapped
# `| z :: _ => return ...` arm makes the second line a fresh `do` element, which
# Lean reports as `do element is unreachable` after the `return` (measured — the
# body-swap form fails the witness's own rival build for that syntactic reason,
# not for anything about the spec). Dropping the monadic wrapper, exactly as the
# `pos-direct-template` positive does, removes the ambiguity while leaving the
# frozen declaration header and the obligation statement untouched.
_WEAK_WRONG_ARG_DECL = (
    "def implementation_printApplication\n"
    "    {Expr : Type}\n"
    "    (render : Expr → String) (funcName : String) (args : List Expr)"
    " : String :=\n"
    "  match args.reverse with\n"
    '  | [] => funcName ++ "[" ++ "" ++ "]"\n'
    '  | z :: _ => funcName ++ "[" ++ String.intercalate ", "\n'
    "      (args.map (fun _ => render z)) ++ \"]\"\n"
)

# weak-separator-transposed: the separator's two characters in the opposite
# order. The tightest near-miss on ingredient (b) available: same length, same
# character multiset, separator still strictly between adjacent fragments — so it
# survives every length- or placement-based argument and is caught only by the
# separator's exact content.
_WEAK_SEP_SWAP = ('  return funcName ++ "[" ++ String.intercalate " ,"'
                  " (args.map render)"
                  ' ++ "]"\n')

# weak-nullary-bare-name: the delimiters are dropped for the DEGENERATE arity —
# an argument-less application is rendered as the bare name with no bracket pair
# at all, while every other arity is rendered correctly. This closes the one
# sub-domain the rest of the reject lane leaves unattacked: the obligation is
# unconditioned and so covers the empty argument list, `admiss-empty-arg-list`
# asserts a correct impl is dischargeable THERE, and this rival is the matching
# negative showing the spec also REJECTS a wrong one there. Every other rival is
# either correct at arity 0 (weak-first-arg-only, weak-drop-first-arg) or wrong
# across arities generally, so none of them attributes anything to the empty-list
# point specifically. Its faithful real counterpart emits a name with no call
# syntax for a no-argument application, which is not the target language's call
# form, so it resolves nothing.
_WEAK_NULLARY = (
    "  match args with\n"
    "  | [] => return funcName\n"
    '  | a :: rest => return funcName ++ "[" ++ renderArgs render (a :: rest)'
    ' ++ "]"\n'
)

# weak-nonterminating: the divergence rival — the renderer never delivers any
# text. This is the port of nagini's `weak-nonterminating`, and it is shippable on
# this carrier, which an earlier revision of this manifest wrongly denied.
#
# Expressibility. A plain `def` with a bare self-call is indeed refused by Lean's
# termination checker (`fail to show termination for spinForever ... failed to
# infer structural recursion: Cannot use parameter n`), which is what the earlier
# revision measured and then over-generalised. But `partial def` elaborates
# without complaint — Lean admits it via an `Inhabited` default instead of a
# decreasing measure — and it is not among the tokens `variant_scope` bans
# (`sorry`/`sorryAx`/`admit`/`native_decide`/`Assume`/`Refute`), adds no theorem,
# no axiom and no helper lemma, and leaves the obligation statement byte-identical.
# So the rival is admissible surgery and the frozen obligation genuinely REJECTS
# it: `Tactic 'rfl' failed: The left-hand side spinForever 0 is not definitionally
# equal to the right-hand side funcName ++ "[" ++ renderArgs render args ++ "]"`.
#
# Its faithful real counterpart is a printer method that hangs: the rendering call
# would never return, so the pinned rendered text is never produced and the test
# that asserts it times out rather than passing. It resolves nothing.
_WEAK_NONTERM_DECL = (
    "partial def spinForever (n : Nat) : String := spinForever (n + 1)\n"
    "\n"
    "def implementation_printApplication\n"
    "    {Expr : Type}\n"
    "    (render : Expr → String) (funcName : String) (args : List Expr)"
    " : String :=\n"
    "  spinForever 0\n"
)

# The witness for it CANNOT be the shared `_witness` shape. Every other rival's
# output is a closed String expression that `decide` evaluates; `spinForever 0` is
# a `partial def`, so it has no reduction behaviour any tactic can appeal to and
# `decide` on the negated predicate at a literal input FAILS against the rival
# (measured: exit 1) — the half that must SUCCEED. That is a property of the
# carrier, not of the spec, and the standard technique for an irreducible carrier
# applies: refute WITHOUT reducing the term.
#
# The refutation used here needs no hypothesis at all. It negates the frozen spec
# predicate quantified over `funcName` alone — a strictly weaker statement than the
# obligation, so refuting it refutes the obligation — and derives the
# contradiction from FUNCTIONAL DEPENDENCE rather than from any value: the rival's
# output does not mention `funcName`, so instantiating at two distinct names gives
# the SAME left-hand side with two different required right-hand sides, and
# `"A[a]" = "B[a]"` is decidably false. `spinForever 0` is never evaluated; it is
# only used as an opaque term equal to itself. Because the witness head binds
# nothing, the gate's consistency probe is `None` and there are no assumptions that
# could be contradictory.
#
# Discrimination is real, and the gold-side failure is a SEMANTIC one about this
# claim rather than a tooling artifact. Measured, in both the required directions
# and the forgery direction:
#   * against the rival: exit 0 (the refutation goes through);
#   * against the frozen solution: exit 1 — `Tactic `rewrite` failed: Did not find
#     an occurrence of the pattern (pure ("A" ++ "[" ++ ", ".intercalate ... ++
#     "]")).run in the target expression (pure ("B" ++ ...)).run = "B" ++ ...`, i.e.
#     gold's two instances have DIFFERENT left-hand sides, so the `rw [hA] at hB`
#     the rival's `funcName`-independence enables has no occurrence to rewrite;
#   * FORGERY, claim flipped (assert the ∀ instead of its negation, closed by the
#     frozen `rfl`): gold exit 0, rival exit 1. Both exit codes invert with the
#     claim, so gold's exit code carries information ABOUT the claim.
#   * FORGERY, type revealed (`exact (hA : Nat)` in place of the final step): gold
#     prints `hA has type (pure ("A" ++ ...)).run = "A" ++ ...`, the rival prints
#     `hA has type spinForever 0 = "A" ++ ...`. Different hypothesis types on the
#     two sides, neither `True` — so no tactic silently proved the equation for
#     either impl, and the discrimination is about the impls' outputs.
_WEAK_NONTERM_WITNESS = (
    "example : ¬ (∀ (funcName : String),\n"
    "    problem_spec_printApplication (fun (s : String) => s) funcName"
    ' ["a"]\n'
    "      (implementation_printApplication (fun (s : String) => s) funcName"
    ' ["a"])) := by\n'
    "  intro h\n"
    '  have hA := h "A"\n'
    '  have hB := h "B"\n'
    "  unfold problem_spec_printApplication implementation_printApplication"
    " renderArgs at hA hB\n"
    "  rw [hA] at hB\n"
    "  exact absurd hB (by decide)\n"
)


SPEC_TESTS = [
    {
        "id": "pos-direct-template",
        "kind": "soundness",
        "expect": "verify",
        "module": _positive(_POS_DIRECT),
        "rationale": "Cheapest honest impl: returns the template splice as a "
                     "plain expression instead of through the monadic wrapper. "
                     "The spec's right-hand side is grounded — every component "
                     "is a literal or `render` applied to an actual argument — "
                     "so producing it IS doing the work, not echoing an "
                     "answer-key. Defends the single postcondition clause: if "
                     "this were rejected the equation would be SPEC-TOO-STRONG. "
                     "Obligation statement untouched; the frozen closer still "
                     "discharges it.",
    },
    {
        "id": "pos-accumulate",
        "kind": "soundness",
        "expect": "verify",
        "module": _positive(_POS_ACC),
        "rationale": "Structurally different but value-identical: builds the "
                     "output by successive mutation of a local accumulator "
                     "(name, opening delimiter, fragment list, closing "
                     "delimiter) rather than as one splice, mirroring an "
                     "imperative renderer emitting the template piecewise. A "
                     "faithful correct impl written another way must still "
                     "verify, else SPEC-TOO-STRONG. This is the port of the "
                     "nagini reordered-fold positive's argument onto a carrier "
                     "whose join is a single total intercalate with no fold to "
                     "reorder.",
    },
    {
        "id": "pos-foldr-fragments",
        "kind": "soundness",
        "expect": "verify",
        "module": _positive(_POS_FOLDR, _POS_FOLDR_CLOSER),
        "rationale": "The positive that carries the SPEC-TOO-STRONG weight. The "
                     "other two are DEFINITIONALLY equal to the frozen body — "
                     "the frozen `rfl` discharges them unchanged, so the "
                     "equation was never asked to accept a value-equal impl it "
                     "cannot see through. This one builds the fragment list by "
                     "an explicit `List.foldr` rather than `List.map`, so the "
                     "two sides agree only up to a lemma and the proof supplies "
                     "the bridging induction; `rfl` alone does not close it. A "
                     "faithful correct impl whose equality to the template needs "
                     "a proof rather than a reduction must still verify, else "
                     "the equation is SPEC-TOO-STRONG in the way that bites — "
                     "rejecting correct code for its shape. Obligation statement "
                     "untouched.",
    },
    {
        "id": "admiss-empty-arg-list",
        "kind": "admissibility",
        "expect": "verify",
        "module": _positive(_ADMISS_EMPTY, _ADMISS_CLOSER),
        "rationale": "The obligation is UNCONDITIONED (no hypothesis restricts "
                     "the inputs), so the spec must be dischargeable on the "
                     "empty argument list, where the fragment list degenerates "
                     "to the empty string and the output is the bare name plus "
                     "an empty delimiter pair. This impl splits the domain and "
                     "handles that boundary in its own branch; the proof closes "
                     "both arms by case analysis on the argument list, "
                     "obligation statement untouched. Verifies => the spec "
                     "admits every input in its own declared domain, boundary "
                     "included. The lean counterpart of the nagini "
                     "admissibility control, whose precondition excluded this "
                     "very input.",
    },
    {
        "id": "admiss-f2p-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_CLOSER, _ADMISS_F2P_CLOSER),
        "rationale": "The other admissibility direction: not that the domain's "
                     "degenerate end is admitted, but that the obligation is "
                     "SATISFIABLE — not vacuously true — at concrete inputs "
                     "shaped like the ones the real oracle exercises. Discharges "
                     "the spec predicate by EVALUATION at a three-argument and a "
                     "two-argument application, as `have`s naming the expected "
                     "rendered text outright, before closing the frozen "
                     "obligation verbatim; the impl is untouched. On a total "
                     "carrier this is the PRECOND-TOO-STRONG analogue: there is "
                     "no precondition to reject, so the failure mode is the "
                     "obligation being unmeetable at exactly an F2P-shaped "
                     "input, which no ∀-proving positive would expose. The "
                     "`have`s are load-bearing, not decorative: the same case "
                     "with a wrong expected text at arity 3 fails, with `decide` "
                     "reporting that concrete equation false.",
    },
    {
        "id": "weak-generic-delimiters",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_DELIMS),
        "refinement": "This is the pre-fix behavior verbatim (it reproduces the "
                      "frozen prepatch impl): the application is emitted with "
                      "the GENERIC rounded call delimiters instead of the target "
                      "language's square-bracket call template. That is exactly "
                      "the defect the issue reports — the reported wrong output "
                      "differs from the expected one in precisely these two "
                      "characters — and the F2P test pins the exact rendered "
                      "text with the bracket form. A faithful real patch with "
                      "this behavior changes nothing and would NOT resolve.",
        "rationale": "Rejected by the sole postcondition clause `result = "
                     "funcName ++ \"[\" ++ renderArgs render args ++ \"]\"`, "
                     "whose bracket literals are pinned: the rival's output "
                     "differs from the required text at the character following "
                     "the name and at the final character. Attacks ingredient "
                     "(a), the call delimiters. Witness probes a two-argument "
                     "application under the identity fragment renderer.",
        "witness": _witness(_ID_RENDER, '"Fn"', '["a", "2"]'),
    },
    {
        "id": "weak-separator-no-space",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_SEP),
        "refinement": "Divides adjacent fragments by the bare punctuation mark, "
                      "dropping the space that the constant separator carries. "
                      "The F2P test pins the rendered text of a product of two "
                      "multi-argument applications character for character, and "
                      "that expected text spaces its argument lists; a faithful "
                      "patch emitting the unspaced form would NOT resolve. (The "
                      "issue text's illustrative unspaced rendering is not the "
                      "oracle — the test is.)",
        "rationale": "Rejected by the postcondition clause via `renderArgs`, "
                     "which is pinned to intercalation by the two-character "
                     "constant separator; dropping its second character makes "
                     "the rival's output shorter than the required text for any "
                     "application with at least two arguments. Attacks "
                     "ingredient (b), the separator's content. Witness probes a "
                     "different two-argument list and a different name from "
                     "weak-generic-delimiters.",
        "witness": _witness(_ID_RENDER, '"Gn"', '["b", "c"]'),
    },
    {
        "id": "weak-trailing-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_TRAILING),
        "refinement": "Folds the separator in AFTER every fragment rather than "
                      "only between adjacent ones, so the argument list closes "
                      "with a dangling separator before the closing delimiter "
                      "(and even a one-argument application gains one). The F2P "
                      "test pins the exact text, which has no separator before "
                      "either closing delimiter, so a faithful patch with this "
                      "behavior would NOT resolve.",
        "rationale": "Rejected by the postcondition clause: `renderArgs` is "
                     "intercalation, which places the separator strictly "
                     "BETWEEN adjacent fragments and never after the last, so "
                     "the rival's output is strictly longer than the required "
                     "text. Attacks ingredient (b), the separator's placement — "
                     "the complementary half of what weak-separator-no-space "
                     "attacks, hence its own witness. Probed under a decorating "
                     "fragment renderer, which also confirms the separator "
                     "defect is not an artifact of identity-rendered fragments.",
        "witness": _witness(_ANGLE_RENDER, '"Hn"', '["b", "c"]'),
    },
    {
        "id": "weak-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_REVERSE),
        "refinement": "Emits every fragment, correctly separated and correctly "
                      "delimited, but with the argument positions back to front. "
                      "The argument order is fixed upstream and is identical "
                      "before and after the fix; the F2P test pins the "
                      "arguments in their given order, so a faithful patch that "
                      "reordered them would NOT resolve.",
        "rationale": "Rejected by the postcondition clause: `args.map render` "
                     "pins fragment i to the i-th argument, so the reversed "
                     "list differs from the required text whenever two "
                     "argument positions render differently. Attacks ingredient "
                     "(c), the ORDER of the fragments. Witness reuses the "
                     "argument list of weak-separator-no-space but under a "
                     "decorating renderer — order is only observable when the "
                     "fragments differ, and this pairs a distinct (render, "
                     "funcName, args) point.",
        "witness": _witness(_ROUND_RENDER, '"Gn"', '["b", "c"]'),
    },
    {
        "id": "weak-drop-first-arg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_DROP_FIRST),
        "refinement": "Omits the leading argument from the fragment list. The "
                      "F2P test pins applications of two and three arguments "
                      "with every argument present, so a faithful patch that "
                      "silently dropped the first would NOT resolve.",
        "rationale": "Rejected by the postcondition clause: `args.map render` "
                     "pins the fragment list to ALL arguments, so dropping one "
                     "leaves the rival short of the required text at every "
                     "non-empty input whose renderer distinguishes the dropped "
                     "fragment (under a renderer that maps every argument to the "
                     "same fragment the two outputs can coincide, so the witness "
                     "fixes the identity renderer, which does not). Attacks "
                     "ingredient (c), the COMPLETENESS "
                     "of the fragment list. A NEAR-MISS — it gets the "
                     "delimiters, the separator and the order of everything it "
                     "does emit right — so it is witnessed at the smallest "
                     "input that exposes it, a single-argument application, "
                     "where its output collapses to an empty argument list. "
                     "That is a strictly more discriminating point than the "
                     "multi-argument ones the other rivals use.",
        "witness": _witness(_ID_RENDER, '"Fn"', '["a"]'),
    },
    {
        "id": "weak-drop-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_NO_NAME),
        "refinement": "Emits a correct bracketed argument list but no leading "
                      "textual name. The F2P test pins the rendered text of "
                      "named applications, so a faithful patch omitting the "
                      "name would NOT resolve — and the omission is observable "
                      "independently of the delimiter fix this instance is "
                      "about.",
        "rationale": "Rejected by the postcondition clause's leading "
                     "`funcName ++`: the name is pinned as the output's prefix "
                     "and is the one output component that is not part of the "
                     "argument list, so leaving it out is the frame-discipline "
                     "hole this clause closes (an unpinned prefix would let a "
                     "rival put anything there). Attacks ingredient (d). "
                     "Witnessed on a one-argument application under a fourth "
                     "distinct name, so the funcName binder is moved rather "
                     "than held.",
        "witness": _witness(_ID_RENDER, '"Kn"', '["d"]'),
    },
    {
        "id": "weak-first-arg-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_FIRST_ONLY),
        "refinement": "Renders only the leading argument and discards the rest, "
                      "so no separator is ever emitted. The F2P test pins "
                      "applications of two and three arguments; a faithful "
                      "patch collapsing them to their first argument would NOT "
                      "resolve.",
        "rationale": "Rejected by the postcondition clause: the fragment list "
                     "is pinned to every argument joined by the separator, and "
                     "the rival emits exactly one fragment and no separator. "
                     "Attacks ingredient (c) from the opposite side of "
                     "weak-drop-first-arg — it keeps the head and drops the "
                     "tail, where that rival drops the head and keeps the tail "
                     "— so the two fail on different sub-domains and are "
                     "witnessed at different inputs. Probed on a THREE-argument "
                     "application: this rival first departs from the spec at "
                     "arity 2 (it is CORRECT at arity 0 and 1, where there is no "
                     "tail to discard), and arity 3 is where the fragment list "
                     "it drops is longer than the one it keeps — so the "
                     "sub-domain it fails on is exhibited with room to spare "
                     "rather than at its own boundary.",
        "witness": _witness(_ID_RENDER, '"Fn"', '["a", "b", "c"]'),
    },
    {
        "id": "weak-render-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_NO_RENDER),
        "refinement": "Emits one fragment per argument, correctly separated and "
                      "delimited, under the correct name — but the arguments "
                      "themselves never reach the per-argument renderer, so "
                      "every fragment is a constant. The F2P test pins the "
                      "rendered text of applications whose arguments render to "
                      "distinct fragments, so a faithful patch that emitted a "
                      "placeholder per argument would NOT resolve.",
        "rationale": "Rejected by the postcondition clause via `renderArgs`, "
                     "whose fragment list is `args.map render`: fragment i is "
                     "pinned to `render` APPLIED TO the i-th argument, not "
                     "merely to some string per argument. Attacks the `render` "
                     "BINDER — the one ingredient that is neither a literal nor "
                     "a position, and the one no other rival touches: this "
                     "rival gets (a), (b) and (d) entirely right and still "
                     "loses. Witnessed under the decorating fragment renderer, "
                     "where the required fragments are observably not the "
                     "constant, at a fifth distinct name.",
        "witness": _witness(_ANGLE_RENDER, '"Mx"', '["p", "q"]'),
    },
    {
        "id": "weak-wrong-arg-per-position",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_DECL, _WEAK_WRONG_ARG_DECL),
        "refinement": "Emits one fragment per argument, correctly separated, "
                      "correctly delimited and correctly named, and each fragment "
                      "IS produced by the per-argument renderer — but always from "
                      "the LAST argument rather than from the argument at that "
                      "position. The F2P test pins the rendered text of "
                      "applications whose arguments render to distinct fragments, "
                      "so a faithful patch that rendered one argument repeatedly "
                      "would emit the wrong fragments and would NOT resolve.",
        "rationale": "Rejected by the postcondition clause via `renderArgs`, whose "
                     "fragment list is `args.map render`: that pins fragment i to "
                     "`render` applied to the I-TH argument, a POSITIONAL pairing "
                     "no other rival attacks. weak-render-ignored is refuted by "
                     "the fragments being constants, so it says nothing about a "
                     "rival that really does call `render` on a real element; "
                     "weak-reversed-order and the two truncating rivals all keep "
                     "the pairing intact on whatever they emit and corrupt only "
                     "which positions survive, or their order. This rival gets "
                     "(a), (b), (d), the arity AND the fact that every fragment is "
                     "a `render` image right, and still loses — so it isolates the "
                     "pairing itself. Correct at arity 0 and 1 (where the last "
                     "argument IS the only argument), so it is witnessed at arity "
                     "2, under the identity renderer at an eighth distinct name, "
                     "where the two fragments are observably different.",
        "witness": _witness(_ID_RENDER, '"Wn"', '["r", "s"]'),
    },
    {
        "id": "weak-separator-transposed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_SEP_SWAP),
        "refinement": "Divides adjacent fragments by the separator's two "
                      "characters in the opposite order. The F2P test pins the "
                      "rendered text character for character, so a faithful "
                      "patch emitting the transposed separator would NOT "
                      "resolve.",
        "rationale": "Rejected by the postcondition clause via `renderArgs`, "
                     "pinned to intercalation by the separator as WRITTEN. "
                     "Attacks ingredient (b) at its tightest near-miss: the "
                     "output has the same LENGTH as the required text and the "
                     "same character multiset, and the separator still appears "
                     "strictly between adjacent fragments — so neither the "
                     "length argument that rejects weak-separator-no-space nor "
                     "the placement argument that rejects "
                     "weak-trailing-separator applies, and only the separator's "
                     "exact content refutes it. Witnessed at a sixth distinct "
                     "name.",
        "witness": _witness(_ID_RENDER, '"Px"', '["p", "q"]'),
    },
    {
        "id": "weak-nullary-bare-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_WEAK_NULLARY),
        "refinement": "Renders an argument-less application as the bare textual "
                      "name with no bracket pair, while every other arity is "
                      "rendered correctly. A faithful patch behaving this way "
                      "emits, for a no-argument application, a bare name that is "
                      "not the target language's call syntax at all — so the "
                      "rendered text is not the pinned one and it would NOT "
                      "resolve.",
        "rationale": "Rejected by the sole postcondition clause, whose bracket "
                     "literals are pinned unconditionally: the obligation carries "
                     "no hypothesis restricting the argument list, so the "
                     "delimiters are required at the empty list too, where the "
                     "clause demands the name followed by an empty bracket pair. "
                     "This is the reject-lane counterpart of "
                     "admiss-empty-arg-list: that case shows a correct impl IS "
                     "dischargeable at the degenerate arity, this one shows a "
                     "wrong one is rejected there. It closes the only sub-domain "
                     "the other rivals leave unattributed — weak-first-arg-only "
                     "and weak-drop-first-arg are both CORRECT at arity 0, and "
                     "the rest are wrong across arities rather than at that point "
                     "— so the empty-list input gains a witness of its own. "
                     "Witnessed at a seventh distinct name on the empty argument "
                     "list, moving the `args` binder to a length the reject lane "
                     "had never probed.",
        "witness": _witness(_ID_RENDER, '"Zn"', '([] : List String)'),
    },
    {
        "id": "weak-nonterminating",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_DECL, _WEAK_NONTERM_DECL),
        "refinement": "The renderer never delivers any text: it recurses on an "
                      "ever-increasing counter and returns nothing. Its faithful "
                      "real counterpart is a printer method that hangs — the "
                      "rendering call never returns, so none of the pinned "
                      "rendered text is ever produced and the test asserting it "
                      "times out instead of passing. It resolves nothing, and it "
                      "fails on EVERY input rather than on a sub-domain, so it is "
                      "the most comprehensively wrong rival in the battery.",
        "rationale": "Rejected by the sole postcondition clause, which is an "
                     "EQUATION pinning the output: an impl that produces no "
                     "output cannot satisfy it at any input. Attacks the lane no "
                     "other rival here touches — every other rival delivers text "
                     "and corrupts one ingredient of it, whereas this one "
                     "corrupts the delivery. This is the port of nagini's "
                     "`weak-nonterminating`, whose rejection there came from the "
                     "termination obligation; here it comes from the value "
                     "equation over a total carrier, `partial def` being the only "
                     "way to write a diverging impl past the elaborator. The "
                     "witness cannot `decide` the rival's irreducible output, so "
                     "it refutes by FUNCTIONAL DEPENDENCE instead: the rival's "
                     "output ignores `funcName`, so the spec quantified over "
                     "`funcName` alone would force one and the same left-hand "
                     "side to equal both `A[a]` and `B[a]`. Binds nothing, hence "
                     "cannot be vacuous by contradictory hypotheses.",
        "witness": _WEAK_NONTERM_WITNESS,
    },
]


# The axiom lane belongs to G-AX, which records this instance as a skip: no
# unchanged callee is consumed as an axiom (the per-argument fragment renderer is
# left universally quantified, so the spec assumes nothing about it), and the
# axioms region is empty. Nothing for this gate to run.
AXIOM_TESTS = []
