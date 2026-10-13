#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9229 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: `commentPresent` / `docForAlias` / `contentForAlias`
              over the alias flag (`doc_as_attr`), the optional doc-comment
              (`get_variable_comment()`), the ordinary documentation
              (`normalDoc`, isAlias=False only), the incoming content
              (`more_content`) and the rendered alias label. The bundle has NO
              axioms (mapping.md §3), so the whole shadow is in scope for G-CONF.
  * ORACLE  — `patch.diff`'s behaviour: the REAL, gold-patched
              `ClassDocumenter.get_doc` (alias branch) and
              `ClassDocumenter.add_content`. We do not build a full Sphinx app;
              both decisions read only `self.doc_as_attr` and
              `self.get_variable_comment()` (plus, on the override branch,
              `self.object` for the alias label). We therefore use a REAL
              `ClassDocumenter` instance (built via `__new__`, bypassing the heavy
              constructor) whose `get_variable_comment` is overridden to return
              the case's optional comment, so the real patched code path decides.

`get_doc` is observed directly: the alias branch returns `[]` (empty container)
or `None`. `add_content`'s decision is observed by temporarily replacing the base
`Documenter.add_content` (the `super().add_content` target) with a recorder that
captures the `more_content` the patched guard forwards — i.e. the rendered alias
label when the override fires, else the incoming content unchanged.

The non-alias leg of `get_doc` (`out = normalDoc`) is a pure R-IDENTITY carrying
no modeled computation (the alias change never touches that path), so it is not
differentially exercised; it is reported below. The non-alias leg of
`add_content` IS exercised (the guard short-circuits to forwarding `incoming`).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. Runs in-container (the prebuilt
SWE-Bench instance image, patch applied), stdlib + the in-image Sphinx only. The
fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 9229
N_FUZZ = 100_000


# --- ORACLE setup: the REAL gold-patched ClassDocumenter ---------------------

def _load_real():
    """Import the gold-patched ClassDocumenter + the base Documenter (whose
    add_content is the `super()` target) + StringList. The harness applies
    patch.diff before this runs."""
    from sphinx.ext.autodoc import ClassDocumenter, Documenter
    from docutils.statemachine import StringList
    return ClassDocumenter, Documenter, StringList


class _AliasObject:
    """A plain class object that `restify(...)` can render into the alias label
    on the override branch (the F2P case's alias target is a real class)."""
    pass


def _make_fake(ClassDocumenter, doc_as_attr, comment, object_):
    """A REAL ClassDocumenter instance with the heavy __init__ bypassed, exposing
    exactly what get_doc / add_content read on the modeled branches."""
    fake = ClassDocumenter.__new__(ClassDocumenter)
    fake.doc_as_attr = doc_as_attr
    # instance attribute shadows the real method for `self.get_variable_comment()`
    fake.get_variable_comment = lambda: comment
    fake.object = object_
    return fake


def oracle_get_doc(ClassDocumenter, doc_as_attr, comment):
    """The REAL patched ClassDocumenter.get_doc alias branch. Only called with
    doc_as_attr=True (the changed branch); returns `[]` or `None`."""
    fake = _make_fake(ClassDocumenter, doc_as_attr, comment, _AliasObject)
    return ClassDocumenter.get_doc(fake)


def oracle_add_content(ClassDocumenter, Documenter, StringList,
                       doc_as_attr, comment, incoming):
    """The REAL patched ClassDocumenter.add_content. Capture the `more_content`
    it forwards to super() by temporarily replacing the base recorder. Returns
    the forwarded content as a list of lines."""
    captured = {}

    def recorder(self, more_content, no_docstring=False):
        captured["mc"] = list(more_content.data) if more_content is not None else None

    orig = Documenter.add_content
    Documenter.add_content = recorder
    try:
        fake = _make_fake(ClassDocumenter, doc_as_attr, comment, _AliasObject)
        mc = StringList(list(incoming), source="<conf>")
        ClassDocumenter.add_content(fake, mc)
        return captured.get("mc")
    finally:
        Documenter.add_content = orig


# --- SHADOW: Solution.lean commentPresent/docForAlias/contentForAlias --------

