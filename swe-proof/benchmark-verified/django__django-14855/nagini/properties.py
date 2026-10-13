# properties.py — PBT falsification battery for django__django-14855. NOT a Nagini
# module; a record of adversarially-reasoned cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are FULL model.py variants that share
# the FROZEN spec byte-for-byte (region surgery: ONLY the text strictly between the
# function's `# impl-start` / `# impl-end` is edited; the spec view — axioms / pure /
# pre-/post-conditions + signatures — is never touched), checked by Nagini verify +
# markers.same_spec. Axiom cases drive the REAL framework callee django.urls.reverse
# in the instance Docker image (the consumed @ContractOnly axiom resolve_prefix),
# reusing the validated G-AX logic from axiom_check.py (embedded below).
#
# ------------------------------------------------------------------------------------
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   related_link_target(names, prefixes, exposes, default_idx, current_idx) -> PSeq[int]
#   Models the gold change to AdminReadonlyField.get_admin_url: the read-only related
#   object's link must point INTO the CURRENT admin-site deployment, so reverse() is
#   now called with current_app=self.model_admin.admin_site.name. The model returns the
#   URL prefix the produced link carries, or the EMPTY sequence when the page produces
#   NO link at all. The F2P (test_readonly_foreignkey_links_custom_admin_site) renders
#   under a NON-default custom admin site and asserts the href carries that site's
#   prefix; it also asserts the NO-LINK outcome for a related model that site does not
#   register (the reason the gold test_patch had to ADD site2.register(...) calls before
#   the link renders at all).
#
#   THE ROUTE AXIS (`exposes`). reverse() narrows to ONE instance namespace and only
#   then looks the view identifier up INSIDE it (django/urls/base.py:41-84, then
#   _reverse_with_prefix), so an identifier a SIBLING deployment carries but the
#   selected deployment does not raises NoReverseMatch — and get_admin_url's
#   `except NoReverseMatch: return str(remote_obj)` arm then renders the object with no
#   link. Sibling AdminSites really do differ this way: each has its own _registry, so a
#   related model's change view exists under a site only if that site registers it.
#   `exposes[k]` is that per-deployment observable: does deployment k carry a route for
#   the identifier and argument being resolved. Resolution is therefore PARTIAL, and the
#   spec says so — see mapping.md §3.1 and the four Q clauses below.
#
#   PRECONDITION (ten clauses):
#     (P1) Requires(Acc(list_pred(names), 1/2))      # HALF permission => READ-ONLY
#     (P2) Requires(Acc(list_pred(prefixes), 1/2))   # HALF permission => READ-ONLY
#     (P2b) Requires(Acc(list_pred(exposes), 1/2))   # HALF permission => READ-ONLY
#     (P3) Requires(len(names) == len(prefixes))      # parallel registry
#     (P3b) Requires(len(exposes) == len(names))      # parallel registry
#     (P4) Requires(0 <= default_idx < len(names))
#     (P5) Requires(0 <= current_idx < len(names))
#     (P6) Requires(Forall2 ... names[a]==names[b] => a==b)  # instance names UNIQUE
#     (P6b) Requires(Forall k: len(prefixes[k]) > 0)  # a registered prefix is NON-EMPTY
#     (P7) Requires(Forall i: names[current_idx][i] != 58)   # current name has no ':'
#   POSTCONDITION (eleven clauses; seven framing + four LOAD-BEARING):
#     (Q1) Ensures(Acc(list_pred(names), 1/2))        # returns the read permission
#     (Q2) Ensures(Acc(list_pred(prefixes), 1/2))     # returns the read permission
#     (Q2b) Ensures(Acc(list_pred(exposes), 1/2))     # returns the read permission
#     (Q3) Ensures(len(prefixes) == len(names))
#     (Q3b) Ensures(len(exposes) == len(names))
#     (Q4) Ensures(0 <= current_idx < len(prefixes))
#     (Q4b) Ensures(0 <= default_idx < len(prefixes))  # framing for Q6a/Q6b
#     (Q5a) Ensures(len(names[current_idx]) > 0 and exposes[current_idx]
#                   ==> Result() == ToSeq(prefixes)[current_idx])   # <-- LOAD-BEARING
#     (Q5b) Ensures(len(names[current_idx]) > 0 and not exposes[current_idx]
#                   ==> len(Result()) == 0)                          # <-- LOAD-BEARING
#     (Q6a) Ensures(len(names[current_idx]) == 0 and exposes[default_idx]
#                   ==> Result() == ToSeq(prefixes)[default_idx])    # <-- LOAD-BEARING
#     (Q6b) Ensures(len(names[current_idx]) == 0 and not exposes[default_idx]
#                   ==> len(Result()) == 0)                          # <-- LOAD-BEARING
#   The four guards are pairwise mutually exclusive and jointly TOTAL over the
#   admissible inputs, so together they still fully PIN the returned value on every
#   admissible input — there is no slack and no unconstrained input. P6b (every
#   registered prefix is non-empty) is what makes "produced no link" (the empty
#   sequence) distinguishable from every prefix a deployment can contribute, so the
#   two len(Result())==0 clauses are as sharp as the two equalities.
#     Q5a is the clause the fix is about (the link points into a deployment you can
#   actually point into, and which carries the route). Q5b/Q6b state what the real
#   composite does when the deployment resolution lands in carries no route for the
#   identifier: NoReverseMatch, hence NO link, hence no prefix. Q6a/Q6b state what the
#   real callee does for a deployment with an EMPTY identifier, which is falsy in
#   reverse's `if current_app:` guard (django/urls/base.py:41) and therefore resolves
#   against the DEFAULT deployment. Q6a/Q6b are NOT weakenings: they are shared by both
#   twins and so carry no discriminating content, while Q5a alone still rejects the
#   pre-patch call. Q5b/Q6b are likewise not weakenings of Q5a/Q6a: they constrain a
#   DISJOINT slice of the input space (the route flag False), on which the old
#   unconditional equality was simply UNSOUND against the real callee — the
#   `echo-unguarded` and `weak-total-resolution` rivals below are the controls that the
#   route axis was added as an obligation and not as an escape hatch. See mapping.md
#   §3.1 "Falsiness dependency" and "Partial resolution".
#
# FRAME-MUTATION lane is MANDATORY: `names`, `prefixes` AND `exposes` are all
#   Acc(list_pred(...),1/2) (read-only). A rival that WRITES any of the three must be
#   REJECTED for INSUFFICIENT PERMISSION. Byte-fuzzers never think to mutate the input;
#   this is the project's #1 weakness class. The real callee only READS the resolver's
#   registered-instance registry (the AdminSite namespace dict) and each site's route
#   table (its _registry-derived URLpatterns); a faithful patch never mutates either (it
#   would corrupt the process-global URL resolver state for every subsequent reverse()
#   in the running site, and registering a model under a site the operator did not ask
#   for would silently expose an admin route). We supply ONE frame-mutation rival per
#   read-only input (names-write, prefixes-write, exposes-write).
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo. Q5a/Q6a pin the result to
#   ToSeq(prefixes)[current_idx] / [default_idx] and Q5b/Q6b pin it to the empty
#   sequence — all GROUNDED entirely in the arguments `prefixes`, `exposes`,
#   `current_idx` and `default_idx`. (Note the bare echo `return pf[current_idx]` is
#   REJECTED, since it violates Q5b on a current deployment without the route and Q6a on
#   an empty current name; that is the `echo-unguarded` rival below.) The @Pure
#   @ContractOnly axiom resolve_prefix is likewise a function of its arguments
#   (names/prefixes/exposes/default_idx/selector/has_selector); it is NOT an opaque
#   answer-key holding the expected output that an impl could echo. On each of the four
#   guarded slices exactly ONE value satisfies the clause, so there is no wrong echo —
#   the honest control is the cheapest faithful impl that produces that grounded value
#   (the positive control), not a wrong echo. The interesting attack is instead
#   WRONG-ARGUMENT use of the grounded axiom (call it with the wrong selector, the wrong
#   has_selector, the wrong default index, or a doctored route vector), covered by the
#   partial-domain rivals below. See 'assessment'.
#
# PARTIAL-DOMAIN lane: the central attack here, along TWO independent axes.
#   AXIS 1 — WHICH DEPLOYMENT (the recorded bug class: "the link points to the WRONG
#   deployment"). Every rival on this axis is correct on the COINCIDENT sub-domain
#   (current_idx == default_idx: the current site IS the default, so prefixes[current]
#   == prefixes[default]) but WRONG on the discriminating sub-domain
#   (current_idx != default_idx — exactly the F2P's non-default custom site):
#     - weak-no-selector : calls resolve_prefix(..., has_selector=False) => returns
#                          prefixes[default_idx]. This IS model_prepatch.py (the
#                          missing current_app). Wrong whenever current != default.
#     - weak-return-default : return prefixes[default_idx] directly (no axiom call).
#                          Same wrong value, most blatant.
#     - weak-default-selector : selector = names[default_idx], has_selector=True. Same
#                          wrong value, dressed up — and it cannot even establish the
#                          axiom's colon-free domain for that name (see its rationale).
#     - weak-default-arg-swapped : names the CURRENT deployment as the callee's fallback
#                          and supplies NO selector. Right on both named legs, WRONG on
#                          the empty-identifier legs where the real callee falls back to
#                          the registered default. Discriminates Q6a.
#   AXIS 2 — WHETHER A LINK IS PRODUCED AT ALL (the route axis this spec adds). Every
#   rival here is correct on the sub-domain where the selected deployment carries the
#   route (the homogeneous registries a fuzzer generates) and WRONG on the heterogeneous
#   registries the F2P and the gold test_patch actually exercise:
#     - weak-total-resolution : treats resolution as TOTAL — always produces a link,
#                          never consulting whether the selected deployment carries the
#                          route. This is the OLD over-claim; it is what the real callee
#                          does NOT do. Discriminates Q5b.
#     - echo-unguarded : returns prefixes[current_idx] unconditionally — the old
#                          unguarded equality, wrong on BOTH new axes at once.
#     - weak-exposes-forced : doctors the route vector (forces the current deployment's
#                          flag True) before resolving, i.e. assumes the deployment
#                          carries every identifier. Discriminates Q5b.
#     - weak-route-axis-swapped : reads the route flag off the CURRENT deployment even on
#                          the empty-identifier leg, where resolution actually lands in
#                          the DEFAULT deployment. Discriminates Q6b.
#     - weak-always-empty : never produces a link. The dual degenerate rival: it
#                          satisfies both len(Result())==0 clauses and nothing else.
#                          Discriminates Q5a.
#
# CONTROL-FLOW-EFFECT lane: N/A. related_link_target has a SINGLE return path and no
#   exceptional / side-effecting fork in its contract (no Exsures, no raise). The
#   NoReverseMatch fork of the real composite is not abstracted away — it is exactly what
#   the EMPTY-sequence result denotes (mapping.md §1), and P6b makes that value
#   unreachable for any produced link, so the fork IS observable in the returned value.
#   The whole observable is therefore the returned value, fully pinned by Q5a/Q5b/Q6a/Q6b,
#   and there is no raise/return/effect difference invisible to the value abstraction to
#   discriminate. Omitted (justified in 'assessment').
#
# AXIOM lane: meta.axioms has ONE A-consumed @ContractOnly axiom, resolve_prefix,
#   modelling django.urls.reverse(viewname, ..., current_app=...) namespace->instance
#   selection AND the in-instance identifier lookup that follows it. The real callee
#   lives only in the instance image, so the axiom probes run in Docker (apply_gold
#   irrelevant — reverse is unchanged by the patch; we set apply_gold=True to match the
#   post-gold runtime, harmless). Both probes EMBED the validated G-AX logic from
#   axiom_check.py (which passes, 2996 obs, 0 violations, every clause exercised) and
#   EXECUTE the real reverse — never scrape source:
#     - ax-sound-resolve_prefix (axiom-soundness): builds real URLconfs holding the
#       3-tuple AdminSite.urls returns — (get_urls(), 'admin', self.name),
#       django/contrib/admin/sites.py:303 — for several siblings sharing ONE app
#       namespace but with distinct instance namespaces, distinct prefixes and DISTINCT
#       ROUTE SETS, drives the real reverse, and asserts all four Ensures clauses: a
#       separator-free registered instance name selects its own prefix when it carries
#       the route and produces NO url when it does not; no current_app (and equally an
#       empty one) does the same for the registered default; + the colon-separator
#       DOMAIN boundary (a ':'-bearing name is split and falls to default, NOT matched
#       whole) so the axiom never over-claims; + the non-empty-prefix domain fact at its
#       root-mount edge; + fuzz. Leg coverage is asserted, so a probe that silently
#       stopped exercising the no-url clauses FAILS. Any disagreement => AXIOM-UNSOUND.
#     - ax-cover-resolve_prefix (axiom-containment): the model reaches resolve_prefix
#       with selector = names[current_idx], which P7 forces to be SEPARATOR-FREE (no ':'
#       code point), has_selector=True, and the route vector `exposes` UNDOCTORED — so
#       the reachable argument space spans BOTH route states of the selected deployment
#       and BOTH of the default's. The probe asserts that exactly this reachable shape
#       lies INSIDE the axiom's domain (Requires: selector has no U+003A; parallel
#       lengths; unique names; non-empty prefixes) AND that the axiom's Ensures covers
#       every reachable combination — including the two no-url legs, which an axiom
#       stated only for route-carrying deployments would leave uncovered
#       (AXIOM-TOO-WEAK-FOR-CALLER).
# ------------------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "django__django-14855"
FLOAT_ENCODING = None  # meta.json float_encoding is null


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


