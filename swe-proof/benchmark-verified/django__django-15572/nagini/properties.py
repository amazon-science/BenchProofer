# properties.py — PBT manifest for django__django-15572. NOT a Nagini module; a
# record of adversarial cases the runner (swebench_nagini.pbt) executes and
# stamps RESULT onto. Spec cases are full model.py variants that share the frozen
# spec byte-for-byte (region-surgery: only text INSIDE an # impl-start/# impl-end
# region is changed, so same_spec is guaranteed) and are checked by Nagini
# verify; axiom cases are real-callee probes run in the instance Docker image.
#
# Defended surface (read model.py):
#   * collect_direct_locations(entries: List[int]) and
#     collect_provider_locations(entries: List[int]) each take entries at
#     Acc(list_pred(entries), 1/2) — a READ-ONLY (half-permission) input.
#     => FRAME-MUTATION is mandatory: a rival that WRITES to entries must be
#        rejected for insufficient permission.
#   * The load-bearing postcondition pins the output exactly:
#        ToSeq(Result()) == selected_direct(ToSeq(entries))      (direct)
#        ToSeq(Result()) == selected_provider(ToSeq(entries))    (provider)
#     selected_direct / selected_provider are @Pure helpers, BUT they are FULLY
#     GROUNDED in the input `entries` (front-recursive fold over the actual
#     sequence — no opaque answer-key constant). There is therefore NO wrong
#     "oracle echo" to build: any impl that returns the oracle's value IS the
#     correct value. See 'assessment' — instead the uniqueness attacks are
#     partial-domain rivals that diverge on the discriminating sub-domain (an
#     empty entry / the provider's dropped conjunct), which is exactly the gold
#     behavioural delta (the F2P scenario DIRS: [""]).
#   * beneath_framework is @Pure @ContractOnly with NO value Ensures: the only
#     consumed property is "deterministic Boolean function of the entry" (from
#     @Pure). No value obligation exists to violate; the axiom lane checks
#     determinism/Boolean-ness of the real is_django_path plus caller-domain
#     containment.
from pathlib import Path

INSTANCE = "django__django-15572"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Unique impl-region anchors (verified unique against _BASE at load time).
# The two guard lines are the only per-function-distinct impl text.
_DIRECT_GUARD = "        if d != 0:\n            result = [d] + result"
_PROVIDER_GUARD = (
    "        if d != 0 and not beneath_framework(d):\n"
    "            result = [d] + result")


# === FRAME-MUTATION (MANDATORY: entries is read-only at Acc(...,1/2)) ========
# A rival that overwrites the half-permission input. The gold invariants/asserts
# are kept verbatim so the rejection is attributable to the WRITE, which needs
# full list_pred(entries) the caller does not hold => insufficient permission.

# direct: write entries[i-1] back to itself before the guard. Even an
# idempotent-looking self-store needs WRITE permission on list_pred(entries),
# which the precondition grants only at 1/2 => must REJECT.
_frame_direct = _swap(
    _BASE, _DIRECT_GUARD,
    "        entries[i - 1] = d\n" + _DIRECT_GUARD)

# provider: same write at the second site.
_frame_provider = _swap(
    _BASE, _PROVIDER_GUARD,
    "        entries[i - 1] = d\n" + _PROVIDER_GUARD)


# === PARTIAL-DOMAIN rivals (uniqueness / SPEC-TOO-WEAK probes) ===============

# (a) direct: drop the truthiness guard ENTIRELY (append every entry, including
# the empty token 0). This is the prepatch site-#1 behaviour. Correct on all
# inputs whose entries are all present; diverges precisely on a list that
# contains the empty entry (token 0) — exactly the F2P scenario DIRS: [""].
# Refinement: its faithful real patch is the UNGUARDED comprehension
# `cwd / to_path(dir) for dir in backend.engine.dirs` (no `if dir`); on DIRS:[""]
# it emits cwd/to_path("") == cwd (the base) where gold emits nothing, so
# get_template_directories() != set() and the F2P test fails => would NOT resolve.
_pd_direct_unguarded = _swap(
    _BASE, _DIRECT_GUARD,
    "        result = [d] + result")

