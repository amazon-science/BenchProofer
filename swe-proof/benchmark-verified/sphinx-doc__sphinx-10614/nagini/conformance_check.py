#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-10614 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. Ghost bookkeeping locals
that existed only to feed Assert calls (old_seq / old_seq2 / old_bare / cf_seq /
empty_seq) are removed together with those Asserts; every executable statement
is otherwise byte-identical, including the `if not vector_format:` early-return
arm. The @Pure helpers copy over as plain functions on top of a tuple-backed
PSeq shim (drop/take/len/index/==). There are no @ContractOnly callees in this
bundle.

ORACLE: the REAL repo function the model models per mapping.md —
sphinx.ext.inheritance_diagram.html_visit_inheritance_diagram — imported from
/testbed (the gate applies the diff before this script runs; this script never
applies any diff itself). The function is driven with a minimal
translator/builder double whose diagram node carries exactly one
cross-reference child per probe. The image format is driven too: the double's
config carries graphviz_output_format, which the real function reads and
upper-cases at line 409, so BOTH the vector ('svg') and the raster ('png',
'pdf', ...) branches of the real code are exercised. The fully-qualified-name ->
hyperlink mapping the function builds is captured at the point it hands that
mapping to the dot generator (before any rendering I/O), so the code under test
is the real mapping-construction loop.

Type bridge (mapping.md section 2): model strings are List[int] of Unicode
code points; a real str s maps to [ord(c) for c in s] and back via chr. The
model's boolean `vector_format` maps to the real observable
`self.builder.env.config.graphviz_output_format.upper() == 'SVG'`.

Three probes per input round, each run under a chosen image format:
  (1) an explicit-destination cross-reference that is externally sourced:
      the emitted link diffs against url_for_destination(uri, vector_format),
      the registration key against trailing_name_for_destination;
  (2) an explicit-destination cross-reference that is internal: the emitted
      link diffs against url_for_destination (its key is the unchanged
      title, checked as exactly that);
  (3) a same-document-anchor cross-reference: the emitted link diffs against
      url_for_self_doc_anchor over (document output name, anchor id,
      vector_format), where the document output name is docname + out-suffix as
      the builder composes it. This probe is run under BOTH formats on every
      input, and additionally checks that the two real links DIFFER whenever
      the document name is non-empty -- i.e. that the format is a real
      observable of the code under test and not a modelling artefact.
The @Pure deep models (after_last_hash, has_scheme) are cross-checked against
the shadow outputs and the corresponding plain string operations on the same
inputs, keeping the pure region covered too.

The model's Requires are permission-only (read access), so every code-point
list qualifies; probe strings are arbitrary well-formed str values and both
values of vector_format are in the domain.

>= 1e5 Requires-satisfying inputs: structured boundary cases (each under every
format below) plus 34000 fuzz rounds x (2 single-format probes + 1 both-format
probe). Pinned fuzz seed: 106140.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
from types import SimpleNamespace

SEED = 106140
N_FUZZ_ROUNDS = 34_000

# (graphviz_output_format config value, the model's vector_format). The real
# function upper-cases the config value at :409 and compares it to 'SVG', so
# the case variants below must land on the same model input as 'svg'.
FORMATS = [("svg", True), ("SVG", True), ("Svg", True),
           ("png", False), ("PNG", False), ("pdf", False)]


# --- PSeq / ToSeq shim: pure Viper sequences as plain tuples ------------------

class PSeq(tuple):
    def __new__(cls, *elems):
        return super().__new__(cls, elems)

    def drop(self, n):
        return PSeq(*tuple.__getitem__(self, slice(n, None)))

    def take(self, n):
        return PSeq(*tuple.__getitem__(self, slice(None, n)))


def ToSeq(xs):
    return PSeq(*xs)


# --- pure region of model.py, contracts stripped ------------------------------

def is_scheme_sep_at(s, i):
    return (0 <= i and i + 2 < len(s)
            and s[i] == 58 and s[i + 1] == 47 and s[i + 2] == 47)


def has_scheme(s):
    if len(s) == 0:
        return False
    if is_scheme_sep_at(s, 0):
        return True
    return has_scheme(s.drop(1))


