"""properties.py — PBT falsification manifest for django__django-14311 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Each case edits ONLY the implementation region (and,
for the soundness positives, the proof body); the spec view is untouched, so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition, never to a tampered spec.

DEFENDED SURFACE
----------------
The modeled function selects which of two candidate names to hand back:

    implementation_relaunchModule (moduleName parentPackage : List Char) : List Char

pinned by the single load-bearing clause

    result = (if isMainEntry moduleName && !parentPackage.isEmpty
              then parentPackage else moduleName)

`isMainEntry` is a concrete deep model (equality against the conventional
entry-point name, OR a suffix test for a dotted entry-point component), so the
whole right-hand side is FULLY TRANSPARENT: no opaque callee, hence every rival
is refutable by `decide` at a concrete input — no carrier conditioning is
needed.

The clause has two input binders, `moduleName` and `parentPackage`, and carves
THREE behavior sub-domains:

  (1) not isMainEntry moduleName                     -> result = moduleName
  (2) isMainEntry moduleName & parentPackage nonempty -> result = parentPackage
  (3) isMainEntry moduleName & parentPackage empty    -> result = moduleName

Sub-domain (1) with a non-empty parent is the F2P bug domain: the buggy
predecessor selected the parent whenever a parent existed, ignoring the
entry-point test entirely.

Because the clause is a single equality against a conditional over BOTH binders,
the frame obligation (nagini's read-only inputs held at 1/2 permission) is
discharged here STRUCTURALLY: a rival that returns the wrong candidate on any
sub-domain fails the equality. Lean is referentially transparent, so nagini's
permission-mutation class (its in-place write through a 1/2 reference) is VACUOUS
on this carrier — there is no aliasing to abuse. It is replaced by rivals that
attack each of the three sub-domains directly, varying both binders.

PORTING NOTES (which nagini cases port, which are omitted)
----------------------------------------------------------
  * `pos-reorder` -> `pos-branch-reorder` (structurally different but correct
    impl: the negated guard handles the `moduleName` case first; proof re-closed).
  * `pos-single-loop` -> `pos-functional-form` (a second correct impl in a
    different shape — a pure functional nested-conditional, no `Id.run do` block;
    proof re-closed). The nagini "single copy loop over a selected-source alias"
    reshaping has no list-copy analogue here (the selection returns an input
    verbatim), so the equivalent reshape is the nested-if form.
  * `partial-prepatch` -> `prepatch-ignore-entry` (the literal pre-gold bug:
    select the parent whenever it is non-empty, ignoring the entry-point test).
  * `partial-always-name` -> `always-name` (never select the parent).
  * `partial-parent-ignores-empty` -> `parent-ignores-empty` (select the parent
    on an entry-point module even when the parent is empty).
  * `empty-always` -> `empty-always` (return the empty name unconditionally;
    supporting tripwire).
  * `entry-suffix-only`, `parent-len-threshold` and `entry-suffix-undotted` have
    NO nagini counterpart:
    they were added by the audit of this port. Nagini's classifier is an OPAQUE
    `@ContractOnly` predicate, so there the entry test has no internal structure
    a rival could attack — it is one atom. Here `isMainEntry` is a deep model with
    two disjuncts and an emptiness conjunct, which is strictly MORE surface than
    the sibling had, and the four ported rivals leave part of it untested: each
    is refuted at an input where both disjuncts of the entry test agree and whose
    parent is empty or multi-character. These rivals drop the equality disjunct,
    weaken the presence test, and drop the DOT from the suffix respectively, and
    are refutable only at the new witness points (__main__, pkg), (a.__main__, a)
    and (x__main__, x).
  * nagini's `frame-mutate-name` rival is VACUOUS on this carrier (referential
    transparency, see above) — reported, not substituted.
  * `admiss-fresh-call` (nagini) tested that the read-only precondition
    `Acc(list_pred,1/2)` is establishable for an F2P-shaped self-call. It ports to
    `admiss-ground-f2p`. The lean obligation carries no precondition hypothesis,
    but "no precondition" is NOT a reason to drop the lane: the analogue on a
    total carrier is the obligation being UNSATISFIABLE at exactly an F2P-shaped
    input, which a positive that discharges the obligation at that concrete input
    — by evaluation, as a `have`, before closing the frozen obligation verbatim —
    tests directly. That is what `admiss-ground-f2p` does, at both the F2P
    directly-named-module shape and the run-as-package shape.
  * No `diverge-*` / `nonterm-*` case exists in the nagini sibling, so there is
    nothing to port and nothing to ship on this lane. (The divergence lane is
    settled corpus-wide in the corpus-wide termination-semantics finding — a `partial`-semantics
    hole on velvet; it is not re-derived or re-reported here. This bundle declares
    `implementation_relaunchModule` as a total Lean `def`.)
  * `AXIOM_TESTS` are dropped: the axiom lane is G-AX's job and this gate ignores
    them.

Every reject case carries a `witness`: a Lean snippet negating the spec predicate
at one concrete input. It is checked in a file with the frozen obligation removed
and must (1) elaborate against the rival (the rival provably contradicts the
spec) and (2) FAIL against the frozen solution (so it is a real discriminator).
All witnesses below were built both ways with scripts/lean_verify.sh.

An independent audit additionally re-derived every witness a THIRD way, to check
that gold's exit code carries information about the CLAIM rather than about a
tactic mismatch: for each reject case it built the witness with its claim FLIPPED
(the negation dropped, i.e. asserting the spec HOLDS at that input). Every
flipped claim elaborated against the frozen solution (exit 0) and failed against
its rival (exit 1), the exact mirror of the witness itself, and every gold-side
failure is a `decide` that REDUCED and refuted rather than a stuck or syntactic
one. So each rejection here is attributable to the postcondition. The audit also
confirmed each rival differs from the frozen impl OBSERVABLY (this carrier
collapses no distinction any of them relies on), and found no input at which the
frozen spec admits a wrong impl or rejects a correct one.
"""
from pathlib import Path

