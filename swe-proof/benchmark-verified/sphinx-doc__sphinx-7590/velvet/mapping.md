# mapping.md — sphinx-doc__sphinx-7590

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 2e506c5ab457cba743bb47eb5b8c8eb9dd51d23d`, states the
Lean↔Python type abstraction (the bijection G-CONF and G-AX use to bridge the
two value domains), and gives the provenance of each modeled callee.

Repo files under change: `sphinx/domains/cpp.py`, `sphinx/domains/c.py`,
`sphinx/util/cfamily.py`. The bundle models the **C++ floating-point literal
branch** of the expression parser — the headline case from the issue
(`6.62607015e-34q_J`) — which is the function the FAIL_TO_PASS test
`tests/test_domain_cpp.py::test_expressions` exercises.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `literalIdAfterFloat (floatText rest : List Char)` | the floating-point branch of `DefinitionParser._parse_literal` — `sphinx/domains/cpp.py:4646` (branch body 4705-4725 post-patch) | the modeled changed function: given a recognized float token and the characters that follow, produce the mangled identifier of the resulting literal node |
| `matchTypeSuffix` *(deep model — A-reference)* | `float_literal_suffix_re = re.compile(r'[fFlL]\b')` — `sphinx/util/cfamily.py:66` (NEW in patch) | recognizes a single typed float suffix bounded by a word boundary |
| `matchUdlIdent` / `takeIdentBody` *(deep model — A-reference)* | `udl_identifier_re = re.compile(r'(?x)[a-zA-Z_][a-zA-Z0-9_]*\b')` — `sphinx/domains/cpp.py:300` (NEW in patch) | recognizes the maximal user-defined-literal suffix identifier |
| (input split `floatText`/`rest`) *(A-reference, upstream)* | `float_literal_re` — `sphinx/util/cfamily.py:44` (UNCHANGED by patch) | the float recognizer; its match defines the `(floatText, rest)` decomposition handed to the model |
| `numberLitId` | `ASTNumberLiteral.get_id` — `sphinx/domains/cpp.py:832` (`"L%sE" % self.data`, UNCHANGED) | id of a plain numeric literal |
| `identId` | `ASTIdentifier.get_id` (version ≥ 2 branch) — `sphinx/domains/cpp.py:574` | id of an identifier: `len(id)+id`, with `std → St` |
| `udlLitId` | `ASTUserDefinedLiteral.get_id` — `sphinx/domains/cpp.py` (NEW: `'clL_Zli{}E{}E'.format(ident.get_id, literal.get_id)`) | id of a user-defined literal: the call-mangling `clL_Zli<identId>E<litId>E` |
| `parsedFloatId` | the observable `ast.get_id(version)` produced by the float branch | pure spec: the id string the parser must produce |

The pre-patch code the change removes (refinement audit only, not in the
consumer spec view): the trailing-suffix consumer
`while self.current_char in 'uUlLfF': self.pos += 1` inside the old
`for regex in [float_literal_re, ...]` loop (`cpp.py:4708-4711` pre-patch),
which produced a plain `ASTNumberLiteral` and never recognized a UDL.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (the matched float text, the trailing chars, the produced id) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]` |
| a single Python character `ch` (ASCII) | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; the relevant alphabet is ASCII (`[a-zA-Z0-9_.+-eEpPxX]`), total and exact |
| `re.match(float_literal_re, tok)` span | the `(floatText, rest)` split: `floatText = tok[:m.end()]`, `rest = tok[m.end():]` | the unchanged float recognizer; G-AX validates the split is faithful on every tested token |
| `self.definition[pos:self.pos]` slice | `List Char` concatenation | identity on character content |
| an `ASTLiteral` node's observable | its `get_id(version)` string | the F2P test observes `str(ast)` and `ast.get_id`; the id is the discriminating observable (§3) |

`List Char` is the carrier because every operation is per-character (regex
classes, word boundaries, slice concatenation, decimal-length prefixes).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `matchTypeSuffix` ↔ `float_literal_suffix_re` (A-reference, NEW regex)
**Callee:** `re.match(r'[fFlL]\b', rest)`. Modeled **deeply**: a single char in
`{f,F,l,L}` is a suffix iff it is *not* immediately followed by another word
character `[a-zA-Z0-9_]` (otherwise the trailing run is a UDL identifier, not a
type suffix — the role of the `\b`). `matchTypeSuffix rest = some c` iff
`rest = c :: cs`, `c ∈ {f,F,l,L}`, and (`cs = []` or `cs.head` is non-word).

### 3.2 `matchUdlIdent`/`takeIdentBody` ↔ `udl_identifier_re` (A-reference, NEW regex)
**Callee:** `re.match(r'(?x)[a-zA-Z_][a-zA-Z0-9_]*\b', rest)`. Modeled **deeply**:
matches iff `rest` starts with `[a-zA-Z_]`, consuming the maximal leading run of
`[a-zA-Z0-9_]`. The trailing `\b` always holds after a maximal word run, so the
model returns the maximal identifier prefix.

### 3.3 float recognizer `float_literal_re` (A-reference, UNCHANGED, upstream)
**Callee:** `re.match(float_literal_re, tok)`. The model takes the
`(floatText, rest)` decomposition as input; G-AX confirms that for every tested
token the real `float_literal_re` produces exactly that split (i.e. the model's
input contract matches reality).

### 3.4 id mangling `numberLitId`/`identId`/`udlLitId` (I + A-reference)
`numberLitId text = "L" ++ text ++ "E"` (= `ASTNumberLiteral.get_id`, unchanged).
`identId id = "St"` if `id = "std"`, else `len(id) ++ id` (= `ASTIdentifier.get_id`,
version ≥ 2). `udlLitId floatText id = "clL_Zli" ++ identId id ++ "E" ++
numberLitId floatText ++ "E"` (= the NEW `ASTUserDefinedLiteral.get_id`). These
are concrete string ops (**I**); G-AX validates the composite against the real
`get_id` of the parsed node.

**Soundness check (G-AX):** `axiom_check.py` constructs the real
`DefinitionParser`, parses each tested token, and asserts the real node's
`get_id(version=3)` (and `==` for version 2) equals `parsedFloatId(floatText,
rest)` under the bijection, over the F2P matrix plus randomized fuzz. It also
asserts the real `float_literal_re`/`float_literal_suffix_re`/`udl_identifier_re`
matches agree with the deep models. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`7590`**. The R/I shadow
it builds transliterates `matchTypeSuffix`/`matchUdlIdent`/`numberLitId`/
`identId`/`udlLitId` (R/I-tagged ops) to Python and diffs the produced id against
the behaviour of `patch.diff` (the real parser) over ≥10⁵ fuzzed literal tokens.
