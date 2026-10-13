#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15731 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped. The single @Pure helper (SIG_FORWARDING) copies over as a
plain function; Func becomes a plain record class (its __init__ keeps the
same field defaults, minus the Ensures). The impl has no @ContractOnly
callees (`reported_signature` appears only in the Ensures, never in the impl
region), so the shadow is fully self-contained.

ORACLE: the REAL patched repo builder the model models per mapping.md --
the inner `create_method` of `BaseManager._get_queryset_methods`
(django/db/models/manager.py). `create_method` is a closure, so it is
exercised through its enclosing classmethod: we call
`BaseManager._get_queryset_methods(QS)` on synthetic queryset classes whose
methods carry controlled names / docstrings / parameter lists, and observe
each returned proxy. The gate applies patch.diff to /testbed before this
script runs (PYTHONPATH=/testbed); this script never applies any diff.

Type bridge (mapping.md section 2): names / docstrings / signatures are
carried as int identity codes, observed only by equality. Each field family
gets an injective encoder (dict from observed value to a fresh int); the
signature encoder pins the code of the proxy's own forwarding parameter
list -- str(signature of `def f(self, *args, **kwargs)`) -- to 0, matching
the model's SIG_FORWARDING() == 0. Per real proxy the observation is:
  name code        <- code(proxy.__name__)
  doc code         <- code(proxy.__doc__)          (None is a valid doc)
  wrapped          <- whether the proxy records an original callable it
                      stands in for (the attribute the signature resolver
                      follows)
  target_sig code  <- code(str(signature(recorded original))) when wrapped,
                      else the model default 0
  sig code         <- code(str(signature(proxy, follow_wrapped=False)))
                      (the proxy's OWN declared parameter list)
The shadow input Func gets source.name/doc/sig from the same encoders
applied to the source method, so codes agree iff the underlying values do.
The model's Requires are pure access permissions (no value constraints), so
every generated input is Requires-satisfying by construction.

Cross-checks per case (real world only, mirrors the spec's observables):
  * the resolver-reported signature of the proxy equals the source's
    declared signature (the discriminating observable), and
  * the source method is left untouched (name/doc/signature unchanged).

>= 1e5 inputs: 66 boundary cases (11 boundary parameter lists, including
the exact bulk_create list from the F2P test and the forwarding shape
itself, crossed with name/doc variants incl. doc=None) plus 100000 fuzz
cases. Pinned fuzz seed: 20260807.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random; hypothesis not needed).
"""
import inspect
import json
import random
import sys

SEED = 20260807
N_FUZZ = 100_000
BATCH = 200  # methods per synthetic queryset class


# --- pure helper from model.py, contracts stripped -----------------------

def SIG_FORWARDING():
    """The signature code of the proxy's own forwarding parameter list (the
    one that captures arbitrary positional and keyword arguments)."""
    return 0


# --- Func record from model.py, Ensures stripped --------------------------

class Func:
    def __init__(self):
        # name / doc: introspectable identity strings (as integer codes)
        self.name = 0
        self.doc = 0
        # wrapped: whether this callable records an original it stands in for
        self.wrapped = False
        # target_sig: the recorded original's signature code (meaningful only
        # when `wrapped`)
        self.target_sig = 0
        # sig: this callable's own declared signature code
        self.sig = SIG_FORWARDING()


# --- the impl region of model.py, verbatim, contract calls stripped -------

def build_proxy(source):
    proxy = Func()
    # proxy's own forwarding parameter list (def manager_method(self, *args,
    # **kwargs)) -- its own sig is the forwarding signature.
    proxy.sig = SIG_FORWARDING()
    # functools.wraps(source): copy the introspectable metadata AND record the
    # original callable the proxy stands in for (so the resolver follows it).
    proxy.name = source.name
    proxy.doc = source.doc
    proxy.wrapped = True
    proxy.target_sig = source.sig
    return proxy


# --- bridge: injective value-to-int-code encoders --------------------------

def _forwarding_sig_str():
    def f(self, *args, **kwargs):
        return None
    return str(inspect.signature(f))


class Encoder:
    """Injective map from observed values to int codes (equality-preserving,
    exactly the model's identity-code abstraction)."""

    def __init__(self, pinned=None):
        self._codes = {}
        self._next = 1
        if pinned is not None:
            self._codes[pinned] = 0  # reserve code 0

    def code(self, value):
        if value not in self._codes:
            self._codes[value] = self._next
            self._next += 1
        return self._codes[value]


SIG_ENC = Encoder(pinned=_forwarding_sig_str())   # forwarding sig <-> 0
NAME_ENC = Encoder()
DOC_ENC = Encoder()


def sig_code_of(fn, own_only=False):
    if own_only:
        return SIG_ENC.code(str(inspect.signature(fn, follow_wrapped=False)))
    return SIG_ENC.code(str(inspect.signature(fn)))


# --- source-method factory --------------------------------------------------

_CODE_CACHE = {}


def make_source(params, name, doc):
    """Build a source callable with the given parameter list string and the
    given display name / docstring."""
    code = _CODE_CACHE.get(params)
    if code is None:
        code = compile("def _src(%s):\n    return None\n" % (params,),
                       "<conf-gen>", "exec")
        _CODE_CACHE[params] = code
    ns = {}
    exec(code, ns)
    f = ns["_src"]
    f.__name__ = name
    f.__doc__ = doc
    return f


def observe_real_proxy(proxy):
    """Map one real proxy's introspectable metadata to the model's Func
    observation (mapping.md section 2)."""
    obs = Func()
    obs.name = NAME_ENC.code(proxy.__name__)
    obs.doc = DOC_ENC.code(proxy.__doc__)
    recorded = getattr(proxy, "__wrapped__", None)
    obs.wrapped = recorded is not None
    obs.target_sig = sig_code_of(recorded) if obs.wrapped else 0
    obs.sig = sig_code_of(proxy, own_only=True)
    return obs


def fields(f):
    return (f.name, f.doc, f.wrapped, f.target_sig, f.sig)


def check_batch(get_queryset_methods, cases):
    """cases: list of (attr_name, source_fn, params). Builds one synthetic
    queryset class, runs the REAL builder over it, and diffs each returned
    proxy against the shadow. Returns an error string or None."""
    ns = {attr: fn for attr, fn, _ in cases}
    QS = type("SyntheticQuerySet", (), ns)
    proxies = get_queryset_methods(QS)
    for attr, source, params in cases:
        if attr not in proxies:
            return ("REAL BUILDER OMITTED a public non-colliding method: "
                    "attr=%r params=%r" % (attr, params))
        proxy = proxies[attr]
        # frame the source's pre-state
        src_name, src_doc = source.__name__, source.__doc__
        src_sig_str = str(inspect.signature(source))
        # shadow input: the source's metadata as identity codes
        model_source = Func()
        model_source.name = NAME_ENC.code(src_name)
        model_source.doc = DOC_ENC.code(src_doc)
        model_source.sig = SIG_ENC.code(src_sig_str)
        shadow = build_proxy(model_source)
        real = observe_real_proxy(proxy)
        if fields(shadow) != fields(real):
            return ("DISAGREEMENT\n"
                    "  source: attr=%r __name__=%r __doc__=%r params=%r\n"
                    "  shadow (name,doc,wrapped,target_sig,sig)=%r\n"
                    "  real   (name,doc,wrapped,target_sig,sig)=%r"
                    % (attr, src_name, src_doc, params,
                       fields(shadow), fields(real)))
        if proxy is source:
            return ("DISAGREEMENT: real builder returned the source itself "
                    "(model requires a distinct proxy): attr=%r" % attr)
        # spec observable: the resolver-reported signature of the proxy
        # equals the source's declared signature
        reported = str(inspect.signature(proxy))
        if reported != src_sig_str:
            return ("DISAGREEMENT (reported signature)\n"
                    "  source: attr=%r params=%r declared=%r\n"
                    "  proxy reported=%r" % (attr, params, src_sig_str,
                                             reported))
        # frame: the source is left exactly as it was
        if (source.__name__ != src_name or source.__doc__ != src_doc
                or str(inspect.signature(source)) != src_sig_str):
            return ("DISAGREEMENT (source mutated)\n  attr=%r params=%r"
                    % (attr, params))
    return None


# --- input generation --------------------------------------------------------

BOUNDARY_PARAMS = [
    "self, *args, **kwargs",                      # == the forwarding shape
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

DOC_POOL = [None, "", "the source docstring", "line one\nline two",
            "  leading whitespace doc  "]
NAME_POOL = ["proxied_method", "bulk_create_like", "m", "alpha_beta",
             "get_things", "Weird_Name_0"]


def random_params(rng):
    names = ["a", "b", "c", "d", "e", "f", "g", "h", "objs", "size", "flag"]
    n = rng.randint(0, 5)
    chosen = rng.sample(names, n)
    parts = []
    if rng.random() < 0.5:
        parts.append("self")
    for nm in chosen:
        if rng.random() < 0.4:
            parts.append("%s=None" % nm)
        else:
            parts.append(nm)
    if rng.random() < 0.3:
        parts.append("*args")
    if parts and rng.random() < 0.15:
        # keyword-only tail (only valid after a *args entry)
        if "*args" not in parts:
            parts.append("*")
        parts.append("kw_only=1")
    if rng.random() < 0.3:
        parts.append("**kwargs")
    return ", ".join(parts)


def main():
    # REAL repo symbol (the enclosing classmethod of the modeled builder,
    # per mapping.md): resolves the patched source at /testbed.
    from django.db.models.manager import BaseManager

    def get_queryset_methods(qs_class):
        return BaseManager._get_queryset_methods(qs_class)

    checked = 0
    counter = [0]

    def fresh_attr():
        # public, unique, and never an attribute of the manager class (the
        # real builder skips colliding or underscore-prefixed names)
        counter[0] += 1
        return "cm%d" % counter[0]

    # --- boundary cases ------------------------------------------------------
    boundary_cases = []
    for params in BOUNDARY_PARAMS:
        for name in ("proxied_method", "another_name"):
            for doc in (None, "", "the source docstring"):
                attr = fresh_attr()
                boundary_cases.append(
                    (attr, make_source(params, name, doc), params))
    for i in range(0, len(boundary_cases), BATCH):
        err = check_batch(get_queryset_methods, boundary_cases[i:i + BATCH])
        if err:
            print(err)
            return 1
    n_boundary = len(boundary_cases)
    checked += n_boundary

    # --- fuzz ----------------------------------------------------------------
    rng = random.Random(SEED)
    remaining = N_FUZZ
    while remaining > 0:
        cases = []
        want = min(BATCH, remaining)
        while len(cases) < want:
            params = random_params(rng)
            name = rng.choice(NAME_POOL)
            doc = rng.choice(DOC_POOL)
            try:
                fn = make_source(params, name, doc)
            except SyntaxError:
                continue
            cases.append((fresh_attr(), fn, params))
        err = check_batch(get_queryset_methods, cases)
        if err:
            print(err)
            return 1
        checked += len(cases)
        remaining -= len(cases)

    print("G-CONF OK: shadow impl == real proxy builder on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
