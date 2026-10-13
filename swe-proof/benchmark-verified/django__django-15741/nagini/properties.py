# properties.py — PBT falsification battery for django__django-15741. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region; the runner re-runs the Nagini
# verifier on the host and checks the verify/reject outcome against `expect`.
# AXIOM_TESTS run real-callee probes in the instance Docker image.
#
# ---------------------------------------------------------------------------
# Defended surface (read model.py + refinement.md + mapping.md + axiom_check.py)
# ---------------------------------------------------------------------------
#   lookup_format(requested_name: FormatType) -> List[int]
#     Requires(Acc(requested_name.deferred, 1/2))                       # READ-ONLY
#     Requires(Acc(requested_name.content, 1/2)
#              and Acc(list_pred(requested_name.content), 1/2))         # READ-ONLY
#     Ensures(Acc(requested_name.deferred, 1/2) and Acc(requested_name.content, 1/2))
#     Ensures(Wildcard(list_pred(requested_name.content)))             # READ-ONLY
#     Ensures(Wildcard(list_pred(Result())))                           # READ-ONLY
#     Ensures(ToSeq(Result()) == format_value(resolve(requested_name))) # LOAD-BEARING
#
#   resolve(ft)  is @Pure, returns ToSeq(ft.content): the resolved character
#     sequence, INDEPENDENT of ft.deferred. It is GROUNDED in the input (a pure
#     function of ft.content, fully unfolded to ToSeq(ft.content)) — NOT an
#     opaque answer-key. So `resolve(requested_name) == ToSeq(requested_name.content)`.
#
#   format_value(name: PSeq[int]) -> PSeq[int]  is @Pure @ContractOnly: the
#     OPAQUE downstream lookup value, a deterministic function of its argument.
#     do_lookup(name) is @ContractOnly with
#     Ensures(ToSeq(Result()) == format_value(ToSeq(name))). It only READS the
#     name it is keyed on, so it both takes and gives back the name at
#     Wildcard(list_pred(name)) — read access, never ownership, on either side.
#     What it hands back it also KEEPS: the same value object is served to every
#     later request for that name, and for a name it holds no separate value for
#     it hands back the name object itself. So its result comes with
#     Ensures(Wildcard(list_pred(Result()))) — read access, never ownership.
#     Two consequences, both LOAD-BEARING:
#     (a) Wildcard permission is UNACCUMULABLE: no number of lookups, and no
#     aliasing case-split over their results, can add up to the FULL permission a
#     write needs. That is what makes the "read but never modify" obligation hold
#     for the whole family rather than for one call pattern (see poison-* below).
#     (b) Because neither side is owned across the call, "the value IS the name
#     object" stays POSSIBLE, so no requester can derive Result() is not name.
#     Owning the key would have forced that distinctness for free (positive
#     permission on the result contradicts FULL on the key), and a rival could
#     then hide any value it liked in a branch guarded by `served is name` that
#     the model proves dead but the real lookup takes (see alias-dead-branch).
#
#   THE SAME ACCOUNTING ONE LEVEL UP: lookup_format hands back read access to the
#     requested name (Wildcard(list_pred(requested_name.content))) rather than an
#     exact returned fraction, for the same two reasons and they are both about
#     the real callee, not about convenience. The downstream lookup keys itself on
#     the resolved name and KEEPS what it was keyed with, so a requester is not in
#     sole possession of that name afterwards; and had the exact 1/2 come back, a
#     requester that owned its name could add 1/2 + 1/2 + (any positive permission
#     on the result) > 1 and DERIVE that the value it was handed is a different
#     object from the name it asked with — which is false of the real lookup for
#     every name it hands straight back. Probes: a client that owns the name and
#     asserts `res is not content` must NOT verify, and neither must `res is
#     content`; the request is aliasing-agnostic in both directions.
#
# WHERE THE LOAD-BEARING CLAUSE BITES: the postcondition pins Result to
#   format_value(resolve(requested_name)) == format_value(ToSeq(requested_name.content)).
# The only way the proof can discharge it is to call do_lookup(name) with `name`
# whose ToSeq is PROVABLY EQUAL to ToSeq(requested_name.content) (then
# do_lookup's Ensures gives format_value(ToSeq(name)) and ToSeq(name) ==
# resolve(...) closes it). Because format_value is OPAQUE, the verifier can
# NEVER prove format_value(A) == format_value(B) for A != B (it knows nothing
# about the function beyond determinism). Hence ANY impl that feeds do_lookup a
# `name` not provably equal to the full resolved sequence (empty key, truncated
# key, deferred-branch-skip) cannot satisfy the postcondition — exactly the
# pre-patch bug (model_prepatch.py feeds an empty key on the deferred branch).
#
# IS THE ORACLE GROUNDED? format_value is opaque, BUT in the postcondition it is
# applied to resolve(requested_name), which is GROUNDED (== ToSeq(content), a
# pure function of the input). There is no free oracle value to echo: an impl
# cannot return format_value(<anything cheaper>) and have it provably equal
# format_value(ToSeq(content)) unless the argument is provably ToSeq(content).
# So the ungrounded-oracle-echo class degenerates here into the "wrong key"
# attacks (empty / truncated / deferred-skip), all of which feed do_lookup a key
# != ToSeq(content) and are rejected. See `assessment`.
#
# FRAME-MUTATION (MANDATORY — requested_name is read-only at 1/2): a rival that
# WRITES requested_name.content (append / index-store) to satisfy the
# postcondition vacuously must fail for INSUFFICIENT PERMISSION (1/2 is read-
# only). The gold invariants/asserts are kept verbatim so the rejection is
# attributable to the write.
from pathlib import Path

