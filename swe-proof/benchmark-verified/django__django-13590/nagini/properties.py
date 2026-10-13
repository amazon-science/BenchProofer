# properties.py — PBT falsification battery for django__django-13590.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside the single # impl-start / # impl-end region, which spec_view elides —
# so same_spec holds by construction) and are checked by Nagini verify; axiom
# cases are real-callee probes checked in Docker.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (what this spec protects — see model.py / refinement.md /
# mapping.md). ONE modeled changed function, ONE impl region:
#
#   resolve_sequence(value: List[int], field_named: bool) -> List[int]
#     Requires Acc(list_pred(value), 1/2)                 <-- READ-ONLY input
#     Ensures  Acc(list_pred(value), 1/2)                 <-- returns half-perm
#     Ensures  Acc(list_pred(Result()))
#     Ensures  len(Result()) == len(value)                <-- length pin
#     Ensures  ToSeq(Result()) == resolved_seq(ToSeq(value))   <-- value pin
#     Ensures  well_formed_container(ToSeq(Result()), field_named)  <-- TOKEN
#
# The model maps the gold list/tuple branch of Query.resolve_lookup_value: each
# sub-value is resolved (resolve_one, A-consumed pure) and a container of the
# SAME kind is rebuilt by the UNCHANGED constructor (build_container, A-consumed)
# under a calling convention chosen by the kind. The patch changes only the
# convention (single iterable vs spread one-per-field):
#     type_(values)          (spread=False)  for a plain list/tuple kind
#     type_(*values)         (spread=True)   for a field-named namedtuple kind
# A field-named kind handed the single un-spread iterable RAISES TypeError
# (the issue's `__new__() missing 1 required positional argument`); spread
# succeeds. That raise-vs-succeed is a CONTROL-FLOW EFFECT invisible to the
# List[int] value abstraction (the contents would be identical if the bad path
# even returned), so the prior batch03 spec — which pinned only contents — was
# SPEC-TOO-WEAK and the bug verified (`return resolved`).
#
# THE LOAD-BEARING CLAUSE is the capability token. build_container has
#     Requires(field_named == spread)          <-- a well-formed (non-raising)
#                                                   construction needs the kind
#                                                   to match the convention
#     Ensures(well_formed_container(ToSeq(Result()), field_named))  <-- grants it
# and well_formed_container is an abstract @ContractOnly @Predicate (NO body) —
# Nagini cannot Fold it, so NO impl can fabricate the token; the ONLY producer
# is a convention-matching build_container call. resolve_sequence's OWN
# postcondition requires the token for `field_named`, so for a field-named kind
# the only way to discharge it is to route the result through the spread
# (non-raising) construction = exactly the gold fix.
#
# THE TOKEN IS A CAPABILITY, NOT AN ANSWER-KEY ORACLE (mapping.md §3): it carries
# no value an impl could echo; it is keyed by the (contents, field_named) VALUE,
# but the only way to MINT one is to actually perform the effectful construction
# under the matching convention. So there is no "wrong echo" attack: a verifying
# impl genuinely went through the spread build (atk_6 in meta — build correctly,
# return the value-equal materialized list — verifies AND resolves, sound). The
# ungrounded-oracle-echo class is therefore N/A; it is replaced by an honest
# cheapest-impl positive control + the structurally-different positive control.
# See 'assessment'.
#
# READ-ONLY INPUT: value carries Acc(list_pred(value), 1/2). The FRAME-MUTATION
# attack (overwrite the half-permission input to satisfy a postcondition
# vacuously) is MANDATORY and present (frame-mutation-write-value). It must FAIL
# for INSUFFICIENT PERMISSION — keeping every gold invariant verbatim so the
# rejection is attributable to the write. has_readonly_input = True.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "django__django-13590"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The VERBATIM gold impl region (between, and including, # impl-start /
# # impl-end). Every variant replaces this whole block; the block is UNIQUE in
# _BASE, and the edit lives entirely inside the impl region, so spec_view —
# hence same_spec — is byte-identical for every case.
# ---------------------------------------------------------------------------
_GOLD = '''    # impl-start
    resolved = []  # type: List[int]
    i = len(value)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(Acc(list_pred(resolved)))
        Invariant(0 <= i and i <= len(value))
        Invariant(len(resolved) == len(value) - i)
        Invariant(ToSeq(resolved) == resolved_seq(ToSeq(value).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        e = value[i - 1]
        Assert(ToSeq(value).drop(i - 1)[0] == e)
        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
        resolved = [resolve_one(e)] + resolved
        i = i - 1
    # Reconstruct the container of the same kind from the resolved elements,
    # choosing the builder convention by the container kind so the construction
    # is well-formed: a field-named kind gets its elements spread one-per-field
    # (spread = True), a plain kind gets the single iterable (spread = False).
    # Either way the well-formed construction holds the resolved elements and
    # grants the token the postcondition requires.
    if field_named:
        result = build_container(resolved, field_named, True)
    else:
        result = build_container(resolved, field_named, False)
    return result
    # impl-end'''

