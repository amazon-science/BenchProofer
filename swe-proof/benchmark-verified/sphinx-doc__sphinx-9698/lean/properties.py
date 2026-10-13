"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9698 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_getIndexText`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total behavior; the whole modeled surface is one function):

  getIndexText (name modname : String)
               (isClassmethod isProperty isStaticmethod addModuleNames : Bool)
    : String     — assemble the index-entry label for a documented class member.

  ``problem_spec_getIndexText`` splits on ``rsplitLastDot name`` and then pins the
  result with SIX independent top-level clauses — two in the ``none`` arm, four in
  the ``some`` arm. Naming them for the case rationales below:

    (N1) no separating dot, module name present:
         result = name ++ "() (in module " ++ modname ++ ")"
    (N2) no separating dot, module name empty:
         result = name ++ "()"
    (S1) splits, call-like kind #1 (isClassmethod):
         result = methname ++ "() (" ++ clsname ++ " class method)"
    (S2) splits, value-like kind (¬isClassmethod ∧ isProperty):
         result = methname ++ " (" ++ clsname ++ " property)"   ← NO argument list
    (S3) splits, call-like kind #2 (¬isClassmethod ∧ ¬isProperty ∧ isStaticmethod):
         result = methname ++ "() (" ++ clsname ++ " static method)"
    (S4) splits, call-like default kind (all three flags false):
         result = methname ++ "() (" ++ clsname ++ " method)"

  and inside (S1)–(S4) the qualifying-class component is itself pinned:
    (Q)  clsname = if addModuleNames && modname != "" then
                     modname ++ "." ++ clsname0 else clsname0
  — a nested conditional that is load-bearing in all four splitting clauses.

  One further component is load-bearing and lives in the (frozen) ``pure`` region
  rather than in a postcondition clause:

    (R)  ``rsplitLastDot`` splits at the FINAL dot and REJOINS everything before
         it, so for a multi-segment dotted name the leading class component keeps
         its own interior dots. (Q) and (S1)–(S4) are stated over exactly that
         component, so an implementation that re-splits or trims it contradicts
         the four splitting clauses — see the multi-segment rival below.

  THE DISCRIMINATOR is the contrast between (S2) and (S1)/(S3)/(S4): the
  value-like kind is named by its bare member name, the three call-like kinds
  carry an empty argument list after it. That contrast is what the nagini
  sibling's (P3) clause encoded as ``is_callable_role(option) == (marker
  present)``; here it is not a separate clause but the DIFFERENCE between the
  four splitting clauses, so an attack on it is an attack on (S2) versus its
  three siblings.

ADVERSARIAL READ of the nagini case classes on THIS carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's mandatory
    ``frame-mutate-methname`` rival writes into a name carrier held at half
    permission and is rejected by the permission system. Lean is referentially
    transparent: ``name`` and ``modname`` are immutable ``String`` values, there
    is no fractional permission to overdraw and no aliasing to exploit, so that
    rival has NO expressible instance here. No substitute is fabricated for it.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole attack surface here. The
    nagini battery's substantive rivals (``partial-property-keeps-parens``,
    ``partial-inverted-discriminator``, ``uniqueness-wrong-class-slice``) all
    port, and the carrier admits four more that nagini's narrower model — which
    folded the module-name qualification and the dotless-name fallback away —
    could not express. See the ``kind`` walk below.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on this backend, DEMONSTRATED. The
    frozen file sets no ``loom.semantics.termination`` option at all (it is not a
    loom bundle; ``implementation_getIndexText`` is a plain total Lean ``def``),
    so the "total" disposition applies: a rival whose recursion carries no
    decreasing measure is not merely rejected, it does not ELABORATE, which means
    there is no rival module for a ``diverge-*`` case to be. Measured rather than
    asserted, with two builds:

      - a self-recursive ``def`` (the fallback arm returns a call on the same six
        arguments) fails with ``fail to show termination for
        implementation_getIndexText`` / ``failed to infer structural recursion:
        ... it is unchanged in the recursive calls``. The failure is in the
        DEFINITION, before any obligation is reached, so the case could not
        distinguish a spec verdict from a well-formedness one;
      - marking that same recursion ``partial`` does not rescue it either: the
        frozen obligation's own ``unfold`` then fails
        (``Tactic `unfold` failed to unfold `implementation_getIndexText```),
        because a ``partial def`` is opaque and has no equation to unfold. So the
        rejection would attest to opacity, not to the spec.

    Both are tooling/well-formedness rejections rather than spec refutations, so
    no witness could discriminate and the class carries nothing. This is the LEAN
    total-carrier disposition; a velvet sibling under PARTIAL termination
    semantics would record a KNOWN SPEC HOLE here instead, which is a different
    finding and does not apply to a total ``def``.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the same reason the nagini sibling
    recorded it N/A: every clause of ``problem_spec_getIndexText`` is grounded in
    the input binders (``rsplitLastDot`` is a concrete split; the four label
    shapes are concatenations of ``methname``/``clsname``/literals). There is no
    opaque answer key an implementation could echo without doing the assembly.
    In its place the battery carries four honest POSITIVE CONTROLS (``pos-*``).

  * ADMISSIBILITY / PRECOND-TOO-STRONG — APPLIES, and is carried. An earlier
    revision of this manifest recorded the lane VACUOUS on the ground that
    ``correct_getIndexText`` is an UNCONDITIONAL ``∀`` over all six binders, so
    there is no precondition hypothesis to be too strong. A later audit measured
    that reason and rejected it: "the obligation has no precondition" is not what
    makes the lane vacuous. On a TOTAL carrier the analogue of PRECOND-TOO-STRONG
    is the obligation being UNSATISFIABLE at exactly a reported-shape input, and
    that is a claim about this spec which nothing else in the battery establishes
    — every other case either reshapes the implementation (the positives) or
    refutes a rival (the rejects); none of them shows that
    ``problem_spec_getIndexText`` can be SATISFIED at a concrete input at all.
    The nagini ``admiss-f2p-shape`` case's counterpart is therefore
    ``admiss-ground-reported-shape`` below, which discharges the obligation BY
    EVALUATION at two concrete points — a dotted name at the value-like kind and
    a dotless name with a module name — as two ``have``s, and only then closes
    the frozen obligation verbatim.

    That the ground ``have`` is not trivially true was measured with a SHARP
    negative control rather than argued: the same tactic
    (``split <;> simp_all``) applied to the same input with a WRONG result
    exits 1, and the failure lands in the SPLITTING arm
    (``⊢ "Class.meth5()" = methname ++ " (" ++ clsname0 ++ " property)"``) rather
    than in the unreachable fallback arm — so the discharge tracks the claimed
    label and is not an artifact of an arm that cannot be reached. The control
    was chosen to satisfy the ``none`` arm on purpose, since a merely wrong
    constant fails in that arm and would prove nothing about the value-like
    clause.

  * AXIOM lane — DROPPED. The nagini bundle's two ``AXIOM_TESTS`` belong to
    G-AX, which the G-PBT spec lane ignores. This bundle consumes no callee
    axiom and declares no A-reference (meta.json: G-AX skip, impl all R/I).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script ends in ``split <;> rfl`` and is
