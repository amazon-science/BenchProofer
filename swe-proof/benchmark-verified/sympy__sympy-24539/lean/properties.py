"""properties.py — G-PBT falsification battery for sympy__sympy-24539 (lean).

NOT a Lean file; a manifest of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for the admissibility positive, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect="reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

This bundle is a PORT of the nagini sibling's battery, re-expressed against the
Lean carrier. The nagini surface contracts a single selection-and-materialise
routine over read-only list inputs; the Lean bundle models the same behaviour as
one total function returning ``Except Unit SymExpr``.

DEFENDED SURFACE (one function over a four-input domain):

  asExpr (d : TermDict) (ngens : Nat) (ringSymbols symbols : List Symb)
      : Except Unit SymExpr
    result is pinned by THREE independent, domain-partitioning clauses:
      (C1) symbols.isEmpty → result = .ok (exprFromDict d ringSymbols)
           -- no caller symbols supplied ⇒ the routine's own default list is used
      (C2) ¬symbols.isEmpty → symbols.length = ngens →
             result = .ok (exprFromDict d symbols)
           -- THE FIX: a correctly-sized caller list is the one actually used,
              never silently replaced by the default list
      (C3) ¬symbols.isEmpty → symbols.length ≠ ngens → result = .error ()
           -- a non-empty caller list of the wrong count is rejected as an error

  The three cases partition every input, so the result is determined in all
  cases. The element-level builder is an UNCHANGED library routine modeled as
  ``opaque exprFromDict : TermDict → List Symb → SymExpr``: it appears
  identically in spec and impl, and the behaviour of interest is WHICH symbol
  list is handed to it. No property of the callee is consumed by the proof.

  A generator (``Symb``) is either a NAMED symbol (``Symb.named name``) or a
  nameless one (``Symb.other tag``): a ring's generators are arbitrary
  expressions, of which only some carry a name. Nothing in the defended
  surface inspects a generator — the surface decides only which list of them
  reaches the builder, and in which order — so the carrier is deliberately
  abstract, and in particular a generator is not reconstructible from a
  string.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and DEMONSTRATED so rather than
    asserted. The nagini sibling makes two input-write attacks MANDATORY because
    its two list inputs are held at fractional (read-only) permission, and a
    rival that overwrites one is rejected for insufficient permission. Both
    nagini rivals write a VALUE NO-OP (``symbols[0] = symbols[0]`` /
    ``default_symbols[0] = default_symbols[0]``): the rejection is purely on
    permission grounds, which is exactly why the class is mandatory there and
    empty here. Lean is referentially transparent — the inputs are plain
    immutable values (``List Symb``), there is no half-permission to violate and
    no aliasing to exploit — so the closest expressible rival is the pointwise
    identity ``gens := gens.set 0 (gens.getD 0 default)``, and it is OBSERVABLY
    GOLD: ``∀ d n r s, implementation_asExpr d n r s = <that impl> d n r s``
    elaborates (by cases on ``symbols``, exit 0). Landing it would be a vacuous
    reject case under attack C, so it is correctly omitted rather than
    fabricated. No substitute is invented for the class (see 'assessment').

  * UNGROUNDED-ORACLE ECHO — N/A. The spec does not equate the result to an
    axiomatised answer key; it is grounded in the input carriers — the returned
    expression is ``exprFromDict`` applied to the SELECTED symbol list, and the
    clauses pin which list (``ringSymbols`` vs the caller's ``symbols``) and the
    error branch structurally. A rival cannot echo an oracle without applying the
    callee to the correct list.

  * OPAQUE CARRIER — the discriminating content of C1/C2 is which list is fed to
    the opaque ``exprFromDict``, whose value cannot be computed. Following the
    conditioning technique, those two rivals are refuted at a point described by
    hypothesis: assuming only that the callee SEPARATES the two candidate lists
    (``exprFromDict d L ≠ exprFromDict d L'``) — the exact sub-domain where the
    rival is wrong — the rival's answer provably differs from the spec's, while
    gold still satisfies it. C3 is fully transparent (``.error () ≠ .ok _``), so
    its witness needs no hypothesis.

  * PARTIAL-DOMAIN / CONTROL-FLOW — APPLY, and are the load-bearing rivals.
    The pre-patch behaviour (always use the default list even for a correctly-
    sized caller list) attacks C2; a never-reject variant attacks C3; and a
    variant that on the empty branch feeds the caller's (empty) list rather than
    the default list attacks C1. Together they attack all three clauses.

REJECT RIVALS (each MUST be rejected; each carries a machine-checked witness):
  * uniq-prepatch-default (C2): the literal pre-patch — a correctly-sized caller
    list is discarded and the default list used instead.
  * uniq-empty-uses-caller (C1): on the no-caller-symbols branch, feed the
    caller's empty list to the builder instead of the default list.
  * uniq-no-reject (C3): never reject a wrong-count caller list; build an
    expression from it instead of erroring.
  * uniq-droplast (C2, tail sub-domain): select the correctly-sized caller list
    but hand the builder that list with its FINAL entry removed. The three
    rivals above all pass the builder a whole, unmodified candidate list, so
    they probe only WHICH list is selected; this one probes the list's CONTENTS
    at the tail, a sub-domain none of them reaches.
  * uniq-reversed-order (C2, order sub-domain): select the correctly-sized
    caller list but hand the builder its entries in reversed order — same list,
    same length, wrong positions. The builder consumes its generator list
    positionally, so order is observable, and no other rival varies it.
  * uniq-namewise-rebuild (C2, carrier sub-domain): select the correctly-sized
    caller list, then hand the builder that list with every NAMELESS generator
    replaced by a named one. Length-preserving, order-preserving and the
    identity on named generators, so none of the five rivals above touches it:
    it varies the generator ITSELF, which is the axis on which a routine that
    rebuilds its generators from their names diverges from one that passes
    them through unchanged.

POSITIVES:
  * pos-explicit-branch (soundness): a structurally different but behaviourally
    identical impl — the three-way selection REORDERED so the count guard is
    tested first, then the empty case, then the matching case, each arm returning
    directly rather than threading a mutable ``gens``. The reorder is required,
    not cosmetic: an impl that keeps the frozen branch ORDER and only unfolds the
    mutable ``gens`` into three returning arms is DEFINITIONALLY EQUAL to the
    frozen impl (``rfl`` closes ``implementation_asExpr = the reshape``), so it
    verifies because it IS the frozen term and probes nothing about spec
    strength. This one is not defeq (the same ``rfl`` probe fails), so the
    verifier reasons about the branch structure; its proof region is therefore
    reproven (statement byte-identical, no new lemma/axiom/assumption token).
  * admiss-correct-count-ground (admissibility): the frozen impl+proof with a
    ground instance discharged at an F2P-shaped input (a correctly-sized caller
    list of a different naming than the ring's, so C2 forces the caller list to
    be selected) inside the proof region, confirming the obligation is satisfiable
    at exactly the input the F2P exercises.

BINDER COVERAGE. Input binders are ``d``, ``ngens``, ``ringSymbols``, ``symbols``.
Across the six reject witnesses:
  * ``symbols`` — a length-1 list (C2, C3 rivals), the empty list (C1 rival),
    AND a length-2 list (droplast, reversed-order rivals), so the ``isEmpty``
    branch selector is varied off a single value and the list is long enough for
    a tail and an order to be observable at all. A length-1 list cannot
    distinguish a list from its own reversal, which is why the order rival needs
    the length-2 point rather than reusing an existing one.
  * ``ringSymbols`` — a non-empty list distinct from ``symbols`` (C1, C2,
    droplast, reversed-order, namewise-rebuild rivals) AND the empty list (C3
    rival).
  * the generator CARRIER — ``Symb.named`` at every point above, AND
    ``Symb.other`` (a nameless generator) at the namewise-rebuild point. This
    is a coverage axis in its own right: a rival that is the identity on named
    generators is invisible at every ``Symb.named`` point however the lists,
    lengths, counts and exponent widths are varied there.
  * ``ngens`` — matched to the caller length at 1 (C1/C2) and at 2 (droplast,
    reversed-order) AND deliberately mismatched (C3, ngens=3 with length-1
    caller list), exercising the count guard on both sides.
  * ``d`` — at a literal in every witness (and quantified only in the
    admissibility positive's ground instance). Its exponent-vector WIDTH is a
    real coverage axis, not decoration: the builder pairs its generator list
    positionally against each monomial's exponent vector, so a width-1 vector
    makes only the FIRST generator observable. The two sub-domain rivals
    therefore carry width-2 vectors matched to ``ngens = 2`` — ``[1, 1]`` for
    the tail rival (so the dropped final generator actually contributes) and
    ``[0, 1]`` for the order rival (so a permutation is visible at all) — while
    the two whole-list-substitution rivals and the transparent one are refuted
    at width 1, which suffices there because they differ already at the first
    position. A conditioning hypothesis stated at a width the deviation cannot
    reach would be FALSE of the routine being modeled, and the gate could not
    detect that: the callee is opaque, so no tactic can derive ``False`` from a
    disequality between two of its applications, and the consistency probe
    passes regardless. Width is checked by hand for each witness.
``pts`` = 6 distinct input points.

OMITTED nagini cases (see 'assessment'): the two frame/permission-mutation
rivals (VACUOUS on a referentially-transparent carrier — the inputs are plain
immutable values, so there is no permission to violate and no aliasing to
exploit); and the AXIOM_TESTS lane (this bundle declares no consumed axiom /
deep-model reference — G-AX is a skip stub — and the axiom lane is not this
gate's job). No carrier-new rival is fabricated for a behaviour this bundle does
not model.

The nagini drop-last off-by-one is NOT omitted: it is `uniq-droplast` above. An
earlier revision of this manifest recorded it as having "no counterpart here",
on the reasoning that the selection hands the WHOLE list to the opaque callee so
any deviation is already covered by the pre-patch rival's mechanism. That
reasoning was wrong on both halves, and the rival is what shows it. The carrier
does express a modified handed list (`gens.dropLast` is an ordinary term of the
same type), and its refutation is a DIFFERENT sub-domain of C2 than the
pre-patch rival's: the pre-patch rival substitutes one whole candidate list for
the other and is refuted wherever the builder separates `ringSymbols` from
`symbols`, whereas this one passes a list that is neither, and is refuted where
the builder separates a list from its own truncation. A spec that pinned only
"which of the two candidate lists" and not "that list, entire" would reject the
first and admit the second. `uniq-reversed-order` closes the same gap on the
positional axis. Both were landed with the two-build discrimination check, so
neither claim here rests on argument.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
selection and the error branch are modeled directly over the inputs, and the
sole callee is an unconstrained ``opaque`` whose property is never consumed, so
there is no axiom-soundness / axiom-containment obligation to probe here.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-24539"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen proof body, so every replacement
# lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_asExpr\n"
    "    (d : TermDict) (ngens : Nat) (ringSymbols symbols : List Symb) :\n"
    "    Except Unit SymExpr := Id.run do\n"
    "  let mut gens := symbols\n"
    "  if symbols.isEmpty then\n"
    "    gens := ringSymbols\n"
    "  else if symbols.length ≠ ngens then\n"
    "    return .error ()\n"
    "  return .ok (exprFromDict d gens)"
)

_PROOF_GOLD = (
    "  intro d ngens ringSymbols symbols\n"
    "  unfold implementation_asExpr\n"
    "  refine ⟨?_, ?_, ?_⟩\n"
    "  · intro h\n"
    "    simp only [h, Id.run, if_true, bind, pure]\n"
    "  · intro h1 h2\n"
    "    simp only [Id.run, if_neg h1, h2, ne_eq, not_true_eq_false, if_false, bind, pure]\n"
    "  · intro h1 h2\n"
    "    simp only [Id.run, if_neg h1, if_pos h2, bind, pure]"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_GOLD) == 1, "proof region drifted; update _PROOF_GOLD"


def _impl(body):
    """Full Solution.lean variant with the gold impl body replaced (proof kept)."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival impl bodies (each a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# PRE-PATCH (C2): a correctly-sized caller list is discarded and the default
