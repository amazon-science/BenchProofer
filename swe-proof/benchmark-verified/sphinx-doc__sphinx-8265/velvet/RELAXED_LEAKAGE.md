# Relaxed-leakage disposition — sphinx-doc__sphinx-8265 (velvet)

**Disposition: ACCEPTED under the relaxed-leakage policy.**
`meta.json` records the top-level `relaxed_leakage: true` flag, which (with
this file present) makes the G-LEAK gate record `status = "relaxed"`
(`src/swebench_unified/gates/leak.py`). The policy is the binding
spec-construction rule, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed"). The sibling nagini bundle of THIS instance carries
the same disposition and re-gated green with it; the lean bundle's P3 audit
independently judged the same facet non-blocking.

The spec view discloses a **second, coupled change site** — that a non-empty
comma-separated group with no unpacking member, used as a subscript *index*,
renders its members directly inside the brackets WITHOUT the surrounding
round brackets that the same group acquires when it stands on its own —
because this instance is a genuine `problem_statement` ↔ gold MISMATCH and a
*faithful* spec cannot avoid naming that behaviour. The mechanical G-LEAK
lexical screen still passes (the leak is semantic, not token-level: no gold
diff line, no patched symbol — `visit_Tuple` / `visit_Subscript` /
`is_simple_tuple` / `ast` / `Starred` / `Index` / `sphinx/pycode/ast.py` are
all absent from the spec view).

## Why faithful + non-leaking is impossible here (adversarial analysis)

Directive 6 judges leakage against the **solver-visible `problem_statement`
ONLY**, never `hints_text` or the hidden `test_patch`.

**What the `problem_statement` actually says.** The public issue is titled
"docstring default arg is broken". Its single concrete example is a tuple
default argument:

    def add_lines(self, lines, color=(1, 1, 1), width=5, label=None, name=None):

which is rendered (wrongly) as `add_lines(lines, color=1, 1, 1, ...)` and is
expected to render as `add_lines(lines, color=(1, 1, 1), ...)`. The entire
public text concerns ONLY a standalone tuple losing its parentheses. The
`problem_statement`:
  - never mentions a **subscript** / **indexing** expression
    (`Tuple[int, int]`, `base[...]`),
  - never contains any of the tokens
    {subscript, index, starred, unpack, spread, slice, join, ast, simple},
  - exhibits only the one symptom (parenthesisation of a bare tuple).
`hints_text` (not public to the solver anyway) carries only a bare cross-link
to a related issue — no discriminating vocabulary.

**Where the second discriminator lives.** The gold patch has TWO coupled hunks
in `sphinx/pycode/ast.py`:
  1. `visit_Tuple`: wrap a non-empty tuple's joined members in `(` … `)`
     (the publicly-reported fix). Modeled by `render`'s `.group` arm /
     `renderGroup` — this facet is PS-derivable (the Expected-behavior line
     shows `color=(1, 1, 1)`), so it does not leak.
  2. `visit_Subscript`: when the index *is itself a simple non-empty tuple
     with no `Starred` member*, render the index body as the BARE
     `", ".join(...)` of its members — WITHOUT the inner round brackets that
     hunk 1 would now add (the added `is_simple_tuple` guard). Modeled by
     `render`'s `.index` arm / `renderIndex` — this facet is the leak.

Hunk 2's discriminating input class (a tuple used as a subscript index) and
the "no inner brackets on a group index" behaviour appear NOWHERE in the
`problem_statement`. They live only in the gold diff and the hidden
`test_patch`.

