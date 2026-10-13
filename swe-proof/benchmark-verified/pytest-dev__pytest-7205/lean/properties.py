"""properties.py — G-PBT falsification battery for pytest-dev__pytest-7205 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with every obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total behavior over a header and an optional parameter):

  actionLine (header : List Char) (param : Option (List Char)) : List Char
      match param with
      | none   => result = header
      | some p => result = header ++ ['['] ++ safeDisplay p ++ [']']

  The text emitted for a fixture action is the unchanged header, followed —
  ONLY when the action carries a parameter value — by that value's safe,
  size-limited representation enclosed in square brackets. When no parameter
  value is present the emitted text is exactly the header, unchanged.

  Load-bearing postcondition clauses (all in ``problem_spec_actionLine``):
    (P-none)    on the absent branch the result is EXACTLY the header — nothing
                appended, no stray brackets.
    (P-prefix)  on the present branch the result BEGINS with the unchanged
                header (the framing prefix is passed through verbatim).
    (P-open)    the parameter rendering is preceded by an opening ``'['``.
    (P-body)    the bracket content is the safe representation of THE PARAMETER,
                ``safeDisplay p`` — not the raw value, and not the
                representation of some other operand. This is the clause the
                modeled change lives in, so the reject lane must reach it;
                U5/U6 below are the two rivals that do.
    (P-close)   the parameter rendering is followed by a closing ``']'`` — the
                delimiter is two-sided, not one-sided.

CARRIER NARROWING vs the nagini sibling (READ THIS — it is why the case set
differs). The nagini bundle models ``render_param_token`` — the apostrophe-
quoting INTERNALS of the safe representation — so its central rivals attack the
CONTENT of the rendering: plain-text-no-delimiters, one-sided apostrophe,
first-interior-code-point-wrong. This lean bundle models a strictly SHALLOWER
surface: the bracket-wrapping and the present/absent branch of the reporting
tail, with the ENTIRE safe-representation behavior absorbed into an ``opaque``
callee ``safeDisplay``. The observable the spec pins about the parameter body is
only "it is ``safeDisplay p``", i.e. the canonical representation is the one
applied; the internal apostrophe-quoting is INTERNAL to the opaque symbol and
the spec neither pins nor may pin it.

The opaque body is nonetheless ATTACKABLE, and the (P-body) clause is where the
whole modeled change lives, so the reject lane must reach it. What is true is the
narrow statement that ``p = safeDisplay p`` is neither provable NOR refutable, so
no LITERAL-input witness decides a body divergence. What does NOT follow is that
the body is unattackable: a witness may state its refutation at a point described
by HYPOTHESIS rather than computed (``hsd : (safeDisplay ['a']).length ≠ 1``),
and opacity is precisely what makes such a hypothesis satisfiable — no tactic can
derive ``False`` from a disequation about an opaque term, which is what the gate's
consistency probe confirms. Both body rivals below (U5 verbatim-value, U6
wrong-operand) are landed that way, each with a machine-checked three-way result
(holds of the rival / fails on gold / hypotheses consistent).

This matters because a purely STRUCTURAL reject lane is blind to the modeled
change. Measured: with the (P-body) clause NEUTERED in both spec and impl (the
bracket content rewritten to the raw ``p`` on both sides, so the clause asserts
nothing), all four structural witnesses (U1–U4) still hold of their rival and
still fail on that gutted gold — they discriminate a spec that has no body clause
at all. So U1–U4 attest only to the delimiters, the prefix and the branch, never
to "the canonical representation is the one applied". U5/U6 are what carry that.

The STRUCTURE surrounding the opaque rendering is attacked by U1–U4 (bracket
delimiters, header prefix, branch selection); each of those refutes its clause via
a LENGTH mismatch that holds for an arbitrary ``safeDisplay`` value, so it needs
no evaluation of the opaque term and no hypothesis.

LENGTH IS NOT THE ONLY PROJECTION, and two rivals require a second one. U1–U6 all
refute via a length equation, which makes the whole set blind to any divergence
that PRESERVES the result's width: the delimiters transposed rather than dropped
(U7), and the rendering's first code point overwritten rather than the whole
rendering replaced (U8). Against both of those every length equation above reduces
to a TRUE arithmetic identity and refutes nothing. U7/U8 project the result's HEAD
(``List.head?``) instead, which discriminates position where length cannot. U8 in
particular is the lean instance of the nagini sibling's ``first-char-wrong``
partial-domain rival: it is expressible here — over ``head?`` under a hypothesis
about the opaque term, the same conditioning U5/U6 apply to length — so opacity is
not what blocked it, and the earlier reading of that case as having no analogue on
this carrier was wrong.

FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: the
inputs carry no heap permission, there is no read-only half-permission to
overwrite and no aliasing to exploit. The nagini frame-mutation rival (a store
into the read-only parameter, rejected for insufficient permission) has NO
expressible instance here and no substitute is fabricated for it. The frame
obligation instead surfaces as clause (P-prefix)/(P-none): the header is pinned
verbatim, so a rival that drops or mangles it is refuted — that is the
referentially-transparent analogue and it IS attacked below.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form —
so a rejection alone attributes nothing to the spec. Every ``expect="reject"``
case therefore carries a Lean snippet proving the rival CONTRADICTS the spec at
one concrete input, checked to hold of its rival and to FAIL on the frozen
solution (so it discriminates rather than asserting a tautology). Two shapes:

  * STRUCTURAL (U1–U4, U7): derive a false LENGTH equation from the
    postcondition. The opaque ``safeDisplay`` term cancels — its length appears
    identically on both sides — and ``omega`` closes the residual arithmetic. No
    hypothesis, so no consistency probe is needed.
  * CONDITIONED (U5, U6, U8): the divergence is in the bracket CONTENT, which no
    literal input decides, so the refutation is stated at a point described by
    hypothesis (a disequation about the opaque term). The gate's consistency
    probe then checks those hypotheses are jointly satisfiable; opacity makes
    that hold, since no tactic can derive ``False`` from them.

THE ``Id.run`` REDUCTION STEP IS LOAD-BEARING — DO NOT DROP IT. Every witness
below reduces the monadic scaffolding (``simp only [..., Id.run, Id.pure_eq,
Id.bind_eq]``) BEFORE it projects the result. This is not cosmetic. The frozen
impl is written ``Id.run do``/``let mut``, and without those three lemmas the
projection is taken of an UNREDUCED ``(do pure ...).run`` term, so the gold-side
build fails because the tactic could not see through the monad — not because gold
satisfies the spec. Measured, with real builds: with the reduction lemmas absent,
each witness's gold-side error is BYTE-IDENTICAL to the error the same witness
produces against a deliberately WRONG impl written in the frozen imperative shape
(e.g. an accumulator that appends ``safeDisplay p`` with no brackets). An error
that does not change when the subject stops satisfying the spec carries no
information about the spec, so such a witness discriminates the impl's SYNTACTIC
SHAPE, not its correctness, and the gate would record ``rejected`` for it either
way.

With the reduction lemmas present the gold-side failure is a genuine refutation,
established by the type-revealing experiment rather than by reading the message:
replacing the closing ``omega`` with a deliberate type error on the derived
hypothesis (``exact (hl : Nat)``) reports ``hl has type True`` on the frozen
solution — i.e. ``simp`` PROVED the length equation there — while on each rival
it reports a concrete false equation (e.g.
``0 + (safeDisplay ['a']).length = 0 + (0+1) + (safeDisplay ['a']).length + (0+1)``).
That pair is what makes the rejection attributable to the spec. Each witness is
additionally checked to FAIL against three further VERIFYING impls of the same
spec (the two positive controls and the non-defeq imperative reshape), so its
failure tracks correctness rather than any single impl's form.

AXIOM lane: DROPPED. The nagini bundle's ``AXIOM_TESTS`` (the deep-model
saferepr soundness/containment probes) belong to G-AX, which the G-PBT spec lane
ignores; meta.json records the A-consumed opaque callee and G-AX validates its
signature against the real callee separately.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7205"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL body of the impl region: every impl reshape lands entirely inside it.
_IMPL = (
    "def implementation_actionLine (header : List Char) (param : Option (List Char)) :\n"
    "    List Char := Id.run do\n"
    "  let mut out := header\n"
    "  match param with\n"
    "  | some p => out := out ++ ['['] ++ safeDisplay p ++ [']']\n"
    "  | none   => pure ()\n"
    "  return out"
)

# The FULL body of the proof region (the obligation only; no helper lemmas).
_PROOF = (
    "theorem correct_actionLine : ∀ (header : List Char) (param : Option (List Char)),\n"
    "    problem_spec_actionLine header param (implementation_actionLine header param) := by\n"
    "  intro header param\n"
    "  unfold problem_spec_actionLine implementation_actionLine\n"
    "  cases param with\n"
    "  | none => rfl\n"
    "  | some p => rfl"
)

assert _BASE.count(_IMPL) == 1, "impl anchor drift"
assert _BASE.count(_PROOF) == 1, "proof anchor drift"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. If a faithful correct implementation cannot satisfy the frozen
# obligation, the spec is SPEC-TOO-STRONG. Each keeps the `correct_actionLine`
# STATEMENT byte-identical; none introduces a helper lemma, an axiom, `sorry`,
# `admit`, or `native_decide`.
# ===========================================================================

# --- pos-func: drop the `Id.run do`/`let mut` scaffolding for a direct
# functional match; both branches return the concatenation in one step. Same
# value on every input, so every clause still holds. `rfl` per branch closes. --
_POS_FUNC_IMPL = (
    "def implementation_actionLine (header : List Char) (param : Option (List Char)) :\n"
    "    List Char :=\n"
    "  match param with\n"
    "  | none   => header\n"
    "  | some p => header ++ ['['] ++ safeDisplay p ++ [']']"
)
_POS_FUNC_PROOF = (
    "theorem correct_actionLine : ∀ (header : List Char) (param : Option (List Char)),\n"
    "    problem_spec_actionLine header param (implementation_actionLine header param) := by\n"
    "  intro header param\n"
    "  unfold problem_spec_actionLine implementation_actionLine\n"
    "  cases param with\n"
    "  | none => rfl\n"
    "  | some p => rfl"
)
POS_FUNC = _swap(_swap(_BASE, _IMPL, _POS_FUNC_IMPL), _PROOF, _POS_FUNC_PROOF)

# --- pos-earlyreturn: keep `Id.run do` but branch with two early `return`s
# instead of a mutable accumulator. Different control shape (no `let mut`, no
# post-match fallthrough), identical value; `rfl` per branch closes. -----------
_POS_ER_IMPL = (
    "def implementation_actionLine (header : List Char) (param : Option (List Char)) :\n"
    "    List Char := Id.run do\n"
    "  match param with\n"
    "  | none   => return header\n"
    "  | some p => return header ++ ['['] ++ safeDisplay p ++ [']']"
)
_POS_ER_PROOF = _POS_FUNC_PROOF
POS_EARLYRETURN = _swap(_swap(_BASE, _IMPL, _POS_ER_IMPL), _PROOF, _POS_ER_PROOF)


# ===========================================================================
# ADMISSIBILITY — the frozen `correct_actionLine` carries NO precondition
# hypothesis (the behavior is total), so there is no precondition binder to
# admit. The honest analogue: discharge the spec predicate by evaluation at two
# representative reporting-shaped inputs (a header with a present parameter, and
# the same header with an absent parameter), inside the proof region alongside
# the frozen obligation. If those ground instances could not be discharged the
# behavior would be unsatisfiable at exactly the shapes the F2P exercises. The
# `correct_actionLine` STATEMENT is byte-identical; the ground instances are
# `have`s prepended to the frozen tactic body; no new declaration is added.
# ===========================================================================
_ADMISS_PROOF = (
    "theorem correct_actionLine : ∀ (header : List Char) (param : Option (List Char)),\n"
    "    problem_spec_actionLine header param (implementation_actionLine header param) := by\n"
    "  -- ADMISSIBILITY: the obligation is satisfiable at representative reporting\n"
    "  -- shapes — a header with a present parameter, and the same header with an\n"
    "  -- absent parameter — discharged by evaluation before the general proof.\n"
    "  have _ground_some : problem_spec_actionLine ['S'] (some ['f','o','o'])\n"
    "      (implementation_actionLine ['S'] (some ['f','o','o'])) := by\n"
    "    unfold problem_spec_actionLine implementation_actionLine\n"
    "    rfl\n"
    "  have _ground_none : problem_spec_actionLine ['S'] none\n"
    "      (implementation_actionLine ['S'] none) := by\n"
    "    unfold problem_spec_actionLine implementation_actionLine\n"
    "    rfl\n"
    "  intro header param\n"
    "  unfold problem_spec_actionLine implementation_actionLine\n"
    "  cases param with\n"
    "  | none => rfl\n"
    "  | some p => rfl"
)
ADMISS = _swap(_BASE, _PROOF, _ADMISS_PROOF)


# ===========================================================================
# UNIQUENESS / REJECT rivals — wrong impls sharing the frozen spec that MUST be
# rejected. Each carries (a) the refinement argument that its faithful real
# patch would NOT resolve the F2P, and (b) a refutation witness pinning the
# violation at one concrete input, checked to hold of the rival and to FAIL on
# the frozen solution. Every rival is refuted by a LENGTH mismatch, so the
# opaque `safeDisplay` term cancels and no evaluation of it is required.
# ===========================================================================

# --- U1 DROP-BRACKETS: append the parameter rendering with NO delimiters. -----
# Correct on the header but omits BOTH square brackets: `header ++ safeDisplay p`.
# Attacks (P-open) and (P-close). The result is 2 code points shorter than the
# spec demands.
_DROP_BRACKETS = (
    "def implementation_actionLine (header : List Char) (param : Option (List Char)) :\n"
    "    List Char :=\n"
    "  match param with\n"
    "  | none   => header\n"
    "  | some p => header ++ safeDisplay p"
)
RIVAL_DROP_BRACKETS = _swap(_BASE, _IMPL, _DROP_BRACKETS)

# --- U2 OPEN-ONLY: opening bracket present, closing bracket omitted. ----------
# `header ++ ['['] ++ safeDisplay p` — attacks (P-close) specifically (the
# delimiter is one-sided). One code point short. A NEAR-MISS of U1 (it agrees
# with the spec on the opening bracket), so it is refuted at its OWN input.
_OPEN_ONLY = (
    "def implementation_actionLine (header : List Char) (param : Option (List Char)) :\n"
    "    List Char :=\n"
    "  match param with\n"
    "  | none   => header\n"
    "  | some p => header ++ ['['] ++ safeDisplay p"
)
RIVAL_OPEN_ONLY = _swap(_BASE, _IMPL, _OPEN_ONLY)

# --- U3 DROP-HEADER: emit only the bracketed rendering, dropping the header. --
# `['['] ++ safeDisplay p ++ [']']` — attacks (P-prefix): the framing prefix is
# lost. The referentially-transparent analogue of the nagini frame-mutation
# rival (which corrupted the read-only input); here the corruption is that the
# unchanged prefix is not passed through.
_DROP_HEADER = (
    "def implementation_actionLine (header : List Char) (param : Option (List Char)) :\n"
    "    List Char :=\n"
    "  match param with\n"
    "  | none   => header\n"
    "  | some p => ['['] ++ safeDisplay p ++ [']']"
)
RIVAL_DROP_HEADER = _swap(_BASE, _IMPL, _DROP_HEADER)

# --- U4 NONE-APPENDS: on the ABSENT branch, append empty brackets. ------------
# `none => header ++ ['['] ++ [']']` — attacks (P-none): the absent case must be
# EXACTLY the header, but this emits stray delimiters. The present branch is
# left correct, so it is a partial-domain rival diverging only on `none`.
_NONE_APPENDS = (
    "def implementation_actionLine (header : List Char) (param : Option (List Char)) :\n"
    "    List Char :=\n"
    "  match param with\n"
    "  | none   => header ++ ['['] ++ [']']\n"
    "  | some p => header ++ ['['] ++ safeDisplay p ++ [']']"
)
RIVAL_NONE_APPENDS = _swap(_BASE, _IMPL, _NONE_APPENDS)

# --- U5 VERBATIM-BODY: the bracket content is the raw parameter value, with no
# canonical representation applied to it. Structure is PERFECT (header, both
# brackets, correct branch), so every clause U1-U4 attack still holds; the ONLY
# divergence is (P-body). This is the shape the port declared unrefutable; it is
# refuted below at a point described by hypothesis. Written in the same direct
# functional shape as U1-U4 (not `Id.run do`): the witness reasons about the
# result's LENGTH, and `unfold` does not reduce a `do` block far enough for the
# length simp set to see through it, so an imperative rival here would fail its
# own witness for a TACTIC reason rather than a spec one. Verified: with the
# imperative shape the witness does not hold of the rival ("omega could not
# prove the goal: No usable constraints found"); with this shape it does.
_VERBATIM_BODY = (
    "def implementation_actionLine (header : List Char) (param : Option (List Char)) :\n"
    "    List Char :=\n"
    "  match param with\n"
    "  | none   => header\n"
    "  | some p => header ++ ['['] ++ p ++ [']']"
)
RIVAL_VERBATIM_BODY = _swap(_BASE, _IMPL, _VERBATIM_BODY)

# --- U6 WRONG-OPERAND: the canonical representation IS applied, but to the wrong
# argument — the header instead of the parameter value. Also attacks (P-body),
# and it is a NEAR-MISS of U5 in the opposite direction: U5 keeps the operand and
# drops the representation, U6 keeps the representation and changes the operand.
# A rival the "just apply the representation somewhere" reading would admit.
_WRONG_OPERAND = (
    "def implementation_actionLine (header : List Char) (param : Option (List Char)) :\n"
    "    List Char :=\n"
    "  match param with\n"
    "  | none   => header\n"
    "  | some p => header ++ ['['] ++ safeDisplay header ++ [']']"
)
RIVAL_WRONG_OPERAND = _swap(_BASE, _IMPL, _WRONG_OPERAND)

# --- U7 SWAPPED-BRACKETS: both delimiters are emitted, but in the wrong ORDER —
# `header ++ [']'] ++ safeDisplay p ++ ['[']`, i.e. the rendering is closed before
# it is opened. Attacks (P-open) and (P-close) at their POSITIONS rather than at
# their presence, and it is the rival every length-counting witness in U1-U4 is
# structurally blind to: it has EXACTLY the length the spec demands, so the whole
# `congrArg List.length` technique cancels to a true equation and cannot refute
# it. Its witness therefore projects the result's HEAD (`List.head?`) instead of
# its length, which is a genuinely different discriminator and the reason this
# case is not subsumed by U1/U2.
_SWAPPED_BRACKETS = (
    "def implementation_actionLine (header : List Char) (param : Option (List Char)) :\n"
    "    List Char :=\n"
    "  match param with\n"
    "  | none   => header\n"
    "  | some p => header ++ [']'] ++ safeDisplay p ++ ['[']"
)
RIVAL_SWAPPED_BRACKETS = _swap(_BASE, _IMPL, _SWAPPED_BRACKETS)

# --- U8 FIRST-CODE-POINT-WRONG: the canonical representation IS applied to the
# right operand, and the delimiters and the LENGTH are perfect, but the first code
# point of the rendering is replaced by a fixed letter — `'X' :: (safeDisplay p).tail`.
# Attacks (P-body) as a PARTIAL-DOMAIN divergence: the rival agrees with the spec
# on every code point of the rendering except index 0. This is the lean instance of
# the nagini sibling's `first-char-wrong` case, which the port had recorded as
# having no expressible analogue on this carrier; it does have one, because the
# refutation can be stated over the `List.head?` projection under a hypothesis
# about the opaque term rather than over its length. Length-blind by construction
# (`'X' :: t` has the same length as `c :: t`), so U1-U4 cannot reach it and
# neither can U5/U6, whose witnesses are length equations.
_FIRST_CHAR_WRONG = (
    "def implementation_actionLine (header : List Char) (param : Option (List Char)) :\n"
    "    List Char :=\n"
    "  match param with\n"
    "  | none   => header\n"
    "  | some p => header ++ ['['] ++ ('X' :: (safeDisplay p).tail) ++ [']']"
)
RIVAL_FIRST_CHAR_WRONG = _swap(_BASE, _IMPL, _FIRST_CHAR_WRONG)


# ---- witnesses (each checked: elaborates vs rival, FAILS vs frozen) ----------
# Each derives `False` from a length equation: the postcondition equates the
# rival's output to `header ++ ['['] ++ safeDisplay p ++ [']']` (or `header`),
# and `congrArg List.length` turns that into an arithmetic identity in which the
# opaque `(safeDisplay p).length` appears on the spec side but the rival's own
# structure is short by a fixed amount — `omega` closes it. Inputs are chosen to
# VARY both binders across the lane (header ∈ {[], ['x'], ['h']}; param ∈
# {some ['a'], none}).
_P = "problem_spec_actionLine"
_I = "implementation_actionLine"

# U1 drop-brackets: header [], param some ['a']. Rival len = len(safeDisplay a);
# spec len = len(safeDisplay a) + 2.  (varies: header=[], param=some)
_WIT_DROP_BRACKETS = (
    f"example : ¬ {_P} [] (some ['a'])\n"
    f"    ({_I} [] (some ['a'])) := by\n"
    f"  unfold {_P} {_I}\n"
    "  intro h\n"
    "  have hl := congrArg List.length h\n"
    "  simp only [List.length_append, List.length_cons, List.length_nil,\n"
    "    Id.run, Id.pure_eq, Id.bind_eq] at hl\n"
    "  omega\n"
)

# U2 open-only: header ['x'], param some ['a']. Rival len = 1 + 1 + len(sd a);
# spec len = 1 + 1 + len(sd a) + 1.  (varies: header=['x'], param=some)
_WIT_OPEN_ONLY = (
    f"example : ¬ {_P} ['x'] (some ['a'])\n"
    f"    ({_I} ['x'] (some ['a'])) := by\n"
    f"  unfold {_P} {_I}\n"
    "  intro h\n"
    "  have hl := congrArg List.length h\n"
    "  simp only [List.length_append, List.length_cons, List.length_nil,\n"
    "    Id.run, Id.pure_eq, Id.bind_eq] at hl\n"
    "  omega\n"
)

# U3 drop-header: header ['h'], param some ['a']. Rival len = 1 + len(sd a) + 1;
# spec len = 1 + 1 + len(sd a) + 1.  (varies: header=['h'], param=some)
_WIT_DROP_HEADER = (
    f"example : ¬ {_P} ['h'] (some ['a'])\n"
    f"    ({_I} ['h'] (some ['a'])) := by\n"
    f"  unfold {_P} {_I}\n"
    "  intro h\n"
    "  have hl := congrArg List.length h\n"
    "  simp only [List.length_append, List.length_cons, List.length_nil,\n"
    "    Id.run, Id.pure_eq, Id.bind_eq] at hl\n"
    "  omega\n"
)

# U4 none-appends: header ['h'], param none. Rival len = 1 + 2; spec = len header
# = 1.  This is the ONLY witness on the `none` branch.  (varies: param=none)
_WIT_NONE_APPENDS = (
    f"example : ¬ {_P} ['h'] none\n"
    f"    ({_I} ['h'] none) := by\n"
    f"  unfold {_P} {_I}\n"
    "  intro h\n"
    "  have hl := congrArg List.length h\n"
    "  simp only [List.length_append, List.length_cons, List.length_nil,\n"
    "    Id.run, Id.pure_eq, Id.bind_eq] at hl\n"
    "  omega\n"
)

# ---- CONDITIONED witnesses for the (P-body) rivals ---------------------------
# A body divergence is invisible to a length count at a literal input, because the
# rival substitutes one unknown-length term for another. So these state the
# refutation at a point described by HYPOTHESIS: a disequation about the opaque
# term, which is exactly the technique an opaque carrier admits. Opacity makes the
# hypothesis satisfiable rather than blocking it — no tactic can derive `False`
# from a disequation between opaque terms — which is what the gate's consistency
# probe (a third build, triggered because these witnesses bind) confirms.

# U5 verbatim-body: header ['h'], param some ['a']. Under `(safeDisplay ['a']).length
# ≠ 1` the postcondition forces 1+1+1+1 = 1+1+len(sd ['a'])+1, i.e. len = 1, a
# contradiction; `omega` closes it. On gold both sides are the same opaque length
# and omega finds no usable constraint — a semantic non-refutation, as required.
# (varies: header=['h'], param=some)
_WIT_VERBATIM_BODY = (
    f"example (hsd : (safeDisplay ['a']).length ≠ 1) :\n"
    f"    ¬ {_P} ['h'] (some ['a'])\n"
    f"    ({_I} ['h'] (some ['a'])) := by\n"
    f"  unfold {_P} {_I}\n"
    "  intro h\n"
    "  have hl := congrArg List.length h\n"
    "  simp only [List.length_append, List.length_cons, List.length_nil,\n"
    "    Id.run, Id.pure_eq, Id.bind_eq] at hl\n"
    "  omega\n"
)

# U6 wrong-operand: header [], param some ['a']. The rival renders `safeDisplay []`
# where the spec demands `safeDisplay ['a']`; under the hypothesis that those two
# have different lengths the postcondition's length equation is false and `omega`
# closes it. Both operands appear, so the two opaque terms cannot cancel — which is
# what makes this discriminate where a plain length count cannot.
# (varies: header=[], param=some — a DIFFERENT point from U5)
_WIT_WRONG_OPERAND = (
    f"example (hsd : (safeDisplay ['a']).length ≠ (safeDisplay []).length) :\n"
    f"    ¬ {_P} [] (some ['a'])\n"
    f"    ({_I} [] (some ['a'])) := by\n"
    f"  unfold {_P} {_I}\n"
    "  intro h\n"
    "  have hl := congrArg List.length h\n"
    "  simp only [List.length_append, List.length_cons, List.length_nil,\n"
    "    Id.run, Id.pure_eq, Id.bind_eq] at hl\n"
    "  omega\n"
)

# ---- POSITIONAL witnesses (U7, U8) -------------------------------------------
# These two rivals have EXACTLY the spec's length, so the `congrArg List.length`
# technique every witness above uses cancels to a true equation and refutes
# nothing. They project the result's HEAD instead. The `Id.run` reduction happens
# on `h` FIRST (before the projection rather than after it) because `List.head?`
# of an unreduced `(do ...).run` term is not a list-head at all — Lean reports
# `Invalid field notation: Type of l is not known`, a syntactic failure that would
# occur on gold and on a wrong impl alike.
#
# The gold-side result was established by the type-revealing experiment, not by
# reading the message: after the reduction, `h` on the frozen solution has type
# `True` — `simp` PROVED the equation there — so `congrArg` has nothing to apply
# and the build fails BECAUSE gold satisfies the spec at this input. The same
# `has type True` appears against both positive controls and the imperative
# reshape, while against each rival `h` is a concrete false equation.

# U7 swapped-brackets: header [], param some ['a']. The rival's first code point
# is ']' where the spec demands '['; `simp` closes the resulting literal clash.
# No hypothesis, so no consistency probe.  (varies: header=[], param=some)
_WIT_SWAPPED_BRACKETS = (
    f"example : ¬ {_P} [] (some ['a'])\n"
    f"    ({_I} [] (some ['a'])) := by\n"
    f"  unfold {_P} {_I}\n"
    "  intro h\n"
    "  simp only [Id.run, Id.pure_eq, Id.bind_eq] at h\n"
    "  have hh := congrArg (fun l => l.head?) h\n"
    "  simp at hh\n"
)

# U8 first-code-point-wrong: header [], param some ['a']. The divergence is at
# index 0 of the RENDERING, so the projection skips the opening bracket
# (`l.tail.head?`). Conditioned on the opaque term: under the hypothesis that the
# representation of `['a']` does not itself begin with 'X', the postcondition's
# head equation is false. Stated over `.head?.getD` — the shape `simp` normalises
# the goal to — so the closing step is an exact application rather than a further
# rewrite. Opacity makes the hypothesis satisfiable; the gate's consistency probe
# confirms it.  (varies: header=[], param=some)
_WIT_FIRST_CHAR_WRONG = (
    f"example (hsd : (safeDisplay ['a']).head?.getD ']' ≠ 'X') :\n"
    f"    ¬ {_P} [] (some ['a'])\n"
    f"    ({_I} [] (some ['a'])) := by\n"
    f"  unfold {_P} {_I}\n"
    "  intro h\n"
    "  simp only [Id.run, Id.pure_eq, Id.bind_eq] at h\n"
    "  have hh := congrArg (fun l => l.tail.head?) h\n"
    "  simp [List.head?_append] at hh\n"
    "  exact hsd hh.symm\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness)
    # =====================================================================
    {
        "id": "pos-func-match",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_FUNC,
        "rationale": "structurally-different CORRECT impl: replace the "
        "`Id.run do`/`let mut`/post-match accumulator with a direct functional "
        "`match`, both branches returning the concatenation in one step. The "
        "value is identical on every input, so all five clauses (P-none, "
        "P-prefix, P-open, P-body, P-close) still hold; if this cannot verify "
        "the spec is SPEC-TOO-STRONG. Proof: after unfolding, each branch is "
        "definitionally equal, so `rfl` per branch closes (the `correct_` "
        "statement is byte-identical; no helper/axiom/sorry).",
    },
    {
        "id": "pos-early-return",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_EARLYRETURN,
        "rationale": "a second structurally-different CORRECT impl: keep the "
        "`Id.run do` monad but branch with two early `return`s instead of a "
        "mutable accumulator with a post-match fallthrough. Same value on every "
        "input, so the postcondition still holds on both branches; must verify "
        "(else SPEC-TOO-STRONG). Proof closes by `rfl` per branch; the "
        "`correct_` statement is byte-identical and nothing is assumed.",
    },

    # =====================================================================
    # ADMISSIBILITY
    # =====================================================================
    {
        "id": "admiss-present-and-absent",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "the obligation is discharged by evaluation at two "
        "representative reporting-shaped inputs — a header with a present "
        "parameter and the same header with an absent parameter — via `have` "
        "blocks prepended to the frozen tactic body, then the general "
        "obligation is closed verbatim. Verifies (else the behavior is "
        "unsatisfiable at the normal input shapes the F2P exercises — the "
        "analogue of PRECOND-TOO-STRONG). Nothing is assumed: no new "
        "declaration, the `correct_` statement is byte-identical, and the "
        "ground instances are `have`s inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / REJECT rivals
    # =====================================================================
    {
        "id": "drop-brackets",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_DROP_BRACKETS,
        "refinement": "appends the parameter rendering with NO surrounding "
        "delimiters. A faithful patch that wrote the safe representation "
        "without the enclosing `[` … `]` would drop the brackets the reporter "
        "puts around every parameter token, so the trace line would lose its "
        "bracketed field entirely; the F2P fnmatch lines that require the "
        "bracketed parameter around the rendered value would then FAIL — it "
        "does NOT resolve.",
        "rationale": "REJECT from (P-open) and (P-close): the result must be "
        "`header ++ ['['] ++ safeDisplay p ++ [']']` but this omits BOTH "
        "brackets, so it is two code points short on every present-parameter "
        "input regardless of what `safeDisplay` returns.",
        "witness": _WIT_DROP_BRACKETS,
    },
    {
        "id": "open-bracket-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_OPEN_ONLY,
        "refinement": "emits the opening bracket but omits the closing one. A "
        "patch producing a one-sided delimiter would render the token as "
        "`[value` (no trailing `]`), so any F2P line requiring the closing "
        "bracket before the next field would FAIL — it does NOT resolve. This "
        "is a NEAR-MISS of drop-brackets: it agrees with the spec on the "
        "opening bracket, so it is refuted at its own distinguishing input.",
        "rationale": "REJECT from (P-close): the two-sided delimiter requires a "
        "trailing `']'`, so the result is exactly one code point short on every "
        "present-parameter input; the opaque `safeDisplay p` cancels in the "
        "length equation.",
        "witness": _WIT_OPEN_ONLY,
    },
    {
        "id": "drop-header",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_DROP_HEADER,
        "refinement": "emits only the bracketed rendering and DROPS the header "
        "prefix. In the repo the header carries the step/scope/fixture framing "
        "already written to the terminal; a patch that discarded it would erase "
        "the `SETUP    S arg_same` framing that every F2P line matches before "
        "the bracketed value, so those lines FAIL — it does NOT resolve. This "
        "is the referentially-transparent analogue of the nagini frame-mutation "
        "rival: the unchanged framing prefix is not passed through verbatim.",
        "rationale": "REJECT from (P-prefix): the result must BEGIN with the "
        "unchanged header, but this rival omits it, so on a non-empty header "
        "the result is `len header` code points short.",
        "witness": _WIT_DROP_HEADER,
    },
    {
        "id": "none-appends-empty-brackets",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_NONE_APPENDS,
        "refinement": "on the ABSENT-parameter branch it appends empty "
        "brackets `[]` instead of leaving the header unchanged. A patch that "
        "unconditionally wrote the bracketed field — even when the fixture "
        "carries no parameter value — would add a spurious `[]` to every "
        "parameterless SETUP/TEARDOWN line, so the P2P lines that expect a bare "
        "header with no bracket (the parameterless fixtures) would FAIL — it "
        "does NOT resolve. Partial-domain: the present branch is left correct; "
        "it diverges only on `none`.",
        "rationale": "REJECT from (P-none): the absent case must be EXACTLY the "
        "header, but this emits `header ++ ['['] ++ [']']`, two code points too "
        "long. This is the ONLY rival on the `none` branch, so it is what "
        "discriminates the `param` binder's absent value.",
        "witness": _WIT_NONE_APPENDS,
    },
    {
        "id": "verbatim-body",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_VERBATIM_BODY,
        "refinement": "puts the parameter value into the brackets as-is, with no "
        "canonical size-limited representation applied to it. Its faithful real "
        "patch is the one that renders the value by plain textual coercion, so a "
        "textual parameter appears bare inside the brackets rather than in the "
        "canonical form the reporter's representation produces, and a "
        "non-textual value is coerced unsafely instead of rendered. The F2P "
        "lines that match the canonical rendering of the parameter, and the one "
        "that requires a non-textual value to render without warning, both FAIL "
        "— it does NOT resolve. Structurally PERFECT (header, both brackets, "
        "correct branch), so it is the near-miss that isolates (P-body) alone.",
        "rationale": "REJECT from (P-body): the bracket content must be "
        "`safeDisplay p`, the canonical representation of the value, but this "
        "rival supplies the raw `p`. No literal input decides this (the two "
        "terms have no computable relation), so the witness refutes it at a "
        "point described by hypothesis — `(safeDisplay ['a']).length ≠ 1` — "
        "under which the postcondition's length equation is false. The gate's "
        "consistency probe confirms that hypothesis is satisfiable, which "
        "opacity guarantees. This rival, with wrong-operand-representation, is "
        "what makes the reject lane test the modeled change at all: the four "
        "structural rivals above still discriminate against a spec whose "
        "(P-body) clause has been neutered, so they do not cover this clause.",
        "witness": _WIT_VERBATIM_BODY,
    },
    {
        "id": "wrong-operand-representation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_WRONG_OPERAND,
        "refinement": "applies the canonical representation, but to the framing "
        "text instead of to the parameter value. A patch that passed the wrong "
        "argument to the representation step would print a rendering of the "
        "line's own framing inside the brackets in place of the parameter, so "
        "every F2P line that matches the parameter's rendered value FAILS — it "
        "does NOT resolve. It is the opposite-direction near-miss of "
        "verbatim-body: that one keeps the operand and drops the "
        "representation, this one keeps the representation and changes the "
        "operand, so neither subsumes the other.",
        "rationale": "REJECT from (P-body): the clause pins the bracket content "
        "to the representation OF THE PARAMETER, `safeDisplay p` — not to the "
        "representation of something else. Because both operands occur, the two "
        "opaque terms cannot cancel in the length equation, so the witness "
        "refutes it under the hypothesis that their lengths differ; the "
        "consistency probe confirms that is satisfiable. This closes the reading "
        "that (P-body) merely demands the representation be applied SOMEWHERE.",
        "witness": _WIT_WRONG_OPERAND,
    },
    {
        "id": "swapped-brackets",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_SWAPPED_BRACKETS,
        "refinement": "emits both delimiters but in the wrong ORDER, closing the "
        "rendering before opening it. A patch that transposed the two delimiter "
        "literals would render the parameter field as `]value[` instead of "
        "`[value]`, so every F2P line that matches the opening bracket "
        "immediately after the framing text FAILS — it does NOT resolve. Both "
        "delimiters are present and the field is the right width, which is "
        "exactly what makes it a near-miss that a presence-only or width-only "
        "reading of the delimiter clauses would admit.",
        "rationale": "REJECT from (P-open) and (P-close) at their POSITIONS: the "
        "clauses pin the opening `'['` BEFORE the rendering and the closing "
        "`']'` AFTER it, not merely that both occur somewhere. This rival has "
        "EXACTLY the length the spec demands, so it is the one case in the lane "
        "that no length equation can refute — the four structural witnesses "
        "(U1-U4) and both body witnesses (U5/U6) all reduce to a true "
        "arithmetic identity against it. Its witness projects the result's HEAD "
        "instead, a genuinely different discriminator, which is why this case is "
        "not subsumed by drop-brackets or open-bracket-only.",
        "witness": _WIT_SWAPPED_BRACKETS,
    },
    {
        "id": "first-code-point-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_FIRST_CHAR_WRONG,
        "refinement": "applies the canonical representation to the right operand "
        "and keeps both delimiters, but replaces the FIRST code point of the "
        "rendering with a fixed letter. A patch that mangled the leading code "
        "point of every rendered parameter would emit that letter where the "
        "canonical form's own first code point belongs, so the F2P lines that "
        "match the parameter's rendered value from its first character FAIL — it "
        "does NOT resolve. Partial-domain: it agrees with the spec on every code "
        "point of the rendering except index 0.",
        "rationale": "REJECT from (P-body) as a PARTIAL-DOMAIN divergence: the "
        "clause pins the bracket content to `safeDisplay p` in full, not up to "
        "its first code point. This is the lean instance of the nagini sibling's "
        "`first-char-wrong` rival, which this port had recorded as having no "
        "expressible analogue on an opaque carrier; it does have one — the "
        "refutation is stated over the `List.head?` projection under a hypothesis "
        "about the opaque term, the same conditioning technique U5/U6 use for "
        "length, so opacity blocks it no more here than there. Length-preserving "
        "by construction (`'X' :: t` and `c :: t` have equal length), so neither "
        "the structural witnesses nor U5/U6 — all length equations — can reach "
        "it. The consistency probe confirms the hypothesis is satisfiable.",
        "witness": _WIT_FIRST_CHAR_WRONG,
    },
]
