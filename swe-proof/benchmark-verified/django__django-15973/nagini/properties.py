"""PBT falsification battery for django__django-15973.

Adversarial, instance-specific. The defended surface of `through_dependency`:

  Inputs (BOTH read-only at Acc(list_pred(x), 1/2)):
    primary_ref  -- the field's PRIMARY related reference (remote_field_model)
    through_ref  -- the INTERMEDIARY reference (field.remote_field.through)
  Precondition: dot_index(ToSeq(through_ref), 0) < len(through_ref)
                (the intermediary "app.Object" token carries a dot)
  Load-bearing postcondition (the single behavioural delta the patch makes):
    ToSeq(Result()[0]) == ref_app(ToSeq(through_ref))    # app label of THROUGH
    ToSeq(Result()[1]) == ref_name(ToSeq(through_ref))   # name of THROUGH, lowered
  plus the frame: Acc(list_pred(primary_ref),1/2) and Acc(list_pred(through_ref),1/2)
  are RE-ENSURED (neither input may be mutated).

The oracle (ref_app / ref_name) is GROUNDED in the input through_ref: both are
@Pure helpers built from dot_index + the lowered fold, fully unfolded over the
code points of through_ref. There is NO opaque answer-key marker to echo, so
there is no ungrounded-oracle-echo attack (see 'assessment'); instead the
weak-spec surface is PARTIAL-DOMAIN: an impl that resolves the WRONG reference
(the pre-patch bug: primary_ref instead of through_ref) agrees with the gold on
the sub-domain where the two references resolve identically and diverges
elsewhere. The frame surface is the two read-only inputs (frame-mutation
MANDATORY).

Region surgery: every variant is built by editing ONLY text inside
# impl-start / # impl-end, so the frozen spec (axioms/pure/pre/post) is never
touched and same_spec holds by construction.
"""
from pathlib import Path

