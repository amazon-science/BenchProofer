"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8621 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over one input binder):

  tokenizeKeystrokes (text : List Char) : List (List Char)
      result = specSplit text

  The specification text is a sequence of characters (mapping.md: the keystroke
  spec, per-code-point, modeled as ``List Char``). ``specSplit`` is a
  TRANSPARENT, fully-unfolded single-pass tokenizer (a ``step``/``finalize``
  fold over the actual input characters), NOT an opaque answer-key oracle. The
  one top-level clause ``result = specSplit text`` pins every produced token —
  its content and its position — to the input, folding several inseparable
  sub-decisions, each observable on a distinct shape of ``text``:

    * a compound-key separator (``-``, ``+``, ``^``) is a boundary ONLY when it
      has a character on both sides, so a STANDALONE separator yields a single
      token equal to the whole input, never a separator framed by two empty
      tokens (observable on the length-1 input);
    * an INTERIOR separator (a keystroke on both sides) is a genuine boundary
      that splits the input into surrounding keystroke tokens (observable on the
      three-character input);
    * a run of horizontal whitespace with a character after it is likewise a
      boundary (observable on the whitespace input).

CARRIER NARROWING vs the nagini sibling. The nagini bundle models TWO functions
— the split itself (``split_keystrokes``) and a downstream predicate over its
part count (``keystroke_is_atomic``, ``Result()==(len(kparts(...))==1)``). This
lean bundle models only the purely functional core, the token list itself, so
every nagini case attached to ``keystroke_is_atomic`` — its self-call
admissibility, its local-reshape positive, and its part-count uniqueness rivals
(``weak-always-atomic``, ``weak-atomic-eq-2``) — has NO counterpart here: the
part-count predicate is not a modeled behavior. Those are omitted as carrier
narrowing (see ``assessment``), NOT because they were hard to express.

The nagini battery carries one further POSITIVE that is not attached to
``keystroke_is_atomic``, and so is NOT covered by that narrowing:
``pos-split-assert-reorder``, a soundness control on the split itself. Its
content — reorder two independent, order-free framing ``Assert``s at the head of
the impl region — is specific to a carrier where the IMPL region carries
proof-relevant annotations. Here it does not: the obligation is discharged in the
``proof`` region, and permuting tactics there is not a reshape of the
implementation. Its soundness role (a correct impl of the SPLIT, shaped
differently, must still verify) is discharged by two positives below —
``pos-functional-foldl``, and ``pos-structural-recursion`` because that first one
is definitionally the frozen fold and so cannot carry the role alone.

ADVERSARIAL READ of the remaining nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY because the input text is held at fractional
    (read-only) permission and a rival that overwrites a code point is rejected
    for insufficient permission. Lean is referentially transparent: ``text`` is
    a plain immutable ``List Char``, there is no half-permission to violate and
    no aliasing to exploit, so this class has NO expressible instance here. No
    substitute is fabricated for it.

  * DIVERGENCE / NON-TERMINATION — VACUOUS, and this was MEASURED rather than
    assumed. The bundle sets no ``loom.semantics.termination`` option: this is a
    plain Lean carrier, where the elaborator itself discharges termination, so
    the class is vacuous only if no diverging rival can be LANDED. Both ways of
    writing one were built:

      - a plain ``def`` whose recursive call does not decrease
        (``spinTok st (c :: cs) => spinTok (step st c) (c :: cs)``) does not
        elaborate at all: ``fail to show termination for spinTok / failed to
        infer structural recursion``. The variant file is uncompilable, so the
        case could only ever record an inconclusive ``witness-unproven``, never a
        refutation attributable to the spec;
      - the same body as ``partial def`` DOES elaborate (and is in variant scope
        — ``partial`` is not a banned token for a MODULE, only for a witness),
        and the obligation correctly fails. But no witness can refute it: a
        ``partial def`` is compiled to an opaque constant with no equations, so
        ``decide`` cannot reduce it. Measured: the witness build against that
        rival fails with ``Tactic `decide` failed … its `Decidable` instance
        instDecidableNot did not reduce to `isTrue` or `isFalse` … reduction got
        stuck``. That is exactly the ``witness-undecided`` stuck-reduction shape,
        which discriminates nothing.

    So the class is genuinely vacuous HERE: not because divergence is
    unexpressible, but because the only expressible diverging rival is
    unrefutable on this carrier. It is recorded as vacuous rather than as a known
    hole because the frozen obligation does reject it — the spec is not weak
    here, the witness lane simply cannot attest to it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: an equality
    against ``specSplit text``, a term built only from the input and fully
    unfolded (the ``step``/``finalize`` fold). The bundle declares no
    ``opaque``/``axiom`` (meta.json: the tokenizer is modeled deeply, no consumed
    callee), so there is no answer key an implementation could echo without doing
    the work. The honest analogue is the cheapest-correct POSITIVE CONTROL below.

  * UNIQUENESS / SPEC-TOO-WEAK — APPLIES, and is the load-bearing lane. The
    pre-fix behavior (a separator splits UNCONDITIONALLY, with no both-sides
    requirement) is the primary rival; two supporting rivals under- or
    over-collapse the split. SIX further NEAR-MISS rivals then pin the clause at
    its boundaries rather than in the middle: each keeps most of the tokenizer
    intact and isolates exactly one sub-decision — the EOS-shaving of a trailing
    whitespace run, the shave AMOUNT, the separator alphabet, the LEADING half of
    the both-sides requirement, the empty specification, and the empty keystroke
    token between two adjacent interior separators. Each of the six agrees with
    the frozen behavior on all three of the coarse witness points (and the last
    three agree on all SIX of the earlier points), so each is refutable only at
    an input shape no earlier case reaches. Every one violates the one clause on
    a distinct input and is refuted with a witness at that input.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (``congr 1`` + a fold-equality
lemma tuned to the ``Id.run do`` / ``for`` form) is tuned to the frozen shape —
so a rejection alone attributes nothing to the spec. Every ``expect="reject"``
case therefore carries a Lean snippet stating the spec predicate directly at a
``decide``-able concrete input; each was checked to HOLD of its rival and to
FAIL on the frozen solution (so it discriminates rather than asserting a
tautology). The carrier is fully transparent, so every witness is a literal
``List Char`` closed by ``decide`` — no opaque term to condition on.

