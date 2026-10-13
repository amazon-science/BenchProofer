# properties.py — PBT manifest for django__django-15957. NOT a Nagini module; a
# record of adversarial falsification cases the runner (swebench_nagini.pbt)
# parses. Spec cases are full model.py variants that share the frozen spec and
# swap ONLY the impl region (between `# impl-start` / `# impl-end`); the runner
# checks each with Nagini verify + markers.same_spec. Axiom cases are real-callee
# probes run in the instance Docker image.
#
# Defended surface (django__django-15957 — Prefetch with sliced querysets):
#   bounded_prefetch(query, member_code, instance_count) -> PrefetchQuery models
#   the new helper _filter_prefetch_queryset. Its postcondition pins:
#     (1) membership_token(query) — the UNFORGEABLE capability granted ONLY by
#         apply_membership (which Requires not is_sliced). This is the load-bearing
#         clause: the membership step is a control-flow effect (filter ANDs the
#         predicate vs. raises TypeError on a sliced query) with NO value-level
#         discriminator, so the forgeable flag membership_applied does NOT pin it.
#     (2) membership_applied == True.
#     (3) Old(is_sliced(query)) == (lower_bound is not None); lower_bound ==
#         Old(offset_mark) when present  — lower restriction iff originally sliced.
#     (4) (Old(is_sliced) and Old(limit_mark) is not None) == (upper_bound is not
#         None); upper_bound == Old(limit_mark) when present.
#     (5) not is_sliced(query) and offset_mark == 0 and limit_mark is None.
#   query is a FULL-permission carrier meant to be mutated (Result() is query); it
#   is NOT a read-only Acc(...,1/2) input, so the classic frame-mutation-on-a-
#   read-only-input probe is N/A here (see 'assessment' in the returned verdict).
#   The analogous permission defense is the capability token: apply_membership
#   holds only 1/4 of the slice marks and is the UNIQUE token producer, so an impl
#   cannot forge membership without routing through a successful unsliced apply.
from pathlib import Path

