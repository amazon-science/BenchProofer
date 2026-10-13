"""properties.py — PBT falsification manifest for django__django-11400.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. Two byte-identical functions are under spec

    related_choice_rows(base: List[int], ordering: List[int]) -> List[int]
    reverse_choice_rows(base: List[int], ordering: List[int]) -> List[int]

modeling `Field.get_choices` / `ForeignObjectRel.get_choices` after the gold
patch `if ordering: qs = qs.order_by(*ordering)`: the queryset is reordered ONLY
when an explicit ordering is supplied; otherwise the base manager order (its
`Meta.ordering`) is preserved verbatim. The load-bearing contract (both fns):

    Requires(Acc(list_pred(base),     1/2))                # READ-ONLY base
    Requires(Acc(list_pred(ordering), 1/2))                # READ-ONLY ordering
    Ensures (Acc(list_pred(base),     1/2))
    Ensures (Acc(list_pred(ordering), 1/2))
    Ensures (Acc(list_pred(Result())))
    Ensures (Implies(len(ordering)==0, ToSeq(Result())==ToSeq(base)))         # EMPTY pin
    Ensures (Implies(len(ordering)>0,
                     ToSeq(Result())==reordered(ToSeq(base),ToSeq(ordering))))# REORDER pin

What the spec actually defends, and the attacks it must survive:

  * The DISCRIMINATING clause is the EMPTY pin
    `Implies(len(ordering)==0, ToSeq(Result())==ToSeq(base))`. The pre-patch code
    applied `.order_by(*ordering)` UNCONDITIONALLY; with an empty ordering this
    routes the result through `reordered(base, [])`, which the `reordered` axiom
    deliberately does NOT tie to `base` (an empty `order_by()` CLEARS the base
    `Meta.ordering` — see G-AX / axiom_check.py). `model_prepatch.py` reproduces
    that (unconditional reorder at both sites) and FAILS exactly this clause
    (G-DIFF). The F2P witnesses set `Meta.ordering` then read `get_choices()`
    (empty ordering) back and require the base Meta order — so the spec's whole
    job is: when no explicit ordering is supplied, do NOT reorder.

  * The REORDER pin is GROUNDED via the callee, not echoable. `reordered` is a
    `@Pure @ContractOnly` value with an EMPTY contract — it is UNINTERPRETED,
    asserting no property of the reorder operation's result whatsoever (in
    particular no length, set or multiset relation to `base`: an ordering path
    across a to-many association repeats base entries, and one across a
    mandatory single-valued association drops entries whose associate is
    absent, so the operation is not a rearrangement — see the axiom lane).
    Because it is uninterpreted, the ONLY way to obtain a value equal to
    `reordered(base, ordering)` is to CALL `apply_order_by` (whose Ensures pins
    `ToSeq(Result())==reordered(...)`). There is no executable materialization
    of the @Pure PSeq into a list_pred list, so there is no WRONG echo to
    construct on the non-empty branch — the cheapest impl that satisfies the
    reorder pin still has to call the real reorder callee (positive control
    `pos-control-explicit-else` is exactly that cheapest honest impl). The real
    "echo the oracle" temptation is to route the EMPTY case through the reorder
    callee too; that is precisely the pre-patch bug, caught by the EMPTY pin
    (rival `rival-prepatch-unconditional`).

  * BOTH `base` and `ordering` are held read-only (1/2). The MANDATORY attack is
    FRAME MUTATION: an impl that WRITES to a read-only input to satisfy a pin
    vacuously must fail for INSUFFICIENT PERMISSION, not for a wrong value
    (`frame-mutate-base`, `frame-mutate-ordering`).

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap_both`)
editing ONLY text strictly inside the two `# impl-start`/`# impl-end` regions, so
`markers.same_spec` is guaranteed and a rejection comes from the POSTCONDITION
catching wrong behaviour (or the permission system), never from a tampered spec.
Because the two functions are byte-identical in their impl, each impl substring
occurs EXACTLY twice; `_swap_both` rewrites both occurrences identically (a wrong
rival is wrong at both sites and the verifier rejects on the first; a correct
control is correct at both). Each `expect:"reject"` rival carries the refinement
argument that its faithful real patch would NOT resolve the F2P/P2P. Axiom cases
run the REAL `QuerySet.order_by` callee in Docker (this bundle has TWO
@ContractOnly A-consumed axioms: `reordered` / `apply_order_by`).
"""
from pathlib import Path

