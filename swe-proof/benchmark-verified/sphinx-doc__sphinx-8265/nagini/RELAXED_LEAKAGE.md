# Relaxed-leakage disposition — sphinx-doc__sphinx-8265

**Disposition: ACCEPTED under the relaxed-leakage policy.**
`meta.json` records the top-level `relaxed_leakage: true` flag, which (with
this file present) makes the G-LEAK gate record `status = "relaxed"`
(`src/swebench_unified/gates/leak.py`). In this unified repo the policy lives
in the binding spec-construction rules, `prompts/nagini/spec_guide.md`
directive 6 ("**Exception — relaxed-leakage:** ... for a proven
`problem_statement ↔ gold` mismatch where the gold's tested discriminator
exists only in `hints_text`/gold internals, so a *faithful* spec MUST name it
... KEEP the instance with the leak allowed"). (The `RELAXED_LEAKAGE.md`
cited by an earlier revision of this file was a source-repo-only doc that does
not exist here — see `prompts/README.md` on dangling source-repo refs.)

The spec view discloses a **second, coupled change site** — that a
comma-separated group used *as a subscript index* must render WITHOUT the
surrounding round brackets that the same group acquires when it stands on its
own — because this instance is a genuine `problem_statement` ↔ gold MISMATCH
and a *faithful* spec cannot avoid naming it. The mechanical G-LEAK lexical
screen still passes (the leak is semantic, not token-level: no diff line, no
patched symbol — `visit_Tuple` / `visit_Subscript` / `is_simple_tuple` /
`ast` / `Starred` / `Index` all absent from the spec view).

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
    {subscript, index, tuple, parenthes, bracket, starred, unpack, spread,
    slice, join, ast, simple},
  - exhibits only the one symptom (parenthesisation of a bare tuple).

**Where the second discriminator lives.** The gold patch has TWO coupled hunks
in `sphinx/pycode/ast.py`:
  1. `visit_Tuple`: wrap a non-empty tuple's joined members in `(` … `)`
     (the publicly-reported fix).
  2. `visit_Subscript`: when the index *is itself a simple non-empty tuple with
     no `Starred` member*, render the index body as the BARE `", ".join(...)` of
     its members — i.e. WITHOUT the inner round brackets that hunk 1 would now
     add (an added `is_simple_tuple` guard).

Hunk 2's discriminating input class (a tuple used as a subscript index) and the
"no inner brackets on a group index" behaviour appear in NONE of the
`problem_statement`. They live only in the gold diff and the hidden
`test_patch`.

**Why hunk 2 is mandatory (the coupling).** The hidden `test_patch` keeps the
PASS_TO_PASS row `test_unparse[Tuple[int, int]-Tuple[int, int]]`. Once hunk 1
parenthesises every non-empty tuple, the pre-patch `visit_Subscript`
(`"%s[%s]" % (self.visit(node.value), self.visit(node.slice))`) would render
`Tuple[int, int]` as `Tuple[(int, int)]` — breaking that P2P test. So a fix that
applies only the PS-derivable tuple hunk does NOT resolve; the subscript guard
is required. A spec that pins the gold behaviour — so the prepatch fails
(G-DIFF) and no wrong impl verifies (G-EQ) — MUST model both sites, hence MUST
disclose the group-as-index "no inner brackets" behaviour. A spec restricted to
the `problem_statement` surface (a bare tuple gaining parentheses) cannot pin it:
that surface never exhibits the subscript interaction at all. Hence **faithful +
non-leaking is provably impossible** — the public text and the gold fix's tested
discriminator are about different expression shapes. This is the directive-6
relaxed-leakage condition, not lazy de-narration: the docstring is
already an abstract behavioural contract (round brackets on a standalone group;
no redundant inner brackets on a group used as an index), names no patched
file/function/symbol, and quotes no diff line; the residual "leak" is the
second behaviour itself.

## Requirements satisfied (directive 6's relaxed-leakage conditions)

1. **Core is sound.** G-VERIFY pass (model.py verifies, <300s, no
   flags). G-DIFF fail with two byte-identical-spec prepatch variants
   (`same_spec` True): `model_prepatch.py` fails the `tuple_render`
   parenthesisation postcondition (site 1); `model_prepatch_2.py` fails the
   `subscript_render` simple-group-index postcondition (site 2 coupling) — each
   on its own discriminating clause. G-EQ sound/tight: every refinement step is
   R / A-reference / I, no kind-3, no consumed `@ContractOnly` axiom; both
   discriminators are exact STRUCTURAL equalities on the input carriers
   (`elts` / `value` / `index_is_member_group` / `slice_rendered`), not an
   opaque oracle (directive 8). G-AX sound: the one A-reference `join_comma` is
   validated == the real `', '.join` callee by `axiom_check.py` (9 boundary +
   30000 fuzz inputs), and the twin discriminates at both sites
   (`(1, 2, 3)` vs `1, 2, 3`; `Tuple[int, int]` vs `Tuple[(int, int)]`).
   G-RESOLVE: `patch.diff` == gold verbatim, applies cleanly at `base_commit`,
   resolves the F2P `tests/test_pycode_ast.py::test_unparse[(1, ...]` plus 22
   P2P (incl. `Tuple[int, int]`).
2. **The leak is genuinely unavoidable**, established by the adversarial
   analysis above: the gold's tested discriminator (group-as-subscript-index
   renders without inner round brackets, and its coupling to the tuple
   parenthesisation) is demonstrably absent from `problem_statement` and present
   only in the gold diff / hidden `test_patch`. No PS-derivable reformulation
   models the gold fix — the public surface (a bare tuple) never exercises the
   subscript interaction, and a one-hunk fix breaks the `Tuple[int, int]` P2P.
   A prior G-PANEL-3 audit of this bundle independently re-derived exactly this
   analysis and concluded the unavoidability argument is "correct, on the
   evidence" (its raw LEAKAGE verdict predates the panel recording convention
   above being documented in-bundle).
3. **Documented in-bundle.** This file; `meta.json` carries the top-level
   `relaxed_leakage: true` flag; the G-LEAK gate reads it (plus this file) and
   records `gates.G-LEAK.status = "relaxed"` pointing at this document.