INSTANCE = "django__django-15973"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The entire gold impl region body (lines between # impl-start / # impl-end).
# We rebuild whole impls by replacing this block so each variant is unambiguous.
_GOLD_IMPL = '''    app = []  # type: List[int]
    name = []  # type: List[int]
    # locate the first dot of the intermediary reference
    d = 0
    while d < len(through_ref) and through_ref[d] != 46:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(0 <= d and d <= len(through_ref))
        # the reference carries a dot (a stable fact about the unchanged input)
        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
        # scanning past non-dots does not change the first-dot index
        Invariant(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), 0))
        # Termination: the guard's FIRST conjunct `d < len(through_ref)` alone
        # bounds the scan -- `d` rises by exactly 1 per pass and
        # `len(through_ref)` is fixed (the input is only read), so
        # `len(through_ref) - d + 1` strictly decreases and is >= 2 at every
        # loop head. The second conjunct `through_ref[d] != 46` can only make
        # the loop exit sooner, so it cannot invalidate the bound.
        Invariant(MustTerminate(len(through_ref) - d + 1))
        # invariants-end
        # ref[d] != 46, so the first dot from d equals the first dot from d+1
        Assert(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), d + 1))
        d = d + 1
    # at exit either d == len(through_ref) or through_ref[d] == 46; both give
    # dot_index(.., d) == d, hence the first dot index is d
    Assert(dot_index(ToSeq(through_ref), d) == d)
    Assert(d == dot_index(ToSeq(through_ref), 0))
    # app label: prefix before the dot (verbatim)
    j = 0
    while j < d:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(Acc(list_pred(app)))
        Invariant(d == dot_index(ToSeq(through_ref), 0))
        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
        Invariant(0 <= j and j <= d)
        Invariant(ToSeq(app) == ToSeq(through_ref).take(d).take(j))
        # Termination: `j` rises by exactly 1 per pass and `d` is fixed inside
        # this loop, so `d - j + 1` strictly decreases; the guard `j < d` makes
        # it >= 2 at every loop head.
        Invariant(MustTerminate(d - j + 1))
        # invariants-end
        Assert(ToSeq(through_ref).take(d)[j] == through_ref[j])
        app = app + [through_ref[j]]
        Assert(ToSeq(app) == ToSeq(through_ref).take(d).take(j + 1))
        j = j + 1
    Assert(ToSeq(app) == ToSeq(through_ref).take(d))
    # the app label equals the deep-model resolver's app projection
    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
    Assert(d == dot_index(ToSeq(through_ref), 0))
    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
    # object name: lower-cased suffix after the dot
    Assert(dot_index(ToSeq(through_ref), 0) < len(through_ref))
    Assert(d == dot_index(ToSeq(through_ref), 0))
    Assert(d < len(through_ref))
    k = len(through_ref)
    while k > d + 1:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(Acc(list_pred(app)))
        Invariant(d == dot_index(ToSeq(through_ref), 0))
        # the app label, fully built, equals the resolver's app projection
        Invariant(ToSeq(app) == ref_app(ToSeq(through_ref)))
        Invariant(d + 1 <= k and k <= len(through_ref))
        Invariant(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1))))
        # Termination: `k` falls by exactly 1 per pass down towards the fixed
        # floor `d + 1`, so `k - d` strictly decreases; the guard `k > d + 1`
        # makes it >= 2 at every loop head.
        Invariant(MustTerminate(k - d))
        # invariants-end
        c = through_ref[k - 1]
        Assert(ToSeq(through_ref).drop(d + 1)[k - (d + 1) - 1] == c)
        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
               == ToSeq(through_ref).drop(d + 1).drop(k - (d + 1)))
        name = [lower_cp(c)] + name
        k = k - 1
    Assert(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1)))
    # connect the spelled-out parts to the deep-model reference resolver
    Assert(d == dot_index(ToSeq(through_ref), 0))
    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
    Assert(ref_name(ToSeq(through_ref)) == lowered(ToSeq(through_ref).drop(dot_index(ToSeq(through_ref), 0) + 1)))
    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
    Assert(ToSeq(name) == ref_name(ToSeq(through_ref)))
    res = (app, name)  # type: Tuple[List[int], List[int]]
    Assert(ToSeq(res[0]) == ref_app(ToSeq(through_ref)))
    Assert(ToSeq(res[1]) == ref_name(ToSeq(through_ref)))
    return res'''

# sanity: the gold impl block is present verbatim and unique in model.py
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block drifted from model.py"


def _with_impl(new_impl_body: str) -> str:
    """Return model.py with the gold impl body replaced by new_impl_body
    (edits stay strictly inside # impl-start / # impl-end)."""
    return _swap(_BASE, _GOLD_IMPL, new_impl_body)


# ---------------------------------------------------------------------------
# (1) POSITIVE CONTROL (soundness) — structurally-different CORRECT impl.
# Local-variable reshape: in the app-prefix loop, read through_ref[j] into a
# local `ch` before appending, and pin every gold framing assert verbatim. This
# is a genuine executable-shape change (an extra binding + a redundant equality
# pin) that keeps the gold proof valid. NOT a loop-direction flip (caution #3:
# forward-append against the front-recursive `lowered` fold would need a
# distribution lemma; we keep the gold suffix loop backward, untouched).
# If a faithful correct impl could not verify => SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS = _GOLD_IMPL.replace(
    """        Assert(ToSeq(through_ref).take(d)[j] == through_ref[j])
        app = app + [through_ref[j]]
        Assert(ToSeq(app) == ToSeq(through_ref).take(d).take(j + 1))""",
    """        Assert(ToSeq(through_ref).take(d)[j] == through_ref[j])
        ch = through_ref[j]  # local-variable reshape (read before append)
        Assert(ch == through_ref[j])
        app = app + [ch]
        Assert(ch == ToSeq(through_ref).take(d)[j])
        Assert(ToSeq(app) == ToSeq(through_ref).take(d).take(j + 1))""",
)
assert _POS != _GOLD_IMPL, "positive-control reshape did not apply"

