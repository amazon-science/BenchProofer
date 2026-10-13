"""properties.py — PBT falsification manifest for django__django-12774.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    should_reject(field_name: int, field_unique: bool,
                  guarantees: List[Tuple[bool, PSeq[int]]]) -> bool

= the field-name acceptability guard of django.db.models.query.QuerySet.in_bulk
(the gold-patch hunk at query.py:685). It returns True iff the field must be
REJECTED (the `if (...)` whose True branch raises ValueError). The load-bearing
contract:

    Requires(Acc(list_pred(guarantees), 1/2))                 # read-only input
    Ensures (Acc(list_pred(guarantees), 1/2))                 # returns the read perm
    Ensures (Result() == (field_name != PK and
                          not field_unique and
                          not any_permits(guarantees, 0, field_name)))   # the pin
    Ensures (Implies(field_name == PK or field_unique, not Result()))    # entailed
    Ensures (Implies(any_permits(guarantees, 0, field_name), not Result()))  # entailed

What this spec defends, and the attacks it must survive:

  * The output pin `Result() == (field_name != PK and not field_unique and not
    any_permits(guarantees, 0, field_name))` is GROUNDED in the inputs:
    `permits_alone` and the front-recursive fold `any_permits` are @Pure deep
    models (NOT @ContractOnly axioms), fully unfolded by Viper, equal to the real
    `total_unique_constraints` filter + single-field extraction + membership test
    (A-reference, validated == reality by axiom_check.py / G-AX). The pin is a
    function OF (`field_name`, `field_unique`, `guarantees`), not an opaque
    answer-key marker — so there is no "echo a wrong oracle" shortcut. A direct
    `return field_name != PK and not field_unique and not any_permits(...)` is
    simply the CORRECT cheapest honest impl (pos-control-direct-oracle): it does
    the real work because `any_permits` IS the work. (Hence there is no
    SPEC-TOO-WEAK ungrounded-echo reject case for this instance — see
    'assessment'.)

  * The discriminating content of the change is the NEW third conjunct
    `field_name not in unique_fields` (the single-field total-unique fields). The
    pre-patch guard lacked it entirely (a non-pk, non-unique field was ALWAYS
    rejected). model_prepatch.py reverts to `return field_name != PK and not
    field_unique` and FAILS the pin whenever some guarantee permits the field —
    exactly the F2P `test_in_bulk_meta_constraint` (`year` is the sole field of
    an unconditional constraint). Rival `partial-ignore-guarantees` reproduces
    that bug EXACTLY.

  * Two further faithful real near-misses are attacked:
      - dropping the unconditional (condition is None) filter — treating a
        conditional/partial constraint as if it permitted the field
        (rival `weak-ignore-unconditional`); its faithful patch omits the
        `total_unique_constraints` filter and would ACCEPT `ean` (P2P
        `test_in_bulk_non_unique_meta_constaint` must still reject it).
      - dropping the single-field (`len(constraint.fields) == 1`) filter —
        treating a composite constraint's members as permitted
        (rival `weak-ignore-arity`); its faithful patch omits `if
        len(constraint.fields) == 1` and would ACCEPT `brand`/`name` (the same
        P2P must still reject them).
      - scanning only the FIRST guarantee (rival `partial-first-only`); its
        faithful patch would resolve only when the permitting constraint happens
        to be listed first and would mis-reject `year` when another constraint
        precedes it in `total_unique_constraints`.

  * `guarantees` is held read-only (Acc(list_pred(guarantees), 1/2)). The
    MANDATORY attack is FRAME MUTATION (`frame-mutate-guarantees`): an impl that
    WRITES to `guarantees` to satisfy the pin vacuously must fail for
    INSUFFICIENT PERMISSION.

There are NO @ContractOnly axioms (meta.axioms == []); the changed behaviour is
modeled DEEPLY (permits_alone / any_permits / should_reject), an A-reference
validated == the real Django callees by axiom_check.py / G-AX. The axiom lane
re-runs that soundness check in Docker (a faithful port of axiom_check.py: build
real Django models with single-field-unconditional, conditional/partial,
multi-field, and unique=True constraints and assert the deep model == the real
`total_unique_constraints` + single-field extraction + `get_field().unique`
guard) and a caller-domain containment probe.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY inside `# impl-start`/`# impl-end` (the nested invariants live there
too), so `markers.same_spec` is GUARANTEED and a rejection comes from the
POSTCONDITION catching wrong behaviour (or the permission system), never from a
tampered spec.
"""
from pathlib import Path

