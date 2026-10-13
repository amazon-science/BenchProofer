"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9229 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a FULL
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte — region
surgery touches only text inside an ``-- impl-start`` / ``-- impl-end`` region
and, where a case legitimately re-proves, inside the matching ``-- proof-start``
/ ``-- proof-end`` region. Both regions are elided by the consumer spec view, so
``markers.same_spec`` holds by construction, and both ``theorem correct_getDoc``
/ ``theorem correct_addContent`` STATEMENTS stay byte-identical (only the tactic
bodies differ). ``expect:"verify"`` passes iff (in scope AND the file elaborates
with every obligation closed, no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``/``lemma``); ``expect:"reject"`` passes iff (in scope AND it
does NOT verify AND the case's refutation ``witness`` discriminates: it
elaborates against the rival and FAILS against the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier; full case-by-case
accounting in the footer. The nagini sibling contracts the SAME TWO changed
decisions this bundle models, so the port is unusually close to one-for-one —
what does NOT carry over is nagini's fractional-permission machinery (its
frame-mutation lane) and its object-identity clauses, both of which are
meaningless on a referentially transparent carrier. Those are recorded as
VACUOUS / RE-AIMED in the footer, never fabricated.

DEFENDED SURFACE (two obligations; the ``axioms`` region is EMPTY, so every
sub-computation is a closed total function of the free inputs and there is no
opaque callee anywhere on this carrier — every rival is refutable at a concrete
literal point, with no need to condition on the carrier).

  * ``problem_spec_getDoc docAsAttr comment normalDoc result`` — TWO independent
    top-level conjuncts:
      (A1) ``docAsAttr = true →
              (commentPresent comment = true  → result = some []) ∧
              (commentPresent comment = false → result = none)``
           the alias-regime decision in BOTH directions: a PRESENT but EMPTY
           documentation block when a comment is present, and NO block at all
           when it is absent. ``some []`` and ``none`` are genuinely different
           results driving different downstream rendering; nothing on this
           carrier can collapse them.
      (A2) ``docAsAttr = false → result = normalDoc``
           the ordinary regime is UNCHANGED: the ordinary block is forwarded.
           This is the frame conjunct — the analogue of nagini's read-only
           obligation on that input.

  * ``problem_spec_addContent docAsAttr comment aliasText incoming result`` —
    TWO independent top-level conjuncts:
      (B1) ``docAsAttr = true ∧ commentPresent comment = false →
              result = some ["alias of " ++ aliasText]``
           the substitution arm: an alias carrying no comment gets a single
           line describing its target, and the line's CONTENT is pinned to the
           rendered target description — grounded in the input ``aliasText``,
           not in an answer key.
      (B2) ``(docAsAttr = false ∨ commentPresent comment = true) →
              result = incoming``
           the pass-through arm: everything else forwards the caller-supplied
           content unchanged. The frame conjunct for this obligation.

``commentPresent`` collapses ``none`` (the lookup did not succeed) and
``some []`` (it succeeded and produced nothing) to the SAME decision while
keeping them DISTINCT inputs, so a rival keying on ``isSome``/``isNone`` instead
of on non-emptiness is wrong on exactly one of the three comment shapes. Neither
obligation carries a precondition: every input is free.

BEHAVIOURAL DISCRIMINATOR. Pre-image behaviour treated EVERY alias the same —
no documentation block, and the target-description line always substituted for
the incoming content — so an alias that does carry a comment attached to its own
name had that comment discarded and was rendered with the default target line
instead. The two ``weak-*-prepatch`` rivals below ARE that pre-image behaviour,
one per obligation, and each is the G-DIFF prepatch of the corresponding
``Solution_prepatch*.lean``.

WITNESS MECHANICS. On a tactic-proof backend "did not verify" is the DEFAULT
outcome of reshaping an implementation — the frozen script is tuned to the frozen
form — so a rejection ALONE attributes nothing to the spec. Every reject case
therefore carries a Lean snippet stating ``¬ problem_spec_<name> <literals>
(implementation_<name> <literals>)`` and closing by ``decide`` after unfolding
the spec, the impl and ``commentPresent``. Every input is a ``Bool`` /
``Option (List String)`` / ``String`` / ``Option (List (List String))`` literal
and both impls are loop-free, so the goal reduces in the kernel. Confirmed
during authoring with two real ``lake env lean`` builds per case: rival build
exit 0, gold build exit 1 failing with ``Tactic `decide` proved that the
proposition ... is false`` — i.e. gold genuinely SATISFIES the spec at that
point, so the witness is a real discriminator and not an elaboration error, an
unknown name, or a timeout. No witness binds anything in its head, so no
consistency probe applies and none can be a forgery resting on contradictory
hypotheses.

BINDER / CLAUSE COVERAGE. Twelve reject witnesses at twelve DISTINCT input
points, six per obligation. Every input binder of both obligations is moved:
  * ``getDoc``: ``docAsAttr`` off ``true`` (weak-A-ignore-regime); ``comment``
    over all three shapes — non-empty single-line (weak-A-prepatch,
    weak-A-forward-normal), non-empty MULTI-line (weak-A-swap), ``none``
    (weak-A-always-empty), ``some []`` (weak-A-someness); ``normalDoc`` over
    ``none`` (weak-A-swap), a one-element block, and a TWO-element block
    (weak-A-ignore-regime, weak-A-forward-normal — which is what makes a
    substituted block observable rather than accidentally equal).
  * ``addContent``: ``docAsAttr`` off ``true`` (weak-B-ignore-regime);
    ``comment`` over all three shapes — non-empty single-line
    (weak-B-prepatch), multi-line (weak-B-swap), ``none`` (weak-B-never,
    weak-B-bare-label), ``some []`` (weak-B-noneness); ``aliasText`` over five
    distinct values; ``incoming`` over ``none`` (weak-B-noneness), a
    one-element and a TWO-element block (weak-B-bare-label).
Clause coverage: (A1) by weak-A-prepatch / weak-A-always-empty / weak-A-swap /
weak-A-someness / weak-A-forward-normal; (A2) by weak-A-ignore-regime, the only
site-A rival that moves the regime selector and therefore the only one able to
attack the frame conjunct. (B1) by weak-B-never / weak-B-swap /
weak-B-noneness / weak-B-bare-label; (B2) by weak-B-prepatch / weak-B-swap /
weak-B-ignore-regime.