def shadow_comment_present(comment):
    # commentPresent: none -> false; some xs -> xs non-empty
    if comment is None:
        return False
    return len(comment) > 0


def shadow_get_doc(doc_as_attr, comment, normal_doc):
    """docForAlias transliterated. Returns the get_doc container:
    None (none) or [] (some []) on the alias branch; normal_doc otherwise."""
    if doc_as_attr:
        return [] if shadow_comment_present(comment) else None
    return normal_doc


def shadow_add_content(doc_as_attr, comment, incoming, alias_label):
    """contentForAlias transliterated. Override with the alias label exactly when
    an alias AND no comment present; else forward incoming unchanged."""
    if doc_as_attr and not shadow_comment_present(comment):
        return list(alias_label)
    return list(incoming)


def main():
    rng = random.Random(SEED)
    try:
        ClassDocumenter, Documenter, StringList = _load_real()
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not import patched ClassDocumenter: %r" % e)
        return 2

    # The rendered alias label the real patched add_content builds on override.
    # Mirror it exactly so the shadow's `aliasLabel` matches the oracle content.
    from sphinx.ext.autodoc import restify
    try:
        from sphinx.locale import _ as _gettext
    except Exception:
        _gettext = lambda s: s  # noqa: E731
    ALIAS_LABEL = [_gettext('alias of %s') % restify(_AliasObject)]

    disagreements = []
    count = 0

    def comment_variants():
        # none, some [], some non-empty (1 line and multi-line)
        yield None
        yield []
        yield ["docstring"]
        yield ["line one", "line two", ""]

    def run_get_doc(comment):
        nonlocal count
        count += 1
        shadow = shadow_get_doc(True, comment, None)
        oracle = oracle_get_doc(ClassDocumenter, True, comment)
        if shadow != oracle:
            disagreements.append(("get_doc", True, comment, None, None,
                                  shadow, oracle))

    def run_add_content(doc_as_attr, comment, incoming):
        nonlocal count
        count += 1
        shadow = shadow_add_content(doc_as_attr, comment, incoming, ALIAS_LABEL)
        oracle = oracle_add_content(ClassDocumenter, Documenter, StringList,
                                    doc_as_attr, comment, incoming)
        if shadow != oracle:
            disagreements.append(("add_content", doc_as_attr, comment, incoming,
                                  ALIAS_LABEL, shadow, oracle))

    # --- boundary cases (the issue + the F2P assertion) ----------------------
    # get_doc alias branch: comment present -> [] (show docstring); absent -> None
    for c in comment_variants():
        run_get_doc(c)
    # add_content: the four (doc_as_attr, comment-present) configurations
    sample_incoming = [["body line"], [], ["a", "b"]]
    for inc in sample_incoming:
        for da in (True, False):
            for c in comment_variants():
                run_add_content(da, c, inc)

    # --- randomized fuzz -----------------------------------------------------
    lines_pool = ["docstring", "alias of X", "", "x", "multi", "  indented"]
    for _ in range(N_FUZZ):
        # comment: None, [], or a random non-empty list
        ch = rng.random()
        if ch < 0.34:
            comment = None
        elif ch < 0.5:
            comment = []
        else:
            comment = [rng.choice(lines_pool)
                       for _ in range(rng.randint(1, 4))]
        da = rng.random() < 0.6
        # exercise add_content for every config; get_doc only on the alias branch
        incoming = [rng.choice(lines_pool) for _ in range(rng.randint(0, 4))]
        run_add_content(da, comment, incoming)
        if da:
            run_get_doc(comment)
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for site, da, c, inc, lbl, sh, orc in disagreements:
            print("  site=%s doc_as_attr=%r comment=%r incoming=%r "
                  "shadow=%r oracle=%r" % (site, da, c, inc, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of aliasDocstrings/aliasContentOverride agrees "
          "with the real patched ClassDocumenter.get_doc (alias branch) and "
          ".add_content on %d inputs (boundary + fuzz, seed=%d), 0 disagreements. "
          "Non-alias get_doc leg is the R-identity `out = normalDoc` (no modeled "
          "computation), not differentially exercised." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