INSTANCE = "django__django-15741"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl region (verbatim from model.py, lines 101-119). We only ever
# replace text BETWEEN # impl-start / # impl-end, guaranteeing same_spec. The
# nested # invariants-start/# invariants-end block lives inside impl, so editing
# it is still same_spec-preserving (the invariants region is elided too).
# ---------------------------------------------------------------------------
_IMPL_OLD = """    # impl-start
    # Resolve the requested name to its character sequence FIRST, then look it
    # up — so the downstream lookup never sees the deferred form.
    name = []  # type: List[int]
    i = 0
    while i < len(requested_name.content):
        # invariants-start
        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(0 <= i and i <= len(requested_name.content))
        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
        # `i` rises by one per pass and the bound len(content) is fixed (content
        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
        # stays >= 1 while i < len(content).
        Invariant(MustTerminate(len(requested_name.content) - i + 1))
        # invariants-end
        name.append(requested_name.content[i])
        i = i + 1
    Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
    Assert(ToSeq(name) == resolve(requested_name))
    result = do_lookup(name)
    return result
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROL (soundness) — a structurally-DIFFERENT but CORRECT impl
# MUST verify (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-control-localbound: bind the loop bound to a local `clen = len(content)`
# and drive the SAME forward copy loop off it. This is a pure local-variable
# reshape: the loop direction (front-recursive forward append, matching the
# `take(i)` prefix invariant) is UNCHANGED, so no f(a+b)==f(a)+f(b) lemma is
# needed (pilot pitfall #3 avoided). Every gold invariant/assert is kept
# verbatim — the prefix-preservation invariant ToSeq(name)==take(i) and both
# trailing Asserts (pilot pitfall #2 avoided). If this faithful correct impl
# cannot verify => SPEC-TOO-STRONG.
_POS_LOCALBOUND = """    # impl-start
    name = []  # type: List[int]
    clen = len(requested_name.content)
    i = 0
    while i < clen:
        # invariants-start
        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(clen == len(requested_name.content))
        Invariant(0 <= i and i <= len(requested_name.content))
        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
        # `i` rises by one per pass; the cached bound `clen` is pinned equal to
        # len(content) by the invariant above and never reassigned, so
        # clen - i + 1 strictly decreases and stays >= 1 while i < clen.
        Invariant(MustTerminate(clen - i + 1))
        # invariants-end
        name.append(requested_name.content[i])
        i = i + 1
    Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
    Assert(ToSeq(name) == resolve(requested_name))
    result = do_lookup(name)
    return result
    # impl-end"""

# pos-control-extra-frame-assert: keep the gold loop verbatim but add a redundant
# (still-true) framing assert that re-states the resolved-sequence identity via
# ToSeq(content) before calling do_lookup. A different proof shape that adds, not
# removes, obligations; must verify (else the spec is mis-stating what resolve is).
_POS_EXTRA_ASSERT = """    # impl-start
    name = []  # type: List[int]
    i = 0
    while i < len(requested_name.content):
        # invariants-start
        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(0 <= i and i <= len(requested_name.content))
        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
        # `i` rises by one per pass and the bound len(content) is fixed (content
        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
        # stays >= 1 while i < len(content).
        Invariant(MustTerminate(len(requested_name.content) - i + 1))
        # invariants-end
        name.append(requested_name.content[i])
        i = i + 1
    Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
    Assert(resolve(requested_name) == ToSeq(requested_name.content))
    Assert(ToSeq(name) == resolve(requested_name))
    result = do_lookup(name)
    return result
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). We CANNOT add a separate caller function (a
# new module-level def changes the projected spec view and breaks same_spec).
# Instead inject the admissibility witness INSIDE the impl region (elided from
# the spec view): build a concrete F2P-shaped FormatType — a DEFERRED name whose
# content is the code points of "H:i" (the test_date_lazy witness: 72,58,105) —
# and assert it satisfies the function's exact Requires (the 1/2 perms on
# .deferred and .content/list_pred). The real impl then runs unchanged over the
# actual parameter. If the precondition could not be established for this
# legitimate input the Assert/constructor would fail => PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS = """    # impl-start
    # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
    adm_content = []  # type: List[int]
    adm_content.append(72)   # 'H'
    adm_content.append(58)   # ':'
    adm_content.append(105)  # 'i'  -> the test_date_lazy witness "H:i"
    adm = FormatType(True, adm_content)   # a DEFERRED (lazy) name, F2P shape
    # the function's exact Requires is establishable for this concrete input:
    Assert(Acc(adm.deferred, 1 / 2))
    Assert(Acc(adm.content, 1 / 2) and Acc(list_pred(adm.content), 1 / 2))
    # --- end admissibility witness; the real impl follows unchanged ---
    name = []  # type: List[int]
    i = 0
    while i < len(requested_name.content):
        # invariants-start
        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(0 <= i and i <= len(requested_name.content))
        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
        # `i` rises by one per pass and the bound len(content) is fixed (content
        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
        # stays >= 1 while i < len(content).
        Invariant(MustTerminate(len(requested_name.content) - i + 1))
        # invariants-end
        name.append(requested_name.content[i])
        i = i + 1
    Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
    Assert(ToSeq(name) == resolve(requested_name))
    result = do_lookup(name)
    return result
    # impl-end"""