**Why hunk 2 is mandatory (the coupling).** The hidden `test_patch` keeps the
PASS_TO_PASS row `test_unparse[Tuple[int, int]-Tuple[int, int]]`. Once hunk 1
parenthesises every non-empty tuple, the pre-patch `visit_Subscript`
(`"%s[%s]" % (self.visit(node.value), self.visit(node.slice))`) would render
`Tuple[int, int]` as `Tuple[(int, int)]` — breaking that P2P test. So a fix
that applies only the PS-derivable tuple hunk does NOT resolve; the subscript
guard is required. A spec that pins the gold behaviour — so the prepatch
fails (G-DIFF) and no wrong impl verifies (G-EQ) — MUST model both sites,
hence MUST disclose the group-as-index "no inner brackets" behaviour. A spec
restricted to the `problem_statement` surface (a bare tuple gaining
parentheses) cannot pin it: that surface never exhibits the subscript
interaction at all. This materiality was independently PROVEN by this
bundle's own G-DIFF: `Solution_prepatch_2.lean` — the natural "always render
the whole slice expression" impl a PS-only solver would write, yielding
`value[(a, b)]` — is same_spec=True (spec region byte-identical) yet FAILS
`ensures out = render (.index value idx)`. Hence **faithful + non-leaking is
provably impossible** — the public text and the gold fix's tested
discriminator are about different expression shapes. This is the directive-6
relaxed-leakage condition, not lazy de-narration: the spec view is already an
abstract behavioural contract over an `Expr` carrier (round brackets on a
standalone group; no redundant inner brackets on a group used as an index),
names no patched file/function/symbol, and quotes no diff line; the residual
"leak" is the second behaviour itself.

## Requirements satisfied (directive 6's relaxed-leakage conditions)

1. **Core is sound.** G-VERIFY pass (Solution.lean verifies, 3.0 s). G-DIFF
   pass with two byte-identical-spec prepatch variants: `Solution_prepatch.lean`
   fails the `renderGroup` parenthesisation postcondition (site 1);
   `Solution_prepatch_2.lean` fails the `renderIndex` simple-group-index
   postcondition (site 2 coupling) — each on its own discriminating clause.
   G-EQ sound/tight: every refinement step is R or I, no kind-3, NO axioms and
   NO A-references — both changed behaviours are modeled deeply by the concrete
   recursive `render`, whose refinement fidelity is independently grounded by
   a non-vacuous G-CONF (100009 fuzzed inputs + boundary set vs the real
   patched `_UnparseVisitor` in-container, 0 disagreements, pinned seed 8265).
   G-PANEL-2 (faithfulness) pass with an independent ~300k-input differential
   fuzz. G-RESOLVE: `patch.diff` == gold verbatim, resolves the F2P
   `tests/test_pycode_ast.py::test_unparse[(1, ...]` plus 22 P2P (incl.
   `Tuple[int, int]`). G-MUT 20/20 killed; G-HYGIENE / G-INTEGRITY / G-LEAK
   (mechanical screen) clean.
2. **The leak is genuinely unavoidable**, established by the adversarial
   analysis above: the gold's tested discriminator (group-as-subscript-index
   renders without inner round brackets, and its coupling to the tuple
   parenthesisation) is demonstrably absent from `problem_statement` and
   present only in the gold diff / hidden `test_patch`. No PS-derivable
   reformulation models the gold fix — the public surface (a bare tuple)
   never exercises the subscript interaction, and a one-hunk fix breaks the
   `Tuple[int, int]` P2P. Two prior independent G-PANEL-3 audits of this
   bundle each re-derived exactly this analysis (the source-repo audit
   recorded in `verdict.md` sub-review 3 concluded RELAXED and flagged only
   the then-missing in-bundle documentation; the 2026-08-02 re-gate audit
   re-proved materiality via `Solution_prepatch_2.lean` but recorded a raw
   LEAKAGE because no disposition was present in-bundle). The sibling nagini
   bundle's dispositioned P3 audit independently re-derived and accepted the
   same unavoidability argument.
3. **Documented in-bundle.** This file; `meta.json` carries the top-level
   `relaxed_leakage: true` flag; the G-LEAK gate reads it (plus this file) and
   records `gates.G-LEAK.status = "relaxed"` pointing at this document.