tuned to the frozen form — so a rejection alone attributes nothing to the spec.
Measured here (re-measured case by case in a later audit, exit codes and error
text recorded): EIGHT of the ten rivals below fail with ``Tactic `rfl` failed:
The left-hand side``; ``nodot-fallback-results-exchanged`` fails with ``Type
mismatch`` on an ``if_pos`` plus ``unsolved goals``; and
``nodot-always-names-a-module`` fails with ``No goals to be solved`` plus
``unsolved goals`` (an earlier revision of this note counted seven ``rfl``
failures and split the last two rivals' signatures into three single-error
classes; the audit rebuild found eight and two, each of the two carrying two
diagnostics). Every one of them is a TACTIC failure of the frozen script,
indistinguishable from what a merely-RESHAPED correct implementation produces.
Confirmed on this very bundle, and re-confirmed by the audit with fresh builds: a
correct reshape that merely COMMUTES the two ``Bool`` conjuncts of (Q) breaks the
frozen ``simp only``/``rfl`` chain the same way (``unsolved goals``, the two sides
differing only in the argument order of ``&&``), and it VERIFIES once the
qualification decision is commuted back with ``Bool.and_comm`` before the four
clauses are split — so its rejection under the frozen script was a tactic
artifact and not a spec verdict. A second correct reshape that hoists the whole
kind-dispatch into a ``let`` and ends in a single concatenation likewise verifies
once ``String.append_assoc`` is supplied. So a rejection alone attributes
nothing. Every ``expect="reject"`` case therefore carries a Lean snippet proving
the rival CONTRADICTS the spec at one concrete input, checked to hold of the rival
and to FAIL on the frozen solution.

Those witnesses are HYPOTHESIS-CONDITIONED, and necessarily so. The carrier will
not compute: ``rsplitLastDot "Class.meth5"`` does not reduce, because
``String.splitOn`` delegates to ``String.splitOnAux``, which the standard library
marks ``@[irreducible]`` — so neither the elaborator nor the KERNEL will unfold it
(``#print axioms String.splitOnAux`` reports only ``propext``, i.e. the blocker is
the reducibility attribute, not an axiom or well-founded-recursion opacity; an
earlier revision of this note attributed it to well-founded recursion, which the
audit corrected). Re-measured directly in an audit, each as a standalone
``example`` against the frozen file, all exit 1:

  * ``by rfl``            — ``is not definitionally equal to the right-hand side``
  * ``by decide``         — ``did not reduce to `isTrue` or `isFalse` ``
  * ``by decide +kernel`` — same, ``Reduction got stuck at the `Decidable` instance``
  * ``by simp [rsplitLastDot]`` — ``unsolved goals`` on the unreduced ``match``
  * ``by simp [String.splitOn]`` — ```simp` made no progress``

An UNCONDITIONED witness confirms this from the other side: the same refutation
stated at literal inputs with no hypothesis fails against the rival with ``failed
to synthesize Decidable``, i.e. it is not merely unproven but undecidable as
stated — which is the ``_STUCK_INSTANCE`` shape the gate screens for.
So each witness conditions on the split instead of computing it —
``(h : rsplitLastDot "Class.meth5" = some ("Class", "meth5"))``, or
``(h : rsplitLastDot "meth5" = none)`` for the dotless-name branch — rewrites by
it, and then ``decide`` closes: past the split every remaining component is a
string literal and every flag is a ``Bool`` literal. Exactly ONE hypothesis per
witness, about one term (two for the multi-segment witness), so the gate's
consistency probe cannot derive ``False`` from it — verified by the audit with
fresh builds: all TEN probes exit 1 with ``simp_all made no progress`` (an earlier
revision said "nine", counting only the single-hypothesis witnesses). The
hypotheses are moreover not merely non-contradictory but TRUE: ``#eval`` on each of
the four conditioned facts — the split of the single-dot name, of the dotless name,
and both splits the multi-segment witness assumes — returns ``true``, so no
witness rests on an unsatisfiable point.

COVERAGE. Ten reject witnesses at TEN distinct input points (verified distinct by
their six-tuples, not by eye), and every one of the six input binders of
``problem_spec_getIndexText`` is varied across them: ``name`` takes a dotless, a
single-dot and a two-dot value (so both arms of the outer match are probed, AND
the rejoining behavior (R) inside the ``some`` arm), ``modname`` both empty and
non-empty, and each of ``isClassmethod`` / ``isProperty`` / ``isStaticmethod`` /
``addModuleNames`` takes both ``true`` and ``false``. Each of the six top-level
clauses (N1, N2, S1, S2, S3, S4) is attacked by some rival, the nested (Q)
conditional is attacked from both of its arms, and (R) is attacked at the only
input shape that can see it.

The variation is MEANINGFUL rather than two spellings of one point: for each
binder there is a pair of cases differing in that binder alone whose rivals have
DIFFERENT error sets — most sharply ``qualify-class-ignoring-flag`` versus
``never-qualify-class``, which are wrong on exactly complementary halves of the
``addModuleNames`` × ``modname`` square, and ``nodot-fallback-results-exchanged``
versus ``nodot-always-names-a-module``, where the second is correct on the whole
sub-domain the first is wrong on.