INSTANCE = "django__django-14311"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of a region substring; assert it actually
    matched so silent drift (Solution.lean edited) fails loudly."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — all strictly INSIDE the impl region (and, for positives,
# the proof body) of Solution.lean.
# ---------------------------------------------------------------------------

# The gold impl body, from the `Id.run do` header through the last `return`.
_GOLD_IMPL = (
    "def implementation_relaunchModule\n"
    "    (moduleName parentPackage : List Char) : List Char := Id.run do\n"
    "  if isMainEntry moduleName && !parentPackage.isEmpty then\n"
    "    return parentPackage\n"
    "  else\n"
    "    return moduleName"
)

# The gold proof body (between the theorem statement and the proof-end marker).
_GOLD_PROOF = (
    "  intro moduleName parentPackage\n"
    "  unfold problem_spec_relaunchModule implementation_relaunchModule\n"
    "  simp only [Id.run]\n"
    "  by_cases h : isMainEntry moduleName && !parentPackage.isEmpty <;>\n"
    "    simp only [h, if_true, pure]"
)

assert _GOLD_IMPL in _BASE, "drift: gold impl body does not match Solution.lean"
assert _GOLD_PROOF in _BASE, "drift: gold proof body does not match Solution.lean"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-branch-reorder) Structurally different but CORRECT: the guard is NEGATED
# and the `moduleName` (default) case is returned FIRST, the parent case in the
# else. Semantically identical, different source. If it fails to verify the spec
# is over-fit to one branch order => SPEC-TOO-STRONG. Proof re-closed.
_POS_REORDER = _swap(
    _swap(
        _BASE, _GOLD_IMPL,
        "def implementation_relaunchModule\n"
        "    (moduleName parentPackage : List Char) : List Char := Id.run do\n"
        "  if !(isMainEntry moduleName && !parentPackage.isEmpty) then\n"
        "    return moduleName\n"
        "  else\n"
        "    return parentPackage",
    ),
    _GOLD_PROOF,
    "  intro moduleName parentPackage\n"
    "  unfold problem_spec_relaunchModule implementation_relaunchModule\n"
    "  by_cases h : isMainEntry moduleName && !parentPackage.isEmpty <;>\n"
    "    simp [Id.run, h, pure]",
)