# list is used instead. Rejects the wrong-count case correctly, but on every
# accepted path overwrites the selected list with `ringSymbols`.
_PREPATCH_IMPL = (
    "def implementation_asExpr\n"
    "    (d : TermDict) (ngens : Nat) (ringSymbols symbols : List Symb) :\n"
    "    Except Unit SymExpr := Id.run do\n"
    "  let mut gens := symbols\n"
    "  if ¬ symbols.isEmpty ∧ symbols.length ≠ ngens then\n"
    "    return .error ()\n"
    "  else\n"
    "    gens := ringSymbols\n"
    "  return .ok (exprFromDict d gens)"
)

# EMPTY-USES-CALLER (C1): on the no-caller-symbols branch, keep the caller's
# (empty) list rather than switching to the default list, so the expression is
# built from the empty list instead of the routine's own default symbols.
_EMPTY_CALLER_IMPL = (
    "def implementation_asExpr\n"
    "    (d : TermDict) (ngens : Nat) (ringSymbols symbols : List Symb) :\n"
    "    Except Unit SymExpr := Id.run do\n"
    "  let mut gens := symbols\n"
    "  if symbols.isEmpty then\n"
    "    gens := symbols\n"
    "  else if symbols.length ≠ ngens then\n"
    "    return .error ()\n"
    "  return .ok (exprFromDict d gens)"
)

