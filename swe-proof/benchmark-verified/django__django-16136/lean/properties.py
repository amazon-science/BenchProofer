# properties.py — G-PBT falsification battery for django__django-16136 (lean lane).
# NOT a Lean module; a record of adversarial cases the gate elaborates against
# the frozen spec. PORTED from the nagini sibling's properties.py, with each
# rival's argument re-expressed against this backend's carrier.
#
# DEFENDED SURFACE (read from Solution.lean):
#   implementation_disallowedResponse (isAsync : Bool) (allowed : List String)
#     : DisallowedResponse
#   The object a view yields when a request uses a method it does not permit.
#   `problem_spec_disallowedResponse` is a conjunction of exactly TWO independent
#   top-level clauses, and between them they pin the whole output:
#     (C1) result.awaitable = isAsync
#          — the returned object is an awaitable wrapper EXACTLY when the view
#            operates in asynchronous mode. This is the DISCRIMINATING clause:
#            Solution_prepatch.lean returns `awaitable := false` unconditionally
#            and cannot close C1 on isAsync = true (the G-DIFF signal).
#     (C2) result.allowed = allowed
#          — payload preservation: the object carries exactly the permitted-method
#            list it was given, in BOTH modes. Deciding the delivery convention
#            must not change WHAT is delivered. This is the frame half (spec_guide
#            §5): without it the payload component would be unconstrained and a
#            rival could put anything there.
#
# GROUNDED ORACLE, no echo. C1 pins `awaitable` to the input `isAsync` directly
# (Bool = Bool, fully unfolded — no opaque callee, no answer-key `def`), and C2
# pins the payload to the input list. The axioms region of the frozen file is
# empty, so there is no oracle for a rival to ECHO: any impl satisfying C1 has
# already computed the right value, because `isAsync` IS the ground truth. So no
# "wrong echo that nonetheless verifies" rival is constructible here, and the
# nagini file's grounded-oracle slot is carried over as an honest cheapest-correct
# POSITIVE control (pos-direct-flag) rather than as a reject case.
#
# CARRIER NARROWING vs the nagini sibling. Nagini modelled the delivery over a
# two-field heap object (`Delivered(is_awaitable, Reply(methods))`) with the
# payload pinned by OBJECT IDENTITY (`Result().reply.methods is allowed_methods`)
# under a fractional read permission. This bundle models the same two observables
# as fields of a `deriving DecidableEq` structure over a `List String`, so:
#   * the nagini P1 clause ports one-for-one onto C1 (Bool mapping), and every
#     nagini P1 rival ports with it;
#   * the nagini P2 IDENTITY pin becomes a VALUE pin (C2). Lean has no aliasing,
#     so `is` and `=` coincide on this carrier and the clause is strictly
#     re-expressed, not weakened. The nagini weak-fresh-reply rival (a brand-new
#     empty list in place of the given one) ports as weak-empty-payload;
#   * the whole structure is decidable at literal inputs, so every witness below
#     states the spec predicate directly and closes by `decide` — no conditioning
#     on an opaque term is needed anywhere in this battery.
#
# VACUOUS / DROPPED CLASSES (stated per directive, never silently omitted):
#   * FRAME / PERMISSION-MUTATION lane — VACUOUS on lean. Nagini shipped
#     `frame-mutate-allowed-methods`, which appends to the read-only method list
#     and must be rejected for INSUFFICIENT PERMISSION at Acc(...,1/2). That
#     rejection is a statement about fractional heap permissions, which this
#     carrier does not have: Lean is referentially transparent, `allowed : List
#     String` is an immutable value, and there is no aliasable input to overwrite.
#     There is nothing to port and no substitute is fabricated. The frame CONCERN
#     it encoded — that the payload must survive the delivery decision unchanged —
#     is what clause C2 states outright, and it is attacked below by three rivals
#     (weak-empty-payload, weak-async-payload-loss, weak-payload-reversed).
#   * DIVERGENCE / NON-TERMINATION lane — VACUOUS on lean, and the nagini sibling
#     carries no such case in any event. `implementation_disallowedResponse` is a
#     total Lean `def`, so a diverging implementation cannot be written at all and
#     the class does not exist on this carrier. This is NOT the velvet situation,
#     where under `set_option loom.semantics.termination "partial"` a
#     non-terminating impl satisfies every `ensures` vacuously and the frozen spec
#     ADMITS the rival — a known spec hole rather than a vacuous class (see
#     the corpus-wide termination-semantics finding). On lean the class really is vacuous.
# WHY SPEC-TOO-WEAK IS STRUCTURALLY IMPOSSIBLE HERE (audit, machine-checked).
# The two clauses TOGETHER pin the whole output, and that is provable rather than
# argued. Both of these were built against the frozen spec and elaborate (exit 0):
#   ∀ isAsync allowed r1 r2, spec isAsync allowed r1 → spec isAsync allowed r2
#       → r1 = r2                                          -- the spec is functional
#   ∀ isAsync allowed r, spec isAsync allowed r ↔ r = implementation ...
#                                                          -- gold's output is the
#                                                             UNIQUE satisfier
# `DisallowedResponse` has exactly the two fields the two clauses constrain, so
# there is no unconstrained component for a rival to exploit: any impl satisfying
# the spec agrees with gold at every input of `Bool × List String`. So no rival can
# both verify and be observably wrong, and the uniqueness lane's job here is to
# confirm the CLAUSES are each load-bearing (each rival is refuted by exactly one
# of them) rather than to hunt for a hole that cannot exist. The audit also ran 8
# NEW wrong impls not in this battery — payload duplicated / upper-cased /
# deduplicated / drop-last / take-one, and C1 conditioned on a single literal
# payload, on payload-length parity, and on payload length with both clauses wrong
# — and every one was rejected; and 7 NEW correct reshapes (match on the flag,
# double negation, `cond`, payload through reverse.reverse, through map id,
# through append-nil, and a `decide`-built flag), every one of which verifies,
# three of them needing a real list lemma rather than `rfl`. The spec is neither
# too weak nor too strong on this carrier.
#
#   * AXIOM lane — DROPPED. meta.axioms == [], the axioms region is empty, and
#     both values the handler consults are unchanged inputs modelled as plain
#     parameters, so no callee is abstracted. Nagini's single AXIOM_TESTS probe
#     re-ran the real delivery mechanism; that is G-AX's job and this gate ignores
#     it. AXIOM_TESTS = [].

