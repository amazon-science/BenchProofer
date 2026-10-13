# refinement.md — sphinx-doc__sphinx-7590

Operation-by-operation correspondence between `implementation_literalId`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `_parse_literal`
numeric-literal id computation). Tags: **R** type refinement, **A-consumed**
proof uses an axiom, **A-reference** deep model validated == real callee, **I**
identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let fl := floatMatch s` | `pos = self.pos; if self.match(float_literal_re):` (`cpp.py:4705` post-patch) | A-reference |
| 2 | float branch: `finishLiteral fl s floatSuffixMatch` | the post-patch float tail: `hasSuffix = self.match(float_literal_suffix_re); floatLit = ASTNumberLiteral(...); return floatLit if hasSuffix else _udl(floatLit)` (`cpp.py:4706-4711`) | R (the discriminating clause) |
| 3 | `for m in [binMatch, hexMatch, decMatch, octMatch] do` | `for regex in [binary_literal_re, hex_literal_re, integer_literal_re, octal_literal_re]:` (`cpp.py:4712-4713`) | A-reference (per-recogniser) + I (loop order) |
| 4 | per-integer `finishLiteral il s intSuffixMatch` | `if self.match(regex): hasSuffix = self.match(integers_literal_suffix_re); intLit = ASTNumberLiteral(...); return intLit if hasSuffix else _udl(intLit)` (`cpp.py:4714-4720`) | R (the discriminating clause) |
| 5 | `finishLiteral`: `if suffixMatch rest > 0 then numId (s.take (baseLen+sfx))` | suffix-present path: keep the suffix in the literal source text, emit `"L"+text+"E"` | I |
| 6 | `finishLiteral`: else `let u := udlMatch rest; if u>0 then udlId (rest.take u) baseId else baseId` | `_udl(literal)`: `if not self.match(udl_identifier_re): return literal; ident = ASTIdentifier(self.matched_text); return ASTUserDefinedLiteral(literal, ident)` (`cpp.py:4694-4700`) | R (the discriminating clause) |
| 7 | `numId data = "L" ++ String.mk data ++ "E"` | `ASTNumberLiteral.get_id` = `"L%sE" % self.data` (`cpp.py:832-834`) | I |
| 8 | `identId ident = if ident = "std".toList then "St" else toString ident.length ++ String.mk ident` | `ASTIdentifier.get_id` (non-anon, v≥2) = `'St'` if `id == "std"` (`cpp.py:586-587`) else `str(len(id)) + id` (`cpp.py:591-595`; `udl_identifier_re` can never yield an anon `@…` or dtor `~…` name) | I |
| 9 | `udlId ident inner = "clL_Zli" ++ identId ident ++ "E" ++ inner ++ "E"` | `ASTUserDefinedLiteral.get_id` = `'clL_Zli{}E{}E'.format(ident.get_id(v), literal.get_id(v))` (`cpp.py:912-915`) | I |
| 10 | `return none` when nothing matched | `return None` (no literal recognised at the head) | I |

Notes:

- **The R legs are the UDL-folding control flow** (ops 2/4/6): after a base
  literal with no standard suffix, the post-patch code folds a trailing identifier
  into a user-defined literal; pre-patch it did not (the `# TODO: user-defined
  lit` line). SPEC_GUIDE §3 forbids axiomatizing this deeply-modeled changed
  decision, so the suffix-vs-UDL recombination is spelled out structurally in both
  `problem_spec_literalId` and the impl (via `finishLiteral`), not axiomatized. The
  three `get_id` mangling formulas (ops 7/8/9) are reproduced concretely (I).
- **The recognisers are A-reference, not A-consumed.** `floatMatch`,
  `floatSuffixMatch`, `binMatch`, `hexMatch`, `decMatch`, `octMatch`,
  `intSuffixMatch`, `udlMatch` model `self.match(<regex>)` for the corresponding
  compiled regex. Each appears IDENTICALLY in the spec and the impl, so it cancels
  in the differential test; the proof consumes no property of any of them, so
  there is no `axiom … _prop` and **G-AX skips**. None leaves an output component
  free — `result` is fully pinned by `problem_spec` to the post-patch
  recombination of the recogniser outputs.
- **Suffix precedence is modeled, not assumed** (op 5 before op 6): `finishLiteral`
  checks the suffix recogniser first and only folds a UDL when no suffix matched,
  matching the post-patch `if hasSuffix: return lit else: _udl(lit)`. The real
  disambiguation (a standard suffix's trailing `\b` vs a longer UDL identifier)
  lives inside the opaque recognisers, which are identical on both sides, so the
  diff isolates exactly the recombination control flow.
- **The fix itself** is ops 2/4/6: pre-patch (`Solution_prepatch.lean`) keeps a
  standard suffix but omits the `udlMatch` fold entirely, so a bare literal
  followed by an identifier (`6.62607015e-34q_J`, `5_udl`) mangles to just the
  bare `numId` and drops the identifier. Its `correct_literalId` is therefore
  unclosable whenever a literal is followed by a UDL identifier with no standard
  suffix (the two results disagree, and the recognisers are opaque so they cannot
  be proved equal) — exactly the signal G-DIFF wants.
- **G-CONF** mechanically refutes the R/I legs over ≥1e5 fuzzed inputs (no
  A-consumed legs): the Python shadow of the impl is diffed against the post-patch
  `_parse_literal` id computation, with all eight recognisers driven by the SAME
  real compiled regexes on both sides so the diff isolates the UDL-folding leg.