def after_last_hash(s):
    if len(s) == 0:
        return s
    tail = after_last_hash(s.drop(1))
    if len(tail) < len(s) - 1:
        # s.drop(1) contained a "#": its trailing component dominates
        return tail
    if s[0] == 35:
        return s.drop(1)
    return s


# --- impl region of model.py, verbatim, contract calls stripped ---------------

def url_for_destination(dest_uri, vector_format):
    result = []  # type: List[int]
    i = 0
    while i < len(dest_uri):
        result.append(dest_uri[i])
        i = i + 1
    return result


def url_for_self_doc_anchor(current_doc_name, anchor_id, vector_format):
    if not vector_format:
        # Raster image: "#" then the anchor identifier.
        bare = [35]  # type: List[int]
        m = 0
        while m < len(anchor_id):
            bare.append(anchor_id[m])
            m = m + 1
        return bare
    result = []  # type: List[int]
    i = 0
    while i < len(current_doc_name):
        result.append(current_doc_name[i])
        i = i + 1
    result.append(35)  # '#'
    j = 0
    while j < len(anchor_id):
        result.append(anchor_id[j])
        j = j + 1
    return result


def trailing_name_for_destination(dest_uri):
    # Scan backward for the last '#'. `start` indexes the beginning of the
    # trailing component.
    start = len(dest_uri)
    i = len(dest_uri)
    while i > 0:
        if dest_uri[i - 1] == 35 and start == i:
            # no '#' seen yet to the right, and this is one: trailing starts here
            start = i
        elif start == i and dest_uri[i - 1] != 35:
            # still no '#' to the right and this char is ordinary: extend left
            start = i - 1
        # else: a '#' already dominates to the right; `start` is unchanged
        i = i - 1
    result = []  # type: List[int]
    k = start
    while k < len(dest_uri):
        result.append(dest_uri[k])
        k = k + 1
    return result


# --- str <-> List[int] bridge --------------------------------------------------

def codes(s):
    return [ord(c) for c in s]


def text(cs):
    return "".join(chr(c) for c in cs)


# --- oracle harness: drive the real function, capture the mapping -------------

class _Captured(Exception):
    def __init__(self, urls):
        self.urls = urls


class _CaptureGraph:
    """Stands in for the diagram-graph object: intercepts the mapping at the
    dot-generation call, before any rendering side effects."""

    def generate_dot(self, name, urls=None, env=None, **kwargs):
        raise _Captured(dict(urls or {}))


class _DiagramNode:
    """Minimal diagram-node double: item access for the attributes the
    function reads, iteration over the cross-reference children."""

    def __init__(self, children):
        self._children = list(children)
        self._attrs = {"graph": _CaptureGraph(), "content": "C", "parts": 0}

    def __getitem__(self, key):
        return self._attrs[key]

    def __iter__(self):
        return iter(self._children)


def run_real(visit, docname, out_suffix, child, output_format):
    """One real call with a single cross-reference child, under the given
    graphviz_output_format; returns the captured key -> link mapping (exactly
    one entry for the probes used here)."""
    builder = SimpleNamespace(
        env=SimpleNamespace(
            config=SimpleNamespace(graphviz_output_format=output_format)),
        current_docname=docname,
        out_suffix=out_suffix,
    )
    fake_self = SimpleNamespace(builder=builder)
    node = _DiagramNode([child])
    try:
        visit(fake_self, node)
    except _Captured as c:
        return c.urls
    raise AssertionError("real function returned without emitting the mapping")


def one_entry(urls, ctx):
    if len(urls) != 1:
        return None, "expected exactly one mapping entry, got %r (%s)" % (urls, ctx)
    ((k, v),) = urls.items()
    return (k, v), None


# --- the three probes ----------------------------------------------------------

