"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9258 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps a verdict onto. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region — which the consumer spec view elides
— and, where noted, the ``prove_correct`` tactic body, are changed, so
``markers.same_spec`` holds and every ``prove_correct`` obligation survives with
a byte-identical header) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates).

DEFENDED SURFACE. One contracted method, ``splitUnionTypeField target``, splits
and classifies a type-field string into its piece stream. The observable is a
``List Token``: each element is the raw text of a piece together with a boolean
saying whether that piece is a member handed on as a linked type reference
(``linked = true``) or a separator kept verbatim (``linked = false``). The
single load-bearing postcondition clause is

  (Q) out = splitUnionType target

which pins the ENTIRE output at once — the NUMBER of pieces, the TEXT of each,
AND the alternation of linked members with verbatim separators. There is no
slack: any rival whose piece stream differs at any position, in a piece's text,
or in a piece's linked flag, violates (Q). The bar (vertical pipe) is the
union-type separator from the problem statement: a bar-separated spec such as
``int | str`` is split into one linked reference per named member interleaved
with the verbatim bar separator, i.e. the token stream
``[member "int" (linked), " | " (separator), member "str" (linked)]``. Note the
separator piece carries its SURROUNDING WHITESPACE verbatim (`` | ``, not ``|``),
which is a distinct sub-aspect of (Q) from the linked flag and is attacked
separately below.

``target`` is the sole FREE input; (Q) must hold for every value it takes, which
is what makes the partial-domain rivals below refutable at a concrete point.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on nagini because
    an input may carry a fractional heap permission an impl can overwrite. Lean
    and Velvet are referentially transparent: ``target`` is an immutable value
    (no ``mut`` binder on any input), there is no heap and no aliasing, so there
    is no read-only input to mutate and no substitute probe to build. Not
    fabricated.
  * DIVERGENCE / NON-TERMINATION — CLOSED at the SPEC level, so there is nothing
    left for this battery to reject, and closed with a PROVEN measure rather than
    an annotated one. This bundle sets ``loom.semantics.termination "total"`` AND
    opens ``TotalCorrectness``; the one loop carries ``decreasing rest.length``.
    Under that pairing the verifier REFUSES a loop with no measure, so the
    diverging rival of ``the corpus-wide termination-semantics finding`` — which under the bundle's
    former ``"partial"`` setting satisfied (Q) vacuously and VERIFIED — is now
    rejected with ``Decreasing annotations are required in total correctness
    semantics``. MEASURED on this cell: splicing a ``while true`` prefix with no
    measure onto the frozen impl fails the build with exactly that error, while
    the frozen impl itself still verifies.

    It is still not shippable as a reject CASE, for a reason that has changed. A
    reject case needs a ``witness`` refuting the rival at a concrete input, and a
    diverging rival has no value at any input to refute — its rejection is a
    MISSING-ANNOTATION judgement by the elaborator, not a disagreement with (Q)
    that a witness could exhibit. The class is therefore enforced by the spec's
    own ``set_option`` plus ``open``, not by this manifest.

    THE FORMER RESIDUAL IS NOW DISCHARGED. It used to read: ``"total"`` under
    ``open PartialCorrectness`` demands that a measure be PRESENT but never
    generates the obligation that it DECREASES, so the measure was decorative —
    the corpus-wide hole of ``the corpus-wide spec-hole register``. The bundle now opens
    ``TotalCorrectness``, so the elaborator emits the real goal — MEASURED here as
    ``case «decreasing_1: rest.length» ⊢ (List.drop (stepLen true rest)
    rest).length < rest.length`` — and it is discharged by the frozen pure
    region's own ``stepLen_drop_length_lt``, itself proven from ``stepLen_pos``
    (every step off a nonempty field consumes ≥ 1 character). Nothing about the
    invariant, the precondition or the measure was weakened to get there: the
    measure is still the loop's own ``rest.length``, now PROVEN to decrease. Every
    SPEC case below inherits the closing tactic line, so the positives exercise
    the real obligation too.

    MEASURED both directions on the diverging-``spin`` probe of the old residual
    (a ``while spin < 3 / decreasing spin`` loop whose body sets ``spin := 0``,
    spliced onto the frozen impl), one build each. Under the former ``open
    PartialCorrectness`` the elaborator emitted NO ``decreasing_1`` case at all —
    the false measure was simply never looked at. Under ``open TotalCorrectness``
    the case is emitted and is FALSE: ``case «decreasing_1: spin» ... if_pos :
    spin < 3 ⊢ 0 < spin``. That presence-vs-absence, not any change in exit code,
    is the hole and its closure.

    The closing line is ``all_goals try exact stepLen_drop_length_lt (by
    assumption)`` and the ``try`` is load-bearing in BOTH directions, measured one
    build each. It is needed because the line is shared with variants that leave a
    DIFFERENT residual goal — the loop-free rivals leave none at all (the tactic
    reports "does nothing"), and ``Solution_prepatch.lean`` leaves the
    ``invariant_1`` mismatch that IS its bug; without ``try`` the prepatch twin
    would fail on a tactic TYPE MISMATCH instead of on its real refutation, hiding
    what G-DIFF is supposed to see. And it cannot hide the measure obligation:
    with the measure swapped for a deliberately FALSE one (``decreasing
    target.length``, on an immutable input) the build still fails with ``unsolved
    goals case «decreasing_1: target.length» ⊢ target.length < target.length``.
    ``try`` swallows a failing TACTIC, never an unproven GOAL.
  * UNGROUNDED-ORACLE ECHO — N/A as a WRONG echo. (Q) is grounded entirely in the
    argument ``target``: ``splitUnionType`` is a total front-recursive fold fully
    unfolded over the input's structure; the ``axioms`` region is empty (no
    opaque answer key to echo). An impl that "echoes the oracle" (returns
    ``splitUnionType target``) is simply a CORRECT impl — and is shipped as the
    ``pos-loopfree-fold`` positive precisely because the reject lane refutes its
    witnesses against it (see WITNESS MECHANICS).
  * PARTIAL-DOMAIN / VALUE — APPLIES, heavily; five rivals below.