# NO-REJECT (C3): never reject a wrong-count caller list — build an expression
# from it instead of returning an error.
_NO_REJECT_IMPL = (
    "def implementation_asExpr\n"
    "    (d : TermDict) (ngens : Nat) (ringSymbols symbols : List Symb) :\n"
    "    Except Unit SymExpr := Id.run do\n"
    "  let mut gens := symbols\n"
    "  if symbols.isEmpty then\n"
    "    gens := ringSymbols\n"
    "  return .ok (exprFromDict d gens)"
)

# DROP-LAST (C2, tail sub-domain): select the correctly-sized caller list, then
# hand the builder that list with its FINAL entry removed. Distinct from the
# pre-patch rival: the list passed is neither candidate list, so the violation is
# "the selected list, entire" rather than "which list was selected".
_DROPLAST_IMPL = (
    "def implementation_asExpr\n"
    "    (d : TermDict) (ngens : Nat) (ringSymbols symbols : List Symb) :\n"
    "    Except Unit SymExpr := Id.run do\n"
    "  let mut gens := symbols\n"
    "  if symbols.isEmpty then\n"
    "    gens := ringSymbols\n"
    "  else if symbols.length ≠ ngens then\n"
    "    return .error ()\n"
    "  return .ok (exprFromDict d gens.dropLast)"
)

