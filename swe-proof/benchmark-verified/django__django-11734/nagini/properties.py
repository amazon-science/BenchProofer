"""properties.py — PBT falsification battery for django__django-11734.

NOT a Nagini module; a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (only the two impl
regions differ — enforced by region-surgery via `_swap`, checked by
markers.same_spec); they are decided by re-running the Nagini verifier on the
host. Axiom cases are real-Django-callee probes run in the instance Docker image.

Defended surface (read model.py + refinement.md + mapping.md):

  Two pure integer/boolean decisions over a tagged domain rhs_kind in {0,1,2}
  = {value, local, outer}; NO library callee consumed, NO @ContractOnly axiom.

  rebind_into_inner_subquery(rhs_kind: int) -> int   [Query.split_exclude hop count]
    Requires: rhs_kind in {value, local, outer}
    Ensures:  Result >= 0
              value  -> Result == 0
              query-expression (local|outer):
                  resolved_level_in_inner(kind) - Result == target_level(kind)
                  => local: 1 - Result == 0  -> Result == 1
                  => outer: 0 - Result == -1 -> Result == 1
    So the postcondition FULLY PINS all three: value->0, local->1, outer->1.
    Load-bearing clause = the level-arithmetic Ensures for kind_outer (the gold
    fix: an OuterRef rhs gets one EXTRA outward hop, not zero). model_prepatch.py
    reverts outer->0 and fails exactly this clause.

  normalize_only_concrete_value(rhs_kind: int) -> bool   [get_prep_lookup guard]
    Requires: rhs_kind in {value, local, outer}
    Ensures:  Result == (not is_query_expression(rhs_kind))   AND
              Result == (rhs_kind == kind_value())
    So the postcondition FULLY PINS all three: value->True, local->False,
    outer->False. model_prepatch_2.py reverts to "normalise everything" and
    fails exactly this clause.

Why the standard weakness classes apply / do not apply here:

  * FRAME-MUTATION: N/A. Both modeled functions take a single `int` BY VALUE.
    There is no pointer / reference / Acc(x, 1/2) read-only input to overwrite,
    so the frame-mutation attack (the project's #1 class) has no surface here.
    Documented in StructuredOutput.assessment; has_readonly_input=False.

  * UNGROUNDED-ORACLE ECHO: N/A as a *defect* vector. The @Pure helpers
    (is_query_expression / target_level / resolved_level_in_inner) are GROUNDED
    functions of the input rhs_kind (each fully unfolds to a conditional on the
    int tag), not an opaque answer-key. Echoing them (`return not
    is_query_expression(rhs_kind)`) IS the correct answer — there is no WRONG
    echo to build. Instead we ship the honest cheapest-impl positive controls
    (pos-*) and attack the genuine load-bearing clauses with partial-domain
    rivals below.

  * PARTIAL-DOMAIN: the principal attack here. Each rival is correct on most of
    the {value,local,outer} domain but diverges on one tag, and carries the
    refinement argument that its faithful real patch would NOT resolve the F2P
    (test_subquery_exclude_outerref) / would regress P2P.

  * CONTROL-FLOW-EFFECT: N/A. The functions are total, side-effect-free, raise
    nothing; the value abstraction (the returned int / bool) captures the entire
    observable behaviour. No raise/return/effect difference is invisible.

The axiom lane re-validates the two A-reference deep models against the REAL
Django objects in Docker (gold applied): the query-expression classification ==
hasattr(rhs,'resolve_expression'), and the OuterRef resolution-level arithmetic
(bare collapses one outward level; OuterRef(OuterRef(.)) preserves it) that
underwrites the one-extra-hop re-anchor. This is the axiom_check.py logic,
self-contained and embedded.
"""
from pathlib import Path

INSTANCE = "django__django-11734"
FLOAT_ENCODING = None  # meta.json float_encoding is null; behaviour is integer/boolean only

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (text strictly INSIDE the two impl regions) --------------
# rebind_into_inner_subquery impl body (lines 136-142 of model.py):
_REBIND_IMPL = """    if rhs_kind == kind_value():
        return 0
    if rhs_kind == kind_local():
        # level +1 in inner must become level 0 -> one outward hop.
        return 1
    # OuterRef: level 0 in inner must become level -1 -> one outward hop.
    return 1"""