WITNESS MECHANICS (this is where the port's real work is, and where the previous
attempt was wrong). The spec is a ``method`` CONTRACT, so a witness reaches (Q)
through Velvet's tester machinery. But the oracle ``splitUnionType`` is defined by
WELL-FOUNDED recursion (``termination_by``) and the frozen impl is a ``while``
loop under ``loom.semantics.choice "demonic"``, so its extracted program
elaborates through a ``forIn`` fixpoint the kernel cannot unfold. MEASURED: a
``decide`` against the frozen tester is stuck for EVERY claim — the real witness,
its exact opposite, and a trivially true claim all fail with ``did not reduce to
`isTrue` or `isFalse` ``. So the frozen side's exit code carries NO information,
and a reject case resting on it attests to nothing (the gate calls this
``witness-undecided``).

Each witness therefore does two things. (1) It states the refutation over the
EXTRACTED PROGRAM directly — ``splitUnionTypeFieldExec target ≠ DivM.res
(splitUnionType target)`` — first proving the oracle's concrete value at that
input by chaining the frozen ``splitTokens_cons`` / ``splitTokens_nil`` unfold
lemmas (the two ``@[grind]`` lemmas already in the frozen pure region; no new
lemma is introduced), then reducing the rival's loop-free program. (2) Because
gold still cannot decide, every reject case names ``witness_reference``:
``_LOOPFREE``, a loop-free impl of the SAME frozen spec that the gate
independently checks shares the spec and VERIFIES. An impl the verifier accepts
cannot violate its own spec, so a genuine witness must still fail there.

Verified by hand for all five rivals before shipping (``scripts/lean_verify.sh``,
four builds each): the witness ELABORATES against the rival (exit 0), FAILS
against ``_LOOPFREE`` by genuine refutation (``decide`` proved ``False`` is
false — a real verdict, NOT a stuck reduction), and its OPPOSITE claim fails
against the rival, while the opposite claim SUCCEEDS against ``_LOOPFREE``. That
last pair is what proves the reference side actually decides in both directions,
which is the check the previous attempt's gold side silently failed. No
``sorry`` / ``admit`` / ``native_decide`` anywhere.