BINDER COVERAGE. There is a single input binder, ``text``. Nine reject witnesses
vary it across EIGHT structurally distinct shapes (two rivals are refuted at the
same point, at different sub-decisions):

  * ``['-']``        — length-1 standalone separator (both-sides requirement,
                       trailing half);
  * ``['a','-','b']``— interior separator (a genuine boundary);
  * ``['a',' ','b']``— whitespace run with characters on both sides;
  * ``['a',' ',' ']``— trailing multi-character whitespace run (used by TWO
                       rivals, at different sub-decisions: whether a shave
                       happens at all, and by how much);
  * ``['a','^','b']``— the third member of the separator alphabet;
  * ``['-','a']``    — leading separator followed by text (the LEADING half of
                       the both-sides requirement, independent of the trailing
                       half);
  * ``[]``           — the empty specification (one empty token, not no tokens);
  * ``['a','-','-','b']`` — two ADJACENT interior separators, so the empty
                       keystroke token between them is a real token.

ESSENTIALITY, measured rather than asserted. The per-point/per-rival divergence
matrix was computed by evaluating every rival alongside ``specSplit`` in Lean and
reading the ``decide`` flags, and it does NOT support the stronger claim that
every point is load-bearing. FIVE of the eight points are essential — each is the
only point in this battery at which some rival diverges at all:

  ``[]`` (``weak-empty-spec-no-token``), ``['a',' ',' ']``
  (``weak-no-eos-shave`` AND ``weak-wrong-shave-amount``, which diverge there for
  different reasons), ``['a','^','b']`` (``weak-narrowed-sep-alphabet``),
  ``['-','a']`` (``weak-leading-sep-splits``), and ``['a','-','-','b']``
  (``weak-drop-empty-interior-token``).

The other three — ``['-']``, ``['a','-','b']``, ``['a',' ','b']`` — are NOT
essential in that sense: every rival they refute is also refuted at another
point, because the rivals they catch (the pre-fix skeleton, the drop-last impl,
the never-split impl) are coarse and diverge on many shapes at once. They are
kept because they are the F2P-shaped and most legible refutation points — ``['-']``
is literally one of the two F2P inputs — not because dropping them would lose a
rival. Recording the distinction matters: an earlier revision of this file
claimed each of its then-six points changed the verdict for a rival that no other
point caught, and measurement contradicts that for exactly these three.

``pts`` = 8 distinct input points across 9 reject witnesses; 5 points essential.

AXIOM lane: EMPTY. The tokenizer is modeled deeply and consumes no unchanged
callee as an axiom (meta.json axioms == []); the in-model soundness/containment
obligations belong to G-AX / G-CONF, not this gate. AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8621"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=\n"
    "  Id.run do\n"
    "    let mut st : TokState := initState\n"
    "    for c in text do\n"
    "      st := step st c\n"
    "    return finalize st\n"
)

