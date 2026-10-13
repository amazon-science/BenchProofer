#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8035.

The proof consumes NO module-level axiom: the keep-decision is modeled deeply
(`memberShown`/`selKeeps`/`shownMembers` in Solution.lean's pure region). What
G-AX must validate are the two A-reference callees that feed the modeled inputs
(mapping.md §4) — unchanged helpers whose results are abstracted into the
`Sel` argument and the `Member` fields:

  (A-reference 1) `Sel` == `members_option`.  The selection tri-state the
      keep-decision tests against is exactly what the real (unchanged)
      `members_option` parser produces, together with option-absence:
        arg is None / True       -> ALL              ↔ Sel.all
        arg = "a, b , a"         -> ["a","b","a"]    ↔ Sel.only [...]  (comma-split,
                                                                       stripped, empties dropped)
        option absent            -> private_members is None ↔ Sel.none
      The spec consumes only `name in names`, so what matters is that the parsed
      list IS the set membership is tested against.

  (A-reference 2) `Member.isRestricted` / `Member.hasDoc` == the real
      `getdoc` + `extract_metadata` / underscore classification.  The model
      abstracts these unchanged callees into the member fields:
        has_doc      = bool(getdoc(member))
        isprivate    = True  if ':meta private:'  in docstring metadata
                       False if ':meta public:'   in docstring metadata
                       else membername.startswith('_')
      G-AX confirms the F2P module's two members classify as the discriminator
      needs (_public_function -> not restricted; private_function -> restricted)
      and fuzzes the classification over many name/doc shapes.

Imports only the repo's own (unchanged) sphinx helpers — the same callees the
keep-decision reads. Exit 0 iff every obligation holds.
"""
import random
import sys
import warnings

warnings.simplefilter("ignore")

from sphinx.ext.autodoc import ALL, members_option            # noqa: E402
from sphinx.util.inspect import getdoc, safe_getattr          # noqa: E402
from sphinx.util.docstrings import extract_metadata           # noqa: E402


# --- model-side reference encodings (lock-step with Solution.lean) -----------

def sel_of_option(parsed):
    """Map the real members_option result (or None for option-absent) to the
    Sel encoding the model uses: None->'none', ALL->'all', list->('only', list)."""
    if parsed is None:
        return ("none", None)
    if parsed is ALL:
        return ("all", None)
    return ("only", list(parsed))


def model_members_option(arg):
    """Reference transliteration of members_option's contract (Sel.only domain):
    comma-split, strip, drop empties; None/True -> ALL."""
    if arg is None or arg is True:
        return ("all", None)
    return ("only", [x.strip() for x in arg.split(",") if x.strip()])


def model_classify(name, doc):
    """Reference (isRestricted, hasDoc) from a member's docstring + name — the
    rule filter_members applies upstream of the keep-decision."""
    has_doc = bool(doc)
    md = extract_metadata(doc) if isinstance(doc, str) else {}
    if "private" in md:
        is_restricted = True
    elif "public" in md:
        is_restricted = False
    else:
        is_restricted = name.startswith("_")
    return is_restricted, has_doc


# --- the real callees --------------------------------------------------------

def real_members_option(arg):
    parsed = members_option(arg)
    return sel_of_option(parsed)


def make_member(doc):
    def f(name):  # pragma: no cover
        pass
    f.__doc__ = doc
    return f


def real_classify(name, doc):
    """Run the REAL getdoc + extract_metadata path on a synthetic member."""
    member = make_member(doc)
    d = getdoc(member, safe_getattr, False, None, None)
    if not isinstance(d, str):
        d = None
    has_doc = bool(d)
    md = extract_metadata(d) if d else {}
    if "private" in md:
        is_restricted = True
    elif "public" in md:
        is_restricted = False
    else:
        is_restricted = name.startswith("_")
    return is_restricted, has_doc


# --- checks ------------------------------------------------------------------

def check_members_option(arg):
    """Assert Sel(real members_option(arg)) == the model's reference Sel."""
    observed = real_members_option(arg)
    expected = model_members_option(arg)
    assert observed == expected, (
        "members_option A-reference unsound on %r: real -> %r, model -> %r"
        % (arg, observed, expected))


def check_classify(name, doc):
    """Assert real (isRestricted,hasDoc) == the model's reference classify."""
    observed = real_classify(name, doc)
    expected = model_classify(name, doc)
    assert observed == expected, (
        "classification A-reference unsound on name=%r doc=%r: real -> %r, "
        "model -> %r" % (name, doc, observed, expected))


def main():
    # --- A-reference 1: members_option (Sel) -----------------------------------
    boundary_args = [
        None, True,
        "_public_function",
        "private_function",
        "a,b,c",
        "a, b , c",
        "  spaced  ",
        "",                       # -> [] (Sel.only [])
        ",,",                     # -> [] (all empties dropped)
        "x,,y",                   # -> ['x','y']
        "dup, dup",               # -> ['dup','dup'] (no dedup; membership unaffected)
        "_a,_b,_c",
    ]
    for arg in boundary_args:
        check_members_option(arg)

    rng = random.Random(8035)
    tokens = ["a", "b", "_x", "foo", "_public_function", "private_function",
              "", " ", "z9", "_", "__d"]
    for _ in range(20000):
        k = rng.randint(0, 6)
        parts = [rng.choice(tokens) for _ in range(k)]
        arg = ",".join(parts)
        check_members_option(arg)
        if rng.random() < 0.05:
            check_members_option(None)

    # --- A-reference 2: classification (isRestricted/hasDoc) -------------------
    # The exact F2P members (the discriminator depends on these two):
    check_classify("_public_function", "public_function is a docstring().\n\n:meta public:\n")
    check_classify("private_function", "private_function is a docstring().\n\n:meta private:\n")
    f2p_pub = real_classify("_public_function",
                            "public_function is a docstring().\n\n:meta public:\n")
    f2p_priv = real_classify("private_function",
                             "private_function is a docstring().\n\n:meta private:\n")
    assert f2p_pub == (False, True), (
        "_public_function must be (not restricted, documented); got %r" % (f2p_pub,))
    assert f2p_priv == (True, True), (
        "private_function must be (restricted, documented); got %r" % (f2p_priv,))

    # boundary + fuzz over name/doc shapes
    names = ["_public_function", "private_function", "_x", "foo", "_bar",
             "baz", "__weird", "_", "Name", "_lead"]
    docs = [
        None,
        "",
        "plain docstring().",
        "doc\n\n:meta private:\n",
        "doc\n\n:meta public:\n",
        "doc\n\n:meta private:\n:meta public:\n",   # both present
        "doc\n\n:param x: y\n",
        ":meta private:\n",
    ]
    for name in names:
        for doc in docs:
            check_classify(name, doc)
    for _ in range(5000):
        name = rng.choice(names)
        doc = rng.choice(docs)
        check_classify(name, doc)

    print("G-AX OK: members_option == Sel over %d boundary + 20000 fuzz args; "
          "classification (isRestricted/hasDoc) == real getdoc/extract_metadata "
          "over the F2P members + %d name/doc shapes + 5000 fuzz."
          % (len(boundary_args), len(names) * len(docs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
