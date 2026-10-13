# refinement.md — sphinx-doc__sphinx-9230

The operation-by-operation correspondence between `model.py`'s implementation
(the two modeled functions `parsed_argument_name` and `parsed_argument_type`,
and the deep helpers `joined` / `last_token` / `encode_name`) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A-reference**
(a deep model validated == the real callee by axiom_check.py / G-AX — NOT a
consumed axiom), or **I** (identical concrete operation). There are **no
A-consumed** rows: the proof consumes no `@ContractOnly` axiom. The claim: *any
implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The single hunk — the typed-argument split (`sphinx/util/docfields.py:301`)

Gold hunk (the whole patch):
```
-                    argtype, argname = fieldarg.split(None, 1)
+                    argtype, argname = fieldarg.rsplit(None, 1)
```

`fieldarg` is the whitespace-separated text of a `:param <type> <name>:` field
argument. The one-line change moves the split from the FIRST whitespace
boundary to the LAST, so a multi-token type (e.g. `dict(str, str)`) is no longer
truncated to its first token and the name is no longer polluted with the tail of
the type. The two observable outputs — `argname` and `argtype` — are modelled by
the two functions below; the per-function marker regions repeat (§3 multi-site,
here two behaviours of one site).

### A. The parsed name — `parsed_argument_name` ↔ `argname`

| # | model.py impl op (`parsed_argument_name`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `tokens: List[int]` (the whitespace tokens of `fieldarg`) | `fieldarg: str` | R | `str` ↔ `List[int]` of whitespace tokens (mapping.md §2); each maximal whitespace-free run ↔ one token. |
| A2 | `last = tokens[len(tokens) - 1]`; `result = [encode_name(last)]` | `argname` = the second element of `fieldarg.rsplit(None, 1)` | R + A-reference | `argname` is exactly the FINAL token of the run. The deep model takes `last_token(tokens)`; G-AX confirms `str.rsplit(None,1)`'s name == the last token over boundary + the full native-domain fuzz. The name side is separator-insensitive (it is the bare last token), so this holds on ALL inputs, not just the single-space domain. `encode_name` is the verbatim token text under the token bijection (mapping.md §2). |

Postcondition `ToSeq(Result()) == PSeq(encode_name(last_token(ToSeq(tokens))))`
pins the name to the single last token. The pre-patch `split(None, 1)` left the
name as the whole remainder after the first token; `model_prepatch.py`
reproduces that (the join of `tokens.drop(1)`) and **fails** this exact
postcondition whenever the type spans more than one token (`n >= 3`).

### B. The parsed type — `parsed_argument_type` ↔ `argtype`

| # | model.py impl op (`parsed_argument_type`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `tokens: List[int]` | `fieldarg: str` | R | as A1. |
| B2 | `prefix_len = len(tokens) - 1`; backward construction loop building `joined(tokens.take(prefix_len))` | `argtype` = the first element of `fieldarg.rsplit(None, 1)` | R + A-reference (single-space domain) | `argtype` is every token BEFORE the last; the model re-emits that prefix separated by single spaces. The deep model `joined`/the verified loop spell that out; **on single-space-separated input** (the form every tested field argument takes, e.g. `Dict[str, str]`) G-AX confirms `str.rsplit(None,1)`'s type == the model's single-space rendering of the leading tokens. On genuine multi-whitespace input the real left piece is preserved verbatim and the single-space model legitimately diverges (out of the modelled domain, mapping.md §2/§3.1); G-AX fuzzes that native domain and asserts the restriction holds rather than dodging it. |

Postcondition `ToSeq(Result()) == joined(ToSeq(tokens).take(len(tokens) - 1))`
pins the type to the full leading run. The pre-patch `split(None, 1)` kept only
the FIRST token as the type; `model_prepatch_2.py` reproduces that
(`PSeq(encode_name(tokens[0]))`) and **fails** this postcondition whenever the
type spans more than one token (`n >= 3`).

## C. No kind-3 (unexpressible-changed-op) steps; no consumed axioms

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — moving the single split from the FIRST whitespace boundary to the
LAST — is modelled **deeply** (the fold `joined` + `last_token` and the verified
loops), not hidden behind an axiom about the function under change. There is
**no `@ContractOnly` axiom** in this bundle: the proof depends on no opaque
callee's `Ensures`. The deep models are instead validated against the real
`str.rsplit(None, 1)` by axiom_check.py (G-AX, mapping.md §3) as
**A-references**. The validation is stated **conditionally on the modelled
single-space-separated domain** (mapping.md §2/§3.1): the name side
(`last_token`) matches on all inputs, while the type side (`joined`) matches
only when the input is single-space-separated — the form every tested F2P/P2P
field argument takes. G-AX fuzzes the callee's full native whitespace domain and
asserts this restriction (in-domain agreement + demonstrated out-of-domain
divergence), rather than only exercising the abstraction's own image.

## D. G-DIFF — which prepatch fails, and on which clause

Two independently-observable fixed behaviours come from the one-line change, so
there are two prepatch skeletons, each keeping the frozen spec byte-identical
(verified) and reverting ONLY one function's impl to the pre-patch LEFT-most
split:

* `model_prepatch.py` reverts `parsed_argument_name`: the name becomes the join
  of every token AFTER the first (`joined(tokens.drop(1))`) — the old
  `split(None, 1)` remainder. For a multi-token type this is not a single token,
  so verification FAILS on
  `ToSeq(Result()) == PSeq(encode_name(last_token(ToSeq(tokens))))`
  (observed: `model_prepatch.py:105 Postcondition of parsed_argument_name might
  not hold`).
* `model_prepatch_2.py` reverts `parsed_argument_type`: the type becomes only
  the FIRST token (`PSeq(encode_name(tokens[0]))`) — the old `split(None, 1)`
  head. For a multi-token type this drops every later token, so verification
  FAILS on `ToSeq(Result()) == joined(ToSeq(tokens).take(len(tokens) - 1))`
  (observed: `model_prepatch_2.py:129 Postcondition of parsed_argument_type
  might not hold`).

Together these are exactly the bug the issue reports: for
`:param dict(str, str) opc_meta:` the old code renders the type as `dict(str,`
and the name as `str) opc_meta`; the fix renders type `dict(str, str)` and name
`opc_meta`. The F2P scenario `:param Dict[str, str] params:` is the same shape
(`n = 3` tokens).

## E. verify(model) ⇒ resolved

`parsed_argument_name` verifies only if its output is the single last token (A2)
and `parsed_argument_type` verifies only if its output is the full leading run
re-emitted with single spaces (B2). By R (str ↔ List[int] tokens, the
single-space-separator abstraction matching the F2P/P2P inputs) the verified
functions equal the gold patch's `argname` / `argtype` on the tested inputs; by
G-AX the deep models equal the real `str.rsplit(None, 1)` on that modelled
single-space-separated domain (A-references), with the type side's restriction
to that domain explicitly verified rather than dodged. Every tested field
argument (`Dict[str, str] params`, `int age`, `Tuple[str, ...] items`, …) lies
in the single-space domain, so the restriction loses no tested coverage.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited deep-model references on the tested
inputs — and the gold patch resolves (G-RESOLVE). The single trust point is
refinement fidelity (this document, G-EQ) plus the G-AX deep-model validation;
there are no consumed axioms.