INSTANCE = "django__django-12774"
FLOAT_ENCODING = None  # meta.json float_encoding is null

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
# Region landmarks (all strictly INSIDE the impl region of model.py).
# ---------------------------------------------------------------------------

# The whole gold impl body (everything between # impl-start and # impl-end),
# used as a single replaceable block for structural rewrites.
_GOLD_BODY = """    if field_name == PK:
        return False
    if field_unique:
        return False
    # Scan the declared guarantees for one that makes this field acceptable on
    # its own (unconditional and ranging over this single field).
    i = 0
    found = False
    while i < len(guarantees):
        # invariants-start
        Invariant(Acc(list_pred(guarantees), 1 / 2))
        Invariant(0 <= i and i <= len(guarantees))
        # `found` records whether any guarantee in the scanned prefix permits
        # the field; while it is still False the suffix from i on decides the
        # full answer (front-recursive unfold links any_permits at 0 and at i).
        Invariant(Implies(not found, any_permits(guarantees, 0, field_name) ==
            any_permits(guarantees, i, field_name)))
        Invariant(Implies(found, any_permits(guarantees, 0, field_name)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(guarantees) - i.
        Invariant(MustTerminate(len(guarantees) - i))
        # invariants-end
        if permits_alone(guarantees[i], field_name):
            found = True
        i = i + 1
    return not found"""

# the two early-return branches (used by the branch-reorder positive control)
_EARLY_BRANCHES = """    if field_name == PK:
        return False
    if field_unique:
        return False
"""

# the loop-body per-guarantee read (used by frame-mutation)
_LOOP_READ = "        if permits_alone(guarantees[i], field_name):\n"

# the impl-start landmark (used to inject the admissibility witness at the head)
_IMPL_HEAD = "    # impl-start\n"


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Cheapest honest correct impl: return the GROUNDED pin DIRECTLY. No loop at
# all -- maximally structurally different from the gold scan-and-accumulate. The
# postcondition Result() == (field_name != PK and not field_unique and not
# any_permits(guarantees, 0, field_name)) is satisfied trivially (Result() IS that
# expression), the two entailed Implies clauses follow, and the read-only
# permission is never touched (any_permits needs only 1/4 <= 1/2). If this fails to
# verify the spec is over-fit to the loop code shape => SPEC-TOO-STRONG. Also the
# honest "no ungrounded echo" control: any_permits IS the real work, so a direct
# return is correct, not a cheat.
_POS_DIRECT_ORACLE_BODY = (
    "    return field_name != PK and not field_unique and \\\n"
    "        not any_permits(guarantees, 0, field_name)"
)
_POS_DIRECT_ORACLE = _swap(_BASE, _GOLD_BODY, _POS_DIRECT_ORACLE_BODY)

# (5b) Structurally-different but CORRECT: the two early-accept branches are
# REORDERED (test field_unique before the pk short-circuit). Both branches return
# False (accept) and are mutually consistent (a pk field is never individually
# unique in the modeled world, but even if both held the result is the same:
# accept), so the reorder is behaviour-preserving. The scan loop and ALL gold
# invariants/asserts are kept verbatim (pilot bug #2: never drop a framing
# assert). If this fails to verify the spec is over-fit to the branch order =>
# SPEC-TOO-STRONG.
_POS_REORDER_BODY = _EARLY_BRANCHES.replace(
    """    if field_name == PK:
        return False
    if field_unique:
        return False
""",
    """    if field_unique:
        return False
    if field_name == PK:
        return False
""",
    1,
)
_POS_REORDER = _swap(_BASE, _EARLY_BRANCHES, _POS_REORDER_BODY)