# ---------------------------------------------------------------------------
# (2) ADMISSIBILITY — the precondition admits a normal F2P-shaped input AND
# both half-permission inputs are usable. The gold impl already reads through_ref
# under Acc(...,1/2) and returns satisfying the postcondition; we additionally
# READ primary_ref (the otherwise-unused half-permission input) to witness its
# permission is consumable, and pin that the dot precondition + len>0 it implies
# hold for the input the body runs on. If the Requires were over-strong/vacuous
# the body could not consume both half-permissions and reach a normal return
# => PRECOND-TOO-STRONG.
# ---------------------------------------------------------------------------
_ADMISS = _GOLD_IMPL.replace(
    "    app = []  # type: List[int]\n    name = []  # type: List[int]\n",
    "    app = []  # type: List[int]\n    name = []  # type: List[int]\n"
    "    # admissibility witness: primary_ref's half-permission is usable\n"
    "    Assert(len(primary_ref) >= 0)\n"
    "    # the dot precondition implies through_ref is non-empty (a normal token)\n"
    "    Assert(dot_index(ToSeq(through_ref), 0) < len(through_ref))\n"
    "    Assert(0 < len(through_ref))\n",
    1,
)
assert _ADMISS != _GOLD_IMPL, "admissibility witness did not apply"

# ---------------------------------------------------------------------------
# (3) FRAME-MUTATION (MANDATORY, reject) — write to the read-only through_ref.
# The precondition guarantees dot_index(through_ref,0) < len(through_ref), so
# len(through_ref) > 0 and through_ref[0] is in-bounds. A VALUE-NEUTRAL write
# through_ref[0] = through_ref[0] is well-typed but needs FULL permission;
# only Acc(list_pred(through_ref), 1/2) is held => Nagini rejects for
# INSUFFICIENT PERMISSION. Every gold invariant/assert is kept verbatim so the
# rejection is attributable to the write, not to a spec change.
# Refinement: writing to the field's `through` reference token corresponds to
# MUTATING field.remote_field.through in place. The real autodetector never
# rewrites the field's through string; a patch that mutated it would corrupt
# shared field state used by other dependency computations and the CreateModel
# operations, breaking the P2P "through model" tests (e.g. the existing
# test_create_with_through_model) — it would NOT resolve the F2P/P2P.
# ---------------------------------------------------------------------------
_FRAME = _GOLD_IMPL.replace(
    "    app = []  # type: List[int]\n    name = []  # type: List[int]\n",
    "    app = []  # type: List[int]\n    name = []  # type: List[int]\n"
    "    # FRAME-MUTATION PROBE: write to the read-only input through_ref.\n"
    "    if 0 < len(through_ref):\n"
    "        through_ref[0] = through_ref[0]  # value-neutral, needs FULL perm\n",
    1,
)
assert _FRAME != _GOLD_IMPL, "frame-mutation write did not apply"

