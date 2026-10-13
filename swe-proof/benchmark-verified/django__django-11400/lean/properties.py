"""properties.py — G-PBT falsification battery for django__django-11400 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant sharing the FROZEN spec
byte-for-byte (region surgery: only text strictly inside an ``-- impl-start`` /
``-- impl-end`` region — and, where a case legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds by construction and both ``theorem correct_*``
STATEMENTS stay byte-identical). ``expect:"verify"`` passes iff the variant is in
scope AND the file elaborates with every obligation closed; ``expect:"reject"``
passes iff it is in scope AND does NOT verify AND the case's refutation
``witness`` holds of the rival while FAILING on the frozen solution.

DEFENDED SURFACE (two obligations, the second layered on the first):

    problem_spec_orderedChoices
        (includeBlank : Bool) (blank : List (Int × String))
        (ordering : List String) (objs : List Obj)
        (result : List (Int × String)) : Prop
      result = (if includeBlank then blank else [])
        ++ (if ordering = [] then objs else applyOrdering ordering objs).map toChoice

    problem_spec_restrictedChoices
        (adminOrdering : Option (List String)) (objs : List Obj)
        (result : List (Int × String)) : Prop
      problem_spec_orderedChoices false [] (configuredOrdering adminOrdering)
        objs result

Four INDEPENDENTLY ATTACKABLE decisions are folded into the single equation of
``orderedChoices``, and the battery attacks each separately:

  * THE DIRECTIVE SPLIT — the load-bearing clause. The re-sequencing primitive
    is consulted ONLY on the non-empty-directive branch; on the empty directive
    the spec pins the result to the collection's own default presentation order
    ``objs``, NOT to ``applyOrdering [] objs``. Since ``applyOrdering`` is
    ``opaque`` and NO axiom constrains it, ``applyOrdering [] objs`` is not
    provably ``objs``, so an impl that routes the empty directive through the
    primitive cannot discharge the equation. Attacked by
    ``rival-unconditional-reorder`` (always re-sequence) and
    ``rival-invert-directive-guard`` (re-sequence exactly when the directive is
    empty).
  * THE DIRECTIVE DOMAIN — every non-empty directive re-sequences, not just some.
    Attacked by ``rival-multi-key-only`` (a single-key directive is silently
    treated as no directive) and ``rival-never-reorder`` (the primitive is never
    consulted at all).
  * THE PRIMITIVE'S ARGUMENTS — the non-empty arm is ``applyOrdering ordering
    objs``, which pins TWO arguments, and "is the primitive consulted" is a
    different question from "is it consulted on the caller's own inputs". Added
    by AUDIT, because the rivals above all vary only the former: attacked by
    ``rival-primitive-wrong-records`` (right guard, right directive, PERMUTED
    collection) and ``rival-primitive-wrong-directive`` (right guard, right
    collection, PERTURBED directive). Together they are what a spec of the form
    "the non-empty arm applies the primitive to something" would admit.
  * THE BLANK PREFIX — present exactly when ``includeBlank`` holds, and the
    ``blank`` argument is what is prepended. Two SEPARATE sub-clauses, each with
    its own rival: the flag's polarity is attacked by ``rival-blank-always``
    (prefix regardless of the flag) and ``rival-blank-never`` (flag ignored the
    other way); the prefix's IDENTITY — that the prepended entries are the ones
    the caller supplied, not merely some prefix of the right length — is attacked
    by ``rival-blank-wrong-value``, which substitutes a fixed constant for the
    supplied argument and is therefore correct on both polarities of the flag.
  * THE CONCATENATION ORDER — the prefix leads, the choices follow. Attacked by
    ``rival-blank-suffix``, which produces exactly the right multiset of choices
    in the wrong arrangement, so it is the case a spec stated as a
    set/permutation rather than a list equality would admit.

  and for ``restrictedChoices``:

  * THE FORWARDED DIRECTIVE — the configuration's directive reaches the inner
    listing rather than being discarded. Attacked by
    ``rival-restricted-drop-directive``.
  * THE RESTRICTED LISTING'S FIXED ARGUMENTS — no blank prefix on this path.
    Attacked by ``rival-restricted-adds-blank``.

ADVERSARIAL READ of the nagini classes on this carrier (nagini's battery is the
design document; see the porting notes in the bundle's assessment):

  * FRAME / PERMISSION MUTATION — nagini's mandatory #1 class, where both inputs
    are held at fractional read-only permission and a rival tries to satisfy a
    postcondition by WRITING to an input. VACUOUS here. Lean is referentially
    transparent: ``objs`` and ``ordering`` are immutable values, there is no
    half-permission to violate and no aliasing to overwrite, so the attack cannot
    even be expressed. No permission-violation substitute is fabricated. The
    SEMANTIC residue of that obligation — "an input is not silently absorbed into
    the answer" — survives as the spec's own structural pinning of each output
    component to a named input, and that IS attacked (the blank-prefix and
    concatenation-order rivals put the wrong input, or the right inputs in the
    wrong arrangement, into the result).
  * DIVERGENCE / NON-TERMINATION — VACUOUS on this backend. Both
    ``implementation_*`` are total Lean ``def``s, so a diverging implementation
    cannot be written at all and there is nothing for a rival to exploit. (This
    is genuinely vacuous here, unlike the velvet ``partial``-semantics case
    recorded in ``the corpus-wide termination-semantics finding``.)
  * UNGROUNDED-ORACLE ECHO — VACUOUS. The re-sequencing primitive is ``opaque``
    and no axiom pins it, so there is no answer key to echo: the only way to
    produce a value equal to ``applyOrdering ordering objs`` is to apply the
    primitive. The temptation the spec must resist is the mirror image — routing
    the EMPTY directive through the primitive too — and that is exactly the
    directive-split attack above.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation (the frozen ``simp only [...] <;> rfl`` script is
tuned to the frozen form), so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate at a concrete input; each was checked by real builds to HOLD of its
rival and to FAIL on the frozen solution.

Five witnesses close on ground data (the EMPTY-directive sub-domain, where the
spec's right-hand side reduces to ``objs`` and the equation is decidable). Seven
cannot, because the rival's divergence lives on the NON-EMPTY branch where the
carrier is the ``opaque`` primitive with no constraining axiom — nothing computes
there. Those CONDITION on the carrier instead: each assumes only that the
primitive's result on ONE concrete directive/record pair differs from the
default-order choice list, and derives that the rival then contradicts the spec
at that point. That is precisely the sub-domain where the rival is wrong (a
primitive that happened to be the identity there would make the rival agree with
the spec), and it is a single hypothesis about a single application of the
primitive, so the assumptions are trivially jointly satisfiable — the gate's
``False``-derivation probe was run on each and failed, as required.

Both properties are established per case BY BUILD, and the gold half is
established the strong way rather than by reading an exit code: for each of the
twelve witness points the FLIPPED claim (the same point, asserting the frozen
impl is CORRECT there) was built against the frozen solution and VERIFIES, while the
witness itself fails there with the goal reduced to ``False`` — i.e. ``simp``
PROVED the spec equation for the frozen impl and could not for the rival. So
gold's exit code demonstrably tracks WHAT IS CLAIMED and not merely the presence
of a claim; see the ``_HPURE`` note for the residue that would otherwise break
exactly that property.

BINDER COVERAGE. Every input binder of both spec predicates is varied across the
reject witnesses:
  * ``ordering`` — ``[]`` (six witnesses), ``["x"]``, ``["y"]``, ``["x", "y"]``
    and ``["p", "q", "r"]``, so the empty / single-key / multi-key regimes are all
    probed and the guard's threshold is pinned on both sides.
  * ``includeBlank`` — ``true`` and ``false`` both occur, so a rival mishandling
    only one polarity of the flag is reachable.
  * ``blank`` — ``[]`` and TWO DISTINCT one-element prefixes occur
    (``[(0, "-")]`` across the flag-polarity and arrangement witnesses, and
    ``[(9, "z")]`` in ``rival-blank-wrong-value``). The second value is what makes
    the prefix's IDENTITY discriminated rather than only its presence: a rival
    that prepends a fixed constant agrees with the spec at every witness whose
    supplied prefix happens to BE that constant, so a battery in which every
    non-empty ``blank`` is spelled the same way pins the prefix's length and
    position but never its contents.
  * ``objs`` — empty, one-record and two-record lists, with distinct keys and
    labels per witness, so neither the traversal nor the per-record projection is
    pinned to one shape.
  * ``adminOrdering`` — ``none`` and ``some ["x"]``, the two regimes the
    configuration lookup distinguishes.
``pts`` = 12 distinct input points (no two reject witnesses share one), plus the
three F2P-shaped points the admissibility positive discharges the obligations at.

AXIOM lane: EMPTY. ``meta.json`` records ``axioms == []`` and
``deep_model_references == []`` — the re-sequencing primitive is an I-tagged echo
validated end-to-end by G-CONF, not a consumed axiom — so there is no
axiom-soundness / axiom-containment obligation here, and that lane belongs to
G-AX regardless. ``AXIOM_TESTS`` is omitted.
"""
from pathlib import Path