# REVERSED ORDER (C2, order sub-domain): select the correctly-sized caller list
# but hand the builder its entries back-to-front. Same list, same length, wrong
# positions — and the builder consumes its generator list positionally.
_REVERSE_IMPL = (
    "def implementation_asExpr\n"
    "    (d : TermDict) (ngens : Nat) (ringSymbols symbols : List Symb) :\n"
    "    Except Unit SymExpr := Id.run do\n"
    "  let mut gens := symbols\n"
    "  if symbols.isEmpty then\n"
    "    gens := ringSymbols\n"
    "  else if symbols.length ≠ ngens then\n"
    "    return .error ()\n"
    "  return .ok (exprFromDict d gens.reverse)"
)

# NAMEWISE REBUILD (C2, carrier sub-domain): select the correctly-sized caller
# list, then hand the builder that list with every NAMELESS generator replaced by
# a named one. Length-preserving, order-preserving, and the identity on the named
# generators, so what it varies is the GENERATOR ITSELF rather than which list
# was selected, its extent or its order. A routine that reconstructs each
# generator from its name behaves this way, and a generator that has no name
# cannot be reconstructed from one.
_COLLAPSE_IMPL = (
    "def implementation_asExpr\n"
    "    (d : TermDict) (ngens : Nat) (ringSymbols symbols : List Symb) :\n"
    "    Except Unit SymExpr := Id.run do\n"
    "  let mut gens := symbols\n"
    "  if symbols.isEmpty then\n"
    "    gens := ringSymbols\n"
    "  else if symbols.length ≠ ngens then\n"
    "    return .error ()\n"
    "  return .ok (exprFromDict d (gens.map (fun s => match s with\n"
    "    | .named n => Symb.named n\n"
    "    | .other _ => Symb.named \"g\")))"
)


# POSITIVE CONTROL (soundness): a structurally different but behaviourally
# identical impl — the three-way selection is REORDERED so the count guard is
# tested FIRST, then the empty case, then the matching case, each arm returning
# directly rather than threading a mutable `gens`. This is the nagini sibling's
# positive control (`pos-control-reorder`) on this carrier.
#
# The reorder is load-bearing, and an earlier revision of this manifest got it
# wrong in a way no gate could see. That revision's positive kept the frozen
# branch ORDER and only unfolded the mutable `gens` into three returning arms:
#
#     if symbols.isEmpty then return .ok (exprFromDict d ringSymbols)
#     else if symbols.length ≠ ngens then return .error ()
#     else return .ok (exprFromDict d symbols)
#
# That impl is DEFINITIONALLY EQUAL to the frozen one — `example :
# implementation_asExpr = implementation_asExpr_pos := by rfl` elaborates (exit
# 0) — because `let mut gens := symbols; if … then gens := ringSymbols` and a
# direct `return` in each arm elaborate to the same `Id.run` join-point term.
# So it verified under the gold proof body for the only reason a defeq term
# can: it IS the frozen term. A soundness positive whose impl is defeq to gold
# probes nothing about spec strength — it cannot detect SPEC-TOO-STRONG,
# because the frozen proof closing it is the frozen proof closing itself — yet
# it passes `expect="verify"` honestly, so the gate records the lane as
# exercised. The reordered impl below is NOT defeq to gold (the same `rfl`
# probe fails: `implementation_asExpr is not definitionally equal to
# implementation_asExpr_alt`), so the verifier has to reason about the branch
# structure rather than reduce it away, and the lane means something.
#
# Consequently the gold proof body does NOT close this one verbatim (measured:
# the three `simp only` calls leave `pure (Except.ok …) = Except.ok …`
# residuals), so the proof region is reproven — which the variant scope permits
# for a soundness positive (`impl_region_only` is not required; the STATEMENT
# stays byte-identical and no axiom / sorry / new theorem is introduced).
_POS_IMPL = (
    "def implementation_asExpr\n"
    "    (d : TermDict) (ngens : Nat) (ringSymbols symbols : List Symb) :\n"
    "    Except Unit SymExpr := Id.run do\n"
    "  if ¬ symbols.isEmpty ∧ symbols.length ≠ ngens then\n"
    "    return .error ()\n"
    "  else if symbols.isEmpty then\n"
    "    return .ok (exprFromDict d ringSymbols)\n"
    "  else\n"
    "    return .ok (exprFromDict d symbols)"
)