assert _GOLD in _BASE, "anchor drift: gold impl region not found verbatim"

# The shared backward resolve-loop prefix (identical to gold) reused by variants
# that keep the loop intact and change only the reconstruction. Keeping it
# VERBATIM preserves every gold proof obligation (the invariants + the two
# framing asserts around the front-recursive resolved_seq unfold), so any
# rejection is attributable to the reconstruction change, NOT a dropped lemma
# (pilot bug #2). NOTE: we never flip the loop to forward-append — that would
# need an f(a+b)==f(a)+f(b) lemma against the front-recursive resolved_seq the
# verifier won't auto-discharge (pilot bug #3).
_LOOP = '''    resolved = []  # type: List[int]
    i = len(value)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(Acc(list_pred(resolved)))
        Invariant(0 <= i and i <= len(value))
        Invariant(len(resolved) == len(value) - i)
        Invariant(ToSeq(resolved) == resolved_seq(ToSeq(value).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        e = value[i - 1]
        Assert(ToSeq(value).drop(i - 1)[0] == e)
        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
        resolved = [resolve_one(e)] + resolved
        i = i - 1'''


# === (1) POSITIVE CONTROL — single computed-spread call site (CORRECT) =========
# meta's pos_control2: instead of the gold's two literal branches, compute
# `spread = field_named` and make ONE build_container call. Same behaviour
# (spread iff field-named), same proof obligations (loop + token). A correct
# structural reshape MUST verify, else SPEC-TOO-STRONG.
_POS_COMPUTED = '''    # impl-start
''' + _LOOP + '''
    # Structurally different but correct: a single computed-spread call site.
    spread = field_named
    result = build_container(resolved, field_named, spread)
    return result
    # impl-end'''

# === (2) POSITIVE CONTROL — branches reordered (plain-first) (CORRECT) =========
# Test the plain kind first (not field_named) and fall through to the field-named
# spread. Same value on every input; the token is minted under the matching
# convention on each branch. A correct branch-reorder MUST verify, else
# SPEC-TOO-STRONG. (Loop + asserts kept verbatim — only the if/else order flips.)
_POS_REORDER = '''    # impl-start
''' + _LOOP + '''
    # Branch-reordered (plain kind first); behaviourally identical to the gold.
    if not field_named:
        result = build_container(resolved, field_named, False)
    else:
        result = build_container(resolved, field_named, True)
    return result
    # impl-end'''

# === (3) POSITIVE CONTROL — honest cheapest correct impl (atk_6) (CORRECT) =====
# The ungrounded-oracle-echo class is N/A (the token is a capability, not an
# answer-key value an impl can echo). The honest cheapest impl that still does
# the load-bearing work: build correctly under the matching convention (earning
# the token on the built CONTENTS), but RETURN the value-equal materialized
# `resolved` list. It verifies because the token is keyed by (contents, kind)
# and `resolved` is value-equal to the built container; crucially it STILL went
# through the (effectful) spread construction for a field-named kind, so its
# faithful refinement does not raise and RESOLVES. This is meta's atk_6: a
# correct, resolving impl. It must verify (else SPEC-TOO-STRONG); admitting it is
# NOT a soundness defect because the load-bearing effect (the spread build does
# not raise) is present.
_POS_ATK6 = '''    # impl-start
''' + _LOOP + '''
    # Perform the convention-matching construction (mints the token on the built
    # contents) but return the value-equal materialized list. The token is keyed
    # by (contents, field_named), so the equal list holds it; the spread build
    # for a field-named kind still executed (no raise), so this resolves.
    if field_named:
        built = build_container(resolved, field_named, True)
    else:
        built = build_container(resolved, field_named, False)
    Assert(ToSeq(built) == ToSeq(resolved))
    return resolved
    # impl-end'''

