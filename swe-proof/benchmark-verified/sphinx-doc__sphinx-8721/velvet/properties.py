"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8721 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps a verdict onto. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct gatedPageEmission``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method):

  gatedPageEmission (fmt : List Char) (ebookOptIn : Bool) (hasModules : Bool)
      (generated : List Page) return (out : List Page)
    ensures out = collectedPages fmt ebookOptIn hasModules generated
    ensures shouldSuppress fmt ebookOptIn =
              (isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn))

The method models the end-of-build companion-page collection step: given the
output-format name (``fmt``), a project opt-in flag (``ebookOptIn``), whether any
source modules were collected (``hasModules``) and the pages the unchanged
emission body would yield (``generated``), it decides whether to emit
``generated`` or nothing. The load-bearing ``ensures`` pins ``out`` to the deep,
fully-unfolded ``collectedPages`` (the ``axioms`` region is empty — no opaque
answer key to echo). ``collectedPages`` composes THREE independently-attackable
gate decisions on top of the emission carrier:

  * NO-MODULES — when nothing was collected the result is ``[]`` regardless of
    format (the pre-existing guard, modeled as the ``hasModules`` binder).
  * SUPPRESS — otherwise, when ``shouldSuppress fmt ebookOptIn`` holds the result
    is ``[]``. ``shouldSuppress`` is itself two independent clauses:
      - the single combined-document format (``isCombinedFormat fmt``), always
        suppressed;
      - the portable e-book family (``isEbookFormat fmt``) UNLESS the project
        opted in (``!ebookOptIn``).
  * KEEP — for every other (format, opt-in) the result is exactly ``generated``.

FOUR INPUT BINDERS, all load-bearing: ``fmt`` (selects combined vs e-book vs
other via an equality and a prefix test), ``ebookOptIn`` (flips the e-book family
between suppress and keep), ``hasModules`` (short-circuits to ``[]``), and
``generated`` (the emitted list on the keep branch — its exact contents are
pinned, not just its emptiness). The reject witnesses drive them to NINE
distinct input points (pts = 9) so the manifest demonstrates the post-image's
dependence on each binder rather than a single pinned shape.

SPEC-TOO-STRONG SURFACE, measured beyond the two positives shipped below. Four
further correct reshapes were built against this frozen spec during the audit and
all VERIFY, so the spec is not over-fit to the frozen impl's branch ladder: a
single conjunctive keep-guard (``if hasModules && !shouldSuppress … then generated
else []``); a pure ``if``-expression ``return``; a ``match`` on the
``(hasModules, shouldSuppress …)`` pair; and the guard ladder with the clauses
REORDERED (suppression tested before the no-modules short-circuit). One reshape
that replaces the family recogniser with an equivalent ``fmt.take 4 == "epub"``
test is NOT closed by the frozen ``loom_solve`` alone, but it IS provable — adding
``all_goals simp_all [collectedPages, shouldSuppress, isEbookFormat,
List.isPrefixOf_iff_prefix, List.prefix_iff_eq_take]`` closes it — so that is a
tactic-tuning fact about the frozen script, not a spec hole.

INDEPENDENT AUDIT RE-MEASUREMENT (second auditor, own builds, exit codes read
rather than inferred). Every claim in the paragraph above was rebuilt and
reproduced: the conjunctive keep-guard, the ``if``-expression ``return``, the
``match`` on the ``(hasModules, shouldSuppress …)`` pair and the REORDERED guard
ladder all verify under the frozen ``loom_solve`` (exit 0); the ``fmt.take 4``
recogniser fails under it (exit 1, ``unsolved goals``) and verifies with the
retuned ``simp_all`` line (exit 0) — a tactic fact, not a spec hole, confirmed.
NINE further wrong impls the battery does not contain were then aimed at the
sub-domains the shipped rivals leave thinnest, and ALL NINE are rejected (exit
1), so no spec hole was found on this surface:
  * recogniser DIRECTION — ``fmt.isPrefixOf "epub"`` (the prefix test reversed);
  * recogniser TOO BROAD — ``"ep"`` as the family token, and ``"single"`` as a
    prefix-recogniser for the combined format (both over-suppress);
  * combined format by PREFIX rather than exact equality;
  * ``hasModules`` polarity inverted, and the no-modules short-circuit made
    conditional on the opt-in;
  * keep-branch VALUE breaks the shipped ``dropLast`` rival does not reach:
    ``generated.reverse`` (order), ``generated.tail`` (drops the head, dual of
    ``dropLast``), and ``generated ++ [extra]`` (emits a page too many).