_PROOF_BODY = (
    "  intro text\n"
    "  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes specSplit\n"
    "  simp only [Id.run, bind, pure]\n"
    "  congr 1\n"
    "  exact forIn_step_eq_foldl text initState\n"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival / positive impl bodies (each is a full impl region; only the impl
# changes, so the spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — the
# direct functional expression of the tokenizer (no `Id.run do` / `let mut` /
# `for`), spelling the fold as `finalize (text.foldl step initState)`. Same value
# on every input; the frozen script (which threads the desugared `for` loop
# through `forIn_step_eq_foldl`) no longer applies to the new shape, so the
# obligation is re-proved by `rfl` — the two sides are definitionally the same
# fold. No helper lemma, axiom, or assumption token is introduced.
_POS_IMPL = (
    "def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=\n"
    "  finalize (text.foldl step initState)\n"
)
_POS_PROOF = (
    "  intro text\n"
    "  rfl\n"
)

# SECOND POSITIVE CONTROL (soundness), NON-definitional. `_POS_IMPL` above is
# definitionally `specSplit` itself, so its obligation closes by `rfl`; that
# shows the spec is SATISFIABLE but not that a correct impl the kernel cannot
# identify with the frozen fold can still be PROVEN. This one spells the traversal
# as explicit structural recursion (`goTok`), which is NOT definitionally
# `List.foldl step`, so `rfl` does not close it: the two are related by an
# induction on the input, supplied as a `have` INSIDE the existing tactic body
# (no new top-level theorem/lemma, no axiom, no assumption token). This is the
# case that actually answers SPEC-TOO-STRONG.
_POS_REC_IMPL = (
    "def goTok : TokState → List Char → TokState\n"
    "  | st, [] => st\n"
    "  | st, c :: cs => goTok (step st c) cs\n"
    "\n"
    "def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=\n"
    "  finalize (goTok initState text)\n"
)
_POS_REC_PROOF = (
    "  intro text\n"
    "  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes"
    " specSplit\n"
    "  have hgo : ∀ (cs : List Char) (st : TokState),\n"
    "      goTok st cs = List.foldl step st cs := by\n"
    "    intro cs\n"
    "    induction cs with\n"
    "    | nil => intro st; rfl\n"
    "    | cons c cs ih => intro st; simp [goTok, List.foldl_cons, ih]\n"
    "  rw [hgo]\n"
)

# PARTIAL-DOMAIN (= the pre-fix bug): every separator character splits
# UNCONDITIONALLY — it is never required to have a character on both sides — and
# a whitespace run always splits. So a leading, trailing, or standalone separator
# is emitted as a real boundary framed by empty keystroke tokens. This is the
# pre-patch skeleton verbatim.
_PREPATCH_IMPL = (
    "def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=\n"
    "  Id.run do\n"
    "    let mut out : List (List Char) := []\n"
    "    let mut cur : List Char := []\n"
    "    let mut pendWs : List Char := []\n"
    "    let mut inWs : Bool := false\n"
    "    for c in text do\n"
    "      if inWs && isWsChar c then\n"
    "        pendWs := pendWs ++ [c]\n"
    "      else\n"
    "        if inWs then\n"
    "          out := out ++ [cur] ++ [pendWs]\n"
    "          cur := []\n"
    "          pendWs := []\n"
    "          inWs := false\n"
    "        if isSepChar c then\n"
    "          out := out ++ [cur] ++ [[c]]\n"
    "          cur := []\n"
    "        else if isWsChar c then\n"
    "          pendWs := [c]\n"
    "          inWs := true\n"
    "        else\n"
    "          cur := cur ++ [c]\n"
    "    if inWs then\n"
    "      out := out ++ [cur] ++ [pendWs]\n"
    "      cur := []\n"
    "    return out ++ [cur]\n"
)

# DROP-LAST: fold over all but the final character, then finalize. The last code
# point is silently dropped, so an interior boundary near the end is mis-tokenized
# and a trailing keystroke loses its final character.
_DROPLAST_IMPL = (
    "def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=\n"
    "  Id.run do\n"
    "    let mut st : TokState := initState\n"
    "    for c in text.dropLast do\n"
    "      st := step st c\n"
    "    return finalize st\n"
)

# NEVER-SPLIT: emit the whole input as one single keystroke token, never
# splitting on any interior separator or whitespace run.
_SINGLE_IMPL = (
    "def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=\n"
    "  [text]\n"
)

# NO-EOS-SHAVE: the trailing-whitespace-run clause is dropped — a pending
# whitespace run at end-of-input is ALWAYS folded whole into the current
# keystroke, instead of contributing all but its last character as the final
# separator. Agrees with the frozen tokenizer on every input whose trailing
# whitespace run is shorter than two characters, and on all three inputs the
# pre-existing rivals are refuted at; diverges only when a run of >= 2
# whitespace characters reaches the end of the specification.
_NOSHAVE_IMPL = (
    "def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=\n"
    "  let st := text.foldl step initState\n"
    "  match st.pend with\n"
    "  | Pend.pendNone => st.out ++ [st.cur]\n"
    "  | Pend.pendSep sc => st.out ++ [st.cur ++ [sc]]\n"
    "  | Pend.pendWs run => st.out ++ [st.cur ++ run]\n"
)

# NARROWED SEPARATOR ALPHABET: `^` is not treated as a compound-key separator
# (only `-` and `+` are), so an interior `^` with keystrokes on both sides is
# swallowed into the surrounding keystroke text instead of becoming a boundary.
# Every other decision — the both-sides requirement, the whitespace run, the
# EOS handling — is kept verbatim, so the rejection is attributable to the
# separator alphabet alone.
_NOCARET_IMPL = (
    "def stepNoPendNoCaret (st : TokState) (c : Char) : TokState :=\n"
    "  if !st.started then\n"
    "    { st with cur := st.cur ++ [c], started := true }\n"
    "  else if c == '-' || c == '+' then\n"
    "    { st with pend := Pend.pendSep c }\n"
    "  else if isWsChar c then\n"
    "    { st with pend := Pend.pendWs [c] }\n"
    "  else\n"
    "    { st with cur := st.cur ++ [c] }\n"
    "\n"
    "def stepNoCaret (st : TokState) (c : Char) : TokState :=\n"
    "  match st.pend with\n"
    "  | Pend.pendNone => stepNoPendNoCaret st c\n"
    "  | Pend.pendSep sc =>\n"
    "      stepNoPendNoCaret\n"
    "        { st with out := st.out ++ [st.cur] ++ [[sc]], cur := [],"
    " pend := Pend.pendNone } c\n"
    "  | Pend.pendWs run =>\n"
    "      if isWsChar c then\n"
    "        { st with pend := Pend.pendWs (run ++ [c]) }\n"
    "      else\n"
    "        stepNoPendNoCaret\n"
    "          { st with out := st.out ++ [st.cur] ++ [run], cur := [],"
    " pend := Pend.pendNone } c\n"
    "\n"
    "def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=\n"
    "  finalize (text.foldl stepNoCaret initState)\n"
)

# LEADING-SEPARATOR SPLITS: the `started` guard is dropped, so a separator at
# the very FRONT of the specification is treated as a boundary candidate and
# commits as soon as any character follows it. The TRAILING half of the
# both-sides requirement is kept intact (a candidate still needs a following
# character), which is why the three pre-existing witness points — `['-']`,
# `['a','-','b']`, `['a',' ','b']` — all agree with the frozen tokenizer here.
# Only a leading separator with text after it diverges.
_LEADING_IMPL = (
    "def stepNoPendNoStart (st : TokState) (c : Char) : TokState :=\n"
    "  if isSepChar c then\n"
    "    { st with pend := Pend.pendSep c }\n"
    "  else if isWsChar c then\n"
    "    { st with pend := Pend.pendWs [c] }\n"
    "  else\n"
    "    { st with cur := st.cur ++ [c], started := true }\n"
    "\n"
    "def stepNoStart (st : TokState) (c : Char) : TokState :=\n"
    "  match st.pend with\n"
    "  | Pend.pendNone => stepNoPendNoStart st c\n"
    "  | Pend.pendSep sc =>\n"
    "      stepNoPendNoStart\n"
    "        { st with out := st.out ++ [st.cur] ++ [[sc]], cur := [],"
    " pend := Pend.pendNone } c\n"
    "  | Pend.pendWs run =>\n"
    "      if isWsChar c then\n"
    "        { st with pend := Pend.pendWs (run ++ [c]) }\n"
    "      else\n"
    "        stepNoPendNoStart\n"
    "          { st with out := st.out ++ [st.cur] ++ [run], cur := [],"
    " pend := Pend.pendNone } c\n"
    "\n"
    "def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=\n"
    "  finalize (text.foldl stepNoStart initState)\n"
)


# EMPTY-SPECIFICATION CLAUSE: the empty specification yields NO tokens instead of
# the single empty token. Identical to the frozen tokenizer on every non-empty
# input, so ALL SIX of the pre-existing witness points agree with it; only the
# empty input separates it. This is the shortest input shape, and no other case in
# the battery states anything about it.
_EMPTYNIL_IMPL = (
    "def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=\n"
    "  match text with\n"
    "  | [] => []\n"
    "  | _ => finalize (text.foldl step initState)\n"
)

# WRONG SHAVE AMOUNT: a trailing whitespace run of >= 2 characters IS recognized
# as reaching end-of-input and IS shaved (so this is not `_NOSHAVE_IMPL` again),
# but the run is emitted WHOLE as the separator with an EMPTY trailing keystroke,
# instead of contributing all-but-its-last character with its last character
# beginning the trailing keystroke. Same token COUNT as the frozen tokenizer on
# every input — so a count-based or length-based check cannot see it — and it
# agrees with the frozen tokenizer everywhere except a trailing multi-character
# whitespace run, where it differs from BOTH the frozen tokenizer and
# `_NOSHAVE_IMPL`.
_SHAVEAMT_IMPL = (
    "def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=\n"
    "  let st := text.foldl step initState\n"
    "  match st.pend with\n"
    "  | Pend.pendNone => st.out ++ [st.cur]\n"
    "  | Pend.pendSep sc => st.out ++ [st.cur ++ [sc]]\n"
    "  | Pend.pendWs run =>\n"
    "      if run.length ≥ 2 then st.out ++ [st.cur] ++ [run] ++ [[]]\n"
    "      else st.out ++ [st.cur ++ run]\n"
)

# EMPTY INTERIOR TOKEN SUPPRESSED: two ADJACENT interior separators are each a
# genuine boundary, so the (empty) keystroke token between them is a real token
# and must be kept. This rival drops empty tokens from a multi-token result — the
# plausible "tidy up the split" reshape — which shortens the alternating
# key/sep/key list and shifts every later token's parity. Agrees with the frozen
# tokenizer on all six pre-existing witness points (none of which has two
# adjacent interior separators).
_NOEMPTY_IMPL = (
    "def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=\n"
    "  let r := finalize (text.foldl step initState)\n"
    "  if r.length ≥ 3 then r.filter (fun t => t ≠ []) else r\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. The `theorem correct_tokenizeKeystrokes`
    # STATEMENT is byte-identical; the tactic body is re-proved for the new shape
    # (the frozen `congr 1; exact forIn_step_eq_foldl …` is tuned to the desugared
    # `for` loop, which the functional reshape no longer has). No helper lemma,
    # axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-functional-foldl",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_IMPL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` / "
            "`for` loop and spells the tokenizer as the direct fold `finalize "
            "(text.foldl step initState)` must satisfy `result = specSplit text`; "
            "if it cannot, the spec is SPEC-TOO-STRONG. This is also the cheapest "
            "HONEST impl of the grounded post (`specSplit` IS `finalize (…foldl "
            "step initState)`), so after `unfold` both sides are definitionally the "
            "same fold and the goal closes by `rfl` — no new declaration, axiom, or "
            "assumption token."
        ),
    },

    # =====================================================================
    # SECOND POSITIVE CONTROL (soundness) — the NON-definitional reshape. The
    # case above is definitionally the frozen fold (`rfl` closes it), so it
    # cannot distinguish "the spec is satisfiable" from "the spec admits a
    # correct impl the kernel does not identify with the frozen one". This one
    # traverses by explicit structural recursion, which `rfl` does NOT close;
    # the obligation is discharged by an induction supplied as a `have` inside
    # the existing tactic body. If THIS could not be proven, the spec would be
    # SPEC-TOO-STRONG in the way that matters.
    # =====================================================================
    {
        "id": "pos-structural-recursion",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_REC_IMPL), _PROOF_BODY, _POS_REC_PROOF),
        "rationale": (
            "a correct impl that traverses the specification by explicit "
            "structural recursion (`goTok`) rather than by `List.foldl` must "
            "still satisfy `result = specSplit text`. Unlike the reshape above "
            "this is NOT definitionally the frozen fold — `rfl` does not close "
            "it — so the obligation is re-established by an induction on the "
            "input, written as a `have` inside the existing tactic body. No new "
            "top-level theorem/lemma, no axiom, no assumption token; the "
            "`theorem correct_tokenizeKeystrokes` STATEMENT is byte-identical. "
            "This is the case that answers SPEC-TOO-STRONG for a correct impl "
            "the kernel cannot simply identify with the frozen one."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the normal, F2P-shaped input rather than only provable in
    # the abstract. The frozen theorem carries NO precondition hypothesis (the
    # behavior is total over `List Char`), so nagini's precondition-admission
    # probe (`admiss-self-call`, which discharges a callee `Requires` from the
    # caller's precondition) has no binder to attack here; the honest analogue is
    # to discharge the spec predicate at a concrete F2P input (a compound
    # keystroke with an interior separator AND a standalone-looking trailing
    # separator) inside the proof region, alongside the frozen obligation. If that
    # ground instance could not be discharged, the modeled behavior would be
    # unsatisfiable at exactly the input the F2P exercises.
    # =====================================================================
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_BODY,
            "  have _ground : problem_spec_tokenizeKeystrokes ['A','l','t','+','^']\n"
            "      (implementation_tokenizeKeystrokes ['A','l','t','+','^']) := by\n"
            "    unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes\n"
            "    decide\n"
            + _PROOF_BODY,
        ),
        "rationale": (
            "the obligation is discharged at a concrete F2P input (a compound "
            "keystroke `Alt+^`: an interior `+` boundary with keystrokes on both "
            "sides, and a trailing `^` that is NOT a boundary because nothing "
            "follows it) by `decide`, then the frozen obligation is closed "
            "verbatim. Verifies (else the spec is unsatisfiable at the normal "
            "input, the analogue of PRECOND-TOO-STRONG). Nothing is assumed: the "
            "theorem STATEMENT is byte-identical, the ground instance is a `have` "
            "inside the existing tactic body, and no new declaration/axiom/`sorry` "
            "is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would be
    # a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-prepatch-unconditional-split",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH_IMPL),
        "refinement": (
            "this is the pre-fix behavior: a compound-key separator splits "
            "unconditionally, with no requirement that a character sit on BOTH "
            "sides. Its faithful real patch is exactly the pre-patch code, which "
            "renders a standalone separator as a boundary framed by two empty "
            "keystroke tokens — precisely the reported bug (a lone `-` becomes an "
            "empty/`-`/empty nesting instead of a single token). That fails the "
            "F2P observable for the standalone-separator keystroke. It does NOT "
            "resolve — this is the leg's prepatch."
        ),
        "rationale": (
            "REJECT from the clause `result = specSplit text`: at `text = ['-']` "
            "the separator has no character before it, so it is not a boundary and "
            "`specSplit` yields the single token `[['-']]`, but the rival splits "
            "unconditionally into `[[], ['-'], []]`. Refuted on a length-1 "
            "standalone separator — the shape that isolates the both-sides "
            "requirement."
        ),
        "witness": (
            "-- Refuted on a standalone separator: with no character before it the\n"
            "-- `-` is not a boundary, so the whole input is one token; a rival that\n"
            "-- splits unconditionally frames it with two empty tokens.\n"
            "example : ¬ problem_spec_tokenizeKeystrokes ['-']\n"
            "    (implementation_tokenizeKeystrokes ['-']) := by\n"
            "  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-drop-last-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROPLAST_IMPL),
        "refinement": (
            "folding over all but the final character silently drops the last code "
            "point of every specification. Because a separator only commits when a "
            "further character arrives, dropping the final character also "
            "un-commits a separator that was the second-to-last code point: `a-b` "
            "collapses to the SINGLE token `a-` instead of `a`/`-`/`b`, and a "
            "standalone `-` becomes the empty token. The rebuilt `<kbd>` would "
            "lose its final keystroke on every compound key — and, because a "
            "one-token result short-circuits the rebuild entirely, a compound key "
            "would render as one flat literal. That fails the F2P renders; it does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = specSplit text`: at `text = "
            "['a','-','b']` the interior `-` has keystrokes on both sides, so "
            "`specSplit` yields the three tokens `[['a'], ['-'], ['b']]`, but "
            "folding only over `['a','-']` leaves the `-` as an UNCOMMITTED "
            "pending candidate (nothing ever arrives after it), so `finalize` "
            "folds it back and the rival returns the single token "
            "`[['a','-']]` — one token where the spec demands three. Refuted on "
            "an interior-separator input of length 3, varying the binder off the "
            "length-1 shape."
        ),
        "witness": (
            "-- Refuted on an interior separator: `a-b` must split into the two\n"
            "-- surrounding keystrokes; dropping the final character loses the\n"
            "-- trailing keystroke `b`.\n"
            "example : ¬ problem_spec_tokenizeKeystrokes ['a','-','b']\n"
            "    (implementation_tokenizeKeystrokes ['a','-','b']) := by\n"
            "  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-never-split",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SINGLE_IMPL),
        "refinement": (
            "emitting the whole input as a single keystroke token never separates "
            "a genuine compound key: `a b` (a whitespace boundary with characters "
            "on both sides) stays one token instead of `a`/` `/`b`, so the "
            "`len(parts)==1` short-circuit downstream would leave a multi-key "
            "specification as a flat single `<kbd>`, failing the compound-key F2P "
            "renders. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = specSplit text`: at `text = "
            "['a',' ','b']` the whitespace run has characters on both sides, so "
            "`specSplit` yields `[['a'], [' '], ['b']]`, but the rival returns the "
            "single token `[['a',' ','b']]`. Refuted on a whitespace-bounded input, "
            "exercising the whitespace-run boundary decision at a third distinct "
            "input shape."
        ),
        "witness": (
            "-- Refuted on a whitespace-bounded input: a whitespace run with\n"
            "-- characters on both sides is a genuine boundary; a never-split impl\n"
            "-- collapses the compound key into one token.\n"
            "example : ¬ problem_spec_tokenizeKeystrokes ['a',' ','b']\n"
            "    (implementation_tokenizeKeystrokes ['a',' ','b']) := by\n"
            "  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes\n"
            "  decide\n"
        ),
    },

    # =====================================================================
    # NEAR-MISS rivals. The three rivals above all diverge from the frozen
    # tokenizer on SHORT, coarse inputs, so each is refuted by a witness that a
    # blunt "never split" or "always split" impl would also fail. These three
    # are tighter: each agrees with the frozen tokenizer on ALL THREE of the
    # witness points used above, and diverges only on a further input shape that
    # isolates one sub-decision of the single clause. They are what pins the
    # clause at the boundary rather than in the middle.
    # =====================================================================
    {
        "id": "weak-no-eos-shave",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NOSHAVE_IMPL),
        "refinement": (
            "this rival keeps the whole both-sides requirement and differs on one "
            "point only: when a whitespace run of two or more characters reaches "
            "the END of the specification, it folds the entire run into the "
            "trailing keystroke instead of emitting all-but-the-last as the "
            "separator and letting the last character begin the trailing "
            "keystroke. On `a` + two spaces the token list would be the single "
            "token `a  ` rather than `a`/` `/` `, so a specification ending in a "
            "multi-space run collapses to one token and the rebuild is "
            "short-circuited instead of producing the separator the real "
            "splitter produces. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = specSplit text`: at `text = "
            "['a',' ',' ']` the frozen tokenizer yields the three tokens "
            "`[['a'], [' '], [' ']]` (the run contributes `run.dropLast` as the "
            "separator and its last character begins the trailing keystroke), "
            "while this rival yields the single token `[['a',' ',' ']]`. This is "
            "the trailing-whitespace-run sub-decision, which no other case in "
            "this battery reaches: the rival AGREES with the frozen tokenizer at "
            "`['-']`, `['a','-','b']` and `['a',' ','b']`, so the three witnesses "
            "above would all fail of it — a fourth input shape is required."
        ),
        "witness": (
            "-- Refuted on a trailing multi-character whitespace run. The run does\n"
            "-- not vanish into the trailing keystroke: all but its last character\n"
            "-- is the separator, and the last character begins the final token.\n"
            "example : ¬ problem_spec_tokenizeKeystrokes ['a',' ',' ']\n"
            "    (implementation_tokenizeKeystrokes ['a',' ',' ']) := by\n"
            "  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-narrowed-sep-alphabet",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NOCARET_IMPL),
        "refinement": (
            "this rival narrows the separator alphabet: `-` and `+` still "
            "separate, `^` never does. Every other decision (the both-sides "
            "requirement, the greedy whitespace run, the end-of-input handling) "
            "is kept verbatim. A keystroke specification whose compound "
            "separator is `^` would render as one flat literal instead of the "
            "two keystrokes on either side of it, so a `^`-separated compound key "
            "is mis-rendered. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = specSplit text`: at `text = "
            "['a','^','b']` the interior `^` has keystrokes on both sides, so "
            "`specSplit` yields `[['a'], ['^'], ['b']]`, while this rival "
            "swallows the `^` and returns the single token `[['a','^','b']]`. "
            "This pins the third member of the separator alphabet, which the "
            "other rivals never isolate — they are refuted at `-` and whitespace "
            "points, and this rival agrees with the frozen tokenizer at all "
            "three of them (including `Alt+^`, where the `^` is trailing and "
            "therefore not a boundary anyway)."
        ),
        "witness": (
            "-- Refuted on an interior `^`: it is a compound-key separator on the\n"
            "-- same footing as `-` and `+`, so with a keystroke on both sides it\n"
            "-- is a genuine boundary.\n"
            "example : ¬ problem_spec_tokenizeKeystrokes ['a','^','b']\n"
            "    (implementation_tokenizeKeystrokes ['a','^','b']) := by\n"
            "  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-leading-sep-splits",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_LEADING_IMPL),
        "refinement": (
            "this rival enforces only HALF of the both-sides requirement. A "
            "separator candidate still has to be followed by a character to "
            "commit, so a trailing or standalone separator is handled correctly; "
            "but the guard that a separator must also have a character BEFORE it "
            "is dropped, so a specification that begins with a separator emits an "
            "empty leading keystroke followed by a separator boundary. A "
            "specification like `-a` would render as a blank keystroke plus `a` "
            "rather than the single keystroke `-a`. This is the more dangerous "
            "half-fix of the reported behavior: it repairs the standalone case "
            "while leaving the leading case broken, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = specSplit text`: at `text = "
            "['-','a']` the leading `-` has no character before it, so it is not "
            "a boundary and `specSplit` yields the single token `[['-','a']]`, "
            "while this rival splits into `[[], ['-'], ['a']]`. Crucially this "
            "rival is NOT caught by the `['-']` witness — with nothing following "
            "the separator it agrees with the frozen tokenizer there, and it "
            "agrees at `['a','-','b']` and `['a',' ','b']` too. Only a leading "
            "separator followed by text separates it from the spec, so this pins "
            "the leading half of the both-sides requirement independently of the "
            "trailing half."
        ),
        "witness": (
            "-- Refuted on a leading separator followed by text: the `-` has no\n"
            "-- character before it, so it is not a boundary and the whole input is\n"
            "-- one keystroke token — no empty leading token is emitted.\n"
            "example : ¬ problem_spec_tokenizeKeystrokes ['-','a']\n"
            "    (implementation_tokenizeKeystrokes ['-','a']) := by\n"
            "  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes\n"
            "  decide\n"
        ),
    },

    # =====================================================================
    # BOUNDARY-OF-THE-BOUNDARY rivals. Every case above is refuted at one of
    # six input points, and three of those six points are NOT essential: each
    # rival they catch is also caught at another point (see BINDER COVERAGE).
    # These three attack sub-decisions that NO point above reaches at all — the
    # empty specification, the shave AMOUNT (as opposed to whether a shave
    # happens), and the empty keystroke token between two adjacent interior
    # separators. Each agrees with the frozen tokenizer at all six points above,
    # so each is refutable only at a seventh, eighth, or ninth input shape.
    # =====================================================================
    {
        "id": "weak-empty-spec-no-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_EMPTYNIL_IMPL),
        "refinement": (
            "an empty keystroke specification yields ONE token — the empty "
            "keystroke — not zero tokens. This rival returns the empty token "
            "list instead, and is otherwise the frozen tokenizer verbatim on "
            "every non-empty input. Downstream, a zero-token result is not a "
            "one-token result, so the rebuild short-circuit that must fire for "
            "an unsplittable specification no longer fires, and an empty "
            "specification is rebuilt with no keystroke children at all instead "
            "of being left alone. It does NOT resolve — it changes behavior only "
            "away from the F2P inputs while breaking the degenerate one."
        ),
        "rationale": (
            "REJECT from the clause `result = specSplit text`: at `text = []` "
            "the fold performs no step and `finalize` emits the accumulated "
            "(empty) keystroke, so `specSplit` yields the single token `[[]]`, "
            "while this rival yields `[]`. This is the empty-input sub-decision, "
            "which no other case in this battery states anything about: the "
            "rival AGREES with the frozen tokenizer at all six of the other "
            "witness points, so every other witness would fail of it."
        ),
        "witness": (
            "-- Refuted on the empty specification: the tokenizer always emits at\n"
            "-- least one keystroke token, so the empty input yields one empty\n"
            "-- token — never an empty token list.\n"
            "example : ¬ problem_spec_tokenizeKeystrokes []\n"
            "    (implementation_tokenizeKeystrokes []) := by\n"
            "  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-wrong-shave-amount",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SHAVEAMT_IMPL),
        "refinement": (
            "this rival DOES recognize that a trailing whitespace run of two or "
            "more characters reaches end-of-input and must be shaved — so it is "
            "not the no-shave rival again — but it shaves by the wrong amount: "
            "it emits the run WHOLE as the separator and an EMPTY trailing "
            "keystroke, instead of emitting all-but-the-last character as the "
            "separator with the last character beginning the trailing keystroke. "
            "The boundary still needs a character after it, and here there is "
            "none, so the final character belongs to the keystroke. It produces "
            "the same NUMBER of tokens as the frozen tokenizer on every input, "
            "so it renders a trailing blank keystroke where the real splitter "
            "renders a whitespace-bearing one. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = specSplit text`: at `text = "
            "['a',' ',' ']` the frozen tokenizer yields `[['a'], [' '], [' ']]` "
            "— `run.dropLast` is the separator and `run.getLast!` begins the "
            "trailing keystroke — while this rival yields `[['a'], [' ',' '], "
            "[]]`. Same token count, different token CONTENT, so this pins the "
            "shave AMOUNT rather than merely whether a shave happens; "
            "`weak-no-eos-shave` cannot distinguish it (that rival does not "
            "shave at all) and all six other witness points agree with it."
        ),
        "witness": (
            "-- Refuted on a trailing multi-character whitespace run: the run is\n"
            "-- split, all but its last character forming the separator and its\n"
            "-- last character beginning the trailing keystroke — the trailing\n"
            "-- keystroke is NOT empty.\n"
            "example : ¬ problem_spec_tokenizeKeystrokes ['a',' ',' ']\n"
            "    (implementation_tokenizeKeystrokes ['a',' ',' ']) := by\n"
            "  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-drop-empty-interior-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NOEMPTY_IMPL),
        "refinement": (
            "two ADJACENT interior separators are each a genuine boundary — each "
            "has a character on both sides — so the keystroke token between them "
            "is a real, empty token and must be kept. This rival tidies empty "
            "tokens out of a multi-token result, which is the plausible "
            "'clean up the split' reshape. Because the result is an ALTERNATING "
            "key/separator/key list read by position, dropping an interior entry "
            "shifts every later token's parity: separators are then read as "
            "keystrokes and keystrokes as separators for the rest of the "
            "specification. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = specSplit text`: at `text = "
            "['a','-','-','b']` both interior `-` characters have a character on "
            "each side, so both are boundaries and `specSplit` yields the FIVE "
            "tokens `[['a'], ['-'], [], ['-'], ['b']]` — the empty keystroke "
            "between the two separators is a real token. This rival filters it "
            "out and returns four tokens. No other case in this battery uses an "
            "input with two adjacent interior separators, and the rival agrees "
            "with the frozen tokenizer at all six other witness points."
        ),
        "witness": (
            "-- Refuted on two adjacent interior separators: each is a boundary,\n"
            "-- so the empty keystroke token between them is a real token and is\n"
            "-- not dropped — the alternating key/separator positions depend on it.\n"
            "example : ¬ problem_spec_tokenizeKeystrokes ['a','-','-','b']\n"
            "    (implementation_tokenizeKeystrokes ['a','-','-','b']) := by\n"
            "  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references consumed by this gate: the
# tokenizer is modeled deeply and grounded in the input, so there is no in-model
# axiom obligation for the PBT axiom lane to re-discharge (the deep-model ==
# real-callee validation belongs to G-AX / G-CONF).
AXIOM_TESTS = []
