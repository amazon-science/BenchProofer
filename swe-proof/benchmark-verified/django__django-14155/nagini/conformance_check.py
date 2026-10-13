#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14155 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (the Assert lines) stripped, plus the @Pure helpers copied over as plain
functions with a tuple shim standing in for PSeq (ToSeq == tuple). The carrier
is List[int] of Unicode code points throughout (mapping.md "Type abstraction").

ORACLE: the REAL patched repo method the model models per mapping.md —
`django.urls.resolvers.ResolverMatch.__repr__` at /testbed with the gold patch
applied by the gate (this script applies nothing itself). Each case builds a
real ResolverMatch from a real callable and real str fields, takes its repr(),
and compares it to the shadow's output under the documented bridges:

  * str <-> List[int] of code points (mapping.md §2): inputs are encoded with
    ord(); the shadow's output list is compared against the code points of the
    oracle string.
  * `is_prebound` <-> the callable being a pre-bound wrapper
    (functools.partial); the check exercises real partials (plain, nested,
    and update_wrapper-ed) as well as plain functions.
  * `func_path` <-> the constructed match's own dotted-path attribute
    (`_func_path`, read off the real object); `func_repr` <-> repr(func).
    Both are opaque code-point strings to the model.
  * the four collection fields are elided from the model as an identity step
    (mapping.md §3.4, refinement.md I-collections). Every case fixes them to
    the canonical empty values, so in the oracle string they render as the two
    CONSTANT segments ", args=(), kwargs={}" and ", app_names=[], "
    "namespaces=[]"; the bridge excises the leftmost occurrence of each
    (length caps on the fuzzed text fields — 24 chars, and 16 for pre-bound
    argument values — keep those constants shorter than any excised anchor
    could be spoofed by, and the leftmost occurrence is the real one because
    the collections render before the text fields).
  * input domain (mapping.md §3.1): the text fields (url_name, route) range
    over the FULL printable-ASCII set (code points 32..126) — the domain the
    model's precondition admits. The apostrophe and the backslash are INSIDE
    it: they drive the delimiter choice and the per-code-point marking, so
    excluding them would hide exactly the behaviour this gate must shadow.