# normalize_only_concrete_value impl body (line 163 of model.py):
_NORM_IMPL = "    return not is_query_expression(rhs_kind)"


# =============================================================================
# SPEC LANE
# =============================================================================
SPEC_TESTS = [

    # ---- POSITIVE CONTROLS (soundness; must verify) -------------------------
    # A structurally-DIFFERENT but CORRECT rebind: branch order flipped (handle
    # the two query-expression kinds first, plain value via the final return),
    # and the hop count is written as the level-arithmetic difference
    # (resolved_level_in_inner - target_level) instead of literal `1`, computed
    # in a local. Same results (value->0, local->1, outer->1); a faithful
    # correct impl MUST verify, else SPEC-TOO-STRONG. No framing lemma is needed
    # (the function is a finite case split over an int), so this is not a proof
    # gap (avoids pilot bug #2/#3).
    {
        "id": "pos-rebind-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _REBIND_IMPL,
            """    if rhs_kind == kind_local() or rhs_kind == kind_outer():
        # one outward hop = the gap between where it resolves in the inner
        # subquery and the level it must still denote.
        hops = resolved_level_in_inner(rhs_kind) - target_level(rhs_kind)  # type: int
        return hops
    # plain value: no reference to re-anchor.
    return 0""",
        ),
        "rationale": "structurally-different CORRECT impl (branch reorder + "
                     "hop computed from the level arithmetic) must verify; the "
                     "postcondition is satisfiable by a faithful impl (else "
                     "SPEC-TOO-STRONG).",
    },
    # A structurally-different but CORRECT normalize: explicit case split over
    # the three tags instead of `not is_query_expression(rhs_kind)`. Same truth
    # table (value->True, local->False, outer->False).
    {
        "id": "pos-normalize-explicit",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _NORM_IMPL,
            """    if rhs_kind == kind_local() or rhs_kind == kind_outer():
        return False
    # plain concrete value: normalise through the relation's value coercion.
    return True""",
        ),
        "rationale": "explicit-case-split CORRECT impl must verify (cheapest "
                     "honest impl positive control; the @Pure oracle is grounded "
                     "in the input so there is no wrong echo).",
    },

    # ---- ADMISSIBILITY (precondition not too strong / not vacuous) ----------
    # The keep-correct impl with a leading Assert that the tagged domain is the
    # expected concrete set {0,1,2} and the F2P-shaped outer kind is in-domain.
    # Verifies iff the precondition admits a normal (F2P-shaped) input and the
    # @Pure helpers are consistent on it; if it could not, PRECOND-TOO-STRONG.
    {
        "id": "admiss-rebind-outer",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _REBIND_IMPL,
            """    # admissibility: the precondition admits the F2P-shaped OuterRef
    # input, and the tagged domain is the expected concrete set.
    Assert(kind_value() == 0 and kind_local() == 1 and kind_outer() == 2)
    Assert(Implies(rhs_kind == kind_outer(), is_query_expression(rhs_kind)))
    if rhs_kind == kind_value():
        return 0
    if rhs_kind == kind_local():
        return 1
    return 1""",
        ),
        "rationale": "the precondition admits a representative F2P input "
                     "(an OuterRef rhs, exercised by test_subquery_exclude_outerref) "
                     "and is internally consistent; verifies => not PRECOND-TOO-STRONG.",
    },

    # ---- UNIQUENESS / PARTIAL-DOMAIN rivals (must be REJECTED) --------------
    # (1) THE GOLD-FIX DISCRIMINATOR: an OuterRef rhs gets ZERO extra hops
    # (== model_prepatch.py == the pre-patch code that handled only F).
    {
        "id": "weak-outer-zero-hops",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _REBIND_IMPL,
            """    if rhs_kind == kind_value():
        return 0
    if rhs_kind == kind_local():
        return 1
    # OuterRef carried into the inner subquery UNCHANGED: zero extra hops.
    return 0""",
        ),
        "refinement": "Faithful real patch: drop the new `if isinstance(filter_rhs, "
                      "OuterRef): filter_expr = (filter_lhs, OuterRef(filter_rhs))` "
                      "branch in Query.split_exclude — i.e. an OuterRef rhs is carried "
                      "into the freshly generated inner subquery unchanged (zero extra "
                      "OuterRef wraps). Then `bare OuterRef.resolve_expression()` "
                      "collapses one outward level (-> ResolvedOuterRef) so the outer "
                      "reference resolves onto the inner subquery instead of the outer "
                      "query: the F2P test_subquery_exclude_outerref returns the wrong "
                      "rows and FAILS. This is exactly the pre-patch behaviour.",
        "rationale": "rejected by the kind_outer level-arithmetic Ensures: "
                     "resolved_level_in_inner(outer)=0, target_level(outer)=-1, "
                     "so 0 - Result == -1 forces Result==1; returning 0 violates it.",
    },
    # (2) PARTIAL-DOMAIN: a LOCAL (F) rhs gets zero hops (value/outer correct).
    {
        "id": "weak-local-zero-hops",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _REBIND_IMPL,
            """    if rhs_kind == kind_value():
        return 0
    if rhs_kind == kind_local():
        # F carried into the inner subquery UNCHANGED: zero extra hops.
        return 0
    return 1""",
        ),
        "refinement": "Faithful real patch: drop the `elif isinstance(filter_rhs, F): "
                      "filter_expr = (filter_lhs, OuterRef(filter_rhs.name))` re-anchor "
                      "in Query.split_exclude for a local F rhs, leaving the F unwrapped "
                      "in the inner subquery. A bare F resolved inside the inner subquery "
                      "denotes the inner subquery's own row (level +1) instead of the "
                      "original query (level 0): an exclude/~Q with a local field rhs over "
                      "an N-to-many relation matches the wrong rows. This regresses the "
                      "pre-existing F-rebind behaviour (a P2P regression) and is not the "
                      "gold patch.",
        "rationale": "rejected by the kind_local level-arithmetic Ensures: "
                     "resolved_level_in_inner(local)=1, target_level(local)=0, "
                     "so 1 - Result == 0 forces Result==1; returning 0 violates it.",
    },
    # (3) PARTIAL-DOMAIN: a plain VALUE gets a spurious hop (local/outer correct).
    {
        "id": "weak-value-one-hop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _REBIND_IMPL,
            """    if rhs_kind == kind_value():
        # spurious extra hop on a plain concrete value.
        return 1
    if rhs_kind == kind_local():
        return 1
    return 1""",
        ),
        "refinement": "Faithful real patch: wrap a plain concrete value rhs in an "
                      "OuterRef when carrying it into the inner subquery. A literal has "
                      "no query reference; wrapping it as an OuterRef turns a constant "
                      "into a (broken) outer-query reference, so an exclude(field=<value>) "
                      "over an N-to-many relation crashes or returns wrong rows. The gold "
                      "patch leaves a plain value untouched (no rewrite branch fires); "
                      "this regresses the common literal-rhs exclude path (P2P).",
        "rationale": "rejected by Ensures(Implies(rhs_kind==kind_value(), Result()==0)); "
                     "returning 1 for a value violates the no-hop clause.",
    },
    # (4) THE NORMALISE-GUARD DISCRIMINATOR: normalise EVERYTHING
    # (== model_prepatch_2.py == pre-patch rhs_is_direct_value()).
    {
        "id": "weak-normalize-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _NORM_IMPL,
            """    # pre-patch rhs_is_direct_value(): normalise every kind, including
    # query expressions (they lack `as_sql`).
    return True""",
        ),
        "refinement": "Faithful real patch: keep the pre-patch guard "
                      "`self.rhs_is_direct_value()` (= not hasattr(self.rhs,'as_sql')) "
                      "in RelatedLookupMixin.get_prep_lookup, which is True for an F and "
                      "an OuterRef too (neither defines as_sql). It then runs "
                      "get_normalized_value(...) on a query expression that has no "
                      "concrete value to coerce, mangling the OuterRef before it can be "
                      "resolved against the right query level — the OuterRef-in-exclude "
                      "path (the F2P motivation) breaks. This is the unfixed behaviour.",
        "rationale": "rejected by Ensures(Result() == (not is_query_expression(rhs_kind))) "
                     "and Ensures(Result() == (rhs_kind == kind_value())): for "
                     "kind_local/kind_outer the spec pins Result==False; returning True "
                     "violates both clauses.",
    },
    # (5) PARTIAL-DOMAIN: normalise a LOCAL (F) but correctly pass an OuterRef.
    {
        "id": "weak-normalize-local-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _NORM_IMPL,
            """    if rhs_kind == kind_outer():
        return False
    # wrongly normalise an F (a query expression) as if it were a plain value.
    return True""",
        ),
        "refinement": "Faithful real patch: guard normalisation on isinstance(self.rhs, "
                      "OuterRef) instead of hasattr(self.rhs,'resolve_expression') — i.e. "
                      "pass through an OuterRef but still normalise an F. An F is a query "
                      "expression with no concrete value; running get_normalized_value on "
                      "it corrupts the field reference for related-field lookups (a P2P "
                      "regression on F-valued related lookups). The gold predicate "
                      "excludes BOTH F and OuterRef from normalisation.",
        "rationale": "rejected by Ensures(Result() == (not is_query_expression(rhs_kind))): "
                     "is_query_expression(local)=True so Result must be False; "
                     "returning True for kind_local violates it.",
    },
]