# (pos-functional-form) A second CORRECT impl in a different shape: a pure
# functional nested conditional (no `Id.run do`), splitting the compound guard
# into two nested `if`s over the two binders separately. If it fails to verify
# the spec is over-fit to one decision shape => SPEC-TOO-STRONG. Proof re-closed
# by casing both binders.
_POS_FUNCTIONAL = _swap(
    _swap(
        _BASE, _GOLD_IMPL,
        "def implementation_relaunchModule\n"
        "    (moduleName parentPackage : List Char) : List Char :=\n"
        "  if isMainEntry moduleName then\n"
        "    (if parentPackage.isEmpty then moduleName else parentPackage)\n"
        "  else moduleName",
    ),
    _GOLD_PROOF,
    "  intro moduleName parentPackage\n"
    "  unfold problem_spec_relaunchModule implementation_relaunchModule\n"
    "  by_cases h1 : isMainEntry moduleName <;>\n"
    "    by_cases h2 : parentPackage.isEmpty <;>\n"
    "    simp [h1, h2]",
)


# ===========================================================================
# ADMISSIBILITY (precond-too-strong probe) — expect "verify"
# ===========================================================================
# (admiss-ground-f2p) The frozen obligation is universally quantified with no
# precondition hypothesis, so nothing can be over-constrained by a `require`.
# The analogue of PRECOND-TOO-STRONG on a total carrier is the obligation being
# UNSATISFIABLE at a concrete, real-shaped input — a spec that no impl can meet
# there, which a universally-quantified statement hides because the whole
# obligation simply fails to close and reads as "the proof broke".
#
# So this positive GROUNDS the obligation at two concrete real-shaped inputs
# before closing the frozen obligation verbatim: it discharges
# `problem_spec ... (implementation ...)` BY EVALUATION (`decide`) as two `have`s,
# at the F2P-shaped directly-named module (a dotted module name whose final
# component is not the entry-point name, with its enclosing package non-empty)
# and at the run-as-package shape (an entry-point submodule with its package).
# The frozen proof body then follows unchanged, so the case adds obligations and
# weakens nothing. If either `have` failed to elaborate, the spec would be
# unsatisfiable at an input the real system actually reaches =>
# PRECOND-TOO-STRONG.
_ADMISS_GROUND = _swap(
    _BASE, _GOLD_PROOF,
    "  have _ground_f2p : problem_spec_relaunchModule\n"
    "      \"utils_tests.test_module.main_module\".toList\n"
    "      \"utils_tests.test_module\".toList\n"
    "      (implementation_relaunchModule\n"
    "        \"utils_tests.test_module.main_module\".toList\n"
    "        \"utils_tests.test_module\".toList) := by\n"
    "    unfold problem_spec_relaunchModule implementation_relaunchModule isMainEntry\n"
    "    simp only [Id.run]\n"
    "    decide\n"
    "  have _ground_pkg : problem_spec_relaunchModule \"django.__main__\".toList\n"
    "      \"django\".toList\n"
    "      (implementation_relaunchModule \"django.__main__\".toList\n"
    "        \"django\".toList) := by\n"
    "    unfold problem_spec_relaunchModule implementation_relaunchModule isMainEntry\n"
    "    simp only [Id.run]\n"
    "    decide\n"
    + _GOLD_PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# Each swaps ONLY the impl body; the frozen proof (tuned to the gold impl) is
# left in place, so the rival fails to verify. The `witness` is what attributes
# that failure to the spec rather than to tactic breakage.
# ===========================================================================

# (prepatch-ignore-entry) THE F2P bug: select the parent whenever it is
# non-empty, ignoring the entry-point test entirely. Correct on sub-domain (2)
# and (empty-parent collapses to moduleName), but WRONG on sub-domain (1) with a
# non-empty parent — a directly-named module returns its parent instead of its
# own name.
_RIVAL_PREPATCH = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_relaunchModule\n"
    "    (moduleName parentPackage : List Char) : List Char := Id.run do\n"
    "  if !parentPackage.isEmpty then\n"
    "    return parentPackage\n"
    "  else\n"
    "    return moduleName",
)

# (always-name) Never select the parent. Correct on sub-domains (1) and (3),
# WRONG on sub-domain (2): an entry-point module with a real parent must yield
# the parent, this yields the module's own name. The "forgot to branch on the
# entry sentinel toward the parent" bug.
_RIVAL_ALWAYS_NAME = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_relaunchModule\n"
    "    (moduleName parentPackage : List Char) : List Char := Id.run do\n"
    "  return moduleName",
)