INSTANCE = "django__django-11400"
FLOAT_ENCODING = None

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap_both(src: str, old: str, new: str) -> str:
    """Replace BOTH occurrences of an impl-region substring (the two identical
    functions). Assert the substring appears exactly twice so silent drift
    (model.py edited) fails loudly at load."""
    n = src.count(old)
    if n == 0:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if n != 2:
        raise AssertionError(
            f"properties.py: expected 2 occurrences (both fns), found {n}: {old!r}")
    return src.replace(old, new, 2)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE the two impl regions of model.py).
# Each occurs exactly twice (the two identical functions).
# ---------------------------------------------------------------------------

# The whole impl body (between # impl-start and # impl-end) of one function.
_IMPL_BODY = """    if len(ordering) > 0:
        qs = apply_order_by(base, ordering)  # type: List[int]
        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
        return qs
    res = copy_rows(base)  # type: List[int]
    Assert(ToSeq(res) == ToSeq(base))
    return res"""

# The branch guard.
_GUARD = "    if len(ordering) > 0:"

# The empty-branch copy call.
_EMPTY_COPY = "    res = copy_rows(base)  # type: List[int]"

# The reorder call on the non-empty branch.
_REORDER_CALL = "        qs = apply_order_by(base, ordering)  # type: List[int]"


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Structurally-different but CORRECT: rewrite the two-branch fall-through
# (guard + fall-through to copy) as an EXPLICIT if/else, swapping which branch is
# written first (empty case stated first). Semantically identical; different
# control-flow source. The gold framing Asserts are KEPT verbatim inside each
# branch (so a failure could only be a spec defect, not a dropped obligation).
# If this fails to verify, the postcondition is over-fit to one branch order =>
# SPEC-TOO-STRONG.  This is also the cheapest HONEST impl: it still calls the
# real reorder callee on the non-empty branch (no oracle echo is possible).
_IMPL_EXPLICIT_ELSE = """    if len(ordering) == 0:
        res = copy_rows(base)  # type: List[int]
        Assert(ToSeq(res) == ToSeq(base))
        return res
    else:
        qs = apply_order_by(base, ordering)  # type: List[int]
        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
        return qs"""
_POS_EXPLICIT_ELSE = _swap_both(_BASE, _IMPL_BODY, _IMPL_EXPLICIT_ELSE)

# (5b) Structurally-different but CORRECT: a local-variable reshape. Compute the
# result into a single local `out` and return it once (single return point),
# keeping both gold framing Asserts. A different code shape over the same logic;
# if it fails to verify the spec is over-fit to the two-return code form =>
# SPEC-TOO-STRONG.
_IMPL_SINGLE_RETURN = """    out = []  # type: List[int]
    if len(ordering) > 0:
        out = apply_order_by(base, ordering)
        Assert(ToSeq(out) == reordered(ToSeq(base), ToSeq(ordering)))
    else:
        out = copy_rows(base)
        Assert(ToSeq(out) == ToSeq(base))
    return out"""
_POS_SINGLE_RETURN = _swap_both(_BASE, _IMPL_BODY, _IMPL_SINGLE_RETURN)

# (6) ADMISSIBILITY. A self-call on an F2P-shaped input under BOTH ordering
# regimes (empty and non-empty) must establish the precondition
# Acc(list_pred(.),1/2) for normal inputs. Freshly-built locals carry full
# permission, so passing 1/2 must succeed; if the self-call fails to verify the
# precondition => PRECOND-TOO-STRONG. The probe inputs are built and the calls
# placed at the very top of the impl, before the gold body runs unchanged.
_IMPL_ADMISS = """    pbase = [10, 20, 30]  # type: List[int]
    pempty = []  # type: List[int]
    pord = [1]  # type: List[int]
    if len(pbase) < len(base):   # keeps the callee's obligation level below ours
        _e = related_choice_rows(pbase, pempty)
        _r = related_choice_rows(pbase, pord)
    if len(ordering) > 0:
        qs = apply_order_by(base, ordering)  # type: List[int]
        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
        return qs
    res = copy_rows(base)  # type: List[int]
    Assert(ToSeq(res) == ToSeq(base))
    return res"""
