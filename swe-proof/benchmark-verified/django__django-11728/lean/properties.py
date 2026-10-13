"""properties.py — G-PBT falsification battery for django__django-11728 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or discharges
a ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a character sequence):

  findGroupEnd (cs : List Char) : Option Nat
      -- scanning `cs` from a single already-open bracket (depth 1), report the
      -- FIRST index at which the running depth returns to zero, or `none`.
      result = some i  ⟺  i < cs.length
                          ∧ depthAfter (cs.take (i+1)) = 0            -- closes here
                          ∧ ∀ j < i, depthAfter (cs.take (j+1)) ≠ 0   -- FIRST such i
      result = none    ⟺  ∀ i < cs.length, depthAfter (cs.take (i+1)) ≠ 0

  ``depthAfter`` is a GROUNDED fold of the input (fully spelled out via
  ``stepBracket``: an unescaped ``(`` raises the depth, an unescaped ``)`` lowers
  it, escaped/other characters leave it unchanged) — not an opaque answer key.
  The single binder is ``cs``; the postcondition's three sub-clauses each pin a
  distinct facet of the reported index:

    * MEMBERSHIP — ``i < cs.length``: the closing position is a real index.
    * CLOSING — ``depthAfter (cs.take (i+1)) = 0``: the depth reaches zero AT
      index ``i`` (consuming the first ``i+1`` characters), so the reported index
      is one PAST the last consumed step — the boundary the instance fix moved.
    * MINIMALITY — ``∀ j < i, … ≠ 0``: ``i`` is the FIRST such index, not merely
      some index where the depth is zero.
    * EXHAUSTION (the ``none`` branch) — the depth never returns to zero anywhere
      in ``cs``.

CARRIER NARROWING vs the nagini sibling. The nagini bundle contracts TWO
byte-identical functions (`named_group_pattern_end` / `unnamed_group_pattern_end`)
that model the inner scan of each of the two patched call sites. The Lean bundle
models the shared behaviour ONCE as ``findGroupEnd`` (mapping.md: both call sites
map to the same offset relation, differing only by a fixed constant index shift
applied downstream by G-CONF). So nagini's `rej-offbyone-unnamed` — a differential
copy of the off-by-one on the SECOND function — has no counterpart here: there is
no second modeled function to attack. Its argument is fully carried by the single
off-by-one rival below. This is expected carrier narrowing, not an omission of
coverage.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION (nagini `rej-frame-mutation`, MANDATORY there) —
    VACUOUS here. Nagini holds ``region`` at fractional (read-only) permission and
    a rival that writes to it is rejected for insufficient permission. Lean is
    referentially transparent: ``cs : List Char`` is a plain immutable value, there
    is no half-permission to violate and no aliasing to exploit, so this class has
    NO expressible instance. No substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. ``depthAfter``/``stepBracket`` are spelled
    out over ``cs``; the bundle declares no ``opaque``/``axiom`` (axioms region is
    empty, meta.json axioms == [], deep_model_references == []), so there is no
    answer key an implementation could echo. The honest analogue is the
    loop-free grounded-search POSITIVE CONTROL below (`pos-grounded-search`,
    nagini `pos-grounded-oracle`), which materializes the first index whose
    scanned prefix has depth zero and is PROVEN correct against the frozen spec.

  * PARTIAL-DOMAIN (nagini `rej-prepatch-top-check`) — APPLIES, and is the
    load-bearing rival. The pre-fix code tested depth-zero at the TOP of the loop,
    so the closing position fires only on the iteration AFTER the closing bracket
    was consumed. When the bracket is the FINAL character the loop exhausts first
    and ``none`` is returned — exactly the reported "trailing group" bug and the
    F2P sub-domain. Refuted where the group closes at the last character.

  * OFF-BY-ONE / VALUE DOUBLE-MASK (nagini `rej-offbyone-named`) — APPLIES.
    Reporting the offset ONE short (the matching-bracket offset itself rather than
    one past it) violates the CLOSING clause on every input whose closing prefix
    is non-trivial: the recorded fragment stops one character short of the
    position that actually closes the group. Refuted at a group closing after a
    genuine prefix.

  * MINIMALITY (no direct nagini analogue; a native attack on the FIRST-index
    clause) — a rival that records the LAST depth-zero position instead of the
    first violates the ``∀ j < i, … ≠ 0`` clause whenever the depth returns to
    zero more than once. Included so the minimality sub-clause is attacked
    (nagini's front-recursive oracle pins first-index implicitly; here it is an
    explicit top-level conjunct and must be probed directly).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (``rfl``-driven, tuned to the
``Id.run do`` form via ``specialize_initial``) breaks on any reshape — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that reduces the rival to its concrete value
(``have h : implementation_findGroupEnd <lit> = <val> := by rfl``) and then states
the spec predicate is violated there (``rw [h]; decide``). Each was built BOTH
ways: it ELABORATES against the rival and FAILS on the frozen solution (whose
``rfl`` yields the correct value, on which ``decide`` cannot prove the negation),
so it discriminates rather than asserting a tautology.

BINDER / CLAUSE COVERAGE. The sole input binder ``cs`` is varied across the four
reject witnesses so the battery exercises the spec's dependence on the input shape
rather than probing one point:
  * ``['a', ')']`` — a group closing at the FINAL character (partial-domain).
  * ``['(', ')', ')']`` — a nested group closing after a real prefix (off-by-one).
  * ``[')', '(', ')']`` — the depth returns to zero at index 0 AND index 2, so the
    FIRST-index clause bites (minimality).
  * ``['(', 'a']`` — the depth NEVER returns to zero, so the spec demands ``none``
    (exhaustion / membership).
Every independent top-level clause is attacked, and in BOTH directions across the
two result branches: CLOSING by off-by-one, MINIMALITY by the last-close rival,
``some``-demanded-but-``none``-returned by the partial-domain rival, and
``none``-demanded-but-``some``-returned by the exhaustion rival (which also
violates MEMBERSHIP, reporting an index past the end). ``pts`` = 4 distinct input
points.

AUDIT NOTE on the soundness lane. The battery originally shipped a positive whose
"different shape" was guard-hoisting into ``let``-bound booleans. That term is
DEFINITIONALLY equal to the frozen impl — the frozen proof closed byte-for-byte
unchanged — so the case verified for a reason that had nothing to do with the
spec, exactly as a verbatim copy of gold would have. It is replaced by a
pair-state reshape that the frozen ``rfl`` provably does NOT accept, so the
positive now has to re-close a proof rather than inherit one.

AXIOM lane: EMPTY. axioms region is empty; ``stepBracket``/``depthAfter`` are
A-reference deep models validated out-of-band (G-AX), not axioms the proof
consumes. AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "django__django-11728"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body, verbatim, so an impl replacement lands entirely
# inside the impl region. The proof anchor is the head of the frozen tactic body.
_IMPL_GOLD = (
    "def implementation_findGroupEnd (cs : List Char) : Option Nat := Id.run do\n"
    "  let mut depth : Int := 1\n"
    "  let mut prev : Option Char := none\n"
    "  let mut idx : Nat := 0\n"
    "  for val in cs do\n"
    "    -- Check for unescaped `(` and `)`; they open and close nested parentheses.\n"
    "    if val == '(' && prev != some '\\\\' then\n"
    "      depth := depth + 1\n"
    "    else if val == ')' && prev != some '\\\\' then\n"
    "      depth := depth - 1\n"
    "    prev := some val\n"
    "    -- When the depth is back to zero, the current position closes the group.\n"
    "    if depth == 0 then\n"
    "      return some idx\n"
    "    idx := idx + 1\n"
    "  return none\n"
)

# Head of the frozen proof body (inside proof-start/proof-end): a legitimate
# ground-instance `have` is spliced in front of it for the admissibility case.
_PROOF_HEAD = (
    "  intro cs\n"
    "  unfold problem_spec_findGroupEnd\n"
)

# The generalized loop (proof region) and the tactic body of the bridge lemma
# that relates one of its iterations to `stepBracket`. A soundness positive that
# reshapes the impl into a form which is NOT definitionally equal to the frozen
# one has to carry the SAME reshape through this helper and re-close the bridge;
# both live in the proof region, so the edit is in scope and the `theorem
# correct_findGroupEnd` STATEMENT stays byte-identical.
_LOOPFROM_GOLD = (
    "def loopFrom (cs : List Char) (d0 : Int) (prev0 : Option Char) (idx0 : Nat) :\n"
    "    Option Nat := Id.run do\n"
    "  let mut depth : Int := d0\n"
    "  let mut prev : Option Char := prev0\n"
    "  let mut idx : Nat := idx0\n"
    "  for val in cs do\n"
    "    if val == '(' && prev != some '\\\\' then\n"
    "      depth := depth + 1\n"
    "    else if val == ')' && prev != some '\\\\' then\n"
    "      depth := depth - 1\n"
    "    prev := some val\n"
    "    if depth == 0 then\n"
    "      return some idx\n"
    "    idx := idx + 1\n"
    "  return none\n"
)

_UNFOLD_STEP_PROOF = (
    "  simp only [loopFrom, List.forIn_cons, stepBracket]\n"
    "  split <;> simp only [beq_iff_eq] <;> split <;> first | rfl | (split <;> rfl)\n"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_HEAD) == 1, "proof region drifted; update _PROOF_HEAD"
assert _BASE.count(_LOOPFROM_GOLD) == 1, "proof region drifted; update _LOOPFROM_GOLD"
assert _BASE.count(_UNFOLD_STEP_PROOF) == 1, "proof drifted; update _UNFOLD_STEP_PROOF"


def _impl(body):
    """Full Solution.lean variant with a replaced impl body (spec + theorem
    STATEMENT + frozen proof body untouched)."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival impl bodies (each a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical). Note the frozen `rfl`-