_BASE = (Path(__file__).parent / "model.py").read_text()


# The frozen FUNCTION impl region body, verbatim (everything strictly BETWEEN the
# function's `# impl-start` / `# impl-end`). Every spec variant _swap()s ONLY this
# block, so the edit never touches the spec (axioms/pure/pre-/post-conditions regions
# + the function signature). same_spec is computed over the spec_view, which elides
# every impl region, so swapping inside here is GUARANTEED same_spec.
_IMPL = """\
    nm = ToSeq(names)
    pf = ToSeq(prefixes)
    ex = ToSeq(exposes)
    selector = nm[current_idx]  # type: PSeq[int]
    url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
    # selector == names[current_idx] is a registered instance name (k=current);
    # uniqueness pins resolve_prefix's choice to prefixes[current_idx].
    Assert(nm[current_idx] == selector)
    return url"""

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the function impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-inline-selector: structurally DIFFERENT but behaviourally identical. Instead of
# binding the locals `ex = ToSeq(exposes)` / `selector = nm[current_idx]` and passing
# them, this variant inlines both directly into the resolve_prefix call (and drops the
# now-unused intermediates), then returns the call result directly. The load-bearing
# facts the gold proof needs are all preserved: the call still passes has_selector=True
# with the selector argument equal to nm[current_idx] and the UNDOCTORED route vector
# (so the axiom's has_selector Foralls instantiate at k=current_idx => the current
# deployment's prefix when it carries the route and the empty sequence when it does
# not), and the Assert pinning nm[current_idx]==nm[current_idx] is kept verbatim as the
# framing trigger. No loop, no recursion, no dropped lemma (directive 2/3): only the
# textual shape (named locals vs inlined arguments, return-call vs return-local)
# changes. If it FAILS => SPEC-TOO-STRONG (a faithful, structurally-different correct
# impl is rejected).
_POS_INLINE = """\
    nm = ToSeq(names)
    pf = ToSeq(prefixes)
    # Inline nm[current_idx] as the selector argument (no intermediate local) and
    # return the call result directly. selector == names[current_idx] (k=current),
    # so the axiom's has_selector Forall pins the choice to prefixes[current_idx]
    # when the current deployment carries the route and to nothing when it does not.
    Assert(nm[current_idx] == nm[current_idx])
    return resolve_prefix(nm, pf, ToSeq(exposes), default_idx, nm[current_idx], True)"""


