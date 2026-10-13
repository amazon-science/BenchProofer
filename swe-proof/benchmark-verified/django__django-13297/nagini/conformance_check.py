#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13297 (nagini).

SHADOW: the impl region of model.py's single contracted function
(`wrap_kwarg_value`), copied VERBATIM below with no contract calls to strip
(the impl region contains none). No PSeq/ToSeq appears anywhere in model.py,
so no sequence shim is needed. The one @ContractOnly callee the impl uses,
`wrap_resolvable`, calls the REAL repo function per the contract: it is
bridged to `django.utils.functional.lazy(access_value, type(value))()` — the
A-consumed axiom's repo counterpart per mapping.md section 1 (the per-value
deferred wrapping the model's axiom stands for), where `access_value` is the
same value-returning closure the real operation defers, INCLUDING the advisory
notice it raises when run. The `Wrapped` carrier class is not needed at
runtime: the bridged callee returns the real deferred entry, and the
observables below read the same facets model.py names.

ORACLE: the REAL patched repo function the model models (mapping.md
section 1): the per-entry value wrapping inside
`django.views.generic.base._wrap_url_kwargs_with_deprecation_warning`.
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched code importable. The script itself
applies no patch. The oracle entry for a value is obtained by calling the
real function on a mapping containing that value and reading the built entry
back out (the surrounding dict rebuild is unchanged control flow,
refinement.md tag I; the key-set passthrough is asserted as a sanity check).

TYPE BRIDGE (mapping.md section 2): the model carries a value as an int
value-tag and its runtime type as an int type-tag (`type_of`) only because
Nagini needs integer carriers; the bridge is "each distinct value/type is a
distinct tag", so at conformance time the shadow simply runs on the REAL
Python values directly (str/int/float/bool/None/bytes/tuple/list/dict) and
the observables compare real values and real runtime types. The entry is
characterised by exactly the facets the model names:

  facet 1 (resolves_to, reachable ONLY via run_deferral): RUNNING the entry's
      deferred computation through ordinary access yields the original value
      (`w == value`) — and it is an effect, not a free read: the run raises
      the advisory notice, so the run count is observed too;
  facet 2 (binder_castable): the entry is a Promise the type-directed
      parameter binder `django.db.models.fields.Field.get_prep_value`
      resolves to a concrete value equal to the original at the original's
      own runtime type (mapping.md section 3.2 — the binder is the base
      Field.get_prep_value Promise cast). Binder resolution is itself a
      deferral run, so its notice count is observed too;
  facet 3 (deferrals_run — the effect ledger): BUILDING the entry runs NO
      deferred computation, i.e. raises ZERO advisory notices. This is
      checked ABSOLUTELY on both sides (not merely differentially): the
      shadow's build and the real function's build must each raise 0 notices
      for every input. It is the observable model.py's `Ensures(deferrals_run(0))`
      stands for, and the reason the deferred entry is still deferred when the
      rebuilt mapping is handed back.

The check diffs the shadow entry's observation tuple against the oracle
entry's observation tuple per input (plus resolved-value equality and
resolved-type identity between the two), and asserts the absolute
zero-notices-at-build-time obligation on both sides.

INPUT DOMAIN: the model's precondition is the trivial value domain plus the
effect ledger at its entry count, so every Python value is admissible as input.
Admissible does not mean the wrapping succeeds on it: the model states the
wrapping as PARTIAL, permitting an exceptional exit when the value is itself a
type. Those inputs are therefore in scope for this check too, and are diffed in
their own lane (`check_partiality`) where the abort is the observable, rather
than in the batched lane below where one aborting value would mask the rest.
Boundary cases cover the empty string,
whitespace/unicode/astral strings, int/float edges, bool, None, bytes,
tuples, lists, dicts; fuzz draws >= 1e5 values across those types (floats
exclude NaN, whose reflexive inequality would fail both sides identically
and tell us nothing). Pinned fuzz seed: 132970.

Exit 0 iff zero disagreements and zero build-time notices; on disagreement
prints the input and both observations and exits 1. stdlib only (random for
fuzz).
"""
import json
import random
import sys
import warnings

SEED = 132970
N_FUZZ = 100000
BATCH = 200  # oracle values wrapped per real-function call (keys k0..k199)


def _ensure_django_configured():
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=True)
    import django
    django.setup()


# --- notice accounting (the effect the ledger models) ----------------------------

_NOTICE = None  # the advisory-notice category, bound in main()


def run_counting(fn):
    """Run fn, returning (kind, payload, n_notices) where n_notices is the number
    of advisory notices raised — i.e. the number of deferred computations run.
    `simplefilter('always')` defeats the per-location dedup so every run counts,
    matching the model's non-memoised `run_deferral`."""
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        try:
            out = ("ok", fn())
        except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
            out = ("raise", exc)
    n = sum(1 for r in rec if issubclass(r.category, _NOTICE))
    return out[0], out[1], n