Each of the ten witnesses was rebuilt from scratch by the audit, twice: against
the rival (all ten exit 0) and against the frozen solution (all ten exit 1, every
one with ``Tactic `decide` proved that the proposition ... is false`` — a plain
EVALUATION of the concrete claim, not a missing identifier, type error, unfolding
failure or timeout). Because a gold-side error is only admissible evidence if it
CHANGES when the claim changes, the audit also ran the forgery pair on all ten:
the same witness with the ``¬`` dropped — i.e. asserting the frozen solution is
CORRECT at that point — PROVES against the frozen solution (exit 0) and FAILS
against the rival (exit 1), the exact mirror of the witness. So gold's exit code
tracks the claim rather than the carrier, and no case is hollow.

SPEC-TOO-WEAK and SPEC-TOO-STRONG were additionally probed by the audit with
implementations this battery does NOT contain. Seven further WRONG impls — the two
named call-like role words exchanged; the fallback's module slot filled from the
member name; the qualification joined without its separator; the qualification
joined in the reverse order; the value-like test promoted above the first
call-like test; the second call-like test promoted above the value-like one; and
the two components of the value-like label exchanged — were each REJECTED, and
each was independently refuted by its own witness (rival exit 0, gold exit 1), so
none of them exposes a hole. Three CORRECT reshapes not carried here (the
commuted (Q) conjuncts, the emptiness tests written with ``String.isEmpty``, and
the hoisted kind-dispatch) were checked to be provable rather than assumed so;
two were closed and verify, which is what tells a tactic artifact from a spec
verdict.

WHAT THIS BATTERY DOES NOT PROBE, stated rather than left implied: the six-clause
postcondition is a total equality on a ``String`` result, so there is no
partiality, no framing and no aliasing dimension to attack, and the termination
dimension is closed by the carrier rather than by the spec (see the DIVERGENCE
note above — a non-terminating rival does not elaborate). The only attack surface
is the VALUE, and these ten rivals partition it by clause; the admissibility case
adds the one direction a value attack cannot see, that the obligation is
satisfiable at a reported-shape input at all.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9698"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Every one lies ENTIRELY inside the `-- impl-start`/`-- impl-end`
# region (or, for `_PROOF_BODY`, inside `-- proof-start`/`-- proof-end`) and is
# unique in the frozen file; `_swap` asserts both, so the manifest breaks loudly
# if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

# The four label-shape returns. The `return ` prefix is what distinguishes each
# from the corresponding `result = ...` text in the (frozen, untouched) spec.
_RET_CLASS = 'return methname ++ "() (" ++ clsname ++ " class method)"'
_RET_VALUE = 'return methname ++ " (" ++ clsname ++ " property)"'
_RET_STATIC = 'return methname ++ "() (" ++ clsname ++ " static method)"'
_RET_PLAIN = 'return methname ++ "() (" ++ clsname ++ " method)"'

# The qualifying-class assembly: the local's initialisation and the conditional
# module-name prefix.
_CLS_INIT = "    let mut clsname := clsname0\n"
_CLS_QUALIFY = (
    '    if addModuleNames && modname != "" then\n'
    '      clsname := modname ++ "." ++ clsname0\n'
)

# The whole dotless-name fallback arm.
_NODOT_ARM = (
    '    if modname != "" then\n'
    '      return name ++ "() (in module " ++ modname ++ ")"\n'
    '    else\n'
    '      return name ++ "()"'
)

# The FULL impl region body and the FULL frozen tactic body, for the positives
# that replace an implementation wholesale and re-prove.
_IMPL_BODY = _BASE.split("-- impl-start\n")[1].split("\n-- impl-end")[0]
_PROOF_BODY = _BASE.split("-- proof-start\n")[1].split("\n-- proof-end")[0]
_PROOF_STMT, _PROOF_TACTICS = _PROOF_BODY.split(":= by\n", 1)
_PROOF_STMT += ":= by\n"


def _reproof(src, tactics):
    """Replace ONLY the tactic body; the `correct_getIndexText` statement (and so
    the obligation the case must discharge) is preserved byte-identically."""
    return _swap(src, _PROOF_TACTICS, tactics)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT
# implementations that MUST verify. If a faithful correct implementation cannot
# satisfy the frozen obligation, the spec is SPEC-TOO-STRONG.
# ===========================================================================

# --- pos-pure-functional: drop the mutable-state shape entirely. --------------
# A pure functional `def` (no `Id.run do`, no `let mut`, no early `return`): the
# qualifying-class component becomes a pure `let` with the conditional inlined,
# and the dotless-name arm tests the module name for EMPTINESS with its two
# results swapped. Same value on every input; the obligation is re-proved for the
# new shape (statement byte-identical, no new declaration).
_POS_PURE_IMPL = (
    "def implementation_getIndexText (name modname : String)\n"
    "    (isClassmethod isProperty isStaticmethod addModuleNames : Bool) : String :=\n"
    "  match rsplitLastDot name with\n"
    "  | none =>\n"
    '    if modname = "" then name ++ "()"\n'
    '    else name ++ "() (in module " ++ modname ++ ")"\n'
    "  | some (clsname0, methname) =>\n"
    "    let clsname :=\n"
    '      if addModuleNames && modname != "" then modname ++ "." ++ clsname0 else clsname0\n'
    '    if isClassmethod then methname ++ "() (" ++ clsname ++ " class method)"\n'
    '    else if isProperty then methname ++ " (" ++ clsname ++ " property)"\n'
    '    else if isStaticmethod then methname ++ "() (" ++ clsname ++ " static method)"\n'
    '    else methname ++ "() (" ++ clsname ++ " method)"'
)
_POS_PURE_TACTICS = (
    "  intro name modname isClassmethod isProperty isStaticmethod addModuleNames\n"
    "  unfold problem_spec_getIndexText implementation_getIndexText\n"
    "  split\n"
    "  · refine ⟨fun hm => if_neg hm, fun hm => if_pos hm⟩\n"
    "  · refine ⟨?_, ?_, ?_, ?_⟩ <;> intros <;> subst_vars <;> rfl"
)
POS_PURE = _reproof(_swap(_BASE, _IMPL_BODY, _POS_PURE_IMPL), _POS_PURE_TACTICS)

