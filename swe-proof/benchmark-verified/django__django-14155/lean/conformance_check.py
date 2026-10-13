#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-14155.

The bundle models the construction of the single representation line a resolved
URL match renders (mapping.md). The decision is a PURE function of the renderings
the routine already has in hand at that point:

    func_is_partial : bool    (isinstance(self.func, functools.partial))
    func_path       : str     (self._func_path)
    func_repr       : str     (repr(self.func))
    args/kwargs/url_name/app_names/namespaces/route : (s:str, r:str)
                              each value's plain (%s/str) and representation
                              (%r/repr) renderings

Standing up Django's URL resolver + a live ResolverMatch to drive __repr__ is
unnecessary: the modeled value is exactly this pure assembly over the renderings
the real method reads. So the ORACLE below is a faithful in-process replica using
the EXACT patched expression (django/urls/resolvers.py, ResolverMatch.__repr__):

    if func_is_partial:            # isinstance(self.func, functools.partial)
        func = func_repr           # repr(self.func)
    else:
        func = func_path           # self._func_path
    return (
        'ResolverMatch(func=%s, args=%r, kwargs=%r, url_name=%r, '
        'app_names=%r, namespaces=%r, route=%r)' % (
            func, args, kwargs, url_name, app_names, namespaces, route,
        )
    )

We supply each remaining value's `%r` rendering directly as `r` (and its `%s`
rendering as `s`), so the oracle's `%`-format reduces to string concatenation of
the supplied `r` fields. The SHADOW is the op-for-op transliteration of
`implementation_resolverMatchRepr` (per refinement.md).

This genuinely tests:
  * the partial-view case (func_is_partial=True) — the slot must show func_repr,
    not the dotted path (F2P: test_repr_functools_partial);
  * the non-partial case — the slot shows func_path;
  * the representation rendering of the six remaining slots — text values keep
    their delimiting quotes (F2P: test_repr).

stdlib-only. Pinned seed: 20240630 (also in mapping.md).
"""
import random
import sys

SEED = 20240630
N = 120_000


# --- ORACLE: faithful in-process replica of the patched __repr__ assembly -----
def oracle(func_is_partial, func_path, func_repr,
           args, kwargs, url_name, app_names, namespaces, route):
    func = func_repr if func_is_partial else func_path
    # The six remaining slots use %r; we supply each value's repr form as `.r`,
    # so the format string reduces to concatenation of the `.r` fields.
    return (
        'ResolverMatch(func=%s, args=%s, kwargs=%s, url_name=%s, '
        'app_names=%s, namespaces=%s, route=%s)' % (
            func, args[1], kwargs[1], url_name[1],
            app_names[1], namespaces[1], route[1],
        )
    )


# --- SHADOW of implementation_resolverMatchRepr (the R/I leg) -----------------
# Mirrors Solution.lean: func := func_path; if func_is_partial then func :=
# func_repr; return "ResolverMatch(func=" ++ func ++ ", args=" ++ args.r ++ ...
def shadow(func_is_partial, func_path, func_repr,
           args, kwargs, url_name, app_names, namespaces, route):
    func = func_path
    if func_is_partial:
        func = func_repr
    return ("ResolverMatch(func=" + func +
            ", args=" + args[1] +
            ", kwargs=" + kwargs[1] +
            ", url_name=" + url_name[1] +
            ", app_names=" + app_names[1] +
            ", namespaces=" + namespaces[1] +
            ", route=" + route[1] + ")")


def disagree(fp, path, frepr, a, k, u, an, ns, rt):
    o = oracle(fp, path, frepr, a, k, u, an, ns, rt)
    s = shadow(fp, path, frepr, a, k, u, an, ns, rt)
    if o != s:
        return ((fp, path, frepr, a, k, u, an, ns, rt), o, s)
    return None


# A rendered value: (plain str form, repr form). For text the two differ
# (repr adds quotes); for collections / None they coincide as Python prints them.
def _rendered(rng):
    kind = rng.randint(0, 4)
    if kind == 0:                       # a plain string value -> repr adds quotes
        txt = rng.choice(["no-kwargs", "partial", "name", "", "a'b", "x"])
        return (txt, repr(txt))
    if kind == 1:                       # a tuple, e.g. args
        t = tuple(rng.choice(["42", "37", "x"]) for _ in range(rng.randint(0, 3)))
        return (str(t), repr(t))
    if kind == 2:                       # a dict, e.g. kwargs
        d = {}
        for _ in range(rng.randint(0, 2)):
            d[rng.choice(["a", "b"])] = rng.choice(["1", "2"])
        return (str(d), repr(d))
    if kind == 3:                       # a list, e.g. app_names / namespaces
        l = [rng.choice(["admin", "ns"]) for _ in range(rng.randint(0, 2))]
        return (str(l), repr(l))
    return (str(None), repr(None))      # None -> both 'None'


def _edge_cases():
    cases = []
    for fp in (True, False):
        cases.append((fp, "views.empty_view",
                      "functools.partial(<function empty_view>, template_name='t')",
                      ("()", "()"),
                      ("{}", "{}"),
                      ("no-kwargs", "'no-kwargs'"),
                      ("[]", "[]"),
                      ("[]", "[]"),
                      ("^route/$", "'^route/$'")))
    # purely-string fields exercising the %s -> %r quoting difference
    cases.append((False, "p.q.r", "rep",
                  ("a", "'a'"), ("b", "'b'"), ("c", "'c'"),
                  ("d", "'d'"), ("e", "'e'"), ("f", "'f'")))
    return cases


def main() -> int:
    checked = 0
    for c in _edge_cases():
        d = disagree(*c)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    paths = ["views.empty_view", "a.b.c", "pkg.mod.View", ""]
    reprs = ["functools.partial(<f>, x=1)", "<function f>", "rep", ""]
    for _ in range(N):
        fp = rng.choice([True, False])
        path = rng.choice(paths)
        frepr = rng.choice(reprs)
        a, k, u = _rendered(rng), _rendered(rng), _rendered(rng)
        an, ns, rt = _rendered(rng), _rendered(rng), _rendered(rng)
        d = disagree(fp, path, frepr, a, k, u, an, ns, rt)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