# based proof does NOT close for any of these reshaped impls — which is why the
# rejection is corroborated by a witness, not by tactic breakage alone.
# ---------------------------------------------------------------------------

# PARTIAL-DOMAIN (= the pre-fix bug): test depth-zero at the TOP of the loop, so
# the closing index is only reported on the iteration AFTER the bracket is
# consumed. A group whose closing bracket is the FINAL character is never
# reported -> `none` where the spec demands `some`.
_PREPATCH_TOP = (
    "def implementation_findGroupEnd (cs : List Char) : Option Nat := Id.run do\n"
    "  let mut depth : Int := 1\n"
    "  let mut prev : Option Char := none\n"
    "  let mut idx : Nat := 0\n"
    "  for val in cs do\n"
    "    if depth == 0 then\n"
    "      return some idx\n"
    "    if val == '(' && prev != some '\\\\' then\n"
    "      depth := depth + 1\n"
    "    else if val == ')' && prev != some '\\\\' then\n"
    "      depth := depth - 1\n"
    "    prev := some val\n"
    "    idx := idx + 1\n"
    "  return none\n"
)

# OFF-BY-ONE: report `idx - 1` (the matching-bracket offset itself) instead of
# `idx` (one past it). Returns the closing prefix ONE character short.
_OFF_BY_ONE = (
    "def implementation_findGroupEnd (cs : List Char) : Option Nat := Id.run do\n"
    "  let mut depth : Int := 1\n"
    "  let mut prev : Option Char := none\n"
    "  let mut idx : Nat := 0\n"
    "  for val in cs do\n"
    "    if val == '(' && prev != some '\\\\' then\n"
    "      depth := depth + 1\n"
    "    else if val == ')' && prev != some '\\\\' then\n"
    "      depth := depth - 1\n"
    "    prev := some val\n"
    "    if depth == 0 then\n"
    "      return some (idx - 1)\n"
    "    idx := idx + 1\n"
    "  return none\n"
)

