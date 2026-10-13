# properties.py — G-PBT falsification battery for django__django-13551 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region is edited; the frozen proof body already closes every positive shape),
# checked by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   tokenState : (pk password loginTs ts : String) → (emailRaw : Option String)
#                → String
#   The account fingerprint state string. The single postcondition
#   `problem_spec_tokenState` pins the result to EXACTLY the ordered concatenation
#     result = pk ++ password ++ loginTs ++ ts ++ emailPart emailRaw
#   where `emailPart emailRaw := emailRaw.getD ""` normalizes an absent value
#   (`none`) to the empty string. This one full-string equality carries several
#   independent, load-bearing aspects, each attackable:
#     (C-COMPONENTS) every one of the five components is PRESENT — in particular
#         the final email contribution, whose omission is the pre-patch bug;
#     (C-ORDER)      the components appear in EXACTLY this order (pk, password,
#         loginTs, ts, email), so any transposition is refutable;
#     (C-EMAIL-NORM) the email contribution is `emailPart emailRaw` — the value's
#         own characters when present, the EMPTY string when absent — so both the
#         present branch (whole value, untruncated) and the absent branch (nothing
#         appended, no sentinel) are pinned.
#   `emailPart` is a total, transparent fold over the input (no opaque callee, no
#   answer-key), and every component is a plain `String`, so witnesses need no
#   conditioning on the carrier — `decide` reduces the concatenation at any
#   literal input.
#
# CARRIER NOTE / relation to the nagini sibling: nagini modeled the fingerprint as
# a `List[int]` built by five explicit per-component loops behind fractional read
# permission, and pinned the output with two clauses — P1 (the exact 5-component
# concatenation) and P2 (a redundant trailing-segment / anti-double-mask guard on
# the resolved address). This backend models the SAME behavior at the value level:
# a single `String` equality to the ordered concatenation, with the email
# contribution normalized by `emailPart`. nagini's value/order rivals port onto
# this equality directly:
#   nagini weak-drop-email            -> riv-drop-email        (C-COMPONENTS)
#   nagini weak-email-truncated-tail  -> riv-truncated-email   (C-EMAIL-NORM, present)
#   nagini weak-reorder-pk-password   -> riv-reorder-pk-pw     (C-ORDER)
#   nagini weak-none-address-sentinel -> riv-none-sentinel     (C-EMAIL-NORM, absent)
# and two additional rivals go beyond the ported set: riv-swap-loginTs-ts exercises
# the middle components — the `loginTs`/`ts` binders — which the ported rivals hold
# fixed, and riv-empty-value-sentinel visits `some ""`, the present-but-empty email,
# where this carrier's `Option String` makes the spec's absent/empty COLLAPSE
# decidable (nagini's `None`-vs-`len==0` guard split the same point).
# Carrier narrowing is expected — this is not a case-count port (see 'assessment').
#
# SECOND AUDIT (independent, adversarial; post-SOUND). Every case was re-derived
# with real builds. Two defects were found and FIXED here; both were invisible to a
# recorded SOUND:
#   A. The ADMISSIBILITY lane was dropped for the reason "the frozen obligation has
#      no precondition hypothesis, so nothing could be PRECOND-TOO-STRONG". That is
#      not a demonstration of vacuity — it restates the carrier's totality. The
#      analogue on a total carrier is the obligation being UNSATISFIABLE at exactly
#      an F2P-shaped input, which a positive that discharges the spec predicate at
#      that concrete input (by evaluation, as a `have`, before closing the frozen
#      obligation verbatim) tests directly. `admiss-f2p-account` was authored and
#      MEASURED to verify (exit 0). The lane is now present.
#   B. The header claimed "measured: the other four rivals all leave `some \"\"`
#      satisfying the spec", justifying riv-empty-value-sentinel's uniqueness. The
#      claim as written is FALSE for three of the four: at
#      (pk,pw,loginTs,ts) = ("p","q","l","t"), riv-drop-email, riv-truncated-email
#      and riv-none-sentinel ALSO violate the spec at `some ""` (witness builds at
#      that point elaborate against them, exit 0) — they diverge on the other four
#      components' handling, not on the email. Re-measured with every component held
#      EQUAL (pk=pw="p", loginTs=ts="l") so ONLY the email normalization can
#      diverge: at ("p","p","l","l", some "") exactly ONE rival violates the spec,
#      riv-empty-value-sentinel (exit 0; the other five satisfy it, exit 1). The
#      sub-domain claim is TRUE, and the corrected measurement is recorded on the
#      case. Prose that overstates its own measurement is the defect, not the case.
# ALSO MEASURED, no change needed: statement integrity (all 10 variants byte-identical
# outside the impl/proof regions AND in the `correct_tokenState` statement); all six
# witnesses rebuilt on both sides (rival exit 0 / gold exit 1) with the FORGERY pair
# (claim flipped by dropping the `¬`: gold exit 0, rival exit 1 — the exit codes
# INVERT with the claim, so gold's failure carries information about the claim and no
# case is hollow); eight NEW wrong impls all rejected and eight NEW correct reshapes
# all admitted (see 'attacks' note at the foot of this file).
#
# FIRST AUDIT NOTE (independent re-derivation, post-port). Two corrections were made
# to this battery and are recorded here because they are the kind of thing a recorded
# SOUND cannot see:
#   1. The two ported positives are both closed by the FROZEN tactic script, i.e.
#      their impls are DEFINITIONALLY the specified concatenation. They pass honestly
#      but test only re-spelling. Two positives that genuinely require a REPROOF were
#      added (pos-case-split-email, pos-right-assoc); both were measured to FAIL under
#      the frozen body (`Tactic 'rfl' failed`) and to verify with their own proof.
#   2. Four rivals' `refinement` arguments claimed the visible test suite catches
#      them. Re-derived by replaying the mint/re-check logic: only riv-drop-email
#      actually fails the F2P. The state string is consumed through a keyed
#      fingerprint that is re-derived by the same builder on both sides, so any
#      DETERMINISTIC reshuffle (order swap, sentinel, truncation) round-trips and
#      resolves. Those refinements were corrected in place; the cases are retained as
#      spec-STRENGTH probes, which is what they always were.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's MANDATORY class: `user.pk` / `user.address` were
#     Acc(.,1/2) read-only inputs and the rivals WROTE back into them —
#     frame-mutate-pk, frame-mutate-address — to be rejected for INSUFFICIENT
#     PERMISSION). Lean is referentially transparent — no aliasing, no fractional
#     permission — so a "store into a read-only input" rival is not expressible and
#     the whole class is VACUOUS here. See 'assessment'.
#   * DIVERGENCE / non-termination. `implementation_tokenState` is a total Lean
#     `def`; a non-terminating implementation cannot be written at all — genuinely
#     VACUOUS on lean (not a spec hole, unlike velvet-partial). See 'assessment'.
#   * AXIOM_TESTS (nagini's ax-ref-effective-address-concatenation). The axiom lane
#     is G-AX's job; this gate ignores them. The email normalization + concatenation
#     is modeled DEEPLY over transparent carriers, so there is no consumed axiom
#     here anyway.
from pathlib import Path

