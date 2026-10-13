#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13297.

Executes the REAL Django deferred-entry callees
(`django.utils.functional.lazy`, `django.utils.functional.SimpleLazyObject`),
the REAL type-directed parameter binder
(`django.db.models.fields.Field.get_prep_value`, which casts a deferred stand-in
through `isinstance(value, Promise)` -> `value._proxy____cast()`), and the REAL
advisory-notice effect that running an entry's deferred computation has, and
asserts that every observation matches the deep-model A-references encoded in
model.py.

There is NO consumed answer-key oracle. The A-references validated are:

  (A-reference, model.py `type_of`) the value's real runtime type is
      value-dependent. Checked: the value the binder resolves the entry to has
      `type(resolved) == type(value)` (the value's OWN real runtime type),
      regardless of the declared result class.

  (A-reference, model.py `wrap_resolvable` / `binder_castable`) the post-change
      construction `lazy(access_value, type(value))()` produces an entry the
      type-directed binder RESOLVES (it is a `Promise`, so `get_prep_value` casts
      it) to the original value at the value's own real runtime type. This is the
      SOLE producer of the `binder_castable(w, value, type_of(value))`
      capability.

  (A-reference, model.py `wrap_opaque`) the pre-change construction
      `SimpleLazyObject(access_value)` produces an entry that resolves to the
      same value through ordinary access but that the type-directed binder does
      NOT resolve (it is NOT a `Promise`, so `get_prep_value` leaves it
      unconverted) — the binder rejects it ("unsupported type" / wrong-type
      error). It does NOT grant the `binder_castable` capability.

  (shared facet 1, model.py `resolves_to`) BOTH constructions produce an entry
      that resolves to the original value (so the resolution value is NOT the
      discriminator).

  (A-reference, model.py `own_type_unpreparable` — the PARTIALITY boundary) the
      post-change construction is PARTIAL, and the family on which it has no
      result is exactly "the value is itself a type". Checked, on the real
      callees, in BOTH directions:
        * for every value that is itself a type, the post-change construction
          RAISES and no entry is produced — so model.py is right to permit the
          exceptional exit there, and would be over-claiming if it promised an
          entry;
        * for every value that is NOT a type, the post-change construction
          returns an entry normally — so the permitted abort is confined to that
          one family and model.py is right not to permit it anywhere else;
        * the abort raises NO advisory notice, so the ledger is genuinely back at
          its entry count on the aborting exit (model.py requires deferral
          preservation on BOTH exits);
        * the PRE-change construction is TOTAL on the same family (it advertises
          no per-value type, so it builds an entry for a type-valued input too).
          The asymmetry is why the partiality is stated as PERMITTED rather than
          REQUIRED: a way of building the entry that consults no per-value type
          never aborts, and the spec must keep admitting it.
      This boundary is the one an earlier revision of the batteries never
      supplied — the case list was str/int/float only — which is why an
      unconditional totality claim went unnoticed.

  (A-reference, model.py `deferrals_run` / `run_deferral` — the EFFECT LEDGER)
      running an entry's deferred computation is an EFFECT, not a free read: it
      raises exactly one advisory notice per run, and it is the only way to
      obtain the entry's value. Checked, on the real callees:
        * CONSTRUCTING either entry raises NO advisory notice — the ledger is
          untouched by construction (`wrap_resolvable` / `wrap_opaque` touch no
          ledger; model.py obligation (3) is satisfiable at all);
        * each resolution of either entry that RUNS the deferred computation
          raises EXACTLY ONE notice, and repeated resolutions of the
          binder-resolvable entry raise one EACH (that construction re-runs its
          closure per access), which is the
          `deferrals_run(n) -> deferrals_run(n + 1)` step of `run_deferral` —
          the ledger counts runs, not accesses, so an entry that keeps the
          object it produced simply performs no further run;
        * resolving through the type-directed binder likewise raises exactly one
          notice, so binder resolution is a deferral run and not a side channel
          around the ledger;
        * the notice is escalatable: under a filter that turns it into an error,
          CONSTRUCTION still succeeds while RESOLUTION raises — which is why
          running a deferral during construction is observably wrong, and why
          model.py requires the ledger back at its entry count.
      Both constructions agree on all of this: the deferral-preservation
      obligation is a property the pre-change code ALSO had, so it is a
      preservation claim, not the patch's delta.

The binder discriminator is binder-resolvability, NOT the entry's surface
`type()`: the real `lazy(..., type(value))()` proxy's own `type()` is `__proxy__`
(it is NOT an instance of `type(value)`), and the SAME resolution succeeds for
ANY result class (`object`, `int`, `str`) — so the property the F2P test observes
is "the binder can cast this Promise to the value at its real type", not
"`type(entry) == type(value)`". This check pins exactly that property.

Imports only `django.utils.functional`, `django.db.models.fields`,
`django.utils.deprecation`, and the standard library; nothing test-specific.
Exit 0 iff every obligation holds.
"""
import sys
import warnings


def _ensure_django_configured():
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=True)
    import django
    django.setup()


def main():
    _ensure_django_configured()

    from django.utils.functional import lazy, SimpleLazyObject, Promise
    from django.db.models.fields import CharField, IntegerField, FloatField
    from django.utils.deprecation import RemovedInDjango40Warning

    def make_access_value(value):
        """Mirror the closure the changed function builds: a callable that raises
        the advisory notice about the entry AND returns the captured value. The
        notice is NOT silenced here — it is the effect the ledger models."""
        def access_value(value=value):
            warnings.warn(
                'passing URL kwargs to the context is deprecated; reference '
                'this key through the view instead',
                RemovedInDjango40Warning, stacklevel=2,
            )
            return value
        return access_value

    def notices(fn):
        """Run fn, returning (result_or_exception, number_of_advisory_notices)."""
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            try:
                out = ("ok", fn())
            except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
                out = ("raise", exc)
        n = sum(1 for r in rec
                if issubclass(r.category, RemovedInDjango40Warning))
        return out, n

    def resolvable_entry(value):
        """The post-change construction: lazy(access_value, type(value))()."""
        return lazy(make_access_value(value), type(value))()

    def opaque_entry(value):
        """The pre-change construction: SimpleLazyObject(access_value)."""
        return SimpleLazyObject(make_access_value(value))

    def binder_resolves(field, entry):
        """The type-directed parameter binder's resolution step:
        Field.get_prep_value casts a Promise via isinstance(value, Promise) ->
        value._proxy____cast(). Returns (ok, resolved, n_notices); ok=False (and
        resolved=None) when the binder rejects the entry (raises, or leaves it an
        unresolved deferred stand-in the DB layer cannot bind)."""
        (kind, out), n = notices(lambda: field.get_prep_value(entry))
        if kind == "raise":
            return False, None, n
        resolved = out
        # The binder must yield a concrete, non-deferred value. An entry the
        # binder did NOT resolve stays a deferred stand-in (a Promise or a
        # SimpleLazyObject) and is rejected downstream as an unsupported type.
        if isinstance(resolved, Promise) or type(resolved).__name__ == "SimpleLazyObject":
            return False, None, n
        return True, resolved, n

    # Representative values across CharField / IntegerField / FloatField (D3:
    # the A-reference witness covers more than just str), including the F2P case
    # (a str slug 'Rene Magritte').
    cases = [
        ("Rene Magritte", CharField()),   # the F2P str case
        ("offer-slug", CharField()),
        ("", CharField()),
        ("42", CharField()),
        (7, IntegerField()),              # int
        (0, IntegerField()),
        (-3, IntegerField()),
        (3.5, FloatField()),              # float
    ]

    for value, field in cases:
        # --- A-reference deferrals_run: CONSTRUCTING either entry runs NO
        #     deferred computation, so it raises NO advisory notice and leaves
        #     the ledger at its entry count. This is what makes model.py's
        #     obligation (3) (deferrals_run back at 0) satisfiable at all, and it
        #     holds for BOTH constructions -> a preservation property, not the
        #     patch delta. --------------------------------------------------
        (kind_post, post), n_build_post = notices(lambda v=value: resolvable_entry(v))
        assert kind_post == "ok", (
            "post-change construction raised for %r: %r" % (value, post))
        assert n_build_post == 0, (
            "post-change CONSTRUCTION for %r raised %d advisory notice(s); the "
            "model says construction runs no deferred computation and leaves the "
            "ledger untouched" % (value, n_build_post))

        (kind_pre, pre), n_build_pre = notices(lambda v=value: opaque_entry(v))
        assert kind_pre == "ok", (
            "pre-change construction raised for %r: %r" % (value, pre))
        assert n_build_pre == 0, (
            "pre-change CONSTRUCTION for %r raised %d advisory notice(s); "
            "deferral-preservation must hold for the pre-change construction "
            "too (it is a preservation property, not the delta)"
            % (value, n_build_pre))

        # --- shared facet 1 (resolves_to): BOTH entries resolve to the
        #     original value through ordinary access, and each such resolution
        #     RUNS the deferred computation, raising EXACTLY ONE notice — the
        #     deferrals_run(n) -> deferrals_run(n + 1) step of run_deferral. --
        (k, eq_post), n_res_post = notices(lambda: post == value)
        assert k == "ok" and eq_post, (
            "post-change entry does not resolve to original value %r" % (value,))
        assert n_res_post == 1, (
            "resolving the post-change entry for %r raised %d advisory "
            "notice(s), expected exactly 1 (run_deferral advances the ledger by "
            "one per run)" % (value, n_res_post))

        (k, eq_pre), n_res_pre = notices(lambda: pre == value)
        assert k == "ok" and eq_pre, (
            "pre-change entry does not resolve to original value %r" % (value,))
        assert n_res_pre == 1, (
            "resolving the pre-change entry for %r raised %d advisory "
            "notice(s), expected exactly 1" % (value, n_res_pre))

        # Repeated resolution raises one notice EACH (no memoisation): the ledger
        # is monotone in the number of runs, which is why a run performed during
        # construction can never be undone.
        fresh = resolvable_entry(value)
        for i in range(3):
            (k, eq), n_i = notices(lambda f=fresh: f == value)
            assert k == "ok" and eq, (
                "post-change entry for %r stopped resolving on run %d"
                % (value, i))
            assert n_i == 1, (
                "run %d of the deferred computation for %r raised %d notice(s), "
                "expected exactly 1 each time (results are not memoised, so the "
                "ledger strictly increases per run)" % (i, value, n_i))

        # --- A-reference wrap_resolvable / binder_castable: the type-directed
        #     binder RESOLVES the post-change entry to the value at its OWN
        #     real runtime type (grants the binder_castable capability) --------
        assert isinstance(post, Promise), (
            "post-change entry for %r is not binder-resolvable (not a Promise; "
            "the binder's cast hook is absent)" % (value,))
        ok_post, resolved_post, n_bind_post = binder_resolves(field, post)
        assert ok_post, (
            "type-directed binder did NOT resolve the post-change entry for %r "
            "(model: binder_castable granted)" % (value,))
        # cast_to == value AND cast_t == type_of(value): resolution yields the
        # original value at the value's OWN real runtime type.
        assert resolved_post == value, (
            "binder resolved post-change entry for %r to a different value %r"
            % (value, resolved_post))
        assert type(resolved_post) is type(value), (
            "binder resolved post-change entry for %r to the wrong runtime type "
            "%r (model: cast_t == type_of(value) == %r)"
            % (value, type(resolved_post), type(value)))
        # Binder resolution IS a deferral run: it raises exactly one notice, so
        # it is not a side channel that reads the value off the ledger's books.
        assert n_bind_post == 1, (
            "binder resolution of the post-change entry for %r raised %d "
            "advisory notice(s), expected exactly 1 (binder resolution runs the "
            "deferred computation and so advances the ledger)"
            % (value, n_bind_post))

        # --- A-reference wrap_opaque: the pre-change entry is NOT a Promise,
        #     so the type-directed binder does NOT resolve it (does NOT grant the
        #     binder_castable capability) — the bug ---------------------------
        assert not isinstance(pre, Promise), (
            "pre-change entry for %r is unexpectedly a Promise" % (value,))
        ok_pre, _, _ = binder_resolves(field, pre)
        assert not ok_pre, (
            "type-directed binder UNEXPECTEDLY resolved the pre-change opaque "
            "entry for %r (it must reject it as an unsupported type)" % (value,))

    # --- A-reference deferrals_run, ESCALATION: the advisory notice is
    #     escalatable to an error by the caller's configuration. Under such a
    #     configuration CONSTRUCTION still succeeds while RESOLUTION raises. That
    #     asymmetry is exactly why running a deferred computation during
    #     construction is observably wrong (it would abort the assembly before
    #     any entry exists), and why model.py requires the ledger back at its
    #     entry count. Holds for BOTH constructions. --------------------------
    for build in (resolvable_entry, opaque_entry):
        with warnings.catch_warnings():
            warnings.simplefilter("error", RemovedInDjango40Warning)
            try:
                entry = build("Rene Magritte")
            except RemovedInDjango40Warning as exc:  # pragma: no cover
                raise AssertionError(
                    "CONSTRUCTION raised the escalated advisory notice (%r); the "
                    "model says construction runs no deferred computation, so it "
                    "must survive an escalating configuration" % (exc,))
            raised = False
            try:
                str(entry)
            except RemovedInDjango40Warning:
                raised = True
            assert raised, (
                "RESOLUTION did not raise under an escalating configuration; the "
                "advisory notice the ledger models is then not observable and "
                "deferral timing would be unobservable")

    # --- alternative-fix admission (G-EQ companion, the verdict's mandated
    #     external-resolver probe): correct fixes that declare a DIFFERENT result
    #     class still produce a binder-resolvable Promise that resolves to the
    #     value at its OWN real type, and still run no deferred computation at
    #     construction time. The discriminators must ADMIT them (they are
    #     wrap_resolvable / grant binder_castable and preserve the ledger),
    #     confirming the spec pins binder-resolvability + deferral preservation,
    #     NOT `type(entry) == type(value)` and NOT the gold's exact result class.
    cf = CharField()
    for rc in (object, int, str):
        (kind, alt), n_build_alt = notices(
            lambda r=rc: lazy(make_access_value("Rene Magritte"), r)())
        assert kind == "ok", (
            "alternative-fix lazy(..., %s)() raised at construction: %r"
            % (rc.__name__, alt))
        assert n_build_alt == 0, (
            "alternative-fix lazy(..., %s)() raised %d advisory notice(s) at "
            "CONSTRUCTION; a correct alternative must also preserve the deferral"
            % (rc.__name__, n_build_alt))
        assert isinstance(alt, Promise), (
            "alternative-fix lazy(..., %s)() is not a Promise" % (rc.__name__,))
        ok_alt, resolved_alt, n_bind_alt = binder_resolves(cf, alt)
        assert ok_alt and resolved_alt == "Rene Magritte" and type(resolved_alt) is str, (
            "alternative-fix lazy(..., %s)() is NOT admitted by the binder-"
            "resolvability discriminator (spec wrongly pins the surface type)"
            % (rc.__name__,))
        assert n_bind_alt == 1, (
            "alternative-fix lazy(..., %s)(): binder resolution raised %d "
            "notice(s), expected exactly 1" % (rc.__name__, n_bind_alt))
        # And the surface type of the proxy is NOT the value's type — proving the
        # OLD `type(entry) == type(value)` discriminator was drift.
        assert type(alt) is not str, (
            "lazy proxy surface type unexpectedly equals the value type")

    # --- A-reference own_type_unpreparable: THE PARTIALITY BOUNDARY -----------------
    #     model.py contracts the post-change construction as PARTIAL, permitted
    #     to abort exactly on values that are themselves types. Check both
    #     directions on the real callee, so neither an over-claim (promising an
    #     entry where there is none) nor an under-claim (permitting an abort where
    #     the real construction always succeeds) can hide.
    class _Meta(type):
        pass

    class _WithMeta(metaclass=_Meta):
        pass

    class _Plain:
        pass

    import abc as _abc
    import enum as _enum

    # --- members of own_type_unpreparable that are NOT types --------------------
    # Route (i): the value's own class shadows `mro` with something that is not a
    # zero-argument ancestor-yielding callable, so functional.py:111 raises.
    class _MroData:
        mro = 42

    class _MroOneArg:
        def mro(self, x):
            return []

    class _MroProp:
        @property
        def mro(self):
            return []

    # Route (ii): the value's METACLASS misreports the delegate comparisons at
    # functional.py:120-123, which run `bytes in resultclasses` / `str in
    # resultclasses` against `type(value)`.
    class _MetaEqBoom(type):
        def __eq__(cls, other):
            raise RuntimeError("metaclass __eq__ boom")

        def __hash__(cls):
            return id(cls)

    class _EqBoom(metaclass=_MetaEqBoom):
        pass

    class _MetaEqAll(type):
        def __eq__(cls, other):
            return True

        def __hash__(cls):
            return id(cls)

    class _EqAll(metaclass=_MetaEqAll):
        pass

    class _MetaEqBytes(type):
        def __eq__(cls, other):
            return other is bytes

        def __hash__(cls):
            return id(cls)

    class _EqBytesOnly(metaclass=_MetaEqBytes):
        pass

    # The same route-(ii) arm, but with a value that CAN be turned into bytes:
    # the arm's post-processing therefore SUCCEEDS and hands back a well-formed
    # object of a different type, with no exception and no extra notice. This is
    # the witness that forces the resolution-value clause to be guarded rather
    # than unconditional: on it, resolution silently does not round-trip.
    # It is parameterised by a per-instance width so that two members of the
    # SAME shape, differing only in the value the entry was built around, can be
    # compared: that is the provenance measurement for `deferral_of` below.
    class _IntBytesArm(metaclass=_MetaEqBytes):
        def __init__(self, width=5):
            self.width = width

        def __index__(self):
            return self.width

    type_valued = [int, str, object, type, bool, tuple, dict, BaseException,
                   _Plain, _WithMeta, _Meta, _abc.ABC, _enum.Enum]
    # Non-type values that are nonetheless in own_type_unpreparable and on which
    # the construction ABORTS: route (i) via a shadowed `mro`, route (ii) via a
    # metaclass __eq__ that raises or reports both delegate arms. These are the
    # members whose absence from this list let an earlier revision claim the
    # family was exactly `isinstance(value, type)`.
    unpreparable_non_type_abort = [_MroData(), _MroOneArg(), _MroProp(),
                                   _EqBoom(), _EqAll()]
    # The route-(ii) bytes-arm member: the construction SUCCEEDS and the entry is
    # Promise-recognised by the binder, but resolving it does NOT yield the value
    # (functional.py:142-143 returns bytes(func(...))). This is why the spec
    # grants binder_accepts unconditionally and binder_castable only OFF the
    # family, rather than treating "unpreparable" as "the build aborts".
    unpreparable_non_type_no_abort = [_EqBytesOnly()]
    # The SILENT sub-shape of the same family: the build succeeds, the binder
    # recognises the entry, resolution succeeds too -- and yields an object that
    # is neither the value nor of the value's type, with 0 extra notices. Nothing
    # raises anywhere, so ONLY a guarded resolution-value clause is faithful here.
    unpreparable_non_type_silent = [_IntBytesArm()]
    not_type_valued = ["Rene Magritte", "", 7, 0, -3, 3.5, 0.0, None, True,
                       b"ab", (1, 2), [1], {"a": 1}, _Plain(), _WithMeta(),
                       object(), _enum.Enum, len]
    # `_enum.Enum` is a type, so keep it only in the type-valued list.
    not_type_valued = [v for v in not_type_valued if not isinstance(v, type)]

    for value in type_valued:
        assert isinstance(value, type), (
            "test-list error: %r is not a type" % (value,))
        (kind, out), n_abort = notices(lambda v=value: resolvable_entry(v))
        assert kind == "raise", (
            "post-change construction UNEXPECTEDLY produced an entry for the "
            "type-valued input %r; model.py permits an exceptional exit there, "
            "which would be an under-claim if the construction always succeeded"
            % (value,))
        assert n_abort == 0, (
            "post-change construction for the type-valued input %r raised %d "
            "advisory notice(s) on the way out; model.py requires the ledger "
            "back at its entry count on the ABORTING exit too" % (value, n_abort))
        # The PRE-change construction is TOTAL here: it advertises no per-value
        # type. This is why the partiality is PERMITTED, never REQUIRED.
        (kind_pre_t, pre_t), n_pre_t = notices(lambda v=value: opaque_entry(v))
        assert kind_pre_t == "ok" and n_pre_t == 0, (
            "pre-change construction unexpectedly failed for the type-valued "
            "input %r (%r); the permitted-not-required framing of the partiality "
            "depends on a per-value-type-free construction being total"
            % (value, pre_t))

    for value in not_type_valued:
        assert not isinstance(value, type)
        (kind, out), _ = notices(lambda v=value: resolvable_entry(v))
        assert kind == "ok", (
            "the hook-exposing construction RAISED for the ordinary value %r "
            "(%r); outside own_type_unpreparable it must return an entry, or "
            "model.py's partiality clause would be too permissive" % (value, out))
        # ... and OFF the family, resolution really does hand the value back
        # unchanged at its own real type, which is what licenses the UNGUARDED
        # binder_castable clause there.
        ent = resolvable_entry(value)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            resolved = ent._proxy____cast()
        assert resolved is value or resolved == value, (
            "off the unpreparable family the entry for %r resolved to %r, not the "
            "original value; the unguarded binder_castable clause would be an "
            "over-claim" % (value, resolved))

    # --- own_type_unpreparable contains NON-TYPE values, on BOTH routes --------
    #     The family model.py names is strictly wider than `isinstance(value, type)`.
    #     Route (i)/(ii)-raising members: the construction aborts, ledger preserved.
    for value in unpreparable_non_type_abort:
        assert not isinstance(value, type), (
            "test-list error: %r is a type" % (value,))
        (kind, out), n_abort = notices(lambda v=value: resolvable_entry(v))
        assert kind == "raise", (
            "the hook-exposing construction unexpectedly SUCCEEDED for the "
            "non-type unpreparable value %r; own_type_unpreparable is supposed to "
            "contain it, so model.py's Exsures guard would be unreachable there"
            % (value,))
        assert n_abort == 0, (
            "the aborting build for %r raised %d advisory notice(s) on the way "
            "out; model.py requires the ledger back at its entry count on the "
            "ABORTING exit too" % (value, n_abort))
        # the hookless construction is TOTAL and faithful here, which is what
        # keeps the abort PERMITTED rather than REQUIRED.
        (kind_pre, pre_e), n_pre = notices(lambda v=value: opaque_entry(v))
        assert kind_pre == "ok" and n_pre == 0, (
            "the hookless construction unexpectedly failed for %r (%r); the "
            "permitted-not-required framing depends on it being total"
            % (value, pre_e))

    #     Route (ii) bytes-arm member: the build SUCCEEDS, the binder RECOGNISES
    #     the entry (it is a Promise, so binder_accepts is granted here too), and
    #     resolution then does NOT yield the value. This is the member that makes
    #     an unguarded binder_castable clause unfaithful, and it is the reason
    #     "unpreparable" is not a synonym for "the build aborts".
    for value in unpreparable_non_type_no_abort:
        assert not isinstance(value, type)
        (kind, ent), n_build = notices(lambda v=value: resolvable_entry(v))
        assert kind == "ok", (
            "expected the bytes-arm member %r to BUILD successfully (%r)"
            % (value, ent))
        assert n_build == 0, (
            "building the bytes-arm entry for %r raised %d notice(s)"
            % (value, n_build))
        assert isinstance(ent, Promise), (
            "the bytes-arm entry for %r is not a Promise, so the binder would "
            "not recognise it and model.py's unconditional binder_accepts clause "
            "would be an over-claim" % (value,))
        (rkind, robj), n_res = notices(lambda e=ent: e._proxy____cast())
        assert rkind == "raise", (
            "resolving the bytes-arm entry for %r unexpectedly succeeded (%r); "
            "the guard on model.py's binder_castable clause is justified by this "
            "resolution NOT yielding the value" % (value, robj))
        assert type(ent)._delegate_bytes and not type(ent)._delegate_text, (
            "the bytes-arm member %r did not actually select the bytes delegate "
            "arm, so it does not exercise route (ii)" % (value,))

    #     THE SILENT sub-shape, and the reason model.py's resolution-value clause
    #     (1) is GUARDED and not unconditional. Here EVERY step succeeds -- build,
    #     binder recognition, resolution -- and the resolution still does not
    #     reproduce the value: it hands back a well-formed object of a different
    #     type, with no exception and no extra advisory notice. An earlier revision
    #     asserted this family only in its RAISING shape, which is precisely how an
    #     unconditional clause (1) survived: a clause that promised resolution
    #     round-trips on the whole domain predicted an outcome the real callee does
    #     not produce, and did so where nothing observable goes wrong.
    for value in unpreparable_non_type_silent:
        assert not isinstance(value, type)
        (kind, ent), n_build = notices(lambda v=value: resolvable_entry(v))
        assert kind == "ok", (
            "expected the silent bytes-arm member %r to BUILD successfully (%r)"
            % (value, ent))
        assert n_build == 0, (
            "building the silent bytes-arm entry for %r raised %d notice(s)"
            % (value, n_build))
        assert isinstance(ent, Promise), (
            "the silent bytes-arm entry for %r is not a Promise, so it would not "
            "witness binder recognition on this family" % (value,))
        assert type(ent)._delegate_bytes and not type(ent)._delegate_text, (
            "the silent member %r did not select the bytes delegate arm, so it "
            "does not exercise route (ii)" % (value,))
        (rkind, robj), n_res = notices(lambda e=ent: e._proxy____cast())
        assert rkind == "ok", (
            "expected resolution of the silent bytes-arm entry for %r to SUCCEED "
            "(%r); the whole point of this witness is that nothing raises"
            % (value, robj))
        assert n_res == 1, (
            "resolving the silent bytes-arm entry for %r raised %d advisory "
            "notice(s), expected exactly 1: the divergence is silent, it does not "
            "announce itself with an extra notice" % (value, n_res))
        assert not (robj is value or robj == value), (
            "resolution of the silent bytes-arm entry for %r DID round-trip to "
            "the value (%r); this witness no longer refutes an unconditional "
            "clause (1) and the guard on it would be unjustified" % (value, robj))
        assert type(robj) is not type(value), (
            "resolution of the silent bytes-arm entry for %r kept the value's own "
            "type (%r); the arm is supposed to hand back a different type"
            % (value, type(robj)))
        # And the binder happily accepts that non-round-tripping resolution: the
        # divergence reaches a consumer, it is not confined to a direct cast.
        ok_b, resolved_b, n_b = binder_resolves(CharField(), ent)
        assert ok_b, (
            "the binder REFUSED the silent bytes-arm entry for %r; the "
            "unconditional binder_accepts clause needs it to be recognised"
            % (value,))
        assert not (resolved_b is value or resolved_b == value), (
            "the binder resolved the silent bytes-arm entry for %r back to the "
            "value (%r); then clause (1) would hold after all" % (value, resolved_b))
        # the hookless construction is total AND faithful on this value too, so
        # the divergence is introduced by the per-value consultation, not inherent.
        (kp, pre_e), n_p = notices(lambda v=value: opaque_entry(v))
        assert kp == "ok" and n_p == 0, (
            "the hookless construction failed for %r (%r)" % (value, pre_e))
        # --- A-reference deferral_of: PROVENANCE, and why it stays UNCONDITIONAL
        #     model.py splits facet (1) into a round-trip half, guarded here, and
        #     a provenance half that holds on the WHOLE domain: the entry carries
        #     the deferred computation captured for THIS value, so what running it
        #     hands back is determined by this value and by nothing else. This is
        #     the family where that distinction has to be earned, because the
        #     round-trip is gone. Measured: what resolution hands back is DERIVED
        #     from this value (its width is the width this value reports), and a
        #     second member of the SAME shape built around a different value
        #     resolves to a correspondingly different object -- so an entry built
        #     around some other value is observably not interchangeable, which is
        #     what the unconditional provenance clause forbids.
        assert len(robj) == value.width, (
            "resolution of the silent bytes-arm entry for %r handed back %r, "
            "which is not derived from this value's own width %d; then the entry "
            "would not be carrying THIS value's deferred computation and the "
            "unconditional provenance clause would be an over-claim"
            % (value, robj, value.width))
        other = _IntBytesArm(width=value.width + 2)
        (okind2, ent2), n_b2 = notices(lambda v=other: resolvable_entry(v))
        assert okind2 == "ok" and n_b2 == 0, (
            "building the entry for the second silent member %r failed (%r)"
            % (other, ent2))
        (rkind2, robj2), n_res2 = notices(lambda e=ent2: e._proxy____cast())
        assert rkind2 == "ok" and len(robj2) == other.width and robj2 != robj, (
            "the entry built around a DIFFERENT value of the same shape resolved "
            "to %r, which is not distinguishable from %r; provenance would then "
            "be unobservable on this family" % (robj2, robj))

    print("G-AX OK: type_of + wrap_resolvable/wrap_opaque + binder_accepts + "
          "binder_castable + run_deferral/deferrals_run/resolves_to/deferral_of/"
          "own_type_unpreparable deep models "
          "sound against "
          "real django.utils.functional.lazy / SimpleLazyObject, "
          "Field.get_prep_value and the real advisory-notice effect on %d values "
          "across CharField/IntegerField/FloatField (incl. F2P str 'Rene "
          "Magritte'): the type-directed binder resolves the post-change Promise "
          "entry to the value at its OWN real type (grants binder_castable) and "
          "rejects the pre-change non-Promise entry (no capability); CONSTRUCTING "
          "either entry runs no deferred computation (raises 0 notices, survives "
          "an escalating configuration) while EACH resolution that runs it costs "
          "exactly 1 notice (repeats of the binder-resolvable entry re-run per "
          "access; binder resolution is itself a run), so "
          "the ledger faithfully models the effect and deferral-preservation is a "
          "property both images share; alternative result classes "
          "(object/int/str) are admitted on both discriminators; and the "
          "PARTIALITY boundary is exercised on BOTH preparation routes -- the "
          "hook-exposing "
          "construction raises for all %d type-valued inputs and for %d NON-TYPE "
          "unpreparable inputs (mro-shadowing and metaclass-__eq__ ones), always "
          "raising 0 notices on the way out so the ledger is preserved on the "
          "aborting exit; it returns an entry that resolves BACK to the original "
          "value for all %d ordinary inputs (licensing the unguarded "
          "binder_castable clause there); and on the bytes-arm member the build "
          "SUCCEEDS, the entry is Promise-recognised, and resolution does NOT "
          "yield the value -- which is exactly why binder_accepts is "
          "unconditional while binder_castable and the resolution-value clause "
          "are guarded; on the %d SILENT member(s) of that family every step "
          "succeeds (build, recognition, resolution, and the binder's own "
          "resolution) with exactly one notice and no exception, and the value "
          "still does not come back, which is what an unconditional "
          "resolution-value clause would have wrongly predicted -- while what "
          "does come back is DERIVED from that same value and a member of the "
          "same shape built around a different value resolves differently, which "
          "is what licenses keeping the PROVENANCE half (deferral_of) "
          "unconditional there. The hookless "
          "construction is total on all of them (so the abort is PERMITTED, "
          "never REQUIRED)."
          % (len(cases), len(type_valued), len(unpreparable_non_type_abort),
             len(not_type_valued), len(unpreparable_non_type_silent)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
