# properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8721 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, for the soundness positive, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival and
# FAILS on the frozen solution, so the rejection is attributable to the postcondition
# and not to a frozen tactic script that merely stopped matching the reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   collectModulePages : Bool → String → Bool → List String → List String
#   A documentation post-processing step decides WHICH of two outcomes it produces
#   for the companion source-page sequence: the full given sequence, or nothing. The
#   single postcondition pins that decision to a three-way cascade over the input flags
#   and the given page list:
#     (C1) no collected source-module data              → nothing;
#     (C2) else an e-book-family format with companion
#          pages NOT wanted for that family              → nothing;
#     (C3) else                                          → the full given sequence.
#   No output component is left free: for every input the result is exactly the empty
#   list or the complete given list.
#
# MODELED BOUNDARY (mapping.md §1, refinement.md). The carrier `generatedPages` is
# bound to *what the active output format publishes for this build when the e-book
# preference does not withhold it*. Clause C3 therefore states "publish that carrier",
# which is the empty sequence at any output format that publishes nothing for reasons
# upstream of the preference. Consequence for this battery: a rival that adds an EXTRA
# suppression keyed to some particular format name is still a divergence from the
# modeled contract at C3 (the contract licenses exactly one withholding reason, the
# e-book preference), and `weak-suppress-singlefile` below pins that. The reject lane
# for the reverse direction ("drop a second, differently-keyed suppression") is not
# expressible against this contract and is NOT shipped as a reject case — it is
# admitted by construction, which is the boundary being declared here rather than a
# gap being papered over.
#
# CARRIER NOTE (why every witness carries one `startsWith` hypothesis): the e-book
# prefix test (`builderName.startsWith "epub"`) does NOT reduce in the Lean kernel —
# `decide`/`rfl`/`simp` all stall on it (it compiles under `#eval`, but the compiled
# evaluator is not the kernel and `native_decide` is banned). So a `decide`-closed
# witness at a concrete builder-name literal still gets stuck on the `startsWith` that
# the frozen spec (and, on some rivals, the impl) evaluates. Each witness therefore
# passes concrete arguments (the builder-name LITERAL is in argument position, so the
# battery visibly varies that binder) and CONDITIONS only on the stuck fact(s) about
# that literal — e.g. `("epub".startsWith "epub") = true` or
# `("html".startsWith "epub") = false`. Each such hypothesis is a TRUE, self-consistent
# statement about a fixed literal (never two assumptions about the same term, never
# contradictory), and `simp only [… , he]` rewrites the stuck call so `decide` can
# finish. The claim it makes is exactly "at this builder name the rival's answer differs
# from the spec's" — which elaborates against the rival and fails on gold.
#
# AUDIT-MEASURED LIMIT OF THAT SHAPE (why the TRUTH of each `he` is load-bearing, and
# is checked here rather than assumed). Because the prefix fact is unprovable on this
# carrier, `consistency_probe` CANNOT refute a FALSE `he`: `omega`/`simp_all`/`decide`
# all stall on the same stuck term, so the probe fails (= "hypotheses satisfiable")
# whether the stated fact is true or not. Measured with real builds: a witness carrying
# the FALSE fact `("html".startsWith "epub") = true`, aimed at a rival whose own guard
# does NOT contain the `startsWith` subterm (so `he` rewrites the SPEC only), elaborates
# against that rival (exit 0), fails on gold (exit 1), and its consistency probe fails
# (exit 1) — i.e. it would be recorded as a refutation at an input THAT DOES NOT EXIST.
# The gate cannot screen this on this carrier. What rules it out for the cases below is
# therefore not the gate but an explicit invariant, verified per case: every stated fact
# is the value the REAL string test takes at that literal ("epub"/"epub3" → prefix true;
# "html"/"singlehtml"/"epa"/"htmlepub" → prefix false; "htmlepub" → suffix true), and
# every rival whose own guard reuses the spec's `startsWith "epub"` subterm has `he`
# rewrite BOTH sides consistently, so no divergence can be manufactured by the
# hypothesis alone. THREE rivals deliberately use a DIFFERENT stuck string term than the
# spec (`weak-short-prefix`: `startsWith "ep"`; `weak-suffix-family`: `endsWith "epub"`;
# `weak-suppress-singlefile`: a decidable string EQUALITY, which needs no extra fact);
# their witnesses state one true fact per DISTINCT term, which are jointly satisfiable.
# A future edit that changes a rival's guard to another string term must re-check its
# witness by hand.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's mandatory #1 class: `name`/`modules` were Acc(...,1/2)
#     read-only, and a write-back rival had to be rejected for insufficient permission).
#     Lean is referentially transparent — no aliasing, no fractional permissions — so a
#     "write into a read-only input" rival is not expressible and the whole lane is
#     VACUOUS here. DEMONSTRATED (audit), not just argued: the closest expressible
#     analogue is an impl that rebinds the input locally (`let mut pages := generatedPages;
#     pages := pages.reverse; …`) and then returns the ORIGINAL. It was built against the
#     frozen proof body and VERIFIES (exit 0) — the mutation is unobservable to the
#     caller, so there is no permission for a spec to withhold and no rejection to
#     attribute. A rival cannot be built here that a permission system would catch.
#     RE-DERIVED INDEPENDENTLY (audit, real build): that impl is exit 0. Confirmed.
#   * DIVERGENCE / non-termination is a KNOWN HOLE, not a vacuous class. The previous
#     text here claimed a diverging impl "cannot be written at all" because the
#     implementation is a total Lean `def`. AUDIT RE-MEASURED THAT AND IT IS FALSE.
#     `while true do i := i + 1` elaborates fine inside the frozen `Id.run do` body:
#     core's `Lean.Loop.forIn` is itself a `partial def`, so the `while` macro carries
#     no termination obligation for the elaborator to discharge. Built with the FROZEN
#     proof body verbatim, such an impl VERIFIES (exit 0) — `#print` confirms the
#     `forIn Lean.Loop.mk` term survives into the definition, and `simp only [Id.run,
#     bind, pure]` still closes the goal because `Id`'s bind beta-reduces the loop's
#     unused result away. So the frozen obligation does NOT pin termination, and this
#     bundle sets no `loom.semantics.termination` (it is vanilla Mathlib lean), i.e. the
#     carrier behaves as the "partial" setting: a non-terminating impl verifies
#     vacuously and NO witness can refute it. Measured on the observable variant too —
#     a loop whose value FEEDS the result is rejected (exit 1), but its witness is
#     ALSO unbuildable (`decide` stuck: "reduction got stuck … instDecidableNot", the
#     un-normalised `forIn Lean.Loop.mk` term), so there is nothing shippable in this
#     lane either way. Recorded as a hole in what the spec pins, NOT as a complete
#     battery.
#   * AXIOM_TESTS. This bundle consumes no callee axiom (the downstream page work is
#     universally quantified as `generatedPages`); the axiom lane is G-AX's job and this
#     gate ignores it regardless.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8721"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchor: the frozen guard body, verbatim. It lies ENTIRELY inside
# impl-start/impl-end and is unique in the file. Every rival _swap()s ONLY this block,
# so the edit never touches the spec / theorem statement (same_spec holds by
# construction). ---------------------------------------------------------------------
_IMPL = (
    "  -- No collected source-module data: publish nothing.\n"
    "  if !hasModules then return []\n"
    "  -- The e-book family publishes companion pages only when they are wanted there.\n"
    '  if builderName.startsWith "epub" && !enableEpub then return []\n'
    "  -- Otherwise publish the full given page sequence.\n"
    "  return generatedPages"
)
assert _BASE.count(_IMPL) == 1, "collectModulePages impl region drifted from expected text"