AXIOM lane: DROPPED. ``meta.json`` records no consumed axiom and no deep-model
reference — the ``axioms`` region is empty and the rendered target description is
carried as the free input ``aliasText`` — so there is no axiom face to probe. The
axiom lane is G-AX's job and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9229"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Frozen region anchors. Each lies WHOLLY inside the region named and is unique
# in the file (both re-asserted at load by _swap / the asserts below), so the
# manifest breaks loudly if the frozen solution ever changes.
# ---------------------------------------------------------------------------

# -- impl regions (the two decision bodies, VERBATIM) --
_IMPL_A = """  if docAsAttr then
    if commentPresent comment then
      return some []
    else
      return none
  return normalDoc"""

_IMPL_B = """  if docAsAttr && (! commentPresent comment) then
    return some ["alias of " ++ aliasText]
  return incoming"""

# -- proof regions (whole tactic bodies, VERBATIM) — replaced only by the two
# positives, which reshape the impl and therefore must re-prove. The theorem
# STATEMENTS are NOT part of these anchors, so they stay byte-identical. --
_PROOF_A = """  intro docAsAttr comment normalDoc
  unfold problem_spec_getDoc implementation_getDoc
  refine ⟨fun hattr => ⟨fun hc => ?_, fun hc => ?_⟩, fun hattr => ?_⟩
  · simp only [Id.run, hattr, hc, if_true]; rfl
  · simp only [Id.run, hattr, hc, if_true, Bool.false_eq_true, if_false]; rfl
  · simp only [Id.run, hattr, Bool.false_eq_true, if_false]; rfl"""

_PROOF_B = """  intro docAsAttr comment aliasText incoming
  unfold problem_spec_addContent implementation_addContent
  refine ⟨fun h => ?_, fun h => ?_⟩
  · obtain ⟨h1, h2⟩ := h
    simp only [Id.run, h1, h2, Bool.not_false, Bool.and_true, if_true]; rfl
  · rcases h with h | h
    · simp only [Id.run, h, Bool.false_and, Bool.false_eq_true, if_false]; rfl
    · simp only [Id.run, h, Bool.not_true, Bool.and_false, Bool.false_eq_true, if_false]; rfl"""

# -- the `intro` line of each proof body: where an admissibility case prepends a
# ground `have` without touching the statement or the spec view. --
_INTRO_A = "  intro docAsAttr comment normalDoc"
_INTRO_B = "  intro docAsAttr comment aliasText incoming"

# -- the first decision's `def` header. The impl region starts AT this line, so a
# rival may replace it (and prepend a helper) without leaving the region. --
_DEF_A = "def implementation_getDoc (docAsAttr"

for _anchor in (_IMPL_A, _IMPL_B, _PROOF_A, _PROOF_B, _INTRO_A, _INTRO_B, _DEF_A):
    if _BASE.count(_anchor) != 1:
        raise AssertionError(f"frozen anchor drifted or is not unique: {_anchor[:48]!r}")


def _impl_a(body):
    """Full Solution.lean variant with ONLY the first decision's impl replaced."""
    return _swap(_BASE, _IMPL_A, body)


def _impl_b(body):
    """Full Solution.lean variant with ONLY the second decision's impl replaced."""
    return _swap(_BASE, _IMPL_B, body)


# ---------------------------------------------------------------------------
# Witness scaffolds. Each states the frozen spec predicate's NEGATION at one
# concrete input tuple and closes by kernel reduction. Nothing is bound in the
# head, so every probed point is a literal the reader can evaluate.
# ---------------------------------------------------------------------------
def _w_a(doc_as_attr, comment, normal_doc):
    return (f"example : ¬ problem_spec_getDoc {doc_as_attr} {comment} {normal_doc}\n"
            f"    (implementation_getDoc {doc_as_attr} {comment} {normal_doc}) := by\n"
            "  unfold problem_spec_getDoc implementation_getDoc commentPresent\n"
            "  decide\n")


def _w_b(doc_as_attr, comment, alias_text, incoming):
    return (f"example : ¬ problem_spec_addContent {doc_as_attr} {comment} "
            f"{alias_text} {incoming}\n"
            f"    (implementation_addContent {doc_as_attr} {comment} "
            f"{alias_text} {incoming}) := by\n"
            "  unfold problem_spec_addContent implementation_addContent "
            "commentPresent\n"
            "  decide\n")


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify, else SPEC-TOO-STRONG. Each reshapes the control flow, so each
# re-proves inside its own `-- proof-start`/`-- proof-end` region; the
# `theorem correct_*` statements stay byte-identical and no helper lemma, new
# axiom or assumption token is introduced. Both confirmed with a real build.
# ---------------------------------------------------------------------------

# Handle the ORDINARY regime FIRST with an early return, then the two alias
# sub-cases as a flat sequence (no nested else). Same three observable outcomes
# on exactly the same inputs. The re-proof is the frozen skeleton with the
# branch-reduction lemmas the new guard shape needs (`Bool.not_true` /
# `Bool.not_false`) in place of the frozen ones.
_POS_A = """  if ! docAsAttr then
    return normalDoc
  if commentPresent comment then
    return some []
  return none"""

_POS_A_PROOF = """  intro docAsAttr comment normalDoc
  unfold problem_spec_getDoc implementation_getDoc
  refine ⟨fun hattr => ⟨fun hc => ?_, fun hc => ?_⟩, fun hattr => ?_⟩
  · simp only [Id.run, hattr, hc, Bool.not_true, Bool.false_eq_true, if_false,
      if_true]; rfl
  · simp only [Id.run, hattr, hc, Bool.not_true, Bool.false_eq_true, if_false]; rfl
  · simp only [Id.run, hattr, Bool.not_false, if_true]; rfl"""

# The De Morgan dual of the frozen gate: pull the FORWARD-UNCHANGED case out
# first (`not in the alias regime, OR a comment is present`), leaving the
# substitution on exactly the remaining sub-domain. Identical semantics on every
# input; the re-proof swaps the frozen conjunction lemmas for the disjunction
# ones (`Bool.or_self` / `Bool.true_or` / `Bool.or_true`).
_POS_B = """  if (! docAsAttr) || commentPresent comment then
    return incoming
  return some ["alias of " ++ aliasText]"""

_POS_B_PROOF = """  intro docAsAttr comment aliasText incoming
  unfold problem_spec_addContent implementation_addContent
  refine ⟨fun h => ?_, fun h => ?_⟩
  · obtain ⟨h1, h2⟩ := h
    simp only [Id.run, h1, h2, Bool.not_true, Bool.or_self, Bool.false_eq_true,
      if_false]; rfl
  · rcases h with h | h
    · simp only [Id.run, h, Bool.not_false, Bool.true_or, if_true]; rfl
    · simp only [Id.run, h, Bool.or_true, if_true]; rfl"""


