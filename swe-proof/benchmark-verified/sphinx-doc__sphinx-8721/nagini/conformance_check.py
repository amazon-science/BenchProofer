#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8721 (nagini).

SHADOW: the impl regions of model.py (`module_source_pages` and its verified
deep helper `begins_with`), copied verbatim below with the contract calls
(Requires/Ensures/Invariant/Assert, incl. the ghost lemma Assert) stripped;
every executable statement is otherwise byte-identical. The @Pure helpers
(`prefix_eq`, `lit_epub`, `suppressed`) copy over as plain functions on a
tuple-backed PSeq shim (drop/len/index/+); they are used only for an internal
sanity cross-check. There are no @ContractOnly callees in this bundle (no
consumed axioms).

ORACLE: the REAL repo function the model models per mapping.md —
`sphinx.ext.viewcode.collect_pages(app)`, imported from /testbed (the gate
applies the diff before this script runs; this script never applies any diff
itself). The generator is driven through a minimal fake `app` object that
supplies only the upstream inputs the modelled path reads: the builder name,
the module-pages preference for electronic-book output, the recorded
per-module source entries, and inert highlighter / relative-uri / page-
regeneration plumbing (all upstream of the modelled behaviour per
mapping.md section 1). The generator body under specification runs unmodified.

Type bridge (mapping.md section 2):
  - output-target (builder) name str -> name: List[int] of Unicode code
    points (name[k] == ord(builder_name[k]));
  - the module-pages preference bool -> enable_epub: bool (identity);
  - the recorded module entries -> modules: List[int], one integer carrier
    per module whose recorded entry is truthy, in the (sorted) order the
    generator presents them; modules with falsy recorded entries yield no
    page and have no carrier;
  - the yielded page set -> Result(): List[int]: each yielded per-module page
    maps back (via its page name) to that module's carrier; the trailing
    overview/index page and the page *content* are unchanged by the patch,
    abstracted away by the model (mapping.md section 2), and excluded from
    the comparison.

Input domain: the modelled contract covers every output target EXCEPT the
single-file HTML target — mapping.md section 1 and refinement.md section A
scope that co-change guard OUT of the modelled, consumer-visible behavioural
contract (it is untested and carried only by patch.diff), so generation
excludes exactly that one builder name (`singlehtml`) and nothing else.
All other Requires-satisfying inputs (any code-point name, any preference,
any recorded-entry multiset) are in scope.

