# properties.py — PBT falsification battery for django__django-15569.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a FULL model.py source that shares the frozen spec byte-for-byte
# (only the # impl-start/# impl-end region is edited, guaranteeing same_spec) and
# is checked by the Nagini verifier; AXIOM_TESTS are real-callee probes run in
# Docker (none here — this bundle has no @ContractOnly axioms).
#
# Defended surface (read from model.py + refinement.md + mapping.md):
#   remove_registration(store: Dict[int,int], view: Dict[int,int],
#                       inherited: Dict[int,int], name: int)
#   removes the LOCAL registration of `name`. `store` (the per-class class_lookups
#   backing dict) and `view` (the lru_cache-memoised get_lookups() view) are held
#   at FULL permission because they are genuinely mutated in place; `inherited`
#   (what the enclosing registration layer provides per name: merge_dicts over the
#   class_lookups of the classes cls.get_lookups() actually merges, MINUS cls
#   itself -- for most classes inspect.getmro(cls)[1:], but NOT for ForeignObject
#   and its subclasses, whose get_lookups override (related.py:858-864) truncates
#   the merge range at ForeignObject so an ancestor above that cut is in the MRO
#   yet is never consulted by a read; mapping.md §1/§2) is READ-ONLY, so it is
#   held at Acc(...,1/2). The precondition's READ-THROUGH LAW is what ties the
#   parameter to that meaning: on the incoming state a locally-registered name
#   resolves to the local registration and a name the local store does not
#   register resolves to exactly what `inherited` provides. It leaves
#   `inherited[name]` itself unconstrained for the AFFECTED name (its fallback
#   leg is guarded by store[k] == unregistered(), which the precondition denies
#   at k == name), which is what keeps clause (2) below discriminating.
#   The postcondition's four load-bearing clauses:
#     (1) store[name] == unregistered()                  -- the store deletion
#                                                            (present pre-patch too)
#     (2) view[name]  == inherited[name]                 -- THE discriminating
#                                                            clause: the derived
#                                                            view must be brought
#                                                            in line with the
#                                                            remaining registration
#                                                            levels; the store-only
#                                                            prepatch FAILS this.
#                                                            Where the enclosing
#                                                            layer registers nothing
#                                                            (inherited[name] ==
#                                                            unregistered()) this
#                                                            says the name stops
#                                                            resolving outright.
#     (3) store[other_name()] == Old(store[other_name()])-- per-key store frame
#     (4) view[other_name()]  == Old(view[other_name()]) -- per-key view frame
#   plus a whole-structure quantified frame: four Forall postconditions pin
#   every name k != name (membership and, when present, bound state unchanged
#   in BOTH structures), so an impl that additionally rebinds ANY unrelated
#   key in either structure is rejected.
#
# There is no @Pure answer-key oracle to echo: unregistered()==0 and
# other_name()==-1 are grounded constants of nothing, and the postconditions are
# structural per-key facts on the input carriers (not pinned to an opaque marker).
# The echo shape that DOES exist is the incoming view itself: the read-through law
# relates `view` to `inherited` on every name the local store does not register, so
# an impl can try to answer the removed name from the incoming carriers (or from
# arithmetic on `name`) instead of consulting the enclosing layer. Those rivals are
# exercised below (weak-view-echo-incoming, weak-view-echo-other-key) and must
# reject: the law's fallback leg is guarded by store[k] == unregistered(), which the
# precondition denies at k == name, so the law says NOTHING about inherited[name] at
# the affected name -- while its other leg pins the INCOMING view[name] to the local
# registration, i.e. provably != unregistered(). Echoing the carriers therefore
# cannot discharge clause (2). The read-through law is also what the faithfulness
# repair added, so the rival aimed straight at it (correct exactly where clause (2)'s
# right-hand side is unregistered(), wrong where the enclosing layer resurfaces an
# ancestor) is exercised as weak-view-branch-halfright. We also supply an honest
# cheapest-impl positive control (assessment §oracle).
#
# `inherited` IS an Acc(...,1/2) read-only input, so the classic "overwrite a
# half-permission input" probe applies and is exercised below (weak-write-
# inherited): it must reject for insufficient permission. The frame over the two
# written carriers is defended by the per-key Old() clauses (3)/(4) plus the
# quantified frame; we attack THAT frame directly with rivals that disturb an
# unrelated name (they must reject for violating the Old() frame clause, not for
# permission).
from pathlib import Path