_POS_ADMISS = _swap_both(_BASE, _IMPL_BODY, _IMPL_ADMISS)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION on `base` — MANDATORY, the #1 weakness class. `base` is
# read-only (1/2). This rival STORES base[0] = base[0] before the guard,
# attempting to touch the read-only input. Under Acc(list_pred(base),1/2) a store
# requires FULL permission, so it must fail for INSUFFICIENT PERMISSION (not a
# value mismatch). The gold body is kept verbatim after the write so the failure
# is attributable solely to the store. Rejection source: the PERMISSION SYSTEM.
_IMPL_FRAME_BASE = "    base[0] = base[0]\n" + _IMPL_BODY
_RIVAL_FRAME_BASE = _swap_both(_BASE, _IMPL_BODY, _IMPL_FRAME_BASE)

# (1b) FRAME MUTATION on `ordering` — the second read-only input. Same attack,
# stores ordering[0]. Must fail for insufficient permission. (Guarded by len so
# the index is in range when reached, but the permission check fires regardless.)
_IMPL_FRAME_ORD = (
    "    if len(ordering) > 0:\n"
    "        ordering[0] = ordering[0]\n"
    "        qs = apply_order_by(base, ordering)  # type: List[int]\n"
    "        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))\n"
    "        return qs\n"
    "    res = copy_rows(base)  # type: List[int]\n"
    "    Assert(ToSeq(res) == ToSeq(base))\n"
    "    return res"
)
_RIVAL_FRAME_ORD = _swap_both(_BASE, _IMPL_BODY, _IMPL_FRAME_ORD)

# (2) THE BUG ITSELF — unconditional reorder (pre-patch behaviour). Drop the
# guard entirely and ALWAYS route through the reorder callee, exactly mirroring
# the removed `...complex_filter(...).order_by(*ordering)` /
# `..._default_manager.order_by(*ordering)` (model_prepatch.py reverts to this at
# both sites). With an empty ordering the result is reordered(base, []), which
# the axiom does NOT tie to base. Its faithful real patch is the UNCHANGED
# pre-patch get_choices, which is precisely what FAILS the F2P
# test_get_choices_default_ordering (Meta.ordering=('d',), empty ordering, must
# return the Meta order but the empty order_by() clears it) — it would NOT
# resolve. Rejection source: the EMPTY pin
# Implies(len(ordering)==0, ToSeq(Result())==ToSeq(base)) — unprovable because
# reordered(base, []) is not tied to base.
_IMPL_UNCONDITIONAL = """    qs = apply_order_by(base, ordering)  # type: List[int]
    Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
    return qs"""
_RIVAL_PREPATCH = _swap_both(_BASE, _IMPL_BODY, _IMPL_UNCONDITIONAL)

# (3) GUARD-INVERSION (control-flow rival). Reorder when the ordering is EMPTY,
# copy (base order) when it is non-empty — the guard is inverted. On empty it
# routes through reordered(base, []) (FAILS the EMPTY pin), and on non-empty it
# returns base order (FAILS the REORDER pin). Its faithful real patch
# (`if not ordering: qs = qs.order_by(*ordering)`) would reorder with an empty
# spec (the exact bug) AND fail to honour an explicit ordering like ('a',) — so
# it FAILS both the empty-ordering F2P and the explicit-ordering P2P
# (test_get_choices, ordering=('a',)/('-a',)) — it would NOT resolve. Rejection
# source: BOTH pins, each violated on the wrong branch.
_IMPL_INVERT = """    if len(ordering) == 0:
        qs = apply_order_by(base, ordering)  # type: List[int]
        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
        return qs
    res = copy_rows(base)  # type: List[int]
    Assert(ToSeq(res) == ToSeq(base))
    return res"""
_RIVAL_INVERT = _swap_both(_BASE, _IMPL_BODY, _IMPL_INVERT)

