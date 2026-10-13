"""PBT manifest for django__django-15731 (NOT a Nagini module; a record of
adversarial cases the runner swebench_nagini.pbt executes + stamps RESULT).

Defended surface (frozen spec in model.py; see refinement.md / mapping.md):

  build_proxy(source: Func) -> Func
    Requires: Acc(source.name,1/2) and Acc(source.doc,1/2) and Acc(source.sig,1/2)
              -- source is READ-ONLY at fractional permission.
    Ensures (frame):  source.{name,doc,sig} == Old(...)  + the 1/2 perms returned.
    Ensures (own):    Result() fully owned (Acc on all five fields), Result() is not source.
    Ensures (name/doc): Result().name == source.name ; Result().doc == source.doc
    Ensures (DISCRIMINATING): reported_signature(Result().wrapped, Result().target_sig)
                              == source.sig
    Ensures (PINNING, clauses 3/4): Result().sig == SIG_FORWARDING() ;
                              Result().wrapped ; Result().target_sig == source.sig
                              -- the proxy's own declared signature stays the
                              forwarding one and the recording of the original is
                              unconditional (closes the free-field/conditional
                              rivals the G-PANEL-1 audit exhibited).

  reported_signature(wrapped, target_sig) is a @Pure @ContractOnly axiom (A-consumed):
    wrapped     -> Result() == target_sig
    not wrapped -> Result() == SIG_FORWARDING()   (== 0)

Gold impl records the source it stands in for (wrapped=True, target_sig=source.sig),
so the resolver reports source.sig. The pre-fix code (only name/doc copied,
wrapped=False) fails the discriminating clause because reported_signature then
returns SIG_FORWARDING()==0 != arbitrary source.sig.

The "oracle" reported_signature is GROUNDED in the proxy's own fields plus the
input source.sig (fully captured by the axiom Ensures + SIG_FORWARDING()==0);
there is no opaque answer-key to echo. So the uniqueness lane is about whether a
rival can satisfy the discriminating clause WITHOUT recording the source, or by
pinning only a sub-domain of source.sig -- it cannot, and we prove that here.

Region-surgery: every variant is built by _swap on _BASE editing ONLY the text
inside # impl-start/# impl-end, so same_spec is guaranteed (the frozen spec --
axioms/pure/pre/post-conditions/signatures -- is never touched).
"""
from pathlib import Path