INSTANCE = "django__django-15957"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The full impl region of the frozen model.py (between # impl-start / # impl-end,
# markers excluded). Every variant is produced by _swap on THIS exact text, so
# the edit is confined to the impl region and same_spec is guaranteed.
_GOLD_IMPL = """    if is_sliced(query):
        low = query.offset_mark
        high = query.limit_mark      # type: Optional[int]
        # record the start offset as the lower position restriction
        query.lower_bound = low
        # record a finite stop limit as the upper position restriction
        if high is not None:
            query.upper_bound = high
        # remove the slice so the membership predicate can be applied
        query.offset_mark = 0
        query.limit_mark = None
    # at this point the query is no longer sliced; the membership predicate is
    # applicable and is ANDed on (apply_membership requires not is_sliced).
    apply_membership(query)
    return query"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in base")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _variant(new_impl):
    """Build a full model.py source whose impl region is `new_impl` (the rest of
    the file — spec/axioms/pure/pre/post — is the frozen model verbatim)."""
    assert _GOLD_IMPL in _BASE, "gold impl region drifted from model.py"
    return _swap(_BASE, _GOLD_IMPL, new_impl)


# --------------------------------------------------------------------------- #
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.                 #
# --------------------------------------------------------------------------- #

# A structurally-DIFFERENT but CORRECT impl: save the marks into locals FIRST,
# clear the slice unconditionally, then record the bounds from the saved locals
# guarded by the *saved* was_sliced flag. This reorders the operations (clear
# before record; one compute of was_sliced reused) yet preserves every gold
# obligation — it must verify, else SPEC-TOO-STRONG. No framing lemma is needed
# (no loops / no @Pure fold), so this avoids the proof-gap pitfalls.
_POS_REORDER = """    was_sliced = is_sliced(query)
    saved_offset = query.offset_mark
    saved_limit = query.limit_mark       # type: Optional[int]
    # clear the slice first (unconditionally; if it was never sliced the marks
    # are already 0/None so this is a no-op on the observable state)
    query.offset_mark = 0
    query.limit_mark = None
    if was_sliced:
        # now record the position restriction from the saved marks
        query.lower_bound = saved_offset
        if saved_limit is not None:
            query.upper_bound = saved_limit
    apply_membership(query)
    return query"""

# A second correct shape: keep the gold branch but compute the upper-bound guard
# with an explicit local and assign lower_bound from a temporary. Reorders the two
# bound writes (upper before lower) — order is irrelevant to the value spec.
_POS_REORDER_WRITES = """    if is_sliced(query):
        low = query.offset_mark
        high = query.limit_mark      # type: Optional[int]
        if high is not None:
            query.upper_bound = high
        query.lower_bound = low
        query.limit_mark = None
        query.offset_mark = 0
    apply_membership(query)
    return query"""

# ADMISSIBILITY: the gold impl itself plus an explicit in-region assertion that an
# F2P-shaped sliced input ([1:] => offset_mark==1, limit_mark==None) drives the
# branch the way the postcondition expects. If the Requires were too strong this
# would fail to establish; it must verify.
_ADMISS = """    # admissibility witness: an F2P-shaped [1:] slice is in-domain — the
    # precondition admits a freshly-assembled sliced query (offset>=0, limit
    # None-or->=0, no predicate yet, no bounds yet).
    Assert(query.offset_mark >= 0)
    Assert(query.limit_mark is None or query.limit_mark >= 0)
    Assert(query.membership_applied == False)
    Assert(query.lower_bound is None and query.upper_bound is None)
    if is_sliced(query):
        low = query.offset_mark
        high = query.limit_mark      # type: Optional[int]
        query.lower_bound = low
        if high is not None:
            query.upper_bound = high
        query.offset_mark = 0
        query.limit_mark = None
    apply_membership(query)
    return query"""


# --------------------------------------------------------------------------- #
# UNIQUENESS / REJECT rivals — must NOT verify (else SPEC-TOO-WEAK).           #
# --------------------------------------------------------------------------- #

# (A) Control-flow-effect / ungrounded echo, STILL SLICED: discharge the
# membership obligation by writing the forgeable flag directly while the query is
# still sliced, never calling apply_membership. The token cannot be obtained
# (only apply_membership grants it, and only under not is_sliced), so the
# Ensures(membership_token(query)) cannot be established. MUST reject.
_ATK_ECHO_SLICED = """    # cheat: claim the membership predicate is applied without doing the work,
    # and without un-slicing — exactly the directive-8 echo cheat.
    query.membership_applied = True
    return query"""

# (B) Echo AFTER a correct un-slice + bound recording, but NEVER routing through
# apply_membership (set the flag by hand). The bounds + marks are all correct, so
# every value clause holds — only the unforgeable token is missing. MUST reject:
# this is the precise reason the token (not the flag) is the postcondition.
_ATK_ECHO_AFTER_CLEAR = """    if is_sliced(query):
        low = query.offset_mark
        high = query.limit_mark      # type: Optional[int]
        query.lower_bound = low
        if high is not None:
            query.upper_bound = high
        query.offset_mark = 0
        query.limit_mark = None
    # cheat: forge the flag instead of applying the predicate. Every value clause
    # is satisfied, but membership_token(query) was never granted.
    query.membership_applied = True
    return query"""

# (C) Partial-domain: only record the lower bound when a finite limit is present
# (i.e. drop the lower restriction on an OFFSET-ONLY slice like [1:]). On [1:]
# (offset_mark==1, limit_mark==None) was_sliced is True but lower_bound stays
# None, violating Old(is_sliced) == (lower_bound is not None). MUST reject.
_ATK_DROP_LOWER_OFFSET_ONLY = """    if is_sliced(query):
        low = query.offset_mark
        high = query.limit_mark      # type: Optional[int]
        if high is not None:
            query.lower_bound = low
            query.upper_bound = high
        query.offset_mark = 0
        query.limit_mark = None
    apply_membership(query)
    return query"""

# (D) No-clear: record both bounds correctly but never reset the marks, so the
# query is still sliced when apply_membership is called. apply_membership's
# Requires(not is_sliced) fails AND the postcondition not is_sliced(query) /
# offset_mark==0 fails. MUST reject.
_ATK_NO_CLEAR = """    if is_sliced(query):
        low = query.offset_mark
        high = query.limit_mark      # type: Optional[int]
        query.lower_bound = low
        if high is not None:
            query.upper_bound = high
    apply_membership(query)
    return query"""

# (E) Swapped bound values: record the offset into upper and the limit into lower
# (value-level corruption of the position restriction). On a sliced query with a
# finite limit, lower_bound == Old(limit_mark) != Old(offset_mark) (when they
# differ), violating lower_bound == Old(offset_mark). MUST reject.
_ATK_SWAP_BOUNDS = """    if is_sliced(query):
        low = query.offset_mark
        high = query.limit_mark      # type: Optional[int]
        if high is not None:
            query.lower_bound = high
            query.upper_bound = low
        else:
            query.lower_bound = low
        query.offset_mark = 0
        query.limit_mark = None
    apply_membership(query)
    return query"""

# (F) Upper-bound recorded unconditionally (even when no finite limit): on [1:]
# (limit_mark==None) upper_bound would be set to None... but the cheat sets it to
# the offset, making upper_bound non-None when it must be None. Violates
# (Old(is_sliced) and Old(limit_mark) is not None) == (upper_bound is not None).
# MUST reject.
_ATK_UPPER_ALWAYS = """    if is_sliced(query):
        low = query.offset_mark
        high = query.limit_mark      # type: Optional[int]
        query.lower_bound = low
        # cheat: always record an upper restriction, even for an unbounded [1:]
        # slice (high is None) — record the offset as a stand-in.
        query.upper_bound = low
        query.offset_mark = 0
        query.limit_mark = None
    apply_membership(query)
    return query"""

# (G) Vacuous: do nothing at all (no un-slice, no bounds, no apply). A pure
# near-miss supporting case — fails the token obligation, the lower-bound
# presence clause, and not is_sliced on any sliced input. MUST reject.
_ATK_VACUOUS = """    return query"""


SPEC_TESTS = [
    {
        "id": "pos-reorder-clear-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_REORDER),
        "rationale": "structurally-different correct impl (save marks -> clear "
                     "unconditionally -> record bounds from saved locals under a "
                     "single was_sliced flag). No loop / no @Pure fold, so no "
                     "framing lemma is needed; every postcondition clause + the "
                     "apply_membership precondition still hold. Must verify, else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-reorder-writes",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_REORDER_WRITES),
        "rationale": "correct impl with the two bound writes reordered (upper "
                     "before lower) and the two mark clears reordered — the value "
                     "spec is order-independent, so this must verify.",
    },
    {
        "id": "admiss-sliced-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_ADMISS),
        "rationale": "the precondition must admit an F2P-shaped freshly-assembled "
                     "sliced query (offset>=0, limit None-or->=0, no predicate, no "
                     "bounds). In-region Asserts confirm the Requires holds; the "
                     "gold body then verifies. If it cannot, PRECOND-TOO-STRONG.",
    },
    {
        "id": "atk-echo-sliced",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_ATK_ECHO_SLICED),
        "refinement": "faithful real patch = drop the slice->bound translation and "
                      "clear_limits, then `queryset.filter(predicate)` on a STILL "
                      "sliced query. Django's filter raises TypeError 'Cannot "
                      "filter a query once a slice has been taken.' (query.py:1440-"
                      "1442, can_filter == not is_sliced), so every F2P "
                      "(test_m2m_forward/reverse, test_foreignkey_reverse, "
                      "test_reverse_ordering) errors out — does NOT resolve.",
        "rationale": "rejection from Ensures(membership_token(query)): the token is "
                     "abstract @ContractOnly, granted ONLY by apply_membership "
                     "under not is_sliced; a forged membership_applied flag cannot "
                     "establish it. (Also fails lower_bound-presence + not "
                     "is_sliced.) If it verified => SPEC-TOO-WEAK (the directive-8 "
                     "echo cheat).",
    },
    {
        "id": "atk-echo-after-clear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_ATK_ECHO_AFTER_CLEAR),
        "refinement": "faithful real patch = correctly translate the slice to "
                      "bounds and clear_limits, but then set a 'filtered' flag "
                      "WITHOUT calling queryset.filter(predicate). The membership "
                      "predicate ({field}__in=instances) is never ANDed, so the "
                      "prefetch returns ALL related objects, not the sliced subset "
                      "— assertEqual(book.authors_sliced, list(...)[1:]) fails on "
                      "every F2P. Does NOT resolve.",
        "rationale": "all VALUE clauses hold (bounds + marks correct), so this is "
                     "pinned ONLY by Ensures(membership_token(query)): the token "
                     "cannot be obtained without routing through apply_membership. "
                     "This is exactly why the postcondition uses the unforgeable "
                     "token, not the forgeable flag. If it verified => SPEC-TOO-WEAK.",
    },
    {
        "id": "atk-drop-lower-offset-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_ATK_DROP_LOWER_OFFSET_ONLY),
        "refinement": "faithful real patch = only AND the GreaterThan(window, "
                      "low_mark) lower bound when high_mark is not None. The F2P "
                      "tests slice with [1:] (offset 1, no stop): "
                      "test_m2m_forward/test_foreignkey_reverse/test_reverse_"
                      "ordering all use authors[1:]. Omitting the lower bound on "
                      "an offset-only slice returns rows from position 0, so "
                      "book.authors_sliced != list(...)[1:] — does NOT resolve.",
        "rationale": "rejection from Ensures(Old(is_sliced(query)) == (lower_bound "
                     "is not None)): on [1:] (offset 1, limit None) Old(is_sliced) "
                     "is True but lower_bound stays None. If it verified => "
                     "SPEC-TOO-WEAK on the offset-only sub-domain (the exact F2P "
                     "slice shape).",
    },
    {
        "id": "atk-no-clear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_ATK_NO_CLEAR),
        "refinement": "faithful real patch = record the window bounds but OMIT "
                      "queryset.query.clear_limits(), then queryset.filter(...) on "
                      "the still-sliced query -> TypeError (the original bug). "
                      "Every F2P errors. Does NOT resolve.",
        "rationale": "rejection from apply_membership's Requires(not is_sliced) "
                     "(the membership precondition might not hold) AND from "
                     "Ensures(not is_sliced(query)) / offset_mark==0. This is the "
                     "literal prepatch failure (G-DIFF, model_prepatch.py:157). "
                     "If it verified => SPEC-TOO-WEAK.",
    },
    {
        "id": "atk-swap-bounds",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_ATK_SWAP_BOUNDS),
        "refinement": "faithful real patch = AND GreaterThan(window, high_mark) "
                      "and LessThanOrEqual(window, low_mark) — i.e. the strict "
                      "lower bound carries the STOP limit and the inclusive upper "
                      "carries the START offset. On [1:2] (test_m2m_reverse: "
                      "books[1:2]) this selects rows with position > 2 and <= 1 "
                      "(empty / wrong), so author.books_sliced != list(...)[1:2] — "
                      "does NOT resolve.",
        "rationale": "rejection from Ensures(Implies(lower_bound is not None, "
                     "lower_bound == Old(offset_mark))): on a finite-limit slice "
                     "lower_bound == Old(limit_mark) != Old(offset_mark). If it "
                     "verified => SPEC-TOO-WEAK on the bound-value clause.",
    },
    {
        "id": "atk-upper-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_ATK_UPPER_ALWAYS),
        "refinement": "faithful real patch = always AND LessThanOrEqual(window, "
                      "<something>) even when high_mark is None (an unbounded "
                      "[1:] slice). That imposes a spurious finite upper bound on "
                      "an open-ended slice, so the prefetch drops rows that [1:] "
                      "would keep — book.authors_sliced != list(...)[1:] (the F2P "
                      "[1:] tests). Does NOT resolve.",
        "rationale": "rejection from Ensures((Old(is_sliced) and Old(limit_mark) "
                     "is not None) == (upper_bound is not None)): on [1:] "
                     "(limit_mark None) the LHS is False but upper_bound becomes "
                     "non-None. If it verified => SPEC-TOO-WEAK on the upper-bound "
                     "presence clause.",
    },
    {
        "id": "atk-vacuous",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_ATK_VACUOUS),
        "refinement": "faithful real patch = return the queryset untouched (no "
                      "translation, no clear, no filter). The membership predicate "
                      "is never applied and any slice survives -> filter would "
                      "later error / the prefetch is unfiltered. Does NOT resolve. "
                      "(Cheap supporting near-miss.)",
        "rationale": "rejection from multiple clauses: Ensures(membership_token), "
                     "Ensures(membership_applied == True), the lower-bound presence "
                     "clause, and not is_sliced(query) on any sliced input. "
                     "Supporting case; the reasoned attacks above carry the lane.",
    },
]


# --------------------------------------------------------------------------- #
# AXIOM lane — two consumed @ContractOnly axioms (apply_membership +           #
# membership_token), both modeling the UNCHANGED QuerySet.filter slice guard.  #
# Soundness: the real callee must match the axiom Ensures on its Requires       #
# domain. Containment: every callee-input the model can reach lies inside the   #
# axiom's Requires domain (not is_sliced).                                      #
# --------------------------------------------------------------------------- #

# Probe S3-soundness: under the caller's real runtime config, QuerySet.filter on
# an UNSLICED query SUCCEEDS and ANDs the membership predicate (the token-grant /
# membership_applied==True path), and on a SLICED query RAISES TypeError (so the
# token is NOT grantable while sliced — exactly Requires(not is_sliced)). Fuzz a
# spread of slice shapes incl. boundary [0:0], [0:N], [k:], [k:k]. This validates
# both apply_membership.Ensures (predicate applied on the unsliced path) and the
# raise guard that makes the token obtainable only under not is_sliced.
_PROBE_AX_SOUND = r'''
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()
except Exception as exc:
    print("AX-SOUND SKIP: Django not configurable: %r" % (exc,))
    sys.exit(0)

from django.db import connection, models
from django.db.models import Q, Window
from django.db.models.functions import RowNumber


class Parent(models.Model):
    class Meta:
        app_label = "axsound"


class Child(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE,
                               related_name="children")
    rank = models.IntegerField(default=0)

    class Meta:
        app_label = "axsound"
        ordering = ["rank"]


with connection.schema_editor() as editor:
    editor.create_model(Parent)
    editor.create_model(Child)

p = Parent.objects.create()
for r in range(5):
    Child.objects.create(parent=p, rank=r)
instances = list(Parent.objects.all())
field_name = "parent"
predicate = Q(**{"%s__in" % field_name: instances})


def _collect(node, acc):
    children = getattr(node, "children", None)
    if children is None:
        acc.append(node)
        return
    for c in children:
        _collect(c, acc)


def membership_present(qs):
    acc = []
    _collect(qs.query.where, acc)
    for lk in acc:
        if not isinstance(getattr(lk, "lhs", None), Window):
            return True
    return False


# UNSLICED -> filter SUCCEEDS (apply_membership.Ensures path: predicate ANDed,
# the membership_token-grant / membership_applied==True step).
unsliced = Child.objects.all()
assert not unsliced.query.is_sliced, "unsliced setup failed"
out = unsliced.filter(predicate)
assert membership_present(out), (
    "AX-SOUND VIOLATION: filter on an unsliced query did NOT AND the membership "
    "predicate — apply_membership.Ensures(membership_applied) would be unsound")
print("AX-SOUND ok: unsliced filter applies the membership predicate")

# SLICED -> filter RAISES TypeError, so the token is NOT grantable while sliced.
# This is the Requires(not is_sliced) guard. Fuzz boundary + sentinel slices.
slice_shapes = [(1, 3), (1, None), (0, 3), (2, 5), (1, 2), (0, 1)]
for low, high in slice_shapes:
    sq = Child.objects.all()
    sq.query.set_limits(low=low if low else None, high=high)
    assert sq.query.is_sliced, "sliced setup failed for (%r,%r)" % (low, high)
    raised = False
    try:
        sq.filter(predicate)
    except TypeError:
        raised = True
    assert raised, (
        "AX-SOUND VIOLATION: filter did NOT raise TypeError on a sliced query "
        "(low=%r high=%r) — the apply_membership precondition not is_sliced "
        "(and the token-only-on-unsliced grant) would be UNSOUND" % (low, high))
print("AX-SOUND ok: filter raises TypeError on every sliced shape %r"
      % (slice_shapes,))
print("AX-SOUND PASS")
sys.exit(0)
'''

# Probe containment: enumerate EXACTLY the queries the MODEL can hand to
# apply_membership and assert each is not is_sliced (the axiom's Requires domain).
# By the model's control flow, apply_membership is reached only AFTER the sliced
# branch has set offset_mark=0/limit_mark=None (or the query was never sliced), so
# is_sliced is False at the call site for every reachable model state. We mirror
# the model's slice->clear transition on the real Query and assert the cleared
# state is not is_sliced for the full F2P/P2P spread of inbound slice shapes (incl.
# the never-sliced case). A reachable sliced input would be AXIOM-TOO-WEAK-FOR-
# CALLER; we show there is none.
_PROBE_AX_CONTAIN = r'''
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()
except Exception as exc:
    print("AX-CONTAIN SKIP: Django not configurable: %r" % (exc,))
    sys.exit(0)

from django.db.models.sql.query import Query as RawQuery

# inbound slice shapes the caller (bounded_prefetch) can be invoked with: the
# never-sliced query plus every F2P/P2P slice shape ([:N], [k:], [k:k], etc.).
inbound = [None, (0, 3), (1, None), (1, 2), (2, 5), (0, 1), (3, 7)]

for shape in inbound:
    q = RawQuery(None)
    if shape is not None:
        low, high = shape
        q.set_limits(low=low if low else None, high=high)
    was_sliced = q.is_sliced
    # The model reaches apply_membership only after un-slicing when it was sliced;
    # if it was never sliced, no clear happens. Mirror that transition:
    if was_sliced:
        q.clear_limits()  # model: offset_mark=0; limit_mark=None
    # CONTAINMENT: the state actually passed to apply_membership must be NOT
    # sliced (the axiom's Requires domain).
    assert not q.is_sliced, (
        "AX-CONTAIN VIOLATION: a caller-reachable apply_membership input is still "
        "sliced for inbound shape=%r (marks=(%r,%r)) — AXIOM-TOO-WEAK-FOR-CALLER"
        % (shape, q.low_mark, q.high_mark))
    assert q.low_mark == 0 and q.high_mark is None, (
        "AX-CONTAIN VIOLATION: cleared marks not (0,None) for shape=%r: (%r,%r)"
        % (shape, q.low_mark, q.high_mark))
print("AX-CONTAIN PASS: every caller-reachable apply_membership input is "
      "not-sliced over inbound shapes %r" % (inbound,))
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-apply-membership",
        "axiom": "apply_membership",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_AX_SOUND,
        "rationale": "the real QuerySet.filter (the callee apply_membership + "
                     "membership_token axiomatize) must, under the caller's config, "
                     "AND the membership predicate on an UNSLICED query (Ensures "
                     "membership_applied / token-grant path) and RAISE TypeError on "
                     "a SLICED query (so the token is grantable only under not "
                     "is_sliced — the Requires guard). A violation in either "
                     "direction is AXIOM-UNSOUND. Validated against real Django 4.2 "
                     "over a spread of slice shapes incl. boundaries.",
    },
    {
        "id": "ax-contain-apply-membership",
        "axiom": "apply_membership",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_AX_CONTAIN,
        "rationale": "every query the MODEL can hand to apply_membership lies in "
                     "the axiom's Requires domain (not is_sliced): the call is "
                     "reached only after the sliced branch clears the marks (or the "
                     "query was never sliced). Mirroring the model's clear_limits "
                     "transition on the real Query for the full F2P/P2P inbound "
                     "slice spread shows the call-site state is always not-sliced — "
                     "no reachable input falls outside the axiom domain, so it is "
                     "not AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