# (4) PARTIAL-DOMAIN. Correct on empty and on MULTI-field orderings, but the
# guard is tightened to `len(ordering) > 1`, so a SINGLE-field ordering
# (len==1) is routed through copy_rows (base order) instead of the reorder.
# The REORDER pin requires reordered(base, ordering) for ALL len(ordering)>0,
# including len==1, but copy_rows gives base order. Its faithful real patch
# (`if len(ordering) > 1: qs = qs.order_by(*ordering)`) would skip the reorder
# for single-field orderings like ('a',)/('-a',) — exactly the explicit-ordering
# F2P/P2P inputs (test_get_choices, test_get_choices_reverse_related_field) — so
# it would NOT resolve. Rejection source: the REORDER pin
# Implies(len(ordering)>0, ToSeq(Result())==reordered(...)) on the len==1
# sub-domain, where copy_rows returns ToSeq(base) which is not provably equal to
# reordered(base, ordering).
_RIVAL_PARTIAL = _swap_both(_BASE, "    if len(ordering) > 0:",
                            "    if len(ordering) > 1:")

# (5, supporting) DROP-THE-REORDER. The non-empty branch returns copy_rows(base)
# (base order) instead of the reorder. A real patch that never reorders would
# leave the choices in base order even when an explicit ordering is supplied,
# failing every explicit-ordering F2P/P2P (test_get_choices with ('a',)/('-a',))
# — it would NOT resolve. Rejection source: the REORDER pin — the non-empty
# Assert ToSeq(qs)==reordered(...) is unprovable for a copy of base.
_IMPL_DROP_REORDER = (
    "    if len(ordering) > 0:\n"
    "        qs = copy_rows(base)  # type: List[int]\n"
    "        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))\n"
    "        return qs\n"
    "    res = copy_rows(base)  # type: List[int]\n"
    "    Assert(ToSeq(res) == ToSeq(base))\n"
    "    return res"
)
_RIVAL_DROP_REORDER = _swap_both(_BASE, _IMPL_BODY, _IMPL_DROP_REORDER)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-explicit-else", "kind": "soundness", "expect": "verify",
     "module": _POS_EXPLICIT_ELSE,
     "rationale": "structurally-different (explicit if/else with the empty branch stated first) "
                  "but semantically identical impl, gold framing Asserts kept verbatim, must "
                  "verify; if not, the postcondition is over-fit to one branch order => "
                  "SPEC-TOO-STRONG. Also the cheapest HONEST impl: the non-empty branch still "
                  "calls the real reorder callee (the reorder pin has no echoable oracle)."},
    {"id": "pos-control-single-return", "kind": "soundness", "expect": "verify",
     "module": _POS_SINGLE_RETURN,
     "rationale": "a correct impl with a DIFFERENT control shape (compute into one local `out`, "
                  "single return), both gold framing Asserts kept, must verify; if not, the spec "
                  "is over-fit to the two-return code form => SPEC-TOO-STRONG."},
    {"id": "admiss-self-call", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "self-calls on F2P-shaped inputs (base=[10,20,30] under empty AND non-empty "
                  "ordering) must establish the precondition Acc(list_pred(.),1/2) for normal "
                  "inputs (freshly-built locals carry full permission); if not, PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-base", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_BASE,
     "refinement": "no faithful real patch corresponds to this: get_choices never mutates its "
                   "base queryset rows; the fix only chooses whether to call .order_by(*ordering). "
                   "The rival exists solely to test whether the read-only (1/2) precondition on "
                   "`base` can be subverted by writing to it. There is no resolving patch that "
                   "overwrites its input, so a verifying rival here would be a pure "
                   "verify-not-resolve artifact (vacuous satisfaction via self-mutation).",
     "rationale": "MANDATORY frame-mutation probe. `base[0] = base[0]` stores through a 1/2 "
                  "(read-only) reference and MUST fail for insufficient permission. Rejection "
                  "source: the PERMISSION SYSTEM (a store needs full perm), not a value mismatch; "
                  "the gold body is kept verbatim. If it verified => SPEC-TOO-WEAK (frame "
                  "protection on `base` hollow)."},
    {"id": "frame-mutate-ordering", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_ORD,
     "refinement": "the ordering tuple is an immutable field-name tuple the patch only reads "
                   "(passes to .order_by); no resolving patch writes to it. A verifying rival here "
                   "would be a verify-not-resolve artifact.",
     "rationale": "MANDATORY frame-mutation probe on the second read-only input. `ordering[0] = "
                  "ordering[0]` stores through a 1/2 reference and MUST fail for insufficient "
                  "permission. Rejection source: the PERMISSION SYSTEM. If it verified => "
                  "SPEC-TOO-WEAK (frame protection on `ordering` hollow)."},
    {"id": "rival-prepatch-unconditional", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "drops the guard and ALWAYS applies the reorder callee — exactly the PRE-PATCH "
                   "unconditional `.order_by(*ordering)` (model_prepatch.py reverts to this at "
                   "both sites). Its faithful real patch is the unchanged pre-patch get_choices, "
                   "which is precisely what FAILS the F2P test_get_choices_default_ordering / "
                   "test_get_choices_reverse_related_field_default_ordering (Meta.ordering set, "
                   "empty ordering, must return the Meta order but an empty order_by() CLEARS it) "
                   "— it would NOT resolve.",
     "rationale": "the DISCRIMINATING bug this patch fixes (mirrors G-DIFF / model_prepatch.py). "
                  "Rejection source: the EMPTY pin Implies(len(ordering)==0, "
                  "ToSeq(Result())==ToSeq(base)) — unprovable because reordered(base, []) is "
                  "deliberately NOT tied to base by the axiom (empty order_by() clears the base "
                  "Meta.ordering, confirmed by G-AX). If it verified => SPEC-TOO-WEAK (admits the "
                  "very bug)."},
    {"id": "rival-invert-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INVERT,
     "refinement": "inverts the guard: reorder when the ordering is EMPTY, keep base order when "
                   "it is non-empty. Its faithful real patch (`if not ordering: qs = "
                   "qs.order_by(*ordering)`) reorders with an empty spec (the exact bug, clearing "
                   "Meta.ordering) AND fails to honour an explicit ordering like ('a',) — so it "
                   "FAILS both the empty-ordering F2P AND the explicit-ordering P2P "
                   "(test_get_choices ordering=('a',)/('-a',)). It would NOT resolve.",
     "rationale": "control-flow rival: the guard is inverted. Rejection source: BOTH pins — on "
                  "the empty branch reordered(base, []) violates the EMPTY pin, and on the "
                  "non-empty branch base order violates the REORDER pin. If it verified => "
                  "SPEC-TOO-WEAK (the guard direction is unconstrained)."},
    {"id": "rival-partial-domain-len1", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL,
     "refinement": "tightens the guard to `len(ordering) > 1`, so a SINGLE-field ordering is "
                   "routed through the base-order copy instead of the reorder. A faithful real "
                   "patch with `if len(ordering) > 1:` would skip the reorder for single-field "
                   "orderings like ('a',)/('-a',) — exactly the explicit-ordering F2P/P2P inputs "
                   "(test_get_choices, test_get_choices_reverse_related_field) — so it would NOT "
                   "resolve.",
     "rationale": "partial-domain: correct on empty and multi-field orderings, wrong on the "
                  "len==1 sub-domain. Rejection source: the REORDER pin Implies(len(ordering)>0, "
                  "ToSeq(Result())==reordered(...)) — for a length-1 ordering copy_rows returns "
                  "ToSeq(base), not provably equal to reordered(base, ordering). If it verified => "
                  "SPEC-TOO-WEAK (domain-incomplete on the reorder branch)."},
    {"id": "rival-drop-reorder", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_REORDER,
     "refinement": "the non-empty branch returns base order (copy_rows) instead of the reorder; a "
                   "real patch that never reorders would leave the choices in base order even when "
                   "an explicit ordering is supplied, failing every explicit-ordering F2P/P2P "
                   "(test_get_choices with ('a',)/('-a',)) — it would NOT resolve.",
     "rationale": "supporting near-miss with a real refinement. Rejection source: the REORDER "
                  "pin — the non-empty Assert ToSeq(qs)==reordered(...) is unprovable for a copy "
                  "of base."},
]

