# properties.py — PBT falsification battery for django__django-13344.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap a
# whole `# impl-start` .. `# impl-end` body for one of the two modeled functions
# and leave the frozen spec (axioms / pure / pre / post-conditions / signatures)
# byte-identical. same_spec is therefore guaranteed for every case.
#
# Defended surface (read from model.py / refinement.md / instance.json):
#   configure_handler(handler, producer) pins three load-bearing facts:
#     (P) handler.producer is producer                  -- producer retained
#     (S) handler.absence_signalled == (producer is None)  -- deprecation signal
#     (A) handler.async_advertised == producer_is_async(producer)  -- the bug-delta
#   configure_settings_handler adds the store-selection invariant:
#     (N) handler.store_name == (override_name if override_name is not None else default_name)
#     (R) handler.store == resolve_store(handler.store_name)   -- cache==caches[alias]
#     (Q) Result() == handler.store
#   (A) is the discriminating fix (the restored _async_check / _is_coroutine
#   marker; the F2P test_coroutine keys on it). (S) is what F2P test_deprecation
#   keys on. (N)+(R) are the cache==caches[cache_alias] invariant the three
#   constructor PASS_TO_PASS tests pin (test_constructor, *_update_*_constructor,
#   *_fetch_*_constructor).
#
# Read-only inputs: NONE. Every handler field is held with FULL permission
# (Acc(handler.f), writable) and the value params (producer/default_name/
# override_name) are immutable Optional[int]/int. The Acc(...,1/2) frame-mutation
# class therefore does not apply here -- see 'assessment' in the structured
# return for why and what stands in for it.
#
# Oracle grounding: producer_is_async / resolve_store are @Pure @ContractOnly,
# but each is GROUNDED in an actual argument (producer / store_name). The
# postconditions read them as functions of the args, so an impl that satisfies
# (A)/(R) is doing the real work -- there is no "wrong echo" of an answer-key.
# The honest stand-in is a cheapest-correct positive control (pos-cheapest).
from pathlib import Path

