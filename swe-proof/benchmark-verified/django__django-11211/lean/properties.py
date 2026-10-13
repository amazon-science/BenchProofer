"""properties.py — G-PBT falsification battery for django__django-11211 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_normalizeKey`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one behavior, a pure input→output map):

  normalizeKey (value : UuidValue) : UuidValue
               result = canonicalValue value

  The prepared value is FULLY pinned to the input: an absent value stays absent,
  an already-canonical identifier is returned unchanged, and a textual spelling
  is decoded to the one canonical identifier it denotes. The single
  postcondition clause leaves no output component free, so two values denoting
  the same identifier are prepared to the SAME canonical value regardless of the
  shape each arrived in. There is exactly one input binder (``value``) and one
  independent top-level clause (the equality against ``canonicalValue value``).

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    the sole input ``value`` is passed by value; there is no read-only heap
    half-permission to overwrite and no aliasing to exploit. The nagini sibling's
    two framing rivals (writing the read-only input's join key, or both facets)
    have no expressible instance here; no substitute is fabricated for them.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is an equality against a
    term (``canonicalValue value``) built ONLY from the input by a fully-unfolded
    deep model (``canonicalValue`` / ``decodeHex``); the bundle declares no
    ``opaque``/``axiom``, so there is nothing an implementation could echo without
    doing the work. In its place the battery carries honest positive controls
    that must verify.

  * PARTIAL-DOMAIN / VALUE — the real attacks, and the ONLY F2P-faithful class.
    The behavior the fix introduces (and the F2P exercises) is the textual→
    canonical conversion: on an absent value and on an already-canonical
    identifier the pinned result equals the input, which is exactly what the
    pre-fix identity pass-through also returns — so gold and the pre-fix behavior
    coincide OFF the textual constructor and differ only ON it. Every rival whose
    faithful real patch would fail the F2P must therefore diverge on a textual
    spelling. The three uniqueness rivals below all attack that clause: the
    pre-fix identity (no conversion at all), a fabricated constant identifier,
    and a near-miss that decodes the digits without positional weight.

CASE-COUNT vs NAGINI. The nagini sibling contracted a three-facet ``Value``
(is_none / canon / key) with four postcondition clauses and ran two framing
rivals against its fractional-permission input, two partial-domain rivals, and a
supporting fabricated-key near-miss, plus two positives and two axiom-lane
probes. This Lean carrier narrows to the purely functional core: a single
``UuidValue`` and one equality clause. The two framing rivals are VACUOUS here
(referential transparency). The nagini partial-domain "drop canonicalize" rival
ports directly as the identity rival; the "keep raw key" partial-domain rival and
the supporting "fabricated zero key" near-miss both collapse onto the textual
constructor here (there is no separate is_none/canon/key facet to preserve while
diverging), so they are re-expressed as two distinct textual attackers — a
constant-identifier forgery and a positional-decode near-miss — probed at
distinct inputs. The two nagini positives (a structural reshape and the
in-domain admissibility control) port; a second reshape positive is added. The
AXIOM_TESTS lane is dropped (it is G-AX's job; meta.json records axioms == []).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate at one concrete,
``decide``-able input; each was BUILT against its rival (elaborates: the rival
provably contradicts the spec there) and against the frozen solution (fails: so
it is a real discriminator, not a tautology). The witnesses are spread across the
textual sub-domain — ``['a','b']`` (decodes 171), ``['f']`` (decodes 15),
``['1','0']`` (decodes 16) — so no two rivals share a probe point and each
rival's claimed divergence is demonstrated at its own input (pts = 3).

BINDER COVERAGE NOTE. The single input binder ``value`` is varied across the
three reject witnesses, but always at the ``textual`` constructor. This is
deliberate and F2P-faithful, not a gap: ``canonicalValue`` is the identity on the
``absent`` and ``canonical`` constructors, identical to the pre-fix pass-through,
so a rival diverging only on those constructors does NOT correspond to the bug
and its faithful patch would still resolve the F2P (the prefetch join filters
absent fk values, and the already-canonical pk is not run through the prepared
conversion on the fk side). Attacking absent/canonical would test spec strength
on a sub-domain the fix does not change; it is intentionally omitted with this
reason rather than left unexplained.
"""
from pathlib import Path