# (parent-ignores-empty) Select the parent on any entry-point module, dropping
# the non-empty-parent guard. Correct on sub-domains (1) and (2), WRONG on
# sub-domain (3): an entry-point module with an EMPTY parent must yield the
# module's own name, this yields the empty parent.
_RIVAL_PARENT_IGNORES_EMPTY = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_relaunchModule\n"
    "    (moduleName parentPackage : List Char) : List Char := Id.run do\n"
    "  if isMainEntry moduleName then\n"
    "    return parentPackage\n"
    "  else\n"
    "    return moduleName",
)

# (entry-suffix-only) Keep only the DOTTED-SUFFIX disjunct of the entry test,
# dropping the exact-name disjunct. Correct on every input whose entry status is
# decided by the suffix (or that is not an entry module at all), WRONG on the
# bare exact-name entry module with a real parent: `isMainEntry` must hold there
# via the equality disjunct, so the spec demands `parentPackage`, but this rival
# reads the module as a non-entry and returns `moduleName`.
#
# Added by audit: the four rivals above are all rejected at witness points where
# BOTH disjuncts of `isMainEntry` agree, so each of them is refuted by inputs
# that never exercise the equality disjunct on its own. Dropping that disjunct is
# therefore a wrong impl the rest of the battery cannot see (verified: the
# suffix-only impl agrees with the frozen one at all four pre-existing witness
# points). This case makes the equality disjunct load-bearing.
_RIVAL_ENTRY_SUFFIX_ONLY = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_relaunchModule\n"
    "    (moduleName parentPackage : List Char) : List Char := Id.run do\n"
    "  if (\".__main__\".toList).isSuffixOf moduleName && !parentPackage.isEmpty then\n"
    "    return parentPackage\n"
    "  else\n"
    "    return moduleName",
)

# (parent-len-threshold) Require the parent to have MORE THAN ONE character
# instead of merely being non-empty. Correct wherever the parent is empty or long,
# WRONG on an entry-point module whose parent package is a single character: the
# spec demands that one-character parent, this rival returns the module's own
# name. A near-miss on the emptiness test itself (`length > 1` for `≠ 0`), which
# the `parent-ignores-empty` rival — attacking the other direction of the same
# conjunct — does not cover.
#
# Added by audit. NOTE (corrected by a later audit): unlike the disjunct case
# above, this rival is NOT invisible to the ported battery — it disagrees with the
# frozen impl at the `always-name` witness point (x.__main__, x), whose parent is
# a single character. So it is not the only rival refuted there. What it still
# adds is a distinct NEAR-MISS SHAPE on the presence conjunct (`length > 1` for
# `≠ 0`) refuted at a point of its own, (a.__main__, a); it is kept for that
# reason and not for an invisibility claim that does not hold.
_RIVAL_PARENT_LEN_THRESHOLD = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_relaunchModule\n"
    "    (moduleName parentPackage : List Char) : List Char := Id.run do\n"
    "  if isMainEntry moduleName && parentPackage.length > 1 then\n"
    "    return parentPackage\n"
    "  else\n"
    "    return moduleName",
)

# (entry-suffix-undotted) Keep both disjuncts of the entry test, but drop the DOT
# from the suffix one: test for a bare `__main__` ending instead of a `.__main__`
# component ending. Correct on every input whose final dotted component really is
# the entry-point name (and on every non-entry input), WRONG on a module whose
# name merely ENDS in those characters without a separating dot: the spec reads
# such a module as an ordinary one and demands its own name, while this rival
# treats it as an entry point and hands back the parent.
#
# Added by audit: no other rival makes the DOT load-bearing. `entry-suffix-only`
# attacks the presence of the suffix disjunct, but every witness in the battery
# uses a name where the dotted and undotted suffix tests agree, so the separator
# itself is untested — a near-miss that widens the entry classifier rather than
# narrowing it, and the only rival here refuted by an input the spec classifies as
# NON-entry while the rival classifies it as entry.
_RIVAL_ENTRY_SUFFIX_UNDOTTED = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_relaunchModule\n"
    "    (moduleName parentPackage : List Char) : List Char := Id.run do\n"
    "  if (moduleName == \"__main__\".toList\n"
    "        || (\"__main__\".toList).isSuffixOf moduleName)\n"
    "      && !parentPackage.isEmpty then\n"
    "    return parentPackage\n"
    "  else\n"
    "    return moduleName",
)