# LAST-CLOSE (minimality attack): never stop early; record the LAST index at
# which the depth is zero. Correct value whenever the depth reaches zero exactly
# once, but reports a non-minimal index when it reaches zero more than once.
_LAST_CLOSE = (
    "def implementation_findGroupEnd (cs : List Char) : Option Nat := Id.run do\n"
    "  let mut depth : Int := 1\n"
    "  let mut prev : Option Char := none\n"
    "  let mut idx : Nat := 0\n"
    "  let mut res : Option Nat := none\n"
    "  for val in cs do\n"
    "    if val == '(' && prev != some '\\\\' then\n"
    "      depth := depth + 1\n"
    "    else if val == ')' && prev != some '\\\\' then\n"
    "      depth := depth - 1\n"
    "    prev := some val\n"
    "    if depth == 0 then\n"
    "      res := some idx\n"
    "    idx := idx + 1\n"
    "  return res\n"
)

# EXHAUSTION rival (attacks the `none` branch in the direction the others do
# not). Every other rival returns a WRONG `some` or a `none` where `some` is
# demanded; none of them is refuted at a fragment the spec says is NEVER closed.
# This one reports the exhausted index instead of `none`, so on a fragment whose
# depth never returns to zero it claims a closing position that does not exist —
# violating the `none` branch's universally-quantified clause AND the MEMBERSHIP
# clause (the reported index is not even an index of the fragment).
_EXHAUST_SOME = (
    "def implementation_findGroupEnd (cs : List Char) : Option Nat := Id.run do\n"
    "  let mut depth : Int := 1\n"
    "  let mut prev : Option Char := none\n"
    "  let mut idx : Nat := 0\n"
    "  for val in cs do\n"
    "    if val == '(' && prev != some '\\\\' then\n"
    "      depth := depth + 1\n"
    "    else if val == ')' && prev != some '\\\\' then\n"
    "      depth := depth - 1\n"
    "    prev := some val\n"
    "    if depth == 0 then\n"
    "      return some idx\n"
    "    idx := idx + 1\n"
    "  return some idx\n"
)

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl.
#
# AUDIT NOTE. The previous positive here hoisted the two branch guards into
# `let`-bound booleans, which is DEFINITIONALLY equal to the frozen impl — the
# frozen `rfl`-driven proof closed verbatim, unchanged, because Lean sees the
# same term. Measured: that variant verified, but so would a copy of the frozen
# impl, so it exercised nothing about the spec and its "different shape" claim was
# false. Replaced by a reshape that is NOT definitionally equal: the two mutable
# scalars (`depth`, `prev`) are collapsed into ONE pair-valued accumulator whose
# update is delegated to the shared `stepBracket`, so the loop's state type
# changes and `Id.run do` elaborates to a different term.
#
# That the reshape is genuinely non-defeq is machine-checked twice over: the
# frozen `specialize_initial := rfl` FAILS on it ("Not a definitional equality:
# implementation_findGroupEnd cs is not definitionally equal to loopFrom cs 1
# none 0"), so the case must carry the SAME reshape through the proof-region
# helper `loopFrom` and re-close the one-iteration bridge lemma. Both edits are
# inside the proof region; the `theorem correct_findGroupEnd` STATEMENT is
# byte-identical and no new declaration/axiom/`sorry`/assumption token appears.
_POS_PAIR_STATE = (
    "def implementation_findGroupEnd (cs : List Char) : Option Nat := Id.run do\n"
    "  let mut st : Int × Option Char := (1, none)\n"
    "  let mut idx : Nat := 0\n"
    "  for val in cs do\n"
    "    st := stepBracket st val\n"
    "    if st.1 == 0 then\n"
    "      return some idx\n"
    "    idx := idx + 1\n"
    "  return none\n"
)

