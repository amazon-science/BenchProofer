#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-10435 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `wrapInlineCode` impl region
              transliterated to Python over the *real* repo type (`str`), via
              the mapping.md bijection (`List Char` ↔ `str`,
              `Char.ofNat (ord ch)` ↔ ch). The A-tagged callee
              `renderedInline`/`highlightInline` (the `:|` stub modeling
              `self.highlighter.highlight_block`) is NOT replaced by its axiom
              here; G-CONF isolates the R/I legs, so the highlighter call is the
              *real* callee on both sides — identical input ⇒ identical `hlcode`,
              and any difference must come from the R/I trailer surgery.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `LaTeXTranslator.visit_literal` applied at base_commit (the real
              correctness oracle, G-RESOLVE), driven on a `literal` node with a
              `code`+language class so the highlighting branch runs.

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), sphinx + stdlib only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

from docutils import nodes
from sphinx.highlighting import PygmentsBridge
from sphinx.writers.latex import LaTeXTranslator

SEED = 10435
N_FUZZ = 100_000

BEGIN = r'\begin{Verbatim}[commandchars=\\\{\}]'
OPEN = r'\sphinxcode{\sphinxupquote{'


# --- the R/I shadow: Solution.lean wrapInlineCode, transliterated ------------
# The highlighter call is the A-tagged callee: G-CONF uses the *real* callee
# (same as the oracle), so the shadow's `hlcode` source is identical to the
# oracle's. The R/I ops are the macro substitution + trailer surgery.
def shadow_wrap(hb, snippet, lang):
    hlcode = hb.highlight_block(snippet, lang)              # real A-callee
    # op 1 (R/I): replace the begin control sequence with OPEN + '%'
    #   (modeled in Lean as openTok ++ hlcode.drop beginTok.length, since BEGIN
    #    is a prefix; here we use the real .replace as the gold does)
    hlcode = hlcode.replace(BEGIN, OPEN + '%')
    # op 2 (R/I): right-strip, then drop the final 15 chars ('\n' + END)
    hlcode = hlcode.rstrip()[:-15]
    # op 3 (R/I): append the trailer '%' + '\n' + '}}'
    return hlcode + '%' + '\n' + '}}'


# --- the oracle: patch.diff behaviour (patched visit_literal) ----------------
class _FakeConfig:
    highlight_options = {}


class _Stub:
    """Minimal carrier of the attributes patched visit_literal touches."""
    pass


def oracle_wrap(hb, snippet, lang):
    t = _Stub()
    t.in_title = 0
    t.body = []
    t.config = _FakeConfig()
    t.highlighter = hb
    node = nodes.literal(snippet, snippet)
    node['classes'] = ['code', 'highlight']
    node['language'] = lang
    try:
        LaTeXTranslator.visit_literal(t, node)             # patched callee
    except nodes.SkipNode:
        pass
    return "".join(t.body)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield 'def foo(1 + 2 + None + "abc"): pass'    # the F2P snippet
    yield ''
    yield '   '
    yield 'x'
    yield 'a + b'
    yield '"a string"'
    yield "'q'"
    yield '# a comment'
    yield 'line1\nline2\nline3'
    yield 'trailing   '
    yield 'multi\n\n\nblank'
    yield '\t'
    yield 'def f():\n    return 1'
    yield 'a' * 200
    yield '<tag attr="v">'
    yield 'foo(1+2)'
    yield '%comment-like%'
    yield '}} braces {{'
    alphabet = list('abcdefghijklmnop ()+-=*/.,:;_"\'#%{}\\\t') + ['\n']
    for _ in range(n):
        k = rng.randint(0, 40)
        yield ''.join(rng.choice(alphabet) for _ in range(k))


def main():
    hb = PygmentsBridge('latex')
    lang = 'python'
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        # Requires: the highlighting branch runs only when pygments can lex the
        # snippet as `lang` (otherwise sphinx warns and skips). Both sides see
        # the identical real callee, so we compare on the same precondition.
        try:
            hl = hb.highlight_block(s, lang)
        except Exception:
            continue
        if not hl.startswith(BEGIN):
            # could-not-lex fallback: outside the modeled branch's precondition
            continue
        count += 1
        shadow = shadow_wrap(hb, s, lang)
        oracle = oracle_wrap(hb, s, lang)
        if shadow != oracle:
            disagreements.append((s, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r\n    shadow=%r\n    oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of wrapInlineCode agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