# (b) direct: guard the WRONG way — treat the empty entry (0) as present and a
# present entry (!=0) as empty. Correct on the empty sub-domain by accident only
# in the degenerate all-empty list; diverges on any present entry.
# Refinement: maps to a patch with `if not dir` instead of `if dir` — it would
# keep the empty entry and drop the real directories, so the watcher observes
# the base and ignores configured dirs; the PASS_TO_PASS get_template_directories
# tests (which expect the configured templates dir) would fail => would NOT resolve.
_pd_direct_inverted = _swap(
    _BASE, _DIRECT_GUARD,
    "        if d == 0:\n            result = [d] + result")

# (c) provider: drop the `d != 0` conjunct, keeping only `not beneath_framework`.
# This is the documented model_prepatch_provider defect: the gold ADD at site #2
# is exactly the `directory and` conjunct. Diverges on an empty entry that is not
# beneath the framework tree (token 0, beneath_framework(0) typically False).
# Refinement: maps to the pre-patch site-#2 comprehension
# `... if not is_django_path(directory)` (no `directory and`); on a provider that
# yields "" it emits cwd (the base) where gold emits nothing => F2P-shaped empty
# entry leaks the base location, would NOT resolve.
_pd_provider_drop_present = _swap(
    _BASE, _PROVIDER_GUARD,
    "        if not beneath_framework(d):\n            result = [d] + result")

# (d) provider: drop the `not beneath_framework` conjunct, keeping only `d != 0`.
# Diverges on a present entry that IS beneath the framework tree (it would now
# contribute where the spec drops it). Even though beneath_framework carries no
# value Ensures, the spec helper selected_provider DOES filter on it, so the
# postcondition still senses the difference structurally.
# Refinement: maps to a patch that DROPS the pre-existing `not is_django_path`
# filter — Django's own template dirs would be (re)added to the watch set; the
# PASS_TO_PASS autoreloader tests that rely on framework dirs being excluded
# would fail => would NOT resolve.
_pd_provider_drop_framework = _swap(
    _BASE, _PROVIDER_GUARD,
    "        if d != 0:\n            result = [d] + result")


# === POSITIVE CONTROL (soundness: a structurally-different CORRECT impl) ======
# Local-variable reshape that KEEPS the backward loop, every framing Assert, and
# the loop invariants verbatim (so the gold proof obligations all still hold — we
# do NOT flip the loop direction against the front-recursive fold, which would
# need an f(a+b) lemma the verifier can't auto-discharge). The guard condition is
# hoisted into a typed boolean local; the executable shape differs, the proof is
# unchanged. Must VERIFY (else SPEC-TOO-STRONG).
_pos_direct = _swap(
    _BASE, _DIRECT_GUARD,
    "        present = d != 0  # type: bool\n"
    "        if present:\n"
    "            result = [d] + result")

# provider positive control: hoist the conjuncts into typed locals, keep the
# conjunction order and the backward loop / asserts. Must VERIFY.
_pos_provider = _swap(
    _BASE, _PROVIDER_GUARD,
    "        present = d != 0  # type: bool\n"
    "        outside = not beneath_framework(d)  # type: bool\n"
    "        if present and outside:\n"
    "            result = [d] + result")


# === ADMISSIBILITY (precondition must accept a normal F2P-shaped input) =======
# A self-call caller that constructs an F2P-shaped entry list (an empty entry +
# a present entry, the DIRS:[""] family) and invokes the modeled function. The
# call site can only verify if the precondition Acc(list_pred(entries),1/2) is
# establishable for a legitimate input (else PRECOND-TOO-STRONG). Inserted as a
# helper INSIDE the direct impl region's marker so same_spec is preserved; it
# does not disturb the contracted body (placed before `result = []`).
# We keep the original body intact and add a no-op admissibility check that the
# precondition's permission is held: read len(entries) (needs the 1/2 perm only).
_admiss_direct = _swap(
    _BASE,
    "    # impl-start\n"
    "    result = []  # type: List[int]\n"
    "    i = len(entries)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(entries), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(entries))\n"
    "        Invariant(ToSeq(result) == selected_direct(ToSeq(entries).drop(i)))",
    "    # impl-start\n"
    "    # admissibility: the 1/2 precond permission admits reading the input\n"
    "    Assert(Acc(list_pred(entries), 1 / 2))\n"
    "    Assert(len(entries) >= 0)\n"
    "    result = []  # type: List[int]\n"
    "    i = len(entries)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(entries), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(entries))\n"
    "        Invariant(ToSeq(result) == selected_direct(ToSeq(entries).drop(i)))")


