#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15916.

This bundle consumes NO `@ContractOnly` axiom: the behaviour under change is a
pure attribute-resolution / data-flow change, modelled DEEPLY over integer
identity codes by `resolve_attr` (model.py pure region). The one thing that
deep model stands in for is the real-Python attribute-resolution semantics the
patched code relies on:

  * an options object reading its builder via `getattr(meta, "attr", None)`
    where `meta` is a `type(...)` whose bases supply the inherited value;
  * the run-time factory creating that options `type` with the passed builder
    set on it (as a `staticmethod`) only when one was given, and -- crucially,
    post-fix -- NOT injecting an overriding class-level attribute on the form;
  * the constructor selecting the builder straight from the resolved options
    attribute.

This A-reference check executes the REAL Python object model (type creation,
MRO attribute lookup, `getattr` with default, `staticmethod`) and asserts that
the integer deep model `resolve_attr` agrees with the genuine resolution on:

  (1) the two FAIL_TO_PASS scenarios (callback declared in own Meta; callback
      inherited from a base form's Meta via the factory, plus a further
      subclass); and
  (2) randomized fuzz over presence/absence of builders at each level.

The widget-type observation the tests make (Textarea vs the model default) is
exactly "which builder drove field construction", which is the resolved builder
identity this check pins. stdlib-only; exit 0 iff sound.
"""
import random
import sys


# --- model.py reference encoding (kept in lock-step with the pure region) ----

def resolve_attr(own, inherited):
    """Reference of model.py's deep model `resolve_attr` (0 == absent)."""
    return own if own != 0 else inherited


def declared_form_callback_model(meta_own, meta_inherited):
    """model.py declared_form_callback impl, on integer codes."""
    return resolve_attr(meta_own, meta_inherited)


def factory_form_callback_model(passed, base_meta_own, base_meta_inherited):
    """model.py factory_form_callback impl, on integer codes."""
    produced_inherited = resolve_attr(base_meta_own, base_meta_inherited)
    produced_own = passed
    return resolve_attr(produced_own, produced_inherited)


# --- the REAL Python object-model resolution the patched code performs -------

_SENTINEL = object()


def _make_meta(bases, own_cb):
    """Build an options-source `type` mirroring a form's inner Meta. `own_cb`
    is the builder declared directly on this Meta (None == not declared);
    `bases` are parent Meta types it inherits from."""
    attrs = {}
    if own_cb is not None:
        # Django stores it directly on Meta (and the factory wraps with
        # staticmethod); attribute *value* identity is what resolution sees.
        attrs["formfield_callback"] = staticmethod(own_cb)
    return type("Meta", tuple(bases), attrs)


def _options_stored_callback(meta):
    """ModelFormOptions.__init__ (post-fix): read the builder from the options
    source via ordinary attribute resolution."""
    val = getattr(meta, "formfield_callback", None)
    # unwrap staticmethod descriptor access (type lookup already binds it)
    return val


def _real_declared(meta_own_fn, base_meta_fn):
    """Real resolution for a directly-declared model form whose own Meta may
    carry `meta_own_fn` and inherits from a base form Meta carrying
    `base_meta_fn` (each None == absent)."""
    base_meta = _make_meta([], base_meta_fn)
    meta = _make_meta([base_meta], meta_own_fn)
    return _options_stored_callback(meta)


def _real_factory(passed_fn, base_meta_own_fn, base_meta_inherited_fn):
    """Real resolution for a factory-produced form: the factory builds a Meta
    inheriting the base form's Meta (own + its parent) and sets the passed
    builder on it only when truthy; post-fix it injects NO class-level
    formfield_callback on the produced form. Then a further subclass inherits."""
    base_parent_meta = _make_meta([], base_meta_inherited_fn)
    base_meta = _make_meta([base_parent_meta], base_meta_own_fn)
    # factory: Meta = type("Meta", (form.Meta,), attrs); set passed iff truthy
    produced_meta = _make_meta([base_meta], None)
    if passed_fn:
        produced_meta.formfield_callback = staticmethod(passed_fn)
    produced = _options_stored_callback(produced_meta)
    # a further subclass (InheritedForm) inherits the same Meta -> same builder
    sub_meta = _make_meta([produced_meta], None)
    sub = _options_stored_callback(sub_meta)
    assert produced is sub or (produced is None and sub is None), (
        "subclass resolution diverged: produced=%r sub=%r" % (produced, sub))
    return produced


