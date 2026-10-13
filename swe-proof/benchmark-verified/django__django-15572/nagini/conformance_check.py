#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15572 (nagini).

SHADOW: the impl region of model.py — `collect_direct_locations` and
`collect_provider_locations` — copied verbatim below with the contract calls
(Requires/Ensures/Invariant/Assert) stripped. The impl calls no @Pure helper
directly (the joined-location map is the identity on tokens there), so no
PSeq shim is needed; the one @ContractOnly callee, `beneath_framework`, is
bridged to the REAL repo predicate `django.utils.autoreload.is_django_path`
through the per-case token table (see the type bridge below).

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.template.autoreload.get_template_directories()`. The gate applies
patch.diff to /testbed before this script runs and sets PYTHONPATH=/testbed,
so the import resolves to the patched code. Each case feeds the oracle by
installing a fresh template-engine configuration on the module-global
EngineHandler (one DjangoTemplates backend whose DIRS list is the directly-
declared source and whose single filesystem loader's dirs list is the
auxiliary-provider source), then calling the function and collecting its
returned set of watched locations.

TYPE BRIDGE (mapping.md section 2): a configured directory entry (a str or a
Path) maps to an int token — the reserved token 0 iff the entry is falsy
(only the empty string is), a distinct positive token per position otherwise,
with a table remembering which entry each token stands for. An emitted token
t maps back to the concrete watched location `cwd / to_path(entry_of(t))`.
The model's ordered token list refines the repo's location set (order- and
duplicate-insensitive), so the comparison is: set-of-locations mapped from
the shadow's two token lists == the oracle's returned set. This also stays
faithful on truthy dot-path entries: they carry a nonzero token yet map back
onto the base location, exactly matching what the real join produces, and the
set comparison absorbs the collapse (mapping.md's scope note — distinctness
of present entries is never assumed here, only the token->location map).

The @ContractOnly callee bridge: `beneath_framework(token)` calls the REAL
`is_django_path` on the entry the token stands for.

Input domain: the model's preconditions require only two Python lists of int
tokens; the corresponding repo-level domain is two lists of str/Path
directory entries (the only entry kinds the configuration machinery accepts).
Boundary cases cover the empty-entry scenarios (an empty string in either
source, alone and mixed), dot-path entries, entries beneath the framework's
own installation tree, Path-typed entries, and empty lists; fuzz draws mixed
lists of all those entry kinds for both sources.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz cases (each
case is one (direct-entries, provider-entries) input pair to the two modeled
functions). Pinned fuzz seed: 155720.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
from pathlib import Path

SEED = 155720
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contracts stripped -----------------
# (`beneath_framework` is the @ContractOnly callee; it is bound per-case to the
# REAL repo predicate through the token table — see _run_shadow.)

_BENEATH_FRAMEWORK = None  # set per-case: token -> bool via the real predicate


def beneath_framework(entry):
    return _BENEATH_FRAMEWORK(entry)


def collect_direct_locations(entries):
    result = []  # type: List[int]
    i = len(entries)
    while i > 0:
        d = entries[i - 1]
        if d != 0:
            result = [d] + result
        i = i - 1
    return result


def collect_provider_locations(entries):
    result = []  # type: List[int]
    i = len(entries)
    while i > 0:
        d = entries[i - 1]
        if d != 0 and not beneath_framework(d):
            result = [d] + result
        i = i - 1
    return result


# --- bridge + differential ------------------------------------------------------

def _tokenize(entries):
    """Entry list -> (token list, token -> entry table). Reserved token 0 for
    the falsy (empty) entry; a fresh positive token per present entry."""
    tokens = []
    table = {}
    for idx, e in enumerate(entries):
        if not e:
            tokens.append(0)
        else:
            t = idx + 1
            table[t] = e
            tokens.append(t)
    return tokens, table


def _run_shadow(direct_entries, provider_entries, is_django_path, cwd, to_path):
    """Shadow of the two modeled collection sites, mapped back to the concrete
    location set they contribute."""
    global _BENEATH_FRAMEWORK
    d_tokens, d_table = _tokenize(direct_entries)
    p_tokens, p_table = _tokenize(provider_entries)
    # @ContractOnly callee -> REAL repo predicate on the entry the token
    # stands for (the predicate is only ever consulted on present entries).
    _BENEATH_FRAMEWORK = lambda t: is_django_path(p_table[t])
    out_d = collect_direct_locations(d_tokens)
    out_p = collect_provider_locations(p_tokens)
    locs = set()
    for t in out_d:
        locs.add(cwd / to_path(d_table[t]))
    for t in out_p:
        locs.add(cwd / to_path(p_table[t]))
    return locs


class _CaseError(Exception):
    pass


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(TEMPLATES=[])
        try:
            django.setup()
        except Exception:
            pass

    # REAL patched function under test + the real helpers the bridge uses.
    from django.template import autoreload as real_autoreload
    from django.template import engines
    from django.utils._os import to_path
    from django.utils.autoreload import is_django_path

    cwd = Path.cwd()
    framework_root = Path(django.__file__).parent

    def oracle(direct_entries, provider_entries):
        """Feed one configuration to the module-global engine handler and call
        the real patched function."""
        engines._templates = [{
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": list(direct_entries),
            "APP_DIRS": False,
            "OPTIONS": {
                "loaders": [(
                    "django.template.loaders.filesystem.Loader",
                    list(provider_entries),
                )],
            },
        }]
        engines._engines = {}
        engines.__dict__.pop("templates", None)  # drop the cached property
        return real_autoreload.get_template_directories()

    def check_case(direct_entries, provider_entries):
        real_out = oracle(direct_entries, provider_entries)
        shadow_out = _run_shadow(direct_entries, provider_entries,
                                 is_django_path, cwd, to_path)
        if shadow_out != real_out:
            raise _CaseError(
                "DISAGREEMENT\n  direct=%r\n  provider=%r\n  shadow=%r\n"
                "  real=%r" % (direct_entries, provider_entries,
                               sorted(map(str, shadow_out)),
                               sorted(map(str, real_out))))

    fw = str(framework_root / "forms" / "templates")   # beneath the framework
    fw2 = str(framework_root / "contrib" / "admin" / "templates")
    boundary = [
        ([], []),
        ([""], []),                       # the empty-entry scenario, site 1
        ([], [""]),                       # the empty-entry scenario, site 2
        ([""], [""]),
        (["", "", ""], ["", ""]),
        (["templates"], []),
        ([], ["templates"]),
        (["templates", ""], ["", "other_templates"]),
        (["/abs/templates_dir", ""], ["/abs/loader_dir"]),
        ([Path("templates_extra")], [Path("loader_extra")]),
        ([Path("")], [Path("")]),         # Path-typed: truthy, base-collapsing
        (["."], ["./."]),                 # dot-paths: truthy, base-collapsing
        (["./", "././."], [Path(".")]),
        ([], [fw]),                       # beneath-framework: filtered, site 2
        ([fw], []),                       # ...but NOT filtered at site 1
        (["a", fw, ""], ["b", fw2, "", fw]),
        (["dir with spaces"], ["../up_one"]),
        (["x/y/z", "x/y/z"], ["x/y/z"]),  # duplicates across sources
        (["", "templates", "", "."], ["", fw, "templates", ""]),
    ]

    parts = ["a", "b", "templates", "x", "y", "z", "dir", "tpl", "sub", "9"]

    def rand_entry(rng, provider_side):
        r = rng.random()
        if r < 0.15:
            return ""                                          # empty entry
        if r < 0.22:
            return rng.choice([".", "./.", "./", "././."])     # dot-paths
        if provider_side and r < 0.34:
            # beneath the framework tree (real filter territory)
            return str(framework_root / rng.choice(parts) / rng.choice(parts))
        if r < 0.44:
            n = rng.randint(1, 3)
            return Path("/".join(rng.choice(parts) for _ in range(n)))
        if r < 0.54:
            n = rng.randint(1, 3)
            return "/" + "/".join(rng.choice(parts) for _ in range(n))
        n = rng.randint(1, 3)
        return "/".join(rng.choice(parts) for _ in range(n))

    def rand_case(rng):
        nd = rng.randint(0, 5)
        np = rng.randint(0, 5)
        return ([rand_entry(rng, False) for _ in range(nd)],
                [rand_entry(rng, True) for _ in range(np)])

    checked = 0
    try:
        for de, pe in boundary:
            check_case(de, pe)
            checked += 1
        rng = random.Random(SEED)
        for _ in range(N_FUZZ):
            de, pe = rand_case(rng)
            check_case(de, pe)
            checked += 1
    except _CaseError as e:
        print(str(e))
        return 1

    print("G-CONF OK: shadow impl == real watched-location collection on %d "
          "input pairs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callee bound to the real "
                                "repo predicate)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