# === (4) ADMISSIBILITY — the precondition admits a normal F2P-shaped input =====
# In-region in resolve_sequence: confirm the Requires (read access to value) is
# usable (len(value) is well-defined and non-negative) and that a normal,
# non-raising return is reachable for an in-domain input (the gold body runs to a
# return). If the precondition were vacuous / over-strong this could not both use
# the read access and return => PRECOND-TOO-STRONG. (Keeps the gold body intact;
# adds only a leading assert that the read permission is usable.)
_ADMISS = '''    # impl-start
    # admissibility: the read-only access granted by Requires is usable — the
    # length is well-defined and non-negative for a legitimate F2P-shaped input
    # (e.g. the 2-field [51, 100] namedtuple case), and a normal return follows.
    Assert(0 <= len(value))
''' + _LOOP + '''
    if field_named:
        result = build_container(resolved, field_named, True)
    else:
        result = build_container(resolved, field_named, False)
    return result
    # impl-end'''

# === (5) FRAME-MUTATION (MANDATORY) — overwrite the read-only input (reject) ===
# `value` carries only Acc(list_pred(value), 1/2): it is READ-ONLY. This rival
# tries to OVERWRITE value[0] (a heap write needing FULL list_pred permission)
# en route to the gold construction. Every gold invariant/assert/return is kept
# verbatim, so the ONLY change is the write — the rejection must be for
# INSUFFICIENT PERMISSION to write value, not for any value/token reason. A
# byte-fuzzer never thinks to mutate the input; this is the project's #1 weakness
# class. NOTE the write is placed BEFORE the loop so the loop's
# Invariant(Acc(list_pred(value),1/2)) framing is irrelevant — the write itself
# is what lacks permission.
_FRAME_MUT = '''    # impl-start
    # FRAME-MUTATION ATTACK: write to the read-only input value (only half
    # permission held) — must FAIL for insufficient permission.
    if len(value) > 0:
        value[0] = value[0]
    resolved = []  # type: List[int]
    i = len(value)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(Acc(list_pred(resolved)))
        Invariant(0 <= i and i <= len(value))
        Invariant(len(resolved) == len(value) - i)
        Invariant(ToSeq(resolved) == resolved_seq(ToSeq(value).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        e = value[i - 1]
        Assert(ToSeq(value).drop(i - 1)[0] == e)
        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
        resolved = [resolve_one(e)] + resolved
        i = i - 1
    if field_named:
        result = build_container(resolved, field_named, True)
    else:
        result = build_container(resolved, field_named, False)
    return result
    # impl-end'''

# === (6) UNIQUENESS — return resolved, never construct (atk_1) (reject) ========
# The verdict's CE: skip the builder entirely and return the materialized
# resolved list. Value pins (len, ToSeq) hold, but NO build_container call ever
# minted the well_formed_container token, and the predicate is abstract (no Fold
# possible), so the postcondition token clause is unprovable.
_ATK1 = '''    # impl-start
''' + _LOOP + '''
    # ATTACK (atk_1): never construct; return the resolved list directly.
    return resolved
    # impl-end'''

# === (7) UNIQUENESS / CONTROL-FLOW-EFFECT — namedtuple-path bug (atk_3) (reject)
# The actual pre-patch-shaped bug: build only for the plain kind; on the
# FIELD-NAMED branch return resolved WITHOUT constructing (the path whose real
# constructor would RAISE pre-patch). The plain branch mints the token, but the
# field-named branch lacks it. This is the control-flow-effect discriminator: a
# raise-vs-succeed difference the value abstraction can't see, caught by the
# token on the field-named branch.
_ATK3 = '''    # impl-start
''' + _LOOP + '''
    # ATTACK (atk_3): construct for the plain kind, but on the field-named branch
    # return resolved without going through the (would-raise) construction.
    if field_named:
        return resolved
    result = build_container(resolved, field_named, False)
    return result
    # impl-end'''

