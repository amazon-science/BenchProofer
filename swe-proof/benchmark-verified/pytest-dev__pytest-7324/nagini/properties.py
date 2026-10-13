"""properties.py — PBT falsification manifest for pytest-dev__pytest-7324.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. There are TWO modeled functions (a genuine two-site change):

    encode_ident(ident: List[int]) -> List[int]      # site 1: prepend prefix
    lookup_key(key:   List[int]) -> bool             # site 2: strip prefix, lookup

with the load-bearing contracts

  encode_ident:
    Requires(Acc(list_pred(ident), 1/2))                       # READ-ONLY input
    Requires(MustTerminate(2))                                 # must deliver
    Ensures (Acc(list_pred(ident), 1/2))
    Ensures (Acc(list_pred(Result())))
    Ensures (ToSeq(Result()) == PSeq(sentinel()) + ToSeq(ident))   # the WHOLE pin
    Ensures (len(Result()) >= 1 and ToSeq(Result())[0] == sentinel())
    Ensures (ToSeq(Result())[0] != 84 / 70 / 78)              # not True/False/None
    Ensures (strip_sentinel(ToSeq(Result())) == ToSeq(ident)) # round trip

  lookup_key:
    Requires(Acc(list_pred(key), 1/2))                        # READ-ONLY input
    Requires(len(ToSeq(key)) >= 1 and ToSeq(key)[0] == sentinel())
    Requires(MustTerminate(2))                                # must deliver
    Ensures (Acc(list_pred(key), 1/2))
    Ensures (len(ToSeq(key)) >= 1 and ToSeq(key)[0] == sentinel())
    Ensures (Result() == match(strip_sentinel(ToSeq(key))))   # the WHOLE pin

What the spec actually defends, and the attacks it must survive:

  * `sentinel()` is a @Pure helper returning the constant 36, and
    `strip_sentinel(name) == name.drop(1)` is a @Pure helper fully unfolded by
    Viper. Both are GROUNDED — not opaque answer-key oracles. So there is no
    "echo the oracle" shortcut for site 1: the only way to satisfy
    `ToSeq(Result()) == PSeq(36) + ToSeq(ident)` is to actually build
    `[36] ++ ident` element by element (the real prepend work). The honest
    cheapest-impl positive control `pos-encode-assert` confirms this.

  * For site 2 the postcondition pins `Result() == match(strip_sentinel(key))`
    where `match` is a @ContractOnly (uninterpreted) predicate. Crucially the
    ARGUMENT is grounded: the verifier knows nothing about match's value, so it
    can only discharge the pin if the impl forwards EXACTLY `strip_sentinel(key)`
    (= key.drop(1)). An impl that echoes `match` on the WRONG argument (e.g. the
    raw prefixed key) cannot prove `match(raw) == match(stripped)` for an
    uninterpreted match — so it is REJECTED. That is the `lookup-no-strip` rival
    (= model_prepatch_2.py). There is therefore no wrong-argument echo that
    verifies; the only echo positive control is the honest one.

  * BOTH functions carry a MustTerminate obligation: the value pins alone are
    only partial-correctness facts, so an implementation that never returns
    (infinite loop, unbounded self-recursion) would otherwise discharge them
    vacuously. The termination obligation makes such implementations fail the
    obligation-leak check — the `encode-loop-forever` / `lookup-loop-forever`
    rivals below pin this defense.

  * BOTH inputs are read-only (Acc(..., 1/2)). The MANDATORY attack on each is
    FRAME MUTATION (`encode-frame-mutate`, `lookup-frame-mutate`): an impl that
    WRITES to its input to satisfy the pin vacuously must fail for INSUFFICIENT
    PERMISSION (a store needs full permission). The gold invariants are kept
    verbatim around the write so the rejection is attributable to the write
    alone, not to a value mismatch.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `# impl-start`/`# impl-end` (the nested invariants live
there too), so `markers.same_spec` is GUARANTEED and a rejection comes from the
POSTCONDITION catching wrong behaviour (or the permission system), never from a
tampered spec. Each `expect:"reject"` rival carries the refinement argument that
its faithful real patch would NOT resolve the F2P (test_valid_idents[True/False/
None]). There are NO @ContractOnly axioms with a value Ensures and NO A-reference
deep models that need a runtime probe here: `match` carries only determinism
(no Ensures the runner can falsify by execution), and the two A-reference deep
models (sites 1/2) are already validated by axiom_check.py (G-AX). AXIOM_TESTS
is therefore [] — justified in the construct assessment.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7324"
FLOAT_ENCODING = None

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE the impl regions of model.py).
# ---------------------------------------------------------------------------

# Whole encode_ident impl body (between impl-start and impl-end), captured
# verbatim so structural rewrites swap exactly one block and never touch spec.
_ENCODE_BODY = """    result = [sentinel()]  # type: List[int]
    i = 0
    while i < len(ident):
        # invariants-start
        Invariant(Acc(list_pred(ident), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(ident))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(ident) - i.
        Invariant(MustTerminate(len(ident) - i))
        Invariant(ToSeq(result) == PSeq(sentinel()) + ToSeq(ident).take(i))
        # invariants-end
        result = result + [ident[i]]
        i = i + 1
    return result"""

# Whole lookup_key impl body.
_LOOKUP_BODY = """    recovered = []  # type: List[int]
    i = 1
    while i < len(key):
        # invariants-start
        Invariant(Acc(list_pred(key), 1 / 2))
        Invariant(Acc(list_pred(recovered)))
        Invariant(len(ToSeq(key)) >= 1 and ToSeq(key)[0] == sentinel())
        Invariant(1 <= i and i <= len(key))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(key) - i.
        Invariant(MustTerminate(len(key) - i))
        Invariant(ToSeq(recovered) == ToSeq(key).drop(1).take(i - 1))
        # invariants-end
        recovered = recovered + [key[i]]
        i = i + 1
    return match(ToSeq(recovered))"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (S.enc) Structurally-different but CORRECT encode_ident: the append reads
# ident[i] into a LOCAL `ch` first, then appends the local. Same forward fold,
# same invariants, different control shape. The gold proof (forward take(i)
# invariant) stays valid, so this is NOT a proof-gap risk. If it fails to verify
# the postcondition is over-fit to the inline `result + [ident[i]]` form =>
# SPEC-TOO-STRONG.
_ENCODE_LOCAL_BODY = _ENCODE_BODY.replace(
    "        result = result + [ident[i]]\n",
    "        ch = ident[i]\n        result = result + [ch]\n",
    1,
)
_POS_ENCODE_LOCAL = _swap(_BASE, _ENCODE_BODY, _ENCODE_LOCAL_BODY)

# (S.enc.assert) The honest cheapest-impl "echo" control. `sentinel()`/the pin
# are GROUNDED (not an opaque marker), so there is no way to echo a @Pure
# answer-key into a list_pred list; the cheapest impl that satisfies
# ToSeq(Result()) == PSeq(36)+ToSeq(ident) still builds [36]++ident per element.
# This control re-asserts that built result equals the grounded pin right before
# the return; it is redundant with the gold proof and MUST verify. It
# demonstrates the spec is NOT echo-vulnerable (no wrong echo verifies; else this
# would be a reject case). Rationale source: postcondition pin + grounded helper.
_ENCODE_ASSERT_BODY = _ENCODE_BODY.replace(
    "    return result",
    "    Assert(ToSeq(result) == PSeq(sentinel()) + ToSeq(ident))\n"
    "    return result",
    1,
)
_POS_ENCODE_ASSERT = _swap(_BASE, _ENCODE_BODY, _ENCODE_ASSERT_BODY)

# (S.lk) Structurally-different but CORRECT lookup_key: read key[i] into a LOCAL
# `ch` before appending. Same forward fold from index 1, same invariants. The
# gold proof stays valid. If it fails to verify => SPEC-TOO-STRONG (over-fit to
# the inline append form).
_LOOKUP_LOCAL_BODY = _LOOKUP_BODY.replace(
    "        recovered = recovered + [key[i]]\n",
    "        ch = key[i]\n        recovered = recovered + [ch]\n",
    1,
)
_POS_LOOKUP_LOCAL = _swap(_BASE, _LOOKUP_BODY, _LOOKUP_LOCAL_BODY)

# (A.enc) ADMISSIBILITY for encode_ident. An F2P-shaped reserved identifier
# "True" = [84,114,117,101] must satisfy the precondition facts (a read-only
# list_pred — no value restriction). The probe builds the list and ASSERTS the
# permission fact the Requires demands (a direct self-call is no longer used:
# the termination obligation forbids a same-measure self-call by design). If
# the asserts cannot discharge for a normal F2P input => PRECOND-TOO-STRONG.
_ADMISS_ENCODE_BODY = _ENCODE_BODY.replace(
    "    result = [sentinel()]  # type: List[int]\n",
    "    # probe: an F2P-shaped reserved identifier 'True' = [84,114,117,101]\n"
    "    probe = [84, 114, 117, 101]  # type: List[int]\n"
    "    Assert(Acc(list_pred(probe), 1 / 2))\n"
    "    result = [sentinel()]  # type: List[int]\n",
    1,
)
_ADMISS_ENCODE = _swap(_BASE, _ENCODE_BODY, _ADMISS_ENCODE_BODY)

# (A.lk) ADMISSIBILITY for lookup_key. A SENTINEL-PREFIXED F2P-shaped key
# "$True" = [36,84,114,117,101] must satisfy lookup_key's Requires facts
# (read perm; len>=1 and key[0]==sentinel()). The probe builds the list and
# ASSERTS those facts (a direct self-call is no longer used: the termination
# obligation forbids a same-measure self-call by design). If it cannot for a
# normal prefixed name the program actually contains => PRECOND-TOO-STRONG.
_ADMISS_LOOKUP_BODY = _LOOKUP_BODY.replace(
    "    recovered = []  # type: List[int]\n",
    "    # probe: a sentinel-prefixed F2P-shaped key '$True' = [36,84,114,117,101]\n"
    "    probe = [36, 84, 114, 117, 101]  # type: List[int]\n"
    "    Assert(Acc(list_pred(probe), 1 / 2))\n"
    "    Assert(len(ToSeq(probe)) >= 1 and ToSeq(probe)[0] == sentinel())\n"
    "    recovered = []  # type: List[int]\n",
    1,
)
_ADMISS_LOOKUP = _swap(_BASE, _LOOKUP_BODY, _ADMISS_LOOKUP_BODY)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (U.enc.frame) FRAME MUTATION on encode_ident — MANDATORY (#1 weakness class).
# `ident` is read-only (1/2). This rival WRITES `ident[i] = sentinel()` before
# reading it, attempting to satisfy the pin vacuously on a self-mutated input.
# A store to `ident` needs FULL permission, so it must fail for INSUFFICIENT
# PERMISSION (not a value mismatch). The gold invariants are kept verbatim around
# the write so the rejection is attributable solely to the store. Rejection
# source: the PERMISSION SYSTEM (Acc(list_pred(ident),1/2) forbids the store).
_ENCODE_FRAME_BODY = _ENCODE_BODY.replace(
    "        result = result + [ident[i]]\n",
    "        ident[i] = sentinel()\n        result = result + [ident[i]]\n",
    1,
)
_RIVAL_ENCODE_FRAME = _swap(_BASE, _ENCODE_BODY, _ENCODE_FRAME_BODY)

# (U.lk.frame) FRAME MUTATION on lookup_key — MANDATORY. `key` is read-only
# (1/2). This rival WRITES `key[i] = sentinel()` before reading it. Must fail for
# INSUFFICIENT PERMISSION. Gold invariants kept verbatim. Rejection source: the
# PERMISSION SYSTEM (Acc(list_pred(key),1/2) forbids the store).
_LOOKUP_FRAME_BODY = _LOOKUP_BODY.replace(
    "        recovered = recovered + [key[i]]\n",
    "        key[i] = sentinel()\n        recovered = recovered + [key[i]]\n",
    1,
)
_RIVAL_LOOKUP_FRAME = _swap(_BASE, _LOOKUP_BODY, _LOOKUP_FRAME_BODY)

# (U.enc.nosent) NO SENTINEL — the pre-gold behaviour (model_prepatch.py). Start
# the result EMPTY ([] instead of [sentinel()]); the loop then yields exactly
# ident, missing the leading sentinel. Faithful real patch = the pre-patch
# `ast.Name(ident.value, Load())` (the bare identifier), which on CPython 3.8+
# crashes compile() / aborts on a debug build for the reserved spellings
# True/False/None — exactly the F2P bug — so it would NOT resolve. Rejection
# source: the pin ToSeq(Result()) == PSeq(sentinel())+ToSeq(ident) (and, for a
# reserved-word ident, the !=84/70/78 safety clauses + the first-char/round-trip
# clauses).
_RIVAL_ENCODE_NOSENT = _swap(
    _BASE,
    "    result = [sentinel()]  # type: List[int]",
    "    result = []  # type: List[int]",
)

# (U.enc.partial) PARTIAL-DOMAIN on encode_ident. Appends every ident[i]
# correctly EXCEPT when it is the FIRST identifier code point (i == 0), where it
# substitutes the sentinel (36) for the real first byte. Pins only the
# non-empty-and-first-char-unchanged sub-domain: every empty ident and every
# ident handled past index 0 is gold, the divergence is confined to inputs whose
# first body code point differs. A faithful real patch of this shape (prefix +
# but corrupt the first identifier char) would emit "$<sentinel>..." instead of
# "$<first>..." and so the membership predicate would be asked the wrong name —
# test_valid_idents (which compiles "True"/etc. and matches it back) would FAIL.
# Rejection source: the whole-sequence pin ToSeq(Result()) ==
# PSeq(36)+ToSeq(ident) — the i==0 iteration cannot close the take(i) invariant
# when ident[0] is replaced by 36 but ToSeq(ident).take(1) != PSeq(36).
_ENCODE_PARTIAL_BODY = _ENCODE_BODY.replace(
    "        result = result + [ident[i]]\n",
    "        if i == 0:\n"
    "            result = result + [sentinel()]\n"
    "        else:\n"
    "            result = result + [ident[i]]\n",
    1,
)
_RIVAL_ENCODE_PARTIAL = _swap(_BASE, _ENCODE_BODY, _ENCODE_PARTIAL_BODY)

# (U.lk.nostrip) NO STRIP — the pre-gold behaviour (model_prepatch_2.py).
# Consult the predicate on the RAW prefixed key (return match(ToSeq(key))),
# skipping the strip entirely. Faithful real patch = the pre-patch
# `self.matcher(key)`, which asks the F2P matcher {"True":True}.__getitem__ about
# "$True" rather than "True" => KeyError, so test_valid_idents would FAIL — it
# would NOT resolve. Rejection source: the pin Result() == match(strip_sentinel(
# ToSeq(key))). `match` is uninterpreted, so the verifier cannot prove
# match(ToSeq(key)) == match(ToSeq(key).drop(1)); the wrong ARGUMENT is caught.
# (This is the grounded-argument analog of an ungrounded-oracle echo: the echo on
# the wrong argument does NOT verify.)
_RIVAL_LOOKUP_NOSTRIP = _swap(
    _BASE,
    "    return match(ToSeq(recovered))",
    "    return match(ToSeq(key))",
)

# (U.lk.overstrip) OVER-STRIP — strip TWO leading code points instead of one
# (start the recovery loop at i = 2). The predicate is then consulted on
# key.drop(2) instead of key.drop(1) = strip_sentinel(key). Faithful real patch =
# `self.matcher(key[2:])` (len(IDENT_PREFIX) miscomputed as 2): for a key "$True"
# it asks the matcher about "rue", missing "True" => the F2P match FAILS, so it
# would NOT resolve. Rejection source: the pin Result() == match(strip_sentinel(
# ToSeq(key))) = match(key.drop(1)); the recovered invariant would build
# key.drop(1).take(i-1) only if i starts at 1, so starting at 2 cannot close the
# postcondition (recovered would be key.drop(2)-shaped, != key.drop(1)).
_RIVAL_LOOKUP_OVERSTRIP = _swap(
    _BASE,
    "    recovered = []  # type: List[int]\n    i = 1\n    while i < len(key):",
    "    recovered = []  # type: List[int]\n    i = 2\n    while i < len(key):",
)

# (U.enc.loop) LOOP FOREVER on encode_ident — the liveness probe. Builds the
# correct seed then spins on a counter that never reaches its bound; the return
# (and thus every value pin) is only reachable after an infinite loop, so all
# value postconditions would hold VACUOUSLY under partial correctness. The
# MustTerminate obligation must reject it: the loop carries no decreasing
# measure, so the obligation-leak check fails.
_ENCODE_LOOP_BODY = """    result = [sentinel()]  # type: List[int]
    j = 0
    while j >= 0:
        # invariants-start
        Invariant(Acc(list_pred(ident), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(j >= 0)
        # invariants-end
        j = j + 1
    return result"""
_RIVAL_ENCODE_LOOP = _swap(_BASE, _ENCODE_BODY, _ENCODE_LOOP_BODY)

# (U.lk.loop) LOOP FOREVER on lookup_key — the liveness probe for site 2.
_LOOKUP_LOOP_BODY = """    recovered = []  # type: List[int]
    j = 0
    while j >= 0:
        # invariants-start
        Invariant(Acc(list_pred(key), 1 / 2))
        Invariant(Acc(list_pred(recovered)))
        Invariant(len(ToSeq(key)) >= 1 and ToSeq(key)[0] == sentinel())
        Invariant(j >= 0)
        # invariants-end
        j = j + 1
    return match(ToSeq(recovered))"""
_RIVAL_LOOKUP_LOOP = _swap(_BASE, _LOOKUP_BODY, _LOOKUP_LOOP_BODY)

# (U.enc.selfrec) SELF-RECURSION on encode_ident — the liveness probe in its
# call-shaped form: the body simply re-invokes itself, so under partial
# correctness the callee's own postcondition would be assumed and the body
# would verify vacuously. The MustTerminate obligation must reject it: the
# self-call cannot take a strictly smaller measure than the caller's own.
_ENCODE_SELFREC_BODY = "    return encode_ident(ident)"
_RIVAL_ENCODE_SELFREC = _swap(_BASE, _ENCODE_BODY, _ENCODE_SELFREC_BODY)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-encode-local", "kind": "soundness", "expect": "verify",
     "module": _POS_ENCODE_LOCAL,
     "rationale": "structurally-different but correct encode_ident (read ident[i] into a "
                  "local `ch`, then append) keeps the gold forward-take(i) proof valid and "
                  "must verify; if not, the postcondition is over-fit to the inline "
                  "`result + [ident[i]]` form => SPEC-TOO-STRONG."},
    {"id": "pos-encode-assert-grounded", "kind": "soundness", "expect": "verify",
     "module": _POS_ENCODE_ASSERT,
     "rationale": "the cheapest impl satisfying the GROUNDED pin still builds [36]++ident per "
                  "element (sentinel()/strip_sentinel are unfolded @Pure helpers, not opaque "
                  "markers). Asserting result == PSeq(sentinel())+ToSeq(ident) before return "
                  "is redundant with the gold proof and MUST verify. Demonstrates the spec is "
                  "NOT echo-vulnerable: there is no wrong oracle-echo that verifies."},
    {"id": "pos-lookup-local", "kind": "soundness", "expect": "verify",
     "module": _POS_LOOKUP_LOCAL,
     "rationale": "structurally-different but correct lookup_key (read key[i] into a local "
                  "`ch`, then append) keeps the gold proof valid and must verify; if not, the "
                  "spec is over-fit to the inline append form => SPEC-TOO-STRONG."},
    {"id": "admiss-encode-reserved", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS_ENCODE,
     "rationale": "an F2P-shaped reserved identifier 'True' ([84,114,117,101]) must satisfy "
                  "encode_ident's Requires facts (Assert of Acc(list_pred(.),1/2) discharges); "
                  "if not, PRECOND-TOO-STRONG (the spec would reject a normal F2P input)."},
    {"id": "admiss-lookup-prefixed", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS_LOOKUP,
     "rationale": "a sentinel-prefixed F2P-shaped key '$True' ([36,84,114,117,101]) must "
                  "satisfy lookup_key's Requires facts (Asserts of the read perm and len>=1 "
                  "and key[0]==sentinel() discharge); if not, PRECOND-TOO-STRONG. Confirms "
                  "the precondition admits the names the program actually contains."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "encode-frame-mutate", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ENCODE_FRAME,
     "refinement": "no faithful real patch corresponds: pytest's not_expr never mutates the "
                   "scanned identifier (a str, immutable). The rival exists only to test "
                   "whether the read-only (1/2) precondition on `ident` can be subverted by "
                   "writing to it. No resolving patch overwrites its input, so a verifying "
                   "rival here would be a pure verify⇏resolve artifact (vacuous satisfaction "
                   "via self-mutation).",
     "rationale": "MANDATORY frame-mutation probe. `ident[i] = sentinel()` writes through a "
                  "1/2 (read-only) reference and MUST fail for insufficient permission. "
                  "Rejection source: the PERMISSION SYSTEM (the store needs full perm), not a "
                  "value mismatch; the gold invariants are kept verbatim. If it verified => "
                  "SPEC-TOO-WEAK (frame protection hollow)."},
    {"id": "lookup-frame-mutate", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LOOKUP_FRAME,
     "refinement": "no faithful real patch corresponds: MatcherAdapter.__getitem__ never "
                   "mutates the key (a str). The rival only tests whether the read-only (1/2) "
                   "precondition on `key` can be subverted by writing to it; no resolving "
                   "patch overwrites its input, so a verifying rival would be a verify⇏resolve "
                   "artifact.",
     "rationale": "MANDATORY frame-mutation probe. `key[i] = sentinel()` writes through a 1/2 "
                  "(read-only) reference and MUST fail for insufficient permission. Rejection "
                  "source: the PERMISSION SYSTEM. If it verified => SPEC-TOO-WEAK."},
    {"id": "encode-no-sentinel", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ENCODE_NOSENT,
     "refinement": "starts the result EMPTY, emitting the bare identifier (no leading "
                   "sentinel) — exactly model_prepatch.py / the pre-patch ast.Name(ident."
                   "value). On CPython 3.8+ compile() rejects the bare ast.Name('True'/"
                   "'False'/'None') (ValueError; debug-build abort), so the F2P "
                   "test_valid_idents[True/False/None] would FAIL — it would NOT resolve.",
     "rationale": "the pre-gold bug. Rejection source: the pin ToSeq(Result()) == "
                  "PSeq(sentinel())+ToSeq(ident), plus (for reserved idents) the first-char "
                  "==sentinel and !=84/70/78 safety clauses and the round-trip clause — all "
                  "fail when no sentinel is prepended. If it verified => SPEC-TOO-WEAK "
                  "(admits the crashing pre-patch)."},
    {"id": "encode-partial-first-char", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ENCODE_PARTIAL,
     "refinement": "appends every ident code point correctly EXCEPT the first body char "
                   "(i==0), which it replaces by the sentinel. A faithful real patch of this "
                   "shape (prepend the prefix but corrupt the first identifier character) "
                   "emits a name whose body's first char is wrong, so the membership predicate "
                   "is asked the wrong identifier and test_valid_idents would FAIL — it would "
                   "NOT resolve.",
     "rationale": "partial-domain: pins only the empty-or-past-index-0 sub-domain. Rejection "
                  "source: the whole-sequence pin ToSeq(Result()) == PSeq(36)+ToSeq(ident); "
                  "the i==0 iteration cannot close the take(i) invariant when ident[0] is "
                  "replaced by 36 but ToSeq(ident).take(1) != PSeq(36). If it verified => "
                  "SPEC-TOO-WEAK (domain-incomplete on the first char)."},
    {"id": "lookup-no-strip", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LOOKUP_NOSTRIP,
     "refinement": "consults the predicate on the RAW prefixed key (return match(ToSeq(key))) "
                   "— exactly model_prepatch_2.py / the pre-patch self.matcher(key). The F2P "
                   "matcher {'True':True}.__getitem__ would be asked about '$True' not 'True' "
                   "=> KeyError, so test_valid_idents would FAIL — it would NOT resolve.",
     "rationale": "the pre-gold bug AND the grounded-argument echo probe: `match` is "
                  "uninterpreted so the verifier cannot prove match(ToSeq(key)) == "
                  "match(ToSeq(key).drop(1)). Rejection source: the pin Result() == "
                  "match(strip_sentinel(ToSeq(key))) — the wrong ARGUMENT is caught. If it "
                  "verified => SPEC-TOO-WEAK (echo on wrong argument admitted)."},
    {"id": "lookup-over-strip", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LOOKUP_OVERSTRIP,
     "refinement": "strips TWO leading code points (loop starts at i=2), so the predicate is "
                   "consulted on key.drop(2) not strip_sentinel(key)=key.drop(1). A faithful "
                   "real patch = self.matcher(key[2:]) (len(IDENT_PREFIX) miscomputed): for "
                   "'$True' it asks about 'rue', missing 'True' => the F2P match FAILS — it "
                   "would NOT resolve.",
     "rationale": "partial/structural divergence on the strip width. Rejection source: the "
                  "pin Result() == match(strip_sentinel(ToSeq(key))) = match(key.drop(1)); the "
                  "recovered invariant builds key.drop(1).take(i-1) only when i starts at 1, "
                  "so starting at 2 cannot close the postcondition (recovered is key.drop(2)-"
                  "shaped). If it verified => SPEC-TOO-WEAK (over-strip admitted)."},
    {"id": "encode-loop-forever", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ENCODE_LOOP,
     "refinement": "the emitted name is only ever produced after an infinite spin, so a "
                   "faithful real patch of this shape hangs the identifier branch and the "
                   "F2P tests (test_valid_idents[True/False/None]) never complete — it "
                   "would NOT resolve.",
     "rationale": "LIVENESS probe (the recorded break class). Every value pin is only "
                  "reachable after a non-terminating loop, so under partial correctness the "
                  "postconditions hold vacuously. Rejection source: the MustTerminate "
                  "obligation — the unbounded loop carries no decreasing measure, so the "
                  "obligation-leak check fails. If it verified => SPEC-TOO-WEAK (no "
                  "termination obligation)."},
    {"id": "lookup-loop-forever", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LOOKUP_LOOP,
     "refinement": "the lookup answer is only ever produced after an infinite spin, so a "
                   "faithful real patch of this shape hangs every membership lookup and the "
                   "F2P tests never complete — it would NOT resolve.",
     "rationale": "LIVENESS probe for site 2, same class. Rejection source: the "
                  "MustTerminate obligation (obligation-leak check on the unbounded loop). "
                  "If it verified => SPEC-TOO-WEAK."},
    {"id": "encode-self-recursion", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ENCODE_SELFREC,
     "refinement": "the body only re-invokes itself, so a faithful real patch of this shape "
                   "recurses without bound on every identifier and the F2P tests error out "
                   "(recursion limit) — it would NOT resolve.",
     "rationale": "LIVENESS probe, call-shaped (the exact recorded break): under partial "
                  "correctness the self-call's own postcondition is assumed and the body "
                  "verifies vacuously. Rejection source: the MustTerminate obligation — a "
                  "self-call cannot take a strictly smaller measure than its caller's. If "
                  "it verified => SPEC-TOO-WEAK."},
]

# ===========================================================================
# AXIOM LANE — none.
# ===========================================================================
# The single consumed axiom `match` is @Pure @ContractOnly with NO value Ensures
# (it constrains only determinism — a function of its argument). There is no
# Ensures the runner could falsify by executing the real callee, and the
# argument-grounding is enforced by the spec lane (lookup-no-strip). The two
# A-reference deep models (site 1 prepend, site 2 strip) are validated against
# the real `not_expr` / `MatcherAdapter.__getitem__` by axiom_check.py (G-AX,
# already pass) — re-running that in Docker is the existing G-AX, not a new PBT
# obligation. Hence AXIOM_TESTS = [].
AXIOM_TESTS = []
