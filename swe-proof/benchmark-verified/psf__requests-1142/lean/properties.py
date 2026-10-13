# properties.py — G-PBT falsification battery for psf__requests-1142 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, for a soundness positive that reproves, the proof body — is
# edited), checked by variant_scope + the Lean verifier. Every expect="reject" case
# carries a refutation `witness`: a self-contained snippet that ELABORATES against
# the rival and FAILS on the frozen solution, so the rejection is attributable to the
# spec and not to a tactic script that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (one contracted function, read from Solution.lean / mapping.md /
# instance.json):
#   prepare_content_length (method : String) (pre : Option String) (body : Option Nat)
#     : Option String
#   Determination of the message-length header slot for a prepared HTTP request.
#   `pre` is the slot's value before the call (`none` = absent); the result is its
#   value after. The SINGLE postcondition `problem_spec_prepare_content_length`
#   pins the whole result by case analysis on `body`, bundling three independent
#   top-level obligations:
#     (C1) VALUE on a present body — `body = some n` ⇒ result = `some (toString n)`.
#          The measured content length, rendered in decimal.
#     (C2) THE DISCRIMINATOR (the changed behaviour) — `body = none` and the method
#          is one of `"GET"`/`"HEAD"` ⇒ result = `pre`: the slot is NOT written and
#          RETAINS its prior value (in particular stays absent when it was absent).
#          This is the fix: a body-less GET/HEAD must not advertise a zero length.
#     (C3) DEFAULT on a body-less payload-carrying method — `body = none` and the
#          method is neither `"GET"` nor `"HEAD"` ⇒ result = `some "0"`.
#   The carrier is fully TRANSPARENT: `String` / `Option` / `Nat` / `toString`, no
#   opaque callee (the axioms region is empty — the body length is a `Nat` type
#   refinement, not a callee). So every reject witness is `decide`-able at concrete
#   literals with no carrier conditioning needed.
#
#   Input binders of the spec predicate, each of which the reject witnesses vary:
#     * `method` — the normalized HTTP verb; drives the C2/C3 fork. Kept as a
#       `String` on this carrier (NOT collapsed to a single boolean), so the two
#       suppressed verbs "GET" and "HEAD" are independently mishandleable — the
#       lane the velvet sibling had to report vacuous is LIVE here.
#     * `pre`    — the slot's prior value; C2 pins the result EQUAL to it, so a
#       rival that clobbers or clears it on the GET/HEAD arm is observable only when
#       `pre ≠ none`.
#     * `body`   — present vs absent; drives C1 vs the C2/C3 fork.
#
# LANES: soundness (2 reshape positives), admissibility (1), uniqueness (6 rivals).
# All three falsification directions are tested — SPEC-TOO-STRONG, PRECOND-TOO-STRONG
# (re-expressed for a total carrier: the obligation must be satisfiable at an
# F2P-shaped input, not merely universally asserted), and SPEC-TOO-WEAK.
#
# LANES THAT DO NOT PORT (nagini -> lean accounting; see footer for the full table):
#   * FRAME / PERMISSION-MUTATION (nagini's MANDATORY `rival-extra-header-smuggle`
#     and the whole-map frame clauses F1/F2, plus the `method == Old(method)` pin):
#     nagini holds a MUTABLE header dict at full permission and its rival writes an
#     unrelated key into it. Lean is referentially transparent — the function
#     returns a single `Option String` (the one modeled slot), declares no aliasable
#     heap and no fractional permission — so a "smuggle a spurious header key" rival
#     is not expressible and there is no `Old`/frame surface to violate. VACUOUS
#     here; no substitute is fabricated. (The one slot the fix touches IS modeled,
#     and its prior-value retention is pinned by C2 and attacked by
#     `weak-clear-slot-on-suppress`.)
#   * DIVERGENCE / NON-TERMINATION: on lean `implementation_prepare_content_length`
#     is a total Lean `def`; a non-terminating implementation cannot be written at
#     all, so the class is genuinely VACUOUS here (the lean disposition, NOT the
#     velvet-`partial` known-spec-hole one). The nagini sibling carries no
#     divergence case either.
#     MEASURED (audit), not argued: the frozen file sets no
#     `loom.semantics.termination` option, so this bundle is on the plain-Lean
#     total carrier. The only way to write a measure-free loop here is to mark the
#     impl `partial def`; a variant doing exactly that (self-call, no decreasing
#     measure) does fail to build, but its failure is `Tactic \`unfold\` failed to
#     unfold \`implementation_prepare_content_length\`` — `partial` yields an
#     opaque constant with no equation lemmas, so NO witness can discriminate
#     against it (the same `unfold` failure hits the witness file, exit 1 on the
#     RIVAL side, which is the half that must succeed). So the class is not
#     shippable as a reject case for a tooling reason, not for a spec reason: the
#     divergence is unobservable rather than admitted. Recorded here rather than
#     faked with a rival whose rejection would attest to `unfold`, not the spec.
#   * AXIOM_TESTS (nagini's empty axiom lane): the axiom lane is G-AX's job and this
#     gate ignores it. meta.json declares no consumed axiom and no deep-model
#     reference; there is nothing here for this spec lane to test.
#
# CARRIER NARROWING / BROADENING vs nagini: nagini modeled six args (a mutable
# `headers` dict, `method`, `seekable`, `stream_len`, `body_present`, `body_len`) and
# a rich multi-clause postcondition (per-branch size pins, a GET/HEAD-vs-other
# discriminator, `headers[size]==0`, two whole-map frame clauses, `method==Old`).
# This backend models only the purely-functional slot decision, so nagini's frame
# clauses and its `method==Old` pin (heap/permission artifacts) have no counterpart.
# But two nagini distinctions SURVIVE more sharply here than on the velvet sibling:
# `method` stays a `String` (so `partial-domain-head-only` is LIVE, not vacuous), and
# the slot's prior value is modeled as `pre` (so C2 pins RETENTION, giving the
# `weak-clear-slot-on-suppress` rival). nagini's U1 (leading unconditional write) and
# U2 (unguarded else) are two impl SHAPES with the SAME observable defect on this
# carrier — a body-less GET/HEAD announces `some "0"` — so they collapse to one rival.
from pathlib import Path