# =============================================================================
# AXIOM LANE  (no @ContractOnly axiom; these re-validate the two A-reference
# deep models against the REAL Django objects in Docker, gold applied — the
# axiom_check.py logic, embedded self-contained. expect="holds".)
# =============================================================================

_PROBE_CLASSIFY = r'''
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
    print("AXIOM-CLASSIFY SKIP: Django not configurable: %r" % (exc,))
    sys.exit(0)

from django.db.models import F
from django.db.models.expressions import OuterRef

KIND_VALUE, KIND_LOCAL, KIND_OUTER = 0, 1, 2
def model_is_query_expression(kind):
    return kind in (KIND_LOCAL, KIND_OUTER)

# Caller-reachable rhs kinds: a plain value, an F (local), an OuterRef (outer).
# The model's is_query_expression(kind) MUST equal the real post-patch predicate
# hasattr(rhs, 'resolve_expression') on each, and the normalise decision
# (not query-expression) must equal (kind == value).
samples = [
    (KIND_VALUE, 7), (KIND_VALUE, "abc"), (KIND_VALUE, None), (KIND_VALUE, 0),
    (KIND_LOCAL, F("name")), (KIND_LOCAL, F("pk")),
    (KIND_OUTER, OuterRef("pk")), (KIND_OUTER, OuterRef("job")),
    (KIND_OUTER, OuterRef(OuterRef("pk"))),   # nested OuterRef is still an OuterRef
]
for kind, rhs in samples:
    has_resolve = hasattr(rhs, "resolve_expression")
    assert has_resolve == model_is_query_expression(kind), (
        "is_query_expression mismatch kind=%d rhs=%r: real hasattr(resolve_expression)=%r model=%r"
        % (kind, rhs, has_resolve, model_is_query_expression(kind)))
    normalise_post = not has_resolve
    assert normalise_post == (kind == KIND_VALUE), (
        "normalise decision wrong kind=%d rhs=%r" % (kind, rhs))
    # the post-patch real predicate is hasattr(resolve_expression), NOT the
    # pre-patch hasattr(as_sql); confirm F/OuterRef have no as_sql (which is why
    # the pre-patch rhs_is_direct_value misclassified them).
    if kind != KIND_VALUE:
        assert not hasattr(rhs, "as_sql"), (
            "query-expression %r unexpectedly has as_sql" % (rhs,))

print("AXIOM-CLASSIFY OK: model is_query_expression matches real "
      "hasattr(resolve_expression) on %d caller-reachable samples; "
      "value->False, local/outer->True; query expressions lack as_sql." % len(samples))
sys.exit(0)
'''