# ===========================================================================
# AXIOM LANE (Docker, real django.db.models.query.QuerySet.order_by callee)
# ===========================================================================
# Two @ContractOnly A-consumed axioms:
#   reordered(base, ordering)      — @Pure and UNINTERPRETED: its contract is
#                                    EMPTY. No length/set/multiset relation to
#                                    base, and silent on the empty case.
#   apply_order_by(base, ordering) — effecting form pinned to reordered(...).
# Both model `QuerySet.order_by(*ordering)` on the base manager queryset. The
# probes EXECUTE the real callee (mirroring axiom_check.py) over in-memory SQLite
# — never scrape source. Imports Django (its ORM IS the callee) + stdlib only.

# Shared bootstrap (configure Django, build a sortable model, return the helpers).
_BOOT = r'''
import sys
def _configure():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )
    django.setup()
_configure()
from django.db import models, connection

class Tag(models.Model):
    label = models.CharField(max_length=10)
    class Meta:
        app_label = "axcheck"
        ordering = ()

class Thing(models.Model):
    a = models.CharField(max_length=10)
    # a TO-MANY association, so an ordering PATH can repeat base entries.
    tags = models.ManyToManyField(Tag, related_name="things")
    class Meta:
        app_label = "axcheck"
        ordering = ()   # base order is insertion / pk order

class Room(models.Model):
    code = models.CharField(max_length=10)
    class Meta:
        app_label = "axcheck"
        ordering = ()

class Desk(models.Model):
    label = models.CharField(max_length=10)
    # MANDATORY single-valued association: ordering across it can DROP an entry
    # whose associate is absent.
    room = models.ForeignKey(Room, models.CASCADE, related_name="desks")
    class Meta:
        app_label = "axcheck"
        ordering = ()

with connection.schema_editor() as se:
    for _m in (Tag, Thing, Room, Desk):
        se.create_model(_m)

# rows whose alphabetical order on `a` is the REVERSE of pk order, so an applied
# ascending order visibly differs from the base order.
rows = [Thing.objects.create(a="d"), Thing.objects.create(a="c"),
        Thing.objects.create(a="b"), Thing.objects.create(a="a")]
base_pks = [t.pk for t in Thing.objects.all()]
assert base_pks == [r.pk for r in rows], base_pks

# one entry gains two associated elements, another gains one.
_t1, _t2 = Tag.objects.create(label="x"), Tag.objects.create(label="y")
rows[0].tags.add(_t1, _t2)
rows[1].tags.add(_t1)

def reordered(ordering):
    # the REAL callee: order_by(*ordering) on the base manager queryset.
    return [t.pk for t in Thing.objects.all().order_by(*ordering)]
'''

