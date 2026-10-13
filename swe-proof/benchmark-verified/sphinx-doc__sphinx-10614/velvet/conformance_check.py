#!/usr/bin/env python3
"""G-CONF differential conformance for sphinx-doc__sphinx-10614 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the produced link map:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`buildLinkMap`
              + the pure `refEntry`/`linkMap` fold + the deep `afterLastHash`)
              transliterated to Python, over the real repo types (str / None /
              bool), via the mapping.md bijection. The A-reference `afterLastHash`
              is exercised as its OWN deep model here (its equality to the real
              rsplit is G-AX's job); G-CONF isolates the R/I refinement.
  * ORACLE  — `patch.diff`'s behaviour: the gold-patched link-map construction
              of `html_visit_inheritance_diagram`, transliterated VERBATIM.

ORACLE CHOICE — why we transliterate the patched loop instead of invoking the
real `html_visit_inheritance_diagram`:
  The real visitor needs a fully-built Sphinx HTML5Translator, a populated
  `builder.env.config`, a resolved doctree of `inheritance_diagram` nodes with
  intersphinx-resolved `pending_xref` children, and graphviz — i.e. essentially
  the F2P test harness. Building that purely to read back the `urls` dict is
  impractical and would not isolate the modeled change. So, per the worker
  prompt, the ORACLE is the patched control/data flow transliterated verbatim
  from the gold-patched sphinx/ext/inheritance_diagram.py:411-423:

      for child in pending_xrefs:
          if child.get('refuri') is not None:
              if not child.get('internal', True):
                  refname = child['refuri'].rsplit('#', 1)[-1]
              else:
                  refname = child['reftitle']
              urls[refname] = child.get('refuri')
          elif child.get('refid') is not None:
              if graphviz_output_format == 'SVG':
                  urls[child['reftitle']] = current_filename + '#' + child.get('refid')
              else:
                  urls[child['reftitle']] = '#' + child.get('refid')

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. stdlib only; fuzz seed pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 10614
N_FUZZ = 100_000


# ---- SHADOW: Solution.lean transliterated ---------------------------------

def after_last_hash(s):
    """`afterLastHash` deep model: maximal '#'-free suffix of s."""
    tail = []
    for ch in reversed(s):
        if ch == '#':
            break
        tail.append(ch)
    return "".join(reversed(tail))


def ref_entry(is_svg, page, c):
    """`refEntry`: the zero/one (key, url) pair a child contributes."""
    if c["target"] is not None:
        uri = c["target"]
        key = after_last_hash(uri) if c["external"] else c["name"]
        return [(key, uri)]
    if c["anchor"] is not None:
        link = (page if is_svg else "") + "#" + c["anchor"]
        return [(c["name"], link)]
    return []


def shadow_build(refs, is_svg, page):
    """`buildLinkMap`/`linkMap`: in-order concatenation of per-child entries,
    collapsed into the produced dict (mapping.md §2: dict ↔ assoc-list)."""
    urls = {}
    for c in refs:
        for (k, v) in ref_entry(is_svg, page, c):
            urls[k] = v
    return urls


# ---- ORACLE: gold-patched inheritance_diagram.py:411-423 transliterated ----

def oracle_build(refs, is_svg, page):
    urls = {}
    graphviz_output_format = 'SVG' if is_svg else 'PNG'
    current_filename = page
    for child in refs:
        refuri = child["target"]
        refid = child["anchor"]
        internal = not child["external"]   # child.get('internal', True)
        if refuri is not None:
            if not internal:
                refname = refuri.rsplit('#', 1)[-1]
            else:
                refname = child["name"]    # child['reftitle']
            urls[refname] = refuri
        elif refid is not None:
            if graphviz_output_format == 'SVG':
                urls[child["name"]] = current_filename + '#' + refid
            else:
                urls[child["name"]] = '#' + refid
    return urls


# ---- fuzzing --------------------------------------------------------------

def rand_str(rng, alphabet, lo=0, hi=12):
    n = rng.randint(lo, hi)
    return "".join(rng.choice(alphabet) for _ in range(n))


def rand_ref(rng):
    name_pool = list("ABC.#_/") + ["é"]
    uri_pool = list("abc.#/:_xyz019") + ["é"]
    name = rand_str(rng, name_pool, 1, 10)
    # kind: 0 = target, 1 = anchor-only, 2 = neither
    kind = rng.randint(0, 2)
    if kind == 0:
        target = rand_str(rng, uri_pool, 0, 16)
        anchor = None
    elif kind == 1:
        target = None
        anchor = rand_str(rng, name_pool, 0, 8)
    else:
        target = None
        anchor = None
    external = (rng.random() < 0.5)
    return {"name": name, "target": target, "anchor": anchor, "external": external}


def boundary_cases():
    """F2P-shaped and edge children lists, on both SVG and non-SVG."""
    cases = []
    # the intersphinx external ref (subdir.other.Bob) the F2P test adds
    ext = {"name": "subdir.other.Bob", "target": "https://example.org/foo.html#subdir.other.Bob",
           "anchor": None, "external": True}
    # an in-project documented class (refuri, internal)
    intern = {"name": "test.DocHere", "target": "../test.html#test.DocHere",
              "anchor": None, "external": False}
    # a fragment-only ref (refid) — the original SVG-404 case
    frag = {"name": "test.Foo", "target": None, "anchor": "test.Foo", "external": False}
    # contributes nothing
    empty = {"name": "test.Bare", "target": None, "anchor": None, "external": False}
    bases = [
        [],
        [ext],
        [intern],
        [frag],
        [empty],
        [ext, intern, frag, empty],
        [frag, intern, ext],
        [intern, intern],   # same reftitle, different... (single diagram: distinct in practice)
    ]
    for page in ["", "index.html", "subdir/index.html"]:
        for is_svg in (True, False):
            for refs in bases:
                cases.append((refs, is_svg, page))
    return cases


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    for refs, is_svg, page in boundary_cases():
        count += 1
        if shadow_build(refs, is_svg, page) != oracle_build(refs, is_svg, page):
            disagreements.append((refs, is_svg, page,
                                  shadow_build(refs, is_svg, page),
                                  oracle_build(refs, is_svg, page)))

    pages = ["", "index.html", "a/b/index.html", "deep/nested/page.html"]
    for _ in range(N_FUZZ):
        count += 1
        k = rng.randint(0, 6)
        refs = [rand_ref(rng) for _ in range(k)]
        is_svg = (rng.random() < 0.5)
        page = rng.choice(pages)
        sh = shadow_build(refs, is_svg, page)
        orc = oracle_build(refs, is_svg, page)
        if sh != orc:
            disagreements.append((refs, is_svg, page, sh, orc))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for d in disagreements:
            print("  refs=%r is_svg=%r page=%r shadow=%r oracle=%r" % d)
        return 1
    print("G-CONF OK: R/I shadow of buildLinkMap agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