# --- proof-region anchor: the frozen proof body (swapped ONLY by the soundness
# positive, whose reshaped impl needs an extra case split). Unique in the file. -------
_PROOF = (
    "  intro hasModules builderName enableEpub generatedPages\n"
    "  unfold problem_spec_collectModulePages implementation_collectModulePages\n"
    "  simp only [Id.run, bind, pure]"
)
assert _BASE.count(_PROOF) == 1, "collectModulePages proof body drifted from expected text"


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-nested-guard: structurally DIFFERENT but behaviourally identical. The frozen
# impl decides the e-book branch with a single conjunctive guard
# (`startsWith "epub" && !enableEpub`); this control splits that conjunction into two
# nested `if`s (first the format-family test, then the preference), which is the shape
# a faithful patch could equally take. The result value is identical on every input.
# The frozen `theorem correct_collectModulePages` STATEMENT is kept byte-identical;
# only the proof body is re-closed (an added case split over the two nested branches).
# If it FAILS => SPEC-TOO-STRONG (a faithful, structurally-different correct impl is
# rejected).
_POS_NESTED = (
    "  -- No collected source-module data: publish nothing.\n"
    "  if !hasModules then return []\n"
    "  -- The e-book family; publish its companion pages only when they are wanted.\n"
    '  if builderName.startsWith "epub" then\n'
    "    if !enableEpub then return []\n"
    "  -- Otherwise publish the full given page sequence.\n"
    "  return generatedPages"
)
_POS_PROOF = (
    "  intro hasModules builderName enableEpub generatedPages\n"
    "  unfold problem_spec_collectModulePages implementation_collectModulePages\n"
    "  simp only [Id.run, bind, pure]\n"
    "  cases hasModules <;> cases enableEpub <;>\n"
    '    (by_cases he : builderName.startsWith "epub") <;>\n'
    "    simp_all"
)
_POS_MODULE = _swap(_swap(_BASE, _IMPL, _POS_NESTED), _PROOF, _POS_PROOF)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (adm-ground-f2p) — must VERIFY. ADDED BY THE INDEPENDENT AUDIT.
#
# The port dropped this lane, on the stated reason that the lean obligation carries NO
# precondition hypothesis so "nothing could be PRECOND-TOO-STRONG". That reason is
# rejected: on a total carrier the analogue of PRECOND-TOO-STRONG is the obligation being
# UNSATISFIABLE at exactly an F2P-shaped input, and a positive that discharges the
# obligation at that concrete input — by evaluation, as a `have`, before closing the
# frozen obligation verbatim — tests it directly. Without this lane the battery tests
# two of the three directions this gate exists for.
#
# Three ground instances, one per outcome the modeled decision can produce, each at a
# SHAPE the shipped test set actually exercises:
#   * _ground_publish  — a plain web format with companion pages wanted: the publish
#     outcome (the PASS_TO_PASS shape). Stated under the TRUE prefix fact for that
#     literal, because the conjunctive guard's first conjunct is the stuck term.
#   * _ground_suppress — the e-book-family format with companion pages NOT wanted: the
#     suppress outcome, i.e. the FAIL_TO_PASS shape. Stated UNDER the prefix hypothesis
#     because that term does not reduce in the kernel (see the CARRIER NOTE); the
#     hypothesis is the same TRUE fact about the same literal the reject witnesses use.
#   * _ground_nodata   — no collected source-module data: the clause-C1 suppress
#     outcome, the one shape holding hasModules=false.
# Each is closed by the frozen file's OWN tactic (`unfold`; `simp only [Id.run, bind,
# pure]`, plus the prefix rewrite where the term is stuck) — so a `have` that failed
# would mean the spec is unsatisfiable at that concrete input rather than that the
# ground proof was under-powered. Nothing is assumed: no new declaration, no new axiom
# token, the frozen theorem STATEMENT is byte-identical, and the frozen tactic body
# follows the `have`s verbatim. If it FAILS => the modeled behavior is unsatisfiable at
# a normal input (the analogue of PRECOND-TOO-STRONG).
_ADM_PROOF = (
    "  have _ground_publish :\n"
    '      ("html".startsWith "epub") = false →\n'
    '      problem_spec_collectModulePages true "html" true ["p"]\n'
    '        (implementation_collectModulePages true "html" true ["p"]) := by\n'
    "    intro hpub\n"
    "    unfold problem_spec_collectModulePages implementation_collectModulePages\n"
    "    simp only [Id.run, bind, pure, hpub]\n"
    "  have _ground_suppress :\n"
    '      ("epub".startsWith "epub") = true →\n'
    '      problem_spec_collectModulePages true "epub" false ["p"]\n'
    '        (implementation_collectModulePages true "epub" false ["p"]) := by\n'
    "    intro hpre\n"
    "    unfold problem_spec_collectModulePages implementation_collectModulePages\n"
    "    simp only [Id.run, bind, pure, hpre]\n"
    "  have _ground_nodata :\n"
    '      problem_spec_collectModulePages false "html" false ["p"]\n'
    '        (implementation_collectModulePages false "html" false ["p"]) := by\n'
    "    unfold problem_spec_collectModulePages implementation_collectModulePages\n"
    "    simp only [Id.run, bind, pure]\n"
) + _PROOF
_ADM_MODULE = _swap(_BASE, _PROOF, _ADM_PROOF)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly, edits ONLY the impl region, keeps the frozen proof body (which will no
# longer close — that is the rejection), and carries a discriminating witness.
# ---------------------------------------------------------------------------

# weak-no-gate: the PRE-PATCH behaviour — no e-book guard at all. Publishes the full
# sequence for every target with collected data.
_WEAK_NO_GATE = (
    "  if !hasModules then return []\n"
    "  return generatedPages"
)

# weak-wrong-pol: inverts the preference test — suppresses when companion pages ARE
# wanted (`&& enableEpub`) instead of when they are not.
_WEAK_WRONG_POL = (
    "  if !hasModules then return []\n"
    '  if builderName.startsWith "epub" && enableEpub then return []\n'
    "  return generatedPages"
)

# weak-ignore-pref: drops the preference conjunct — suppresses ALL e-book-family
# targets regardless of whether companion pages are wanted.
_WEAK_IGNORE_PREF = (
    "  if !hasModules then return []\n"
    '  if builderName.startsWith "epub" then return []\n'
    "  return generatedPages"
)

# weak-drop-hasmodules: drops the no-collected-data guard (clause C1) — publishes the
# sequence even when no source-module data was collected.
_WEAK_DROP_HAS = (
    '  if builderName.startsWith "epub" && !enableEpub then return []\n'
    "  return generatedPages"
)

# weak-exact-family (ADDED BY AUDIT): tests the family membership by EXACT equality
# instead of by prefix. Correct on the bare family name, wrong on every VERSIONED member
# of the family (e.g. the "…3" variant), which it publishes when it must suppress. The
# shipped rivals all state their witness at the bare family literal, so prefix-vs-exact
# was the one shape of the e-book test left unpinned by the battery; the frozen spec does
# reject it (machine-checked).
_WEAK_EXACT_FAMILY = (
    "  if !hasModules then return []\n"
    '  if builderName = "epub" && !enableEpub then return []\n'
    "  return generatedPages"
)

# weak-short-prefix (ADDED BY AUDIT): tests a TRUNCATED prefix, so it suppresses names
# that merely share the family prefix's first characters without belonging to the family.
# The dual boundary error to weak-exact-family: over-suppress instead of over-publish.
# Its guard uses a DIFFERENT stuck prefix term than the spec's, so its witness must state
# a fact about BOTH terms (two distinct, jointly-satisfiable facts — not two claims about
# one term, which is the shape consistency_probe exists to catch).
_WEAK_SHORT_PREFIX = (
    "  if !hasModules then return []\n"
    '  if builderName.startsWith "ep" && !enableEpub then return []\n'
    "  return generatedPages"
)

# weak-suffix-family (ADDED BY THIS PASS): tests where in the name the family token
# occurs — SUFFIX instead of PREFIX. A name that merely ENDS with the family token does
# not belong to the family, so this rival withholds the companion pages of an unrelated
# plain build. Aimed squarely at the one clause that now carries the whole suppression
# obligation: it pins that the family test is anchored at the START of the name and not
# merely somewhere in it. Its guard uses a DIFFERENT stuck string term than the spec's,
# so its witness states one true fact per term.
_WEAK_SUFFIX_FAMILY = (
    "  if !hasModules then return []\n"
    '  if builderName.endsWith "epub" && !enableEpub then return []\n'
    "  return generatedPages"
)

# weak-suppress-singlefile (ADDED BY THIS PASS; replaces the previous rival that
# attacked this axis from the other direction): keeps the whole modeled cascade but
# withholds the sequence for one additional, differently-keyed output format name. The
# modeled contract licenses exactly ONE withholding reason — the e-book preference — so
# a second, unlicensed one diverges from clause C3.
_WEAK_SUPPRESS_SINGLEFILE = (
    "  if !hasModules then return []\n"
    '  if builderName = "singlehtml" then return []\n'
    '  if builderName.startsWith "epub" && !enableEpub then return []\n'
    "  return generatedPages"
)

# weak-drop-last: keeps every guard but, on the publish path, emits all pages EXCEPT
# the last (`.dropLast`). Correct on the empty page list, wrong on any non-empty one.
_WEAK_DROP_LAST = (
    "  if !hasModules then return []\n"
    '  if builderName.startsWith "epub" && !enableEpub then return []\n'
    "  return generatedPages.dropLast"
)

# weak-head-only (ADDED BY THIS PASS): publishes only the FIRST page of the sequence.
# Agrees with the frozen result wherever a clause pins `[]` AND on any one-element
# sequence, so it is correct exactly where the surviving suppression clause decides —
# which makes it the natural probe of whether clause C3 still pins the whole sequence
# rather than merely "something non-empty". Distinguished from weak-drop-last by a
# three-element witness, where the two rivals disagree with each other as well as with
# the spec (`take 1 => ["a"]`, `dropLast => ["a","b"]`).
_WEAK_HEAD_ONLY = (
    "  if !hasModules then return []\n"
    '  if builderName.startsWith "epub" && !enableEpub then return []\n'
    "  return generatedPages.take 1"
)

# weak-suppress-all: removes the publish path entirely — always produces nothing.
_WEAK_SUPPRESS_ALL = "  return []"


def _wit(bname, hasm, enable, pages, prefix):
    """A refutation witness: `¬ problem_spec … (implementation …)` at concrete
    arguments, closed by `decide` after the ONE stuck `startsWith` fact about the
    builder-name literal is rewritten. Elaborates against a rival that diverges from
    the frozen result there; FAILS on gold (which satisfies the spec at that input).

    `bname` is the builder-name String literal (in argument position, so the coverage
    parser sees it vary); `prefix` is its true `startsWith "epub"` value ("true" or
    "false"). The single hypothesis `he` is a self-consistent fact about that literal."""
    hyp = f'(he : ({bname}.startsWith "epub") = {prefix})'
    args = f'{hasm} {bname} {enable} {pages}'
    return (
        f"example {hyp} :\n"
        f"    ¬ problem_spec_collectModulePages {args}\n"
        f"      (implementation_collectModulePages {args}) := by\n"
        f"  unfold problem_spec_collectModulePages implementation_collectModulePages\n"
        f"  simp only [Id.run, bind, pure, he]\n"
        f"  decide"
    )


def _wit2(bname, hasm, enable, pages, prefix, alt_op, alt_arg, alt_value):
    """As `_wit`, but for a rival whose own guard tests a DIFFERENT stuck string term.

    `he` rewrites the SPEC's `startsWith "epub"`; `hs` rewrites the RIVAL's
    `<alt_op> <alt_arg>` (e.g. `startsWith "ep"`, `endsWith "epub"`). Both are TRUE
    facts about the same fixed builder-name literal and about DISTINCT terms, so they
    are jointly satisfiable — this is not the "two assumptions about one term" shape
    that would let a contradiction close the goal. Without `hs` the rival's own guard
    stays stuck and `decide` cannot finish (measured: the witness then fails against
    its own rival, exit 1)."""
    args = f'{hasm} {bname} {enable} {pages}'
    return (
        f'example (he : ({bname}.startsWith "epub") = {prefix})\n'
        f'    (hs : ({bname}.{alt_op} "{alt_arg}") = {alt_value}) :\n'
        f"    ¬ problem_spec_collectModulePages {args}\n"
        f"      (implementation_collectModulePages {args}) := by\n"
        f"  unfold problem_spec_collectModulePages implementation_collectModulePages\n"
        f"  simp only [Id.run, bind, pure, he, hs]\n"
        f"  decide"
    )


SPEC_TESTS = [
    {
        "id": "pos-nested-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MODULE,
        "rationale": (
            "structurally-different but CORRECT impl: the e-book branch's conjunctive "
            "guard is re-expressed as two nested `if`s (the format-family test, then "
            "the preference), producing the identical result on every input. The frozen "
            "`theorem correct_collectModulePages` STATEMENT is kept byte-identical; only "
            "the proof body is re-closed with an added case split over the nested "
            "branches (cases on the two flags × by_cases on the e-book prefix test, then "
            "simp_all). If it FAILS => SPEC-TOO-STRONG (a faithful correct impl "
            "rejected). Verified: real build, exit 0."
        ),
    },
    {
        "id": "adm-ground-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM_MODULE,
        "rationale": (
            "ADDED BY AUDIT (the port dropped this lane; its stated reason — 'the lean "
            "obligation carries no precondition hypothesis, so nothing could be "
            "PRECOND-TOO-STRONG' — is rejected, because the analogue on a total carrier "
            "is the obligation being UNSATISFIABLE at exactly an F2P-shaped input). The "
            "obligation is discharged at three concrete inputs, one per outcome the "
            "modeled decision can produce, each at a shape the shipped test set "
            "exercises: the publish outcome at a plain web format with companion pages "
            "wanted (the PASS_TO_PASS shape); the suppress outcome at the e-book-family "
            "format with companion pages NOT wanted (the FAIL_TO_PASS shape); and the "
            "clause-C1 suppress outcome with no collected source-module data (the only "
            "shape holding hasModules=false). The first two are stated under the same "
            "TRUE prefix facts the reject witnesses use, because that term does not "
            "reduce in the kernel. Each `have` is closed by the frozen file's OWN tactic, "
            "so a failure would mean the spec is unsatisfiable there rather than that the "
            "ground proof was under-powered; then the frozen obligation is closed "
            "verbatim. Nothing is assumed: no new declaration, no new axiom token, "
            "statement byte-identical. If it FAILS => the modeled behavior is "
            "unsatisfiable at a normal input (the analogue of PRECOND-TOO-STRONG)."
        ),
    },
    {
        "id": "weak-no-gate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_NO_GATE),
        "refinement": (
            "drops the e-book gate entirely — the recorded PRE-CHANGE behaviour of the "
            "modeled decision. It still publishes the e-book companion pages when they "
            "are not wanted for that family — exactly the FAIL_TO_PASS "
            "test_viewcode_epub_default, which asserts that page does NOT exist. It does "
            "NOT resolve, so a verifying rival here would be a true "
            "verify-does-not-imply-resolve break. This is the rival the prepatch twin "
            "encodes, so its rejection is the same fact G-DIFF measures on "
            "Solution_prepatch.lean."
        ),
        "rationale": (
            "REJECTED by clause C2: on the sub-domain of an e-book-family name with the "
            "preference OFF the spec pins the result to the empty list, but the rival "
            "publishes the full sequence. Attacks the e-book guard (the load-bearing "
            "modeled change) from the over-publish side. If it VERIFIES => SPEC-TOO-WEAK "
            "(the e-book suppression is unpinned)."
        ),
        # e-book name, preference off: gold => [], rival => ["p"].
        "witness": _wit('"epub"', "true", "false", '["p"]', "true"),
    },
    {
        "id": "weak-wrong-pol",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_WRONG_POL),
        "refinement": (
            "inverting the preference test (suppress when companion pages ARE wanted "
            "instead of when they are NOT) is what a patch that flipped the config "
            "polarity would do. For the FAIL_TO_PASS e-book build with the preference "
            "OFF the guard does not fire, so the module page IS published — it fails "
            "test_viewcode_epub_default. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 / C3: on an e-book-family name with the preference "
            "ON the spec (C3) demands the full sequence, but the rival suppresses; and "
            "with the preference OFF (C2) the spec demands nothing but the rival "
            "publishes. The witness pins the ON sub-domain: gold => full, rival => []. "
            "Attacks the enableEpub polarity. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # e-book name, preference on: gold => ["p"], rival => [].
        "witness": _wit('"epub"', "true", "true", '["p"]', "true"),
    },
    {
        "id": "weak-exact-family",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_EXACT_FAMILY),
        "refinement": (
            "testing family membership by EXACT equality instead of by prefix is what a "
            "patch that compared the format name against the bare family name would do. "
            "The e-book family has VERSIONED members whose names extend the family "
            "prefix; for such a target with companion pages not wanted, this rival "
            "publishes the sequence the desired behavior suppresses. TRANSPARENCY: the "
            "shipped F2P/P2P set exercises the bare family name, so this specific "
            "divergence is not covered by those tests — but the frozen spec pins clause "
            "C2 by PREFIX, and a rival narrowing it to equality that still verified would "
            "be SPEC-TOO-WEAK."
        ),
        "rationale": (
            "REJECTED by clause C2: on a versioned e-book-family name with the preference "
            "OFF the spec (whose test is a PREFIX test) pins the result to the empty "
            "list, but the rival's equality test does not fire and it publishes the full "
            "sequence. ADDED BY AUDIT: every other e-book witness is stated at the BARE "
            "family literal, so prefix-vs-exact-match was the one shape of the family "
            "test the battery left unpinned. If it VERIFIES => SPEC-TOO-WEAK (the e-book "
            "test would be pinned only at the bare name)."
        ),
        # versioned e-book name, preference off: gold => [], rival => ["p"].
        "witness": _wit('"epub3"', "true", "false", '["p"]', "true"),
    },
    {
        "id": "weak-short-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_SHORT_PREFIX),
        "refinement": (
            "testing a TRUNCATED family prefix is the dual boundary error: a patch that "
            "mistyped the prefix suppresses formats that merely begin with those "
            "characters without belonging to the e-book family, so a plain build whose "
            "name shares that lead-in loses its companion pages. Over-suppress rather "
            "than over-publish. TRANSPARENCY: no shipped F2P/P2P build has such a name, "
            "so this divergence is not covered by those tests — but the frozen spec pins "
            "the exact family prefix and a rival widening it that verified would be "
            "SPEC-TOO-WEAK."
        ),
        "rationale": (
            "REJECTED by clause C3: at a name that shares the truncated lead-in but is "
            "NOT in the e-book family, the spec's prefix test is false, so C3 demands the "
            "full sequence — but the rival's widened test fires and it suppresses. ADDED "
            "BY AUDIT (the over-suppress dual of weak-exact-family: together they pin the "
            "family test's boundary from both sides). Its guard uses a DIFFERENT stuck "
            "prefix term than the spec's, so the witness states one TRUE fact about each "
            "of the two distinct terms; with only the spec's fact, `decide` stays stuck on "
            "the rival's own guard and the witness fails against its own rival. If it "
            "VERIFIES => SPEC-TOO-WEAK (the family prefix's width is unpinned)."
        ),
        # shares "ep" but NOT the family prefix, preference off: gold => ["p"], rival => [].
        "witness": _wit2('"epa"', "true", "false", '["p"]', "false",
                         "startsWith", "ep", "true"),
    },
    {
        "id": "weak-suffix-family",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_SUFFIX_FAMILY),
        "refinement": (
            "matching the family token at the END of the format name instead of at the "
            "START is what a patch that reached for the wrong string test would do. A "
            "name that merely ends with that token is not a member of the family, so the "
            "rival withholds the companion pages of an unrelated plain build; combined "
            "output builds whose names concatenate format tokens are exactly the shape "
            "this hits. TRANSPARENCY: no shipped F2P/P2P build has such a name, so this "
            "divergence is not covered by those tests — but the frozen spec anchors the "
            "family test at the start of the name, and a rival re-anchoring it that "
            "verified would be SPEC-TOO-WEAK."
        ),
        "rationale": (
            "REJECTED by clause C3: at a name that ends with the family token but does "
            "not begin with it, the spec's prefix test is false, so C3 demands the full "
            "sequence — but the rival's suffix test fires and it suppresses. ADDED BY "
            "THIS PASS, aimed at the clause that carries the whole suppression "
            "obligation: it pins WHERE in the name the family token must occur, which "
            "neither the exact-match nor the truncated-prefix rival tests. Its guard uses "
            "a DIFFERENT stuck string term than the spec's, so the witness states one "
            "TRUE fact per distinct term. If it VERIFIES => SPEC-TOO-WEAK (the anchoring "
            "of the family test is unpinned)."
        ),
        # ends with the family token but does not begin with it, preference off:
        # gold => ["p"], rival => [].
        "witness": _wit2('"htmlepub"', "true", "false", '["p"]', "false",
                         "endsWith", "epub", "true"),
    },
    {
        "id": "weak-ignore-pref",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_IGNORE_PREF),
        "refinement": (
            "suppressing ALL e-book-family targets regardless of the preference (drop "
            "the `&& not …` conjunct) is what a patch that omitted the preference check "
            "would do. For the PASS_TO_PASS e-book build with the preference ENABLED it "
            "suppresses a page the test requires to exist — it fails "
            "test_viewcode_epub_enabled. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C3: on an e-book-family name with the preference ON the "
            "target is NOT suppressed, so the spec demands the full sequence, but the "
            "rival returns the empty list. Attacks the enableEpub conjunct from the "
            "over-suppress side (the dual of weak-wrong-pol). If it VERIFIES => "
            "SPEC-TOO-WEAK (the preference is unpinned in the other direction)."
        ),
        # e-book name, preference on: gold => ["p"], rival => [].
        "witness": _wit('"epub"', "true", "true", '["p"]', "true"),
    },
    {
        "id": "weak-suppress-singlefile",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_SUPPRESS_SINGLEFILE),
        "refinement": (
            "keeping the whole modeled cascade but ADDING a second withholding rule keyed "
            "to one particular output-format name is what a patch that generalised the "
            "fix beyond its brief would do. The modeled contract names exactly one reason "
            "to withhold the sequence — the e-book preference — so an extra, unlicensed "
            "one changes the decision the consumer was promised. REPLACES the previous "
            "rival on this axis, which attacked it from the other direction; that "
            "direction is admitted by the modeled contract (see MODELED BOUNDARY at the "
            "top of this file) and shipping it as a reject case would have been a false "
            "obligation. TRANSPARENCY: the shipped F2P/P2P set contains no build with "
            "this name, so the divergence is not covered by those tests."
        ),
        "rationale": (
            "REJECTED by clause C3: at a name outside the e-book family with collected "
            "data the spec pins the result to the full given sequence, but the rival "
            "returns the empty list. Attacks clause C3 from the over-suppress side at a "
            "single named point — the narrowest possible over-suppression, and therefore "
            "the hardest for a total-equality postcondition to catch. Its extra guard is "
            "a decidable string EQUALITY, so the witness needs only the spec's own stuck "
            "prefix fact. If it VERIFIES => SPEC-TOO-WEAK (clause C3 would permit "
            "arbitrary extra name-keyed suppression)."
        ),
        # a non-e-book name, preference off, non-empty sequence: gold => ["p"], rival => [].
        "witness": _wit('"singlehtml"', "true", "false", '["p"]', "false"),
    },
    {
        "id": "weak-drop-hasmodules",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_DROP_HAS),
        "refinement": (
            "dropping the no-collected-data guard (clause C1) is what removing the "
            "pre-existing early return would do; the step would then publish the "
            "companion sequence for a build that collected no source-module data, where "
            "the real downstream work has nothing to enumerate. TRANSPARENCY: the "
            "ext-viewcode fixtures always collect module data, so this divergence is not "
            "exercised by the shipped F2P/P2P set — but the frozen spec models clause C1 "
            "and a rival dropping it that verified would be SPEC-TOO-WEAK. Included so "
            "the hasModules binder is varied (false) rather than held constant at true "
            "across every witness (see 'assessment')."
        ),
        "rationale": (
            "REJECTED by clause C1: when no source-module data was collected the spec "
            "pins the result to the empty list, but the rival publishes the full "
            "sequence. Attacks the hasModules clause — the only clause exercising "
            "hasModules=false. If it VERIFIES => SPEC-TOO-WEAK (the no-data suppression "
            "is unpinned)."
        ),
        # no collected data, plain non-e-book name: gold => [], rival => ["p"].
        "witness": _wit('"html"', "false", "false", '["p"]', "false"),
    },
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_DROP_LAST),
        "refinement": (
            "emitting every companion page except the LAST (an off-by-one over the "
            "published sequence) is what a patch with a truncated page loop would do. "
            "On a publish-path build the last page — e.g. the recorded module page the "
            "PASS_TO_PASS test_viewcode_epub_enabled / test_linkcode / "
            "test_local_source_files assert EXISTS — would be missing. Does NOT resolve. "
            "A genuine partial-domain break: correct on the empty page list, wrong on "
            "any non-empty one."
        ),
        "rationale": (
            "REJECTED by clause C3: on a non-suppressed target the spec demands EXACTLY "
            "the full given sequence, but the rival returns it with the last element "
            "dropped, which differs whenever the sequence is non-empty. Attacks the "
            "publish-path result value / the generatedPages binder. If it VERIFIES => "
            "SPEC-TOO-WEAK (the published page count is unpinned)."
        ),
        # non-suppressed target, two-element page list: gold => ["a","b"], rival => ["a"].
        "witness": _wit('"html"', "true", "false", '["a", "b"]', "false"),
    },
    {
        "id": "weak-head-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_HEAD_ONLY),
        "refinement": (
            "publishing only the FIRST companion page is what a patch that replaced the "
            "page loop with a single emission would do; the remaining module pages the "
            "PASS_TO_PASS builds assert EXIST would be missing. Does NOT resolve. ADDED "
            "BY THIS PASS: it agrees with the frozen result on every input where a "
            "suppression clause fires AND on every one-element sequence, so it is right "
            "exactly where the suppression clauses decide and wrong only in the sequence "
            "value — which makes it the direct probe of whether clause C3 still pins the "
            "WHOLE sequence rather than merely 'something non-empty'."
        ),
        "rationale": (
            "REJECTED by clause C3: on a non-suppressed target the spec demands EXACTLY "
            "the full given sequence, but the rival returns only its first element, which "
            "differs whenever the sequence has more than one. Distinguished from "
            "weak-drop-last by a THREE-element witness, where the two rivals disagree "
            "with each other as well as with the spec. If it VERIFIES => SPEC-TOO-WEAK "
            "(the sequence value on the publish path is only partly pinned)."
        ),
        # non-suppressed target, three-element page list: gold => ["a","b","c"],
        # rival => ["a"] (weak-drop-last would give ["a","b"]).
        "witness": _wit('"html"', "true", "false", '["a", "b", "c"]', "false"),
    },
    {
        "id": "weak-suppress-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_SUPPRESS_ALL),
        "refinement": (
            "producing nothing for EVERY target is what a patch that placed the early "
            "return unconditionally (before any guard) would do. It suppresses the "
            "companion pages for plain web builds (PASS_TO_PASS test_linkcode / "
            "test_local_source_files) and for the preference-enabled e-book build "
            "(test_viewcode_epub_enabled), all of which assert the module page EXISTS. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C3: on any non-suppressed target the spec demands the "
            "full given sequence, but the rival always returns the empty list, which "
            "differs whenever the sequence is non-empty. CONTROL-FLOW: the publish path "
            "is removed entirely. If it VERIFIES => SPEC-TOO-WEAK (the spec would admit "
            "suppress-everything, which clause C3 exists precisely to block)."
        ),
        # non-suppressed target, non-empty page list: gold => ["p"], rival => [].
        "witness": _wit('"html"', "true", "false", '["p"]', "false"),
    },
]


# No @ContractOnly axioms and no opaque callees: the whole decision is modeled
# transparently over the input flags and the universally-quantified page list, so the
# axiom lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