# The same pair-state reshape applied to the generalized loop, so the
# characterization lemma still describes the impl it is about.
_POS_PAIR_LOOPFROM = (
    "def loopFrom (cs : List Char) (d0 : Int) (prev0 : Option Char) (idx0 : Nat) :\n"
    "    Option Nat := Id.run do\n"
    "  let mut st : Int × Option Char := (d0, prev0)\n"
    "  let mut idx : Nat := idx0\n"
    "  for val in cs do\n"
    "    st := stepBracket st val\n"
    "    if st.1 == 0 then\n"
    "      return some idx\n"
    "    idx := idx + 1\n"
    "  return none\n"
)

# The bridge lemma's tactic body, re-closed for the pair-state loop: the guard
# case-split the frozen script performed by hand is now exactly `stepBracket`'s
# own definition, so the proof is a single split on whether the stepped depth is
# zero. Only the TACTIC BODY changes; the lemma's statement is untouched.
_POS_PAIR_UNFOLD_PROOF = (
    "  simp only [loopFrom, List.forIn_cons]\n"
    "  by_cases h : (stepBracket (d0, prev0) c).1 = 0 <;> simp [h]\n"
)


# SECOND POSITIVE CONTROL (soundness) — the nagini `pos-grounded-oracle`
# analogue, and a MAXIMALLY different shape: no loop and no mutable state at all.
# The closing position is obtained by searching the fragment's own indices for the
# first one whose scanned prefix has depth zero.
#
# This is an honest positive, not a cheat, for exactly nagini's reason: the search
# key `depthAfter` is a GROUNDED fold of the input (spelled out via `stepBracket`),
# not an opaque answer key, so materializing the first index that satisfies it IS a
# correct implementation. There is no oracle to echo — the bundle declares no
# `axiom`/`opaque` and `deep_model_references == []`.
#
# It shares NO term structure with the frozen `Id.run do` loop, so none of the
# frozen proof-region machinery applies: the whole proof region is rewritten to
# discharge the three `some`-branch atoms and the `none` branch directly from
# `List.find?`'s own characterization. The `theorem correct_findGroupEnd`
# STATEMENT is byte-identical and no new declaration/axiom/`sorry` appears — the
# rewritten region declares strictly FEWER helpers than the frozen one.
_POS_ORACLE_IMPL = (
    "def implementation_findGroupEnd (cs : List Char) : Option Nat :=\n"
    "  (List.range cs.length).find? (fun i => depthAfter (cs.take (i + 1)) == 0)\n"
)