INSTANCE = "django__django-15731"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The full gold impl body (everything strictly between # impl-start/# impl-end).
# Swapping on this whole block keeps all edits inside the impl region.
_GOLD_IMPL = (
    "    proxy = Func()\n"
    "    # proxy's own forwarding parameter list (def manager_method(self, *args,\n"
    "    # **kwargs)) -- its own sig is the forwarding signature.\n"
    "    proxy.sig = SIG_FORWARDING()\n"
    "    # functools.wraps(source): copy the introspectable metadata AND record the\n"
    "    # original callable the proxy stands in for (so the resolver follows it).\n"
    "    proxy.name = source.name\n"
    "    proxy.doc = source.doc\n"
    "    proxy.wrapped = True\n"
    "    proxy.target_sig = source.sig\n"
    "    return proxy"
)

# sanity: the anchor must be present exactly once in the frozen model
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl anchor drifted"


def _impl(body: str) -> str:
    """Return a full model.py whose impl region body is `body`."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------

SPEC_TESTS = [

    # --- 5. POSITIVE CONTROL (soundness) -----------------------------------
    # Structurally different but CORRECT: record-the-source FIRST, copy
    # name/doc LAST, set sig last, via a renamed local. Straight-line code, no
    # induction lemma needed, so the gold proof stays valid. MUST verify; else
    # SPEC-TOO-STRONG (a faithful correct impl that the postcondition rejects).
    {
        "id": "pos-control-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    p = Func()\n"
            "    # record the original FIRST (the discriminating step), then copy\n"
            "    # name/doc, then set the proxy's own forwarding signature.\n"
            "    p.wrapped = True\n"
            "    p.target_sig = source.sig\n"
            "    p.doc = source.doc\n"
            "    p.name = source.name\n"
            "    p.sig = SIG_FORWARDING()\n"
            "    return p"
        ),
        "rationale": "a correct impl with reordered straight-line assignments + a "
                     "renamed local must verify; the postcondition pins values, "
                     "not statement order, so rejecting it would be SPEC-TOO-STRONG.",
    },

    # --- 6. ADMISSIBILITY --------------------------------------------------
    # A self-call on an F2P-shaped, freshly-constructed source proves the
    # Requires (Acc(source.{name,doc,sig},1/2)) admits a normal input; then the
    # gold impl runs on the actual `source`. MUST verify; else PRECOND-TOO-STRONG.
    {
        "id": "admiss-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    # admissibility: a freshly-built source (full Acc on every field)\n"
            "    # establishes the 1/2-permission Requires, so the precondition\n"
            "    # admits a normal F2P-shaped input.\n"
            "    probe_src = Func()\n"
            "    Assert(Acc(probe_src.name, 1 / 2) and Acc(probe_src.doc, 1 / 2))\n"
    "    Assert(Acc(probe_src.sig, 1 / 2))\n"
                            "    # now the real builder on the actual source (the gold body).\n"
            "    proxy = Func()\n"
            "    proxy.sig = SIG_FORWARDING()\n"
            "    proxy.name = source.name\n"
            "    proxy.doc = source.doc\n"
            "    proxy.wrapped = True\n"
            "    proxy.target_sig = source.sig\n"
            "    return proxy"
        ),
        "rationale": "the precondition must accept a normal input: a self-call on a "
                     "fresh Func establishes Acc(...,1/2) and the result-property "
                     "asserts hold; else PRECOND-TOO-STRONG.",
    },

    # --- 1. FRAME-MUTATION (MANDATORY: source is read-only Acc(...,1/2)) ----
    # A rival that WRITES the read-only source to satisfy the postcondition
    # vacuously. Here it overwrites source.name to force name-equality and
    # mirrors source.sig, then returns a proxy. MUST be rejected for INSUFFICIENT
    # PERMISSION: only 1/2 of source.name is held, a write needs full perm.
    # Gold invariants are kept verbatim so the rejection is attributable to the write.
    {
        "id": "frame-mutate-source-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    proxy = Func()\n"
            "    proxy.sig = SIG_FORWARDING()\n"
            "    # FRAME-MUTATION attack: write the read-only source. Only Acc(.,1/2)\n"
            "    # is held -> this needs full permission and must be rejected.\n"
            "    source.name = source.doc\n"
            "    proxy.name = source.name\n"
            "    proxy.doc = source.doc\n"
            "    proxy.wrapped = True\n"
            "    proxy.target_sig = source.sig\n"
            "    return proxy"
        ),
        "refinement": "writing source.name corresponds to mutating the proxied "
                      "QuerySet method's __name__ -- the source is a SHARED class "
                      "method, so this would corrupt QuerySet introspection and "
                      "Old(source.name)/test_manager_method_attributes; a faithful "
                      "real patch that mutates the source would not resolve.",
        "rationale": "rejection comes from the permission system: Requires grants "
                     "only Acc(source.name,1/2); a write demands full permission.",
    },

    # --- 1b. FRAME-MUTATION supporting case: write source.sig ---------------
    # Cheaper supporting variant: overwrite source.sig (also read-only at 1/2)
    # so that even a wrapped=False proxy would satisfy the discriminating clause
    # (set source.sig = SIG_FORWARDING() so reported_signature(False,_)==source.sig).
    # MUST reject for insufficient permission.
    {
        "id": "frame-mutate-source-sig",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    proxy = Func()\n"
            "    proxy.sig = SIG_FORWARDING()\n"
            "    proxy.name = source.name\n"
            "    proxy.doc = source.doc\n"
            "    # FRAME-MUTATION: force source.sig to the forwarding code so an\n"
            "    # unwrapped proxy trivially satisfies the discriminating clause.\n"
            "    source.sig = SIG_FORWARDING()\n"
            "    proxy.wrapped = False\n"
            "    proxy.target_sig = 0\n"
            "    return proxy"
        ),
        "refinement": "this only 'works' by rewriting the source method's signature, "
                      "which a real patch cannot do (it would break Old(source.sig) "
                      "and every other consumer of bulk_create's real signature); "
                      "the faithful patch would report the forwarding signature and "
                      "fail test_manager_method_signature.",
        "rationale": "rejection from the permission system: Acc(source.sig,1/2) "
                     "forbids the write to source.sig.",
    },

    # --- 2/3. DISCRIMINATING (pre-fix echo / partial-domain on source.sig) --
    # The pre-fix impl: copy name/doc only, record NOTHING (wrapped=False). The
    # discriminating clause needs reported_signature(False,_) == source.sig, i.e.
    # SIG_FORWARDING()==0 == source.sig, which holds ONLY on the sub-domain
    # source.sig==0. For arbitrary source.sig it cannot verify. This is exactly
    # what model_prepatch.py reproduces. MUST reject; else SPEC-TOO-WEAK.
    {
        "id": "weak-prefix-no-record",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    proxy = Func()\n"
            "    proxy.sig = SIG_FORWARDING()\n"
            "    proxy.name = source.name\n"
            "    proxy.doc = source.doc\n"
            "    # pre-fix: only name/doc copied, NO original recorded. The resolver\n"
            "    # then reports the forwarding signature, not the source's.\n"
            "    proxy.wrapped = False\n"
            "    proxy.target_sig = 0\n"
            "    return proxy"
        ),
        "refinement": "this is the pre-patch behaviour (no @wraps, __wrapped__ never "
                      "set): inspect.signature(Article.objects.bulk_create) reports "
                      "'(*args, **kwargs)' instead of bulk_create's real signature -- "
                      "exactly the F2P test_manager_method_signature failure.",
        "rationale": "rejection from the discriminating postcondition clause "
                     "reported_signature(wrapped,target_sig)==source.sig: with "
                     "wrapped=False it forces source.sig==SIG_FORWARDING()==0, false "
                     "for arbitrary source.sig.",
    },

    # --- 3b. PARTIAL-DOMAIN: record the source but with the WRONG signature --
    # wrapped=True (looks correct) but target_sig = SIG_FORWARDING() instead of
    # source.sig. Then reported_signature(True, 0) == 0, needs source.sig==0.
    # Correct ONLY on the sub-domain source.sig==SIG_FORWARDING(); wrong otherwise.
    # MUST reject; else SPEC-TOO-WEAK.
    {
        "id": "weak-wrapped-wrong-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    proxy = Func()\n"
            "    proxy.sig = SIG_FORWARDING()\n"
            "    proxy.name = source.name\n"
            "    proxy.doc = source.doc\n"
            "    proxy.wrapped = True\n"
            "    # PARTIAL-DOMAIN: record the forwarding sig as the 'original', so\n"
            "    # the resolver reports SIG_FORWARDING() regardless of the source.\n"
            "    proxy.target_sig = SIG_FORWARDING()\n"
            "    return proxy"
        ),
        "refinement": "recording the proxy's own forwarding signature as __wrapped__'s "
                      "signature still makes inspect.signature report '(*args, "
                      "**kwargs)' for bulk_create -- the F2P test_manager_method_"
                      "signature still fails on every method whose signature differs "
                      "from the forwarding shape.",
        "rationale": "rejection from reported_signature(Result().wrapped, "
                     "Result().target_sig)==source.sig: target_sig must equal "
                     "source.sig, not the forwarding code.",
    },

    # --- 3c. PARTIAL-DOMAIN: name/doc swapped -------------------------------
    # Signature handled correctly, but proxy.name = source.doc. Verifies ONLY on
    # the sub-domain source.name==source.doc. MUST reject; else SPEC-TOO-WEAK.
    {
        "id": "weak-name-doc-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    proxy = Func()\n"
            "    proxy.sig = SIG_FORWARDING()\n"
            "    # PARTIAL-DOMAIN: copy doc into name (wrong unless name==doc).\n"
            "    proxy.name = source.doc\n"
            "    proxy.doc = source.doc\n"
            "    proxy.wrapped = True\n"
            "    proxy.target_sig = source.sig\n"
            "    return proxy"
        ),
        "refinement": "the proxy's __name__ would not match the source method's -- "
                      "test_manager_method_attributes (P2P) asserts "
                      "Article.objects.count.__name__ == QuerySet.count.__name__ and "
                      "would fail; a faithful patch copying the wrong name does not "
                      "resolve.",
        "rationale": "rejection from the name-equality postcondition clause "
                     "Result().name == source.name.",
    },

    # --- 3d. FREE-FIELD: proxy's own sig set to the source's ----------------
    # Correct wrapped/target_sig/name/doc, but proxy.sig = source.sig instead of
    # the forwarding code. The reported-signature clause still holds, so without
    # the pinning clause Result().sig == SIG_FORWARDING() this rival verifies
    # (the G-PANEL-1 audit's atk_3). MUST reject; else SPEC-TOO-WEAK.
    {
        "id": "weak-own-sig-source",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    proxy = Func()\n"
            "    # FREE-FIELD attack: give the proxy's OWN declared signature the\n"
            "    # source's code instead of the forwarding one.\n"
            "    proxy.sig = source.sig\n"
            "    proxy.name = source.name\n"
            "    proxy.doc = source.doc\n"
            "    proxy.wrapped = True\n"
            "    proxy.target_sig = source.sig\n"
            "    return proxy"
        ),
        "refinement": "a builder that declares manager_method with a different own "
                      "parameter list than the forwarding (self, *args, **kwargs) "
                      "diverges from the modeled change (the proxy body is untouched "
                      "by the gold edit); the spec must pin the proxy's own declared "
                      "signature to the forwarding one.",
        "rationale": "rejection from the pinning postcondition clause "
                     "Result().sig == SIG_FORWARDING().",
    },

    # --- 3e. FREE-FIELD: proxy's own sig set to an arbitrary constant --------
    # Same shape as 3d but with an arbitrary constant code (the audit's atk_8).
    # MUST reject; else SPEC-TOO-WEAK.
    {
        "id": "weak-own-sig-arbitrary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    proxy = Func()\n"
            "    # FREE-FIELD attack: arbitrary own-signature code.\n"
            "    proxy.sig = 12345\n"
            "    proxy.name = source.name\n"
            "    proxy.doc = source.doc\n"
            "    proxy.wrapped = True\n"
            "    proxy.target_sig = source.sig\n"
            "    return proxy"
        ),
        "refinement": "declaring the proxy with some unrelated own parameter list "
                      "(e.g. manager_method(self, arg_12345=None, *args, **kwargs)) "
                      "is not the modeled change; the proxy's own parameter list is "
                      "untouched by the gold edit.",
        "rationale": "rejection from the pinning postcondition clause "
                     "Result().sig == SIG_FORWARDING().",
    },

    # --- 3f. CONTROL-FLOW: conditional recording ------------------------------
    # Record the original ONLY when the source's signature differs from the
    # forwarding code (the audit's atk_5). The reported-signature clause holds on
    # BOTH branches (when equal, the fallback reports SIG_FORWARDING()==source.sig),
    # so without the unconditional-recording clause this rival verifies.
    # MUST reject; else SPEC-TOO-WEAK.
    {
        "id": "weak-conditional-record",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    proxy = Func()\n"
            "    proxy.sig = SIG_FORWARDING()\n"
            "    proxy.name = source.name\n"
            "    proxy.doc = source.doc\n"
            "    # CONTROL-FLOW attack: record the original only on the sub-domain\n"
            "    # where the source's signature differs from the forwarding code.\n"
            "    if source.sig != SIG_FORWARDING():\n"
            "        proxy.wrapped = True\n"
            "        proxy.target_sig = source.sig\n"
            "    return proxy"
        ),
        "refinement": "a builder that applies the recording conditionally (e.g. "
                      "wraps(method)(manager_method) only when "
                      "str(inspect.signature(method)) != '(self, *args, **kwargs)') "
                      "diverges from the modeled change, which decorates EVERY "
                      "proxied method unconditionally; the recording must not be "
                      "restricted to a sub-domain of sources.",
        "rationale": "rejection from the pinning postcondition clause "
                     "Result().wrapped (the recording is unconditional).",
    },

    # --- 4. CONTROL-FLOW / ALIASING: return the source itself ---------------
    # An identity rival returns `source`, echoing all its metadata. Even though
    # name/doc/sig would 'match', the postcondition Result() is not source rejects
    # it (and returning source would also need full Acc on the returned fields).
    # MUST reject; else SPEC-TOO-WEAK.
    {
        "id": "weak-return-source",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # ALIASING attack: return the source itself so all metadata\n"
            "    # trivially 'agrees'. The proxy must be a DISTINCT object.\n"
            "    return source"
        ),
        "refinement": "returning the source queryset method as the manager method "
                      "destroys the forwarding wrapper (self.get_queryset() "
                      "delegation) -- the manager would expose the raw QuerySet "
                      "method bound wrong; nothing about the change is implemented "
                      "and no test resolves.",
        "rationale": "rejection from the distinctness postcondition clause "
                     "Result() is not source (and the Result()-ownership Acc "
                     "clauses, which an aliased source cannot supply at full perm).",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE  (reported_signature is @ContractOnly, A-consumed -> probe needed)
# ---------------------------------------------------------------------------
#
# axiom-soundness: run the REAL callees (inspect.signature + functools.wraps,
#   stdlib -- the exact modules the F2P test and gold patch use) under the
#   caller's actual config (follow_wrapped=True, the CPython default and the F2P
#   call inspect.signature(Article.objects.bulk_create)). Assert both axiom
#   branches and the exact bulk_create boundary. Mirrors/strengthens axiom_check.py.
# axiom-containment: enumerate the EXACT (wrapped, target_sig) pairs the MODEL
#   can pass to reported_signature. From the postcondition the only call is
#   reported_signature(Result().wrapped, Result().target_sig); the gold impl can
#   reach (True, source.sig) for any source.sig, and a verifying rival could also
#   reach (False, _) only if source.sig==SIG_FORWARDING(). The axiom's Requires
#   is `True` for ALL (bool, int) -- it is total -- so every reachable input is
#   covered. We assert the axiom Requires places NO restriction the caller can fall
#   outside of (and that both branches are defined for both bool values).

AXIOM_TESTS = [

    {
        "id": "ax-sound-reported-signature",
        "axiom": "reported_signature",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": r'''
import functools, inspect, random, sys

def forwarding():
    def manager_method(self, *args, **kwargs):
        return None
    return manager_method

SIG_FORWARDING = str(inspect.signature(forwarding()))

def make_source(params):
    ns = {}
    exec("def _src(%s):\n    return None\n" % params, ns)
    f = ns["_src"]; f.__name__ = "proxied"; f.__doc__ = "d"
    return f

def proxy_wrapped(source):
    @functools.wraps(source)
    def manager_method(self, *args, **kwargs):
        return None
    return manager_method

def proxy_unwrapped(source):
    def manager_method(self, *args, **kwargs):
        return None
    manager_method.__name__ = source.__name__
    manager_method.__doc__ = source.__doc__
    return manager_method

boundary = [
    "self, *args, **kwargs", "", "self", "a, b, c",
    "objs, batch_size=None, ignore_conflicts=False",
    ("objs, batch_size=None, ignore_conflicts=False, update_conflicts=False, "
     "update_fields=None, unique_fields=None"),   # the exact bulk_create list
    "a, b=1, *c, d, **e", "*args", "**kwargs", "x, /, y, *, z", "a=1, b=2",
]

def check(source):
    # wrapped branch: reported_signature(True, target_sig) == target_sig
    pw = proxy_wrapped(source)
    assert getattr(pw, "__wrapped__", None) is source, "wraps did not set __wrapped__"
    target = str(inspect.signature(source))                 # follow_wrapped default
    observed = str(inspect.signature(pw))                   # caller config: default
    assert observed == target, ("AXIOM-UNSOUND wrapped: reported %r != target %r"
                                % (observed, target))
    # unwrapped branch: reported_signature(False, _) == SIG_FORWARDING()
    pu = proxy_unwrapped(source)
    assert not hasattr(pu, "__wrapped__")
    obs_u = str(inspect.signature(pu))
    assert obs_u == SIG_FORWARDING, ("AXIOM-UNSOUND unwrapped: reported %r != %r"
                                     % (obs_u, SIG_FORWARDING))
    # name/doc copied in both worlds (P2P)
    assert pw.__name__ == source.__name__ and pw.__doc__ == source.__doc__
    assert pu.__name__ == source.__name__ and pu.__doc__ == source.__doc__

for p in boundary:
    check(make_source(p))

# the exact F2P observable: a bulk_create-shaped source, wrapped proxy reports it
src = make_source("objs, batch_size=None, ignore_conflicts=False, "
                  "update_conflicts=False, update_fields=None, unique_fields=None")
pw = proxy_wrapped(src)
assert str(inspect.signature(pw)) == ("(objs, batch_size=None, ignore_conflicts=False, "
    "update_conflicts=False, update_fields=None, unique_fields=None)"), \
    "F2P-shaped wrapped proxy did not report the bulk_create signature"
# pre-fix proxy reports the forwarding signature (the bug the F2P catches)
pu = proxy_unwrapped(src)
assert str(inspect.signature(pu)) == SIG_FORWARDING and str(inspect.signature(pu)) != \
    str(inspect.signature(src)), "pre-fix proxy unexpectedly reported the source sig"

rng = random.Random(15731)
names = ["a","b","c","d","e","objs","size","flag"]
for _ in range(3000):
    n = rng.randint(0, 5)
    chosen = rng.sample(names, n)
    parts = [(nm + "=None") if rng.random() < 0.4 else nm for nm in chosen]
    if rng.random() < 0.3: parts.append("*args")
    if rng.random() < 0.3: parts.append("**kwargs")
    try:
        s = make_source(", ".join(parts))
    except SyntaxError:
        continue
    check(s)

print("ax-sound OK: inspect.signature follows __wrapped__ (follow_wrapped=True, "
      "the F2P config) when functools.wraps records it, else reports the "
      "forwarding signature; over %d boundary + 3000 fuzz lists." % len(boundary))
sys.exit(0)
''',
        "rationale": "if the real inspect.signature/functools.wraps violate either "
                     "axiom branch under follow_wrapped=True (the F2P config), "
                     "AXIOM-UNSOUND.",
    },

    {
        "id": "ax-contain-reported-signature",
        "axiom": "reported_signature",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": r'''
import sys
# The model calls reported_signature ONLY at the postcondition:
#   reported_signature(Result().wrapped, Result().target_sig).
# Result().wrapped is a bool; Result().target_sig is an int (Func fields).
# The axiom reported_signature(wrapped: bool, target_sig: int) has NO Requires
# clause -> its domain is ALL (bool, int). So every (wrapped, target_sig) the
# model can reach is trivially inside the axiom domain. We assert the reachable
# set is exactly typed (bool, int) and that the axiom places no narrower guard.
#
# Reachable inputs:
#   * gold impl: (True, source.sig) for ANY int source.sig.
#   * any same-spec rival that verifies could only reach (False, t) when the
#     discriminating clause forces SIG_FORWARDING()==source.sig; still a (bool,int).
# There is NO float/None/str the model can pass: Func.wrapped is declared bool,
# Func.target_sig is declared int (model.py __init__). Containment holds because
# the axiom domain (all bool x all int) >= the reachable set (subset of bool x int).
reachable_wrapped = [True, False]            # bool, both values reachable in principle
reachable_target = [-3, -1, 0, 1, 2, 7, 1000, 2**31, -2**31]  # arbitrary int codes
for w in reachable_wrapped:
    assert isinstance(w, bool), "model can only pass a bool for `wrapped`"
    for t in reachable_target:
        assert isinstance(t, int), "model can only pass an int for `target_sig`"
        # axiom Requires is empty (total) -> (w, t) is in-domain by construction.
print("ax-contain OK: reported_signature has no Requires guard; its domain is "
      "all (bool, int), which contains every (Result().wrapped, Result().target_sig) "
      "the model can reach. No caller-reachable input lies outside the axiom domain.")
sys.exit(0)
''',
        "rationale": "the axiom Requires is empty (total over bool x int); the model "
                     "can only pass a bool and an int, so every reachable callee-input "
                     "is in-domain. A reachable input outside would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER -- none exists here.",
    },
]