INSTANCE = "psf__requests-1142"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and the pure-match positive) swaps THIS block.
_IMPL = (
    "def implementation_prepare_content_length\n"
    "    (method : String) (pre : Option String) (body : Option Nat) :\n"
    "    Option String := Id.run do\n"
    "  -- the header slot starts at its pre-call value; only writes change it\n"
    "  let mut clen : Option String := pre\n"
    "  match body with\n"
    "  | some n =>\n"
    "      -- a body is present: its content length is reported\n"
    "      clen := some (toString n)\n"
    "  | none =>\n"
    "      -- no body: only methods that may carry a payload write a zero length;\n"
    "      -- for GET/HEAD nothing is written and the slot retains `pre`\n"
    '      if method ≠ "GET" ∧ method ≠ "HEAD" then\n'
    '        clen := some "0"\n'
    "  return clen"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# A single-guard landmark, strictly inside the impl region, unique in the file. Used
# by the partial-domain rival (drop the HEAD conjunct only).
_GUARD = '      if method ≠ "GET" ∧ method ≠ "HEAD" then'
assert _BASE.count(_GUARD) == 1, "guard anchor drifted from expected text"

# The frozen proof body (tactic lines inside proof-start/proof-end). Swapped only by
# the pure-match positive, whose different impl shape needs an (equally cheap,
# honest) reproof of the byte-identical theorem statement.
_PROOF = (
    "  intro method pre body\n"
    "  unfold problem_spec_prepare_content_length implementation_prepare_content_length\n"
    "  cases body with\n"
    "  | some n => rfl\n"
    "  | none =>\n"
    "      simp only [Id.run]\n"
    '      by_cases h : method = "GET" ∨ method = "HEAD"\n'
    "      · rw [if_pos h]\n"
    '        have h\' : ¬ (method ≠ "GET" ∧ method ≠ "HEAD") := by\n'
    "          rcases h with h | h <;> simp [h]\n"
    "        simp only [if_neg h']\n"
    "        rfl\n"
    "      · rw [if_neg h]\n"
    "        push_neg at h\n"
    '        have h\' : method ≠ "GET" ∧ method ≠ "HEAD" := ⟨h.1, h.2⟩\n'
    "        simp only [if_pos h']\n"
    "        rfl"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-swap-conjuncts: gold impl shape, but the two disequalities in the body-less
# guard are SWAPPED (`method ≠ "HEAD" ∧ method ≠ "GET"`). Conjunction is symmetric so
# the guard fires on exactly the same methods; the output equals the frozen impl's on
# every input. The theorem STATEMENT is byte-identical; the frozen proof body, which
# builds `⟨h.1, h.2⟩` from the GET-first split, no longer type-matches the HEAD-first
# guard, so the proof is reproven honestly (same `by_cases`/`push_neg` shape, the
# conjunction pair reordered) — no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-
# STRONG (the postcondition is over-fit to the gold conjunction order).
_POS_SWAP = _swap(
    _swap(
        _BASE,
        _GUARD,
        '      if method ≠ "HEAD" ∧ method ≠ "GET" then',
    ),
    _PROOF,
    "  intro method pre body\n"
    "  unfold problem_spec_prepare_content_length implementation_prepare_content_length\n"
    "  cases body with\n"
    "  | some n => rfl\n"
    "  | none =>\n"
    "      simp only [Id.run]\n"
    '      by_cases h : method = "GET" ∨ method = "HEAD"\n'
    "      · rw [if_pos h]\n"
    '        have h\' : ¬ (method ≠ "HEAD" ∧ method ≠ "GET") := by\n'
    "          rcases h with h | h <;> simp [h]\n"
    "        simp only [if_neg h']\n"
    "        rfl\n"
    "      · rw [if_neg h]\n"
    "        push_neg at h\n"
    '        have h\' : method ≠ "HEAD" ∧ method ≠ "GET" := ⟨h.2, h.1⟩\n'
    "        simp only [if_pos h']\n"
    "        rfl",
)

# pos-pure-match: a structurally different CORRECT impl written as a pure functional
# `match` (no `Id.run do`, no `let mut`), returning the result of each branch
# directly. Semantics identical to gold on every input. The theorem STATEMENT is
# byte-identical; its proof is reproven honestly (`by_cases` on the GET/HEAD guard,
# `if_pos`/`if_neg` on both sides) — no new axiom/lemma/sorry, the cheapest tactic for
# the new shape. If it FAILS => SPEC-TOO-STRONG (the postcondition is bound to the
# monadic/mutable impl shape rather than the behaviour).
_POS_PURE = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_prepare_content_length\n"
        "    (method : String) (pre : Option String) (body : Option Nat) :\n"
        "    Option String :=\n"
        "  match body with\n"
        "  | some n => some (toString n)\n"
        '  | none => if method = "GET" ∨ method = "HEAD" then pre else some "0"',
    ),
    _PROOF,
    "  intro method pre body\n"
    "  unfold problem_spec_prepare_content_length implementation_prepare_content_length\n"
    "  cases body with\n"
    "  | some n => rfl\n"
    "  | none =>\n"
    '      by_cases h : method = "GET" ∨ method = "HEAD"\n'
    "      · rw [if_pos h, if_pos h]\n"
    "      · rw [if_neg h, if_neg h]",
)