# --- bridge for the @ContractOnly callee ----------------------------------------

def make_access_value(value):
    """The value-returning closure the wrapping operation defers. Like the real
    one, running it raises the advisory notice about the entry AND returns the
    captured value: the notice is NOT silenced, because it is the observable the
    effect ledger (`deferrals_run` / `run_deferral`) models."""
    def access_value(value=value):
        warnings.warn(
            'passing URL kwargs to the context is deprecated; reference this '
            'key through the view instead',
            _NOTICE, stacklevel=2,
        )
        return value
    return access_value


def _install_real_callee():
    """`wrap_resolvable` calls the REAL repo callee the A-consumed axiom
    models: lazy(access_value, type(value))() (mapping.md section 1)."""
    from django.utils.functional import lazy

    def wrap_resolvable(value):
        return lazy(make_access_value(value), type(value))()

    globals()["wrap_resolvable"] = wrap_resolvable


# --- the impl region of model.py, verbatim ---------------------------------------

def wrap_kwarg_value(value):
    w = wrap_resolvable(value)  # type: Wrapped
    return w


# --- observables (the facets model.py names) --------------------------------------

def observe(w, value, Promise, binder_field):
    """Read an entry's observation tuple: (facet-1 resolution, notices raised by
    that resolution, Promise-ness, binder resolution outcome, notices raised by
    the binder resolution, resolved-value equality, resolved runtime type).
    Returns (obs_tuple, resolved_or_None)."""
    # facet 1: run the deferred computation through ordinary access. This is an
    # effect: count the notices it raises (the ledger step).
    kind, payload, n_force = run_counting(lambda: bool(w == value))
    forces = (payload if kind == "ok" else "raise:%s" % type(payload).__name__)
    is_promise = isinstance(w, Promise)       # facet 2 hook presence
    # facet 2: the type-directed binder's resolution — itself a deferral run.
    bkind, bpayload, n_bind = run_counting(lambda: binder_field.get_prep_value(w))
    if bkind == "raise":
        return (forces, n_force, is_promise,
                "raise:%s" % type(bpayload).__name__, n_bind, None, None), None
    resolved = bpayload
    concrete = (not isinstance(resolved, Promise)
                and type(resolved).__name__ != "SimpleLazyObject")
    if not concrete:
        return (forces, n_force, is_promise, "unresolved", n_bind,
                None, None), None
    return (forces, n_force, is_promise, "resolved", n_bind,
            bool(resolved == value), type(resolved).__name__), resolved


# --- differential driver -----------------------------------------------------------