# admiss-reads: an admissibility positive control. The precondition grants the three
# half-permissions (P1,P2,P2b) plus the structural/uniqueness/non-empty-prefix/colon
# Requires (P3-P7). This control keeps the gold impl VERBATIM but FIRST asserts, under
# those permissions, that the reads a normal F2P-shaped registry needs are admitted: the
# three lengths are equal and readable, the indices are in range, and both the current
# instance name AND the current deployment's route flag are readable under the
# half-permissions. No write, so no extra permission demand. If the precondition could
# not admit a legitimate sibling-registry input — in particular a HETEROGENEOUS one,
# where the route flags differ across siblings, which is the shape the gold test_patch
# builds — this would fail => PRECOND-TOO-STRONG.
_ADMISS = (
    "    # Admissibility: a normal F2P-shaped sibling registry is in-domain; the\n"
    "    # half-permissions admit reading the parallel lengths, the current name and\n"
    "    # the current deployment's route flag.\n"
    "    Assert(len(names) == len(prefixes))\n"
    "    Assert(len(exposes) == len(names))\n"
    "    Assert(0 <= current_idx and current_idx < len(names))\n"
    "    Assert(ToSeq(names)[current_idx] == ToSeq(names)[current_idx])  # read OK at 1/2\n"
    "    Assert(ToSeq(exposes)[current_idx] == ToSeq(exposes)[current_idx])  # read OK at 1/2\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVALS (MANDATORY — names, prefixes AND exposes are Acc(...,1/2)).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-names: keeps the gold body VERBATIM (so the rejection is attributable
# SOLELY to the added write, not to a value mismatch), then WRITES BACK into the
# read-only input `names`: names[current_idx] = names[current_idx]. A no-op store, but
# a STORE — it demands FULL list_pred(names) permission, which the caller granted only
# at 1/2 (P1). The verifier must reject for insufficient permission. P5 guarantees
# current_idx is a valid index so the store is reachable on the F2P input.
_FRAME_MUT_NAMES = (
    "    # Frame violation: write back into the read-only (Acc(list_pred(names),1/2)) input.\n"
    "    names[current_idx] = names[current_idx]\n"
    + _IMPL
)

# frame-mut-prefixes: the dual — keeps the gold body verbatim then WRITES BACK into the
# read-only input `prefixes`: prefixes[current_idx] = prefixes[current_idx]. A no-op
# store demanding FULL list_pred(prefixes) permission, granted only at 1/2 (P2). The
# verifier must reject for insufficient permission.
_FRAME_MUT_PREFIXES = (
    "    # Frame violation: write back into the read-only (Acc(list_pred(prefixes),1/2)) input.\n"
    "    prefixes[current_idx] = prefixes[current_idx]\n"
    + _IMPL
)

# frame-mut-exposes: the third read-only input, and the one with the sharpest real-world
# reading — keeps the gold body verbatim then WRITES BACK into `exposes`:
# exposes[current_idx] = exposes[current_idx]. A no-op store demanding FULL
# list_pred(exposes) permission, granted only at 1/2 (P2b). The verifier must reject for
# insufficient permission.
_FRAME_MUT_EXPOSES = (
    "    # Frame violation: write back into the read-only (Acc(list_pred(exposes),1/2)) input.\n"
    "    exposes[current_idx] = exposes[current_idx]\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each shares the frozen spec exactly; only the impl changes.
# ---------------------------------------------------------------------------

# --- AXIS 1: which deployment does the link point into? --------------------

# weak-no-selector: PARTIAL-DOMAIN + the literal pre-patch (model_prepatch.py). Calls
# resolve_prefix with has_selector=False, which by the axiom's `not has_selector`
# Ensures returns prefixes[default_idx] — the registered default's prefix (or nothing,
# when the DEFAULT deployment lacks the route). Correct only on the coincident
# sub-domain current_idx==default_idx; WRONG whenever the current deployment is not the
# default (the F2P custom site). Q5a demands prefixes[current_idx]; the verifier cannot
# prove prefixes[default_idx]==prefixes[current_idx] for arbitrary distinct indices, so
# it rejects.
_WEAK_NO_SELECTOR = """\
    nm = ToSeq(names)
    pf = ToSeq(prefixes)
    ex = ToSeq(exposes)
    selector = nm[current_idx]  # type: PSeq[int]
    # PRE-PATCH: omit the current_app selector (has_selector=False) -> default prefix.
    url = resolve_prefix(nm, pf, ex, default_idx, selector, False)
    return url"""

# weak-default-selector: PARTIAL-DOMAIN. Supplies has_selector=True but with the
# DEFAULT instance's name as the selector (names[default_idx]) — what a real patch that
# passed the wrong site's name to current_app would do. See its rationale for the exact
# clause that rejects it: this rival never even reaches the value comparison, because
# the caller knows nothing about the DEFAULT deployment's name (P7 constrains only the
# CURRENT one), so it cannot establish the axiom's colon-free domain for it.
_WEAK_DEFAULT_SELECTOR = """\
    nm = ToSeq(names)
    pf = ToSeq(prefixes)
    ex = ToSeq(exposes)
    sel = nm[default_idx]  # type: PSeq[int]
    # Resolve relative to the DEFAULT deployment's name instead of the current one.
    url = resolve_prefix(nm, pf, ex, default_idx, sel, True)
    Assert(nm[default_idx] == sel)
    return url"""

# weak-return-default: PARTIAL-DOMAIN, most blatant. Returns prefixes[default_idx]
# directly without consulting the axiom at all. Same wrong value as weak-no-selector;
# correct only when current==default. Q5a demands prefixes[current_idx]; rejected
# whenever current != default. (Bound to a typed local first to avoid the bare-return
# `# type:` pitfall.)
_WEAK_RETURN_DEFAULT = """\
    pf = ToSeq(prefixes)
    out = pf[default_idx]  # type: PSeq[int]
    return out"""

# weak-default-arg-swapped: PARTIAL-DOMAIN on the EMPTY-IDENTIFIER slice, and the
# sharpest in-domain probe of Q6a. It names the CURRENT deployment as the fallback the
# callee uses when no selector is supplied (default_idx := current_idx) and then
# supplies NO selector. By the axiom's no-selector clauses the result is the CURRENT
# deployment's prefix (or nothing) — so it is RIGHT on both named legs and WRONG exactly
# on the empty-identifier legs, where the real callee falls back to the REGISTERED
# default. Unlike weak-default-selector it stays entirely inside the axiom's domain (it
# passes no name as a selector at all), so its rejection is a genuine VALUE-level one.
_WEAK_DEFAULT_ARG_SWAPPED = """\
    nm = ToSeq(names)
    pf = ToSeq(prefixes)
    ex = ToSeq(exposes)
    selector = nm[current_idx]  # type: PSeq[int]
    # Name the CURRENT deployment as the fallback the callee uses when no selector
    # is supplied, and supply no selector.
    url = resolve_prefix(nm, pf, ex, current_idx, selector, False)
    return url"""


# --- AXIS 2: is a link produced at all? (the route axis) -------------------

# weak-total-resolution: THE REGRESSION RIVAL for the faithfulness repair on the route
# axis. It treats resolution as TOTAL — it always produces a link, carrying the current
# deployment's prefix when that deployment has a non-empty identifier and the default's
# otherwise, WITHOUT ever consulting whether the deployment resolution lands in carries
# a route for the identifier at all. That is precisely the behaviour the OLD, route-blind
# postcondition demanded, and precisely what the real composite does NOT do: reverse
# narrows to one instance first and raises NoReverseMatch when the identifier is absent
# from it, and get_admin_url's except-arm then renders NO link. It must be REJECTED, on
# Q5b. If it VERIFIES the spec is back to modelling resolution as total.
_WEAK_TOTAL_RESOLUTION = """\
    nm = ToSeq(names)
    pf = ToSeq(prefixes)
    # Treat resolution as TOTAL: always produce a link, carrying the current
    # deployment's prefix when it has a non-empty identifier and the default
    # deployment's otherwise, without consulting whether the deployment
    # resolution lands in carries a route for the identifier at all.
    out = pf[default_idx]  # type: PSeq[int]
    if len(nm[current_idx]) > 0:
        out = pf[current_idx]
    return out"""

# echo-unguarded: the doubly-wrong echo. Returns prefixes[current_idx] unconditionally —
# route-blind AND identifier-blind, i.e. exactly what a real patch would do if it
# bypassed reverse entirely and pasted the current site's mount in directly. It diverges
# from the gold patch on BOTH axes: where the current site carries no route for the
# related model (the gold test_patch's own starting state, before it adds the
# site2.register(...) calls) the real patched code renders NO link while this rival
# emits a URL; and where the current AdminSite's name is '' (legal and unvalidated,
# sites.py:36) the falsy `if current_app:` guard makes the real patched code resolve
# against the DEFAULT site while this rival emits the empty-named site's prefix.
_ECHO_UNGUARDED = """\
    pf = ToSeq(prefixes)
    out = pf[current_idx]  # type: PSeq[int]
    return out"""

# weak-exposes-forced: WRONG-ARGUMENT use of the grounded axiom on the route axis. It
# calls the axiom correctly in every respect except that it first DOCTORS the route
# vector, forcing the current deployment's flag True — i.e. it assumes the deployment
# carries a route for whatever identifier is asked of it. The real patch has no such
# freedom: whether a site exposes a related model's change view is fixed by that site's
# own _registry. Note the doctored vector still satisfies every Requires of the axiom
# (update preserves length), so the rejection cannot come from the domain — it is a
# VALUE-level rejection on Q5b.
_WEAK_EXPOSES_FORCED = """\
    nm = ToSeq(names)
    pf = ToSeq(prefixes)
    ex = ToSeq(exposes)
    # Force the current deployment's route flag to True before resolving: claim a
    # link is always producible for the current deployment.
    ex2 = ex.update(current_idx, True)  # type: PSeq[bool]
    selector = nm[current_idx]  # type: PSeq[int]
    url = resolve_prefix(nm, pf, ex2, default_idx, selector, True)
    return url"""

# weak-route-axis-swapped: the CROSS-AXIS rival, and the one a route-blind reader is
# most likely to write. It gets the route axis right for the named leg but reads the
# flag off the CURRENT deployment in BOTH legs — including the empty-identifier leg,
# where resolution actually lands in the DEFAULT deployment and it is the DEFAULT's
# route set that decides whether any link is produced. It is therefore correct on every
# homogeneous registry and on every non-empty current identifier, and wrong exactly on
# the empty-identifier rows where the two deployments' route flags differ (measured
# against the real patched callee: current site name '', current carries the route, the
# default does not => real renders NO link). Discriminates Q6b.
_WEAK_ROUTE_AXIS_SWAPPED = """\
    nm = ToSeq(names)
    pf = ToSeq(prefixes)
    ex = ToSeq(exposes)
    # Read the route flag off the CURRENT deployment in both legs, including the
    # empty-identifier leg where resolution actually lands in the default one.
    out = PSeq()  # type: PSeq[int]
    if ex[current_idx]:
        if len(nm[current_idx]) > 0:
            out = pf[current_idx]
        else:
            out = pf[default_idx]
    return out"""

# weak-always-empty: the DUAL degenerate rival, and the control that the two
# len(Result())==0 clauses did not swallow the spec. It never produces a link at all —
# it satisfies Q5b and Q6b vacuously and nothing else. A spec that had "handled"
# partiality by merely permitting the empty result (rather than pinning WHEN it occurs)
# would admit this. Q5a rejects it.
_WEAK_ALWAYS_EMPTY = """\
    # Never produce a link at all.
    out = PSeq()  # type: PSeq[int]
    return out"""


SPEC_TESTS = [
    {
        "id": "pos-inline-selector",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_INLINE),
        "rationale": (
            "structurally-different but CORRECT impl: the intermediate locals `ex = "
            "ToSeq(exposes)` and `selector = nm[current_idx]` are dropped and both are "
            "inlined directly into the resolve_prefix call, returning the call result "
            "directly. Every load-bearing fact the gold proof needs is kept: "
            "has_selector=True with selector == nm[current_idx] and the UNDOCTORED route "
            "vector (so the axiom's has_selector Foralls instantiate at k=current_idx => "
            "prefixes[current_idx] when that deployment carries the route, the empty "
            "sequence when it does not) and the framing "
            "Assert(nm[current_idx]==nm[current_idx]). No loop / recursion / dropped "
            "lemma (directive 2/3). If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (three Acc(list_pred,1/2) half-permissions + the "
            "parallel-length / index-range / name-uniqueness / non-empty-prefix / "
            "colon-free Requires) must admit a normal F2P-shaped sibling registry, "
            "including a HETEROGENEOUS one whose siblings carry different route sets: "
            "the three parallel lengths are equal and readable, the indices in range, "
            "and both the current instance name and the current deployment's route flag "
            "readable under the half-permissions. The gold impl is otherwise verbatim "
            "(only reads/asserts added inside the impl region, no write). If it FAILS "
            "=> PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-names",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT_NAMES),
        "refinement": (
            "the gold patch only READS the resolver's registered-instance registry "
            "(reverse() consults resolver.app_dict / namespace_dict; it never mutates "
            "the AdminSite name list). A faithful real patch that wrote back into the "
            "instance-name registry would corrupt the process-global URL resolver state "
            "for every subsequent reverse() in the running site — it would not be the "
            "gold patch and would not faithfully resolve. The store here is a no-op only "
            "by coincidence; the point is the spec must forbid ANY write to `names`."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `names` is granted at "
            "Acc(list_pred(names),1/2) (P1); the store names[current_idx]="
            "names[current_idx] demands FULL write permission, unavailable, so the "
            "verifier rejects for INSUFFICIENT PERMISSION. The gold body is kept "
            "verbatim so the rejection is attributable solely to the write. If it "
            "VERIFIES => the read-only frame on `names` is hollow (frame-mutation, the "
            "#1 weakness class)."
        ),
    },
    {
        "id": "frame-mut-prefixes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT_PREFIXES),
        "refinement": (
            "the gold patch only READS the per-instance mount prefixes (reverse() reads "
            "resolver.namespace_dict[ns]); it never mutates them. A faithful real patch "
            "that wrote back into the prefix registry would corrupt the resolver's "
            "namespace->prefix mapping for every subsequent reverse() — it would not be "
            "the gold patch and would not faithfully resolve. The store is a no-op only "
            "by coincidence; the spec must forbid ANY write to `prefixes`."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `prefixes` is granted at "
            "Acc(list_pred(prefixes),1/2) (P2); the store prefixes[current_idx]="
            "prefixes[current_idx] demands FULL write permission, unavailable, so the "
            "verifier rejects for INSUFFICIENT PERMISSION. The gold body is kept "
            "verbatim so the rejection is attributable solely to the write. If it "
            "VERIFIES => the read-only frame on `prefixes` is hollow (frame-mutation)."
        ),
    },
    {
        "id": "frame-mut-exposes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT_EXPOSES),
        "refinement": (
            "which related models a given admin deployment exposes a change view for is "
            "that deployment's OWN state (its AdminSite._registry, from which its "
            "URLpatterns are built). reverse() only READS the resulting route table; a "
            "faithful real patch never registers a model under a site to make its own "
            "link resolve — that would silently expose an admin route the operator never "
            "asked for, and would corrupt the resolver's route table for every "
            "subsequent reverse(). The store is a no-op only by coincidence; the spec "
            "must forbid ANY write to `exposes`."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `exposes` is granted at "
            "Acc(list_pred(exposes),1/2) (P2b); the store exposes[current_idx]="
            "exposes[current_idx] demands FULL write permission, unavailable, so the "
            "verifier rejects for INSUFFICIENT PERMISSION. The gold body is kept "
            "verbatim so the rejection is attributable solely to the write. If it "
            "VERIFIES => the read-only frame on the route axis is hollow, and an impl "
            "could 'fix' an unresolvable link by registering the route (frame-mutation)."
        ),
    },
    {
        "id": "weak-no-selector",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NO_SELECTOR),
        "refinement": (
            "this IS the pre-patch behaviour (model_prepatch.py): reverse() called "
            "WITHOUT current_app. Its faithful real patch is the UNCHANGED repo line "
            "`url = reverse(url_name, args=[quote(remote_obj.pk)])`, which resolves the "
            "link into the DEFAULT admin site (app_dict['admin'][0]) instead of the "
            "current one — exactly the bug the gold fixes. It fails the F2P "
            "test_readonly_foreignkey_links_custom_admin_site, which renders under a "
            "NON-default custom site and asserts the href carries that site's prefix. "
            "Does NOT resolve (precisely what G-DIFF senses)."
        ),
        "rationale": (
            "REJECTED by Q5a (the non-empty-name + route-carrying clause pinning "
            "Result() to ToSeq(prefixes)[current_idx]): with has_selector=False the "
            "axiom's `not has_selector` Ensures pins the result to prefixes[default_idx], "
            "but Q5a demands prefixes[current_idx]; the verifier cannot prove "
            "prefixes[default_idx]==prefixes[current_idx] for arbitrary distinct "
            "indices. PARTIAL-DOMAIN: correct only on current_idx==default_idx. If it "
            "VERIFIES => SPEC-TOO-WEAK (the current-vs-default selection is not "
            "enforced)."
        ),
    },
    {
        "id": "weak-return-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_RETURN_DEFAULT),
        "refinement": (
            "returning the default deployment's prefix directly is the degenerate wrong "
            "patch (e.g. hard-coding the default site's URL prefix, or never threading "
            "current_app through). The link always points into the default site, so "
            "under the F2P's non-default custom site the href is wrong. Does NOT "
            "resolve. Supporting near-miss carrying the same partial-domain refinement "
            "as weak-no-selector, reached without the axiom."
        ),
        "rationale": (
            "REJECTED by Q5a (the non-empty-name + route-carrying clause pinning "
            "Result() to ToSeq(prefixes)[current_idx]): the rival returns "
            "prefixes[default_idx], and the verifier cannot prove "
            "prefixes[default_idx]==prefixes[current_idx] for arbitrary distinct "
            "indices. PARTIAL-DOMAIN: correct only on current_idx==default_idx. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-default-selector",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DEFAULT_SELECTOR),
        "refinement": (
            "resolving relative to the DEFAULT deployment's name "
            "(current_app=names[default_idx]) is what a real patch that passed the wrong "
            "site's name to current_app would do — e.g. `current_app=self.admin_site"
            "._default_name` or a hard-coded default. The produced link carries the "
            "DEFAULT site's prefix, not the current site's, so under the F2P's "
            "non-default custom site the href is wrong. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED at the CALL SITE, before any value comparison: passing "
            "nm[default_idx] as the selector requires establishing the axiom's "
            "separator-free domain (Requires: no U+003A in `selector`) for the DEFAULT "
            "deployment's name, and the caller knows nothing about it — P7 constrains "
            "only names[current_idx]. So the verifier reports the unsatisfied "
            "PRECONDITION of resolve_prefix. That is a legitimate rejection of a rival "
            "that reaches outside what the caller was told, and it is a PRE-EXISTING "
            "property of this axiom's domain restriction, not an artefact of the route "
            "axis (measured: the same rival is rejected the same way against the "
            "pre-route-axis model). Its VALUE-level twin — same wrong deployment, but "
            "reached entirely inside the axiom's domain — is `weak-default-arg-swapped`, "
            "and the blunt version is `weak-return-default`; those two carry the "
            "partial-domain content on Axis 1. If this rival VERIFIES => SPEC-TOO-WEAK "
            "(either the domain restriction or the selection is not enforced)."
        ),
    },
    {
        "id": "weak-default-arg-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DEFAULT_ARG_SWAPPED),
        "refinement": (
            "this is the real patch that threads the CURRENT site in as the resolver's "
            "fallback rather than as the selector — e.g. mutating the resolver's default "
            "instance for the current app, or calling a helper that takes 'the site to "
            "fall back to' and passing self.model_admin.admin_site.name to it, while "
            "still calling reverse() with no current_app. On every named site it happens "
            "to produce the right prefix, so it passes the F2P; but for an AdminSite "
            "whose name is '' the real patched code resolves against the REGISTERED "
            "default (reverse's `if current_app:` guard, django/urls/base.py:41) while "
            "this rival resolves against the current site. Not the gold patch's "
            "behaviour."
        ),
        "rationale": (
            "REJECTED by Q6a (empty current identifier + route-carrying default => "
            "Result()==ToSeq(prefixes)[default_idx]): the rival names current_idx as the "
            "callee's fallback, so on that slice the axiom pins the result to "
            "prefixes[current_idx], which the verifier cannot prove equal to "
            "prefixes[default_idx] for distinct indices. It stays entirely INSIDE the "
            "axiom's domain (it passes no name as a selector at all), so this is a "
            "genuine value-level partial-domain rejection: right on both named legs, "
            "wrong exactly on the empty-identifier slice. If it VERIFIES => "
            "SPEC-TOO-WEAK on the fallback direction."
        ),
    },
    {
        "id": "weak-total-resolution",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_TOTAL_RESOLUTION),
        "refinement": (
            "treating resolution as TOTAL is what a real patch does if it builds the "
            "link from the current site's mount prefix instead of asking the resolver — "
            "or if it wraps reverse() so that a failure is papered over with a "
            "best-effort URL. It always emits a link. The gold patch does not: reverse() "
            "narrows to the selected instance FIRST and raises NoReverseMatch when the "
            "identifier is absent from THAT instance, and get_admin_url's "
            "`except NoReverseMatch: return str(remote_obj)` arm then renders the related "
            "object with NO link. That is not a corner case: sibling AdminSites each have "
            "their own _registry, and the gold test_patch itself has to ADD "
            "site2.register(...) calls before the custom-site link renders at all. Does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q5b (non-empty current identifier + the current deployment does "
            "NOT carry the route => len(Result())==0): the rival returns "
            "prefixes[current_idx] there, and P6b says every registered prefix is "
            "NON-EMPTY, so the verifier can see the two are incompatible. This is the "
            "REGRESSION CONTROL for the route axis: it is precisely the impl a "
            "route-blind postcondition admits. If it VERIFIES => the spec models "
            "resolution as total again and the over-claim is back."
        ),
    },
    {
        "id": "echo-unguarded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ECHO_UNGUARDED),
        "refinement": (
            "returning the current deployment's prefix UNCONDITIONALLY is what a real "
            "patch would do if it bypassed reverse's selector and lookup handling and "
            "pasted the current site's mount in directly. It diverges from the gold patch "
            "on BOTH axes at once: where the current site carries no route for the "
            "related model (the gold test_patch's own starting state) the real patched "
            "code renders NO link while this emits a URL; and where the current "
            "AdminSite's name is '' (legal and unvalidated, sites.py:36) the falsy "
            "`if current_app:` guard makes the real patched code resolve against the "
            "DEFAULT site while this emits the empty-named site's prefix. Not the gold "
            "patch's behaviour."
        ),
        "rationale": (
            "REJECTED by Q5b (and independently by Q6a): on a current deployment that "
            "carries no route the spec pins len(Result())==0 while the rival returns the "
            "NON-EMPTY prefixes[current_idx] (P6b), and on an empty current identifier "
            "the spec pins prefixes[default_idx] which is not provably equal to "
            "prefixes[current_idx]. This is the double control that neither repaired axis "
            "was bought by deleting an obligation: this rival is exactly what the older, "
            "unguarded equality admitted. If it VERIFIES => both over-claims are back."
        ),
    },
    {
        "id": "weak-exposes-forced",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_EXPOSES_FORCED),
        "refinement": (
            "the real-patch reading is a patch that makes the link resolve by asserting "
            "the current site exposes the target — e.g. calling reverse() against a "
            "route table it built itself for the current site, or retrying with the "
            "target force-registered. Whether a site exposes a related model's change "
            "view is fixed by that site's own _registry, and the gold patch takes it as "
            "given: it changes only WHICH instance reverse() resolves against. Does NOT "
            "resolve for a target the current site does not register."
        ),
        "rationale": (
            "REJECTED by Q5b: the doctored route vector makes the axiom pin the result "
            "to prefixes[current_idx] even when the real flag exposes[current_idx] is "
            "False, where Q5b demands len(Result())==0 (and P6b makes the prefix "
            "non-empty). Note the doctored vector still satisfies EVERY Requires of the "
            "axiom (update preserves length), so this is a VALUE-level rejection, not a "
            "domain one: it is WRONG-ARGUMENT use of a grounded axiom, the sharpest "
            "attack shape available against an axiomatized callee. If it VERIFIES => "
            "SPEC-TOO-WEAK on the route axis."
        ),
    },
    {
        "id": "weak-route-axis-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ROUTE_AXIS_SWAPPED),
        "refinement": (
            "the CROSS-AXIS near-miss, and the rival a reader who understood partiality "
            "but not the fallback is most likely to write: a real patch that decides "
            "whether to emit a link by testing the CURRENT site (e.g. "
            "`if remote_field.model in self.model_admin.admin_site._registry:`) and only "
            "then reverses. For an AdminSite named '' the real patched code resolves "
            "against the REGISTERED DEFAULT site, so it is the DEFAULT's route table that "
            "decides whether any link is produced. Measured against the real patched "
            "callee: current name '', the current site registers the target and the "
            "default does not => the real page renders NO link while this rival emits "
            "one. Not the gold patch's behaviour."
        ),
        "rationale": (
            "REJECTED by Q6b (empty current identifier + the DEFAULT deployment does not "
            "carry the route => len(Result())==0): the rival consults "
            "exposes[current_idx] on that leg, so when the current flag is True and the "
            "default's is False it returns the non-empty prefixes[default_idx] (P6b). "
            "Correct on every homogeneous registry and on every non-empty current "
            "identifier — a genuine partial-domain rival that only the heterogeneous "
            "empty-identifier rows expose. If it VERIFIES => SPEC-TOO-WEAK: the spec "
            "would not say WHICH deployment's route table governs the fallback."
        ),
    },
    {
        "id": "weak-always-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS_EMPTY),
        "refinement": (
            "never producing a link is the real patch that gives up on resolution — e.g. "
            "one that catches NoReverseMatch around the whole rendering and always falls "
            "through to `return str(remote_obj)`. Every read-only related object renders "
            "as bare text, so the F2P (which asserts an href carrying the custom site's "
            "prefix) fails outright. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q5a (non-empty current identifier + the current deployment "
            "carries the route => Result()==ToSeq(prefixes)[current_idx]): the rival "
            "returns the empty sequence, which P6b says no registered prefix equals. "
            "This is the DUAL degenerate control for the route axis: a spec that had "
            "'handled' partiality by merely PERMITTING an empty result — rather than "
            "pinning exactly when it occurs — would admit this. If it VERIFIES => the "
            "route axis swallowed the spec instead of sharpening it."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — the A-consumed @ContractOnly axiom resolve_prefix vs the REAL
# django.urls.reverse. meta.axioms has ONE consumed axiom. The real callee lives only
# in the instance image, so these probes run in Docker. Both EMBED the validated G-AX
# logic from axiom_check.py (2996 observations, 0 violations, every clause exercised)
# and EXECUTE the real reverse — they never scrape source (directive 4). The shared
# builder constructs real URLconfs holding the 3-tuple AdminSite.urls returns —
# (get_urls(), 'admin', self.name), django/contrib/admin/sites.py:303 — for several
# siblings sharing ONE app namespace but with distinct instance namespaces, distinct
# prefixes and DISTINCT ROUTE SETS, plus a NON-default colon-named sibling to validate
# the domain boundary. Per-sibling route sets are essential: with one shared inner
# URLconf every sibling would carry identical routes, the route axis would be
# unobservable, and the axiom's two no-url clauses would never be exercised at all.
# `exposes[k]` is OBSERVED by reversing against a ONE-deployment URLconf holding
# deployment k's route set (with a single instance there is nothing to select, so the
# observation does not depend on the selection mechanism under test).
# ---------------------------------------------------------------------------

# The shared real-callee harness (a faithful transcription of axiom_check.py's URLconf
# builder + reverse driver). Embedded into both probes; opens nothing on disk (no codec
# pitfall) and imports only django (present in the instance image). The probe body that
# follows decides which obligation to assert.
_AX_HARNESS = '''
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
import types

try:
    import django  # noqa: F401
    from django.urls import path
    from django.http import HttpResponse
except Exception as exc:  # pragma: no cover - environment guard
    print("G-AX SKIP: Django not importable in this environment: %r" % (exc,))
    sys.exit(0)


def _view(request, object_id):
    return HttpResponse("")


APP_NAME = "the_app"
ANCHOR_VIEW = "obj_change"        # carried by EVERY deployment: default discovery
EXTRA_VIEWS = ["extra_change", "third_change"]
ALL_VIEWS = [ANCHOR_VIEW] + EXTRA_VIEWS
COLON_NAME = "a:b"            # a registered NON-default sibling whose name embeds ':'

A = frozenset(ALL_VIEWS)
MID = frozenset([ANCHOR_VIEW, EXTRA_VIEWS[0]])
ANC = frozenset([ANCHOR_VIEW])

# Each entry is the 3-tuple AdminSite.urls returns, so an EMPTY instance name is
# registrable exactly as AdminSite(name='') is. Route sets DIFFER per sibling.
# The colon sibling is registered FIRST so it is NOT the default (app_dict[app][0] is
# the LAST-registered instance), which keeps the domain-boundary assert unambiguous.
SHAPES = [
    [(COLON_NAME, "/colon1/", A), ("first_site", "/first/", ANC),
     ("namespaced_site", "/ns/", MID), ("third_site", "/third/", A)],
    [(COLON_NAME, "/colon2/", A), ("rich_site", "/rich/", A),
     ("mid_site", "/mid/", MID), ("poor_site", "/poor/", ANC)],
    [("", "/emptyfirst/", A), ("plain_site", "/plain/", MID)],
    [("plain2_site", "/plain2/", A), ("", "/emptylast/", ANC)],
    [("solo", "/solo/", A)],
    [("solo2", "/solo2/", ANC)],
    [("rootmount", "/", A)],
]

_SERIAL = [0]


def patterns_for(view_names):
    return [path("%s/<int:object_id>/change/" % v, _view, name=v)
            for v in ALL_VIEWS if v in view_names]


def build(shape):
    _SERIAL[0] += 1
    modname = "axprobe_urls_%d" % _SERIAL[0]
    mod = types.ModuleType(modname)
    mod.urlpatterns = [
        path(mount.strip("/") + "/" if mount.strip("/") else "",
             (patterns_for(views), APP_NAME, name))
        for (name, mount, views) in shape]
    sys.modules[modname] = mod
    return modname


FIRST_MOD = build(SHAPES[0])

import django as _dj
from django.conf import settings as _settings
if not _settings.configured:
    _settings.configure(DEBUG=True, ROOT_URLCONF=FIRST_MOD,
                        INSTALLED_APPS=[], DATABASES={})
_dj.setup()

from django.urls import reverse, NoReverseMatch

_PROBE_MODS = {}


def probe_mod(views):
    """A ONE-deployment URLconf holding just this route set."""
    if views not in _PROBE_MODS:
        _PROBE_MODS[views] = build([("probe", "/probeonly/", views)])
    return _PROBE_MODS[views]


def observes(views, view_name, oid=7):
    """exposes[k]: does this route set carry the identifier? Observed with a SINGLE
    registered deployment, so no selection is involved in the observation."""
    try:
        reverse("%s:%s" % (APP_NAME, view_name), args=[oid],
                urlconf=probe_mod(views))
        return True
    except NoReverseMatch:
        return False


def rev(modname, view_name, oid=7, selector=None, has_selector=False):
    """The real callee. Returns None when it produces NO url (NoReverseMatch), which
    is what the axiom's empty-sequence result denotes."""
    kwargs = {}
    if has_selector:
        kwargs["current_app"] = selector
    try:
        return reverse("%s:%s" % (APP_NAME, view_name), args=[oid],
                       urlconf=modname, **kwargs)
    except NoReverseMatch:
        return None


def default_idx_of(modname, shape):
    """OBSERVE the registered default: the no-selector path with the ANCHOR route,
    which every deployment carries. Selection happens before the in-instance lookup,
    so the instance the no-selector path picks does not depend on the identifier."""
    prefixes = [p for (_, p, _) in shape]
    u = rev(modname, ANCHOR_VIEW)
    assert u is not None, "the anchor route did not resolve on the no-selector path"
    hits = [k for k in range(len(prefixes)) if u.startswith(prefixes[k])]
    # longest match: a root-mounted deployment's "/" prefixes everything
    return max(hits, key=lambda k: len(prefixes[k]))
'''


# axiom-soundness probe: assert every Ensures clause of resolve_prefix on the real
# reverse — both production clauses on BOTH the selector and the no-selector branch —
# plus the colon-separator and non-empty-prefix domain facts, mirroring axiom_check.py.
_AX_SOUND_PROBE = _AX_HARNESS + '''
import random
fails = []
checks = 0
legs = {"sel_route": 0, "sel_noroute": 0, "nosel_route": 0, "nosel_noroute": 0,
        "emptysel_route": 0, "emptysel_noroute": 0, "colon_boundary": 0,
        "rootprefix": 0}

for si, shape in enumerate(SHAPES):
    modname = build(shape)
    names = [n for (n, _, _) in shape]
    prefixes = [p for (_, p, _) in shape]
    viewsets = [v for (_, _, v) in shape]

    # DOMAIN premises, checked rather than assumed.
    assert len(set(names)) == len(names), "shape %d has duplicate instance names" % si
    for p in prefixes:
        assert len(p) > 0, ("shape %d registers an EMPTY prefix; the axiom's domain "
                            "says a registered prefix carries at least the "
                            "resolution root" % si)
        if p == "/":
            legs["rootprefix"] += 1
    checks += 1

    exposes = {}
    for v in ALL_VIEWS:
        exposes[v] = [observes(viewsets[k], v) for k in range(len(shape))]
        checks += len(shape)

    d_idx = default_idx_of(modname, shape)
    checks += 1

    for v in ALL_VIEWS:
        exp = exposes[v]

        # Ensures 1/2 (no selector) -> the registered default, in BOTH route states.
        u = rev(modname, v)
        if exp[d_idx]:
            if u is None or not u.startswith(prefixes[d_idx]):
                fails.append("UNSOUND no-selector (shape %d, view %r): reverse gave "
                             "%r, axiom requires the default prefix %r (exposes=%r)"
                             % (si, v, u, prefixes[d_idx], exp))
            else:
                legs["nosel_route"] += 1
        else:
            if u is not None:
                fails.append("UNSOUND no-selector (shape %d, view %r): the default "
                             "deployment %r carries no route yet reverse produced %r; "
                             "the axiom requires no url at all (exposes=%r)"
                             % (si, v, names[d_idx], u, exp))
            else:
                legs["nosel_noroute"] += 1
        checks += 1

        # The EMPTY selector is absorbed by the default clauses (`if current_app:`).
        u0 = rev(modname, v, selector="", has_selector=True)
        if u0 != u:
            fails.append("UNSOUND empty selector (shape %d, view %r): current_app='' "
                         "gave %r but no selector at all gave %r; the axiom's default "
                         "clauses absorb the empty selector" % (si, v, u0, u))
        else:
            legs["emptysel_route" if exp[d_idx] else "emptysel_noroute"] += 1
        checks += 1

        # Ensures 3/4 (a NON-EMPTY separator-free registered name), BOTH route states.
        for k in range(len(shape)):
            if len(names[k]) == 0 or ":" in names[k]:
                continue          # outside the axiom's selector domain
            uk = rev(modname, v, selector=names[k], has_selector=True)
            if exp[k]:
                if uk is None or not uk.startswith(prefixes[k]):
                    fails.append("UNSOUND has_selector (shape %d, view %r, selector="
                                 "%r): reverse gave %r, axiom requires that "
                                 "deployment's prefix %r (exposes=%r)"
                                 % (si, v, names[k], uk, prefixes[k], exp))
                else:
                    legs["sel_route"] += 1
            else:
                if uk is not None:
                    fails.append("UNSOUND has_selector (shape %d, view %r, selector="
                                 "%r): the deployment carries no route yet reverse "
                                 "produced %r; the axiom requires no url at all. The "
                                 "identifier IS carried by %r, so this would be the "
                                 "callee consulting a sibling, which it does not do"
                                 % (si, v, names[k], uk,
                                    [names[j] for j in range(len(shape)) if exp[j]]))
                else:
                    legs["sel_noroute"] += 1
            checks += 1

        # DOMAIN boundary: a ':'-bearing selector is SPLIT before matching, so it is
        # NOT matched whole -> it falls to the default, NOT its own prefix. An
        # unrestricted axiom would over-claim here; the model's colon-free Requires
        # excludes exactly this.
        if COLON_NAME in names:
            ci = names.index(COLON_NAME)
            uc = rev(modname, v, selector=COLON_NAME, has_selector=True)
            if uc is not None and uc.startswith(prefixes[ci]) and ci != d_idx:
                fails.append("DOMAIN premise broken (shape %d, view %r): "
                             "reverse(current_app=%r) gave %r which DOES carry the "
                             "colon instance prefix %r as a whole-name match"
                             % (si, v, COLON_NAME, uc, prefixes[ci]))
            elif uc != u:
                fails.append("DOMAIN (shape %d, view %r): reverse(current_app=%r) gave "
                             "%r; expected the colon name to be split and the call to "
                             "behave as the default fallback %r"
                             % (si, v, COLON_NAME, uc, u))
            else:
                legs["colon_boundary"] += 1
            checks += 1

# colon-separator fuzz: many ':'-bearing selectors, none may select the colon
# sibling's prefix via a whole-name match (the over-claim channel).
fuzz_mod = build(SHAPES[0])
fnames = [n for (n, _, _) in SHAPES[0]]
fprefixes = [p for (_, p, _) in SHAPES[0]]
fviews = [v for (_, _, v) in SHAPES[0]]
colon_prefix = fprefixes[fnames.index(COLON_NAME)]
rngc = random.Random(0xC010)
colon_checks = 0
for _ in range(2000):
    L = rngc.randint(1, 8)
    sel = "".join(rngc.choice("abc:xyz:") for _ in range(L))
    if ":" not in sel:
        continue
    u = rev(fuzz_mod, ANCHOR_VIEW, oid=3, selector=sel, has_selector=True)
    if u is not None and u.startswith(colon_prefix):
        fails.append("colon-fuzz domain violation: current_app=%r selected %r"
                     % (sel, colon_prefix))
    colon_checks += 1
    checks += 1
if colon_checks == 0:
    fails.append("colon-fuzz generated no separator-bearing selectors")

# fuzz: random (instance, identifier, argument) selection, both route states.
rng = random.Random(14855)
for _ in range(2000):
    k = rng.randrange(len(fnames))
    v = rng.choice(ALL_VIEWS)
    oid = rng.randint(0, 10 ** 6)
    if ":" in fnames[k] or len(fnames[k]) == 0:
        continue
    u = rev(fuzz_mod, v, oid=oid, selector=fnames[k], has_selector=True)
    if observes(fviews[k], v, oid=oid):
        if u is None or not u.startswith(fprefixes[k]):
            fails.append("UNSOUND fuzz (selector=%r,view=%r,id=%d): reverse gave %r, "
                         "axiom requires %r" % (fnames[k], v, oid, u, fprefixes[k]))
    else:
        if u is not None:
            fails.append("UNSOUND fuzz (selector=%r,view=%r,id=%d): the deployment "
                         "carries no route yet reverse gave %r; the axiom requires no "
                         "url" % (fnames[k], v, oid, u))
    checks += 1

# every clause must actually have been exercised
for leg in sorted(legs):
    if legs[leg] == 0:
        fails.append("COVERAGE: the %r leg of the axiom was never exercised, so this "
                     "probe cannot witness its soundness" % leg)

if fails:
    print("AXIOM-SOUNDNESS FAIL: %d disagreement(s) between resolve_prefix axiom and "
          "the real django.urls.reverse" % len(fails))
    for f in fails[:20]:
        print("  " + f)
    sys.exit(1)
print("AXIOM-SOUNDNESS OK: resolve_prefix axiom sound against real django.urls.reverse "
      "on %d observations (per-instance separator-free selection with and without a "
      "route for the identifier + default fallback in both route states + the empty "
      "selector absorbed by the default clauses + colon-separator domain boundary + "
      "root-mount prefix edge + fuzz); leg coverage %r" % (checks, legs))
sys.exit(0)
'''


# axiom-containment probe: the model reaches resolve_prefix ONLY with
# selector = names[current_idx] (which the consumer precondition P7 forces to be
# SEPARATOR-FREE — every code point != 58 / ':'), has_selector=True, and the route
# vector UNDOCTORED. So the caller-reachable argument space is: a separator-free name
# (possibly EMPTY, which the axiom's default clauses cover explicitly), together with
# BOTH route states of the selected deployment AND both of the default's. The probe
# confirms containment by executing the real reverse over exactly that space: every
# reachable combination must be inside the axiom's domain (Requires) and covered by one
# of its four Ensures clauses. A reachable combination the axiom did NOT cover would be
# AXIOM-TOO-WEAK-FOR-CALLER — in particular an axiom stated only for route-carrying
# deployments would leave the two no-url legs uncovered, and the consumer's Q5b/Q6b
# could not be discharged.
_AX_COVER_PROBE = _AX_HARNESS + '''
import random
fails = []
checks = 0
covered = {"sel_route": 0, "sel_noroute": 0, "nosel_route": 0, "nosel_noroute": 0}

# The caller (related_link_target) reaches resolve_prefix with:
#   selector     = names[current_idx]  -- P7 forces it separator-free (no ':' code pt)
#   has_selector = True
#   exposes      = the registry's own route vector, UNDOCTORED
# Containment claim: every such call is INSIDE the axiom's domain, and exactly one of
# the four Ensures clauses pins its result. The two no-url clauses are as reachable as
# the two prefix clauses: the current deployment may simply not carry the identifier.
for si, shape in enumerate(SHAPES):
    modname = build(shape)
    names = [n for (n, _, _) in shape]
    prefixes = [p for (_, p, _) in shape]
    viewsets = [v for (_, _, v) in shape]

    # the domain the caller's own precondition guarantees
    assert len(set(names)) == len(names), "shape %d: names not unique (P6)" % si
    for p in prefixes:
        assert len(p) > 0, "shape %d: empty registered prefix (P6b)" % si
    d_idx = default_idx_of(modname, shape)

    for v in ALL_VIEWS:
        exp = [observes(viewsets[k], v) for k in range(len(shape))]
        for k in range(len(shape)):
            if ":" in names[k]:
                continue     # P7 forbids the caller from reaching this selector
            reachable_selector = names[k]
            assert ":" not in reachable_selector, "unreachable selector sampled"
            u = rev(modname, v, selector=reachable_selector, has_selector=True)
            if len(reachable_selector) == 0:
                # an EMPTY reachable selector: the axiom's default clauses cover it
                if exp[d_idx]:
                    ok = (u is not None and u.startswith(prefixes[d_idx]))
                    covered["nosel_route"] += 1
                else:
                    ok = (u is None)
                    covered["nosel_noroute"] += 1
                clause = "no-selector/empty-selector"
            else:
                if exp[k]:
                    ok = (u is not None and u.startswith(prefixes[k]))
                    covered["sel_route"] += 1
                else:
                    ok = (u is None)
                    covered["sel_noroute"] += 1
                clause = "has_selector"
            if not ok:
                fails.append("CONTAINMENT FAIL (shape %d, view %r, selector=%r): the "
                             "reachable call is not covered by the %s clauses -- real "
                             "reverse gave %r with exposes=%r, default=%r"
                             % (si, v, reachable_selector, clause, u, exp,
                                names[d_idx]))
            checks += 1

# Randomized separator-free selectors (the reachable shape): each must either resolve
# or produce NO url -- never anything the axiom cannot describe.
rng = random.Random(0x14855C)
fuzz_mod = build(SHAPES[0])
fnames = [n for (n, _, _) in SHAPES[0]]
fprefixes = [p for (_, p, _) in SHAPES[0]]
fviews = [v for (_, _, v) in SHAPES[0]]
d_idx = default_idx_of(fuzz_mod, SHAPES[0])
reg = {}
for i, n in enumerate(fnames):
    reg[n] = i
for _ in range(3000):
    L = rng.randint(1, 12)
    sel = "".join(rng.choice("abcdefghijklmnop_0123456789") for _ in range(L))
    assert ":" not in sel  # by construction: the reachable (separator-free) domain
    v = rng.choice(ALL_VIEWS)
    try:
        u = rev(fuzz_mod, v, oid=2, selector=sel, has_selector=True)
    except Exception as e:
        fails.append("CONTAINMENT FAIL: separator-free reachable selector %r raised %r "
                     "-- an outcome the axiom (a total function to a prefix or the "
                     "empty sequence) cannot describe" % (sel, e))
        continue
    if sel in reg:
        k = reg[sel]
        if observes(fviews[k], v):
            if u is None or not u.startswith(fprefixes[k]):
                fails.append("CONTAINMENT FAIL: registered separator-free %r gave %r, "
                             "axiom requires %r" % (sel, u, fprefixes[k]))
        else:
            if u is not None:
                fails.append("CONTAINMENT FAIL: registered separator-free %r carries no "
                             "route for %r yet gave %r" % (sel, v, u))
    checks += 1

# Boundary confirmation that the EXCLUDED slice is exactly the un-reachable one: the
# ONLY selector the axiom's domain leaves out is the ':'-bearing name, which P7 forbids
# the caller from reaching. (If a ':'-bearing selector were reachable AND uncovered we
# would have AXIOM-TOO-WEAK-FOR-CALLER; P7 makes it unreachable, so covering only the
# separator-free names is sound containment, not a defect.)
ci = fnames.index(COLON_NAME)
u_colon = rev(fuzz_mod, ANCHOR_VIEW, oid=1, selector=COLON_NAME, has_selector=True)
if u_colon is not None and u_colon.startswith(fprefixes[ci]) and ci != d_idx:
    fails.append("CONTAINMENT premise broken: ':'-bearing selector %r matched its own "
                 "prefix (would make it reachable-and-in-domain)" % (COLON_NAME,))
checks += 1

for leg in sorted(covered):
    if covered[leg] == 0:
        fails.append("COVERAGE: the caller-reachable %r combination was never sampled, "
                     "so containment for that Ensures clause is unwitnessed" % leg)

if fails:
    print("AXIOM-CONTAINMENT FAIL: %d caller-reachable call(s) outside the axiom domain "
          "or not covered by its Ensures" % len(fails))
    for f in fails[:20]:
        print("  " + f)
    sys.exit(1)
print("AXIOM-CONTAINMENT OK: every call the caller can reach (selector=names"
      "[current_idx], separator-free by P7, has_selector=True, undoctored route vector) "
      "lies inside the axiom's domain and is pinned by one of its four Ensures clauses "
      "on the real reverse -- including BOTH no-url legs; the only excluded slice "
      "(':'-bearing names) is exactly the unreachable one (%d checks, reachable-clause "
      "coverage %r)" % (checks, covered))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-resolve_prefix",
        "axiom": "resolve_prefix",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "resolve_prefix is an A-consumed @ContractOnly axiom of "
            "django.urls.reverse's namespace->instance selection AND the in-instance "
            "identifier lookup that follows it. AXIOM-SOUNDNESS: the real reverse must "
            "satisfy every Ensures clause on every input in the axiom's Requires domain. "
            "The probe builds real URLconfs holding the 3-tuple AdminSite.urls returns "
            "(sites.py:303) for siblings sharing ONE app namespace with distinct instance "
            "namespaces, distinct prefixes and DISTINCT ROUTE SETS — incl. a NON-default "
            "colon-named sibling, an empty-named sibling and a root-mounted one — and "
            "drives the live reverse: each separator-free name selects its own prefix "
            "when it carries the route and produces NO url when it does not; no "
            "current_app (and equally an empty one) does the same for the registered "
            "default; the colon name is split and falls to default (domain boundary — the "
            "axiom must NOT over-claim there); + colon fuzz + 2000 selection fuzz. Leg "
            "coverage is asserted, so a probe that stopped exercising the no-url clauses "
            "FAILS rather than passing vacuously. Mirrors axiom_check.py / G-AX (2996 "
            "obs, 0 violations). Any disagreement => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-cover-resolve_prefix",
        "axiom": "resolve_prefix",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "AXIOM-CONTAINMENT: related_link_target reaches resolve_prefix ONLY with "
            "selector=names[current_idx] (P7 forces it separator-free, every code point "
            "!= 58/':'), has_selector=True, and the registry's route vector UNDOCTORED. "
            "The reachable argument space therefore spans a separator-free name — "
            "possibly EMPTY, which the axiom's default clauses cover explicitly — "
            "together with BOTH route states of the selected deployment and both of the "
            "default's. The probe walks exactly that space on the real reverse and "
            "asserts each reachable call is in-domain and pinned by one of the four "
            "Ensures clauses, with per-clause coverage asserted so the two no-url legs "
            "cannot go unwitnessed: an axiom stated only for route-carrying deployments "
            "would leave them uncovered and the consumer's Q5b/Q6b could not be "
            "discharged (AXIOM-TOO-WEAK-FOR-CALLER). It also confirms the ONLY excluded "
            "slice (':'-bearing names) is exactly the one P7 makes unreachable, so "
            "covering only the separator-free names is sound containment, not a defect."
        ),
    },
]