# ---------------------------------------------------------------------------
# (4) PARTIAL-DOMAIN (reject) — the PRE-PATCH BUG: resolve primary_ref instead
# of through_ref. This is the canonical wrong impl (model_prepatch.py reproduces
# it). It builds (ref_app(primary_ref), ref_name(primary_ref)); the postcondition
# demands (ref_app(through_ref), ref_name(through_ref)). It agrees with the gold
# only on the sub-domain where the two references resolve identically (same app
# label AND same lowered name) and diverges otherwise.
# Refinement: this IS the pre-patch behaviour the issue reports. On the F2P
# test_create_with_through_model_separate_apps the through model
# `contract.Contract` lives in a DIFFERENT app from the target `testapp.Publisher`,
# so the intermediary dependency would point at the wrong app and the
# assertMigrationDependencies set {(authors,..),(contract,..),(testapp,..)}
# would be wrong => the F2P would NOT pass.
# ---------------------------------------------------------------------------
_PARTIAL = '''    app = []  # type: List[int]
    name = []  # type: List[int]
    # WRONG: resolve the PRIMARY reference (pre-patch bug), not the intermediary.
    d = 0
    while d < len(primary_ref) and primary_ref[d] != 46:
        # invariants-start
        Invariant(Acc(list_pred(primary_ref), 1 / 2))
        Invariant(0 <= d and d <= len(primary_ref))
        Invariant(dot_index(ToSeq(primary_ref), d) == dot_index(ToSeq(primary_ref), 0))
        # Termination: the guard's FIRST conjunct `d < len(primary_ref)` alone
        # bounds the scan -- `d` rises by exactly 1 per pass and
        # `len(primary_ref)` is fixed, so `len(primary_ref) - d + 1` strictly
        # decreases and is >= 2 at every loop head. The second conjunct
        # `primary_ref[d] != 46` can only make the loop exit sooner.
        Invariant(MustTerminate(len(primary_ref) - d + 1))
        # invariants-end
        Assert(dot_index(ToSeq(primary_ref), d) == dot_index(ToSeq(primary_ref), d + 1))
        d = d + 1
    Assert(dot_index(ToSeq(primary_ref), d) == d)
    Assert(d == dot_index(ToSeq(primary_ref), 0))
    j = 0
    while j < d:
        # invariants-start
        Invariant(Acc(list_pred(primary_ref), 1 / 2))
        Invariant(Acc(list_pred(app)))
        Invariant(d == dot_index(ToSeq(primary_ref), 0))
        Invariant(0 <= j and j <= d)
        Invariant(ToSeq(app) == ToSeq(primary_ref).take(d).take(j))
        # Termination: `j` rises by exactly 1 per pass and `d` is fixed inside
        # this loop, so `d - j + 1` strictly decreases; the guard `j < d` makes
        # it >= 2 at every loop head.
        Invariant(MustTerminate(d - j + 1))
        # invariants-end
        Assert(ToSeq(primary_ref).take(d)[j] == primary_ref[j])
        app = app + [primary_ref[j]]
        Assert(ToSeq(app) == ToSeq(primary_ref).take(d).take(j + 1))
        j = j + 1
    Assert(ToSeq(app) == ToSeq(primary_ref).take(d))
    Assert(ref_app(ToSeq(primary_ref)) == ToSeq(primary_ref).take(dot_index(ToSeq(primary_ref), 0)))
    Assert(ToSeq(app) == ref_app(ToSeq(primary_ref)))
    if d < len(primary_ref):
        k = len(primary_ref)
        while k > d + 1:
            # invariants-start
            Invariant(Acc(list_pred(primary_ref), 1 / 2))
            Invariant(Acc(list_pred(name)))
            Invariant(Acc(list_pred(app)))
            Invariant(d == dot_index(ToSeq(primary_ref), 0))
            Invariant(ToSeq(app) == ref_app(ToSeq(primary_ref)))
            Invariant(d + 1 <= k and k <= len(primary_ref))
            Invariant(ToSeq(name) == lowered(ToSeq(primary_ref).drop(d + 1).drop(k - (d + 1))))
            # Termination: `k` falls by exactly 1 per pass down towards the
            # fixed floor `d + 1`, so `k - d` strictly decreases; the guard
            # `k > d + 1` makes it >= 2 at every loop head.
            Invariant(MustTerminate(k - d))
            # invariants-end
            c = primary_ref[k - 1]
            Assert(ToSeq(primary_ref).drop(d + 1)[k - (d + 1) - 1] == c)
            Assert(ToSeq(primary_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
            Assert(ToSeq(primary_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
                   == ToSeq(primary_ref).drop(d + 1).drop(k - (d + 1)))
            name = [lower_cp(c)] + name
            k = k - 1
        Assert(ToSeq(name) == lowered(ToSeq(primary_ref).drop(d + 1)))
        Assert(ToSeq(name) == ref_name(ToSeq(primary_ref)))
    res = (app, name)  # type: Tuple[List[int], List[int]]
    return res'''
assert _PARTIAL != _GOLD_IMPL