# --- bridge: integer code <-> real callable identity -------------------------

def _fn_of_code(code, pool):
    """0 -> None (absent); positive code -> the distinct callable pool[code]."""
    return None if code == 0 else pool[code]


def _code_of_fn(fn, pool_inv):
    return 0 if fn is None else pool_inv[id(fn)]


def main():
    # distinct callable identities for codes 1..6
    pool = {i: (lambda *a, **k: i) for i in range(1, 7)}
    pool_inv = {id(f): c for c, f in pool.items()}

    checks = 0

    # --- (1) the two FAIL_TO_PASS scenarios -------------------------------
    # test_custom_callback_in_meta: builder declared only on the form's own
    # Meta (code 1), no base builder. Resolved builder must be code 1
    # (Textarea), NOT 0 (model default).
    real = _real_declared(pool[1], None)
    assert _code_of_fn(real, pool_inv) == 1, "F2P meta: real resolution wrong"
    assert declared_form_callback_model(1, 0) == _code_of_fn(real, pool_inv), \
        "F2P meta: model disagrees with real resolution"
    assert declared_form_callback_model(1, 0) == 1, \
        "F2P meta: builder declared in own Meta must be selected (not 0)"
    checks += 1

    # test_custom_callback_from_base_form_meta: base form's Meta carries the
    # builder (code 2), factory given none, plus a further subclass. Resolved
    # builder must be code 2 for the produced class (and its subclass).
    real = _real_factory(None, pool[2], None)
    assert _code_of_fn(real, pool_inv) == 2, "F2P factory: real resolution wrong"
    assert factory_form_callback_model(0, 2, 0) == _code_of_fn(real, pool_inv), \
        "F2P factory: model disagrees with real resolution"
    assert factory_form_callback_model(0, 2, 0) == 2, \
        "F2P factory: base-Meta builder must survive a no-callback factory call"
    checks += 1

    # --- (2) randomized fuzz over presence/absence at each level ----------
    rng = random.Random(15916)
    for _ in range(20000):
        # declared form: own + inherited (base form class Meta)
        mo = rng.randint(0, 3)
        mi = rng.randint(0, 3)
        real = _real_declared(_fn_of_code(mo, pool), _fn_of_code(mi, pool))
        assert declared_form_callback_model(mo, mi) == _code_of_fn(real, pool_inv), \
            "declared deep model unsound at (own=%d, inh=%d): model=%d real=%d" % (
                mo, mi, declared_form_callback_model(mo, mi),
                _code_of_fn(real, pool_inv))

        # factory form: passed + base own + base inherited
        p = rng.randint(0, 3)
        bo = rng.randint(0, 3)
        bi = rng.randint(0, 3)
        real = _real_factory(_fn_of_code(p, pool), _fn_of_code(bo, pool),
                             _fn_of_code(bi, pool))
        assert factory_form_callback_model(p, bo, bi) == _code_of_fn(real, pool_inv), \
            "factory deep model unsound at (passed=%d, bo=%d, bi=%d): model=%d real=%d" % (
                p, bo, bi, factory_form_callback_model(p, bo, bi),
                _code_of_fn(real, pool_inv))
        checks += 2

    print("G-AX OK: resolve_attr deep model == real Python attribute "
          "resolution on the 2 FAIL_TO_PASS scenarios + %d fuzz resolutions; "
          "no consumed axiom" % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
