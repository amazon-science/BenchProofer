# mapping.md — sphinx-doc__sphinx-7590

## Symbol binding (file:line @ base_commit 2e506c5ab457cba743bb47eb5b8c8eb9dd51d23d)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_literalId` / `problem_spec_literalId` / `correct_literalId` | the literal-recognition body of `DefinitionParser._parse_literal` that produces the parsed literal's mangled id (`get_id`) | `sphinx/domains/cpp.py` `_parse_literal` (`cpp.py:4689-4742` post-patch; `cpp.py:4651-4694` pre-patch) |
| `numId data` | `ASTNumberLiteral(data).get_id(...)` = `"L%sE" % data` | `cpp.py:832-834` (`ASTNumberLiteral.get_id`) |
| `identId ident` | `ASTIdentifier(ident).get_id(version>=2, non-anon)` = `'St'` when `ident == "std"` (the reserved-namespace abbreviation, `cpp.py:586-587`), else `str(len(ident)) + ident` | `cpp.py:578-595` (`ASTIdentifier.get_id`) |
| `udlId ident inner` | `ASTUserDefinedLiteral(literal, ident).get_id(...)` = `'clL_Zli{}E{}E'.format(ident.get_id(v), literal.get_id(v))` | `cpp.py:904-915` (post-patch `ASTUserDefinedLiteral.get_id`, the `_udl(...)` wrapper) |
| `finishLiteral` | the per-branch tail in `_parse_literal`: match the class suffix; if present return the suffixed `ASTNumberLiteral`, else call `_udl(...)` which folds a trailing `udl_identifier_re` identifier into an `ASTUserDefinedLiteral` | `cpp.py:4689-4730` post-patch (`_udl`, the float branch, the integer loop) |
| `floatMatch` (opaque) | `self.match(float_literal_re)` | `cfamily.py:50-60` (`float_literal_re`) |
| `floatSuffixMatch` (opaque) | `self.match(float_literal_suffix_re)` = `[fFlL]\b` | `cfamily.py:66` (`float_literal_suffix_re`, ADDED by patch) |
| `binMatch` / `hexMatch` / `decMatch` / `octMatch` (opaque) | `self.match(binary_literal_re / hex_literal_re / integer_literal_re / octal_literal_re)` | `cfamily.py:38-43` |
| `intSuffixMatch` (opaque) | `self.match(integers_literal_suffix_re)` (ADDED by patch; replaces the old `while self.current_char in 'uUlLfF': self.pos += 1` loop) | `cfamily.py:44-53` (`integers_literal_suffix_re`) |
| `udlMatch` (opaque) | `self.match(udl_identifier_re)` inside `_udl` | `cpp.py:300-302` (`udl_identifier_re`, ADDED by patch) |

### What the patch changes (base_commit)

The C++ literal parser `_parse_literal` recognises a numeric literal and builds an
`ASTNumberLiteral` whose `get_id` is `"L" + sourceText + "E"`. Pre-patch:

```python
for regex in [float_literal_re, binary_literal_re, hex_literal_re,
              integer_literal_re, octal_literal_re]:
    pos = self.pos
    if self.match(regex):
        while self.current_char in 'uUlLfF':   # ad-hoc suffix consumption
            self.pos += 1
        return ASTNumberLiteral(self.definition[pos:self.pos])
# TODO: user-defined lit
```

