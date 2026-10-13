"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8621 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — which the consumer spec view elides — is changed, plus
the ``prove_correct`` proof body where a reshape needs it, so
``markers.same_spec`` holds and the single ``prove_correct kbdSplit`` obligation
survives with a byte-identical ``method`` header) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL, by GENUINE REFUTATION, against a verifying
impl of the same spec).

DEFENDED SURFACE (one contracted method over a purely-functional core):

  kbdSplit (text : List Char) return (out : List (List Char))
    ensures out = splitParts false [] text

A keystroke is segmented into its keys interleaved with the SEPARATORS that join
them. A separator is EITHER a single connector character (``-``, ``+``, ``^``) OR
a MAXIMAL RUN of whitespace (the full 29-code-point Unicode whitespace class of
``isBlank``), and either form counts as a separator ONLY where a flanking key
character sits immediately on BOTH sides of it — where "flanking key character"
means any character except the line feed U+000A (``isFlank``). A candidate
separator run that reaches the end of the input, or is followed only by a line
feed, is TRIMMED one character at a time (``gapFit``) until a flanking character
follows, and is rejected outright if none does. So a separator at the very start,
at the very end, or standing alone is an ordinary key character.
``splitParts`` is the concrete well-founded ``def`` computing that segmentation
(no ``require`` clause: the domain is TOTAL over every ``text : List Char``,
whitespace and line feeds included). The single load-bearing ``ensures`` pins the
output to that exact interleaving — both flanks of the separator test, the
separator ALPHABET (connectors AND whitespace), the MAXIMAL-MUNCH grouping of a
whitespace run into ONE segment, the line-feed exclusion from the flank class,
the ordering of keys and separators, and the full segment count.

CARRIER NOTE (decisive for this port). ``splitParts`` is a computable ``def``
over ``List Char``; there is NO opaque callee and NO axiom (the ``axioms`` region
is empty). So a rival's disagreement with the spec is a DECIDABLE proposition at
a concrete input, and the uniqueness lane is LIVE. There is likewise no
ungrounded oracle to echo: the cheapest correct impl simply produces the
segmentation, which the positive controls cover honestly (spec_guide directive 8).

WITNESS MECHANICS (measured on this backend; this is where the port's real work
is). The spec is a ``method`` CONTRACT, so a witness reaches the postcondition
through Velvet's extraction machinery. But ``splitParts`` is defined by
WELL-FOUNDED recursion (``termination_by rest.length``), so a bare
``decide`` against it is STUCK: measured directly,
``splitParts false [] ['-'] = [['-']]`` — a TRUE claim — fails with "did not
reduce to `isTrue` or `isFalse` … reduction got stuck at the `Decidable`
instance", and so do ``decide +kernel``, ``simp [splitParts]`` (maximum recursion
depth), and ``unfold splitParts; decide``. The frozen ``while`` impl compounds
this: under ``loom.semantics.choice "demonic"`` its extracted program elaborates
through a fixpoint the kernel cannot unfold. So neither the oracle's value nor
the frozen impl's exit code can be obtained by evaluation.

Each witness therefore does two things.

  (1) It states the refutation over the EXTRACTED PROGRAM directly —
      ``kbdSplitExec <input> ≠ DivM.res (splitParts false [] <input>)`` — after
      FIRST proving the oracle's concrete value at that input by chaining the
      frozen ``splitParts_step`` / ``splitParts_nil`` unfold lemmas (the two
      ``@[grind]`` lemmas already in the frozen pure region; no new lemma is
      introduced), one step per scan step, each step's ``sepLen`` / ``stepLen`` /
      ``take`` / ``drop`` / ``lastFlank`` value supplied as a ``decide``d rewrite.
      That reduces the oracle to a literal, leaving only the rival's own
      kernel-reducible program to evaluate.

  (2) Because the frozen impl still cannot decide, every reject case names
      ``witness_reference``: ``_LOOPFREE``, a loop-free impl of the SAME frozen
      spec that the gate independently checks shares the spec AND VERIFIES. An
      impl the verifier accepts cannot violate its own spec, so a genuine witness
      must still fail there. That is checked rather than trusted — a reference
      that merely failed everything would refute every witness, honest or forged.

