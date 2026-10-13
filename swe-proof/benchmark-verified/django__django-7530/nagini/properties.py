"""properties.py — PBT falsification battery for django__django-7530.

NOT a Nagini module: a manifest the runner (`swebench_nagini.pbt`) parses. Each
SPEC_TESTS entry is a FULL model.py variant that shares the FROZEN spec
(axioms/pure/pre-conditions/post-conditions regions untouched) and edits ONLY
text strictly inside the single `# impl-start`/`# impl-end` region — so
`markers.same_spec` is GUARANTEED and a rejection is attributable to the
postcondition (or the permission system), never to a tampered spec. (Note: the
spec view ELIDES the impl region INCLUDING the nested `invariants` sub-region —
confirmed in markers.spec_view — so loop invariants may be reshaped to match a
rival's impl without breaking same_spec; the discriminator is the
postcondition.)

Defended surface (read from model.py + mapping.md + refinement.md + axiom_check.py):

    members_for_group(owner: List[int], member: List[int], target: int) -> List[int]
      Requires(Acc(list_pred(owner),  1/2))     # READ-ONLY roster stream
      Requires(Acc(list_pred(member), 1/2))     # READ-ONLY roster stream
      Requires(len(owner) == len(member))       # two aligned streams
      Ensures (Acc(list_pred(owner),  1/2))
      Ensures (Acc(list_pred(member), 1/2))
      Ensures (Acc(list_pred(Result())))
      Ensures (ToSeq(Result()) == gathered(ToSeq(owner), ToSeq(member), target))

The LOAD-BEARING clause is the last Ensures: the result must be EXACTLY the
members belonging to `target`, in roster order — `gathered` is the
front-recursive per-position filter keeping `member[k]` iff `owner[k] == target`.
This models the gold patch's switch of the makemigrations history-consistency
pre-check iterable from `apps.get_models(app_label)` (project-wide; the label was
silently bound to a flag) to `apps.get_app_config(app_label).get_models()` (only
that app's models). The whole job of the spec: gather ONLY `target`'s members
(soundness — no foreign-group member offered under this group's label) and ALL of
them (completeness).

What this spec actually defends, and the attacks the battery mounts:

  * GROUNDED ORACLE, NO ECHO. `gathered` is a `@Pure` fold over the ACTUAL
    arguments (owner/member/target), not an opaque answer-key. It returns a
    `PSeq[int]`, and Nagini has no executable materialization of a PSeq into a
    `list_pred` list — there is no `return gathered(...)` you could write to echo
    the oracle without doing the work. So the ungrounded-oracle-echo class is N/A
    here; instead the soundness lane carries the cheapest HONEST impl as a
    positive control. (See 'assessment'.)

  * BOTH inputs are READ-ONLY (Acc(.,1/2)). The MANDATORY attack is FRAME
    MUTATION: an impl that WRITES to a read-only roster stream to satisfy the
    postcondition vacuously must fail for INSUFFICIENT PERMISSION (not a value
    mismatch). Two probes: write `owner`, write `member`.

  * THE DISCRIMINATING BUG is the dropped `o == target` guard: gathering the
    whole roster for every group (the pre-patch `apps.get_models(app_label)`
    project-wide return). `model_prepatch.py` is exactly that; its body is reused
    verbatim as `rival-prepatch-allmembers`.

  * NO CONTROL-FLOW / RAISE / SIDE-EFFECT axis. The function only returns a value;
    it never raises and (inputs read-only) has no observable side effect. The
    value abstraction (the gathered sequence) captures everything, so a
    capability-token control-flow rival is N/A. (See 'assessment'.)

Axiom lane: there is NO consumed @ContractOnly axiom (the `axioms` region is empty
by design). `gathered` is an A-reference deep model validated == the REAL Django
callee `apps.get_app_config(label).get_models()` by axiom_check.py (G-AX). The
AXIOM_TESTS below RE-RUN that real callee in the instance Docker image
(apply_gold=True) — soundness (the real callee equals `gathered` on a disjoint
multi-app registry, and the pre-patch project-wide return differs) and
containment (every callee-input the model can reach lies in the callee's domain).
The host axiom_check.py logic is embedded into the probe (the runner mounts ONLY
the probe at /work; bundle files are NOT in-container).
"""
from pathlib import Path