INSTANCE = "django__django-13551"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchor ------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and the positives) swap THIS block. The frozen proof body
# (`intro …; unfold …; rfl`) closes both positive shapes unchanged, so the positives
# leave the proof region byte-identical too.
_IMPL = (
    "def implementation_tokenState\n"
    "    (pk password loginTs ts : String) (emailRaw : Option String) : String :=\n"
    "  Id.run do\n"
    "    let email := emailPart emailRaw\n"
    "    let mut s := pk\n"
    "    s := s ++ password\n"
    "    s := s ++ loginTs\n"
    "    s := s ++ ts\n"
    "    s := s ++ email\n"
    "    return s"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-pure-expression: a structurally DIFFERENT but CORRECT impl written as a pure
# concatenation expression (no `Id.run do` monad, no mutable accumulator, no early
# return) — directly returning `pk ++ password ++ loginTs ++ ts ++ emailPart
# emailRaw`. Semantics identical on every input. The `theorem correct_tokenState`
# STATEMENT is byte-identical and the FROZEN proof body (`unfold …; rfl`) still
# closes (the expression is definitionally the concatenation the spec names). No
# reproof, no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition
# over-fit to the monadic accumulator shape).
_POS_PURE = _swap(
    _BASE,
    _IMPL,
    "def implementation_tokenState\n"
    "    (pk password loginTs ts : String) (emailRaw : Option String) : String :=\n"
    "  pk ++ password ++ loginTs ++ ts ++ emailPart emailRaw",
)

# pos-inline-email: a structurally different CORRECT impl that keeps the imperative
# `Id.run do` accumulator but INLINES the email contribution (`emailPart emailRaw`)
# into the final append instead of binding it to a local `email` first. Same result
# on every input. The theorem STATEMENT is byte-identical and the FROZEN proof body
# still closes. No reproof, no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG
# (postcondition over-fit to the exact let-binding shape).
_POS_INLINE = _swap(
    _BASE,
    _IMPL,
    "def implementation_tokenState\n"
    "    (pk password loginTs ts : String) (emailRaw : Option String) : String :=\n"
    "  Id.run do\n"
    "    let mut s := pk\n"
    "    s := s ++ password\n"
    "    s := s ++ loginTs\n"
    "    s := s ++ ts\n"
    "    s := s ++ emailPart emailRaw\n"
    "    return s",
)

# The `_PROOF` anchor: the FROZEN proof body. The two positives above are closed by
# it UNCHANGED, which is exactly their limitation — `rfl` closing means their impls
# are DEFINITIONALLY the frozen concatenation, so they exercise the spec's tolerance
# for re-spelling but never its tolerance for a shape that must be RE-PROVEN. The
# two positives below are the ones that carry that load: each is observationally
# correct on every input, each REQUIRES a genuine reproof (measured: with the frozen
# body left in place both fail — `Tactic 'rfl' failed`, exit 1), and each supplies
# one inside the proof region. `variant_scope` keeps that honest: the theorem
# STATEMENT stays byte-identical and no axiom/sorry/new lemma is admitted, so the
# only thing that changed is the tactic script, which a variant may legitimately
# rewrite. If either FAILS => SPEC-TOO-STRONG.
_PROOF = (
    "  intro pk password loginTs ts emailRaw\n"
    "  unfold problem_spec_tokenState implementation_tokenState\n"
    "  rfl"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


def _reproved(impl_body, proof_body):
    """A variant swapping BOTH the impl body and the frozen tactic script."""
    return _swap(_swap(_BASE, _IMPL, impl_body), _PROOF, proof_body)


# The frozen proof's `intro` line — unique in the file and wholly inside the proof
# region — so the admissibility positive can PREPEND ground `have`s without touching
# the impl, the spec, or the `correct_tokenState` STATEMENT.
_INTRO = "  intro pk password loginTs ts emailRaw"
assert _BASE.count(_INTRO) == 1, "intro anchor drifted from expected text"


# pos-case-split-email: a CORRECT impl that dispatches on the email input instead of
# normalizing it — the `none` branch returns the four-component concatenation, the
# `some e` branch appends `e`. Observationally identical to gold at every input
# (`emailPart none = ""` and `x ++ "" = x`), but NOT definitionally: the frozen `rfl`
# cannot see through the `match`, so this is a shape the spec must be re-proven for.
# Reproof: `cases emailRaw <;> simp [emailPart]`. If it FAILS => SPEC-TOO-STRONG (the
# postcondition would only admit impls that normalize before concatenating).
_POS_CASESPLIT = _reproved(
    "def implementation_tokenState\n"
    "    (pk password loginTs ts : String) (emailRaw : Option String) : String :=\n"
    "  match emailRaw with\n"
    "  | none => pk ++ password ++ loginTs ++ ts\n"
    "  | some e => pk ++ password ++ loginTs ++ ts ++ e",
    "  intro pk password loginTs ts emailRaw\n"
    "  unfold problem_spec_tokenState implementation_tokenState\n"
    "  cases emailRaw <;> simp [emailPart]",
)

# pos-right-assoc: a CORRECT impl that builds the same five components with the
# opposite APPEND ASSOCIATIVITY — `pk ++ (password ++ (loginTs ++ (ts ++ email)))`
# rather than the left-nested spelling the spec names. Equal by associativity of
# `String.append`, but not definitionally so (measured: the frozen `rfl` fails on it),
# so the associativity step has to be discharged. Reproof:
# `simp [String.append_assoc]`. This is the reshape that would expose a postcondition
# over-fit to one particular nesting of `++`. If it FAILS => SPEC-TOO-STRONG.
_POS_RIGHTASSOC = _reproved(
    "def implementation_tokenState\n"
    "    (pk password loginTs ts : String) (emailRaw : Option String) : String :=\n"
    "  pk ++ (password ++ (loginTs ++ (ts ++ emailPart emailRaw)))",
    "  intro pk password loginTs ts emailRaw\n"
    "  unfold problem_spec_tokenState implementation_tokenState\n"
    "  simp [String.append_assoc]",
)


# ===========================================================================
# ADMISSIBILITY (added by the second audit) — the obligation must be SATISFIABLE at
# a concrete, F2P-shaped account, non-vacuously.
#
# The port dropped this lane on the ground that the frozen obligation carries no
# precondition hypothesis, so "nothing could be PRECOND-TOO-STRONG". That is a
# restatement of the carrier's totality, not a demonstration that the lane is
# vacuous. On a total carrier the analogue of PRECOND-TOO-STRONG is the obligation
# being UNSATISFIABLE at exactly a normal input — a spec so tight that no impl,
# including the frozen one, can discharge it there — which is detected by discharging
# the spec predicate at that concrete input BY EVALUATION, as a `have`, before closing
# the frozen obligation verbatim.
#
# The input is F2P-shaped in all three of the shapes the change has to serve: an
# account WITH an email value, the same account with NO email value (the optional
# input's absent branch), and an account whose email value later CHANGES. The third
# `have` is what makes the positive non-vacuous rather than merely satisfiable: it
# discharges, at ground values, the disequality that the whole fingerprint exists to
# produce — two accounts differing ONLY in their email value have DIFFERENT state
# strings. A spec that admitted an impl collapsing those two would satisfy the first
# two `have`s and fail this one.
#
# Nothing is assumed: no new declaration, no axiom/sorry/lemma, the theorem STATEMENT
# is byte-identical, and the ground instances are `have`s prepended to the EXISTING
# tactic body, which then closes the frozen obligation unchanged. Measured: exit 0.
_ADMISS = _swap(
    _BASE,
    _INTRO,
    '  have _ground_present : problem_spec_tokenState "1" "pbkdf2$hash" "" "42"\n'
    '      (some "a@b.example")\n'
    '      (implementation_tokenState "1" "pbkdf2$hash" "" "42"'
    ' (some "a@b.example")) := by\n'
    "    unfold problem_spec_tokenState implementation_tokenState emailPart\n"
    "    decide\n"
    '  have _ground_absent : problem_spec_tokenState "1" "pbkdf2$hash" "" "42" none\n'
    '      (implementation_tokenState "1" "pbkdf2$hash" "" "42" none) := by\n'
    "    unfold problem_spec_tokenState implementation_tokenState emailPart\n"
    "    decide\n"
    "  have _discriminates :\n"
    '      implementation_tokenState "1" "pbkdf2$hash" "" "42" (some "a@b.example")\n'
    '        ≠ implementation_tokenState "1" "pbkdf2$hash" "" "42"'
    ' (some "c@d.example") := by\n'
    "    unfold implementation_tokenState emailPart\n"
    "    decide\n" + _INTRO,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; each carries a witness that
# ELABORATES against the rival and FAILS on the frozen solution. The frozen proof
# body is left in place (it will not close for the reshaped impl, but the gate reads
# the witness, checked in a file with the obligation removed).
# ===========================================================================

# riv-drop-email: THE BUG ITSELF (ports nagini weak-drop-email / model_prepatch.py).
# Builds ONLY the four leading components and stops — the email contribution is never
# appended. This is the pre-patch behaviour verbatim (Solution_prepatch.lean's impl).
# CORRECT on every account whose email contributes the empty string, WRONG whenever
# the email is non-empty. Attacks clause (C-COMPONENTS).
_RIV_DROP = _swap(
    _BASE,
    _IMPL,
    "def implementation_tokenState\n"
    "    (pk password loginTs ts : String) (emailRaw : Option String) : String :=\n"
    "  Id.run do\n"
    "    let mut s := pk\n"
    "    s := s ++ password\n"
    "    s := s ++ loginTs\n"
    "    s := s ++ ts\n"
    "    return s",
)

# riv-reorder-pk-pw: emits `password` BEFORE `pk` (transposes the first two
# components) but still appends the email last. Ports nagini weak-reorder-pk-password.
# The multiset of characters matches gold, but the ORDER differs whenever pk != password.
# Attacks clause (C-ORDER).
_RIV_REORDER = _swap(
    _BASE,
    _IMPL,
    "def implementation_tokenState\n"
    "    (pk password loginTs ts : String) (emailRaw : Option String) : String :=\n"
    "  Id.run do\n"
    "    let email := emailPart emailRaw\n"
    "    let mut s := password\n"
    "    s := s ++ pk\n"
    "    s := s ++ loginTs\n"
    "    s := s ++ ts\n"
    "    s := s ++ email\n"
    "    return s",
)

# riv-truncated-email: appends the email but DROPS its last character
# (`(emailPart emailRaw).dropRight 1`). Ports nagini weak-email-truncated-tail.
# CORRECT only when the email is empty; WRONG on every non-empty email (the trailing
# contribution is one character short). Attacks clause (C-EMAIL-NORM, present branch).
_RIV_TRUNC = _swap(
    _BASE,
    _IMPL,
    "def implementation_tokenState\n"
    "    (pk password loginTs ts : String) (emailRaw : Option String) : String :=\n"
    "  Id.run do\n"
    "    let email := (emailPart emailRaw).dropRight 1\n"
    "    let mut s := pk\n"
    "    s := s ++ password\n"
    "    s := s ++ loginTs\n"
    "    s := s ++ ts\n"
    "    s := s ++ email\n"
    "    return s",
)

# riv-none-sentinel: normalizes an ABSENT email (`none`) to a fixed sentinel string
# `\"X\"` instead of the empty string; a present value is handled correctly. Ports
# nagini weak-none-address-sentinel. CORRECT whenever the email is present, WRONG on
# every email-less account (the spec appends nothing, this appends a sentinel).
# Attacks clause (C-EMAIL-NORM, absent branch).
_RIV_SENTINEL = _swap(
    _BASE,
    _IMPL,
    "def implementation_tokenState\n"
    "    (pk password loginTs ts : String) (emailRaw : Option String) : String :=\n"
    "  Id.run do\n"
    "    let email := match emailRaw with | some e => e | none => \"X\"\n"
    "    let mut s := pk\n"
    "    s := s ++ password\n"
    "    s := s ++ loginTs\n"
    "    s := s ++ ts\n"
    "    s := s ++ email\n"
    "    return s",
)

# riv-swap-loginTs-ts: transposes the MIDDLE two components (`ts` before `loginTs`),
# every component present and identities correct. No direct nagini twin at the value
# level (nagini's per-component loops made these two components positionally
# indistinguishable in the same way); the lean value carrier makes the transposition
# refutable. Attacks clause (C-ORDER) on the `loginTs`/`ts` binders the other rivals
# hold fixed.
_RIV_SWAPMID = _swap(
    _BASE,
    _IMPL,
    "def implementation_tokenState\n"
    "    (pk password loginTs ts : String) (emailRaw : Option String) : String :=\n"
    "  Id.run do\n"
    "    let email := emailPart emailRaw\n"
    "    let mut s := pk\n"
    "    s := s ++ password\n"
    "    s := s ++ ts\n"
    "    s := s ++ loginTs\n"
    "    s := s ++ email\n"
    "    return s",
)


# riv-empty-value-sentinel: splits the sub-domain the sentinel rival CANNOT reach.
# SUB-DOMAIN CLAIM, re-measured by the second audit. The original prose read
# "measured: the other four rivals all satisfy the spec at `some \"\"`", which is
# false as stated: at the witness point ("p","q","l","t") three of them ALSO violate
# the spec at `some \"\"` — but for a reason that has nothing to do with the email
# (they mishandle the other four components there too). Isolating the email requires
# holding every other component EQUAL so no other clause can diverge. Re-measured at
# ("p","p","l","l", some \"\"): exactly ONE of the six rivals violates the spec —
# this one (exit 0); the other five satisfy it (exit 1). So the claim stands, on the
# corrected measurement: this is the only case that pins the absent/empty collapse.
# `emailPart` sends BOTH an absent value (`none`) and a PRESENT-but-empty value
# (`some ""`) to the empty contribution, and that collapse is load-bearing: the
# account state may carry an email attribute whose value is empty, and it must
# fingerprint identically to an account carrying no value at all. This rival treats
# the two differently — `none` contributes the empty string (correct), but a present
# empty value contributes a sentinel. It is therefore correct on every input
# riv-none-sentinel probes and on every non-empty email, and WRONG on exactly the one
# point `some ""` that no other case in this battery visits (measured: the other four
# rivals all leave `some ""` satisfying the spec). Attacks clause (C-EMAIL-NORM) at
# the boundary BETWEEN its two branches.
_RIV_EMPTYVAL = _swap(
    _BASE,
    _IMPL,
    "def implementation_tokenState\n"
    "    (pk password loginTs ts : String) (emailRaw : Option String) : String :=\n"
    "  Id.run do\n"
    "    let email := match emailRaw with\n"
    "      | some e => if e.isEmpty then \"Z\" else e\n"
    "      | none => \"\"\n"
    "    let mut s := pk\n"
    "    s := s ++ password\n"
    "    s := s ++ loginTs\n"
    "    s := s ++ ts\n"
    "    s := s ++ email\n"
    "    return s",
)


def _wit(pk, password, loginTs, ts, emailRaw, note):
    """A refutation witness: `¬ problem_spec_tokenState … (implementation_tokenState …)`
    at a concrete literal (pk, password, loginTs, ts, emailRaw), closed by `decide`
    after unfolding. `decide` reduces the string concatenation and the disequality at
    the literal point. Elaborates against a rival that diverges from the spec there,
    and FAILS on gold (which satisfies the spec at every input) — SEEN to discriminate
    both ways (verified with scripts/lean_verify.sh against rival and gold)."""
    args = f'{pk} {password} {loginTs} {ts} {emailRaw}'
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_tokenState {args}\n"
        f"    (implementation_tokenState {args}) := by\n"
        f"  unfold problem_spec_tokenState implementation_tokenState emailPart\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-pure-expression",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "a structurally different CORRECT impl written as a pure concatenation "
            "expression (no `Id.run do`, no mutable accumulator, no early return), "
            "directly returning `pk ++ password ++ loginTs ++ ts ++ emailPart emailRaw`. "
            "Semantics identical on every input. The `theorem correct_tokenState` "
            "STATEMENT is byte-identical and the FROZEN proof body (`unfold …; rfl`) "
            "still closes — a faithful restructure with no reproof and no new "
            "axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit "
            "to the monadic accumulator shape)."
        ),
    },
    {
        "id": "pos-inline-email",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_INLINE,
        "rationale": (
            "a structurally different CORRECT impl that keeps the imperative `Id.run do` "
            "accumulator but INLINES the email contribution into the final append "
            "instead of binding it to a local first. Result identical on every input. "
            "The theorem STATEMENT is byte-identical and the FROZEN proof body still "
            "closes; no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG "
            "(postcondition over-fit to the exact let-binding shape)."
        ),
    },
    {
        "id": "pos-case-split-email",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CASESPLIT,
        "rationale": (
            "the first positive that actually requires a REPROOF. Both positives above "
            "are closed by the FROZEN tactic script, which means their impls are "
            "DEFINITIONALLY the concatenation the spec names — they test re-spelling, "
            "not the spec's tolerance for a shape that has to be re-derived. This impl "
            "dispatches on the email input (`none` -> four components, `some e` -> "
            "append `e`) instead of normalizing first. Observationally identical at "
            "every input (`emailPart none = \"\"`, `x ++ \"\" = x`) but not "
            "definitionally: with the frozen body left in place it FAILS (`Tactic "
            "'rfl' failed`, exit 1, measured). It supplies its own proof "
            "(`cases emailRaw <;> simp [emailPart]`) with the theorem STATEMENT "
            "byte-identical and no axiom/sorry/new lemma. If it FAILS => "
            "SPEC-TOO-STRONG (the postcondition would admit only impls that normalize "
            "the email before concatenating)."
        ),
    },
    {
        "id": "pos-right-assoc",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_RIGHTASSOC,
        "rationale": (
            "a CORRECT impl that nests the five appends to the RIGHT — `pk ++ "
            "(password ++ (loginTs ++ (ts ++ emailPart emailRaw)))` — where the spec "
            "names the left-nested spelling. Equal by associativity of `String.append`, "
            "but NOT definitionally (measured: the frozen `rfl` fails on it, exit 1), so "
            "the associativity step must be discharged; the case supplies "
            "`simp [String.append_assoc]`. This is the reshape that would expose a "
            "postcondition over-fit to one particular nesting of `++`. If it FAILS => "
            "SPEC-TOO-STRONG."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-f2p-account",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "ADDED by the second audit; the port had dropped this lane. The frozen "
            "obligation carries no precondition hypothesis, so the port concluded "
            "PRECOND-TOO-STRONG was unreachable — but that restates the carrier's "
            "totality rather than demonstrating the lane vacuous. On a total carrier "
            "the analogue is the obligation being UNSATISFIABLE at exactly a normal, "
            "F2P-shaped input, which this case tests directly: the spec predicate is "
            "discharged BY EVALUATION (`decide`) as a `have` at a concrete account "
            "with an email value, then again at the SAME account carrying NO value "
            "(the optional input's absent branch) — both shapes the change has to "
            "serve — and the frozen obligation is then closed verbatim by the "
            "unchanged tactic body. A third ground `have` makes the positive "
            "non-vacuous rather than merely satisfiable: it discharges, at ground "
            "values, the disequality the fingerprint exists to produce — two "
            "accounts differing ONLY in their email value get DIFFERENT state "
            "strings. Nothing is assumed: no new declaration, no axiom/sorry/lemma, "
            "the `correct_tokenState` STATEMENT is byte-identical, and the ground "
            "instances are `have`s prepended to the existing tactic body. If it "
            "FAILS => the obligation is unsatisfiable at a normal input (the "
            "PRECOND-TOO-STRONG analogue on this carrier)."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "riv-drop-email",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP,
        "refinement": (
            "this is the PRE-PATCH behaviour verbatim (Solution_prepatch.lean's impl): "
            "the state string is assembled from the four leading components only and the "
            "email contribution is never appended. Its faithful real patch is the "
            "unchanged pre-change code, whose fingerprint is INVARIANT under an email "
            "change — a token minted before an email change still matches afterwards. "
            "The F2P test asserts the token is REJECTED once the email changes, so the "
            "faithful real patch FAILS the F2P and does NOT resolve. A verifying rival "
            "here is a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "the DISCRIMINATING bug this change fixes. REJECTED by clause (C-COMPONENTS): "
            "the spec pins the result to include `emailPart emailRaw` as the final "
            "component, but the rival stops after `ts`. Witness probes an account with a "
            "NON-EMPTY email (the sub-domain where the omission shows). If it VERIFIES => "
            "SPEC-TOO-WEAK (admits the very bug)."
        ),
        # non-empty email: gold appends "e", rival omits it -> strings differ.
        "witness": _wit('"p"', '"q"', '"l"', '"t"', '(some "e")',
                        "non-empty email: gold appends the email, rival drops it"),
    },
    {
        "id": "riv-reorder-pk-pw",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REORDER,
        "refinement": (
            "emits the password component before the primary-key component (transposes "
            "the first two), so its state string differs from the real one for every "
            "account where pk != password. CORRECTION to the ported argument: this rival "
            "is NOT caught by the visible test suite. The state string is consumed only "
            "through a keyed fingerprint, and the round-trip tests mint and re-check "
            "with the SAME state-string builder, so a deterministic permutation of the "
            "components is self-consistent — it round-trips, it stays timestamp-bound, "
            "and it still changes when the email changes. Re-derived here by replaying "
            "the mint/re-check logic over this rival: F2P PASS, and every token "
            "round-trip / timeout / same-request P2P PASS; no visible test pins a "
            "literal token value (0 hex-literal token assertions in the suite). So its "
            "faithful real patch WOULD resolve, and this case does not stand as a "
            "verify-does-not-imply-resolve probe. It is retained as a pure SPEC-STRENGTH "
            "probe: the spec pins the component ORDER, which is behaviour the test suite "
            "under-determines, and a spec that admitted the transposition would be "
            "strictly weaker than the code it models. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "rationale": (
            "order rival (leading components). REJECTED by clause (C-ORDER): the spec "
            "pins `pk ++ password ++ …`, and the rival produces `password ++ pk ++ …`, "
            "not provably equal whenever pk != password. Witness varies the `pk`/"
            "`password` binders to DISTINCT values so the transposition is observable. "
            "If it VERIFIES => SPEC-TOO-WEAK (leading component order unconstrained)."
        ),
        # pk="1", password="2" distinct: gold => "12lte", rival => "21lte".
        "witness": _wit('"1"', '"2"', '"l"', '"t"', '(some "e")',
                        "distinct pk/password: gold keeps pk-then-password, rival swaps them"),
    },
    {
        "id": "riv-truncated-email",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TRUNC,
        "refinement": (
            "appends the email contribution but drops its final character, so two "
            "distinct emails sharing an all-but-last-character prefix fingerprint "
            "identically and a token is NOT invalidated across such a change — a real "
            "residue of the very defect this change is about (re-derived: the two "
            "addresses differing only in the final character collide under this rival). "
            "CORRECTION to the ported argument: that residual hole is NOT exercised by "
            "the visible tests. The F2P's before/after addresses differ well before "
            "their last character, and the round-trip tests re-check with the same "
            "builder, so the truncation is self-consistent. Re-derived by replaying the "
            "mint/re-check logic: F2P PASS and all token round-trip P2P PASS. So the "
            "faithful real patch WOULD resolve; the case stands as a SPEC-STRENGTH probe "
            "of the near-miss, not as a resolve break. If it VERIFIES => SPEC-TOO-WEAK "
            "(the email contribution is only partially pinned, and the spec would then "
            "admit an impl carrying a prefix-collision hole the tests cannot see)."
        ),
        "rationale": (
            "value-level near-miss on the email contribution. REJECTED by clause "
            "(C-EMAIL-NORM, present branch): the spec pins the WHOLE `emailPart emailRaw` "
            "as the trailing contribution, but the rival emits it one character short, "
            "not provably equal on any email of length >= 1. Witness varies the "
            "`emailRaw` binder to a >=2-char value so the truncation is observable and "
            "distinguishes this near-miss from riv-drop-email. If it VERIFIES => "
            "SPEC-TOO-WEAK (the email contribution is only partially pinned)."
        ),
        # emailRaw = some "ab": gold appends "ab", rival appends "a".
        "witness": _wit('"p"', '"q"', '"l"', '"t"', '(some "ab")',
                        "multi-char email: gold appends the whole email, rival drops its last char"),
    },
    {
        "id": "riv-none-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SENTINEL,
        "refinement": (
            "for an account carrying NO email value the spec contributes the empty "
            "string, but this rival contributes a fixed sentinel character, so the "
            "fingerprint of an email-less account differs from the real one. CORRECTION "
            "to the ported argument: the claim that such accounts 'never round-trip' is "
            "wrong — round-tripping only needs the builder to agree with ITSELF, which a "
            "constant sentinel does. Re-derived by replaying the mint/re-check logic over "
            "this rival, including the email-less and blank-email accounts: F2P PASS and "
            "every token round-trip / timeout P2P PASS. So the faithful real patch WOULD "
            "resolve. The case is retained as a SPEC-STRENGTH probe of the absent-email "
            "branch: that branch is pinned by the spec and under-determined by the tests, "
            "and it is the sub-domain no other rival reaches. If it VERIFIES => "
            "SPEC-TOO-WEAK (the absent-email normalization is unpinned)."
        ),
        "rationale": (
            "REJECTED by clause (C-EMAIL-NORM, absent branch): `emailPart none = \"\"`, so "
            "the spec requires NOTHING appended on the `none` case, but the rival appends "
            "a sentinel. Witness varies the `emailRaw` binder to `none` — the sub-domain "
            "the other rivals never probe. If it VERIFIES => SPEC-TOO-WEAK (the "
            "absent-email normalization is unpinned)."
        ),
        # emailRaw = none: gold appends nothing, rival appends "X".
        "witness": _wit('"p"', '"q"', '"l"', '"t"', 'none',
                        "absent email: gold appends nothing, rival appends a sentinel"),
    },
    {
        "id": "riv-swap-loginTs-ts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SWAPMID,
        "refinement": (
            "transposes the middle two components (token timestamp before last-login "
            "timestamp), so the state string differs from the real one whenever the two "
            "renderings differ. CORRECTION to the ported argument, for the same reason as "
            "the other order rival: a deterministic permutation is self-consistent under "
            "mint/re-check, so the round-trip P2P tests do NOT fail. Re-derived by "
            "replaying that logic: F2P PASS, all token round-trip / timeout P2P PASS. The "
            "faithful real patch WOULD resolve. Retained as a SPEC-STRENGTH probe of the "
            "component order on the two binders every other rival holds fixed. If it "
            "VERIFIES => SPEC-TOO-WEAK (middle component order unconstrained)."
        ),
        "rationale": (
            "order rival (middle components). REJECTED by clause (C-ORDER): the spec "
            "pins `… ++ loginTs ++ ts ++ …`, and the rival produces `… ++ ts ++ loginTs "
            "++ …`, not provably equal whenever loginTs != ts. Witness varies the "
            "`loginTs`/`ts` binders to DISTINCT values — the binders every other rival "
            "holds fixed — so this rival is what exercises them. If it VERIFIES => "
            "SPEC-TOO-WEAK (middle component order unconstrained)."
        ),
        # loginTs="L", ts="T" distinct: gold => "pqLTe", rival => "pqTLe".
        "witness": _wit('"p"', '"q"', '"L"', '"T"', '(some "e")',
                        "distinct loginTs/ts: gold keeps loginTs-then-ts, rival swaps them"),
    },
    {
        "id": "riv-empty-value-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EMPTYVAL,
        "refinement": (
            "distinguishes an account carrying NO email value from one carrying a PRESENT "
            "but EMPTY value, contributing a sentinel for the latter. The spec collapses "
            "the two (`emailPart` sends both to the empty contribution), which is the "
            "faithful reading: the normalization the modeled function applies maps an "
            "absent and a falsy-empty value to the same contribution. A faithful real "
            "patch of this rival would fingerprint a blank-valued account differently "
            "from an unset one. Like the other value rivals it is self-consistent under "
            "mint/re-check, so — re-derived by replaying that logic — the visible F2P and "
            "token round-trip P2P all PASS and it WOULD resolve; it is a SPEC-STRENGTH "
            "probe, not a resolve break. Its value is the sub-domain: it is the ONLY case "
            "in this battery that visits `some \"\"`, the point where the spec's "
            "absent/empty collapse is decided. RE-MEASURED by the second audit, which "
            "corrected an overstated version of this claim: it is not true that the "
            "other rivals all satisfy the spec at `some \"\"` outright — at the witness "
            "point three of them violate it there too, for reasons unrelated to the "
            "email. Isolating the email means holding every other component EQUAL so no "
            "other clause can diverge; at (\"p\",\"p\",\"l\",\"l\", some \"\") exactly "
            "ONE rival violates the spec — this one (witness build exit 0) — and the "
            "other five satisfy it (exit 1). On that corrected measurement the collapse "
            "is demonstrated here and nowhere else in the battery."
        ),
        "rationale": (
            "REJECTED by clause (C-EMAIL-NORM) at the boundary between its branches: "
            "`emailPart (some \"\") = \"\"`, so a present-but-empty value must contribute "
            "NOTHING, exactly as an absent one does; this rival appends a sentinel there. "
            "It is correct on `none` (unlike riv-none-sentinel) and correct on every "
            "non-empty email (unlike riv-truncated-email), so its witness point is "
            "reachable by no other case. If it VERIFIES => SPEC-TOO-WEAK (the "
            "absent/empty collapse the normalization exists to enforce is unpinned)."
        ),
        # emailRaw = some "": gold appends nothing, rival appends "Z".
        "witness": _wit('"p"', '"q"', '"l"', '"t"', '(some "")',
                        "present-but-empty email: gold appends nothing, rival appends a sentinel"),
    },
]


# SECOND-AUDIT ATTACK LOG (probes built and measured, NOT shipped as cases —
# recorded so the next auditor need not re-derive which directions were already
# swept, and which corner of the carrier is genuinely out of reach).
#
# SPEC-TOO-WEAK probe (8 NEW wrong impls, none in the battery; all REJECTED, exit 1):
#   drop the loginTs component entirely; move the email contribution to the FRONT;
#   append a separator before the second component; append the email TWICE; append
#   only the email's LENGTH rendered as a string (the pre-patch bug wearing a
#   length-preserving disguise); append the email only when it exceeds one character
#   (a second-order near-miss on the present branch); lower-case the email
#   contribution; strip surrounding whitespace from it. No spec hole: every one is
#   rejected, and for the six that reduce, a witness at a discriminating literal
#   elaborates against the rival (exit 0), so each rejection is attributable to the
#   spec and not to tactic breakage.
#
# TWO of those eight are REJECTED but NOT WITNESSABLE on this carrier, which is why
# they are not shipped as cases: the case-folding rival (`.toLower`) and the
# whitespace-stripping rival (`.trim`). Both are genuinely wrong (a mixed-case or
# space-padded email value fingerprints identically to its folded/stripped form, so a
# token survives a change between them), and both would be valuable near-misses on the
# present branch. But their refutation does not REDUCE: `decide` reports
# "did not reduce to `isTrue` or `isFalse` ... reduction got stuck at the `Decidable`
# instance", because `String.toLower`/`String.trim` go through `String.mapAux` /
# `String.Iterator`, whose recursion is not unfolded by the `Decidable` instance for
# `String` equality. Measured, all exit 1: `decide`, `decide +kernel`,
# `simp [String.toLower, String.map, String.mapAux]` (leaves
# `⊢ ¬"pqlt" ++ "E".toLower = "pqltE"`), and a refutation restated over the computable
# `.data` projection (deterministic `whnf` heartbeat timeout). A witness that cannot be
# closed cannot be shipped, and shipping the rival WITHOUT one would be exactly the
# vacuous reject case the witness rule exists to forbid. Recorded as a carrier
# limitation on `String`'s per-character combinators, not as a spec finding: the six
# witnessable rivals already pin the present branch (whole value, untruncated, at the
# right position), which is the clause these two would attack.
#
# SPEC-TOO-STRONG probe (4 NEW correct reshapes beyond the four shipped positives; all
# ADMITTED, exit 0): `String.join [pk, password, loginTs, ts, emailPart emailRaw]`;
# a `List.foldl (· ++ ·) ""` over the same five components; `emailRaw.elim "" id` in
# place of `emailPart` (bypassing the named normalizer entirely); and a
# pair-GROUPED nesting `(pk ++ password) ++ (loginTs ++ ts) ++ emailPart emailRaw`.
# Each needed its own proof (`simp [String.join]`, `simp [List.foldl]`,
# `cases emailRaw <;> simp`, `simp [String.append_assoc]`) and each closed, so the
# spec admits list-shaped, fold-shaped, normalizer-free and re-grouped assemblies. No
# soundness hole.
#
# No @ContractOnly axioms and no opaque callees: the email normalization
# (`emailPart`) and the five-component concatenation are modeled DEEPLY over
# transparent carriers, so the axiom lane is vacuous here and belongs to G-AX
# regardless.
AXIOM_TESTS = []