The too-broad direction is worth naming because the shipped rivals only attack
the recognisers for being too NARROW (weak-exact-ebook); the spec pins both
directions.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``gatedPageEmissionTester fmt ebookOptIn hasModules
generated = false`` says the extracted program's result violates the
postcondition at that concrete input) and closes by ``decide``, checked in a file
whose ``prove_correct`` block has been stripped so no tactic script can mask the
verdict. Every argument is a concrete literal — ``List Char`` via ``"…".toList``,
``Bool`` literals, and a small ``List Page`` literal — so ``decide`` settles the
whole equality with no opaque term. The frozen impl and every rival here are
loop-free straight-line branch ladders, so the extracted tester reduces cleanly;
each witness was checked with ``scripts/lean_verify.sh`` to elaborate green
against its rival and to fail (``decide proved … is false``) against the frozen
solution — the required discriminator.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Two structurally different but
    behaviourally identical impls (return the grounded model directly; hoist the
    suppression decision into a local) must verify, else the spec is
    SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the sibling self-asserts an F2P-shaped input satisfies its
    fractional-permission precondition. This method has NO ``require`` clause and
    no permission surface, so that probe is degenerate; the residual risk is a
    DEGENERATE post-image. ``admiss-nondegenerate`` discharges an in-region
    ``assert`` pinning FOUR observable outcomes (e-book-default suppressed,
    e-book-opted-in kept, combined-document suppressed, no-modules suppressed) at
    F2P/P2P-shaped inputs; the impl is kept verbatim so the method's own
    obligation still discharges.
  * FRAME-MUTATION — real here, but enforced one level EARLIER than the spec, so
    it cannot be a G-PBT case. The sibling carries this because a read-only
    sequence input is held at a fractional heap permission an impl can illegally
    overwrite. On this carrier an impl that assigns to a read-only input does not
    ELABORATE at all (measured: ``error: `generated` cannot be mutated, only
    variables declared using `let mut` can be mutated``), so the rival build — the
    half a witness must SUCCEED on — fails for a non-spec reason and the gate would
    record ``witness-unproven``. That is a STRONGER frame guarantee than the
    sibling's permission check, not a weaker one, but it leaves no wrong-but-
    elaborating impl for the case to exhibit. NOT ported, with the reason measured
    rather than asserted; see the accounting block at the bottom.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to ``collectedPages
    fmt ebookOptIn hasModules generated``, a fully-unfolded ``def`` over the
    method's own arguments; there is no answer-key term a wrong impl could echo.
    The cheapest correct impl computes the decision honestly (a positive control).
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * PARTIAL-DOMAIN / VALUE / CONTROL-FLOW — carries the reject lane. Each rival
    gets most of the (format, opt-in, has-modules) domain right yet diverges on
    one sub-domain: the keep branch, one of the two suppress clauses, the opt-in
    polarity, the no-modules short-circuit, or the emitted per-module page count.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8721"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- facts asserted at load). Every reject rival and the direct/hoisted