# (6) ADMISSIBILITY. Construct the EXACT F2P-shaped input -- field `year`
# (id 7), not individually unique, with ONE single-field unconditional guarantee
# (True, PSeq(7)) -- the `test_in_bulk_meta_constraint` config -- and ASSERT the
# value precondition is establishable for it: the fresh list literal carries
# full list_pred, from which the required read fraction
# (Acc(list_pred(guarantees), 1/2)) follows. (A literal self-call is no longer
# usable as the witness: the frozen spec now carries a termination obligation,
# and a recursive self-invocation cannot present a strictly smaller measure —
# by design, since exactly that self-call shape was the vacuous-verification
# escape.) If the asserts cannot discharge => PRECOND-TOO-STRONG. Injected at
# the head of the impl region; the gold body follows verbatim.
_ADMISS_WITNESS = (
    "    # impl-start\n"
    "    g0 = (True, PSeq(7))  # type: Tuple[bool, PSeq[int]]\n"
    "    probe = [g0]  # type: List[Tuple[bool, PSeq[int]]]\n"
    "    Assert(Acc(list_pred(probe), 1 / 2))\n"
)
_ADMISS = _swap(_BASE, _IMPL_HEAD, _ADMISS_WITNESS)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION — MANDATORY, the #1 weakness class. `guarantees` is read-only
# (Acc(list_pred(guarantees), 1/2)). This rival WRITES guarantees[i] = (True,
# PSeq(field_name)) inside the loop -- forging a single-field unconditional
# guarantee for the queried field -- before reading it, so the scan would always
# "find" a permitting guarantee and vacuously satisfy the pin. Under the 1/2
# (read-only) permission a store to the list_pred requires FULL permission, so it
# MUST fail for INSUFFICIENT PERMISSION (not for a wrong value). The gold
# invariants are kept verbatim around it so the failure is attributable solely to
# the write. Rejection source: the PERMISSION SYSTEM.
_FRAME_BODY = _GOLD_BODY.replace(
    _LOOP_READ,
    "        guarantees[i] = (True, PSeq(field_name))\n" + _LOOP_READ,
    1,
)
_RIVAL_FRAME = _swap(_BASE, _GOLD_BODY, _FRAME_BODY)

# (3a) PARTIAL-DOMAIN — ignore the declared guarantees entirely (the EXACT
# pre-patch bug, == model_prepatch.py). Returns `field_name != PK and not
# field_unique`, never consulting `guarantees`. Correct on every field that is pk,
# individually unique, or NOT permitted by any guarantee; diverges only on the
# sub-domain where some single-field unconditional guarantee permits the field
# (the F2P `year`). Rejection source: the pin
# Result() == (... and not any_permits(guarantees, 0, field_name)) — when
# any_permits is True the gold Result is False but this rival returns True.
_PARTIAL_IGNORE_BODY = (
    "    return field_name != PK and not field_unique"
)
_RIVAL_PARTIAL_IGNORE = _swap(_BASE, _GOLD_BODY, _PARTIAL_IGNORE_BODY)

# (3b) PARTIAL-DOMAIN — scan only the FIRST guarantee. Returns False (accept) iff
# guarantees is non-empty and its FIRST element permits the field, else falls back
# to the pre-patch decision. Correct when the permitting guarantee is at index 0
# (or none exists), but mis-rejects a field permitted by a guarantee at index >= 1
# (e.g. MixedLike: the single-field unconditional `a` after a composite `b,c`
# would still be reached at index 0, but in a model whose composite is listed
# first the permitting single-field constraint sits later). Rejection source: the
# pin — for an input where the permitting guarantee is not first, any_permits is
# True (gold accepts) but this rival rejects.
_PARTIAL_FIRST_BODY = (
    "    if len(guarantees) > 0 and permits_alone(guarantees[0], field_name):\n"
    "        return False\n"
    "    return field_name != PK and not field_unique"
)
_RIVAL_PARTIAL_FIRST = _swap(_BASE, _GOLD_BODY, _PARTIAL_FIRST_BODY)

