"""properties.py — G-PBT falsification battery for django__django-14771 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct relaunchArgv`` obligation survives) and swaps in a
candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: it must elaborate against the rival and FAIL against the frozen
solution).

DEFENDED SURFACE (one contracted method):

  relaunchArgv (executable warnopts isCpython xopts argv) return (out)
    ensures out = relaunchArgvSpec executable warnopts isCpython xopts argv

The method assembles the argument vector used to relaunch the interpreter under
the auto-reloader. The single load-bearing clause pins the WHOLE vector to the
pure, TRANSPARENT ``relaunchArgvSpec`` — the interpreter path, then one flag per
warning option, then (only when the running interpreter is the reference
implementation) one flag per configured runtime option in configured order —
each serialized as ``prefix+key`` when it carries no value and as
``prefix+key+"="+value`` when it does — then the trailing program arguments; off
the reference implementation the runtime options contribute nothing.

WHICH CLAUSE CONSTRAINS THE IMPL. There is ONE top-level ``ensures`` — a full
equality of the produced vector with ``relaunchArgvSpec …``. Its right-hand side
is a composition of the plain ``def``s ``relaunchArgvSpec`` / ``xFlag`` /
``warnFlag`` over the method's OWN inputs; the ``axioms`` region is empty, so
there is NO opaque answer-key oracle to echo — the pin is grounded, not an echo.
Every uniqueness rival therefore attacks a distinguishable FACET of this one
equality: the reference-implementation gate on the runtime-option segment, the
no-value/has-value serialization split, the configured ORDER of that segment,
the count of forwarded options, the PLACEMENT of the segment relative to the
trailing arguments, and forwarding the segment at all.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling reasons over
    fractional permissions on immutable pure-sequence VALUES and records this
    class as N/A by construction. Lean and Velvet are referentially transparent:
    every input here is an immutable value, the method declares no ``mut``
    parameter, and there is no heap, aliasing, or permission system to subvert.
    No read-only input to overwrite, so the class is vacuous. No substitute
    probe is fabricated (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. The post-image is
    ``relaunchArgvSpec …``, a transparent composition over the method's own
    arguments; there is no answer key to echo. The honest cheapest CORRECT
    reshape is carried as a POSITIVE control instead.
  * PARTIAL-DOMAIN / VALUE / ORDER / PLACEMENT — the whole reject surface, all
    against the single ensures. Twelve rivals: one per facet above, plus the
    facets the second audit found unattacked (each concatenation leg's own
    contribution, and the warning-option leg's order).
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
    and no recursion), so there is no control flow here to make diverge: a
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
    REJECTED on the measure's own ``decreasing_1`` goal. Dropping the clause
    rather than faking it is refused even earlier, by the elaborator's own
    check (``Decreasing annotations are required in total correctness
    semantics``). So divergence neither applies to this impl nor discharges the
    ``ensures`` clauses vacuously if a rival introduces it.

WITNESS MECHANICS ON THIS BUNDLE. Unlike the opaque-callee siblings, this spec
is FULLY TRANSPARENT: the ``axioms`` region is empty and ``relaunchArgvSpec`` /
``xFlag`` / ``warnFlag`` are plain ``def``s over ``List Char`` / ``Bool`` / an
``XVal`` with ``DecidableEq``, and the gold impl is loop-free. So the Velvet
tester path is LIVE here: ``prove_postcondition_decidable_for`` yields a genuine
decidable instance and ``derive_tester_for relaunchArgv`` emits a computable
``relaunchArgvTester``. Each reject witness states, at one concrete input,

    relaunchArgvTester <executable> <warnopts> <isCpython> <xopts> <argv> = false

i.e. the extracted program's output violates the ensures at that point.
Machine-checked both halves with ``scripts/lean_verify.sh``: every witness
ELABORATES against its rival (``decide`` closes; exit 0) and FAILS against the
frozen solution (``decide`` reports the tester is TRUE there, so the ``= false``
goal cannot close; exit 1) — the discrimination the gate requires. No witness
binds a hypothesis (every input is a concrete literal that decides the tester),
so no consistency probe is needed. No banned token
(sorry/admit/native_decide/axiom/opaque).

BINDER / POINT COVERAGE. The ensures has five input binders
(``executable``, ``warnopts``, ``isCpython``, ``xopts``, ``argv``); the twelve
reject witnesses probe twelve DISTINCT points and vary every binder —
``warnopts`` is empty in some, one-element in others, two-element in others;
``isCpython`` is exercised both ``false`` (drop-guard) and ``true`` (the rest);
``xopts`` ranges over bare/keyed and one/two-element lists; ``argv`` is empty in
some and non-empty in others. No binder is held fixed by every witness.

Distinctness here means distinct ON THE BINDERS THAT MOVE THE VERDICT.
``executable`` also takes a distinct value in every witness, but that is a LABEL,
not a probe: the spec passes it through unchanged, so no two witnesses are
distinct by virtue of differing there alone. The second audit found exactly one
pair that had been counted as two points on that basis and re-aimed one of them
(see the repoint note on ``rival-drop-warnopt-leg``).

AUDIT RECORD (two independent adversarial re-derivations of this battery; the
SECOND audit's findings and repairs are marked).
  * Attack A (statement integrity): every case's module diffed against the
    frozen file. All twelve diffs are confined to the impl region (or, for the
    admissibility case, the elided tactic body); no statement, ``ensures``, or
    pure ``def`` is reformatted or weakened anywhere. Re-derived independently by
    the second audit on all twelve.
  * Attack B (witness discrimination, re-derived): all witnesses rebuilt by hand,
    both halves. Rival builds exit 0; gold builds exit 1 with
    ``Tactic `decide` proved that the proposition … = false is false`` — i.e. the
    tester is TRUE on the frozen impl at that exact input. That is a SEMANTIC
    refutation, not a missing identifier, a type error, or a stuck reduction.
  * Attack B′ (FORGERY test, added by the second audit): for every reject case,
    a second file differing from the witness ONLY in what it claims (``= false``
    flipped to ``= true``) was built against BOTH subjects. Against the frozen
    solution the flipped claim builds CLEAN (exit 0); against the rival it FAILS
    (exit 1) — the exact mirror of the witness itself. So each gold-side exit
    code carries full information about the claim: it is not a hollow signature
    that would fire for any assertion. Both directions machine-checked on all
    twelve cases.
  * Attack C (wrong vs merely different): every rival differs from the frozen
    impl OBSERVABLY on this carrier — each one's witness input is a concrete
    point where the two produce different vectors, machine-checked. No rival is
    definitionally equal to gold; none is vacuous.
  * Attack D (SPEC-TOO-WEAK probe): fourteen NEW wrong impls written and built
    across the two audits — segment before the warning options; keyed value
    dropped; warning-option leg dropped; warning options reversed; interpreter
    path dropped; trailing arguments dropped; wrong flag prefix; inverted gate;
    segment emitted twice; bare options filtered out; segment de-duplicated.
    ALL were REJECTED. No spec hole — expected, and the reason is structural: the
    single ensures is a total functional pin of the whole vector to a transparent
    composition over the method's own inputs, so ANY impl differing from it at
    any input is refutable at that input. Six are now carried as cases (they
    covered facets the ported six left free); the rest are subsumed.
  * Attack E (SPEC-TOO-STRONG probe): six NEW correct reshapes written and built
    — the segment via an explicit ``foldr``; via a double reverse; the gate as an
    if-EXPRESSION with a fully parenthesized concatenation; the gate as a
    ``match``; the segment via ``flatMap`` of singletons; the gate inline as an
    if-expression inside one append. Four verify under the frozen tactic
    unchanged. TWO (the ``match`` gate, the ``flatMap`` segment) do NOT close
    under the frozen script but DO close with a strictly local tactic addition
    (``cases isCpython`` for the first; that plus a three-line ``flatMap``/``map``
    induction for the second) — machine-checked, exit 0. So both are TACTIC-FIT
    limits of the frozen script, not spec soundness holes: the spec accepts every
    faithful correct impl tried, and neither is carried as a positive since a
    positive must close under a proof the case supplies.
  * Repairs made by the FIRST audit: the admissibility case was a HOLLOW positive
    (its module was the frozen file verbatim, so its pass restated the frozen
    build); the drop-gate rival's refinement OVERCLAIMED an F2P failure the
    failing test cannot see, corrected to the demonstrable behavioural
    divergence.
  * Repairs made by the SECOND audit: (1) the admissibility case, though no
    longer hollow, discharged its evaluations at ARBITRARY synthetic points, so it
    tested non-degeneracy SOMEWHERE rather than satisfiability at the shape this
    cell is about — re-aimed at the failing-test-shaped input, with a
    machine-checked falsified control (one expected token corrupted => exit 1) to
    show the ``have``s are load-bearing; (2) ``rival-drop-warnopt-leg``'s witness
    collided with ``rival-segment-before-warnopts`` on every verdict-moving
    binder, so it was re-aimed at a genuinely distinct point; (3) three rivals
    added for the three concatenation legs that were probed only as context —
    the interpreter-path leg's contribution, the trailing-arguments leg's
    presence, and the warning-option leg's ORDER.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. mapping.md §3 records this bundle has
NO axioms (the changed region calls no library function whose behaviour the
proof must assume; every leg is R/I). The nagini sibling's axiom-soundness /
containment probes over its deep ``option_tokens`` model are G-AX's job; the
G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14771"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the entire frozen impl body (the executable code
# ---- lines strictly BETWEEN the method's `-- impl-start` / `-- impl-end`
# ---- comments). Every variant replaces exactly this text, so each edit lies
# ---- wholly inside the one impl region and same_spec holds by construction
# ---- (both facts asserted at load by _swap). The leading/closing marker
# ---- comments are untouched.
_IMPL = (
    "    let mut args : List (List Char) := [executable]\n"
    "    args := args ++ warnopts.map warnFlag\n"
    "    if isCpython then\n"
    "      args := args ++ xopts.map xFlag\n"
    "    args := args ++ argv\n"
    "    return args"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced. The frozen
    `prove_correct` block is left intact; correct reshapes still close under it
    (checked), and rivals' rejection is carried by the witness, not the tactic."""
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble + builder. The spec is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester machinery.
# ---- The carrier is fully transparent and decidable (empty `axioms`; the pure
# ---- defs are over List Char / Bool / an XVal with DecidableEq), so
# ---- `derive_tester_for` yields a COMPUTABLE `relaunchArgvTester` and
# ---- `<tester> args = false` decides. Checked in a file whose `prove_correct`
# ---- block has been stripped, so no tactic script can mask the verdict.
_TESTER = (
    "extract_program_for relaunchArgv\n"
    "prove_precondition_decidable_for relaunchArgv\n"
    "prove_postcondition_decidable_for relaunchArgv\n"
    "derive_tester_for relaunchArgv\n\n"
)


