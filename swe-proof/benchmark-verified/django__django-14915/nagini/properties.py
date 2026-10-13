# properties.py — PBT falsification battery for django__django-14915. NOT a Nagini
# module; a record of adversarially-reasoned cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are FULL model.py variants that share
# the FROZEN spec byte-for-byte (region surgery: ONLY the text strictly between the
# method's `# impl-start` / `# impl-end` is edited; the spec view — axioms / pure /
# pre-conditions / post-conditions regions + every signature — is never touched),
# checked by Nagini verify + markers.same_spec. Axiom cases probe the A-consumed
# `value_identity` axiom against the REAL built-in `hash` (see AXIOM_TESTS below).
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   ChoiceValue.membership_identity(self) -> int
#   Models the gold-added ModelChoiceIteratorValue.__hash__ (`return hash(self.value)`):
#   the wrapper's membership identity is the identity of its WRAPPED VALUE, computed
#   from `value` ALONE and never from the derived-object field `instance`. The F2P
#   test_choice_value_hash asserts (1) hash(value_1) == hash(ModelChoiceIteratorValue(
#   c1.pk, None)) — equal value, different derived object => equal hash — and
#   (2) hash(value_1) != hash(value_2) — distinct auto-increment pks => distinct hash.
#
#   PRECONDITION (two clauses: HALF permission on BOTH facets => READ-ONLY, plus a
#   TERMINATION obligation):
#     (P1) Requires(Acc(self.value, 1/2) and Acc(self.instance, 1/2))
#     (P2) Requires(MustTerminate(1))  # total correctness: the bounded straight-line
#            delegation must terminate; forbids diverging rivals that satisfy the value
#            postconditions vacuously
#   POSTCONDITION (four clauses; one framing/permission, two no-mutation, one
#   LOAD-BEARING value clause):
#     (Q1) Ensures(Acc(self.value, 1/2) and Acc(self.instance, 1/2))   # returns perm
#     (Q2) Ensures(self.value == Old(self.value))        # the wrapped value unchanged
#     (Q3) Ensures(self.instance == Old(self.instance))  # the derived object unchanged
#     (Q4) Ensures(Result() == value_identity(self.value))
#            -- THE discriminating clause: the result is EXACTLY value_identity of the
#               wrapped value, a function of `self.value` alone. It therefore CANNOT
#               depend on `self.instance` (so two wrappers with equal value agree, and a
#               wrapper agrees with the bare value), and any other return value is wrong.
#
# FRAME-MUTATION lane is MANDATORY and exercised TWICE: BOTH facets are read-only
#   (P1 grants only Acc(self.value,1/2) and Acc(self.instance,1/2)). A rival that WRITES
#   either facet must be REJECTED for INSUFFICIENT PERMISSION. The `instance` write is
#   the sharpest attack — it is the classic "overwrite the read-only derived-object
#   field to make it equal `value`, then read the hash from it" cheat that satisfies Q4
#   vacuously. The gold `__hash__` only READS self.value; it never mutates either
#   attribute (and a real patch that did would corrupt the live wrapper a caller still
#   holds — e.g. a dict key whose stored value silently changed). Byte-fuzzers never
#   think to mutate the input; this is the project's #1 weakness class.
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo, but there IS an oracle to scrutinise.
#   Q4 is pinned to `value_identity(self.value)`, where value_identity is a @Pure
#   @ContractOnly axiom. An impl that "echoes the oracle" would be exactly
#   `return value_identity(self.value)` — which is the GOLD impl, hence correct. The
#   oracle is GROUNDED in the argument `self.value` (Q4 fixes Result == f(self.value)
#   for that one fixed function f), so there is no *value* an echo could carry that
#   satisfies Q4 yet is wrong. The only ways to be wrong are to (a) read the WRONG field
#   (value_identity(self.instance) — the prepatch bug; covered by weak-wrong-field), or
#   (b) return some OTHER integer (covered by weak-const). Both are rejected by Q4. The
#   honest control is therefore the cheapest faithful impl that returns the grounded
#   oracle (the positive control below), not a wrong echo. See 'assessment'.
#
# CONTROL-FLOW-EFFECT lane: N/A for exceptional paths. The method is a single total
#   expression with no raise, no early return, no side effect, and no exceptional path in
#   either the spec (no Exsures) or the gold (`return hash(self.value)`). There is no
#   control-flow fork for a capability-token rival to discriminate.
#
# DIVERGENCE (non-termination) lane: MANDATORY here. Nagini verifies PARTIAL correctness
#   by default, so before the spec carried Requires(MustTerminate(1)) a diverging impl
#   (`while True: pass`) satisfied every value postcondition VACUOUSLY yet its faithful
#   real patch (a __hash__ that hangs) does not resolve — the exact verify⇏correct break
#   a G-EQ audit exhibited. The termination obligation closes the class: any loop now
#   needs a decreasing MustTerminate measure and unbounded recursion is rejected. The
#   gold `return hash(self.value)` is straight-line and discharges MustTerminate(1)
#   trivially, so the obligation is faithful (the real method terminates), not
#   spec-too-strong. Exercised by diverge-loop below.
#
# PARTIAL-DOMAIN lane: exercised by weak-wrong-field (the prepatch bug — correct ONLY
#   when value_identity(instance) happens to equal value_identity(value), wrong on the
#   F2P shape where instance != value) and the supporting weak-const near-miss.
#
# AXIOM lane: meta.axioms has ONE A-consumed @ContractOnly axiom (value_identity ==
#   built-in hash); deep_model_references == []. The axiom's encoded property is the
#   WEAKEST sufficient one — value_identity is a fixed @Pure (deterministic) function of
#   its single argument; it deliberately does NOT claim injectivity. axiom-soundness
#   runs the REAL `hash` and asserts (a) determinism (what the axiom claims) and (b) the
#   two F2P obligations the proof relies on `hash` to satisfy on the test inputs (equal
#   value => equal hash regardless of derived object; distinct auto-increment pks =>
#   distinct hash). axiom-containment confirms the only callee-input the model reaches
#   (self.value : int) lies in `hash`'s domain. `hash` is a Python built-in, so the
#   probes need NO repo import and run anywhere; they mirror axiom_check.py / G-AX.
from pathlib import Path