# === (8) UNIQUENESS — literal pre-patch single-iterable (atk_4) (reject) =======
# The literal pre-patch: hand the single iterable to the builder unconditionally
# (spread=False) regardless of kind — exactly model_prepatch.py. For a
# field-named kind this violates build_container's precondition field_named ==
# spread (a namedtuple handed one iterable cannot well-form). This is THE G-DIFF
# behaviour.
_ATK4 = '''    # impl-start
''' + _LOOP + '''
    # ATTACK (atk_4): always single-iterable construction (the pre-patch path).
    result = build_container(resolved, field_named, False)
    return result
    # impl-end'''

# === (9) UNIQUENESS — lie about the kind to dodge the precondition (atk_5) (rej)
# Claim a plain kind (field_named=False) so the single-iterable precondition
# field_named==spread holds — but then the token granted is
# well_formed_container(_, False), whereas the postcondition requires it for the
# REAL field_named. On a field-named input the postcondition token clause fails.
_ATK5 = '''    # impl-start
''' + _LOOP + '''
    # ATTACK (atk_5): pass field_named=False to dodge the precondition; the token
    # minted is for the WRONG kind (False), not the required field_named.
    result = build_container(resolved, False, False)
    return result
    # impl-end'''

# === (10) PARTIAL-DOMAIN — drop the last element for field-named len>=1 (reject)
# Correct element-wise resolution and a convention-matching build, EXCEPT on the
# field-named sub-domain with at least one element the loop stops one step early
# (i > 1 instead of i > 0), so `resolved` is one element short. build_container
# then mints a token on the SHORT contents, and len(Result()) == len(value)-1 !=
# len(value): the length pin (and ToSeq pin) fail on that sub-domain. Correct on
# the plain kind and on empty field-named inputs; diverges precisely on the F2P
# shape (a >=1-field namedtuple). The token alone does NOT save it because the
# pins are value-level.
_PARTIAL = '''    # impl-start
    resolved = []  # type: List[int]
    i = len(value)
    # PARTIAL-DOMAIN: for a field-named kind, stop the loop one step early so the
    # first element is dropped (resolved is one short). Plain / empty inputs are
    # handled correctly; only the field-named >=1-element sub-domain diverges.
    stop = 1 if field_named and len(value) > 0 else 0
    while i > stop:
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(Acc(list_pred(resolved)))
        Invariant(stop <= i and i <= len(value))
        Invariant(len(resolved) == len(value) - i)
        Invariant(ToSeq(resolved) == resolved_seq(ToSeq(value).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        e = value[i - 1]
        Assert(ToSeq(value).drop(i - 1)[0] == e)
        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
        resolved = [resolve_one(e)] + resolved
        i = i - 1
    if field_named:
        result = build_container(resolved, field_named, True)
    else:
        result = build_container(resolved, field_named, False)
    return result
    # impl-end'''