INSTANCE = "django__django-13344"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two whole-impl anchors (each unique; each terminated distinctly so the
# swap stays strictly inside one function's # impl-start/# impl-end region).
# ---------------------------------------------------------------------------

_CH_IMPL = """    if producer is None:
        handler.absence_signalled = True
    else:
        handler.absence_signalled = False
    handler.producer = producer
    handler.async_advertised = producer_is_async(producer)
    # impl-end"""

_CSH_IMPL = """    if producer is None:
        handler.absence_signalled = True
    else:
        handler.absence_signalled = False
    handler.producer = producer
    handler.async_advertised = producer_is_async(producer)
    # Defaults established first (as super().__init__ -> base init does):
    handler.store_name = default_name
    handler.store = resolve_store(handler.store_name)
    # An explicit override re-selects the name AND re-resolves the store from it:
    if override_name is not None:
        handler.store_name = override_name
        handler.store = resolve_store(handler.store_name)
    return handler.store
    # impl-end"""


def _ch(new_body: str) -> str:
    """Replace ONLY configure_handler's impl body (keeps the trailing
    `# impl-end` marker so the region boundary is untouched)."""
    return _swap(_BASE, _CH_IMPL, new_body + "\n    # impl-end")


def _csh(new_body: str) -> str:
    """Replace ONLY configure_settings_handler's impl body."""
    return _swap(_BASE, _CSH_IMPL, new_body + "\n    # impl-end")


SPEC_TESTS = [

    # ----------------------------------------------------------------- soundness
    # POSITIVE CONTROL: a structurally-different but fully CORRECT impl. The
    # branch is reordered (set False first, override to True on None), the
    # producer is stored before the signal, and the async flag is bound via a
    # local before assignment. No framing lemma is needed (the postconditions are
    # direct field equalities, not a fold), so this must verify. If it cannot =>
    # SPEC-TOO-STRONG.
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _ch(
            "    handler.producer = producer\n"
            "    handler.absence_signalled = False\n"
            "    if producer is None:\n"
            "        handler.absence_signalled = True\n"
            "    is_async = producer_is_async(producer)  # type: bool\n"
            "    handler.async_advertised = is_async"
        ),
        "rationale": "a correct but reordered/temp-reshaped impl must verify "
                     "(facts are direct field equalities; no fold lemma needed).",
    },

    # The cheapest HONEST positive control: since the oracle is grounded in the
    # args, the cheapest correct impl just echoes the grounded oracle value
    # directly -- which is exactly the work the gold does. Stands in for the
    # ungrounded-oracle case (there is no wrong echo to build).
    {
        "id": "pos-cheapest-grounded",
        "kind": "soundness",
        "expect": "verify",
        "module": _csh(
            "    handler.producer = producer\n"
            "    handler.absence_signalled = (producer is None)\n"
            "    handler.async_advertised = producer_is_async(producer)\n"
            "    name = default_name if override_name is None else override_name  # type: int\n"
            "    handler.store_name = name\n"
            "    handler.store = resolve_store(name)\n"
            "    return handler.store"
        ),
        "rationale": "cheapest correct impl: assigns each field its grounded "
                     "oracle/arg value in one pass; the store-name selection is "
                     "computed up front. Grounded oracle => no wrong echo; this "
                     "is the honest positive control.",
    },

    # ----------------------------------------------------------------- admissibility
    # A caller that constructs a fresh Handler and invokes the modeled function on
    # an F2P-shaped input (a supplied, non-None producer token) and on the absent
    # producer, then asserts a postcondition consequence of each. If the Requires
    # cannot be met for a normal input => PRECOND-TOO-STRONG.
    #
    # The probe is HOSTED IN configure_settings_handler's impl region (it calls
    # configure_handler) rather than in configure_handler's own. Both host the
    # identical claim -- a fresh Handler + a supplied producer satisfies
    # configure_handler's precondition, the call site verifies, and the post facts
    # are derivable -- but the original self-hosted form made configure_handler
    # UNCONDITIONALLY self-recursive (every call re-entered with producer=7), which
    # is a genuinely diverging program. Under the termination obligation Nagini
    # rightly refuses it:
    #   error: Obligation leak check failed. Callee configure_handler might not
    #   take all unsatisfied obligations from the caller.
    # A caller's level must be STRICTLY greater than its callee's, and no method can
    # outrank itself. Cross-hosting satisfies that ordering (configure_settings_handler
    # is level 10, configure_handler level 6) and keeps the admissibility claim
    # intact; it is not a weakening, since a non-terminating probe never evidenced
    # precondition admissibility in the first place.
    #
    # Not vacuous: Assert(False) spliced at the end of this same body is REJECTED
    # ("Assertion False might not hold"), so the call site's path is reachable and
    # the asserted post facts are really being discharged.
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _csh(
            "    if producer is None:\n"
            "        handler.absence_signalled = True\n"
            "    else:\n"
            "        handler.absence_signalled = False\n"
            "    handler.producer = producer\n"
            "    handler.async_advertised = producer_is_async(producer)\n"
            "    handler.store_name = default_name\n"
            "    handler.store = resolve_store(handler.store_name)\n"
            "    if override_name is not None:\n"
            "        handler.store_name = override_name\n"
            "        handler.store = resolve_store(handler.store_name)\n"
            "    # admissibility probe: a fresh handler + an F2P-shaped supplied\n"
            "    # producer satisfies the precondition; the call site verifies and\n"
            "    # the post facts are derivable.\n"
            "    probe = Handler()\n"
            "    configure_handler(probe, 7)\n"
            "    Assert(probe.absence_signalled == False)\n"
            "    Assert(probe.producer is 7)\n"
            "    Assert(probe.async_advertised == producer_is_async(7))\n"
            "    probe2 = Handler()\n"
            "    configure_handler(probe2, None)\n"
            "    Assert(probe2.absence_signalled == True)\n"
            "    return handler.store"
        ),
        "rationale": "the precondition must admit a normal F2P-shaped input "
                     "(a fresh handler + a supplied producer); else PRECOND-TOO-STRONG. "
                     "Hosted cross-method so the probe's own call graph terminates "
                     "(caller level 10 > callee level 6); the asserted post facts are "
                     "unchanged and Assert(False) here is still rejected.",
    },

    # ----------------------------------------------------------------- uniqueness
    # ATTACK 1 (partial-domain, THE bug-delta). Drop the async_check: hardcode
    # async_advertised = False. Correct on every sync/None producer, WRONG on an
    # async producer. This is exactly model_prepatch.py's omission and the bug the
    # gold fix restores.
    {
        "id": "weak-async-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ch(
            "    if producer is None:\n"
            "        handler.absence_signalled = True\n"
            "    else:\n"
            "        handler.absence_signalled = False\n"
            "    handler.producer = producer\n"
            "    handler.async_advertised = False"
        ),
        "refinement": "this is the pre-patch omission of self._async_check(): the "
                      "_is_coroutine marker is never set, so "
                      "asyncio.iscoroutinefunction(instance) is always False. The "
                      "F2P test_coroutine asserts it is True for an async "
                      "get_response => the faithful real patch FAILS the F2P; it "
                      "does NOT resolve.",
        "rationale": "violates postcondition (A) "
                     "async_advertised == producer_is_async(producer) on any async "
                     "producer (producer_is_async is left general for non-None).",
    },

    # ATTACK 2 (partial-domain, the deprecation signal). Always signal absence,
    # regardless of producer. Correct only on the None producer; WRONG for any
    # supplied producer.
    {
        "id": "weak-signal-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ch(
            "    handler.absence_signalled = True\n"
            "    handler.producer = producer\n"
            "    handler.async_advertised = producer_is_async(producer)"
        ),
        "refinement": "this fires the deprecation signal even for a supplied "
                      "get_response. The F2P test_deprecation / "
                      "test_passing_explicit_none assert the warning fires ONLY "
                      "when get_response is None (and the constructor-with-callable "
                      "P2P paths must NOT warn) => the faithful real patch warns "
                      "spuriously and does NOT resolve.",
        "rationale": "violates postcondition (S) "
                     "absence_signalled == (producer is None) for every non-None producer.",
    },

    # ATTACK 3 (value double-mask / producer not retained). Store a sentinel
    # instead of the real producer. The async/signal facts are still computed
    # from the real `producer`, so a value-proxy that only checked async/signal
    # would miss it -- but (P) pins identity, so it must reject.
    {
        "id": "weak-producer-not-retained",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ch(
            "    if producer is None:\n"
            "        handler.absence_signalled = True\n"
            "    else:\n"
            "        handler.absence_signalled = False\n"
            "    handler.producer = None\n"
            "    handler.async_advertised = producer_is_async(producer)"
        ),
        "refinement": "this drops self.get_response = get_response (retains None "
                      "instead of the supplied producer). Downstream the middleware "
                      "would call None(request) instead of the real get_response => "
                      "the chain breaks; the constructor/middleware P2P behaviour "
                      "diverges and the faithful real patch does NOT resolve.",
        "rationale": "violates postcondition (P) handler.producer is producer "
                     "for any supplied producer.",
    },

    # ATTACK 4 (store-selection partial-domain, override ignored). In the
    # store-selecting variant, ignore override_name and always select the default
    # name + default-resolved store. Correct on the default path, WRONG on the
    # explicit-custom path (an override cache_alias is requested).
    {
        "id": "weak-override-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _csh(
            "    if producer is None:\n"
            "        handler.absence_signalled = True\n"
            "    else:\n"
            "        handler.absence_signalled = False\n"
            "    handler.producer = producer\n"
            "    handler.async_advertised = producer_is_async(producer)\n"
            "    handler.store_name = default_name\n"
            "    handler.store = resolve_store(handler.store_name)\n"
            "    return handler.store"
        ),
        "refinement": "this ignores the explicit cache_alias kwarg: the override "
                      "branch (self.cache_alias = cache_alias) is dropped. "
                      "test_constructor asserts cache_alias == 'other' and cache "
                      "== self.other_cache when an explicit alias is passed => the "
                      "faithful real patch keeps the default alias and FAILS the "
                      "constructor P2P; it does NOT resolve.",
        "rationale": "violates postcondition (N) "
                     "store_name == (override_name if override_name is not None "
                     "else default_name) when an override is supplied.",
    },

    # ATTACK 5 (store double-mask: name updated, store NOT re-resolved). The
    # subtlest: select the override NAME but leave the store resolved from the
    # default name. This is exactly the cache==caches[cache_alias] invariant the
    # patch restructure preserves -- a refinement that updated cache_alias but
    # forgot self.cache = caches[self.cache_alias].
    {
        "id": "weak-store-stale",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _csh(
            "    if producer is None:\n"
            "        handler.absence_signalled = True\n"
            "    else:\n"
            "        handler.absence_signalled = False\n"
            "    handler.producer = producer\n"
            "    handler.async_advertised = producer_is_async(producer)\n"
            "    handler.store_name = default_name\n"
            "    handler.store = resolve_store(handler.store_name)\n"
            "    if override_name is not None:\n"
            "        handler.store_name = override_name\n"
            "    return handler.store"
        ),
        "refinement": "this updates cache_alias to the override but FORGETS "
                      "self.cache = caches[self.cache_alias], leaving cache "
                      "resolved from the default alias. test_constructor / "
                      "test_*_constructor assert middleware.cache == "
                      "caches[middleware.cache_alias] (== self.other_cache) => the "
                      "store is stale w.r.t. the selected alias and the faithful "
                      "real patch FAILS those constructor P2P tests; it does NOT "
                      "resolve.",
        "rationale": "violates postcondition (R) "
                     "store == resolve_store(store_name) when an override is "
                     "supplied (store_name updated, store left at the default "
                     "resolution).",
    },

    # ATTACK 6 (supporting near-miss: store reported back wrong). Return a stale
    # default-resolved store while leaving fields consistent. Hits (Q)
    # Result() == handler.store. Cheap supporting case, still carries refinement.
    {
        "id": "weak-result-stale",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _csh(
            "    if producer is None:\n"
            "        handler.absence_signalled = True\n"
            "    else:\n"
            "        handler.absence_signalled = False\n"
            "    handler.producer = producer\n"
            "    handler.async_advertised = producer_is_async(producer)\n"
            "    default_store = resolve_store(default_name)  # type: int\n"
            "    handler.store_name = default_name\n"
            "    handler.store = default_store\n"
            "    if override_name is not None:\n"
            "        handler.store_name = override_name\n"
            "        handler.store = resolve_store(handler.store_name)\n"
            "    return default_store"
        ),
        "refinement": "this returns the default-resolved store rather than the "
                      "actually-selected store. The constructed middleware's "
                      "observable .cache must equal caches[.cache_alias]; reporting "
                      "a different store breaks the constructor P2P assertions on "
                      "the override path => the faithful real patch does NOT resolve.",
        "rationale": "violates postcondition (Q) Result() == handler.store on the "
                     "override path (Result is the default store, handler.store is "
                     "the override-resolved store).",
    },
]


