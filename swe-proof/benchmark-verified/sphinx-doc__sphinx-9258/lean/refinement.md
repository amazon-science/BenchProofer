# refinement.md — sphinx-doc__sphinx-9258

Operation-by-operation correspondence between `implementation_splitTypeSpec`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH
`PyXrefMixin.make_xrefs`). Tags: **R** type refinement, **A-consumed** proof
uses an axiom, **A-reference** deep model validated == real callee, **I**
identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let subTargets := reSplit true target` | `delims = r'(…|\s*\|\s*|\.\.\.)'; delims_re = re.compile(delims); sub_targets = re.split(delims, target)` | R |
| 2 | `for sub in subTargets do` | `for sub_target in filter(None, sub_targets):` (empty pieces dropped by the `if sub ≠ []` guard) | R |
| 3 | `if sub ≠ [] then …` | `filter(None, sub_targets)` — skip empty pieces | I |
| 4 | `if (delimLen true sub).isSome then results := results ++ [Seg.sep sub]` | `if delims_re.match(sub_target): results.append(contnode or innernode(sub_target, sub_target))` | R |
| 5 | `else results := results ++ [Seg.name sub]` | `else: results.append(self.make_xref(rolename, domain, sub_target, …))` | R |
| 6 | `return results` | `return results` | I |

## Deep-model rows (the changed op)

The patch changes op #1's `delims` regex (adds the `\s*\|\s*` alternative). Per
SPEC_GUIDE §3, a changed op is modeled DEEPLY, never axiomatized. The deep model
is the `pure`-region tower:

| Lean helper | Python counterpart | tag |
|---|---|---|
| `delimLen pipe` (+ `spacesLen`, `isSp`, `isBracket`, `dotsLen`, `pipeOrDots`, `tailDelim`) | greedy prefix match of the `delims` alternation (`\s*[\[\]\(\),](?:\s*or\s)?\s*` \| `\s+or\s+` \| `\s*\|\s*` \| `\.\.\.`) | R (deep model) |
| `reSplitFuel` / `reSplit pipe` | `re.split(delims, target)` with capturing group (interleaved text/sep pieces incl. empties) | R (deep model) |
| `classifySeg` | `Seg.sep`/`Seg.name` by `bool(delims_re.match(piece))` | R (deep model) |
| `tokenize` | `[classify(p) for p in filter(None, re.split(delims,target))]` | R (deep model) |

## Notes

- **Every step is R or I — no A.** The regex tokeniser (the changed op) is
  modeled deeply as pure functions over `List Char`; there is no `opaque`/`axiom`
  callee. The `axioms` region is empty; **G-AX skips**.
- **R vs I.** Steps 3, 6 are **I** (unchanged control flow, literal
  transliteration). Steps 1, 2, 4, 5 are **R**: the Python `str`/`re`/node
  objects are refined to the `List Char` / `List Seg` carriers per the mapping.md
  bijection (`re.split`↔`reSplit`, `delims_re.match`↔`delimLen`, the two
  `append` branches ↔ `Seg.sep`/`Seg.name`).
- **The fix itself** is the extra `\s*\|\s*` alternative inside `delimLen`
  (via `pipeOrDots`), reached with the `true` flag. The pre-patch impl
  (`Solution_prepatch.lean`) calls `reSplit false` / `delimLen false`, which omits
  that alternative, so `int | str` is never split around the bar and stays one
  `Seg.name` — the actual pre-fix behaviour. That impl cannot satisfy
  `problem_spec_splitTypeSpec` (whose `tokenize` uses the pipe), so its proof is
  unclosable (G-DIFF).
- The `contnode` / `innernode` details of the real separator/xref nodes are
  UNCHANGED by the patch and orthogonal to it (the fix only changes which
  substrings become names vs separators); they are represented by the `Seg`
  carrier and not modeled as node objects. No dead axiom.
- **Grounded oracle, no echo weakness.** The spec is definitional
  (`result = tokenize target`) over a DEEP, fully-grounded model: `tokenize`
  is validated byte-for-byte against the real post-patch
  `re.split`+classify (G-CONF fuzz; `isSp` equals Python `\s` over all of
  Unicode). Consequently an impl-region body that echoes the oracle
  (`:= tokenize target`) is extensionally the post-patch behavior itself —
  its faithful refined patch IS the gold patch and resolves under the
  harness. Such an echo is a CORRECT implementation (a positive control),
  not a wrong-impl counterexample; a genuine spec-too-weak attack must
  diverge from `tokenize` on some input.
- **G-CONF** mechanically refutes the R/I legs: a Python replica of the Lean
  model (byte-identical logic) is diffed against the real post-patch
  `re.split`+classify over ≥1e5 fuzzed inputs (NEW pattern), and cross-checked
  against the direct `re.split` for BOTH the NEW and OLD patterns. No A legs.
