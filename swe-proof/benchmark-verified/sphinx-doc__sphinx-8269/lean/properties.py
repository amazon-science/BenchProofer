"""properties.py — PBT falsification manifest for sphinx-doc__sphinx-8269 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Each case edits ONLY the implementation region (and,
for the positive controls, the proof body); the spec view is untouched, so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition, never to a tampered spec.

DEFENDED SURFACE
----------------
The modeled function reports the outcome of validating one remote hyperlink that
carries both a target document and an in-page fragment, given two independent
server observations (an HTTP status code and whether the fragment is present) and
three arbitrary payloads (the two candidate explanatory messages and the outcome
of the unchanged success continuation):

    implementation_classifyLink
        (statusCode : Nat) (anchorFound : Bool)
        (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome

pinned by the single load-bearing equality clause `result = <dispatch table>`.
The dispatch table is a TOTAL, fully-GROUNDED decision over the inputs:

  * (E) status in the 4xx/5xx error band — settled by the STATUS ALONE, the
    fragment never consulted:
      (E1) "unauthorized" (401)        -> ⟨"working"," - unauthorized",0⟩
      (E2) "service unavailable" (503) -> ⟨"ignored", httpErrMsg, 0⟩
      (E3) every other error status    -> ⟨"broken",  httpErrMsg, 0⟩
  * (N) a non-error status — now the fragment governs:
      (N1) fragment absent             -> ⟨"broken",  anchorErrMsg, 0⟩
      (N2) fragment present            -> onSuccess (the unchanged continuation)

The carrier is FULLY TRANSPARENT: `Nat` / `Bool` / `String` / `Int`, no opaque
callee. The 4xx/5xx band, the 401/503 specials, and the message routing are all
computed, so every rival is refutable by `decide` at one concrete input — no
carrier conditioning is needed and no witness binds a hypothesis (nothing to be
inconsistent).

The LOAD-BEARING change clauses are (E3) and the (E)-before-(N) ordering: on an
error status the report carries the HTTP-level message and is settled BEFORE the
fragment search, never the fragment-level "absent" message. This is the exact
F2P discriminator (a 500 must be reported with the HTTP transport error, not
"Anchor not found"). Every INPUT BINDER of the spec is exercised by the reject
witnesses below: `statusCode` across 200/400/401/500/502/503; `anchorFound` at
both polarities; `httpErrMsg` vs `anchorErrMsg` as the discriminating datum; and
`onSuccess` as the deferred non-error-present outcome.

The band THRESHOLD (`400 ≤ statusCode`) is a load-bearing clause in its own
right and is covered by `band-lower-edge`, added during audit: the other rivals
all vary which branch fires within a correctly-drawn band, so before that case
the boundary itself was unprobed and a spec pinning only `401 ≤ statusCode`
would have satisfied the whole battery.

Two further clauses were unprobed until a later audit and now carry their own
rivals. `nonerror-absent-wrong-datum` covers the MESSAGE ROUTING on clause N1:
the existing rivals discriminate the two messages only on the error side (E3) or
attack the non-error side's control flow (N2), so a spec that left N1's message
free would have passed. `code-field` covers the numeric CODE component: every
other witness differs from the frozen impl in the status label or the message, so
the third field of the reported triple could have been left unpinned unnoticed —
its witness is stated at an input where gold and rival agree on both the label
and the message and differ ONLY in the code.

The ADMISSIBILITY lane is present (`admiss-ground-f2p`) and is not vacuous here;
see the porting note below for why the earlier "no precondition, so nothing to
constrain" reasoning was wrong.

PORTING NOTES (which nagini cases port, which are omitted, and why)
-------------------------------------------------------------------
The nagini sibling models `classify_fragment_link(status, fragment_present) ->
(status-class, datum-kind)`, a two-code abstraction of the same dispatch. The
lean carrier is RICHER (it carries the actual message strings and the deferred
success outcome), so several nagini rivals port and gain sharper witnesses.

  * nagini `pos-control-flat-dispatch` (soundness) -> `pos-flat-dispatch`:
    a structurally-different CORRECT impl (pure functional expression, `match`
    on `anchorFound` with the present/absent branches inverted). Proof re-closed.
    If it fails to verify => SPEC-TOO-STRONG.
  * added `pos-commuted-guard` (soundness): a second correct impl with the range
    guard's conjunction commuted (`statusCode < 600 ∧ 400 ≤ statusCode`) and a
    nested else-if ladder. Guards that the spec pins the classification, not one
    syntactic guard order. Proof re-closed.
  * nagini `admiss-f2p-shaped-selfcall` (admissibility) -> `admiss-ground-f2p`.
    An earlier note here recorded this class as VACUOUS because the lean
    obligation carries NO precondition hypothesis, so "there is nothing to
    over/under-constrain". That reason is WRONG and the case is restored: the
    analogue on a total carrier is not a precondition to relax but the obligation
    being UNSATISFIABLE at exactly an F2P-shaped input, which a positive that
    discharges the spec predicate at that concrete input — by evaluation, as a
    `have`, before closing the frozen obligation verbatim — tests directly. Built
    and verified (exit 0) with `variant_scope` clean, so the class is expressible
    here and its omission was a real gap in the ported battery, not a property of
    the carrier.
  * nagini `partial-prepatch-no-gate` -> `prepatch-no-gate` (reject): the
    pre-patch skeleton — the status is never consulted, only the fragment. On an
    error status with the fragment absent it reports the fragment-absent message
    instead of the HTTP message. This IS the bug the patch fixes.
  * nagini `wrong-error-datum` -> `wrong-error-datum` (reject): the general-error
    branch attaches the FRAGMENT-level message to a broken report instead of the
    HTTP-level message — right status label, wrong datum. The load-bearing hole.
  * nagini `partial-drop-401` -> `drop-401` (reject): 401 falls into the
    general-error branch (broken/HTTP) instead of the working/unauthorized report.
  * nagini `partial-drop-503` -> `drop-503` (reject): 503 falls into the
    general-error branch (broken) instead of the ignored report.
  * nagini `const-echo-failed-transport` -> `const-echo` (reject): the cheapest
    "echo the F2P answer" impl — always ⟨"broken", httpErrMsg, 0⟩.
  * nagini `partial-nonerror-present-misclassified` -> `nonerror-present-broken`
    (reject): on a non-error status, always report broken/fragment-absent
    regardless of `anchorFound`, so a present fragment (which must defer to
    `onSuccess`) is mis-reported.
  * nagini `vacuous-nonterminating-loop` (`diverge`-class): OMITTED, but NOT
    because the class is inexpressible — an earlier note here claimed a
    non-terminating impl "cannot be expressed at all" on this carrier, and that
    is false. Measured: as a plain `def`, unguarded self-recursion is refused by
    the equation compiler ("fail to show termination", exit 1), but as a
    `partial def` it elaborates fine and passes `variant_scope` cleanly (no new
    theorem, spec view untouched). So the class IS expressible. It is omitted
    because it can be neither a verify case nor an ATTRIBUTABLE reject case:
      - not a spec hole: the diverging `partial def` does NOT verify against the
        frozen obligation (four independent tactic attempts — `simp [spec, impl]`,
        `unfold spec; rfl`, `unfold spec; aesop`, and a `first | decide |
        simp_all | trivial | cases` ladder — all exit 1, `unsolved goals` /
        `rfl failed`), so there is nothing to escalate;
      - not a landable reject: a `partial def` has no equation lemma, so a
        witness cannot reduce it. `unfold implementation_classifyLink` fails
        outright ("Tactic `unfold` failed to unfold"), and every claim about the
        impl is stuck the same way — the exit code would attest to an
        irreducible term, not to a refutation, which is exactly the
        `witness-undecided` shape the gate rejects.
    Recorded as omitted-with-reason rather than inexpressible, since the
    distinction matters: the honest statement is "expressible, does not verify,
    not attributable", not "cannot be written".
  * nagini frame/permission-mutation class: VACUOUS here — the surface takes only
    pass-by-value primitives / immutable inputs and Lean is referentially
    transparent, so there is no aliased read-only reference to overwrite. No
    substitute fabricated.
  * `AXIOM_TESTS`: dropped — the axiom lane is G-AX's job and this gate ignores
    it. (The bundle has no `opaque`/`axiom` callee anyway; `axiom_check.py` is a
    skip stub.)

Every reject case carries a `witness`: a Lean snippet negating the spec
predicate at one concrete input, checked in a file with the frozen obligation
removed. Each was built BOTH ways with scripts/lean_verify.sh — it ELABORATES
against the rival (rival exit 0) and FAILS against the frozen solution (gold exit
1), so it is a real discriminator and not a tautology.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8269"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (Solution.lean edited) fails loudly."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks. The full frozen impl body (between # impl-start / # impl-end,
# exclusive) is swapped wholesale by every variant, so the spec view (everything
# outside the impl+proof regions) stays byte-identical to Solution.lean.
# ---------------------------------------------------------------------------
_GOLD_IMPL = (
    "def implementation_classifyLink\n"
    "    (statusCode : Nat) (anchorFound : Bool)\n"
    "    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do\n"
    "  -- The reply's HTTP status is consulted before its body: an error status in the\n"
    "  -- 4xx/5xx range settles the outcome on its own.\n"
    "  if 400 ≤ statusCode ∧ statusCode < 600 then\n"
    "    if statusCode = 401 then\n"
    "      return ⟨\"working\", \" - unauthorized\", 0⟩\n"
    "    if statusCode = 503 then\n"
    "      return ⟨\"ignored\", httpErrMsg, 0⟩\n"
    "    return ⟨\"broken\", httpErrMsg, 0⟩\n"
    "  -- A non-error status: now the in-page fragment is consulted.\n"
    "  if anchorFound = false then\n"
    "    return ⟨\"broken\", anchorErrMsg, 0⟩\n"
    "  return onSuccess\n"
)

_PROOF_HEAD = "-- proof-start"
_PROOF_TAIL = "-- proof-end"


def _with_impl(new_impl: str) -> str:
    """Build a full Solution variant whose impl-region body is `new_impl`."""
    return _swap(_BASE, _GOLD_IMPL, new_impl)


def _swap_proof(src: str, new_proof_body: str) -> str:
    """Replace everything strictly between the proof markers with
    `new_proof_body`. The `theorem correct_classifyLink` STATEMENT is re-emitted
    byte-identically inside `new_proof_body`; only the tactic body changes, which
    variant_scope permits."""
    s = src.index(_PROOF_HEAD)
    e = src.index(_PROOF_TAIL)
    return src[: s + len(_PROOF_HEAD)] + "\n" + new_proof_body + "\n" + src[e:]


# The theorem statement, re-emitted verbatim so the obligation survives.
_THM_STMT = (
    "theorem correct_classifyLink :\n"
    "    ∀ (statusCode : Nat) (anchorFound : Bool)\n"
    "      (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome),\n"
    "      problem_spec_classifyLink statusCode anchorFound httpErrMsg anchorErrMsg onSuccess\n"
    "        (implementation_classifyLink statusCode anchorFound httpErrMsg anchorErrMsg onSuccess) := by"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-flat-dispatch) A structurally-different CORRECT impl: a pure functional
# expression (no `Id.run do`, no early `return`) with the error ladder as nested
# else-if and the non-error case as a `match anchorFound` whose present/absent
# arms are written in the inverted order. Pins exactly the same table.
_POS_FLAT_IMPL = (
    "def implementation_classifyLink\n"
    "    (statusCode : Nat) (anchorFound : Bool)\n"
    "    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome :=\n"
    "  if 400 ≤ statusCode ∧ statusCode < 600 then\n"
    "    if statusCode = 401 then ⟨\"working\", \" - unauthorized\", 0⟩\n"
    "    else if statusCode = 503 then ⟨\"ignored\", httpErrMsg, 0⟩\n"
    "    else ⟨\"broken\", httpErrMsg, 0⟩\n"
    "  else\n"
    "    match anchorFound with\n"
    "    | true  => onSuccess\n"
    "    | false => ⟨\"broken\", anchorErrMsg, 0⟩\n"
)
_POS_FLAT_PROOF = (
    _THM_STMT + "\n"
    "  intro statusCode anchorFound httpErrMsg anchorErrMsg onSuccess\n"
    "  unfold problem_spec_classifyLink implementation_classifyLink\n"
    "  cases anchorFound <;> simp\n"
)
_POS_FLAT = _swap_proof(_with_impl(_POS_FLAT_IMPL), _POS_FLAT_PROOF)

# (pos-commuted-guard) A second correct impl with the range guard's conjunction
# COMMUTED (`statusCode < 600 ∧ 400 ≤ statusCode`) and the non-error case written
# as `if anchorFound = true then onSuccess else …`. Semantically identical; the
# equality clause is agnostic to guard order and to how the boolean is tested.
_POS_COMM_IMPL = (
    "def implementation_classifyLink\n"
    "    (statusCode : Nat) (anchorFound : Bool)\n"
    "    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome :=\n"
    "  if statusCode < 600 ∧ 400 ≤ statusCode then\n"
    "    if statusCode = 401 then ⟨\"working\", \" - unauthorized\", 0⟩\n"
    "    else if statusCode = 503 then ⟨\"ignored\", httpErrMsg, 0⟩\n"
    "    else ⟨\"broken\", httpErrMsg, 0⟩\n"
    "  else if anchorFound = true then onSuccess\n"
    "  else ⟨\"broken\", anchorErrMsg, 0⟩\n"
)
_POS_COMM_PROOF = (
    _THM_STMT + "\n"
    "  intro statusCode anchorFound httpErrMsg anchorErrMsg onSuccess\n"
    "  unfold problem_spec_classifyLink implementation_classifyLink\n"
    "  by_cases h : 400 ≤ statusCode ∧ statusCode < 600\n"
    "  · simp [h]\n"
    "  · have h' : ¬ (statusCode < 600 ∧ 400 ≤ statusCode) := fun hc => h ⟨hc.2, hc.1⟩\n"
    "    simp [h, h']\n"
    "    cases anchorFound <;> simp\n"
)
_POS_COMM = _swap_proof(_with_impl(_POS_COMM_IMPL), _POS_COMM_PROOF)


# ===========================================================================
# ADMISSIBILITY — expect "verify"
# ===========================================================================
# The frozen obligation is universally quantified with NO precondition
# hypothesis, so there is no precondition to relax; the analogue of
# PRECOND-TOO-STRONG on a total carrier is the obligation being UNSATISFIABLE at
# exactly an F2P-shaped input. This case tests that directly: the impl is the
# FROZEN one (untouched) and the spec predicate is discharged at the concrete
# F2P-shaped point (an error status in the general band with the fragment ABSENT,
# the one place where the two candidate messages disagree) by EVALUATION, as a
# `have`, before the frozen tactic body closes the obligation verbatim. Nothing
# is assumed: no new declaration, statement byte-identical, only the tactic body
# gains a leading ground instance.
_ADMISS_PROOF = (
    _THM_STMT + "\n"
    "  have _ground : problem_spec_classifyLink 500 false \"H\" \"A\" ⟨\"working\", \"\", 0⟩\n"
    "      (implementation_classifyLink 500 false \"H\" \"A\" ⟨\"working\", \"\", 0⟩) := by\n"
    "    unfold problem_spec_classifyLink implementation_classifyLink\n"
    "    decide\n"
    "  intro statusCode anchorFound httpErrMsg anchorErrMsg onSuccess\n"
    "  unfold problem_spec_classifyLink implementation_classifyLink\n"
    "  simp only [Id.run, bind, pure]\n"
)
_ADMISS = _swap_proof(_BASE, _ADMISS_PROOF)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (prepatch-no-gate) The pre-patch skeleton: the status is NEVER consulted; only
# the fragment governs. On an error status with the fragment absent it reports
# the fragment-absent message instead of the HTTP message.
_RIVAL_PREPATCH = (
    "def implementation_classifyLink\n"
    "    (statusCode : Nat) (anchorFound : Bool)\n"
    "    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do\n"
    "  if anchorFound = false then\n"
    "    return ⟨\"broken\", anchorErrMsg, 0⟩\n"
    "  return onSuccess\n"
)

# (wrong-error-datum) The gate IS consulted and 401/503 dispatched correctly, but
# the general-error branch attaches the FRAGMENT-level message to the broken
# report instead of the HTTP-level message — right label, wrong datum.
_RIVAL_WRONGDATUM = (
    "def implementation_classifyLink\n"
    "    (statusCode : Nat) (anchorFound : Bool)\n"
    "    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do\n"
    "  if 400 ≤ statusCode ∧ statusCode < 600 then\n"
    "    if statusCode = 401 then\n"
    "      return ⟨\"working\", \" - unauthorized\", 0⟩\n"
    "    if statusCode = 503 then\n"
    "      return ⟨\"ignored\", httpErrMsg, 0⟩\n"
    "    return ⟨\"broken\", anchorErrMsg, 0⟩\n"
    "  if anchorFound = false then\n"
    "    return ⟨\"broken\", anchorErrMsg, 0⟩\n"
    "  return onSuccess\n"
)

# (drop-401) The 401 special-case dropped: 401 falls into the general-error
# branch -> broken/HTTP instead of working/unauthorized.
_RIVAL_DROP401 = (
    "def implementation_classifyLink\n"
    "    (statusCode : Nat) (anchorFound : Bool)\n"
    "    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do\n"
    "  if 400 ≤ statusCode ∧ statusCode < 600 then\n"
    "    if statusCode = 503 then\n"
    "      return ⟨\"ignored\", httpErrMsg, 0⟩\n"
    "    return ⟨\"broken\", httpErrMsg, 0⟩\n"
    "  if anchorFound = false then\n"
    "    return ⟨\"broken\", anchorErrMsg, 0⟩\n"
    "  return onSuccess\n"
)

# (drop-503) The 503 special-case dropped: 503 falls into the general-error
# branch -> broken instead of ignored.
_RIVAL_DROP503 = (
    "def implementation_classifyLink\n"
    "    (statusCode : Nat) (anchorFound : Bool)\n"
    "    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do\n"
    "  if 400 ≤ statusCode ∧ statusCode < 600 then\n"
    "    if statusCode = 401 then\n"
    "      return ⟨\"working\", \" - unauthorized\", 0⟩\n"
    "    return ⟨\"broken\", httpErrMsg, 0⟩\n"
    "  if anchorFound = false then\n"
    "    return ⟨\"broken\", anchorErrMsg, 0⟩\n"
    "  return onSuccess\n"
)

# (const-echo) The cheapest "echo the F2P answer" impl: unconditionally report
# ⟨"broken", httpErrMsg, 0⟩ — the exact shape a 500 expects, but wrong everywhere
# else (401, 503, and every non-error case).
_RIVAL_CONST = (
    "def implementation_classifyLink\n"
    "    (statusCode : Nat) (anchorFound : Bool)\n"
    "    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do\n"
    "  return ⟨\"broken\", httpErrMsg, 0⟩\n"
)

# (band-lower-edge) The error band's LOWER EDGE slipped from `≤` to `<`, so the
# first error status (400) is no longer in the band and falls through to the
# fragment search. Every other status classifies correctly, so this is invisible
# except exactly at the threshold the change introduces.
_RIVAL_BAND400 = (
    "def implementation_classifyLink\n"
    "    (statusCode : Nat) (anchorFound : Bool)\n"
    "    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do\n"
    "  if 400 < statusCode ∧ statusCode < 600 then\n"
    "    if statusCode = 401 then\n"
    "      return ⟨\"working\", \" - unauthorized\", 0⟩\n"
    "    if statusCode = 503 then\n"
    "      return ⟨\"ignored\", httpErrMsg, 0⟩\n"
    "    return ⟨\"broken\", httpErrMsg, 0⟩\n"
    "  if anchorFound = false then\n"
    "    return ⟨\"broken\", anchorErrMsg, 0⟩\n"
    "  return onSuccess\n"
)

# (nonerror-absent-wrong-datum) The NON-ERROR fragment-absent branch carries the
# HTTP-level message instead of the fragment-level one. This attacks clause N1's
# DATUM, which no other rival reaches: `wrong-error-datum` attacks the datum on
# the ERROR side (E3) and `nonerror-present-broken` attacks the non-error side's
# CONTROL (N2), so before this case the message routing on N1 was unprobed and a
# spec that left N1's message free would have satisfied the whole battery.
_RIVAL_NONERR_DATUM = (
    "def implementation_classifyLink\n"
    "    (statusCode : Nat) (anchorFound : Bool)\n"
    "    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do\n"
    "  if 400 ≤ statusCode ∧ statusCode < 600 then\n"
    "    if statusCode = 401 then\n"
    "      return ⟨\"working\", \" - unauthorized\", 0⟩\n"
    "    if statusCode = 503 then\n"
    "      return ⟨\"ignored\", httpErrMsg, 0⟩\n"
    "    return ⟨\"broken\", httpErrMsg, 0⟩\n"
    "  if anchorFound = false then\n"
    "    return ⟨\"broken\", httpErrMsg, 0⟩\n"
    "  return onSuccess\n"
)

# (code-field) The third component of the reported triple perturbed (0 -> 1) on
# the general-error branch. Every status LABEL and every message is still routed
# correctly, so this is invisible to any check that only compares the label and
# the message: it isolates the numeric code, the one output component no other
# rival varies.
_RIVAL_CODE = (
    "def implementation_classifyLink\n"
    "    (statusCode : Nat) (anchorFound : Bool)\n"
    "    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do\n"
    "  if 400 ≤ statusCode ∧ statusCode < 600 then\n"
    "    if statusCode = 401 then\n"
    "      return ⟨\"working\", \" - unauthorized\", 0⟩\n"
    "    if statusCode = 503 then\n"
    "      return ⟨\"ignored\", httpErrMsg, 0⟩\n"
    "    return ⟨\"broken\", httpErrMsg, 1⟩\n"
    "  if anchorFound = false then\n"
    "    return ⟨\"broken\", anchorErrMsg, 0⟩\n"
    "  return onSuccess\n"
)

# (nonerror-present-broken) On a non-error status, always report the
# fragment-absent broken result regardless of `anchorFound`, so a present
# fragment (which must defer to `onSuccess`) is mis-reported.
_RIVAL_NONERR = (
    "def implementation_classifyLink\n"
    "    (statusCode : Nat) (anchorFound : Bool)\n"
    "    (httpErrMsg anchorErrMsg : String) (onSuccess : Outcome) : Outcome := Id.run do\n"
    "  if 400 ≤ statusCode ∧ statusCode < 600 then\n"
    "    if statusCode = 401 then\n"
    "      return ⟨\"working\", \" - unauthorized\", 0⟩\n"
    "    if statusCode = 503 then\n"
    "      return ⟨\"ignored\", httpErrMsg, 0⟩\n"
    "    return ⟨\"broken\", httpErrMsg, 0⟩\n"
    "  return ⟨\"broken\", anchorErrMsg, 0⟩\n"
)


# --- witnesses (checked with the frozen obligation removed) ----------------
# Each negates the spec predicate at one concrete input; the carrier is
# transparent, so `decide` closes and no witness binds a hypothesis. Binder
# values are diversified across witnesses so every input the spec depends on is
# varied by some reject witness.

def _wit(statusCode, anchorFound, httpErrMsg, anchorErrMsg, onSuccess):
    args = f"{statusCode} {anchorFound} {httpErrMsg} {anchorErrMsg} {onSuccess}"
    return (
        "example : ¬ problem_spec_classifyLink\n"
        f"    {args}\n"
        "    (implementation_classifyLink\n"
        f"      {args}) := by\n"
        "  unfold problem_spec_classifyLink implementation_classifyLink\n"
        "  decide"
    )


# Error status (500), fragment absent: gold => broken/HTTP, prepatch => broken/frag.
_WIT_PREPATCH = _wit('500', 'false', '"He"', '"An"', '⟨"working", "", 0⟩')
# General error (502), fragment present: gold => broken/HTTP, rival => broken/frag.
_WIT_WRONGDATUM = _wit('502', 'true', '"Hx"', '"Ax"', '⟨"working", "", 0⟩')
# 401 (fragment absent): gold => working/unauthorized, rival => broken/HTTP.
_WIT_DROP401 = _wit('401', 'false', '"H1"', '"A1"', '⟨"redirected", "r", 1⟩')
# 503, fragment present: gold => ignored/HTTP, rival => broken/HTTP.
_WIT_DROP503 = _wit('503', 'true', '"H2"', '"A2"', '⟨"working", "", 0⟩')
# 401, fragment present: gold => working/unauthorized, const => broken/HTTP.
_WIT_CONST = _wit('401', 'true', '"H3"', '"A3"', '⟨"working", "w", 0⟩')
# Non-error (200), fragment present: gold => onSuccess, rival => broken/frag.
# The ONLY witness that makes the result depend on `onSuccess` (a rich outcome).
_WIT_NONERR = _wit('200', 'true', '"H4"', '"A4"', '⟨"redirected", "R", 7⟩')
# statusCode=400 exactly — the band's lower EDGE, with the fragment PRESENT so
# the fall-through is observable as onSuccess rather than the fragment message:
# gold => ⟨"broken", httpErrMsg, 0⟩, rival => onSuccess.
_WIT_BAND400 = _wit('400', 'true', '"H5"', '"A5"', '⟨"redirected", "R", 7⟩')
# Non-error (200) with the fragment ABSENT: gold => ⟨"broken", anchorErrMsg, 0⟩,
# rival => ⟨"broken", httpErrMsg, 0⟩. Discriminates the two messages on the N1
# branch (the mirror of wrong-error-datum, which discriminates them on E3).
_WIT_NONERR_DATUM = _wit('200', 'false', '"H6"', '"A6"', '⟨"working", "", 0⟩')
# General error (500), fragment absent: gold => code 0, rival => code 1. Same
# label and same message on both sides, so ONLY the numeric code separates them.
_WIT_CODE = _wit('500', 'false', '"H7"', '"A7"', '⟨"working", "", 0⟩')


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-flat-dispatch", "kind": "soundness", "expect": "verify",
     "module": _POS_FLAT,
     "rationale": "a structurally-different but correct impl: a pure functional "
                  "expression (no imperative do-block / early return) with the "
                  "error ladder as nested else-if and the non-error case a `match "
                  "anchorFound` whose present/absent arms are inverted. Pins "
                  "exactly the same total table (clauses E1-E3, N1-N2 all hold). "
                  "Proof re-closed by `cases anchorFound <;> simp`. If it fails to "
                  "verify the spec is over-fit to the imperative shape "
                  "=> SPEC-TOO-STRONG."},
    {"id": "pos-commuted-guard", "kind": "soundness", "expect": "verify",
     "module": _POS_COMM,
     "rationale": "a second correct impl with the range guard's conjunction "
                  "COMMUTED (`statusCode < 600 ∧ 400 ≤ statusCode`) and the "
                  "non-error case written `if anchorFound = true then onSuccess "
                  "else …`. Semantically identical; the equality clause is "
                  "agnostic to guard order and to how the boolean is tested. Proof "
                  "re-closed by `by_cases` on the range membership then `cases "
                  "anchorFound`. Guards that the spec pins the classification, not "
                  "one syntactic guard order. If it fails => SPEC-TOO-STRONG."},

    # ---- admissibility (must VERIFY) ----
    {"id": "admiss-ground-f2p", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "the obligation is universally quantified with no precondition "
                  "hypothesis, so the analogue of PRECOND-TOO-STRONG here is the "
                  "obligation being UNSATISFIABLE at exactly an F2P-shaped input, "
                  "not a precondition to relax. This discharges the spec predicate "
                  "at that concrete point — a general-band error status with the "
                  "fragment ABSENT, the one input where the two candidate messages "
                  "disagree and the load-bearing clause E3 decides between them — "
                  "by evaluation as a `have`, then closes the frozen obligation "
                  "verbatim with the unchanged tactic body. The impl is the FROZEN "
                  "one; only the tactic body gains a leading ground instance "
                  "(statement byte-identical, no new declaration or assumption). "
                  "If the ground instance cannot be discharged the modeled "
                  "behaviour is unsatisfiable at a normal input "
                  "=> PRECOND-TOO-STRONG. Restores the nagini admissibility case, "
                  "which this port had dropped on the incorrect ground that the "
                  "class is vacuous whenever there is no precondition.",
     "refinement": "not a rival: a satisfiability control. It fixes every binder "
                   "to the F2P-shaped observation and shows the spec predicate "
                   "actually HOLDS there of the frozen impl by computation, so the "
                   "battery's rejections are refutations of wrong behaviour and not "
                   "artifacts of an obligation nothing can satisfy."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "prepatch-no-gate", "kind": "uniqueness", "expect": "reject",
     "module": _with_impl(_RIVAL_PREPATCH), "witness": _WIT_PREPATCH,
     "refinement": "this is the pre-patch behaviour — the reply's HTTP status is "
                   "never inspected on this branch, so an error response is passed "
                   "straight to the fragment search; a server error with the "
                   "fragment absent is reported with the fragment-level 'not found' "
                   "message instead of the HTTP-level message. The F2P asserts the "
                   "exact HTTP transport line, so this real patch does NOT resolve "
                   "(it is the very bug the fix closes).",
     "rationale": "attacks the (E)-before-(N) ordering and clause E3: on an error "
                  "status the status must govern and carry httpErrMsg, never "
                  "anchorErrMsg. Witness at statusCode=500, anchorFound=false: gold "
                  "=> ⟨\"broken\", httpErrMsg, 0⟩, rival => ⟨\"broken\", "
                  "anchorErrMsg, 0⟩. Built both ways (rival exit 0, gold exit 1). "
                  "If it verified => SPEC-TOO-WEAK on the load-bearing ordering."},
    {"id": "wrong-error-datum", "kind": "uniqueness", "expect": "reject",
     "module": _with_impl(_RIVAL_WRONGDATUM), "witness": _WIT_WRONGDATUM,
     "refinement": "the status IS consulted and 401/503 dispatched correctly, but "
                   "the general-error report carries the fragment-level message "
                   "instead of the HTTP-level message. The status label 'broken' "
                   "matches, but the F2P asserts the EXACT info string is the HTTP "
                   "transport error, so the printed line still reads the fragment "
                   "message and the F2P FAILS => does NOT resolve. Right label, "
                   "wrong datum — the subtle hole.",
     "rationale": "attacks clause E3 (a general error status must report "
                  "httpErrMsg). Witness at statusCode=502, anchorFound=true: gold "
                  "=> ⟨\"broken\", httpErrMsg, 0⟩, rival => ⟨\"broken\", "
                  "anchorErrMsg, 0⟩ — distinguishes httpErrMsg from anchorErrMsg. "
                  "Built both ways (rival 0, gold 1). If it verified => "
                  "SPEC-TOO-WEAK on the error datum."},
    {"id": "drop-401", "kind": "uniqueness", "expect": "reject",
     "module": _with_impl(_RIVAL_DROP401), "witness": _WIT_DROP401,
     "refinement": "dropping the 401 special-case sends 'unauthorized' into the "
                   "general-error branch -> broken/HTTP; a 401 link is reported "
                   "broken instead of working. This diverges from the "
                   "classification the unchanged status dispatch establishes for "
                   "401, so it does not preserve the tested behaviour.",
     "rationale": "attacks clause E1 (401 must be ⟨\"working\", \" - "
                  "unauthorized\", 0⟩). Witness at statusCode=401, anchorFound="
                  "false: gold => working/unauthorized, rival => broken/HTTP. "
                  "Varies statusCode onto the 401 special. Built both ways (rival "
                  "0, gold 1). If it verified => SPEC-TOO-WEAK on the 401 special."},
    {"id": "drop-503", "kind": "uniqueness", "expect": "reject",
     "module": _with_impl(_RIVAL_DROP503), "witness": _WIT_DROP503,
     "refinement": "dropping the 503 special-case sends 'service unavailable' into "
                   "the general-error branch -> broken; a 503 link is reported "
                   "broken instead of ignored. This changes the 503 classification "
                   "the unchanged dispatch establishes, so it does not preserve the "
                   "tested behaviour for that status.",
     "rationale": "attacks clause E2 (503 must be ⟨\"ignored\", httpErrMsg, 0⟩). "
                  "Witness at statusCode=503, anchorFound=true: gold => "
                  "ignored/HTTP, rival => broken/HTTP (wrong status label). Varies "
                  "statusCode onto the 503 special. Built both ways (rival 0, gold "
                  "1). If it verified => SPEC-TOO-WEAK on the 503 special."},
    {"id": "const-echo", "kind": "uniqueness", "expect": "reject",
     "module": _with_impl(_RIVAL_CONST), "witness": _WIT_CONST,
     "refinement": "unconditionally reporting ⟨\"broken\", httpErrMsg, 0⟩ is the "
                   "cheapest impl matching the F2P answer (a 500 -> broken/HTTP) "
                   "without doing any classification. But it marks EVERY link "
                   "broken — a 401 link and a working (2xx, fragment-present) link "
                   "are both reported broken, so the success / auth P2P cases FAIL "
                   "and it does NOT resolve.",
     "rationale": "the grounded total table has no ungrounded oracle to echo; the "
                  "cheapest 'echo the F2P answer' impl is this constant. Rejected "
                  "by clause E1 (401 must be working). Witness at statusCode=401, "
                  "anchorFound=true: gold => working/unauthorized, rival => "
                  "broken/HTTP. Built both ways (rival 0, gold 1). If it verified "
                  "=> SPEC-TOO-WEAK (a constant would satisfy the spec)."},
    {"id": "band-lower-edge", "kind": "uniqueness", "expect": "reject",
     "module": _with_impl(_RIVAL_BAND400), "witness": _WIT_BAND400,
     "refinement": "the error band's lower edge slipped from `≤` to `<`, so the "
                   "FIRST error status (400) is no longer treated as an error: it "
                   "falls through to the fragment search, exactly the pre-patch "
                   "routing, but for one status only. Every other status still "
                   "classifies correctly. A 400 reply whose fragment is absent is "
                   "then reported with the fragment-level message instead of the "
                   "HTTP-level one, and a 400 reply whose fragment is present is "
                   "reported as working — so the transport error is masked for the "
                   "whole 400 class and it does NOT resolve.",
     "rationale": "attacks the BAND THRESHOLD itself, which no other rival "
                  "probes: the existing rivals all vary WHICH branch fires inside "
                  "or outside a correctly-drawn band, leaving the boundary "
                  "`400 ≤ statusCode` untested, so a spec that pinned only "
                  "`401 < statusCode` would have passed the rest of this battery. "
                  "Witness at statusCode=400 (the exact edge), anchorFound=true so "
                  "the fall-through shows up as onSuccess: gold => ⟨\"broken\", "
                  "httpErrMsg, 0⟩, rival => onSuccess. Built both ways (rival exit "
                  "0, gold exit 1, gold failing by `decide` evaluating the "
                  "concrete claim to false — a semantic refutation). Added during "
                  "audit; if it verified => SPEC-TOO-WEAK on the band boundary."},
    {"id": "nonerror-absent-wrong-datum", "kind": "uniqueness", "expect": "reject",
     "module": _with_impl(_RIVAL_NONERR_DATUM), "witness": _WIT_NONERR_DATUM,
     "refinement": "on a non-error status whose fragment is absent, the report "
                   "carries the HTTP-level message instead of the fragment-level "
                   "one. The status label 'broken' is right and the error path is "
                   "untouched, but a page that answered fine and merely lacks the "
                   "requested fragment is now reported with a transport message "
                   "that describes nothing that happened — on a successful reply "
                   "that message is empty or stale, so the fragment-absent "
                   "diagnostic the P2P cases read is destroyed and it does NOT "
                   "resolve.",
     "rationale": "attacks clause N1's DATUM, which no other rival reaches: "
                  "wrong-error-datum discriminates the two messages on the ERROR "
                  "side (E3) and nonerror-present-broken attacks the non-error "
                  "side's CONTROL (N2), so N1's message routing was unprobed and a "
                  "spec leaving it free would have satisfied the whole battery. "
                  "Witness at statusCode=200, anchorFound=false: gold => "
                  "⟨\"broken\", anchorErrMsg, 0⟩, rival => ⟨\"broken\", httpErrMsg, "
                  "0⟩. Added during audit; built both ways (rival exit 0, gold exit "
                  "1 by `decide` evaluating the concrete claim to false). If it "
                  "verified => SPEC-TOO-WEAK on the non-error message routing."},
    {"id": "code-field", "kind": "uniqueness", "expect": "reject",
     "module": _with_impl(_RIVAL_CODE), "witness": _WIT_CODE,
     "refinement": "the numeric third component of the reported triple is 1 "
                   "instead of 0 on the general-error branch. Both other "
                   "components are routed correctly, so the human-readable line is "
                   "unchanged; what changes is the machine-readable code that "
                   "accompanies it, which the structured (JSON) output surfaces "
                   "directly — so a consumer reading the code sees a different "
                   "outcome class than the label states and it does NOT resolve.",
     "rationale": "isolates the ONE output component no other rival varies: every "
                  "existing witness differs from gold in the status label or the "
                  "message, so the `code` field could have been left unpinned "
                  "without any of them noticing. Witness at statusCode=500, "
                  "anchorFound=false, where gold and rival agree on BOTH the label "
                  "and the message and differ only in the code: gold => code 0, "
                  "rival => code 1. Added during audit; built both ways (rival exit "
                  "0, gold exit 1 by `decide` evaluating the concrete claim to "
                  "false). If it verified => SPEC-TOO-WEAK on the numeric code, "
                  "i.e. the spec would not pin every output component."},
    {"id": "nonerror-present-broken", "kind": "uniqueness", "expect": "reject",
     "module": _with_impl(_RIVAL_NONERR), "witness": _WIT_NONERR,
     "refinement": "on a non-error status this always reports the fragment-absent "
                   "broken result regardless of whether the fragment is present, so "
                   "a working link whose fragment IS present is reported broken "
                   "instead of deferring to the success continuation. The success "
                   "P2P cases expect a present fragment on a 2xx page to be "
                   "working, so this real patch FAILS them and does NOT resolve.",
     "rationale": "supporting partial-domain on the UNCHANGED half of the table "
                  "(guards the spec pins more than the error path). Rejected by "
                  "clause N2 (non-error + fragment present must defer to "
                  "onSuccess). The ONLY witness that makes the result depend on the "
                  "`onSuccess` binder: statusCode=200, anchorFound=true, "
                  "onSuccess=⟨\"redirected\",\"R\",7⟩ — gold => onSuccess, rival => "
                  "⟨\"broken\", anchorErrMsg, 0⟩. Built both ways (rival 0, gold "
                  "1). If it verified => SPEC-TOO-WEAK on the non-error success "
                  "sub-domain."},
]
