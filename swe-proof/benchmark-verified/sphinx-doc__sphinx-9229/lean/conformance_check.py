#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadows of implementation_getDoc and
implementation_addContent against the patch.diff behaviour.

Both impl regions are pure control flow over abstract inputs (the looked-up
documentation comment, the rendered alias description, the caller-supplied
content). Every op is I (identical concrete control flow) modulo the type-only
R refinement declared in refinement.md (Python `None`/`list` truthiness modeled
as Lean `Option`/`List` with `commentPresent`). The shadow therefore reproduces
the post-patch behaviour op-for-op; we assert zero disagreements vs an
independent reconstruction of the two patched functions over >=10^5 fuzzed
inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 9229
N = 120_000           # >= 10^5


# ---- Lean models (the R/I shadow) ---------------------------------------

def comment_present(comment):
    """commentPresent: present iff lookup succeeded with >=1 line.
    comment is None (failed lookup) or a list of strings."""
    return comment is not None and len(comment) > 0


def shadow_get_doc(doc_as_attr, comment, normal_doc):
    """R/I shadow of implementation_getDoc."""
    if doc_as_attr:
        if comment_present(comment):
            return []          # some []  -> empty doc block
        else:
            return None        # none
    return normal_doc


def shadow_add_content(doc_as_attr, comment, alias_text, incoming):
    """R/I shadow of implementation_addContent."""
    if doc_as_attr and not comment_present(comment):
        return ["alias of " + alias_text]
    return incoming


# ---- Independent reconstruction of the patched functions ----------------

def patched_get_doc(doc_as_attr, comment, normal_doc):
    """Post-patch ClassDocumenter.get_doc alias branch:
        if self.doc_as_attr:
            comment = self.get_variable_comment()
            if comment: return []
            else:       return None
        ... (otherwise the ordinary docstring path) ...
    `comment` here is the value get_variable_comment() returns (None on
    failure, else list(attr_docs.get(key, []))). `if comment:` is list
    truthiness."""
    if doc_as_attr:
        if comment:            # None -> False; [] -> False; [x..] -> True
            return []
        else:
            return None
    return normal_doc


def patched_add_content(doc_as_attr, comment, alias_text, incoming):
    """Post-patch ClassDocumenter.add_content:
        if self.doc_as_attr and not self.get_variable_comment():
            more_content = StringList([_('alias of %s') % restify(self.object)])
        super().add_content(more_content)
    i.e. the forwarded content becomes the alias line only when documenting as
    an alias AND no doc-comment is present; otherwise the caller content is
    forwarded unchanged."""
    if doc_as_attr and not comment:
        return ["alias of " + alias_text]
    return incoming


# ---- Fuzz ---------------------------------------------------------------

def rand_comment(rng):
    r = rng.random()
    if r < 0.34:
        return None                                   # failed lookup
    if r < 0.55:
        return []                                      # empty lookup
    return [rng.choice(["x", "doc", "line", ""]) for _ in range(rng.randint(1, 3))]


def rand_normal_doc(rng):
    if rng.random() < 0.4:
        return None
    return [[rng.choice(["a", "b", ""]) for _ in range(rng.randint(0, 2))]
            for _ in range(rng.randint(0, 2))]


def rand_incoming(rng):
    if rng.random() < 0.4:
        return None
    return [rng.choice(["c", "more", ""]) for _ in range(rng.randint(0, 2))]


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    targets = ["target.classes.Foo", "x", "", "a.b.C", "Some.Long.Path"]

    for _ in range(N):
        doc_as_attr = rng.random() < 0.6
        comment = rand_comment(rng)
        normal_doc = rand_normal_doc(rng)
        incoming = rand_incoming(rng)
        alias_text = rng.choice(targets)

        g_got = shadow_get_doc(doc_as_attr, comment, normal_doc)
        g_want = patched_get_doc(doc_as_attr, comment, normal_doc)
        a_got = shadow_add_content(doc_as_attr, comment, alias_text, incoming)
        a_want = patched_add_content(doc_as_attr, comment, alias_text, incoming)

        if g_got != g_want or a_got != a_want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((doc_as_attr, comment, normal_doc, incoming,
                                 alias_text, (g_got, g_want), (a_got, a_want)))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for e in examples:
            print("  ", e)
        return 1

    print(f"G-CONF OK: {N} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