from pathlib import Path

INSTANCE = "django__django-16136"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- Frozen editable regions, extracted verbatim so the manifest breaks loudly
# if Solution.lean ever changes. The impl region body and the proof TACTIC body
# are the only regions a variant may touch; the spec view and the byte-identical
# `theorem correct_disallowedResponse` statement are never edited, so same_spec
# and obligation-preservation hold by construction.

_IMPL_OLD = """\
def implementation_disallowedResponse
    (isAsync : Bool) (allowed : List String) : DisallowedResponse := Id.run do
  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
  if isAsync then
    return { response with awaitable := true }
  else
    return response"""

assert _BASE.count(_IMPL_OLD) == 1, "impl region drifted from expected text"

_PROOF_OLD = """\
  intro isAsync allowed
  unfold problem_spec_disallowedResponse implementation_disallowedResponse
  cases isAsync <;> exact ⟨rfl, rfl⟩"""

assert _BASE.count(_PROOF_OLD) == 1, "proof region drifted from expected text"

# Every variant impl reuses the frozen signature line verbatim.
_HDR = """\
def implementation_disallowedResponse
    (isAsync : Bool) (allowed : List String) : DisallowedResponse := Id.run do
"""


def _impl(new_impl, new_proof=None):
    """A full Solution.lean variant: impl body replaced, and for a reshaped
    positive the proof tactic body replaced too. No new axiom / lemma / sorry."""
    out = _swap(_BASE, _IMPL_OLD, new_impl)
    if new_proof is not None:
        out = _swap(out, _PROOF_OLD, new_proof)
    return out


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY. Each is a structurally different
# but behaviourally identical correct impl, shipped WITH a proof that actually
# closes for the new shape. The theorem STATEMENT is byte-identical; only the
# tactic body moves. All three were built against the shared workspace.
# ---------------------------------------------------------------------------

# pos-branch-reorder: ports nagini pos-branch-reorder. Test the SYNCHRONOUS case
# first and handle the asynchronous case in the else — mirrored control flow,
# identical values. The frozen `cases isAsync <;> exact ⟨rfl, rfl⟩` still closes
# because each branch reduces definitionally.
_POS_REORDER = _HDR + """\
  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
  if !isAsync then
    return response
  else
    return { response with awaitable := true }"""

_POS_REORDER_PROOF = """\
  intro isAsync allowed
  unfold problem_spec_disallowedResponse implementation_disallowedResponse
  cases isAsync <;> exact ⟨rfl, rfl⟩"""

