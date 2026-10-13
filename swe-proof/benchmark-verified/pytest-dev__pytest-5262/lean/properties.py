"""properties.py — G-PBT falsification battery for pytest-dev__pytest-5262 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with every obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total behavior over a character sequence):

  mode (bufferMode : List Char) : List Char
      result = stripBinary bufferMode

  ``stripBinary`` is a front-recursive fold that keeps every character except the
  binary-indicator character ``'b'``, in order: ``stripBinary (c :: cs) =
  (if c = 'b' then stripBinary cs else c :: stripBinary cs)``. The reported
  text-stream mode is exactly the underlying stream's mode string with every
  binary-indicator character removed and every OTHER character preserved in its
  original order.

  Load-bearing postcondition clause (the whole of ``problem_spec_mode``):
    (P-eq) result = stripBinary bufferMode — the EXACT per-character deletion.
           This single equality subsumes two observations that a weaker spec
           might split: (a) every binary-indicator character is removed — the
           behavior the reporting scenario demands — AND (b) every other
           character is preserved unchanged and in order. A rival can break
           either half independently, so both are probed below.

  ``stripBinary`` is fully GROUNDED in the input (it unfolds character by
  character over ``bufferMode``); it is NOT an opaque answer key, so there is no
  "wrong echo" — any implementation satisfying (P-eq) has actually performed the
  deletion. The pre-patch behavior returned the underlying stream's mode string
  verbatim (the binary marker NOT removed); that is exactly the ``r-keep-marker``
  rival below, and it fails (P-eq) whenever a marker is present.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and DEMONSTRATED so. Lean is
    referentially transparent: the input ``List Char`` carries no heap
    permission, there is no read-only half-permission to overwrite and no
    aliasing to exploit. The nagini frame-mutation rival (a store into the
    read-only input, rejected for insufficient permission) has NO expressible
    instance here. Demonstration rather than assertion: the closest expressible
    analogue — bind a local mutable copy of the input, clobber its head, then run
    the frozen deletion over the ORIGINAL binding — VERIFIES against the frozen
    obligation with the frozen proof text unchanged. That is the correct outcome
    and precisely why the case cannot be ported: the "mutation" is unobservable,
    so the impl remains extensionally the frozen one and there is nothing for
    (P-eq) to reject. Shipping it as ``expect="reject"`` would be a case that
    fails only if the carrier stops being referentially transparent; shipping it
    as ``expect="verify"`` would duplicate the positive controls. No substitute is
    fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. (P-eq) is grounded in the input carrier
    (``stripBinary bufferMode`` unfolds element-by-element); the bundle declares
    no ``opaque``/``axiom``, so there is nothing an implementation could echo
    without doing the deletion. In its place the battery carries honest
    cheapest-implementation POSITIVE CONTROLS.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the character
    domain but diverging elsewhere: one that keeps EVERY character (no deletion —
    the pre-patch identity), one that keeps a LEADING marker only, and one that
    over-deletes a non-marker character. (P-eq) rejects each on the sub-domain
    where it diverges. Two further rivals were added by AUDIT to cover axes the
    three above all leave fixed: ``wrong-needle-target`` varies WHICH character is
    deleted (the three originals all target exactly 'b' and differ only in the
    positions they act on), and ``reverse-order-output`` varies the ORDER of the
    output (the three originals only drop-or-keep in place, so all are
    order-preserving and none witnesses the "in their original order" half of
    (P-eq)).

  RESOLVE-BREAK vs SPEC-STRENGTH — stated honestly per rival. The shipped visible
  test observes only that the reported mode carries no binary indicator, and the
  runtime normalizes its mode strings (measured by enumerating every mode
  argument of length <= 4 it accepts: exactly 'rb','wb','ab','xb','rb+','ab+',
  'xb+' — the indicator never leads and never repeats). So only
  ``keep-marker-identity`` and ``wrong-needle-target`` have faithful patches that
  fail that visible test. ``keep-leading-marker``, ``over-delete-non-marker`` and
  ``reverse-order-output`` diverge from the exact deletion on the MODELED domain
  (an unrestricted ``List Char``) while a faithful patch of each would still pass
  the visible test; they stand as spec-strength probes, and each ``refinement``
  below says so rather than over-claiming a resolve-break.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form —
so a rejection alone attributes nothing to the spec. Every ``expect="reject"``
case therefore carries a Lean snippet proving the rival CONTRADICTS the spec at
one concrete input. Each is stated directly against the spec predicate at
``decide``-able character literals, and each was checked to hold of its rival and
to FAIL on the frozen solution (so it discriminates rather than asserting a
tautology). The five witnesses probe five DISTINCT inputs, one per rival's
divergence sub-domain. Each gold-side failure was additionally read to confirm it
is a SEMANTIC refutation and not a syntactic accident: every one is
``Tactic `decide` proved that the proposition ¬(<the frozen loop at that literal>
= stripBinary <that literal>) is false`` — i.e. the frozen impl DOES satisfy
(P-eq) there, which is exactly the discrimination the two-build check is meant to
establish. No gold-side failure is an unknown identifier, a type error, an
unfolding failure, or a timeout.

AXIOM lane: DROPPED. The nagini bundle's ``AXIOM_TESTS`` (the deep-model
identity-soundness probe validating the fold == the real stdlib character
deletion) belong to G-AX, which the G-PBT spec lane ignores; meta.json records
the A-reference deep model and G-AX validated it separately.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-5262"

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
    "-- impl-start\n"
    "def implementation_mode (bufferMode : List Char) : List Char := Id.run do\n"
    "  let mut acc : List Char := []\n"
    "  for c in bufferMode do\n"
    "    if c ≠ 'b' then\n"
    "      acc := acc ++ [c]\n"
    "  return acc\n"
)

# The FULL body of the proof region (frozen helper `mode_forIn_helper` + the
# obligation). A positive that reshapes the impl into a non-loop form reproves
# inside here; the `theorem correct_mode` STATEMENT is preserved byte-identically
# (only its tactic body — and, where a different helper shape is needed, the body
# of the already-frozen `mode_forIn_helper` — changes; no NEW theorem/lemma name
# and no new axiom/sorry is introduced).
_PROOF = _BASE[_BASE.index("-- proof-start"):_BASE.index("-- proof-end")]
assert _BASE.count(_PROOF) == 1

# The frozen obligation's opening two tactic lines — the injection point for the
# admissibility ground instance (a `have` prepended before the frozen body).
_INTRO = "  intro bufferMode\n  unfold problem_spec_mode implementation_mode"
assert _BASE.count(_INTRO) == 1


# === POSITIVE CONTROLS (soundness) — structurally different but CORRECT ======
# implementations that MUST verify. If a faithful correct implementation cannot
# satisfy the frozen obligation, the spec is SPEC-TOO-STRONG. Each keeps the
# `theorem correct_mode` statement byte-identical and re-proves it for the new
# shape; none introduces a helper name, an axiom, or an assumption token beyond
# the frozen set.

# --- pos-cheap: return the grounded fold directly (P-eq trivially). -----------
# The impl IS `stripBinary bufferMode`; after `intro` the two sides are
# definitionally equal, so `rfl` closes. The frozen helper is dropped from the
# proof region (its name need not persist — only `correct_mode`'s statement is
# pinned; dropping a frozen theorem introduces no NEW name and no assumption).
_CHEAP_IMPL = (
    "-- impl-start\n"
    "def implementation_mode (bufferMode : List Char) : List Char :=\n"
    "  stripBinary bufferMode\n"
)
_CHEAP_PROOF = (
    "-- proof-start\n"
    "theorem correct_mode : ∀ bufferMode : List Char,\n"
    "    problem_spec_mode bufferMode (implementation_mode bufferMode) := by\n"
    "  intro bufferMode\n"
    "  rfl\n"
)
POS_CHEAP = _swap(_swap(_BASE, _IMPL, _CHEAP_IMPL), _PROOF, _CHEAP_PROOF)

# --- pos-filter: express the deletion as `List.filter` (a genuinely different
# implementation shape than the frozen `Id.run do … for` accumulator loop). ----
# Correct — filtering out `'b'` keeps exactly the non-marker characters in order.
# Re-proved by restating the ALREADY-FROZEN helper `mode_forIn_helper` over the
# filter form (its STATEMENT changes; it is NOT the `correct_` obligation and its
# name stays in the frozen declaration set, so no NEW theorem/lemma is declared).
_FILTER_IMPL = (
    "-- impl-start\n"
    "def implementation_mode (bufferMode : List Char) : List Char :=\n"
    "  bufferMode.filter (fun c => c ≠ 'b')\n"
)
_FILTER_PROOF = (
    "-- proof-start\n"
    "theorem mode_forIn_helper (xs : List Char) :\n"
    "    xs.filter (fun c => c ≠ 'b') = stripBinary xs := by\n"
    "  induction xs with\n"
    "  | nil => rfl\n"
    "  | cons a as ih =>\n"
    "    rw [List.filter_cons, stripBinary]\n"
    "    by_cases h : a = 'b' <;> simp_all\n"
    "\n"
    "theorem correct_mode : ∀ bufferMode : List Char,\n"
    "    problem_spec_mode bufferMode (implementation_mode bufferMode) := by\n"
    "  intro bufferMode\n"
    "  unfold problem_spec_mode implementation_mode\n"
    "  exact mode_forIn_helper bufferMode\n"
)
POS_FILTER = _swap(_swap(_BASE, _IMPL, _FILTER_IMPL), _PROOF, _FILTER_PROOF)


# === ADMISSIBILITY ===========================================================
# The frozen `correct_mode` theorem carries NO precondition hypothesis (the
# behavior is total, so `∀` is unguarded), so the nagini precondition-admission
# probe has no binder to attack. The honest analogue: discharge the spec
# predicate by evaluation at the representative reporting-shaped input — the
# FD-capture buffer mode "rb+" = ['r','b','+'], which carries the binary marker
# and a trailing '+', exactly the shape the F2P exercises — inside the proof
# region, before the frozen obligation. If that ground instance could not be
# discharged the modeled behavior would be unsatisfiable at exactly the shape the
# F2P exercises (the analogue of PRECOND-TOO-STRONG). Nothing is assumed: no new
# declaration, the `correct_mode` statement is byte-identical, and the ground
# instance is a `have` inside the existing tactic body.
_ADMISS_BLOCK = (
    "  have _ground : problem_spec_mode ['r', 'b', '+']\n"
    "      (implementation_mode ['r', 'b', '+']) := by\n"
    "    unfold problem_spec_mode implementation_mode\n"
    "    decide\n"
    + _INTRO
)
ADMISS = _swap(_BASE, _INTRO, _ADMISS_BLOCK)


# === UNIQUENESS / REJECT rivals ==============================================
# Wrong implementations sharing the frozen spec that MUST be rejected. Each
# carries (a) the refinement argument that its faithful real patch would NOT
# resolve the F2P — so a verifying rival would be a true
# verify-does-not-imply-resolve break, not an artifact — and (b) a refutation
# witness pinning the violation at one concrete input, checked to hold of the
# rival and to FAIL on the frozen solution.

# --- r-keep-marker: keep EVERY character (no deletion). This is the PRE-PATCH
# identity: the reported mode is the underlying stream's mode string verbatim. --
_KEEPMARKER_IMPL = (
    "-- impl-start\n"
    "def implementation_mode (bufferMode : List Char) : List Char := Id.run do\n"
    "  let mut acc : List Char := []\n"
    "  for c in bufferMode do\n"
    "    acc := acc ++ [c]\n"
    "  return acc\n"
)
RIVAL_KEEPMARKER = _swap(_BASE, _IMPL, _KEEPMARKER_IMPL)

# --- r-keep-leading: delete the binary marker everywhere EXCEPT the first
# character (a leading marker survives). ---------------------------------------
_KEEPLEAD_IMPL = (
    "-- impl-start\n"
    "def implementation_mode (bufferMode : List Char) : List Char := Id.run do\n"
    "  let mut acc : List Char := []\n"
    "  let mut first : Bool := true\n"
    "  for c in bufferMode do\n"
    "    if first ∨ c ≠ 'b' then\n"
    "      acc := acc ++ [c]\n"
    "    first := false\n"
    "  return acc\n"
)
RIVAL_KEEPLEAD = _swap(_BASE, _IMPL, _KEEPLEAD_IMPL)

# --- r-over-delete: delete the binary marker AND also drop the '+' character. -
_OVERDEL_IMPL = (
    "-- impl-start\n"
    "def implementation_mode (bufferMode : List Char) : List Char := Id.run do\n"
    "  let mut acc : List Char := []\n"
    "  for c in bufferMode do\n"
    "    if c ≠ 'b' ∧ c ≠ '+' then\n"
    "      acc := acc ++ [c]\n"
    "  return acc\n"
)
RIVAL_OVERDEL = _swap(_BASE, _IMPL, _OVERDEL_IMPL)

# --- r-wrong-needle: delete the WRONG character. Filters out 'r' instead of the
# binary indicator, so the indicator SURVIVES untouched. Added by audit: the
# three rivals above all target exactly 'b' and differ only in WHICH POSITIONS
# they delete at, leaving the identity of the deleted character unprobed. This is
# also the strongest refinement case in the battery — its faithful patch fails
# the shipped visible test at every reachable mode string. -------------------
_WRONGNEEDLE_IMPL = (
    "-- impl-start\n"
    "def implementation_mode (bufferMode : List Char) : List Char := Id.run do\n"
    "  let mut acc : List Char := []\n"
    "  for c in bufferMode do\n"
    "    if c ≠ 'r' then\n"
    "      acc := acc ++ [c]\n"
    "  return acc\n"
)
RIVAL_WRONGNEEDLE = _swap(_BASE, _IMPL, _WRONGNEEDLE_IMPL)

# --- r-reverse-order: delete exactly the right characters but emit them in
# REVERSED order (prepend instead of append). Added by audit: the result is a
# permutation of the correct one, so every rival above (which only ever drops or
# keeps characters in place) leaves the ORDER half of (P-eq) unprobed. This is
# the case that shows (P-eq) is a list equality and not a multiset/membership
# claim — the exact reading `stripBinary` would collapse to if the spec had been
# written as "the result contains no marker and no non-marker was lost". ------
_REVORDER_IMPL = (
    "-- impl-start\n"
    "def implementation_mode (bufferMode : List Char) : List Char := Id.run do\n"
    "  let mut acc : List Char := []\n"
    "  for c in bufferMode do\n"
    "    if c ≠ 'b' then\n"
    "      acc := c :: acc\n"
    "  return acc\n"
)
RIVAL_REVORDER = _swap(_BASE, _IMPL, _REVORDER_IMPL)


# ---- witnesses (each checked: elaborates vs rival, fails vs frozen) ----------
_P = "problem_spec_mode"
_I = "implementation_mode"

# input ['r','b','+'] (the FD-capture mode): spec = ['r','+']; keep-marker keeps
# the 'b' -> ['r','b','+'], violating (P-eq).
_WIT_KEEPMARKER = (
    f"example : ¬ {_P} ['r', 'b', '+'] ({_I} ['r', 'b', '+']) := by\n"
    f"  unfold {_P} {_I}\n"
    "  decide\n"
)

# input ['b','r'] (leading marker): spec = ['r']; keep-leading keeps the leading
# 'b' -> ['b','r'], violating (P-eq) only at a leading-marker input.
_WIT_KEEPLEAD = (
    f"example : ¬ {_P} ['b', 'r'] ({_I} ['b', 'r']) := by\n"
    f"  unfold {_P} {_I}\n"
    "  decide\n"
)

# input ['w','+'] (no marker, has '+'): spec = ['w','+']; over-delete drops the
# '+' -> ['w'], violating (P-eq) on the preserve-non-marker half.
_WIT_OVERDEL = (
    f"example : ¬ {_P} ['w', '+'] ({_I} ['w', '+']) := by\n"
    f"  unfold {_P} {_I}\n"
    "  decide\n"
)

# input ['r','b','+'] (the FD-capture mode): spec = ['r','+']; the wrong-needle
# rival deletes 'r' and KEEPS the marker -> ['b','+'], violating (P-eq) on the
# marker-removal half at the very input the reporting scenario produces.
_WIT_WRONGNEEDLE = (
    f"example : ¬ {_P} ['r', 'b', '+'] ({_I} ['r', 'b', '+']) := by\n"
    f"  unfold {_P} {_I}\n"
    "  decide\n"
)

# input ['r','+'] (no marker, two distinct survivors): spec = ['r','+']; the
# reverse-order rival emits ['+','r'] — same multiset, wrong order, violating
# (P-eq) on the ORDER half alone. Note the input carries NO marker, so this
# isolates ordering from deletion entirely.
_WIT_REVORDER = (
    f"example : ¬ {_P} ['r', '+'] ({_I} ['r', '+']) := by\n"
    f"  unfold {_P} {_I}\n"
    "  decide\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness)
    # =====================================================================
    {
        "id": "pos-cheap-grounded-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_CHEAP,
        "rationale": "honest cheapest implementation: return the GROUNDED fold "
        "`stripBinary bufferMode` directly. The fold is fully unfolded over the "
        "input — not an opaque answer key — so this is a faithful one-liner that "
        "MUST satisfy (P-eq) `result = stripBinary bufferMode`; if it cannot, the "
        "postcondition is SPEC-TOO-STRONG. Proof: after `intro` the two sides are "
        "definitionally equal, so `rfl` closes (the `correct_mode` statement is "
        "kept byte-identical; no new declaration, axiom, or assumption token).",
    },
    {
        "id": "pos-filter-shape",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_FILTER,
        "rationale": "structurally-different CORRECT implementation: express the "
        "deletion with `List.filter (· ≠ 'b')` instead of the frozen `Id.run do … "
        "for` accumulator loop. Filtering keeps exactly the non-marker characters "
        "in order, so (P-eq) still holds; must verify (else SPEC-TOO-STRONG). "
        "Re-proved by restating the ALREADY-FROZEN helper `mode_forIn_helper` over "
        "the filter form (its own statement changes; its name stays in the frozen "
        "declaration set, and the `correct_mode` obligation statement is "
        "byte-identical — no NEW theorem/lemma, axiom, or assumption token).",
    },

    # =====================================================================
    # ADMISSIBILITY
    # =====================================================================
    {
        "id": "admiss-fd-capture-mode",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "the obligation is discharged by `decide` at the "
        "representative reporting-shaped input ['r','b','+'] (the FD-capture buffer "
        "mode carrying the binary marker and a trailing '+'), then the frozen "
        "obligation is closed verbatim. Verifies (else the behavior is "
        "unsatisfiable at the normal input — the analogue of PRECOND-TOO-STRONG). "
        "Nothing is assumed: no new declaration, the `correct_mode` statement is "
        "byte-identical, and the ground instance is a `have` inside the existing "
        "tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / REJECT rivals
    # =====================================================================
    {
        "id": "keep-marker-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_KEEPMARKER,
        "refinement": "this IS the pre-patch behavior: with no dedicated property "
        "the reported mode falls through to the underlying stream's mode string "
        "verbatim, so the binary marker is NOT removed. Under FD capture that "
        "underlying mode carries the marker, so the reported mode still contains it "
        "and the F2P assertion (that the reported mode has no binary marker) FAILS. "
        "A faithful real patch that performs no character deletion does NOT resolve "
        "— it is the very failure the fix removes.",
        "rationale": "REJECT from (P-eq): keeping every character makes "
        "`result = bufferMode`, but `bufferMode ≠ stripBinary bufferMode` whenever "
        "a binary marker is present. partial-domain: correct only on inputs that "
        "already contain no marker, wrong on every input that carries one.",
        "witness": _WIT_KEEPMARKER,
    },
    {
        "id": "keep-leading-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_KEEPLEAD,
        "refinement": "the real deletion removes EVERY binary marker including a "
        "leading one; this rival keeps the head character unconditionally, so any "
        "mode string that begins with the marker still reports a leading marker. "
        "HONESTY BOUND (measured, not argued): the runtime normalizes its mode "
        "strings so the binary indicator is never in first position — enumerating "
        "every mode argument of length <= 4 the runtime accepts yields exactly "
        "{'rb','wb','ab','xb','rb+','ab+','xb+'}, none leading with the marker and "
        "none repeating it. So on the REACHABLE sub-domain this rival agrees with "
        "the faithful deletion and its patch would still pass the shipped visible "
        "test. Its standing is therefore as a SPEC-STRENGTH probe over the modeled "
        "domain, not as a resolve-break: the modeled carrier is an unrestricted "
        "`List Char`, ['b','r'] is a legitimate input of the modeled behavior, and "
        "(P-eq) must pin the head like every other position — a spec that special-"
        "cased the head would be satisfied by an impl that is NOT the exact "
        "deletion. See `wrong-needle-target` for the rival whose faithful patch "
        "does demonstrably fail the visible test.",
        "rationale": "REJECT from (P-eq): when the input begins with the marker the "
        "result keeps the leading marker, so `result ≠ stripBinary bufferMode` "
        "(which deletes it). A genuine partial-domain rival: correct on every input "
        "whose first character is not the marker, wrong on leading-marker inputs — "
        "the head the front-recursive fold peels first.",
        "witness": _WIT_KEEPLEAD,
    },
    {
        "id": "over-delete-non-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_OVERDEL,
        "refinement": "the real deletion removes ONLY the binary marker and "
        "preserves every OTHER character; this rival also drops the '+' character, "
        "so the FD-capture mode 'rb+' reports 'r' instead of 'r+' — a divergence at "
        "a REACHABLE input (measured: 'rb+' and 'ab+'/'xb+' are among the mode "
        "strings the runtime actually produces). HONESTY BOUND: the shipped visible "
        "test observes only marker-ABSENCE, which this rival still satisfies, so it "
        "is not a visible-test break; a consumer reading the reported mode for "
        "read/write/append capability (the '+' marks updatable) would nonetheless "
        "mis-classify the stream. Its standing is as the probe that (P-eq) pins the "
        "PRESERVE half and not merely marker-absence: a marker-absence-only spec "
        "would admit it, and the equality does not.",
        "rationale": "REJECT from (P-eq): `stripBinary` preserves every non-marker "
        "character, so dropping '+' makes the result a character short of "
        "`stripBinary bufferMode`. This break is on the PRESERVE-non-marker half of "
        "(P-eq), independent of marker removal — confirming the equality pins BOTH "
        "'remove every marker' AND 'preserve everything else in order'; a "
        "marker-absent-only spec would be too weak and this case pins that. "
        "partial-domain: correct on modes without '+', wrong on modes with one.",
        "witness": _WIT_OVERDEL,
    },
    {
        "id": "wrong-needle-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_WRONGNEEDLE,
        "refinement": "this deletes the WRONG character: it strips 'r' and leaves "
        "the binary indicator in place. The reported mode therefore still carries "
        "the indicator at every mode string the runtime actually produces "
        "(measured: 'rb','wb','ab','xb','rb+','ab+','xb+' all retain it), so the "
        "shipped visible test — which asserts the reported mode contains no binary "
        "indicator — FAILS on all of them. This is the battery's strongest "
        "refinement case: a faithful real patch that filters the wrong character "
        "demonstrably does NOT resolve, at every reachable input rather than only "
        "at a modeled one.",
        "rationale": "REJECT from (P-eq): `stripBinary` deletes 'b' and preserves "
        "'r'; this rival does the exact opposite, so on any input containing either "
        "character the result differs from `stripBinary bufferMode`. Added by audit "
        "to probe the one axis the other rivals share and never vary — the IDENTITY "
        "of the deleted character. The three pre-existing rivals all target exactly "
        "'b' and differ only in which positions they act on, so none of them would "
        "detect a spec that pinned 'delete some one character' rather than 'delete "
        "the binary indicator'.",
        "witness": _WIT_WRONGNEEDLE,
    },
    {
        "id": "reverse-order-output",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_REVORDER,
        "refinement": "this deletes exactly the right characters but reports them "
        "in reversed order, so the FD-capture mode 'rb+' would report '+r' instead "
        "of 'r+'. HONESTY BOUND: the shipped visible test observes only marker-"
        "absence, which a reversal preserves, so this is not a visible-test break; "
        "any consumer parsing the reported mode positionally (the leading character "
        "carries the read/write/append intent) would mis-read the stream. Its "
        "standing is as the probe that (P-eq) is an ORDERED list equality.",
        "rationale": "REJECT from (P-eq): the result is a PERMUTATION of "
        "`stripBinary bufferMode` — same characters, same multiplicities, wrong "
        "order — so it satisfies every membership/multiset reading of the clause "
        "while failing the list equality. Added by audit: the three pre-existing "
        "rivals only ever drop or retain characters in place, so all of them are "
        "order-preserving and none witnesses the 'in their original order' half of "
        "(P-eq) that the docstring claims is load-bearing. The witness input "
        "['r','+'] contains NO marker at all, which isolates ordering from deletion: "
        "a spec asserting only 'no marker survives and no non-marker is lost' would "
        "admit this rival, and the equality does not.",
        "witness": _WIT_REVORDER,
    },
]