INSTANCE = "django__django-14915"
FLOAT_ENCODING = None  # meta.json float_encoding is null


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen method impl region body, verbatim (everything strictly BETWEEN the
# method's `# impl-start` / `# impl-end`). Every spec variant _swap()s ONLY this block,
# so the edit never touches the spec (axioms/pure/pre-/post-conditions regions + the
# method signature). same_spec is computed over the spec_view, which elides every impl
# region, so swapping inside here is GUARANTEED same_spec.
_IMPL = "        return value_identity(self.value)"

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the method impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-local-reshape: structurally DIFFERENT but behaviourally identical. Instead of a
# single return-expression, it reads the wrapped value into a typed local, computes the
# grounded oracle into a second typed local, and returns that — a pure local-variable
# reshape (directive 3: NOT a loop-direction flip / forward-append against a recursive
# fold; there is no loop here). value_identity is @Pure, so binding it to a local and
# returning the local is semantically identical to returning the call directly, and the
# verifier discharges Q4 (Result() == value_identity(self.value)) and Q2/Q3 (no write,
# self.value/self.instance unchanged) with no extra lemma. If it FAILS => SPEC-TOO-STRONG
# (a faithful, structurally-different correct impl is rejected).
_POS_RESHAPE = (
    "        v = self.value           # type: int\n"
    "        ident = value_identity(v)  # type: int\n"
    "        return ident"
)


# admiss-reads: an admissibility positive control. The precondition is the single
# half-permission Acc(self.value,1/2) and Acc(self.instance,1/2). This control keeps the
# grounded return VERBATIM but FIRST asserts, under that half-permission, that the reads
# a normal F2P-shaped wrapper needs are admitted — BOTH facets are readable at 1/2 (the
# F2P constructs ModelChoiceIteratorValue(c1.pk, c1) and (c1.pk, None), i.e. an int value
# with an arbitrary derived object). No write, so no extra permission demand. If the
# precondition could not admit a legitimate wrapper, this would fail => PRECOND-TOO-STRONG.
_ADMISS = (
    "        # Admissibility: a normal F2P-shaped wrapper is in-domain; the\n"
    "        # half-permission admits READING both facets (no write).\n"
    "        Assert(self.value == self.value)      # read admitted under Acc(...,1/2)\n"
    "        Assert(self.instance == self.instance)  # read admitted under Acc(...,1/2)\n"
    "        return value_identity(self.value)"
)


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVALS (MANDATORY — BOTH facets are Acc(...,1/2), read-only).
# Each must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-instance: the SHARPEST frame attack. It OVERWRITES the read-only derived
# object field with the wrapped value (self.instance = self.value) and then returns the
# oracle of that field (value_identity(self.instance)). After the write the *values*
# would satisfy Q4 (self.instance now equals self.value, so value_identity(self.instance)
# == value_identity(self.value)) AND Q3 would even appear to hold post-hoc — but the
# write itself demands FULL write permission on self.instance, granted only at 1/2, so
# the verifier must reject for INSUFFICIENT PERMISSION before any value reasoning. This
# is the exact cheat the read-only frame exists to forbid.
_FRAME_MUT_INSTANCE = (
    "        # Frame violation: overwrite the read-only (Acc(self.instance,1/2)) field\n"
    "        # to make it equal `value`, then read the oracle from it.\n"
    "        self.instance = self.value\n"
    "        return value_identity(self.instance)"
)

# frame-mut-value: writes back into the read-only wrapped value (self.value = self.value),
# a no-op STORE, then returns the gold oracle VERBATIM (so the rejection is attributable
# SOLELY to the write, not to a value mismatch). The store demands FULL write permission
# on self.value, granted only at 1/2 => INSUFFICIENT PERMISSION. The gold __hash__ never
# mutates self.value; a real patch that did would corrupt the live wrapper's key.
_FRAME_MUT_VALUE = (
    "        # Frame violation: write back into the read-only (Acc(self.value,1/2)) field.\n"
    "        self.value = self.value\n"
    "        return value_identity(self.value)"
)


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each shares the frozen spec exactly; only the impl changes.
# ---------------------------------------------------------------------------

# weak-wrong-field: the EXACT pre-patch bug (model_prepatch.py). It reads the DERIVED
# OBJECT field instead of the wrapped value — return value_identity(self.instance). This
# is the membership identity governed by the object/instance (what the class had before
# the patch added __hash__, when __eq__-without-__hash__ left identity keyed on the
# object). value_identity is uninterpreted and not injective-claimed, but the spec pins
# Q4 to value_identity(self.value): for a wrapper where instance != value (the F2P shape:
# value=c1.pk, instance=c1 — a distinct opaque object identity) value_identity(self.instance)
# is NOT value_identity(self.value), so Q4 fails. PARTIAL-DOMAIN: correct ONLY on the
# measure-zero slice where the two oracle inputs coincide; wrong on the F2P input.
_WEAK_WRONG_FIELD = "        return value_identity(self.instance)"

# diverge-loop: the non-termination rival — an infinite `while True: pass` in place of
# the return. Under partial correctness this VERIFIES (all value postconditions hold
# vacuously on the unreachable exit); its faithful real patch is a ModelChoiceIteratorValue
# .__hash__ that never returns, which hangs the F2P test => does NOT resolve. The spec's
# Requires(MustTerminate(1)) forces the verifier to demand a termination measure the bare
# loop cannot supply, so the rival must be REJECTED.
_DIVERGE_LOOP = (
    "        # Divergence: never return; every value postcondition holds vacuously.\n"
    "        while True:\n"
    "            pass"
)

# weak-const: a supporting near-miss — return a fixed integer (0) ignoring both facets.
# It trivially satisfies Q1/Q2/Q3 (no write) but Q4 demands Result() ==
# value_identity(self.value), and value_identity is an uninterpreted @Pure function whose
# value the verifier cannot equate to the literal 0 for an arbitrary self.value. Rejected
# by Q4. (A real __hash__ that returned a constant would collapse every wrapper into one
# hash bucket — distinct pks would COLLIDE, failing F2P assertion 2; and it does not
# compute the wrapped value's identity at all.)
_WEAK_CONST = (
    "        zero = 0  # type: int\n"
    "        return zero"
)


SPEC_TESTS = [
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_RESHAPE),
        "rationale": (
            "structurally-different but CORRECT impl: the single return-expression is "
            "reshaped into two typed locals (read self.value into `v`, compute the "
            "grounded oracle value_identity(v) into `ident`, return `ident`). value_identity "
            "is @Pure so this is semantically identical to the gold single return; Q4 "
            "(Result() == value_identity(self.value)) and Q2/Q3 (no write) are discharged "
            "with no extra lemma (directive 3: no loop, no fold, no append). If it FAILS "
            "=> SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (Acc(self.value,1/2) and Acc(self.instance,1/2)) must admit "
            "a normal F2P-shaped wrapper: BOTH facets readable at half-permission (the F2P "
            "constructs ModelChoiceIteratorValue(c1.pk, c1) and (c1.pk, None)). The control "
            "asserts both reads succeed under Acc(...,1/2) then returns the gold oracle "
            "verbatim (only reads/asserts added inside the impl region, no write). If it "
            "FAILS => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-instance",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT_INSTANCE),
        "refinement": (
            "the gold __hash__ is `return hash(self.value)` — it NEVER assigns to "
            "self.instance (nor to anything). A faithful real patch that overwrote the "
            "derived-object attribute (self.instance = self.value) would silently corrupt "
            "the wrapper that callers still hold — ModelChoiceIteratorValue is used as a "
            "live choice value and dict/set member; mutating its `instance` during a hash "
            "computation is not the gold's read-only delegation and would not faithfully "
            "model it. Such a patch is not the gold and would not resolve. The only reason "
            "the post-write VALUES would satisfy Q4 is the illegal write itself."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: self.instance is granted only at "
            "Acc(self.instance,1/2) (P1); the store `self.instance = self.value` demands "
            "FULL write permission, which is not available, so the verifier rejects for "
            "INSUFFICIENT PERMISSION before any value reasoning. This is the classic "
            "frame-mutation cheat (overwrite the read-only field to make value_identity of "
            "it equal value_identity(self.value), satisfying Q4 vacuously). If it VERIFIES "
            "=> the read-only frame on self.instance is hollow (frame-mutation, the #1 "
            "weakness class; a byte-fuzzer never thinks to mutate the input)."
        ),
    },
    {
        "id": "frame-mut-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT_VALUE),
        "refinement": (
            "the gold __hash__ only READS self.value; it never assigns to it. A real patch "
            "that wrote back into the wrapped value (even the no-op self.value = self.value) "
            "would diverge from the gold's pure read-only delegation and could corrupt the "
            "stored lookup value a caller relies on as a dict key. The store is a no-op only "
            "by coincidence; the point is the spec must forbid ANY write to the read-only "
            "input — such a patch is not the gold and would not faithfully resolve."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: self.value is granted only at "
            "Acc(self.value,1/2) (P1); the store `self.value = self.value` demands FULL "
            "write permission, not available, so the verifier rejects for INSUFFICIENT "
            "PERMISSION. The gold oracle return is kept verbatim so the rejection is "
            "attributable solely to the write. If it VERIFIES => the read-only frame on "
            "self.value is hollow (frame-mutation)."
        ),
    },
    {
        "id": "weak-wrong-field",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_WRONG_FIELD),
        "refinement": (
            "this IS the pre-patch behaviour (model_prepatch.py): membership identity "
            "governed by the DERIVED OBJECT (self.instance), not the wrapped value — the "
            "state of the class BEFORE the patch added __hash__ (an __eq__-without-__hash__ "
            "class hashes on object identity, the instance). Its faithful real patch is the "
            "unchanged repo (no __hash__ that defers to the value), under which "
            "hash(ModelChoiceIteratorValue(c1.pk, c1)) is NOT hash(ModelChoiceIteratorValue("
            "c1.pk, None)) — the two share the value but differ in the derived object — so "
            "F2P assertion 1 (equal value => equal hash) fails. Does NOT resolve; exactly "
            "the change the spec senses (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by Q4 (Ensures(Result() == value_identity(self.value))): the rival "
            "returns value_identity(self.instance). value_identity is an uninterpreted @Pure "
            "function with NO injectivity claim, so the verifier cannot equate "
            "value_identity(self.instance) with value_identity(self.value) for arbitrary "
            "self.instance != self.value (the F2P shape: value=c1.pk, instance=c1 a distinct "
            "object). PARTIAL-DOMAIN: correct only where the two oracle inputs coincide, "
            "wrong on the F2P input. If it VERIFIES => SPEC-TOO-WEAK (Q4 does not actually "
            "pin the result to the VALUE facet)."
        ),
    },
    {
        "id": "diverge-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DIVERGE_LOOP),
        "refinement": (
            "the faithful real patch for this impl is a __hash__ that never returns "
            "(`while True: pass`) — hashing any ModelChoiceIteratorValue then hangs, so "
            "the F2P test_choice_value_hash never completes and the patch does NOT "
            "resolve. The gold `return hash(self.value)` is a bounded straight-line "
            "delegation that terminates on every input."
        ),
        "rationale": (
            "REJECTED by the TERMINATION OBLIGATION: the precondition carries "
            "Requires(MustTerminate(1)), so the verifier demands every loop consume the "
            "obligation with a strictly decreasing measure; the bare `while True: pass` "
            "cannot supply one. Under partial correctness (the spec before the "
            "obligation) this rival VERIFIED — all value postconditions hold vacuously "
            "on the unreachable exit — the exact verify⇏correct break a G-EQ audit "
            "exhibits. If it VERIFIES => SPEC-TOO-WEAK (divergence unconstrained)."
        ),
    },
    {
        "id": "weak-const",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_CONST),
        "refinement": (
            "returning a fixed integer (0) for every wrapper is what a real __hash__ that "
            "ignored the value would do (`return 0`). Every distinct pk would then COLLIDE "
            "into one hash, failing F2P assertion 2 (hash(value_1) != hash(value_2) for "
            "distinct auto-increment pks). It does not compute the wrapped value's identity "
            "at all. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q4 (Ensures(Result() == value_identity(self.value))): Result is the "
            "literal 0, but value_identity is an uninterpreted @Pure function the verifier "
            "cannot equate to 0 for an arbitrary self.value. Supporting near-miss carrying a "
            "real refinement (the constant-hash collision). If it VERIFIES => SPEC-TOO-WEAK "
            "(Q4 does not pin the result to the oracle's value)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — the A-consumed `value_identity` axiom vs the REAL built-in `hash`.
# meta.axioms has ONE entry (value_identity, A-consumed, == built-in hash applied to the
# wrapped value); deep_model_references == []. The axiom's encoded property is the WEAKEST
# sufficient one: value_identity is a fixed @Pure (deterministic) function of its single
# argument — it deliberately does NOT claim injectivity. The real callee `hash` is a
# Python BUILT-IN, so the probes need NO repo import and run anywhere (Docker or host);
# they mirror axiom_check.py / G-AX. The probes EXECUTE the real `hash` (directive 4: never
# scrape source) and open no files, so directives 5/6 are moot.
# ---------------------------------------------------------------------------

_AX_SOUND_PROBE = r'''
import random
import sys

# A faithful stand-in for the gold ModelChoiceIteratorValue.__hash__ semantics
# (django/forms/models.py post-patch): __hash__ delegates to the wrapped value's hash
# and is independent of `instance`. This is what the modeled method abstracts.
class ChoiceValue:
    def __init__(self, value, instance):
        self.value = value
        self.instance = instance
    def __hash__(self):
        return hash(self.value)            # the gold patch, verbatim semantics

fails = 0

# (a) AXIOM-SOUNDNESS — what value_identity actually CLAIMS: a fixed @Pure
# (deterministic) function of its single argument. The REAL `hash` must return the same
# integer on repeated calls for the same value (and depend on `v` alone). Boundary keys
# + the F2P auto-increment pk pattern + fuzz.
boundary = [0, 1, -1, 2, 7, 255, 256, 2 ** 31 - 1, 2 ** 31, -(2 ** 31),
            2 ** 63, -(2 ** 63), 2 ** 63 - 1,
            1, 2, 3, 4, 5, 42, 1000, 2 ** 31, 2 ** 63 + 7]
for v in boundary:
    a = hash(v)
    b = hash(v)
    if a != b:
        fails += 1
        print("UNSOUND determinism: hash(%r) = %r then %r" % (v, a, b))

rng = random.Random(14915)
for _ in range(20000):
    v = rng.randint(-(2 ** 40), 2 ** 40)
    if hash(v) != hash(v):
        fails += 1
        print("UNSOUND determinism (fuzz): hash(%r) non-deterministic" % (v,))

# (b) the two FAIL_TO_PASS obligations the proof relies on `hash` to satisfy on the
# specific test inputs (these are properties of the REAL callee on those inputs, NOT
# claimed by the bare axiom). The model proves them via Q4 pinning Result to the VALUE
# facet; here we confirm the real callee makes them TRUE so verify => resolve.
#
#   (1) equal value, different derived object => equal hash.
pk_pattern = [1, 2, 3, 4, 5, 42, 1000, 2 ** 31, 2 ** 63 + 7]
objects = [object(), None, "an-instance", 12345, ("a", "tuple")]
for pk in pk_pattern:
    for inst in objects:
        cv = ChoiceValue(pk, inst)
        if hash(cv) != hash(pk):
            fails += 1
            print("F2P-1 FAIL: hash(wrapper(%r,%r))=%r != hash(value)=%r"
                  % (pk, inst, hash(cv), hash(pk)))
    if hash(ChoiceValue(pk, objects[0])) != hash(ChoiceValue(pk, None)):
        fails += 1
        print("F2P-1 FAIL: equal value %r => different hash for different derived objects" % (pk,))

#   (2) distinct auto-increment pks => distinct hash (the F2P pair + a broad sweep).
for i in range(1, 5000):
    for j in (i + 1, i + 7, i + 1000):
        if hash(ChoiceValue(i, None)) == hash(ChoiceValue(j, None)):
            fails += 1
            print("F2P-2 FAIL: distinct pks %r and %r collide" % (i, j))

if fails:
    print("AXIOM-SOUNDNESS FAIL: %d violation(s) of value_identity (== built-in hash)" % fails)
    sys.exit(1)
print("AXIOM-SOUNDNESS OK: built-in hash deterministic on %d boundary + 20000 fuzz keys "
      "(value_identity is a fixed @Pure function of its argument); wrapper hash == "
      "wrapped-value hash (instance-independent, F2P-1); distinct auto-increment pks => "
      "distinct hash over a 5000-wide sweep (F2P-2)." % (len(boundary),))
sys.exit(0)
'''

_AX_COVER_PROBE = r'''
import random
import sys

# (axiom-containment) Which callee-inputs can the MODEL actually reach? The A-consumed
# axiom value_identity is applied by ChoiceValue.membership_identity to EXACTLY ONE
# operand: self.value, typed `int` (mapping.md §2: the wrapped value is a prepared
# primary key, an auto-increment integer; modeled directly as int). The real callee is
# the built-in `hash`, whose domain is any hashable object — every Python int is hashable
# (int implements __hash__), so every caller-reachable callee-input (an int) lies INSIDE
# hash's domain. Covering MORE than the caller reaches (e.g. hashing strings/tuples/None)
# would be sound, not a defect — we only need containment for the reachable `int` slice.
# We CONFIRM containment by executing the real `hash` on a heavy sample of the reachable
# operand space (the int line: boundaries + the F2P pk pattern + fuzz) and asserting it
# raises nothing and returns an int.
fails = 0
rng = random.Random(2024)

def reachable_values():
    # representative reachable `self.value` ints: 0, +/- small, the F2P auto-increment
    # pk pattern, 32/64-bit boundaries, and randomized fuzz (no length/value bound in P1).
    for v in [0, 1, -1, 2, 7, 42, 255, 256, 1000,
              2 ** 31 - 1, 2 ** 31, -(2 ** 31),
              2 ** 63 - 1, 2 ** 63, -(2 ** 63), 2 ** 63 + 7]:
        yield v
    for i in range(1, 5001):
        yield i
    for _ in range(20000):
        yield rng.randint(-(2 ** 64), 2 ** 64)

for v in reachable_values():
    try:
        h = hash(v)                         # the real callee on a reachable input
    except TypeError as e:
        fails += 1
        print("CONTAINMENT FAIL: hash raised on reachable int input %r: %s" % (v, e))
        continue
    if not isinstance(h, int):
        fails += 1
        print("CONTAINMENT FAIL: hash(%r) returned non-int %r" % (v, type(h)))

if fails:
    print("AXIOM-CONTAINMENT FAIL: %d reachable callee-input(s) outside built-in hash's domain"
          % fails)
    sys.exit(1)
print("AXIOM-CONTAINMENT OK: the only callee-input the model reaches (self.value : int) "
      "lies in built-in hash's domain — every int is hashable (no TypeError, int result) "
      "over boundaries + the F2P pk pattern + 20000 fuzz ints. Covering more (str/tuple/None) "
      "than the caller reaches is sound, not a defect.")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-value_identity",
        "axiom": "value_identity",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "value_identity is an A-consumed @ContractOnly axiom == the built-in `hash` "
            "applied to the wrapped value. AXIOM-SOUNDNESS: the probe EXECUTES the real "
            "`hash` (directive 4) and asserts (a) determinism — the property the axiom "
            "actually claims (a fixed @Pure function of its single argument) — on boundary "
            "ints + the F2P pk pattern + 20000 fuzz keys, and (b) the two F2P obligations "
            "the proof relies on `hash` to make true on the test inputs: equal value => "
            "equal hash regardless of derived object (F2P-1), and distinct auto-increment "
            "pks => distinct hash over a 5000-wide sweep (F2P-2). Mirrors axiom_check.py / "
            "G-AX. If the real callee disagrees anywhere => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-cover-value_identity",
        "axiom": "value_identity",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "AXIOM-CONTAINMENT: ChoiceValue.membership_identity applies value_identity to "
            "exactly ONE operand — self.value : int (the wrapped prepared primary key; P1 "
            "places no length/value bound). The real callee `hash` accepts any hashable, "
            "and every int is hashable, so every caller-reachable callee-input lies INSIDE "
            "hash's domain. The probe runs the real `hash` on a heavy sample of the "
            "reachable int line (boundaries + the F2P pk pattern + 20000 fuzz) and asserts "
            "it raises nothing and returns an int. A reachable input outside the domain => "
            "AXIOM-TOO-WEAK-FOR-CALLER (none expected: covering more than the caller reaches "
            "is sound, not a defect)."
        ),
    },
]
