# refinement.md — sphinx-doc__sphinx-10435

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`wrapInlineCode` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** where
the proof uses the axiom's `ensures`/frame, **A-reference** where a deep model is
validated == the real callee by G-AX), or **I** (identical concrete op). EVERY
step is R, A, or I; no kind-3 (changed-op inexpressible).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A leg and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviorally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The inline-code branch — `LaTeXTranslator.visit_literal` (`sphinx/writers/latex.py:1695`, changed lines 1710–1717)

Gold hunk:
```
  hlcode = hlcode.replace(r'\begin{Verbatim}[commandchars=\\\{\}]',
-                         r'\sphinxcode{\sphinxupquote{')
+                         r'\sphinxcode{\sphinxupquote{%')
  # get consistent trailer
- hlcode = hlcode.rstrip()[:-14]  # strip \end{Verbatim}
+ hlcode = hlcode.rstrip()[:-15]  # strip \n\end{Verbatim}
  self.body.append(hlcode)
- self.body.append('}}')
+ self.body.append('%' + CR + '}}')
```

| # | Solution.lean impl op (`wrapInlineCode`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A0 | parameter `snippet : List Char` (not `mut`) | `node.astext()` passed to the highlighter | R | `str` ↔ `List Char` (mapping §2). Read-only input: the branch renders it and never mutates it (directive 5) — not `mut`, so no frame obligation arises. |
| A1 | `let hlcode :| hlcode = beginTok ++ ['\n'] ++ renderedInline snippet ++ ['\n'] ++ endTok ++ ['\n']` | `hlcode = self.highlighter.highlight_block(node.astext(), lang, opts=opts, location=node)` (line 1707, UNCHANGED by the patch) | A-consumed | the unchanged highlighter callee, modeled by its weakest sufficient FRAME (mapping §3.1): begin prefix (37), newline, unconstrained body, newline, end (14), final newline. The proof consumes this frame to discharge the slicing; the body content is irrelevant to the spec. G-AX validates the frame against the real callee. NOT a deep model ⇒ not an A-reference. |
| A2 | `let hlcode := openTok ++ hlcode.drop beginTok.length` where `openTok = codeOpen ++ ['%']` | `hlcode = hlcode.replace(r'\begin{Verbatim}…\}]', r'\sphinxcode{\sphinxupquote{%')` (the added `%`) | R + I | `BEGIN` is a fixed-length prefix of `hlcode` (frame A1), so the single `.replace` of that prefix ↔ `openTok ++ hlcode.drop beginTok.length` (mapping §2 `s.replace(prefix,r)` row). The substituted string includes the new `%` (`openTok`). Concrete op transliterated by G-CONF. |
| A3 | `let stripped := rstrip hlcode` | `hlcode.rstrip()` | I | `str.rstrip()` ↔ `rstrip` (drop trailing whitespace; mapping §2). By the frame the only trailing whitespace is the single final newline. |
| A4 | `let hlcode := stripped.take (stripped.length - 15)` | `[:-15]  # strip \n\end{Verbatim}` (was `[:-14]`) | R + I | Python `s[:-15]` ↔ `s.take (s.length - 15)` (mapping §2). Drops the trailing `'\n' + END` (15 = 1 + 14). The change from 14 to 15 also removes the newline preceding END — half the fix. |
| A5 | `return hlcode ++ ['%', '\n', '}', '}']` | `self.body.append(hlcode); self.body.append('%' + CR + '}}')` (was `append('}}')`) | R + I | the two appends concatenate to `hlcode ++ '%' ++ '\n' ++ '}}'` (mapping §2 append row); `CR = '\n'`. The added leading `%` is the other half of the fix. |

**Net effect / discriminating content.** The post-fix output is exactly
`wrapped (renderedInline snippet) = codeOpen ++ ['%','\n'] ++ body ++ ['%','\n','}','}']`:
the `%` after the macro opening and the `%` before the closing braces are
line-break-suppressing LaTeX comment markers, so the newlines that bracket the
body no longer render as a spurious leading/trailing space. The two halves of
the fix (the two `%` markers; and dropping the pre-END newline via `[:-15]`)
together produce this. The frozen spec `out = wrapped (renderedInline snippet)`
pins this byte sequence exactly.

## B. The prepatch (the actual bug) and the discriminating clause

`Solution_prepatch.lean` keeps the spec byte-identical (G-DIFF `same_spec`) and
reproduces the pre-patch skeleton: substitutes `codeOpen` WITHOUT the `%`
(A2 without `openTok`'s marker), takes `length - 14` instead of `length - 15`
(A4: keeps the pre-END newline), and returns the bare `['}','}']` trailer
(A5 without the leading `%` and `\n`). Its output is
`codeOpen ++ ['\n'] ++ body ++ ['\n','}','}']` — it carries both surrounding
newlines unsuppressed and omits both markers. `prove_correct` therefore cannot
discharge `out = wrapped (renderedInline snippet)`: the verifier's residual goal
is the buggy slice `… ++ ['}','}'] = wrapped body`, which is false (it lacks the
`%`/`%\n` markers). Verified: prepatch fails at the `rw [compute …]` step
because the impl's concrete term does not match `wrapped body` (G-DIFF exit 1).
This is exactly the bug the issue + F2P `test_latex_code_role` observes.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operations that genuinely *changed* — the
substituted opening string (`+%`), the trailer count (`-14`→`-15`), and the
appended trailer (`}}`→`%\n}}`) — are all ordinary `List Char` slice/concat ops
modeled **concretely** (steps A2/A4/A5, R + I), transliterated by G-CONF. The
only axiomatized construct is the **unchanged** highlighter callee (A1,
A-consumed, frame-only), never the function under change and never the changed
ops. No dead axioms: the frame is consumed by `compute`.

**Termination semantics.** The file uses `loom.semantics.termination "total"`
(total correctness). The real routine is straight-line (one render call plus
bounded list surgery) — it always terminates and returns, and the F2P test
observes its returned markup, so total correctness is the faithful semantics.
Partial correctness would admit a same-spec implementation that diverges (a
non-terminating body vacuously satisfies every `ensures`) — an impl the tests
would reject — leaving the spec under-constrained on exactly that axis.

## D. verify(Solution) ⇒ resolved

`wrapInlineCode` verifies only if its output equals `wrapped (renderedInline
snippet)` — the exact post-fix byte sequence with both `%` markers and the
suppressed pre-END newline (A2/A4/A5). By R (`str ↔ List Char`, the prefix-`replace`,
`take`, and append bijections of mapping §2) the verified routine equals the
patched `visit_literal` branch on the highlighter's framed output; by A-consumed
(G-AX) the real `highlight_block` meets the frame the proof uses; by G-CONF the
R/I transliteration of the trailer surgery agrees with `patch.diff`'s behavior on
≥10⁵ inputs (seed 10435), the real callee on both sides. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and one audited unchanged callee — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: axiom soundness
(G-AX, the highlighter frame) and refinement fidelity (this doc, G-EQ + G-CONF).