# (empty-always) Return the empty name unconditionally. A cheap mechanical
# near-miss: fails the equality on every input whose selected name is non-empty.
# Supporting tripwire that the reject path works; the reasoned attacks above are
# the substance.
_RIVAL_EMPTY = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_relaunchModule\n"
    "    (moduleName parentPackage : List Char) : List Char := Id.run do\n"
    "  return []",
)


# --- witnesses (checked with obligation removed) ---------------------------
# Each negates the spec predicate at one concrete input. Shared preamble unfolds
# the three defs and discharges by `decide` (the carrier is fully transparent).

def _wit(moduleName: str, parentPackage: str) -> str:
    return (
        f'example : ¬ problem_spec_relaunchModule "{moduleName}".toList'
        f' "{parentPackage}".toList\n'
        f'    (implementation_relaunchModule "{moduleName}".toList'
        f' "{parentPackage}".toList) := by\n'
        "  unfold problem_spec_relaunchModule implementation_relaunchModule isMainEntry\n"
        "  simp only [Id.run]\n"
        "  decide"
    )


# Sub-domain (1), non-empty parent — the F2P shape. A directly-named module whose
# final component is NOT the entry-point name, with a real parent package.
_WIT_PREPATCH = _wit("foo.bar.baz", "foo.bar")
# Sub-domain (2) — an entry-point module (dotted-suffix form) with a real parent.
_WIT_ALWAYS_NAME = _wit("x.__main__", "x")
# Sub-domain (3) — an entry-point module (exact form) with an EMPTY parent.
_WIT_PARENT_IGNORES_EMPTY = _wit("__main__", "")
# A non-entry module with an empty parent (sub-domain 1); the selected name is
# non-empty, so the empty-return rival is wrong here.
_WIT_EMPTY = _wit("django", "")
# Sub-domain (2) reached via the EXACT-name entry form (not the dotted suffix)
# with a real parent. This is the only point in the battery where the equality
# disjunct of `isMainEntry` is load-bearing on its own: the suffix test is false
# here, so an impl that keeps only the suffix disjunct diverges from the spec.
_WIT_ENTRY_SUFFIX_ONLY = _wit("__main__", "pkg")
# Sub-domain (2) with a SINGLE-CHARACTER parent package: non-empty, so the spec
# demands it, but a `length > 1` emptiness test rejects it.
_WIT_PARENT_LEN_THRESHOLD = _wit("a.__main__", "a")
# Sub-domain (1) at a name that ends in the entry-point characters but WITHOUT the
# dotted separator, with a real parent. The spec's suffix disjunct requires the
# dot, so this name is NOT an entry point and the spec demands the name itself;
# a rival testing an undotted suffix hands back the parent. The only witness in
# the battery where the separator is load-bearing.
_WIT_ENTRY_SUFFIX_UNDOTTED = _wit("x__main__", "x")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-branch-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but correct impl (guard negated, the "
                  "default `moduleName` case returned first and the parent case in "
                  "the else). The equality clause is order-agnostic; if this fails "
                  "to verify the spec is over-fit to one branch order => "
                  "SPEC-TOO-STRONG. Proof re-closed by casing the compound guard "
                  "with `simp [Id.run, h, pure]`."},
    {"id": "pos-functional-form", "kind": "soundness", "expect": "verify",
     "module": _POS_FUNCTIONAL,
     "rationale": "a second correct impl in a different shape: a pure functional "
                  "nested conditional (no imperative do-block) that splits the "
                  "compound guard into two nested `if`s over the two binders "
                  "separately. The carrier is transparent so there is no oracle to "
                  "echo; this stands purely as a soundness positive of a different "
                  "decision shape. If it fails to verify the spec is over-fit to "
                  "one decision shape => SPEC-TOO-STRONG. Proof re-closed by casing "
                  "both binders."},

    # ---- admissibility (must VERIFY) ----
    {"id": "admiss-ground-f2p", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS_GROUND,
     "rationale": "grounds the obligation at two CONCRETE real-shaped inputs by "
                  "evaluation, as `have`s, before closing the frozen obligation "
                  "verbatim. The frozen obligation has no precondition "
                  "hypothesis, so the analogue of PRECOND-TOO-STRONG on this "
                  "total carrier is the obligation being UNSATISFIABLE at an "
                  "input the real system reaches — which a universally "
                  "quantified statement otherwise hides, since the obligation "
                  "just fails to close and reads as a broken proof. The two "
                  "points are the F2P shape (a dotted module name whose final "
                  "component is not the entry-point name, enclosing package "
                  "non-empty: the spec must demand the module's own name there) "
                  "and the run-as-package shape (an entry-point submodule with "
                  "its package: the spec must demand the package). Both "
                  "discharge by `decide`, so the spec is satisfiable at each. "
                  "If either failed => PRECOND-TOO-STRONG. Landed by audit: the "
                  "sibling's `admiss-fresh-call` was dropped by the port on the "
                  "ground that a missing precondition makes the lane vacuous, "
                  "which is not a sufficient reason."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "prepatch-ignore-entry", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "witness": _WIT_PREPATCH,
     "refinement": "this is the literal pre-gold behaviour: select the parent "
                   "whenever a parent exists, ignoring the entry-point test. Its "
                   "faithful real patch relaunches a directly-named module through "
                   "its parent package instead of its own fully-qualified name — "
                   "the exact non-resolution the F2P "
                   "test_run_as_non_django_module_non_package asserts against. It "
                   "would NOT resolve; a verifying rival here is a true "
                   "verify-does-not-imply-resolve break.",
     "rationale": "rejected by the equality clause on sub-domain (1) with a "
                  "non-empty parent: `isMainEntry` is false there, so the spec "
                  "demands `moduleName`, but the rival returns `parentPackage`. "
                  "Witness at (foo.bar.baz, foo.bar): rival yields `foo.bar`, spec "
                  "demands `foo.bar.baz`. Seen to elaborate against the rival and "
                  "fail against gold."},
    {"id": "always-name", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ALWAYS_NAME,
     "witness": _WIT_ALWAYS_NAME,
     "refinement": "never selects the parent. Its faithful real patch relaunches "
                   "a true package entry point (an executed `__main__` submodule "
                   "with a real parent) through its own `*.__main__` name instead "
                   "of the parent package — breaking the run-as-package relaunch. "
                   "It would NOT resolve.",
     "rationale": "rejected by the equality clause on sub-domain (2): "
                  "`isMainEntry` holds and the parent is non-empty, so the spec "
                  "demands `parentPackage`, but the rival returns `moduleName`. "
                  "Witness at (x.__main__, x): the `.__main__` suffix makes "
                  "`isMainEntry` true, rival yields `x.__main__`, spec demands "
                  "`x`. Varies `moduleName` (dotted-suffix entry form) versus the "
                  "prepatch witness. Seen to elaborate against the rival and fail "
                  "against gold."},
    {"id": "parent-ignores-empty", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARENT_IGNORES_EMPTY,
     "witness": _WIT_PARENT_IGNORES_EMPTY,
     "refinement": "selects the parent on any entry-point module, dropping the "
                   "non-empty-parent guard. Its faithful real patch relaunches a "
                   "top-level entry point (an executed `__main__` with no parent "
                   "package) through the empty parent name instead of its own "
                   "name — breaking the bare-entry-point relaunch. It would NOT "
                   "resolve.",
     "rationale": "rejected by the equality clause on sub-domain (3): "
                  "`isMainEntry` holds but the parent is empty, so the spec "
                  "demands `moduleName`, but the rival returns the empty "
                  "`parentPackage`. Witness at (__main__, \"\"): `isMainEntry` "
                  "true via exact match, empty parent; rival yields `[]`, spec "
                  "demands `__main__`. This is the sub-domain the non-empty-parent "
                  "conjunct of the guard exists to protect — no other witness "
                  "probes an empty parent on an entry module. Seen to elaborate "
                  "against the rival and fail against gold."},
    {"id": "entry-suffix-only", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ENTRY_SUFFIX_ONLY,
     "witness": _WIT_ENTRY_SUFFIX_ONLY,
     "refinement": "keeps only the dotted-suffix half of the entry-point test and "
                   "drops the exact-name half. Its faithful real patch treats a "
                   "bare top-level entry-point module that DOES have a parent "
                   "package as an ordinary module, relaunching it through its own "
                   "name instead of the parent package — the run-as-package "
                   "relaunch for the exact-name entry form. It would NOT resolve.",
     "rationale": "rejected by the equality clause on sub-domain (2) reached via "
                  "the exact-name entry form: the entry test holds there through "
                  "its equality disjunct alone (the dotted-suffix test is false), "
                  "so the spec demands `parentPackage` while the rival returns "
                  "`moduleName`. Witness at (__main__, pkg): rival yields "
                  "`__main__`, spec demands `pkg`. Added by audit — the four "
                  "rivals ported from the sibling are each refuted at points "
                  "where both disjuncts of the entry test agree, so none of them "
                  "makes the equality disjunct load-bearing on its own. Built "
                  "both ways: elaborates against the rival (exit 0), and `decide` "
                  "reduces and refutes against gold (exit 1)."},
    {"id": "parent-len-threshold", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARENT_LEN_THRESHOLD,
     "witness": _WIT_PARENT_LEN_THRESHOLD,
     "refinement": "tests the parent package for length greater than one instead "
                   "of for being present at all. Its faithful real patch "
                   "relaunches an entry-point module whose parent package has a "
                   "single-character name through the module's own name instead "
                   "of that parent — breaking the run-as-package relaunch for "
                   "short package names. It would NOT resolve.",
     "rationale": "rejected by the equality clause on sub-domain (2) with a "
                  "single-character parent: the parent is non-empty, so the spec "
                  "demands it, but the rival's `length > 1` test rejects it and "
                  "returns `moduleName`. Witness at (a.__main__, a): rival yields "
                  "`a.__main__`, spec demands `a`. Attacks the presence test from "
                  "the opposite side to `parent-ignores-empty` (which drops the "
                  "conjunct entirely). A later audit corrected the original "
                  "claim here: this rival is NOT invisible to the ported battery "
                  "(it also disagrees with the frozen impl at the `always-name` "
                  "point, whose parent is one character); it is kept as a "
                  "distinct near-miss shape on the presence conjunct, refuted at "
                  "a witness point of its own. Built both ways: "
                  "elaborates against the rival (exit 0), refuted against gold by "
                  "a reduced `decide` (exit 1)."},
    {"id": "entry-suffix-undotted", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ENTRY_SUFFIX_UNDOTTED,
     "witness": _WIT_ENTRY_SUFFIX_UNDOTTED,
     "refinement": "tests whether the module name ENDS IN the entry-point "
                   "characters instead of whether its final dotted COMPONENT is "
                   "the entry-point name — i.e. it forgets the separator. Its "
                   "faithful real patch misreads an ordinary module whose name "
                   "merely ends in those characters as an entry-point module, "
                   "relaunching it through its enclosing package instead of its "
                   "own fully-qualified name; that module then does not resolve. "
                   "It would NOT resolve.",
     "rationale": "rejected by the equality clause on sub-domain (1): the spec's "
                  "suffix disjunct requires the dotted separator, so a name that "
                  "merely ends in the entry-point characters is NOT an entry "
                  "point and the spec demands the name itself, while the rival "
                  "returns the parent. Witness at (x__main__, x): rival yields "
                  "`x`, spec demands `x__main__`. Added by audit — this is the "
                  "only case that makes the SEPARATOR load-bearing (every other "
                  "witness uses a name where the dotted and undotted suffix "
                  "tests agree) and the only rival refuted at an input the spec "
                  "classifies as non-entry while the rival classifies it as "
                  "entry, i.e. a classifier WIDENING rather than a narrowing. "
                  "Built both ways: elaborates against the rival (exit 0), and "
                  "`decide` reduces and refutes against gold (exit 1); the "
                  "flipped claim elaborates on gold (exit 0) and fails on the "
                  "rival (exit 1), so gold's exit code tracks the claim."},
    {"id": "empty-always", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EMPTY,
     "witness": _WIT_EMPTY,
     "refinement": "returns the empty name unconditionally. Its faithful real "
                   "patch relaunches with an empty `-m` argument, resolving "
                   "nothing. Supporting tripwire only.",
     "rationale": "rejected by the equality clause: the selected name is "
                  "non-empty on every input with a non-empty candidate, but the "
                  "rival returns `[]`. Witness at (django, \"\"): non-entry, empty "
                  "parent, so the spec demands `django` (varying `moduleName` to a "
                  "plain module name and `parentPackage` to empty); rival yields "
                  "`[]`. Seen to elaborate against the rival and fail against "
                  "gold."},
]