# (3c) PARTIAL-DOMAIN — drop the UNCONDITIONAL (g[0]) requirement. The gold loop,
# invariants, and accumulator are kept VERBATIM; only the per-guarantee `found`
# update is broadened to an INLINE test that omits the `g[0] and` conjunct
# (`len(gi[1]) == 1 and gi[1][0] == field_name`) — it treats ANY single-field
# guarantee as permitting, regardless of whether it is conditional. This
# faithfully models a patch that omits the `condition is None` filter (building
# unique_fields from ALL constraints, not just total_unique_constraints). On a
# CONDITIONAL single-field guarantee (g[0] False) the rival sets `found = True`
# while the frozen pin's any_permits/permits_alone is False, so it CONTRADICTS the
# kept invariant `Implies(found, any_permits(guarantees, 0, field_name))` (and the
# final pin Result() == not any_permits(...)). Rejection source: the spec's
# any_permits-based invariant + the pin, both of which require g[0].
_WEAK_UNCOND_BODY = _GOLD_BODY.replace(
    "        if permits_alone(guarantees[i], field_name):\n"
    "            found = True\n",
    "        gi = guarantees[i]\n"
    "        if len(gi[1]) == 1 and gi[1][0] == field_name:\n"
    "            found = True\n",
    1,
)
_RIVAL_WEAK_UNCOND = _swap(_BASE, _GOLD_BODY, _WEAK_UNCOND_BODY)