# ---------------------------------------------------------------------------
# (5) PARTIAL-DOMAIN, app-only mix (reject) — resolve the app label from the
# PRIMARY reference but the object name (correctly) from through_ref. Agrees
# with the gold whenever the two references share an app label; diverges only on
# the app-label component. A subtler near-miss than the full pre-patch bug.
# Refinement: the F2P separate-apps case has through=`contract.Contract` whose
# app `contract` differs from the primary `testapp.Publisher`'s `testapp`, so
# the dependency's app_label would be wrong and the dependency SET would not
# match => F2P would NOT pass. This rival pins only PART of the postcondition's
# domain (the name half), leaving the app half wrong.
# ---------------------------------------------------------------------------
_PARTIAL_APP = '''    app = []  # type: List[int]
    name = []  # type: List[int]
    # app label from the WRONG (primary) reference; name from the right one.
    da = 0
    while da < len(primary_ref) and primary_ref[da] != 46:
        # invariants-start
        Invariant(Acc(list_pred(primary_ref), 1 / 2))
        Invariant(0 <= da and da <= len(primary_ref))
        Invariant(dot_index(ToSeq(primary_ref), da) == dot_index(ToSeq(primary_ref), 0))
        # Termination: the guard's FIRST conjunct `da < len(primary_ref)` alone
        # bounds the scan -- `da` rises by exactly 1 per pass and
        # `len(primary_ref)` is fixed, so `len(primary_ref) - da + 1` strictly
        # decreases and is >= 2 at every loop head; `primary_ref[da] != 46` can
        # only make the loop exit sooner.
        Invariant(MustTerminate(len(primary_ref) - da + 1))
        # invariants-end
        Assert(dot_index(ToSeq(primary_ref), da) == dot_index(ToSeq(primary_ref), da + 1))
        da = da + 1
    Assert(dot_index(ToSeq(primary_ref), da) == da)
    Assert(da == dot_index(ToSeq(primary_ref), 0))
    ja = 0
    while ja < da:
        # invariants-start
        Invariant(Acc(list_pred(primary_ref), 1 / 2))
        Invariant(Acc(list_pred(app)))
        Invariant(da == dot_index(ToSeq(primary_ref), 0))
        Invariant(0 <= ja and ja <= da)
        Invariant(ToSeq(app) == ToSeq(primary_ref).take(da).take(ja))
        # Termination: `ja` rises by exactly 1 per pass and `da` is fixed, so
        # `da - ja + 1` strictly decreases; the guard `ja < da` makes it >= 2.
        Invariant(MustTerminate(da - ja + 1))
        # invariants-end
        Assert(ToSeq(primary_ref).take(da)[ja] == primary_ref[ja])
        app = app + [primary_ref[ja]]
        Assert(ToSeq(app) == ToSeq(primary_ref).take(da).take(ja + 1))
        ja = ja + 1
    Assert(ToSeq(app) == ToSeq(primary_ref).take(da))
    Assert(ref_app(ToSeq(primary_ref)) == ToSeq(primary_ref).take(dot_index(ToSeq(primary_ref), 0)))
    Assert(ToSeq(app) == ref_app(ToSeq(primary_ref)))
    # object name: correctly from through_ref (backward suffix scan)
    d = 0
    while d < len(through_ref) and through_ref[d] != 46:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(0 <= d and d <= len(through_ref))
        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
        Invariant(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), 0))
        # Termination: the guard's FIRST conjunct `d < len(through_ref)` alone
        # bounds the scan -- `d` rises by exactly 1 per pass and
        # `len(through_ref)` is fixed (the input is only read), so
        # `len(through_ref) - d + 1` strictly decreases and is >= 2 at every
        # loop head. The second conjunct `through_ref[d] != 46` can only make
        # the loop exit sooner, so it cannot invalidate the bound.
        Invariant(MustTerminate(len(through_ref) - d + 1))
        # invariants-end
        Assert(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), d + 1))
        d = d + 1
    Assert(dot_index(ToSeq(through_ref), d) == d)
    Assert(d == dot_index(ToSeq(through_ref), 0))
    Assert(d < len(through_ref))
    k = len(through_ref)
    while k > d + 1:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(Acc(list_pred(app)))
        Invariant(d == dot_index(ToSeq(through_ref), 0))
        Invariant(d + 1 <= k and k <= len(through_ref))
        Invariant(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1))))
        # Termination: `k` falls by exactly 1 per pass down towards the fixed
        # floor `d + 1`, so `k - d` strictly decreases; the guard `k > d + 1`
        # makes it >= 2 at every loop head.
        Invariant(MustTerminate(k - d))
        # invariants-end
        c = through_ref[k - 1]
        Assert(ToSeq(through_ref).drop(d + 1)[k - (d + 1) - 1] == c)
        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
               == ToSeq(through_ref).drop(d + 1).drop(k - (d + 1)))
        name = [lower_cp(c)] + name
        k = k - 1
    Assert(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1)))
    Assert(ToSeq(name) == ref_name(ToSeq(through_ref)))
    res = (app, name)  # type: Tuple[List[int], List[int]]
    return res'''
assert _PARTIAL_APP != _GOLD_IMPL

