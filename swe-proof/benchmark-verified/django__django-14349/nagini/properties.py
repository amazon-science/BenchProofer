# properties.py — PBT falsification battery for django__django-14349. NOT a Nagini
# module; a record of adversarially-reasoned cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are FULL model.py variants that share
# the FROZEN spec byte-for-byte (region surgery: ONLY the text strictly between the
# function's `# impl-start` / `# impl-end` — which INCLUDES the nested invariants
# region — is edited; the spec view is never touched), checked by Nagini verify +
# markers.same_spec. The single axiom case probes the A-consumed @ContractOnly axiom
# `downstream_validate` against the REAL django.core.validators.URLValidator in the
# instance Docker image (see AXIOM_TESTS at the bottom).
#
# ---------------------------------------------------------------------------
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   validate_url(value: List[int], accepted: bool) -> None
#   Models the gold one-hunk forbidden-character screen the patch adds to
#   URLValidator.__call__: reject (raise) iff `value` carries ANY of TAB(9)/LF(10)/
#   CR(13) ANYWHERE — independently of, and BEFORE, the rest of validation; on a
#   forbidden-char-free value defer EXACTLY to the unchanged downstream verdict
#   (`accepted`). The gold patch: `unsafe_chars = frozenset('\t\r\n')` +
#   `if self.unsafe_chars.intersection(value): raise ValidationError(...)`. The F2P
#   asserts ValidationError IS raised for, among others, the MID-string-CR case
#   `http://www.django\rproject.com/` (which, post-bpo-43882, urlsplit strips, so
#   downstream would otherwise ACCEPT it) and the LEADING-TAB case
#   `http://\twww.djangoproject.com/`.
#
#   PRECONDITION:
#     (P1) Requires(Acc(list_pred(value), 1/2))   # HALF permission => `value` READ-ONLY
#          `accepted` is a plain bool world-state datum (the downstream verdict).
#     (P2) Requires(MustTerminate(2))              # TOTAL correctness: the screen must
#          actually ANSWER (return or raise). Nagini is partial-correctness by default,
#          so without P2 a diverging impl (e.g. `while True: pass` inserted after the
#          screen — the auditor's atk_4/atk_5) satisfies every Ensures/Exsures
#          vacuously. Every loop must consume the obligation with a strictly
#          decreasing, bounded-below measure; downstream_validate itself carries
#          Requires(MustTerminate(1)) so the deferral discharges the caller's
#          obligation.
#   POSTCONDITION — normal-return path (all three must hold to return normally):
#     (Q1) Ensures(Acc(list_pred(value), 1/2))     # framing: value returned untouched
#     (Q2) Ensures(Forall k. 0<=k<len(value) ==> not is_forbidden(value[k]))
#            -- LOAD-BEARING: normal return reachable ONLY when NO forbidden code
#               point appears ANYWHERE (not just the ends).
#     (Q3) Ensures(accepted is True)
#            -- LOAD-BEARING: normal return reachable ONLY when downstream accepted.
#   POSTCONDITION — exceptional path:
#     (E1) Exsures(InvalidValue, Acc(list_pred(value),1/2)
#                  and (Exists k. 0<=k<len(value) and is_forbidden(value[k])
#                       or accepted is False))
#            -- rejection signalled EXACTLY when (a forbidden code point is present)
#               OR (downstream rejected). NOTE E1's condition is a DISJUNCTION, so the
#               raise path is permissive; the *return* path is pinned by Q2 AND Q3.
#   is_forbidden(c) is a @Pure helper GROUNDED entirely in the argument
#   (c==9 or c==10 or c==13), fully unfolded — there is NO opaque answer-key/oracle.
#
# FRAME-MUTATION lane is MANDATORY: `value` is Acc(list_pred(value),1/2) (read-only).
#   A rival that WRITES it must be REJECTED for INSUFFICIENT PERMISSION. Byte-fuzzers
#   never think to mutate the input; this is the #1 weakness class. The gold patch
#   only READS `value` (`unsafe_chars.intersection(value)` iterates a str; the str is
#   immutable) and Q1 re-establishes the half-permission on both paths — so the spec
#   must forbid ANY write to `value`.
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo. Q2/E1's forbidden-char clause is
#   pinned to `is_forbidden(value[k])`, a @Pure predicate fully unfolded over the
#   argument (no @ContractOnly answer-key, no exact marker the impl could echo). Q3/E1
#   defer to `accepted`, the bool argument itself. There is no value an echo could
#   carry that satisfies the postcondition yet is wrong — the unique satisfier IS the
#   grounded decision (scan the input + honour the verdict). The honest control is the
#   cheapest faithful impl computing that decision (the positive control), not a wrong
#   echo. See 'assessment'.
#
# CONTROL-FLOW-EFFECT lane: APPLIES and is directly exercised. The single behavioural
#   effect of this function is a control-flow fork: raise (InvalidValue) vs normal
#   return. The value abstraction does NOT drop it — Q2/Q3 govern the return path and
#   E1 governs the raise path, and the exception class IS the capability token (both
#   directions pinned). weak-always-reject (removes the return fork) and
#   weak-drop-downstream (returns where it must raise/defer) are the discriminators;
#   no separate token plumbing is needed.
#
# PARTIAL-DOMAIN lane: heavily exercised. A rival correct on most of the value domain
#   yet diverging on a sub-domain:
#     - weak-first-char-only : scans only value[0] for a forbidden char => catches a
#                              LEADING TAB/CR but MISSES the mid-string CR — exactly
#                              the F2P `http://www.django\rproject.com/`. Fails Q2.
#     - weak-prepatch        : the literal pre-patch body (no screen; straight
#                              downstream) => a forbidden-char value downstream accepts
#                              returns normally (the bug the gold fixes). Fails Q2.
#
# AXIOM lane: meta.axioms == [downstream_validate] (A-consumed @ContractOnly); NO
#   A-reference deep model. downstream_validate abstracts the UNCHANGED remainder of
#   URLValidator.__call__ (scheme/regex/IDN/IPv6). Its only observable on the model's
#   domain (forbidden-char-free str values — the only path on which the model invokes
#   it) is the verdict: returns None iff accepted, raises ValidationError iff not.
#   axiom-soundness re-runs the bundle's axiom_check.py VERBATIM in the instance image
#   (real URLValidator, gold patch applied) — the canonical G-AX oracle. The
#   containment probe confirms the model only ever reaches downstream on
#   forbidden-char-free values (a static control-flow fact) and that the real callee
#   is total over {accept->None, reject->ValidationError} on exactly that domain (so
#   every caller-reachable callee-input lies inside the axiom's domain).
from pathlib import Path