def probe_external(visit, refuri, fmt, vec):
    """External explicit-destination reference: shadow key and link."""
    child = {"refuri": refuri, "internal": False, "reftitle": "ignored.Title"}
    entry, err = one_entry(run_real(visit, "docA", ".html", child, fmt),
                           "external refuri=%r fmt=%r" % (refuri, fmt))
    if err:
        return err
    real_key, real_val = entry
    shadow_val = text(url_for_destination(codes(refuri), vec))
    shadow_key = text(trailing_name_for_destination(codes(refuri)))
    if real_val != shadow_val:
        return ("DISAGREEMENT (external link)\n  refuri=%r fmt=%r\n"
                "  shadow=%r  real=%r" % (refuri, fmt, shadow_val, real_val))
    if real_key != shadow_key:
        return ("DISAGREEMENT (external key)\n  refuri=%r fmt=%r\n"
                "  shadow=%r  real=%r" % (refuri, fmt, shadow_key, real_key))
    # pure-region cross-checks on the same input
    if text(after_last_hash(ToSeq(codes(refuri)))) != shadow_key:
        return ("DISAGREEMENT (pure after_last_hash vs impl)\n  refuri=%r"
                % (refuri,))
    if has_scheme(ToSeq(codes(refuri))) != ("://" in refuri):
        return "DISAGREEMENT (pure has_scheme)\n  refuri=%r" % (refuri,)
    if has_scheme(ToSeq(codes(shadow_val))) != has_scheme(ToSeq(codes(refuri))):
        return ("DISAGREEMENT (scheme preservation)\n  refuri=%r" % (refuri,))
    return None


def probe_internal(visit, refuri, reftitle, explicit_internal, fmt, vec):
    """Internal explicit-destination reference: shadow link; key is the
    unchanged title (I-tagged, checked as exactly the title)."""
    child = {"refuri": refuri, "reftitle": reftitle}
    if explicit_internal:
        child["internal"] = True
    entry, err = one_entry(run_real(visit, "docB", ".html", child, fmt),
                           "internal refuri=%r fmt=%r" % (refuri, fmt))
    if err:
        return err
    real_key, real_val = entry
    shadow_val = text(url_for_destination(codes(refuri), vec))
    if real_val != shadow_val:
        return ("DISAGREEMENT (internal link)\n  refuri=%r reftitle=%r fmt=%r\n"
                "  shadow=%r  real=%r"
                % (refuri, reftitle, fmt, shadow_val, real_val))
    if real_key != reftitle:
        return ("DISAGREEMENT (internal key: expected the unchanged title)\n"
                "  refuri=%r reftitle=%r  real_key=%r"
                % (refuri, reftitle, real_key))
    return None


def probe_anchor(visit, docname, out_suffix, refid, reftitle, fmt, vec):
    """Same-document-anchor reference: shadow link over (output name, anchor,
    image format)."""
    child = {"refid": refid, "reftitle": reftitle}
    entry, err = one_entry(run_real(visit, docname, out_suffix, child, fmt),
                           "anchor refid=%r fmt=%r" % (refid, fmt))
    if err:
        return err
    real_key, real_val = entry
    current_doc_name = docname + out_suffix  # as the builder composes it
    shadow_val = text(url_for_self_doc_anchor(codes(current_doc_name),
                                              codes(refid), vec))
    if real_val != shadow_val:
        return ("DISAGREEMENT (anchor link)\n"
                "  docname=%r out_suffix=%r refid=%r fmt=%r\n"
                "  shadow=%r  real=%r"
                % (docname, out_suffix, refid, fmt, shadow_val, real_val))
    if real_key != reftitle:
        return ("DISAGREEMENT (anchor key: expected the unchanged title)\n"
                "  refid=%r reftitle=%r  real_key=%r"
                % (refid, reftitle, real_key))
    return None


def probe_anchor_both(visit, docname, out_suffix, refid, reftitle):
    """The anchor probe under both formats, plus the cross-format observation
    that the real links DIFFER whenever the document name is non-empty. A
    format-blind model would match at most one of the two arms."""
    err = probe_anchor(visit, docname, out_suffix, refid, reftitle, "svg", True)
    if err:
        return err, 1
    err = probe_anchor(visit, docname, out_suffix, refid, reftitle, "png", False)
    if err:
        return err, 2
    current_doc_name = docname + out_suffix
    if current_doc_name:
        (_, svg_val), _e = one_entry(
            run_real(visit, docname, out_suffix,
                     {"refid": refid, "reftitle": reftitle}, "svg"), "svg")
        (_, png_val), _e = one_entry(
            run_real(visit, docname, out_suffix,
                     {"refid": refid, "reftitle": reftitle}, "png"), "png")
        if svg_val == png_val:
            return ("DISAGREEMENT (image format is not observable in the real "
                    "code)\n  docname=%r out_suffix=%r refid=%r\n"
                    "  svg=%r  png=%r"
                    % (docname, out_suffix, refid, svg_val, png_val)), 2
    return None, 2


