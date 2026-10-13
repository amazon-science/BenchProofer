#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14155.

This bundle consumes NO `@ContractOnly` axiom: the behaviour (a parenthesised
textual description built by string interpolation, with a quoted rendering of
the text fields and a wrapper-sensitive choice of callable name) is modelled
DEEPLY in model.py over `List[int]` / `PSeq[int]`. G-AX therefore validates the
deep model against the REAL Python operations it abstracts (A-reference):

  * `quoted(s)`  == the real `'%r' % s` rendering of a text value, over the
                    FULL printable-ASCII domain the model's precondition admits
                    (code points 32..126) -- including the apostrophe and the
                    backslash, which drive the delimiter choice and the
                    per-code-point marking respectively.
  * `func_token` == the real selection performed by the description: the
                    callable's own textual form (`repr`) when it is a
                    `functools.partial` wrapper, else its dotted import path.
  * `built_repr` == the REAL post-patch interpolation
                    'ResolverMatch(func=%s, ... url_name=%r, ... route=%r)' % ...
                    restricted to the modelled fields, reproduced exactly.

The collection fields elided from the model (args/kwargs/app_names/namespaces)
are additionally checked here to confirm the refinement's identity claim that
their `%r` rendering equals their `%s` rendering for the values that occur.

Imports only the Python standard library (`functools`) -- the same module the
gold patch calls. Exit 0 iff every observation matches the model.
"""
import functools
import random
import sys


# --- model.py reference encodings (kept in lock-step with the deep model) ----

def contains(codepoints, x):
    """Reference for model.py `contains`."""
    return x in list(codepoints)


def delim(codepoints):
    """Reference for model.py `delim`: the apostrophe (39), except that a value
    holding an apostrophe and no double quote is delimited by the double quote
    (34)."""
    if contains(codepoints, 39) and not contains(codepoints, 34):
        return 34
    return 39


def esc_char(c, d):
    """Reference for model.py `esc_char`: a backslash (92) and the delimiter
    itself are each preceded by an additional backslash."""
    if c == 92:
        return [92, 92]
    if c == d:
        return [92, c]
    return [c]


def esc_body(codepoints, d):
    """Reference for model.py `esc_body`."""
    out = []
    for c in codepoints:
        out += esc_char(c, d)
    return out


def quoted_with(codepoints, d):
    """Reference for model.py `quoted_with`."""
    return [d] + esc_body(codepoints, d) + [d]


def quoted(codepoints):
    """Reference for model.py `quoted`."""
    return quoted_with(codepoints, delim(codepoints))


def func_token(func_path, func_repr, is_prebound):
    """Reference for model.py `func_token`."""
    return list(func_repr) if is_prebound else list(func_path)


_HEAD = [ord(c) for c in "ResolverMatch(func="]
_LIT_URL_NAME = [ord(c) for c in ", url_name="]
_LIT_ROUTE = [ord(c) for c in ", route="]
_TAIL = [ord(c) for c in ")"]


def built_repr(func_path, func_repr, is_prebound, url_name, route):
    """Reference for model.py `built_repr` (the modelled fields only)."""
    return (_HEAD + func_token(func_path, func_repr, is_prebound)
            + _LIT_URL_NAME + quoted(url_name)
            + _LIT_ROUTE + quoted(route)
            + _TAIL)


def cps(s):
    return [ord(c) for c in s]


# --- the checks --------------------------------------------------------------

def check_quoted_is_repr(s):
    """Assert quoted(s) == real `'%r' % s` for ANY printable-ASCII text value
    (code points 32..126) -- the whole domain the model's precondition admits.

    CPython's `repr`/`%r` of such a `str` delimits it with the apostrophe,
    except that a value containing an apostrophe and no double quote is
    delimited by the double quote instead; between the delimiters a backslash
    and each occurrence of the chosen delimiter are preceded by an additional
    backslash. The model's `delim`/`esc_body`/`quoted` encode exactly that, so
    NO code point of the printable range is excluded from this check -- in
    particular the apostrophe and the backslash, which the route patterns this
    function actually renders (regex escapes like \\d, \\w, \\.) carry
    routinely, are inside the checked domain."""
    observed = cps('%r' % s)
    expected = quoted(cps(s))
    assert observed == expected, (
        "quoted deep model unsound on %r: '%%r' gave %r, model gives %r"
        % (s, observed, expected))


def check_built_repr(func, func_path_str, url_name, route):
    """Assert built_repr == the REAL post-patch interpolation, restricted to
    the modelled fields (func, url_name, route)."""
    is_prebound = isinstance(func, functools.partial)
    func_field = repr(func) if is_prebound else func_path_str
    real = 'ResolverMatch(func=%s, url_name=%r, route=%r)' % (
        func_field, url_name, route)
    observed = cps(real)
    expected = built_repr(cps(func_path_str), cps(repr(func)),
                          is_prebound, cps(url_name), cps(route))
    assert observed == expected, (
        "built_repr deep model unsound: real=%r observed=%r model=%r"
        % (real, observed, expected))


def check_collection_field_identity(value):
    """Refinement identity claim: for the collection fields the model elides,
    the `%r` rendering equals the `%s` rendering -- so dropping the str->repr
    change for them is behaviour-preserving."""
    assert ('%r' % (value,)) == ('%s' % (value,)), (
        "collection field %r differs under %%r vs %%s" % (value,))


def empty_view(request, *args, **kwargs):
    """Stand-in for the test fixture view, so `functools.partial` reprs match
    the real callable-naming behaviour structurally."""


def main():
    # --- quoted == '%r' % s over the FULL printable-ASCII domain -----------
    # url_name / route values are dotted names, regex routes (with backslash
    # escapes), slugs, digits, symbols, and may contain apostrophes and double
    # quotes. Every printable code point is in the checked domain.
    text_boundary = [
        "", "no-kwargs", "^no_kwargs/([0-9]+)/([0-9]+)/$",
        "partial", "partial_nested", "partial_wrapped", "partial/",
        "a", "Z", "0", "/path/to/x", "name-with-dashes", "name_with_underscore",
        "^a$", "(?P<id>[0-9]+)", "[abc]", "{1,2}", "a.b.c", "  spaced  ",
        '"', "%", ":", ";", "=", "~", "@", "+", "*", "?", ".",
        # The backslash and apostrophe classes -- the reviewer's witnesses and
        # their neighbours. A regex route carrying escapes is the ORDINARY
        # input to this function; an apostrophe-bearing name sends the
        # delimiter to the double quote; a value holding BOTH keeps the
        # apostrophe delimiter, which is then marked.
        "^\\d+/$", "^\\w+/\\d+/$", "a\\.b", "\\", "\\\\", "\\d", "\\'",
        "it's", "'", "''", "o'clock/", "'leading", "trailing'",
        "both'and\"", "\"'", "'\"", "a\\'b", "'\\", "\\\"",
    ]
    for s in text_boundary:
        check_quoted_is_repr(s)

    rng = random.Random(14155)
    # the FULL printable-ASCII range: the domain the model's precondition
    # admits, apostrophe and backslash included.
    alphabet = [chr(cp) for cp in range(32, 127)]
    # exhaustive single-printable-char sweep over the whole range
    for c in alphabet:
        check_quoted_is_repr(c)
    for _ in range(20000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_quoted_is_repr(s)

    # --- built_repr == real interpolation, partial and non-partial ---------
    partial1 = functools.partial(empty_view, template_name="template.html")
    partial2 = functools.partial(partial1, template_name="nested_partial.html")
    partial3 = functools.update_wrapper(
        functools.partial(empty_view, template_name="template.html"), empty_view)

    cases = [
        # (func, func_path_str, url_name, route)
        (empty_view, "urlpatterns_reverse.views.empty_view",
         "no-kwargs", "^no_kwargs/([0-9]+)/([0-9]+)/$"),
        (partial1, "functools.partial", "partial", "partial/"),
        (partial2, "functools.partial", "partial_nested", "partial_nested/"),
        (partial3, "urlpatterns_reverse.views.empty_view",
         "partial_wrapped", "partial_wrapped/"),
        (empty_view, "urlpatterns_reverse.views.empty_view", "", ""),
    ]
    for func, fp, un, rt in cases:
        check_built_repr(func, fp, un, rt)

    # randomized: pick partial vs plain callable and fuzz the text fields
    for _ in range(5000):
        use_partial = rng.random() < 0.5
        func = partial1 if use_partial else empty_view
        fp = "functools.partial" if use_partial else "urlpatterns_reverse.views.empty_view"
        def rand_text():
            n = rng.randint(0, 16)
            return "".join(rng.choice(alphabet) for _ in range(n))
        check_built_repr(func, fp, rand_text(), rand_text())

    # --- collection-field identity (the elided fields) ---------------------
    for value in [(), ('42', '37'), ('a',), {}, {'k': 'v'}, [],
                  ['ns'], ['a', 'b'], (1, 2, 3)]:
        check_collection_field_identity(value)

    print("G-AX OK: deep model (quoted/func_token/built_repr) == real Python "
          "interpolation over %d text-boundary + 20000 fuzz + %d repr cases "
          "+ 5000 fuzz; collection-field %%r==%%s identity holds."
          % (len(text_boundary), len(cases)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