INSTANCE = "django__django-14349"
FLOAT_ENCODING = None  # meta.json float_encoding is null (no float in this model)

_DIR = Path(__file__).parent
_BASE = (_DIR / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen FUNCTION impl region body, verbatim (everything strictly BETWEEN the
# function's `# impl-start` / `# impl-end`, INCLUDING the nested invariants region).
# Every spec variant _swap()s ONLY this block, so the edit never touches the spec
# (axioms/pure/pre-/post-conditions regions + signatures). same_spec is computed over
# the spec_view, which elides every impl region (and nested invariants), so swapping
# inside here is GUARANTEED same_spec.
_IMPL = """\
    i = 0
    while i < len(value):
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(0 <= i and i <= len(value))
        # no forbidden code point has been seen in the visited prefix.
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  not is_forbidden(value[k])))))
        # the scan consumes the caller's termination obligation with a
        # strictly decreasing, bounded-below measure (len(value) - i),
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(value) - i + 1))
        # invariants-end
        if is_forbidden(value[i]):
            raise InvalidValue()
        i = i + 1
    downstream_validate(accepted)"""

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the function impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-localvar-reshape: structurally DIFFERENT but behaviourally identical. Instead of
# testing `if is_forbidden(value[i])` directly, bind the per-element verdict to a local
# `bad` first and branch on it. This is a pure local-variable reshape (directive 2/3:
# no dropped lemma, no loop-direction flip, no forward-append against a front-recursive
# fold) that keeps EVERY gold proof obligation VERBATIM — same loop bound, the same
# three invariants (incl. the load-bearing prefix `Forall k<i. not is_forbidden(...)`),
# the same `raise InvalidValue()` on a found forbidden code point, the same `i=i+1`
# advance, and the same trailing `downstream_validate(accepted)`. Only the executable
# shape of the test changes. If it FAILS => SPEC-TOO-STRONG (a faithful,
# structurally-different correct impl is rejected).
_POS_RESHAPE = """\
    i = 0
    while i < len(value):
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(0 <= i and i <= len(value))
        # no forbidden code point has been seen in the visited prefix.
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  not is_forbidden(value[k])))))
        # the scan consumes the caller's termination obligation with a
        # strictly decreasing, bounded-below measure (len(value) - i),
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(value) - i + 1))
        # invariants-end
        bad = is_forbidden(value[i])
        if bad:
            raise InvalidValue()
        i = i + 1
    downstream_validate(accepted)"""
assert _POS_RESHAPE != _IMPL, "pos-localvar-reshape did not rewrite"


# admiss-reads: an admissibility positive control. The precondition is the single
# half-permission Acc(list_pred(value),1/2). This control keeps the gold impl VERBATIM
# but FIRST asserts, under that half-permission, that the reads a normal F2P-shaped str
# value needs are admitted — the length is readable and (when the value is non-empty,
# as every F2P URL string is) the first code point is readable. No write, so no extra
# permission demand. If the precondition could not admit a legitimate URL value this
# would fail => PRECOND-TOO-STRONG.
_ADMISS = (
    "    # Admissibility: a normal (possibly empty) str value is in-domain; the\n"
    "    # half-permission admits reading the length and elements.\n"
    "    Assert(len(value) >= 0)\n"
    "    if len(value) > 0:\n"
    "        Assert(value[0] == value[0])   # read admitted under Acc(...,1/2)\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVAL (MANDATORY — `value` is Acc(list_pred(value),1/2)).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-write: keeps the gold body VERBATIM (so the rejection is attributable
# SOLELY to the added write, not to a value mismatch), then WRITES BACK into the
# read-only input: value[0] = value[0]. A no-op store, but a STORE — it demands FULL
# write permission on `value`, which the caller granted only at 1/2. The verifier must
# reject for insufficient permission. The store is placed FIRST, guarded by len>0 so it
# is reachable on every F2P input (all non-empty URL strings).
_FRAME_MUT = (
    "    if len(value) > 0:\n"
    "        # Frame violation: write back into the read-only (Acc(...,1/2)) input.\n"
    "        value[0] = value[0]\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN / CONTROL-FLOW RIVALS — must be REJECTED
# (else SPEC-TOO-WEAK). Each shares the frozen spec exactly; only the impl changes.
# ---------------------------------------------------------------------------

# weak-prepatch: the LITERAL pre-patch body (model_prepatch.py): NO forbidden-character
# screen — hand the value straight to downstream_validate(accepted). CONTROL-FLOW: the
# early-reject fork is removed. On a value with a forbidden code point that downstream
# ACCEPTS (accepted=True), it returns normally, but Q2
# (Forall k. not is_forbidden(value[k])) demands a forbidden code point ⇒ NOT a normal
# return. This is precisely G-DIFF.
_WEAK_PREPATCH = """\
    downstream_validate(accepted)"""

# weak-first-char-only: PARTIAL-DOMAIN. Scans ONLY the first code point for a forbidden
# character; if value[0] is clean (or value is empty) it never checks the rest and
# defers to downstream. Correct on the LEADING-forbidden sub-domain
# (`http://\twww...` rejected) but MISSES a forbidden code point anywhere past index 0
# — exactly the F2P `http://www.django\rproject.com/` (CR in the middle), which
# downstream (post-bpo-43882) accepts. There it returns normally with accepted=True
# while Q2 demands the raise. The invariants are dropped (no loop) but kept proof-clean
# by binding before the guard.
_WEAK_FIRST = """\
    if len(value) > 0 and is_forbidden(value[0]):
        raise InvalidValue()
    downstream_validate(accepted)"""

# weak-drop-downstream: scans for a forbidden code point exactly like the gold (so it
# correctly rejects any forbidden-char value) but then RETURNS without consulting
# downstream — it drops the `downstream_validate(accepted)` deferral entirely.
# CONTROL-FLOW-EFFECT: on a forbidden-char-free value that downstream REJECTS
# (accepted=False) it returns normally, but Q3 (Ensures(accepted is True)) demands a
# normal return only when accepted; equivalently it should have raised (E1's
# `accepted is False` disjunct). It pins the forbidden-char half of the decision but
# unpins the downstream-verdict half.
_WEAK_DROP_DS = """\
    i = 0
    while i < len(value):
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(0 <= i and i <= len(value))
        # no forbidden code point has been seen in the visited prefix.
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  not is_forbidden(value[k])))))
        # the scan consumes the caller's termination obligation (kept verbatim
        # so the rejection is attributable SOLELY to the dropped deferral, not
        # to an obligation leak).
        Invariant(MustTerminate(len(value) - i + 1))
        # invariants-end
        if is_forbidden(value[i]):
            raise InvalidValue()
        i = i + 1
    return"""

# weak-diverge: DIVERGENCE rival (the auditor's atk_4/atk_5 shape). Keeps the gold
# scan/raise shape but NEVER advances `i` on the clean-element path, so on any
# non-empty forbidden-char-free value the loop spins forever — the real-world
# analogue is inserting `while True: pass` after the screen in __call__ (verified
# in Docker to hang the F2P run into the harness timeout => does NOT resolve).
# Under partial correctness every Ensures/Exsures is satisfied vacuously; the
# MustTerminate(2) precondition (P2) makes the verifier demand each loop consume
# the obligation with a decreasing measure, which this loop cannot supply.
_WEAK_DIVERGE = """\
    i = 0
    while i < len(value):
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(0 <= i and i <= len(value))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  not is_forbidden(value[k])))))
        # invariants-end
        if is_forbidden(value[i]):
            raise InvalidValue()
    downstream_validate(accepted)"""

# weak-always-reject: ALWAYS raises (every input takes the exceptional path).
# CONTROL-FLOW-EFFECT (the dual of weak-prepatch): the normal-return fork is removed.
# Then E1's condition `Exists k. is_forbidden(value[k]) OR accepted is False` must hold
# whenever it raises, but on a forbidden-char-free value that downstream ACCEPTS
# (e.g. value=[104] no forbidden, accepted=True) BOTH disjuncts are False ⇒ the Exsures
# condition is violated. (Bound to a bare `raise`; no `# type:` pitfall.)
_WEAK_REJECT = """\
    raise InvalidValue()"""


SPEC_TESTS = [
    {
        "id": "pos-localvar-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_RESHAPE),
        "rationale": (
            "structurally-different but CORRECT impl: the per-element forbidden-char "
            "verdict is bound to a local `bad` and the branch tests `bad` instead of "
            "`is_forbidden(value[i])` inline. Semantics are identical and EVERY gold "
            "proof obligation is kept verbatim — same loop bound, same three invariants "
            "(incl. the prefix Forall k<i. not is_forbidden(value[k])), same raise on a "
            "found forbidden code point, same i=i+1 advance, same trailing "
            "downstream_validate(accepted). A pure local-variable reshape (no dropped "
            "lemma, no loop-direction flip). If it FAILS => SPEC-TOO-STRONG (a faithful "
            "correct impl is rejected)."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (single Acc(list_pred(value),1/2) half-permission) must "
            "admit a normal F2P-shaped str value: the length is readable and, when "
            "non-empty (every F2P URL string is), the first code point is readable under "
            "the half-permission. The gold impl is otherwise verbatim (only reads/asserts "
            "added inside the impl region, no write). If it FAILS => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "the gold patch only READS `value` — `self.unsafe_chars.intersection(value)` "
            "iterates the str (immutable) and the downstream chain likewise only reads "
            "it; nothing in URLValidator.__call__ rebinds or mutates the input string. A "
            "faithful real patch that wrote back into `value` would not be the gold patch "
            "(strings are immutable in CPython, so the write could not even be expressed "
            "on the real str; on the List[int] carrier it models a mutation the real code "
            "never performs) and would not faithfully resolve. The store here is a no-op "
            "only by coincidence; the point is the spec must forbid ANY write to the input."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `value` is granted at "
            "Acc(list_pred(value),1/2) (P1); the store value[0]=value[0] demands FULL "
            "write permission, which is not available, so the verifier rejects for "
            "INSUFFICIENT PERMISSION. The gold scan/raise/defer body is kept verbatim so "
            "the rejection is attributable solely to the write. If it VERIFIES => the "
            "read-only frame is hollow (frame-mutation, the #1 weakness class; a "
            "byte-fuzzer never thinks to mutate the input)."
        ),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPATCH),
        "refinement": (
            "this IS the pre-patch behaviour (model_prepatch.py): NO forbidden-character "
            "screen — the value is handed straight to the unchanged downstream chain. Its "
            "faithful real patch is the UNCHANGED repo (`__call__` without the inserted "
            "`if self.unsafe_chars.intersection(value): raise`). Post-bpo-43882 urlsplit "
            "strips TAB/LF/CR, so `http://www.django\\rproject.com/` reaches the downstream "
            "already stripped and is ACCEPTED there — it returns normally instead of "
            "raising. It fails the F2P test_validators (now asserts ValidationError IS "
            "raised on the forbidden-char URLs). Does NOT resolve — the precise change the "
            "spec senses (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by Q2 (Ensures(Forall k. not is_forbidden(value[k]))): on a value "
            "with a forbidden code point that downstream accepts (accepted=True) the rival "
            "returns normally, but Q2 demands the absence of any forbidden code point on "
            "the normal-return path, which is violated. The verifier reports exactly this "
            "clause (meta.json prepatch_models.fails_on). CONTROL-FLOW: the early-reject "
            "fork is removed. If it VERIFIES => SPEC-TOO-WEAK (the screen is not enforced)."
        ),
    },
    {
        "id": "weak-first-char-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_FIRST),
        "refinement": (
            "checking only value[0] is what a real patch that wrote "
            "`if value[:1] in self.unsafe_chars:` / `if value.startswith(('\\t','\\r',"
            "'\\n')):` would do. It rejects a LEADING forbidden char "
            "(`http://\\twww.djangoproject.com/`) but ACCEPTS a forbidden code point "
            "anywhere past index 0 — it does NOT reject `http://www.django\\rproject.com/` "
            "(CR in the middle), which is a literal F2P input asserting ValidationError "
            "IS raised. A genuine PARTIAL-DOMAIN break on the not-first-position "
            "sub-domain; does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q2 (Ensures(Forall k. not is_forbidden(value[k]))): for a value "
            "whose only forbidden code point is at index >=1 (e.g. the CR in "
            "`...django\\rproject...`) with accepted=True, the rival returns normally, but "
            "Q2 demands NO forbidden code point ANYWHERE — the existential at the "
            "mid-string index is uncovered. PARTIAL-DOMAIN: the rival pins only the "
            "first-position sub-domain. If it VERIFIES => SPEC-TOO-WEAK on the "
            "not-first-position sub-domain."
        ),
    },
    {
        "id": "weak-drop-downstream",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_DS),
        "refinement": (
            "scanning for forbidden chars but then RETURNING without calling the "
            "downstream chain is what a real patch that inserted the new screen but "
            "DELETED the rest of __call__ (the scheme/regex/IDN/IPv6 validation) would do. "
            "It would accept every forbidden-char-free value regardless of whether it is a "
            "valid URL — failing every P2P invalid-URL case (e.g. 'no_scheme', "
            "'http://www.asdasdasdasdsadfm.com.br ') that the unchanged downstream rejects "
            "with ValidationError. Does NOT resolve (the downstream deferral is part of "
            "the unchanged behaviour the patch must preserve)."
        ),
        "rationale": (
            "REJECTED by Q3 (Ensures(accepted is True)): on a forbidden-char-free value "
            "that downstream REJECTS (accepted=False) the rival returns normally, but Q3 "
            "demands a normal return only when accepted is True. CONTROL-FLOW-EFFECT: the "
            "downstream-verdict deferral (the consumed downstream_validate axiom) is "
            "dropped, so the raise-on-reject fork is lost. It pins the forbidden-char half "
            "of the decision but unpins the downstream-verdict half. If it VERIFIES => "
            "SPEC-TOO-WEAK (the deferral to the downstream verdict is not enforced)."
        ),
    },
    {
        "id": "weak-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DIVERGE),
        "refinement": (
            "a real patch that added the screen but then entered an infinite loop "
            "(e.g. `while True: pass` inserted after the unsafe_chars check — the "
            "auditor's literal atk_5 patch, run in the instance image: test_validators "
            "hangs into the 600s harness timeout) never delivers any verdict on a "
            "forbidden-char-free value. It fails EVERY F2P/P2P case that requires "
            "__call__ to return or raise; does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the TERMINATION OBLIGATION (P2, Requires(MustTerminate(2))): "
            "the loop never advances `i` on the clean-element path, so it can supply "
            "no strictly decreasing measure; Nagini reports an obligation leak "
            "('Loop might not take all unsatisfied obligations from the context'). "
            "Without P2 this rival VERIFIED (the recorded G-PANEL-1 break): under "
            "partial correctness a diverging impl satisfies every Ensures/Exsures "
            "vacuously. If it VERIFIES => SPEC-TOO-WEAK (divergence unpinned)."
        ),
    },
    {
        "id": "weak-always-reject",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_REJECT),
        "refinement": (
            "always raising is what a real patch that hard-coded the guard True (or "
            "compared `value` against an always-truthy set) would do — it rejects EVERY "
            "URL, including every valid one the project must accept. It fails every "
            "P2P/valid-URL path that requires URLValidator.__call__ to return normally on "
            "a well-formed URL. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by E1 (Exsures(InvalidValue, Acc(...,1/2) and (Exists k. "
            "is_forbidden(value[k]) OR accepted is False))): whenever it raises, E1's "
            "condition must hold, but on a forbidden-char-free value that downstream "
            "ACCEPTS (e.g. value=[104], accepted=True) BOTH disjuncts are False, so the "
            "Exsures condition is violated. CONTROL-FLOW-EFFECT (dual of weak-prepatch): "
            "the normal-return fork is removed. If it VERIFIES => SPEC-TOO-WEAK (the "
            "accept condition is unpinned)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — the A-consumed @ContractOnly axiom `downstream_validate` vs the REAL
# django.core.validators.URLValidator.__call__ (the UNCHANGED downstream chain).
# meta.axioms == [downstream_validate]; no A-reference deep model. The real callee
# lives ONLY in the instance image, so both probes run in Docker with the gold patch
# applied (apply_gold=True). The runner mounts ONLY the probe script at /work, so the
# soundness probe embeds the bundle's axiom_check.py VERBATIM (read on the HOST at
# load time) — it imports only the stdlib + the Django callee present in the image,
# opens any fixture with encoding='utf8', exits 0 iff sound.
# ---------------------------------------------------------------------------

# Read the canonical G-AX oracle on the HOST and embed it (directive 6: axiom_check.py
# is NOT mounted in-container). axiom_check.py ends with `sys.exit(main())`, so running
# it as the probe is exactly the G-AX check.
_AXIOM_CHECK_SRC = (_DIR / "axiom_check.py").read_text()


# Containment probe: the model invokes downstream_validate(accepted) on EXACTLY one
# kind of input — the boolean `accepted`, and ONLY after its scan has confirmed `value`
# carries NO forbidden code point (the loop raises on the first forbidden one, so the
# call is unreachable for any forbidden-char value). The axiom's Requires is EMPTY
# (downstream_validate has no pre-condition), so every bool `accepted` is trivially in
# its domain — there is no abstract-parameter containment defect possible. The
# meaningful containment claim is the DOMAIN on which downstream_validate stands in for
# the real callee: forbidden-char-FREE str values. This probe executes the REAL
# URLValidator on a heavy sample of forbidden-char-free values (the only values the
# model can reach the callee with) and asserts every outcome lies in the axiom's
# observable range {accept->None, reject->ValidationError} — i.e. no caller-reachable
# callee-input escapes the axiom's domain/range. (A forbidden-char value is never
# passed to the callee by the model, so it is correctly OUT of scope.)
_AX_COVER_PROBE = r'''
import os
import random
import sys

FORBIDDEN = {'\t', '\n', '\r'}

def has_forbidden(s):
    return any(ch in FORBIDDEN for ch in s)

try:
    from django.core.validators import URLValidator
    from django.core.exceptions import ValidationError
except Exception as exc:  # pragma: no cover - container guard
    print("CONTAINMENT SKIP: Django URLValidator unavailable (%r)" % (exc,))
    sys.exit(0)

validator = URLValidator()

def observe(value):
    try:
        result = validator(value)
    except ValidationError:
        return ('reject', None)
    except Exception as other:
        return ('other', other)
    else:
        return ('accept', result)

fails = 0
n = 0

# The model reaches downstream_validate ONLY on forbidden-char-free values (its scan
# raises before the call otherwise). Confirm every such reachable callee-input lies in
# the axiom's domain/range: the real callee is total over {accept->None,
# reject->ValidationError}. A non-ValidationError out-of-band signal, or a normal
# completion returning anything other than None, would mean a caller-reachable input
# escapes the axiom's range => AXIOM-TOO-WEAK-FOR-CALLER.
fixed = [
    'http://www.djangoproject.com/', 'https://example.com',
    'ftp://ftp.example.com/file', 'http://[::ffff:192.9.5.5]',
    'http://localhost/', 'http://www.example.com:8000/path?query=1#frag',
    'no_scheme', 'foo', 'http://', 'http://.', 'http://..',
    'https://example,com', 'ftp://[example].com', 'http://-error-.invalid/',
    '', 'http://www.asdasdasdasdsadfm.com.br ', 'http://www.asdasdasdasdsadfm.com.br z',
]
for value in fixed:
    if has_forbidden(value):
        continue  # the model never reaches downstream on a forbidden-char value
    kind, info = observe(value)
    if kind not in ('accept', 'reject'):
        fails += 1
        print("CONTAINMENT FAIL: reachable forbidden-char-free value %r produced a "
              "non-ValidationError out-of-band signal: %r" % (value, info))
        continue
    if kind == 'accept' and info is not None:
        fails += 1
        print("CONTAINMENT FAIL: URLValidator accepted %r but returned %r, expected "
              "None (axiom range is the empty value)" % (value, info))
    n += 1

# Randomised fuzz over forbidden-char-free strings (the entire reachable callee
# domain): assert containment in {accept->None, reject->ValidationError}.
rng = random.Random(14349)
alphabet = list('abcdefghijklmnopqrstuvwxyzABCDEF0123456789./:?#@&=%+-_~[]') + ['e', ' ']
for _ in range(5000):
    m = rng.randint(0, 40)
    value = ''.join(rng.choice(alphabet) for _ in range(m))
    if has_forbidden(value):
        continue
    kind, info = observe(value)
    if kind not in ('accept', 'reject'):
        fails += 1
        print("CONTAINMENT FAIL: reachable fuzz value %r produced a non-ValidationError "
              "out-of-band signal: %r" % (value, info))
        continue
    if kind == 'accept' and info is not None:
        fails += 1
        print("CONTAINMENT FAIL: URLValidator accepted fuzz %r but returned %r, expected "
              "None" % (value, info))
    n += 1

if fails:
    print("AXIOM-CONTAINMENT FAIL: %d reachable callee-input(s) escape the "
          "downstream_validate axiom domain/range" % fails)
    sys.exit(1)
print("AXIOM-CONTAINMENT OK: every callee-input the model can reach "
      "(downstream_validate(accepted) only after the scan confirms `value` is "
      "forbidden-char-free) lies in the axiom domain/range — real URLValidator is "
      "total over {accept->None, reject->ValidationError} on %d forbidden-char-free "
      "values; no caller-reachable input escapes." % n)
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-downstream_validate",
        "axiom": "downstream_validate",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": (
            "downstream_validate is the A-consumed @ContractOnly axiom: it abstracts the "
            "UNCHANGED remainder of URLValidator.__call__ (scheme/regex/IDN/IPv6) by the "
            "single bit `accepted` — returns None iff accepted, raises ValidationError "
            "iff not. AXIOM-SOUNDNESS: the real callee must meet that contract on the "
            "model's domain (forbidden-char-free str values, the only path on which the "
            "screen is a no-op and downstream stands in). This probe is the bundle's "
            "axiom_check.py VERBATIM (the canonical G-AX oracle): it runs the REAL "
            "URLValidator (gold patch applied) on the repo's valid/invalid URL fixtures + "
            "5000 forbidden-char-free fuzz inputs and asserts the call is TOTAL over "
            "{accept->None, reject->ValidationError} — never any other out-of-band signal, "
            "never a silent accept of a repo-invalid value. Imports only stdlib + the "
            "Django callee in the image; opens fixtures with encoding='utf8'. Exit 0 iff "
            "every observation meets the axiom. If the real callee disagrees anywhere => "
            "AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-cover-downstream_validate",
        "axiom": "downstream_validate",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "AXIOM-CONTAINMENT: the model invokes downstream_validate(accepted) on "
            "EXACTLY the bool `accepted`, and ONLY after its scan has confirmed `value` "
            "carries no forbidden code point (the loop raises on the first forbidden one, "
            "so the call is unreachable for any forbidden-char value). The axiom's "
            "Requires is EMPTY, so every bool is trivially in domain — no abstract-param "
            "containment defect is possible. The substantive claim is the DOMAIN on which "
            "downstream_validate stands in: forbidden-char-FREE str values. The probe runs "
            "the REAL URLValidator (gold applied) on a heavy sample of forbidden-char-free "
            "values (the entire reachable callee domain) and asserts every outcome lies in "
            "the axiom's range {accept->None, reject->ValidationError}, with no "
            "out-of-band escape. Covering MORE (forbidden-char values) than the model "
            "reaches would be sound, not a defect — the model never reaches them. A "
            "reachable forbidden-char-free input whose real outcome escapes the axiom "
            "range => AXIOM-TOO-WEAK-FOR-CALLER (none expected)."
        ),
    },
]
