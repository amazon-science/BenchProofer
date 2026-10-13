# mapping.md — sphinx-doc__sphinx-7590

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 2e506c5ab457cba743bb47eb5b8c8eb9dd51d23d`, states the type
abstraction (the C++ definition string ↔ `List[int]` of code points), and gives
the provenance of each axiom (callee source + the exact behaviour the axiom
encodes).

Repo files under change: `sphinx/domains/cpp.py`, `sphinx/domains/c.py`,
`sphinx/util/cfamily.py`. The F2P-discriminating behaviour lives in the C++
domain (`tests/test_domain_cpp.py::test_expressions`); the parallel
suffix-handling rewrite in the simpler dialect (`sphinx/domains/c.py`) is also
modeled (`c_number_literal_id`) and validated against the real C-domain parser by
G-AX, though no FAIL_TO_PASS test exercises it directly.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `number_literal_id(lit, ident, suffixed, ident_id)` | `DefinitionParser._parse_literal` — `sphinx/domains/cpp.py:4640` (number-literal branch, body lines 4661-4667 pre-patch) + the new `_udl` nested helper (post-patch lines 4692-4699) + `ASTUserDefinedLiteral.get_id` (post-patch) | the modeled changed function: given a numeric literal already matched (`lit`), whether a recognised numeric suffix follows (`suffixed`), and the trailing UDL identifier (`ident`, with its precomputed component id `ident_id`), decide between a plain number literal and a user-defined literal and return the resulting v3/v4 mangled id |
| `c_number_literal_id(lit, trail, valid)` | `DefinitionParser._parse_literal` — `sphinx/domains/c.py` (the parallel simpler-dialect number-literal branch, pre-patch maximal-run loop `while self.current_char in 'uUlLfF': self.pos += 1`) | the modeled changed function for the simpler dialect (which has NO user-defined literals): given a matched numeric literal (`lit`), the maximal trailing suffix-alphabet run (`trail`), and whether that run is a recognised numeric suffix (`valid`), decide whether the run is folded into the literal text and return the resulting ordinary numeric-literal id (`L<text>E`). Carrier shared with the cpp model: `List[int]` of code points; id via the shared `number_id_seq` deep model |
| `udl_id_seq(lit, ident)` *(deep model — A-reference)* | `ASTUserDefinedLiteral.get_id` — newly added class, `sphinx/domains/cpp.py` (post-patch), `get_id` body `'clL_Zli{}E{}E'.format(self.ident.get_id(version), self.literal.get_id(version))` | the modeled NEW mangling: id of a user-defined literal = `clL_Zli<ident-id>E<literal-id>E`; validated == the real `ASTUserDefinedLiteral.get_id` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `number_id_seq(lit)` *(deep model — A-reference)* | `ASTNumberLiteral.get_id` — `sphinx/domains/cpp.py:832` | UNCHANGED sub-callee modelled DEEPLY: `"L%sE" % self.data`, i.e. `L` + lit + `E`; validated == the real `ASTNumberLiteral.get_id` by axiom_check.py (G-AX) |
| `ident_mangle(ident)` *(axiom — A-consumed)* | `ASTIdentifier.get_id` — `sphinx/domains/cpp.py:578` | UNCHANGED callee; on a nonempty, ordinary identifier (NOT the reserved `std`, NOT a destructor `~…`, NOT anon `@…`) the v3/v4 branch returns `str(len(ident)) + ident` (a strict length prefix, so the identifier text is a proper suffix of its id). The axiom is contracted to exactly this domain by precondition — `std` is excluded (the real generator returns `'St'` there), `~`/`@` cannot begin a UDL identifier |

The pre-patch repo behaviour the change removes (for the refinement audit, not
referenced from the consumer spec view): the suffix-consuming loop
`while self.current_char in 'uUlLfF': self.pos += 1`
(`sphinx/domains/cpp.py:4665-4666`), which (a) only ever consumes the fixed
alpha-suffix run and (b) never builds a user-defined literal — so a numeric
literal immediately followed by a UDL identifier (e.g. `6.62607015e-34q_J`)
left the identifier unconsumed and the surrounding parse failed with
"Expected end of definition".

The parallel C-domain `_parse_literal` rewrite (`sphinx/domains/c.py`) is now
MODELED by `c_number_literal_id` (§3.4), not carried as a non-discriminating
hunk. The remaining gold hunks are non-discriminating for the modeled behaviour
and are carried by `patch.diff` verbatim: the new `udl_identifier_re` regex and
the `'udl'` description mode (`sphinx/util/cfamily.py`, `sphinx/domains/cpp.py`);
the `'udl'` branch of `ASTIdentifier.describe_signature`; the two TODO comments;
and the `key = symbol.get_lookup_key()` inlining. (The
`integers_literal_suffix_re` / `float_literal_suffix_re` regexes are the
acceptance predicate the C-domain decision consumes, abstracted by the `valid`
parameter — §3.4 — and likewise used by the cpp `suffixed` parameter.) None
changes the v2/v3/v4 id or the `str()` of a parsed literal beyond what the modeled
functions pin.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the matched numeric-literal text `self.definition[pos:self.pos]` (`str`) | `lit: List[int]` of code points | `lit[k]` ↔ `ord(text[k])`; `len(lit)` ↔ `len(text)` |
| the UDL identifier `self.matched_text` from `udl_identifier_re` (`str`) | `ident: List[int]` of code points | as above; empty list ↔ no UDL identifier present |
| whether a valid numeric suffix follows (`self.match(float_literal_suffix_re)` / `integers_literal_suffix_re`) | `suffixed: bool` (cpp) / `valid: bool` (C-domain) | `True` ↔ the regex matched at the current position |
| the maximal trailing run of suffix-alphabet chars `uUlLfF` after a C-domain numeric literal (what the pre-patch loop scanned) | `trail: List[int]` of code points | a code-point run ↔ a `List[int]`; empty list ↔ no trailing suffix-alphabet character |
| the produced id string (`str`, v3/v4) | `List[int]` of code points; specification carried by `PSeq[int]` via `ToSeq` | `str` concatenation ↔ list `+`; literal id characters as their ASCII code points |

`str` indexing/iteration is banned in Nagini, so all character data is carried
as `List[int]`; the specification is phrased over `PSeq[int]` via `ToSeq`.

Code points used in the id-mangling constants: `clL_Zli` =
`PSeq(99,108,76,95,90,108,105)`; `L` = `76`; `E` = `69`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `ident_mangle` ↔ `ASTIdentifier.get_id` (A-consumed)
**Callee:** `ASTIdentifier.get_id(version)` (`sphinx/domains/cpp.py:578-593`),
UNCHANGED by the patch. The real v3/v4 body has special-case branches:

```python
if self.identifier == "std":        return 'St'        # length 2, NOT length-prefixed
elif self.identifier[0] == "~":     return 'D0'        # destructor
else:
    if self.is_anon():              return 'Ut%d_%s' % (len(...)-1, ...)
    else:                           return str(len(self.identifier)) + self.identifier