# The reordered positive needs its own proof body: `simp_all` closes the three
# clause goals from the reordered branch structure, where the frozen script's
# `if_neg`/`if_pos` rewrites are aimed at the frozen order and leave residuals.
_POS_PROOF = (
    "  intro d ngens ringSymbols symbols\n"
    "  unfold problem_spec_asExpr implementation_asExpr\n"
    "  refine ⟨?_, ?_, ?_⟩ <;> intros <;> simp_all [Id.run, pure]"
)

# ADMISSIBILITY: the frozen impl+proof, with a ground instance discharged at the
# F2P-shaped input (a correctly-sized caller list [u,v,w] of a different naming
# than the ring's [x,y,z]; ngens = 3) BEFORE the frozen obligation, proving the
# modeled behavior is satisfiable at exactly the input the F2P exercises.
_ADMISS_PROOF = (
    "  have _ground : ∀ (d : TermDict),\n"
    "      problem_spec_asExpr d 3 [Symb.named \"x\", Symb.named \"y\", Symb.named \"z\"] [Symb.named \"u\", Symb.named \"v\", Symb.named \"w\"]\n"
    "        (implementation_asExpr d 3 [Symb.named \"x\", Symb.named \"y\", Symb.named \"z\"] [Symb.named \"u\", Symb.named \"v\", Symb.named \"w\"]) := by\n"
    "    intro d\n"
    "    unfold problem_spec_asExpr implementation_asExpr\n"
    "    refine ⟨?_, ?_, ?_⟩\n"
    "    · intro h; exact absurd h (by decide)\n"
    "    · intro _ _; rfl\n"
    "    · intro _ h2; exact absurd rfl h2\n"
    + _PROOF_GOLD
)


# ---------------------------------------------------------------------------
# Witnesses. On this carrier `exprFromDict` is opaque, so the C1/C2 rivals are
# refuted by CONDITIONING on the callee separating the two candidate lists (the
# exact sub-domain where the rival is wrong); the C3 rival is transparent.
# Each was built against the rival (must elaborate) and against the frozen
# solution (must fail), and each conditioning hypothesis is jointly satisfiable
# (single hypothesis about a single opaque term).
# ---------------------------------------------------------------------------

# C2 (pre-patch): at ngens = 1, caller list [a] (correctly sized), default list
# [b]. Whenever the builder separates [a] and [b], the pre-patch answer
# (built from [b]) differs from the spec's demand (built from [a]).
_WIT_PREPATCH = (
    "example\n"
    "    (h : exprFromDict { entries := [([1], 2)] } [Symb.named \"b\"]\n"
    "         ≠ exprFromDict { entries := [([1], 2)] } [Symb.named \"a\"]) :\n"
    "    ¬ problem_spec_asExpr { entries := [([1], 2)] } 1 [Symb.named \"b\"] [Symb.named \"a\"]\n"
    "      (implementation_asExpr { entries := [([1], 2)] } 1 [Symb.named \"b\"] [Symb.named \"a\"]) := by\n"
    "  unfold problem_spec_asExpr implementation_asExpr\n"
    "  simp only [Id.run]\n"
    "  intro hspec\n"
    "  obtain ⟨_, h2, _⟩ := hspec\n"
    "  have := h2 (by decide) (by decide)\n"
    "  simp only [pure] at this\n"
    "  exact h (by injection this)"
)

# C1 (empty-uses-caller): at symbols = [] (empty), default list [r]. Whenever the
# builder separates [] and [r], the rival's answer (built from the empty caller
# list) differs from the spec's demand (built from [r]).
_WIT_EMPTY_CALLER = (
    "example\n"
    "    (h : exprFromDict { entries := [([2], 3)] } []\n"
    "         ≠ exprFromDict { entries := [([2], 3)] } [Symb.named \"r\"]) :\n"
    "    ¬ problem_spec_asExpr { entries := [([2], 3)] } 1 [Symb.named \"r\"] []\n"
    "      (implementation_asExpr { entries := [([2], 3)] } 1 [Symb.named \"r\"] []) := by\n"
    "  unfold problem_spec_asExpr implementation_asExpr\n"
    "  simp only [Id.run]\n"
    "  intro hspec\n"
    "  obtain ⟨h1, _, _⟩ := hspec\n"
    "  have := h1 (by decide)\n"
    "  simp only [pure] at this\n"
    "  exact h (by injection this)"
)