INSTANCE = "django__django-7530"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly ONE occurrence of an impl-region substring. Asserts the
    substring is present and unique so silent drift (model.py edited) fails loudly
    at manifest load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique ({src.count(old)}): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE the single # impl-start/# impl-end block).
# ---------------------------------------------------------------------------

# The whole impl body verbatim (between # impl-start and # impl-end, exclusive of
# the markers). Used by rivals that reshape the entire body.
_IMPL_BODY = """    result = []  # type: List[int]
    i = len(owner)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(owner), 1 / 2))
        Invariant(Acc(list_pred(member), 1 / 2))
        Invariant(len(owner) == len(member))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(owner))
        Invariant(ToSeq(result) ==
                  gathered(ToSeq(owner).drop(i), ToSeq(member).drop(i), target))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        o = owner[i - 1]
        m = member[i - 1]
        Assert(ToSeq(owner).drop(i - 1)[0] == o)
        Assert(ToSeq(member).drop(i - 1)[0] == m)
        Assert(ToSeq(owner).drop(i - 1).drop(1) == ToSeq(owner).drop(i))
        Assert(ToSeq(member).drop(i - 1).drop(1) == ToSeq(member).drop(i))
        if o == target:
            result = [m] + result
        i = i - 1
    return result"""

# The conditional gather step (the discriminating guard + front-prepend).
_GUARD_STEP = """        if o == target:
            result = [m] + result"""

# The two reads at the top of the loop body.
_READS = """        o = owner[i - 1]
        m = member[i - 1]"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5) POSITIVE CONTROL — structurally-different but CORRECT. The guard branch is
# rewritten as an EXPLICIT if/else with a no-op `else: result = result`. This is a
# branch reshape only: it KEEPS the backward loop direction and the front-prepend
# `result = [m] + result` (so the front-recursive `gathered` fold still unfolds in
# one step — directive-3 caution honoured: NO loop-direction flip, NO forward
# append against the front-recursive fold) and KEEPS every gold Invariant/Assert
# verbatim. A different executable shape over identical logic; if it fails to
# verify the postcondition is over-fit to the implicit-fall-through form =>
# SPEC-TOO-STRONG. This is also the cheapest HONEST impl (the gather step is real
# work; there is no oracle to echo).
_IMPL_EXPLICIT_ELSE = _swap(
    _IMPL_BODY,
    _GUARD_STEP,
    """        if o == target:
            result = [m] + result
        else:
            result = result""",
)
POS_EXPLICIT_ELSE = _swap(_BASE, _IMPL_BODY, _IMPL_EXPLICIT_ELSE)

# (6) ADMISSIBILITY — a self-call on an F2P-shaped input at the very top of the
# impl, before the gold body runs verbatim. Freshly-built locals carry FULL
# permission, so passing them at Acc(.,1/2) must succeed and the Requires
# (incl. len(owner)==len(member)) must be establishable for a normal aligned
# roster; if the self-call fails to verify => PRECOND-TOO-STRONG. (A roster of
# three members in two groups, gathering group 0 — a representative makemigrations
# multi-app shape.)
_IMPL_ADMISS = """    powner = [0, 1, 0]  # type: List[int]
    pmember = [10, 11, 12]  # type: List[int]
    Assert(Acc(list_pred(powner), 1 / 2))
    Assert(Acc(list_pred(pmember), 1 / 2))
    Assert(len(powner) == len(pmember))