# adm-f2p-shaped-inputs: the ADMISSIBILITY lane (PRECOND-TOO-STRONG direction).
# The frozen obligation is `∀ method pre body, problem_spec … (impl …)` with no
# hypothesis, so there is no precondition to be too strong — but that is NOT a
# reason to drop the lane. The analogue on a total carrier is the obligation being
# UNSATISFIABLE at exactly an F2P-shaped input: a spec whose C2 arm could not be
# discharged at a body-less GET / body-less HEAD would be vacuously "provable"
# only by never being instantiated there. This positive discharges the obligation
# at those two concrete inputs BY EVALUATION, as `have`s, and only then closes the
# frozen obligation verbatim (the frozen tactic body is kept byte-for-byte below
# the two `have`s, so the general proof is not weakened — the haves are additional
# demands, not substitutes). The theorem STATEMENT is byte-identical; no new
# axiom/lemma/sorry. If either `decide` FAILED => the obligation cannot be met at
# the input the shipped behaviour is exercised at (PRECOND-TOO-STRONG's analogue).
_POS_ADMISS = _swap(
    _BASE,
    _PROOF,
    "  -- ADMISSIBILITY: the obligation must be SATISFIABLE at the two concrete\n"
    "  -- F2P-shaped inputs (body-less GET, body-less HEAD), discharged here by\n"
    "  -- evaluation before the general obligation is closed verbatim.\n"
    '  have adm_get : problem_spec_prepare_content_length "GET" none none\n'
    '      (implementation_prepare_content_length "GET" none none) := by\n'
    "    unfold problem_spec_prepare_content_length "
    "implementation_prepare_content_length\n"
    "    decide\n"
    '  have adm_head : problem_spec_prepare_content_length "HEAD" none none\n'
    '      (implementation_prepare_content_length "HEAD" none none) := by\n'
    "    unfold problem_spec_prepare_content_length "
    "implementation_prepare_content_length\n"
    "    decide\n"
    + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-prepatch-unconditional: the pre-patch behaviour. Initialize the slot to
# `some "0"` UNCONDITIONALLY (clobbering `pre`); a present body overrides it; a
# body-less request is left at `some "0"` regardless of method. Attacks clause C2:
# a body-less GET/HEAD is left advertising a zero length instead of retaining `pre`.
# (nagini's U1 "leading unconditional write" and U2 "unguarded else" are two impl
# SHAPES with this SAME observable defect on this carrier — both leave a body-less
# request at `some "0"` for every method — so they collapse to this one rival.)
_RIV_PREPATCH = _swap(
    _BASE,
    _IMPL,
    "def implementation_prepare_content_length\n"
    "    (method : String) (pre : Option String) (body : Option Nat) :\n"
    "    Option String := Id.run do\n"
    '  let mut clen : Option String := some "0"\n'
    "  match body with\n"
    "  | some n => clen := some (toString n)\n"
    "  | none => pure ()\n"
    "  return clen",
)

# partial-domain-head-only: the body-less guard drops the HEAD conjunct, suppressing
# the zero length for GET only. Correct on a body-less GET (retains `pre`) and on
# every payload-carrying method (`some "0"`), but WRONG on a body-less HEAD: it still
# writes `some "0"`. This is the lane the velvet sibling reports VACUOUS (it collapses
# the method distinction into one boolean); on this carrier `method` is a `String`,
# so "GET" and "HEAD" are independently mishandleable and the rival is LIVE. Attacks
# clause C2 at `method = "HEAD"`.
_RIV_PARTIAL_HEAD = _swap(
    _BASE,
    _GUARD,
    '      if method ≠ "GET" then',
)

# weak-clear-slot-on-suppress: on the body-less GET/HEAD arm, instead of RETAINING
# the prior value the slot is CLEARED to `none` (an explicit `else` that overwrites).
# Correct whenever `pre = none` (absent stays absent) but WRONG when the caller
# supplied a prior value: C2 pins the result EQUAL to `pre`, and this rival drops it.
# Attacks clause C2's retention sub-clause, varying the `pre` binder off `none` — the
# binder every other reject witness that touches the GET/HEAD arm holds at `none`.
# (This is the lean analogue of nagini's frame concern — a part of the modeled state
# the spec pins beyond the discriminator — re-expressed on the one slot the fix owns,
# since the whole-map frame is not expressible on this transparent carrier.)
_RIV_CLEAR = _swap(
    _BASE,
    _IMPL,
    "def implementation_prepare_content_length\n"
    "    (method : String) (pre : Option String) (body : Option Nat) :\n"
    "    Option String := Id.run do\n"
    "  let mut clen : Option String := pre\n"
    "  match body with\n"
    "  | some n => clen := some (toString n)\n"
    "  | none =>\n"
    '      if method ≠ "GET" ∧ method ≠ "HEAD" then\n'
    '        clen := some "0"\n'
    "      else\n"
    "        clen := none\n"
    "  return clen",
)

# weak-overcorrect-never-announce: the DUAL over-correction — a body-less request
# NEVER writes the slot, for ANY method (drop the guarded write entirely). Correct on
# the body-less GET/HEAD arm (retains `pre`) but WRONG on a body-less payload-carrying
# method: C3 pins `some "0"` there and the rival leaves `pre`. Attacks clause C3,
# varying `method` off the suppressed verbs (e.g. "POST"). None of nagini's rivals
# attacked this arm on the modeled side; it is required so that some reject witness
# depends on the C3 clause and on a non-GET/HEAD method value.
_RIV_OVERCORRECT = _swap(
    _BASE,
    _IMPL,
    "def implementation_prepare_content_length\n"
    "    (method : String) (pre : Option String) (body : Option Nat) :\n"
    "    Option String := Id.run do\n"
    "  let mut clen : Option String := pre\n"
    "  match body with\n"
    "  | some n => clen := some (toString n)\n"
    "  | none => pure ()\n"
    "  return clen",
)

# weak-wrong-body-value: on a present body, announce the WRONG length — `n + 1`
# instead of the measured `n`. Correct on both body-less arms (C2/C3), but violates
# clause C1 (the announced value). This is nagini's `rival-wrong-stream-value`
# (announce a size different from the measured one) re-expressed: the two real
# length-producing branches (`body.tell()` / `len(body)`) collapse to the one `Nat`
# carrier here, so a single value-divergence rival covers it. Attacks clause C1,
# varying the `body` binder off `none`.
_RIV_WRONG_VALUE = _swap(
    _BASE,
    _IMPL,
    "def implementation_prepare_content_length\n"
    "    (method : String) (pre : Option String) (body : Option Nat) :\n"
    "    Option String := Id.run do\n"
    "  let mut clen : Option String := pre\n"
    "  match body with\n"
    "  | some n => clen := some (toString (n + 1))\n"
    "  | none =>\n"
    '      if method ≠ "GET" ∧ method ≠ "HEAD" then\n'
    '        clen := some "0"\n'
    "  return clen",
)


# weak-zero-length-body-blank: on a present body, render a ZERO content length as the
# empty string instead of the decimal numeral `"0"`. Agrees with gold on every n > 0
# — including the `n = 7` point the other C1 rival is caught at — and diverges only
# at exactly `n = 0`. Added by the audit: the shipped C1 witness sits at n = 7, so a
# rival mishandling only the zero-length boundary went uncaught, and `body = some 0`
# (an empty-but-present body — a real, reachable shape) is where C1 and C3 both pin
# the same rendered value by different routes. Attacks clause C1 at its boundary.
_RIV_ZERO_BLANK = _swap(
    _BASE,
    _IMPL,
    "def implementation_prepare_content_length\n"
    "    (method : String) (pre : Option String) (body : Option Nat) :\n"
    "    Option String := Id.run do\n"
    "  let mut clen : Option String := pre\n"
    "  match body with\n"
    '  | some n => clen := if n = 0 then some "" else some (toString n)\n'
    "  | none =>\n"
    '      if method ≠ "GET" ∧ method ≠ "HEAD" then\n'
    '        clen := some "0"\n'
    "  return clen",
)


# --- witnesses ---------------------------------------------------------------------
# Each witness states `¬ problem_spec_prepare_content_length method pre body
# (impl method pre body)` at a concrete input, then `decide`s. The carrier is fully
# transparent (String/Option/Nat/toString), so no conditioning hypothesis is needed
# and there is no consistency concern. Each ELABORATES against its rival (which
# produces the wrong slot value there) and FAILS on gold (checked out-of-band with
# scripts/lean_verify.sh: `decide` proves the spec HOLDS of gold at each point, so
# the negation is unprovable there).

# C2 @ GET, pre absent: gold retains `none`; prepatch left `some "0"`.
_WIT_PREPATCH = (
    "example : ¬ problem_spec_prepare_content_length \"GET\" none none\n"
    "    (implementation_prepare_content_length \"GET\" none none) := by\n"
    "  unfold problem_spec_prepare_content_length implementation_prepare_content_length\n"
    "  decide"
)

# C2 @ HEAD, pre absent: gold retains `none`; the GET-only guard writes `some "0"`.
# Probes HEAD specifically — the verb the partial guard forgets.
_WIT_PARTIAL_HEAD = (
    "example : ¬ problem_spec_prepare_content_length \"HEAD\" none none\n"
    "    (implementation_prepare_content_length \"HEAD\" none none) := by\n"
    "  unfold problem_spec_prepare_content_length implementation_prepare_content_length\n"
    "  decide"
)

# C2 (retention) @ GET, pre = some "9": gold retains `some "9"`; the clear rival
# returns `none`. This is the ONLY witness with `pre ≠ none`, so it is what varies the
# `pre` binder.
_WIT_CLEAR = (
    "example : ¬ problem_spec_prepare_content_length \"GET\" (some \"9\") none\n"
    "    (implementation_prepare_content_length \"GET\" (some \"9\") none) := by\n"
    "  unfold problem_spec_prepare_content_length implementation_prepare_content_length\n"
    "  decide"
)

# C3 @ POST, pre absent: gold writes `some "0"`; the over-correction leaves `none`.
# The only witness on a non-GET/HEAD method — varies the `method` binder off the
# suppressed verbs and exercises the C3 clause.
_WIT_OVERCORRECT = (
    "example : ¬ problem_spec_prepare_content_length \"POST\" none none\n"
    "    (implementation_prepare_content_length \"POST\" none none) := by\n"
    "  unfold problem_spec_prepare_content_length implementation_prepare_content_length\n"
    "  decide"
)

# C1 @ GET, body = some 7: gold announces `some "7"`; the rival announces `some "8"`.
# The only witness on a present body — varies the `body` binder off `none`.
_WIT_WRONG_VALUE = (
    "example : ¬ problem_spec_prepare_content_length \"GET\" none (some 7)\n"
    "    (implementation_prepare_content_length \"GET\" none (some 7)) := by\n"
    "  unfold problem_spec_prepare_content_length implementation_prepare_content_length\n"
    "  decide"
)


# C1 @ POST, body = some 0: gold announces `some "0"`; the rival announces `some ""`.
# The n = 0 boundary of the announced length — the point the n = 7 witness misses.
_WIT_ZERO_BLANK = (
    "example : ¬ problem_spec_prepare_content_length \"POST\" none (some 0)\n"
    "    (implementation_prepare_content_length \"POST\" none (some 0)) := by\n"
    "  unfold problem_spec_prepare_content_length implementation_prepare_content_length\n"
    "  decide"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-swap-conjuncts",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SWAP,
        "rationale": (
            "structurally-different but CORRECT impl: the two disequalities in the "
            "body-less guard are swapped (HEAD-first). Conjunction is symmetric, so the "
            "guard fires on exactly the same methods and the output equals the frozen "
            "impl's on every input. The theorem STATEMENT is byte-identical; the frozen "
            "proof — which builds the conjunction from the GET-first split — is reproven "
            "with the pair reordered (same by_cases/push_neg shape), no new "
            "axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit "
            "to the gold conjunction order)."
        ),
    },
    {
        "id": "pos-pure-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "a structurally different CORRECT impl written as a pure functional `match` "
            "(no Id.run do, no let mut), returning each branch's value directly. "
            "Semantics identical to gold on every input. The theorem STATEMENT is "
            "byte-identical; its proof is reproven honestly (by_cases on the GET/HEAD "
            "guard, if_pos/if_neg on both sides) — the cheapest tactic for the new "
            "shape, no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (the "
            "postcondition is bound to the monadic/mutable impl shape rather than the "
            "behaviour)."
        ),
    },

    {
        "id": "adm-f2p-shaped-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": (
            "ADMISSIBILITY (PRECOND-TOO-STRONG direction). The frozen obligation "
            "carries no precondition hypothesis, so the analogue on this total "
            "carrier is that the obligation must be SATISFIABLE at an F2P-shaped "
            "input rather than only universally asserted. This positive discharges "
            "it by EVALUATION at the two concrete such inputs — a body-less GET and "
            "a body-less HEAD, the C2 arm the shipped behaviour turns on — as "
            "`have`s, and only then closes the frozen obligation with the frozen "
            "tactic body kept byte-for-byte. The `have`s are additional demands, "
            "not substitutes, so nothing is weakened. If either `decide` FAILS the "
            "obligation cannot be met exactly where the behaviour is exercised."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-prepatch-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PREPATCH,
        "refinement": (
            "this IS the pre-patch behaviour: the slot is set to a zero length "
            "unconditionally first, and a body-less request is left carrying it "
            "regardless of method. Its faithful real patch is exactly the UNCHANGED "
            "pre-gold function, under which a body-less GET/HEAD still advertises a "
            "zero-length body — the F2P test (a body-less GET and a body-less HEAD must "
            "carry NO such header) fails directly. It would NOT resolve; this is "
            "precisely the change the spec senses (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by clause C2 (the discriminator). For a body-less GET/HEAD the "
            "spec pins result = pre (absent stays absent), but the rival leaves "
            "`some \"0\"`. Witness probes a body-less GET with `pre = none`: gold "
            "retains `none`, the rival returns `some \"0\"` — `decide` closes the "
            "disequality with no opaque term. If it VERIFIES => SPEC-TOO-WEAK (admits "
            "the pre-patch bug)."
        ),
        "witness": _WIT_PREPATCH,
    },
    {
        "id": "partial-domain-head-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PARTIAL_HEAD,
        "refinement": (
            "the body-less guard drops the HEAD conjunct, suppressing the zero length "
            "for GET only — a faithful real patch that guards `method not in ('GET',)`, "
            "forgetting HEAD. It passes the GET half of the F2P but a body-less HEAD "
            "still advertises a zero length, so the HEAD half of the F2P (a body-less "
            "HEAD must carry NO such header) fails. It would NOT resolve. On the velvet "
            "sibling's carrier the method distinction is a single boolean and this rival "
            "is vacuous; here `method` is a String, so HEAD is independently "
            "mishandleable and the rival is live."
        ),
        "rationale": (
            "REJECTED by clause C2 at `method = \"HEAD\"`. In the body-less case the "
            "spec pins result = pre for HEAD too, but the rival (guarding GET only) "
            "writes `some \"0\"`. Witness probes a body-less HEAD with `pre = none`: "
            "gold retains `none`, the rival returns `some \"0\"`. Probes the HEAD verb "
            "the guard forgets — a distinct method value from the prepatch witness's "
            "GET. If it VERIFIES => SPEC-TOO-WEAK (the HEAD sub-domain is uncovered)."
        ),
        "witness": _WIT_PARTIAL_HEAD,
    },
    {
        "id": "weak-clear-slot-on-suppress",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CLEAR,
        "refinement": (
            "on the body-less GET/HEAD arm the slot is CLEARED rather than retained — a "
            "faithful real patch that, on that arm, deletes the header instead of "
            "leaving it untouched. Correct when no prior value was present, but a "
            "caller-supplied prior value (copied in before this step runs) would be "
            "silently dropped — observably different wire behaviour from gold, which "
            "leaves such a value in place. The retention of a user-supplied value is a "
            "behaviour the gold contract pins (mapping.md: no branch fires on the "
            "GET/HEAD arm, so the slot keeps its prior value); dropping it diverges from "
            "gold, so it would NOT resolve on any input carrying a prior value."
        ),
        "rationale": (
            "REJECTED by clause C2's RETENTION sub-clause. The spec pins result = pre "
            "on the GET/HEAD arm; the rival returns `none` regardless of `pre`. Witness "
            "probes a body-less GET with `pre = some \"9\"`: gold retains `some \"9\"`, "
            "the rival returns `none`. This is the ONLY witness with `pre ≠ none`, so it "
            "is what varies the `pre` binder — a rival mishandling only a present prior "
            "value would otherwise go uncaught. If it VERIFIES => SPEC-TOO-WEAK (the "
            "prior-value retention is unpinned)."
        ),
        "witness": _WIT_CLEAR,
    },
    {
        "id": "weak-overcorrect-never-announce",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OVERCORRECT,
        "refinement": (
            "the dual over-correction: a body-less request NEVER writes the slot, for "
            "ANY method (the guarded write is dropped). Correct on the body-less "
            "GET/HEAD arm, but a body-less payload-carrying method (e.g. POST) is left "
            "with no announced length where gold announces a zero one. The shipped F2P "
            "set exercises only the GET/HEAD arm, so this is not the F2P discriminator; "
            "it is a legitimate SPEC-TOO-WEAK probe guarding the gold-pinned C3 "
            "behaviour — the spec is faithful to gold there (G-CONF fuzzes all common "
            "verbs), and admitting a rival that diverges on it would be a real "
            "spec-too-weak hole."
        ),
        "rationale": (
            "REJECTED by clause C3. For a body-less method that is neither GET nor HEAD "
            "the spec pins result = `some \"0\"`, but the rival leaves `pre`. Witness "
            "probes a body-less POST with `pre = none`: gold writes `some \"0\"`, the "
            "rival returns `none`. The only witness on a non-GET/HEAD method — varies "
            "the `method` binder off the suppressed verbs and is the only one exercising "
            "the C3 clause. If it VERIFIES => SPEC-TOO-WEAK (the default-zero behaviour "
            "is unpinned)."
        ),
        "witness": _WIT_OVERCORRECT,
    },
    {
        "id": "weak-wrong-body-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WRONG_VALUE,
        "refinement": (
            "on a present body, announce the wrong length (`n + 1` instead of the "
            "measured `n`). This is nagini's wrong-stream-value rival re-expressed: the "
            "two real length-producing branches (`str(body.tell())` and "
            "`str(len(body))`) collapse to the one `Nat` carrier here, so one "
            "value-divergence rival covers both. A faithful real patch announcing a "
            "size different from the measured one diverges from the size-correctness "
            "behaviour the P2P test_basic_building and the gold contract pin — it would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (the announced value). For `body = some n` the spec "
            "pins result = `some (toString n)`, but the rival announces "
            "`some (toString (n+1))`. Witness probes `body = some 7`: gold announces "
            "`some \"7\"`, the rival `some \"8\"`. The only witness on a PRESENT body — "
            "varies the `body` binder off `none` and is the only one exercising the C1 "
            "clause. If it VERIFIES => SPEC-TOO-WEAK (the announced length is unpinned)."
        ),
        "witness": _WIT_WRONG_VALUE,
    },
    {
        "id": "weak-zero-length-body-blank",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ZERO_BLANK,
        "refinement": (
            "on a present body, a ZERO content length is rendered as the empty "
            "string instead of the decimal numeral. A faithful real patch of this "
            "shape special-cases the empty-but-present body and emits a blank "
            "message-length value, which is not the decimal rendering the "
            "size-correctness behaviour pins (P2P test_basic_building and the gold "
            "contract require the decimal numeral for every measured length, zero "
            "included) — a blank header value is not even a valid field value on "
            "the wire. It agrees with gold on every non-zero length, so it would "
            "pass any test that only exercises non-empty bodies, and would NOT "
            "resolve on one that sends an empty body."
        ),
        "rationale": (
            "REJECTED by clause C1 at its BOUNDARY. For `body = some n` the spec "
            "pins result = `some (toString n)`; at n = 0 that is `some \"0\"` and "
            "the rival gives `some \"\"`. Witness probes `body = some 0` on a POST: "
            "gold announces `some \"0\"`, the rival `some \"\"`. Added by the audit "
            "because the other C1 witness sits at n = 7, where this rival is "
            "CORRECT — so the zero boundary of the announced length was unprobed, "
            "and it is the one length at which C1 and C3 pin the same rendered "
            "value by different routes. If it VERIFIES => SPEC-TOO-WEAK (the "
            "announced length is pinned only away from zero)."
        ),
        "witness": _WIT_ZERO_BLANK,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness) plus an empty AXIOM lane.
#
#   sibling case                    -> here                              disposition
#   -------------------------------------------------------------------------------
#   pos-control-reordered           -> pos-swap-conjuncts / pos-pure-match PORTED (2 reshapes)
#   echo-honest                     -> (subsumed by the positives)        RE-EXPRESSED
#   admiss-bodyless-get             -> adm-f2p-shaped-inputs               PORTED (re-expr.)
#   rival-prepatch-unconditional    -> weak-prepatch-unconditional (U1)   PORTED
#   rival-drop-method-guard         -> (folds into weak-prepatch-...)     COLLAPSED (U2==U1 here)
#   partial-domain-head-only        -> partial-domain-head-only           PORTED (LIVE here)
#   rival-wrong-stream-value        -> weak-wrong-body-value              PORTED (re-expr.)
#   rival-extra-header-smuggle      -> weak-clear-slot-on-suppress        RE-AIMED (frame -> slot)
#   (no sibling)                    -> weak-overcorrect-never-announce    ADDED (C3 / binder cov.)
#
# ECHO-HONEST (subsumed): nagini's echo-honest keeps the gold impl and asserts the
#   decision table to show the spec is not echo-vulnerable (the @Pure GET/HEAD tokens
#   are constants, not an answer key). This carrier's post-image is likewise grounded
#   (a concrete `def` over the inputs, empty axioms region — no opaque oracle), so
#   there is no wrong echo to build; the point is covered by the two grounded reshape
#   positives (the cheapest satisfier IS the gold decision). No separate assert-only
#   variant is shipped: an in-region `Assert` has no lean counterpart that adds spec
#   coverage here.
# PORTED (admissibility, re-expressed): nagini's admiss-bodyless-get self-calls to
#   check the Requires (dict_pred, size-header absent, Implies(seekable, body_present))
#   is establishable. The lean obligation is `∀ method pre body, problem_spec … (impl
#   …)` with NO precondition hypothesis — but an earlier revision of this file read
#   that as making the lane degenerate and shipped nothing, which the audit corrected:
#   "the frozen obligation has no precondition" is not a reason, because the analogue
#   on a total carrier is the obligation being UNSATISFIABLE at an F2P-shaped input.
#   `adm-f2p-shaped-inputs` tests that directly — it discharges the obligation by
#   EVALUATION at a body-less GET and a body-less HEAD as `have`s before closing the
#   frozen obligation verbatim — and it BUILDS, so the lane is live, not vacuous, and
#   PRECOND-TOO-STRONG is now one of the three directions this battery actually tests.
# COLLAPSED (rival-drop-method-guard): nagini's U1 (leading unconditional write) and
#   U2 (unguarded else) are two impl SHAPES with the SAME observable defect on this
#   carrier — a body-less request is left at `some "0"` for EVERY method (verified
#   equal on all method/pre/body combinations). Porting both would ship the identical
#   observable twice; U2 folds into weak-prepatch-unconditional.
# VACUOUS (rival-extra-header-smuggle -> the FRAME class): nagini injects an unrelated
#   key into a mutable header dict, caught by whole-map frame clauses. Lean is
#   referentially transparent — the function returns a single Option String (the one
#   modeled slot), no heap, no aliasing, no Old/frame surface — so a spurious-key
#   rival is not expressible. The nagini absence of a read-only Acc(.,1/2) input and
#   its `method==Old(method)` pin are likewise permission/heap artifacts with no
#   counterpart. NOT faked with an inapplicable probe. What DOES survive of the frame
#   intent is that the one slot the fix owns must retain its prior value on the
#   GET/HEAD arm; that is pinned by C2 and attacked by weak-clear-slot-on-suppress.
# DIVERGENCE / NON-TERMINATION: genuinely VACUOUS on lean (implementation_* is a total
#   Lean def; a diverging impl cannot be written). The nagini sibling carries no such
#   case either.
# ADDED (weak-overcorrect-never-announce): nagini's rivals all attack the GET/HEAD
#   (suppress) arm; none attacks the payload-carrying arm on the modeled side (nagini's
#   clause (4) `headers[size]==0` lives there). Here that arm is C3 (`some "0"`), an
#   independent top-level clause with the `method` binder held off GET/HEAD. A battery
#   whose every reject rival held method ∈ {GET,HEAD} would never demonstrate the
#   spec's dependence on the C3 arm, so this rival drops the zero there.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 5 distinct input points):
#   method — "GET" (prepatch, clear), "HEAD" (partial-head), "POST" (over-correct),
#            "GET" (wrong-value): all three modeled verb classes exercised, incl. the
#            HEAD verb the partial guard singles out — never held fixed.
#   pre    — none (prepatch, partial-head, over-correct, wrong-value), some "9"
#            (clear): the `some` arm exercised by the retention rival — never fixed.
#   body   — none (prepatch, partial-head, clear, over-correct), some 7 (wrong-value),
#            some 0 (zero-blank): absent, and present at BOTH a non-zero length and the
#            zero boundary, which are separate points of the C1 clause.
#   Clauses — C1 attacked by wrong-value (n = 7) AND zero-blank (n = 0, the boundary);
#             C2 by prepatch/partial-head/clear (incl. the retention sub-clause); C3
#             by over-correct. Every top-level clause of the sole postcondition is
#             attacked, and all three positives defend all three.
#
# AUDIT-MEASURED coverage limits (probes written, built, and NOT shipped because the
# spec already rejects them — recorded so the next auditor need not re-measure):
#   * suppressing a LOWER-CASE "get" as well (method = "get", body = none): rejected,
#     witness discriminates. The upper-case normalization the model relies on is
#     genuinely pinned — the spec compares against the literals, so an impl that also
#     suppresses an un-normalized spelling is caught.
#   * an empty method string added to the suppressed set (method = "", body = none):
#     rejected, witness discriminates.
#   * falling back to `some "0"` when the slot was absent on the suppress arm
#     (`pre.getD "0"`, the exact complement of weak-clear-slot-on-suppress): rejected,
#     witness discriminates. C2's retention is pinned in BOTH directions of `pre`.
#   * preferring an already-set slot over the measured length on a present body
#     (body = some 7, pre = some "9" — the one binder COMBINATION no shipped witness
#     holds): rejected, witness discriminates. C1 dominates `pre`, as the spec pins.
#   Four correct reshapes were also built against the frozen spec and all VERIFY
#   (nested single-verb ifs; list membership `method ∈ ["GET","HEAD"]`; the answer
#   routed through `Option.map`/`orElse`); no faithful correct impl was found that the
#   spec rejects. So neither the SPEC-TOO-WEAK nor the SPEC-TOO-STRONG probe found a
#   hole in the frozen postcondition.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no axiom
# and no deep-model reference (the body length is a Nat type refinement, not a
# callee), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