# C2 tail sub-domain (droplast): at ngens = 2 with a correctly-sized caller list
# [a,b]. Whenever the builder separates [a] from [a,b] — a list from its own
# truncation — the rival's answer (built from the truncation) differs from the
# spec's demand (built from the whole caller list). Note the conditioning is on a
# pair the pre-patch witness never mentions: neither side of it is `ringSymbols`.
#
# The exponent vector carries TWO positions (`[1, 1]`), and that is load-bearing
# rather than cosmetic. The builder pairs its generator list positionally against
# each monomial's exponent vector, so a ONE-position vector never reaches the
# second generator: at `[([1], 2)]` the builder's answers on `[a]` and on `[a,b]`
# are the same expression, the conditioning hypothesis is FALSE of the routine
# being modeled, and the rival would in fact agree with the frozen behaviour at
# that point. The refutation would then rest on an unrealizable assumption — and
# the gate's consistency probe cannot see it, because `exprFromDict` is opaque, so
# no tactic can derive `False` from a disequality between two of its applications.
# Matching the vector's width to `ngens` is what makes the truncation observable
# and the hypothesis satisfiable at the real routine.
_WIT_DROPLAST = (
    "example\n"
    "    (h : exprFromDict { entries := [([1, 1], 2)] } [Symb.named \"a\"]\n"
    "         ≠ exprFromDict { entries := [([1, 1], 2)] } [Symb.named \"a\", Symb.named \"b\"]) :\n"
    "    ¬ problem_spec_asExpr { entries := [([1, 1], 2)] } 2\n"
    "        [Symb.named \"r\", Symb.named \"s\"] [Symb.named \"a\", Symb.named \"b\"]\n"
    "      (implementation_asExpr { entries := [([1, 1], 2)] } 2\n"
    "        [Symb.named \"r\", Symb.named \"s\"] [Symb.named \"a\", Symb.named \"b\"]) := by\n"
    "  unfold problem_spec_asExpr implementation_asExpr\n"
    "  simp only [Id.run]\n"
    "  intro hspec\n"
    "  obtain ⟨_, h2, _⟩ := hspec\n"
    "  have := h2 (by decide) (by decide)\n"
    "  simp only [pure] at this\n"
    "  exact h (by injection this)"
)

# C2 order sub-domain (reversed): at ngens = 2 with caller list [a,b] and a term
# whose monomial exponent vector has two positions, so the generator order is
# observable. Whenever the builder separates [b,a] from [a,b] — a list from its
# own permutation — the rival's answer differs from the spec's demand.
_WIT_REVERSE = (
    "example\n"
    "    (h : exprFromDict { entries := [([0, 1], 5)] } [Symb.named \"b\", Symb.named \"a\"]\n"
    "         ≠ exprFromDict { entries := [([0, 1], 5)] } [Symb.named \"a\", Symb.named \"b\"]) :\n"
    "    ¬ problem_spec_asExpr { entries := [([0, 1], 5)] } 2\n"
    "        [Symb.named \"r\", Symb.named \"s\"] [Symb.named \"a\", Symb.named \"b\"]\n"
    "      (implementation_asExpr { entries := [([0, 1], 5)] } 2\n"
    "        [Symb.named \"r\", Symb.named \"s\"] [Symb.named \"a\", Symb.named \"b\"]) := by\n"
    "  unfold problem_spec_asExpr implementation_asExpr\n"
    "  simp only [Id.run]\n"
    "  intro hspec\n"
    "  obtain ⟨_, h2, _⟩ := hspec\n"
    "  have := h2 (by decide) (by decide)\n"
    "  simp only [pure, List.reverse, List.reverseAux] at this\n"
    "  exact h (by injection this)"
)

# C2 carrier sub-domain (namewise rebuild): at ngens = 1 with a correctly-sized
# caller list holding a single NAMELESS generator. Whenever the builder separates
# that list from the one holding a named generator in its place, the rival's
# answer (built over the substituted generator) differs from the spec's demand
# (built over the caller's own generator). The point sits on the carrier axis no
# other witness varies: every other witness names only `Symb.named` generators,
# on which this rival is the identity, so none of them reaches it. Width 1
# suffices -- the deviation is at the FIRST generator - and the hypothesis is
# realizable at the real routine, which renders `2*g` where the frozen behaviour
# renders `2*<the caller's own generator>`.
_WIT_COLLAPSE = (
    "example\n"
    "    (h : exprFromDict { entries := [([1], 2)] } [Symb.named \"g\"]\n"
    "         ≠ exprFromDict { entries := [([1], 2)] } [Symb.other 0]) :\n"
    "    ¬ problem_spec_asExpr { entries := [([1], 2)] } 1 [Symb.named \"r\"] [Symb.other 0]\n"
    "      (implementation_asExpr { entries := [([1], 2)] } 1 [Symb.named \"r\"] [Symb.other 0]) := by\n"
    "  unfold problem_spec_asExpr implementation_asExpr\n"
    "  simp only [Id.run]\n"
    "  intro hspec\n"
    "  obtain ⟨_, h2, _⟩ := hspec\n"
    "  have := h2 (by decide) (by decide)\n"
    "  simp only [pure, List.map, List.map_cons, List.map_nil] at this\n"
    "  exact h (by injection this)"
)

