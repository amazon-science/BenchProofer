#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-10614.

This bundle has NO consumed @ContractOnly axioms: every modelled operation is
plain Python string/sequence arithmetic. What it DOES carry is a set of
A-reference deep models (model.py's `pure` region and the three implemented
functions) that mirror the exact string operations the gold patch performs.
This script validates those deep models against the REAL Python operations on
boundary + fuzz inputs. Exit 0 iff every observation matches.

The image format is one of the modelled inputs (`vector_format`), and it is the
real code's own observable: sphinx/ext/inheritance_diagram.py:409 computes
`graphviz_output_format = self.builder.env.config.graphviz_output_format
.upper()`, so vector_format corresponds to that value being 'SVG'. Every check
below is therefore run for BOTH formats.

The patch's three behaviours (sphinx/ext/inheritance_diagram.py,
`html_visit_inheritance_diagram`, post-patch line numbers):

  (1) refuri branch value (:421):  urls[refname] = child.get('refuri')
        -> the link is the destination URI itself, NOT '../' + refuri. The
        statement sits OUTSIDE any `if graphviz_output_format` test, so it is
        the same in both formats (pre-patch it was '../' + refuri for SVG only,
        and the fix removed the branch rather than the else arm).
        deep model: url_for_destination(refuri, vector_format) == refuri
                    has_scheme(refuri) iff '://' occurs in refuri

  (2) refid branch value (:423-426):
        if graphviz_output_format == 'SVG': current_filename + '#' + refid
        else:                               '#' + refid
        -> for the vector image NOT '../' + current_filename + '#' + refid, and
        for the raster image no document name at all.
        deep model: url_for_self_doc_anchor(cf, refid, True)  == cf + '#' + refid
                    url_for_self_doc_anchor(cf, refid, False) == '#' + refid

  (3) external key (:417):   refname = refuri.rsplit('#', 1)[-1]
        (also outside any format test -> no format parameter)
        deep model: trailing_name_for_destination(refuri) == after_last_hash(refuri)
                    == refuri.rsplit('#', 1)[-1]

Imports only the Python standard library. Nothing repo-specific.
"""
import random
import sys


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def has_scheme(s):
    """model.py `has_scheme`: True iff '://' occurs somewhere in s."""
    for i in range(len(s)):
        if i + 2 < len(s) and s[i] == ':' and s[i + 1] == '/' and s[i + 2] == '/':
            return True
    return False


def after_last_hash(s):
    """model.py `after_last_hash`: the trailing component after the final '#'
    (s itself if it has no '#')."""
    p = 0
    for i in range(len(s)):
        if s[i] == '#':
            p = i + 1
    return s[p:]


def url_for_destination(refuri, vector_format):
    """model.py function 1 impl: returns the URI itself, in either format."""
    return refuri


def url_for_self_doc_anchor(cf, refid, vector_format):
    """model.py function 2 impl: cf + '#' + refid for the vector image,
    '#' + refid for the raster image."""
    if vector_format:
        return cf + '#' + refid
    return '#' + refid


def trailing_name_for_destination(refuri):
    """model.py function 3 impl: trailing component after last '#'."""
    return after_last_hash(refuri)


# --- the real operations, as the patched source spells them ------------------
# `fmt` is the value of graphviz_output_format at :409 (already .upper()'d).

def real_destination(refuri, fmt):
    """:421 -- outside any format branch."""
    return refuri


def real_self_doc(cf, refid, fmt):
    """:423-426 -- the one format-dependent value."""
    if fmt == 'SVG':
        return cf + '#' + refid
    return '#' + refid


FORMATS = [('SVG', True), ('PNG', False), ('PDF', False)]


# --- the checks: deep model == the REAL patch string operation ---------------

def check_destination(refuri):
    for fmt, vec in FORMATS:
        real = real_destination(refuri, fmt)
        assert url_for_destination(refuri, vec) == real, (fmt, refuri, real)
        # scheme preservation: '://' membership is invariant under the identity
        assert has_scheme(refuri) == ('://' in refuri), refuri
        assert has_scheme(url_for_destination(refuri, vec)) == ('://' in real), \
            (fmt, refuri)


def check_self_doc(cf, refid):
    for fmt, vec in FORMATS:
        real = real_self_doc(cf, refid, fmt)
        assert url_for_self_doc_anchor(cf, refid, vec) == real, (fmt, cf, refid, real)
        if vec:
            # begins with the current document's own name
            assert real.startswith(cf), (cf, refid, real)
        else:
            # the document name is absent, not merely un-prefixed
            assert real == '#' + refid, (cf, refid, real)
    # the two formats genuinely differ whenever the document name is non-empty:
    # a format-blind model could not match both arms.
    if cf:
        assert (url_for_self_doc_anchor(cf, refid, True)
                != url_for_self_doc_anchor(cf, refid, False)), (cf, refid)


def check_external_key(refuri):
    # real patch op (:417, external refuri key): refuri.rsplit('#', 1)[-1]
    real = refuri.rsplit('#', 1)[-1]
    assert trailing_name_for_destination(refuri) == real, (refuri, real)


def main():
    # --- boundary inputs over the operations actually exercised -----------
    refuris = [
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
        "a:b/c",            # colon but not '://'
        "a.h",              # short URI: no test fixture contains one
        "abc",
    ]
    filenames = ["index.html", "subdir/index.html", "a/b/c.html", "x.htm", ""]
    refids = ["test.DocHere", "my_package.MyClass1", "a.b.c", "x", ""]

    for u in refuris:
        check_destination(u)
        check_external_key(u)
    for cf in filenames:
        for rid in refids:
            check_self_doc(cf, rid)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(10614)
    alphabet = list("abcXYZ._/-0129") + ["#", "#", ":", "/", "://", "https://"]
    for _ in range(40000):
        u = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 14)))
        check_destination(u)
        check_external_key(u)
        cf = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 10)))
        rid = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 10)))
        check_self_doc(cf, rid)

    print("G-AX OK: deep models (url_for_destination, url_for_self_doc_anchor, "
          "trailing_name_for_destination/after_last_hash, has_scheme) == the "
          "real patch string operations in BOTH image formats on %d boundary + "
          "40000 fuzz inputs" % len(refuris))
    return 0


if __name__ == "__main__":
    sys.exit(main())
