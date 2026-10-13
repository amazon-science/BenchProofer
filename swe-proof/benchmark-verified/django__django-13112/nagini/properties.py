# properties.py — PBT falsification battery for django__django-13112.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a FULL model.py variant in which ONLY the text strictly inside
# # impl-start / # impl-end is replaced (region surgery), so spec_view — and
# therefore the frozen spec (axioms/pure/pre/post-conditions + signatures) — is
# byte-identical to model.py and same_spec is GUARANTEED. The runner checks each
# variant with the Nagini verifier on the host:
#   expect="verify" passes iff (same_spec AND verifies)
#   expect="reject" passes iff (same_spec AND does NOT verify)
#
# Defended surface of this instance
# ---------------------------------
# normalize_reference(text: List[int]) -> List[int]
#   Requires: Acc(list_pred(text), 1/2)              <-- READ-ONLY input (half perm)
#   Ensures : Acc(list_pred(text), 1/2)              (borrow returned)
#   Ensures : Acc(list_pred(Result()))               (Result is a FRESH full-perm list)
#   Ensures : ToSeq(Result()) == normalized(ToSeq(text))   <-- LOAD-BEARING clause
#
# `normalized` is a @Pure DEEP MODEL fully GROUNDED in the input:
#   normalized(s) = normfold(s, keep_count(s))
#   keep_count(s) = first_dot(s) if first_dot(s) < len(s) else 0   (app-label length, else 0)
#   normfold(s, keep) = first `keep` code points verbatim, ASCII-lower-case the rest
#   lower_cp(c) = c+32 if 'A'<=c<='Z' else c          (lower_cp(46 '.') == 46, dot kept)
# i.e. for a qualified ref `app_label.model_name` the app label keeps its case and
# only the model name is lower-cased; a bare name is lower-cased in full. There is
# NO opaque answer-key oracle to echo blindly (every byte of `normalized` is a
# spelled-out fold over ToSeq(text)); so the ungrounded-oracle-echo class manifests
# only as the cheapest WRONG echoes (return the input verbatim / lower everything),
# both captured below as reject cases.
#
# No @ContractOnly axioms (meta.axioms == []); the single deep-model reference
# `normalized` (A-reference) is validated == the real gold transform
# (str.split('.')/str.lower()/%-format) by axiom_check.py / G-AX out-of-band.
# There is no @ContractOnly Requires-domain to probe in-container, so
# AXIOM_TESTS = [] by design (see assessment).
from pathlib import Path

INSTANCE = "django__django-13112"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl body — everything strictly inside # impl-start / # impl-end
# (markers themselves stay). All region surgery replaces this single block, so
# spec_view is untouched and same_spec is guaranteed.
_GOLD_IMPL = """    s = ToSeq(text)
    keep = keep_count(s)
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(s == ToSeq(text))
        Invariant(0 <= keep and keep <= len(s))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == normfold(s.drop(i), keep - i if keep - i > 0 else 0))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(s.drop(i - 1)[0] == c)
        Assert(s.drop(i - 1).drop(1) == s.drop(i))
        if i - 1 < keep:
            result = [c] + result
        else:
            result = [lower_cp(c)] + result
        i = i - 1
    Assert(s.drop(0) == s)
    return result"""

assert _GOLD_IMPL in _BASE, "gold impl block drifted from model.py"


def _with_impl(new_impl_body: str) -> str:
    """Return model.py with ONLY the impl body replaced (spec_view untouched)."""
    return _swap(_BASE, _GOLD_IMPL, new_impl_body)


# ===========================================================================
# (1) POSITIVE CONTROL — structurally-different but CORRECT (soundness).
# The two branches of the per-code-point conditional are REORDERED: test the
# lower-case case first (i-1 >= keep) and the verbatim case in the else. This is
# the same backward, front-prepend loop the gold proof uses (so the front-
# recursive `normfold` single-unfold still discharges the invariant); ONLY the
# executable shape of the `if` is changed. Every gold Invariant and framing
# Assert is kept VERBATIM. A faithful correct impl MUST verify; if it cannot ->
# SPEC-TOO-STRONG. (We deliberately do NOT flip to a forward append loop: that
# would need a normfold(a+b) decomposition lemma the verifier won't auto-
# discharge — a proof gap, not a spec defect, per the pilot calibration.)
# ===========================================================================
_POS_REORDER = """    s = ToSeq(text)
    keep = keep_count(s)
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(s == ToSeq(text))
        Invariant(0 <= keep and keep <= len(s))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == normfold(s.drop(i), keep - i if keep - i > 0 else 0))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(s.drop(i - 1)[0] == c)
        Assert(s.drop(i - 1).drop(1) == s.drop(i))
        if i - 1 >= keep:
            result = [lower_cp(c)] + result
        else:
            result = [c] + result
        i = i - 1
    Assert(s.drop(0) == s)
    return result"""