>= 1e5 Requires-satisfying inputs: boundary cases (electronic-book names and
near-miss prefixes crossed with both preference values and several
module-entry shapes, incl. empty and falsy-entry mixes) plus 100000 fuzz
cases. Pinned fuzz seed: 8721.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random; no hypothesis needed).
"""
import json
import random
import sys
from types import SimpleNamespace

SEED = 8721
N_FUZZ = 100_000

# The single-file output-target name excluded from the modelled contract
# (disclosed modeling boundary, mapping.md section 1 / refinement.md A).
EXCLUDED_TARGET = "singlehtml"


# --- PSeq / ToSeq shim: pure Viper sequences as plain tuples ------------------

class PSeq(tuple):
    def __new__(cls, *elems):
        return super().__new__(cls, elems)

    def drop(self, n):
        return PSeq(*tuple.__getitem__(self, slice(n, None)))

    def take(self, n):
        return PSeq(*tuple.__getitem__(self, slice(None, n)))

    def __add__(self, other):
        return PSeq(*(tuple.__add__(self, tuple(other))))


def ToSeq(xs):
    return PSeq(*xs)


# --- pure region of model.py, contracts stripped (sanity cross-check only) ----

def prefix_eq(s, lit):
    if len(lit) == 0:
        return True
    if len(s) == 0:
        return False
    return s[0] == lit[0] and prefix_eq(s.drop(1), lit.drop(1))


def lit_epub():
    # 'epub'
    return PSeq(101, 112, 117, 98)


def suppressed(name, enable_epub):
    return prefix_eq(name, lit_epub()) and not enable_epub


# --- impl regions of model.py, verbatim, contract calls stripped --------------

def begins_with(name, lit):
    n = len(lit)
    if n > len(name):
        return False
    ok = True
    i = n
    while i > 0:
        if name[i - 1] != lit[i - 1]:
            ok = False
        i = i - 1
    return ok


def module_source_pages(name, enable_epub, modules):
    empty = []  # type: list
    ep = [101, 112, 117, 98]  # type: list
    if begins_with(name, ep) and not enable_epub:
        return empty
    # The guard did not fire: the target is not suppressed.
    result = []  # type: list
    i = 0
    n = len(modules)
    while i < n:
        result = result + [modules[i]]
        i = i + 1
    return result


# --- oracle driver: run the REAL page collector on a minimal fake app ---------

INDEX_PAGENAME = "_modules/index"


def real_module_carriers(collect_pages, builder_name, enable_epub,
                         carriers, n_falsy):
    """Run the REAL collect_pages generator; return the list of carriers of
    the per-module pages it yields, in yield order (the overview/index page
    is abstracted away by the model and dropped from the comparison).

    Module names are chosen so that lexicographic (iteration) order equals
    carrier index order; `n_falsy` modules with a falsy recorded entry are
    interleaved (they yield no page and carry no carrier)."""
    entry_code = "line one\nline two\n"
    moddict = {}
    t_map = {}
    for i, c in enumerate(carriers):
        mn = "m%03d" % i
        moddict[mn] = (entry_code, {}, {}, mn)
        t_map["_modules/" + mn] = c
    for j in range(n_falsy):
        # sorts between "m%03d" names without disturbing their order
        moddict["m%03df" % j] = None

    highlighter = SimpleNamespace(
        highlight_block=lambda code, lexer, linenos=False, **kw:
            '<span><pre>' + code + '</pre></span>')
    env = SimpleNamespace(
        _viewcode_modules=moddict,
        config=SimpleNamespace(viewcode_enable_epub=enable_epub,
                               highlight_language='default'))
    builder = SimpleNamespace(env=env, name=builder_name,
                              highlighter=highlighter,
                              get_relative_uri=lambda a, b: 'u')
    # emit_firstresult truthy => the page-freshness probe always says
    # regenerate (upstream plumbing, not part of the modelled behaviour)
    app = SimpleNamespace(builder=builder, verbosity=0,
                          emit_firstresult=lambda *a, **kw: True)

    out = []
    for pagename, _context, _templ in collect_pages(app):
        if pagename == INDEX_PAGENAME:
            continue
        if pagename not in t_map:
            raise AssertionError("unexpected page %r (a falsy-entry module "
                                 "must yield nothing)" % pagename)
        out.append(t_map[pagename])
    return out


# --- differential check --------------------------------------------------------

def check_one(collect_pages, builder_name, enable_epub, carriers, n_falsy=0):
    name_cps = [ord(ch) for ch in builder_name]
    shadow = module_source_pages(name_cps, enable_epub, list(carriers))

    # internal sanity: the pure suppression predicate agrees with the shadow
    if suppressed(ToSeq(name_cps), enable_epub):
        assert shadow == [], "shadow inconsistent with its own pure region"
    else:
        assert shadow == list(carriers), \
            "shadow inconsistent with its own pure region"

    real = real_module_carriers(collect_pages, builder_name, enable_epub,
                                carriers, n_falsy)
    if real != shadow:
        return ("DISAGREEMENT\n  builder_name=%r\n  enable_epub=%r\n"
                "  modules=%r (plus %d falsy entries)\n"
                "  shadow=%r\n  real=%r"
                % (builder_name, enable_epub, list(carriers), n_falsy,
                   shadow, real))
    return None


def boundary_cases():
    """Names pinning the gate boundary (electronic-book names, near-miss
    prefixes, ordinary targets) crossed with both preference values and
    several module-entry shapes."""
    names = [
        "", "html", "dirhtml", "epub", "epub2", "epub3", "epubfoo",
        "ep", "e", "Epub", "EPUB", "epu", "pub", "json", "latex", "text",
        "man", "texinfo", "linkcheck", "xml", "pseudoxml", "gettext",
        "epubsinglehtml",
    ]
    module_shapes = [
        ([], 0),           # no recorded entries at all
        ([], 2),           # only falsy entries: no page either way
        ([7], 0),          # single module
        ([1, 2, 3], 0),    # several, in order
        ([5, 5, 5], 1),    # duplicate carrier values + a falsy entry
        ([9, 0, 4, 4, 2, 8, 1, 3], 2),   # larger mix
    ]
    for name in names:
        for enable in (True, False):
            for carriers, n_falsy in module_shapes:
                yield name, enable, carriers, n_falsy


def main():
    # REAL repo symbol (the generator the model models, per mapping.md):
    from sphinx.ext.viewcode import collect_pages

    checked = 0
    n_boundary = 0
    for name, enable, carriers, n_falsy in boundary_cases():
        err = check_one(collect_pages, name, enable, carriers, n_falsy)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    # alphabet keeping the boundary near the electronic-book prefix
    # interesting (near-prefixes, not just random noise)
    alphabet = list("epubsinglhtmxz123 ")
    for _ in range(N_FUZZ):
        r = rng.random()
        if r < 0.30:
            # force an electronic-book-prefixed name
            n = rng.randint(0, 6)
            name = "epub" + "".join(rng.choice(alphabet) for _ in range(n))
        else:
            n = rng.randint(0, 14)
            name = "".join(rng.choice(alphabet) for _ in range(n))
        if name == EXCLUDED_TARGET:
            # outside the modelled contract (disclosed modeling boundary)
            name = name + "x"
        enable = rng.random() < 0.5
        carriers = [rng.randint(0, 9) for _ in range(rng.randint(0, 4))]
        n_falsy = rng.randint(0, 2)
        err = check_one(collect_pages, name, enable, carriers, n_falsy)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real page collector on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