# pos-direct-flag: ports nagini pos-direct-bool, the honest grounded-oracle
# control. C1 pins the awaitable field to the input `isAsync`, so binding that
# input into a local and building the object ONCE — dropping the branch entirely —
# is correct by construction. The branch collapse makes the proof strictly
# cheaper: no case split is needed, so `exact ⟨rfl, rfl⟩` alone closes it. If this
# failed, the spec would be constraining the impl's SHAPE rather than its
# observable behaviour (SPEC-TOO-STRONG).
_POS_DIRECT_FLAG = _HDR + """\
  let flag : Bool := isAsync
  let response : DisallowedResponse := { awaitable := flag, allowed := allowed }
  return response"""

_POS_DIRECT_FLAG_PROOF = """\
  intro isAsync allowed
  unfold problem_spec_disallowedResponse implementation_disallowedResponse
  exact ⟨rfl, rfl⟩"""

# pos-collapsed-pure: ports nagini pos-collapsed-direct, adapted to this carrier.
# Nagini's collapse dropped the temporaries but stayed a Python statement body;
# the lean analogue drops the imperative wrapper as well — no `Id.run do`, no
# `let`, no early `return`, just the record built directly. This is the strongest
# shape-independence control in the battery: it confirms the spec does not
# secretly depend on the monadic encoding the frozen impl happens to use.
_POS_COLLAPSED_PURE = """\
def implementation_disallowedResponse
    (isAsync : Bool) (allowed : List String) : DisallowedResponse :=
  { awaitable := isAsync, allowed := allowed }"""

_POS_COLLAPSED_PURE_PROOF = """\
  intro isAsync allowed
  unfold problem_spec_disallowedResponse implementation_disallowedResponse
  exact ⟨rfl, rfl⟩"""

# admiss-shape: ports nagini admiss-f2p-shaped-input. Nagini injected a concrete
# method-token list into the impl body and pinned the two observable facts with
# in-body `Assert(...)`; the lean analogue states the SPEC PREDICATE itself at
# three concrete inhabited points as in-body `have`s discharged by `decide`. It
# keeps the frozen impl body and the frozen proof script otherwise verbatim, so
# the only thing it can fail on is the spec being unsatisfiable at a normal input
# — i.e. a vacuous/over-strong precondition, which would make the whole
# obligation hollow. The three points cover both execution modes and the empty
# payload.
_ADMISS_SHAPE = _HDR + """\
  have _hAsyncShape :
      problem_spec_disallowedResponse true ["GET", "POST", "OPTIONS"]
        { awaitable := true, allowed := ["GET", "POST", "OPTIONS"] } := by
    unfold problem_spec_disallowedResponse; decide
  have _hSyncShape :
      problem_spec_disallowedResponse false ["GET", "POST", "OPTIONS"]
        { awaitable := false, allowed := ["GET", "POST", "OPTIONS"] } := by
    unfold problem_spec_disallowedResponse; decide
  have _hEmptyShape :
      problem_spec_disallowedResponse true []
        { awaitable := true, allowed := ([] : List String) } := by
    unfold problem_spec_disallowedResponse; decide
  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
  if isAsync then
    return { response with awaitable := true }
  else
    return response"""


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each edits ONLY the
# impl region and ships a `witness` that was BUILT BOTH WAYS before shipping:
# it elaborates against the rival, and on the frozen solution `decide` proves the
# negation FALSE (gold satisfies the spec there), so every witness is a confirmed
# discriminator rather than a tautology or a tactic-breakage artifact.
# ---------------------------------------------------------------------------

# weak-always-sync: ports nagini weak-always-sync-prepatch. THE PRE-CHANGE
# BEHAVIOUR — the bare object is handed back unconditionally, never an awaitable
# wrapper. Correct on the whole synchronous sub-domain, wrong on the asynchronous
# one. Identical to Solution_prepatch.lean's impl.
_WEAK_ALWAYS_SYNC = _HDR + """\
  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
  return response"""

# weak-always-async: ports nagini weak-always-async. The dual — always hand back
# an awaitable wrapper, even for a synchronous view. Correct on the asynchronous
# sub-domain, wrong on the synchronous one (the common path).
_WEAK_ALWAYS_ASYNC = _HDR + """\
  let response : DisallowedResponse := { awaitable := true, allowed := allowed }
  return response"""

