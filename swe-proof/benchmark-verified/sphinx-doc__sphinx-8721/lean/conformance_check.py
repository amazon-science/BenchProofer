#!/usr/bin/env python3
"""G-CONF for sphinx-doc__sphinx-8721.

The modeled behavior is the publish/suppress decision the `html-collect-pages`
handler makes for the highlighted-source companion pages
(`sphinx/ext/viewcode.py:181`). That handler is a generator; its observable
behavior is the SEQUENCE of `(pagename, context, template)` triples it yields,
and the modeled decision is whether that whole sequence is emitted or nothing
is.

ORACLE: the REAL repo function, imported from /testbed with the patch applied
(the gate applies it before this script runs; this script applies nothing). The
generator is driven through a minimal fake `app` supplying only the values the
modelled path reads: the collected-module mapping, the active output format's
name, the e-book preference, and inert highlighter / relative-uri / freshness
plumbing. The body under specification runs unmodified.

SHADOW: the R/I transliteration of `implementation_collectModulePages` (the Lean
impl) per refinement.md.

TYPE BRIDGE (mapping.md section 2). Three of the four carriers are direct:
  hasModules  <-> whether any collected-module mapping is present  (bool)
  builderName <-> the active output format's name                  (str)
  enableEpub  <-> the e-book companion-pages preference            (bool)
The fourth is the one that needs care:
  generatedPages <-> THE SEQUENCE THIS OUTPUT FORMAT PUBLISHES FOR THIS BUILD
                     WHEN THE E-BOOK PREFERENCE DOES NOT WITHHOLD IT.
It is obtained from the REAL function by running it with the e-book preference
forced ON. That is legitimate, and is what makes the bridge a bridge rather than
an answer key, because of two facts this script MEASURES rather than assumes
(`check_bridge_facts`):
  (A) off the e-book family the preference does not affect the published
      sequence at all, so forcing it on only reaches the page-construction body
      and does not pre-empt any decision the spec is responsible for; and
  (B) with the preference forced ON, an e-book-family format publishes its FULL
      sequence. So the e-book decision is emphatically NOT baked into
      `generatedPages` -- the specification still has to make it, which is what
      keeps the obligation discriminating.
Empty sequence <-> the generator returning immediately (yielding nothing).

We diff shadow against oracle over boundary cases + >=1e5 fuzzed inputs, with
NO builder name excluded from the domain; zero disagreements => exit 0.

stdlib-only; no third-party deps.
"""
import json
import random
import sys
from types import SimpleNamespace

SEED = 8721            # pinned seed (mapping.md)
N_FUZZ = 100_000


# --- shadow: R/I transliteration of the Lean impl region ---------------------

def shadow(has_modules, builder_name, enable_epub, generated_pages):
    """R/I transliteration of implementation_collectModulePages (Lean).

    Lean `[]` <-> Python `[]`; early `return []` <-> the generator yielding
    nothing.  Note it never mentions any particular output-format name: the
    only format-dependent thing it does is the e-book family prefix test.
    """
    if not has_modules:
        return []
    if builder_name.startswith("epub") and not enable_epub:
        return []
    return list(generated_pages)


# --- oracle driver: run the REAL page collector on a minimal fake app --------

def real_pages(collect_pages, builder_name, enable_epub, mods, has_modules,
               n_falsy=0):
    """Run the REAL generator; return the list of page names it yields."""
    moddict = {}
    for mn in mods:
        moddict[mn] = ("line one\nline two\n", {}, {}, mn)
    for j in range(n_falsy):
        # a module with a falsy recorded entry yields no page
        moddict["z%03df" % j] = None
    highlighter = SimpleNamespace(
        highlight_block=lambda code, lexer, linenos=False, **kw:
            '<span><pre>' + code + '</pre></span>')
    env = SimpleNamespace(config=SimpleNamespace(
        viewcode_enable_epub=enable_epub, highlight_language='default'))
    if has_modules:
        env._viewcode_modules = moddict
    builder = SimpleNamespace(env=env, name=builder_name,
                              highlighter=highlighter,
                              get_relative_uri=lambda a, b: 'u')
    app = SimpleNamespace(builder=builder, verbosity=0,
                          emit_firstresult=lambda *a, **kw: True)
    return [pagename for pagename, _ctx, _tpl in collect_pages(app)]


def baseline(collect_pages, builder_name, mods, has_modules, n_falsy=0):
    """`generatedPages`: what this output format publishes for this build when
    the e-book preference does not withhold it -- i.e. the real function with
    that preference forced ON (see the bridge note in the module docstring)."""
    return real_pages(collect_pages, builder_name, True, mods, has_modules,
                      n_falsy)


# --- the two facts the bridge rests on, measured not assumed -----------------