# ---------------------------------------------------------------------------
# (6) PARTIAL-DOMAIN, no-lowercase echo (reject) — resolve through_ref but skip
# the case fold on the object name (return the suffix verbatim). Agrees with the
# gold whenever the object-name suffix is already all-lowercase (no cased
# letters) and diverges when it has an uppercase letter.
# Refinement: every real F2P/P2P through reference is a CamelCase model name
# (`contract.Contract`, `fonte_variavel.FonteVariavelModel`); the resolver
# lower-cases the object name (utils.py:44 model_name.lower()). An impl that
# skipped .lower() would emit `Contract`/`FonteVariavelModel` where Django emits
# `contract`/`fontevariavelmodel`, so the dependency object_name would mismatch
# and the F2P would NOT pass. This rival pins the value on the all-lowercase
# sub-domain only.
# ---------------------------------------------------------------------------
_NO_LOWER = _GOLD_IMPL.replace(
    "        name = [lower_cp(c)] + name",
    "        name = [c] + name  # WRONG: object name not lower-cased",
).replace(
    "    Assert(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1)))",
    "    # (no-lowercase rival: the lowered() pin no longer holds)",
)
assert _NO_LOWER != _GOLD_IMPL

# ---------------------------------------------------------------------------
# (7) PARTIAL-DOMAIN, split-on-last-dot (reject, supporting near-miss) — split
# the through reference on the LAST dot instead of the FIRST. Agrees with the
# gold for single-dot tokens and diverges for multi-dot tokens.
# Refinement: resolve_relation uses model.split(".", 1) — split on the FIRST dot
# (utils.py:43); a last-dot split would put the wrong text in the app label /
# object name for multi-segment references. On single-dot references it would
# coincide, but the spec must pin the first-dot semantics for the resolver to be
# faithful; an impl that split last would diverge from the real callee on any
# multi-dot reference and would not be a faithful resolve_relation. Supporting
# near-miss with a real refinement (it still encodes the wrong split rule).
# ---------------------------------------------------------------------------
# Implemented as: scan for the LAST dot (backward) for the dot index `d`.
_LAST_DOT = '''    app = []  # type: List[int]
    name = []  # type: List[int]
    # WRONG split point: scan for the LAST dot instead of the first.
    d = len(through_ref)
    while d > 0 and through_ref[d - 1] != 46:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(0 <= d and d <= len(through_ref))
        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
        # Termination: `d` falls by exactly 1 per pass towards the fixed floor
        # 0, so `d + 1` strictly decreases; the guard's first conjunct `d > 0`
        # makes it >= 2 at every loop head, and `through_ref[d - 1] != 46` can
        # only make the loop exit sooner.
        Invariant(MustTerminate(d + 1))
        # invariants-end
        d = d - 1
    # d now points just past the last dot (or 0); reuse the gold app/name loops
    # against this (wrong) split point. We do NOT attempt to pin the gold
    # postcondition asserts (they would not hold for a last-dot split).
    j = 0
    while j < d:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(Acc(list_pred(app)))
        Invariant(0 <= j and j <= d)
        Invariant(d <= len(through_ref))
        # Termination: `j` rises by exactly 1 per pass and `d` is fixed, so
        # `d - j + 1` strictly decreases; the guard `j < d` makes it >= 2.
        Invariant(MustTerminate(d - j + 1))
        # invariants-end
        app = app + [through_ref[j]]
        j = j + 1
    k = len(through_ref)
    while k > d:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(0 <= d and d <= k and k <= len(through_ref))
        # Termination: `k` falls by exactly 1 per pass towards the fixed floor
        # `d`, so `k - d + 1` strictly decreases; the guard `k > d` makes it
        # >= 2 at every loop head.
        Invariant(MustTerminate(k - d + 1))
        # invariants-end
        c = through_ref[k - 1]
        name = [lower_cp(c)] + name
        k = k - 1
    res = (app, name)  # type: Tuple[List[int], List[int]]
    return res'''
assert _LAST_DOT != _GOLD_IMPL