BINDER / CLAUSE COVERAGE. The one spec binder is ``target``; the five reject
witnesses probe FIVE DISTINCT points, none shared, varying every property of the
input the spec can depend on — length (3, 5, 5, 5, 9), token count (3 and 5),
separator TEXT (``|`` bare vs `` | `` whitespace-padded), separator KIND (bar vs
comma), and member-name length (1 vs 3 chars). Clause (Q) is attacked on four
independent sub-aspects: whether the input is split at all, WHICH separator set
is honoured, the piece COUNT, the per-piece CLASSIFICATION flag, and the
separator piece's exact TEXT.

AXIOM lane: the ``axioms`` region is empty (no consumed axiom). ``splitTokens``
is an A-REFERENCE deep model validated against the real split engine by G-AX /
axiom_check.py, NOT this gate's job. ``AXIOM_TESTS`` is dropped.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9258"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the method's
# ---- `-- impl-start` / `-- impl-end` block (or, for _PROOF, the `prove_correct`
# ---- tactic body) and is unique in the file — both facts asserted at load by
# ---- _swap, so the manifest breaks loudly if the frozen solution ever changes.
_IMPL_FULL = (
    "    let mut result : List Token := []\n"
    "    let mut rest := target\n"
    "    while rest ≠ []\n"
    "      invariant result ++ splitTokens true rest = splitUnionType target\n"
    "      done_with rest = []\n"
    "      decreasing rest.length\n"
    "    do\n"
    "      let L := stepLen true rest\n"
    "      result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]\n"
    "      rest := rest.drop L\n"
    "    return result"
)
_LOOP_BODY = (
    "      let L := stepLen true rest\n"
    "      result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]\n"
    "      rest := rest.drop L\n"
)
_DECL = "    let mut result : List Token := []\n"
_PROOF = (
    "prove_correct splitUnionTypeField by\n"
    "  unfold splitUnionType\n"
    "  loom_solve\n"
    "  all_goals try exact stepLen_drop_length_lt (by assumption)"
)


# ---------------------------------------------------------------------------
# The shared WITNESS REFERENCE. A loop-free impl of the frozen spec: it returns
# the spec's own fold instead of recomputing it with a `while`. It is a CORRECT
# impl (it verifies — shipped below as `pos-loopfree-fold` so the battery itself
# records that loop-freeness is not what any rival is rejected for), and unlike
# the frozen impl its extracted program reduces, so `decide` against it returns a
# real verdict instead of getting stuck on the loop's fixpoint. The gate checks
# both properties (same spec + verifies) before refuting any witness against it.
# ---------------------------------------------------------------------------
_LOOPFREE = _swap(_BASE, _IMPL_FULL, "    return splitUnionType target")


# ---------------------------------------------------------------------------
# Witness builders. Mirrors of the frozen pure region's scanner, used ONLY to
# compute each witness's expected token stream at authoring time (they never
# appear in a variant). Kept in lock-step with Solution.lean's isWS / isBracket /
# wsLen / delimEllipsis / delimPipe / delimOr / delimLen / contentLen / stepLen /
# splitTokens; a drift shows up immediately as a witness that stops elaborating.
# ---------------------------------------------------------------------------

def _is_ws(c):
    n = ord(c)
    return ((0x9 <= n <= 0xd) or (0x1c <= n <= 0x20)
            or n in (0x85, 0xa0, 0x1680, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000)
            or (0x2000 <= n <= 0x200a))


def _ws_len(s):
    n = 0
    for c in s:
        if not _is_ws(c):
            break
        n += 1
    return n


def _delim_ellipsis(s):
    return 3 if s[:3] == ["."] * 3 else 0


def _delim_pipe(pipe, s):
    if not pipe:
        return _delim_ellipsis(s)
    w1 = _ws_len(s)
    rest = s[w1:]
    if rest[:1] == ["|"]:
        return w1 + 1 + _ws_len(rest[1:])
    return _delim_ellipsis(s)