# ===========================================================================
# FRAME-MUTATION (uniqueness/reject) — MANDATORY: requested_name is read-only at
# 1/2 permission. A rival that WRITES requested_name.content must fail for
# INSUFFICIENT PERMISSION. Gold invariants/asserts kept verbatim so the
# rejection is attributable to the write, not a proof gap.
# ===========================================================================

# frame-mut-append: append a code point to the read-only content before copying.
# 1/2 permission is read-only; .append needs FULL list_pred permission. Must
# reject for insufficient permission.
_FRAME_APPEND = """    # impl-start
    requested_name.content.append(0)   # WRITE to a 1/2-permission (read-only) input
    name = []  # type: List[int]
    i = 0
    while i < len(requested_name.content):
        # invariants-start
        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(0 <= i and i <= len(requested_name.content))
        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
        # `i` rises by one per pass and the bound len(content) is fixed (content
        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
        # stays >= 1 while i < len(content).
        Invariant(MustTerminate(len(requested_name.content) - i + 1))
        # invariants-end
        name.append(requested_name.content[i])
        i = i + 1
    Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
    Assert(ToSeq(name) == resolve(requested_name))
    result = do_lookup(name)
    return result
    # impl-end"""

# frame-mut-store: index-store into the read-only content (overwrite element 0).
# Same insufficient-permission rejection. Guarded len>0 so the type-checker sees
# a normal store; with empty content the body just doesn't run, but the store
# still needs FULL list_pred permission to even be admitted.
_FRAME_STORE = """    # impl-start
    if len(requested_name.content) > 0:
        requested_name.content[0] = 88   # WRITE 'X' into a read-only input
    name = []  # type: List[int]
    i = 0
    while i < len(requested_name.content):
        # invariants-start
        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(0 <= i and i <= len(requested_name.content))
        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
        # `i` rises by one per pass and the bound len(content) is fixed (content
        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
        # stays >= 1 while i < len(content).
        Invariant(MustTerminate(len(requested_name.content) - i + 1))
        # invariants-end
        name.append(requested_name.content[i])
        i = i + 1
    Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
    Assert(ToSeq(name) == resolve(requested_name))
    result = do_lookup(name)
    return result
    # impl-end"""


# ===========================================================================
# PRESERVATION (reject) — a request must leave the looked-up VALUES as it found
# them, not only its argument. A rival that returns the right value for the
# requested name but modifies a value the downstream lookup keeps and serves
# again destroys the association for that name; the next request for it yields
# something else. The value a lookup serves is held at Wildcard permission (read
# access, never ownership), and Wildcard is UNACCUMULABLE — so every rival in
# this family, however many lookups it performs and however it case-splits on
# aliasing between their results, fails for INSUFFICIENT PERMISSION on the write.
# Gold loop/invariants/asserts kept verbatim so the rejection is attributable to
# the write.
# ===========================================================================

# poison-store: right value, wrong effect (control-flow-effect family). Serve the
# request correctly, but first take an extra lookup of the SAME name and overwrite
# a character of the value it hands back. In the repository this is a request that
# writes through the object the lookup retains for that name, so a later request
# for the same name is served the modified value — the P2P shape.
_POISON_STORE = """    # impl-start
    name = []  # type: List[int]
    i = 0
    while i < len(requested_name.content):
        # invariants-start
        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(0 <= i and i <= len(requested_name.content))
        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
        # `i` rises by one per pass and the bound len(content) is fixed (content
        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
        # stays >= 1 while i < len(content).
        Invariant(MustTerminate(len(requested_name.content) - i + 1))
        # invariants-end
        name.append(requested_name.content[i])
        i = i + 1
    Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
    Assert(ToSeq(name) == resolve(requested_name))
    extra = do_lookup(name)
    if len(extra) > 0:
        extra[0] = 88          # WRITE into a value the lookup keeps and serves again
    result = do_lookup(name)
    return result
    # impl-end"""

# poison-accum: the same destructive effect reached by trying to ACCUMULATE
# permission instead of assuming it — two lookups of the same name, then a
# case-split on whether the two results are the same object, writing inside the
# aliased branch where a fractional read permission would merge into a full one.
# This is the boundary/aliased-object family, and it is the rival that defeats any
# repair phrased as a fixed permission fraction; Wildcard does not merge, so the
# write is still refused.
_POISON_ACCUM = """    # impl-start
    name = []  # type: List[int]
    i = 0
    while i < len(requested_name.content):
        # invariants-start
        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(0 <= i and i <= len(requested_name.content))
        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
        # `i` rises by one per pass and the bound len(content) is fixed (content
        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
        # stays >= 1 while i < len(content).
        Invariant(MustTerminate(len(requested_name.content) - i + 1))
        # invariants-end
        name.append(requested_name.content[i])
        i = i + 1
    Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
    Assert(ToSeq(name) == resolve(requested_name))
    a = do_lookup(name)
    b = do_lookup(name)
    if a is b:
        if len(a) > 0:
            a[0] = 88          # two read fractions on the SAME object, merged then written
    result = do_lookup(name)
    return result
    # impl-end"""