```

so the length-prefixed form `str(len(ident)) + ident` holds ONLY for a nonempty,
ordinary identifier that is not `std`, not `~…`, not anon `@…`
(`"_udl"` → `"4_udl"`, `"q_J"` → `"3q_J"`, `"uludl"` → `"5uludl"`). A UDL
identifier comes from `udl_identifier_re = [a-zA-Z_][a-zA-Z0-9_]*`, so it cannot
begin with `~`/`@` — but it **can** be exactly `std` (e.g. `5std` parses as a UDL
with identifier `std`, giving the real id `clL_ZliStEL5EE`, NOT
`clL_Zli3stdEL5EE`). The earlier provenance claim that a `std` UDL suffix is
impossible was FALSE. Therefore the axiom is contracted over a RESTRICTED domain
— nonempty and `!= std` (code points 115,116,100), imposed by precondition and
threaded through `udl_id_seq` / `number_literal_id` — on which the
length-prefixed form is exact; it is the weakest contract the UDL mangling needs.
G-AX (`axiom_check.py`) validates the axiom on this domain (boundary + 5000
in-domain fuzz) AND asserts the excluded branches `std`/`~…`/`@…` genuinely
deviate from the length-prefixed claim, so the over-claim is caught, not hidden,
and the exclusion is load-bearing and complete. The F2P UDL suffixes
(`_udl`/`q_J`/`uludl`/`fudl`) are all in-domain, so no tested behaviour is lost.
Provenance evidence: the source above; the F2P test expectations
(`clL_Zli4_udlE…`, `clL_Zli3q_JE…`).

### 3.2 `number_id_seq` ↔ `ASTNumberLiteral.get_id` (A-reference, deep model)
**Callee:** `ASTNumberLiteral.get_id(version)` (`sphinx/domains/cpp.py:832-833`),
UNCHANGED by the patch: `return "L%sE" % self.data`, i.e. `L` + the literal text
+ `E`. This trivial `L…E` framing is modelled DEEPLY (`number_id_seq(lit) =
PSeq(76) + lit + PSeq(69)`), not behind a consumed axiom; G-AX asserts it equals
the real `ASTNumberLiteral.get_id`. Provenance: the source above; the F2P
expectations (`…EL6.62607015e-34EE`, `…EL5EE`).

### 3.3 The mangling and the parse decision (modeled DEEPLY — A-reference)
The NEW operation is `ASTUserDefinedLiteral.get_id` =
`'clL_Zli{}E{}E'.format(ident.get_id(version), literal.get_id(version))` and the
decision in `_parse_literal` to build a UDL when a numeric literal carries no
valid numeric suffix but is followed by a UDL identifier. These are modeled
DEEPLY (the spelled-out concatenation `udl_id` and the branch in
`number_literal_id`), not behind a consumed axiom about the function under
change. `axiom_check.py` (G-AX) constructs the real
`ASTUserDefinedLiteral`/`ASTNumberLiteral`/`ASTIdentifier` objects (and exercises
the real `DefinitionParser` on the issue's `6.62607015e-34q_J` token and the
F2P UDL tokens) and asserts the real `get_id(3)`/`get_id(4)` and parsed `str()`
equal the model's predicted id-string and acceptance — validating the deep model
against the real callees. The two `get_id` sub-callees of the formula are the
A-consumed axioms §3.1/§3.2.

### 3.4 `c_number_literal_id` ↔ C-domain `DefinitionParser._parse_literal` (A-reference, deep model)
**Callee:** `DefinitionParser._parse_literal` (`sphinx/domains/c.py`, the
simpler dialect, which has **no user-defined literals**). The change is the
suffix-handling: the pre-patch maximal-run loop
`while self.current_char in 'uUlLfF': self.pos += 1` is replaced by a single
recognised-suffix regex match (`self.match(float_literal_suffix_re)` /
`self.match(integers_literal_suffix_re)`). The produced `ASTNumberLiteral` text
is `self.definition[pos:self.pos]`, which equals `lit + suffix` where `suffix`
is what the regex consumed.

The model carrier is `(lit, trail, valid)`: `lit` the matched numeric literal,
`trail` the maximal `uUlLfF` run following it, `valid` whether that run is a
recognised numeric suffix. The decision is modelled DEEPLY: `valid` ⇒ the run is
folded into the text (id `number_id_seq(lit+trail)`); `not valid` ⇒ the run is
left unconsumed (id `number_id_seq(lit)`). FAITHFULNESS of the abstraction: a
`\b`-terminated suffix regex matches the WHOLE maximal run or nothing — never a
strict, nonempty prefix — so the consumed suffix is exactly `trail` (when valid)
or empty (when not). The id-framing reuses the shared `number_id_seq` deep model
(`ASTNumberLiteral.get_id` is `"L%sE" % data`, identical class in both dialects).

The pre-patch behaviour the change removes (audit only, not referenced from the
consumer spec view): the maximal-run loop ALWAYS folds `trail`, so for a
non-recognised run (e.g. float `5.0` + `u`, integer `5` + `f`) it produced
`L5.0uE`/`L5fE` whereas the gold produces `L5.0E`/`L5E`. The model's `valid`
branch is exactly the discriminator. **Soundness check (G-AX):** §below.

**Soundness check (G-AX):** `axiom_check.py` imports only `sphinx.domains.cpp` /
`sphinx.domains.c` (the patched modules, in-container) and `sphinx.util.cfamily`;
for each F2P UDL token (ints/decimal-floats/hex-floats × suffixes, the
char-literal UDLs, the string UDL, and the issue's `6.62607015e-34q_J`) it parses
the expression with the real cpp parser and asserts `str(ast)` round-trips and
`ast.get_id(3)` equals the model-predicted mangling, and independently asserts
`ASTIdentifier.get_id` and `ASTNumberLiteral.get_id` meet the two axioms on
boundary + fuzz. For `c_number_literal_id` it runs the real C-domain
`_parse_literal` on an 888-token (literal × trailing-run) matrix + 2000 fuzz
tokens, splitting each token into `(lit, trail)` via the real literal-match
pipeline, and asserts the produced `ASTNumberLiteral.data` equals the model's
text prediction AND that the pre-patch maximal-run behaviour provably diverges on
every non-recognised run (1902 such cases). Exit 0 iff sound.