def _delim_or(pipe, s):
    w1 = _ws_len(s)
    if w1 >= 1:
        rest = s[w1:]
        if rest[:2] == ["o", "r"]:
            w2 = _ws_len(rest[2:])
            if w2 >= 1:
                return w1 + 2 + w2
    return _delim_pipe(pipe, s)


def _delim_len(pipe, s):
    w1 = _ws_len(s)
    r = s[w1:]
    if r and r[0] in "[](),":
        rest = r[1:]
        w2 = _ws_len(rest)
        after = rest[w2:]
        opt = w2 + 2 + 1 if (after[:2] == ["o", "r"] and len(after) >= 3
                             and _is_ws(after[2])) else 0
        return w1 + 1 + opt + _ws_len(rest[opt:])
    return _delim_or(pipe, s)


def _content_len(pipe, s):
    n = 0
    while n < len(s) and _delim_len(pipe, s[n:]) == 0:
        n += 1
    return n


def _step_len(pipe, s):
    d = _delim_len(pipe, s)
    return _content_len(pipe, s) if d == 0 else d


def _split_tokens(pipe, s):
    out = []
    while s:
        L = _step_len(pipe, s)
        out.append((s[:L], _delim_len(pipe, s) == 0))
        s = s[L:]
    return out


def _clist(cs):
    return "[" + ",".join("'" + c + "'" for c in cs) + "]" if cs \
        else "([] : List Char)"


def _toks(spec, pipe=True):
    return "[" + ", ".join(
        "⟨" + _clist(t) + ", " + ("true" if k else "false") + "⟩"
        for t, k in _split_tokens(pipe, list(spec))) + "]"


def _chain(spec, pipe, name):
    """`have <name> : splitTokens <pipe> <spec> = <literal>`, proven by chaining
    the frozen `splitTokens_cons` front-unfold with a decidable drop step per
    piece, then closing on `splitTokens_nil`. Uses only lemmas already present in
    the frozen pure region."""
    p = "true" if pipe else "false"
    out = ["  have " + name + " : splitTokens " + p + " " + _clist(list(spec)),
           "      = " + _toks(spec, pipe) + " := by"]
    cur = list(spec)
    while cur:
        nxt = cur[_step_len(pipe, cur):]
        out.append("    rw [splitTokens_cons (p := " + p + ") (s := "
                   + _clist(cur) + ") (by decide)]")
        out.append("    rw [show List.drop (stepLen " + p + " " + _clist(cur)
                   + ") " + _clist(cur) + " = " + _clist(nxt)
                   + " from by decide]")
        cur = nxt
    out += ["    rw [splitTokens_nil]", "    decide"]
    return "\n".join(out)


def _witness(spec, with_pipe_disabled=False):
    """A refutation witness at the concrete input `spec`.

    States that the rival's EXTRACTED PROGRAM disagrees with the spec's oracle at
    `spec`. Going through `...Exec` rather than the derived tester is what keeps
    the claim reducible: the tester wraps the comparison in a `Decidable`
    instance that gets stuck on the oracle's well-founded recursion, whereas here
    the oracle is first rewritten to a literal by `_chain` and only the rival's
    own (loop-free) program is left to reduce.
    """
    lit = _clist(list(spec))
    body = ["extract_program_for splitUnionTypeField\n",
            "example : splitUnionTypeFieldExec " + lit,
            "    ≠ DivM.res (splitUnionType " + lit + ") := by",
            _chain(spec, True, "hgold"),
            "  have hval : splitUnionType " + lit + " = " + _toks(spec)
            + " := by",
            "    unfold splitUnionType; exact hgold"]
    if with_pipe_disabled:
        # The rival's own answer is `splitTokens false target`, itself
        # well-founded-recursive; pin its value too so the comparison reduces.
        body.append(_chain(spec, False, "hbad"))
    body += ["  unfold splitUnionTypeFieldExec splitUnionTypeField",
             "  rw [hval]"]
    body.append("  simp [NonDetT.run, pure, hbad]" if with_pipe_disabled
                else "  simp [NonDetT.run, pure]")
    body.append("  all_goals decide")
    return "\n".join(body) + "\n"