INSTANCE = "django__django-11211"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique, entirely inside the region it edits) ------
# The FULL impl-region body and the FULL proof-region tactic body of the frozen
# solution. Every replacement lands inside the region it names, so `same_spec`
# holds and the theorem STATEMENT is untouched.
_IMPL = (
    "def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do\n"
    "  -- First apply the pass-through preparation, then convert the result to its\n"
    "  -- canonical identifier shape.\n"
    "  let mut v := value\n"
    "  v := basePrep v\n"
    "  return canonicalValue v"
)
_PROOF = (
    "  intro value\n"
    "  unfold problem_spec_normalizeKey implementation_normalizeKey basePrep\n"
    "  rfl"
)

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness / admissibility) — structurally different
    # but CORRECT implementations that MUST verify. If a faithful correct
    # implementation cannot satisfy the frozen obligation the spec is
    # SPEC-TOO-STRONG. Each keeps the theorem STATEMENT byte-identical; none
    # introduces a helper lemma, an axiom, or an assumption token.
    # =====================================================================
    {
        "id": "pos-compose",
        "kind": "soundness",
        "expect": "verify",
        # Functional reshape: drop the imperative `do`/`let mut` scaffold and
        # compose the two steps directly as a pure application. Same value on
        # every input; the frozen tactic body still closes (basePrep unfolds to
        # the identity, leaving `canonicalValue value = canonicalValue value`).
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_normalizeKey (value : UuidValue) : UuidValue :=\n"
            "  canonicalValue (basePrep value)",
        ),
        "rationale": "a correct reshape (pure composition instead of the "
                     "imperative pass-through-then-convert) computes "
                     "`canonicalValue value` on every input, so it must satisfy "
                     "the sole clause `result = canonicalValue value`; if it "
                     "cannot, the postcondition is SPEC-TOO-STRONG. Proof: frozen "
                     "tactic body retained — `basePrep` unfolds to the identity, "
                     "so `rfl` still closes.",
    },
    {
        "id": "pos-branch",
        "kind": "soundness",
        "expect": "verify",
        # Structural reshape: split on the constructor with an explicit
        # early-return per shape rather than delegating to `canonicalValue`.
        # Same value; the proof is re-closed by `cases value <;> rfl` (a change
        # to the proof BODY only — the theorem statement is byte-identical).
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do\n"
                "  let v := basePrep value\n"
                "  match v with\n"
                "  | .absent      => return .absent\n"
                "  | .canonical n => return .canonical n\n"
                "  | .textual s   => return .canonical (decodeHex s)",
            ),
            _PROOF,
            "  intro value\n"
            "  unfold problem_spec_normalizeKey implementation_normalizeKey basePrep\n"
            "  cases value <;> rfl",
        ),
        "rationale": "an explicit per-constructor build (absent→absent, "
                     "canonical n→canonical n, textual s→canonical (decodeHex s)) "
                     "is pointwise equal to `canonicalValue value`, so a correct "
                     "reshape must verify (else SPEC-TOO-STRONG). Proof body "
                     "changed to `cases value <;> rfl`; the theorem statement is "
                     "byte-identical and no helper/axiom is added.",
    },
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen theorem has no precondition binder to admit, so the honest
        # analogue of the nagini precondition-admission probe is to discharge the
        # spec at a ground, F2P-shaped input (a textual spelling — the exact shape
        # the stored fk value takes) by evaluation, alongside the frozen
        # obligation. Verifies iff the spec is satisfiable at a normal input.
        "module": _swap(
            _BASE, _PROOF,
            "  have _ground : problem_spec_normalizeKey (.textual ['1', 'a'])\n"
            "      (implementation_normalizeKey (.textual ['1', 'a'])) := by\n"
            "    unfold problem_spec_normalizeKey implementation_normalizeKey basePrep\n"
            "    decide\n"
            + _PROOF,
        ),
        "rationale": "the obligation is discharged at a ground F2P-shaped input "
                     "(a textual spelling — the exact shape the stored value "
                     "arrives in) by `decide`, then the frozen obligation is "
                     "closed verbatim. Verifies (else the spec is unsatisfiable at "
                     "the normal input, the analogue of PRECOND-TOO-STRONG). "
                     "Nothing is assumed: no new declaration, the theorem "
                     "statement is byte-identical, the ground instance is a `have` "
                     "inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at
    # one concrete textual input (built ELABORATING against the rival and
    # FAILING against gold).
    # =====================================================================
    {
        "id": "weak-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix baseline: apply only the pass-through and return the value
        # in whatever shape it arrived in, with no canonicalising conversion.
        # (== Solution_prepatch.lean's impl.)
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do\n"
            "  let mut v := value\n"
            "  v := basePrep v\n"
            "  return v",
        ),
        "refinement": "returning the value unchanged for a textual spelling is "
                      "exactly the pre-fix behavior: the stored text stays text "
                      "instead of becoming the canonical identifier it denotes, so "
                      "the comparison key on the text side never equals the "
                      "canonical-identifier key on the other side and the "
                      "membership join finds no match — the prepared attribute "
                      "comes back empty. It would NOT resolve the F2P; this is the "
                      "leg's prepatch.",
        "rationale": "REJECT from `result = canonicalValue value`: on a textual "
                     "input the result must be `canonical (decodeHex s)`, but the "
                     "rival returns `textual s`. Refuted at textual ['a','b'] "
                     "(decodes 171), this rival's own probe point.",
        "witness": (
            "example : ¬ problem_spec_normalizeKey\n"
            "    (UuidValue.textual ['a', 'b'])\n"
            "    (implementation_normalizeKey (UuidValue.textual ['a', 'b'])) := by\n"
            "  unfold problem_spec_normalizeKey implementation_normalizeKey\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-constant-identifier",
        "kind": "uniqueness",
        "expect": "reject",
        # Faithful on the absent and already-canonical shapes, but fabricates a
        # FIXED identifier for every textual spelling instead of decoding it.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do\n"
            "  match value with\n"
            "  | .absent      => return .absent\n"
            "  | .canonical n => return .canonical n\n"
            "  | .textual _   => return .canonical 0",
        ),
        "refinement": "mapping every textual spelling to one fixed identifier "
                      "cannot equal the distinct identifier each stored value "
                      "actually denotes (except the single all-zero value), so the "
                      "membership join keys the text against the wrong canonical "
                      "identifier and misses. A real patch of this shape would not "
                      "resolve the F2P for any non-zero stored identifier.",
        "rationale": "REJECT from `result = canonicalValue value`: on a textual "
                     "input decoding to a non-zero identifier the result must be "
                     "`canonical (decodeHex s)`, but the rival returns "
                     "`canonical 0`. Refuted at textual ['f'] (decodes 15 ≠ 0), a "
                     "point distinct from every other rival's.",
        "witness": (
            "example : ¬ problem_spec_normalizeKey\n"
            "    (UuidValue.textual ['f'])\n"
            "    (implementation_normalizeKey (UuidValue.textual ['f'])) := by\n"
            "  unfold problem_spec_normalizeKey implementation_normalizeKey\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-nonpositional-decode",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: converts a textual spelling by SUMMING its hex digits
        # instead of accumulating them with positional (base-16) weight.
        # Agrees with gold only for spellings of at most one significant digit.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do\n"
            "  match value with\n"
            "  | .absent      => return .absent\n"
            "  | .canonical n => return .canonical n\n"
            "  | .textual s   => return .canonical (s.foldl (fun acc c =>\n"
            "      match hexVal? c with | some d => acc + d | none => acc) 0)",
        ),
        "refinement": "summing the hex digits without positional weight decodes a "
                      "multi-digit spelling to the wrong number (e.g. a spelling "
                      "denoting a large identifier collapses to the small sum of "
                      "its digits), so the text side keys against a different "
                      "canonical identifier than the stored value denotes and the "
                      "join misses. A real patch that dropped the positional "
                      "weighting would not resolve the F2P for any multi-digit "
                      "stored identifier — a NEAR-MISS that is right only on "
                      "single-digit spellings, so it is probed where it diverges.",
        "rationale": "REJECT from `result = canonicalValue value`: at textual "
                     "['1','0'] gold decodes to `canonical 16` (positional: "
                     "1·16+0) but the rival returns `canonical 1` (digit sum). "
                     "Refuted at a two-digit input where positional and summed "
                     "decodes diverge — distinct from the other rivals' points.",
        "witness": (
            "example : ¬ problem_spec_normalizeKey\n"
            "    (UuidValue.textual ['1', '0'])\n"
            "    (implementation_normalizeKey (UuidValue.textual ['1', '0'])) := by\n"
            "  unfold problem_spec_normalizeKey implementation_normalizeKey\n"
            "  decide\n"
        ),
    },
]
