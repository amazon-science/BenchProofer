#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14155 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`resolverMatchRepr`, routed through the deep model `matchRepr`)
              transliterated to Python over the real repo object (a
              `ResolverMatch`), via the mapping.md §2 bijection (a ResolverMatch
              ↔ its observable-field record `MatchView`; `Option String` ↔
              `None`/`str`; `quoted s` ↔ Python `repr(str)` over the ASCII
              plane). There are NO A-tagged callees in the impl region (no
              axioms), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `ResolverMatch.__repr__` applied at base_commit (the harness
              applies the gold patch before this runs).

They must agree on the rendered text line for every input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import functools
import random
import string
import sys

SEED = 14155
N_FUZZ = 100_000

# --- minimal django bootstrap (ResolverMatch.__init__ needs no settings) -----
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        USE_TZ=True,
    )
    django.setup()

from django.urls.resolvers import ResolverMatch


# --- the R/I shadow: Solution.lean matchRepr/resolverMatchRepr, transliterated

def hex_digit(n):
    """`hexDigit n` from Solution.lean: 0-9 then lowercase a-f."""
    return chr(48 + n) if n < 10 else chr(87 + n)


def esc_char(delim, c):
    """`escChar delim c` from Solution.lean: the escape character and the
    wrapping quote mark render escaped; tab/LF/CR as their two-letter escape
    codes; any other control char (and DEL) as a two-hex-digit escape; every
    other character as itself."""
    if c == "\\":
        return "\\\\"
    if c == delim:
        return "\\" + delim
    if c == "\t":
        return "\\t"
    if c == "\n":
        return "\\n"
    if c == "\r":
        return "\\r"
    n = ord(c)
    if n < 32 or n == 127:
        return "\\x" + hex_digit(n // 16) + hex_digit(n % 16)
    return c


def quoted(s):
    """`quoted s` from Solution.lean: the Python `repr(str)` rule over the
    ASCII plane — wrap in single quotes with backslash/quote escaping and
    control-character escape codes, EXCEPT wrap in double quotes when the
    value contains a single quote but no double quote (mapping.md §2)."""
    delim = '"' if ("'" in s and '"' not in s) else "'"
    return delim + "".join(esc_char(delim, c) for c in s) + delim


def quoted_opt(o):
    """`quotedOpt` from Solution.lean: None -> literal `None`, else quoted."""
    return "None" if o is None else quoted(o)


def match_view(m):
    """The mapping.md §2 bijection: a real ResolverMatch -> its observable slice
    (the fields __repr__ actually reads). The two textual `func` forms and the
    three already-rendered list/mapping components are carried verbatim as the
    repr text the source inserts via `%r`."""
    return {
        "isPartialFunc": isinstance(m.func, functools.partial),
        "funcPartialText": repr(m.func),
        "funcPath": m._func_path,
        "argsText": repr(m.args),
        "kwargsText": repr(m.kwargs),
        "urlName": m.url_name,
        "appNamesText": repr(m.app_names),
        "namespacesText": repr(m.namespaces),
        "route": m.route,
    }


def shadow_match_repr(m):
    """matchRepr (match_view m) transliterated to Python. Branch order EXACTLY
    as Solution.lean's matchRepr: a partial-application callable shown by its
    full textual form, else its dotted path; the optional name and route shown
    quoted (an absent one as `None`)."""
    v = match_view(m)
    func_str = v["funcPartialText"] if v["isPartialFunc"] else v["funcPath"]
    return ("ResolverMatch(func=" + func_str +
            ", args=" + v["argsText"] +
            ", kwargs=" + v["kwargsText"] +
            ", url_name=" + quoted_opt(v["urlName"]) +
            ", app_names=" + v["appNamesText"] +
            ", namespaces=" + v["namespacesText"] +
            ", route=" + quoted_opt(v["route"]) + ")")


def oracle_repr(m):
    """patch.diff's behaviour: the REAL patched ResolverMatch.__repr__."""
    return repr(m)


# --- corpus: callables spanning the func branches ----------------------------

def plain_view(request, *args, **kwargs):
    pass


class ClassBasedView:
    def __call__(self, request, *args, **kwargs):
        pass


_PARTIAL = functools.partial(plain_view, template_name="template.html")
_NESTED_PARTIAL = functools.partial(_PARTIAL, template_name="nested_partial.html")
_WRAPPED_PARTIAL = functools.update_wrapper(
    functools.partial(plain_view, template_name="template.html"), plain_view,
)
_CBV = ClassBasedView()

FUNCS = [plain_view, _CBV, _PARTIAL, _NESTED_PARTIAL, _WRAPPED_PARTIAL]

# url-name / route domain: the modeled slice is the ASCII plane — identifiers,
# dashes, slashes, regex-route chars, backslash (regex escapes like \d are
# routine in real URLconf patterns), both quote characters, AND control
# characters (tab/LF/CR/NUL/ESC/DEL), so the shadow's `quoted`/`escChar`
# escaping, control-code rendering and delimiter choice are all exercised
# against real Python repr().
_CONTROLS = "\t\n\r\x00\x1b\x7f\x01\x0b"
NAME_ALPHABET = string.ascii_letters + string.digits + "-_" + "\\'\"" + _CONTROLS
ROUTE_ALPHABET = (string.ascii_letters + string.digits + "/^$()[]+*-_."
                  + "\\'\"<>?{}" + _CONTROLS)


def rand_str(rng, alphabet, maxlen=24):
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(0, maxlen)))


