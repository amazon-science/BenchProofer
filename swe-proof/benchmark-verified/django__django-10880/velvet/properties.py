"""properties.py — G-PBT falsification battery for django__django-10880 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method rendering an aggregate SQL call over a
per-character string carrier, ``List Char``):

  aggregateAsSql (function : List Char) (distinct : Bool)
      (expressions : List Char) return (out : List Char)
    ensures out = renderCall function distinct expressions    -- the only clause

where ``renderCall f d e = f ++ ['('] ++ distinctQualifier d ++ e ++ [')']`` and
``distinctQualifier true = "DISTINCT ".toList`` (the keyword FOLLOWED BY A
SEPARATOR), ``distinctQualifier false = []``. ``renderCall``/``distinctQualifier``
are TRANSPARENT ``def``s spelled out over the inputs (directive 8), NOT an opaque
answer-key: the whole clause reduces to an ordered concatenation of the three
method inputs and two literal parens, so ``decide`` computes it and no rival can
"echo an oracle" — the only way to satisfy it is to build the exact string. The
callee it stands in for (the generic percent-template renderer) is validated
equal by G-AX (an A-reference); this gate ignores that lane.

WHAT THE SPEC DEFENDS. The entire content of the modeled fix is the trailing
SEPARATOR after the deduplication keyword: with deduplication requested the
qualifier is the keyword + one separator, so it never abuts the argument text
that follows. That separator lives inside ``distinctQualifier true`` and is
pinned by the whole-string equality. The reject rivals attack, in order: the
separator itself (drop it / use the wrong code point), the keyword content
(wrong bytes), and the placement of the two other inputs in the rendered string.

BINDER STRUCTURE (read before judging binder coverage). The postcondition
depends on all THREE inputs — ``function``, ``distinct``, ``expressions``:

  * ``distinct`` selects the qualifier arm. The separator/keyword rivals differ
    from gold ONLY when ``distinct = true`` (they are correct on the
    ``distinct = false`` arm), so they are necessarily refuted at
    ``distinct = true``. To keep ``distinct`` from being pinned at one value
    across the whole battery, two further rivals mishandle the placement of
    ``function`` / ``expressions`` regardless of the qualifier and are refuted at
    ``distinct = false``.
  * ``function`` and ``expressions`` are the surrounding text. A rival that drops
    either from the rendered call is caught by the whole-string equality; those
    two rivals are what VARY these binders across the witness set.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS. The nagini sibling carries this MANDATORY because
    its list inputs are held at a fractional heap permission (``Acc(.,1/2)``) an
    impl can illegally overwrite. Lean/Velvet are referentially transparent:
    every input here is an immutable value, there is no ``mut`` binder, no heap
    and no aliasing — so there is no read-only field to mutate and no substitute
    probe to build. Not fabricated (porting map: this class is vacuous here).
  * ADMISSIBILITY (nagini's F2P-shaped self-call proving the precondition) —
    PORTED, as ``admiss-f2p-render``. The absence of a ``require`` clause is NOT
    a reason to drop this lane: on a TOTAL carrier the analogue of
    PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly an
    F2P-shaped input, which a positive that discharges the obligation at that
    concrete input — by evaluation, as an in-region assert, before closing the
    frozen obligation verbatim — tests directly. Nor would such an assert be the
    trivial ``renderCall … = renderCall …``: the case states the post-image's
    value at the F2P-shaped input as an INDEPENDENTLY WRITTEN literal string, so
    ``decide`` must evaluate the post-image and compare, and a wrong literal
    leaves the goal unsolved (confirmed: the same assert with the qualifier's
    separator removed from the expected literal FAILS to build).
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a transparent ``def`` over
    the method inputs, not an axiomatized oracle; the ``axioms`` region is empty.
  * AXIOM lane (nagini's 2 percent-template-substitution probes) — DROPPED. The
    axiom lane is G-AX's job; this gate ignores ``AXIOM_TESTS``.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``aggregateAsSqlTester function distinct expressions = false`` says the extracted
program's result violates the postcondition at that concrete input. It is checked
in a file whose ``prove_correct`` block has been stripped (so no tactic script
can mask the verdict) and there are no ``require`` clauses, so every input reaches
the postcondition. ``List Char`` literals via ``"…".toList`` and ``Bool`` literals
are fully concrete, so ``decide`` settles the whole equality — no opaque term, no
conditioning, no head binders (hence no consistency obligation).
"""
from pathlib import Path