# --- pos-match-kinds: dispatch on the three kind flags as a match. ------------
# Replace the `if/else if/else if/else` kind chain with a single `match` on the
# triple of flags, spelling out the four reachable patterns. Mutually exclusive
# and exhaustive, and each arm returns the same label as the corresponding
# branch of the frozen chain, so the value is unchanged on every input. The
# reshaped dispatch desugars differently, so the obligation is re-proved.
_POS_MATCH_IMPL = _swap(
    _IMPL_BODY,
    "    if isClassmethod then\n"
    f"      {_RET_CLASS}\n"
    "    else if isProperty then\n"
    f"      {_RET_VALUE}\n"
    "    else if isStaticmethod then\n"
    f"      {_RET_STATIC}\n"
    "    else\n"
    f"      {_RET_PLAIN}",
    "    match isClassmethod, isProperty, isStaticmethod with\n"
    f"    | true,  _,     _     => {_RET_CLASS}\n"
    f"    | false, true,  _     => {_RET_VALUE}\n"
    f"    | false, false, true  => {_RET_STATIC}\n"
    f"    | false, false, false => {_RET_PLAIN}",
)
_POS_MATCH_TACTICS = (
    "  intro name modname isClassmethod isProperty isStaticmethod addModuleNames\n"
    "  unfold problem_spec_getIndexText implementation_getIndexText\n"
    "  simp only [Id.run, bind, pure]\n"
    "  split\n"
    "  · constructor\n"
    "    · intro hm\n"
    "      simp only [bne_iff_ne]\n"
    "      exact if_pos hm\n"
    "    · intro hm\n"
    "      simp only [bne_iff_ne, hm, ne_eq, not_true_eq_false, if_false]\n"
    "  · refine ⟨?_, ?_, ?_, ?_⟩ <;> intros <;> subst_vars <;>\n"
    '      (by_cases hq : (addModuleNames && modname != "") = true <;>\n'
    "        simp only [hq, if_true, if_false, Bool.false_eq_true])"
)
POS_MATCH = _reproof(_swap(_BASE, _IMPL_BODY, _POS_MATCH_IMPL), _POS_MATCH_TACTICS)

# --- pos-let-qualify: bind the qualification decision to a local. -------------
# The cheapest honest reshape: name the module-qualification decision once and
# branch on the local instead of on the compound expression. The desugared shape
# is close enough that the FROZEN tactic body closes it VERBATIM — the strongest
# form of "the spec did not have to move".
_POS_LET_IMPL = _swap(
    _IMPL_BODY,
    _CLS_INIT + _CLS_QUALIFY,
    '    let qualify := addModuleNames && modname != ""\n'
    "    let mut clsname := clsname0\n"
    "    if qualify then\n"
    '      clsname := modname ++ "." ++ clsname0\n',
)
POS_LET = _swap(_BASE, _IMPL_BODY, _POS_LET_IMPL)

# --- pos-nodot-swap: invert the dotless-name test and swap its two arms. ------
# In the fallback arm, test the module name for EMPTINESS (`==`) rather than
# non-emptiness (`!=`) and exchange the two results. Same value on every input;
# only the executable branch order flips. Re-proved for the flipped arm; the
# splitting arm's tactics are unchanged.
_POS_SWAP_IMPL = _swap(
    _IMPL_BODY,
    _NODOT_ARM,
    '    if modname == "" then\n'
    '      return name ++ "()"\n'
    "    else\n"
    '      return name ++ "() (in module " ++ modname ++ ")"',
)
_POS_SWAP_TACTICS = (
    "  intro name modname isClassmethod isProperty isStaticmethod addModuleNames\n"
    "  unfold problem_spec_getIndexText implementation_getIndexText\n"
    "  simp only [Id.run, bind, pure]\n"
    "  split\n"
    "  · constructor\n"
    "    · intro hm\n"
    "      simp only [beq_iff_eq, hm, if_false]\n"
    "    · intro hm\n"
    "      simp only [beq_iff_eq, hm, if_true]\n"
    "  · refine ⟨?_, ?_, ?_, ?_⟩\n"
    "    · intro h; subst h; simp only [if_true]; split <;> rfl\n"
    "    · intro h1 h2; subst h1; subst h2; simp only; split <;> rfl\n"
    "    · intro h1 h2 h3; subst h1; subst h2; subst h3; simp only; split <;> rfl\n"
    "    · intro h1 h2 h3; subst h1; subst h2; subst h3; simp only; split <;> rfl"
)
POS_SWAP = _reproof(_swap(_BASE, _IMPL_BODY, _POS_SWAP_IMPL), _POS_SWAP_TACTICS)


# ===========================================================================
# ADMISSIBILITY — the obligation is SATISFIABLE at a reported-shape input.
# ===========================================================================
# The frozen obligation is an unconditional `∀` over all six binders, so there is
# no precondition binder to attack directly. On a total carrier the analogue of
# PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly a
# reported-shape input, and this case tests that directly: two ground instances of
# `problem_spec_getIndexText` are discharged BY EVALUATION as `have`s — one at a
# dotted name under the value-like kind (the shape the failing assertion
# exercises), one at a dotless name with a module name (the fallback arm) — and
# only then is the frozen obligation closed VERBATIM. Nothing is assumed: the
# implementation is the frozen one, the `correct_getIndexText` STATEMENT is
# byte-identical, the ground facts are `have`s inside the existing tactic body,
# and no new theorem / lemma / axiom / `sorry` token appears.
#
# Both `have`s close with `split <;> simp_all`, which does NOT need the outer
# split to reduce: it case-splits on the (definite but unevaluated) `match` and
# discharges the reachable arm from the hypothesis `heq` the split introduces.
# That the discharge is not trivial was measured with a sharp negative control —
# see the ADMISSIBILITY note in the module docstring.
_ADMISS_GROUND = (
    '  have _ground_value : problem_spec_getIndexText "Class.meth5" "" '
    "false true false false\n"
    '      (implementation_getIndexText "Class.meth5" "" false true false false)'
    " := by\n"
    "    unfold problem_spec_getIndexText implementation_getIndexText\n"
    "    simp only [Id.run, bind, pure]\n"
    "    split <;> simp_all\n"
    '  have _ground_nodot : problem_spec_getIndexText "meth5" "mod" '
    "false false false false\n"
    '      (implementation_getIndexText "meth5" "mod" false false false false)'
    " := by\n"
    "    unfold problem_spec_getIndexText implementation_getIndexText\n"
    "    simp only [Id.run, bind, pure]\n"
    "    split <;> simp_all\n"
)
ADMISS_GROUND = _reproof(_BASE, _ADMISS_GROUND + _PROOF_TACTICS)


