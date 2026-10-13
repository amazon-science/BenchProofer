#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15731.

The metadata-propagation operation the gold patch introduces is modeled DEEPLY
in Solution.lean's `pure` region as `propagate`, an A-reference (NOT a consumed
axiom):

    propagate (forwarder target : CallableMeta) : CallableMeta :=
      { name := target.name, doc := target.doc, sig := target.sig }

i.e. when a forwarding wrapper is decorated so it presents as `target` under
introspection, all three observed fields of the wrapper — its introspected name,
its documentation, AND the string form of its call signature — are those of
`target`, regardless of the wrapper's own (generic forwarding) metadata.

This check validates that deep model against the REAL standard facility the gold
patch uses: `functools.wraps`. For a battery of real target callables it builds
the actual forwarding wrapper

    @functools.wraps(target)
    def manager_method(self, *args, **kwargs): ...

and asserts that the real introspected triple of the decorated wrapper

    (wrapper.__name__, wrapper.__doc__ or "", str(inspect.signature(wrapper)))

equals `propagate(forwarder, target)` computed from the TARGET's own introspected
triple. The load-bearing field is `sig`: `inspect.signature` follows the
`__wrapped__` link `functools.wraps` sets, so the wrapper renders the target's
signature, never its own `(*args, **kwargs)`.