# weak-inverted: ports nagini weak-inverted-mapping. Flips C1 outright — awaitable
# iff SYNCHRONOUS. Wrong on the entire domain while still producing a well-formed
# object, so the rejection is squarely the C1 mapping and not the shape.
_WEAK_INVERTED = _HDR + """\
  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
  if isAsync then
    return response
  else
    return { response with awaitable := true }"""

# weak-async-nonempty-only: NO nagini counterpart — a PARTIAL-DOMAIN near-miss on
# C1 that the three rivals above cannot isolate. Each of those is wrong on a whole
# half of the `isAsync` domain, so any of them is refuted at almost any input.
# This one gets C1 right everywhere EXCEPT when the view is asynchronous and the
# permitted-method list is empty, where it falls back to the bare object.
#
# AUDIT SCOPE CORRECTION. This case is kept as a SPEC-DOMAIN rival only. The
# empty permitted-method list is a point of the modeled domain `Bool × List
# String` at which the spec has force, and the rival's C1 violation there is a
# genuine, machine-checked spec violation — but it is NOT a reachable
# configuration of the real system, and this case must not be advertised as a
# verify-does-not-imply-resolve break. See _C1_UNREACHABLE below for the derived
# argument. The port originally attached the shared `_C1_TAIL` (which asserts a
# failing F2P row) to this case; that claim was false, because a faithful patch
# conditioning the wrapper on a non-empty payload passes BOTH F2P rows. Corrected
# here. The uniform-in-`allowed` concern this case encodes is real and is now
# also carried by weak-async-readverb-only at a REACHABLE input.
_WEAK_ASYNC_NONEMPTY_ONLY = _HDR + """\
  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
  if isAsync && !allowed.isEmpty then
    return { response with awaitable := true }
  else
    return response"""

# weak-async-readverb-only: ADDED BY AUDIT. NO nagini counterpart. The
# payload-conditioned C1 attack made REACHABLE. weak-async-nonempty-only
# conditions the delivery convention on the payload being non-empty, which is a
# valid spec-domain rival but degenerate as real behaviour: the permitted-method
# payload is derived and is never empty (the base view class always contributes
# its own always-present handler), and a view carrying no request handler at all
# is classified synchronous, so the asynchronous-and-empty sub-domain is doubly
# unreachable. This rival conditions the SAME way — on the payload contents —
# but at a point that is ordinary: it hands back an awaitable wrapper only when
# the permitted methods mention the read verb, so a write-only asynchronous view
# (exactly the shape in the public report: a view defining only an asynchronous
# write handler) regresses. That IS a failing F2P row, so this case restores the
# verify-does-not-imply-resolve claim that weak-async-nonempty-only cannot carry
# while keeping the payload-conditioned attack on C1's uniformity in `allowed`.
_WEAK_ASYNC_READVERB_ONLY = _HDR + """\
  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
  if isAsync && allowed.contains "GET" then
    return { response with awaitable := true }
  else
    return response"""

# weak-empty-payload: ports nagini weak-fresh-reply-identity onto the value pin.
# Keeps the delivery mapping C1 entirely CORRECT and instead builds the object
# over a brand-new EMPTY list rather than the one it was given. Rejected only by
# C2. (Nagini needed an `is` pin to catch this because a value-only abstraction
# would miss a fresh-but-equal list; on this carrier the fresh list is also
# UNEQUAL, so the value pin catches it directly.)
_WEAK_EMPTY_PAYLOAD = _HDR + """\
  let response : DisallowedResponse := { awaitable := false, allowed := [] }
  if isAsync then
    return { response with awaitable := true }
  else
    return response"""

# weak-async-payload-loss: NO nagini counterpart — the payload attack made
# MODE-DEPENDENT. weak-empty-payload drops the payload in both modes and so is
# refutable in either; this one preserves it correctly on the synchronous path and
# loses it only on the asynchronous one. That is precisely the "the payload is
# identical in both modes" half of C2, and it is the shape a real regression takes
# when the wrapping path is written separately from the direct path and forgets to
# carry the payload through. No other rival distinguishes per-mode payload
# handling.
_WEAK_ASYNC_PAYLOAD_LOSS = _HDR + """\
  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
  if isAsync then
    return { awaitable := true, allowed := [] }
  else
    return response"""