class Checker(object):
    def __init__(self):
        from django.utils.functional import Promise
        from django.db.models.fields import Field
        from django.views.generic.base import (
            _wrap_url_kwargs_with_deprecation_warning as real_wrap,
        )
        self.Promise = Promise
        self.binder_field = Field()
        self.real_wrap = real_wrap
        self.checked = 0
        self.partiality_checked = 0
        self.silent_checked = 0
        self.build_notices_shadow = 0
        self.build_notices_oracle = 0

    def check_batch(self, values):
        """Diff shadow vs oracle on a batch of values; returns an error string
        on the first disagreement, else None."""
        kwargs = {}
        for i, v in enumerate(values):
            kwargs["k%d" % i] = v
        # facet 3 (ORACLE side, ABSOLUTE): building the whole batch of entries
        # must run NO deferred computation -> zero advisory notices.
        kind, out, n_build_oracle = run_counting(
            lambda: self.real_wrap(dict(kwargs)))
        if kind == "raise":
            return ("ORACLE raised while building entries: %r" % (out,))
        if n_build_oracle != 0:
            return ("ORACLE ran %d deferred computation(s) while BUILDING %d "
                    "entries (expected 0): building an entry must leave its "
                    "deferred computation unrun"
                    % (n_build_oracle, len(values)))
        self.build_notices_oracle += n_build_oracle
        if set(out.keys()) != set(kwargs.keys()):
            return ("ORACLE key passthrough mismatch: in=%r out=%r"
                    % (sorted(kwargs), sorted(out)))
        for i, v in enumerate(values):
            # facet 3 (SHADOW side, ABSOLUTE): the impl region must likewise run
            # no deferred computation while building the entry.
            skind, shadow_w, n_build_shadow = run_counting(
                lambda v=v: wrap_kwarg_value(v))
            if skind == "raise":
                return ("SHADOW raised on value %r (type %s): %r"
                        % (v, type(v).__name__, shadow_w))
            if n_build_shadow != 0:
                return ("SHADOW ran %d deferred computation(s) while BUILDING "
                        "the entry for %r (expected 0)"
                        % (n_build_shadow, v))
            self.build_notices_shadow += n_build_shadow
            oracle_w = out["k%d" % i]
            s_obs, s_res = observe(shadow_w, v, self.Promise, self.binder_field)
            o_obs, o_res = observe(oracle_w, v, self.Promise, self.binder_field)
            if s_obs != o_obs:
                return ("DISAGREEMENT on value %r (type %s):\n"
                        "  shadow (impl region) observation = %r\n"
                        "  real (patched repo wrapping) observation = %r"
                        % (v, type(v).__name__, s_obs, o_obs))
            # Running the deferred computation is never free: obtaining the
            # value must have raised at least one notice on both sides (this is
            # what makes `run_deferral`'s ledger step, and hence facet 3,
            # meaningful rather than vacuous).
            if s_obs[1] < 1:
                return ("value %r: resolving the entry raised %d advisory "
                        "notice(s); running a deferred computation must raise "
                        "at least one (else the effect is unobservable)"
                        % (v, s_obs[1]))
            if s_obs[3] == "resolved":
                if not (s_res == o_res and type(s_res) is type(o_res)):
                    return ("DISAGREEMENT on value %r: binder-resolved values "
                            "differ: shadow=%r (%s) real=%r (%s)"
                            % (v, s_res, type(s_res).__name__,
                               o_res, type(o_res).__name__))
            self.checked += 1
        return None


def type_valued_inputs():
    """Values in the family on which the modelled wrapping is PARTIAL (model.py's
    permitted exceptional exit) AND on which the real wrapping ABORTS. Kept in
    their own lane rather than in boundary_values(): the oracle wraps a whole
    batch in one call, so a value that makes the real wrapping abort would take
    the batch down with it. Here the abort IS the observable being checked.

    The family is NOT just "the value is a type". The real preparation walks the
    advertised type's ancestors and then overlays a delegate-arm choice made by
    comparing that type against the built-in result types, so a NON-type value
    reaches the same abort two ways: by shadowing the ancestor-enumeration name,
    or by having a metaclass whose comparison raises or reports both arms. Both
    kinds are included here; their absence is why an earlier revision of this
    battery could claim the family was exactly `isinstance(value, type)`."""
    class Meta(type):
        pass

    class WithMeta(metaclass=Meta):
        pass

    class Plain:
        pass

    # non-type members, ancestor-enumeration route
    class MroData:
        mro = 42

    class MroOneArg:
        def mro(self, x):
            return []

    class MroProp:
        @property
        def mro(self):
            return []

    # non-type members, delegate-overlay route
    class MetaEqBoom(type):
        def __eq__(cls, other):
            raise RuntimeError("metaclass __eq__ boom")

        def __hash__(cls):
            return id(cls)

    class EqBoom(metaclass=MetaEqBoom):
        pass

    class MetaEqAll(type):
        def __eq__(cls, other):
            return True

        def __hash__(cls):
            return id(cls)

    class EqAll(metaclass=MetaEqAll):
        pass

    import abc
    import enum
    return [int, str, object, type, bool, tuple, dict, BaseException,
            Plain, WithMeta, Meta, abc.ABC, enum.Enum,
            MroData(), MroOneArg(), MroProp(), EqBoom(), EqAll()]