Imports only the Python standard library (`functools`, `inspect`) — the same
modules the gold patch calls. Exit 0 iff every obligation holds.
"""
import functools
import inspect
import random
import sys


# --- the introspectable triple (the CallableMeta bijection, mapping.md §2) ---

def observe(c):
    """The three modeled CallableMeta fields of a real callable `c`:
    (name, doc, sig).  `__doc__` of None bridges to "" (mapping.md §2)."""
    return (c.__name__, c.__doc__ or "", str(inspect.signature(c)))


# --- the deep model `propagate` (Solution.lean pure region), transliterated --

def propagate(forwarder_triple, target_triple):
    """propagate(forwarder, target) = all three fields taken from `target`."""
    _ = forwarder_triple  # read-only frame: forwarder fields must NOT survive
    name, doc, sig = target_triple
    return (name, doc, sig)


# --- the real facility: build the actual functools.wraps forwarding wrapper ---

def real_forwarder_meta(target):
    """patch.diff's behaviour: the inner `manager_method` decorated with
    `@functools.wraps(target)` (gold `manager.py:84`), then introspected."""

    @functools.wraps(target)
    def manager_method(self, *args, **kwargs):  # the proxy body (manager.py:84-85)
        return None

    return observe(manager_method)


def raw_forwarder_meta():
    """The wrapper's OWN pre-propagation triple (the `forwarder` input): a plain
    `manager_method(self, *args, **kwargs)` with no metadata conferred."""

    def manager_method(self, *args, **kwargs):
        return None

    return observe(manager_method)


# --- the check ---------------------------------------------------------------

def check(target, label):
    """Validate the `propagate` deep model == the real functools.wraps effect on
    the three observed fields for `target`.  Returns True iff this target is
    *discriminating* — i.e. its propagated signature differs from the generic
    forwarder form, so it actively exercises the __wrapped__-following path that
    the bug is about.  (A target whose genuine signature legitimately coincides
    with `(self, *args, **kwargs)` — e.g. `QuerySet.get`, declared
    `def get(self, *args, **kwargs)` — is still a sound obligation; it simply
    happens not to discriminate.  The non-triviality of the battery is asserted
    globally in `main`, never per-target.)"""
    forwarder_triple = raw_forwarder_meta()
    # sanity: the raw forwarder really does carry the generic forwarding sig.
    assert forwarder_triple[2] == "(self, *args, **kwargs)", (
        "unexpected raw forwarder signature %r" % (forwarder_triple[2],))

    observed = real_forwarder_meta(target)                 # real functools.wraps
    target_triple = observe(target)
    expected = propagate(forwarder_triple, target_triple)  # deep model
    # THE soundness obligation: the deep model equals the real facility's effect
    # on all three observed fields (name, doc, signature).
    assert observed == expected, (
        "propagate deep model unsound for %s: real wraps gave %r, "
        "deep model gives %r" % (label, observed, expected))
    # the discriminating field, stated explicitly: signature must resolve to the
    # target's, not stay an unrelated wrapper signature.
    assert observed[2] == target_triple[2], (
        "signature not propagated for %s: wrapper sig %r != target sig %r"
        % (label, observed[2], target_triple[2]))
    # this target genuinely discriminates the fix iff the propagated signature
    # is NOT the generic forwarder form. Targets like QuerySet.get whose true
    # signature is itself `(self, *args, **kwargs)` are sound but non-
    # discriminating — do NOT fail them (that was the v1 over-strong assertion).
    return observed[2] != forwarder_triple[2]


# --- boundary target callables ------------------------------------------------

def f_noargs():
    """no-arg docstring."""


def f_args_kwargs(*args, **kwargs):
    """variadic docstring."""


def f_defaults(objs, batch_size=None, ignore_conflicts=False):
    """positional + defaults docstring."""


def f_kwonly(a, *, b, c=3):
    """keyword-only docstring."""


def f_posonly(a, b, /, c):
    """positional-only docstring."""


def f_annotated(x: int, y: "str" = "z") -> bool:
    """annotated docstring."""
    return True


def f_nodoc(p, q=1):
    pass  # __doc__ is None -> bridges to ""


def main():
    boundary = [
        (f_noargs, "noargs"),
        (f_args_kwargs, "args_kwargs"),
        (f_defaults, "defaults"),
        (f_kwonly, "kwonly"),
        (f_posonly, "posonly"),
        (f_annotated, "annotated"),
        (f_nodoc, "nodoc"),
    ]

    # The exact F2P target, when django is importable in the eval container.
    try:
        from django.db.models import QuerySet
        boundary.append((QuerySet.bulk_create, "QuerySet.bulk_create"))
        boundary.append((QuerySet.get, "QuerySet.get"))
        boundary.append((QuerySet.count, "QuerySet.count"))
    except Exception:
        pass  # stdlib-only check still meaningful without django on the path

    n_discriminating = 0
    for target, label in boundary:
        if check(target, label):
            n_discriminating += 1

    # --- randomized fuzz: synthesize callables with varied signatures ---------
    rng = random.Random(15731)
    POOL = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "m"]
    n_fuzz = 20000
    for i in range(n_fuzz):
        n_pos = rng.randint(0, 4)
        n_def = rng.randint(0, 3)
        has_args = rng.random() < 0.5
        has_kwargs = rng.random() < 0.5
        n_kwonly = rng.randint(0, 2)
        names = POOL[: n_pos + n_def + n_kwonly]
        # build a unique parameter list
        params = []
        idx = 0
        for _ in range(n_pos):
            params.append(names[idx]); idx += 1
        for _ in range(n_def):
            params.append("%s=None" % names[idx]); idx += 1
        if has_args:
            params.append("*rest")
        elif n_kwonly:
            params.append("*")
        for _ in range(n_kwonly):
            params.append("%s=0" % names[idx]); idx += 1
        if has_kwargs:
            params.append("**kw")
        src = "def _fuzz(%s):\n    %s\n" % (
            ", ".join(params),
            repr("doc#%d" % i) if i % 3 else "pass",
        )
        ns = {}
        exec(src, ns)  # noqa: S102 - synthesizing a callable for introspection
        target = ns["_fuzz"]
        if i % 3 == 0:
            target.__doc__ = None  # exercise the None-doc bridge
        if check(target, "fuzz#%d %s" % (i, src.splitlines()[0])):
            n_discriminating += 1

    # non-triviality of the WHOLE battery (not of any single target): at least
    # one checked target must have a real signature distinct from the generic
    # forwarder form, so the suite genuinely exercises the signature-propagation
    # path the bug is about (e.g. f_defaults / QuerySet.bulk_create). This is the
    # correct home for the meaningfulness guard — the per-target form failed on
    # sound-but-non-discriminating targets like QuerySet.get.
    assert n_discriminating > 0, (
        "G-AX battery is trivial: no checked target had a signature distinct "
        "from the generic forwarder form")

    print("G-AX OK: propagate deep model (== functools.wraps effect on "
          "name/doc/signature) sound on %d boundary + %d fuzz callables; "
          "signature resolves through __wrapped__ in every case "
          "(%d discriminating, i.e. true sig != generic forwarder form)."
          % (len(boundary), n_fuzz, n_discriminating))
    return 0


if __name__ == "__main__":
    sys.exit(main())