# ===========================================================================
# UNIQUENESS / REJECT rivals
# ===========================================================================

# --- R1: the value-like kind keeps the empty argument list. -------------------
# The port of nagini's `partial-property-keeps-parens`: correct on the three
# call-like kinds and on the dotless-name fallback, wrong on exactly the
# value-like kind. Attacks (S2).
RIVAL_VALUE_PARENS = _swap(
    _BASE, _RET_VALUE,
    'return methname ++ "() (" ++ clsname ++ " property)"')

# --- R2: the discriminator, exactly inverted. ---------------------------------
# The port of nagini's `partial-inverted-discriminator`: the value-like kind
# gains the empty argument list and all three call-like kinds lose it. Correct on
# no splitting kind at all. Attacks (S1), (S2), (S3) and (S4) simultaneously.
_INVERTED = _swap(_BASE, _RET_CLASS,
                  'return methname ++ " (" ++ clsname ++ " class method)"')
_INVERTED = _swap(_INVERTED, _RET_VALUE,
                  'return methname ++ "() (" ++ clsname ++ " property)"')
_INVERTED = _swap(_INVERTED, _RET_STATIC,
                  'return methname ++ " (" ++ clsname ++ " static method)"')
RIVAL_INVERTED = _swap(_INVERTED, _RET_PLAIN,
                       'return methname ++ " (" ++ clsname ++ " method)"')

# --- R3: one call-like kind loses its argument list. --------------------------
# A NEAR-MISS of R2 that agrees with the frozen behavior on strictly more of the
# domain: only the second call-like kind is affected, the other three splitting
# kinds and the fallback are untouched. Attacks (S3) alone, so it gets its own
# witness at the input that isolates that kind.
RIVAL_STATIC_BARE = _swap(
    _BASE, _RET_STATIC,
    'return methname ++ " (" ++ clsname ++ " static method)"')

# --- R4: the default call-like kind loses its argument list. ------------------
# The mirror near-miss: only the kind reached when all three flags are false.
# Attacks (S4) alone.
RIVAL_PLAIN_BARE = _swap(
    _BASE, _RET_PLAIN,
    'return methname ++ " (" ++ clsname ++ " method)"')

# --- R5: qualify the class component on the module name alone. ----------------
# Drop `addModuleNames` from the qualification test, so a present module name is
# prefixed onto the class component whether or not the flag asks for it.
# Attacks (Q) from its FALSE arm (flag off, module name present). This rival
# ignores the `addModuleNames` binder entirely.
RIVAL_QUALIFY_ALWAYS = _swap(
    _BASE, _CLS_QUALIFY,
    '    if modname != "" then\n'
    '      clsname := modname ++ "." ++ clsname0\n')

# --- R6: never qualify the class component. -----------------------------------
# The mirror of R5: the qualification never fires, so the module name is dropped
# even when the flag asks for it and a module name is present. Attacks (Q) from
# its TRUE arm. Also ignores `addModuleNames`, but at the complementary input,
# which is why it does not share R5's witness.
RIVAL_QUALIFY_NEVER = _swap(
    _BASE, _CLS_QUALIFY,
    "    if false then\n"
    '      clsname := modname ++ "." ++ clsname0\n')

# --- R7: the dotless-name fallback, with its two results exchanged. -----------
# In the no-separating-dot arm, return the bare form when a module name IS
# present and the module-qualified form when it is NOT. Attacks (N1) and (N2).
RIVAL_NODOT_SWAPPED = _swap(
    _BASE, _NODOT_ARM,
    '    if modname != "" then\n'
    '      return name ++ "()"\n'
    "    else\n"
    '      return name ++ "() (in module " ++ modname ++ ")"')

# --- R8: name the member in the qualifying-class slot. ------------------------
# The port of nagini's `uniqueness-wrong-class-slice`: substitute the trailing
# member component for the class component everywhere the class component is
# assembled. The label still BEGINS with the member name in every splitting
# clause — nagini's (P2) prefix clause would still hold — so this probes that
# the full-equality clauses are independently load-bearing and are not subsumed
# by "the label starts with the member name". Attacks (S1)–(S4) via (Q).
_WRONG_SLOT = _swap(_BASE, _CLS_INIT, "    let mut clsname := methname\n")
RIVAL_WRONG_SLOT = _swap(
    _WRONG_SLOT, _CLS_QUALIFY,
    '    if addModuleNames && modname != "" then\n'
    '      clsname := modname ++ "." ++ methname\n')

# --- R9: always emit the module-qualified fallback. ---------------------------
# In the no-separating-dot arm, drop the test on the module name and always
# return the module-qualified form — which, with no module name, names an empty
# module. Attacks (N2) alone; a NEAR-MISS of R7 that agrees with the frozen
# behavior whenever a module name IS present, so it gets its own witness at the
# empty-module-name input that isolates the difference.
RIVAL_NODOT_ALWAYS_MOD = _swap(
    _BASE, _NODOT_ARM,
    '    return name ++ "() (in module " ++ modname ++ ")"')

# --- R10: keep only the LAST segment of a multi-segment class component. -------
# Added by audit: every other rival in this battery is refuted at a name with
# exactly ONE dot, at which point the leading class component is a single segment
# and clause (R) — that `rsplitLastDot` REJOINS everything before the final dot —
# is indistinguishable from "take the segment before the dot". So the whole
# battery was blind to an implementation that re-splits the class component and
# keeps only its trailing segment: correct on every single-dot name, wrong on
# every multi-segment one. This rival is exactly that, and its witness is the
# battery's only refutation at a two-dot name.
RIVAL_CLASS_TAIL_ONLY = _swap(
    _BASE, _CLS_INIT,
    "    let mut clsname := clsname0\n"
    "    match rsplitLastDot clsname0 with\n"
    "    | some (_, tail) => clsname := tail\n"
    "    | none => pure ()\n")