# --- input domains ---------------------------------------------------------------

BOUNDARY_URIS = [
    "",
    "foo.html",
    "my_class_1.html#my_package.MyClass1",
    "../my_package/my_class_2.html#my_package.MyClass2",
    "https://example.org/foo.html#subdir.other.Bob",
    "https://example.org/foo.html",
    "#anchor-only",
    "no-hash",
    "a#b#c#d",
    "trailing#",
    "#",
    "##",
    "scheme://host/p#frag",
    "subdir.other.Bob",
    "x://y",            # minimal scheme separator
    ":/incomplete",     # not a scheme separator
    "a:b/c",            # colon but not a scheme separator
    "a.h",              # short URI: shorter than any test fixture's
    "caf\u00e9.html#\u00fcnic\u00f8de",  # non-ASCII code points
]
BOUNDARY_DOCNAMES = ["index", "subdir/index", "a/b/c", "x", ""]
BOUNDARY_SUFFIXES = [".html", ".htm", ".xhtml", ""]
BOUNDARY_REFIDS = ["test.DocHere", "my_package.MyClass1", "a.b.c", "x", ""]
BOUNDARY_TITLES = ["pkg.Cls", "", "title with space", "t#hash", "\u00e9t\u00e9"]


def main():
    # REAL repo symbol (the function the model models, per mapping.md):
    from sphinx.ext.inheritance_diagram import html_visit_inheritance_diagram

    visit = html_visit_inheritance_diagram
    checked = 0

    def run(err, n=1):
        nonlocal checked
        if err:
            print(err)
            sys.exit(1)
        checked += n

    # --- boundary sweep (every case under every format) ---------------------
    for fmt, vec in FORMATS:
        for u in BOUNDARY_URIS:
            run(probe_external(visit, u, fmt, vec))
            for t in BOUNDARY_TITLES:
                run(probe_internal(visit, u, t, len(u) % 2 == 0, fmt, vec))
        for dn in BOUNDARY_DOCNAMES:
            for sfx in BOUNDARY_SUFFIXES:
                for rid in BOUNDARY_REFIDS:
                    for t in BOUNDARY_TITLES[:2]:
                        run(probe_anchor(visit, dn, sfx, rid, t, fmt, vec))
    for dn in BOUNDARY_DOCNAMES:
        for sfx in BOUNDARY_SUFFIXES:
            for rid in BOUNDARY_REFIDS:
                err, n = probe_anchor_both(visit, dn, sfx, rid, "pkg.Cls")
                run(err, n)
    n_boundary = checked

    # --- randomized fuzz (pinned seed) --------------------------------------
    rng = random.Random(SEED)
    pieces = (list("abcXYZ._/-0129") +
              ["#", "#", ":", "/", "://", "https://", "\u00e9", "\u2713"])

    def rand_str(max_pieces):
        return "".join(rng.choice(pieces)
                       for _ in range(rng.randint(0, max_pieces)))

    for _ in range(N_FUZZ_ROUNDS):
        fmt, vec = FORMATS[rng.randrange(len(FORMATS))]
        u = rand_str(14)
        run(probe_external(visit, u, fmt, vec))
        fmt2, vec2 = FORMATS[rng.randrange(len(FORMATS))]
        run(probe_internal(visit, rand_str(14), rand_str(8),
                           rng.random() < 0.5, fmt2, vec2))
        dn = rand_str(8)
        sfx = rng.choice(BOUNDARY_SUFFIXES + [rand_str(3)])
        err, n = probe_anchor_both(visit, dn, sfx, rand_str(8), rand_str(6))
        run(err, n)

    print("G-CONF OK: shadow impl == real hyperlink-mapping construction in "
          "both image formats on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, checked - n_boundary, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "formats": [f for f, _ in FORMATS],
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