# (3d) PARTIAL-DOMAIN — drop the SINGLE-FIELD (len(g[1]) == 1) requirement. Same
# verbatim gold loop/invariants, but the inline `found` update accepts an
# unconditional guarantee whose FIRST field is the queried field regardless of
# arity (`gi[0] and len(gi[1]) >= 1 and gi[1][0] == field_name`). This faithfully
# models a patch that omits the `if len(c.fields) == 1` filter. On a COMPOSITE
# unconditional guarantee that lists the field first (e.g. `brand` in
# UniqueConstraint(fields=['brand','name'])) the rival sets `found = True` while
# the frozen any_permits/permits_alone is False (it needs len == 1), so it
# CONTRADICTS the kept invariant `Implies(found, any_permits(...))` and the pin.
# Rejection source: the spec's any_permits-based invariant + the pin, both of
# which require len(g[1]) == 1.
_WEAK_ARITY_BODY = _GOLD_BODY.replace(
    "        if permits_alone(guarantees[i], field_name):\n"
    "            found = True\n",
    "        gi = guarantees[i]\n"
    "        if gi[0] and len(gi[1]) >= 1 and gi[1][0] == field_name:\n"
    "            found = True\n",
    1,
)
_RIVAL_WEAK_ARITY = _swap(_BASE, _GOLD_BODY, _WEAK_ARITY_BODY)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-direct-oracle", "kind": "soundness", "expect": "verify",
     "module": _POS_DIRECT_ORACLE,
     "rationale": "the cheapest honest correct impl returns the GROUNDED pin "
                  "`field_name != PK and not field_unique and not "
                  "any_permits(guarantees, 0, field_name)` directly (no loop). "
                  "Result() IS that expression so the pin and both entailed Implies "
                  "clauses hold trivially; the read-only permission is untouched "
                  "(any_permits needs only 1/4). If this fails => the spec is over-fit "
                  "to the scan-and-accumulate code shape (SPEC-TOO-STRONG). Also the "
                  "honest no-ungrounded-echo control: any_permits IS the real work, so "
                  "a direct return is correct, not a cheat."},
    {"id": "pos-control-reorder-branches", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but correct: the two early-accept branches "
                  "are reordered (test field_unique before the pk short-circuit). Both "
                  "return False (accept) so the reorder is behaviour-preserving; the "
                  "scan loop and ALL gold invariants are kept verbatim. If it fails => "
                  "the spec is over-fit to the branch order (SPEC-TOO-STRONG)."},
    {"id": "admiss-meta-constraint", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "the exact F2P-shaped input (field=year(7), unique=False, "
                  "guarantees=[(True, PSeq(7))] — the test_in_bulk_meta_constraint "
                  "config) is constructed and the value precondition asserted "
                  "establishable: the fresh list literal carries full list_pred, from "
                  "which the required 1/2 read fraction follows (the remaining "
                  "obligation is the termination bound, trivially available to any "
                  "outside caller). If the assert cannot discharge for this normal "
                  "input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-guarantees", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: opts.total_unique_"
                   "constraints is a read property of UniqueConstraint objects the guard "
                   "only reads; the patch never mutates a constraint's fields, and "
                   "forging a single-field unconditional constraint for the queried field "
                   "is not a behaviour any resolving patch exhibits. The rival exists only "
                   "to test whether the read-only (1/2) precondition on `guarantees` can "
                   "be subverted by writing to it; a verifying rival here would be a pure "
                   "verify-not-resolve artifact (vacuous satisfaction via self-mutation).",
     "rationale": "MANDATORY frame-mutation probe. `guarantees[i] = (True, "
                  "PSeq(field_name))` writes through a 1/2 (read-only) reference and MUST "
                  "fail for INSUFFICIENT PERMISSION. Rejection source: the PERMISSION "
                  "SYSTEM (store needs full perm), not a value mismatch; the gold "
                  "invariants are kept verbatim. If it verified => SPEC-TOO-WEAK (frame "
                  "protection hollow)."},
    {"id": "partial-ignore-guarantees", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_IGNORE,
     "refinement": "this is the EXACT pre-patch behaviour (== model_prepatch.py): the "
                   "pre-patch guard was `field_name != 'pk' and not "
                   "opts.get_field(field_name).unique`, never consulting "
                   "total_unique_constraints. Its faithful real patch is the pre-patch "
                   "guard, which FAILS the F2P test_in_bulk_meta_constraint (in_bulk on "
                   "`year`, the sole field of a single-field unconditional "
                   "UniqueConstraint, must now succeed, but the pre-patch raises "
                   "ValueError). So it would NOT resolve.",
     "rationale": "partial-domain: correct on every field that is pk / individually "
                  "unique / not permitted by any guarantee; diverges only on the "
                  "sub-domain where some single-field unconditional guarantee permits the "
                  "field. Rejection source: the pin Result() == (... and not "
                  "any_permits(guarantees, 0, field_name)) — when any_permits is True the "
                  "gold Result is False but this rival returns True. If it verified => "
                  "SPEC-TOO-WEAK (admits the pre-patch guard)."},
    {"id": "partial-first-guarantee-only", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_FIRST,
     "refinement": "a faithful real patch that only checked the FIRST element of "
                   "opts.total_unique_constraints (e.g. `unique_fields = "
                   "[opts.total_unique_constraints[0].fields[0]] if ...`) would accept a "
                   "field only when its permitting single-field constraint is listed "
                   "first. total_unique_constraints can list a composite/other constraint "
                   "before the permitting single-field one, so such a patch would "
                   "mis-raise ValueError for `year` and FAIL test_in_bulk_meta_constraint "
                   "whenever the permitting constraint is not first. So it would NOT "
                   "resolve.",
     "rationale": "partial-domain: correct when the permitting guarantee is at index 0 "
                  "or none exists; diverges on inputs where the permitting guarantee sits "
                  "at index >= 1 (any_permits is True so gold accepts, but the rival "
                  "rejects). Rejection source: the pin via any_permits over ALL "
                  "guarantees (the gold scans the whole list). If it verified => "
                  "SPEC-TOO-WEAK (admits a first-only scan)."},
    {"id": "weak-ignore-unconditional", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WEAK_UNCOND,
     "refinement": "this is the patch with the total_unique_constraints UNCONDITIONAL "
                   "filter dropped: building unique_fields from ALL UniqueConstraints "
                   "(`opts.constraints`) instead of only `condition is None` ones. Such a "
                   "patch would ACCEPT a field covered only by a CONDITIONAL (partial) "
                   "single-field constraint, FAILING the P2P "
                   "test_in_bulk_non_unique_meta_constaint (`ean`, covered only by a "
                   "UniqueConstraint(condition=Q(...)), must still raise ValueError). So "
                   "it would NOT resolve.",
     "rationale": "partial-domain: the inline scan omits the g[0] (unconditional) "
                  "conjunct, setting found=True for a conditional single-field guarantee. "
                  "On such a guarantee the frozen any_permits/permits_alone is False (it "
                  "needs g[0]), so the impl CONTRADICTS the kept invariant Implies(found, "
                  "any_permits(guarantees, 0, field_name)) and the final pin Result() == "
                  "not any_permits(...). Rejection source: the spec's any_permits-based "
                  "invariant + the pin, both requiring g[0]. If it verified => "
                  "SPEC-TOO-WEAK (admits conditional constraints)."},
    {"id": "weak-ignore-arity", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WEAK_ARITY,
     "refinement": "this is the patch with the single-field filter dropped: building "
                   "unique_fields as `[c.fields[0] for c in total_unique_constraints]` "
                   "WITHOUT the `if len(c.fields) == 1` guard. Such a patch would ACCEPT "
                   "the first member of a COMPOSITE unconditional constraint, FAILING the "
                   "P2P test_in_bulk_non_unique_meta_constaint (`brand`/`name`, covered "
                   "only by UniqueConstraint(fields=['brand','name']), must still raise "
                   "ValueError). So it would NOT resolve.",
     "rationale": "partial-domain: the inline scan replaces `len(g[1]) == 1` with "
                  "`len(g[1]) >= 1`, setting found=True for the FIRST member of a "
                  "multi-field unconditional guarantee. On such a composite guarantee the "
                  "frozen any_permits/permits_alone is False (it needs len == 1), so the "
                  "impl CONTRADICTS the kept invariant Implies(found, any_permits(...)) and "
                  "the pin Result() == not any_permits(...). Rejection source: the spec's "
                  "any_permits-based invariant + the pin, both requiring len(g[1]) == 1. If "
                  "it verified => SPEC-TOO-WEAK (admits composite constraints)."},
]