# ---------------------------------------------------------------------------
# ADMISSIBILITY proof: the frozen tactic keeps its header + body, then an extra
# bullet discharges the prepended in-region assert (which `loom_solve` leaves
# open because the deep model is irreducible). The assert is a LIVE claim, not
# decoration — verified during authoring by flipping the separator's flag to
# `true`, which makes the build fail with "`decide` proved ... is false".
# ---------------------------------------------------------------------------
_ADMISS_ASSERT = (
    "    assert (with_name_prefix `assert\n"
    "      (splitUnionType ['a','|','b'] = [⟨['a'], true⟩, ⟨['|'], false⟩, ⟨['b'], true⟩]))\n"
)
_ADMISS_PROOF = (
    "prove_correct splitUnionTypeField by\n"
    "  unfold splitUnionType\n"
    "  loom_solve\n"
    "  · rw [splitTokens_cons (s := ['a','|','b']) (by decide)]\n"
    "    rw [show List.drop (stepLen true ['a','|','b']) ['a','|','b'] = ['|','b'] from by decide]\n"
    "    rw [splitTokens_cons (s := ['|','b']) (by decide)]\n"
    "    rw [show List.drop (stepLen true ['|','b']) ['|','b'] = ['b'] from by decide]\n"
    "    rw [splitTokens_cons (s := ['b']) (by decide)]\n"
    "    rw [show List.drop (stepLen true ['b']) ['b'] = ([] : List Char) from by decide]\n"
    "    rw [splitTokens_nil]\n"
    "    decide\n"
    "  all_goals try exact stepLen_drop_length_lt (by assumption)"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl were rejected the spec would
    # be SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-bind-piece-local",
        "kind": "soundness",
        "expect": "verify",
        # Bind the constructed piece to a typed local before appending it.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "      let L := stepLen true rest\n"
            "      let piece : Token := ⟨rest.take L, delimLen true rest == 0⟩\n"
            "      result := result ++ [piece]\n"
            "      rest := rest.drop L\n"),
        "rationale": "a correct reshape that binds the constructed piece to a "
                     "typed local before extending the accumulator computes the "
                     "same piece stream, so clause (Q) still discharges; must "
                     "verify (else SPEC-TOO-STRONG). The fold and its invariant "
                     "are unchanged, so the frozen tactic body closes.",
    },
    {
        "id": "pos-hoist-flag-local",
        "kind": "soundness",
        "expect": "verify",
        # Hoist the classification boolean and the singleton fragment into locals.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "      let L := stepLen true rest\n"
            "      let isContent := delimLen true rest == 0\n"
            "      let head : List Token := [⟨rest.take L, isContent⟩]\n"
            "      result := result ++ head\n"
            "      rest := rest.drop L\n"),
        "rationale": "hoisting the linked-classification boolean and the "
                     "appended singleton fragment into typed locals leaves the "
                     "emitted stream unchanged, so clause (Q) still holds; a "
                     "correct reshape must verify.",
    },
    {
        "id": "pos-loopfree-fold",
        "kind": "soundness",
        "expect": "verify",
        # The SHARED witness reference, shipped as a case in its own right.
        # Structurally maximally different from the frozen impl: no loop, no
        # accumulator, no invariant — it returns the spec's fold directly. This
        # is the honest substitute for nagini's ungrounded-oracle-echo slot:
        # because (Q) is grounded in `target` with no opaque answer key, an impl
        # that "echoes the oracle" is simply CORRECT, and saying so out loud is
        # what makes it usable as the reject lane's refutation subject.
        "module": _LOOPFREE,
        "rationale": "a loop-free impl that returns the spec's own fold instead "
                     "of recomputing it with a `while` accumulator satisfies (Q) "
                     "definitionally, so it must verify. Shipped explicitly "
                     "because it is also the `witness_reference` every reject "
                     "case is refuted against: recording its verification HERE "
                     "is what shows loop-freeness is not the property any rival "
                     "is being rejected for. If it FAILED, every reject case's "
                     "refutation subject would be invalid.",
    },

    # =====================================================================
    # ADMISSIBILITY. The method has no `require` clause, so the usual "a normal
    # input satisfies the precondition" probe is vacuous. Re-aimed at the
    # residual admissibility risk on a total domain: that the postcondition is
    # UNSATISFIABLE / DEGENERATE at the interesting point.
    # =====================================================================
    {
        "id": "admiss-interleaved-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _DECL, _ADMISS_ASSERT + _DECL),
            _PROOF, _ADMISS_PROOF),
        "rationale": "the postcondition is satisfiable AND non-degenerate at the "
                     "discriminating point: for a bar-separated spec it demands "
                     "one linked member per name INTERLEAVED with the verbatim "
                     "(non-linked) bar separator — not a single lumped reference "
                     "and not an all-linked stream. The in-region assert must "
                     "discharge (else the obligation is unsatisfiable where the "
                     "behaviour matters); the impl is kept verbatim so clause (Q) "
                     "discharges too. Confirmed LIVE during authoring: flipping "
                     "the separator's flag to linked makes the build fail.",
    },

    # =====================================================================
    # UNIQUENESS / PARTIAL-DOMAIN rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is loop-FREE (so its extracted program
    # reduces), carries a machine-checked witness at a DISTINCT concrete input,
    # and names the shared `witness_reference` because the frozen `while` impl
    # cannot decide anything. Each `refinement` argues why the faithful real
    # counterpart would not resolve the failing test.
    # =====================================================================
    {
        "id": "weak-no-split",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behaviour: never treat the bar as a separator, so the whole
        # field is emitted as ONE linked reference.
        "module": _swap(
            _BASE, _IMPL_FULL, "    return [(⟨target, true⟩ : Token)]\n"),
        "refinement": "emitting the whole field as one linked reference is "
                      "exactly the pre-fix behaviour: with the bar absent from "
                      "the separator set, a bar-separated field is not split and "
                      "renders as a single cross-reference whose target is the "
                      "entire literal string. The failing test writes a "
                      "two-member bar-separated field and asserts TWO separate "
                      "linked references with a verbatim separator between them; "
                      "this rival produces one reference and no separator, so it "
                      "would NOT resolve — this is precisely the change the spec "
                      "senses.",
        "rationale": "REJECT from clause (Q): at the failing test's own field "
                     "shape the oracle is a three-piece stream (member, verbatim "
                     "separator, member) but the rival returns a single piece "
                     "carrying the whole string. PARTIAL-DOMAIN: correct only on "
                     "the no-separator sub-domain. Witness probes the LONGEST "
                     "point (9 chars, 3-char member names, whitespace-padded "
                     "separator) — the exact shape the fix targets.",
        "witness": _witness("int | str"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-pipe-disabled",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on the separator SET: honours every OTHER separator (comma,
        # brackets, word join, ellipsis) but not the bar. Agrees with gold on the
        # whole no-bar sub-domain, which is why it needs a MIXED-separator
        # witness rather than a bar-only one.
        "module": _swap(
            _BASE, _IMPL_FULL, "    return splitTokens false target\n"),
        "refinement": "honouring every separator except the bar is the faithful "
                      "model of the pre-fix separator set — the one alternative "
                      "the change adds. Such a counterpart still passes the "
                      "surviving type-field tests (commas, brackets and the word "
                      "join are unaffected) but leaves a bar-separated field "
                      "unsplit, so the failing test's assertion of two separate "
                      "linked references with a separator between them still "
                      "fails. It would NOT resolve.",
        "rationale": "REJECT from clause (Q) at the SEPARATOR-SET sub-aspect. "
                     "This is the sharpest near-miss in the battery: it agrees "
                     "with gold everywhere except where a bar appears, so a "
                     "bar-only witness would understate what it gets right. The "
                     "witness input MIXES a comma with a bar — the rival splits "
                     "on the comma exactly like gold and then fails to split on "
                     "the bar, lumping the trailing members into one piece, so "
                     "the refutation isolates the bar alternative alone.",
        "witness": _witness("a,b|c", with_pipe_disabled=True),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-drop-separators",
        "kind": "uniqueness",
        "expect": "reject",
        # Splits on the bar and emits one linked reference per member, but OMITS
        # the verbatim separator pieces entirely. Right members, wrong count.
        "module": _swap(
            _BASE, _IMPL_FULL,
            "    return (target.splitOn '|').map (fun p => (⟨p, true⟩ : Token))\n"),
        "refinement": "splitting on the bar yet dropping the separator pieces is "
                      "what a counterpart that filtered the split output down to "
                      "the member pieces would do. The failing test asserts the "
                      "verbatim separator node is present BETWEEN the two linked "
                      "references (it is rendered, not dropped); a stream missing "
                      "it is structurally different and fails the node "
                      "assertion. It would NOT resolve.",
        "rationale": "REJECT from clause (Q) at the piece-COUNT sub-aspect: for a "
                     "three-member field the oracle interleaves two verbatim "
                     "separators among the three members (five pieces) but the "
                     "rival emits only the three members. Witness uses a "
                     "MULTI-BAR input, so the count disagreement is 5-vs-3 "
                     "rather than the minimal 3-vs-2 — moving the binder off the "
                     "single-separator shape the other rivals probe.",
        "witness": _witness("a|b|c"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-link-separators",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on CLASSIFICATION: right piece count, right texts, but every
        # piece — separators included — is flagged as a linked reference.
        "module": _swap(
            _BASE, _IMPL_FULL,
            "    return List.intersperse (⟨['|'], true⟩ : Token) "
            "((target.splitOn '|').map (fun p => (⟨p, true⟩ : Token)))\n"),
        "refinement": "classifying every split piece — separators included — as "
                      "a linked reference is what a counterpart that dropped the "
                      "per-piece separator test would do: it would render the "
                      "verbatim bar as a linked cross-reference instead of a "
                      "plain separator node, so the failing test (which asserts "
                      "the bar is a verbatim separator, NOT a reference) fails. "
                      "It would NOT resolve.",
        "rationale": "REJECT from clause (Q) at the CLASSIFICATION sub-aspect: "
                     "the oracle flags the separator piece non-linked, the rival "
                     "flags it linked. A NEAR-MISS — right count, right texts — "
                     "so it is refuted at the SHORTEST bar input (3 chars), where "
                     "the ONLY thing left to disagree about is the flag; the "
                     "count/structure rivals never reach this sub-aspect.",
        "witness": _witness("x|y"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-bare-bar-text",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAREST MISS: right count, right classification flags — the separator
        # is correctly non-linked — but its TEXT drops the surrounding
        # whitespace, emitting a bare bar instead of the verbatim run.
        "module": _swap(
            _BASE, _IMPL_FULL,
            "    return List.intersperse (⟨['|'], false⟩ : Token) "
            "((target.splitOn '|').map (fun p => (⟨p, true⟩ : Token)))\n"),
        "refinement": "a counterpart that split on the bar and correctly kept "
                      "the separator as a non-reference, but normalised its text "
                      "to a bare bar, would render the separator without its "
                      "surrounding spaces. The failing test asserts the "
                      "separator node's text INCLUDING the spaces around the "
                      "bar, so the node comparison fails on text even though the "
                      "node count and kinds are right. It would NOT resolve.",
        "rationale": "REJECT from clause (Q) at the separator-TEXT sub-aspect — "
                     "the only sub-aspect no other rival attacks, since all of "
                     "them get the separator's text trivially right or drop it "
                     "entirely. The witness input pads the bar with spaces on "
                     "BOTH sides, so the oracle's separator piece is the "
                     "three-character run while the rival's is the bare bar; "
                     "count and flags agree exactly, isolating text alone.",
        "witness": _witness("a | b"),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation rival, 3 uniqueness rivals) plus 2
# axiom-lane entries. This bundle models the SAME single behaviour, so the
# spec-lane port is close to one-for-one, with two positives and two rivals ADDED
# where this carrier exposes sub-aspects nagini's boolean-kind abstraction could
# not express.
#
#   sibling case          -> here                          disposition
#   ---------------------------------------------------------------------
#   pos-local-reshape      -> pos-bind-piece-local          PORTED
#   (none)                 -> pos-hoist-flag-local          ADDED (2nd positive)
#   (none)                 -> pos-loopfree-fold             ADDED (witness ref)
#   admiss-reads           -> admiss-interleaved-shape      RE-AIMED
#   frame-mut-write        -> (none)                        VACUOUS
#   weak-single-xref       -> weak-no-split                 PORTED
#   weak-no-sep            -> weak-drop-separators          PORTED
#   weak-all-xref          -> weak-link-separators          PORTED
#   (none)                 -> weak-pipe-disabled            ADDED (separator set)
#   (none)                 -> weak-bare-bar-text            ADDED (piece text)
#   ax-sound-kinds         -> (none)                        DROPPED (G-AX lane)
#   ax-cover-kinds         -> (none)                        DROPPED (G-AX lane)
#
# VACUOUS (frame-mutation): the sibling rejects an impl that WRITES to a
#   read-only half-permission input. This backend is referentially transparent
#   and declares no `mut` binder on any input, so there is no read-only input to
#   overwrite and no substitute probe. Not fabricated.
# RE-AIMED (admissibility): the sibling's case witnesses that the fractional
#   precondition admits a normal union-type field. This method has NO `require`
#   clause (total domain), so that probe is vacuous; re-aimed at postcondition
#   non-degeneracy at the discriminating point.
# ADDED (two rivals): nagini abstracts each rendered node to a single BOOLEAN
#   kind, so its carrier cannot express a rival that gets the kinds right and the
#   piece TEXT wrong. This carrier keeps `Token.text`, so `weak-bare-bar-text` is
#   refutable here and has no sibling counterpart. Likewise `weak-pipe-disabled`
#   models the separator SET as a parameter the frozen spec exposes, giving the
#   sharpest near-miss in the battery.
# DROPPED (axiom lane): the sibling's two AXIOM_TESTS validate the deep model
#   against the real split engine. That is G-AX / axiom_check.py's job; this gate
#   ignores AXIOM_TESTS.
# NOT PORTABLE AS A REJECT CASE (divergence): see the module docstring. The class
#   is CLOSED by the spec itself — this bundle sets termination "total", opens
#   `TotalCorrectness`, and the loop carries `decreasing rest.length`, so a
#   measure-less diverging rival is rejected by the elaborator and a present-but-
#   false measure is rejected by the `decreasing_1` obligation. It stays unportable
#   as a CASE because a diverging rival has no value at any input for a `witness`
#   to refute; the rejection is a missing-annotation judgement, not a disagreement
#   with (Q). The former residual ("total" checking the measure's PRESENCE only,
#   under `open PartialCorrectness`) is now DISCHARGED — see the module docstring.
#
# BINDER / CLAUSE COVERAGE. The sole binder `target` is probed at FIVE distinct
#   points (`int | str`, `a,b|c`, `a|b|c`, `x|y`, `a | b`) — pts=5, none shared —
#   varying length, piece count, separator text, separator kind and member-name
#   length. Clause (Q) is attacked on every sub-aspect it pins: split-or-not
#   (weak-no-split), WHICH separator set (weak-pipe-disabled), piece COUNT
#   (weak-drop-separators), per-piece CLASSIFICATION (weak-link-separators) and
#   per-piece TEXT (weak-bare-bar-text).
#
# WITNESS DISCRIMINATION — measured, not assumed. Four builds per rival:
#   (a) witness vs rival           -> exit 0 (elaborates: the rival contradicts Q)
#   (b) witness vs _LOOPFREE       -> exit 1 by GENUINE refutation ("`decide`
#                                     proved ... is false"), never a stuck
#                                     reduction
#   (c) OPPOSITE claim vs rival    -> exit 1 (so (a) is not a tautology)
#   (d) OPPOSITE claim vs _LOOPFREE-> exit 0 (so (b)'s exit code carries real
#                                     information — the check the previous
#                                     attempt's gold side silently failed)
#   The frozen `while` impl is NOT usable as the refutation subject: `decide`
#   against it is stuck for every claim, true or false, which is why each case
#   names `witness_reference` instead.
AXIOM_TESTS = []
