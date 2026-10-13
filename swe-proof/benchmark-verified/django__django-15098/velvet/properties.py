"""properties.py — G-PBT falsification battery for django__django-15098 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct resolvePathLanguage``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct resolvePathLanguage``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation; it is judged by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (``resolvePathLanguage (path : List Char) (strict : Bool)
  return (out : Option (List Char))``):
  Resolve the leading locale tag a URL path carries to a configured language.
  The method scans the path left-to-right recognising the tag (a primary subtag
  plus UP TO TWO further subtags — a script and a region — per the public
  langtag grammar), then resolves that tag to a language. Two input binders,
  ``path`` and ``strict``, one precondition, and one top-level postcondition:

    (P1) require ∀ c ∈ path, c.toNat < 128     the path is ASCII (in-domain)
    (Q1) ensures out = pathLanguage path strict  the resolved language is the
         path's leading locale tag (decoded with the primary subtag plus up to
         TWO additional subtags) resolved through the configured language table.

  ``pathLanguage`` is a deterministic function of ``(path, strict)`` fully
  unfolded in the frozen pure region: the leading-locale-tag automaton
  ``leadingLocaleTag 2`` (``initLS`` / ``lstep`` / ``ldecode`` folded over the
  path with subtag budget TWO) composed with the language resolver
  ``listedLanguage``.

THE BEHAVIOURAL DELTA of the gold change is the subtag budget: ``?`` / budget 1
  (pre-patch — a primary subtag plus at most ONE further subtag) becomes
  ``{0,2}`` / budget 2 (patched — plus up to TWO). Q1 pins ``out`` to
  ``pathLanguage``, whose automaton runs at budget 2; every budget rival below is
  refuted through Q1 because it decodes a DIFFERENT tag on some path, which
  resolves to a different language.

CARRIER NOTE — conditioning on the opaque resolver. ``listedLanguage`` is an
  OPAQUE axiom (``List Char → Bool → Option (List Char)``, the weakest possible
  contract: no asserted property). Its value at any concrete tag is unknown to
  the kernel, so a rival that decodes the WRONG tag cannot be refuted at a
  literal input by ``decide`` — the resolved language never reduces to a
  concrete value. This is what makes the surface faithful (no concrete resolved
  language is pinned), and it dictates the witness technique. Two decidable
  facts DO hold about the automaton half of Q1: the tag ``leadingLocaleTag 2``
  decodes to reduces under ``decide``, and on some paths one side of Q1 is
  ``none`` (an unrecognised / rejected tag resolves to no language, regardless of
  ``listedLanguage``). Each budget/termination rival changes the DECODED TAG on a
  chosen path — from ``none`` to ``some t`` or the reverse — and the witness
  refutes it by CONDITIONING on the resolver at that one tag:

    * where the RIVAL decodes ``some t`` and gold decodes ``none``: gold's Q1 is
      ``out = none`` (``pathLanguage`` reduces to ``none`` by ``decide``), the
      rival's is ``out = listedLanguage t strict``; hypothesise
      ``listedLanguage t strict ≠ none`` and the two are unequal.
    * where the RIVAL decodes ``none`` and gold decodes ``some t``: symmetric,
      with the hypothesis separating gold's ``listedLanguage t strict`` from the
      rival's ``none``.

  Each witness carries exactly that one hypothesis. It is satisfiable — a single
  disequality about one opaque term with no constraining axiom — so the gate's
  consistency probe cannot derive ``False`` from the binders alone. The ``strict``
  binder is left universally quantified in every witness (never pinned).

WITNESS MECHANICS. ``resolvePathLanguage`` depends on the opaque ``listedLanguage``
  so it is ``noncomputable`` and no executable program / tester can be extracted;
  each witness reaches Q1 DIRECTLY over the method's own ``.run``. Every witness in
  this battery uses ONE shape — the ``_RUN_FULL`` reduction — and the uniformity is
  load-bearing, not stylistic (see WITNESS SHAPE DISCIPLINE below):

    simp only [resolvePathLanguage, pathLanguage, leadingLocaleTag, NonDetT.run,
      NonDetT.bind, NonDetT.pickSuchThat, pickSuchThat, findableEqOpt, bind, pure]
    simp only [ne_eq, DivM.res.injEq]
    intro heq
    exact h heq            -- or `h heq.symm`, per tag-direction

  Against a LOOP-FREE rival the ``.run`` reduces to ``DivM.res (<the rival's
  resolved language>)`` (the ``:| result = …`` demonic choice is discharged by the
  ``findableEqOpt`` Findable instance), BOTH sides of Q1 unfold to their decoded
  tag over ``listedLanguage``, and ``heq`` survives as the CONCRETE equation
  between the two resolver applications — which the conditioning hypothesis
  refutes. Against an impl that satisfies Q1 the same ``simp only`` PROVES the
  equation, so ``heq`` collapses to ``True`` and the final ``exact`` fails. That
  ``True`` vs concrete-equation pair is the refutation. No tester, no banned token
  (``sorry``/``admit``/``native_decide``/``axiom``).

WITNESS SHAPE DISCIPLINE — why every witness reduces BOTH sides with _RUN_FULL.
  The frozen impl is a WHILE-LOOP, and under ``loom.semantics.choice "demonic"``
  its ``.run`` elaborates to an un-normalised ``forIn Lean.Loop.mk`` term the
  kernel will not unfold. That makes gold's exit code easy to misread, and a
  witness may fail on gold for either of two completely different reasons:

    (a) SEMANTIC — the reduction went through and ``simp`` proved Q1's equation
        for that impl (``heq : True``). This is a refutation: the error tracks the
        claim, and flipping the claim changes it.
    (b) SYNTACTIC — a tactic in the witness never matched the loop term at all
        (e.g. a ``rw [if_pos …]`` aimed at a rival-only ``if`` that gold does not
        contain). The error is about the loop's shape, NOT about the claim: the
        byte-identical error appears for the OPPOSITE claim, and it appears just as
        hard against a VERIFYING loop-free impl of the same spec.

  Only (a) discriminates. A witness of form (b) would be recorded ``rejected`` even
  if it asserted gold is CORRECT at that input, so it attests to nothing. This
  battery therefore forbids witnesses that ``rw`` into the rival's own control
  flow, and states every refutation over the two ``listedLanguage`` applications
  that ``_RUN_FULL`` exposes on both sides. Two cases in an earlier revision of
  this file (``reject-drop-termination``, ``reject-allow-empty-run``) were of form
  (b) and have been re-landed in the ``_RUN_FULL`` shape; the audit trail is in the
  per-case notes.

ADVERSARIAL READ of the nagini classes:
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling
    makes it MANDATORY because ``path`` is ``Acc(list_pred(path), 1/2)`` there (a
    HALF, read-only permission), so a rival that WRITES the input must be rejected
    for insufficient permission. Velvet has no such lane: it is referentially
    transparent, ``path`` is an immutable ``List Char`` VALUE parameter, and this
    bundle declares NO ``mut`` binder on the inputs — there is no read-only heap
    reference to overwrite and no store to attempt, so there is no substitute
    probe to build. Not fabricated; VACUOUS by the carrier.
  * UNGROUNDED-ORACLE ECHO — N/A as a wrong echo. Q1 pins ``out`` to
    ``pathLanguage path strict``, a deterministic FUNCTION of the arguments (the
    automaton composed with the resolver), not an opaque answer-key an impl could
    echo. The unique satisfier of Q1 is the correct resolution, so the positive
    controls are cheapest faithful reshapes, not wrong echoes.
  * CONTROL-FLOW-EFFECT — N/A. The method returns a pure ``Option (List Char)``
    abstraction with no raise / effect / capability difference; the one genuine
    control-flow point (a tag matched, ``some``, vs no match, ``none``) is fully
    captured by the value ``out`` (Q1).
  * BUDGET / DOMAIN rivals — the bulk of the battery. Each rival decodes the wrong
    tag on some sub-domain (too small a budget, too large a budget, dropped
    termination, empty run, either side of the trailing-terminator alternative) and
    is refuted through Q1 at the smallest path exposing it.
  * RESOLVER-ARGUMENT rival — `reject-ignore-strict`, added by the audit. Q1
    threads BOTH of the method's binders into `pathLanguage`; the six path rivals
    leave `strict` universally quantified, where it cancels on both sides of Q1, so
    they cannot see a spec that dropped the flag. This one pins the path (the tag
    AGREES with gold) and separates the two resolver applications by the flag
    alone. It is stated by hypothesis, which is exactly what an opaque resolver
    makes sound: `listedLanguage t true ≠ listedLanguage t false` is satisfiable
    because the axiom asserts nothing about either.
"""
from pathlib import Path