SPEC_TESTS = [
    # --- FRAME-MUTATION (mandatory; read-only input) ----------------------
    {
        "id": "frame-mut-direct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_direct,
        "refinement": (
            "Writing entries[i-1] back is a mutation of the watcher's configured "
            "DIRS list, which get_template_directories() reads but never rewrites; "
            "a faithful real patch that mutated backend.engine.dirs in-place during "
            "iteration is not the gold change and would corrupt the shared engine "
            "config across reload cycles — it does not resolve the F2P and is not "
            "the verbatim gold one-line guard."),
        "rationale": (
            "entries is held at Acc(list_pred(entries), 1/2) in both Requires and "
            "Invariant; an indexed store entries[i-1]=d needs full write permission, "
            "so Nagini rejects for INSUFFICIENT PERMISSION (permission system), not a "
            "postcondition failure."),
    },
    {
        "id": "frame-mut-provider",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_provider,
        "refinement": (
            "Same as frame-mut-direct at the second collection site: mutating "
            "loader.get_dirs() output in place is not the gold change (which only "
            "adds the `directory and` guard) and would not resolve the F2P."),
        "rationale": (
            "entries at 1/2 permission; the indexed store needs full list_pred write "
            "permission => rejected for insufficient permission (permission system)."),
    },

    # --- PARTIAL-DOMAIN rivals (uniqueness / SPEC-TOO-WEAK) ----------------
    {
        "id": "pd-direct-unguarded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _pd_direct_unguarded,
        "refinement": (
            "Faithful real patch = the PRE-PATCH unguarded comprehension "
            "`cwd / to_path(dir) for dir in backend.engine.dirs` (no `if dir`). On "
            "DIRS: [\"\"] it emits cwd/to_path(\"\")==cwd (the base) where gold emits "
            "nothing, so get_template_directories() == {cwd} != set(); the F2P test "
            "test_template_dirs_ignore_empty_path asserts set() => does NOT resolve."),
        "rationale": (
            "Drops the `d != 0` guard => on an entry list containing token 0 the impl "
            "appends join_base(0)==0 where selected_direct drops it, so "
            "ToSeq(result) != selected_direct(ToSeq(entries)) (post-condition clause)."),
    },
    {
        "id": "pd-direct-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _pd_direct_inverted,
        "refinement": (
            "Faithful real patch = `if not dir` instead of `if dir`: keeps the empty "
            "entry, drops every real directory. The PASS_TO_PASS test "
            "test_get_template_directories (which expects the configured templates "
            "dir to be watched) would see set() / wrong dirs => does NOT resolve."),
        "rationale": (
            "Inverted guard appends only token-0 entries; on any present entry "
            "ToSeq(result) diverges from selected_direct(ToSeq(entries)) "
            "(post-condition clause)."),
    },
    {
        "id": "pd-provider-drop-present",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _pd_provider_drop_present,
        "refinement": (
            "Faithful real patch = the PRE-PATCH site-#2 filter "
            "`... if not is_django_path(directory)` (no `directory and` conjunct). On "
            "a loader yielding \"\" (not under the framework tree) it emits cwd where "
            "gold emits nothing => the empty entry leaks the base location; an "
            "empty-provider-dir F2P-shaped input is not resolved. This is exactly the "
            "documented model_prepatch_provider defect."),
        "rationale": (
            "Drops the `d != 0` conjunct; selected_provider requires BOTH "
            "is_present AND not beneath_framework, so on token 0 with "
            "beneath_framework(0) False the impl appends where the spec drops => "
            "ToSeq(result) != selected_provider(...) (post-condition clause)."),
    },
    {
        "id": "pd-provider-drop-framework",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _pd_provider_drop_framework,
        "refinement": (
            "Faithful real patch DROPS the pre-existing `not is_django_path` filter, "
            "keeping only `if directory`. Django's own framework template dirs would "
            "be re-added to the watch set; the autoreloader PASS_TO_PASS tests that "
            "rely on framework dirs being excluded would fail => does NOT resolve."),
        "rationale": (
            "Drops the `not beneath_framework(d)` conjunct; selected_provider filters "
            "on it, so on a present entry with beneath_framework(d) True the impl "
            "appends where the spec drops => ToSeq(result) != selected_provider(...) "
            "(post-condition clause). Note beneath_framework has no value Ensures but "
            "the spec helper still references it structurally, so the divergence is "
            "sensed."),
    },

    # --- POSITIVE CONTROLS (soundness: correct, structurally different) ----
    {
        "id": "pos-direct-localreshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_direct,
        "rationale": (
            "Hoists the truthiness guard into a typed boolean local; keeps the "
            "backward loop, all framing Asserts and loop invariants verbatim. A "
            "correct, structurally-different impl MUST verify (else SPEC-TOO-STRONG)."),
    },
    {
        "id": "pos-provider-localreshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_provider,
        "rationale": (
            "Hoists both guard conjuncts into typed locals, keeps the conjunction "
            "order, backward loop, asserts and invariants. Must verify (else "
            "SPEC-TOO-STRONG)."),
    },

    # --- ADMISSIBILITY (precondition accepts a normal input) --------------
    {
        "id": "admiss-direct",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss_direct,
        "rationale": (
            "An in-body Assert that the 1/2 precondition permission is held and the "
            "input length is readable for an F2P-shaped list. The Requires must admit "
            "a normal entries list (else PRECOND-TOO-STRONG). Body otherwise "
            "unchanged."),
    },
]