INSTANCE = "django__django-10880"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The COMPLETE three-line impl body; lies wholly inside
# ---- the single `-- impl-start`/`-- impl-end` region and is unique in
# ---- Solution.lean (both facts asserted at load by _swap). Anchoring on the
# ---- whole body keeps every surgery inside the elided region — the frozen spec
# ---- (the `method` header, `ensures`, and the `pure` region that also spells
# ---- "DISTINCT ") is never touched. ----
_IMPL = (
    '    let qualifier : List Char := if distinct then "DISTINCT ".toList else []\n'
    "    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']\n"
    "    return out"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- the frozen proof, verbatim. Elided from the consumer spec view, so a case
# ---- may retune it; rivals never do (they leave `loom_solve` to fail on the
# ---- postcondition goal). Only the admissibility positive retunes it, and only
# ---- to discharge the EXTRA in-region assert goal it adds. ----
_PROOF = "prove_correct aggregateAsSql by\n  loom_solve"


def _with_impl_reproved(new_impl: str, new_proof: str) -> str:
    """Impl body replaced AND the (elided) proof body retuned."""
    return _swap(_with_impl(new_impl), _PROOF, new_proof)


# ---- witness preamble: reach the contract through Velvet's tester machinery. ----
_TESTER = (
    "extract_program_for aggregateAsSql\n"
    "prove_precondition_decidable_for aggregateAsSql\n"
    "prove_postcondition_decidable_for aggregateAsSql\n"
    "derive_tester_for aggregateAsSql\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Both verified out-of-band with a
    # real build against the frozen `prove_correct … by loom_solve` script.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # The qualifier decision is REORDERED so the no-qualifier arm comes first
        # (`if !distinct then [] else <keyword+separator>`). Semantically identical,
        # different source. Ports the nagini branch-reorder positive.
        "module": _with_impl(
            '    let qualifier : List Char := if !distinct then [] else "DISTINCT ".toList\n'
            "    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']\n"
            "    return out"),
        "rationale": "structurally-different (qualifier decision reordered, the "
                     "no-qualifier arm first) but semantically identical impl must "
                     "verify against `out = renderCall function distinct expressions`. "
                     "If it fails to verify, the spec is over-fit to one branch order "
                     "=> SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-cheapest-render",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest impl satisfying the clause: return the transparent render
        # directly. Because `renderCall` is a spelled-out `def` over the three
        # inputs (not an opaque oracle), this still does the real string
        # construction — there is no wrong echo that verifies. Re-expresses the
        # nagini no-echo (`pos-master-assert`) control.
        "module": _with_impl(
            "    let out := renderCall function distinct expressions\n"
            "    return out"),
        "rationale": "the cheapest impl satisfying the clause still builds the exact "
                     "rendered string, because the post-image `renderCall` is a "
                     "transparent function of the three inputs — not an axiomatized "
                     "answer key. Demonstrates the spec is NOT echo-vulnerable: there "
                     "is no wrong echo that verifies (else this would be a reject "
                     "case). Must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the direction that detects PRECOND-TOO-STRONG. This carrier
    # is TOTAL and the obligation carries no `require`, so the analogue is not "can
    # the precondition be established" but "is the obligation SATISFIABLE, and
    # non-degenerately so, at an F2P-shaped input". The case discharges exactly
    # that at the concrete shape the failing test exercises — a deduplicating
    # aggregate over a conditional argument — as an in-region assert, BY
    # EVALUATION, before closing the frozen obligation verbatim.
    #
    # The assert is LIVE, not a restatement: the expected value is written out
    # independently as a literal string, so `decide` must evaluate the post-image
    # and compare byte-for-byte. Confirmed by a real build of the same case with
    # the separator removed from the expected literal — it does NOT verify
    # (`decide` proved the proposition false), so a wrong claim here is caught.
    # =====================================================================
    {
        "id": "admiss-f2p-render",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            '      (renderCall "COUNT".toList true "CASE WHEN c THEN v END".toList\n'
            '        = "COUNT(DISTINCT CASE WHEN c THEN v END)".toList))\n'
            '    let qualifier : List Char := if distinct then "DISTINCT ".toList else []\n'
            "    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']\n"
            "    return out",
            "prove_correct aggregateAsSql by\n  loom_solve\n  all_goals decide"),
        "rationale": "the obligation is SATISFIABLE, and non-degenerately so, at an "
                     "F2P-shaped input: a deduplicating aggregate whose argument is a "
                     "conditional expression. The in-region assert pins the "
                     "post-image's value there to an independently written literal, so "
                     "`decide` evaluates the whole rendered string and compares — the "
                     "qualifier's keyword AND its trailing separator both have to come "
                     "out right, and the argument text has to survive unfused. If this "
                     "input were out of the obligation's reachable domain, or the "
                     "post-image collapsed there, the assert would not discharge => "
                     "PRECOND-TOO-STRONG. The impl is kept verbatim so the method's own "
                     "`ensures` still discharges; only the elided proof body is "
                     "retuned, and only to clear the extra assert goal.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input (ELABORATES against the rival, FAILS against gold — both
    # halves confirmed out-of-band with real builds) and the refinement argument
    # for why its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "drop-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # THE modeled bug: emit the deduplication keyword with NO trailing
        # separator, so it fuses with the argument text. Correct on the
        # no-deduplication arm, wrong on every deduplication input.
        "module": _with_impl(
            '    let qualifier : List Char := if distinct then "DISTINCT".toList else []\n'
            "    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']\n"
            "    return out"),
        "refinement": "omits the trailing separator after the deduplication keyword — "
                      "the exact pre-fix behaviour. Its faithful real counterpart "
                      "renders the keyword glued onto the first argument token "
                      "(`NAME(KEYWORD<args>)`), an invalid call, so the failing test "
                      "that exercises a deduplicated aggregate over a conditional "
                      "argument still errors — it would NOT resolve. This is the bug "
                      "the fix removes.",
        "rationale": "REJECT from `out = renderCall function distinct expressions`: "
                     "with `distinct = true` the post-image carries the separator the "
                     "rival never emits, so the rendered strings differ. Correct on "
                     "the `distinct = false` sub-domain, wrong on the `distinct = "
                     "true` arm (partial-domain). Refuted at `distinct = true`.",
        "witness": _witness('aggregateAsSqlTester "C".toList true "X".toList'),
    },
    {
        "id": "wrong-separator-comma",
        "kind": "uniqueness",
        "expect": "reject",
        # A delimiter is present after the keyword, but the WRONG code point (a
        # comma, not a space).
        "module": _with_impl(
            '    let qualifier : List Char := if distinct then "DISTINCT,".toList else []\n'
            "    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']\n"
            "    return out"),
        "refinement": "uses a comma as the delimiter after the keyword instead of the "
                      "separator. Its faithful real counterpart renders "
                      "`NAME(KEYWORD,<args>)` — an invalid call — so the failing test "
                      "still errors; it would NOT resolve.",
        "rationale": "REJECT from `out = renderCall …`: the post-image pins the "
                     "qualifier to the keyword + the exact separator code point, not "
                     "a comma; on the `distinct = true` arm the rendered strings "
                     "differ at that byte. Refuted at `distinct = true`. Near-miss to "
                     "drop-separator (a delimiter IS present), refuted at a distinct "
                     "input.",
        "witness": _witness('aggregateAsSqlTester "A".toList true "Y".toList'),
    },
    {
        "id": "wrong-keyword",
        "kind": "uniqueness",
        "expect": "reject",
        # The keyword's final character is dropped, then the correct separator: a
        # delimiter is present and in the right relative place, but the keyword
        # bytes are wrong.
        "module": _with_impl(
            '    let qualifier : List Char := if distinct then "DISTINC ".toList else []\n'
            "    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']\n"
            "    return out"),
        "refinement": "emits a truncated keyword (final character dropped) followed by "
                      "the correct separator. Its faithful real counterpart renders an "
                      "invalid keyword before the argument text, so the failing test "
                      "still errors; it would NOT resolve.",
        "rationale": "REJECT from `out = renderCall …`: the post-image pins the "
                     "qualifier's keyword bytes exactly; on the `distinct = true` arm "
                     "the truncated keyword differs from the pinned one. Refuted at "
                     "`distinct = true`. A separate failure mode from the separator "
                     "rivals (right delimiter, wrong keyword content).",
        "witness": _witness('aggregateAsSqlTester "B".toList true "Z".toList'),
    },
    {
        "id": "sep-wrong-side",
        "kind": "uniqueness",
        "expect": "reject",
        # TIGHTEST near-miss in the qualifier family: the separator IS present and
        # the keyword bytes ARE right — the separator is merely on the wrong SIDE
        # of the keyword (leading, not trailing). Same characters, same length, so
        # no length- or multiset-based reading of the clause could catch it; only
        # the ORDERED equality does.
        "module": _with_impl(
            '    let qualifier : List Char := if distinct then " DISTINCT".toList else []\n'
            "    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']\n"
            "    return out"),
        "refinement": "puts the separator BEFORE the keyword instead of after it. Its "
                      "faithful real counterpart renders the keyword still fused to "
                      "the argument text that follows (`NAME( KEYWORD<args>)`) while "
                      "also spacing it away from the opening delimiter — an invalid "
                      "call either way — so the failing test that exercises a "
                      "deduplicated aggregate over a conditional argument still "
                      "errors; it would NOT resolve.",
        "rationale": "REJECT from `out = renderCall …`: the post-image pins the "
                     "qualifier as the keyword THEN the separator, an ORDERED "
                     "sequence. This rival emits the same character multiset with the "
                     "separator moved to the front, so it agrees with gold on the "
                     "qualifier's length and content-as-a-set and differs only in "
                     "ORDER — the sharpest probe that the clause is a sequence "
                     "equality and not a weaker length-or-contents check. Refuted at "
                     "`distinct = true`.",
        "witness": _witness('aggregateAsSqlTester "M".toList true "W".toList'),
    },
    {
        "id": "qualifier-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        # The one arm of the qualifier NO other rival attacks: every separator /
        # keyword rival is CORRECT when deduplication is not requested, so the
        # `distinct = false` arm of the QUALIFIER itself went unprobed. This rival
        # emits the qualifier unconditionally — correct on the `distinct = true`
        # arm, wrong on `distinct = false`. It is the exact MIRROR of
        # drop-separator's partial domain.
        "module": _with_impl(
            '    let qualifier : List Char := "DISTINCT ".toList\n'
            "    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']\n"
            "    return out"),
        "refinement": "emits the deduplication qualifier even when deduplication was "
                      "not requested. Its faithful real counterpart deduplicates every "
                      "aggregate unconditionally, changing the result of every "
                      "non-deduplicating aggregate in the suite — so the many passing "
                      "tests that read back plain aggregate values would break, and "
                      "the fix would not be behaviour-preserving; it would NOT resolve.",
        "rationale": "REJECT from `out = renderCall …`: the post-image emits NO "
                     "qualifier on the `distinct = false` arm, and this rival emits "
                     "one, so the rendered strings differ there. This is the arm the "
                     "separator/keyword rivals cannot reach — all of them agree with "
                     "gold when the qualifier is absent — so it is what pins the "
                     "qualifier's FALSE arm and makes `distinct` load-bearing in both "
                     "directions. Refuted at `distinct = false`.",
        "witness": _witness('aggregateAsSqlTester "S".toList false "E".toList'),
    },
    {
        "id": "drop-expressions",
        "kind": "uniqueness",
        "expect": "reject",
        # Whole-string / placement attack: omit the argument text from the
        # rendered call entirely. Independent of the qualifier, so refutable on the
        # `distinct = false` arm — this is what varies the `distinct` and
        # `expressions` binders across the battery.
        "module": _with_impl(
            '    let qualifier : List Char := if distinct then "DISTINCT ".toList else []\n'
            "    let out := function ++ ['('] ++ qualifier ++ [')']\n"
            "    return out"),
        "refinement": "drops the rendered argument text from the call. Its faithful "
                      "real counterpart renders `NAME()` with no arguments — a "
                      "different query — so every test that reads back a value "
                      "computed from the arguments still fails; it would NOT resolve.",
        "rationale": "REJECT from `out = renderCall …`, whose post-image places "
                     "`expressions` between the qualifier and the closing paren. The "
                     "rival omits it, so the rendered strings differ whenever "
                     "`expressions` is non-empty. Refuted at `distinct = false` with "
                     "non-empty `expressions` — the witness that VARIES the `distinct` "
                     "binder (false here vs. true for the qualifier rivals) and pins "
                     "the `expressions` binder.",
        "witness": _witness('aggregateAsSqlTester "F".toList false "Q".toList'),
    },
    {
        "id": "drop-function",
        "kind": "uniqueness",
        "expect": "reject",
        # Whole-string / placement attack: omit the leading function name. Also
        # independent of the qualifier; refutable on the `distinct = false` arm.
        "module": _with_impl(
            '    let qualifier : List Char := if distinct then "DISTINCT ".toList else []\n'
            "    let out := ['('] ++ qualifier ++ expressions ++ [')']\n"
            "    return out"),
        "refinement": "drops the leading function name from the call. Its faithful "
                      "real counterpart renders `(<args>)` with no function — invalid "
                      "SQL — so the failing test still errors; it would NOT resolve.",
        "rationale": "REJECT from `out = renderCall …`, whose post-image prepends "
                     "`function` before the opening paren. The rival omits it, so the "
                     "rendered strings differ whenever `function` is non-empty. "
                     "Refuted at `distinct = false` with non-empty `function` — the "
                     "witness that pins the `function` binder (a second "
                     "`distinct = false` point, distinct from drop-expressions' "
                     "input).",
        "witness": _witness('aggregateAsSqlTester "G".toList false "R".toList'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation, 3 uniqueness rivals) plus a
# 2-case AXIOM lane. This bundle models the SAME functional core (the rendered
# aggregate call), so the SPEC lane ports almost directly; the permission and
# precondition classes are vacuous on a referentially-transparent carrier.
#
#   sibling case                 -> here
#   ---------------------------------------------------------------------
#   pos-branch-reorder           -> pos-branch-reorder        PORTED
#   pos-master-assert (no-echo)  -> pos-cheapest-render        RE-EXPRESSED
#   admiss-fshape                -> admiss-f2p-render          PORTED (re-derived)
#   frame-mutate-operands        -> (none)                     VACUOUS (no heap)
#   drop-separator (the bug)     -> drop-separator             PORTED
#   wrong-separator-comma        -> wrong-separator-comma      PORTED
#   wrong-keyword                -> wrong-keyword              PORTED
#   (new — order vs. content)    -> sep-wrong-side             ADDED (audit)
#   (new — qualifier FALSE arm)  -> qualifier-unconditional    ADDED (audit)
#   (new — binder coverage)      -> drop-expressions           ADDED
#   (new — binder coverage)      -> drop-function              ADDED
#   AXIOM_TESTS (2)              -> (none)                     DROPPED (G-AX lane)
#
# RE-EXPRESSED (pos-cheapest-render): nagini's no-echo control asserts, after the
#   result is fully built, that it equals the @Pure oracle `fragment(...)`, to
#   show no wrong echo verifies. Here the post-image `renderCall` is a transparent
#   `def` (no @Pure PSeq to echo), so the equivalent demonstration is the cheapest
#   correct impl — return `renderCall …` directly. It verifies (real build), and
#   because `renderCall` reduces to a concatenation of the inputs there is no
#   wrong echo that could verify. Same argument, expressed for this carrier.
# PORTED (admissibility, re-derived by audit): the earlier reading — "no `require`
#   clause, so nothing to admit, and any assert would be the trivial
#   `renderCall … = renderCall …`" — was wrong on both halves. On a TOTAL carrier
#   the PRECOND-TOO-STRONG analogue is the obligation being unsatisfiable at an
#   F2P-shaped input, and an assert that states the post-image's value there as an
#   INDEPENDENTLY WRITTEN literal is not a restatement: `decide` has to evaluate
#   the post-image and compare byte-for-byte. Landed as `admiss-f2p-render` and
#   confirmed live — the same assert with the separator dropped from the expected
#   literal does NOT build (`decide` proved the proposition false).
# VACUOUS (frame-mutation): this backend is referentially transparent, declares no
#   `mut` binder, and has no heap — there is no read-only input to overwrite and
#   no substitute probe. Not fabricated (porting map: vacuous here).
# ADDED (drop-expressions, drop-function): the nagini whole-sequence pin covered
#   the placement of `function`/`operands` implicitly; here they are made explicit
#   rivals so the `function` and `expressions` binders are attacked and, crucially,
#   so the `distinct` binder is not pinned at `true` across the whole battery — the
#   qualifier rivals are correct on the `distinct = false` arm and can only be
#   refuted at `distinct = true`, so these two carry the `distinct = false` points.
#
#   The seven reject witnesses probe seven DISTINCT input tuples. Across them
#   function takes {"C","A","B","M","S","F","G"}, distinct takes {true,false},
#   expressions takes {"X","Y","Z","W","E","Q","R"}. The load-bearing `distinct`
#   binder is varied across both arms AND the qualifier itself is now attacked on
#   both arms (the separator/keyword rivals on `true`, qualifier-unconditional on
#   `false`); `function` and `expressions` are each varied and each pinned by at
#   least one rival. Every rival's witness was confirmed with two real builds to
#   ELABORATE against the rival and FAIL against the frozen solution, and each
#   gold-side failure is a PLAIN EVALUATION (`decide` proved the proposition
#   false) — not a tactic or unfolding artifact. The forgery check was run on all
#   seven: flipping the claim to `= true` makes the gold-side build SUCCEED, so
#   gold's exit code tracks what the witness claims.
#
# WHAT THE AUDIT PROBED AND DID NOT FIND. Eight further wrong impls were built
#   against the frozen spec and all EIGHT were rejected: qualifier emitted
#   unconditionally, branch polarity inverted, qualifier moved after the argument
#   text, separator leading instead of trailing, separator doubled, the two
#   literal delimiters swapped, function/argument text transposed, and a
#   lowercased keyword. (The two sharpest — the leading separator and the
#   unconditional qualifier — were promoted into the battery above.) Six correct
#   reshapes were also built and all six are provable: `match` on the Bool,
#   right-associated appends, the delimiters as one-char string literals, a staged
#   prefix binding, the branch lifted to the whole body, and routing through the
#   `distinctQualifier` def. The string-literal-delimiter reshape needs the
#   (elided) proof body retuned from `loom_solve` to `loom_solve; all_goals rfl`,
#   which is permitted and is a tactic-tuning fact, not a spec restriction. So the
#   clause is neither too weak nor too strong on this surface.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the generic renderer is an
# A-reference validated there, and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