_POS_ORACLE_PROOF = (
    "theorem correct_findGroupEnd :\n"
    "    ∀ (cs : List Char),\n"
    "      problem_spec_findGroupEnd cs (implementation_findGroupEnd cs) := by\n"
    "  intro cs\n"
    "  unfold problem_spec_findGroupEnd implementation_findGroupEnd\n"
    "  cases h : (List.range cs.length).find? "
    "(fun i => depthAfter (cs.take (i + 1)) == 0) with\n"
    "  | some i =>\n"
    "    have hsat := List.find?_some h\n"
    "    have hi : i < cs.length := List.mem_range.mp (List.mem_of_find?_eq_some h)\n"
    "    refine ⟨hi, by simpa using hsat, ?_⟩\n"
    "    intro j hj hz\n"
    "    rw [List.find?_eq_some_iff_getElem] at h\n"
    "    obtain ⟨-, k, hk, hkeq, hprev⟩ := h\n"
    "    have hik : i = k := by simpa [List.getElem_range] using hkeq.symm\n"
    "    have := hprev j (by omega)\n"
    "    simp [List.getElem_range] at this\n"
    "    exact this hz\n"
    "  | none =>\n"
    "    intro i hi\n"
    "    simpa using List.find?_eq_none.mp h i (List.mem_range.mpr hi)\n"
)

_PROOF_START = "-- proof-start\n"
_PROOF_END = "-- proof-end"
assert _BASE.count(_PROOF_START) == 1 and _BASE.count(_PROOF_END) == 1