SPEC_TESTS = [
    {
        "id": "pos-control-computed-spread",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _POS_COMPUTED),
        "rationale": "meta's pos_control2: a single computed-spread call site "
                     "(spread = field_named; one build_container call) instead of "
                     "the gold's two literal branches. Same behaviour and same "
                     "proof obligations (the backward loop + invariants/asserts "
                     "kept verbatim; the token minted under the matching "
                     "convention). A correct structural reshape MUST verify; if "
                     "not => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _POS_REORDER),
        "rationale": "Branch-reorder positive control: test the plain kind first "
                     "(not field_named) and fall through to the field-named spread. "
                     "Behaviourally identical to the gold; both branches mint the "
                     "token under the matching convention. The loop and framing "
                     "asserts are byte-identical to gold (only the if/else order "
                     "flips), so the gold proof still discharges. Must verify, else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-atk6-equal-list",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _POS_ATK6),
        "rationale": "meta's atk_6 (the SOUND verifying impl): perform the "
                     "convention-matching construction — which mints "
                     "well_formed_container on the built contents AND, for a "
                     "field-named kind, executes the spread build (the effect that "
                     "does not raise) — then return the value-equal materialized "
                     "`resolved`. The token is keyed by the (contents, field_named) "
                     "VALUE, so the equal list holds it; the load-bearing effect is "
                     "present. It must verify (the token is a capability, not an "
                     "echo-able answer-key value), and its faithful refinement "
                     "RESOLVES (test_range_lookup_namedtuple PASSES) — so admitting "
                     "it is verify=>resolve, NOT a SPEC-TOO-WEAK defect. If it "
                     "failed to verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-readonly-usable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _ADMISS),
        "rationale": "In-region: confirms the Requires (read-only access to value) "
                     "is usable — len(value) is well-defined and non-negative for a "
                     "legitimate F2P-shaped input (the 2-field [51,100] namedtuple) "
                     "— and that a normal, non-raising return is reachable (the gold "
                     "body runs to a return). If the precondition were vacuous or "
                     "over-strong this could not both use the read access and "
                     "return => PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutation-write-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _FRAME_MUT),
        "refinement": "A faithful real patch that OVERWRITES the caller's input "
                      "sequence (`value[0] = ...`) to manufacture its result would "
                      "MUTATE the lookup argument the caller still holds — "
                      "Query.resolve_lookup_value must NOT mutate the value it is "
                      "passed; aliasing the rebuilt container onto the input is a "
                      "different (incorrect) computation and would corrupt the "
                      "caller's data, so such a patch does NOT resolve "
                      "test_range_lookup_namedtuple / the P2P lookup suite.",
        "rationale": "value carries only Acc(list_pred(value), 1/2) (READ-ONLY). "
                     "The write `value[0] = value[0]` needs FULL list_pred "
                     "permission; with only half it FAILS for INSUFFICIENT "
                     "PERMISSION. Every gold invariant/assert/return is kept "
                     "verbatim, so the rejection is attributable purely to the "
                     "write. Source: the precondition's fractional permission "
                     "(the frame condition).",
    },
    {
        "id": "uniqueness-atk1-never-construct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _ATK1),
        "refinement": "This is the batch03 verdict's CE refined: skip the "
                      "constructor and return the resolved generator's contents "
                      "directly. The faithful real patch (`return values` without "
                      "ever calling type_(...)) returns a generator, not a rebuilt "
                      "list/tuple/namedtuple — the __range lookup receives an "
                      "unconstructed iterable and the queryset filter fails to "
                      "produce the expected rows, so it does NOT resolve "
                      "test_range_lookup_namedtuple.",
        "rationale": "The value pins (len, ToSeq) hold, but NO build_container call "
                     "minted the well_formed_container token, and the predicate is "
                     "abstract @ContractOnly (no body, Nagini cannot Fold it), so "
                     "the postcondition clause well_formed_container(ToSeq(Result()),"
                     " field_named) is unprovable => FAILS, insufficient permission "
                     "to the token. Source: the load-bearing token postcondition.",
    },
    {
        "id": "control-flow-effect-atk3-namedtuple-bug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _ATK3),
        "refinement": "THIS IS the gold patch's target bug: build for the plain "
                      "kind but, for a field-named namedtuple, skip the spread "
                      "construction and return the bare contents (the path whose "
                      "real constructor type_(values) RAISES TypeError "
                      "`__new__() missing 1 required positional argument`). The "
                      "faithful real patch on this branch raises on the F2P 2-field "
                      "EmployeeRange(minimum=51, maximum=100), so the lookup blows "
                      "up — it does NOT resolve test_range_lookup_namedtuple.",
        "rationale": "The raise-vs-succeed difference on the field-named branch is a "
                     "CONTROL-FLOW EFFECT invisible to the List[int] value "
                     "abstraction; it is lifted into the well_formed_container "
                     "token. The plain branch mints the token, but the field-named "
                     "branch returns resolved without a convention-matching "
                     "build_container call, so it lacks the token for field_named => "
                     "FAILS. Source: the token postcondition on the field-named "
                     "branch (the control-flow-effect discriminator).",
    },
    {
        "id": "uniqueness-atk4-prepatch-single-iterable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _ATK4),
        "refinement": "The literal pre-patch (model_prepatch.py): hand the single "
                      "iterable to the constructor unconditionally — `type(value)"
                      "(values)` regardless of kind. For a field-named namedtuple "
                      "this is precisely the pre-patch code that RAISES TypeError on "
                      "EmployeeRange(<generator>); the faithful real patch does NOT "
                      "resolve test_range_lookup_namedtuple (it is the bug the gold "
                      "fixes).",
        "rationale": "On a field-named input (field_named == True) the unconditional "
                     "spread=False call violates build_container's precondition "
                     "Requires(field_named == spread) (a namedtuple handed one "
                     "iterable cannot well-form) => FAILS the precondition. This is "
                     "the G-DIFF behaviour (meta gates.G-DIFF). Source: "
                     "build_container's well-formed-construction precondition.",
    },
    {
        "id": "uniqueness-atk5-lie-about-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _ATK5),
        "refinement": "Claim the container is a plain kind (pass field_named=False) "
                      "so the single-iterable convention is precondition-legal, then "
                      "build with spread=False. A faithful real patch that treats a "
                      "namedtuple as a plain list/tuple would call type_(values) on "
                      "the namedtuple and RAISE (same pre-patch TypeError) — it does "
                      "NOT resolve test_range_lookup_namedtuple.",
        "rationale": "build_container grants well_formed_container(ToSeq(Result()), "
                     "False) (the kind it was TOLD), but resolve_sequence's "
                     "postcondition requires well_formed_container(ToSeq(Result()), "
                     "field_named). On a field-named input (field_named == True) the "
                     "minted token (_, False) does not match the required (_, True) "
                     "=> FAILS the token postcondition. Source: the field_named "
                     "argument of the token clause.",
    },
    {
        "id": "partial-domain-drop-first-field-named",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _PARTIAL),
        "refinement": "A faithful real patch correct for plain and empty inputs but "
                      "dropping the first sub-value for a non-empty field-named kind "
                      "would rebuild EmployeeRange from one fewer element — on the "
                      "F2P 2-field case it would either raise (too few positional "
                      "args) or build the wrong-arity container, yielding the wrong "
                      "range bounds. It does NOT resolve test_range_lookup_namedtuple "
                      "(the queryset would not return exactly [c5]).",
        "rationale": "On the field-named non-empty sub-domain the loop stops one "
                     "step early, so len(resolved) == len(value) - 1; "
                     "build_container then pins len(Result()) == len(elems), giving "
                     "len(Result()) == len(value) - 1, which contradicts the "
                     "postcondition len(Result()) == len(value) (and the ToSeq pin) "
                     "=> FAILS on that sub-domain. The token is minted (matching "
                     "convention) but cannot rescue the value-level length/ToSeq "
                     "pins. Source: the len/ToSeq postcondition on the field-named "
                     ">=1-element sub-domain.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — two A-consumed axioms about UNCHANGED callees:
#   * resolve_one          — the recursive per-element resolution (consumed only
#                            as a deterministic pure function of the sub-value).
#   * build_container       — the UNCHANGED container constructor, whose
#     + well_formed_container  well-formed (non-raising) construction is
#                            reachable only under the matching convention
#                            (field_named == spread) and which grants the token.
#
# Both probes CALL the real callees (Python's own list/tuple/namedtuple
# constructors and the identity pass-through resolution), never scrape source
# (pilot bug #4). They import only the standard library, open nothing on disk
# (no codec concern, pilot bug #5), and self-contain the oracle — the runner
# mounts ONLY the probe at /work (pilot bug #6). apply_gold=True (the axioms
# describe the post-gold construction the patch performs).
#
# AXIOM-SOUNDNESS: assert the real constructions match the contract on the F2P
# boundary [51,100] + sentinels + fuzz — plain single-iterable well-forms ==
# elements; namedtuple SPREAD well-forms == elements; namedtuple SINGLE-ITERABLE
# does NOT well-form (RAISES for >=2 fields, bundles into field 0 for 1 field).
# Any disagreement => AXIOM-UNSOUND.
#
# AXIOM-CONTAINMENT: the model passes build_container ONLY a list of resolved
# sub-values with spread == field_named (so its Requires(field_named == spread)
# is always satisfied by construction — the impl picks spread = field_named) and
# resolve_one ONLY plain integer scalars (List[int] carrier). Every such input
# lies in the axioms' Requires domain. The probe enumerates exactly the
# caller-reachable convention pairs (field_named, spread) ∈ {(F,F),(T,T)} and
# asserts each is precondition-legal AND well-forms; the would-raise pair (T,F)
# is the one the precondition FORBIDS and the impl never reaches. Covering the
# (T,F) raise as "not well-formed" is sound (it is the convention the caller
# never uses). A reachable input outside the covered domain would be
# AXIOM-TOO-WEAK-FOR-CALLER — none exists.
# ---------------------------------------------------------------------------