INSTANCE = "django__django-11400"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each is the FULL body of one impl region (or one proof
# region), so every replacement lands entirely inside the region it edits, and
# each is unique in the frozen file (asserted at load by _swap).
# ---------------------------------------------------------------------------

_IMPL_ORDERED = """  let mut qs := objs
  if ordering ≠ [] then
    qs := applyOrdering ordering objs
  return (if includeBlank then blank else []) ++ qs.map toChoice
"""

_IMPL_RESTRICTED = """  let ordering := configuredOrdering adminOrdering
  return implementation_orderedChoices false [] ordering objs
"""

_PROOF_ORDERED = """  intro includeBlank blank ordering objs
  unfold problem_spec_orderedChoices implementation_orderedChoices
  by_cases h : ordering = [] <;>
    simp only [h, Id.run, ne_eq, not_true_eq_false, not_false_eq_true,
      if_true, if_false] <;> rfl
"""

_PROOF_RESTRICTED = """  intro adminOrdering objs
  unfold problem_spec_restrictedChoices implementation_restrictedChoices
  simp only [Id.run]
  exact correct_orderedChoices false [] (configuredOrdering adminOrdering) objs
"""


# ---------------------------------------------------------------------------
# Shared witness preambles. `simp only [Id.run]` peels the `Id.run` wrapper the
# imperative shape introduces; the following `simp` normalizes the list
# concatenation and the branch selection so what remains is either ground data
# (the empty-directive witnesses, closed by `decide`) or exactly the conditioned
# hypothesis (the non-empty-directive witnesses, closed by `exact h`).
#
# `hpure` is LOAD-BEARING and is why these preambles are not just
# `simp only [Id.run]; simp`. `Id.run` leaves a residual `pure x` — the
# `return` of the `Id.run do` block — that no `simp` lemma in scope discharges,
# so the plain preamble stalls with `⊢ pure X = X` unreduced on BOTH subjects.
# The consequence is not cosmetic: it is exactly the hollow-gold-signature
# failure mode. With the residue in place, gold's build dies in the leftover
# `pure` obligation rather than in the CLAIM, so gold's exit code stops tracking
# what the witness asserts — a FLIPPED witness (asserting gold is CORRECT at
# the very same point) fails on gold with the same shape of error, which is what
# would let a forged non-refutation be recorded as `rejected`. Measured with
# real builds on this cell: with `hpure`, the flipped/positive claim VERIFIES
# against the frozen solution (exit 0) at every one of the ten witness points,
# while each negated witness fails there with `⊢ False` — i.e. `simp` PROVED the
# spec equation for the frozen impl and could not for the rival. `hpure` itself
# assumes nothing: it is `fun _ => rfl`, `pure` on `Id` being the identity by
# definition.
# ---------------------------------------------------------------------------

_HPURE = """  have hpure : ∀ (x : List (Int × String)), (pure x : Id (List (Int × String))) = x :=
    fun _ => rfl
"""

_U_ORDERED = _HPURE + """  unfold problem_spec_orderedChoices implementation_orderedChoices
  simp only [Id.run]
  simp [hpure]
"""

_U_RESTRICTED = _HPURE + """  unfold problem_spec_restrictedChoices problem_spec_orderedChoices
    implementation_restrictedChoices implementation_orderedChoices
  simp only [Id.run, configuredOrdering]
  simp [hpure]
"""


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (P1) Structurally different but CORRECT: the fall-through mutable-accumulator
# shape is rewritten as an EXPLICIT two-branch if/else with the empty-directive
# case stated FIRST, each branch returning its own fully-built list. Same
# behavior, different control flow and a different number of return points. The
# obligation is re-proved for the new shape (the frozen `<;> rfl` script no
# longer matches), with the STATEMENT untouched. If this failed to verify, the
# postcondition would be over-fit to one branch order / one return point =>
# SPEC-TOO-STRONG.
_IMPL_P1 = """  if ordering = [] then
    return (if includeBlank then blank else []) ++ objs.map toChoice
  else
    return (if includeBlank then blank else [])
      ++ (applyOrdering ordering objs).map toChoice
"""
_PROOF_P1 = """  intro includeBlank blank ordering objs
  unfold problem_spec_orderedChoices implementation_orderedChoices
  by_cases h : ordering = [] <;> simp only [h, Id.run, if_true, if_false] <;> rfl
"""
_POS_EXPLICIT_ELSE = _swap(_swap(_BASE, _IMPL_ORDERED, _IMPL_P1),
                           _PROOF_ORDERED, _PROOF_P1)

# (P2) Structurally different but CORRECT: the branch is lifted out of the
# statement sequence into a single pure `let` binding whose right-hand side is a
# conditional expression, and the result is assembled once. No mutable local, no
# early return — a different code shape over identical logic. If this failed to
# verify, the spec would be over-fit to the imperative accumulator form =>
# SPEC-TOO-STRONG.
_IMPL_P2 = """  let qs := if ordering = [] then objs else applyOrdering ordering objs
  return (if includeBlank then blank else []) ++ qs.map toChoice
"""
_PROOF_P2 = """  intro includeBlank blank ordering objs
  unfold problem_spec_orderedChoices implementation_orderedChoices
  simp only [Id.run]
  rfl
"""
_POS_SINGLE_BIND = _swap(_swap(_BASE, _IMPL_ORDERED, _IMPL_P2),
                         _PROOF_ORDERED, _PROOF_P2)

# (P3) Structurally different but CORRECT on the SECOND obligation: the
# configuration lookup is inlined as an explicit case analysis on the optional
# directive instead of being funneled through the shared selector, so both
# regimes are written out separately. The proof follows the same split and closes
# each arm via the callee's own correctness theorem (callee-under-spec, proved
# not assumed). If this failed, the layered spec would be over-fit to the
# selector's syntactic form => SPEC-TOO-STRONG.
_IMPL_P3 = """  match adminOrdering with
  | none => return implementation_orderedChoices false [] [] objs
  | some xs => return implementation_orderedChoices false [] xs objs
"""
_PROOF_P3 = """  intro adminOrdering objs
  unfold problem_spec_restrictedChoices implementation_restrictedChoices
  cases adminOrdering with
  | none =>
    simp only [Id.run, configuredOrdering, Option.getD]
    exact correct_orderedChoices false [] [] objs
  | some xs =>
    simp only [Id.run, configuredOrdering, Option.getD]
    exact correct_orderedChoices false [] xs objs
"""
_POS_MATCH_OPTION = _swap(_swap(_BASE, _IMPL_RESTRICTED, _IMPL_P3),
                          _PROOF_RESTRICTED, _PROOF_P3)


# ---------------------------------------------------------------------------
# (P4) ADMISSIBILITY. The nagini sibling carries `admiss-self-call`: self-calls
# on F2P-shaped inputs must establish the read-only fractional preconditions, so
# a PRECOND-TOO-STRONG spec (one no normal caller can satisfy) is caught. Both
# frozen obligations here are unconditionally quantified — there is no
# precondition to over-constrain — so the analogue on this total carrier is the
# obligation being UNSATISFIABLE at exactly an F2P-shaped input. That is a real
# risk and not a formality: the spec's right-hand side is an equation whose two
# branches are selected by `ordering = []`, and if the branch selection or the
# prefix/concatenation shape did not actually reduce at a concrete input, the
# obligation would hold only universally-by-tactic and never be checkable at a
# point a caller can name.
#
# So the case discharges the obligation AT the two F2P-shaped points, BY
# evaluation, as `have`s prepended to each frozen tactic body, and then closes
# the frozen obligation verbatim. The three points, all with a two-record
# collection whose default presentation order is what the assertions read back:
#   * the empty directive (`decide` — ground data, so the equation is DECIDED,
#     not merely rewritten: this is the sub-domain the reported defect lives in);
#   * a supplied one-key directive (`rfl` — the primitive is opaque, so the
#     equation reduces to a reflexivity on the primitive's own application, which
#     is precisely what "the directive reaches the primitive" means at a point);
#   * the restricted listing with a configured directive, closed through the
#     inner obligation's own theorem.
# Nothing is assumed: no new declaration, no axiom, both STATEMENTS
# byte-identical, `expect="verify"`. If this failed, the modeled behavior would
# be unsatisfiable at exactly a normal F2P input => PRECOND-TOO-STRONG.
_PROOF_ADMISS_ORDERED = """  have _f2p_default_order : problem_spec_orderedChoices false []
      [] [{ pk := 10, label := "a" }, { pk := 20, label := "b" }]
      (implementation_orderedChoices false []
        [] [{ pk := 10, label := "a" }, { pk := 20, label := "b" }]) := by
    unfold problem_spec_orderedChoices implementation_orderedChoices
    simp only [Id.run]
    decide
  have _f2p_supplied_directive : problem_spec_orderedChoices true [((0 : Int), "-")]
      ["x"] [{ pk := 10, label := "a" }, { pk := 20, label := "b" }]
      (implementation_orderedChoices true [((0 : Int), "-")]
        ["x"] [{ pk := 10, label := "a" }, { pk := 20, label := "b" }]) := by
    unfold problem_spec_orderedChoices implementation_orderedChoices
    simp only [Id.run]
    rfl
""" + _PROOF_ORDERED

_PROOF_ADMISS_RESTRICTED = """  have _f2p_configured : problem_spec_restrictedChoices (some ["x"])
      [{ pk := 10, label := "a" }, { pk := 20, label := "b" }]
      (implementation_restrictedChoices (some ["x"])
        [{ pk := 10, label := "a" }, { pk := 20, label := "b" }]) := by
    unfold problem_spec_restrictedChoices implementation_restrictedChoices
    simp only [Id.run]
    exact correct_orderedChoices false [] (configuredOrdering (some ["x"]))
      [{ pk := 10, label := "a" }, { pk := 20, label := "b" }]
""" + _PROOF_RESTRICTED

_POS_ADMISS = _swap(_swap(_BASE, _PROOF_ORDERED, _PROOF_ADMISS_ORDERED),
                    _PROOF_RESTRICTED, _PROOF_ADMISS_RESTRICTED)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (R1) THE BUG ITSELF — the re-sequencing primitive is applied UNCONDITIONALLY,
# so the empty directive also overwrites the default presentation order. This is
# the pre-patch behavior `Solution_prepatch_1.lean` reverts to.
_RIVAL_UNCONDITIONAL = _swap(_BASE, _IMPL_ORDERED, """  let qs := applyOrdering ordering objs
  return (if includeBlank then blank else []) ++ qs.map toChoice
""")
# The hypothesis is stated in the SHAPE the shared preamble's `simp` normalizes
# the goal to (a one-record collection makes `List.map f l = [c]` decompose into
# "the sole record's choice differs from the expected one"), rather than as the
# list equation, so the closing `exact h` matches with no bespoke rewriting.
_W_UNCONDITIONAL = """
example (h : ∀ (x : Obj), applyOrdering [] [{ pk := 1, label := "a" }] = [x]
      → ¬ toChoice x = toChoice { pk := 1, label := "a" }) :
    ¬ problem_spec_orderedChoices false [] [] [{ pk := 1, label := "a" }]
        (implementation_orderedChoices false [] [] [{ pk := 1, label := "a" }]) := by
""" + _U_ORDERED + "  exact h\n"

# (R2) DIRECTIVE-GUARD INVERSION — the primitive is applied exactly when the
# directive is EMPTY, and a non-empty directive is ignored. Wrong on BOTH
# branches.
_RIVAL_INVERT = _swap(_BASE, _IMPL_ORDERED, """  let mut qs := objs
  if ordering = [] then
    qs := applyOrdering ordering objs
  return (if includeBlank then blank else []) ++ qs.map toChoice
""")
_W_INVERT = """
example (h : ¬ ([toChoice { pk := 1, label := "a" }]
      = List.map toChoice (applyOrdering ["x", "y"] [{ pk := 1, label := "a" }]))) :
    ¬ problem_spec_orderedChoices true [((0 : Int), "-")] ["x", "y"]
        [{ pk := 1, label := "a" }]
        (implementation_orderedChoices true [((0 : Int), "-")] ["x", "y"]
          [{ pk := 1, label := "a" }]) := by
""" + _U_ORDERED + "  exact h\n"

# (R3) PARTIAL DOMAIN — the guard is tightened so only a MULTI-key directive
# re-sequences; a single-key directive is silently treated as no directive.
_RIVAL_MULTI_ONLY = _swap(_BASE, _IMPL_ORDERED, """  let mut qs := objs
  if ordering.length > 1 then
    qs := applyOrdering ordering objs
  return (if includeBlank then blank else []) ++ qs.map toChoice
""")
_W_MULTI_ONLY = """
example (h : ¬ ([toChoice { pk := 2, label := "b" }, toChoice { pk := 3, label := "c" }]
      = List.map toChoice (applyOrdering ["x"]
          [{ pk := 2, label := "b" }, { pk := 3, label := "c" }]))) :
    ¬ problem_spec_orderedChoices false [] ["x"]
        [{ pk := 2, label := "b" }, { pk := 3, label := "c" }]
        (implementation_orderedChoices false [] ["x"]
          [{ pk := 2, label := "b" }, { pk := 3, label := "c" }]) := by
""" + _U_ORDERED + "  exact h\n"

# (R4) THE PRIMITIVE IS NEVER CONSULTED — every directive, empty or not, leaves
# the default presentation order in place.
_RIVAL_NEVER_REORDER = _swap(_BASE, _IMPL_ORDERED, """  let qs := objs
  return (if includeBlank then blank else []) ++ qs.map toChoice
""")
_W_NEVER_REORDER = """
example (h : ¬ ([toChoice { pk := 5, label := "e" }]
      = List.map toChoice (applyOrdering ["p", "q", "r"]
          [{ pk := 5, label := "e" }]))) :
    ¬ problem_spec_orderedChoices true [] ["p", "q", "r"]
        [{ pk := 5, label := "e" }]
        (implementation_orderedChoices true [] ["p", "q", "r"]
          [{ pk := 5, label := "e" }]) := by
""" + _U_ORDERED + "  exact h\n"

# (R5) BLANK PREFIX ALWAYS — the leading blank choice is prepended regardless of
# the flag that is supposed to select it.
_RIVAL_BLANK_ALWAYS = _swap(_BASE, _IMPL_ORDERED, """  let mut qs := objs
  if ordering ≠ [] then
    qs := applyOrdering ordering objs
  return blank ++ qs.map toChoice
""")
_W_BLANK_ALWAYS = """
example : ¬ problem_spec_orderedChoices false [((0 : Int), "-")] [] []
    (implementation_orderedChoices false [((0 : Int), "-")] [] []) := by
""" + _U_ORDERED

# (R6) BLANK PREFIX NEVER — the flag is ignored the other way: the prefix is
# dropped even when it is requested.
_RIVAL_BLANK_NEVER = _swap(_BASE, _IMPL_ORDERED, """  let mut qs := objs
  if ordering ≠ [] then
    qs := applyOrdering ordering objs
  return qs.map toChoice
""")
_W_BLANK_NEVER = """
example : ¬ problem_spec_orderedChoices true [((0 : Int), "-")] []
    [{ pk := 1, label := "a" }]
    (implementation_orderedChoices true [((0 : Int), "-")] []
      [{ pk := 1, label := "a" }]) := by
""" + _U_ORDERED

# (R6b) BLANK PREFIX VALUE — the flag is honored in BOTH polarities and the
# prefix lands in the right place, but a fixed constant is prepended instead of
# the prefix the caller actually supplied. This is the sub-clause the other two
# blank rivals leave unattacked: `rival-blank-always` and `rival-blank-never`
# both differ from the spec in the prefix's PRESENCE, so either would still be
# refuted by a spec that pinned only "some one-entry prefix when requested".
# Observably differs from gold exactly when the supplied prefix is not that
# constant, so its witness must carry a `blank` value distinct from the one every
# other witness uses.
_RIVAL_BLANK_VALUE = _swap(_BASE, _IMPL_ORDERED, """  let mut qs := objs
  if ordering ≠ [] then
    qs := applyOrdering ordering objs
  return (if includeBlank then [((0 : Int), "-")] else []) ++ qs.map toChoice
""")
_W_BLANK_VALUE = """
example : ¬ problem_spec_orderedChoices true [((9 : Int), "z")] []
    [{ pk := 4, label := "d" }]
    (implementation_orderedChoices true [((9 : Int), "z")] []
      [{ pk := 4, label := "d" }]) := by
""" + _U_ORDERED

# (R7) CONCATENATION ORDER — the blank choice is APPENDED rather than prepended.
# The right multiset of choices, the wrong arrangement.
_RIVAL_BLANK_SUFFIX = _swap(_BASE, _IMPL_ORDERED, """  let mut qs := objs
  if ordering ≠ [] then
    qs := applyOrdering ordering objs
  return qs.map toChoice ++ (if includeBlank then blank else [])
""")
_W_BLANK_SUFFIX = """
example : ¬ problem_spec_orderedChoices true [((0 : Int), "-")] []
    [{ pk := 7, label := "g" }]
    (implementation_orderedChoices true [((0 : Int), "-")] []
      [{ pk := 7, label := "g" }]) := by
""" + _U_ORDERED + "  decide\n"

# (R8) THE SECOND BUG — the restricted listing DISCARDS the configuration's
# directive and always presents the default order. This is the pre-patch
# behavior `Solution_prepatch_2.lean` reverts to.
_RIVAL_RESTRICTED_DROP = _swap(_BASE, _IMPL_RESTRICTED,
                               """  return implementation_orderedChoices false [] [] objs
""")
_W_RESTRICTED_DROP = """
example (h : ¬ ([toChoice { pk := 1, label := "a" }]
      = List.map toChoice (applyOrdering ["x"] [{ pk := 1, label := "a" }]))) :
    ¬ problem_spec_restrictedChoices (some ["x"]) [{ pk := 1, label := "a" }]
        (implementation_restrictedChoices (some ["x"])
          [{ pk := 1, label := "a" }]) := by
""" + _U_RESTRICTED + "  exact h\n"

# (R9) THE RESTRICTED LISTING'S FIXED ARGUMENTS — it forwards the directive
# correctly but ALSO prepends a leading blank choice, which this path must not
# have.
_RIVAL_RESTRICTED_BLANK = _swap(_BASE, _IMPL_RESTRICTED, """  let ordering := configuredOrdering adminOrdering
  return implementation_orderedChoices true [((0 : Int), "-")] ordering objs
""")
_W_RESTRICTED_BLANK = """
example : ¬ problem_spec_restrictedChoices none
    [{ pk := 2, label := "b" }, { pk := 3, label := "c" }]
    (implementation_restrictedChoices none
      [{ pk := 2, label := "b" }, { pk := 3, label := "c" }]) := by
""" + _U_RESTRICTED

# (R10) THE PRIMITIVE'S RECORD ARGUMENT — added by audit. Every other rival that
# touches the non-empty arm attacks WHETHER the primitive is consulted (never /
# only for multi-key / on the wrong branch). None attacks WHAT it is consulted
# ON, and the spec's non-empty arm pins two arguments, not one: the directive AND
# the collection. This rival consults the primitive on a PERMUTED collection, so
# the guard fires on exactly the right inputs and the primitive is genuinely
# applied — only its record argument is not the collection the caller passed.
# A spec that pinned merely "the non-empty arm calls the primitive on the
# directive" would admit it.
_RIVAL_PRIMITIVE_ARG = _swap(_BASE, _IMPL_ORDERED, """  let mut qs := objs
  if ordering ≠ [] then
    qs := applyOrdering ordering objs.reverse
  return (if includeBlank then blank else []) ++ qs.map toChoice
""")
_W_PRIMITIVE_ARG = """
example (h : ¬ (List.map toChoice (applyOrdering ["y"]
        (List.reverse [{ pk := 6, label := "f" }, { pk := 8, label := "h" }]))
      = List.map toChoice (applyOrdering ["y"]
        [{ pk := 6, label := "f" }, { pk := 8, label := "h" }]))) :
    ¬ problem_spec_orderedChoices true [((0 : Int), "-")] ["y"]
        [{ pk := 6, label := "f" }, { pk := 8, label := "h" }]
        (implementation_orderedChoices true [((0 : Int), "-")] ["y"]
          [{ pk := 6, label := "f" }, { pk := 8, label := "h" }]) := by
""" + _U_ORDERED + "  exact h\n"

# (R11) THE PRIMITIVE'S DIRECTIVE ARGUMENT — added by audit, the mirror of R10 on
# the other argument. The primitive is consulted on the right collection, under
# the right guard, but the directive handed to it is a PERTURBED copy of the one
# supplied (each key duplicated). The spec pins `applyOrdering ordering objs`, so
# the directive that reaches the primitive must be the caller's own; without that,
# the non-empty arm would constrain only that SOME directive is used. Distinct
# from R3 (`rival-multi-key-only`), which changes the guard's threshold and leaves
# the argument alone.
_RIVAL_PRIMITIVE_DIRECTIVE = _swap(_BASE, _IMPL_ORDERED, """  let mut qs := objs
  if ordering ≠ [] then
    qs := applyOrdering (ordering ++ ordering) objs
  return (if includeBlank then blank else []) ++ qs.map toChoice
""")
_W_PRIMITIVE_DIRECTIVE = """
example (h : ¬ (List.map toChoice (applyOrdering (["x"] ++ ["x"]) [{ pk := 1, label := "a" }])
      = List.map toChoice (applyOrdering ["x"] [{ pk := 1, label := "a" }]))) :
    ¬ problem_spec_orderedChoices false [] ["x"] [{ pk := 1, label := "a" }]
        (implementation_orderedChoices false [] ["x"] [{ pk := 1, label := "a" }]) := by
""" + _U_ORDERED + "  exact h\n"


# ---------------------------------------------------------------------------
# Shared refinement argument for the directive-split rivals. Every one of them
# would, as a faithful real patch, leave a supplied-directive or an
# empty-directive listing in the wrong arrangement, which is exactly what the
# F2P assertions read back.
# ---------------------------------------------------------------------------

_REF_EMPTY = (
    "its faithful real patch consults the re-sequencing primitive on the EMPTY "
    "directive, and doing so is what DISCARDS the collection's own default "
    "presentation order — the defect the issue reports. The F2P assertions "
    "configure a related collection with a default order, request its choices "
    "with no explicit directive, and require the default order back; this "
    "variant returns the primitive's empty-directive arrangement instead, so it "
    "would NOT resolve.")

_REF_NONEMPTY = (
    "its faithful real patch skips the re-sequencing primitive on a directive "
    "the caller did supply, so a listing requested with an explicit directive "
    "comes back in the collection's default order. The F2P/P2P assertions "
    "supply single-key directives (ascending and descending) and read the "
    "requested arrangement back, so it would NOT resolve.")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-explicit-else", "kind": "soundness", "expect": "verify",
     "module": _POS_EXPLICIT_ELSE,
     "rationale": "a CORRECT impl of the first obligation with a different "
                  "control shape: an explicit two-branch if/else with the "
                  "empty-directive case stated first and one return per branch, "
                  "instead of the mutable accumulator with a fall-through. The "
                  "obligation is re-proved for the new shape with its STATEMENT "
                  "byte-identical. Must verify; if not, the postcondition is "
                  "over-fit to one branch order / one return point => "
                  "SPEC-TOO-STRONG. Also the cheapest HONEST impl on the "
                  "non-empty branch: the re-sequencing primitive is opaque and "
                  "unconstrained, so the only way to satisfy that arm is to "
                  "apply the primitive — there is no oracle to echo."},
    {"id": "pos-single-bind", "kind": "soundness", "expect": "verify",
     "module": _POS_SINGLE_BIND,
     "rationale": "a CORRECT impl of the first obligation that lifts the "
                  "directive split out of the statement sequence into one pure "
                  "`let` bound to a conditional expression, assembling the "
                  "result once — no mutable local, no early return. Must "
                  "verify; if not, the spec is over-fit to the imperative "
                  "accumulator form => SPEC-TOO-STRONG."},
    {"id": "pos-match-option", "kind": "soundness", "expect": "verify",
     "module": _POS_MATCH_OPTION,
     "rationale": "a CORRECT impl of the SECOND obligation, which the other two "
                  "positives leave at its frozen form: the configuration "
                  "lookup is inlined as an explicit case analysis over the "
                  "optional directive rather than funneled through the shared "
                  "selector, and the proof splits the same way, closing each arm "
                  "through the inner obligation's own theorem. Must verify; if "
                  "not, the layered spec is over-fit to the selector's "
                  "syntactic form => SPEC-TOO-STRONG."},
    {"id": "admiss-f2p-shaped-points", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "the ADMISSIBILITY lane, ported from the nagini sibling's "
                  "`admiss-self-call`. Both frozen obligations are "
                  "unconditionally quantified, so there is no precondition to "
                  "over-constrain; the analogue on this total carrier is the "
                  "obligation being UNSATISFIABLE at an F2P-shaped input, which "
                  "this case tests directly: each obligation is discharged at "
                  "concrete F2P-shaped points BY EVALUATION as a `have`, before "
                  "the frozen obligation is closed verbatim. The points are a "
                  "two-record collection under (a) the EMPTY directive, closed "
                  "by `decide` so the equation is genuinely DECIDED on ground "
                  "data rather than rewritten — this is the sub-domain the "
                  "reported defect lives in; (b) a SUPPLIED one-key directive, "
                  "closed by `rfl` on the primitive's own application; and (c) "
                  "the restricted listing with a CONFIGURED directive, closed "
                  "through the inner obligation's theorem. Must verify; if not, "
                  "the modeled behavior is unsatisfiable at exactly a normal "
                  "F2P-shaped input => PRECOND-TOO-STRONG. Nothing is assumed: "
                  "no new declaration, both STATEMENTS byte-identical."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-unconditional-reorder", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_UNCONDITIONAL,
     "refinement": _REF_EMPTY,
     "rationale": "the DISCRIMINATING defect: the re-sequencing primitive is "
                  "applied unconditionally, so the empty directive is routed "
                  "through it too. Rejection source: the DIRECTIVE SPLIT clause "
                  "`if ordering = [] then objs else applyOrdering ordering objs` "
                  "at `ordering = []`, where the spec pins the result to `objs` "
                  "and the primitive is unconstrained — `applyOrdering [] objs` "
                  "is not provably `objs`, so the equation cannot be "
                  "discharged. If it verified => SPEC-TOO-WEAK (the spec would "
                  "admit the very defect). The witness conditions on the "
                  "primitive at the one point it is applied: whenever its "
                  "empty-directive result on a one-record collection differs "
                  "from that collection's own choice list, the rival's answer "
                  "differs from the spec's — which is exactly the sub-domain "
                  "where routing through the primitive is wrong.",
     "witness": _W_UNCONDITIONAL},
    {"id": "rival-invert-directive-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INVERT,
     "refinement": _REF_EMPTY + " It is additionally wrong the other way: a "
                   "supplied directive is ignored, so it also fails the "
                   "explicit-directive assertions. " + _REF_NONEMPTY,
     "rationale": "control-flow rival: the directive guard is INVERTED, so the "
                  "primitive fires exactly when the directive is empty. "
                  "Rejection source: the DIRECTIVE SPLIT clause, violated on "
                  "BOTH arms — the empty directive gets the primitive's "
                  "arrangement where `objs` is required, and a non-empty "
                  "directive gets `objs` where the primitive's arrangement is "
                  "required. If it verified => SPEC-TOO-WEAK (the guard's "
                  "direction would be unconstrained). The witness probes the "
                  "NON-EMPTY arm at a two-key directive, with the blank prefix "
                  "requested so the prefix is carried through the refutation "
                  "rather than held at the empty list.",
     "witness": _W_INVERT},
    {"id": "rival-multi-key-only", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_MULTI_ONLY,
     "refinement": "its faithful real patch guards the re-sequencing on a "
                   "directive of more than one key, so a SINGLE-key directive is "
                   "silently treated as no directive at all. The F2P/P2P "
                   "assertions supply exactly single-key directives (a field "
                   "ascending, and the same field descending) and read the "
                   "requested arrangement back, so it would NOT resolve.",
     "rationale": "partial-domain near-miss: correct on the empty directive AND "
                  "on multi-key directives, wrong only on the single-key "
                  "sub-domain — it agrees with gold over strictly more of the "
                  "domain than `rival-never-reorder`, so it gets its own "
                  "witness at a SINGLE-key directive, the input that "
                  "distinguishes the two. Rejection source: the DIRECTIVE "
                  "DOMAIN — the spec's non-empty arm requires the primitive's "
                  "arrangement for EVERY non-empty directive, and a one-key "
                  "directive yields the default order instead. If it verified "
                  "=> SPEC-TOO-WEAK (domain-incomplete on the re-sequencing "
                  "arm). The witness also carries a two-record collection, so "
                  "the traversal is exercised on a shape no other witness uses.",
     "witness": _W_MULTI_ONLY},
    {"id": "rival-never-reorder", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NEVER_REORDER,
     "refinement": "its faithful real patch never consults the re-sequencing "
                   "primitive at all, so every listing comes back in the "
                   "collection's default order even when a directive is "
                   "supplied. That fails every explicit-directive assertion in "
                   "the F2P/P2P set, so it would NOT resolve.",
     "rationale": "the re-sequencing branch is removed outright. Rejection "
                  "source: the DIRECTIVE SPLIT clause on its non-empty arm — "
                  "the default-order carrier is not provably equal to the "
                  "primitive's arrangement. Distinct from "
                  "`rival-multi-key-only`, which is wrong only for a one-key "
                  "directive, so this witness probes a THREE-key directive: "
                  "the point where this rival is wrong and that one is right, "
                  "which is what makes the two rationales' sub-domain claims "
                  "separately demonstrated.",
     "witness": _W_NEVER_REORDER},
    {"id": "rival-blank-always", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BLANK_ALWAYS,
     "refinement": "its faithful real patch prepends the leading blank choice "
                   "unconditionally, ignoring the flag that selects it. The "
                   "P2P set reads choice lists requested WITHOUT the blank "
                   "entry (the restricted and filter paths request exactly "
                   "that) and compares them element-wise against the expected "
                   "lists, so an extra leading entry fails them; it would NOT "
                   "resolve.",
     "rationale": "attacks the BLANK PREFIX clause `if includeBlank then blank "
                  "else []` at `includeBlank = false`, where the spec requires "
                  "no prefix. Rejection source: that clause alone — the "
                  "directive handling is untouched and correct. If it verified "
                  "=> SPEC-TOO-WEAK (the flag would be unconstrained in one "
                  "polarity). Witness `decide`s outright: it probes the "
                  "empty-directive sub-domain on an EMPTY collection, so the "
                  "opaque primitive never appears and the whole equation is "
                  "ground data — the extra prefix is the only difference.",
     "witness": _W_BLANK_ALWAYS},
    {"id": "rival-blank-never", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BLANK_NEVER,
     "refinement": "its faithful real patch drops the leading blank choice even "
                   "when it is requested — a regression in behavior this change "
                   "is supposed to leave alone, since the prefix is prepended by "
                   "the same expression the ordering guard sits in and any edit "
                   "there can break it. Honest scope note: the assertions in "
                   "THIS instance's F2P/P2P set that read the modeled "
                   "related-collection listing all request it WITHOUT a leading "
                   "entry, so they would not themselves catch the drop; the "
                   "callers that do request one (a listing rendered as radio "
                   "inputs, and the non-relational choice paths that share this "
                   "entry point) are covered elsewhere in the suite. The case is "
                   "therefore carried for its SPEC value — see the rationale — "
                   "and its refinement claim is the weaker 'regresses a "
                   "preserved behavior', not 'fails an assertion in this set'.",
     "rationale": "the mirror of `rival-blank-always`: same clause, opposite "
                  "polarity of the flag. Both are needed — a spec that pinned "
                  "the prefix in only one direction would admit one of them. "
                  "Rejection source: the BLANK PREFIX clause at `includeBlank "
                  "= true`, where the requested prefix is missing from the "
                  "result. Witness `decide`s on a one-record collection under "
                  "the empty directive.",
     "witness": _W_BLANK_NEVER},
    {"id": "rival-blank-wrong-value", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BLANK_VALUE,
     "refinement": "its faithful real patch hardcodes the leading entry instead "
                   "of prepending the one its caller passed in. The prefix is a "
                   "caller-supplied argument precisely because different callers "
                   "need different leading text, and a caller that asks for its "
                   "own wording would silently get the default instead. Same "
                   "honest scope note as `rival-blank-never`: the assertions in "
                   "THIS instance's set that read the modeled listing request no "
                   "leading entry, so the substitution is invisible to them; the "
                   "case is carried for its SPEC value (the prefix's contents are "
                   "a named binder the spec must pin) rather than on a claim that "
                   "it fails an assertion here.",
     "rationale": "attacks the BLANK PREFIX clause's second, independent "
                  "sub-clause: not WHETHER a prefix appears but WHICH one. This "
                  "rival honors the flag in both polarities and puts the prefix "
                  "in the right position, so neither `rival-blank-always` nor "
                  "`rival-blank-never` nor `rival-blank-suffix` covers it — all "
                  "three differ from the spec in the prefix's presence or "
                  "placement, and each would still be refuted by a spec that "
                  "pinned only 'a one-entry prefix exactly when requested'. "
                  "Rejection source: the `blank` binder itself, which the spec "
                  "names as the thing prepended. If it verified => "
                  "SPEC-TOO-WEAK (the prefix's CONTENTS would be free). Witness "
                  "`decide`s under the empty directive, on the only `blank` "
                  "value in the battery that differs from the rival's constant "
                  "— the point at which the substitution is observable at all.",
     "witness": _W_BLANK_VALUE},
    {"id": "rival-blank-suffix", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BLANK_SUFFIX,
     "refinement": "its faithful real patch appends the leading blank choice "
                   "after the record choices instead of before them. The blank "
                   "entry's whole purpose is to be the FIRST, pre-selected "
                   "option, and the P2P assertions compare the choice list "
                   "element-wise in order, so it would NOT resolve.",
     "rationale": "attacks the CONCATENATION ORDER independently of the other "
                  "clauses: this rival produces exactly the right MULTISET of "
                  "choices, with the prefix present exactly when requested and "
                  "the directive handled correctly — only the arrangement is "
                  "wrong. It is therefore the case that would survive a spec "
                  "stated as a set/permutation rather than an equality of "
                  "lists; on the one-record witness point its result is exactly "
                  "the spec's answer with the two entries transposed. If "
                  "it verified => SPEC-TOO-WEAK (the result's ORDER would be "
                  "unconstrained). Witness `decide`s on a one-record "
                  "collection whose key and label are distinct from every "
                  "other witness's.",
     "witness": _W_BLANK_SUFFIX},
    {"id": "rival-restricted-drop-directive", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_RESTRICTED_DROP,
     "refinement": "its faithful real patch omits the directive when the "
                   "restricted listing delegates to the inner one, so the "
                   "narrowed record set is presented unordered — the second "
                   "half of the reported defect. The F2P assertions read the "
                   "restricted listing back and require the configured order, "
                   "so it would NOT resolve.",
     "rationale": "the DISCRIMINATING defect of the SECOND obligation: the "
                  "configuration's directive is DISCARDED instead of forwarded. "
                  "Rejection source: the FORWARDED DIRECTIVE — the layered spec "
                  "pins the result to the inner relation at `configuredOrdering "
                  "adminOrdering`, and this variant supplies the empty "
                  "directive there instead, so the inner directive split takes "
                  "the wrong arm. If it verified => SPEC-TOO-WEAK (the second "
                  "behavior's whole content would be unconstrained). The "
                  "witness probes `adminOrdering = some [\"x\"]` — the regime "
                  "where a directive IS configured, the only regime in which "
                  "discarding it is observable — and conditions on the "
                  "primitive there.",
     "witness": _W_RESTRICTED_DROP},
    {"id": "rival-restricted-adds-blank", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_RESTRICTED_BLANK,
     "refinement": "its faithful real patch forwards the directive correctly "
                   "but also requests the leading blank choice on a path that "
                   "must not have one. The assertions that read the restricted "
                   "listing compare it element-wise against the expected "
                   "choices with no leading entry, so it would NOT resolve.",
     "rationale": "attacks the SECOND obligation's FIXED ARGUMENTS rather than "
                  "its directive: the layered spec pins the inner call's blank "
                  "flag to `false` and its blank list to `[]`, and this variant "
                  "supplies `true` and a non-empty prefix. Rejection source: "
                  "those pinned arguments — without them the layered spec would "
                  "constrain only the directive and leave the prefix free. "
                  "Witness probes `adminOrdering = none` (the OTHER regime of "
                  "that binder, complementing the drop-directive rival's "
                  "`some`), on a two-record collection, and `decide`s: with no "
                  "configured directive the primitive never appears.",
     "witness": _W_RESTRICTED_BLANK},
    {"id": "rival-primitive-wrong-records", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PRIMITIVE_ARG,
     "refinement": "its faithful real patch re-sequences a permuted copy of the "
                   "record set rather than the set the caller narrowed, so a "
                   "listing requested with an explicit directive comes back "
                   "re-sequenced from the wrong starting arrangement. The "
                   "re-sequencing primitive is not a total order on this data "
                   "(records tie on the sort key, and the primitive is documented "
                   "as consulted rather than specified), so a tie broken by input "
                   "position lands in a different arrangement. The F2P/P2P "
                   "assertions supply single-key directives and compare the "
                   "resulting choice list element-wise, so it would NOT resolve.",
     "rationale": "added by AUDIT to close an unattacked sub-clause. The spec's "
                  "non-empty arm is `applyOrdering ordering objs` — TWO pinned "
                  "arguments — and every pre-existing rival on that arm attacks "
                  "only WHETHER the primitive is consulted (`rival-never-reorder`: "
                  "never; `rival-multi-key-only`: only above a key threshold; "
                  "`rival-invert-directive-guard`: on the wrong branch). None "
                  "attacks WHAT it is consulted on. This rival fires the guard on "
                  "exactly the right inputs and genuinely applies the primitive, "
                  "differing only in its record argument, so it is the case a spec "
                  "stated as `∃ p, result = p objs` — the primitive is applied to "
                  "SOMETHING — would admit. Rejection source: the record argument "
                  "of the non-empty arm. If it verified => SPEC-TOO-WEAK. The "
                  "witness conditions on the carrier at the one point the argument "
                  "differs (the primitive is opaque, so nothing computes on that "
                  "arm) and uses a record pair and a directive key no other "
                  "witness uses.",
     "witness": _W_PRIMITIVE_ARG},
    {"id": "rival-primitive-wrong-directive", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PRIMITIVE_DIRECTIVE,
     "refinement": "its faithful real patch hands the primitive a perturbed copy "
                   "of the directive (each sort key repeated) instead of the "
                   "directive it was given. The directive is a caller-supplied "
                   "argument whose content selects the arrangement, so a "
                   "perturbation of it is a perturbation of the answer for any "
                   "directive the perturbation does not fix. It would NOT resolve "
                   "on the explicit-directive assertions.",
     "rationale": "added by AUDIT as the mirror of `rival-primitive-wrong-records` "
                  "on the OTHER pinned argument of the non-empty arm. Consults the "
                  "primitive on the right collection under the right guard, but "
                  "with a directive that is not the caller's. Distinct from "
                  "`rival-multi-key-only`, which moves the guard's THRESHOLD and "
                  "leaves both arguments alone: this one leaves the guard exactly "
                  "as the spec has it. Rejection source: the directive argument of "
                  "the non-empty arm — the spec names `ordering` itself as what "
                  "reaches the primitive. If it verified => SPEC-TOO-WEAK (the "
                  "directive's content would be free once its emptiness was "
                  "settled). Witness conditions on the carrier at a single-key "
                  "directive, on a `blank`/`includeBlank`/record combination "
                  "distinct from every other witness's.",
     "witness": _W_PRIMITIVE_DIRECTIVE},
]