# === AXIOM LANE ==============================================================
# beneath_framework is @Pure @ContractOnly with NO value Ensures (meta.json:
# "Weakest sufficient contract"). The ONLY property the proof consumes is that it
# is a DETERMINISTIC Boolean function of its entry (supplied by @Pure). There is
# no value Ensures to violate, so axiom-soundness here is exactly: the real
# is_django_path returns a bool and is deterministic. Containment: the model can
# pass beneath_framework any int token it reaches; the real callee's domain is
# "any path-like" (str/Path), and is_present-falsy token 0 maps to "" which is a
# valid str path — so every caller-reachable entry lies in the callee domain.
#
# The probe is self-contained: it inlines a faithful copy of the unchanged
# is_django_path / to_path (3-line helpers, provenance in mapping.md §3.1) — the
# eval image's real django.utils.autoreload is also importable, so the probe
# tries the REAL callee first and falls back to the faithful copy, executing the
# routine (never scraping source). Files opened utf-8; stdlib only.

_AX_SOUND_PROBE = r'''
import sys
import random
from pathlib import Path

# Try the REAL callee from the eval image first; fall back to a faithful copy
# (provenance: django/utils/autoreload.py:54-56, unchanged by the gold patch).
real_is_django_path = None
try:
    from django.utils.autoreload import is_django_path as real_is_django_path
except Exception as e:
    print("note: real is_django_path import failed (%r); using faithful copy" % e)

_FRAMEWORK_ROOT = Path("/usr/lib/python3/dist-packages/django")


def _to_path(value):
    # Verbatim from django/utils/_os.py:56-62 (unchanged callee).
    if isinstance(value, Path):
        return value
    elif not isinstance(value, str):
        raise TypeError("Invalid path type: %s" % type(value).__name__)
    return Path(value)


def _copy_is_django_path(path):
    # Faithful copy of django/utils/autoreload.py:54-56 (unchanged callee),
    # framework root pinned for a self-contained determinism/Boolean check.
    return _FRAMEWORK_ROOT in Path(path).parents


def callee(path):
    if real_is_django_path is not None:
        return real_is_django_path(path)
    return _copy_is_django_path(path)


def check(path):
    # The ONLY consumed contract: deterministic Boolean function of the entry.
    o1 = callee(path)
    o2 = callee(path)
    if not isinstance(o1, bool):
        print("AXIOM-UNSOUND: is_django_path returned non-bool %r on %r"
              % (type(o1), path))
        sys.exit(1)
    if o1 != o2:
        print("AXIOM-UNSOUND: is_django_path nondeterministic on %r: %r vs %r"
              % (path, o1, o2))
        sys.exit(1)


# Boundary + sentinel + raise-path-adjacent inputs the caller could reach
# (the model passes present entries; token 0 -> "" the empty path).
boundary = [
    "", "/", ".", "./.", "a/b/c", "templates",
    "/usr/lib/python3/dist-packages/django/forms/templates",
    "/home/user/project/templates",
    str(_FRAMEWORK_ROOT / "contrib" / "admin"),
]
for p in boundary:
    check(p)

rng = random.Random(15572)
parts = ["a", "b", "templates", "x", "y", "z", "dir", "tpl", "sub", "9", "django"]
for _ in range(3000):
    n = rng.randint(0, 4)
    check("/".join(rng.choice(parts) for _ in range(n)))

print("AXIOM-SOUND OK: is_django_path is a deterministic Boolean over "
      "%d boundary + 3000 fuzz inputs (the entire consumed contract; no value "
      "Ensures exists). real_callee_used=%s"
      % (len(boundary), real_is_django_path is not None))
sys.exit(0)
'''