# weak-payload-reversed: NO nagini counterpart. Every payload rival above replaces
# the list with the EMPTY one, so C2 is only ever pinned against total loss; if
# C2 constrained the payload merely up to membership, length, or "some list", all
# of them would still be caught and nothing would show that C2 pins the list
# EXACTLY. This rival returns a PERMUTATION — the same tokens, reversed — so it is
# refutable only if C2 is a genuine list equality. The tightest miss available on
# this clause.
_WEAK_PAYLOAD_REVERSED = _HDR + """\
  let response : DisallowedResponse := { awaitable := false, allowed := allowed.reverse }
  if isAsync then
    return { response with awaitable := true }
  else
    return response"""


def _witness(args):
    """State the spec predicate directly at a concrete input and refute it. The
    structure derives DecidableEq and every argument is a literal, so `decide`
    settles it with no conditioning on any opaque term. Checked in a file with the
    frozen obligation removed, so no tactic script can interfere."""
    return f"""\
example : ¬ problem_spec_disallowedResponse {args}
    (implementation_disallowedResponse {args}) := by
  unfold problem_spec_disallowedResponse implementation_disallowedResponse
  decide"""


# The refinement argument shared by the C1 rivals. The F2P test
# test_http_method_not_allowed_responds_correctly drives both a synchronous and an
# asynchronous view and asserts, per row, that whether the returned object must be
# awaited matches the view's mode; a faithful patch that gets that mapping wrong
# fails the corresponding subTest outright.
_C1_TAIL = (
    " The F2P test asserts, for a synchronous and an asynchronous view "
    "respectively, that the returned object must-be-awaited flag equals the "
    "view's mode; this rival's faithful real patch therefore fails that "
    "assertion on the row named below, so it is a genuine "
    "verify-does-not-imply-resolve break rather than an artifact."
)

# AUDIT-ADDED. The honest scope note for a rival whose C1 violation sits at an
# EMPTY permitted-method payload. The modeled domain is `Bool × List String` and
# the spec has force at every point of it, so such a rival is a real, machine
# checked spec violation and belongs in the uniqueness lane. But the empty list
# is not a reachable configuration of the real system, so the case must not claim
# a failing F2P row. Derived from the UNCHANGED inputs only (no gold needed):
# the permitted-method payload is computed from the handlers the view class
# carries, the base class always contributes its own always-present handler, so
# the payload always holds at least that one token; and a class carrying no
# request handler beyond that one is classified SYNCHRONOUS, so asynchronous mode
# cannot co-occur with an empty payload at all. Both halves of the sub-domain are
# therefore unreachable, and the rival's faithful patch passes both F2P rows.
_C1_UNREACHABLE = (
    " HONEST SCOPE NOTE (audit): this rival's C1 violation sits at an EMPTY "
    "permitted-method payload, which is a point of the MODELED domain but not a "
    "reachable configuration of the real system: the payload is derived from the "
    "handlers the view carries and the base class always contributes its own "
    "always-present handler, so the payload is never empty; and a view carrying "
    "no other handler is classified synchronous, so asynchronous mode and an "
    "empty payload cannot co-occur. This rival's faithful patch therefore PASSES "
    "both F2P rows, and this case is NOT advertised as a "
    "verify-does-not-imply-resolve break. It stands as a SPEC-DOMAIN uniqueness "
    "rival: the spec quantifies over all of `Bool × List String` and this rival "
    "violates C1 at a point of that domain, which is what the case attests. The "
    "same payload-conditioned attack at a REACHABLE input is carried by "
    "weak-async-readverb-only."
)

# The refinement argument shared by the C2 (payload) rivals. Stated HONESTLY: the
# F2P test observes the delivered object's TYPE, not the method list it carries,
# so a payload-dropping patch is NOT caught by the F2P assertions. C2 is the frame
# half of the postcondition (spec_guide §5) and is deliberately stronger than the
# F2P, because without it the payload component would be entirely unconstrained
# and any rival could put anything there.
_C2_TAIL = (
    " HONEST SCOPE NOTE: unlike the C1 rivals, this one's faithful real patch "
    "would still satisfy the F2P assertions, which observe the delivered "
    "object's TYPE and its must-be-awaited flag but never read back the "
    "permitted-method list it carries; no test in this instance's F2P or P2P set "
    "pins that payload. So this case is NOT advertised as a "
    "verify-does-not-imply-resolve break. It is the FRAME obligation (spec_guide "
    "§5): the delivered payload is unchanged context that the modeled change must "
    "carry through untouched, and C2 is the clause that says so. Were C2 absent "
    "or loose, the payload component would be unconstrained and a rival could "
    "return an arbitrary method list while verifying — which is exactly what this "
    "rival does, and why the clause needs an attacker even though the F2P is "
    "blind to it. Its faithful patch would deliver a 405 whose permitted-method "
    "header no longer reflects the view's actual permitted methods, a real "
    "behavioural regression outside the F2P's view."
)