# ---------------------------------------------------------------------------
# Witnesses.
#
# `String.splitOn` is defined by well-founded recursion, so the outer split does
# NOT reduce: `decide` gets stuck at the `Decidable` instance, `rfl` reports the
# two sides not definitionally equal, and `simp [String.splitOn]` loops into a
# whnf timeout. So each witness CONDITIONS on the split rather than computing it
# — one hypothesis, about one term — rewrites by it, and then `decide` closes,
# because past the split every component is a string literal and every flag is a
# `Bool` literal. Each was built against the rival (must elaborate) and against
# the frozen solution (must fail); each single hypothesis is satisfiable, so the
# gate's consistency probe cannot derive `False` from it.
# ---------------------------------------------------------------------------

_SPLITS = 'rsplitLastDot "Class.meth5" = some ("Class", "meth5")'
_NOSPLIT = 'rsplitLastDot "meth5" = none'


def _wit(hyp, name, modname, cm, pr, sm, amn):
    flags = f"{cm} {pr} {sm} {amn}"
    return (
        f"example (h : {hyp}) :\n"
        f'    ¬ problem_spec_getIndexText "{name}" "{modname}" {flags}\n'
        f'      (implementation_getIndexText "{name}" "{modname}" {flags}) := by\n'
        "  unfold problem_spec_getIndexText implementation_getIndexText\n"
        "  rw [h]\n"
        "  simp only [Id.run, pure]\n"
        "  decide\n"
    )


# Nine DISTINCT input points. Read down the columns: `name` varies over dotted /
# dotless, `modname` over empty / non-empty, and each of the four flags takes
# both `true` and `false` somewhere, so no binder is held fixed across the
# battery.
_W_VALUE_PARENS = _wit(_SPLITS, "Class.meth5", "", "false", "true", "false", "false")
_W_INVERTED = _wit(_SPLITS, "Class.meth5", "", "true", "false", "false", "false")
_W_STATIC_BARE = _wit(_SPLITS, "Class.meth5", "", "false", "false", "true", "false")
_W_PLAIN_BARE = _wit(_SPLITS, "Class.meth5", "", "false", "false", "false", "false")
_W_QUALIFY_ALWAYS = _wit(_SPLITS, "Class.meth5", "mod", "false", "true", "false", "false")
_W_QUALIFY_NEVER = _wit(_SPLITS, "Class.meth5", "mod", "true", "false", "false", "true")
_W_NODOT_SWAPPED = _wit(_NOSPLIT, "meth5", "mod", "false", "false", "false", "false")
_W_WRONG_SLOT = _wit(_SPLITS, "Class.meth5", "mod", "false", "false", "false", "true")
_W_NODOT_ALWAYS_MOD = _wit(_NOSPLIT, "meth5", "", "false", "false", "false", "false")