def check_partiality(chk):
    """Differential check of the PARTIALITY the model states: on a value that is
    itself a type, shadow and oracle must AGREE that no entry is produced, and
    neither may run a deferred computation on the way out (model.py requires the
    ledger preserved on the aborting exit too). A disagreement here — either side
    succeeding where the other aborts — is exactly the over/under-claim an
    earlier revision of this battery could not see, because its generated domain
    contained no class objects at all."""
    for v in type_valued_inputs():
        okind, opayload, o_notices = run_counting(
            lambda v=v: chk.real_wrap({"k": v}))
        skind, spayload, s_notices = run_counting(
            lambda v=v: wrap_kwarg_value(v))
        if okind != skind:
            return ("PARTIALITY DISAGREEMENT on the unpreparable input %r: "
                    "shadow %s, real patched wrapping %s — the model's permitted "
                    "exceptional exit must match the real callee's"
                    % (v, skind, okind))
        if okind != "raise":
            return ("PARTIALITY: the real patched wrapping unexpectedly produced "
                    "an entry for the unpreparable input %r; model.py permits an "
                    "exceptional exit there, which would be an under-claim if the "
                    "real construction always succeeded" % (v,))
        if o_notices != 0 or s_notices != 0:
            return ("PARTIALITY: aborting on the unpreparable input %r ran a "
                    "deferred computation (%d shadow / %d oracle advisory "
                    "notices); model.py requires the ledger back at its entry "
                    "count on the ABORTING exit too" % (v, s_notices, o_notices))
        chk.partiality_checked += 1
    return None


def silent_divergence_inputs():
    """The OTHER shape of the unpreparable family: values on which the real
    wrapping does NOT abort, produces an entry the binder recognises, and whose
    resolution then does not give the value back. Kept out of boundary_values()
    only for clarity — the point of this lane is the non-round-trip itself.

    Two sub-shapes: one where the resolution RAISES, and one where it SUCCEEDS
    and silently hands back a well-formed object of another type. The silent one
    is what makes an UNCONDITIONAL resolution-value clause unfaithful, and its
    absence from this battery is why one shipped: every other lane here either
    round-trips or aborts, so nothing contradicted it."""
    class MetaEqBytes(type):
        def __eq__(cls, other):
            return other is bytes

        def __hash__(cls):
            return id(cls)

    class ResolutionRaises(metaclass=MetaEqBytes):
        pass

    class ResolutionSilentlyDiverges(metaclass=MetaEqBytes):
        def __index__(self):
            return 5

    return [ResolutionRaises(), ResolutionSilentlyDiverges()]


def check_silent_divergence(chk):
    """Differential check of the NON-ABORTING shape of the unpreparable family:
    shadow and oracle must agree, the entry must be produced without running any
    deferred computation, the binder must RECOGNISE it (model.py grants that
    unconditionally), and resolution must NOT give the value back (which is what
    model.py's GUARDED resolution-value clause states, and what an unconditional
    one would have contradicted)."""
    for v in silent_divergence_inputs():
        okind, oentry, o_build = run_counting(
            lambda v=v: chk.real_wrap({"k": v}))
        skind, sentry, s_build = run_counting(lambda v=v: wrap_kwarg_value(v))
        if okind != "ok" or skind != "ok":
            return ("NON-ABORTING SHAPE: expected both sides to PRODUCE an entry "
                    "for %r, got shadow %s / real %s; this lane is about the "
                    "family members on which the wrapping does not abort"
                    % (v, skind, okind))
        if o_build != 0 or s_build != 0:
            return ("NON-ABORTING SHAPE: building the entry for %r ran a deferred "
                    "computation (%d shadow / %d oracle notices), which the "
                    "ledger obligation forbids" % (v, s_build, o_build))
        o_w = oentry["k"]
        s_obs, s_res = observe(sentry, v, chk.Promise, chk.binder_field)
        o_obs, o_res = observe(o_w, v, chk.Promise, chk.binder_field)
        if s_obs != o_obs:
            return ("DISAGREEMENT on the non-aborting unpreparable input %r:\n"
                    "  shadow (impl region) observation = %r\n"
                    "  real (patched repo wrapping) observation = %r"
                    % (v, s_obs, o_obs))
        if not s_obs[2]:
            return ("NON-ABORTING SHAPE: the entry for %r is not recognised by "
                    "the binder; model.py grants recognition UNCONDITIONALLY, so "
                    "that clause would be an over-claim here" % (v,))
        # facet 1 must FAIL here: either the resolution raises, or it succeeds
        # and yields something that is not the value. If it round-tripped, the
        # guard on model.py's resolution-value clause would be unjustified.
        round_tripped = (s_obs[0] is True)
        if round_tripped:
            return ("NON-ABORTING SHAPE: resolution of the entry for %r DID give "
                    "the value back; then the guard on model.py's "
                    "resolution-value clause would be unjustified and the clause "
                    "should be unconditional" % (v,))
        if s_obs[3] == "resolved" and s_obs[5]:
            return ("NON-ABORTING SHAPE: the binder resolved the entry for %r "
                    "back to the value; the guard would be unjustified" % (v,))
        chk.silent_checked += 1
    return None