# C3 (no-reject): fully transparent. At symbols = [a], ngens = 3 (wrong count),
# the spec demands `.error ()` but the rival returns `.ok _`.
_WIT_NO_REJECT = (
    "example : ¬ problem_spec_asExpr\n"
    "    { entries := [] } 3 [] [Symb.named \"a\"]\n"
    "    (implementation_asExpr { entries := [] } 3 [] [Symb.named \"a\"]) := by\n"
    "  unfold problem_spec_asExpr implementation_asExpr\n"
    "  simp [Id.run]"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify under the gold proof body VERBATIM. If a faithful correct
    # impl cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. The
    # `theorem correct_asExpr` STATEMENT is byte-identical; no helper lemma,
    # axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-explicit-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_IMPL), _PROOF_GOLD, _POS_PROOF),
        "rationale": (
            "a correct reshape that REORDERS the three-way selection — the count "
            "guard tested first, then the empty case, then the matching case, each "
            "arm returning directly instead of threading a mutable `gens` — must "
            "still satisfy all three clauses; if it cannot, the spec is "
            "SPEC-TOO-STRONG. The reorder is what makes this lane mean anything: "
            "the impl is NOT definitionally equal to the frozen one (the `rfl` "
            "probe `implementation_asExpr = implementation_asExpr_alt` FAILS), so "
            "the verifier must reason about the branch structure rather than "
            "reduce it away. A positive that merely unfolds the mutable `gens` "
            "into three returning arms IS defeq to gold and probes nothing; see "
            "the note on `_POS_IMPL`. Because the branch order changed, the frozen "
            "tactic body no longer closes it verbatim, so the proof region is "
            "reproven with `simp_all` — permitted for a soundness positive: the "
            "theorem STATEMENT is byte-identical and no new declaration, axiom, "
            "`sorry`, or assumption token is introduced."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the F2P-shaped input. The frozen theorem carries NO
    # precondition hypothesis (the behaviour is total, so `∀` is unguarded), so
    # nagini's precondition-admission probe has no binder to attack; the honest
    # analogue discharges the spec predicate at the F2P ground input (a
    # correctly-sized caller list differently named than the ring's) inside the
    # proof region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-correct-count-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_GOLD, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at the F2P ground input (a correctly-"
            "sized caller list [u,v,w] with ngens = 3, differently named than the "
            "ring's [x,y,z], so clause C2 forces the caller list to be the one "
            "used) as a `have` inside the existing tactic body, then the frozen "
            "obligation is closed verbatim. Verifies (else the spec is "
            "unsatisfiable at the normal input — the analogue of PRECOND-TOO-"
            "STRONG). Nothing is assumed: the theorem STATEMENT is byte-identical, "
            "the ground instance is a local `have`, and no new declaration / axiom "
            "/ `sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would
    # be a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "uniq-prepatch-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH_IMPL),
        "refinement": (
            "this is the literal pre-patch behaviour: a correctly-sized caller "
            "list is discarded and the routine's own default list is used on every "
            "accepted path. On the F2P observable — a correctly-sized caller list "
            "differently named than the ring's — the expression is rendered over "
            "the default list, so it equals the polynomial in the ring's own "
            "symbols rather than the caller's, and the F2P equality against the "
            "caller-symbol polynomial FAILS. This is exactly the reported bug; the "
            "faithful patch does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C2 (¬symbols.isEmpty → symbols.length = ngens → "
            "result = .ok (exprFromDict d symbols)): it returns the expression "
            "built from `ringSymbols`, which differs from the one built from "
            "`symbols` whenever the builder separates the two lists. If it "
            "verifies, the spec does not force the correctly-sized caller list to "
            "be the one used (SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_PREPATCH,
    },
    {
        "id": "uniq-empty-uses-caller",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_EMPTY_CALLER_IMPL),
        "refinement": (
            "on the no-caller-symbols branch this keeps the caller's (empty) list "
            "rather than switching to the routine's own default list, so with no "
            "caller symbols the expression is built from an empty generator list "
            "instead of the default symbols. A real patch that failed to fall back "
            "to the default list on the empty-supply path would render the wrong "
            "expression (no generators) and NOT resolve the no-argument F2P case."
        ),
        "rationale": (
            "REJECT from clause C1 (symbols.isEmpty → result = "
            ".ok (exprFromDict d ringSymbols)): on the empty-caller path it "
            "returns the expression built from the empty caller list, which "
            "differs from the one built from `ringSymbols` whenever the builder "
            "separates the two. Attacks C1 specifically — the clause the pre-patch "
            "rival satisfies — and varies `symbols` to the empty list. If it "
            "verifies, C1 does not pin the default-list fallback (SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_EMPTY_CALLER,
    },
    {
        "id": "uniq-no-reject",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NO_REJECT_IMPL),
        "refinement": (
            "a faithful patch that never rejects a wrong-count caller list — "
            "building an expression from it instead of erroring — would render a "
            "result rather than raising on the wrong-count input the F2P exercises "
            "with a `raises`-style check, so the error arm of the F2P FAILS (no "
            "error is produced) and the patch does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C3 (¬symbols.isEmpty → symbols.length ≠ ngens → "
            "result = .error ()): on a non-empty caller list whose length ≠ ngens "
            "it returns `.ok _`, which is structurally distinct from `.error ()`. "
            "Refuted at ngens = 3 with a length-1 caller list — deliberately "
            "mismatching the count guard, off the matched value the other rivals "
            "use. If it verifies, the spec does not force rejection on the "
            "wrong-count path (SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_NO_REJECT,
    },
    {
        "id": "uniq-droplast",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROPLAST_IMPL),
        "refinement": (
            "a faithful patch that selects the correctly-sized caller list but "
            "hands the builder that list with its last entry dropped renders the "
            "polynomial over too few generators: the builder consumes its "
            "generator list positionally against each monomial's exponent "
            "vector, so every monomial loses its final factor. On the F2P "
            "observable — a correctly-sized caller list differently named than "
            "the ring's — the rendered expression is missing the last "
            "generator's contribution and the F2P equality against the "
            "caller-symbol polynomial FAILS, so the patch does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C2 (¬symbols.isEmpty → symbols.length = ngens → "
            "result = .ok (exprFromDict d symbols)): it returns the expression "
            "built from the caller list's truncation, which differs from the one "
            "built from `symbols` whenever the builder separates a list from its "
            "own front-prefix. Attacks a sub-domain of C2 that the pre-patch "
            "rival does not reach: that rival swaps one whole candidate list for "
            "the other, so a spec pinning only WHICH list was selected would "
            "reject it while admitting this one, which passes a list that is "
            "neither. The refutation is conditioned at a monomial whose exponent "
            "vector is as WIDE as `ngens`, which is where dropping the final "
            "generator is observable at all — at a narrower vector the builder "
            "never reaches the dropped position and the rival would agree with "
            "the frozen behaviour. If it verifies, C2 does not pin the selected "
            "list ENTIRE (SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_DROPLAST,
    },
    {
        "id": "uniq-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_REVERSE_IMPL),
        "refinement": (
            "a faithful patch that selects the correctly-sized caller list but "
            "hands the builder its entries back-to-front pairs each monomial's "
            "exponents with the wrong generators, since the builder consumes the "
            "generator list positionally. On the F2P observable the rendered "
            "expression carries the caller's symbols raised to permuted powers "
            "rather than the intended polynomial, so the F2P equality FAILS and "
            "the patch does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C2 (¬symbols.isEmpty → symbols.length = ngens → "
            "result = .ok (exprFromDict d symbols)): it returns the expression "
            "built from the caller list's reversal, which differs from the one "
            "built from `symbols` whenever the builder separates a list from its "
            "own permutation. Length-preserving, so neither the count guard nor a "
            "length-only reading of C2 sees it, and it is the only rival that "
            "varies generator ORDER — the length-1 caller lists the other rivals "
            "use cannot distinguish a list from its reversal at all. If it "
            "verifies, C2 pins the selected list only up to permutation "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_REVERSE,
    },
    {
        "id": "uniq-namewise-rebuild",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_COLLAPSE_IMPL),
        "refinement": (
            "a faithful routine that rebuilds each generator from its NAME before "
            "handing the list to the builder renders the polynomial over "
            "substituted generators. A ring may be built over generators that are "
            "not named symbols at all — `PolyRing((pi, sqrt(2)), ZZ, lex)` is a "
            "ring whose two generators carry no name — and the no-argument call "
            "reaches exactly those generators, deep inside library code: a "
            "cancellation on an expression-domain coefficient renders a ring's own "
            "generators back to expressions. Measured through the oracle on this "
            "instance: such a routine applies cleanly at base_commit, keeps the "
            "FAIL_TO_PASS test green, and FAILS the PASS_TO_PASS test "
            "`test_PolyElement___mul__`, whose observable is a product against an "
            "expression-domain coefficient. So the faithful routine does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from clause C2 (¬symbols.isEmpty → symbols.length = ngens → "
            "result = .ok (exprFromDict d symbols)): it returns the expression "
            "built from a list in which a nameless generator has been replaced by "
            "a named one, which differs from the one built from `symbols` whenever "
            "the builder separates the two. Attacks the CARRIER sub-domain of C2 "
            "that no other rival reaches: it preserves length and order and is the "
            "identity on named generators, so a spec pinning only which list was "
            "selected, that list entire, and its order would admit it. If it "
            "verifies, C2 pins the selected list only up to rebuilding its "
            "generators from their names (SPEC-TOO-WEAK), which is not something "
            "the modeled routine may do — a generator that has no name cannot be "
            "rebuilt from one."
        ),
        "witness": _WIT_COLLAPSE,
    },
]


# No consumed axioms and no deep-model references: the selection and the error
# branch are modeled directly over the inputs, and the sole callee is an
# unconstrained `opaque` whose property is never consumed by the proof, so there
# is no in-model axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