SPEC_TESTS = [
    # ----- soundness / positive controls (must verify) --------------------
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER, _POS_REORDER_PROOF),
        "rationale": (
            "ports nagini pos-branch-reorder: the SYNCHRONOUS case is tested "
            "first and the ASYNCHRONOUS case handled in the else — mirrored "
            "control flow, identical values. Keeps both obligations (C1 "
            "awaitable = isAsync, C2 allowed = allowed); the frozen `cases "
            "isAsync <;> exact ⟨rfl, rfl⟩` still closes because each branch "
            "reduces definitionally. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-direct-flag",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_DIRECT_FLAG, _POS_DIRECT_FLAG_PROOF),
        "rationale": (
            "ports nagini pos-direct-bool, the honest grounded-oracle control. "
            "C1 pins the awaitable field to the input `isAsync`, so binding that "
            "input into a local and building the object once — dropping the "
            "branch entirely — is correct by construction. The collapse removes "
            "the case split, so `exact ⟨rfl, rfl⟩` closes it without `cases`. "
            "The cheapest correct impl on this carrier; if it fails => "
            "SPEC-TOO-STRONG (the spec would be pinning the impl's shape rather "
            "than its observable behaviour)."
        ),
    },
    {
        "id": "pos-collapsed-pure",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_COLLAPSED_PURE, _POS_COLLAPSED_PURE_PROOF),
        "rationale": (
            "ports nagini pos-collapsed-direct and pushes it further on this "
            "carrier: nagini's collapse dropped the temporaries but stayed a "
            "statement body, whereas this drops the imperative wrapper too — no "
            "`Id.run do`, no `let`, no early `return`, the record built directly. "
            "The strongest shape-independence control here: it confirms the spec "
            "does not secretly depend on the monadic encoding the frozen impl "
            "uses. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS_SHAPE),
        "rationale": (
            "ports nagini admiss-f2p-shaped-input. Nagini pinned the two "
            "observable facts at a concrete method-token list with in-body "
            "`Assert(...)`; the lean analogue states the SPEC PREDICATE itself at "
            "three concrete inhabited points as in-body `have`s discharged by "
            "`decide` — both execution modes with a realistic three-token payload, "
            "plus the empty payload. Impl body and frozen proof script are "
            "otherwise verbatim, so the only thing this can fail on is the spec "
            "being unsatisfiable at a normal input. If it fails => "
            "PRECOND-TOO-STRONG / a vacuous obligation, which would make the "
            "whole theorem hollow."
        ),
    },
    # ----- uniqueness rivals against C1 (the discriminating clause) --------
    {
        "id": "weak-always-sync",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS_SYNC),
        "witness": _witness('true ["GET", "OPTIONS"]'),
        "refinement": (
            "this IS the pre-change behaviour, identical to the impl in "
            "Solution_prepatch.lean: the bare object is handed back "
            "unconditionally and never an awaitable wrapper. Its faithful real "
            "patch is simply the unpatched repo, whose asynchronous view yields "
            "an object the calling machinery then tries to await — the exact "
            "reported failure." + _C1_TAIL + " (Row: the asynchronous view, "
            "which expects a must-be-awaited object and gets a bare one.) Does "
            "NOT resolve."
        ),
        "rationale": (
            "rejected by C1: result.awaitable = isAsync, but this rival pins the "
            "flag to false unconditionally, so on the asynchronous sub-domain "
            "false ≠ true. Rejection comes from the discriminating clause, not "
            "from shape — a well-formed object is still produced and C2 holds. "
            "Witness at (true, [\"GET\", \"OPTIONS\"]). If it verifies => "
            "SPEC-TOO-WEAK, and the spec would not even see the reported bug."
        ),
    },
    {
        "id": "weak-always-async",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS_ASYNC),
        "witness": _witness('false ["POST"]'),
        "refinement": (
            "ports nagini weak-always-async: the dual partial-domain rival, always "
            "wrapping even for a synchronous view. Its faithful real patch drops "
            "the mode guard and always returns the wrapper, so a synchronous view "
            "hands back an object the synchronous calling path never resolves — a "
            "regression on the common path." + _C1_TAIL + " (Row: the synchronous "
            "view, which expects a bare object and gets a must-be-awaited one.) "
            "Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1: the flag is pinned to true unconditionally, so on the "
            "synchronous sub-domain true ≠ false. C2 is untouched, so the "
            "rejection is squarely the C1 mapping. Witness at (false, [\"POST\"]) "
            "— the opposite mode from weak-always-sync, so the two probe genuinely "
            "different halves of the `isAsync` domain. If it verifies => "
            "SPEC-TOO-WEAK on the synchronous sub-domain."
        ),
    },
    {
        "id": "weak-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_INVERTED),
        "witness": _witness("false []"),
        "refinement": (
            "ports nagini weak-inverted-mapping: inverts the mapping outright — "
            "awaitable iff SYNCHRONOUS. A faithful real patch with the mode guard "
            "negated is wrong for both kinds of view at once." + _C1_TAIL +
            " (Rows: BOTH — the synchronous view expects a bare object and the "
            "asynchronous one a must-be-awaited object, and this rival has each "
            "exactly backwards, so both subTests fail.) Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1 on the ENTIRE domain: awaitable = !isAsync contradicts "
            "awaitable = isAsync for every value of the flag. The strongest C1 "
            "violation in the battery. Witness at (false, []) — the empty payload, "
            "which also confirms the C1 refutation does not depend on the payload "
            "being inhabited. If it verifies => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-async-nonempty-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ASYNC_NONEMPTY_ONLY),
        "witness": _witness("true []"),
        "refinement": (
            "NO nagini counterpart. A PARTIAL-DOMAIN near-miss: the delivery "
            "convention is correct everywhere except for an asynchronous view "
            "whose permitted-method list is empty, where it falls back to the bare "
            "object. A faithful real patch conditioning the wrapping on the "
            "payload being non-empty behaves correctly for every ordinary view and "
            "regresses only the degenerate one." + _C1_UNREACHABLE
        ),
        "rationale": (
            "rejected by C1 on exactly the sub-domain isAsync = true ∧ allowed = "
            "[]. One of two rivals whose C1 violation depends on the SECOND "
            "binder: weak-always-sync / weak-always-async / weak-inverted are each "
            "wrong on a whole half of the `isAsync` domain and so are refutable at "
            "almost any input, which means none of them shows that C1 must hold "
            "UNIFORMLY in `allowed`. Without this case and "
            "weak-async-readverb-only, a rival that conditioned the delivery "
            "convention on the payload would verify unnoticed. Witness at "
            "(true, []) — a boundary a byte-fuzzer never targets. If it verifies "
            "=> SPEC-TOO-WEAK on that sub-domain. Scope: the violated point is "
            "unreachable in the real system, so the attestation is about the "
            "spec's domain, not about a failing F2P row; see _C1_UNREACHABLE."
        ),
    },
    {
        "id": "weak-async-readverb-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ASYNC_READVERB_ONLY),
        "witness": _witness('true ["POST", "OPTIONS"]'),
        "refinement": (
            "ADDED BY AUDIT to carry, at a REACHABLE input, the "
            "payload-conditioned C1 attack that weak-async-nonempty-only can only "
            "make at an unreachable one. Same shape of error — the delivery "
            "convention is conditioned on the payload CONTENTS instead of on the "
            "view's mode alone — but the point of failure is ordinary rather than "
            "degenerate: an awaitable wrapper is handed back only when the "
            "permitted methods mention the read verb, so an asynchronous view that "
            "permits only a write verb gets the bare object. That is exactly the "
            "configuration in the public report (a view defining only an "
            "asynchronous write handler, probed with a disallowed read request)." +
            _C1_TAIL + " (Row: the asynchronous view, whose permitted-method "
            "payload need not mention the read verb.) Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1 on the sub-domain isAsync = true ∧ the payload does "
            "not contain the read verb. Together with weak-async-nonempty-only "
            "this pins C1's UNIFORMITY in the second binder — that the delivery "
            "convention may not be conditioned on the payload in any way — and "
            "unlike that case it does so at an input the real system actually "
            "reaches, so it is a genuine verify-does-not-imply-resolve break. "
            "Witness at (true, [\"POST\", \"OPTIONS\"]): a non-empty payload "
            "without the read verb, a point no other rival in the battery probes "
            "and one no byte-fuzzer targets. If it verifies => SPEC-TOO-WEAK on "
            "payload-conditioned delivery."
        ),
    },
    # ----- uniqueness rivals against C2 (the payload/frame clause) ---------
    {
        "id": "weak-empty-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_EMPTY_PAYLOAD),
        "witness": _witness('false ["GET", "POST"]'),
        "refinement": (
            "ports nagini weak-fresh-reply-identity onto this carrier's value pin. "
            "Keeps the delivery mapping C1 entirely correct and builds the object "
            "over a brand-new EMPTY list instead of the one it was given. Nagini "
            "needed an object-identity pin to catch this, because a value-only "
            "abstraction would miss a fresh-but-equal list; on this carrier the "
            "fresh list is also UNEQUAL, so the value pin catches it directly and "
            "the clause is re-expressed rather than weakened." + _C2_TAIL
        ),
        "rationale": (
            "rejected by C2 alone: result.allowed = allowed, but the rival's "
            "payload is the fresh empty list. C1 is deliberately satisfied, so the "
            "rejection is attributable purely to the payload-preservation clause. "
            "Witness at (false, [\"GET\", \"POST\"]) — a non-empty payload in "
            "synchronous mode, a point no C1 rival probes. If it verifies => "
            "SPEC-TOO-WEAK: the payload component would be unconstrained."
        ),
    },
    {
        "id": "weak-async-payload-loss",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ASYNC_PAYLOAD_LOSS),
        "witness": _witness('true ["GET", "POST"]'),
        "refinement": (
            "NO nagini counterpart — the payload attack made MODE-DEPENDENT. "
            "weak-empty-payload drops the payload in both modes and so is "
            "refutable in either; this one preserves it correctly on the "
            "synchronous path and loses it only on the asynchronous one. That is "
            "the shape a real regression actually takes when the wrapping path is "
            "written separately from the direct path and forgets to carry the "
            "payload through — the wrapper closes over a freshly built object "
            "rather than the one already constructed." + _C2_TAIL
        ),
        "rationale": (
            "rejected by C2 on the asynchronous sub-domain only. C1 holds "
            "everywhere and C2 holds on the synchronous path, so this isolates the "
            "'the payload is identical in BOTH modes' half of C2 — the half "
            "weak-empty-payload cannot isolate, since it breaks C2 uniformly. "
            "Witness at (true, [\"GET\", \"POST\"]): same payload as "
            "weak-empty-payload but the opposite mode, which is exactly the pair "
            "of points that separates a per-mode payload bug from a uniform one. "
            "If it verifies => SPEC-TOO-WEAK on per-mode payload handling."
        ),
    },
    {
        "id": "weak-payload-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PAYLOAD_REVERSED),
        "witness": _witness('true ["GET", "HEAD", "OPTIONS"]'),
        "refinement": (
            "NO nagini counterpart, and the tightest miss available on C2. Both "
            "payload rivals above replace the list with the EMPTY one, so C2 is "
            "only ever pinned against TOTAL loss; this rival returns a PERMUTATION "
            "— the same tokens, reversed — and is therefore refutable only if C2 is "
            "a genuine list equality rather than a constraint up to membership, "
            "length, or 'some list'. A faithful real patch reordering the "
            "permitted-method list would render the 405's permitted-method header "
            "in an order that no longer matches the view's declared method order, "
            "which is the ordering the sibling handler for the same view also "
            "renders." + _C2_TAIL + " Additionally weaker than the other two on "
            "the real-behaviour axis: the rendered header carries the same token "
            "SET, so the divergence is confined to ordering."
        ),
        "rationale": (
            "rejected by C2, and only at a permutation point. This is the case "
            "that makes 'C2 pins the payload EXACTLY' a measured claim rather than "
            "an assumed one: if C2 constrained the payload only up to membership "
            "or length, weak-empty-payload and weak-async-payload-loss would both "
            "still be caught while this one slipped through. Witness at (true, "
            "[\"GET\", \"HEAD\", \"OPTIONS\"]) — a three-token payload whose "
            "reversal is distinguishable, a fresh input point and the longest "
            "payload any witness probes. If it verifies => SPEC-TOO-WEAK on "
            "payload ORDER."
        ),
    },
]

# No @ContractOnly axioms and no opaque callee on this path (meta.axioms == [],
# the axioms region is empty, deep_model_references none): both values the
# handler consults are unchanged inputs modelled as plain parameters, so nothing
# is abstracted behind a callee. Nothing for the axiom lane to execute here, and
# the axiom lane is G-AX's job in any event.
AXIOM_TESTS = []