def _witness(args):
    return (
        _TESTER +
        f"example : relaunchArgvTester {args} = false := by\n  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify under the frozen proof. If a faithful correct impl cannot
    # verify, the spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-localvar",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the forwarded runtime-option segment to a typed local
        # inside the reference-implementation branch before appending it. Same
        # value flow, different SSA shape; the frozen proof closes unchanged.
        "module": _impl(
            "    let mut args : List (List Char) := [executable]\n"
            "    args := args ++ warnopts.map warnFlag\n"
            "    if isCpython then\n"
            "      let xf := xopts.map xFlag\n"
            "      args := args ++ xf\n"
            "    args := args ++ argv\n"
            "    return args"),
        "rationale": (
            "binding the forwarded runtime-option segment to a typed local before "
            "appending it is a pure SSA reshape with identical produced vector, so "
            "the single ensures still discharges and the frozen proof closes as-is. "
            "Ports the nagini pos-control-localvar-reshape; if it fails => "
            "SPEC-TOO-STRONG (over-fit to the inline-append code form)."
        ),
    },
    {
        "id": "pos-control-ifexpr",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: compute the (possibly empty) forwarded segment as a single
        # if-EXPRESSION, then build the whole vector as one pure concatenation
        # (no mutable accumulator). Structurally different control/data shape,
        # identical produced vector; the frozen proof still closes.
        "module": _impl(
            "    let extra := if isCpython then xopts.map xFlag else []\n"
            "    let args := [executable] ++ warnopts.map warnFlag ++ extra ++ argv\n"
            "    return args"),
        "rationale": (
            "computing the forwarded segment as an if-expression and assembling "
            "the vector as one pure concatenation (no mutable accumulator) is a "
            "correct impl with a DIFFERENT control/data shape; the produced vector "
            "is unchanged so the ensures discharges. Re-expresses the nagini "
            "pos-control-branch-reorder (that case reordered the trailing dispatch "
            "branches — module-launch / recovery / fallthrough — which this "
            "narrowed carrier does not model; the modeled construction is reshaped "
            "instead). If it fails => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO `require` clause (the
    # pre-conditions region is empty), so nothing could exclude a normal input
    # and the classic "a normal input is admitted" probe has nothing to
    # exclude. On a TOTAL carrier the analogue of PRECOND-TOO-STRONG is the
    # obligation being UNSATISFIABLE at exactly a failing-test-shaped input,
    # which a positive that discharges the obligation at that concrete input —
    # by evaluation, as `have`s, before closing the frozen obligation verbatim —
    # tests directly. MUST verify, else SPEC-UNSATISFIABLE at the very input the
    # cell exists to fix.
    # =====================================================================
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        # SECOND AUDIT REPAIR. Two prior shapes were both weaker than this:
        #   (1) the original port carried `module = _BASE` — the frozen file
        #       verbatim, so its pass restated the frozen build (G-VERIFY/G-GOLD)
        #       and attested to no property of the spec: a hollow positive;
        #   (2) the first repair added two `decide`d evaluations, but at ARBITRARY
        #       synthetic points ("p"/"w"/"k"/"j"/"t") — which tests non-degeneracy
        #       somewhere, not admissibility at the shape this cell is about.
        # Re-aimed at the failing-test-shaped input itself, per the admissibility
        # lane's stated analogue on a total carrier.
        #
        # The impl region stays the frozen one (the admissibility subject must be
        # the gold-shaped computation); the obligation's TACTIC body — an elided
        # region a variant may rewrite freely, so `same_spec` and the
        # `prove_correct relaunchArgv` header both survive — first discharges by
        # `decide` three CONCRETE evaluations of the post-image at the shape the
        # failing test drives:
        #   * the failing-test shape itself — no warning option, on the reference
        #     implementation, a no-value option followed by a has-value option, two
        #     trailing arguments — computes to the one expected vector, in that
        #     order, with both serialization arms distinguished;
        #   * the same shape with a warning option live, which pins the forwarded
        #     segment strictly BETWEEN the warning-option flag and the trailing
        #     arguments (the placement a passing sibling test covers);
        #   * off the reference implementation the same configured options
        #     contribute nothing, leaving path + trailing arguments.
        # Machine-checked load-bearing: the same case with one expected token
        # corrupted (`-Xa=b` -> `-Xa`) FAILS to build (exit 1, `decide` proving the
        # equation false), so these `have`s are not decoration — a degenerate,
        # collapsed, or misordered post-image cannot satisfy them.
        "module": _swap(
            _BASE,
            "prove_correct relaunchArgv by\n"
            "  loom_solve <;>\n"
            "    simp_all [relaunchArgvSpec, List.append_assoc]",
            "prove_correct relaunchArgv by\n"
            "  have atF2PShape :\n"
            "      relaunchArgvSpec \"py\".toList []  true\n"
            "          [(\"utf8\".toList, XVal.bare), (\"a\".toList, XVal.eq \"b\".toList)]\n"
            "          [\"mng\".toList, \"runserver\".toList]\n"
            "        = [\"py\".toList, \"-Xutf8\".toList, \"-Xa=b\".toList,\n"
            "           \"mng\".toList, \"runserver\".toList] := by decide\n"
            "  have withWarnopt :\n"
            "      relaunchArgvSpec \"py\".toList [\"error\".toList] true\n"
            "          [(\"utf8\".toList, XVal.bare)] [\"mng\".toList, \"runserver\".toList]\n"
            "        = [\"py\".toList, \"-Werror\".toList, \"-Xutf8\".toList,\n"
            "           \"mng\".toList, \"runserver\".toList] := by decide\n"
            "  have gatedOff :\n"
            "      relaunchArgvSpec \"py\".toList [] false\n"
            "          [(\"utf8\".toList, XVal.bare), (\"a\".toList, XVal.eq \"b\".toList)]\n"
            "          [\"mng\".toList, \"runserver\".toList]\n"
            "        = [\"py\".toList, \"mng\".toList, \"runserver\".toList] := by decide\n"
            "  loom_solve <;>\n"
            "    simp_all [relaunchArgvSpec, List.append_assoc]"),
        "rationale": (
            "the method carries no `require`, so it is total and nothing could "
            "EXCLUDE an input; on a total carrier the PRECOND-TOO-STRONG analogue "
            "is the obligation being UNSATISFIABLE at a failing-test-shaped input. "
            "The three `decide`d evaluations discharge the post-image at exactly "
            "that shape — no warning option, on the reference implementation, a "
            "no-value option then a has-value option, two trailing arguments — "
            "plus the warning-option-live variant that pins the forwarded segment "
            "strictly between the warning flag and the trailing arguments, plus "
            "the off-reference-implementation vector where the configured options "
            "contribute nothing; the gold computation then closes the frozen "
            "obligation verbatim. Verifies iff the ensures is jointly satisfiable "
            "AT THAT INPUT and non-degenerate there. Ports the nagini "
            "admiss-f2p-shape's INTENT (it asserted the Requires at the "
            "failing-test shape; there is no Requires here, so the shape is "
            "asserted against the post-image instead). Else SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real patch
    # would NOT resolve the F2P (`test_xoptions`). All attack the single ensures;
    # the witnesses probe distinct points and vary every binder.
    # =====================================================================
    {
        "id": "rival-drop-cpython-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Forward the runtime-option segment UNCONDITIONALLY (drop the
        # reference-implementation gate): emit -X flags even off the reference
        # interpreter.
        "module": _impl(
            "    let mut args : List (List Char) := [executable]\n"
            "    args := args ++ warnopts.map warnFlag\n"
            "    args := args ++ xopts.map xFlag\n"
            "    args := args ++ argv\n"
            "    return args"),
        # AUDIT NOTE on the refinement claim below. This case's refinement
        # previously asserted flatly that the faithful patch "would NOT resolve".
        # That overclaims: the failing test does not vary the implementation-name
        # read, so it exercises only the reference interpreter, and no
        # PASS_TO_PASS test covers the ungated path either — a patch dropping the
        # gate would in fact still be reported resolved by the official harness.
        # The claim is corrected to what is actually demonstrable: the rival
        # diverges from the REAL post-patch behaviour on the isCpython binder,
        # which is the behaviour this spec models and which G-CONF differential-
        # tests over that binder. The rejection is earned on the spec, not on the
        # F2P.
        "refinement": (
            "the fix forwards the runtime options ONLY under the "
            "reference-implementation gate; dropping that gate forwards the -X "
            "flags on a non-reference interpreter, where the real post-patch "
            "construction emits none. So the faithful patch is NOT behaviourally "
            "equivalent to the fix — it diverges on the reference-implementation "
            "input, the divergence G-CONF exercises over that binder. Unlike the "
            "other five rivals this divergence is invisible to the failing test "
            "(which never varies that read), so the claim here is spec/behaviour "
            "divergence, not an F2P failure."
        ),
        "rationale": (
            "REJECT from the ensures: `relaunchArgvSpec` selects the EMPTY segment "
            "when `isCpython = false`; forwarding unconditionally makes the "
            "produced vector diverge there. Refuted at `isCpython = false` with one "
            "configured option — the sole witness exercising the false branch of "
            "the gate. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '"a".toList ["w1".toList] false [("k".toList, XVal.bare)] ["z1".toList]'),
    },
    {
        "id": "rival-flip-flag-rule",
        "kind": "uniqueness",
        "expect": "reject",
        # Always emit the has-value serialization (prefix+key+"="+value), even
        # for a no-value option — for which the value is empty, so it emits
        # `-Xkey=` instead of `-Xkey`.
        "module": _impl(
            "    let mut args : List (List Char) := [executable]\n"
            "    args := args ++ warnopts.map warnFlag\n"
            "    if isCpython then\n"
            "      args := args ++ xopts.map (fun kv => \"-X\".toList ++ kv.1 "
            "++ \"=\".toList ++ (match kv.2 with | XVal.bare => [] | XVal.eq v => v))\n"
            "    args := args ++ argv\n"
            "    return args"),
        "refinement": (
            "the fix serializes a no-value option as `prefix+key` (no `=`); forcing "
            "the has-value form makes a no-value option emit `key=` with a trailing "
            "separator instead. The failing test supplies a no-value option and "
            "pins the bare form, so the faithful patch fails `test_xoptions` (would "
            "not resolve)."
        ),
        "rationale": (
            "REJECT from the ensures: `xFlag` maps an `XVal.bare` option to "
            "`prefix+key` with NO separator; a rival appending `=` (empty value) "
            "diverges from the post-image on any bare option. Refuted at a single "
            "bare option — the no-value serialization facet. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness('"b".toList [] true [("k".toList, XVal.bare)] []'),
    },
    {
        "id": "rival-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the forwarded segment in REVERSE configured order.
        "module": _impl(
            "    let mut args : List (List Char) := [executable]\n"
            "    args := args ++ warnopts.map warnFlag\n"
            "    if isCpython then\n"
            "      args := args ++ (xopts.reverse.map xFlag)\n"
            "    args := args ++ argv\n"
            "    return args"),
        "refinement": (
            "the fix preserves the configured order of the runtime options; a "
            "reversed order emits them back-to-front. The failing test supplies two "
            "options and pins their configured order, so the faithful patch fails "
            "`test_xoptions` (would not resolve)."
        ),
        "rationale": (
            "REJECT from the ensures: `relaunchArgvSpec` maps `xopts` in place "
            "(order-preserving); reversing yields a different vector whenever two "
            "or more options are configured. Refuted at a TWO-option input — a "
            "distinct point from the single-option rivals, and the only witness "
            "that pins configured order. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '"c".toList ["w2".toList] true '
            '[("a".toList, XVal.bare), ("b".toList, XVal.bare)] []'),
    },
    {
        "id": "rival-only-first-option",
        "kind": "uniqueness",
        "expect": "reject",
        # Forward ONLY the first configured option (drop the rest).
        "module": _impl(
            "    let mut args : List (List Char) := [executable]\n"
            "    args := args ++ warnopts.map warnFlag\n"
            "    if isCpython then\n"
            "      args := args ++ ((xopts.take 1).map xFlag)\n"
            "    args := args ++ argv\n"
            "    return args"),
        "refinement": (
            "the fix forwards EVERY configured runtime option; forwarding only the "
            "first drops the rest. The failing test supplies two options and pins "
            "both, so the faithful patch loses the second and fails `test_xoptions` "
            "(would not resolve)."
        ),
        "rationale": (
            "REJECT from the ensures: `relaunchArgvSpec` maps over ALL of `xopts`; "
            "taking only the first yields a strictly shorter segment whenever two "
            "or more options are configured. Refuted at a TWO-option input with a "
            "non-empty `argv` — a distinct count/argv point from reverse-order. If "
            "it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '"d".toList [] true '
            '[("a".toList, XVal.bare), ("b".toList, XVal.bare)] ["z2".toList]'),
    },
    {
        "id": "rival-options-after-cmdline",
        "kind": "uniqueness",
        "expect": "reject",
        # Insert the forwarded segment AFTER the trailing program arguments
        # instead of before them.
        "module": _impl(
            "    let mut args : List (List Char) := [executable]\n"
            "    args := args ++ warnopts.map warnFlag\n"
            "    args := args ++ argv\n"
            "    if isCpython then\n"
            "      args := args ++ xopts.map xFlag\n"
            "    return args"),
        "refinement": (
            "the fix places the forwarded segment BEFORE the trailing program "
            "arguments; appending it after argv reorders the vector. The failing "
            "test pins the segment ahead of the trailing arguments, so the faithful "
            "patch fails `test_xoptions` (would not resolve)."
        ),
        "rationale": (
            "REJECT from the ensures: `relaunchArgvSpec` concatenates the forwarded "
            "segment BEFORE `argv`; placing it after argv violates the "
            "concatenation order whenever both a runtime option and a trailing "
            "argument are present. Refuted at one option and a non-empty `argv` — "
            "the placement facet, the only witness where the segment and argv are "
            "both non-empty AND their order distinguishes gold. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '"e".toList [] true [("k".toList, XVal.bare)] ["s".toList]'),
    },
    {
        "id": "rival-omit-forwarding",
        "kind": "uniqueness",
        "expect": "reject",
        # The PRE-PATCH behaviour: never forward the runtime options (the segment
        # is omitted even on the reference implementation). This is exactly
        # Solution_prepatch.lean's impl.
        "module": _impl(
            "    let mut args : List (List Char) := [executable]\n"
            "    args := args ++ warnopts.map warnFlag\n"
            "    args := args ++ argv\n"
            "    return args"),
        "refinement": (
            "this is the PRE-PATCH behaviour (Solution_prepatch.lean): the runtime "
            "options are never forwarded, so on the reference implementation with "
            "options configured the child argv omits the -X flags — exactly the bug "
            "the fix corrects. G-DIFF confirms this prepatch fails the ensures; the "
            "F2P `test_xoptions` fails (would not resolve)."
        ),
        "rationale": (
            "REJECT from the ensures: when `isCpython = true` and `xopts` is "
            "non-empty, `relaunchArgvSpec` requires the mapped segment, not the "
            "empty one; omitting it entirely diverges. Refuted with a KEYED "
            "(has-value) option and a non-empty `warnopts` — the only witness "
            "exercising the `XVal.eq` serialization arm, a distinct point from the "
            "bare-option rivals. If it verified => SPEC-TOO-WEAK (admits the bug)."
        ),
        "witness": _witness(
            '"f".toList ["w3".toList] true [("k".toList, XVal.eq "v".toList)] []'),
    },

    # =====================================================================
    # ADDED BY AUDIT (attack D). The six ported rivals leave three facets of the
    # single ensures unattacked; each gap below was found by writing a NEW wrong
    # impl and confirming the frozen spec REJECTS it with a discriminating
    # witness (rival build exit 0, gold build exit 1 by `decide` proving the
    # tester TRUE on gold at that input). No new rival verified, so attack D
    # found no spec hole — these are carried so the battery, not just the audit,
    # covers the facets.
    # =====================================================================
    {
        "id": "rival-segment-before-warnopts",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the forwarded segment BEFORE the warning-option flags instead of
        # after them. The ported placement rival only pins the segment against
        # `argv` on its RIGHT; nothing pinned its left boundary, so a rival that
        # slides it leftward past the warning options was unattacked.
        "module": _impl(
            "    let mut args : List (List Char) := [executable]\n"
            "    if isCpython then\n"
            "      args := args ++ xopts.map xFlag\n"
            "    args := args ++ warnopts.map warnFlag\n"
            "    args := args ++ argv\n"
            "    return args"),
        "refinement": (
            "the fix inserts the forwarded segment AFTER the warning-option flags "
            "and before the trailing arguments; emitting it ahead of the warning "
            "options reorders the vector whenever both a warning option and a "
            "configured runtime option are present, so the faithful patch produces "
            "a different child argv than the fix and is not equivalent to it."
        ),
        "rationale": (
            "REJECT from the ensures: `relaunchArgvSpec` concatenates "
            "`warnopts.map warnFlag` BEFORE the forwarded segment; swapping the "
            "two violates the concatenation order. Pins the segment's LEFT "
            "boundary, which the ported placement rival "
            "(rival-options-after-cmdline) leaves free — it only pins the right "
            "boundary against `argv`. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '"g".toList ["w".toList] true [("k".toList, XVal.bare)] []'),
    },
    {
        "id": "rival-drop-keyed-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Always emit the NO-VALUE serialization, so a has-value option silently
        # loses its value. This is the opposite direction from
        # rival-flip-flag-rule, which only forces the has-value form onto a
        # no-value option; the `XVal.eq` arm was therefore attacked in one
        # direction only.
        "module": _impl(
            "    let mut args : List (List Char) := [executable]\n"
            "    args := args ++ warnopts.map warnFlag\n"
            "    if isCpython then\n"
            "      args := args ++ xopts.map (fun kv => \"-X\".toList ++ kv.1)\n"
            "    args := args ++ argv\n"
            "    return args"),
        "refinement": (
            "the fix serializes a has-value option as `prefix+key+\"=\"+value`; "
            "emitting only `prefix+key` drops the value outright. The failing test "
            "supplies a has-value option and pins its value in the expected "
            "vector, so the faithful patch fails it (would not resolve)."
        ),
        "rationale": (
            "REJECT from the ensures: `xFlag` maps an `XVal.eq value` option to "
            "`prefix+key+\"=\"+value`; a rival emitting the bare form loses the "
            "value on any keyed option. Attacks the `XVal.eq` arm in the "
            "value-DROPPING direction, the converse of rival-flip-flag-rule's "
            "value-ADDING direction. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness('"h".toList [] true [("k".toList, XVal.eq "v".toList)] []'),
    },
    {
        "id": "rival-drop-warnopt-leg",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the warning-option flags entirely. No ported rival touches the
        # `warnopts` binder's CONTRIBUTION — six of six vary it only as context
        # for the runtime-option segment — so the pre-existing warning-option
        # forwarding was pinned by the ensures but never probed.
        "module": _impl(
            "    let mut args : List (List Char) := [executable]\n"
            "    if isCpython then\n"
            "      args := args ++ xopts.map xFlag\n"
            "    args := args ++ argv\n"
            "    return args"),
        "refinement": (
            "the fix leaves the pre-existing warning-option forwarding intact; "
            "dropping that leg regresses behaviour the spec pins and that a "
            "PASS_TO_PASS test over the warning options already covers, so the "
            "faithful patch breaks a passing test (would not resolve)."
        ),
        "rationale": (
            "REJECT from the ensures: `relaunchArgvSpec` includes "
            "`warnopts.map warnFlag` unconditionally; omitting it yields a shorter "
            "vector whenever a warning option is active. The only rival attacking "
            "the `warnopts` leg's CONTRIBUTION rather than using it as context — "
            "a regression facet the six ported rivals leave unprobed. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        # AUDIT REPOINT. This witness previously read
        #   '"i".toList ["w".toList] true [("k".toList, XVal.bare)] []'
        # which is identical to rival-segment-before-warnopts's point on EVERY
        # binder except `executable` — and `executable` never changes the spec's
        # verdict, it is only a label. So the two were two SPELLINGS of one point,
        # not two points, and the manifest's "nine distinct points" claim was
        # inflated by one. Re-aimed at a genuinely distinct point: TWO warning
        # options (so the dropped leg's LENGTH, not just its presence, is pinned),
        # a has-value option, and a non-empty argv. Rebuilt: rival exit 0, gold
        # exit 1 by `decide` proving the tester TRUE there.
        "witness": _witness(
            '"i".toList ["w1".toList, "w2".toList] true '
            '[("k".toList, XVal.eq "v".toList)] ["z".toList]'),
    },

    # =====================================================================
    # ADDED BY THE SECOND AUDIT (attack D again). The nine cases above attack
    # every facet of the FORWARDED SEGMENT, but they leave three legs of the
    # concatenation probed only as CONTEXT, never in their own contribution:
    # the interpreter-path leg, the trailing-arguments leg, and the
    # warning-option leg's ORDER. Each gap below was found by writing a NEW
    # wrong impl; all three were REJECTED with a discriminating witness (rival
    # build exit 0, gold build exit 1 by `decide` proving the tester TRUE at
    # that input, and the FLIPPED claim building CLEAN on gold — so gold's exit
    # code tracks the claim). No new rival verified: attack D found no spec hole.
    # =====================================================================
    {
        "id": "rival-drop-executable",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the leading interpreter path. No prior case attacks the
        # `executable` binder's CONTRIBUTION — all nine only vary it as a
        # distinguishing label, so a rival dropping the leg outright was
        # unattacked even though the ensures pins it.
        "module": _impl(
            "    let mut args : List (List Char) := []\n"
            "    args := args ++ warnopts.map warnFlag\n"
            "    if isCpython then\n"
            "      args := args ++ xopts.map xFlag\n"
            "    args := args ++ argv\n"
            "    return args"),
        "refinement": (
            "the fix leaves the leading interpreter path in place; dropping it "
            "emits a vector with no interpreter to relaunch, regressing behaviour "
            "the spec pins unconditionally and that every PASS_TO_PASS test over "
            "this construction already covers, so the faithful patch breaks "
            "passing tests (would not resolve)."
        ),
        "rationale": (
            "REJECT from the ensures: `relaunchArgvSpec` begins with "
            "`[executable]`; starting from the empty vector drops it at every "
            "input. The only rival attacking the `executable` leg's CONTRIBUTION "
            "rather than using it as a label. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '"p1".toList ["w".toList] true [("k".toList, XVal.bare)] ["z".toList]'),
    },
    {
        "id": "rival-drop-argv",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the trailing program arguments. The placement rival pins argv's
        # ORDER relative to the segment, but nothing pinned argv's PRESENCE.
        "module": _impl(
            "    let mut args : List (List Char) := [executable]\n"
            "    args := args ++ warnopts.map warnFlag\n"
            "    if isCpython then\n"
            "      args := args ++ xopts.map xFlag\n"
            "    return args"),
        "refinement": (
            "the fix ends the vector with the trailing program arguments; dropping "
            "them relaunches the interpreter with no program arguments at all, "
            "regressing behaviour the spec pins unconditionally and that the "
            "PASS_TO_PASS tests over this construction cover, so the faithful "
            "patch breaks passing tests (would not resolve)."
        ),
        "rationale": (
            "REJECT from the ensures: `relaunchArgvSpec` ends with `++ argv`; "
            "omitting it yields a strictly shorter vector whenever a trailing "
            "argument is present. Attacks argv's PRESENCE, which "
            "rival-options-after-cmdline leaves free — that case only pins argv's "
            "ORDER relative to the segment. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '"p2".toList ["w".toList] true [("k".toList, XVal.bare)] ["z".toList]'),
    },
    {
        "id": "rival-reverse-warnopts",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the warning-option flags in REVERSE order. rival-reverse-order
        # pins the runtime-option segment's order and rival-drop-warnopt-leg pins
        # the warning leg's presence; neither pins the warning leg's ORDER.
        "module": _impl(
            "    let mut args : List (List Char) := [executable]\n"
            "    args := args ++ warnopts.reverse.map warnFlag\n"
            "    if isCpython then\n"
            "      args := args ++ xopts.map xFlag\n"
            "    args := args ++ argv\n"
            "    return args"),
        "refinement": (
            "the fix preserves the order of the active warning options; reversing "
            "them emits the flags back-to-front, regressing behaviour the spec "
            "pins and that a PASS_TO_PASS test over the warning options covers, so "
            "the faithful patch breaks a passing test (would not resolve)."
        ),
        "rationale": (
            "REJECT from the ensures: `relaunchArgvSpec` maps `warnopts` in place "
            "(order-preserving); reversing yields a different vector whenever two "
            "or more warning options are active. The ORDER facet of the "
            "warning-option leg — rival-reverse-order pins order only on the "
            "runtime-option segment, and rival-drop-warnopt-leg pins only the "
            "warning leg's presence. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '"p3".toList ["w1".toList, "w2".toList] true '
            '[("k".toList, XVal.bare)] []'),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING.
#
# The nagini sibling contracts a RICHER function (child_arguments): it rebuilds
# the full reloader child argv with a leading `prefix`, a module-launch branch
# (clause A: prefix + options + `-m`/package + argv.drop(1)), a script-present
# branch (clause B), and a Windows-recovery fallthrough (clause C). This bundle
# models only the purely-functional core the fix turns on — the argument-vector
# construction with the -X forwarding — as `relaunchArgv`, whose single ensures
# pins `out = relaunchArgvSpec …` (mapping.md). The module-launch / script-exists
# / windows-recovery branches, the `prefix`, and the `-m` dispatch are downstream
# structure the gold patch does not touch and this bundle does not model, so the
# nagini cases attached to that structure are re-expressed against the modeled
# construction rather than ported verbatim.
#
#   nagini case                    -> here
#   -----------------------------------------------------------------------
#   pos-control-branch-reorder     -> pos-control-ifexpr           RE-EXPRESSED
#   pos-control-localvar-reshape   -> pos-control-localvar         PORTED
#   admiss-f2p-shape               -> admiss-f2p-shape             RE-AIMED
#   weak-drop-cpython-guard        -> rival-drop-cpython-guard     PORTED
#   weak-flip-flag-rule            -> rival-flip-flag-rule         PORTED
#   weak-reverse-order             -> rival-reverse-order          PORTED
#   weak-only-first-option         -> rival-only-first-option      PORTED
#   weak-options-after-cmdline     -> rival-options-after-cmdline  PORTED
#   weak-omit-forwarding-prepatch  -> rival-omit-forwarding        PORTED
#   AXIOM_TESTS (2)                -> (none)                        DROPPED (G-AX)
#   (no nagini counterpart)        -> rival-segment-before-warnopts ADDED (audit D)
#   (no nagini counterpart)        -> rival-drop-keyed-value        ADDED (audit D)
#   (no nagini counterpart)        -> rival-drop-warnopt-leg        ADDED (audit D)
#   (no nagini counterpart)        -> rival-drop-executable          ADDED (audit2 D)
#   (no nagini counterpart)        -> rival-drop-argv                ADDED (audit2 D)
#   (no nagini counterpart)        -> rival-reverse-warnopts         ADDED (audit2 D)
#
# 15 velvet SPEC cases: 2 soundness, 1 admissibility, 12 uniqueness. EVERY nagini
# uniqueness rival that attacks the modeled ensures is ported intact — the six
# facets of the -X forwarding (gate / no-value-vs-has-value serialization /
# order / count / placement / omit) each carry their nagini refinement argument,
# now backed by a machine-checked tester witness. Nothing was omitted for being
# hard to prove. SIX further rivals were ADDED by the two adversarial audits, for
# facets no nagini case covered because the nagini carrier pinned them
# differently. The first audit added three: the segment's LEFT boundary against
# the warning options, the has-value serialization arm in the value-DROPPING
# direction, and the warning-option leg's own contribution. The second audit added
# three more, for the concatenation legs the first nine probed only as CONTEXT:
# the interpreter-path leg's contribution, the trailing-arguments leg's PRESENCE
# (as against its order, which the placement rival already pinned), and the
# warning-option leg's ORDER.
#
# RE-EXPRESSED (pos-control-branch-reorder -> pos-control-ifexpr): the nagini
#   positive reordered the trailing dispatch (recovery-first, then module-launch,
#   then fallthrough) of the RICHER child_arguments. Those branches — module
#   launch, script_exists, windows_recovery — are not modeled on this narrowed
#   carrier, so there is no dispatch to reorder; the structurally-different-but-
#   correct control here computes the forwarded segment as an if-expression and
#   assembles the vector as one pure concatenation (no mutable accumulator).
# PORTED (localvar + 6 rivals): the reshape and the six wrong impls carry across
#   intact — only the carrier changes from a nagini `PSeq` fold to a Velvet
#   `List (List Char)` map. Each rival's nagini refinement (unpatched/non-cpython
#   forwarding / flag-vs-value form / reversed order / dropped options / options
#   after the command line / prepatch omission all fail `test_xoptions`) is
#   preserved and now witnessed at a concrete input.
# RE-AIMED (admiss-f2p-shape -> admiss-f2p-shape): the nagini case re-derived the
#   Requires (aligned option sequences, argv non-empty) at impl entry. This method
#   has NO `require` clause (the pre-conditions region is empty) and no heap
#   permission, so re-deriving a Requires is not available here. The lane is NOT
#   vacuous for that reason though: on a TOTAL carrier the PRECOND-TOO-STRONG
#   analogue is the obligation being UNSATISFIABLE at exactly a
#   failing-test-shaped input, and a positive that discharges the obligation at
#   that concrete input — by evaluation, as `have`s, before closing the frozen
#   obligation verbatim — tests it directly. That is what this case now does, so
#   the nagini case's INTENT (assert the lane at the failing-test shape) is
#   preserved even though its mechanism is not.
#   REPAIRED TWICE. The port discharged the lane by handing the case the frozen
#   file verbatim, which passes but attests to nothing G-VERIFY/G-GOLD had not
#   already established — a hollow positive. The first audit gave it two `decide`d
#   post-image evaluations, which fixed the hollowness but sited them at ARBITRARY
#   synthetic points, so it tested non-degeneracy SOMEWHERE rather than
#   satisfiability at the shape this cell is about. The second audit re-aimed the
#   evaluations at the failing-test shape itself (no warning option, on the
#   reference implementation, a no-value option then a has-value option, two
#   trailing arguments), added the warning-option-live variant that pins the
#   forwarded segment strictly BETWEEN the warning flag and the trailing
#   arguments, and kept the off-reference-implementation vector. Load-bearing,
#   machine-checked: the same case with one expected token corrupted (`-Xa=b` ->
#   `-Xa`) FAILS to build, exit 1, with `decide` proving that equation false.
# FRAME-MUTATION: VACUOUS. The nagini sibling reasons over fractional permissions
#   but records this class N/A (all inputs are immutable pure-sequence values).
#   Velvet is referentially transparent, every input is an immutable value, no
#   `mut` binder, no heap, no aliasing, no permission system — no read-only input
#   to overwrite. No substitute fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own ``decreasing_1`` goal. Dropping the clause
#   rather than faking it is refused even earlier, by the elaborator's own
#   check (``Decreasing annotations are required in total correctness
#   semantics``). So divergence neither applies to this impl nor discharges the
#   ``ensures`` clauses vacuously if a rival introduces it.
# DROPPED (AXIOM_TESTS, 2): mapping.md §3 records this bundle has NO axioms (every
#   leg is R/I; the -X forwarding is modeled deeply, not axiomatized). The nagini
#   axiom-soundness / containment probes over its deep option_tokens model are
#   G-AX's job; the G-PBT gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. The single top-level ensures
#   (`out = relaunchArgvSpec …`) is the only impl-constraining clause and is
#   attacked on all TWELVE of its distinguishable facets (gate, serialization
#   split in BOTH directions, segment order, segment count, segment placement
#   against the trailing arguments, segment placement against the warning
#   options, omission of the segment, omission of the warning-option leg,
#   warning-option ORDER, omission of the interpreter-path leg, omission of the
#   trailing-arguments leg) plus DEFENDED by both positives and the admissibility
#   case (all discharge on gold). Its five input binders are all varied by the
#   reject witnesses: `warnopts` empty, one-element and two-element; `isCpython`
#   both false (drop-guard) and true (the rest); `xopts` over bare/keyed and
#   one/two-element lists; `argv` empty and non-empty.
#   TWELVE distinct witness points, so pts=12 and no binder is held fixed by
#   every witness. Both audits confirmed the variation is MEANINGFUL: each witness
#   input is a point where its own rival and the frozen impl produce different
#   vectors, and the gold-side `decide` proves the tester TRUE there, so every
#   point changes the spec's verdict. The SECOND audit tightened what counts as
#   distinct — `executable` also differs in every witness, but the spec passes it
#   through unchanged, so differing there ALONE does not make two witnesses two
#   points. It found exactly one pair counted that way (drop-warnopt-leg vs
#   segment-before-warnopts, identical on all four verdict-moving binders) and
#   re-aimed one of them.
#
# WITNESS MECHANICS: the carrier is FULLY TRANSPARENT (empty `axioms`; pure defs
#   over List Char / Bool / an XVal with DecidableEq) and the gold impl is
#   loop-free, so the Velvet tester+`decide` path is LIVE: `derive_tester_for`
#   yields a computable `relaunchArgvTester` and `<tester> args = false` decides.
#   Each witness elaborates against its rival (exit 0) and FAILS against the
#   frozen solution (decide reports the tester TRUE there; exit 1). No witness
#   binds a hypothesis, so no consistency probe is needed. All NINE checked with
#   scripts/lean_verify.sh: rival exit 0, gold exit 1. The audit independently
#   rebuilt all of them and read the gold-side error text: every one is
#   `Tactic `decide` proved that the proposition … = false is false`, a decided
#   semantic refutation — not an unknown identifier, not a type error, and not the
#   `did not reduce to isTrue or isFalse` stuck reduction that would make the
#   exit code meaningless.
AXIOM_TESTS = []