INSTANCE = "django__django-15098"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen resolvePathLanguage impl body (the
# ---- while-loop scan with its two nested invariants, the decode, and the
# ---- resolver choice). It lies wholly inside the single resolvePathLanguage
# ---- -- impl-start / -- impl-end region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap), so each edit keeps same_spec by
# ---- construction and leaves the `prove_correct` STATEMENT intact. ----
_IMPL = (
    "    let mut st := initLS\n"
    "    let mut i := 0\n"
    "    while i < path.length\n"
    "      -- invariants-start\n"
    "      invariant 0 ≤ i ∧ i ≤ path.length\n"
    "      invariant st = (path.take i).foldl (lstep 2) initLS\n"
    "      done_with i = path.length\n"
    "      decreasing path.length - i\n"
    "      -- invariants-end\n"
    "    do\n"
    "      st := lstep 2 st path[i]!\n"
    "      i := i + 1\n"
    "    let tag := ldecode st\n"
    "    let result :| result = (match tag with\n"
    "      | none    => none\n"
    "      | some lc => listedLanguage lc strict)\n"
    "    return result\n"
)
assert _BASE.count(_IMPL) == 1, "resolvePathLanguage impl region drifted from expected text"

# ---- the frozen resolvePathLanguage proof block. A tactic body is elided from
# ---- the consumer spec view, so a positive control that reshapes the impl may
# ---- retune it without touching the spec or dropping the obligation. A reject
# ---- rival keeps it VERBATIM (the rejection is the frozen script failing to
# ---- discharge the reshaped obligation, corroborated by the witness). Unique. ----
_PROVE = (
    "prove_correct resolvePathLanguage by\n"
    "  loom_solve\n"
    "  · rw [foldl_take_succ (lstep 2) initLS path i (by omega), ← invariant_2]\n"
    "  · simp_all [pathLanguage, leadingLocaleTag, List.take_length]"
)
assert _BASE.count(_PROVE) == 1, "prove_correct resolvePathLanguage body drifted"


def _impl(new_impl):
    """Full Solution.lean with ONLY resolvePathLanguage's impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_and_proof(new_impl, new_proof):
    """Reshape the impl AND retune the (elided) resolvePathLanguage tactic body."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROVE, new_proof)


# ---- THE witness reduction preamble — the ONLY one this battery uses, and the
# ---- exclusivity is the point (see WITNESS SHAPE DISCIPLINE in the docstring).
# ----
# ---- It unfolds the method `.run` AND `pathLanguage`/`leadingLocaleTag`, so BOTH
# ---- sides of Q1 reduce to their decoded tag over `listedLanguage` and the
# ---- residual `heq` is the concrete equation between the two resolver
# ---- applications — the thing the conditioning hypothesis refutes. Against an
# ---- impl that SATISFIES Q1 the same `simp only` proves that equation, so `heq`
# ---- becomes `True` and the closing `exact` fails: the gold-side error therefore
# ---- tracks the CLAIM, which is what makes it admissible evidence.
# ----
# ---- A variant preamble that reduced only `.run` and then rewrote into the
# ---- rival's own `if` was removed by the audit: gold has no such `if`, so the
# ---- rewrite failed on the un-normalised `forIn Lean.Loop.mk` term for EVERY
# ---- claim, including the opposite one, and against a verifying loop-free impl
# ---- too. Do not reintroduce it. The `:| result = …` demonic choice is
# ---- discharged by the findableEqOpt Findable instance. ----
_RUN_FULL = (
    "  simp only [resolvePathLanguage, pathLanguage, leadingLocaleTag, NonDetT.run,\n"
    "    NonDetT.bind, NonDetT.pickSuchThat, pickSuchThat, findableEqOpt, bind, pure]\n"
)


# A loop-free tag over the recognised word-run (drop the leading '/', take the
# leading word characters). Used by both termination-domain rivals; the empty
# guard is what the empty-run rival relaxes.
def _run_tag(empty_guard):
    cond = "path.headD ' ' = '/' ∧ run ≠ []" if empty_guard else "path.headD ' ' = '/'"
    return (
        "    let run := (path.drop 1).takeWhile isWordChar\n"
        "    let tag : Option (List Char) :=\n"
        f"      if {cond} then some run else none\n"
        "    let result :| result = (match tag with\n"
        "      | none    => none\n"
        "      | some lc => listedLanguage lc strict)\n"
        "    return result\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Port the nagini `pos-ternary-reshape`
    # ARGUMENT ("a faithful, structurally-different correct impl is not rejected")
    # onto this carrier as TWO honest reshapes.
    # =====================================================================
    {
        "id": "pos-loop-free-tag",
        "kind": "soundness",
        "expect": "verify",
        # Replace the explicit while-loop scan with the SAME automaton expressed
        # as the pure `leadingLocaleTag 2` fold (initLS/lstep/ldecode over the
        # whole path), then resolve. Observationally identical to gold on every
        # (path, strict) — same budget 2, same decode — so Q1 still holds. The
        # frozen bullet-script (tuned to the loop's invariants) no longer applies,
        # so the proof is retuned to close the loop-free obligation directly.
        "module": _impl_and_proof(
            "    -- Same automaton as gold, expressed as the pure budget-2 fold\n"
            "    -- (initLS/lstep/ldecode over the whole path) instead of an\n"
            "    -- explicit while-loop scan; then resolve the decoded tag.\n"
            "    let tag := leadingLocaleTag 2 path\n"
            "    let result :| result = (match tag with\n"
            "      | none    => none\n"
            "      | some lc => listedLanguage lc strict)\n"
            "    return result\n",
            "prove_correct resolvePathLanguage by\n"
            "  loom_solve\n"
            "  simp_all [pathLanguage, leadingLocaleTag]\n"),
        "rationale": "PASS SOURCE = Q1. Expressing the scan as `leadingLocaleTag 2 "
                     "path` (the same initLS/lstep/ldecode automaton at the same "
                     "budget 2 that `pathLanguage` uses) computes the SAME decoded "
                     "tag and hence the same resolved language as gold on every "
                     "input, so `out = pathLanguage path strict`. A structurally-"
                     "different faithful reshape MUST verify; else the "
                     "postcondition over-constrains the executable shape "
                     "(SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-direct-spec",
        "kind": "soundness",
        "expect": "verify",
        # Commit the resolved language directly as `pathLanguage path strict`
        # through the `:| result = …` demonic choice. The most direct faithful
        # impl; the frozen bullet-script (which discharges the loop invariants)
        # is retuned to the trivial obligation.
        "module": _impl_and_proof(
            "    -- Commit the resolved language directly: it is exactly the\n"
            "    -- path's leading-locale-tag resolution.\n"
            "    let result :| result = pathLanguage path strict\n"
            "    return result\n",
            "prove_correct resolvePathLanguage by\n"
            "  loom_solve\n"),
        "rationale": "PASS SOURCE = Q1. Committing `pathLanguage path strict` "
                     "directly trivially satisfies `out = pathLanguage path "
                     "strict`. A second faithful reshape that MUST verify; else "
                     "SPEC-TOO-STRONG on the executable staging.",
    },

    # =====================================================================
    # ADMISSIBILITY — ported from nagini `admiss-reads`. The method HAS a real
    # precondition (`require ∀ c ∈ path, c.toNat < 128`), so the nagini probe is
    # NOT vacuous here: it asserts an F2P-shaped request path ("/en-latn-us/")
    # lies inside the admitted domain (every code point is ASCII), i.e. the
    # precondition does not exclude a legitimate request path. The impl is kept
    # behaviourally identical to gold and the in-region `assert` (a decidable
    # fact about that literal path) is discharged, so the method's own obligation
    # still closes. MUST verify, else PRECOND-TOO-STRONG.
    # =====================================================================
    {
        "id": "admiss-ascii-path",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_and_proof(
            "    -- Admissibility: a normal request path is in-domain — every code\n"
            "    -- point of an F2P-shaped path is ASCII, so the precondition does\n"
            "    -- not exclude it.\n"
            "    assert (with_name_prefix `assert (∀ c ∈ \"/en-latn-us/\".toList, c.toNat < 128))\n"
            + _IMPL,
            "prove_correct resolvePathLanguage by\n"
            "  loom_solve\n"
            "  · decide\n"
            "  · rw [foldl_take_succ (lstep 2) initLS path i (by omega), ← invariant_2]\n"
            "  · simp_all [pathLanguage, leadingLocaleTag, List.take_length]\n"),
        "rationale": "the precondition (`∀ c ∈ path, c.toNat < 128`) admits the "
                     "exact F2P-shaped request path \"/en-latn-us/\" (every code "
                     "point ASCII), so a normal request path is in-domain and the "
                     "postcondition is admissible on it. The in-region `assert "
                     "(∀ c ∈ \"/en-latn-us/\".toList, c.toNat < 128)` is a live, "
                     "decidable claim about that F2P point — LIVENESS CONFIRMED by "
                     "the audit: falsifying the bound to `c.toNat < 100` makes the "
                     "build FAIL with \"Tactic `decide` proved that the proposition "
                     "∀ c ∈ \"/en-latn-us/\".toList, c.toNat < 100 is false\", so "
                     "this case's EXIT 0 is contingent on the claim it makes and "
                     "not on the assert being elided; the impl is otherwise gold, so "
                     "`out = pathLanguage path strict` discharges too. If it "
                     "cannot verify ⇒ PRECOND-TOO-STRONG (a legitimate ASCII "
                     "request path would be excluded from the domain).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness that
    # CONDITIONS on the opaque resolver at one concrete path. Each attacks the
    # load-bearing value clause Q1 by decoding the WRONG tag on that path. Each
    # rival keeps the frozen proof VERBATIM (the rejection is the frozen script
    # failing on the reshaped obligation; the witness corroborates it is the SPEC
    # that refutes, not a mere tactic mismatch).
    # =====================================================================

    # ---- the pre-patch bug: subtag budget 1 (the old `?`) ----
    {
        "id": "reject-budget1",
        "kind": "uniqueness",
        "expect": "reject",
        # Decode with subtag budget 1 (the pre-patch `?` / {0,1}) instead of 2.
        # On a script+region path (two additional subtags) the automaton rejects,
        # so the tag is `none` where gold decodes the full tag.
        "module": _impl(
            "    -- PRE-PATCH behaviour: subtag budget 1 (the old `?`), so a\n"
            "    -- script+region path is REJECTED instead of decoded.\n"
            "    let tag := leadingLocaleTag 1 path\n"
            "    let result :| result = (match tag with\n"
            "      | none    => none\n"
            "      | some lc => listedLanguage lc strict)\n"
            "    return result\n"),
        "refinement": "this is exactly the pre-patch behaviour: the subtag budget "
                      "reverts to 1 (the old regex `?` / {0,1}). Its faithful real "
                      "patch is the UNPATCHED matcher, which rejects a "
                      "script+region path — a request for \"/en-latn-us/\" resolves "
                      "to no language instead of the intended locale, failing the "
                      "F2P that now requires a primary subtag plus two further "
                      "subtags to resolve. Does NOT resolve.",
        "rationale": "REJECT from Q1 (out = pathLanguage path strict): on the "
                     "script+region path \"/en-latn-us/\" the budget-1 automaton "
                     "decodes `none` (rejecting the second additional subtag) and "
                     "resolves to `none`, while `pathLanguage` (budget 2) decodes "
                     "the full tag ['e','n','-','l','a','t','n','-','u','s'] and "
                     "resolves it. This is precisely the {0,2} delta the spec "
                     "senses (G-DIFF). If it verifies ⇒ SPEC-TOO-WEAK. Refuted at "
                     "\"/en-latn-us/\", conditioned on "
                     "listedLanguage ['e','n','-','l','a','t','n','-','u','s'] "
                     "strict ≠ none (the resolver is opaque, so the divergence is "
                     "stated at the tag gold decodes, not computed).",
        "witness":
            "example (strict : Bool)\n"
            "    (h : listedLanguage ['e','n','-','l','a','t','n','-','u','s'] strict ≠ none) :\n"
            "    (resolvePathLanguage \"/en-latn-us\".toList strict).run\n"
            "      ≠ DivM.res (pathLanguage \"/en-latn-us\".toList strict) := by\n"
            + _RUN_FULL +
            "  simp only [ne_eq, DivM.res.injEq]\n"
            "  intro heq\n"
            "  exact h heq.symm\n",
    },

    # ---- over-accept: subtag budget 3 (widen past {0,2}) ----
    {
        "id": "reject-budget3",
        "kind": "uniqueness",
        "expect": "reject",
        # Decode with subtag budget 3 instead of 2. On a path with THREE
        # additional subtags the automaton accepts, so the tag is `some t` where
        # gold (budget 2) rejects (`none`).
        "module": _impl(
            "    -- OVER-ACCEPT: subtag budget 3, so a path with three additional\n"
            "    -- subtags is decoded instead of rejected.\n"
            "    let tag := leadingLocaleTag 3 path\n"
            "    let result :| result = (match tag with\n"
            "      | none    => none\n"
            "      | some lc => listedLanguage lc strict)\n"
            "    return result\n"),
        "refinement": "widening the budget to 3 over-accepts: a real patch writing "
                      "{0,3} (or dropping the bound) would extract a 3-subtag run, "
                      "so a request for \"/de-simple-page-test/\" would attempt to "
                      "resolve the 3-subtag tag instead of correctly matching no "
                      "language — failing the test that expects such an "
                      "over-length prefix NOT to resolve. Does NOT resolve.",
        "rationale": "REJECT from Q1: on \"/de-simple-page-test\" (three additional "
                     "subtags) the budget-3 automaton decodes the full tag and "
                     "resolves it, while `pathLanguage` (budget 2) decodes `none` "
                     "and resolves to `none`. If it verifies ⇒ SPEC-TOO-WEAK (the "
                     "upper edge of the {0,2} budget would not be enforced). "
                     "Refuted at \"/de-simple-page-test\", conditioned on "
                     "listedLanguage <that tag> strict ≠ none — a DIFFERENT path "
                     "and the OPPOSITE tag-direction (rival some / gold none) from "
                     "reject-budget1.",
        "witness":
            "example (strict : Bool)\n"
            "    (h : listedLanguage\n"
            "        ['d','e','-','s','i','m','p','l','e','-','p','a','g','e','-','t','e','s','t']\n"
            "        strict ≠ none) :\n"
            "    (resolvePathLanguage \"/de-simple-page-test\".toList strict).run\n"
            "      ≠ DivM.res (pathLanguage \"/de-simple-page-test\".toList strict) := by\n"
            + _RUN_FULL +
            "  simp only [ne_eq, DivM.res.injEq]\n"
            "  intro heq\n"
            "  exact h heq\n",
    },

    # ---- partial-domain: drop the trailing-terminator requirement ----
    {
        "id": "reject-drop-termination",
        "kind": "uniqueness",
        "expect": "reject",
        # Accept the leading word-run regardless of the following character
        # (drop the trailing `(/|$)` anchor the automaton enforces via its
        # status transitions). Correct on properly-terminated paths, but on a run
        # followed by non-'/' punctuation it decodes `some run` where gold rejects.
        "module": _impl(
            "    -- DROP TERMINATION: accept the leading word-run regardless of the\n"
            "    -- character that follows it (no trailing (/|$) anchor).\n"
            + _run_tag(empty_guard=True)),
        "refinement": "dropping the trailing (/|$) anchor treats a word run "
                      "followed by other punctuation as a match: a request for "
                      "\"/aaa.bbb\" (run \"aaa\", next char '.') would extract "
                      "\"aaa\" and try to resolve it, instead of correctly matching "
                      "no language (the tag must be followed by '/' or end of "
                      "path). A PARTIAL-DOMAIN break on the terminator sub-domain "
                      "— correct on every properly-terminated path. Does NOT "
                      "resolve.",
        "rationale": "REJECT from Q1: on \"/aaa.bbb\" (word run \"aaa\" followed by "
                     "'.', not a terminator) the rival decodes `some ['a','a','a']` "
                     "and resolves it, while `pathLanguage` decodes `none` (the "
                     "run is not terminated by '/' or end) and resolves to `none`. "
                     "Correct on every properly-terminated F2P path, so a true "
                     "PARTIAL-DOMAIN attack, not a blanket wrong impl. If it "
                     "verifies ⇒ SPEC-TOO-WEAK on the terminator sub-domain. "
                     "Refuted at \"/aaa.bbb\", conditioned on "
                     "listedLanguage ['a','a','a'] strict ≠ none.",
        # WITNESS (re-landed in the _RUN_FULL shape — see WITNESS SHAPE
        # DISCIPLINE). The previous revision reduced only the method `.run` and
        # then `rw [if_pos …]` into the RIVAL's own `if path.headD ' ' = '/' ∧
        # run ≠ []` guard. Gold has no such `if`, so that rewrite failed on the
        # un-normalised `forIn Lean.Loop.mk` term — a SYNTACTIC failure, form (b):
        # measured, the byte-identical `Tactic 'rewrite' failed: Did not find an
        # occurrence of the pattern if "/aaa.bbb".toList.headD ' ' = '/' ∧ …` was
        # printed by (i) the witness against gold, (ii) the FLIPPED claim (`=`
        # instead of `≠`, i.e. asserting gold is CORRECT at "/aaa.bbb") against
        # gold, and (iii) both of those against the VERIFYING `pos-loop-free-tag`
        # impl. Gold's exit code carried no information about the claim.
        #
        # This shape reduces BOTH sides of Q1 to their decoded tag over
        # `listedLanguage` and never mentions the rival's control flow. Measured:
        # `heq : True` against `pos-loop-free-tag` (simp PROVED Q1's equation
        # there) versus `heq : (match if … then some (takeWhile …) else none with
        # …) = match ldecode (foldl (lstep 2) …) with …` against the rival, and the
        # FLIPPED claim now fails differently on each side (`No goals to be
        # solved` on the verifying impl, `simp made no progress` on gold). The
        # error tracks the claim.
        "witness":
            "example (strict : Bool)\n"
            "    (h : listedLanguage ['a','a','a'] strict ≠ none) :\n"
            "    (resolvePathLanguage \"/aaa.bbb\".toList strict).run\n"
            "      ≠ DivM.res (pathLanguage \"/aaa.bbb\".toList strict) := by\n"
            + _RUN_FULL +
            "  simp only [ne_eq, DivM.res.injEq]\n"
            "  intro heq\n"
            "  exact h heq\n",
    },

    # ---- partial-domain: accept an EMPTY leading run (the no-prefix boundary) ----
    {
        "id": "reject-allow-empty-run",
        "kind": "uniqueness",
        "expect": "reject",
        # Accept even an EMPTY leading word-run (drop the `run ≠ []` guard): a
        # path with a leading '/' but no word character decodes `some []` where
        # gold decodes `none` (the primary subtag requires at least one word char).
        "module": _impl(
            "    -- ALLOW EMPTY RUN: accept even an empty leading word-run (no\n"
            "    -- requirement that the primary subtag be non-empty).\n"
            + _run_tag(empty_guard=False)),
        "refinement": "accepting an empty leading run corresponds to a real patch "
                      "that treated \"matched an empty prefix\" as success: a "
                      "request for \"/\" would feed an empty tag to the resolver "
                      "instead of correctly matching no language (the primary "
                      "subtag requires at least one word character, \\w+, never "
                      "empty). The no-prefix boundary. Does NOT resolve.",
        "rationale": "REJECT from Q1: on \"/\" (a leading '/' with no following "
                     "word character) the rival decodes `some []` and resolves it, "
                     "while `pathLanguage` decodes `none` (the primary subtag needs "
                     "≥1 word char) and resolves to `none`. If it verifies ⇒ "
                     "SPEC-TOO-WEAK at the no-prefix boundary. Refuted at \"/\", "
                     "conditioned on listedLanguage ([] : List Char) strict ≠ none "
                     "— the smallest path, at the exact no-match boundary.",
        # WITNESS (re-landed in the _RUN_FULL shape — same defect and the same
        # repair as reject-drop-termination above). The previous revision's
        # `rw [if_pos (show "/".toList.headD ' ' = '/' …)]` aimed at the RIVAL's
        # guard; measured, `Tactic 'rewrite' failed: Did not find an occurrence of
        # the pattern if "/".toList.headD ' ' = '/' then …` was printed
        # byte-identically for the witness on gold, for the FLIPPED claim on gold,
        # and for both against the verifying `pos-loop-free-tag` impl.
        #
        # This shape: `heq : True` against `pos-loop-free-tag` versus a concrete
        # equation between the rival's `if …` tag and gold's `ldecode (foldl
        # (lstep 2) …)` tag against the rival, and the flipped claim fails
        # differently on each side. The error tracks the claim.
        "witness":
            "example (strict : Bool)\n"
            "    (h : listedLanguage ([] : List Char) strict ≠ none) :\n"
            "    (resolvePathLanguage \"/\".toList strict).run\n"
            "      ≠ DivM.res (pathLanguage \"/\".toList strict) := by\n"
            + _RUN_FULL +
            "  simp only [ne_eq, DivM.res.injEq]\n"
            "  intro heq\n"
            "  exact h heq\n",
    },

    # ---- NEW (audit): the trailing line-terminator clause, both directions ----
    # Attack D found the `status 3` clause of `lstep`/`ldecode` — a word run
    # closed by a single trailing line-terminator that is the LAST character of
    # the path — entirely unprobed by the ported rivals: all four attack the
    # subtag budget or the leading-'/' / non-empty-run guards. Two rivals below
    # break it in opposite directions. Both were confirmed to fail to verify with
    # the frozen proof and to carry a witness that discriminates in the
    # _RUN_FULL shape.
    {
        "id": "reject-drop-terminator-accept",
        "kind": "uniqueness",
        "expect": "reject",
        # UNDER-ACCEPT: refuse the tentative `status 3` close, so a word run
        # ending in a single trailing line-terminator (which IS the last
        # character) decodes `none` where gold decodes the run.
        "module": _impl(
            "    -- UNDER-ACCEPT: refuse to close a tag on a trailing\n"
            "    -- line-terminator, so such a path is rejected outright.\n"
            "    let st := path.foldl (lstep 2) initLS\n"
            "    let tag : Option (List Char) :=\n"
            "      if st.status = 3 then none else ldecode st\n"
            "    let result :| result = (match tag with\n"
            "      | none    => none\n"
            "      | some lc => listedLanguage lc strict)\n"
            "    return result\n"),
        "refinement": "the recognised tag may be closed by a single trailing "
                      "line-terminator that is the last character of the path; a "
                      "real patch that dropped that alternative would make such a "
                      "request path resolve to no language instead of the intended "
                      "locale. A PARTIAL-DOMAIN break on the terminator "
                      "alternative — correct on every path that ends in a path "
                      "separator or a word character. Does NOT resolve.",
        "rationale": "REJECT from Q1: on \"/en\\n\" the scan reaches status 3 "
                     "(`(path.foldl (lstep 2) initLS).status = 3`, by decide) so "
                     "`pathLanguage` decodes ['e','n'] and resolves it, while this "
                     "rival maps status 3 to `none` and resolves to `none`. "
                     "Rival none / gold some. If it verifies ⇒ SPEC-TOO-WEAK on the "
                     "trailing-terminator alternative of the decode. Refuted at "
                     "\"/en\\n\", conditioned on "
                     "listedLanguage ['e','n'] strict ≠ none.",
        "witness":
            "example (strict : Bool)\n"
            "    (h : listedLanguage ['e','n'] strict ≠ none) :\n"
            "    (resolvePathLanguage \"/en\\n\".toList strict).run\n"
            "      ≠ DivM.res (pathLanguage \"/en\\n\".toList strict) := by\n"
            + _RUN_FULL +
            "  simp only [ne_eq, DivM.res.injEq]\n"
            "  intro heq\n"
            "  exact h heq.symm\n",
    },
    {
        "id": "reject-terminator-hard-accept",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-ACCEPT the OTHER way: treat a line-terminator as a HARD close
        # (status 1) rather than the tentative status 3, so a character AFTER the
        # terminator no longer turns the prefix into a rejection.
        "module": _impl(
            "    -- OVER-ACCEPT: treat a line-terminator as a HARD close, so a\n"
            "    -- character after it no longer rejects the prefix.\n"
            "    let st := path.foldl\n"
            "      (fun s c => if c = '\\n' then { s with status := 1 } else lstep 2 s c) initLS\n"
            "    let result :| result = (match ldecode st with\n"
            "      | none    => none\n"
            "      | some lc => listedLanguage lc strict)\n"
            "    return result\n"),
        "refinement": "the trailing line-terminator closes the tag only when it is "
                      "the LAST character of the path; a real patch that treated it "
                      "as an unconditional terminator would resolve a language for "
                      "a path carrying further characters after it, which must not "
                      "match. The exact near-miss on the other side of the same "
                      "clause as reject-drop-terminator-accept. Does NOT resolve.",
        "rationale": "REJECT from Q1: on \"/en\\nx\" gold's tentative close is "
                     "undone by the following 'x' (status 3 → 2), so `pathLanguage` "
                     "decodes `none` and resolves to `none`, while this rival's hard "
                     "close keeps the tag and resolves ['e','n']. Rival some / gold "
                     "none — the OPPOSITE direction from "
                     "reject-drop-terminator-accept on the SAME clause, so the pair "
                     "pins the clause rather than one side of it. If it verifies ⇒ "
                     "SPEC-TOO-WEAK (the terminator would not have to be last). "
                     "Refuted at \"/en\\nx\", conditioned on "
                     "listedLanguage ['e','n'] strict ≠ none.",
        "witness":
            "example (strict : Bool)\n"
            "    (h : listedLanguage ['e','n'] strict ≠ none) :\n"
            "    (resolvePathLanguage \"/en\\nx\".toList strict).run\n"
            "      ≠ DivM.res (pathLanguage \"/en\\nx\".toList strict) := by\n"
            + _RUN_FULL +
            "  simp only [ne_eq, DivM.res.injEq]\n"
            "  intro heq\n"
            "  exact h heq\n",
    },

    # ---- NEW (audit): the `strict` binder, which no ported case discriminated ----
    {
        "id": "reject-ignore-strict",
        "kind": "uniqueness",
        "expect": "reject",
        # Decode the tag correctly (budget 2) but resolve it with the strict flag
        # PINNED to `true`, ignoring the caller's `strict` argument.
        "module": _impl(
            "    -- IGNORE THE FLAG: resolve with the strict flag pinned to `true`\n"
            "    -- instead of the one the caller passed.\n"
            "    let tag := leadingLocaleTag 2 path\n"
            "    let result :| result = (match tag with\n"
            "      | none    => none\n"
            "      | some lc => listedLanguage lc true)\n"
            "    return result\n"),
        "refinement": "the resolution of a recognised tag to a configured language "
                      "depends on BOTH the tag and the strictness of the lookup; a "
                      "real patch that hard-wired the strict lookup would resolve "
                      "the wrong language (or none) for every non-strict request, "
                      "on paths whose tag the change now decodes correctly. Does "
                      "NOT resolve.",
        "rationale": "REJECT from Q1: Q1 pins `out` to `pathLanguage path strict`, "
                     "which threads the caller's flag into the resolver; this rival "
                     "resolves at `true` unconditionally, so at strict = false the "
                     "two sides are `listedLanguage ['e','n'] true` and "
                     "`listedLanguage ['e','n'] false`. Refuted at \"/en\" with "
                     "strict = false, conditioned on those two differing. This is "
                     "the ONLY case in the battery that discriminates the `strict` "
                     "BINDER rather than `path`: the four ported rivals leave "
                     "`strict` universally quantified, so a spec that dropped the "
                     "flag from Q1 would pass all of them. If it verifies ⇒ "
                     "SPEC-TOO-WEAK (the flag would not be threaded).",
        "witness":
            "example (h : listedLanguage ['e','n'] true ≠ listedLanguage ['e','n'] false) :\n"
            "    (resolvePathLanguage \"/en\".toList false).run\n"
            "      ≠ DivM.res (pathLanguage \"/en\".toList false) := by\n"
            + _RUN_FULL +
            "  simp only [ne_eq, DivM.res.injEq]\n"
            "  intro heq\n"
            "  exact h heq\n",
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation, 4 uniqueness rivals) plus 0
# AXIOM_TESTS. This bundle models the SAME single operation (resolve a URL path's
# leading locale tag — primary subtag plus up to TWO additional subtags — to a
# configured language) as the `resolvePathLanguage` method with one postcondition
# clause Q1. Every sibling case is accounted for below.
#
#   sibling case (nagini)       -> here
#   -----------------------------------------------------------------------
#   pos-ternary-reshape         -> pos-loop-free-tag
#                                  + pos-direct-spec              PORTED (x2)
#   admiss-reads                -> admiss-ascii-path              PORTED
#   frame-mut-write             -> (none)                         VACUOUS
#   weak-budget1                -> reject-budget1                 PORTED
#   weak-budget3                -> reject-budget3                 PORTED
#   weak-drop-termination       -> reject-drop-termination        PORTED
#   weak-allow-empty-run        -> reject-allow-empty-run         PORTED
#   AXIOM_TESTS (0)             -> (none)                          N/A
#   (no sibling)                -> reject-drop-terminator-accept   ADDED (audit)
#   (no sibling)                -> reject-terminator-hard-accept   ADDED (audit)
#   (no sibling)                -> reject-ignore-strict            ADDED (audit)
#
# PORTED (positives): the sibling ships ONE structurally-different correct impl
#   (ternary-reshape). It is carried here by TWO honest reshape positives:
#   pos-loop-free-tag (express the while-loop scan as the pure budget-2
#   `leadingLocaleTag 2` fold — same automaton, same budget) and pos-direct-spec
#   (commit `pathLanguage path strict` directly through the `:|` choice). Both are
#   correct on every (path, strict) and both verify EXIT 0 (the frozen bullet
#   script is retuned, since it is tuned to the loop's invariants which the
#   reshapes remove — the SPEC is untouched, only the elided tactic body).
# PORTED (admissibility): the method HAS a real `require ∀ c ∈ path, c.toNat <
#   128`, so the nagini probe is NOT vacuous. The case asserts an F2P-shaped
#   request path ("/en-latn-us/") is in-domain (every code point ASCII) via a
#   live decidable in-region `assert` discharged by a retuned proof; the impl is
#   otherwise gold so Q1 still discharges. Verified EXIT 0. Establishes
#   PRECOND-NOT-TOO-STRONG on the F2P shape.
# PORTED (rivals): all FOUR nagini VALUE rivals port 1:1 — budget1 (the pre-patch
#   `?`, the G-DIFF discriminator), budget3 (over-accept past {0,2}),
#   drop-termination (drop the trailing (/|$) anchor), allow-empty-run (accept an
#   empty primary subtag). Each is refuted through the load-bearing clause Q1 at a
#   DISTINCT path, by CONDITIONING on the opaque resolver `listedLanguage` (the
#   resolved language never reduces to a value, so `decide` is dead on it; the
#   AUTOMATON half of Q1 does reduce, and each rival decodes a different tag —
#   none↔some — on its path; the witness states the divergence at exactly that
#   tag under one disequality hypothesis). Each witness's single hypothesis is a
#   lone disequality about one opaque term, hence satisfiable (the gate's
#   consistency probe cannot derive False from it). Every reject MODULE keeps the
#   frozen proof VERBATIM; the loop-free rivals were confirmed to (a) fail to
#   verify with the frozen script and (b) carry a witness that ELABORATES against
#   the rival and FAILS on gold.
#
#   AUDIT CORRECTION to (b). "Fails on gold" is necessary and NOT sufficient, and
#   two of the four ported rivals originally relied on the insufficient half. Under
#   `loom.semantics.choice "demonic"` gold's while-loop `.run` is an un-normalised
#   `forIn Lean.Loop.mk` term, so a witness that rewrites into the RIVAL's own
#   control flow fails on gold for a reason that has nothing to do with the claim:
#   re-measured, `reject-drop-termination` and `reject-allow-empty-run` printed the
#   byte-identical `Tactic 'rewrite' failed …` for the witness, for the FLIPPED
#   claim (asserting gold is CORRECT at that path), and against a VERIFYING
#   loop-free impl of the same spec. Both have been re-landed in the single
#   `_RUN_FULL` shape, where the gold-side error is `heq : True` (simp PROVED Q1's
#   equation for that impl) versus a concrete equation between the two
#   `listedLanguage` applications for the rival, and the flipped claim fails
#   DIFFERENTLY on each side. See WITNESS SHAPE DISCIPLINE.
#
# ADDED (audit, 3 rivals). Attack D probed the clauses the ported set leaves
#   unattacked and found two:
#   * The trailing-line-terminator alternative of the decode (`lstep`'s tentative
#     `status 3`, which stands only if the terminator is the LAST character). None
#     of the four ported rivals touches it — they attack the subtag budget and the
#     leading-'/' / non-empty-run guards. `reject-drop-terminator-accept` refuses
#     the close (rival none / gold some at "/en\n") and
#     `reject-terminator-hard-accept` makes it unconditional (rival some / gold
#     none at "/en\nx"): opposite directions on the SAME clause, so the pair pins
#     the clause rather than one side of it.
#   * The `strict` BINDER. See WITNESS DISTINCTNESS below — the previous revision
#     recorded it as not-independently-discriminable, which is FALSE on this
#     carrier. `reject-ignore-strict` discriminates it.
#   None of the three verifies against the frozen spec (so no spec hole was found
#   here), and each carries a `_RUN_FULL` witness whose gold-side failure was
#   confirmed to track the claim by the same type-revealing probe.
#
# WITNESS DISTINCTNESS. Seven reject cases over six distinct paths, both
# tag-directions of Q1 exercised on each attacked clause:
#   "/en-latn-us"          reject-budget1                 (rival none / gold some)
#   "/de-simple-page-test" reject-budget3                 (rival some / gold none)
#   "/aaa.bbb"             reject-drop-termination         (rival some / gold none)
#   "/"                    reject-allow-empty-run          (rival some / gold none)
#   "/en\n"                reject-drop-terminator-accept   (rival none / gold some)
#   "/en\nx"               reject-terminator-hard-accept   (rival some / gold none)
#   "/en", strict = false  reject-ignore-strict            (tag agrees, FLAG differs)
# The `path` binder ranges over six distinct values across the boundary of the
# budget delta (too-small / too-large), the two run-shape edges (unterminated run /
# empty run), and both sides of the trailing-terminator clause.
#
# The `strict` binder is DISCRIMINATED, by reject-ignore-strict. A previous
# revision of this file recorded it as "not independently discriminable on this
# carrier — no decidable fact separates `listedLanguage t true` from
# `listedLanguage t false`", and the audit found that reason to be wrong in the way
# the opaque-carrier trap always is: nothing has to DECIDE the difference. The
# witness states it as a HYPOTHESIS (`listedLanguage ['e','n'] true ≠ listedLanguage
# ['e','n'] false`), which is satisfiable precisely BECAUSE the resolver is opaque
# and asserts nothing — the gate's consistency probe cannot derive `False` from it,
# and it was confirmed not to. Without that case a spec whose Q1 dropped the flag
# entirely would pass every other case in the battery, since the other six leave
# `strict` universally quantified and it cancels on both sides of Q1.
#
# VACUOUS (frame / permission-mutation): the nagini sibling makes this lane
#   MANDATORY because its `path` carries `Acc(list_pred(path), 1/2)` — a HALF,
#   read-only heap permission — so a rival that WRITES the input must be rejected
#   for insufficient permission. Velvet has no such lane: it is referentially
#   transparent, `path` is an immutable `List Char` VALUE parameter, and this
#   bundle declares NO `mut` binder on the inputs. There is no read-only heap
#   reference to overwrite and no store to attempt, so there is no substitute
#   probe to build. Not fabricated; VACUOUS by the carrier. (This is the single
#   nagini case with NO velvet analogue.)
#
#   DEMONSTRATED, not asserted (the audit built it). Writing the nagini probe's
#   analogue — a store back into the input, `path := path`, before the gold body —
#   does not produce a rival the verifier judges: the elaborator refuses the file
#   with "`path` cannot be mutated, only variables declared using `let mut` can be
#   mutated", and the `prove_correct` block then fails to parse. That is a
#   compile-time syntactic refusal, i.e. the write is INEXPRESSIBLE on this
#   carrier, not a spec-level rejection the case could attribute to anything. A
#   case built on it would be `witness-unproven` at best and would attest to the
#   parser, not the spec.
#
# COVERAGE. The operation-under-spec obligation (`prove_correct
# resolvePathLanguage`) is defended (two soundness positives + the admissibility
# case) and attacked (SEVEN reject rivals). Its sole load-bearing clause Q1
# (out = pathLanguage path strict) is attacked by all seven, spanning the entire
# behavioural delta and every clause of the automaton the delta runs through:
# the budget lower edge (budget1), the budget upper edge (budget3), the two
# run-shape edges (drop-termination, allow-empty-run), both sides of the
# trailing-terminator alternative (drop-terminator-accept, terminator-hard-accept),
# and the resolver's strictness argument (ignore-strict). The precondition P1
# (∀ c ∈ path, c.toNat < 128) is defended by the admissibility case, whose in-region
# `assert` was confirmed LIVE: falsifying it to `c.toNat < 100` makes the build fail
# with "Tactic `decide` proved that the proposition … is false", so the case's
# verification is contingent on the claim it makes about the F2P point and not on
# the assert being ignored. Both BINDERS are discriminated: `path` across six
# distinct values, `strict` by reject-ignore-strict.
#
# DIVERGENCE. Under `set_option loom.semantics.termination "total"`, which this
# bundle carries, a non-terminating impl is REJECTED rather than verifying
# vacuously: a postcondition is claimed of ALL runs and every loop owes a measure
# that STRICTLY DECREASES. Measured on this cell, a `while true` loop CARRYING
# `decreasing (1 : Nat)` is rejected on the measure's own goal,
# `case «decreasing_1: (1 : Nat)» ... 1 < 1`. An earlier version of this note had
# it backwards, calling vacuous verification a known corpus-wide spec hole
# measured on a `partial` cohort; that is withdrawn, all 500 velvet bundles set
# `"total"`. There is nothing case-shaped to ship for the class in this battery,
# since a reject case needs a witness that elaborates against the rival and a
# diverging rival's module does not compile at all.
# That is the shape with NO measure. A rival that CARRIES a measure which does
# not decrease is refused at the ``prove_correct`` site instead, which the
# witness file strips, so that module does elaborate; but its post-image is
# then an unreduced ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` /
# ``onDoneGadget`` / ``decreasingGadget``, which the kernel will not normalise
# to a value a concrete-input tester can decide. Both shapes therefore land
# ``witness-unproven``.
AXIOM_TESTS = []