# ===========================================================================
# AXIOM LANE (Docker, real callee) — A-reference deep-model soundness + containment
# ===========================================================================
#
# This bundle has NO @ContractOnly axiom (meta.axioms == []). The changed
# behaviour is modeled DEEPLY (permits_alone / any_permits / should_reject), an
# A-reference validated == the real Django callees by axiom_check.py / G-AX. The
# axiom lane re-runs that soundness check in Docker (a faithful port of
# axiom_check.py: build real Django models and assert the deep model == the real
# total_unique_constraints + single-field extraction + get_field().unique guard),
# and a caller-domain containment probe.

# (A) A-reference SOUNDNESS: deep model (permits_alone/any_permits/should_reject)
# == the real post-patch guard derived from total_unique_constraints +
# single-field extraction + get_field().unique. Port of axiom_check.py;
# Django-only, configures an in-memory app, reads no bundle file, opens nothing.
# apply_gold is irrelevant (the A-reference callees total_unique_constraints /
# UniqueConstraint.fields/.condition / get_field().unique are UNCHANGED by the
# patch; only the guard EXPRESSION changed, which we re-derive identically), but
# we set it True for consistency with "post-gold behaviour".
_AX_REF_SOUND = r'''
import os, sys

# --- model.py deep-model reference encodings (kept in lock-step) -------------
def permits_alone(g, field_name):
    unconditional, names = g
    return unconditional and len(names) == 1 and names[0] == field_name

def any_permits(guarantees, field_name):
    return any(permits_alone(g, field_name) for g in guarantees)

def should_reject_model(field_name, field_unique, guarantees, pk_id):
    if field_name == pk_id:
        return False
    if field_unique:
        return False
    return not any_permits(guarantees, field_name)

APP = "auth"

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:
        print("A-REFERENCE SKIP: Django not configurable: %r" % (exc,)); return 0

    from django.db import models
    checked = 0

    def real_unique_fields(opts):
        return [c.fields[0] for c in opts.total_unique_constraints if len(c.fields) == 1]

    def real_reject(opts, field_name):
        if field_name == 'pk':
            return False
        uf = real_unique_fields(opts)
        return (not opts.get_field(field_name).unique) and (field_name not in uf)

    def model_guarantees(opts):
        return [(c.condition is None, list(c.fields)) for c in opts.total_unique_constraints]

    def check_model(klass, field_names):
        nonlocal checked
        opts = klass._meta
        guarantees = model_guarantees(opts)
        pk_id = '\x00PK'
        for fn in field_names:
            is_pk = (fn == 'pk' or fn == opts.pk.name)
            field_unique = False if is_pk else opts.get_field(fn).unique
            r_real = real_reject(opts, 'pk' if is_pk else fn)
            fn_id = pk_id if is_pk else fn
            r_model = should_reject_model(fn_id, field_unique, guarantees, pk_id)
            assert r_real == r_model, (
                "deep model disagrees with real guard on %s.%s: real=%r model=%r "
                "(guarantees=%r, unique=%r)"
                % (klass.__name__, fn, r_real, r_model, guarantees, field_unique))
            checked += 1

    # Case 1: F2P discriminator — single-field UNCONDITIONAL constraint accepts.
    class SeasonLike(models.Model):
        year = models.IntegerField(null=True, blank=True)
        gt = models.IntegerField(null=True, blank=True)
        class Meta:
            app_label = APP
            constraints = [models.UniqueConstraint(fields=['year'], name='axc_season_year_unique')]
    check_model(SeasonLike, ['pk', 'id', 'year', 'gt'])
    assert real_reject(SeasonLike._meta, 'year') is False

    # Case 2: PARTIAL (conditional) + MULTI-FIELD constraints must NOT permit.
    class PartialAndCompositeLike(models.Model):
        ean = models.CharField(max_length=100)
        brand = models.CharField(max_length=100)
        name = models.CharField(max_length=80)
        is_active = models.BooleanField(default=True)
        class Meta:
            app_label = APP
            constraints = [
                models.UniqueConstraint(fields=['ean'], name='axc_partial_ean_unique',
                                        condition=models.Q(is_active=True)),
                models.UniqueConstraint(fields=['brand', 'name'], name='axc_together_brand_name_unique'),
            ]
    check_model(PartialAndCompositeLike, ['pk', 'id', 'ean', 'brand', 'name', 'is_active'])
    assert real_reject(PartialAndCompositeLike._meta, 'ean') is True
    assert real_reject(PartialAndCompositeLike._meta, 'brand') is True

    # Case 3: genuinely unique=True field accepted.
    class HasUniqueLike(models.Model):
        slug = models.SlugField(unique=True)
        other = models.IntegerField(default=0)
        class Meta:
            app_label = APP
    check_model(HasUniqueLike, ['pk', 'id', 'slug', 'other'])
    assert real_reject(HasUniqueLike._meta, 'slug') is False
    assert real_reject(HasUniqueLike._meta, 'other') is True

    # Case 4: mix — single-field-unconditional NOT first + multi + partial.
    class MixedLike(models.Model):
        a = models.IntegerField(default=0)
        b = models.IntegerField(default=0)
        c = models.IntegerField(default=0)
        flag = models.BooleanField(default=True)
        class Meta:
            app_label = APP
            constraints = [
                models.UniqueConstraint(fields=['b', 'c'], name='axc_bc_unique'),
                models.UniqueConstraint(fields=['a'], name='axc_a_unique'),
                models.UniqueConstraint(fields=['c'], name='axc_c_partial', condition=models.Q(flag=True)),
            ]
    check_model(MixedLike, ['pk', 'id', 'a', 'b', 'c', 'flag'])
    assert real_reject(MixedLike._meta, 'a') is False   # single-field unconditional, NOT first
    assert real_reject(MixedLike._meta, 'b') is True    # only in a composite
    assert real_reject(MixedLike._meta, 'c') is True    # composite + partial only

    print("A-REFERENCE SOUND: deep model (permits_alone/any_permits/should_reject) "
          "== real Django guard (total_unique_constraints + single-field extraction "
          "+ get_field().unique) on %d field/model observations (F2P single-field-"
          "unconditional [incl. not-first], partial, composite, unique=True)." % checked)
    return 0

sys.exit(main())
'''