def boundary_values():
    return [
        "Rene Magritte",              # the F2P-exercised str case
        "", "a", "0", ":", "@", "/", " ", "\t", "\n",
        "slug-with-dashes", "under_score", "sp ace", "x" * 300,
        "\xa0", "caf\xe9", " ", "\U0001F600", "　ideographic",
        0, 1, -1, 7, -3, 2**31, -(2**31), 2**63, 10**30,
        0.0, -0.0, 3.5, -2.25, 1e-300, 1e300, float("inf"), float("-inf"),
        True, False,
        None,
        b"", b"bytes", b"\x00\xff",
        (), (1, 2), ("a", 3.5),
        [], [1, "two"], list(range(5)),
        {}, {"n": 1}, {"a": [1, 2], "b": None},
    ]


def fuzz_values(rng, n):
    letters = ("abcdefghijklmnopqrstuvwxyz"
               "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.:/@%\xe9\xa0 ")
    astral = "\U0001F600\U0001F4A9"
    for _ in range(n):
        kind = rng.randrange(9)
        if kind == 0:                                  # str
            m = rng.randint(0, 20)
            yield "".join(rng.choice(letters) for _ in range(m))
        elif kind == 1:                                # str with astral cps
            m = rng.randint(0, 6)
            yield "".join(rng.choice(letters + astral) for _ in range(m))
        elif kind == 2:                                # int
            yield rng.randint(-2**40, 2**40)
        elif kind == 3:                                # small int
            yield rng.randint(-5, 5)
        elif kind == 4:                                # float (no NaN)
            yield rng.uniform(-1e6, 1e6)
        elif kind == 5:                                # bool / None
            yield rng.choice([True, False, None])
        elif kind == 6:                                # bytes
            m = rng.randint(0, 12)
            yield bytes(rng.randrange(256) for _ in range(m))
        elif kind == 7:                                # tuple of scalars
            m = rng.randint(0, 4)
            yield tuple(rng.randint(-9, 9) for _ in range(m))
        else:                                          # list of scalars
            m = rng.randint(0, 4)
            yield [rng.choice(["s", 1, 2.5, None]) for _ in range(m)]


def main():
    global _NOTICE
    _ensure_django_configured()
    from django.utils.deprecation import RemovedInDjango40Warning
    _NOTICE = RemovedInDjango40Warning
    _install_real_callee()

    chk = Checker()

    boundary = boundary_values()
    err = chk.check_batch(boundary)
    if err:
        print(err)
        return 1

    err = check_partiality(chk)
    if err:
        print(err)
        return 1

    err = check_silent_divergence(chk)
    if err:
        print(err)
        return 1

    rng = random.Random(SEED)
    batch = []
    for v in fuzz_values(rng, N_FUZZ):
        batch.append(v)
        if len(batch) >= BATCH:
            err = chk.check_batch(batch)
            if err:
                print(err)
                return 1
            batch = []
    if batch:
        err = chk.check_batch(batch)
        if err:
            print(err)
            return 1

    print("G-CONF OK: shadow impl (bridged @ContractOnly deferred-wrapping "
          "callee) == real patched per-entry wrapping on %d inputs "
          "(%d boundary + %d fuzz, seed %d); 0 disagreements; and BOTH sides "
          "ran 0 deferred computations at build time (%d shadow / %d oracle "
          "advisory notices while building), while resolving an entry raised "
          "one or more on every input; and both sides agreed on the PARTIAL "
          "exit (no entry, 0 deferral runs) for %d unpreparable inputs, AND on "
          "the non-aborting shape of that same family for %d more, where an "
          "entry IS produced and recognised by the binder and its resolution "
          "does NOT give the value back -- which is what the GUARDED "
          "resolution-value clause states and what an unconditional one would "
          "contradict."
          % (chk.checked, len(boundary), N_FUZZ, SEED,
             chk.build_notices_shadow, chk.build_notices_oracle,
             chk.partiality_checked, chk.silent_checked))
    print(json.dumps({
        "checked": chk.checked, "disagreements": 0, "seed": SEED,
        "partiality_inputs_checked": chk.partiality_checked,
        "non_aborting_unpreparable_inputs_checked": chk.silent_checked,
        "build_time_deferral_runs_shadow": chk.build_notices_shadow,
        "build_time_deferral_runs_oracle": chk.build_notices_oracle,
        "shadow": ("direct (impl region verbatim; @ContractOnly callee "
                   "bridged to the real deferred-wrapping repo callee)")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