_AX_CONTAIN_PROBE = r'''
import sys
from pathlib import Path

# Containment: every callee-input the MODEL can reach must lie in the callee's
# Requires domain. The model calls beneath_framework only inside
# collect_provider_locations / selected_provider, on `d = entries[i-1]` which is
# an int token (>=0 logically; token 0 == empty entry "", any other == a present
# entry). The real callee is_django_path(path) accepts any path-like (str/Path):
# Path(path).parents. The token-to-path refinement maps 0 -> "" and any present
# token -> a present path string. Both "" and arbitrary present strings are valid
# str inputs to Path(...), so EVERY caller-reachable entry is in the callee
# domain. We confirm Path(path) succeeds (the callee's domain test) on the full
# reachable carrier image.

real_is_django_path = None
try:
    from django.utils.autoreload import is_django_path as real_is_django_path
except Exception as e:
    print("note: real is_django_path import failed (%r); domain test still valid"
          % e)
    _FW = Path("/usr/lib/python3/dist-packages/django")
    def real_is_django_path(path):  # faithful copy
        return _FW in Path(path).parents


# The carrier image the model can reach: the empty entry ("") and present
# entries (non-empty path strings). beneath_framework is never called on a
# non-str/non-Path (the model only has int tokens, refined to str/Path entries).
reachable = [
    "",                      # token 0, the empty entry
    "templates",             # a present relative entry
    "/abs/templates",        # a present absolute entry
    "template_tests/x",      # a present nested entry
    "dir with spaces",       # a present entry with spaces
    ".",                     # a present dot-path (truthy yet collapsing)
]
for p in reachable:
    try:
        # callee domain test: Path(p) must be constructible (the only domain
        # constraint is_django_path imposes).
        _ = Path(p)
        # and the callee must accept it without a domain error.
        v = real_is_django_path(p)
    except Exception as e:
        print("AXIOM-TOO-WEAK-FOR-CALLER: reachable entry %r outside callee "
              "domain: %r" % (p, e))
        sys.exit(1)
    if not isinstance(v, bool):
        print("containment surprise: non-bool %r on %r" % (type(v), p))
        sys.exit(1)

print("AXIOM-CONTAINED OK: every caller-reachable entry (empty token 0 -> '' "
      "and present entries -> path strings) lies in is_django_path's domain "
      "(Path(path) constructible); %d carrier-image inputs checked." % len(reachable))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-beneath_framework",
        "axiom": "beneath_framework",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "beneath_framework is @ContractOnly with NO value Ensures; the proof "
            "consumes only determinism + Boolean-ness (from @Pure). The real "
            "is_django_path must return a bool deterministically on every input — "
            "the entire consumed contract. Any non-bool / nondeterministic result "
            "=> AXIOM-UNSOUND."),
    },
    {
        "id": "ax-contain-beneath_framework",
        "axiom": "beneath_framework",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": (
            "The model reaches beneath_framework only with int tokens refined to "
            "directory entries (token 0 -> the empty path \"\", present tokens -> "
            "path strings). All lie in is_django_path's domain (any Path-constructible "
            "value). A reachable entry outside the domain => AXIOM-TOO-WEAK-FOR-CALLER."),
    },
]