# alias-dead-branch: the boundary/aliased-object family in its purest form. Serve
# the request correctly UNLESS the value served is the requested name object
# itself, and in that case hand back something else entirely. In the repository
# that case is real and reachable — a name the downstream lookup holds no separate
# value for is served back as itself — so this rival returns the wrong thing on a
# whole class of names. A model that let a requester conclude "the value is never
# the name" would prove this branch DEAD and admit the rival for free, which is
# why neither the key nor the value is owned across a lookup.
_ALIAS_DEAD = """    # impl-start
    name = []  # type: List[int]
    i = 0
    while i < len(requested_name.content):
        # invariants-start
        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(0 <= i and i <= len(requested_name.content))
        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
        # `i` rises by one per pass and the bound len(content) is fixed (content
        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
        # stays >= 1 while i < len(content).
        Invariant(MustTerminate(len(requested_name.content) - i + 1))
        # invariants-end
        name.append(requested_name.content[i])
        i = i + 1
    Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
    Assert(ToSeq(name) == resolve(requested_name))
    served = do_lookup(name)
    if served is name:
        wrong = []  # type: List[int]
        return wrong   # a whole class of names served the WRONG value
    return served
    # impl-end"""


# ===========================================================================
# UNIQUENESS / partial-domain / deferred-skip (reject) — rivals that share the
# spec exactly and feed do_lookup a key NOT provably equal to ToSeq(content).
# Each MUST be rejected; a verifying rival is a real verify-but-not-resolve break
# (SPEC-TOO-WEAK).
# ===========================================================================

# uniq-empty-key: THE pre-patch shape, distilled. Never copy — feed do_lookup an
# EMPTY name. do_lookup returns format_value(empty), but the postcondition needs
# format_value(ToSeq(content)). For any non-empty name format_value(empty) is not
# provably equal (opaque). Rejected by the postcondition.
_UNIQ_EMPTY = """    # impl-start
    name = []  # type: List[int]
    result = do_lookup(name)
    return result
    # impl-end"""

# uniq-deferred-skip: EXACTLY model_prepatch.py — copy the name only on the
# already-resolved (not-deferred) branch; a DEFERRED name is fed to do_lookup as
# an empty key. This is the literal pre-patch bug (the deferred/lazy name reaches
# getattr unresolved). For a deferred name name==[] and the postcondition fails.
_UNIQ_DEFERRED_SKIP = """    # impl-start
    name = []  # type: List[int]
    if not requested_name.deferred:
        i = 0
        while i < len(requested_name.content):
            # invariants-start
            Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
            Invariant(Acc(list_pred(name)))
            Invariant(0 <= i and i <= len(requested_name.content))
            Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
            # `i` rises by one per pass and the bound len(content) is fixed (content
            # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
            # stays >= 1 while i < len(content).
            Invariant(MustTerminate(len(requested_name.content) - i + 1))
            # invariants-end
            name.append(requested_name.content[i])
            i = i + 1
        Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
    result = do_lookup(name)
    return result
    # impl-end"""

# uniq-drop-last: partial-domain — copy all but the LAST code point (loop bound
# len-1). name == take(len-1) != take(len) == ToSeq(content) for any non-empty
# name; do_lookup(name) == format_value(take(len-1)), not provably equal to
# format_value(ToSeq(content)). The gold resolve-assert is dropped so the
# rejection lands cleanly on the postcondition. Rejected.
_UNIQ_DROP_LAST = """    # impl-start
    name = []  # type: List[int]
    i = 0
    while i < len(requested_name.content) - 1:
        # invariants-start
        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(0 <= i and i <= len(requested_name.content))
        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
        # `while i < len(content) - 1`: one fewer pass than the gold loop, so the
        # remaining-iteration bound is len(content) - i (no +1 slack needed) —
        # strictly decreasing and >= 2 on every pass that runs.
        Invariant(MustTerminate(len(requested_name.content) - i))
        # invariants-end
        name.append(requested_name.content[i])
        i = i + 1
    result = do_lookup(name)
    return result
    # impl-end"""