def rand_args(rng):
    n = rng.randint(0, 3)
    return tuple(rand_str(rng, NAME_ALPHABET, 6) for _ in range(n))


def rand_kwargs(rng):
    n = rng.randint(0, 2)
    return {rand_str(rng, string.ascii_lowercase, 5) or "k": rand_str(rng, NAME_ALPHABET, 6)
            for _ in range(n)}


def rand_namelist(rng):
    n = rng.randint(0, 3)
    return [rand_str(rng, string.ascii_lowercase, 6) or "a" for _ in range(n)]


def make_match(rng):
    func = rng.choice(FUNCS)
    args = rand_args(rng)
    kwargs = rand_kwargs(rng)
    url_name = None if rng.random() < 0.25 else (rand_str(rng, NAME_ALPHABET, 16) or "n")
    app_names = rand_namelist(rng)
    namespaces = rand_namelist(rng)
    route = None if rng.random() < 0.25 else (rand_str(rng, ROUTE_ALPHABET, 24) or "r")
    return ResolverMatch(func, args, kwargs, url_name=url_name,
                         app_names=app_names, namespaces=namespaces, route=route)


def boundary_matches():
    """Deterministic coverage: each func branch, None vs present name/route,
    empty vs non-empty containers."""
    out = []
    for func in FUNCS:
        out.append(ResolverMatch(func, (), {}, url_name=None,
                                 app_names=[], namespaces=[], route=None))
        out.append(ResolverMatch(func, ("42", "37"), {"k": "v"},
                                 url_name="no-kwargs", app_names=["app"],
                                 namespaces=["ns"], route="^no_kwargs/([0-9]+)/$"))
    # the three F2P partial cases (func rendered via repr)
    for tn in ("template.html", "nested_partial.html"):
        p = functools.partial(plain_view, template_name=tn)
        out.append(ResolverMatch(p, (), {}, url_name="partial",
                                 app_names=[], namespaces=[], route="partial/"))
    # escaping / delimiter-choice boundary cases: backslash regex routes
    # (repr doubles the backslash), single/double quotes (repr flips the
    # wrapping delimiter or escapes), control characters (repr renders their
    # escape codes), and mixes of all of these.
    for tricky in (r"^articles/(?P<year>\d{4})/$", "a'b", 'a"b', "a'b\"c",
                   "\\", "'", '"', r"\'", r"back\slash-and-'quote'",
                   "a\tb", "a\nb", "a\rb", "a\x00b", "a\x1bb", "a\x7fb",
                   "\t", "\x00", "tab\tand'quote'", "nl\nand\\back"):
        out.append(ResolverMatch(plain_view, (), {}, url_name=tricky,
                                 app_names=[], namespaces=[], route=tricky))
    return out


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    def check(m):
        nonlocal count
        count += 1
        shadow = shadow_match_repr(m)
        oracle = oracle_repr(m)
        if shadow != oracle:
            disagreements.append((shadow, oracle))

    for m in boundary_matches():
        check(m)

    for _ in range(N_FUZZ):
        check(make_match(rng))
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for sh, orc in disagreements:
            print("  shadow=%r oracle=%r" % (sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of resolverMatchRepr agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