There is no support for **user-defined literals** (UDLs): a literal directly
followed by an identifier, e.g. `6.62607015e-34q_J` (the issue's repro) or
`5_udl`. Parsing such input fails ("Expected end of definition") because the
trailing identifier is left unconsumed.

The gold patch:
1. splits the float branch out of the loop and gives it a dedicated float suffix
   recogniser (`float_literal_suffix_re = [fFlL]\b`);
2. replaces the ad-hoc `while … in 'uUlLfF'` integer-suffix loop with a proper
   `integers_literal_suffix_re` (with a trailing `\b`, so it does not eat a UDL);
3. adds a local `_udl(literal)` helper: after a base literal with **no** standard
   suffix, if a `udl_identifier_re` identifier follows, it wraps the literal in a
   new `ASTUserDefinedLiteral(literal, ident)`. Its `get_id` mangles the UDL as a
   call of the identifier on the literal:
   `'clL_Zli{}E{}E'.format(ident.get_id(v), literal.get_id(v))`.

A standard suffix takes precedence over a UDL identifier (the suffix recognisers'
trailing `\b` is what disambiguates `5l` the suffixed long from `5lll` the UDL).
The same UDL folding is applied to string and character literals too and the
analogous (UDL-free) suffix cleanup is mirrored in `sphinx/domains/c.py`; the
bundle models the **numeric** literal id computation in `cpp.py`, which is the
behaviour the F2P test (`test_expressions`) exercises with the issue's
`6.62607015e-34q_J` case and the `i + '_udl'` / `f + 'fudl'` families.

### Lean modeling

- A literal is recognised at the head of the input `s : List Char`. Each lexical
  recogniser is modeled as an `opaque … : List Char → Nat` returning the length
  of the prefix it consumes (0 = no match) — `match` on a compiled regex anchored
  at `self.pos` either advances `self.pos` by the match length or leaves it.
- `numId`, `identId`, `udlId` reproduce the three `get_id` formulas exactly.
- `finishLiteral baseLen s suffixMatch` is the shared per-branch tail: it tries
  the class suffix recogniser on the tail after the base literal; if it matches
  (length > 0) the suffix is folded into the literal's source text and the bare
  `numId` is returned; otherwise it tries `udlMatch` on the tail and, on a match,
  wraps the base `numId` in `udlId` — exactly the post-patch `_udl` logic.
- `problem_spec_literalId` / `implementation_literalId` first try the float
  branch (`floatMatch` + `floatSuffixMatch`), then the integer recognisers in the
  patch's order binary, hex, decimal, octal (each with `intSuffixMatch`).
- The pre-patch impl (`Solution_prepatch.lean`) keeps a standard suffix but never
  folds a trailing identifier (no `udlMatch` step), so `6.62607015e-34q_J` mangles
  to `L6.62607015e-34E` (the `q_J` is dropped) instead of the UDL mangling — the
  bug. Its `correct_literalId` is unclosable whenever a bare literal is followed
  by an identifier with no standard suffix.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.definition[self.pos:]` (the unparsed head) | `s : List Char` | per-code-point list, total Lean indexing |
| `self.match(regex)` advancing `self.pos` by `k` | recogniser returns `k : Nat` (0 = no match) | length of consumed prefix |
| `ASTNumberLiteral(data).get_id` = `"L"+data+"E"` | `numId data` | string equality |
| `ASTIdentifier(id).get_id` = `'St'` if `id == "std"` else `str(len(id))+id` | `identId id` | string equality (non-anon, non-dtor, version ≥ 2; `udl_identifier_re` can never produce an anon `@…` or dtor `~…` name) |
| `ASTUserDefinedLiteral.get_id` = `clL_Zli{ident}E{inner}E` | `udlId ident inner` | string equality |
| parse result mangled id, or parse failure | `Option String` (`some id` / `none`) | `None ↔ none` |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behaviour the patch changes is the CONTROL
  FLOW that recombines the lexical recognisers (folding a trailing identifier into
  a user-defined literal, and suffix-takes-precedence), modeled DEEPLY and
  structurally. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed
  decision. The `axioms` region declares only `opaque` signatures, no
  `axiom … _prop`, so **G-AX skips**.
- The eight recognisers (`floatMatch`, `floatSuffixMatch`, `binMatch`, `hexMatch`,
  `decMatch`, `octMatch`, `intSuffixMatch`, `udlMatch`) are the unchanged (or, for
  the two new suffix regexes and the udl regex, purely-lexical) prefix matchers.
  Each appears IDENTICALLY in the spec and the impl, so it cancels in the
  differential test — an A-reference, not a consumed axiom. None leaves an output
  component free: `result` is fully pinned by `problem_spec` to the post-patch
  recombination.
- **Suffix precedence:** the disambiguation between a standard suffix and a UDL
  identifier lives in the recognisers' trailing `\b` (`[fFlL]\b`,
  `integers_literal_suffix_re … \b`). In the model `finishLiteral` checks the
  suffix recogniser FIRST and only tries `udlMatch` when no suffix matched, which
  is faithful to the post-patch branch (`if hasSuffix: return lit else: _udl(lit)`).
  G-CONF fuzzes both suffixed and UDL-suffixed inputs to exercise this.

## G-CONF fuzz seed

Pinned LCG seed: **7590** (see `conformance_check.py` `SEED`). Corpus: the
real compiled regexes from `sphinx/util/cfamily.py` + `udl_identifier_re` drive
the recognisers on both differential sides; inputs are randomly assembled from
{integer / decimal-float / hex-float bodies} × {no suffix, a standard suffix, a
UDL identifier, a non-matching trailer}, ≥1e5 fuzzed strings, plus the F2P
edge cases (`6.62607015e-34q_J`, `5_udl`, `5uludl`, `5.0fudl`, `0xApF_udl`, bare
`5`, `5ul`, `5.0f`). The shadow of `implementation_literalId` is diffed against an
in-process replica of the POST-PATCH `_parse_literal` id computation.