# ---- soundness reshapes swap on this block.
_IMPL = """    -- impl-start
    -- Nothing was collected: emit nothing.
    if !hasModules then
      return []
    else
      -- The single combined-document format hosts no separate companion pages.
      if isCombinedFormat fmt then
        return []
      else
        -- Suppress for the e-book family unless the project opted in.
        if isEbookFormat fmt && !ebookOptIn then
          return []
        else
          return generated
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). The
# ---- reject rivals keep it verbatim: the frozen `loom_solve` no longer closes
# ---- the reshaped/wrong impl, so the verifier rejects — but the ATTRIBUTION to
# ---- the spec comes from the machine-checked witness, not from tactic breakage.
# ---- The admissibility case retunes it to clear its added assert goal.
_PROOF_GOLD = "prove_correct gatedPageEmission by\n  loom_solve\n"
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"


def _impl(new_block):
    """Full variant with only the impl block replaced (frozen proof kept)."""
    return _swap(_BASE, _IMPL, new_block)


def _block(body):
    """Wrap a straight-line impl body in the frozen impl markers."""
    return "    -- impl-start\n" + body + "\n    -- impl-end"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `gatedPageEmissionTester fmt ebookOptIn hasModules generated = false` says
# ---- the extracted program's result violates the method's postcondition at that
# ---- concrete input. Checked in a file whose `prove_correct` block has been
# ---- stripped. Every argument is a concrete literal so `decide` reduces the
# ---- extracted straight-line program without getting stuck.
def _tester(body):
    return ("\n"
            "extract_program_for gatedPageEmission\n"
            "prove_precondition_decidable_for gatedPageEmission\n"
            "prove_postcondition_decidable_for gatedPageEmission\n"
            "derive_tester_for gatedPageEmission\n\n" + body)


def _pages(*names):
    """A concrete `List Page` literal for a witness input point."""
    return "[" + ", ".join('{name := "%s".toList}' % n for n in names) + "]"


def _witness(fmt, ebook_opt_in, has_modules, generated):
    call = (f'gatedPageEmissionTester "{fmt}".toList '
            f'{ "true" if ebook_opt_in else "false" } '
            f'{ "true" if has_modules else "false" } {generated}')
    return _tester(f"example : {call} = false := by\n  decide\n")


# ---------------------------------------------------------------------------
# SOUNDNESS POSITIVES — structurally different but CORRECT impls that MUST
# verify. If a faithful correct impl cannot verify, the spec is SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------

_POS_DIRECT = _block(
    "    return collectedPages fmt ebookOptIn hasModules generated")

_POS_HOISTED = _block(
    "    -- Hoist the suppression decision into a local; same behaviour.\n"
    "    let suppress := isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn)\n"
    "    if !hasModules then\n"
    "      return []\n"
    "    else\n"
    "      if suppress then\n"
    "        return []\n"
    "      else\n"
    "        return generated")

# ---------------------------------------------------------------------------
# ADMISSIBILITY — the method has no `require`, so the sibling's precondition probe
# is degenerate; instead pin the post-image NON-DEGENERATE at the F2P/P2P-shaped
# inputs. The impl is kept verbatim (its own obligation still discharges); the
# proof gains a `decide` arm for the added assert goal.
# ---------------------------------------------------------------------------

_ADMISS_ASSERT = (
    _IMPL_START +
    "    assert (with_name_prefix `adm (\n"
    "      collectedPages \"epub\".toList false true [{name := \"m\".toList}] = [] ∧\n"
    "      collectedPages \"epub\".toList true true [{name := \"m\".toList}]\n"
    "        = [{name := \"m\".toList}] ∧\n"
    "      collectedPages \"singlehtml\".toList false true [{name := \"m\".toList}] = [] ∧\n"
    "      collectedPages \"html\".toList false false [{name := \"m\".toList}] = []))\n"
)
_ADMISS_PROOF = ("prove_correct gatedPageEmission by\n"
                 "  loom_solve\n"
                 "  all_goals decide\n")


def _admiss_module():
    return _swap(_swap(_BASE, _IMPL_START, _ADMISS_ASSERT),
                 _PROOF_GOLD, _ADMISS_PROOF)


# ---------------------------------------------------------------------------
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected, each with a machine-checked refutation witness at a DISTINCT
# concrete input and the refinement argument that its faithful real counterpart
# would NOT resolve the failing test.
# ---------------------------------------------------------------------------

# suppress-all: remove the keep path entirely; always emit nothing.
_WEAK_SUPPRESS_ALL = _block("    return []")

# drop-combined: drop the single-combined-document guard — emit pages under that
# format where the spec suppresses them.
_WEAK_DROP_COMBINED = _block(
    "    if !hasModules then\n"
    "      return []\n"
    "    else\n"
    "      if isEbookFormat fmt && !ebookOptIn then\n"
    "        return []\n"
    "      else\n"
    "        return generated")

# drop-ebook: drop the e-book opt-in guard entirely (the pre-patch bug) — emit
# pages for an e-book-default build.
_WEAK_DROP_EBOOK = _block(
    "    if !hasModules then\n"
    "      return []\n"
    "    else\n"
    "      if isCombinedFormat fmt then\n"
    "        return []\n"
    "      else\n"
    "        return generated")

# ignore-optin: suppress ALL e-book targets regardless of the opt-in.
_WEAK_IGNORE_OPTIN = _block(
    "    if !hasModules then\n"
    "      return []\n"
    "    else\n"
    "      if isCombinedFormat fmt then\n"
    "        return []\n"
    "      else\n"
    "        if isEbookFormat fmt then\n"
    "          return []\n"
    "        else\n"
    "          return generated")

# wrong-polarity: suppress the e-book family when the opt-in is ON instead of OFF.
_WEAK_WRONG_POL = _block(
    "    if !hasModules then\n"
    "      return []\n"
    "    else\n"
    "      if isCombinedFormat fmt then\n"
    "        return []\n"
    "      else\n"
    "        if isEbookFormat fmt && ebookOptIn then\n"
    "          return []\n"
    "        else\n"
    "          return generated")

# drop-last: on the keep branch, emit every collected page except the last.
_WEAK_DROP_LAST = _block(
    "    if !hasModules then\n"
    "      return []\n"
    "    else\n"
    "      if isCombinedFormat fmt then\n"
    "        return []\n"
    "      else\n"
    "        if isEbookFormat fmt && !ebookOptIn then\n"
    "          return []\n"
    "        else\n"
    "          return generated.dropLast")

# exact-ebook: recognise the e-book family by an EXACT name match instead of the
# leading-token test, so the family's versioned members are not recognised.
_WEAK_EXACT_EBOOK = _block(
    "    if !hasModules then\n"
    "      return []\n"
    "    else\n"
    "      if isCombinedFormat fmt then\n"
    "        return []\n"
    "      else\n"
    "        if fmt == \"epub\".toList && !ebookOptIn then\n"
    "          return []\n"
    "        else\n"
    "          return generated")

# optin-gates-combined: let the project opt-in govern BOTH suppression clauses,
# so the combined-document format stops suppressing once the opt-in is ON.
_WEAK_OPTIN_GATES_COMBINED = _block(
    "    if !hasModules then\n"
    "      return []\n"
    "    else\n"
    "      if (isCombinedFormat fmt || isEbookFormat fmt) && !ebookOptIn then\n"
    "        return []\n"
    "      else\n"
    "        return generated")

# ignore-hasmodules: drop the no-modules short-circuit — emit pages even when
# nothing was collected.
_WEAK_IGNORE_HASMODS = _block(
    "    if isCombinedFormat fmt then\n"
    "      return []\n"
    "    else\n"
    "      if isEbookFormat fmt && !ebookOptIn then\n"
    "        return []\n"
    "      else\n"
    "        return generated")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — must VERIFY.
    # =====================================================================
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_DIRECT),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`collectedPages fmt ebookOptIn hasModules generated` directly (no "
            "branch ladder). `out` IS that model, so the ensures holds on the whole "
            "domain and the frozen `loom_solve` still closes. If this fails to "
            "verify the spec is over-fit to the branch-ladder shape "
            "(SPEC-TOO-STRONG). Also the honest no-ungrounded-echo control: the "
            "decision function IS the real work, so a direct return is correct, not "
            "a cheat. (Sibling: pos-local-reshape — a structurally-different correct "
            "impl.)"),
    },
    {
        "id": "pos-hoisted-decision",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_HOISTED),
        "rationale": (
            "hoists the suppression decision into a local boolean `suppress` and "
            "collapses the two suppress clauses into one guard "
            "(`if suppress then [] else generated`), keeping the no-modules "
            "short-circuit. Observationally identical for every input, so "
            "`out = collectedPages …` still holds on the whole domain and the "
            "frozen proof closes. A correct reshape must verify, else the "
            "postcondition is SPEC-TOO-STRONG (rejects a faithful impl over the "
            "shape of the guard ladder). (Sibling: pos-local-reshape, hoisting the "
            "gate decision into a local.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — pin the post-image non-degenerate at F2P/P2P-shaped inputs.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss_module(),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P/P2P-shaped "
            "inputs: an e-book-default build with modules must give `[]` (F2P — no "
            "pages), an e-book build with the opt-in ON must KEEP the collected "
            "pages (P2P), the single combined-document build must give `[]`, and a "
            "no-modules build must give `[]` — four genuinely distinct outcomes over "
            "the modeled binders. The in-region assert must discharge (else the "
            "obligation is degenerate); the impl is kept verbatim so "
            "`out = collectedPages …` still verifies. (Sibling: admiss-reads, "
            "re-aimed from precondition admissibility to post-image non-degeneracy "
            "since this method has no require clause and no permission surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — must be REJECTED.
    # =====================================================================
    {
        "id": "weak-suppress-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SUPPRESS_ALL),
        "refinement": (
            "returning nothing for EVERY build is what a patch that put the early "
            "return before the gate (unconditionally) would do. It suppresses the "
            "companion pages for plain html builds (P2P test_linkcode / "
            "test_local_source_files) and for e-book-opted-in builds (P2P "
            "test_viewcode_epub_enabled), all of which require the pages to exist. "
            "Does NOT resolve."),
        "rationale": (
            "REJECT from `out = collectedPages …` via the KEEP branch: for a "
            "non-suppressing build with modules (`!shouldSuppress`, `hasModules`) "
            "the spec demands `out = generated`, but this returns `[]`. Verifying "
            "would be SPEC-TOO-WEAK (the emission path unpinned; the companion "
            "clause exists precisely to block suppress-everything). Refuted at a "
            "plain html build with a collected module. (Sibling: weak-suppress-all.)"),
        "witness": _witness("html", False, True, _pages("m")),
    },
    {
        "id": "weak-drop-combined",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_COMBINED),
        "refinement": (
            "dropping the single-combined-document guard is what a patch that "
            "omitted that inserted early return would do: the combined-document "
            "build would emit companion pages the patched collection step provably "
            "suppresses. It diverges from the gold patched behaviour at that format "
            "(mechanically refuted by G-CONF against the real patched collection "
            "step), so it is not the gold patch and would not faithfully resolve."),
        "rationale": (
            "REJECT from `out = collectedPages …` via the isCombinedFormat suppress "
            "clause: for the single combined-document format with modules "
            "`shouldSuppress` holds, so the spec demands `[]`, but with the guard "
            "removed the rival falls through and returns `generated`. Verifying "
            "would be SPEC-TOO-WEAK (the combined-document suppression unpinned). "
            "Refuted at the combined-document build — the sub-domain no other rival "
            "probes. (Velvet-specific clause the sibling did not model; ADDED.)"),
        "witness": _witness("singlehtml", False, True, _pages("m")),
    },
    {
        "id": "weak-drop-ebook",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_EBOOK),
        "refinement": (
            "this IS the pre-patch behaviour restricted to the e-book gate: the "
            "collection step with no e-book opt-in guard emits companion pages for "
            "an e-book-default build — exactly the reported bug. It FAILS the F2P "
            "test that asserts the module page does NOT exist under `make html "
            "epub` with the opt-in OFF. Does NOT resolve — the precise change the "
            "spec senses (G-DIFF)."),
        "rationale": (
            "REJECT from `out = collectedPages …` via the e-book suppress clause: "
            "for an e-book target with the opt-in OFF and modules present "
            "`shouldSuppress` holds (isEbookFormat && !ebookOptIn), so the spec "
            "demands `[]`, but the rival returns `generated`. Verifying would be "
            "SPEC-TOO-WEAK (the e-book suppression gate unpinned). Refuted at the "
            "e-book-default build. (Sibling: weak-no-gate.)"),
        "witness": _witness("epub", False, True, _pages("m")),
    },
    {
        "id": "weak-ignore-optin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_IGNORE_OPTIN),
        "refinement": (
            "suppressing ALL e-book targets regardless of the opt-in is what a "
            "patch that dropped the `and not …opt-in` conjunct would do. For the "
            "P2P e-book-opted-in build it suppresses pages the test requires to "
            "exist. It FAILS the P2P test that asserts the module page EXISTS when "
            "the opt-in is ON. Does NOT resolve."),
        "rationale": (
            "REJECT from `out = collectedPages …` via the KEEP branch on the "
            "opted-in e-book sub-domain: with the opt-in ON `shouldSuppress` is "
            "FALSE (isEbookFormat && !ebookOptIn is false), so the spec demands "
            "`out = generated`, but the rival suppresses and returns `[]`. Verifying "
            "would be SPEC-TOO-WEAK (the opt-in unpinned in the keep direction). "
            "Refuted at the e-book-opted-in build — the sub-domain the drop-ebook / "
            "wrong-polarity rivals agree with gold on, so no shared witness. "
            "(Sibling: weak-ignore-pref.)"),
        "witness": _witness("epub", True, True, _pages("m")),
    },
    {
        "id": "weak-wrong-polarity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_WRONG_POL),
        "refinement": (
            "inverting the opt-in test (suppress when the flag is ON instead of "
            "OFF) is what a patch that flipped the config polarity would do. For the "
            "F2P e-book-default build (opt-in OFF) the guard does not fire, so pages "
            "ARE emitted. It FAILS the F2P test. Does NOT resolve."),
        "rationale": (
            "REJECT from `out = collectedPages …` via the e-book suppress clause "
            "with inverted polarity: for an e-book target with the opt-in OFF "
            "`shouldSuppress` holds, but the rival's guard (isEbookFormat && "
            "ebookOptIn) is false, so it emits `generated` instead of `[]`. "
            "Verifying would be SPEC-TOO-WEAK (the opt-in polarity unpinned). "
            "Refuted at a versioned e-book-default build (`epub3`), which also "
            "exercises the prefix recogniser beyond the bare `epub` literal. "
            "(Sibling: weak-wrong-pol.)"),
        "witness": _witness("epub3", False, True, _pages("m")),
    },
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_LAST),
        "refinement": (
            "emitting every collected page except the LAST is what an off-by-one "
            "emission loop would do. The collected set includes the module page the "
            "P2P tests assert exists; dropping the last entry means that page is not "
            "written when it is last. It FAILS the P2P tests that assert the module "
            "page EXISTS. Does NOT resolve. A genuine partial-domain break: correct "
            "ONLY on the empty keep set, wrong on every non-empty one."),
        "rationale": (
            "REJECT from `out = collectedPages …` via the KEEP branch value: the "
            "spec pins `out = generated` exactly, but the rival returns "
            "`generated.dropLast`, which differs whenever `generated` has ≥ 1 "
            "element. This is the sub-domain that proves `generated` is "
            "LOAD-BEARING beyond emptiness — the witness fixes a non-suppressing "
            "build and varies only `generated` to a TWO-page list (gold keeps both, "
            "the rival drops the second). Verifying would be SPEC-TOO-WEAK (the "
            "per-module page count unpinned). Domain boundary MEASURED, not "
            "asserted: the tester refutes this rival at a ONE-page keep set too "
            "(`dropLast [a] = [] ≠ [a]`) and does NOT refute it at the EMPTY keep "
            "set (`dropLast [] = []`, which agrees with gold) — so the break is "
            "`generated ≠ []`, not `length ≥ 2`. (Sibling: weak-drop-last.)"),
        "witness": _witness("html", False, True, _pages("a", "b")),
    },
    {
        "id": "weak-exact-ebook",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_EXACT_EBOOK),
        "refinement": (
            "recognising the e-book family by an EXACT name equality instead of the "
            "leading-token test is what a patch that compared the whole format name "
            "would do. The family's versioned member is the one an ordinary project "
            "actually builds, and under it the rival emits the companion pages the "
            "patched collection step suppresses — the reported symptom, unfixed for "
            "that member. Diverges from the gold patched behaviour at that format "
            "(mechanically refuted by G-CONF against the real patched collection "
            "step), so it is not the gold patch and would not faithfully resolve."),
        "rationale": (
            "REJECT from `out = collectedPages …` via the e-book suppress clause on "
            "the RECOGNISER's shape: `isEbookFormat` is a PREFIX test, so a versioned "
            "family member with the opt-in OFF has `shouldSuppress` true and the spec "
            "demands `[]`, but the rival's exact-equality guard does not fire and it "
            "returns `generated`. This is the sub-domain that proves the recogniser is "
            "load-bearing as a PREFIX and not as an equality — the gap the other "
            "rivals leave open, since every one of them keeps `isEbookFormat` verbatim "
            "and so agrees with gold on exactly this point. Verifying would be "
            "SPEC-TOO-WEAK (the family recogniser's breadth unpinned). Refuted at a "
            "versioned e-book-default build — a DIFFERENT versioned member than "
            "weak-wrong-polarity's, so the two do not share an input point. "
            "(ADDED by audit — attack D.)"),
        "witness": _witness("epub2", False, True, _pages("m")),
    },
    {
        "id": "weak-optin-gates-combined",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_OPTIN_GATES_COMBINED),
        "refinement": (
            "letting the project opt-in govern BOTH suppression clauses is what a "
            "patch that merged the two inserted early returns into one disjunctive "
            "guard would do. It gets the whole e-book dimension right, but a project "
            "that sets the opt-in then starts emitting companion pages under the "
            "single combined-document format, where the patched collection step "
            "provably emits nothing (mechanically refuted by G-CONF against the real "
            "patched collection step). Not the gold patch; would not faithfully "
            "resolve."),
        "rationale": (
            "REJECT from `out = collectedPages …` via the combined-document suppress "
            "clause's INDEPENDENCE from the opt-in: `shouldSuppress` is "
            "`isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn)`, so the "
            "combined-document clause holds for EVERY opt-in value and the spec "
            "demands `[]`; the rival conjoins `!ebookOptIn` onto both clauses, so with "
            "the opt-in ON its guard is false and it returns `generated`. The sub-domain "
            "no other rival probes: weak-drop-combined deletes the clause outright and "
            "is refuted with the opt-in OFF, whereas this rival KEEPS the clause and "
            "agrees with gold everywhere except at (combined-document, opt-in ON) — the "
            "one point that pins the two clauses as independent rather than sharing a "
            "condition. Verifying would be SPEC-TOO-WEAK (the clause's opt-in "
            "independence unpinned). (ADDED by audit — attack D.)"),
        "witness": _witness("singlehtml", True, True, _pages("m")),
    },
    {
        "id": "weak-ignore-hasmodules",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_IGNORE_HASMODS),
        "refinement": (
            "dropping the no-modules short-circuit is what a patch that removed the "
            "pre-existing guard returning early when no source modules were "
            "recorded would do: the collection step would try to emit pages for a "
            "build where nothing was collected, diverging from the real collection "
            "step (which yields nothing in that state). Not the gold patch; would "
            "not faithfully resolve."),
        "rationale": (
            "REJECT from `out = collectedPages …` via the NO-MODULES clause: when "
            "`!hasModules` the spec demands `[]` regardless of format, but with the "
            "short-circuit removed a non-suppressing format falls through and "
            "returns `generated`. Verifying would be SPEC-TOO-WEAK (the no-modules "
            "short-circuit unpinned). Refuted at a plain html build with NO modules "
            "collected — the witness that fixes format non-suppressing and drives "
            "`hasModules` false, which no other rival does. (Modeled binder the "
            "sibling folded into its yield guard; ADDED.)"),
        "witness": _witness("html", False, False, _pages("m")),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 8 SPEC cases (1
# soundness positive `pos-local-reshape`, 1 admissibility `admiss-reads`, 5
# uniqueness value/control rivals `weak-no-gate` / `weak-wrong-pol` /
# `weak-ignore-pref` / `weak-drop-last` / `weak-suppress-all`, and 1 MANDATORY
# frame-mutation rival `frame-mut-write`) plus an AXIOM lane
# (`ax-sound-prefix_eq`, `ax-cover-prefix_eq`). This port ships 12 SPEC cases
# (2 soundness, 1 admissibility, 9 uniqueness).
#
#   sibling case            kind          -> here                       disposition
#   -----------------------------------------------------------------------------------
#   pos-local-reshape       soundness     -> pos-direct-model           RE-SHAPED
#                                            (+ pos-hoisted-decision     ADDED)
#   admiss-reads            admissibility -> admiss-nondegenerate        RE-AIMED
#   weak-no-gate            uniqueness    -> weak-drop-ebook             PORTED
#   weak-wrong-pol          uniqueness    -> weak-wrong-polarity         PORTED
#   weak-ignore-pref        uniqueness    -> weak-ignore-optin           PORTED
#   weak-drop-last          uniqueness    -> weak-drop-last              PORTED
#   weak-suppress-all       uniqueness    -> weak-suppress-all           PORTED
#   frame-mut-write         uniqueness    -> (none)                      VACUOUS
#   (none — velvet models   uniqueness    -> weak-drop-combined          ADDED
#    the singlehtml guard)
#   (none — velvet models   uniqueness    -> weak-ignore-hasmodules      ADDED
#    the hasModules binder)
#   (none — audit attack D) uniqueness    -> weak-exact-ebook            ADDED
#   (none — audit attack D) uniqueness    -> weak-optin-gates-combined   ADDED
#   ax-sound-prefix_eq      axiom         -> (none)                      DROPPED (G-AX)
#   ax-cover-prefix_eq      axiom         -> (none)                      DROPPED (G-AX)
#
# 5 uniqueness ported, 4 uniqueness added (carrier WIDENING: this bundle models
# BOTH inserted guards plus the pre-existing no-modules short-circuit, whereas the
# nagini sibling modeled only the epub gate; mapping.md §"Modeled scope"), 1
# admissibility re-aimed, 1 soundness re-shaped + 1 added; 1 uniqueness vacuous;
# axiom lane dropped (G-AX's job — this gate ignores AXIOM_TESTS).
#
# RE-SHAPED (pos-local-reshape -> pos-direct-model): the sibling's positive hoists
#   the gate decision into a local boolean, a shape it needs because its impl is a
#   permission-fenced loop. On this carrier the maximally-different correct impl is
#   a loop-free direct return of the grounded model `collectedPages …`; a second,
#   guard-ladder-preserving correct reshape (pos-hoisted-decision) is ADDED so the
#   soundness surface is defended both from a fully-collapsed shape AND from the
#   sibling's own local-hoist shape (both verified: frozen `loom_solve` closes).
# RE-AIMED (admiss-reads -> admiss-nondegenerate): the sibling asserts an
#   F2P-shaped input satisfies its half-permission Requires. This method has no
#   `require` clause and no permission surface, so that probe is degenerate; the
#   sharper residual risk is a DEGENERATE post-image, so the case is re-aimed to a
#   live in-region assert pinning FOUR observable outcomes (e-book-default
#   suppressed, e-book-opted-in kept, combined-document suppressed, no-modules
#   suppressed) at F2P/P2P-shaped inputs. Liveness of the assert re-MEASURED by
#   this audit: a deliberately FALSE assert of the same shape fails to elaborate
#   (`decide proved ... is false`), so the four pinned outcomes are discharged
#   obligations rather than decoration.
# INEXPRESSIBLE AS A G-PBT CASE (frame-mut-write): the sibling's MANDATORY
#   frame-mutation rival writes back into the read-only `modules` list (held at
#   Acc(...,1/2)) and is rejected for insufficient permission. The reason it does
#   not port is NOT "no carrier analogue" — it is that the carrier rejects the
#   write one level EARLIER than the spec, so the case cannot carry a witness and
#   therefore cannot be a well-formed reject case. MEASURED (audit attack F): a
#   rival whose impl region assigns to the read-only input
#   (`generated := []`) does not elaborate at all —
#     `error: `generated` cannot be mutated, only variables declared using
#      `let mut` can be mutated`
#   — an ELABORATION error, not a spec violation, and it also breaks the witness
#   file, whose `decide` then reports the tester's `Decidable` instance "got stuck"
#   rather than refuting anything. So the rival build (the half that must SUCCEED)
#   fails, and the gate would record `witness-unproven`: inconclusive, never a
#   pass. The frame property is real here and it is enforced STATICALLY by the
#   elaborator rather than by the postcondition, which is strictly stronger than
#   the sibling's permission check — there is no impl this spec admits that mutates
#   an input, so there is no wrong impl for the case to exhibit. The `let mut`
#   SHADOW form (`let mut g := generated; g := []`) does elaborate, but it mutates
#   a LOCAL, not the input; it is a value bug, and as a value bug it is already
#   covered by weak-suppress-all (both return `[]` on the keep branch), so adding
#   it would duplicate an existing point rather than defend the frame.
# DROPPED (AXIOM lane): the sibling's two A-reference axiom probes validate the
#   deep prefix_eq / suppressed models against the real str.startswith. This gate
#   (G-PBT) ignores AXIOM_TESTS; the axiom lane is G-AX's job. mapping.md §3 /
#   refinement.md §C record `axioms: []` and `G-AX: skip` for this bundle (the
#   gate decision is modeled deeply and validated by G-CONF, no consumed axiom),
#   so there is nothing to port even were the lane in scope.
#
# BINDER / CLAUSE COVERAGE. The load-bearing `ensures` is `out = collectedPages
#   fmt ebookOptIn hasModules generated`, with FOUR binders and THREE independent
#   top-level decisions (no-modules / suppress / keep), and `shouldSuppress` splits
#   into two independent clauses (combined-document; e-book && !opt-in). The nine
#   reject witnesses probe nine DISTINCT input points (pts = 9):
#     * weak-suppress-all       (html,       optin F, hasMods T, [m])
#     * weak-drop-combined      (singlehtml, optin F, hasMods T, [m])
#     * weak-drop-ebook         (epub,       optin F, hasMods T, [m])
#     * weak-ignore-optin       (epub,       optin T, hasMods T, [m])
#     * weak-wrong-polarity     (epub3,      optin F, hasMods T, [m])
#     * weak-drop-last          (html,       optin F, hasMods T, [a,b])
#     * weak-exact-ebook        (epub2,      optin F, hasMods T, [m])
#     * weak-optin-gates-combined (singlehtml, optin T, hasMods T, [m])
#     * weak-ignore-hasmodules  (html,       optin F, hasMods F, [m])
#   So `fmt` ranges over {html, singlehtml, epub, epub2, epub3} — exercising the
#   combined-document equality, the e-book prefix on both the bare literal and a
#   versioned variant, and a neither-format; `ebookOptIn` ranges over {F, T} (and
#   is demonstrated load-bearing: weak-drop-ebook and weak-ignore-optin sit at the
#   SAME e-book format and opposite opt-in, refuted on opposite sub-domains);
#   `hasModules` ranges over {T, F} (weak-ignore-hasmodules is the sole point that
#   drives it false, proving the short-circuit load-bearing); and `generated`
#   ranges over one- and two-element lists (weak-drop-last holds every gate
#   non-suppressing and varies ONLY `generated` to length 2, proving its exact
#   contents load-bearing beyond emptiness). All THREE outcomes are attacked:
#   NO-MODULES (weak-ignore-hasmodules), SUPPRESS — both sub-clauses
#   (weak-drop-combined for combined-document, weak-drop-ebook / weak-wrong-polarity
#   for the e-book family) — and KEEP (weak-suppress-all, weak-ignore-optin;
#   weak-drop-last on the value). No binder is pinned at a single value across the
#   reject set. Beyond the three outcomes, the two suppress clauses are pinned as
#   INDEPENDENT (weak-optin-gates-combined: only the combined-document clause's
#   freedom from the opt-in refutes it) and the e-book recogniser is pinned as a
#   PREFIX rather than an equality (weak-exact-ebook: refuted only at a versioned
#   family member).
#
#   The second `ensures` (`shouldSuppress … = isCombinedFormat … || …`) is a
#   definitional restatement of `shouldSuppress`, true for EVERY impl, so it carries
#   no independent refutable content and is not separately attacked. AUDIT-CHECKED
#   rather than asserted: across every rival build the only unsolved goal reported is
#   `case «ensures_2: out = collectedPages fmt ebookOptIn hasModules generated»`, so
#   the load-bearing clause is the one doing all the rejecting — the restatement
#   never fails and never contributes to a rejection. RE-CONFIRMED by a second
#   auditor over all nine rival builds: the string `shouldSuppress fmt ebookOptIn =`
#   appears in ZERO unsolved-goal labels. Two rivals (weak-exact-ebook,
#   weak-wrong-polarity) report that SAME ensures_2 label TWICE — one goal per
#   surviving branch of their guard ladder, not a second clause failing — which is
#   why the count of goal blocks differs between rivals while the failing clause
#   does not.
#
# AUDIT NOTE — what the reject lane's outcomes were measured to mean. All nine
#   witnesses were rebuilt independently against BOTH sides. Every one elaborates
#   against its rival (exit 0) and fails against the frozen solution (exit 1), and
#   every gold-side failure is SEMANTIC — `Tactic decide proved that the proposition
#   gatedPageEmissionTester … = false is false`, i.e. gold's extracted tester
#   SATISFIES the postcondition at exactly that input — never a missing identifier,
#   type error, unfolding failure or timeout. No witness binds anything (each states
#   its refutation at concrete literals), so no consistency probe is required.
#   In-region `assert`s were confirmed to be LIVE obligations, not decoration: a
#   deliberately FALSE assert of the same shape as admiss-nondegenerate's fails to
#   elaborate (`decide proved … is false`), so the admissibility case's four pinned
#   outcomes are genuinely discharged.
#
#   RE-RUN BY AN INDEPENDENT SECOND AUDITOR (30 builds: 12 modules, 9 rival-side and
#   9 gold-side witness files, all regenerated through the gate's own
#   `witness_file`). Exit codes observed: 3 positives 0; 9 rivals 1; 9 rival-side
#   witnesses 0; 9 gold-side witnesses 1. Every gold-side log carries the semantic
#   `decide` refutation naming its own concrete input, and NO gold-side log contains
#   a stuck reduction, an unknown constant/identifier, a type error or a timeout —
#   checked by grepping for each, so the gate's `witness-undecided` screen is not
#   merely unhit but inapplicable here. The nine gold-side messages quote nine
#   DISTINCT tester applications, so pts = 9 is a fact about the builds and not a
#   count of manifest entries. Two further controls, because "gold fails" only means
#   "discriminator" if the exit code carries information at all:
#     * TESTER-NOT-STUCK / anti-forgery: the witness that refutes weak-suppress-all
#       at (html, F, T, [m]) was ALSO built against weak-drop-ebook — a rival that
#       AGREES with gold there — and it fails (exit 1) with `decide proved … is
#       false`. So `decide` genuinely evaluates this tester and a claim asserting a
#       correct impl is wrong is rejected, which is exactly what a stuck kernel
#       could not do.
#     * weak-drop-last's DOMAIN BOUNDARY, re-measured rather than trusted: the same
#       witness shape refutes that rival at a ONE-page keep set (exit 0) and does
#       NOT refute it at the EMPTY keep set (exit 1, `dropLast [] = []` agreeing
#       with gold). The break really is `generated ≠ []`, as the rationale states.
#   Frame-mutation was re-measured too and the recorded reason reproduces verbatim:
#   an impl assigning to the read-only input fails to ELABORATE (`generated cannot
#   be mutated, only variables declared using `let mut` can be mutated`, followed by
#   `Failed to parse an assertion without names: WPGen sorry`) — not a spec
#   violation, so it cannot carry a witness. The `let mut` SHADOW form does
#   elaborate and is rejected on `ensures_2` (exit 1) as a plain VALUE bug, i.e. it
#   duplicates weak-suppress-all's point and defends no frame property, confirming
#   the port's disposition.
AXIOM_TESTS = []