_RESOLVE_ONE_PROBE = r'''
import sys


def resolve_one(x):
    """Reference for model.py's resolve_one: the recursive per-element
    resolution bottoms out, for a non-expression sub-value (no
    resolve_expression attribute), in the pass-through `return value` branch.
    Identity on such scalars; deterministic and side-effect-free."""
    if hasattr(x, "resolve_expression"):  # pragma: no cover
        raise AssertionError("fuzz sub-values are plain scalars")
    return x


def main():
    # The model carries sub-values as opaque int identities (List[int]); the
    # caller-reachable domain for resolve_one is therefore plain integers
    # (plus, for completeness, the scalar sentinels the gold pass-through sees).
    scalars = [0, 1, -1, 7, 42, -99, 51, 100, 2 ** 31, -(2 ** 31), 123456789]
    bad = 0
    for x in scalars:
        a = resolve_one(x)
        b = resolve_one(x)
        if a != b:
            print("VIOLATION: resolve_one not deterministic on %r: %r vs %r"
                  % (x, a, b))
            bad += 1
        if a != x:
            print("VIOLATION: resolve_one not identity on non-expression %r: %r"
                  % (x, a))
            bad += 1
    if bad:
        print("resolve_one axiom VIOLATED: %d disagreements" % bad)
        sys.exit(1)
    print("resolve_one axiom OK: deterministic + identity pass-through on %d "
          "integer scalars (the model's caller-reachable List[int] domain)"
          % len(scalars))
    sys.exit(0)


main()
'''