# No @ContractOnly axioms reach a caller-supplied input outside the model's
# Requires domain that needs a separate Docker probe beyond what axiom_check.py
# already exercises; the existing G-AX check (axiom_check.py) executes the real
# asyncio.iscoroutinefunction (producer_is_async) and the registry-read
# reproduction (resolve_store) on boundary + 4000 fuzz inputs and asserts the
# axiom Ensures + determinism + the deep-model containment. We re-run that exact
# host-validated oracle in-container as a single soundness+containment probe so
# the axiom lane is grounded in the REAL callee (not a regex over source), as the
# plan requires.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-producer-is-async-and-resolve-store",
        "axiom": "producer_is_async,resolve_store",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        # The probe is the bundle's host-validated G-AX oracle, embedded verbatim
        # (the runner mounts only this script; axiom_check.py is NOT in-container).
        # It CALLS the real asyncio.iscoroutinefunction and reproduces the real
        # caches[alias] registry read -- it never scrapes source. Files are not
        # read, so no utf-8 codec concern. Exits 0 iff:
        #   producer_is_async axiom (None -> False, determinism, exact match vs
        #   real asyncio.iscoroutinefunction) holds on 9 boundary + 4000 fuzz
        #   producer tokens; the configuration deep model (the super().__init__
        #   marker mechanism) matches the three facts; resolve_store is
        #   deterministic; and the store-selection deep model
        #   store == resolve_store(store_name) holds on every default/
        #   explicit-default/explicit-custom name pair.
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "axiom-soundness: the real asyncio.iscoroutinefunction must "
                     "satisfy producer_is_async's sole Ensures (None -> False) and "
                     "the registry read must be deterministic, on every input the "
                     "model's Requires admits; a violation => AXIOM-UNSOUND. Also "
                     "covers containment: the model only passes Optional[int] "
                     "producer tokens and int store names, all inside the axiom "
                     "Requires domains (no domain restriction beyond purity).",
    },
]