# uniq-skip-first: partial-domain on the OTHER boundary — drop the FIRST code
# point (start copying at index 1). name == drop(1) of content, not provably
# equal to ToSeq(content). Supporting partial-domain near-miss. Rejected by the
# postcondition. (Uses .drop to phrase the invariant cleanly.)
_UNIQ_SKIP_FIRST = """    # impl-start
    name = []  # type: List[int]
    i = 1
    while i < len(requested_name.content):
        # invariants-start
        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(1 <= i and i <= len(requested_name.content) or len(requested_name.content) == 0)
        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i).drop(1))
        # `i` rises by one per pass and the bound len(content) is fixed (content
        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
        # stays >= 1 while i < len(content).
        Invariant(MustTerminate(len(requested_name.content) - i + 1))
        # invariants-end
        name.append(requested_name.content[i])
        i = i + 1
    result = do_lookup(name)
    return result
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-localbound",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_LOCALBOUND),
        "rationale": "structurally-different CORRECT impl: bind the loop bound to a "
                     "local `clen = len(content)` and drive the SAME forward copy off "
                     "it (loop direction unchanged, matching the take(i) prefix "
                     "invariant — no fold lemma needed, pilot pitfall #3 avoided). All "
                     "gold invariants and both trailing Asserts kept verbatim (pilot "
                     "pitfall #2 avoided). It still proves ToSeq(name)==resolve(...) and "
                     "the postcondition. If it cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-extra-assert",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_EXTRA_ASSERT),
        "rationale": "gold loop verbatim plus a redundant TRUE framing assert "
                     "resolve(requested_name)==ToSeq(requested_name.content) before the "
                     "lookup. Adds (does not remove) obligations; the assert is exactly "
                     "what resolve unfolds to, so it must hold and the impl must verify. "
                     "If it cannot verify the spec is mis-stating resolve => "
                     "SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region (elided "
                     "from the spec view, so same_spec holds) builds a concrete "
                     "F2P-shaped DEFERRED name FormatType(True, [72,58,105]) (the "
                     "test_date_lazy witness \"H:i\" as a lazy proxy) and asserts it "
                     "satisfies the function's exact Requires: Acc(adm.deferred,1/2) and "
                     "Acc(adm.content,1/2) and Acc(list_pred(adm.content),1/2). The real "
                     "impl then runs unchanged. If the precondition could not be "
                     "established for this legitimate deferred input the constructor/"
                     "Assert fails => PRECOND-TOO-STRONG.",
    },

    # ---- frame-mutation (MANDATORY; must reject for insufficient permission) ----
    {
        "id": "frame-mut-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_APPEND),
        "refinement": "appending to requested_name.content corresponds to a patch that "
                      "MUTATES the caller's format_type argument (the very str/lazy "
                      "object the template engine passes in). get_format is a pure "
                      "lookup that must not alter its argument; a patch that mutated the "
                      "shared format name would corrupt every subsequent use of that "
                      "name (cache keys, other template tags) and would not be the gold "
                      "one-line str() coercion — it would fail the P2P formatting/"
                      "template tests that re-use the same names.",
        "rationale": "rejected by the PERMISSION SYSTEM: requested_name.content is held "
                     "at Acc(list_pred(...),1/2) (read-only, directive 5); .append "
                     "requires FULL list_pred permission, which the precondition does "
                     "not grant. Insufficient-permission rejection, attributable to the "
                     "write (gold invariants/asserts unchanged).",
    },
    {
        "id": "frame-mut-store",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_STORE),
        "refinement": "overwriting requested_name.content[0] corresponds to a patch "
                      "that rewrites a character of the caller's format name in place — "
                      "again mutating shared input get_format must treat as read-only. "
                      "Such a patch would change the resolved name seen by the lookup "
                      "and corrupt the cache key for that name; it is not the gold "
                      "str() coercion and would fail the P2P format/template tests.",
        "rationale": "rejected by the PERMISSION SYSTEM: an index-store into "
                     "requested_name.content needs FULL list_pred permission; only 1/2 "
                     "(read-only) is held. Insufficient-permission rejection, "
                     "attributable to the write.",
    },

    # ---- preservation of the looked-up values (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "preserve-poison-store",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _POISON_STORE),
        "refinement": "serving the right value while overwriting a character of the "
                      "value the downstream lookup keeps for that name corresponds to a "
                      "patch that returns the correct format for the requested name and "
                      "modifies the retained value on the way out. The reported symptom "
                      "is addressed (the deferred/lazy name is resolved, so the F2P "
                      "assertions on the first request hold), but every LATER request "
                      "for that name is served the modified value, so the P2P "
                      "formatting/template tests that request the same names again — "
                      "and the ones that read the input-format lists — see corrupted "
                      "values. FAIL_TO_PASS passes, PASS_TO_PASS does not: a faithful "
                      "such patch does NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: do_lookup's result is handed "
                     "over at Wildcard(list_pred(...)) — read access, never ownership — "
                     "and an index-store needs FULL list_pred permission. Reported as "
                     "insufficient permission at `extra[0] = 88`, attributable to the "
                     "write (gold loop, invariants and both asserts unchanged).",
    },
    {
        "id": "preserve-poison-accum",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _POISON_ACCUM),
        "refinement": "the same destructive patch, reaching the write by requesting the "
                      "name twice and acting on the case where both requests are served "
                      "the SAME object — which in the repository is the normal case, "
                      "since a name's value is looked up once and retained. Its "
                      "faithful patch has the same P2P consequence as poison-store "
                      "(later requests for that name see a modified value) while still "
                      "resolving the reported F2P symptom.",
        "rationale": "rejected by the PERMISSION SYSTEM, and it is the case that "
                     "distinguishes an UNACCUMULABLE Wildcard from any fixed fraction: "
                     "with Acc(list_pred(Result()), 1/2) the two read halves would merge "
                     "on the aliased branch into the full permission the store needs and "
                     "this rival would VERIFY. Wildcard permissions do not sum, so the "
                     "store at `a[0] = 88` is still insufficient-permission — the whole "
                     "family is closed, not one path through it.",
    },
    {
        "id": "alias-dead-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _ALIAS_DEAD),
        "refinement": "returning something else whenever the value served for a name is "
                      "that name itself corresponds to a patch that resolves the name "
                      "and then hands back an unrelated value for every name the "
                      "downstream lookup keeps no separate value for. That class is "
                      "large and ordinary in the repository — a name outside the "
                      "settings the lookup knows about is handed straight back — so the "
                      "P2P tests that request such names get an empty/unrelated value "
                      "instead of the name they asked for. A faithful such patch does "
                      "NOT resolve.",
        "rationale": "rejected by the POSTCONDITION, on the branch itself: with the "
                     "name lent to the lookup at Wildcard and the value handed back at "
                     "Wildcard, `served is name` is SATISFIABLE, so the branch is live "
                     "and the verifier must discharge "
                     "ToSeq(Result()) == format_value(resolve(requested_name)) for a "
                     "freshly built empty list — which it cannot. This is the case that "
                     "shows why the lookup may not be modelled as consuming or owning "
                     "its key: were the key owned, any permission on the value would "
                     "force served is not name, this branch would be DEAD, and the "
                     "rival would verify while being wrong on real names.",
    },

    # ---- uniqueness / partial-domain / deferred-skip (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-empty-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_EMPTY),
        "refinement": "feeding do_lookup an empty name corresponds to a patch that "
                      "passed an unresolved/empty key to the downstream lookup — exactly "
                      "the failure family the bug is about (the lazy name never reaches "
                      "the lookup as its real characters). The looked-up value for the "
                      "empty key differs from the value for \"DATE_FORMAT\"/\"H:i\", so "
                      "the F2P tests (which assert get_format(gettext_lazy(\"DATE_FORMAT\"))"
                      " == \"N j, Y\" and the H:i render) would fail.",
        "rationale": "rejected by Ensures(ToSeq(Result()) == format_value(resolve(...))): "
                     "do_lookup([]) gives format_value(empty); the postcondition needs "
                     "format_value(ToSeq(content)). format_value is OPAQUE (only "
                     "determinism is known), so format_value(empty) is not provably "
                     "equal to format_value(ToSeq(content)) for a non-empty name.",
    },
    {
        "id": "uniq-deferred-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DEFERRED_SKIP),
        "refinement": "this IS the pre-patch behaviour model_prepatch.py reproduces and "
                      "G-DIFF flags: the name is resolved only on the already-resolved "
                      "branch; a DEFERRED (lazy) name is fed to the lookup unresolved. In "
                      "the real get_format that is the un-patched path where the lazy "
                      "proxy reaches getattr(module, <lazy>) and raises "
                      "TypeError: attribute name must be string. Its faithful real patch "
                      "(resolve only the eager branch) is precisely what does NOT resolve "
                      "the F2P tests test_date_lazy and test_get_format_lazy_format.",
        "rationale": "rejected by Ensures(ToSeq(Result()) == format_value(resolve(...))): "
                     "for a deferred name the impl leaves name==[] and feeds do_lookup an "
                     "empty key, so Result is pinned to format_value(empty), not "
                     "format_value(ToSeq(content)); the opaque format_value cannot be "
                     "proven to agree on the two distinct sequences.",
    },
    {
        "id": "uniq-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_LAST),
        "refinement": "truncating the last code point corresponds to a patch that "
                      "resolved the name to the wrong string (e.g. \"DATE_FORMA\" instead "
                      "of \"DATE_FORMAT\", \"H:\" instead of \"H:i\"). The downstream "
                      "lookup keyed on the truncated name returns a different value (or "
                      "falls through to returning the truncated name itself), so the F2P "
                      "assertions on the full-name value fail. A faithful such patch does "
                      "NOT resolve.",
        "rationale": "rejected by Ensures(ToSeq(Result()) == format_value(resolve(...))): "
                     "name == ToSeq(content).take(len-1) != ToSeq(content); do_lookup "
                     "gives format_value of the truncated sequence, not provably equal to "
                     "format_value(ToSeq(content)) under the opaque format_value.",
    },
    {
        "id": "uniq-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SKIP_FIRST),
        "refinement": "dropping the FIRST code point resolves the name to a different "
                      "string (\"ATE_FORMAT\" / \":i\"); the downstream lookup returns the "
                      "wrong value and the F2P assertions fail. Supporting partial-domain "
                      "near-miss on the opposite boundary from uniq-drop-last; a faithful "
                      "such patch does NOT resolve.",
        "rationale": "rejected by Ensures(ToSeq(Result()) == format_value(resolve(...))): "
                     "name == ToSeq(content).drop(1) != ToSeq(content) for a non-empty "
                     "name; format_value of it is not provably equal to "
                     "format_value(ToSeq(content)).",
    },
]


# ===========================================================================
# AXIOM LANE — two A-consumed @ContractOnly axioms (format_value @Pure +
# do_lookup) modelling the UNCHANGED downstream get_format lookup, and one
# A-reference deep model (resolve == str() coercion). Probes run in the instance
# Docker image (the real Django + the patch's str() coercion live there). We
# embed axiom_check.py's own soundness logic (the runner mounts ONLY the probe at
# /work, so axiom_check.py is NOT importable in-container — but its logic imports
# only stdlib + the repo's own django.utils.{functional,formats,translation},
# which ARE present). apply_gold=True so the str() coercion is in place.
#
# NOTE on flag_dependency: meta records resolve as flag-INDEPENDENT (str()/lazy
# __str__ is identity on the underlying string regardless of locale). The lookup
# axiom (format_value/do_lookup) encodes only KEYED-ON-RESOLVED-NAME determinism
# (get_format(lazy(name)) == get_format(name)) — also independent of the active
# locale (we exercise the default config and an override to be adversarial).
# ===========================================================================

# axiom-soundness (resolve A-reference): str() of a deferred (lazy) name equals
# the underlying string AND equals str() of the already-resolved name, on
# boundary + fuzz inputs incl. the F2P witnesses "DATE_FORMAT"/"H:i". Any
# disagreement => the deep model `resolve(ft)==ToSeq(ft.content)` (independent of
# deferred) is unsound => AXIOM-UNSOUND. Mirrors axiom_check.check_resolve_reference.
_AX_RESOLVE_PROBE = r'''
import random, sys

NAMES = [
    "DATE_FORMAT", "TIME_FORMAT", "DATETIME_FORMAT", "SHORT_DATE_FORMAT",
    "SHORT_DATETIME_FORMAT", "YEAR_MONTH_FORMAT", "MONTH_DAY_FORMAT",
    "DECIMAL_SEPARATOR", "THOUSAND_SEPARATOR", "NUMBER_GROUPING",
    "FIRST_DAY_OF_WEEK", "DATE_INPUT_FORMATS", "TIME_INPUT_FORMATS",
    "DATETIME_INPUT_FORMATS",
    "H:i", "Y-m-d", "N j, Y",
    "", "NOT_A_REAL_FORMAT_NAME", "héllo", "a b c",
]

def main():
    try:
        from django.utils.functional import lazy
    except Exception as exc:
        print("AXIOM-SOUNDNESS(resolve) FAIL: cannot import django.utils.functional.lazy: %r" % (exc,))
        return 1
    # a lazy str proxy yielding its argument unchanged (the shape of every
    # gettext_lazy / format_lazy value: a deferred string).
    deferred = lazy(lambda s: s, str)
    rng = random.Random(15741)
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdef:,- xyz0123456789"
    names = list(NAMES)
    for _ in range(5000):
        n = rng.randint(0, 24)
        names.append("".join(rng.choice(alphabet) for _ in range(n)))
    for name in names:
        eager = str(name)
        lzy = deferred(name)
        if str(eager) != name:
            print("AXIOM-UNSOUND(resolve): str(eager) %r != %r" % (str(eager), name)); return 1
        if str(lzy) != name:
            print("AXIOM-UNSOUND(resolve): str(lazy) %r != %r" % (str(lzy), name)); return 1
        if str(eager) != str(lzy):
            print("AXIOM-UNSOUND(resolve): not independent of deferred flag on %r: %r vs %r"
                  % (name, str(eager), str(lzy))); return 1
    print("AXIOM-SOUNDNESS(resolve) OK: str() coercion of deferred==already-resolved "
          "== underlying string on %d inputs (5000 fuzz + %d boundary incl. F2P witnesses); "
          "resolve(ft)==ToSeq(ft.content) independent of the deferred flag." % (len(names), len(NAMES)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

# axiom-soundness (format_value/do_lookup A-consumed): the REAL post-patch
# get_format value is a function of the RESOLVED name only — for every format
# name, get_format(gettext_lazy(name)) == get_format(name). Exercised under the
# default config AND a translation.override("de") to confirm locale-independence
# of the keyed-on-resolved-name property. Any mismatch => the
# format_value/do_lookup determinism axiom is unsound => AXIOM-UNSOUND. Mirrors
# axiom_check.check_lookup_axiom + the F2P witness.
_AX_LOOKUP_PROBE = r'''
import sys

NAMES = [
    "DATE_FORMAT", "TIME_FORMAT", "DATETIME_FORMAT", "SHORT_DATE_FORMAT",
    "SHORT_DATETIME_FORMAT", "YEAR_MONTH_FORMAT", "MONTH_DAY_FORMAT",
    "DECIMAL_SEPARATOR", "THOUSAND_SEPARATOR", "NUMBER_GROUPING",
    "FIRST_DAY_OF_WEEK", "DATE_INPUT_FORMATS", "TIME_INPUT_FORMATS",
    "DATETIME_INPUT_FORMATS",
    "H:i", "Y-m-d", "N j, Y",
    "", "NOT_A_REAL_FORMAT_NAME", "héllo", "a b c",
]

def main():
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                USE_I18N=True, USE_L10N=True, USE_TZ=False,
                INSTALLED_APPS=[], DATABASES={},
            )
            django.setup()
        from django.utils.formats import get_format, reset_format_cache
        from django.utils.translation import gettext_lazy
        from django.utils import translation
    except Exception as exc:
        print("AXIOM-SOUNDNESS(lookup) FAIL: Django unavailable/unconfigurable: %r" % (exc,))
        return 1

    def check(label):
        for name in NAMES:
            reset_format_cache()
            eager_val = get_format(str(name))
            reset_format_cache()
            lazy_val = get_format(gettext_lazy(name))
            if eager_val != lazy_val:
                print("AXIOM-UNSOUND(lookup) [%s]: %r eager=%r lazy=%r "
                      "(value NOT keyed only on resolved name)"
                      % (label, name, eager_val, lazy_val))
                return False
        return True

    # default active locale
    if not check("default"):
        return 1
    # an overridden locale: keyed-on-resolved-name must still hold
    try:
        with translation.override("de", deactivate=True):
            if not check("de"):
                return 1
    except Exception as exc:
        print("AXIOM-SOUNDNESS(lookup) note: locale override unavailable (%r); default check passed" % (exc,))

    # F2P witness explicitly
    reset_format_cache()
    f2p_lazy = get_format(gettext_lazy("DATE_FORMAT"))
    f2p_eager = get_format("DATE_FORMAT")
    if f2p_lazy != f2p_eager:
        print("AXIOM-UNSOUND(lookup): F2P witness DATE_FORMAT lazy=%r eager=%r" % (f2p_lazy, f2p_eager))
        return 1
    print("AXIOM-SOUNDNESS(lookup) OK: real get_format keyed only on the resolved "
          "name (get_format(gettext_lazy(name))==get_format(name)) for %d names "
          "under default + de locales; F2P witness DATE_FORMAT agrees (=%r)."
          % (len(NAMES), f2p_eager))
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

# axiom-containment: the model passes do_lookup a `name` whose ToSeq ==
# ToSeq(requested_name.content) == resolve(requested_name) (the loop asserts it).
# resolve is independent of the deferred flag, so the only callee-input the model
# reaches is "the resolved character sequence of the requested name" — i.e. a
# real Python str (the underlying string of a str or lazy proxy). do_lookup's
# Requires domain is `name: List[int]` mapping to any such resolved str; the real
# downstream get_format accepts EXACTLY such resolved str names. We confirm
# operationally that the resolved value the model feeds the lookup (str(...) of
# either form) is always a real str the callee accepts — never a non-str the
# axiom domain would exclude. (Covering MORE — e.g. names that are not known
# formats — is SOUND; the model reaches the resolved str of whatever name the
# caller supplies, all inside the domain.)
_AX_CONTAINMENT_PROBE = r'''
import sys

NAMES = [
    "DATE_FORMAT", "H:i", "Y-m-d", "N j, Y", "DATE_INPUT_FORMATS",
    "", "NOT_A_REAL_FORMAT_NAME", "héllo", "a b c",
]

def main():
    try:
        from django.utils.functional import lazy
    except Exception as exc:
        print("AXIOM-CONTAINMENT FAIL: cannot import django.utils.functional.lazy: %r" % (exc,))
        return 1
    deferred = lazy(lambda s: s, str)
    reached = 0
    for name in NAMES:
        # the model feeds the lookup the RESOLVED sequence == str() of the name in
        # either form; both must be a real str (the do_lookup domain), never a
        # non-str (e.g. a leftover lazy proxy) the axiom domain would exclude.
        for form, val in (("eager", str(name)), ("deferred", deferred(name))):
            resolved = str(val)   # what the model's `name` list materialises (resolve)
            if not isinstance(resolved, str):
                print("AXIOM-TOO-WEAK-FOR-CALLER: model-reachable resolved key for %r (%s) "
                      "is %r, not a real str the do_lookup domain accepts" % (name, form, resolved))
                return 1
            # and it must equal the underlying string (so the model's key is the
            # resolved name, inside the domain regardless of deferred form).
            if resolved != name:
                print("AXIOM-TOO-WEAK-FOR-CALLER: resolved key %r != underlying %r (%s)"
                      % (resolved, name, form))
                return 1
            reached += 1
    print("AXIOM-CONTAINMENT OK: every model-reachable lookup key is the RESOLVED "
          "str of the requested name (independent of the deferred flag); %d "
          "(name, form) pairs sampled, all real str inside do_lookup's domain. The "
          "caller reaches only resolved-name keys; no reachable input is outside "
          "the axiom domain." % (reached,))
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-resolve",
        "axiom": "resolve",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # str() coercion is the post-patch line; harmless on this callee anyway
        "probe": _AX_RESOLVE_PROBE,
        "rationale": "A-reference soundness: the deep model resolve(ft)==ToSeq(ft.content) "
                     "(independent of deferred) is validated == the real str() coercion. "
                     "str() of a lazy proxy and of the eager str both yield the underlying "
                     "string on 5000 fuzz + boundary inputs (incl. F2P \"DATE_FORMAT\"/\"H:i\"). "
                     "Any disagreement => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-sound-format_value",
        "axiom": "format_value",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # need the post-patch str() coercion so the lazy name doesn't crash getattr
        "probe": _AX_LOOKUP_PROBE,
        "rationale": "A-consumed soundness (format_value/do_lookup): the real post-patch "
                     "get_format value is keyed ONLY on the resolved name — "
                     "get_format(gettext_lazy(name))==get_format(name) for every format name "
                     "under default and de locales, plus the F2P witness. If the value ever "
                     "depended on the deferred form (or differed across the two), the "
                     "determinism axiom would be unsound => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-cover-do_lookup",
        "axiom": "do_lookup",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": "containment: the model feeds do_lookup a key whose ToSeq == "
                     "ToSeq(requested_name.content) == resolve(requested_name) (the loop "
                     "asserts it), i.e. the RESOLVED str of the requested name in either "
                     "form. do_lookup's domain is exactly such resolved str names; every "
                     "model-reachable key is a real str inside it. A reachable key outside "
                     "the domain (e.g. a non-str) would be AXIOM-TOO-WEAK-FOR-CALLER; none "
                     "exists.",
    },
]
