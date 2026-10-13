# refinement.md — sphinx-doc__sphinx-7590

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `literalIdAfterFloat` `do` block plus the deep `pure`-region models it
calls) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A-consumed** (proof uses an axiom's
property), **A-reference** (a deep model validated == its real callee by G-AX),
or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A-reference legs are validated by **G-AX** (`axiom_check.py`); the narrative
is audited by **G-EQ**. Claim: any impl verifying against this frozen spec,
refined per the map below, produces the same literal id as the gold patch on
the tested tokens, so the F2P test passes and the harness resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The modeled site — the C++ float branch of `DefinitionParser._parse_literal`

The bundle models the floating-point branch of `_parse_literal`
(`sphinx/domains/cpp.py:4646`). Post-patch that branch is:

```python
pos = self.pos
if self.match(float_literal_re):
    hasSuffix = self.match(float_literal_suffix_re)
    floatLit = ASTNumberLiteral(self.definition[pos:self.pos])
    if hasSuffix:
        return floatLit
    else:
        return _udl(floatLit)        # try a UDL identifier; wrap if present
```

with `_udl(literal)` matching `udl_identifier_re` and, on success, returning
`ASTUserDefinedLiteral(literal, ASTIdentifier(matched_text))`. The observable
the F2P `test_expressions` checks is `ast.get_id(version)` (and `str(ast)`).

| # | Solution.lean impl op (`literalIdAfterFloat`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `floatText`, `rest : List Char` | the recognized float text `self.definition[pos:self.pos]` and the chars that follow it | R | `str` ↔ `List Char` (mapping.md §2); the split is the unchanged `float_literal_re` match (mapping.md §3.3), validated by G-AX. |
| A2 | `matchTypeTag rest` | `self.match(float_literal_suffix_re)` (`[fFlL]\b`, NEW) | A-reference + I | deep model of the NEW one-char suffix regex; the `\b` ⇔ "next char non-word or end". G-AX validates `matchTypeTag` == real `re.match(float_literal_suffix_re, rest)`. The branch (`if hasSuffix`) is concrete control flow (I). |
| A3 | `matchSuffixName rest` | `self.match(udl_identifier_re)` inside `_udl` (`[a-zA-Z_][a-zA-Z0-9_]*\b`, NEW) | A-reference + I | deep model of the NEW UDL-identifier regex (maximal word run from a letter/underscore start). G-AX validates == real `re.match(udl_identifier_re, rest)`. |
| A4 | `numberLitId text = "L"++text++"E"` | `ASTNumberLiteral.get_id` (`"L%sE" % self.data`, UNCHANGED) | I | identical concrete string op; G-AX validates against the real node's id. |
| A5 | `identId ident` (`std→St`, else `len++ident`) | `ASTIdentifier.get_id` version≥2 branch (`str(len)+identifier`, `std→St`) | A-reference + I | deep model of the unchanged identifier mangling, restricted to the ordinary-name case the UDL suffix produces (never anon, never `~`). G-AX validates. |
| A6 | `suffixedLitId floatText ident = "clL_Zli"++identId ident++"E"++numberLitId floatText++"E"` | `ASTUserDefinedLiteral.get_id` (`'clL_Zli{}E{}E'.format(ident.get_id, literal.get_id)`, NEW class) | I | identical concrete composition of A4/A5; this is the genuinely-new behavior, modeled **deeply/concretely**, not axiomatized. G-AX validates the composite against the real node id. |
| A7 | `return`/`pure` of the selected id | the `return floatLit` / `return _udl(floatLit)` choice mapped through `get_id` | I | the three-way `match` mirrors `if hasSuffix … else _udl(…)` exactly. |

## B. The discriminating change

Pre-patch the float branch lived inside the loop
`for regex in [float_literal_re, …]` and consumed trailing chars with
`while self.current_char in 'uUlLfF': self.pos += 1`, then returned a plain
`ASTNumberLiteral` — it had **no UDL recognition**. So `6.62607015e-34q_J`
parsed as the number `6.62607015e-34` (id `L6.62607015e-34E`) and the `q_J`
caused "Expected end of definition" downstream (the issue's symptom).

Post-patch the same token yields the user-defined literal with id
`clL_Zli3q_JEL6.62607015e-34EE`. `Solution_prepatch.lean` reproduces the
pre-patch op (`numberLitId (floatText ++ <uUlLfF run>)`) and **fails**
`out = parsedFloatId floatText rest` precisely on the UDL case (the suffix-name
branch of `parsedFloatId` produces `suffixedLitId`, which the prepatch never
emits) — G-DIFF. The discriminating clause is the `matchSuffixName rest = some
ident` case.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — recognizing
a trailing UDL identifier and producing the call-mangled id — is modeled
**deeply/concretely** (`matchSuffixName` + `suffixedLitId`, steps A3/A6),
**not** hidden behind an axiom about the function under change. There is no
consumed axiom. The A-references (A2, A3, A5) cover the NEW/unchanged regexes
and the unchanged identifier mangling, each executable-validated by G-AX.

## D. verify(Solution) ⇒ resolved

`literalIdAfterFloat` verifies only if its output equals `parsedFloatId` for all
`(floatText, rest)` — i.e. it picks the type-tag id when a tag follows, the
`clL_Zli…` UDL id when a name follows, and the plain id otherwise. By R
(`str ↔ List Char`, the unchanged-float-regex split) the verified function
equals the post-patch float branch's `get_id` on every tested token; by G-AX
the deep models `matchTypeTag`/`matchSuffixName`/`identId` equal the real
regexes/mangling and the composite equals the real node id (A-references); by
G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵
fuzzed tokens. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and audited callees — and the gold
patch resolves (G-RESOLVE). Trust points: A-reference soundness (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).