INSTANCE = "django__django-15569"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact impl region of the frozen model.py (the gold deep model: store
# deletion + view invalidation). Region-surgery target: we only ever replace the
# text BETWEEN the markers, so spec_view (markers-inclusive elision) is unchanged
# and same_spec is guaranteed.
_GOLD_IMPL = (
    "    # impl-start\n"
    "    store[name] = unregistered()\n"
    "    view[name] = inherited[name]\n"
    "    reader_view[name] = reader_rest[name]\n"
    "    # impl-end\n"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(body_lines):
    """Build a full model.py variant whose impl region is exactly body_lines
    (a list of source lines, indentation included), leaving the frozen spec
    untouched. Editing ONLY between the markers => same_spec True."""
    region = "    # impl-start\n" + "".join(l + "\n" for l in body_lines) + "    # impl-end\n"
    return _swap(_BASE, _GOLD_IMPL, region)


# Sanity: the frozen impl region we surgically replace is present exactly once.
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted; update _GOLD_IMPL"


SPEC_TESTS = [
    # ------------------------------------------------------------------ #
    # POSITIVE CONTROLS (soundness): structurally-different CORRECT impls #
    # that MUST verify. If a faithful correct impl cannot => SPEC-TOO-STRONG.
    # The impl is assignment-only, so the gold proof has no loop invariant /
    # framing lemma to drop (pilot bug #2 N/A); a branch-reorder / local-temp
    # reshape is safe.
    # ------------------------------------------------------------------ #
    {
        "id": "pos-reorder-writes",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl([
            # bring the derived view in line first, then delete from the store:
            # the two writes commute (distinct carriers), so a correct impl in
            # the other order must still verify.
            "    reader_view[name] = reader_rest[name]",
            "    view[name] = inherited[name]",
            "    store[name] = unregistered()",
        ]),
        "rationale": (
            "a correct impl that writes view then store (reversed order) satisfies "
            "all four postcondition clauses identically; if it fails to verify the "
            "spec is too strong about write order (SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "pos-local-temp",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl([
            # read the remaining registration level into a typed local first,
            # then assign from it: a different executable shape, same result.
            "    u = inherited[name]  # type: int",
            "    r = reader_rest[name]  # type: int",
            "    store[name] = unregistered()",
            "    view[name] = u",
            "    reader_view[name] = r",
        ]),
        "rationale": (
            "a correct impl that reads inherited[name] once into a typed local and "
            "assigns the view from it is observably identical to the gold; it "
            "must verify (else SPEC-TOO-STRONG against a trivial local reshape)."
        ),
    },

    # ------------------------------------------------------------------ #
    # ADMISSIBILITY: the precondition must admit a normal F2P-shaped input.#
    # A self-call caller builds two dicts that satisfy every Requires and    #
    # invokes remove_registration. If the Requires cannot be established for #
    # a legitimate input => PRECOND-TOO-STRONG.                              #
    # ------------------------------------------------------------------ #
    {
        "id": "admiss-incoming-precond-noncontradictory",
        "kind": "admissibility",
        "expect": "verify",
        # Region-surgery admissibility: we keep the gold writes and ADD, inside
        # the impl region, assertions of facts that follow ONLY from the incoming
        # precondition for a concrete F2P-shaped name relationship -- BEFORE doing
        # the work. If the precondition were contradictory/over-constrained in a
        # way that excluded a legitimate input, the modeled function would still
        # be reachable (callers must establish Requires); the genuine cross-check
        # that the precondition admits a normal input is the dedicated caller
        # below (admiss-caller-in-region). Here we additionally confirm the
        # incoming state is the F2P shape: name and other_name() both registered,
        # both resolving, and distinct -- read straight off the precondition.
        "module": _impl([
            "    # the precondition gives us a normal two-name F2P input: confirm",
            "    # we can read the keys and that they are registered/resolving",
            "    # (these follow directly from Requires; if the precondition were",
            "    # unsatisfiable this would be vacuous, so the load-bearing",
            "    # admissibility cross-check is the dedicated caller case).",
            "    Assert(name in store and name in view and name in inherited)",
            "    Assert(other_name() in store and other_name() in view)",
            "    Assert(name != other_name())",
            "    Assert(store[name] != unregistered())",
            "    Assert(view[name] != unregistered())",
            "    Assert(name in reader_view and name in reader_rest)",
            "    Assert(other_name() in reader_view)",
            "    store[name] = unregistered()",
            "    view[name] = inherited[name]",
            "    reader_view[name] = reader_rest[name]",
        ]),
        "rationale": (
            "the incoming precondition (name+other registered and resolving, "
            "distinct) is read off and asserted before the work; with the gold "
            "writes this still satisfies the postcondition. Supporting admissibility "
            "evidence; the load-bearing precond-satisfiability witness is "
            "admiss-caller-in-region."
        ),
    },
    {
        "id": "admiss-caller-in-region",
        "kind": "admissibility",
        "expect": "verify",
        # The load-bearing admissibility witness, kept same_spec by building a
        # concrete F2P-shaped input INSIDE the impl region (elided from
        # spec_view) and asserting it satisfies EVERY Requires conjunct -- i.e.
        # exhibiting a concrete value at which the precondition holds.
        #
        # NOTE: an earlier revision tried to express this as a NESTED function
        # `def _caller(): ... remove_registration(s, v, 5)` so the call site
        # would discharge the precondition. That is infeasible in this fragment:
        # Nagini categorically bans nested function declarations
        # (Invalid program: nested.function.declaration), so the module failed
        # TRANSLATION (never reaching verification); the runner reported the
        # translation failure as "rejected" and mis-binned it PRECOND-TOO-STRONG.
        # A top-level caller cannot be used either, because spec_view only elides
        # the impl region -- a new top-level function would break same_spec.
        # The faithful, expressible admissibility check is therefore to BUILD the
        # concrete input and ASSERT every Requires conjunct on it: if the
        # precondition were contradictory/over-constrained these asserts could
        # not all hold for any concrete value, so verifying them witnesses that
        # the precondition admits a normal two-name input (else PRECOND-TOO-STRONG).
        "module": _impl([
            "    # gold work on the actual argument:",
            "    store[name] = unregistered()",
            "    view[name] = inherited[name]",
            "    reader_view[name] = reader_rest[name]",
            "    # admissibility witness (inside the impl region => elided from",
            "    # spec_view, so same_spec is preserved): construct a concrete",
            "    # F2P-shaped input from scratch and assert it satisfies every",
            "    # Requires conjunct. A nested caller cannot be used (Nagini bans",
            "    # nested def), and a top-level caller would break same_spec; this",
            "    # concrete-witness form proves the precondition is jointly",
            "    # satisfiable (else PRECOND-TOO-STRONG).",
            "    s = {}  # type: Dict[int, int]",
            "    v = {}  # type: Dict[int, int]",
            "    w = {}  # type: Dict[int, int]",
            "    s[5] = 7",
            "    v[5] = 7",
            "    w[5] = unregistered()",
            "    s[other_name()] = 9",
            "    v[other_name()] = 9",
            "    rv = {}  # type: Dict[int, int]",
            "    rr = {}  # type: Dict[int, int]",
            "    rv[5] = 7",
            "    rr[5] = unregistered()",
            "    rv[other_name()] = 9",
            "    # every Requires conjunct of remove_registration, established on",
            "    # the concrete witness (name=5, store=view={5:7, -1:9}, and the",
            "    # enclosing layer registering nothing under 5):",
            "    Assert(5 in s and 5 in v and 5 in w)",
            "    Assert(other_name() in s and other_name() in v)",
            "    Assert(other_name() != 5)",
            "    Assert(s[5] != unregistered())",
            "    Assert(v[5] != unregistered())",
            "    # the arbitrary-reader carriers of the same concrete witness: a",
            "    # reader that reaches this component reports the local",
            "    # registration for name 5 and its own remaining levels provide",
            "    # nothing under it, which satisfies the per-reader read-through",
            "    # law's first disjunct.",
            "    Assert(5 in rv and 5 in rr)",
            "    Assert(other_name() in rv)",
            "    Assert(rv[5] == s[5] or rv[5] == rr[5])",
        ]),
        "rationale": (
            "a concrete F2P-shaped input (name 5->7, other_name() -1->9, both "
            "registered and resolving, distinct, and an enclosing layer that "
            "registers nothing under 5 -- the shape both F2P tests have) is built "
            "from scratch and EVERY Requires conjunct of remove_registration is "
            "asserted on it and verifies, witnessing that the precondition admits a "
            "normal two-name input (else PRECOND-TOO-STRONG). Expressed as a "
            "concrete witness rather than a call because Nagini bans nested "
            "functions and a top-level caller would break same_spec; the witness "
            "lives inside the impl region so spec_view elides it and same_spec "
            "holds, while the gold writes on the real argument keep the modeled "
            "function correct."
        ),
    },

    # ------------------------------------------------------------------ #
    # UNIQUENESS / completeness (postcondition too weak): adversarial rivals #
    # that share the spec exactly and change only the impl. If any VERIFIES, #
    # the spec admits a wrong impl => SPEC-TOO-WEAK.                          #
    # ------------------------------------------------------------------ #

    # (A) The canonical discriminating rival: the BASE_COMMIT / pre-patch
    #     view-blind removal -- update only the backing store, leave the
    #     derived view stale. This is EXACTLY the bug the gold patch fixes
    #     (the missing cls._clear_cached_lookups()). Must reject on clause (2).
    {
        "id": "weak-store-only-viewblind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    store[name] = unregistered()",
        ]),
        "refinement": (
            "this is the base_commit _unregister_lookup verbatim (del "
            "class_lookups[name] with NO cls._clear_cached_lookups()). Its faithful "
            "real patch is the unpatched tree, which FAILS both F2P tests: "
            "test_lookups_caching asserts assertNotIn('exactly', field.get_lookups()) "
            "after unregistration (the stale lru_cache still reports it), and "
            "test_get_transforms drops its now-redundant manual _clear_cached_lookups() "
            "and relies on _unregister_lookup busting the cache. So a verify here would "
            "be a true verify-but-not-resolve break."
        ),
        "rationale": (
            "rejects on postcondition clause (2) view[name] == inherited[name]: the "
            "derived view still reports the removed LOCAL registration "
            "(model_prepatch.py, G-DIFF). This is the load-bearing discriminator of "
            "the whole bundle."
        ),
    },

    # (B) The mirror omission: invalidate the view but forget to delete from the
    #     backing store. Fails clause (1). A faithful real patch would be a
    #     _unregister_lookup that calls _clear_cached_lookups() but skips
    #     `del cls.class_lookups[lookup_name]`.
    {
        "id": "weak-view-only-no-delete",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    view[name] = inherited[name]",
        ]),
        "refinement": (
            "faithful real patch: a removal that busts the memoised view but never "
            "does `del cls.class_lookups[lookup_name]`. class_lookups still registers "
            "the name, so on the next read get_lookups() recomputes from the store and "
            "STILL resolves the name -- test_lookups_caching's assertNotIn('exactly', "
            "field.get_lookups()) fails. Does NOT resolve."
        ),
        "rationale": (
            "rejects on postcondition clause (1) store[name] == unregistered(): the "
            "backing store still registers the removed name."
        ),
    },

    # (C) A NO-OP rival (the empty impl): does nothing. Trivially wrong; it pins
    #     that the spec is not vacuously satisfiable. Fails clauses (1) and (2).
    {
        "id": "weak-noop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    pass",
        ]),
        "refinement": (
            "faithful real patch: an _unregister_lookup that returns without "
            "touching class_lookups or the cache. The name stays registered and "
            "resolving -- both F2P tests fail outright. Does NOT resolve."
        ),
        "rationale": (
            "rejects on clauses (1) and (2): the spec is not vacuously satisfiable; a "
            "no-op cannot meet store[name]==unregistered() nor view[name]==inherited[name] "
            "(the incoming view still holds the local registration, which is "
            "!= unregistered() by the precondition)."
        ),
    },

    # (D) FRAME ATTACK on the store: do the correct two writes BUT also clobber
    #     an unrelated name in the backing store. This is the value-level frame
    #     mutation analog (there is no Acc(...,1/2) input here, so the attack is
    #     against the per-key Old() frame clause, not the permission system).
    #     Must reject on clause (3).
    {
        "id": "weak-frame-store-other-clobber",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    store[name] = unregistered()",
            "    view[name] = inherited[name]",
            # collateral damage: unregister an UNRELATED name from the store too.
            "    store[other_name()] = unregistered()",
        ]),
        "refinement": (
            "faithful real patch: a _unregister_lookup that, besides removing "
            "lookup_name, also does `del cls.class_lookups[some_other_name]`. That "
            "deletes a still-registered lookup, so any read of that other name no "
            "longer resolves -- it changes behaviour for an unrelated lookup the "
            "operation must leave intact. The P2P suite (which registers/uses many "
            "lookups) would break; does NOT resolve."
        ),
        "rationale": (
            "rejects on frame clause (3) store[other_name()] == Old(store[other_name()]): "
            "an unrelated name's registration was disturbed."
        ),
    },

    # (E) FRAME ATTACK on the view: correct two writes BUT also invalidate an
    #     unrelated name in the derived view (e.g. an over-broad cache wipe that
    #     drops a different name's resolution). Must reject on clause (4).
    {
        "id": "weak-frame-view-other-clobber",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    store[name] = unregistered()",
            "    view[name] = inherited[name]",
            # collateral damage: drop an UNRELATED name's resolution from the view.
            "    view[other_name()] = unregistered()",
        ]),
        "refinement": (
            "faithful real patch: a removal whose cache handling drops a DIFFERENT "
            "name's resolution (e.g. evicting one entry but recomputing it wrong, so "
            "an unrelated lookup stops resolving on the next read). The frame "
            "(other names resolve exactly as before) is violated; reads of that "
            "other name regress -- does NOT resolve (the P2P lookup suite breaks)."
        ),
        "rationale": (
            "rejects on frame clause (4) view[other_name()] == Old(view[other_name()]): "
            "an unrelated name's resolution was disturbed in the derived view."
        ),
    },

    # (F) PARTIAL / WRONG-VALUE rival: delete from the store but set the view's
    #     removed-name entry to a NON-unregistered value (here other_name(),
    #     which is -1 != 0 == unregistered()), i.e. the read still resolves the
    #     removed name to some bogus item. Fails clause (2) with a value that is
    #     provably != unregistered() (a sharper miss than leaving it stale).
    {
        "id": "weak-view-bogus-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    store[name] = unregistered()",
            # other_name() == -1, which is provably != unregistered() (== 0):
            "    view[name] = other_name()",
        ]),
        "refinement": (
            "faithful real patch: a removal that, instead of clearing the cache, "
            "rebinds the removed name's memoised entry to some other lookup. A read "
            "of the removed name still resolves (to the wrong lookup) -- "
            "test_lookups_caching's assertNotIn('exactly', field.get_lookups()) fails. "
            "Does NOT resolve."
        ),
        "rationale": (
            "rejects on clause (2): view[name] == other_name() == -1, which the spec "
            "does not permit unless the enclosing layer happens to provide exactly "
            "that; inherited[name] is unconstrained at the AFFECTED name (the "
            "read-through law's fallback leg is guarded by store[k] == unregistered(), "
            "which the precondition denies at k == name), so the equality with a "
            "hard-coded constant cannot be proved."
        ),
    },

    # (G) OVER-EAGER rival: do the store deletion but force the view to report
    #     "does not resolve" UNCONDITIONALLY, ignoring what the enclosing
    #     registration layer provides for the name. Correct only in the special
    #     case where the enclosing layer registers nothing under that name; on
    #     the inputs where it does register something, this loses the answer a
    #     read must still get. Must reject on clause (2).
    {
        "id": "weak-view-unconditional-unresolve",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    store[name] = unregistered()",
            # ignores inherited[name]: claims the name resolves nowhere at all.
            "    view[name] = unregistered()",
        ]),
        "refinement": (
            "faithful real patch: a removal that, after deleting the local "
            "registration, forces a read of that name to report nothing -- e.g. "
            "`del cls.class_lookups[n]; cls.class_lookups[n] = None; "
            "cls._clear_cached_lookups()`, which under the mapping.md §2 bridge "
            "(key absent <-> unregistered()) satisfies BOTH of the old spec's "
            "clauses. Executed in-container against the gold-patched tree: after it, "
            "`'exactly' in field.get_lookups()` is True (the merged view carries the "
            "None binding), so test_lookups_caching's "
            "assertNotIn('exactly', field.get_lookups()) FAILS. It also masks a name "
            "an enclosing class legitimately registers, which the real removal "
            "resurfaces -- measured on the gold-patched tree: registering 'exactly' on "
            "models.CharField AND on models.Field, then removing CharField's, leaves "
            "the real recomputed CharField.get_lookups()['exactly'] == Field's lookup, "
            "not absent. (The value unregistered() is the RIGHT answer on the "
            "ForeignObject family, whose get_lookups truncates the merge range so "
            "nothing in the read-fallback range provides the name -- there "
            "inherited[name] == unregistered() and this impl coincides with the gold "
            "one. Hard-coding the constant is what makes it wrong everywhere else.) "
            "Does NOT resolve."
        ),
        "rationale": (
            "rejects on clause (2) view[name] == inherited[name]: inherited[name] is "
            "unconstrained at the AFFECTED name (the read-through law's fallback leg is "
            "guarded by store[k] == unregistered(), denied at k == name), so an impl "
            "that hard-codes unregistered() cannot discharge the equality. This is the "
            "clause that pins the view to the REMAINING registration levels rather than "
            "to 'nothing at all'."
        ),
    },

    # (H) PERMISSION rival: mutate the READ-ONLY enclosing layer. `inherited` is
    #     held at Acc(dict_pred(inherited), 1/2), so a write to it must be
    #     rejected for insufficient permission -- the operation may consult the
    #     enclosing registration layer but never alter it.
    {
        "id": "weak-write-inherited",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    store[name] = unregistered()",
            "    view[name] = inherited[name]",
            # writing a half-permission input: not allowed.
            "    inherited[name] = unregistered()",
        ]),
        "refinement": (
            "faithful real patch: a removal that also deletes the name from an "
            "ENCLOSING class's class_lookups (`del Ancestor.class_lookups[n]`), "
            "de-registering a lookup that class still owns. Every reader inheriting "
            "from it loses that lookup; the P2P lookup suite breaks. Does NOT resolve."
        ),
        "rationale": (
            "rejects for insufficient permission: `inherited` is passed at "
            "Acc(dict_pred(inherited), 1/2) (read-only), so the operation cannot "
            "write it. Pins that the enclosing registration layer is consulted, "
            "never modified."
        ),
    },

    # (I) UNGROUNDED-ORACLE ECHO, incoming-view flavour: do the store deletion and
    #     then answer the removed name by re-asserting the value the argument
    #     carrier already holds, instead of consulting the enclosing layer. This
    #     is the echo shape the read-through-law precondition makes available, so
    #     it is the rival that tests whether that precondition turned clause (2)
    #     into a tautology. Must reject on clause (2).
    {
        "id": "weak-view-echo-incoming",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    store[name] = unregistered()",
            # echo: derive the answer from the incoming carrier, do no work.
            "    view[name] = view[name]",
        ]),
        "refinement": (
            "faithful real patch: a removal that deletes the local registration and "
            "then RE-PRIMES the memoised view with the value it already had -- e.g. "
            "`old = cls.get_lookups(); del cls.class_lookups[n]; "
            "cls._clear_cached_lookups()` followed by re-seeding the cache from `old`. "
            "The read of the removed name still returns the deleted local lookup, so "
            "test_lookups_caching's assertNotIn('exactly', field.get_lookups()) fails "
            "exactly as on the unpatched tree. Does NOT resolve."
        ),
        "rationale": (
            "rejects on clause (2) view[name] == inherited[name]. The read-through law "
            "does NOT make this a tautology: its fallback leg (view[k] == inherited[k]) "
            "is guarded by store[k] == unregistered(), which the precondition denies at "
            "k == name, while its other leg gives view[name] == store[name] != "
            "unregistered() on the incoming state. So the echoed value is provably the "
            "stale local registration and provably not derivable-equal to "
            "inherited[name]. Proves the added precondition did not hollow out the "
            "discriminating clause."
        ),
    },

    # (J) UNGROUNDED-ORACLE ECHO, wrong-key flavour: answer the removed name from a
    #     DIFFERENT key of the incoming view -- the one key the read-through law
    #     does constrain. The law is keyed per name, so a cross-key derivation
    #     carries no information about inherited[name]. Must reject on clause (2).
    {
        "id": "weak-view-echo-other-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    store[name] = unregistered()",
            # cross-key echo: the other name's resolution, not this name's layer.
            "    view[name] = view[other_name()]",
        ]),
        "refinement": (
            "faithful real patch: a removal whose cache handling re-seeds the removed "
            "name's memoised entry from a DIFFERENT lookup's entry (a mis-keyed "
            "re-prime). A read of the removed name still resolves, to an unrelated "
            "lookup: test_lookups_caching's assertNotIn('exactly', "
            "field.get_lookups()) fails, and the wrong lookup class would be handed to "
            "any query using it. Does NOT resolve."
        ),
        "rationale": (
            "rejects on clause (2): the read-through law constrains view[other_name()] "
            "in terms of the OTHER key's own registration/enclosing layer, never in "
            "terms of inherited[name], so no cross-key derivation from the incoming "
            "carriers can discharge view[name] == inherited[name]. Pins that the "
            "operation must consult the enclosing layer AT THE REMOVED NAME."
        ),
    },

    # (K) THE HALF-RIGHT BRANCH: an impl that is correct exactly where clause (2)'s
    #     right-hand side is unregistered() -- the truncating ForeignObject family,
    #     where nothing in the read window provides the name -- and wrong on every
    #     class where the enclosing layer resurfaces an ancestor's registration.
    #     This is the rival aimed at what the faithfulness repair relaxed: if the
    #     spec only pinned the "resolves nowhere" case it would verify. Must reject
    #     on clause (2) in the else-branch.
    {
        "id": "weak-view-branch-halfright",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    store[name] = unregistered()",
            "    if inherited[name] == unregistered():",
            "        view[name] = unregistered()",
            "    else:",
            "        view[name] = other_name()",
        ]),
        "refinement": (
            "faithful real patch: a removal that busts the cache properly on the "
            "classes whose read window provides nothing for the name (ForeignObject "
            "and its subclasses, whose get_lookups truncates the merge range at "
            "related.py:858-864) but on every other class rebinds the memoised entry "
            "to an unrelated lookup. Measured on the gold-patched tree, the case it "
            "gets wrong is real: registering 'exactly' on models.CharField AND on "
            "models.Field and then removing CharField's leaves the recomputed "
            "CharField.get_lookups()['exactly'] == Field's lookup, which this impl "
            "replaces with a different one. The P2P lookup suite reads that name and "
            "gets the wrong lookup class. Does NOT resolve."
        ),
        "rationale": (
            "rejects on clause (2) in the else-branch: there inherited[name] != "
            "unregistered() and the impl writes other_name(), so view[name] == "
            "inherited[name] cannot be proved. This is the load-bearing check that the "
            "READ-THROUGH LAW precondition restricted the DOMAIN (to states whose view "
            "is in sync with the store and the enclosing layer) without weakening the "
            "OBLIGATION: clause (2) still pins the answer on the resurfacing states, "
            "not merely on the resolves-nowhere ones."
        ),
    },
    # ------------------------------------------------------------------ #
    # (L)-(P) THE READER-BLIND FAMILY: rivals that satisfy every clause    #
    # about the requesting component's OWN answers and neglect the other   #
    # readers of the same registration layer. This is the family the       #
    # per-reader clause (2b) exists to reject; each is a distinct way to   #
    # get one derived view right and the rest wrong.                       #
    # ------------------------------------------------------------------ #

    # (L) The component-only rival: delete from the store and bring the
    #     requesting component's OWN memoised answers in line, leaving every
    #     other reader of the same registration layer reporting the removed
    #     local registration. Satisfies clauses (1) and (2) exactly; must reject
    #     on clause (2b).
    {
        "id": "weak-reader-blind-component-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    store[name] = unregistered()",
            "    view[name] = inherited[name]",
        ]),
        "refinement": (
            "faithful real patch: a removal that deletes the local registration and "
            "refreshes ONLY the requesting class's own memoised read -- e.g. "
            "`del cls.class_lookups[n]` followed by an in-place repair of the entry "
            "cls.get_lookups() returns for cls, rather than an invalidation that "
            "reaches every class whose reads merge cls.class_lookups. A read through "
            "cls is then correct while a read through any subclass of cls still "
            "reports the deleted lookup. Measured on the gold-patched tree: this is "
            "the exact shape of the F2P failure, since test_lookups_caching registers "
            "on ForeignObject and then reads through a ForeignKey -- "
            "assertNotIn('exactly', ForeignKey_instance.get_lookups()) FAILS while the "
            "same assertion on ForeignObject passes. Does NOT resolve."
        ),
        "rationale": (
            "rejects on clause (2b) reader_view[name] == reader_rest[name]: the "
            "arbitrary reader's memoised answers still hold the removed LOCAL "
            "registration. Because the reader is a parameter, the obligation covers "
            "every component through which the registry can be read, so an impl that "
            "repairs only the requesting component's own view -- however faithfully -- "
            "cannot discharge it. This is the load-bearing discriminator for the "
            "per-reader observable."
        ),
    },

    # (M) The reader-blind rival with a LOCAL TEMP: behaviourally identical to
    #     (L) but routes the value through a local, so an impl cannot pass by
    #     being merely syntactically different from the component-only shape.
    #     Must reject on clause (2b) for the same reason.
    {
        "id": "weak-reader-blind-via-temp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    saved = inherited[name]  # type: int",
            "    store[name] = unregistered()",
            "    view[name] = saved",
        ]),
        "refinement": (
            "faithful real patch: the same component-only invalidation as (L), "
            "written so the fallback answer is read before the store deletion "
            "instead of after. Observably identical to (L) -- the requesting class's "
            "reads are correct, every dependent reader's are stale -- so it fails "
            "test_lookups_caching identically. Does NOT resolve."
        ),
        "rationale": (
            "rejects on clause (2b): reordering or naming the intermediate value "
            "changes nothing about the other readers' answers, so the per-reader "
            "obligation is still open. Pins that clause (2b) is about an observable, "
            "not about the shape of the code that satisfies clause (2)."
        ),
    },

    # (N) READER FRAME ATTACK: bring the removed name in line for the arbitrary
    #     reader BUT disturb an unrelated name in that reader's answers. Must
    #     reject on the per-reader frame clause.
    {
        "id": "weak-reader-frame-other-clobber",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    store[name] = unregistered()",
            "    view[name] = inherited[name]",
            "    reader_view[name] = reader_rest[name]",
            # collateral damage in the OTHER reader's answers.
            "    reader_view[other_name()] = unregistered()",
        ]),
        "refinement": (
            "faithful real patch: a removal whose invalidation reaches every reader "
            "but is over-broad in what it recomputes, so a DIFFERENT name stops "
            "resolving for a dependent reader (e.g. evicting the reader's whole "
            "merged view and re-seeding it short one entry). Reads of that other name "
            "through the dependent reader regress; the P2P lookup suite breaks. Does "
            "NOT resolve."
        ),
        "rationale": (
            "rejects on the per-reader frame clause reader_view[other_name()] == "
            "Old(reader_view[other_name()]): the operation may not bring the removed "
            "name in line for a reader by disturbing another name's resolution for "
            "that same reader."
        ),
    },

    # (O) READER PERMISSION rival: write the READ-ONLY carrier that says what the
    #     arbitrary reader's OWN remaining levels provide. Held at
    #     Acc(dict_pred(reader_rest), 1/2), so it must reject for insufficient
    #     permission -- the operation may consult those levels, never alter them.
    {
        "id": "weak-write-reader-rest",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    store[name] = unregistered()",
            "    view[name] = inherited[name]",
            # writing a half-permission input: not allowed.
            "    reader_rest[name] = unregistered()",
            "    reader_view[name] = reader_rest[name]",
        ]),
        "refinement": (
            "faithful real patch: a removal that, to make a dependent reader report "
            "nothing for the name, ALSO de-registers the name from some other class "
            "in that reader's own fallback range. It clears the reader's answer by "
            "destroying a registration that class still owns, so every other reader "
            "inheriting from it loses that lookup too. Does NOT resolve."
        ),
        "rationale": (
            "rejects for insufficient permission: `reader_rest` is passed at "
            "Acc(dict_pred(reader_rest), 1/2) (read-only). Pins that what the other "
            "registration levels provide to a reader is consulted, never modified -- "
            "the operation's licence is over the LOCAL store and over the derived "
            "answers, not over other components' registrations."
        ),
    },

    # (P) UNGROUNDED-ORACLE ECHO, reader flavour: bring the requesting component
    #     in line correctly, then answer the reader from the carrier it already
    #     holds. Tests that the per-reader read-through law did not turn clause
    #     (2b) into a tautology, exactly as (I) does for clause (2).
    {
        "id": "weak-reader-echo-incoming",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl([
            "    store[name] = unregistered()",
            "    view[name] = inherited[name]",
            # echo: re-assert the reader's incoming answer, do no work for it.
            "    reader_view[name] = reader_view[name]",
        ]),
        "refinement": (
            "faithful real patch: a removal that invalidates the requesting class's "
            "memoised read and then RE-SEEDS each dependent reader's memo from the "
            "answers it already held. Reads through those readers still return the "
            "deleted lookup, so test_lookups_caching fails exactly as on the "
            "unpatched tree. Does NOT resolve."
        ),
        "rationale": (
            "rejects on clause (2b). The per-reader read-through law does NOT make "
            "this a tautology: it admits reader_view[name] == store[name] (the "
            "incoming local registration, provably != unregistered() by the "
            "precondition) as well as reader_view[name] == reader_rest[name], and it "
            "constrains reader_rest[name] no further, so the echoed value cannot be "
            "proved equal to reader_rest[name]. Proves the added precondition "
            "restricted the DOMAIN to states whose readers are in sync, without "
            "weakening the per-reader OBLIGATION."
        ),
    },
]

# No @ContractOnly axioms and no A-consumed deep-model axioms in this bundle
# (meta.json axioms == []). The single A-reference (the view-update deep
# model) is validated out-of-band by axiom_check.py / G-AX, which runs the real
# RegisterLookupMixin in Docker and is a separate gate from the PBT axiom lane
# (that lane checks @ContractOnly axiom Ensures against the real callee; there is
# no such axiom here). Hence the PBT axiom lane is vacuous for this instance.
AXIOM_TESTS = []