def _pos_oracle():
    """The loop-free grounded-search positive: impl replaced, and the whole
    proof region replaced by a direct `List.find?` argument (the frozen
    loop-characterization machinery is about a loop this impl does not have)."""
    src = _swap(_BASE, _IMPL_GOLD, _POS_ORACLE_IMPL)
    head = src.index(_PROOF_START) + len(_PROOF_START)
    return src[:head] + _POS_ORACLE_PROOF + src[src.index(_PROOF_END):]


def _pos_pair():
    """The pair-state soundness positive: impl reshaped, plus the matching
    reshape of the proof-region helper and its bridge lemma's tactic body."""
    src = _swap(_BASE, _IMPL_GOLD, _POS_PAIR_STATE)
    src = _swap(src, _LOOPFROM_GOLD, _POS_PAIR_LOOPFROM)
    return _swap(src, _UNFOLD_STEP_PROOF, _POS_PAIR_UNFOLD_PROOF)

# ADMISSIBILITY: discharge the obligation at the F2P GROUND input (a group whose
# closing bracket is the FINAL character — the trailing-group case the fix
# repairs) as a `have` inside the existing tactic body, then close the frozen
# obligation verbatim. Verifies iff the spec is satisfiable at exactly the input
# the F2P exercises (the analogue of a non-vacuous precondition). No new
# declaration/axiom/token; the theorem STATEMENT is byte-identical.
_ADM_GROUND = (
    "  have _ground : problem_spec_findGroupEnd ['a', ')']\n"
    "      (implementation_findGroupEnd ['a', ')']) := by\n"
    "    have h : implementation_findGroupEnd ['a', ')'] = some 1 := by rfl\n"
    "    rw [h]; unfold problem_spec_findGroupEnd; decide\n"
    + _PROOF_HEAD
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different CORRECT impl that
    # MUST verify (else SPEC-TOO-STRONG). The two branch conditions are hoisted
    # into `let`-bound booleans; the term is definitionally equal to gold, so the
    # frozen proof closes unchanged. Ports nagini `pos-break-reshape` /
    # `pos-grounded-oracle` (a genuinely different-shaped correct impl).
    # =====================================================================
    {
        "id": "pos-pair-state-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_pair(),
        "rationale": (
            "a correct reshape that collapses the two mutable scalars (`depth`, "
            "`prev`) into ONE pair-valued accumulator, delegating the per-character "
            "update to the shared `stepBracket`, must still satisfy the frozen "
            "postcondition — the reported first-zero index is unchanged. Unlike a "
            "guard-hoisting reshape (which Lean sees as the SAME term, so it tests "
            "nothing), this changes the loop's state type and is NOT definitionally "
            "equal to the frozen impl: the frozen `specialize_initial := rfl` fails "
            "on it outright, so the case carries the same reshape through the "
            "proof-region helper `loopFrom` and re-closes the one-iteration bridge "
            "lemma's TACTIC BODY. Theorem STATEMENT byte-identical; no new "
            "declaration/axiom/`sorry`/assumption token. If it could not verify, the "
            "spec would be SPEC-TOO-STRONG (rejecting a faithful correct impl whose "
            "shape merely differs)."
        ),
    },

    {
        "id": "pos-grounded-search",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_oracle(),
        "rationale": (
            "the nagini `pos-grounded-oracle` analogue, and the maximally different "
            "correct shape: NO loop and no mutable state — the closing position is "
            "the first of the fragment's own indices whose scanned prefix has depth "
            "zero. Honest rather than a cheat because the search key `depthAfter` is "
            "a GROUNDED fold of the input (spelled out via `stepBracket`), not an "
            "opaque answer key, so materializing the first index satisfying it IS a "
            "correct impl; the bundle declares no `axiom`/`opaque`, so there is no "
            "oracle to echo. It shares no term structure with the frozen `Id.run do` "
            "loop, so the whole proof region is rewritten to discharge the three "
            "`some`-branch atoms and the `none` branch from `List.find?`'s own "
            "characterization — declaring strictly FEWER helpers than the frozen "
            "region, with the theorem STATEMENT byte-identical and no new "
            "declaration/axiom/`sorry`. Verifying it confirms the spec admits a "
            "faithful correct impl of a wholly different shape (else "
            "SPEC-TOO-STRONG); it is also the strongest available check that the "
            "postcondition pins BEHAVIOR rather than the frozen loop's form."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is discharged additionally at the F2P GROUND
    # input (trailing group closing at the final character) inside the proof
    # region, confirming the modeled behavior is SATISFIABLE there rather than
    # only provable in the abstract. The frozen theorem carries no precondition
    # hypothesis (behavior is total), so nagini's precondition-admission probe
    # (`adm-nonvacuous-precond`) has no binder to attack; discharging the F2P
    # ground instance is the faithful analogue.
    # =====================================================================
    {
        "id": "adm-trailing-group-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_HEAD, _ADM_GROUND),
        "rationale": (
            "the obligation is discharged at the F2P ground input `['a', ')']` — a "
            "group whose closing bracket is the FINAL character, the exact "
            "trailing-group shape the instance repairs — where the spec requires "
            "`some 1` (index one PAST the last consumed step). Established by "
            "reducing the impl (`rfl`) then `decide`, as a `have` in front of the "
            "frozen obligation, which is then closed verbatim. Verifies (else the "
            "spec would be unsatisfiable at exactly the F2P input — the analogue of "
            "PRECOND-TOO-STRONG). Nothing is assumed: the theorem STATEMENT is "
            "byte-identical and no new declaration/axiom/`sorry` appears."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries (a) the refinement argument that its faithful
    # real patch would NOT resolve the F2P, and (b) a refutation witness pinning
    # the violation at one concrete input (built both ways: holds of the rival,
    # fails on gold).
    # =====================================================================
    {
        "id": "weak-prepatch-top-check",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH_TOP),
        "refinement": (
            "this is the literal PRE-FIX placement: the depth-zero test sits at the "
            "TOP of the loop, so the closing index fires only on the iteration AFTER "
            "the closing bracket is consumed. When the bracket is the FINAL "
            "character the loop exhausts first and the group is never recorded — "
            "exactly the reported trailing-group bug (F2P inputs with no trailing "
            "`/` or `$`). Its faithful real patch is the pre-patch code, which fails "
            "those F2P observables — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the EXHAUSTION/`none` branch (and the CLOSING clause): at "
            "`cs = ['a', ')']` the group closes at the final index 1, so the spec "
            "demands `some 1`, but the rival returns `none`. Refuted where the "
            "closing bracket is the last character — the discriminating sub-domain."
        ),
        "witness": (
            "-- Group closing at the FINAL character: the spec demands `some 1`\n"
            "-- (depth returns to zero consuming both characters), but a top-of-loop\n"
            "-- depth test never re-enters the body to record it and returns `none`.\n"
            "example : ¬ problem_spec_findGroupEnd ['a', ')']\n"
            "    (implementation_findGroupEnd ['a', ')']) := by\n"
            "  have h : implementation_findGroupEnd ['a', ')'] = none := by rfl\n"
            "  rw [h]; unfold problem_spec_findGroupEnd; decide\n"
        ),
    },
    {
        "id": "weak-off-by-one-short",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_OFF_BY_ONE),
        "refinement": (
            "reporting `idx - 1` (the matching-bracket offset itself) instead of "
            "`idx` (one past it) captures the group ONE character short, dropping "
            "the closing bracket from the recorded fragment. The downstream "
            "replacement would then be wrong for every real group — it does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the CLOSING clause `depthAfter (cs.take (i+1)) = 0`: at "
            "`cs = ['(', ')', ')']` the initially-open bracket closes at index 2 "
            "(depths 2,1,0), so the spec demands `some 2`, but the rival reports "
            "`some 1` (`depthAfter (take 2) = 1 ≠ 0`). Refuted at a nested group "
            "whose closing prefix is non-trivial."
        ),
        "witness": (
            "-- Nested group closing at index 2 (depths 2,1,0): the spec demands\n"
            "-- `some 2`, but reporting the offset one short gives `some 1`, whose\n"
            "-- prefix has depth 1 ≠ 0 — the closing clause is violated.\n"
            "example : ¬ problem_spec_findGroupEnd ['(', ')', ')']\n"
            "    (implementation_findGroupEnd ['(', ')', ')']) := by\n"
            "  have h : implementation_findGroupEnd ['(', ')', ')'] = some 1 := by rfl\n"
            "  rw [h]; unfold problem_spec_findGroupEnd; decide\n"
        ),
    },
    {
        "id": "weak-exhaust-reports-some",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_EXHAUST_SOME),
        "refinement": (
            "returning the exhausted index instead of reporting the group unclosed "
            "means a fragment in which the parenthesis never closes is treated as "
            "though it closed just past its end. The downstream slice would run to "
            "the end of the text and substitute over a fragment that is not a "
            "complete group at all, so a malformed or truncated pattern silently "
            "produces a bogus replacement instead of being left alone — it does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the `none`/EXHAUSTION branch and the MEMBERSHIP clause "
            "`i < cs.length`: at `cs = ['(', 'a']` the depth runs 2,2 and never "
            "returns to zero, so the spec demands `none`, but the rival reports "
            "`some 2` — an index that is not even an index of a 2-character "
            "fragment. This is the one direction the other rivals leave unattacked: "
            "each of those returns a wrong `some` (or a `none` where `some` is "
            "demanded) at an input the spec says IS closed, so no existing case is "
            "refuted at a fragment the spec says is NEVER closed."
        ),
        "witness": (
            "-- A fragment whose depth never returns to zero (depths 2,2): the spec\n"
            "-- demands `none`, but reporting the exhausted index claims the group\n"
            "-- closes at index 2, which is not an index of a 2-character fragment.\n"
            "example : ¬ problem_spec_findGroupEnd ['(', 'a']\n"
            "    (implementation_findGroupEnd ['(', 'a']) := by\n"
            "  have h : implementation_findGroupEnd ['(', 'a'] = some 2 := by rfl\n"
            "  rw [h]; unfold problem_spec_findGroupEnd; decide\n"
        ),
    },
    {
        "id": "weak-last-close-not-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_LAST_CLOSE),
        "refinement": (
            "recording the LAST depth-zero position instead of stopping at the "
            "FIRST corresponds to running the scan past the group's own closing "
            "bracket and capturing up to a later balance point. The recorded group "
            "substring would then swallow trailing text belonging to a following "
            "group, so the replacement is wrong wherever the depth returns to zero "
            "more than once — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the MINIMALITY clause `∀ j < i, depthAfter (cs.take (j+1)) "
            "≠ 0`: at `cs = [')', '(', ')']` the depth is zero at BOTH index 0 "
            "(depth 0) and index 2, so the spec demands the FIRST, `some 0`, but the "
            "rival reports the last, `some 2` — which fails minimality at `j = 0`. "
            "Refuted where the depth returns to zero more than once."
        ),
        "witness": (
            "-- Depth reaches zero at index 0 AND index 2: the spec demands the\n"
            "-- FIRST (`some 0`); a last-close impl reports `some 2`, violating the\n"
            "-- minimality clause at j = 0 (depthAfter (take 1) = 0).\n"
            "example : ¬ problem_spec_findGroupEnd [')', '(', ')']\n"
            "    (implementation_findGroupEnd [')', '(', ')']) := by\n"
            "  have h : implementation_findGroupEnd [')', '(', ')'] = some 2 := by rfl\n"
            "  rw [h]; unfold problem_spec_findGroupEnd; decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references: the per-character depth update
# is modeled directly (`stepBracket`/`depthAfter`), so there is no in-model axiom
# obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