# (1) axiom-soundness — `reordered` IS UNINTERPRETED, AND MUST BE. The axiom
# states NO property of the reorder operation's value. This probe shows that is
# forced, not lazy: it exhibits the real callee BREAKING the tempting positive
# clauses, in BOTH directions. An ordering specification names traversal paths;
# a path across a to-many association REPEATS base entries (result LONGER), and
# one across a mandatory single-valued association DROPS an entry whose
# associate is absent (result SHORTER, row set changed). So an axiom asserting
# any length / set / multiset relation to `base` would be UNSOUND. If the callee
# turned out to preserve length on BOTH shapes, the axiom could soundly say so
# and this probe reports that instead.
_AX_UNINTERPRETED_SOUND = _BOOT + r'''
problems = []
# (a) GROWTH: a to-many ordering path repeats base entries.
fanned = reordered(("tags__label",))
if len(fanned) <= len(base_pks):
    problems.append("a to-many ordering path did NOT repeat base entries: "
                    "len %d vs base %d (%r)" % (len(fanned), len(base_pks), fanned))
# (b) SHRINK + membership change: a mandatory single-valued path drops an entry.
_room = Room.objects.create(code="r1")
_d1 = Desk.objects.create(label="d1", room=_room)
_d2 = Desk.objects.create(label="d2", room=_room)
desk_base = [d.pk for d in Desk.objects.all()]
with connection.cursor() as c:
    c.execute("PRAGMA foreign_keys=OFF")
    c.execute("UPDATE axcheck_desk SET room_id=%s WHERE id=%s",
              [max(desk_base) + 9999, _d2.pk])
dropped = [d.pk for d in Desk.objects.all().order_by("room__code")]
with connection.cursor() as c:   # restore: teardown runs an integrity check
    c.execute("UPDATE axcheck_desk SET room_id=%s WHERE id=%s", [_room.pk, _d2.pk])
    c.execute("PRAGMA foreign_keys=ON")
if len(dropped) >= len(desk_base):
    problems.append("a mandatory single-valued ordering path did NOT drop the "
                    "entry with a missing associate: len %d vs base %d (%r)"
                    % (len(dropped), len(desk_base), dropped))
if set(dropped) == set(desk_base):
    problems.append("the dropped entry did not leave the row set: %r vs %r"
                    % (dropped, desk_base))
if problems:
    print("AXIOM-MISMATCH (an uninterpreted axiom would be needlessly weak):",
          problems); sys.exit(1)
print("OK reordered must be uninterpreted: a to-many ordering path GROWS the "
      "collection (len %d > base %d) and a mandatory single-valued one SHRINKS "
      "it and changes its row set (len %d < base %d) — so no length, set or "
      "multiset clause tying reordered(b, o) to b would be sound"
      % (len(fanned), len(base_pks), len(dropped), len(desk_base))); sys.exit(0)
'''