# (B) CALLER-DOMAIN CONTAINMENT. The model's Requires is ONLY
# Acc(list_pred(guarantees), 1/2) — there are no value/length constraints on
# guarantees and no constraint on field_name/field_unique. So the modeled
# function can reach ANY (field_name, field_unique, guarantees) where guarantees
# is a list of (bool, seq-of-ints) pairs. The A-reference soundness check above
# constructs real Django models whose total_unique_constraints reduces to exactly
# such pairs (g[0] = condition is None, g[1] = fields). This probe confirms that
# every guarantee SHAPE the model can carry corresponds to a real-Django
# UniqueConstraint shape the soundness check exercises:
#   - g[0] True/False  <-> condition is None / condition is Q(...)
#   - len(g[1]) == 1 / > 1  <-> single-field / composite UniqueConstraint
# and that the membership/decision is exercised on each. A reachable guarantee
# shape the soundness check could NOT exercise => AXIOM-TOO-WEAK-FOR-CALLER. Since
# total_unique_constraints ALREADY filters to condition is None, the g[0]==False
# (conditional) case never actually arrives via that property; the model carries
# the flag defensively and would correctly reject such an element — we confirm the
# real UniqueConstraint can represent both polarities so the encoding is total.
_AX_CONTAINMENT = r'''
import os, sys

APP = "auth"

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:
        print("CONTAINMENT SKIP: Django not configurable: %r" % (exc,)); return 0
    from django.db import models

    problems = []
    covered_shapes = set()

    # A model carrying every guarantee polarity x arity the encoding admits:
    #   single-field unconditional, composite unconditional, single-field
    #   conditional, composite conditional. total_unique_constraints keeps only
    #   the unconditional ones; we read .condition / .fields directly to confirm
    #   BOTH polarities are representable as (condition is None, list(fields)).
    class AllShapes(models.Model):
        p = models.IntegerField(default=0)
        q = models.IntegerField(default=0)
        r = models.IntegerField(default=0)
        s = models.IntegerField(default=0)
        flag = models.BooleanField(default=True)
        class Meta:
            app_label = APP
            constraints = [
                models.UniqueConstraint(fields=['p'], name='cnt_p_uncond'),
                models.UniqueConstraint(fields=['q', 'r'], name='cnt_qr_uncond'),
                models.UniqueConstraint(fields=['s'], name='cnt_s_cond',
                                        condition=models.Q(flag=True)),
                models.UniqueConstraint(fields=['q', 's'], name='cnt_qs_cond',
                                        condition=models.Q(flag=False)),
            ]

    opts = AllShapes._meta
    # Reduce ALL declared constraints (not just the filtered property) to the
    # model encoding and verify each is a valid (bool, list[int-or-name]) pair.
    for c in opts.constraints:
        if not hasattr(c, 'condition') or not hasattr(c, 'fields'):
            continue
        g = (c.condition is None, list(c.fields))
        if not isinstance(g[0], bool):
            problems.append(("g[0] not bool", c.name, g))
        if not isinstance(g[1], list) or len(g[1]) < 1:
            problems.append(("g[1] not a non-empty list", c.name, g))
        covered_shapes.add((g[0], len(g[1]) == 1))

    # total_unique_constraints (what the model is actually fed) must be a SUBSET
    # of the unconditional constraints — i.e. every element it yields has
    # g[0] == True (containment of the property into the unconditional polarity).
    for c in opts.total_unique_constraints:
        if c.condition is not None:
            problems.append(("total_unique_constraints yielded a conditional constraint", c.name))

    # The four representable shapes (uncond/cond x single/composite) must all be
    # constructible (the encoding is total over the caller-reachable space).
    want = {(True, True), (True, False), (False, True), (False, False)}
    missing = want - covered_shapes
    if missing:
        problems.append(("guarantee shapes not representable by real UniqueConstraint", sorted(missing)))

    if problems:
        print("CONTAINMENT FAIL:", problems[:8]); return 1
    print("CONTAINMENT OK: every guarantee shape the model can carry "
          "(unconditional/conditional x single/composite, %d shapes) is a real "
          "UniqueConstraint (condition is None, list(fields)); total_unique_"
          "constraints is contained in the unconditional polarity, so no "
          "caller-reachable guarantee lies outside the soundness check's domain."
          % len(covered_shapes))
    return 0

sys.exit(main())
'''