# ---------------------------------------------------------------------------
# ADMISSIBILITY (re-aimed). Neither obligation carries a precondition, so
# nagini's "the fractional half-permissions ADMIT a normal input" probe has no
# counterpart: nothing here could exclude an in-domain input. Re-aimed at the
# residual admissibility risk on a total domain — that the post-image is
# UNSATISFIABLE or DEGENERATE at exactly the points the modeled behaviour
# targets (a spec no impl can meet reads exactly like a spec every impl meets).
# Each case discharges the spec predicate BY EVALUATION at all four interesting
# points as an anonymous `have` prepended to the frozen tactic body, then closes
# the frozen obligation verbatim. Nothing is assumed: no new declaration, the
# statements stay byte-identical, and the impl is untouched so every clause of
# both obligations still discharges. Both confirmed with a real build.
# ---------------------------------------------------------------------------
_ADMISS_A_HAVE = """  have _ground : problem_spec_getDoc true (some ["docstring"]) (some [["ordinary"]])
      (implementation_getDoc true (some ["docstring"]) (some [["ordinary"]])) ∧
      problem_spec_getDoc true none (some [["ordinary"]])
        (implementation_getDoc true none (some [["ordinary"]])) ∧
      problem_spec_getDoc true (some []) (some [["ordinary"]])
        (implementation_getDoc true (some []) (some [["ordinary"]])) ∧
      problem_spec_getDoc false (some ["docstring"]) (some [["ordinary"]])
        (implementation_getDoc false (some ["docstring"]) (some [["ordinary"]])) := by
    refine ⟨?_, ?_, ?_, ?_⟩ <;>
      (unfold problem_spec_getDoc implementation_getDoc commentPresent; decide)
"""

_ADMISS_B_HAVE = """  have _ground : problem_spec_addContent true none "Foo" (some ["body"])
      (implementation_addContent true none "Foo" (some ["body"])) ∧
      problem_spec_addContent true (some []) "Foo" (some ["body"])
        (implementation_addContent true (some []) "Foo" (some ["body"])) ∧
      problem_spec_addContent true (some ["docstring"]) "Foo" (some ["body"])
        (implementation_addContent true (some ["docstring"]) "Foo" (some ["body"])) ∧
      problem_spec_addContent false none "Foo" (some ["body"])
        (implementation_addContent false none "Foo" (some ["body"])) := by
    refine ⟨?_, ?_, ?_, ?_⟩ <;>
      (unfold problem_spec_addContent implementation_addContent commentPresent; decide)
"""


# ---------------------------------------------------------------------------
# DIVERGENCE rival. This bundle's carrier IS total (a plain Lean `def` must show
# termination), but `partial def` is a first-class Lean declaration and the impl
# region begins AT the `def` header, so a NON-TERMINATING implementation is
# expressible here and passes the scope check with no problems: no new axiom, no
# `sorry`, statements byte-identical, spec view unchanged. The frozen verifier
# then genuinely REJECTS it, so the case is shippable rather than vacuous.
#
# The refutation cannot be stated by evaluation — `spinForever 0` is exactly the
# term the kernel cannot reduce, and a `decide` witness at that point is stuck
# for EVERY claim, which is the hollow-signature failure mode. So the witness
# argues by FUNCTIONALITY instead, over two inputs that differ ONLY in the
# ordinary block: (A2) forces `result = normalDoc` at each, while the rival's
# ordinary path returns the same `normalDoc`-independent term at both, so the two
# instances of (A2) together entail `some [["a"]] = some [["b"]]`. The `rfl`
# step that identifies the two results is the discriminating one: it holds of the
# rival (whose ordinary path ignores `normalDoc`) and FAILS on the frozen
# solution (whose ordinary path forwards it).
_DIVERGE_A_HELPER = """partial def spinForever (n : Nat) : Option (List (List String)) :=
  spinForever (n + 1)

def implementation_getDoc (docAsAttr"""