_PROBE_LEVELS = r'''
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
    print("AXIOM-LEVELS SKIP: Django not configurable: %r" % (exc,))
    sys.exit(0)

from django.db.models import F
from django.db.models.expressions import OuterRef, ResolvedOuterRef

KIND_VALUE, KIND_LOCAL, KIND_OUTER = 0, 1, 2
def model_target_level(kind):
    return -1 if kind == KIND_OUTER else 0
def model_resolved_level_in_inner(kind):
    if kind == KIND_LOCAL: return 1
    if kind == KIND_OUTER: return 0
    return 0
def model_rebind_hops(kind):
    return 0 if kind == KIND_VALUE else 1  # both local and outer get one extra hop

# (a) a bare OuterRef collapses one outward level on resolution -> ResolvedOuterRef.
bare = OuterRef("pk")
rb = bare.resolve_expression()
assert isinstance(rb, ResolvedOuterRef) and not isinstance(rb, OuterRef), (
    "bare OuterRef should resolve to a (non-OuterRef) ResolvedOuterRef, got %r" % (rb,))

# (b) OuterRef(OuterRef(name)) PRESERVES one outward level: resolves to the inner
# still-unresolved OuterRef (this is precisely why the gold patch adds the extra
# wrap for an OuterRef rhs; without it, level -1 collapses onto level 0).
wrapped = OuterRef(OuterRef("pk"))
rw = wrapped.resolve_expression()
assert isinstance(rw, OuterRef) and not isinstance(rw, ResolvedOuterRef), (
    "OuterRef(OuterRef(..)) should resolve to the inner unresolved OuterRef, got %r" % (rw,))
assert getattr(rw, "name", None) == "pk", "inner OuterRef name not preserved: %r" % (getattr(rw, "name", None),)

# (c) an F re-anchored as OuterRef(name) resolves to a ResolvedOuterRef (the
# originally-local reference now denotes one level out from the inner subquery).
reanchored_local = OuterRef("name")  # models F('name') -> OuterRef('name')
rl = reanchored_local.resolve_expression()
assert isinstance(rl, ResolvedOuterRef), (
    "F re-anchored as OuterRef should resolve to ResolvedOuterRef, got %r" % (rl,))

# (d) the model's level arithmetic is internally consistent for both
# query-expression kinds and gives one extra hop each; zero for a plain value.
for kind in (KIND_LOCAL, KIND_OUTER):
    assert model_resolved_level_in_inner(kind) - model_rebind_hops(kind) == model_target_level(kind), (
        "model level arithmetic inconsistent for kind=%d" % kind)
    assert model_rebind_hops(kind) == 1, "expected one extra hop for kind=%d" % kind
assert model_rebind_hops(KIND_VALUE) == 0

print("AXIOM-LEVELS OK: real OuterRef.resolve_expression confirms bare collapses "
      "one outward level (-> ResolvedOuterRef) while OuterRef(OuterRef(.)) preserves "
      "it (-> inner unresolved OuterRef); the model's one-extra-outward-hop re-anchor "
      "for both local and outer (and zero for value) is sound and consistent.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-classify-query-expression",
        "axiom": "is_query_expression (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_CLASSIFY,
        "rationale": "the deep model is_query_expression(kind) must equal the real "
                     "post-patch predicate hasattr(rhs,'resolve_expression') on every "
                     "caller-reachable rhs (plain value / F / OuterRef / nested OuterRef); "
                     "if the real classification disagreed the A-reference would be "
                     "unsound (AXIOM-UNSOUND).",
    },
    {
        "id": "ax-outerref-resolution-levels",
        "axiom": "rebind_into_inner_subquery level arithmetic (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_LEVELS,
        "rationale": "the deep model's one-extra-outward-hop re-anchor must match real "
                     "OuterRef.resolve_expression: a bare OuterRef collapses one outward "
                     "level (-> ResolvedOuterRef) while OuterRef(OuterRef(.)) preserves it; "
                     "if the real resolution disagreed the level arithmetic would be "
                     "unsound (AXIOM-UNSOUND).",
    },
]