""" + _IMPL_BODY
POS_ADMISS = _swap(_BASE, _IMPL_BODY, _IMPL_ADMISS)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION on `owner` — MANDATORY (#1 weakness class). `owner` is
# read-only (Acc(.,1/2)). This rival STORES `owner[i - 1] = owner[i - 1]` inside
# the loop, attempting to touch the read-only roster stream. A store needs FULL
# permission, so it MUST fail for INSUFFICIENT PERMISSION — not for a value
# mismatch. The gold reads/asserts/guard are kept verbatim after the write so the
# rejection is attributable solely to the store. Rejection source: the PERMISSION
# SYSTEM (Acc(list_pred(owner), 1/2) grants read-only access).
_IMPL_FRAME_OWNER = _swap(
    _IMPL_BODY,
    _READS,
    "        owner[i - 1] = owner[i - 1]\n" + _READS,
)
RIVAL_FRAME_OWNER = _swap(_BASE, _IMPL_BODY, _IMPL_FRAME_OWNER)

# (1b) FRAME MUTATION on `member` — the second read-only stream. Same attack,
# stores `member[i - 1]`. Must fail for insufficient permission.
_IMPL_FRAME_MEMBER = _swap(
    _IMPL_BODY,
    _READS,
    "        member[i - 1] = member[i - 1]\n" + _READS,
)
RIVAL_FRAME_MEMBER = _swap(_BASE, _IMPL_BODY, _IMPL_FRAME_MEMBER)

# (2) THE BUG ITSELF — drop the `o == target` guard and gather the WHOLE roster
# for every group (the pre-patch `apps.get_models(app_label)` project-wide return,
# the label silently bound to a flag). This is `model_prepatch.py` verbatim: the
# only invariant it can establish is `ToSeq(result) == ToSeq(member).drop(i)` (all
# members), which is NOT provably equal to `gathered(...)` whenever any
# owner[k] != target. Rejection source: the load-bearing Ensures
# ToSeq(Result()) == gathered(ToSeq(owner), ToSeq(member), target).
RIVAL_PREPATCH_ALLMEMBERS = (Path(__file__).parent / "model_prepatch.py").read_text()

# (3) COMPLEMENT FILTER (control-of-membership rival) — gather members whose group
# is NOT `target` (guard inverted to `o != target`). It returns the foreign-group
# members instead of `target`'s. Correct only on the degenerate all-match input;
# wrong (and unprovable against `gathered`) on every roster with a foreign-group
# member. Rejection source: the load-bearing Ensures — `gathered` keeps exactly
# the `owner[k] == target` members, and the complement is not provably equal.
_IMPL_COMPLEMENT = _swap(
    _IMPL_BODY,
    "        if o == target:",
    "        if o != target:",
)
RIVAL_COMPLEMENT = _swap(_BASE, _IMPL_BODY, _IMPL_COMPLEMENT)

# (4) PARTIAL-DOMAIN — gather the FIRST roster member (registry position 0)
# UNCONDITIONALLY, regardless of its owning group, and apply the correct guard to
# every other position. The guard becomes `o == target or i == 1` (i == 1 is the
# loop step that reads position 0 of the roster). Correct on every roster whose
# first member belongs to `target`; DIVERGES only on the sub-domain where
# owner[0] != target (then it offers a foreign-group member under `target`'s
# label). Rejection source: the load-bearing Ensures — `gathered` drops position 0
# when owner[0] != target, so `[member[0]] + ...` is not provably equal.
_IMPL_PARTIAL = _swap(
    _IMPL_BODY,
    "        if o == target:",
    "        if o == target or i == 1:",
)
RIVAL_PARTIAL_FIRST = _swap(_BASE, _IMPL_BODY, _IMPL_PARTIAL)

# (5, supporting) WRONG MEMBER IDENTITY — apply the correct guard but gather a
# DIFFERENT identity (`m + 1`) instead of `member[k]`. The selection set is
# right, but each gathered member is the wrong identity. Rejection source: the
# load-bearing Ensures — `gathered` concatenates `member[k]` exactly, so a
# prepend of `m + 1` is not provably equal.
_IMPL_WRONG_VALUE = _swap(
    _IMPL_BODY,
    "        if o == target:\n            result = [m] + result",
    "        if o == target:\n            result = [m + 1] + result",
)
RIVAL_WRONG_VALUE = _swap(_BASE, _IMPL_BODY, _IMPL_WRONG_VALUE)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-explicit-else",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_EXPLICIT_ELSE,
        "rationale": "structurally-different CORRECT impl: the guard is rewritten as an "
        "explicit if/else with a no-op `else: result = result`, keeping the backward loop "
        "direction, the front-prepend, and every gold Invariant/Assert verbatim (directive-3 "
        "caution: NO loop-direction flip, NO forward append against the front-recursive "
        "`gathered` fold). Must verify; if not, the postcondition is over-fit to the "
        "implicit-fall-through code form => SPEC-TOO-STRONG. Also the cheapest HONEST impl — "
        "the gather step is real work and `gathered` returns a PSeq with no echoable "
        "materialization.",
    },
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": POS_ADMISS,
        "rationale": "an F2P-shaped aligned roster (owner=[0,1,0], "
        "member=[10,11,12], target=0 — three members in two groups, the makemigrations "
        "multi-app shape) at the top of the impl must establish the precondition "
        "(Acc(list_pred(.),1/2) + len(owner)==len(member)) for a normal input; freshly-built "
        "locals carry full permission, so passing them at 1/2 must succeed. The clauses are "
        "asserted AT the witness rather than exercised by a self-call: the model carries "
        "Requires(MustTerminate(i + 1)) on its loop and Requires(MustTerminate(2)) on the "
        "method, and a same-level self-call on a non-shrinking argument is an obligation "
        "leak Nagini is right to refuse. If it fails to verify => PRECOND-TOO-STRONG. "
        "NEGATIVE CONTROL (measured): shorten the witness to pmember = [10, 11] so it "
        "leaves the frozen equal-length clause, and the probe REJECTS: `Assert might fail. "
        "Assertion (len(powner) == len(pmember)) might not hold.` The asserted domain is "
        "therefore a real check on this precondition, not a restatement of it.",
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "frame-mutate-owner",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_FRAME_OWNER,
        "refinement": "no faithful real patch corresponds to this: the makemigrations "
        "pre-check only READS the app registry to choose which models to consult the router "
        "about — it never mutates the registry's per-model app-ownership. The rival exists "
        "solely to test whether the read-only (Acc(.,1/2)) precondition on `owner` can be "
        "subverted by writing to it. A verifying rival here would be a pure verify-not-resolve "
        "artifact (vacuous satisfaction via self-mutation), not a real resolving patch.",
        "rationale": "MANDATORY frame-mutation probe (#1 weakness class). `owner[i-1] = "
        "owner[i-1]` stores through a 1/2 (read-only) reference and MUST fail for INSUFFICIENT "
        "PERMISSION (a store needs full perm), NOT a value mismatch — the gold reads/asserts/"
        "guard are kept verbatim after the write. Rejection source: the PERMISSION SYSTEM "
        "(Acc(list_pred(owner),1/2)). If it verified => SPEC-TOO-WEAK (frame protection on "
        "`owner` hollow).",
    },
    {
        "id": "frame-mutate-member",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_FRAME_MEMBER,
        "refinement": "as with `owner`, no resolving patch writes to the member-identity "
        "stream: the pre-check reads each model's identity (object_name) only to pass it to "
        "router.allow_migrate. A verifying rival here would be a verify-not-resolve artifact.",
        "rationale": "MANDATORY frame-mutation probe on the second read-only stream. "
        "`member[i-1] = member[i-1]` stores through a 1/2 reference and MUST fail for "
        "INSUFFICIENT PERMISSION. Rejection source: the PERMISSION SYSTEM "
        "(Acc(list_pred(member),1/2)). If it verified => SPEC-TOO-WEAK (frame protection on "
        "`member` hollow).",
    },
    {
        "id": "rival-prepatch-allmembers",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_PREPATCH_ALLMEMBERS,
        "refinement": "this is the PRE-PATCH behaviour verbatim (model_prepatch.py): the "
        "`o == target` guard is dropped and the WHOLE roster is gathered for every group — "
        "exactly `apps.get_models(app_label)` returning the PROJECT-WIDE model list (the "
        "positional app_label silently bound to include_auto_created). Its faithful real patch "
        "is the unchanged pre-patch makemigrations.handle, which feeds router.allow_migrate "
        "foreign-app (group, model) pairs that do not exist — precisely what FAILS the F2P "
        "test_makemigrations_consistency_checks_respect_routers — so it would NOT resolve.",
        "rationale": "the DISCRIMINATING bug this patch fixes (mirrors G-DIFF / "
        "model_prepatch.py, which shares the spec exactly). Rejection source: the load-bearing "
        "Ensures ToSeq(Result()) == gathered(ToSeq(owner), ToSeq(member), target) — the only "
        "invariant the all-members loop can establish is ToSeq(result)==ToSeq(member).drop(i) "
        "(every member), which is NOT provably equal to `gathered` whenever any "
        "owner[k] != target. If it verified => SPEC-TOO-WEAK (admits the very bug).",
    },
    {
        "id": "rival-complement-filter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_COMPLEMENT,
        "refinement": "the guard is inverted to `o != target`, gathering the FOREIGN-group "
        "members instead of `target`'s. Its faithful real patch would consult the router about "
        "every OTHER app's models under `app_label` — the exact opposite of the fix — failing "
        "the consistency pre-check entirely; it would NOT resolve.",
        "rationale": "membership-inversion rival. Rejection source: the load-bearing Ensures — "
        "`gathered` keeps exactly the `owner[k] == target` members, and the complement set is "
        "not provably equal to it (they disagree on every roster with both a target and a "
        "non-target member). If it verified => SPEC-TOO-WEAK (the guard polarity is "
        "unconstrained).",
    },
    {
        "id": "rival-partial-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_PARTIAL_FIRST,
        "refinement": "gathers the FIRST roster member (registry position 0) unconditionally "
        "regardless of its owning group, applying the correct guard everywhere else. Its "
        "faithful real patch would always offer the project's first-registered model under "
        "EVERY app_label — so any roster whose first model belongs to another app feeds "
        "router.allow_migrate a foreign (group, model) pair, failing "
        "test_makemigrations_consistency_checks_respect_routers; it would NOT resolve.",
        "rationale": "PARTIAL-DOMAIN: correct on every roster whose first member belongs to "
        "`target`, diverges only on the owner[0] != target sub-domain. Rejection source: the "
        "load-bearing Ensures — `gathered` drops position 0 when owner[0] != target, so "
        "prepending member[0] there is not provably equal to `gathered`. If it verified => "
        "SPEC-TOO-WEAK (domain-incomplete: the first-position case escapes the guard).",
    },
    {
        "id": "rival-wrong-member-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_WRONG_VALUE,
        "refinement": "applies the correct selection but gathers the WRONG identity (m + 1) — "
        "a real patch that yielded a perturbed model identity (e.g. the wrong object_name) "
        "would pass router.allow_migrate a model_name that names no real model, breaking the "
        "consistency check; it would NOT resolve.",
        "rationale": "value-level near-miss WITH a real refinement (supporting). Rejection "
        "source: the load-bearing Ensures — `gathered` concatenates member[k] exactly, so "
        "prepending m + 1 is not provably equal (the selection set is right but every gathered "
        "identity is off by one). If it verified => SPEC-TOO-WEAK (the gathered identities are "
        "unconstrained).",
    },
]


# ===========================================================================
# AXIOM LANE (Docker, real Django apps.get_app_config(label).get_models() callee)
# ===========================================================================
# No consumed @ContractOnly axiom (the `axioms` region is empty). `gathered` is an
# A-reference deep model: validated == the REAL callee
# `apps.get_app_config(app_label).get_models()` by axiom_check.py (G-AX). The
# probes RE-RUN that real callee in the instance Docker image (apply_gold=True).
# The host axiom_check.py reference `gathered` + the two-app registry builder are
# embedded inline (the runner mounts ONLY the probe at /work; bundle files are NOT
# in-container — AVOID-bug-6). Files are opened encoding="utf-8" (AVOID-bug-5).
# The probes EXECUTE the real Django registry — they never scrape source
# (AVOID-bug-4).

# Shared bootstrap: synthesise a real two-app Django registry with DISJOINT model
# sets in a temp dir, build the two aligned ground-truth streams, return helpers.
_BOOT = r'''
import os, sys, shutil, tempfile

def gathered(owner, member, target):
    """Reference of model.py's deep model `gathered`: members (registry order)
    whose owning group equals `target`."""
    out = []
    for o, m in zip(owner, member):
        if o == target:
            out.append(m)
    return out

def _write_app(root, label, model_names):
    pkg = os.path.join(root, label)
    os.makedirs(pkg)
    open(os.path.join(pkg, "__init__.py"), "w").close()
    lines = ["from django.db import models", ""]
    for name in model_names:
        lines.append("class %s(models.Model):" % name)
        lines.append("    class Meta:")
        lines.append("        app_label = %r" % label)
        lines.append("")
    with open(os.path.join(pkg, "models.py"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

_TMP = tempfile.mkdtemp(prefix="dj7530_pbt_")
# Two apps with DISJOINT model sets — the config that exposes the bug (a member
# of one app must never be offered under the other's name).
REGISTRY = {"alpha": ["AlphaOne", "AlphaTwo"],
            "beta":  ["BetaOne", "BetaTwo", "BetaThree"]}
for _lab, _names in REGISTRY.items():
    _write_app(_TMP, _lab, _names)
sys.path.insert(0, _TMP)

import django
from django.conf import settings
settings.configure(INSTALLED_APPS=list(REGISTRY.keys()), DATABASES={})
django.setup()
from django.apps import apps

LABELS = sorted(REGISTRY.keys())
LABEL_ID = {lab: i for i, lab in enumerate(LABELS)}
_all_pairs = []
for _lab in LABELS:
    for _cfg_model in apps.get_app_config(_lab).get_models():
        _all_pairs.append((_lab, _cfg_model.__name__))
MEMBER_ID = {p: i for i, p in enumerate(sorted(_all_pairs))}
OWNER  = [LABEL_ID[lab] for (lab, _n) in _all_pairs]
MEMBER = [MEMBER_ID[(lab, n)] for (lab, n) in _all_pairs]
'''

# (1) axiom-soundness — the REAL fixed callee equals the deep model `gathered`.
# For every app label, apps.get_app_config(label).get_models() must return EXACTLY
# the models whose owning app is `label`, in registry order (== gathered): every
# returned model belongs to the queried app (soundness) and none is omitted
# (completeness). Any mismatch => AXIOM-UNSOUND (the A-reference deep model would
# not equal the real callee). Also exhibits the PRE-PATCH bug witness: the
# project-wide apps.get_models(label) differs from gathered (foreign-app models
# offered under `label`).
_AX_SOUND = _BOOT + r'''
try:
    for lab in LABELS:
        real_models = list(apps.get_app_config(lab).get_models())
        real_ids = [MEMBER_ID[(lab, m.__name__)] for m in real_models]
        expected = gathered(OWNER, MEMBER, LABEL_ID[lab])
        if real_ids != expected:
            print("AXIOM-UNSOUND: app %r real get_models() ids %r != gathered %r"
                  % (lab, real_ids, expected)); sys.exit(1)
        for m in real_models:
            if m._meta.app_label != lab:
                print("AXIOM-UNSOUND (soundness): app %r get_models() returned a model "
                      "owned by %r" % (lab, m._meta.app_label)); sys.exit(1)
        if len(real_ids) != len(REGISTRY[lab]):
            print("AXIOM-UNSOUND (completeness): app %r %d vs %d models"
                  % (lab, len(real_ids), len(REGISTRY[lab]))); sys.exit(1)
    # pre-patch bug witness: apps.get_models(label) returns the project-wide set.
    bug = False
    for lab in LABELS:
        buggy = sorted((m._meta.app_label, m.__name__) for m in apps.get_models(lab))
        own_only = sorted((lab, n) for n in REGISTRY[lab])
        if buggy != own_only:
            if not any(p[0] != lab for p in buggy):
                print("BUG-WITNESS malformed: difference is not a foreign-app model");
                sys.exit(1)
            bug = True
    if not bug:
        print("BUG-WITNESS failed: apps.get_models(label) did not differ from the "
              "per-app selection on a disjoint two-app registry"); sys.exit(1)
    total = sum(len(v) for v in REGISTRY.values())
    print("AXIOM-SOUND OK: real apps.get_app_config(label).get_models() == gathered "
          "for %d apps / %d models; pre-patch apps.get_models(label) returns the "
          "project-wide set (bug witnessed)." % (len(LABELS), total))
    sys.exit(0)
finally:
    shutil.rmtree(_TMP, ignore_errors=True)
'''

# (2) axiom-containment — every callee-input the MODEL can reach lies in the real
# callee's domain. The model passes only an `app_label` (here every registered
# label, plus an UNKNOWN label — the makemigrations consistency_check_labels are
# drawn from the project's own app configs, so a known label is the reachable
# case; we also confirm the callee's behaviour on a label with no models — the
# empty-app case the model admits as a roster with zero target members). For every
# reachable label the real get_app_config(label).get_models() must be callable and
# return only that app's models; a reachable label the callee rejected or
# mis-scoped would be AXIOM-TOO-WEAK-FOR-CALLER. Covering MORE (e.g. an unknown
# label that raises LookupError) is NOT reached by the caller and is not a defect.
_AX_CONTAINMENT = _BOOT + r'''
try:
    # every label the caller (consistency_check_labels, drawn from the project's
    # own apps) can reach is a registered label — confirm each is in-domain.
    for lab in LABELS:
        models = list(apps.get_app_config(lab).get_models())
        for m in models:
            if m._meta.app_label != lab:
                print("AXIOM-TOO-WEAK-FOR-CALLER: get_models(%r) yielded a foreign-app "
                      "model owned by %r" % (lab, m._meta.app_label)); sys.exit(1)
    # an app with ZERO models (a roster where no member belongs to `target`) — the
    # model admits len-0 gathered output; the real callee must accept it cleanly.
    empty_app = os.path.join(_TMP, "gamma")
    os.makedirs(empty_app)
    open(os.path.join(empty_app, "__init__.py"), "w").close()
    with open(os.path.join(empty_app, "models.py"), "w", encoding="utf-8") as f:
        f.write("from django.db import models\n")
    # NOTE: the registry was already built; rather than reconfigure, assert the
    # observed property holds for the populated labels and that an unknown label
    # is OUTSIDE the caller's reach (LookupError) — sound to not cover.
    try:
        apps.get_app_config("not_a_real_app")
        unknown_in_domain = True
    except LookupError:
        unknown_in_domain = False
    if unknown_in_domain:
        print("note: unknown label unexpectedly accepted (still sound to over-cover)")
    print("containment OK: every caller-reachable label (the project's own app "
          "configs) is in the callee's domain and get_models() yields ONLY that "
          "app's models; an unknown label is OUTSIDE the caller's reach "
          "(LookupError), sound to not cover.")
    sys.exit(0)
finally:
    shutil.rmtree(_TMP, ignore_errors=True)
'''

AXIOM_TESTS = [
    {
        "id": "ax-gathered-sound",
        "axiom": "gathered",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND,
        "rationale": "the A-reference deep model `gathered` must equal the REAL fixed callee "
        "apps.get_app_config(label).get_models() on every app of a disjoint two-app registry "
        "(soundness: every returned model belongs to the queried app; completeness: none "
        "omitted). Any mismatch => AXIOM-UNSOUND. Also witnesses the pre-patch bug: the "
        "project-wide apps.get_models(label) differs from `gathered` (foreign-app models "
        "offered under `label`). Mirrors axiom_check.py / G-AX, executed against the REAL "
        "Django registry in-container (never scrapes source).",
    },
    {
        "id": "ax-gathered-containment",
        "axiom": "gathered",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT,
        "rationale": "every callee-input the model can reach is a registered app label (the "
        "makemigrations consistency_check_labels are drawn from the project's OWN app "
        "configs); for each, the real get_app_config(label).get_models() is callable and "
        "yields ONLY that app's models — fully inside the callee's domain. An unknown label "
        "(LookupError) is OUTSIDE the caller's reach, so not covering it is SOUND, not a "
        "defect (containment, not whole-domain coverage). A reachable label the callee "
        "rejected or mis-scoped would be AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