# The multi-segment witness needs TWO hypotheses, because the rival splits twice:
# the outer split of the whole name, and the rival's own inner split of the class
# component. Both are facts about the same non-reducing helper at two different
# literal arguments (`#eval` confirms each), so they are jointly satisfiable and
# the gate's consistency probe cannot derive `False` from them — measured.
_W_CLASS_TAIL_ONLY = (
    'example (h : rsplitLastDot "A.B.meth5" = some ("A.B", "meth5"))\n'
    '    (h2 : rsplitLastDot "A.B" = some ("A", "B")) :\n'
    '    ¬ problem_spec_getIndexText "A.B.meth5" "" false false false false\n'
    '      (implementation_getIndexText "A.B.meth5" "" false false false false) := by\n'
    "  unfold problem_spec_getIndexText implementation_getIndexText\n"
    "  rw [h]\n"
    "  simp only [Id.run, pure, h2]\n"
    "  decide\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness)
    # =====================================================================
    {
        "id": "pos-pure-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_PURE,
        "rationale": "structurally different but CORRECT: the mutable-state "
        "shape is dropped entirely for a pure functional `def` — no `Id.run do`, "
        "no `let mut`, no early `return`. The qualifying-class component becomes "
        "a pure `let` with the (Q) conditional inlined, and the "
        "no-separating-dot arm tests the module name for EMPTINESS with its two "
        "results exchanged. Every one of (N1), (N2), (S1)–(S4) is satisfied at "
        "the same value as the frozen implementation on every input, so this MUST "
        "verify; if it cannot, the postcondition is SPEC-TOO-STRONG. Re-proved "
        "for the new shape (the `correct_getIndexText` STATEMENT is byte-"
        "identical, only the tactic body differs; no new theorem, lemma, axiom, "
        "or assumption token).",
    },
    {
        "id": "pos-match-kinds",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_MATCH,
        "rationale": "structurally different but CORRECT: the four-way kind "
        "dispatch is rewritten from a chain of nested conditionals into a single "
        "`match` on the triple of kind flags, spelling out the four reachable "
        "patterns. The patterns are mutually exclusive and exhaustive and each "
        "arm produces the same label as the corresponding branch of the frozen "
        "chain, so (S1)–(S4) hold unchanged and the value is identical on every "
        "input. Must verify (else SPEC-TOO-STRONG). Re-proved because the "
        "reshaped dispatch desugars differently; statement byte-identical, no "
        "new declaration.",
    },
    {
        "id": "pos-let-qualify",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_LET,
        "rationale": "the cheapest honest reshape: bind the module-qualification "
        "decision to a local and branch on the local instead of on the compound "
        "expression. Same value on every input, so (Q) and all four splitting "
        "clauses are untouched, and the desugared shape stays close enough that "
        "the FROZEN tactic body closes it VERBATIM — the strongest available "
        "evidence that the spec did not have to move to accept a reshaped "
        "implementation. Must verify (else SPEC-TOO-STRONG). (An earlier revision "
        "of this rationale also offered this case as the bundle's stand-in for an "
        "admissibility control, on the ground that the obligation is an "
        "unconditional `∀`. That claim is withdrawn: closing the obligation over "
        "the whole binder space says nothing about whether it is SATISFIABLE at a "
        "concrete reported-shape input, which is the admissibility question on a "
        "total carrier. `admiss-ground-reported-shape` now tests that directly.)",
    },
    {
        "id": "pos-nodot-swap",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_SWAP,
        "rationale": "branch reorder confined to the no-separating-dot fallback: "
        "test the module name for emptiness rather than non-emptiness and "
        "exchange the two results. Observationally identical — (N1) and (N2) are "
        "each still produced on exactly their own input — only the executable "
        "branch order flips, which is precisely the reshape that breaks a "
        "form-tuned tactic script without changing any value. Must verify (else "
        "SPEC-TOO-STRONG). Re-proved for the flipped arm; the splitting arm's "
        "tactics are unchanged, statement byte-identical.",
    },

    # =====================================================================
    # ADMISSIBILITY
    # =====================================================================
    {
        "id": "admiss-ground-reported-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS_GROUND,
        "rationale": "the obligation is SATISFIABLE at a reported-shape input. "
        "`correct_getIndexText` is an unconditional `∀` over all six binders, so "
        "there is no precondition binder to attack directly; on this total "
        "carrier the analogue of PRECOND-TOO-STRONG is the obligation being "
        "UNSATISFIABLE at exactly such an input. This case discharges "
        "`problem_spec_getIndexText` BY EVALUATION at two concrete points as "
        "`have`s — a dotted name under the value-like kind (the shape the "
        "failing assertion exercises, where the label must name the member bare) "
        "and a dotless name with a module name (the fallback arm) — and only then "
        "closes the frozen obligation VERBATIM. If either ground instance could "
        "not be discharged, the modeled behavior would be unsatisfiable at a "
        "normal input and the spec would be defective in the PRECOND-TOO-STRONG "
        "direction, which no other case in this battery can see: the positives "
        "reshape the implementation and the rejects refute rivals, but none of "
        "them shows the predicate can be satisfied at a concrete input at all. "
        "Nothing is assumed — the implementation is the frozen one, the statement "
        "is byte-identical, the ground facts are `have`s inside the existing "
        "tactic body, and no new declaration or assumption token appears. The "
        "discharge is not vacuous: the same tactic applied at the same input to a "
        "WRONG label fails in the SPLITTING arm, so it tracks the claimed value "
        "rather than an unreachable branch.",
    },

    # =====================================================================
    # UNIQUENESS / REJECT rivals
    # =====================================================================
    {
        "id": "value-like-keeps-argument-list",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_VALUE_PARENS,
        "refinement": "This is the behavior the failing test was changed to "
        "forbid: the label for a value-like member is shown with an empty "
        "argument list after the member name, as though the member were invoked "
        "rather than accessed. The test asserts the index entry registered for a "
        "value-like class member as an exact string, and that string names the "
        "member bare. A real change carrying this behavior therefore leaves the "
        "asserted entry unchanged from the failing state, so it does NOT resolve "
        "the instance — which makes this rival the sharpest possible probe of "
        "the clause the fix is about.",
        "rationale": "REJECT from (S2): under `¬isClassmethod ∧ isProperty` the "
        "result must be `methname ++ \" (\" ++ clsname ++ \" property)\"`, but "
        "this rival returns the form with the empty argument list. "
        "partial-domain: correct on the three call-like kinds and on the "
        "no-separating-dot fallback, wrong on exactly the value-like kind. "
        "Witness at a dotted name with an empty module name and the value-like "
        "flag set — the shape the failing test exercises; the single hypothesis "
        "is the outer split, which `decide` cannot reduce, and it is "
        "satisfiable.",
        "witness": _W_VALUE_PARENS,
    },
    {
        "id": "argument-list-discriminator-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_INVERTED,
        "refinement": "Inverts which kinds carry the empty argument list: the "
        "value-like member gains it and all three call-like members lose it. "
        "Both the failing test's assertion (a bare value-like label) and the "
        "still-passing assertions for the call-like kinds — which name those "
        "members WITH an empty argument list — would be contradicted, so a real "
        "change carrying this behavior resolves nothing and breaks what already "
        "worked.",
        "rationale": "REJECT from all four splitting clauses at once: the empty "
        "argument list is present exactly when (S2) applies and absent exactly "
        "when (S1)/(S3)/(S4) apply, the opposite of what the spec pins. Correct "
        "on no splitting kind at all. The witness isolates (S1) at the "
        "classmethod flag, so it varies `isClassmethod` to `true` — a value no "
        "other witness in the battery shares with it at an otherwise-identical "
        "point.",
        "witness": _W_INVERTED,
    },
    {
        "id": "one-call-like-kind-loses-argument-list",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_STATIC_BARE,
        "refinement": "A near-miss that touches ONE call-like kind: that kind's "
        "member is named bare, as though it were accessed rather than invoked. "
        "The already-passing assertion for that kind's index entry names the "
        "member WITH an empty argument list, so a real change carrying this "
        "behavior breaks a passing assertion while leaving the failing one "
        "untouched — it does NOT resolve.",
        "rationale": "REJECT from (S3) alone: under `¬isClassmethod ∧ "
        "¬isProperty ∧ isStaticmethod` the result must carry the empty argument "
        "list. This rival agrees with the frozen behavior on strictly more of the "
        "domain than the inverted rival (three splitting kinds and the fallback "
        "are untouched), so it gets its OWN witness, at the input that isolates "
        "that kind — the only point in the battery where `isStaticmethod` is "
        "`true`.",
        "witness": _W_STATIC_BARE,
    },
    {
        "id": "default-kind-loses-argument-list",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_PLAIN_BARE,
        "refinement": "The mirror near-miss, on the kind reached when no kind "
        "flag is set: an ordinary member is named bare. The already-passing "
        "assertion for an ordinary member's index entry names it WITH an empty "
        "argument list, so this breaks a passing assertion and does NOT resolve.",
        "rationale": "REJECT from (S4) alone: with all three kind flags false "
        "the result must carry the empty argument list. Distinct sub-domain from "
        "every other rival — it is the only rival wrong ONLY on the default "
        "kind. (Two witnesses in the battery sit at the default kind with a "
        "dotted name — this one and `member-name-in-class-slot` — but they "
        "differ in the module name and the qualification flag, and they refute "
        "different rivals; the sub-domain claim here is about the RIVAL's error "
        "set, not about exclusive ownership of the input point.)",
        "witness": _W_PLAIN_BARE,
    },
    {
        "id": "qualify-class-ignoring-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_QUALIFY_ALWAYS,
        "refinement": "Drops the flag from the qualification decision, so the "
        "module name is prefixed onto the class component whenever a module name "
        "exists — even when the configuration asks for unqualified names. Every "
        "assertion that pins an index entry naming the class WITHOUT a module "
        "prefix (the default configuration in the tests) would then read a "
        "differently-spelled class, so a real change carrying this behavior "
        "breaks passing assertions and does NOT resolve.",
        "rationale": "REJECT from (Q) at its FALSE arm, inside (S2): with "
        "`addModuleNames = false` and a non-empty module name the class "
        "component must be the trailing class part alone, but this rival "
        "prefixes the module name. It ignores the `addModuleNames` binder "
        "entirely — the battery's demonstration that the spec genuinely depends "
        "on it. Witness at a non-empty module name with the flag OFF.",
        "witness": _W_QUALIFY_ALWAYS,
    },
    {
        "id": "never-qualify-class",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_QUALIFY_NEVER,
        "refinement": "The complementary error: the qualification never fires, "
        "so the module name is dropped from the class component even when the "
        "configuration asks for qualified names and a module name is present. "
        "Any assertion pinning a module-qualified index entry would read an "
        "unqualified class, so a real change carrying this behavior does NOT "
        "resolve.",
        "rationale": "REJECT from (Q) at its TRUE arm, inside (S1): with "
        "`addModuleNames = true` and a non-empty module name the class component "
        "must be `modname ++ \".\" ++ clsname0`. Also ignores `addModuleNames`, "
        "but at the COMPLEMENTARY input to the previous rival — it agrees with "
        "the frozen behavior wherever that one is wrong and vice versa — so it "
        "does not share that witness. This is the only witness in the battery at "
        "`isClassmethod = true` with the flag ON.",
        "witness": _W_QUALIFY_NEVER,
    },
    {
        "id": "nodot-fallback-results-exchanged",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_NODOT_SWAPPED,
        "refinement": "Exchanges the two results of the no-separating-dot "
        "fallback: the bare form is emitted when a module name IS present and "
        "the module-qualified form when it is NOT (naming an empty module). Any "
        "assertion pinning the index entry for a member documented without a "
        "class part would read the wrong one of the two forms, so a real change "
        "carrying this behavior does NOT resolve.",
        "rationale": "REJECT from (N1) and (N2): the fallback's two clauses are "
        "each keyed to the presence of a module name, and this rival satisfies "
        "each on the other's input. This is the only pair of rivals that "
        "attacks the `none` arm of the outer split at all, so it is what "
        "demonstrates the spec's dependence on the SHAPE of `name` rather than "
        "just its content. Witness at a dotless name with a non-empty module "
        "name; the single hypothesis is that the split yields `none`, which "
        "`decide` cannot reduce, and it is satisfiable.",
        "witness": _W_NODOT_SWAPPED,
    },
    {
        "id": "member-name-in-class-slot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_WRONG_SLOT,
        "refinement": "Substitutes the trailing member component for the class "
        "component wherever the class component is assembled, so the label names "
        "the member twice and never names its enclosing class. Every assertion "
        "pinning an index entry that names the real enclosing class would read "
        "the member name there instead, so a real change carrying this behavior "
        "does NOT resolve.",
        "rationale": "REJECT from (S1)–(S4) via (Q): the class component must be "
        "built from the leading class part of the split, not from its trailing "
        "member part. Ported from the nagini sibling's wrong-class-slice rival "
        "for the reason it existed there: the label still BEGINS with the member "
        "name, so a spec that only pinned the label's prefix would accept this — "
        "the case proves the full-equality clauses are independently "
        "load-bearing. Witness at a non-empty module name with the "
        "qualification flag ON and no kind flag set, so it also exercises the "
        "(Q) TRUE arm feeding the default clause.",
        "witness": _W_WRONG_SLOT,
    },
    {
        "id": "nodot-always-names-a-module",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_NODOT_ALWAYS_MOD,
        "refinement": "Drops the module-name test from the no-separating-dot "
        "fallback and always emits the module-qualified form, which with no "
        "module name announces an empty module. An assertion pinning the index "
        "entry for a member documented with neither a class part nor a module "
        "would read a label claiming an unnamed module, so a real change "
        "carrying this behavior does NOT resolve.",
        "rationale": "REJECT from (N2) alone: with an empty module name the "
        "result must be the bare form. This is a NEAR-MISS of the previous "
        "fallback rival — it agrees with the frozen behavior on the whole "
        "sub-domain where a module name IS present, where that one is wrong — so "
        "it carries its own witness, at the empty-module-name input that "
        "isolates the difference. Without that separate point its rationale "
        "would claim a sub-domain the manifest never demonstrates.",
        "witness": _W_NODOT_ALWAYS_MOD,
    },
    {
        "id": "multi-segment-class-keeps-last-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_CLASS_TAIL_ONLY,
        "refinement": "Re-splits the qualifying-class component and keeps only "
        "its final segment, so a member documented under a nested class path is "
        "labelled with the innermost name alone and the enclosing path is "
        "silently discarded. An assertion pinning an index entry that names the "
        "full class path would read only its last segment, so a real change "
        "carrying this behavior does NOT resolve. It is invisible to every "
        "single-dot input, which is what makes it worth carrying.",
        "rationale": "REJECT from (S1)–(S4) via (R): the class component is "
        "whatever precedes the FINAL dot, rejoined with its own interior dots, "
        "and this rival returns only that component's trailing segment. Added by "
        "audit to close a measured blind spot: every other witness in this "
        "battery refutes at a name with exactly one dot, where the leading "
        "component is a single segment and (R) cannot be distinguished from "
        "'take the part before the dot'. This is the battery's only refutation "
        "at a name with TWO dots, so it is what demonstrates the spec depends on "
        "the rejoining and not merely on the split position. Correct on the whole "
        "single-dot sub-domain — a strict near-miss of every other splitting "
        "rival — and its witness therefore has to live at a multi-segment name.",
        "witness": _W_CLASS_TAIL_ONLY,
    },
]