Verified by hand for every rival before shipping (``scripts/lean_verify.sh``, two
builds each): the witness ELABORATES against the rival (exit 0) and FAILS against
``_LOOPFREE`` by GENUINE refutation — ``Tactic `decide` proved that the
proposition False is false``, a real verdict, NOT a stuck reduction. Measured
control that the rival half is load-bearing rather than decoration: the same
witness statement built against a rival at an input where that rival AGREES with
the spec fails too, and reports the disagreement it could not find (e.g. the
line-feed rival at ``a\\n-b``: ``decide`` proved ``¬… = [['a'], ['\\n'], ['-','b']]``
is false — the rival's value there is correct, so the witness is refuted). No
``sorry`` / ``admit`` / ``native_decide`` anywhere.

BINDER / CLAUSE COVERAGE (read before judging coverage). The postcondition has a
SINGLE input binder, ``text``, and its discriminating content spreads over SIX
independent axes: the LEADING flank (a key character precedes the separator), the
TRAILING flank (a key character follows it, after trimming), the separator
ALPHABET (which characters can separate at all — connectors AND whitespace), the
MAXIMAL-MUNCH grouping of a whitespace run (one segment, not one per character),
the FLANK CLASS (the line feed is not a key character, so it neither opens nor
closes a key around a separator), and the segment ORDER / COUNT. The reject
witnesses probe NINE DISTINCT inputs, none shared, spanning all six axes.

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive control — APPLIES. A structurally different but
    behaviourally identical assembly (produce the segmentation directly from the
    model, or bind it to a local first) must still verify, else SPEC-TOO-STRONG
    on the shape of the assembly (the mutable loop is not load-bearing).
    (``pos-*``.)
  * ADMISSIBILITY — RE-AIMED. There is NO ``require`` clause, so the nagini
    "the precondition admits a normal keystroke text" self-call probe is vacuous
    (nothing to admit). Re-aimed at the residual risk that the post-image is
    degenerate / unsatisfiable at the interesting points: two in-region
    ``assert``s pin the post-image's concrete value at the headline
    standalone-connector input (``['-'] ↦ [['-']]`` — one key, no split) and at a
    whitespace-separated input (``['a',' ',' ','b'] ↦ [['a'], [' ',' '], ['b']]``
    — ONE separator segment holding the whole run), with the frozen loop kept so
    the method's own obligation still discharges. (``admiss-*``.)
  * UNIQUENESS / SPEC-TOO-WEAK rivals — APPLY, and carry the port's
    discriminating content. NINE rivals attack the ``ensures`` across the six
    axes above, each with a machine-checked refutation witness at a distinct
    concrete input.
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling carries this
    MANDATORY because its read-only input is held at a fractional heap permission
    (``Acc(.,1/2)``) an impl can illegally overwrite. Lean and Velvet are
    referentially transparent: ``text`` is an immutable value (this bundle
    declares no ``mut`` binder on an input), there is no heap and no aliasing, so
    there is no read-only input to mutate and no substitute probe to build. Not
    fabricated (porting map: this class is vacuous here).
  * UNGROUNDED-ORACLE ECHO — N/A as an ATTACK. ``splitParts`` is a concrete
    ``def`` in the ``pure`` region; the ``axioms`` region is empty (no opaque
    answer key). An impl that "echoes" it is simply a CORRECT impl, and is
    shipped as ``pos-direct-model`` — which is also the shared
    ``witness_reference`` ``_LOOPFREE``, precisely so the battery records that
    loop-freeness is not what any rival is rejected for.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom`` and there is no
A-reference; the segmentation is modeled deeply). The gate ignores ``AXIOM_TESTS``
regardless. See the footer for the full nagini→velvet accounting.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8621"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the frozen while-loop body, verbatim (every line
# ---- strictly inside kbdSplit's -- impl-start / -- impl-end). Lies wholly
# ---- inside the single impl region and is unique in Solution.lean (the prepatch
# ---- skeleton lives in a separate file); both facts asserted at load by _swap.
# ---- Every variant _swap()s only this block (and, where the reshape needs it,
# ---- the proof body below), so the edit never touches the spec regions
# ---- (axioms/pure/pre/post + the method signature and the `ensures`).
_IMPL = (
    "    let mut acc : List (List Char) := []\n"
    "    let mut cur : List Char := []\n"
    "    let mut leftOk := false\n"
    "    let mut rest := text\n"
    "    while rest ≠ []\n"
    "      invariant splitParts false [] text = acc ++ splitParts leftOk cur rest\n"
    "      done_with rest = []\n"
    "      decreasing rest.length\n"
    "    do\n"
    "      let L := stepLen leftOk rest\n"
    "      if sepLen leftOk rest = 0 then\n"
    "        cur := cur ++ rest.take L\n"
    "        leftOk := lastFlank (rest.take L)\n"
    "        rest := rest.drop L\n"
    "      else\n"
    "        acc := acc ++ [cur, rest.take L]\n"
    "        cur := []\n"
    "        leftOk := lastFlank (rest.take L)\n"
    "        rest := rest.drop L\n"
    "    return acc ++ [cur]"
)
assert _BASE.count(_IMPL) == 1, "kbdSplit impl region drifted"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a case that reshapes the impl (or adds an in-region
# ---- assert) may retune its script without touching the spec or dropping the
# ---- obligation.
_PROOF = (
    "prove_correct kbdSplit by\n"
    "  loom_solve\n"
    "  all_goals try exact stepLen_drop_lt (by assumption)"
)
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_proof(new_impl, new_proof):
    """Reshape the impl region AND retune the tactic body."""
    src = _swap(_BASE, _IMPL, new_impl)
    return _swap(src, _PROOF, new_proof)


# ---------------------------------------------------------------------------
# The shared WITNESS REFERENCE. A loop-free impl of the frozen spec: it returns
# the spec's own model instead of recomputing it with a `while`. It is a CORRECT
# impl (it verifies — shipped below as `pos-direct-model`, so the battery itself
# records that loop-freeness is not what any rival is rejected for), and unlike
# the frozen impl its extracted program reduces once the oracle has been rewritten
# to a literal, so a witness against it returns a REAL verdict (`decide` proved
# `False` is false) instead of getting stuck on the loop's fixpoint. The gate
# checks both properties (same spec + verifies) before refuting any witness
# against it.
# ---------------------------------------------------------------------------
_LOOPFREE = _impl_proof("    return splitParts false [] text",
                        "prove_correct kbdSplit by\n  loom_solve")


# ---------------------------------------------------------------------------
# Witness builders. Mirrors of the frozen pure region's scanner, used ONLY to
# compute each witness's expected segmentation at authoring time (they never
# appear in a variant). Kept in lock-step with Solution.lean's isSep / isBlank /
# isFlank / headFlanks / lastFlank / blankRun / gapFit / sepLen / stepLen /
# splitParts; a drift shows up immediately as a witness that stops elaborating.
# ---------------------------------------------------------------------------

# The 29 code points of `isBlank`, spelled out so the mirror cannot silently
# diverge from the Lean predicate's ranges.
_BLANK = (set(range(0x9, 0xe)) | set(range(0x1c, 0x21))
          | {0x85, 0xa0, 0x1680, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000}
          | set(range(0x2000, 0x200b)))


def _is_blank(c):
    return ord(c) in _BLANK


def _is_sep(c):
    return c in "-+^"


def _is_flank(c):
    return c != "\n"


def _blank_run(s):
    n = 0
    for c in s:
        if not _is_blank(c):
            break
        n += 1
    return n


def _gap_fit(rest, n):
    while n > 0:
        tail = rest[n:]
        if tail and _is_flank(tail[0]):
            return n
        n -= 1
    return 0


def _sep_len(left_ok, rest):
    if not rest or not left_ok:
        return 0
    c = rest[0]
    if _is_sep(c):
        return _gap_fit(rest, 1)
    if _is_blank(c):
        return _gap_fit(rest, _blank_run(rest))
    return 0


def _step_len(left_ok, rest):
    s = _sep_len(left_ok, rest)
    return 1 if s == 0 else s


def _last_flank(s):
    return _is_flank(s[-1]) if s else False


def _split_parts(s):
    out, cur, left = [], "", False
    while s:
        L = _step_len(left, s)
        piece = s[:L]
        if _sep_len(left, s) == 0:
            cur = cur + piece
        else:
            out.append(cur)
            out.append(piece)
            cur = ""
        left = _last_flank(piece)
        s = s[L:]
    out.append(cur)
    return out


def _ch(c):
    if c == "\\":
        return "'\\\\'"
    if c == "'":
        return "'\\''"
    if c == "\n":
        return "'\\n'"
    if c == "\t":
        return "'\\t'"
    if c == "\r":
        return "'\\r'"
    if ord(c) < 0x20 or ord(c) > 0x7e:
        return f"(Char.ofNat {ord(c)})"
    return f"'{c}'"


def _clist(s):
    return "[" + ", ".join(_ch(c) for c in s) + "]" if s else "([] : List Char)"


def _cllist(ps):
    return "[" + ", ".join(_clist(p) for p in ps) + "]"


def _chain(s, name):
    """`have <name> : splitParts false [] <lit> = <literal>`, proven by chaining
    the frozen `splitParts_step` front-unfold with decidable per-step rewrites,
    then closing on `splitParts_nil`. Uses only lemmas already present in the
    frozen pure region — the oracle's well-founded recursion is what makes a bare
    `decide` stuck, and this is the reduction the kernel cannot perform on its
    own."""
    out = [f"  have {name} : splitParts false [] {_clist(s)}",
           f"      = {_cllist(_split_parts(s))} := by"]
    left, cur, rest = False, "", s
    while rest:
        L, sl = _step_len(left, rest), _sep_len(left, rest)
        piece, nxt, nl = rest[:L], rest[L:], _last_flank(rest[:L])
        lb = "true" if left else "false"
        out += [
            f"    rw [splitParts_step {lb} {_clist(cur)} {_clist(rest)} (by decide)]",
            f"    rw [show sepLen {lb} {_clist(rest)} = {sl} from by decide]",
            f"    rw [show stepLen {lb} {_clist(rest)} = {L} from by decide]",
            f"    rw [show List.take {L} {_clist(rest)} = {_clist(piece)} from by decide]",
            f"    rw [show List.drop {L} {_clist(rest)} = {_clist(nxt)} from by decide]",
            f"    rw [show lastFlank {_clist(piece)} "
            f"= {'true' if nl else 'false'} from by decide]",
        ]
        if sl == 0:
            new_cur = cur + piece
            out.append(f"    rw [show ({_clist(cur)} ++ {_clist(piece)} : List Char) "
                       f"= {_clist(new_cur)} from by decide]")
            cur = new_cur
        else:
            cur = ""
        left, rest = nl, nxt
    out += ["    rw [splitParts_nil]", "    decide"]
    return "\n".join(out)


def _witness(s):
    """A refutation witness at the concrete input `s`.

    States that the rival's EXTRACTED PROGRAM disagrees with the spec's oracle at
    `s`. Going through `...Exec` rather than the derived tester is what keeps the
    claim reducible: the tester wraps the comparison in a `Decidable` instance
    that gets stuck on the oracle's well-founded recursion, whereas here the
    oracle is FIRST rewritten to a literal by `_chain` and only the rival's own
    kernel-reducible program is left to evaluate. Nothing is bound, so no
    consistency probe is needed.
    """
    lit = _clist(s)
    return ("extract_program_for kbdSplit\n\n"
            f"example : kbdSplitExec {lit} ≠ DivM.res (splitParts false [] {lit}) := by\n"
            + _chain(s, "hgold") + "\n"
            "  unfold kbdSplitExec kbdSplit\n"
            "  rw [hgold]\n"
            "  simp [NonDetT.run, pure]\n"
            "  all_goals decide\n")


# A loop-free structural fold parameterised by the split guard, for the rivals
# that attack the CONNECTOR half of the separator test one character at a time.
# The `let rec seg` inside the do block reduces under `decide` (structural
# recursion), unlike the frozen well-founded `while`.
def _seg_rival(guard):
    return (f"    let rec seg (started : Bool) (cur : List Char) : List Char → List (List Char)\n"
            f"      | [] => [cur]\n"
            f"      | c :: cs =>\n"
            f"          if {guard}\n"
            f"          then cur :: [c] :: seg true [] cs\n"
            f"          else seg true (cur ++ [c]) cs\n"
            f"    return seg false [] text")


# A loop-free FUEL-bounded scanner parameterised by the whole `sepLen`
# computation, for the rivals whose defect is in the RUN-LENGTH or FLANK-CLASS
# half of the separator test (a one-character step cannot express those). Fuel is
# `text.length`, which is always enough — one step consumes at least one
# character — so the bound is not itself the defect, and the recursion is
# structural on `fuel` so the extracted program reduces under `decide`.
def _scan_rival(sep_len_expr):
    return ("    let rec segF (fuel : Nat) (leftOk : Bool) (cur : List Char)\n"
            "        (rest : List Char) : List (List Char) :=\n"
            "      match fuel, rest with\n"
            "      | 0, _ => [cur]\n"
            "      | _ + 1, [] => [cur]\n"
            "      | f + 1, r =>\n"
            "        let s := " + sep_len_expr + "\n"
            "        let L := if s = 0 then 1 else s\n"
            "        if s = 0\n"
            "        then segF f (lastFlank (r.take L)) (cur ++ r.take L) (r.drop L)\n"
            "        else cur :: r.take L :: segF f (lastFlank (r.take L)) [] (r.drop L)\n"
            "    return segF text.length false [] text")


# `sepLen` written out over `r`, with the TRIM step (`gapFit`) replaced by a
# plain "something follows" test — i.e. the flank class widened to include the
# line feed. Everything else is the frozen computation.
_SEP_ANY_FOLLOWS = (
    "(match r with\n"
    "         | [] => 0\n"
    "         | c :: cs =>\n"
    "             if leftOk = true then\n"
    "               (if isSep c then (if cs ≠ [] then 1 else 0)\n"
    "                else if isBlank c then\n"
    "                  (let n := blankRun (c :: cs)\n"
    "                   if (c :: cs).drop n ≠ [] then n else 0)\n"
    "                else 0)\n"
    "             else 0)")

# `sepLen` with the whitespace alternative DELETED: only connectors separate.
_SEP_NO_BLANK = (
    "(match r with\n"
    "         | [] => 0\n"
    "         | c :: cs =>\n"
    "             if leftOk = true then\n"
    "               (if isSep c then gapFit (c :: cs) 1 else 0)\n"
    "             else 0)")

# `sepLen` with the whitespace RUN truncated to a single character: whitespace
# separates, but a run of it becomes one separator PER CHARACTER instead of one
# maximal-munch segment.
_SEP_BLANK_ONE = (
    "(match r with\n"
    "         | [] => 0\n"
    "         | c :: cs =>\n"
    "             if leftOk = true then\n"
    "               (if isSep c then gapFit (c :: cs) 1\n"
    "                else if isBlank c then gapFit (c :: cs) 1\n"
    "                else 0)\n"
    "             else 0)")

# `sepLen` with `isBlank` narrowed to the ASCII space: the other 28 whitespace
# code points stop separating.
_SEP_BLANK_ASCII = (
    "(match r with\n"
    "         | [] => 0\n"
    "         | c :: cs =>\n"
    "             if leftOk = true then\n"
    "               (if isSep c then gapFit (c :: cs) 1\n"
    "                else if c == ' ' then\n"
    "                  gapFit (c :: cs) (blankRun (c :: cs))\n"
    "                else 0)\n"
    "             else 0)")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. Each drops the mutable while-loop for a direct
    # value expression, leaving the observable value (and thus the master
    # equality the frozen `ensures` pins) intact. If a faithful correct reshape
    # could not verify, the spec would be SPEC-TOO-STRONG on the assembly shape.
    # (Both build clean; `loom_solve` closes the reshaped obligation.)
    # =====================================================================
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Produce the segmentation directly from the deep model instead of
        # accumulating it with the forward-scanning loop. Same value; the
        # loop-free obligation closes with `loom_solve` alone. This is also the
        # shared `witness_reference` (_LOOPFREE), so the battery records
        # explicitly that being loop-free is not what any rival is rejected for.
        "module": _LOOPFREE,
        "rationale": "a correct reshape that returns the segmentation directly "
                     "(no mutable loop) computes the same output, so "
                     "`out = splitParts false [] text` discharges definitionally; "
                     "must verify (else SPEC-TOO-STRONG on the loop being "
                     "load-bearing). Doubles as the witness reference: every "
                     "reject witness must FAIL here, which is only sound because "
                     "this impl is independently required to verify.",
    },
    {
        "id": "pos-local-bind",
        "kind": "soundness",
        "expect": "verify",
        # Bind the segmentation to a named local, then return it — pure reshape
        # of the direct form, identical value flow.
        "module": _impl_proof(
            "    let out := splitParts false [] text\n"
            "    return out",
            "prove_correct kbdSplit by\n  loom_solve"),
        "rationale": "binding the segmentation to a local before returning it "
                     "leaves the output unchanged, so the master equality still "
                     "holds; a faithful correct reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — re-aimed. There is NO `require` clause (total domain), so
    # the nagini "a normal keystroke text satisfies the precondition" self-call
    # probe is vacuous. Re-aimed at the residual risk: that the post-image is
    # UNSATISFIABLE / degenerate at the interesting points (a spec no impl can
    # meet reads exactly like one every impl meets). Two in-region asserts pin
    # the post-image's concrete value — at the headline standalone-connector
    # input, and at a whitespace-RUN input where the run must come out as ONE
    # segment — and the frozen loop is kept verbatim so the method's own
    # obligation still discharges. Both asserts are LIVE claims: the oracle's
    # well-founded recursion means `decide` cannot close them, so each is proven
    # by the same unfold chain the witnesses use. Liveness verified during
    # authoring by a real build: replacing the whitespace assert's value with the
    # per-character segmentation `[['a'], [' '], [], [' '], ['b']]` makes the
    # build FAIL (exit 1) with `unsolved goals … case «assert_2: …»`, so the
    # assert is checked and not decoration.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      (splitParts false [] ['-'] = [['-']]))\n"
            "    assert (with_name_prefix `assert\n"
            "      (splitParts false [] ['a', ' ', ' ', 'b']\n"
            "        = [['a'], [' ', ' '], ['b']]))\n" + _IMPL,
            # The two assert goals are proven by the SAME unfold chain the
            # witnesses use (a bare `decide` is stuck on the oracle's
            # well-founded recursion), established as hypotheses BEFORE
            # `loom_solve` splits the obligation and then discharged
            # positionally.
            "prove_correct kbdSplit by\n"
            + _chain("-", "hA") + "\n"
            + _chain("a  b", "hB") + "\n"
            "  loom_solve\n"
            "  all_goals try exact hA\n"
            "  all_goals try exact hB\n"
            "  all_goals try exact stepLen_drop_lt (by assumption)"),
        "rationale": "the post-image is satisfiable AND non-degenerate at both "
                     "interesting points: a standalone connector must segment to "
                     "a single one-key segment `[['-']]` (NOT a separator flanked "
                     "by two empty keys), and a two-character whitespace run "
                     "between two keys must come out as ONE separator segment "
                     "`[' ',' ']` (NOT two one-character separators with an empty "
                     "key between them). Both asserts must discharge (else the "
                     "obligation is unsatisfiable / the spec is degenerate here); "
                     "the loop is kept verbatim so the method's own `ensures` "
                     "still discharges.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # distinct concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. Each rival is written so
    # its extracted program is kernel-reducible (a structural fold, or a
    # fuel-bounded scanner) — see WITNESS MECHANICS.
    #
    # AXIS 1-2: the two FLANKS of the separator test.
    # =====================================================================
    {
        "id": "weak-split-every-connector",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behaviour: a connector splits at EVERY occurrence,
        # regardless of whether keys flank it (BOTH flank checks dropped). On a
        # standalone connector this emits a separator with empty keys around it.
        "module": _impl(_seg_rival("isSep c = true")),
        "refinement": "this is the literal pre-fix defect: a standalone connector "
                      "is treated as a separator with two blank keystrokes around "
                      "it (`['-'] ↦ [empty, connector, empty]`), which is exactly "
                      "the reported bug — the failing test that expects a single "
                      "key element for `:kbd:` with a bare `-` would instead "
                      "observe two blank `<kbd>` elements and FAIL. It would NOT "
                      "resolve; it is the behaviour the fix removes.",
        "rationale": "REJECT from `out = splitParts false [] text`: dropping BOTH "
                     "flank checks splits on a leading/trailing/standalone "
                     "connector, which the flank-sensitive spec never does, so the "
                     "output differs (segment count and content) whenever a "
                     "connector lacks a flank. Verifying would be SPEC-TOO-WEAK on "
                     "the flank sensitivity. Refuted at `['-']` (a standalone "
                     "connector: BOTH flanks absent, the headline sub-domain).",
        "witness": _witness("-"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-split-trailing-connector",
        "kind": "uniqueness",
        "expect": "reject",
        # The TRAILING flank alone dropped: a connector splits whenever a
        # character precedes it, even with NO character following it. A near-miss
        # — it agrees with gold on every interior connector; only a TRAILING
        # connector exposes it.
        "module": _impl(_seg_rival("isSep c = true ∧ started = true")),
        "refinement": "a counterpart that requires only a preceding character (the "
                      "lookbehind) but omits the following-character check (the "
                      "lookahead) splits on a TRAILING connector — e.g. the final "
                      "`^` of `Alt+^` becomes a separator with a blank keystroke "
                      "after it. The `Alt+^` F2P expects the trailing `^` rendered "
                      "as a single key; this impl emits a blank `<kbd>` after it "
                      "and FAILS. It would NOT resolve.",
        "rationale": "REJECT from `out = splitParts false [] text`: keeping only "
                     "the leading flank splits whenever a connector follows some "
                     "character, which diverges from the spec exactly when a "
                     "connector ends the string (trailing flank absent). Verifying "
                     "would be SPEC-TOO-WEAK on the trailing flank. A near-miss "
                     "the split-every rival does not subsume (correct on all "
                     "interior connectors). Refuted at `['A','+','^']` (an "
                     "F2P-shaped trailing connector: leading flank present, "
                     "trailing absent).",
        "witness": _witness("A+^"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-split-leading-connector",
        "kind": "uniqueness",
        "expect": "reject",
        # The LEADING flank alone dropped: a connector splits whenever a
        # character FOLLOWS it, even with nothing before it. The exact mirror of
        # `weak-split-trailing-connector`. NOT subsumed by
        # weak-split-every-connector: the two disagree with each other on
        # `['+','-']`, and on `['-']`, `['a','-']`, `['-','-']` this rival AGREES
        # with the spec where the split-every rival does not.
        "module": _impl(_seg_rival("isSep c = true ∧ cs ≠ []")),
        "refinement": "a counterpart that checks only the lookahead (a character "
                      "follows) but omits the lookbehind (a character precedes) "
                      "splits on a LEADING connector — a keystroke written with a "
                      "connector first, e.g. `-a`, becomes a blank keystroke, a "
                      "separator, then `a`. The test that expects a single key "
                      "element for a leading-connector `:kbd:` would instead "
                      "observe a blank `<kbd>` before it and FAIL. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = splitParts false [] text`: keeping only "
                     "the trailing flank splits whenever a connector is followed "
                     "by something, which diverges from the spec exactly when a "
                     "connector STARTS the string (leading flank absent). "
                     "Verifying would be SPEC-TOO-WEAK on the leading flank "
                     "specifically. Refuted at `['-','a']` (leading flank absent, "
                     "trailing present; the spec demands the single key "
                     "`[['-','a']]`, the rival produces `[[], ['-'], ['a']]`).",
        "witness": _witness("-a"),
        "witness_reference": _LOOPFREE,
    },

    # =====================================================================
    # AXIS 3: the separator ALPHABET — WHICH characters can separate at all.
    # =====================================================================
    {
        "id": "weak-narrow-connector-set",
        "kind": "uniqueness",
        "expect": "reject",
        # Keeps the two-flank guard EXACTLY right but narrows the CONNECTOR set:
        # `^` is no longer a connector.
        "module": _impl(_seg_rival(
            "(c == '-' || c == '+') = true ∧ started = true ∧ cs ≠ []")),
        "refinement": "a counterpart that recognises only two of the three "
                      "connectors never splits a compound keystroke joined by the "
                      "third, so `a^b` renders as one key `a^b` instead of `a`, "
                      "`^`, `b`. The `Alt+^`-family tests enumerate `^` as a "
                      "connector in its own right; a segmentation that swallows it "
                      "into the surrounding key FAILS. It would NOT resolve.",
        "rationale": "REJECT from `out = splitParts false [] text`: `isSep` pins "
                     "the connector alphabet to all THREE characters, so dropping "
                     "one makes the output differ on every input whose only "
                     "interior separator is that character. Verifying would be "
                     "SPEC-TOO-WEAK on the connector SET — an axis the flank, "
                     "count and order rivals all leave untouched. Refuted at "
                     "`['a','^','b']` (an interior `^`: both flanks present, so "
                     "the guard is not at issue).",
        "witness": _witness("a^b"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-no-whitespace-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # The whitespace alternative DELETED outright: only connectors separate,
        # whitespace is an ordinary key character. The two-flank test, the
        # connector set, the ordering and the count are all kept EXACTLY right,
        # so this rival agrees with the spec on every whitespace-free input —
        # which is what makes it the sharpest probe of the separator alphabet's
        # whitespace half.
        "module": _impl(_scan_rival(_SEP_NO_BLANK)),
        "refinement": "a counterpart whose separator set omits whitespace renders "
                      "a keystroke sequence written with a space between two keys "
                      "as ONE key containing the space, instead of two keys with "
                      "the space as the separator between them — e.g. `M-x  M-s` "
                      "collapses to the three segments `M`, `-`, `x  M-s` rather "
                      "than the seven the renderer needs. The passing test that "
                      "renders a multi-keystroke `:kbd:` with a whitespace gap "
                      "compares the emitted key and separator elements verbatim, "
                      "so it would observe a key holding the gap and FAIL. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = splitParts false [] text`: `sepLen` "
                     "recognises a whitespace RUN as a separator form alongside a "
                     "connector, so an impl that never separates on whitespace "
                     "differs from the spec on every input with an interior "
                     "whitespace gap — the segment count and the segment contents "
                     "both change. Verifying would be SPEC-TOO-WEAK on the "
                     "whitespace half of the separator alphabet, the axis every "
                     "connector-only rival leaves entirely unprobed. Refuted at "
                     "`['a',' ','b']` (an interior single space, both flanks "
                     "present: the spec demands `[['a'], [' '], ['b']]`, the "
                     "rival produces `[['a',' ','b']]`).",
        "witness": _witness("a b"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-ascii-space-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Whitespace DOES separate, but only the ASCII space: the other 28 code
        # points of the class stop separating. A near-miss that agrees with the
        # spec on every plain-space input, so `weak-no-whitespace-separator` does
        # not subsume it.
        "module": _impl(_scan_rival(_SEP_BLANK_ASCII)),
        "refinement": "a counterpart whose whitespace class is only the ASCII "
                      "space swallows any other whitespace character into the "
                      "surrounding key — a keystroke sequence joined by a tab or a "
                      "no-break space becomes one long key instead of two keys "
                      "around a separator. The renderer's per-segment output would "
                      "differ from what the tests compare against on such an "
                      "input. It would NOT resolve.",
        "rationale": "REJECT from `out = splitParts false [] text`: `isBlank` pins "
                     "the whitespace class to all 29 code points, so narrowing it "
                     "to the space alone makes the output differ on every input "
                     "whose only interior separator is one of the other 28. "
                     "Verifying would be SPEC-TOO-WEAK on the EXTENT of the "
                     "whitespace class — distinct from whether whitespace "
                     "separates at all. Refuted at `['a','\\t','b']` (an interior "
                     "tab: the spec demands `[['a'], ['\\t'], ['b']]`, the rival "
                     "produces `[['a','\\t','b']]`).",
        "witness": _witness("a\tb"),
        "witness_reference": _LOOPFREE,
    },

    # =====================================================================
    # AXIS 4: MAXIMAL MUNCH — a whitespace run is ONE separator segment.
    # =====================================================================
    {
        "id": "weak-whitespace-run-per-char",
        "kind": "uniqueness",
        "expect": "reject",
        # Whitespace separates and the class is right, but the RUN is truncated
        # to one character: a two-space gap becomes two separators with an empty
        # key between them instead of one two-character separator. Agrees with
        # the spec on every single-character gap, so neither whitespace-alphabet
        # rival subsumes it.
        "module": _impl(_scan_rival(_SEP_BLANK_ONE)),
        "refinement": "a counterpart that consumes one whitespace character per "
                      "separator instead of the maximal run splits a two-space gap "
                      "into two separators with a BLANK key between them — "
                      "`M-x  M-s` gains an empty key element in the middle. The "
                      "passing test for a multi-keystroke `:kbd:` with a "
                      "two-space gap enumerates the key and separator elements in "
                      "order and would observe the extra blank `<kbd>` and FAIL. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `out = splitParts false [] text`: `sepLen` takes "
                     "the whole `blankRun` as ONE separator, so a per-character "
                     "rival produces MORE segments (and an empty key between "
                     "consecutive whitespace) on every run of length ≥ 2. "
                     "Verifying would be SPEC-TOO-WEAK on maximal munch — an axis "
                     "independent of whether whitespace separates at all and of "
                     "which characters are whitespace. Refuted at "
                     "`['a',' ',' ','b']` (a two-space gap: the spec demands "
                     "`[['a'], [' ',' '], ['b']]` — three segments — the rival "
                     "produces five).",
        "witness": _witness("a  b"),
        "witness_reference": _LOOPFREE,
    },

    # =====================================================================
    # AXIS 5: the FLANK CLASS — the line feed is not a key character.
    # =====================================================================
    {
        "id": "weak-linefeed-flanks",
        "kind": "uniqueness",
        "expect": "reject",
        # Everything right EXCEPT the flank class: the trim step is replaced by a
        # plain "something follows" test, so a line feed counts as a key
        # character to the RIGHT of a separator. Agrees with the spec on every
        # input containing no line feed, which is what makes it the sharpest
        # probe of `isFlank` / `gapFit`.
        "module": _impl(_scan_rival(_SEP_ANY_FOLLOWS)),
        "refinement": "a counterpart that treats a line feed as an ordinary "
                      "character on the right of a separator splits a keystroke "
                      "whose connector is followed only by a line break, emitting "
                      "a separator with a blank key after it where the spec keeps "
                      "the connector inside the key. The rendered output gains a "
                      "spurious separator and an empty key element on such an "
                      "input, so an ordered comparison of the emitted elements "
                      "FAILS. It would NOT resolve.",
        "rationale": "REJECT from `out = splitParts false [] text`: `gapFit` "
                     "requires a FLANKING character after the separator, and "
                     "`isFlank` excludes the line feed, so trimming against a "
                     "plain non-emptiness test diverges exactly when a separator "
                     "is followed only by a line feed. Verifying would be "
                     "SPEC-TOO-WEAK on the flank CLASS — the one axis no flank, "
                     "alphabet, munch, count or order rival touches (each of those "
                     "keeps `isFlank` intact). Refuted at `['a','-','\\n']` (a "
                     "connector followed only by a line feed: the spec demands the "
                     "single key `[['a','-','\\n']]`, the rival produces "
                     "`[['a'], ['-'], ['\\n']]`). Control measured during "
                     "authoring: the SAME witness statement at `['a','\\n','-','b']` "
                     "— where this rival AGREES with the spec — is refuted against "
                     "the rival, so the rival half of the check is load-bearing.",
        "witness": _witness("a-\n"),
        "witness_reference": _LOOPFREE,
    },

    # =====================================================================
    # AXIS 6: segment COUNT and ORDER.
    # =====================================================================
    {
        "id": "weak-drop-last-segment",
        "kind": "uniqueness",
        "expect": "reject",
        # Segment correctly, then DROP the last segment. Correct on every segment
        # it does emit, but the result is one segment short.
        "module": _impl("    return (splitParts false [] text).dropLast"),
        "refinement": "a counterpart with an off-by-one that omits the final "
                      "segment produces a segmentation one piece short — e.g. "
                      "`a+b` renders as `<kbd>a</kbd>+` with the trailing `b` key "
                      "missing. The failing test that enumerates every key/"
                      "separator would be missing the last one and FAIL. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = splitParts false [] text`: dropping the "
                     "last segment yields a list one shorter than the pinned "
                     "interleaving whenever the segmentation is non-empty, so the "
                     "outputs differ in length. Verifying would be SPEC-TOO-WEAK "
                     "on the segment count. Refuted at `['a','+','b']` (an "
                     "interior connector: both flanks present).",
        "witness": _witness("a+b"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Right segments, wrong ORDER: reverse the interleaving. Correct multiset
        # of segments and correct count, but the keys and separators come out
        # back-to-front — a near-miss the length/flank rivals do not subsume.
        "module": _impl("    return (splitParts false [] text).reverse"),
        "refinement": "a counterpart that lists the keys and separators in reverse "
                      "order renders the compound keystroke backwards — e.g. `a-b` "
                      "as `<kbd>b</kbd>-<kbd>a</kbd>`. The failing test matches the "
                      "keys and separators in source order verbatim; a reversed "
                      "rendering FAILS the ordered comparison. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = splitParts false [] text`: the spec pins "
                     "the interleaving in source order; the reverse differs "
                     "whenever the segmentation is not a palindrome. Verifying "
                     "would be SPEC-TOO-WEAK on segment ORDER — a near-miss "
                     "(correct segment multiset and count) the drop/flank rivals "
                     "do not subsume. Refuted at `['a','-','b']`.",
        "witness": _witness("a-b"),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 6 SPEC cases (1
# admissibility self-call, 2 soundness positives, 1 MANDATORY frame-mutation
# rival, 3 uniqueness rivals — one on the atomic decision, two on the split) plus
# a 2-case AXIOM lane. The sibling contracts a RICHER surface: TWO functions,
# `split_keystrokes` (a heap `PSeq[PSeq[int]]` held at a fractional permission)
# and `keystroke_is_atomic` (a derived boolean over the part count), both with a
# read-only `Acc(list_pred(text),1/2)` input. This velvet bundle models only the
# purely-functional CORE that the issue is actually about — the SEGMENTATION,
# `kbdSplit` — as a single method over an immutable `List Char` with a concrete
# `splitParts` def and NO axioms. `keystroke_is_atomic` (the len==1 decision) is
# NOT modeled here (carrier narrowing, per the porting map), so every nagini case
# attached to it has no counterpart. The accounting below records every sibling
# case.
#
#   sibling case                       -> here
#   ---------------------------------------------------------------------
#   admiss-self-call                   -> admiss-nondegenerate          RE-AIMED
#   pos-atomic-local-reshape           -> (none)                        UNMODELED
#   pos-split-assert-reorder           -> pos-direct-model + pos-local-bind
#                                                                    RE-EXPRESSED
#   frame-mutate-atomic-input (MAND.)  -> (none)                        VACUOUS
#   weak-always-atomic                 -> (none)                        UNMODELED
#   weak-atomic-eq-2                   -> (none)                        UNMODELED
#   weak-split-drop-last               -> weak-drop-last-segment        PORTED
#   AXIOM_TESTS (2)                    -> (none)                        DROPPED (G-AX)
#
# RE-AIMED (admissibility): the sibling's self-call establishes the callee's
#   domain precondition from the caller's identical precondition. This bundle has
#   NO `require` clause (total domain over `List Char`), so there is nothing to
#   admit — the self-call probe is vacuous. Re-aimed at post-image degeneracy
#   with two in-region asserts pinning the segmentation's concrete value at the
#   standalone-connector input (`['-'] ↦ [['-']]`) and at a whitespace-run input
#   (`a  b ↦ [['a'], [' ',' '], ['b']]`, ONE separator segment); the frozen loop
#   is kept so the method obligation still discharges. Verified to build.
# RE-EXPRESSED (positives): the sibling's `pos-atomic-local-reshape` reshapes the
#   UNMODELED atomic decision, and `pos-split-assert-reorder` reorders two
#   pre-loop framing asserts specific to nagini's proof discipline (no counterpart
#   on this backend's `loom_solve` proof). The soundness ARGUMENT ("a structurally
#   different but faithful impl must verify, else SPEC-TOO-STRONG") is carried by
#   the two reshapes that ARE natural on this carrier: return the segmentation
#   directly, and bind it to a local first — both drop the mutable loop, keeping
#   the observable value the `ensures` pins. Both verified to build.
# UNMODELED (`keystroke_is_atomic` rivals): pos-atomic-local-reshape,
#   weak-always-atomic (len>=1, always true) and weak-atomic-eq-2 (len==2) all
#   attack the LEN==1 atomic decision — a derived boolean over the part count that
#   this velvet bundle does not model (only the segmentation is contracted). They
#   have NO counterpart here and are legitimately omitted (carrier narrowing). The
#   segmentation itself is attacked directly by the nine uniqueness rivals above.
# PORTED (split rival): the sibling's `weak-split-drop-last` (the last-code-point
#   branch is a no-op, dropping the final key) ports as `weak-drop-last-segment`
#   (drop the final segment). Same failure mode (the last piece of the
#   segmentation is lost), refuted by a length/content disagreement.
# VACUOUS (frame-mutation): the sibling carries this MANDATORY because its input
#   `text` is held at `Acc(list_pred(text),1/2)` an impl can illegally write. This
#   backend is referentially transparent and declares no `mut` binder on an input
#   — `text : List Char` is an immutable value with no heap footprint — so there
#   is no read-only field to overwrite and no substitute probe. Not fabricated
#   (porting map: this class is vacuous on Lean/Velvet).
#
# UNIQUENESS COVERAGE, by axis of the `ensures`. The one binder is `text`, and the
#   nine rivals attack six INDEPENDENT properties of the pinned segmentation, none
#   of them subsuming another (for each pair there is an input on which the two
#   rivals disagree with each other):
#     * LEADING flank      — weak-split-leading-connector   at ['-','a']
#     * TRAILING flank     — weak-split-trailing-connector  at ['A','+','^']
#       (and both flanks together — weak-split-every-connector at ['-'], the
#        literal pre-fix behaviour the prepatch skeleton carries)
#     * separator ALPHABET — weak-narrow-connector-set       at ['a','^','b']
#                          — weak-no-whitespace-separator    at ['a',' ','b']
#                          — weak-ascii-space-only           at ['a','\t','b']
#     * MAXIMAL MUNCH      — weak-whitespace-run-per-char    at ['a',' ',' ','b']
#     * FLANK CLASS        — weak-linefeed-flanks            at ['a','-','\n']
#     * COUNT / ORDER      — weak-drop-last-segment          at ['a','+','b']
#                          — weak-reverse-order              at ['a','-','b']
#   Nine DISTINCT inputs, no two rivals refuted at the same one, spanning a
#   standalone separator (both flanks absent), a trailing one (leading present),
#   a leading one (trailing present), interior connectors, an interior single
#   space, an interior tab, a two-character whitespace run, and a separator
#   followed only by a line feed.
#
#   Independence of the three whitespace-axis rivals, since they are the newest
#   and the most likely to look redundant: weak-no-whitespace-separator and
#   weak-ascii-space-only disagree with each other on ['a',' ','b'] (the former
#   emits one segment, the latter three); weak-ascii-space-only and
#   weak-whitespace-run-per-char disagree on ['a','\t','b'] (one segment vs
#   three) AND on ['a',' ',' ','b'] (three vs five); weak-no-whitespace-separator
#   and weak-whitespace-run-per-char disagree on ['a',' ','b'] (one vs three).
#   And all three agree with the spec on every input in the connector-only
#   sub-domain, so no connector rival covers any of them.
#
#   WITNESS ATTESTATION on this cell (measured, not argued). `splitParts` is
#   defined by WELL-FOUNDED recursion, so `decide` is stuck on it for EVERY claim,
#   true or false — measured: `splitParts false [] ['-'] = [['-']]`, which is
#   TRUE, fails with "did not reduce to `isTrue` or `isFalse`", and so do
#   `decide +kernel`, `unfold splitParts; decide`, and `simp [splitParts]`
#   (maximum recursion depth). The frozen `while` impl is stuck for the further
#   reason the sibling records (its extracted program elaborates through a
#   fixpoint the kernel cannot unfold). So each witness FIRST reduces the oracle
#   to a literal by chaining the frozen `splitParts_step`/`splitParts_nil` unfold
#   lemmas with per-step decidable rewrites, and each reject case names
#   `witness_reference` = `_LOOPFREE` (== `pos-direct-model`'s module, which the
#   battery independently requires to VERIFY). Per rival, two real builds were run
#   during authoring:
#     (a) witness vs the rival    -> exit 0
#     (b) witness vs _LOOPFREE    -> exit 1 by GENUINE refutation
#                                    ("`decide` proved that the proposition False
#                                     is false"), NOT a stuck reduction.
#   And the rival half was shown to be load-bearing rather than automatic: the
#   line-feed rival's witness statement rebuilt at ['a','\n','-','b'] — an input
#   where that rival AGREES with the spec — is REFUTED against the rival
#   ("`decide` proved ¬… = [['a'], ['\n'], ['-','b']] is false"), so exit 0 on
#   (a) really does mean the rival violates the spec at the named input.
#   No `sorry` / `admit` / `native_decide` anywhere.
#
# AXIOM_TESTS: dropped. The sibling's axiom lane validates a deep-model reference
#   (`kparts` == the real `re.split`) — an A-reference this velvet bundle also
#   models deeply (`splitParts`), but whose fidelity to the real patched callee is
#   G-CONF's / G-AX's lane (meta.json records G-AX as a skip stub: no axiom, no
#   A-reference to probe). This gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