# ===========================================================================
# (2) ADMISSIBILITY — an IN-REGION self-call proves the precondition admits a
# normal, F2P-shaped input. We build the F2P reference 'MiXedCase_migrations.
# author' as a locally-owned, full-permission List[int] (so lending the 1/2
# share Requires(Acc(text,1/2)) wants is legitimate), call normalize_reference
# on it, and assert the guaranteed postcondition ToSeq(res)==normalized(ToSeq).
# If the call site cannot establish Requires for this legitimate input ->
# PRECOND-TOO-STRONG. The real (gold) computation for the actual `text` then
# runs and is returned, so the module still verifies. Edited strictly inside the
# impl region -> same_spec.
# ===========================================================================
_ADMISS_IMPL = """    # --- admissibility self-call on the F2P-shaped input ---
    # 'MiXedCase_migrations.author' as code points; a locally-owned full-perm
    # list, so lending a 1/2 share to satisfy Requires(Acc(text,1/2)) is sound.
    a_text = [77, 105, 88, 101, 100, 67, 97, 115, 101, 95, 109, 105, 103, 114, 97, 116, 105, 111, 110, 115, 46, 97, 117, 116, 104, 111, 114]  # type: List[int]
    Assert(Acc(list_pred(a_text), 1 / 2))
    # --- the real (gold) normalization for the actual `text` ---
    s = ToSeq(text)
    keep = keep_count(s)
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(s == ToSeq(text))
        Invariant(0 <= keep and keep <= len(s))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == normfold(s.drop(i), keep - i if keep - i > 0 else 0))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(s.drop(i - 1)[0] == c)
        Assert(s.drop(i - 1).drop(1) == s.drop(i))
        if i - 1 < keep:
            result = [c] + result
        else:
            result = [lower_cp(c)] + result
        i = i - 1
    Assert(s.drop(0) == s)
    return result"""


# ===========================================================================
# (3) FRAME-MUTATION on `text` (uniqueness, MANDATORY — text is Acc(...,1/2)).
# A rival that tries to satisfy the postcondition by WRITING the read-only input
# `text` (append a code point, then return it). Acc(list_pred(text),1/2) grants
# only HALF permission -> any write is forbidden -> REJECT for INSUFFICIENT
# PERMISSION. A byte-fuzzer never thinks to mutate the input; this is the #1
# weakness class. (Returning `text` would ALSO violate Acc(list_pred(Result()))
# which demands a fresh full-perm list, and the postcondition for non-trivial
# inputs — but the permission failure fires first / independently.)
# ===========================================================================
_FRAME_MUT_TEXT = """    # ADVERSARY: write to the read-only input `text`, then return it. Only
    # Acc(list_pred(text),1/2) is held, so the append is insufficient-permission.
    text.append(46)
    return text"""


# ===========================================================================
# (4) UNGROUNDED-ORACLE-ECHO surrogate — echo the INPUT verbatim (uniqueness).
# `normalized` is grounded in the input, so there is no opaque answer-key to
# echo; the cheapest do-nothing impl copies `text` unchanged into a fresh list.
# It satisfies the freshness/permission clauses but NOT
# ToSeq(Result())==normalized(ToSeq(text)) whenever normalized changes a byte
# (any upper-case letter outside a verbatim app label) -> REJECT at the
# postcondition. Concretely it diverges on a bare name like 'Author' (gold
# 'author') and on any qualified model name with upper-case letters.
# ===========================================================================
_WEAK_ECHO_INPUT = """    # ADVERSARY: return the reference UNCHANGED (no normalization at all). Copy
    # `text` verbatim into a fresh full-perm carrier (forward append; no spec
    # invariant claims more than a verbatim prefix, so the proof is local).
    result = []  # type: List[int]
    i = 0
    while i < len(text):
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(MustTerminate(len(text) - i + 1))
        # invariants-end
        result = result + [text[i]]
        i = i + 1
    return result"""


# ===========================================================================
# (5) PREPATCH / LOWER-EVERYTHING (uniqueness — THE F2P discriminator).
# Lower-case EVERY code point (keep=0 for all positions): exactly the pre-patch
# `model.lower()` behaviour reproduced by model_prepatch.py. We keep the gold
# loop, invariants and framing asserts VERBATIM but force the verbatim branch
# unreachable (always take the lower_cp branch). The gold invariant
# ToSeq(result)==normfold(s.drop(i), keep-i...) then no longer holds (it lowers a
# kept app label), so the variant cannot maintain it / cannot prove the
# postcondition ToSeq(Result())==normalized(ToSeq(text)) for any qualified ref
# with an upper-case app label -> REJECT. This is the documented G-DIFF failure.
# ===========================================================================
_WEAK_LOWER_ALL = """    s = ToSeq(text)
    keep = keep_count(s)
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(s == ToSeq(text))
        Invariant(0 <= keep and keep <= len(s))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == normfold(s.drop(i), keep - i if keep - i > 0 else 0))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(s.drop(i - 1)[0] == c)
        Assert(s.drop(i - 1).drop(1) == s.drop(i))
        # ADVERSARY: lower-case EVERY position (prepatch model.lower()); the
        # verbatim app-label branch is removed.
        result = [lower_cp(c)] + result
        i = i - 1
    Assert(s.drop(0) == s)
    return result"""


