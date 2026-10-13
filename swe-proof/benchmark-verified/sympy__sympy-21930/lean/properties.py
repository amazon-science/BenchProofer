"""properties.py — G-PBT falsification battery for sympy__sympy-21930 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside an ``-- impl-start`` / ``-- impl-end`` region — and,
for a positive that legitimately re-proves a reshaped impl, inside the matching
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_*`` STATEMENT stays
byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with the obligation closed, no ``sorry``/``admit``/``native_decide``/
new axiom); ``expect="reject"`` passes iff (in scope AND it does NOT verify AND
the case's refutation ``witness`` HOLDS of the rival while FAILING on the frozen
solution).

DEFENDED SURFACE — this bundle models the purely functional core as THREE
independent total renderers (mapping.md: value-level string formatting, identity
on the character sequence). The nagini sibling contracts three byte-identical
renderers over a ``List[int]`` code-point carrier; here the carrier is ``String``
and ``List String`` and each renderer has its own obligation:

  tensorMarkup (sym : String) (upper lower : List String) : String
      result = "{" ++ sym ++ "^{" ++ join upper ++ "}_{" ++ join lower ++ "}}"
  bosonCreatorMarkup (name : String) : String
      result = "{b^\\dagger_{" ++ name ++ "}}"
  fermionCreatorMarkup (name : String) : String
      result = "{a^\\dagger_{" ++ name ++ "}}"

Each postcondition is a single top-level equality that pins the ENTIRE output to
a term built only from the inputs (string concatenation, and the front-recursive
``join`` of the index names). The bundle declares NO ``opaque``/``axiom`` — the
carrier is fully transparent, so ``decide`` computes every clause at a concrete
input and there is no answer key an impl could echo without doing the work. The
uniqueness lane is therefore about whether a rival can render a token that
diverges from the required single-outer-group form on some sub-domain.

The desired behavior each renderer encodes: emit the token as ONE self-contained
group (the inner token enclosed in a single outer brace pair), so that a
following exponent binds to the whole token rather than colliding with the body's
interior superscript. A rival that drops the outer close, opens with the wrong
delimiter, drops the whole wrap, or drops a body character renders a token that
is NOT the required form; its faithful real patch would fail the F2P observables
(which assert the wrapped form on each of the three carriers and on the squared
composite), so it does NOT resolve — a verifying rival would be a true
verify-does-not-imply-resolve break.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION (nagini 3a store, 3b append) — VACUOUS here. The
    nagini sibling makes an input-write attack MANDATORY: the body list is held
    at fractional (read-only) permission and a rival that stores into or appends
    to it is rejected for insufficient permission, independent of any value
    mismatch. Lean is referentially transparent: the inputs are plain immutable
    values, there is no half-permission to violate and no aliasing to exploit, so
    this class has NO expressible instance here. No substitute is fabricated.

  * VACUOUS NON-TERMINATION (nagini 6, the MustTerminate probe) — VACUOUS here,
    and MEASURED so rather than assumed. This backend is vanilla Lean 4 (there is
    no ``loom.semantics.termination`` setting to read: that option belongs to the
    velvet carrier), so a plain ``def`` must already be shown terminating by the
    equation compiler and cannot diverge. The only way to write a diverging
    renderer is ``partial def``, and that was BUILT: the resulting file does not
    verify, but the witness against it cannot refute anything either — a
    ``partial def`` has no equational unfolding, so the refutation fails with
    ``Tactic `unfold` failed to unfold `implementation_...``` rather than by
    deciding the claim. There is no discriminating witness to ship, so the class
    is vacuous here (nothing that verifies, nothing refutable), not a spec hole.
    (On velvet under partial semantics the same class WOULD be a known spec hole —
    the corpus-wide termination-semantics finding.)

  * PARTIAL-DOMAIN / PREPATCH (nagini 4, 4b, 4c, 5) — APPLIES, load-bearing.
    Ported below across the three carriers so every input binder of every
    obligation is varied:
      - PREPATCH bare body, NO braces (nagini 5) — the exact pre-fix behaviour;
      - DROP the closing outer brace (nagini 4);
      - WRONG opening delimiter (nagini 4c);
      - DROP the last body character via a short loop (nagini 4b) — the
        length-class attack, which naturally varies the ``upper`` list binder;
      - SWAPPED index blocks and an EMPTY-upper-block regression (both added by
        audit): the first attacks which index list feeds which block — a clause
        every delimiter rival leaves untouched — and the second attacks the one
        sub-domain (empty ``upper``) on which the drop-last rival is CORRECT by
        construction, so neither was covered before.

  * UNGROUNDED-ORACLE ECHO — N/A. Every clause equates the result to a term
    grounded in the inputs; the honest cheapest-correct impls are the POSITIVE
    CONTROLS below.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an impl — the frozen script (``rfl`` / a ``forIn`` induction tuned to
the frozen form) breaks on any reshape — so a rejection alone attributes nothing
to the spec. Every ``expect="reject"`` case therefore carries a Lean snippet
stating the relevant spec predicate directly at a ``decide``-able concrete input;
each was built and confirmed to HOLD of its rival and to FAIL on the frozen
solution (so it discriminates rather than asserting a tautology). Inputs are
concrete string / list-of-string literals — the carrier is transparent, so no
conditioning on an opaque term is needed and every witness closes by ``decide``.

BINDER + OBLIGATION COVERAGE (pbt_coverage.py is advisory and does not gate):
  * correct_tensorMarkup — defended by a reproven `foldl` positive (not defeq to
    the frozen loop) and an F2P-ground admissibility positive; attacked by five
    rivals whose witnesses probe distinct (sym, upper, lower) points, so all three
    input binders vary, INCLUDING the empty `upper` list and an asymmetric
    upper/lower pair. Two clauses are attacked that the delimiter rivals cannot
    reach: which index list feeds which block, and the empty-index-block
    sub-domain.
  * correct_bosonCreatorMarkup — defended by an inner-then-wrap reshape positive
    (not defeq); attacked by two rivals at name="i" and name="q" (the single
    binder varies).
  * correct_fermionCreatorMarkup — defended by a `String.join` reshape positive
    (not defeq); attacked by two rivals at name="a" and name="p".

Every positive's impl was checked NOT to be definitionally equal to the frozen
impl (`example : frozenImpl = variantImpl := rfl` must FAIL), because a defeq
"reshape" passes the gate while testing nothing: the frozen tactic script closes
it for free. Three earlier candidates — a loop reorder, a `let`-bound return, and
dropping the `Id.run do` wrapper — were rejected for exactly that reason after
the probe elaborated on each.

AXIOM lane: DROPPED. The axiom lane is G-AX's job; this gate ignores it. (The
nagini sibling's AXIOM_TESTS re-ran the deep-model conformance probe; here
mapping.md records the only sub-operation — the empty-string join of names — as a
deep-model reference validated by G-AX, and there is no consumed-callee axiom for
the PBT lane to re-discharge.)
"""
from pathlib import Path