_BUILD_CONTAINER_PROBE = r'''
import collections
import random
import sys


def resolve_one(x):
    if hasattr(x, "resolve_expression"):  # pragma: no cover
        raise AssertionError("fuzz sub-values are plain scalars")
    return x


def check_plain_single_iterable(elements):
    """spread == False, field_named == False: a plain kind built from a single
    iterable WELL-FORMS holding exactly the elements (the matching convention)."""
    for kind in (list, tuple):
        gen = (resolve_one(e) for e in elements)
        built = kind(gen)                              # real construction
        if list(built) != [resolve_one(e) for e in elements]:
            print("VIOLATION: plain %s single-iterable contents wrong on %r"
                  % (kind.__name__, elements))
            return 1
    return 0


def check_named_spread(elements):
    """spread == True, field_named == True: a namedtuple built by spreading
    one-per-field WELL-FORMS holding exactly the elements (the matching
    convention = the gold's type_(*values))."""
    n = len(elements)
    if n == 0:
        return 0  # a namedtuple has >= 1 field; empty is the plain case
    NT = collections.namedtuple("NT", ["f%d" % k for k in range(n)])
    gen = (resolve_one(e) for e in elements)
    built = NT(*gen)                                   # real construction (fix)
    if list(built) != [resolve_one(e) for e in elements]:
        print("VIOLATION: namedtuple spread contents wrong on %r" % (elements,))
        return 1
    return 0


def check_named_single_iterable_NOT_wellformed(elements):
    """spread == False, field_named == True: the MISMATCHED convention the
    precondition (field_named == spread) FORBIDS and the impl never reaches.
    It must NOT well-form: raise for >= 2 fields, bundle into field 0 for 1
    field. (Establishes that the token-granting construction is reachable only
    under the matching convention.)"""
    n = len(elements)
    if n == 0:
        return 0
    NT = collections.namedtuple("NT", ["f%d" % k for k in range(n)])
    gen = (resolve_one(e) for e in elements)
    if n == 1:
        wrong = NT(gen)                                # bundles iterable -> field0
        if list(wrong) == [resolve_one(e) for e in elements]:
            print("VIOLATION: 1-field single-iterable unexpectedly well-formed "
                  "on %r" % (elements,))
            return 1
        return 0
    raised = False
    try:
        NT(gen)                                        # too few positional args
    except TypeError:
        raised = True
    if not raised:
        print("VIOLATION: %d-field namedtuple single-iterable did NOT raise on "
              "%r" % (n, elements))
        return 1
    return 0


def main():
    boundary = [
        [],
        [10],
        [51, 100],            # the F2P case: EmployeeRange(minimum=51, maximum=100)
        [1, 2, 3],
        [0, 0],
        [-5, 7, -9, 11],
        list(range(8)),
    ]
    bad = 0
    checks = 0
    for elements in boundary:
        # CONTAINMENT: the model only ever reaches the matching-convention pairs
        # (field_named==spread): (F,F) for a plain kind and (T,T) for a named
        # kind. Both must well-form (precondition-legal + correct contents).
        bad += check_plain_single_iterable(elements)        # (F, F)
        bad += check_named_spread(elements)                 # (T, T)
        # The precondition-forbidden mismatched pair (T, F) must NOT well-form —
        # it is the convention the caller never uses (the would-raise path).
        bad += check_named_single_iterable_NOT_wellformed(elements)  # (T, F)
        checks += 3

    rng = random.Random(13590)
    for _ in range(20000):
        n = rng.randint(0, 8)
        elements = [rng.randint(-1000, 1000) for _ in range(n)]
        bad += check_plain_single_iterable(elements)
        bad += check_named_spread(elements)
        bad += check_named_single_iterable_NOT_wellformed(elements)
        checks += 3

    if bad:
        print("build_container axiom VIOLATED: %d disagreements" % bad)
        sys.exit(1)
    print("build_container axiom OK over %d construction checks (7 boundary incl. "
          "the F2P [51,100] + 20000 fuzz element lists): plain single-iterable "
          "well-forms == elements; namedtuple spread well-forms == elements; "
          "namedtuple single-iterable (the forbidden mismatched convention) does "
          "NOT well-form (raises for >=2 fields, bundles for 1). The token-"
          "granting construction is reachable only under the matching convention "
          "field_named == spread." % checks)
    sys.exit(0)


main()
'''


AXIOM_TESTS = [
    {
        "id": "ax-resolve-one-soundness",
        "axiom": "resolve_one",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _RESOLVE_ONE_PROBE,
        "rationale": "resolve_one is consumed ONLY as a deterministic pure "
                     "function of the sub-value (no Ensures beyond purity). The "
                     "probe CALLS the real pass-through resolution on the model's "
                     "caller-reachable integer domain (List[int] carrier) and "
                     "asserts determinism + the identity pass-through that the "
                     "recursive resolve_lookup_value bottoms out in for a "
                     "non-expression scalar (query.py:1083). A non-deterministic or "
                     "non-identity observation => AXIOM-UNSOUND. Covers both "
                     "soundness and containment (integers are exactly what the "
                     "model passes).",
    },
    {
        "id": "ax-build-container-soundness-containment",
        "axiom": "build_container",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _BUILD_CONTAINER_PROBE,
        "rationale": "build_container + well_formed_container model the UNCHANGED "
                     "container constructor. The probe CALLS the real Python "
                     "constructors (list/tuple/collections.namedtuple) on the F2P "
                     "boundary [51,100] + sentinels + 20000 fuzz lists and asserts "
                     "the contract: the matching-convention pairs (field_named=="
                     "spread) — plain single-iterable and namedtuple spread — both "
                     "WELL-FORM holding exactly the elements; the precondition-"
                     "forbidden mismatched pair (named, single-iterable) does NOT "
                     "well-form (raises for >=2 fields, bundles for 1). Any "
                     "disagreement => AXIOM-UNSOUND. CONTAINMENT: the impl only ever "
                     "reaches the matching pairs (it sets spread = field_named), all "
                     "covered; the would-raise pair is exactly the precondition-"
                     "forbidden one the caller never uses, so the axiom is not "
                     "too-weak-for-caller.",
    },
]