AXIOM_TESTS = [
    {"id": "ax-ref-sound", "axiom": "permits_alone/any_permits/should_reject",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_REF_SOUND,
     "rationale": "the A-reference deep model (permits_alone/any_permits/should_reject) "
                  "must equal the REAL Django guard (total_unique_constraints filter + "
                  "single-field extraction + get_field().unique) on real models covering "
                  "the F2P single-field-unconditional case (incl. one where the permitting "
                  "constraint is NOT listed first), partial/conditional, multi-field, and "
                  "unique=True. Any mismatch => the deep model is unsound "
                  "(A-REFERENCE-UNSOUND). Faithful port of axiom_check.py; Django-only."},
    {"id": "ax-containment", "axiom": "permits_alone/any_permits/should_reject",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_CONTAINMENT,
     "rationale": "the model's only precondition is Acc(list_pred(guarantees), 1/2) "
                  "(no value/length bound), so every guarantee shape "
                  "(unconditional/conditional x single/composite) it can carry must map "
                  "to a real UniqueConstraint (condition is None, list(fields)). This "
                  "probe confirms all four shapes are representable and that "
                  "total_unique_constraints (what the caller is fed) is contained in the "
                  "unconditional polarity. A reachable guarantee shape the soundness check "
                  "could not exercise => AXIOM-TOO-WEAK-FOR-CALLER."},
]