>= 1e5 Requires-satisfying inputs: 30 boundary cases + 100000 fuzz cases.
Pinned fuzz seed: 14155.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (functools, random).
"""
import functools
import json
import random
import sys

SEED = 14155
N_FUZZ = 100_000


# --- PSeq/ToSeq shim: pure sequences become plain tuples ---------------------

def PSeq(*items):
    return tuple(items)


def ToSeq(xs):
    return tuple(xs)


# --- @Pure helpers from model.py, decorators/contracts stripped --------------

def lit_head():
    # 'ResolverMatch(func='
    return PSeq(82, 101, 115, 111, 108, 118, 101, 114, 77, 97, 116, 99, 104,
                40, 102, 117, 110, 99, 61)


def lit_url_name():
    # ', url_name='
    return PSeq(44, 32, 117, 114, 108, 95, 110, 97, 109, 101, 61)


def lit_route():
    # ', route='
    return PSeq(44, 32, 114, 111, 117, 116, 101, 61)


def lit_tail():
    # ')'
    return PSeq(41)


def contains(s, x):
    return x in tuple(s)


def delim(s):
    if contains(s, 39) and not contains(s, 34):
        return 34
    return 39


def esc_char(c, d):
    if c == 92:
        return PSeq(92, 92)
    if c == d:
        return PSeq(92, c)
    return PSeq(c)


def esc_body(s, d):
    out = PSeq()
    for c in s:
        out = out + esc_char(c, d)
    return out


def quoted_with(s, d):
    return PSeq(d) + esc_body(s, d) + PSeq(d)


def quoted(s):
    return quoted_with(s, delim(s))


def func_token(func_path, func_repr, is_prebound):
    if is_prebound:
        return func_repr
    return func_path


def built_repr(func_path, func_repr, is_prebound, url_name, route):
    return (lit_head() + func_token(func_path, func_repr, is_prebound)
            + lit_url_name() + quoted(url_name)
            + lit_route() + quoted(route)
            + lit_tail())


# --- the impl region of model.py, verbatim (Assert lines stripped) -----------

def resolver_match_repr(func_path, func_repr, is_prebound, url_name, route):
    if is_prebound:
        func = func_repr  # type: List[int]
    else:
        func = func_path
    head = [82, 101, 115, 111, 108, 118, 101, 114, 77, 97, 116, 99, 104,
            40, 102, 117, 110, 99, 61]  # type: List[int]
    seg_url_name = [44, 32, 117, 114, 108, 95, 110, 97, 109, 101, 61]  # type: List[int]
    seg_route = [44, 32, 114, 111, 117, 116, 101, 61]  # type: List[int]
    cu = 0
    cr = 0
    du = delim(ToSeq(url_name))
    ub = []  # type: List[int]
    i = len(url_name)
    while i > 0:
        cu = url_name[i - 1]
        if cu == 92:
            ub = [92, 92] + ub
        elif cu == du:
            ub = [92, cu] + ub
        else:
            ub = [cu] + ub
        i = i - 1
    q_url = [du] + ub + [du]  # type: List[int]
    dr = delim(ToSeq(route))
    rb = []  # type: List[int]
    j = len(route)
    while j > 0:
        cr = route[j - 1]
        if cr == 92:
            rb = [92, 92] + rb
        elif cr == dr:
            rb = [92, cr] + rb
        else:
            rb = [cr] + rb
        j = j - 1
    q_route = [dr] + rb + [dr]  # type: List[int]
    result = head + func + seg_url_name + q_url + seg_route + q_route + [41]  # type: List[int]
    return result


# --- bridges ------------------------------------------------------------------

def cps(s):
    return [ord(c) for c in s]


# The elided collection fields, fixed to the canonical empty values, render as
# these constant oracle segments (mapping.md §3.4: an identity step the model
# omits). The leftmost occurrence of each is the real one: both render before
# the fuzzed text fields, and the length caps on all fuzzed strings keep them
# too short to contain either segment.
SEG_COLLECTIONS_1 = ", args=(), kwargs={}"
SEG_COLLECTIONS_2 = ", app_names=[], namespaces=[]"


def oracle_reduced(match_repr_str):
    """Excise the constant empty-collection segments from the real repr,
    leaving exactly the modelled portion. Returns None if a segment is
    missing (itself a disagreement signal)."""
    if SEG_COLLECTIONS_1 not in match_repr_str:
        return None
    reduced = match_repr_str.replace(SEG_COLLECTIONS_1, "", 1)
    if SEG_COLLECTIONS_2 not in reduced:
        return None
    return reduced.replace(SEG_COLLECTIONS_2, "", 1)


def check_case(ResolverMatch, func, url_name, route):
    """One differential case: real ResolverMatch repr vs the shadow."""
    match = ResolverMatch(func, (), {}, url_name=url_name,
                          app_names=[], namespaces=[], route=route)
    real_full = repr(match)
    real = oracle_reduced(real_full)

    # bridged model inputs, read off the real object per mapping.md §2
    func_path = cps(match._func_path)
    func_repr = cps(repr(func))
    is_prebound = isinstance(func, functools.partial)
    shadow = resolver_match_repr(func_path, func_repr, is_prebound,
                                 cps(url_name), cps(route))
    # internal consistency (mirrors the stripped Assert lines): the impl
    # region agrees with the pure-region assembly
    assert ToSeq(shadow) == built_repr(ToSeq(func_path), ToSeq(func_repr),
                                       is_prebound, ToSeq(cps(url_name)),
                                       ToSeq(cps(route)))

    real_cps = None if real is None else cps(real)
    if shadow != real_cps:
        return ("DISAGREEMENT\n"
                "  func=%r  is_prebound=%r\n"
                "  _func_path=%r  url_name=%r  route=%r\n"
                "  real (full)   = %r\n"
                "  real (bridged)= %r\n"
                "  shadow        = %r"
                % (func, is_prebound, match._func_path, url_name, route,
                   real_full, real,
                   None if shadow is None else "".join(chr(c) for c in shadow)))
    return None


# --- input generation ----------------------------------------------------------

def base_view(request, *args, **kwargs):
    """A plain module-level callable for the non-pre-bound cases."""


def another_view(request):
    """A second plain callable (different dotted path)."""


class ClassView:
    """A callable instance: no __name__, so its dotted path is the class path."""
    def __call__(self, request):
        pass


def make_named(module, name):
    """A fresh plain function with a chosen dotted path."""
    def f(request):
        pass
    f.__module__ = module
    f.__name__ = name
    return f


def make_partial(value, nested=False, wrapped=False):
    """A real pre-bound wrapper over base_view; optionally nested or carrying
    the wrapped callable's metadata."""
    p = functools.partial(base_view, template_name=value)
    if nested:
        p = functools.partial(p, other=value)
    if wrapped:
        p = functools.update_wrapper(p, base_view)
    return p