_DIVERGE_A_WITNESS = """example : ¬ (problem_spec_getDoc false none (some [["a"]])
      (implementation_getDoc false none (some [["a"]])) ∧
    problem_spec_getDoc false none (some [["b"]])
      (implementation_getDoc false none (some [["b"]]))) := by
  rintro ⟨⟨-, h1⟩, ⟨-, h2⟩⟩
  have key : implementation_getDoc false none (some [["a"]])
      = implementation_getDoc false none (some [["b"]]) := rfl
  have bad : (some [["a"]] : Option (List (List String))) = some [["b"]] := by
    rw [← h1 rfl, key, h2 rfl]
  exact absurd bad (by decide)
"""


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — one per obligation.
    # =====================================================================
    {
        "id": "pos-A-regime-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _swaps(_BASE, (_IMPL_A, _POS_A), (_PROOF_A, _POS_A_PROOF)),
        "rationale": (
            "structurally-different but CORRECT first decision: the ORDINARY "
            "regime is handled FIRST by an early return (`if ! docAsAttr then "
            "return normalDoc`), then the two alias sub-cases as a flat sequence "
            "instead of a nested if/else. Pure branch logic — no loop, invariant "
            "or fold to lose. The three observable outcomes (present-empty block, "
            "no block, the ordinary block forwarded) are produced on exactly the "
            "same inputs, so both (A1) and (A2) still discharge. Re-proved inside "
            "the proof region for the new guard shape (`Bool.not_true` / "
            "`Bool.not_false` replacing the frozen branch lemmas); the "
            "`theorem correct_getDoc` STATEMENT is byte-identical, no helper "
            "lemma, no new axiom, no assumption token. If it FAILS => "
            "SPEC-TOO-STRONG on branch order. Ports nagini's pos-A-reorder."
        ),
    },
    {
        "id": "pos-B-demorgan",
        "kind": "soundness",
        "expect": "verify",
        "module": _swaps(_BASE, (_IMPL_B, _POS_B), (_PROOF_B, _POS_B_PROOF)),
        "rationale": (
            "structurally-different but CORRECT second decision: the De Morgan "
            "dual of the frozen gate — the forward-unchanged case "
            "(`(! docAsAttr) || commentPresent comment`) returns `incoming` "
            "first, leaving the substitution on exactly the remaining "
            "sub-domain, and the substituted line is still built from "
            "`aliasText` on the only branch (B1) permits. Identical semantics on "
            "every input, so both (B1) and (B2) still discharge. Re-proved for "
            "the disjunctive guard (`Bool.or_self` / `Bool.true_or` / "
            "`Bool.or_true` replacing the frozen conjunction lemmas); the "
            "`theorem correct_addContent` STATEMENT is byte-identical, no helper "
            "lemma, no new axiom, no assumption token. If it FAILS => "
            "SPEC-TOO-STRONG on gate shape. Ports nagini's pos-B-reorder."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY (re-aimed from nagini's precondition-admits probes).
    # =====================================================================
    {
        "id": "admiss-A-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _INTRO_A, _ADMISS_A_HAVE + _INTRO_A),
        "rationale": (
            "the first decision is SATISFIABLE and NON-DEGENERATE at every point "
            "that matters, discharged BY EVALUATION as an anonymous `have`: with "
            "a comment present an alias must expose the PRESENT but EMPTY block "
            "(`some []`); with the comment absent — in BOTH of its shapes, "
            "`none` and the analysed-but-empty `some []` — it must expose NO "
            "block (`none`); and outside the alias regime the ordinary block "
            "must be forwarded. The frozen obligation is then closed verbatim, "
            "so (A1)/(A2) discharge too. Re-aimed because the obligation carries "
            "NO precondition, which makes nagini's admits-a-normal-input probe "
            "vacuous here — nothing could exclude an in-domain input. If it "
            "FAILS => the obligation is unsatisfiable at exactly the points the "
            "modeled behaviour targets (the analogue of PRECOND-TOO-STRONG). "
            "Ports nagini's admiss-A."
        ),
    },
    {
        "id": "admiss-B-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _INTRO_B, _ADMISS_B_HAVE + _INTRO_B),
        "rationale": (
            "the second decision is SATISFIABLE and NON-DEGENERATE at the four "
            "interesting points, discharged BY EVALUATION as an anonymous "
            "`have`: an alias with no comment — in BOTH absent shapes — must "
            "expose the single line built from the rendered target description, "
            "an alias WITH a comment must forward the caller-supplied content "
            "unchanged, and so must a non-alias. In particular the substitution "
            "arm is reachable with a `some [...]` result distinct from "
            "`incoming`, so the post-image is not degenerate. Frozen obligation "
            "closed verbatim, so (B1)/(B2) discharge too. Re-aimed for the same "
            "reason as admiss-A-nondegenerate (no precondition to admit). Ports "
            "nagini's admiss-B."
        ),
    },

    # =====================================================================
    # UNIQUENESS rivals against the FIRST decision (getDoc). Each shares the
    # frozen spec exactly; only the impl region changes. Each carries the
    # partial-domain argument, the clause it violates, and a machine-checked
    # witness at a concrete input.
    # =====================================================================
    {
        "id": "weak-A-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image decision (= Solution_prepatch.lean): an alias NEVER
        # exposes a documentation block; the comment is not consulted at all.
        "module": _impl_a("""  if docAsAttr then
    return none
  return normalDoc"""),
        "refinement": (
            "this is the pre-image decision exactly: an alias entry exposes no "
            "documentation block whatever, so an alias that DOES carry a comment "
            "attached to its own name is documented as though it had none — the "
            "comment is dropped and the entry falls back to the default rendering "
            "of its target. That is precisely the symptom the failing test "
            "asserts is gone: it pins the alias entry's rendered body to the "
            "comment text. A faithful real patch keeping this decision therefore "
            "does NOT resolve the F2P."
        ),
        "rationale": (
            "REJECT from (A1)'s comment-present arm: for `docAsAttr = true` and "
            "`commentPresent comment = true` the spec demands `result = some []` "
            "(a present but empty block) and the rival returns `none`. "
            "PARTIAL-DOMAIN — correct on the comment-absent and non-alias "
            "sub-domains, wrong only where a comment is present. Refuted at "
            "(true, some [\"docstring\"], some [[\"ordinary\"]]). If it VERIFIES "
            "=> SPEC-TOO-WEAK (the present-vs-absent block decision is "
            "unpinned). This is the G-DIFF prepatch."
        ),
        "witness": _w_a("true", '(some ["docstring"])', '(some [["ordinary"]])'),
    },
    {
        "id": "weak-A-always-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual revert: an alias ALWAYS exposes the empty block, comment or
        # not. Correct where a comment is present, wrong where it is absent.
        "module": _impl_a("""  if docAsAttr then
    return some []
  return normalDoc"""),
        "refinement": (
            "a faithful real patch exposing an empty documentation block for "
            "EVERY alias would make a bare alias — one with no comment attached "
            "to its name — look as though it had documentation of its own, "
            "suppressing the default target rendering that the passing suite "
            "pins for exactly that case. So it regresses a P2P and does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from (A1)'s comment-absent arm: for `docAsAttr = true` and "
            "`commentPresent comment = false` the spec demands `result = none` "
            "(no block) and the rival returns `some []`. PARTIAL-DOMAIN, the "
            "exact dual of the pre-image. Refuted at "
            "(true, none, some [[\"ordinary\"]]) — the only site-A witness whose "
            "`comment` is the failed-lookup shape `none`. If it VERIFIES => "
            "SPEC-TOO-WEAK. Ports nagini's weak-A-always-present."
        ),
        "witness": _w_a("true", "none", '(some [["ordinary"]])'),
    },
    {
        "id": "weak-A-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # The comment decision INVERTED: comment present -> no block, comment
        # absent -> the empty block. Wrong on BOTH alias sub-domains.
        "module": _impl_a("""  if docAsAttr then
    if commentPresent comment then
      return none
    else
      return some []
  return normalDoc"""),
        "refinement": (
            "the comment decision inverted. Its faithful real patch is the exact "
            "opposite of the intended behaviour and is wrong on BOTH alias "
            "sub-domains at once: it drops the comment of an alias that has one "
            "(failing the F2P) AND fabricates a documentation block for a bare "
            "alias, suppressing the default target rendering the passing suite "
            "pins (failing a P2P). So it does NOT resolve."
        ),
        "rationale": (
            "REJECT from (A1)'s comment-present arm (returns `none` where "
            "`some []` is demanded) and INDEPENDENTLY from its comment-absent "
            "arm (returns `some []` where `none` is demanded) — a "
            "branch-inversion rival hitting both directions of the load-bearing "
            "decision. Refuted at (true, some [\"one\", \"two\"], none), a point "
            "no other witness uses: a MULTI-line comment with `normalDoc` itself "
            "absent, so neither the comment length nor the ordinary block could "
            "be masking the disagreement. If it VERIFIES => SPEC-TOO-WEAK. Ports "
            "nagini's weak-A-swap."
        ),
        "witness": _w_a("true", '(some ["one", "two"])', "none"),
    },
    {
        "id": "weak-A-ignore-regime",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores the regime selector entirely: the alias-specific decision is
        # applied to EVERY entry, so an ordinary entry loses its documentation.
        # The only site-A rival that can attack the frame conjunct (A2), and the
        # only site-A witness that moves `docAsAttr` off `true`.
        "module": _impl_a("""  if commentPresent comment then
    return some []
  return none"""),
        "refinement": (
            "a faithful real patch applying the alias-specific decision to EVERY "
            "documented entry would discard the ordinary documentation of every "
            "non-alias class in the suite — replacing it with an empty block or "
            "with no block at all — so essentially the whole passing suite "
            "regresses. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from (A2), the frame conjunct: at `docAsAttr = false` clause "
            "(A1) has a FALSE antecedent and says nothing, so this is the case "
            "that shows `result = normalDoc` is load-bearing on its own — the "
            "spec demands the ordinary block be forwarded UNCHANGED and the "
            "rival returns `some []` instead. Refuted at "
            "(false, some [\"docstring\"], some [[\"p\"], [\"q\"]]) — the only "
            "site-A witness that moves `docAsAttr` off `true`, with a TWO-element "
            "ordinary block so the forwarded value cannot coincide with "
            "`some []`. If it VERIFIES => SPEC-TOO-WEAK (the regime selector is "
            "unpinned and the read-only ordinary path is hollow). This is the "
            "value-level heir of nagini's read-only frame obligation on that "
            "input (see the footer)."
        ),
        "witness": _w_a("false", '(some ["docstring"])', '(some [["p"], ["q"]])'),
    },
    {
        "id": "weak-A-someness",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS: keys the decision on whether the lookup produced ANYTHING
        # (`isSome`) rather than on whether it produced a NON-EMPTY comment.
        # Agrees with the frozen decision at `none` and at every non-empty
        # comment; diverges on exactly `some []`, so it gets its own point.
        "module": _impl_a("""  if docAsAttr then
    if comment.isSome then
      return some []
    else
      return none
  return normalDoc"""),
        "refinement": (
            "a faithful real patch treating a SUCCESSFUL-but-empty lookup as "
            "though a comment were present would give every bare alias in an "
            "analysable module an empty documentation block, suppressing the "
            "default target rendering the passing suite pins for a bare alias — "
            "and that is the common case, since a bare alias in an analysable "
            "module is exactly the analysed-and-empty shape. So it regresses a "
            "P2P and does NOT resolve."
        ),
        "rationale": (
            "REJECT from (A1)'s comment-absent arm: the spec's notion of "
            "presence is NON-EMPTINESS, so an analysed-but-empty lookup "
            "(`some []`) counts as ABSENT and demands `result = none`; keying on "
            "`isSome` returns `some []`. A NEAR-MISS that agrees with gold at "
            "`none` and at every non-empty comment, so it gets its OWN "
            "discriminating point rather than sharing one: refuted at "
            "(true, some [], some [[\"ordinary\"]]) — the only site-A witness at "
            "the analysed-but-empty comment shape, precisely the sub-domain its "
            "rationale claims. If it VERIFIES => SPEC-TOO-WEAK (the spec would "
            "not distinguish `none` from `some []` in the way it states)."
        ),
        "witness": _w_a("true", "(some [])", '(some [["ordinary"]])'),
    },
    {
        "id": "weak-A-forward-normal",
        "kind": "uniqueness",
        "expect": "reject",
        # Right DECISION, wrong CONTENT: on the comment-present arm it forwards
        # the ordinary block instead of the empty one. The value-level heir of
        # nagini's object-identity rivals — this carrier has no `is`, but the
        # CONTENT of the block is still fully observable.
        "module": _impl_a("""  if docAsAttr then
    if commentPresent comment then
      return normalDoc
    else
      return none
  return normalDoc"""),
        "refinement": (
            "a faithful real patch that, for an alias carrying a comment, "
            "exposed the ordinary documentation it would have produced for a "
            "non-alias instead of the empty block would render the aliased "
            "target's own docstring under the alias entry rather than the "
            "comment attached to the alias name. The failing test pins the alias "
            "entry's rendered body to the comment text exactly, so the wrong "
            "body fails it. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from (A1)'s comment-present arm on the CONTENT of the block, "
            "not on the branch decision: the spec pins `result = some []`, an "
            "EMPTY block, while the rival forwards `normalDoc`. They agree only "
            "when `normalDoc` happens to be `some []`. Refuted at "
            "(true, some [\"note\"], some [[\"v\"], [\"w\"]]) — a TWO-element "
            "ordinary block on the alias regime, which is what makes the "
            "substituted content observable rather than accidentally equal. This "
            "is the value-level heir of nagini's weak-A-copy (see the footer). "
            "If it VERIFIES => SPEC-TOO-WEAK (the block's content is unpinned)."
        ),
        "witness": _w_a("true", '(some ["note"])', '(some [["v"], ["w"]])'),
    },

    # =====================================================================
    # UNIQUENESS rivals against the SECOND decision (addContent). Same witness
    # mechanics; each attacks a specific clause and moves a distinct binder.
    # =====================================================================
    {
        "id": "weak-B-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image gate (= Solution_prepatch_2.lean): the target-description
        # line replaces the content for EVERY alias, regardless of the comment.
        "module": _impl_b("""  if docAsAttr then
    return some ["alias of " ++ aliasText]
  return incoming"""),
        "refinement": (
            "this is the pre-image gate exactly: an alias entry's content is "
            "always replaced by the rendered target description. So an alias "
            "that DOES carry a comment has its own documentation overwritten by "
            "the default target line — the very symptom the failing test asserts "
            "is gone (it pins the alias entry's body to the comment text, with "
            "no target line at all). A faithful real patch does NOT resolve the "
            "F2P."
        ),
        "rationale": (
            "REJECT from (B2): for `docAsAttr = true` and `commentPresent "
            "comment = true` the antecedent `docAsAttr = false ∨ commentPresent "
            "comment = true` holds, so the spec demands `result = incoming` "
            "(forward unchanged), but the rival returns the substituted line. "
            "PARTIAL-DOMAIN — correct on the comment-absent and non-alias "
            "sub-domains. Refuted at (true, some [\"docstring\"], \"Foo\", "
            "some [\"body\"]), where `incoming` is distinct from the substituted "
            "line so the replacement is observable. If it VERIFIES => "
            "SPEC-TOO-WEAK. This is the G-DIFF prepatch_2."
        ),
        "witness": _w_b("true", '(some ["docstring"])', '"Foo"', '(some ["body"])'),
    },
    {
        "id": "weak-B-never",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual revert: the line is NEVER substituted; every entry forwards
        # its incoming content.
        "module": _impl_b("  return incoming"),
        "refinement": (
            "a faithful real patch that never substituted the rendered target "
            "description would leave a bare alias — one with no comment attached "
            "to its name — with no target line at all, while the passing suite "
            "pins exactly that line for a bare alias. So it regresses a P2P and "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from (B1): for `docAsAttr = true` and `commentPresent "
            "comment = false` the spec demands `result = some [\"alias of \" ++ "
            "aliasText]` and the rival returns `incoming`. PARTIAL-DOMAIN / dual "
            "revert — correct on the whole forward-unchanged sub-domain. Refuted "
            "at (true, none, \"Bar\", some [\"body\"]) — the "
            "absent-by-failed-lookup shape, with `incoming` distinct from the "
            "substituted line. If it VERIFIES => SPEC-TOO-WEAK. Ports nagini's "
            "weak-B-never."
        ),
        "witness": _w_b("true", "none", '"Bar"', '(some ["body"])'),
    },
    {
        "id": "weak-B-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # The comment condition INVERTED: substitute exactly when a comment IS
        # present. Wrong on BOTH alias sub-domains.
        "module": _impl_b("""  if docAsAttr && commentPresent comment then
    return some ["alias of " ++ aliasText]
  return incoming"""),
        "refinement": (
            "the comment condition inverted, so the faithful real patch is wrong "
            "on both alias sub-domains at once: it overwrites the documentation "
            "of an alias that HAS a comment with the target line (failing the "
            "F2P) and it leaves a bare alias with no target line (failing a "
            "P2P). It does NOT resolve."
        ),
        "rationale": (
            "REJECT from (B2) on the comment-present sub-domain (returns the "
            "substituted line where `incoming` is demanded) and INDEPENDENTLY "
            "from (B1) on the comment-absent sub-domain (returns `incoming` "
            "where the substituted line is demanded). Refuted at "
            "(true, some [\"one\", \"two\"], \"Baz\", some [\"body\"]) — a "
            "MULTI-line comment, a point no other witness uses, so the "
            "disagreement cannot be an artifact of a single-line comment. If it "
            "VERIFIES => SPEC-TOO-WEAK. The site-B mirror of weak-A-swap."
        ),
        "witness": _w_b("true", '(some ["one", "two"])', '"Baz"',
                        '(some ["body"])'),
    },
    {
        "id": "weak-B-ignore-regime",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores the regime selector: the substitution is applied to any entry
        # lacking a comment. The only site-B witness that moves `docAsAttr` off
        # `true`, and the case that shows (B2) is load-bearing where (B1) is
        # vacuous.
        "module": _impl_b("""  if ! commentPresent comment then
    return some ["alias of " ++ aliasText]
  return incoming"""),
        "refinement": (
            "a faithful real patch dropping the regime gate would replace the "
            "content of every ordinary documented entry that has no comment "
            "attached to its name with a target-description line — mislabelling "
            "classes that are not aliases at all. The whole passing suite of "
            "ordinary class rendering regresses, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from (B2) at `docAsAttr = false`, where (B1)'s antecedent is "
            "FALSE and that clause says nothing: this is the case that shows the "
            "pass-through conjunct is load-bearing on its own — it demands "
            "`result = incoming` and the rival returns the substituted line. "
            "Refuted at (false, none, \"Qux\", some [\"body\"]) — the only "
            "site-B witness that moves `docAsAttr` off `true`. If it VERIFIES => "
            "SPEC-TOO-WEAK (the regime gate is unpinned and the read-only "
            "caller-supplied content is hollow — the value-level heir of "
            "nagini's frame obligation on that input)."
        ),
        "witness": _w_b("false", "none", '"Qux"', '(some ["body"])'),
    },
    {
        "id": "weak-B-noneness",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS mirroring weak-A-someness on site B: substitutes only when
        # the lookup produced NOTHING (`isNone`), so an analysed-but-empty lookup
        # wrongly counts as a comment being present. Agrees with gold everywhere
        # except at `some []`, so it gets its own point — and that point is also
        # the only one where `incoming` is absent.
        "module": _impl_b("""  if docAsAttr && comment.isNone then
    return some ["alias of " ++ aliasText]
  return incoming"""),
        "refinement": (
            "a faithful real patch substituting the target line only when the "
            "lookup produced nothing at all would leave a bare alias in an "
            "ANALYSABLE module — the ordinary case, whose lookup succeeds and "
            "yields an empty result — with no target line, since it would "
            "mistake the empty result for a comment being present. The passing "
            "suite pins that line, so it regresses a P2P and does NOT resolve."
        ),
        "rationale": (
            "REJECT from (B1): the spec's notion of absence is EMPTINESS-or-"
            "nothing, so an analysed-but-empty lookup (`some []`) counts as "
            "ABSENT and demands the substituted line; keying on `isNone` "
            "forwards `incoming` instead. A NEAR-MISS agreeing with gold at "
            "`none` and at every non-empty comment, so it gets its OWN "
            "discriminating point: refuted at (true, some [], \"Foo\", none) — "
            "the only site-B witness at the analysed-but-empty comment shape "
            "(the exact sub-domain its rationale claims) AND the only one where "
            "`incoming` is absent, so the forwarded value cannot coincide with "
            "any `some [...]` the spec demands. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _w_b("true", "(some [])", '"Foo"', "none"),
    },
    {
        "id": "weak-B-bare-label",
        "kind": "uniqueness",
        "expect": "reject",
        # Right DECISION, wrong CONTENT: takes the substitution branch on exactly
        # the right sub-domain but emits the bare target description without the
        # descriptive prefix the spec pins. Attacks the VALUE (B1) pins, and is
        # the only rival returning neither `incoming` nor what (B1) demands.
        "module": _impl_b("""  if docAsAttr && (! commentPresent comment) then
    return some [aliasText]
  return incoming"""),
        "refinement": (
            "a faithful real patch taking the substitution branch on exactly the "
            "right entries but emitting the bare rendered target description "
            "without the descriptive prefix would render a bare alias's body as "
            "the target name alone. The passing suite pins the full line text "
            "for that case, so the wrong body fails it and the patch does NOT "
            "resolve, even though its branch decision is right."
        ),
        "rationale": (
            "REJECT from (B1) on the VALUE, not the branch decision: the spec "
            "pins `result = some [\"alias of \" ++ aliasText]`, so the line's "
            "content is grounded in the input `aliasText` THROUGH a fixed "
            "prefix; the rival returns `some [aliasText]`, which differs at "
            "every `aliasText`. This is the site-B content attack — the routing "
            "is correct, so only the pinned value can refute it, and it is the "
            "only rival returning neither `incoming` nor the demanded line. "
            "Refuted at (true, none, \"Quux\", some [\"m\", \"n\"]) — a "
            "TWO-element `incoming` distinct from both candidates, so neither "
            "the forwarded value nor the emitted one could coincide with what "
            "the spec demands. This is the value-level heir of nagini's "
            "weak-B-copy (see the footer). If it VERIFIES => SPEC-TOO-WEAK (the "
            "substituted content is unpinned)."
        ),
        "witness": _w_b("true", "none", '"Quux"', '(some ["m", "n"])'),
    },

    # =====================================================================
    # DIVERGENCE rival against the FIRST decision. Added by audit: the class is
    # EXPRESSIBLE on this carrier, not vacuous (see the footer).
    # =====================================================================
    {
        "id": "diverge-A-nonterminating",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swaps(_BASE,
                         (_DEF_A, _DIVERGE_A_HELPER),
                         ("  return normalDoc\n-- impl-end",
                          "  return spinForever 0\n-- impl-end")),
        "refinement": (
            "a faithful real patch whose ordinary-regime path never returns "
            "would hang the documentation build on every non-alias entry in the "
            "suite rather than producing wrong output, so the entire passing "
            "suite fails to complete and the F2P never runs. It does NOT "
            "resolve. Included because a NON-TERMINATING implementation is "
            "genuinely expressible here — `partial def` is an ordinary Lean "
            "declaration and the impl region starts at the `def` header — so "
            "this class is a shippable rival, not a carrier impossibility."
        ),
        "rationale": (
            "REJECT from (A2), the frame conjunct, in the one way an evaluation "
            "witness cannot reach: the rival's ordinary path returns a term the "
            "kernel cannot reduce, so no `decide` at a literal point can refute "
            "it (that is exactly the stuck-reduction shape a witness must not "
            "rest on). The refutation is stated by FUNCTIONALITY instead, over "
            "two inputs differing ONLY in `normalDoc`: (A2) forces "
            "`result = normalDoc` at (false, none, some [[\"a\"]]) AND at "
            "(false, none, some [[\"b\"]]), while the rival's ordinary result is "
            "the same `normalDoc`-independent term at both, so the two instances "
            "together entail `some [[\"a\"]] = some [[\"b\"]]`. The step "
            "identifying the two results is the discriminating one — it holds of "
            "the rival, whose ordinary path ignores `normalDoc`, and fails on "
            "the frozen solution, which forwards it. If it VERIFIES => "
            "SPEC-TOO-WEAK (the ordinary regime could be answered by a "
            "computation that never produces a value)."
        ),
        "witness": _DIVERGE_A_WITNESS,
    },
]


# ===========================================================================
# NAGINI -> LEAN ACCOUNTING
#
# The nagini sibling ships 12 SPEC cases (2 soundness positives, 2
# admissibility, 2 frame-mutation rivals, 6 uniqueness rivals) plus 2
# AXIOM_TESTS. It contracts the same TWO changed decisions this bundle models —
# unusual for this corpus, where the Lean-family bundle normally narrows to one
# purely-functional core — so the port is close to one-for-one rather than a
# narrowing. Case count is 16 here only because the free-input structure of the
# two obligations admits binder-coverage rivals nagini's carrier could not
# express.
#
#   nagini case              -> here                             status
#   ---------------------------------------------------------------------------
#   pos-A-reorder            -> pos-A-regime-first                PORTED (reproved)
#   pos-B-reorder            -> pos-B-demorgan                    PORTED (reproved)
#   admiss-A                 -> admiss-A-nondegenerate            RE-AIMED
#   admiss-B                 -> admiss-B-nondegenerate            RE-AIMED
#   frame-mut-A              -> (none)                            VACUOUS
#   frame-mut-B              -> (none)                            VACUOUS
#   weak-A-prepatch          -> weak-A-prepatch                   PORTED
#   weak-A-always-present    -> weak-A-always-empty               PORTED
#   weak-A-swap              -> weak-A-swap                       PORTED
#   weak-A-copy              -> weak-A-forward-normal             RE-AIMED
#   weak-B-prepatch          -> weak-B-prepatch                   PORTED
#   weak-B-never             -> weak-B-never                      PORTED
#   weak-B-copy              -> weak-B-bare-label                 RE-AIMED
#   AXIOM_TESTS (x2)         -> (none)                            DROPPED
#   (no counterpart)         -> weak-A-ignore-regime              ADDED
#   (no counterpart)         -> weak-A-someness                   ADDED
#   (no counterpart)         -> weak-B-swap                       ADDED
#   (no counterpart)         -> weak-B-ignore-regime              ADDED
#   (no counterpart)         -> weak-B-noneness                   ADDED
#
# PORTED (8). The two pre-image reverts, the two dual reverts, the site-A branch
#   inversion and the two positive reshapes carry over directly: nagini's
#   `is_attr_alias` / `has_authored_comment(comment)` guards are this carrier's
#   `docAsAttr` / `commentPresent comment`, and its `Optional[List[int]]`
#   present-empty-vs-absent result is `some [] vs none`. Each keeps the nagini
#   partial-domain ARGUMENT and its F2P/P2P grounding, restated over the modeled
#   carrier. The two positives needed real proof work that nagini did not: their
#   reshapes change the guard shape, so each re-proves inside its own proof
#   region (branch-reduction lemmas swapped, statement byte-identical, no helper
#   lemma and no assumption token). Both close — confirmed with real builds — so
#   neither positive was dropped.
#
# RE-AIMED (4).
#   * admissibility (x2): nagini's two cases assert that the fractional
#     half-permission preconditions ADMIT a normal input (reading a length,
#     reading a first element). Neither obligation here carries a precondition,
#     so nothing could exclude an in-domain input and that probe is vacuous as
#     written. Each is re-aimed at the residual admissibility risk on a total
#     domain — that the post-image is unsatisfiable or degenerate at the
#     interesting points — by discharging the spec predicate BY EVALUATION at
#     all four of them, including that the two comment-absent shapes agree. One
#     case per obligation, matching nagini's one-per-site structure.
#   * weak-A-copy / weak-B-copy: nagini's VALUE-DOUBLE-MASK rivals return a
#     value-equal FRESH LIST to break `Result() is prepared` / `is more_content`.
#     This carrier has no object identity — a value equal to `incoming` IS
#     `incoming` — so the rivals as written are not rivals at all and those
#     clauses cannot be attacked that way. What survives is the ARGUMENT: a path
#     that forwards a value must forward THAT value, and a path that builds one
#     must build exactly the pinned one. Re-aimed as value-level content attacks
#     this carrier CAN refute — weak-A-forward-normal substitutes the ordinary
#     block for the empty one, weak-B-bare-label emits the bare target
#     description in place of the pinned line. Both take the RIGHT branch, so
#     only the pinned value can refute them: the same defect class one level
#     down.
#
# VACUOUS (2, frame-mutation). The nagini sibling calls this its #1 weakness
#   class and rejects an impl that WRITES a read-only `Acc(...,1/2)` input for
#   INSUFFICIENT PERMISSION. Lean is referentially transparent: every input here
#   is an immutable value, there is no `mut` binder, no aliasing and no
#   read-only cell to overwrite, so the class collapses and NO substitute probe
#   is fabricated. What the nagini cases were protecting — that the untouched
#   paths really are pinned to their inputs — is carried instead by the two
#   frame conjuncts (A2)/(B2), which weak-A-ignore-regime and
#   weak-B-ignore-regime attack directly.
#
# DIVERGENCE lane: SHIPPED as `diverge-A-nonterminating` (added by audit). The
#   nagini sibling carries no `diverge-*` / `nonterm-*` case, so nothing was
#   omitted from the port — but the ORIGINAL port note here claimed the class was
#   "genuinely vacuous" on this backend because "a diverging implementation
#   cannot be written at all", and that claim is FALSE and was corrected. A
#   frozen `def` must indeed show termination, but `partial def` is an ordinary
#   Lean declaration and the impl region begins AT the `def` header, so a
#   non-terminating rival is expressible, passes the scope check with no problems
#   (no new axiom, no `sorry`, statements byte-identical, spec view unchanged),
#   and is genuinely REJECTED by the frozen obligation. That makes it a shippable
#   reject case. What is NOT available at such a rival is an evaluation witness:
#   the diverging term is precisely what the kernel cannot reduce, so a `decide`
#   at a literal point is stuck for every claim. The witness therefore argues by
#   FUNCTIONALITY over two inputs differing only in `normalDoc` — see the case's
#   own rationale. (Contrast velvet under
#   `set_option loom.semantics.termination "partial"`, where such a rival
#   satisfies every clause VACUOUSLY and verifies — a KNOWN SPEC HOLE there, not
#   here; see the corpus-wide termination-semantics finding.)
#
# DROPPED (2, AXIOM_TESTS). The nagini sibling consumes one `@ContractOnly`
#   axiom (`placeholder_seq` / `make_placeholder`, the unchanged line formatter)
#   and probes its soundness and containment. This bundle has NO axiom: the
#   `axioms` region is empty, and the rendered target description is carried as
#   the free input `aliasText` (an R-refinement validated by G-CONF), so there
#   is no axiom face to probe. The axiom lane is G-AX's job and this gate
#   ignores AXIOM_TESTS regardless. Correspondingly, nagini's
#   UNGROUNDED-ORACLE-ECHO note carries over unchanged in conclusion: the
#   postcondition is GROUNDED (both results are pinned by equations over the
#   obligation's own arguments, and (B1)'s content is `"alias of " ++
#   aliasText`), so there is no opaque answer key an impl could echo. The honest
#   controls are the two positives.
#
# ADDED (5, binder/clause coverage). Nagini's carrier could not express these,
#   and a battery that never moves an input says nothing about the spec's
#   dependence on it:
#   * weak-A-ignore-regime / weak-B-ignore-regime — the ONLY witnesses that move
#     `docAsAttr` off `true`, and the only ones that attack the frame conjuncts
#     (A2)/(B2) where the other clause's antecedent is FALSE. Without them
#     nothing in the battery would show those conjuncts are load-bearing, and a
#     rival that mishandled the ordinary regime would verify.
#   * weak-A-someness / weak-B-noneness — NEAR-MISSES keying on
#     `isSome`/`isNone` rather than on non-emptiness. They agree with the frozen
#     decision at `none` and at every non-empty comment and diverge only at
#     `some []`, so each is refuted AT `some []` — the analysed-but-empty shape
#     no other witness probes. This is the axis this carrier introduces (nagini's
#     `has_authored_comment` predicate hid the two absent shapes behind one
#     boolean), and without these two rivals nothing would depend on the
#     distinction the modeled comment carrier exists to preserve.
#   * weak-B-swap — the site-B branch inversion, the mirror of the ported
#     weak-A-swap; nagini attacks the inversion on site A only.
#
# POINT SPREAD (pts=6 per obligation, 12 distinct points overall). No two rivals
# share a point, and each NEAR-MISS is refuted at the input that distinguishes
# it from gold rather than at one a coarser rival already covers:
#   (docAsAttr, comment, normalDoc)
#     (true,  some ["docstring"],  some [["ordinary"]])   weak-A-prepatch
#     (true,  none,                some [["ordinary"]])   weak-A-always-empty
#     (true,  some ["one","two"],  none)                  weak-A-swap
#     (false, some ["docstring"],  some [["p"],["q"]])    weak-A-ignore-regime
#     (true,  some [],             some [["ordinary"]])   weak-A-someness
#     (true,  some ["note"],       some [["v"],["w"]])    weak-A-forward-normal
#   (docAsAttr, comment, aliasText, incoming)
#     (true,  some ["docstring"], "Foo",  some ["body"])  weak-B-prepatch
#     (true,  none,               "Bar",  some ["body"])  weak-B-never
#     (true,  some ["one","two"], "Baz",  some ["body"])  weak-B-swap
#     (false, none,               "Qux",  some ["body"])  weak-B-ignore-regime
#     (true,  some [],            "Foo",  none)           weak-B-noneness
#     (true,  none,               "Quux", some ["m","n"]) weak-B-bare-label
#
# WITNESS DISCRIMINATION. All 12 reject witnesses were checked during authoring
# with two real `lake env lean` builds each: rival build exit 0, gold build
# exit 1 with `Tactic `decide` proved that the proposition ... is false` — i.e.
# gold genuinely satisfies the spec at that point, never an elaboration error,
# an unknown name or a timeout. No witness binds a variable, so none can be a
# forgery resting on contradictory hypotheses and no consistency probe applies.
# The four positive/admissibility cases were likewise confirmed to elaborate
# with every obligation closed.
AXIOM_TESTS = []