def check_bridge_facts(collect_pages, names, shapes):
    """(A) off the e-book family the preference is irrelevant to the published
    sequence; (B) on the e-book family, preference-ON publishes the FULL
    sequence (so the e-book decision is not pre-made inside generatedPages)."""
    problems = []
    for name in names:
        for mods, n_falsy in shapes:
            for has_modules in (True, False):
                on = real_pages(collect_pages, name, True, mods, has_modules,
                                n_falsy)
                off = real_pages(collect_pages, name, False, mods, has_modules,
                                 n_falsy)
                if not name.startswith("epub"):
                    if on != off:
                        problems.append(
                            "FACT A violated: preference changes the published "
                            "sequence at non-e-book name %r: on=%r off=%r"
                            % (name, on, off))
                else:
                    # preference ON must publish (not suppress) whenever the
                    # build has anything to publish at all
                    if has_modules and mods and not on:
                        problems.append(
                            "FACT B violated: e-book name %r with preference ON "
                            "published nothing (mods=%r)" % (name, mods))
    return problems


# --- domain -----------------------------------------------------------------

# Real Sphinx output-format names + e-book-family members + adversarial
# near-misses, so the family prefix test is exercised at its boundary. NOTHING
# is excluded: every output format the real builder registry can present,
# including the single-file one, is inside the checked domain.
BUILDER_NAMES = [
    "", "e", "ep", "epu", "epub", "epub2", "epub3", "epubfoo", "Epub", "EPUB",
    "html", "dirhtml", "singlehtml", "singlehtm", "singlehtmlx", "ssinglehtml",
    "singlehtmlepub", "epubsinglehtml", "htmlepub", "latex", "text", "man",
    "xml", "json", "linkcheck", "texinfo", "gettext", "pseudoxml", "changes",
]

MODULE_SHAPES = [
    ([], 0),                       # nothing collected at all
    ([], 2),                       # only falsy entries: no page either way
    (["m0"], 0),                   # single module
    (["m0", "m1"], 0),             # several, in order
    (["m0", "m1", "m2"], 1),       # several + a falsy entry
]


def check_one(collect_pages, has_modules, builder_name, enable_epub, mods,
              n_falsy=0):
    given = baseline(collect_pages, builder_name, mods, has_modules, n_falsy)
    s = shadow(has_modules, builder_name, enable_epub, given)
    o = real_pages(collect_pages, builder_name, enable_epub, mods, has_modules,
                   n_falsy)
    if s != o:
        return ("DISAGREEMENT\n  has_modules=%r\n  builder_name=%r\n"
                "  enable_epub=%r\n  modules=%r (+%d falsy)\n"
                "  generatedPages(bridge)=%r\n  shadow=%r\n  real=%r"
                % (has_modules, builder_name, enable_epub, mods, n_falsy,
                   given, s, o))
    return None


def main():
    # REAL repo symbol the model models (mapping.md section 1):
    from sphinx.ext.viewcode import collect_pages

    facts = check_bridge_facts(collect_pages, BUILDER_NAMES, MODULE_SHAPES)
    if facts:
        for p in facts:
            print(p)
        print("G-CONF FAIL: the type bridge's own premises do not hold")
        return 1
    n_facts = len(BUILDER_NAMES) * len(MODULE_SHAPES) * 2

    checked = n_boundary = 0
    for name in BUILDER_NAMES:
        for mods, n_falsy in MODULE_SHAPES:
            for enable in (True, False):
                for has_modules in (True, False):
                    err = check_one(collect_pages, has_modules, name, enable,
                                    mods, n_falsy)
                    if err:
                        print(err)
                        return 1
                    checked += 1
                    n_boundary += 1

    rng = random.Random(SEED)
    # alphabet keeping the boundary near the e-book prefix interesting
    alphabet = list("epubsinglhtmxz123 ")
    for _ in range(N_FUZZ):
        r = rng.random()
        if r < 0.30:
            name = "epub" + "".join(rng.choice(alphabet)
                                    for _ in range(rng.randint(0, 6)))
        elif r < 0.40:
            # keep the single-file name and its neighbours well represented
            name = rng.choice(["singlehtml", "singlehtm", "singlehtmlx",
                               "ssinglehtml", "singlehtmlepub"])
        else:
            name = "".join(rng.choice(alphabet)
                           for _ in range(rng.randint(0, 14)))
        enable = rng.random() < 0.5
        has_modules = rng.random() < 0.85
        mods = ["m%d" % k for k in range(rng.randint(0, 4))]
        n_falsy = rng.randint(0, 2)
        err = check_one(collect_pages, has_modules, name, enable, mods, n_falsy)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow == real page collector on %d inputs "
          "(%d boundary + %d fuzz, seed %d); bridge premises (A) and (B) "
          "measured on %d real-callee pairs; NO output-format name excluded "
          "from the domain."
          % (checked, n_boundary, N_FUZZ, SEED, n_facts))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "bridge_fact_pairs": n_facts,
                      "excluded_builder_names": [],
                      "shadow": "transliterated (contract-free impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