# the FULL printable-ASCII range (32..126): the domain the model's precondition
# admits, apostrophe and backslash included (mapping.md §3.1)
ALPHABET = [chr(cp) for cp in range(32, 127)]


def rand_text(rng, max_len=24):
    n = rng.randint(0, max_len)
    return "".join(rng.choice(ALPHABET) for _ in range(n))


def boundary_cases():
    """Fixture-shaped and edge cases: the plain callable with the regex route,
    partial / nested / wrapped pre-bound wrappers, a class-based callable,
    empty and single-char text fields."""
    p1 = make_partial("template.html")
    p2 = make_partial("nested_partial.html", nested=True)
    p3 = make_partial("template.html", wrapped=True)
    cv = ClassView()
    return [
        (base_view, "no-kwargs", "^no_kwargs/([0-9]+)/([0-9]+)/$"),
        (base_view, "", ""),
        (base_view, "a", "b"),
        (base_view, "", "route/only/"),
        (base_view, "name-only", ""),
        (another_view, "x", "^x/$"),
        (cv, "class-based", "cb/"),
        (cv, "", ""),
        (p1, "partial", "partial/"),
        (p2, "partial_nested", "partial_nested/"),
        (p3, "partial_wrapped", "partial_wrapped/"),
        (p1, "", ""),
        (p2, "0", "$"),
        (p3, '"', "%"),
        (base_view, '"double"', 'a"b'),
        (base_view, "  spaced  ", "  "),
        (base_view, "(?P<id>[0-9]+)", "[abc]{1,2}"),
        (base_view, "a.b.c", "~!@#$%^&*()_+"),
        (make_named("m", "f"), "tiny.path", "t/"),
        (make_named("some.long.module.path", "view_name_x"), "n", "r"),
        (p1, "^a$", "(?P<id>[0-9]+)"),
        (p2, "=;:", "?*+."),
        (base_view, "0123456789", "/"),
        (cv, "under_score", "da-sh/"),
        (p3, "n", ""),
        (p1, " ", " "),
        (base_view, "~", "@"),
        (another_view, "", "^$"),
        (make_named("a", "b"), "", ""),
        (base_view, "x" * 24, "y" * 24),
        # The backslash and apostrophe classes -- the reviewer's witnesses and
        # their neighbours. A regex route carrying escapes is the ORDINARY
        # input to this function; an apostrophe-bearing name sends the
        # delimiter to the double quote; a value holding BOTH keeps the
        # apostrophe delimiter, which is then marked.
        (base_view, "no-kwargs", "^\\d+/$"),
        (base_view, "digits", "^\\w+/\\d+/$"),
        (base_view, "it's", "^\\d+/$"),
        (base_view, "it's", "o'clock/"),
        (base_view, "'", "'"),
        (base_view, "''", "\\"),
        (base_view, "both'and\"", "a\\'b"),
        (base_view, "\"'", "'\""),
        (base_view, "\\", "\\\\"),
        (base_view, "a\\.b", "\\d"),
        (base_view, "'leading", "trailing'"),
        (cv, "it's", "^\\d+/$"),
        (p1, "it's", "^\\d+/$"),
        (p2, "both'and\"", "a\\'b"),
        (p3, "\\", "'"),
        (make_partial("it's \\ a value"), "partial'q", "p\\d/"),
    ]


def main():
    from django.urls.resolvers import ResolverMatch

    checked = 0
    bcases = boundary_cases()
    for func, url_name, route in bcases:
        err = check_case(ResolverMatch, func, url_name, route)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    plain_funcs = [base_view, another_view, ClassView()]
    for _ in range(N_FUZZ):
        kind = rng.randint(0, 5)
        if kind == 0:
            func = rng.choice(plain_funcs)
        elif kind == 1:
            func = make_named(rand_text(rng, 12).replace(" ", "_") or "m",
                              rand_text(rng, 12).replace(" ", "_") or "f")
        elif kind == 2:
            func = make_partial(rand_text(rng, 16))
        elif kind == 3:
            func = make_partial(rand_text(rng, 16), nested=True)
        elif kind == 4:
            func = make_partial(rand_text(rng, 16), wrapped=True)
        else:
            func = make_partial("")
        err = check_case(ResolverMatch, func, rand_text(rng), rand_text(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched repr (modelled fields) on "
          "%d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(bcases), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