# (2) axiom-soundness — NON-EMPTY ORDERING IS HONOURED (the REORDER pin ties
# Result() to reordered(base, ordering); confirm the real callee realises the
# requested arrangement, ascending and descending by `a`). If a non-empty
# order_by did NOT yield the requested order, the REORDER pin would be pinned to
# a wrong value => AXIOM-UNSOUND.
_AX_NONEMPTY_HONORED = _BOOT + r'''
asc = reordered(("a",))     # a ascending -> reverse of pk order
desc = reordered(("-a",))   # a descending -> pk order
ok = True
if asc != [rows[3].pk, rows[2].pk, rows[1].pk, rows[0].pk]:
    print("AXIOM-UNSOUND: ascending order_by('a') not honoured:", asc); ok = False
if desc != [rows[0].pk, rows[1].pk, rows[2].pk, rows[3].pk]:
    print("AXIOM-UNSOUND: descending order_by('-a') not honoured:", desc); ok = False
if not ok:
    sys.exit(1)
print("OK non-empty ordering honoured: asc('a')=%r desc('-a')=%r" % (asc, desc))
sys.exit(0)
'''

# (3) axiom-soundness — THE CRUX: the `reordered` axiom's SILENCE on the empty
# case is SOUND. The axiom deliberately does NOT promise reordered(base, [])==base
# because an empty order_by() CLEARS the base manager's Meta.ordering. This probe
# exhibits a base manager with a non-trivial Meta.ordering and shows that
# order_by() (empty) produces a DIFFERENT arrangement than the base order — so an
# axiom that DID promise reordered(b, [])==b would be UNSOUND, and the patched
# code's skip on the empty case is what makes the base order observable. If the
# empty order_by() unexpectedly reproduced the base Meta order, the axiom's
# silence would be needlessly weak AND the EMPTY pin in model.py could not be
# discriminating — we assert the divergence holds.
_AX_EMPTY_SILENCE_SOUND = _BOOT + r'''
Thing._meta.ordering = ("a",)
base_ordered_pks = [t.pk for t in Thing.objects.all()]   # now = ascending a
assert base_ordered_pks == [rows[3].pk, rows[2].pk, rows[1].pk, rows[0].pk], \
    base_ordered_pks
empty_applied = reordered(())                            # order_by() clears it
Thing._meta.ordering = ()
if empty_applied == base_ordered_pks:
    print("AXIOM-MISMATCH: order_by() reproduced the base Meta.ordering (%r); the "
          "axiom's silence on the empty case would be over-weak and the EMPTY pin "
          "non-discriminating" % (empty_applied,)); sys.exit(1)
# NOTE: on the EMPTY specification the operation names no traversal path, so it
# emits no join and the row SET happens to survive. That is an incidental
# observation, NOT something the axiom asserts -- the axiom is uninterpreted, and
# probe (1) shows why it must be. Recorded, not required.
set_incidentally_kept = sorted(empty_applied) == sorted(base_ordered_pks)
print("OK empty-case silence sound: order_by() = %r != base Meta order %r "
      "(row set incidentally kept: %s -- not an axiom claim), so reordered(b, []) "
      "must NOT be tied to b and the skip on the empty branch is required"
      % (empty_applied, base_ordered_pks, set_incidentally_kept)); sys.exit(0)
'''

