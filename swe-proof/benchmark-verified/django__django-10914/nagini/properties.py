# properties.py — PBT falsification battery for django__django-10914. NOT a Nagini
# module; a record of adversarial cases the runner (swebench_nagini.pbt) executes.
#
# Defended surface (read from model.py + refinement.md):
#   resolve_storage_mode(override: Optional[int]) -> Optional[int]
#   The store's effective file-upload mode. An explicit per-store override passes
#   through verbatim; with NO override the result is the DEFINITE project-wide
#   default 0o644 == 420 (the gold patch's only change: FILE_UPLOAD_PERMISSIONS
#   None -> 0o644). Four load-bearing postcondition clauses:
#     (C1) Implies(override is not None, Result() is override)   # passthrough
#     (C2) Implies(override is None,     Result() is not None)   # definite (FIX)
#     (C3) Implies(override is None,     Result() == default_mode())
#     (C4) Implies(override is None,     Result() == 420)
#
# Why no FRAME-MUTATION lane: the only input `override` is an immutable scalar
#   (Optional[int]); the model declares NO heap permissions (pre-conditions
#   region is empty, no Acc(...)). There is no read-only-with-full-permission
#   input to overwrite, so the #1 weakness class does not apply here.
# Why no AXIOM lane: meta.axioms == [] and deep_model_references == []. The whole
#   resolution (_value_or_setting) and the changed value are modeled DIRECTLY as
#   a concrete int/None computation; no @ContractOnly axiom, no real opaque
#   callee, no axiom_check.py. AXIOM_TESTS = [].
# Why no UNGROUNDED-ORACLE-ECHO reject case: the postcondition is NOT pinned to
#   an opaque answer-key. default_mode() is a @Pure constant `return 420`, and
#   C4 redundantly pins the SAME concrete literal 420. An echo
#   `return default_mode()` on the None branch is therefore CORRECT, not a wrong
#   echo — there is no value an echo could carry that satisfies C3/C4 yet is
#   wrong. We instead include that grounded echo as an honest positive control
#   (pos-grounded-oracle, expect verify).
from pathlib import Path