SPEC_TESTS = [
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS),
        "rationale": "structurally-different CORRECT impl (read through_ref[j] "
                     "into a local `ch` before append, plus a redundant equality "
                     "pin). Keeps every gold framing assert/invariant verbatim so "
                     "the gold proof stays valid. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISS),
        "rationale": "the precondition (dot in through_ref) admits a normal "
                     "F2P-shaped input and BOTH half-permission inputs are usable: "
                     "the body reads primary_ref (Acc 1/2) and reaches a normal "
                     "return satisfying the postcondition. If it failed => "
                     "PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutate-through-ref",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_FRAME),
        "refinement": "writing through_ref[0] models mutating "
                      "field.remote_field.through in place. The real autodetector "
                      "never rewrites the field's through token; a patch that did "
                      "would corrupt shared field state used by the FK-target "
                      "dependency and the CreateModel ops, breaking the existing "
                      "through-model tests (test_create_with_through_model and the "
                      "F2P) — it would NOT resolve.",
        "rationale": "through_ref is held at Acc(list_pred(through_ref), 1/2); a "
                     "write needs FULL permission. Nagini must reject for "
                     "INSUFFICIENT PERMISSION (the frame/permission system). If it "
                     "verified, the read-only frame would be unenforced.",
    },
    {
        "id": "wrong-ref-primary-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL),
        "refinement": "this is the PRE-PATCH bug verbatim: resolve primary_ref "
                      "instead of through_ref. On the F2P "
                      "test_create_with_through_model_separate_apps the through "
                      "model `contract.Contract` is in a different app from the "
                      "primary `testapp.Publisher`, so the intermediary dependency "
                      "points at the wrong app and the dependency set "
                      "{(authors..),(contract..),(testapp..)} is wrong => the F2P "
                      "does NOT pass (this is exactly what the patch fixes).",
        "rationale": "the postcondition pins Result to "
                     "ref_app/ref_name(ToSeq(through_ref)); an impl returning "
                     "ref_app/ref_name(ToSeq(primary_ref)) only matches when the "
                     "two references resolve identically (partial domain). Must be "
                     "rejected, else SPEC-TOO-WEAK.",
    },
    {
        "id": "wrong-app-from-primary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_APP),
        "refinement": "app label taken from primary_ref, object name correctly "
                      "from through_ref. On the separate-apps F2P the app label "
                      "would be `testapp` (primary) instead of `contract` "
                      "(through), so the dependency app would be wrong and the "
                      "assertMigrationDependencies set would not match => F2P "
                      "does NOT pass. Subtler than the full pre-patch bug: only the "
                      "app component is wrong.",
        "rationale": "the postcondition clause ToSeq(Result()[0]) == "
                     "ref_app(ToSeq(through_ref)) is violated whenever the two "
                     "references' app labels differ. Must be rejected, else the "
                     "app-label half of the spec would be too weak.",
    },
    {
        "id": "no-lowercase-objname",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_NO_LOWER),
        "refinement": "object name returned verbatim (no case fold). The resolver "
                      "lower-cases the object name (utils.py:44). All F2P/P2P "
                      "through references are CamelCase model names "
                      "(`contract.Contract`), so this rival would emit `Contract` "
                      "where Django emits `contract`, mismatching the dependency "
                      "object_name => F2P does NOT pass. Coincides only on the "
                      "all-lowercase sub-domain.",
        "rationale": "violates ToSeq(Result()[1]) == ref_name(ToSeq(through_ref)) "
                     "(ref_name applies the lowered fold) on any name with a cased "
                     "letter. Must be rejected, else the case-fold clause is too "
                     "weak.",
    },
    {
        "id": "split-on-last-dot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_LAST_DOT),
        "refinement": "split the through reference on the LAST dot instead of the "
                      "first. resolve_relation uses model.split('.', 1) — the FIRST "
                      "dot (utils.py:43). For a multi-dot reference (e.g. an app "
                      "with a dotted name) the app label / object name would be "
                      "wrong, diverging from the real resolver; the spec must pin "
                      "first-dot semantics. Supporting near-miss carrying a real "
                      "refinement (it encodes the wrong split rule).",
        "rationale": "with a last-dot split point, ToSeq(app) != "
                     "ref_app(ToSeq(through_ref)) for multi-dot tokens, so the "
                     "postcondition (pinned to dot_index = FIRST dot) is violated. "
                     "Must be rejected, else first-dot semantics is under-pinned.",
    },
]

# No @ContractOnly axioms are consumed (meta.json axioms == []). The only callee
# is resolve_relation, modeled as an A-reference deep model (ref_app/ref_name)
# and validated == the real callee out-of-band by axiom_check.py / G-AX. G-AX is
# its own gate; the PBT axiom lane is therefore vacuous here.
AXIOM_TESTS = []
