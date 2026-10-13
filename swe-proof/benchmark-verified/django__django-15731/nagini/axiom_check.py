#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15731.

Executes the REAL standard-library introspection callees (`inspect.signature`,
`functools.wraps`) on inputs (boundary signatures + randomized fuzz) and
asserts that every observation matches the model, as encoded in model.py.

The single consumed axiom is `reported_signature(wrapped, target_sig)` in
model.py's axioms region -- the unchanged signature resolver:

    reported_signature(wrapped, target_sig)
        == target_sig        when wrapped   (the recorded original's signature)
        == SIG_FORWARDING()  otherwise      (the proxy's own forwarding sig)

We model SIG_FORWARDING() as the signature of a forwarding callable
`def f(self, *args, **kwargs)` -- exactly the body of Django's `manager_method`.
The real-callee soundness obligation, in concrete terms:

  (i)  if a proxy records the source it stands in for (the `__wrapped__`
       attribute, which `functools.wraps` sets), `inspect.signature(proxy)`
       reports the SOURCE's declared signature, not the forwarding one; and
  (ii) if a proxy records nothing (only `__name__`/`__doc__` copied, as the
       pre-fix code did), `inspect.signature(proxy)` reports the proxy's own
       forwarding signature.

We also validate the end-to-end faithfulness used by the F2P test: building the
proxy with the REAL `functools.wraps(source)` (the gold patch's mechanism) makes
`inspect.signature(proxy)` equal `inspect.signature(source)`, while the pre-fix
manual `__name__`/`__doc__` copy does not.

Imports nothing repo-specific: `inspect`/`functools` are the Python standard
library -- the same modules the F2P test and the gold patch use. Exit 0 iff
every obligation holds.
"""
import functools
import inspect
import random
import sys


def forwarding_proxy():
    """A bare forwarding callable identical in shape to Django's
    `manager_method(self, *args, **kwargs)`."""
    def manager_method(self, *args, **kwargs):
        return None
    return manager_method


def make_source(params):
    """Build a source callable with the given parameter spec string, e.g.
    "objs, batch_size=None, ignore_conflicts=False". Returns the function."""
    src_code = "def _src(%s):\n    return None\n" % (params,)
    ns = {}  # type: dict
    exec(src_code, ns)
    f = ns["_src"]
    f.__name__ = "proxied_method"
    f.__doc__ = "the source docstring"
    return f


def sig_str(f):
    return str(inspect.signature(f))


# The proxy's own forwarding signature -- SIG_FORWARDING() in the model.
SIG_FORWARDING = sig_str(forwarding_proxy())


def build_proxy_real(source):
    """The gold-patch mechanism: a forwarding proxy decorated with the REAL
    functools.wraps(source) (records __wrapped__ = source)."""
    @functools.wraps(source)
    def manager_method(self, *args, **kwargs):
        return getattr(source, "whatever", None)
    return manager_method


def build_proxy_prefix(source):
    """The pre-fix mechanism: a forwarding proxy with only __name__/__doc__
    manually copied (no __wrapped__ recorded)."""
    def manager_method(self, *args, **kwargs):
        return None
    manager_method.__name__ = source.__name__
    manager_method.__doc__ = source.__doc__
    return manager_method


def check_axiom_wrapped(source):
    """(i) wrapped == True: inspect.signature reports the source's signature
    (== target_sig), not the forwarding signature."""
    proxy = build_proxy_real(source)
    # functools.wraps must have recorded the original callable.
    assert getattr(proxy, "__wrapped__", None) is source, (
        "functools.wraps did not record __wrapped__ for %r" % source)
    observed = sig_str(proxy)                 # real inspect.signature, wrapped
    target_sig = sig_str(source)              # the recorded original's sig
    assert observed == target_sig, (
        "axiom unsound (wrapped branch): inspect.signature reported %r, "
        "axiom requires the recorded target signature %r"
        % (observed, target_sig))
    # And the F2P observable: the proxy's reported signature is NOT the bare
    # forwarding one, exactly when the source's own signature differs from it.
    if target_sig != SIG_FORWARDING:
        assert observed != SIG_FORWARDING, (
            "wrapped proxy still reported the forwarding signature for %r"
            % source)


def check_axiom_unwrapped(source):
    """(ii) wrapped == False: inspect.signature reports the proxy's own
    forwarding signature (== SIG_FORWARDING())."""
    proxy = build_proxy_prefix(source)
    assert not hasattr(proxy, "__wrapped__"), (
        "pre-fix proxy unexpectedly recorded __wrapped__")
    observed = sig_str(proxy)                 # real inspect.signature, unwrapped
    assert observed == SIG_FORWARDING, (
        "axiom unsound (unwrapped branch): inspect.signature reported %r, "
        "axiom requires the forwarding signature %r"
        % (observed, SIG_FORWARDING))
    # name/doc are still copied in BOTH worlds (P2P test_manager_method_attributes)
    assert proxy.__name__ == source.__name__
    assert proxy.__doc__ == source.__doc__


def main():
    # --- boundary signatures (incl. the exact bulk_create one from the F2P) --
    boundary = [
        "self, *args, **kwargs",                      # == SIG_FORWARDING shape
        "",                                           # zero-arg
        "self",
        "objs, batch_size=None, ignore_conflicts=False",
        ("objs, batch_size=None, ignore_conflicts=False, "
         "update_conflicts=False, update_fields=None, unique_fields=None"),
        "a, b, c",
        "a, b=1, *c, d, **e",
        "*args",
        "**kwargs",
        "x, /, y, *, z",
        "a=1, b=2, c=3",
    ]
    for params in boundary:
        source = make_source(params)
        check_axiom_wrapped(source)
        check_axiom_unwrapped(source)

    # --- end-to-end faithfulness: real functools.wraps vs the pre-fix copy ---
    for params in boundary:
        source = make_source(params)
        proxy_fixed = build_proxy_real(source)
        proxy_pre = build_proxy_prefix(source)
        # The gold mechanism makes the proxy's signature equal the source's.
        assert sig_str(proxy_fixed) == sig_str(source), (
            "gold mechanism failed faithfulness for %r" % params)
        # The pre-fix mechanism reports the forwarding signature instead --
        # wrong exactly when the source's signature differs.
        if sig_str(source) != SIG_FORWARDING:
            assert sig_str(proxy_pre) != sig_str(source), (
                "pre-fix mechanism unexpectedly faithful for %r" % params)

    # --- randomized fuzz over parameter lists --------------------------------
    rng = random.Random(15731)
    names = ["a", "b", "c", "d", "e", "f", "g", "h", "objs", "size", "flag"]
    for _ in range(5000):
        n = rng.randint(0, 5)
        chosen = rng.sample(names, n) if n <= len(names) else names
        parts = []
        for nm in chosen:
            if rng.random() < 0.4:
                parts.append("%s=None" % nm)
            else:
                parts.append(nm)
        if rng.random() < 0.3:
            parts.append("*args")
        if rng.random() < 0.3:
            parts.append("**kwargs")
        params = ", ".join(parts)
        try:
            source = make_source(params)
        except SyntaxError:
            continue
        check_axiom_wrapped(source)
        check_axiom_unwrapped(source)

    print("G-AX OK: reported_signature axiom sound -- inspect.signature follows "
          "the recorded original (functools.wraps' __wrapped__) when present and "
          "falls back to the forwarding signature otherwise, over %d boundary + "
          "5000 fuzz parameter lists." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