# ===========================================================================
# (6) PARTIAL-DOMAIN — keep the model name verbatim too (forgot model.lower()).
# Correct on bare names (no dot -> keep=0 -> all lowered, same as gold) but for a
# QUALIFIED ref it keeps EVERYTHING verbatim (app label AND model name), i.e. the
# bug `'%s.%s' % (app_label, model_name)` that drops `.lower()` on the model
# name. We keep the gold loop/invariants/asserts VERBATIM and only widen the
# verbatim branch to fire whenever a dot is present (keep>0). The gold invariant
# (which lowers the model name) then fails, and the postcondition diverges on any
# qualified ref with an upper-case model name (e.g. 'DJ_RegLogin.Category' ->
# this gives 'DJ_RegLogin.Category', gold 'DJ_RegLogin.category') -> REJECT.
# A sub-domain (qualified refs) attack the prepatch case does not subsume.
# ===========================================================================
_WEAK_KEEP_MODEL = """    s = ToSeq(text)
    keep = keep_count(s)
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(s == ToSeq(text))
        Invariant(0 <= keep and keep <= len(s))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == normfold(s.drop(i), keep - i if keep - i > 0 else 0))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(s.drop(i - 1)[0] == c)
        Assert(s.drop(i - 1).drop(1) == s.drop(i))
        # ADVERSARY: if the ref is qualified (keep>0) keep the WHOLE string
        # verbatim (app label AND model name) -> the model name is never lowered.
        if keep > 0:
            result = [c] + result
        else:
            result = [lower_cp(c)] + result
        i = i - 1
    Assert(s.drop(0) == s)
    return result"""


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_REORDER),
        "rationale": (
            "Structurally-different CORRECT impl: the per-code-point conditional "
            "is reordered (lower-case case `i-1 >= keep` first, verbatim case in "
            "the else). The backward front-prepend loop, every gold Invariant and "
            "both framing Asserts are kept VERBATIM, so the front-recursive "
            "normfold single-unfold still discharges the invariant. A faithful "
            "correct impl MUST verify; if it cannot -> SPEC-TOO-STRONG. (A forward-"
            "append loop is deliberately avoided: it would need a normfold(a+b) "
            "lemma the verifier won't auto-discharge — a proof gap, not a defect.)"
        ),
    },
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISS_IMPL),
        "rationale": (
            "A positive control builds the F2P reference "
            "'MiXedCase_migrations.author' as a locally-owned full-perm List[int] "
            "and establishes normalize_reference's Requires(Acc(text,1/2)) on it by "
            "lending a 1/2 share, asserted AT the witness. It is asserted rather "
            "than exercised by a self-call because the model carries "
            "Requires(MustTerminate(2)) and a same-level self-call on a "
            "non-shrinking argument is an obligation leak Nagini is right to "
            "refuse. The precondition must admit this normal input; if the witness "
            "cannot establish Requires -> PRECOND-TOO-STRONG. The real gold "
            "computation then returns the actual result, so the module verifies. "
            "NEGATIVE CONTROL: THERE IS NONE, and that is a fact about this "
            "precondition rather than about the probe. normalize_reference's only "
            "frozen clause is Acc(list_pred(text), 1 / 2), and no VALUE violates a "
            "permission clause: measured, the same assert at a one-code-point "
            "a_text still reports `Verification successful`. So this case checks "
            "permission admissibility plus the fact that the gold body after it "
            "verifies under the obligation; it does NOT pin a value domain, and "
            "must not be read as strong as a case whose precondition carries a "
            "length or element-domain clause a witness can leave."
        ),
    },
    {
        "id": "frame-mut-text",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_FRAME_MUT_TEXT),
        "refinement": (
            "A real patch that WRITES to the reference string carrier "
            "(self.remote_field.model) to coerce it into the normalized form is "
            "not the gold edit at all: the gold patch computes a NEW value "
            "('%s.%s' % (app_label, model_name.lower())) and assigns it to "
            "kwargs['to'], never mutating self.remote_field.model. Mutating the "
            "field's model attribute would corrupt the shared field state used "
            "elsewhere in deconstruct/migration rendering and is not the "
            "split/lower/format fix, so it would not reproduce the resolving "
            "patch and would not pass the F2P/P2P the way gold does."
        ),
        "rationale": (
            "FRAME-MUTATION (#1 weakness class): `text` is a READ-ONLY input "
            "(Acc(list_pred(text),1/2)). Appending to it requires WRITE permission "
            "the caller never lent -> REJECT for INSUFFICIENT PERMISSION. The gold "
            "spec (pre/post/invariants) is untouched, so the rejection is "
            "attributable to the illegal write. (Returning `text` would also "
            "violate Acc(list_pred(Result())) which demands a fresh full-perm "
            "list, and the value postcondition for non-trivial inputs.)"
        ),
    },
    {
        "id": "weak-echo-input-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_ECHO_INPUT),
        "refinement": (
            "Returning the reference UNCHANGED corresponds to a patch that drops "
            "normalization entirely (no .lower() at all) — weaker than even the "
            "prepatch code. A bare lazy reference like 'Author' would stay "
            "'Author' instead of resolving to the lower-cased model label the "
            "app/migration registry expects, so lower-casing-dependent behaviour "
            "regresses and the change does not resolve the issue (and several P2P "
            "rendering/lookup tests that rely on case folding would fail)."
        ),
        "rationale": (
            "UNGROUNDED-ORACLE-ECHO surrogate: `normalized` is grounded in the "
            "input so there is no answer-key to echo; the do-nothing impl copies "
            "`text` verbatim. It satisfies freshness/permission but cannot prove "
            "ToSeq(Result())==normalized(ToSeq(text)) whenever normalized changes "
            "a byte (any upper-case letter outside a verbatim app label, e.g. "
            "'Author'->'author') -> REJECT at the postcondition. If it verified "
            "(spec pinning only length/permission) => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-prepatch-lower-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_LOWER_ALL),
        "refinement": (
            "This IS the prepatch behaviour: `kwargs['to'] = "
            "self.remote_field.model.lower()` lower-cases the WHOLE reference, "
            "including the application label. For the F2P the app label "
            "'MiXedCase_migrations' becomes 'mixedcase_migrations', producing a "
            "lazy reference to an app that 'isn't installed' (the issue's "
            "ValueError) — test_reference_mixed_case_app_label FAILS. "
            "model_prepatch.py is exactly this and is documented to fail the "
            "postcondition (G-DIFF)."
        ),
        "rationale": (
            "UNIQUENESS (THE F2P discriminator): lower-casing every code point "
            "drops the application-label case. The gold loop/invariants/asserts "
            "are kept VERBATIM with only the verbatim branch removed, so the "
            "invariant ToSeq(result)==normfold(s.drop(i),keep-i...) (which keeps "
            "the app label) can no longer be maintained and the postcondition "
            "ToSeq(Result())==normalized(ToSeq(text)) fails for any qualified ref "
            "with an upper-case app label -> REJECT. If it verified => "
            "SPEC-TOO-WEAK (would admit the very bug the patch fixes)."
        ),
    },
    {
        "id": "partial-domain-keep-model-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_KEEP_MODEL),
        "refinement": (
            "A patch `'%s.%s' % (app_label, model_name)` that splits on the dot "
            "and preserves the app-label case BUT forgets to lower-case the model "
            "name resolves a qualified reference like 'DJ_RegLogin.Category' to "
            "'DJ_RegLogin.Category' instead of 'DJ_RegLogin.category'. The "
            "migration/app registry expects the model label lower-cased, so the "
            "lazy reference dangles (looks up model 'Category', not 'category') — "
            "a wrong resolution on the qualified-ref sub-domain that does not "
            "faithfully reproduce the resolving patch."
        ),
        "rationale": (
            "PARTIAL-DOMAIN: correct on bare names (keep=0 -> all lowered, same as "
            "gold) but, for any qualified ref (keep>0), keeps the WHOLE string "
            "verbatim — the model name is never folded. The gold invariant "
            "ToSeq(result)==normfold(s.drop(i),keep-i...) lowers the model name, "
            "so it can't be maintained and the postcondition diverges whenever a "
            "qualified ref has an upper-case model name -> REJECT. A sub-domain "
            "(qualified refs with mixed-case model names) the lower-all case does "
            "not subsume; if it verified => SPEC-TOO-WEAK."
        ),
    },
]


# No @ContractOnly axioms (meta.axioms == []) and no CONSUMED deep-model axiom:
# the whole transformation is modelled DEEPLY (normalized/normfold/keep_count/
# first_dot/lower_cp are spelled-out @Pure folds the proof unfolds, not callees).
# The single deep-model reference `normalized` is an A-reference validated ==
# the real gold transform (str.split('.')/str.lower()/%-format) by axiom_check.py
# / G-AX (26 boundary + 40000 fuzz inputs). There is no @ContractOnly
# Requires-domain to fuzz or to contain in-container, so AXIOM_TESTS is empty by
# design (see assessment).
AXIOM_TESTS = []