INSTANCE = "django__django-10914"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl region body, verbatim (everything strictly BETWEEN the
# markers). All variants _swap this single block, so edits never touch the spec
# (axioms/pure/pre/post regions + signature) and same_spec is guaranteed.
_IMPL = """\
    # The project-wide default mode handed back when nothing is configured.
    default = 420  # type: Optional[int]   # 0o644
    # Resolution: an absent override falls back to the project-wide default;
    # otherwise the override is used verbatim.
    if override is None:
        return default
    return override"""

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"


def _impl(new_body):
    """Build a full model.py variant with the impl region body replaced. Only the
    text strictly inside # impl-start / # impl-end changes."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-branch-reorder: structurally different but behaviourally identical — the
# guard is inverted (test the present branch first). Keeps the gold proof valid;
# no framing asserts/lemmas are needed (no loops, no @Pure fold).
_POS_REORDER = """\
    # Branch-reordered resolution: handle a present override first, fall back to
    # the project-wide default 0o644 == 420 only when the override is absent.
    if override is not None:
        return override
    default = 420  # type: Optional[int]   # 0o644
    return default"""

# pos-grounded-oracle: the honest grounded-echo positive control. Return the
# @Pure default_mode() (== 420) on the absent-override branch instead of the
# inline literal. The oracle is grounded (a constant equal to the required
# value), so this is CORRECT and must verify — there is no wrong echo to build.
_POS_ORACLE = """\
    # Absent override -> the project-wide default, sourced from the @Pure
    # reference default_mode() (which is the concrete 0o644 == 420); a present
    # override passes through verbatim.
    if override is None:
        return default_mode()
    return override"""

# admiss-roundtrip: an admissibility positive control. The precondition is empty
# (no Requires), so it trivially admits any input; we additionally assert the
# postcondition SHAPE holds for two F2P/P2P-shaped inputs (the `None` case the
# F2P test exercises -> 420, and a concrete override 0o777 == 511 -> passthrough,
# the sibling P2P case) so a PRECOND-TOO-STRONG / spec-shape regression would
# surface here. Asserts are over local immutable scalars; no proof gap.
_ADMISS = """\
    # Admissibility / shape control: both F2P/P2P-shaped inputs are in-domain.
    default = 420  # type: Optional[int]   # 0o644
    if override is None:
        # F2P: default_storage (no override configured) -> definite 0o644.
        Assert(default == 420)
        Assert(default is not None)
        return default
    # P2P sibling: a configured override (e.g. 0o777 == 511) passes through.
    Assert(override is override)
    return override"""


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each shares the frozen spec exactly and changes only the impl region.
# ---------------------------------------------------------------------------

# weak-default-none: the PRE-PATCH behaviour — leave the default absent (None).
# This is precisely model_prepatch.py. Violates C2/C3/C4.
_WEAK_NONE = """\
    # Adversary: keep the pre-patch absent default (None) instead of 0o644.
    default = None  # type: Optional[int]
    if override is None:
        return default
    return override"""

# weak-always-default: ignore the override entirely; always return 420.
# Satisfies the None branch but violates C1 (override passthrough).
_WEAK_ALWAYS = """\
    # Adversary: always return the default mode, ignoring any configured override.
    result = 420  # type: Optional[int]   # 0o644
    return result"""

# weak-wrong-default: use 0o600 == 384 as the default (the value the issue
# thread first floated and the community REJECTED in favour of 0o644). Satisfies
# C1/C2 but violates C3/C4 (Result() must equal 420 on the absent-override case).
_WEAK_WRONG = """\
    # Adversary: fall back to 0o600 == 384 (the rejected proposal) not 0o644.
    default = 384  # type: Optional[int]   # 0o600
    if override is None:
        return default
    return override"""

# weak-swap-branches: swap the two return arms — return the (absent) override on
# the absent branch and the default when an override is present. Violates both
# C1 (present override -> returns default, not the override) and C2/C3/C4
# (absent override -> returns None).
_WEAK_SWAP = """\
    # Adversary: swap the return arms (absent -> override [None], present ->
    # default). Inverts both the passthrough and the fallback.
    default = 420  # type: Optional[int]   # 0o644
    if override is None:
        return override
    return default"""

# weak-partial-zero: correct on almost the whole domain, but special-cases the
# valid mode override == 0 (0o000, all-permissions-cleared, a real chmod value)
# to return the default instead of passing it through. Violates C1 on the single
# sub-domain override == 0. A byte-fuzzer never targets this boundary value.
_WEAK_ZERO = """\
    # Adversary: passthrough EXCEPT the boundary mode 0 (0o000), which it
    # silently rewrites to the project-wide default — diverging only on that
    # one valid override value.
    default = 420  # type: Optional[int]   # 0o644
    if override is None:
        return default
    if override == 0:
        return default
    return override"""


SPEC_TESTS = [
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "a structurally-different but behaviourally-identical impl "
            "(guard inverted, default built in the absent branch) must verify; "
            "no loop/lemma so the gold proof stays valid. If it fails => "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-grounded-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_ORACLE),
        "rationale": (
            "the postcondition's @Pure reference default_mode() is GROUNDED "
            "(a constant == 420 == the required default), so returning it on the "
            "absent branch is correct and must verify — there is no wrong echo to "
            "construct. Honest grounded-oracle positive control per directive 2."
        ),
    },
    {
        "id": "admiss-roundtrip",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the (empty) precondition must admit the two F2P/P2P-shaped inputs "
            "(None -> 0o644; a concrete override -> passthrough); asserts over "
            "immutable scalars introduce no proof gap. If it fails => "
            "PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "weak-default-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NONE),
        "refinement": (
            "this IS the pre-patch code (FILE_UPLOAD_PERMISSIONS = None). Its "
            "faithful real patch is the unpatched repo, which fails the F2P "
            "test_override_file_upload_permissions assertion "
            "assertEqual(default_storage.file_permissions_mode, 0o644) (it is "
            "None pre-patch). Does NOT resolve."
        ),
        "rationale": (
            "rejected by C2/C3/C4 (Implies(override is None, Result() is not None "
            "/ == default_mode() / == 420)); the absent default is exactly what "
            "model_prepatch.py reverts to. If it verifies => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-always-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS),
        "refinement": (
            "always returning 0o644 ignores a configured override. Its faithful "
            "real patch would drop self._file_permissions_mode, so the "
            "with self.settings(FILE_UPLOAD_PERMISSIONS=0o777) branch of the F2P "
            "test (and the sibling directory-permissions P2P) would resolve to "
            "0o644 != 0o777. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1 (Implies(override is not None, Result() is override)) "
            "— a present override must pass through, not be overwritten by 420. "
            "If it verifies => SPEC-TOO-WEAK (override branch unconstrained)."
        ),
    },
    {
        "id": "weak-wrong-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_WRONG),
        "refinement": (
            "0o600 == 384 is the default the issue thread first proposed and the "
            "community explicitly REJECTED in favour of 0o644. A real patch "
            "setting FILE_UPLOAD_PERMISSIONS = 0o600 fails the F2P assertion "
            "assertEqual(default_storage.file_permissions_mode, 0o644). Does NOT "
            "resolve."
        ),
        "rationale": (
            "satisfies C1/C2 but rejected by C3/C4 (Result() must == "
            "default_mode() == 420 on the absent-override case). If it verifies "
            "=> SPEC-TOO-WEAK (the exact default value would be unpinned)."
        ),
    },
    {
        "id": "weak-swap-branches",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SWAP),
        "refinement": (
            "swapping the arms is the inverted resolver (setting if value is not "
            "None else value). Its real patch returns the global default when an "
            "override IS set and None when it is not — failing BOTH the F2P "
            "0o644 case and the 0o777 override case. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1 (present override -> returns default, not override) "
            "AND C2/C3/C4 (absent override -> returns None). A supporting "
            "near-miss that nonetheless carries a real refinement."
        ),
    },
    {
        "id": "weak-partial-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ZERO),
        "refinement": (
            "0o000 (override == 0) is a legitimate chmod mode a store could "
            "configure (clear all permissions). A real patch with this special "
            "case would, for a store with file_permissions_mode == 0, resolve to "
            "0o644 instead of 0 — diverging from the unchanged _value_or_setting "
            "rule (which passes 0 through, since `0 is None` is False). Does NOT "
            "faithfully implement the resolver. PARTIAL-DOMAIN attack."
        ),
        "rationale": (
            "rejected by C1 on the sub-domain override == 0: "
            "Implies(override is not None, Result() is override) requires the "
            "value 0 to pass through, but this impl returns 420 for it. If it "
            "verifies => SPEC-TOO-WEAK on a boundary a byte-fuzzer never targets."
        ),
    },
]

# No @ContractOnly axioms and no deep-model A-references on this path
# (meta.axioms == [], deep_model_references == []); the resolution and the
# changed value are modeled directly. Nothing for the axiom lane to execute.
AXIOM_TESTS = []