# (4) axiom-containment — every callee-input the MODEL can reach lies in the
# axiom's Requires domain. The model passes `base` (any row list) and `ordering`
# (empty OR non-empty). `QuerySet.order_by(*ordering)` accepts ANY field-name
# tuple, including the empty tuple, and `reordered`/`apply_order_by` are typed
# over arbitrary PSeq[int]/List[int] with no value restriction. So every input
# the two contracted functions can produce is inside the axiom domain. We assert
# the real callee ACCEPTS both an empty and a non-empty ordering (the only two
# regimes the model's control flow distinguishes) without error; a regime the
# callee rejected would be AXIOM-TOO-WEAK-FOR-CALLER.
_AX_CONTAINMENT = _BOOT + r'''
# the two regimes the model's `if len(ordering) > 0` branch distinguishes.
try:
    empty_ok = reordered(())          # empty-ordering regime (copy_rows branch)
    nonempty_ok = reordered(("a",))   # non-empty regime (apply_order_by branch)
except Exception as e:
    print("AXIOM-TOO-WEAK-FOR-CALLER: order_by rejected a model-reachable ordering:",
          repr(e)); sys.exit(1)
# and on an EMPTY base (len 0) under both regimes -- the model admits any base.
class Empty(models.Model):
    a = models.CharField(max_length=10)
    class Meta:
        app_label = "axcheck"
        ordering = ()
with connection.schema_editor() as se:
    se.create_model(Empty)
try:
    eo = [t.pk for t in Empty.objects.all().order_by()]
    en = [t.pk for t in Empty.objects.all().order_by("a")]
except Exception as e:
    print("AXIOM-TOO-WEAK-FOR-CALLER: order_by rejected an empty-base reachable input:",
          repr(e)); sys.exit(1)
assert eo == [] and en == [], (eo, en)
print("containment OK: order_by accepts every model-reachable input -- empty AND "
      "non-empty ordering, on populated AND empty base; no caller-reachable input "
      "lies outside the axiom domain."); sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-reordered-uninterpreted-sound", "axiom": "reordered",
     "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_UNINTERPRETED_SOUND,
     "rationale": "the reordered axiom makes NO positive claim at all, and this probe shows that "
                  "is FORCED rather than lazy. An ordering specification names traversal paths: "
                  "the real QuerySet.order_by(*ordering) REPEATS base entries when a path crosses "
                  "a to-many association (result longer) and DROPS an entry whose associate is "
                  "absent when a path crosses a mandatory single-valued one (result shorter, row "
                  "set changed). So it is not a rearrangement, and any length/set/multiset clause "
                  "tying reordered(base, ordering) to base -- e.g. the tempting "
                  "len(reordered(base, ordering))==len(base) -- would be AXIOM-UNSOUND. If the "
                  "callee preserved length on both shapes the axiom could soundly say so, and "
                  "this probe reports that as an AXIOM-MISMATCH instead."},
    {"id": "ax-nonempty-honored", "axiom": "apply_order_by", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_NONEMPTY_HONORED,
     "rationale": "the REORDER pin ties Result() to reordered(base, ordering); confirm the real "
                  "callee realises the requested arrangement (ascending/descending by a field). "
                  "If a non-empty order_by did not honour the requested order, the pin would be "
                  "pinned to a wrong value => AXIOM-UNSOUND."},
    {"id": "ax-empty-silence-sound", "axiom": "reordered", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_EMPTY_SILENCE_SOUND,
     "rationale": "the crux of the fix: the axiom deliberately does NOT promise "
                  "reordered(base, [])==base because an empty order_by() CLEARS the base "
                  "Meta.ordering. The real callee must DIVERGE from the base Meta order on the "
                  "empty case (same row set), confirming the silence is sound and the EMPTY pin "
                  "is discriminating. If order_by() reproduced the base Meta order, the axiom "
                  "would be needlessly weak and the EMPTY pin non-discriminating."},
    {"id": "ax-containment", "axiom": "reordered", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_CONTAINMENT,
     "rationale": "every callee-input the model can reach (base = any row list; ordering = empty "
                  "OR non-empty) lies in the axiom domain: QuerySet.order_by accepts any "
                  "field-name tuple incl. the empty tuple, on any base incl. empty. A "
                  "model-reachable input the callee rejected would be AXIOM-TOO-WEAK-FOR-CALLER; "
                  "here the domain is total over the distinguished regimes."},
]