INSTANCE = "sympy__sympy-21930"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (each unique inside Solution.lean; uniqueness verified by
# _swap at load). Each lies ENTIRELY inside the region it means to edit.
# ---------------------------------------------------------------------------

# tensor impl — the FULL impl-region body (so a reshape lands wholly inside it)
_TENSOR_IMPL = (
    "def implementation_tensorMarkup\n"
    "    (sym : String) (upper lower : List String) : String := Id.run do\n"
    "  let mut up := \"\"\n"
    "  for i in upper do\n"
    "    up := up ++ i\n"
    "  let mut lo := \"\"\n"
    "  for i in lower do\n"
    "    lo := lo ++ i\n"
    "  return \"{\" ++ sym ++ \"^{\" ++ up ++ \"}_{\" ++ lo ++ \"}}\"\n"
)
# tensor: the single final assembly line, unique in the file
_TENSOR_RET = (
    "  return \"{\" ++ sym ++ \"^{\" ++ up ++ \"}_{\" ++ lo ++ \"}}\""
)
# tensor: the upper-index loop head, unique in the file
_TENSOR_UP_LOOP = "  for i in upper do"

# boson impl return line (distinct from the spec's `result = ...` line)
_BOSON_RET = "  return \"{b^\\\\dagger_{\" ++ name ++ \"}}\""
# fermion impl return line
_FERMION_RET = "  return \"{a^\\\\dagger_{\" ++ name ++ \"}}\""

# tensor frozen proof body (the tactic body only). A reproven positive replaces
# it wholesale; the theorem STATEMENT above it is never touched.
_TENSOR_PROOF_BODY = (
    "  intro sym upper lower\n"
    "  unfold problem_spec_tensorMarkup implementation_tensorMarkup\n"
    "  simp only [Id.run, bind]\n"
    "  rw [tensorMarkup_loop_eq, tensorMarkup_loop_eq]\n"
    "  simp only [String.empty_append, pure, String.append_assoc]\n"
)
# boson / fermion frozen proof bodies, each anchored on the preceding statement
# tail so the two `intro name; rfl` scripts stay distinguishable.
_BOSON_PROOF_TAIL = (
    "        (implementation_bosonCreatorMarkup name) := by\n"
    "  intro name; rfl\n"
)
_FERMION_PROOF_TAIL = (
    "        (implementation_fermionCreatorMarkup name) := by\n"
    "  intro name; rfl\n"
)

# tensor frozen proof body (only the tactic body; the theorem STATEMENT is not
# touched). Used by the loop-reorder positive (proof carried verbatim) and by
# the admissibility positive (a `have` inserted at the head).
_TENSOR_PROOF_INTRO = "  intro sym upper lower\n"

for _a in (_TENSOR_IMPL, _TENSOR_RET, _TENSOR_UP_LOOP, _BOSON_RET, _FERMION_RET,
           _TENSOR_PROOF_INTRO, _TENSOR_PROOF_BODY, _BOSON_PROOF_TAIL,
           _FERMION_PROOF_TAIL):
    assert _BASE.count(_a) == 1, f"anchor drifted / not unique: {_a!r}"


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify; else the postcondition is over-fit to the impl FORM
# (SPEC-TOO-STRONG). Each keeps the theorem STATEMENT byte-identical and adds no
# helper lemma, axiom, or assumption token.
# ---------------------------------------------------------------------------

# AUDIT NOTE (why these three positives are shaped the way they are). A positive
# whose impl is DEFINITIONALLY EQUAL to the frozen one passes honestly while
# testing nothing: the frozen tactic script closes it because the elaborator
# never sees a different term. That was measured on this carrier, not assumed —
# `example : frozenImpl = reorderImpl := rfl` and the two analogous probes for
# the dagger renderers all ELABORATED (exit 0), i.e. a loop reorder, a
# `let`-bound return, and dropping the `Id.run do` wrapper are each defeq to the
# frozen impl here. So all three positives now RE-ASSOCIATE the concatenation
# (build the inner token first, then wrap it), which is NOT defeq — the same
# `rfl` probe fails with `Type mismatch` on each — and each carries its own
# reproven tactic body inside the `proof` region. The frozen script does NOT
# close any of them, so verifying is real evidence the spec admits a genuinely
# different impl FORM.

# tensor: no imperative accumulator loop at all — a `List.foldl` over each index
# block, reassociated. Not defeq to the frozen `forIn` form (`rfl` probe: Type
# mismatch), so the frozen `tensorMarkup_loop_eq` rewrite does not apply; the
# case reproves the obligation with its own `foldl` accumulation lemma stated as
# a `have` inside the existing tactic body.
_POS_TENSOR = _swap(
    _swap(
        _BASE, _TENSOR_IMPL,
        "def implementation_tensorMarkup\n"
        "    (sym : String) (upper lower : List String) : String :=\n"
        "  \"{\" ++ sym ++ \"^{\" ++ upper.foldl (fun a s => a ++ s) \"\" ++ \"}_{\"\n"
        "    ++ lower.foldl (fun a s => a ++ s) \"\" ++ \"}}\"\n",
    ),
    _TENSOR_PROOF_BODY,
    "  intro sym upper lower\n"
    "  have hfold : ∀ (xs : List String) (init : String),\n"
    "      xs.foldl (fun a s => a ++ s) init = init ++ joinNames xs := by\n"
    "    intro xs\n"
    "    induction xs with\n"
    "    | nil => intro init; simp [joinNames]\n"
    "    | cons a as ih =>\n"
    "      intro init\n"
    "      simp only [List.foldl_cons, ih, joinNames, String.append_assoc]\n"
    "  unfold problem_spec_tensorMarkup implementation_tensorMarkup\n"
    "  rw [hfold, hfold]\n"
    "  simp only [String.empty_append]\n",
)

# boson: build the INNER token first and wrap it in a separate step, so the
# concatenation is reassociated relative to the frozen single-expression form.
# Not defeq (`rfl` probe: Type mismatch) and `intro name; rfl` does NOT close it,
# so the case supplies its own tactic body.
_POS_BOSON = _swap(
    _swap(
        _BASE, _BOSON_RET,
        "  let inner := \"b^\\\\dagger_{\" ++ name ++ \"}\"\n"
        "  return \"{\" ++ inner ++ \"}\"",
    ),
    _BOSON_PROOF_TAIL,
    "        (implementation_bosonCreatorMarkup name) := by\n"
    "  intro name\n"
    "  unfold problem_spec_bosonCreatorMarkup implementation_bosonCreatorMarkup\n"
    "  simp only [Id.run, pure, String.append_assoc]\n"
    "  have h1 : (\"{\" : String) ++ \"b^\\\\dagger_{\" = \"{b^\\\\dagger_{\" := by decide\n"
    "  have h2 : (\"}\" : String) ++ \"}\" = \"}}\" := by decide\n"
    "  rw [← h1, ← h2, String.append_assoc]\n",
)

# fermion: assemble the token from a LIST of pieces via `String.join` — no
# `Id.run do`, no direct `++` chain. Not defeq (`rfl` probe: Type mismatch);
# `intro name; rfl` does NOT close it, so the case reproves the obligation by
# unfolding the fold and reassociating.
_POS_FERMION = _swap(
    _swap(
        _BASE,
        "def implementation_fermionCreatorMarkup (name : String) : String := Id.run do\n"
        "  return \"{a^\\\\dagger_{\" ++ name ++ \"}}\"",
        "def implementation_fermionCreatorMarkup (name : String) : String :=\n"
        "  String.join [\"{\", \"a^\\\\dagger_{\", name, \"}}\"]",
    ),
    _FERMION_PROOF_TAIL,
    "        (implementation_fermionCreatorMarkup name) := by\n"
    "  intro name\n"
    "  unfold problem_spec_fermionCreatorMarkup implementation_fermionCreatorMarkup\n"
    "  simp only [String.join, List.foldl, String.append_assoc, String.empty_append]\n"
    "  have h1 : (\"{\" : String) ++ \"a^\\\\dagger_{\" = \"{a^\\\\dagger_{\" := by decide\n"
    "  rw [← String.append_assoc, h1]\n",
)

# ADMISSIBILITY — discharge the tensor obligation at the F2P ground input
# (sym="t", upper=["a","b"], lower=["i","j"] — exactly the `t^{ab}_{ij}` witness),
# where the spec demands the wrapped `{t^{ab}_{ij}}`, by `decide`; then close the
# frozen obligation verbatim. A `have` inserted at the head of the existing tactic
# body (theorem STATEMENT byte-identical; no new declaration/axiom/`sorry`).
_ADMISS_TENSOR = _swap(
    _BASE, _TENSOR_PROOF_INTRO,
    "  have _ground : problem_spec_tensorMarkup \"t\" [\"a\", \"b\"] [\"i\", \"j\"]\n"
    "      (implementation_tensorMarkup \"t\" [\"a\", \"b\"] [\"i\", \"j\"]) := by\n"
    "    unfold problem_spec_tensorMarkup implementation_tensorMarkup\n"
    "    decide\n"
    "  intro sym upper lower\n",
)


# ---------------------------------------------------------------------------
# UNIQUENESS rivals (expect="reject"). Each edits ONE impl region; the frozen
# proof for that renderer no longer closes against the reshaped impl, so the
# build fails — and each case ships a discriminating witness (built to HOLD of
# the rival and FAIL on gold) so the rejection is attributed to the SPEC.
# ---------------------------------------------------------------------------

# tensor PREPATCH — drop the whole outer brace pair (the pre-fix bare token).
# AUDIT REPAIR: the ported form dropped the outer braces AND the inner token's
# own trailing `}` (`... ++ lo`), so the rival was a two-character divergence and
# the case's own prose ("the inner token is emitted bare") did not describe it.
# Restored to the genuine unwrapped inner token, `sym^{up}_{lo}`, which is the
# form the pre-fix behaviour renders; rebuilt and reconfirmed to reject with the
# same discriminating witness.
_REJ_TENSOR_PREPATCH = _swap(
    _BASE, _TENSOR_RET,
    "  return sym ++ \"^{\" ++ up ++ \"}_{\" ++ lo ++ \"}\"",
)

# tensor WRONG-OPEN — open the group with `^` instead of `{` (nagini 4c).
_REJ_TENSOR_WRONGOPEN = _swap(
    _BASE, _TENSOR_RET,
    "  return \"^\" ++ sym ++ \"^{\" ++ up ++ \"}_{\" ++ lo ++ \"}}\"",
)

# tensor DROP-LAST-UPPER — the upper-index loop stops one element early, so the
# last upper index name is dropped (nagini 4b, length class). Correct on empty
# `upper`, wrong on any non-empty `upper`; naturally varies the `upper` binder.
_REJ_TENSOR_DROPLAST = _swap(
    _BASE, _TENSOR_UP_LOOP,
    "  for i in upper.dropLast do",
)

# boson PREPATCH — bare token, no outer braces (nagini 5).
_REJ_BOSON_PREPATCH = _swap(
    _BASE, _BOSON_RET,
    "  return \"b^\\\\dagger_{\" ++ name ++ \"}\"",
)

# boson DROP-CLOSE — omit the trailing outer close brace (nagini 4).
_REJ_BOSON_DROPCLOSE = _swap(
    _BASE, _BOSON_RET,
    "  return \"{b^\\\\dagger_{\" ++ name ++ \"}\"",
)

# fermion PREPATCH — bare token, no outer braces (nagini 5).
_REJ_FERMION_PREPATCH = _swap(
    _BASE, _FERMION_RET,
    "  return \"a^\\\\dagger_{\" ++ name ++ \"}\"",
)

# fermion WRONG-OPEN — open the group with `^` instead of `{` (nagini 4c).
_REJ_FERMION_WRONGOPEN = _swap(
    _BASE, _FERMION_RET,
    "  return \"^a^\\\\dagger_{\" ++ name ++ \"}}\"",
)

# AUDIT ADDITION — tensor SWAPPED INDEX BLOCKS. The wrap is perfectly correct and
# every body character is present; only the two index blocks are exchanged, so
# the upper block renders the lower names and vice versa. This attacks a clause
# the delimiter rivals leave alone (which index list feeds which block) and it is
# correct on the whole sub-domain where the two blocks join to the same text,
# including every symmetric input — a rival that no brace-shaped attack reaches.
_REJ_TENSOR_SWAP_BLOCKS = _swap(
    _BASE, _TENSOR_IMPL,
    "def implementation_tensorMarkup\n"
    "    (sym : String) (upper lower : List String) : String := Id.run do\n"
    "  let mut up := \"\"\n"
    "  for i in lower do\n"
    "    up := up ++ i\n"
    "  let mut lo := \"\"\n"
    "  for i in upper do\n"
    "    lo := lo ++ i\n"
    "  return \"{\" ++ sym ++ \"^{\" ++ up ++ \"}_{\" ++ lo ++ \"}}\"\n",
)

# AUDIT ADDITION — tensor EMPTY-UPPER-BLOCK regression. Renders the fully wrapped
# token on every input EXCEPT when the upper index block is empty, where it falls
# back to the unwrapped pre-fix form. Every other rival in the battery is wrong on
# a whole binder's worth of inputs; this one is correct on all of them and wrong
# only on the empty-`upper` sub-domain, which is exactly the sub-domain the
# drop-last rival is CORRECT on. Without it the spec's coverage of the empty index
# block rests on no case at all.
_REJ_TENSOR_EMPTY_UPPER = _swap(
    _BASE, _TENSOR_IMPL,
    "def implementation_tensorMarkup\n"
    "    (sym : String) (upper lower : List String) : String := Id.run do\n"
    "  let mut up := \"\"\n"
    "  for i in upper do\n"
    "    up := up ++ i\n"
    "  let mut lo := \"\"\n"
    "  for i in lower do\n"
    "    lo := lo ++ i\n"
    "  if upper.isEmpty then\n"
    "    return sym ++ \"^{\" ++ up ++ \"}_{\" ++ lo ++ \"}\"\n"
    "  return \"{\" ++ sym ++ \"^{\" ++ up ++ \"}_{\" ++ lo ++ \"}}\"\n",
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — MUST verify.
    # =====================================================================
    {
        "id": "pos-tensor-foldl-reassoc",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_TENSOR,
        "rationale": (
            "a correct reshape of the indexed-symbol renderer that carries NO "
            "imperative accumulator loop: each index block is a `List.foldl` "
            "concatenation, and the assembly is reassociated. Same value on every "
            "(sym, upper, lower), but NOT definitionally equal to the frozen "
            "`forIn` form — `example : frozenImpl = foldlImpl := rfl` fails with a "
            "type mismatch — so the frozen `tensorMarkup_loop_eq` rewrite does not "
            "apply and the case reproves the obligation from its own `foldl` "
            "accumulation lemma (a `have` inside the existing tactic body; the "
            "theorem STATEMENT is byte-identical, no new top-level "
            "declaration/axiom/`sorry`). Verifying is therefore evidence the spec "
            "admits a different impl FORM; if it could not verify => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-boson-inner-then-wrap",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BOSON,
        "rationale": (
            "a correct reshape of the bosonic renderer that builds the INNER token "
            "first and wraps it in a separate step, reassociating the concatenation "
            "relative to the frozen single-expression form. Same value on every "
            "name, and NOT definitionally equal to the frozen impl (the `rfl` probe "
            "fails with a type mismatch), so the frozen `intro name; rfl` does NOT "
            "close it — the case supplies its own tactic body, keeping the theorem "
            "STATEMENT byte-identical. Must verify; else the boson spec is over-fit "
            "to the exact concatenation FORM (SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "pos-fermion-join-pieces",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FERMION,
        "rationale": (
            "a correct reshape of the fermionic renderer that assembles the token "
            "from a LIST of pieces via `String.join` — no imperative wrapper and no "
            "direct `++` chain. Same value on every name, and NOT definitionally "
            "equal to the frozen impl (the `rfl` probe fails with a type mismatch), "
            "so the frozen `intro name; rfl` does NOT close it; the case reproves "
            "the obligation by unfolding the fold and reassociating, with the "
            "theorem STATEMENT byte-identical. Must verify; else the fermion spec is "
            "over-fit to the direct-concatenation FORM (SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "admiss-tensor-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_TENSOR,
        "rationale": (
            "the tensor obligation is discharged at the F2P ground input (sym=\"t\", "
            "upper=[\"a\",\"b\"], lower=[\"i\",\"j\"] — exactly the `t^{ab}_{ij}` "
            "witness), where the spec demands the single-outer-group form "
            "\"{t^{ab}_{ij}}\", by `decide`; then the frozen obligation is closed "
            "verbatim. Verifies (else the spec is unsatisfiable at the normal F2P "
            "input — the analogue of PRECOND-TOO-STRONG). Nothing is assumed: the "
            "theorem STATEMENT is byte-identical, the ground instance is a `have` "
            "inserted at the head of the existing tactic body, and no new "
            "declaration/axiom/`sorry` is introduced. (The frozen theorems carry no "
            "precondition hypothesis — the behavior is total — so nagini's "
            "precondition-admission probe has no binder to attack; discharging the "
            "spec at the F2P ground input is the honest analogue.)"
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — MUST reject.
    # =====================================================================
    {
        "id": "weak-tensor-prepatch-no-braces",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_TENSOR_PREPATCH,
        "refinement": (
            "the pre-fix behaviour of the indexed-symbol renderer: the inner token "
            "is emitted with NO outer brace pair. A faithful patch that leaves the "
            "token unwrapped renders the bare form, which is not the wrapped form "
            "the F2P observable asserts and, when the token is squared, produces the "
            "ill-formed double superscript the issue is about — so it does NOT "
            "resolve. This is the precise verify-does-not-resolve discriminator."
        ),
        "rationale": (
            "REJECT from the tensor postcondition equality: at sym=\"g\", "
            "upper=[\"p\"], lower=[\"q\"] the spec demands \"{g^{p}_{q}}\" but the "
            "rival returns the bare inner token \"g^{p}_{q}\" — every body character "
            "present, only the outer brace pair absent, so the divergence is exactly "
            "the wrap and nothing else. Refuted with sym/upper/lower at a point "
            "distinct from the other two tensor rivals."
        ),
        "witness": (
            "-- Refuted at (sym=\"g\", upper=[\"p\"], lower=[\"q\"]): the inner token\n"
            "-- must be enclosed in a single outer brace pair, but the pre-patch impl\n"
            "-- emits it bare.\n"
            "example : ¬ problem_spec_tensorMarkup \"g\" [\"p\"] [\"q\"]\n"
            "    (implementation_tensorMarkup \"g\" [\"p\"] [\"q\"]) := by\n"
            "  unfold problem_spec_tensorMarkup implementation_tensorMarkup\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-tensor-wrong-open-delimiter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_TENSOR_WRONGOPEN,
        "refinement": (
            "the group is opened with `^` instead of the outer brace. A faithful "
            "patch that emitted a stray superscript marker instead of the opening "
            "brace renders a token that both fails the wrapped-form F2P observable "
            "and is itself a malformed double-superscript — so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the tensor postcondition equality: at sym=\"t\", "
            "upper=[\"a\",\"b\"], lower=[\"i\",\"j\"] the spec demands "
            "\"{t^{ab}_{ij}}\" (first character the outer open brace) but the rival "
            "opens with `^`. Single-character divergence at index 0; varies sym off "
            "the value the prepatch rival uses."
        ),
        "witness": (
            "-- Refuted at (sym=\"t\", upper=[\"a\",\"b\"], lower=[\"i\",\"j\"]): the\n"
            "-- token must open with the outer brace, but the rival opens with `^`.\n"
            "example : ¬ problem_spec_tensorMarkup \"t\" [\"a\", \"b\"] [\"i\", \"j\"]\n"
            "    (implementation_tensorMarkup \"t\" [\"a\", \"b\"] [\"i\", \"j\"]) := by\n"
            "  unfold problem_spec_tensorMarkup implementation_tensorMarkup\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-tensor-drop-last-upper-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_TENSOR_DROPLAST,
        "refinement": (
            "the upper-index accumulator loop stops one element early, so the last "
            "upper index name is dropped from the rendered token. It is correct on "
            "an empty upper index block but wrong on every operator with a non-empty "
            "upper block — a truncated index rendering that fails the F2P token "
            "equality, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the tensor postcondition equality: at sym=\"v\", "
            "upper=[\"a\",\"b\"], lower=[\"i\"] the spec demands \"{v^{ab}_{i}}\" but "
            "the short loop drops the last upper name, yielding \"{v^{a}_{i}}\". "
            "Length-class / last-element attack that varies the `upper` binder off "
            "the singleton the prepatch rival uses."
        ),
        "witness": (
            "-- Refuted at (sym=\"v\", upper=[\"a\",\"b\"], lower=[\"i\"]): the upper\n"
            "-- index block is the in-order concatenation of ALL its names, but the\n"
            "-- short loop drops the last one.\n"
            "example : ¬ problem_spec_tensorMarkup \"v\" [\"a\", \"b\"] [\"i\"]\n"
            "    (implementation_tensorMarkup \"v\" [\"a\", \"b\"] [\"i\"]) := by\n"
            "  unfold problem_spec_tensorMarkup implementation_tensorMarkup\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-boson-prepatch-no-braces",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_BOSON_PREPATCH,
        "refinement": (
            "the pre-fix behaviour of the bosonic renderer: the token is emitted "
            "with NO outer brace pair. A faithful patch leaving it unwrapped renders "
            "the bare form (and the ill-formed double superscript when squared), "
            "failing the F2P observable — so it does NOT resolve. This is the exact "
            "pre-fix behaviour the bundle exists to sense."
        ),
        "rationale": (
            "REJECT from the boson postcondition equality: at name=\"i\" the spec "
            "demands \"{b^\\dagger_{i}}\" but the rival returns \"b^\\dagger_{i}\" "
            "(no outer braces). Attacks the boson obligation at name=\"i\"."
        ),
        "witness": (
            "-- Refuted at name=\"i\": the bosonic token must be enclosed in a single\n"
            "-- outer brace pair, but the pre-patch impl emits it bare.\n"
            "example : ¬ problem_spec_bosonCreatorMarkup \"i\"\n"
            "    (implementation_bosonCreatorMarkup \"i\") := by\n"
            "  unfold problem_spec_bosonCreatorMarkup implementation_bosonCreatorMarkup\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-boson-drop-closing-brace",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_BOSON_DROPCLOSE,
        "refinement": (
            "the bosonic renderer opens the outer group but omits the trailing close "
            "brace, so the token is left unbalanced. A faithful patch that wrapped "
            "the token without closing it renders a malformed token that fails the "
            "F2P observable and does not make a following exponent bind to the whole "
            "token — so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the boson postcondition equality: at name=\"q\" the spec "
            "demands \"{b^\\dagger_{q}}\" but the rival returns \"{b^\\dagger_{q}\" "
            "(missing the outer close). Attacks the boson obligation at name=\"q\", "
            "varying the single binder off the prepatch rival's \"i\"."
        ),
        "witness": (
            "-- Refuted at name=\"q\": the outer brace pair must be balanced, but the\n"
            "-- rival omits the closing brace.\n"
            "example : ¬ problem_spec_bosonCreatorMarkup \"q\"\n"
            "    (implementation_bosonCreatorMarkup \"q\") := by\n"
            "  unfold problem_spec_bosonCreatorMarkup implementation_bosonCreatorMarkup\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-fermion-prepatch-no-braces",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_FERMION_PREPATCH,
        "refinement": (
            "the pre-fix behaviour of the fermionic renderer: the token is emitted "
            "with NO outer brace pair. A faithful patch leaving it unwrapped renders "
            "the bare form (and the ill-formed double superscript when squared), "
            "failing the F2P observable — so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the fermion postcondition equality: at name=\"a\" the spec "
            "demands \"{a^\\dagger_{a}}\" but the rival returns \"a^\\dagger_{a}\" "
            "(no outer braces). Attacks the fermion obligation at name=\"a\"."
        ),
        "witness": (
            "-- Refuted at name=\"a\": the fermionic token must be enclosed in a\n"
            "-- single outer brace pair, but the pre-patch impl emits it bare.\n"
            "example : ¬ problem_spec_fermionCreatorMarkup \"a\"\n"
            "    (implementation_fermionCreatorMarkup \"a\") := by\n"
            "  unfold problem_spec_fermionCreatorMarkup implementation_fermionCreatorMarkup\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-fermion-wrong-open-delimiter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_FERMION_WRONGOPEN,
        "refinement": (
            "the fermionic group is opened with `^` instead of the outer brace. A "
            "faithful patch emitting a stray superscript marker instead of the "
            "opening brace renders a token that fails the wrapped-form F2P observable "
            "and is itself a malformed double-superscript — so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the fermion postcondition equality: at name=\"p\" the spec "
            "demands \"{a^\\dagger_{p}}\" (first character the outer open brace) but "
            "the rival opens with `^`. Attacks the fermion obligation at name=\"p\", "
            "varying the single binder off the prepatch rival's \"a\"."
        ),
        "witness": (
            "-- Refuted at name=\"p\": the token must open with the outer brace, but\n"
            "-- the rival opens with `^`.\n"
            "example : ¬ problem_spec_fermionCreatorMarkup \"p\"\n"
            "    (implementation_fermionCreatorMarkup \"p\") := by\n"
            "  unfold problem_spec_fermionCreatorMarkup implementation_fermionCreatorMarkup\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-tensor-swapped-index-blocks",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_TENSOR_SWAP_BLOCKS,
        "refinement": (
            "the two index blocks are exchanged: the upper block renders the lower "
            "names and the lower block renders the upper names. The outer wrap is "
            "correct and no character is lost — only the routing of the two index "
            "lists into the two blocks is wrong. A faithful patch that crossed the "
            "two index sequences would render a token whose indices sit in the wrong "
            "position, which is not the token the F2P observable on the indexed "
            "carrier asserts, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the tensor postcondition equality, on a clause NO other "
            "rival in this battery touches: every brace-shaped rival attacks the "
            "delimiters, so each of them would still pass a spec that got the block "
            "ROUTING wrong. At sym=\"t\", upper=[\"a\"], lower=[\"b\"] the spec "
            "demands \"{t^{a}_{b}}\" but the rival renders \"{t^{b}_{a}}\". Note the "
            "rival is CORRECT wherever the two blocks join to the same text (all "
            "symmetric inputs), so it is a genuine partial-domain attack and the "
            "witness has to pick an asymmetric point — this one does."
        ),
        "witness": (
            "-- Refuted at (sym=\"t\", upper=[\"a\"], lower=[\"b\"]): the upper block\n"
            "-- must render the UPPER names and the lower block the LOWER ones, but\n"
            "-- the rival exchanges them.\n"
            "example : ¬ problem_spec_tensorMarkup \"t\" [\"a\"] [\"b\"]\n"
            "    (implementation_tensorMarkup \"t\" [\"a\"] [\"b\"]) := by\n"
            "  unfold problem_spec_tensorMarkup implementation_tensorMarkup\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-tensor-empty-upper-block-unwrapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_TENSOR_EMPTY_UPPER,
        "refinement": (
            "the renderer emits the correctly wrapped token on every input EXCEPT "
            "when the upper index block is empty, where it falls back to the "
            "unwrapped pre-fix form. A faithful patch that special-cased the "
            "no-upper-index shape and left it unwrapped renders the bare token for "
            "those operators — the same ill-formed composite when a further exponent "
            "is appended — so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the tensor postcondition equality on the EMPTY-upper "
            "sub-domain, which no other case in this battery reaches: the drop-last "
            "rival is CORRECT there by construction, and every delimiter rival "
            "diverges uniformly, so a spec that admitted an empty-block exception "
            "would be caught by nothing else here. At sym=\"t\", upper=[], "
            "lower=[\"i\"] the spec demands \"{t^{}_{i}}\" but the rival returns the "
            "bare \"t^{}_{i}\". Varies the `upper` binder to the empty list — the one "
            "value the rest of the battery never puts there."
        ),
        "witness": (
            "-- Refuted at (sym=\"t\", upper=[], lower=[\"i\"]): the wrap is required\n"
            "-- for EVERY input including an empty upper index block, but the rival\n"
            "-- drops it exactly there.\n"
            "example : ¬ problem_spec_tensorMarkup \"t\" [] [\"i\"]\n"
            "    (implementation_tensorMarkup \"t\" [] [\"i\"]) := by\n"
            "  unfold problem_spec_tensorMarkup implementation_tensorMarkup\n"
            "  decide\n"
        ),
    },
]


# Axiom lane dropped: the axiom lane is G-AX's job; this gate ignores it. The
# only sub-operation (the empty-string join of index names) is a deep-model
# reference validated against the real join by G-AX, not a consumed-callee axiom
# the PBT lane could re-discharge.
AXIOM_TESTS = []
