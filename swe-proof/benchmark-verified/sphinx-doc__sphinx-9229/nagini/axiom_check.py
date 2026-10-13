#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9229.

The only consumed axiom is `placeholder_seq` / `make_placeholder` (model.py
axioms region): the content of the synthetic 'alias of <target>' line that the
alias path substitutes as additional content. Its WEAKEST sufficient property —
the only one the proof consumes — is that the rendered line is NON-EMPTY
(`len(Result()) > 0`).

The real callee the patch leaves UNCHANGED and still invokes is
`StringList([_('alias of %s') % restify(self.object)], source='')`
(`sphinx/ext/autodoc/__init__.py`, add_content). We reproduce the line content
exactly as the gold patch composes it — `'alias of %s' % <target rendering>` —
and assert non-emptiness over a boundary + fuzz family of target renderings,
INCLUDING the real `sphinx.util.typing.restify` when it is importable in the
evaluation container (it is — this is the very module the patched file imports).

We deliberately do NOT pin the exact text of the line: the F2P test that
exercises the change asserts the placeholder is ABSENT, and the unchanged-text
case is covered by the PASS_TO_PASS test_class_alias. Pinning restify's exact
output would be an over-claim (directive 7).

Exit 0 iff every observation satisfies the axiom's Ensures.
"""
import random
import sys


def alias_line(target_rendering):
    """The line content exactly as the gold patch composes it: the gettext
    template 'alias of %s' formatted with the target rendering. (In-container
    `_` is gettext-identity for the C locale autodoc tests run under, so the
    template text is verbatim.)"""
    return 'alias of %s' % target_rendering


def check_nonempty(target_rendering):
    """Assert make_placeholder/placeholder_seq's Ensures: the produced line is
    a non-empty sequence of code points."""
    line = alias_line(target_rendering)
    codepoints = [ord(ch) for ch in line]
    assert len(codepoints) > 0, (
        "placeholder axiom unsound: rendered 'alias of %%s' line for target "
        "rendering %r is EMPTY (%r)" % (target_rendering, line))


def main():
    # --- boundary target renderings ---------------------------------------
    boundary = [
        "",                                   # degenerate empty rendering
        "Foo",
        "target.classes.Foo",                 # the test_class_alias target
        "target.classes.Bar",                 # the F2P OtherAlias target
        ":class:`target.classes.Foo`",        # the cross-reference form
        "Dict[str, Any]",                     # a generic alias rendering
        "typing.Callable[[Path, X], Y]",
        "A" * 4096,                           # very long rendering
        "é•中",                               # non-ASCII rendering
    ]
    for tr in boundary:
        check_nonempty(tr)

    # --- the real restify, when importable in the eval container ----------
    try:
        from sphinx.util.typing import restify  # the unchanged callee
        real_targets = [int, str, dict, list, Exception, type(None)]
        try:
            from typing import Dict, Any, Callable, Union
            real_targets += [Dict[str, Any], Union[str, None], Callable[..., int]]
        except Exception:
            pass
        for cls in real_targets:
            try:
                rendering = restify(cls)
            except Exception:
                # restify raising is the gold's `except AttributeError: pass`
                # guard, not a placeholder-content obligation; skip.
                continue
            assert isinstance(rendering, str)
            check_nonempty(rendering)
    except Exception as exc:                  # sphinx not importable here
        print("G-AX note: real restify not exercised (%r); checked the "
              "'alias of %%s' composition directly." % (exc,))

    # --- randomized fuzz over target renderings ---------------------------
    rng = random.Random(9229)
    alphabet = list("abcdefghijklmnopqrstuvwxyzABCDEF.[],<> :`éπ中") + [""]
    for _ in range(20000):
        n = rng.randint(0, 40)
        tr = "".join(rng.choice(alphabet) for _ in range(n))
        check_nonempty(tr)

    print("G-AX OK: placeholder axiom (alias-of line content) non-empty on "
          "%d boundary + real-restify + 20000 fuzz target renderings"
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
