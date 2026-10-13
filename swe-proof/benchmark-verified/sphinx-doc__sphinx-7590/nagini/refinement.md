# refinement.md — sphinx-doc__sphinx-7590

The operation-by-operation correspondence between `model.py`'s implementation
(the `number_literal_id` and `c_number_literal_id` impl regions, the deep
`udl_id_seq` / `number_id_seq` models, and the live `ident_mangle` axiom) and
`patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses the axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The new mangling — `ASTUserDefinedLiteral.get_id` (`sphinx/domains/cpp.py`)

Gold hunk (new class):
```python
def get_id(self, version: int) -> str:
    # mangle as if it was a function call: ident(literal)
    return 'clL_Zli{}E{}E'.format(self.ident.get_id(version), self.literal.get_id(version))
```

| # | model.py impl op (`number_literal_id`, UDL branch / `udl_id_seq`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `lit: List[int]`, `ident: List[int]` | the `str` `self.literal.data` and `self.ident.identifier` | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | literal `[99,108,76,95,90,108,105]` prefix | the format string prefix `'clL_Zli'` | I | the seven ASCII code points of `clL_Zli`. |
| A3 | `ident_id` (supplied param, tied by precondition to `ident_mangle(ToSeq(ident))` when `len(ident)>0`) | `self.ident.get_id(version)` | A-consumed | `ident.get_id` is the UNCHANGED identifier id-generator; on the axiom's RESTRICTED domain (nonempty, identifier `!= std`) it is `str(len)+ident`. The real generator special-cases `std`→`St` (and `~…`→`D0`, `@…`→`Ut…`), where the length-prefixed claim fails; `~`/`@` cannot begin a UDL identifier, but `std` is a reachable UDL suffix (`5std`), so the axiom is contracted to exclude `std` by precondition (the F2P never hits it). The proof consumes the axiom's `Ensures` on this domain; G-AX checks it against the real `ASTIdentifier.get_id` and asserts the excluded branches deviate (mapping.md §3.1). |
| A4 | literal `[69]` between the two parts, and the trailing `[69]` | the two `E` framing characters in `'…E{}E'` | I | ASCII `E` = 69. |
| A5 | `[76] + lit + [69]` (the numeric-literal id, via `number_id_seq`) | `self.literal.get_id(version)` = `"L%sE" % self.data` | A-reference | the numeric-literal mangling is modelled DEEPLY (`number_id_seq(lit) = L + lit + E`); G-AX asserts it == the real `ASTNumberLiteral.get_id` (mapping.md §3.2). The op is the trivial `L…E` framing, identical concrete bytes. |
| A6 | result `= prefix + ident_id + [69,76] + lit + [69,69]` | `'clL_Zli{}E{}E'.format(ident_id, number_id)` | R + I | Python string `.format` interpolation ↔ list `+`; the `{}E{}E` skeleton expands to `ident_id + 'E' + ('L'+lit+'E') + 'E'`, exactly the concatenation. |

`udl_id_seq` (the deep model the postcondition pins) is therefore the real
`ASTUserDefinedLiteral.get_id` under R, with the two sub-`get_id` callees being
the A-consumed `ident_mangle` (A3) and the A-reference `number_id_seq` (A5).

## B. The parse decision — `_parse_literal` (`sphinx/domains/cpp.py:4640`)

Gold hunk (number-literal branch):
```python
-        for regex in [float_literal_re, binary_literal_re, hex_literal_re,
+        pos = self.pos
+        if self.match(float_literal_re):
+            hasSuffix = self.match(float_literal_suffix_re)
+            floatLit = ASTNumberLiteral(self.definition[pos:self.pos])
+            if hasSuffix:  return floatLit
+            else:          return _udl(floatLit)
+        for regex in [binary_literal_re, hex_literal_re,
                       integer_literal_re, octal_literal_re]:
-            pos = self.pos
             if self.match(regex):
-                while self.current_char in 'uUlLfF':
-                    self.pos += 1
-                return ASTNumberLiteral(self.definition[pos:self.pos])
+                hasSuffix = self.match(integers_literal_suffix_re)
+                intLit = ASTNumberLiteral(self.definition[pos:self.pos])
+                if hasSuffix:  return intLit
+                else:          return _udl(intLit)
```
where `_udl(lit)` matches `udl_identifier_re` and, if present, returns
`ASTUserDefinedLiteral(lit, ASTIdentifier(matched_text))`, else returns `lit`.

| # | model.py impl op (`number_literal_id`, the branch) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | the boolean parameter `suffixed` | the result of `self.match(<…>_literal_suffix_re)` (`hasSuffix`) | R | a regex-match boolean ↔ a `bool` (mapping.md §2); whether a recognised numeric suffix follows the matched numeric literal. |
| B2 | the parameter `ident` (empty ⇔ no trailing UDL identifier) | `self.match(udl_identifier_re)` + `self.matched_text` inside `_udl` | R | a regex-captured identifier ↔ a `List[int]`; empty list ⇔ the match failed (no UDL identifier). |
| B3 | `if not suffixed and len(ident) > 0: return udl mangling` | `if hasSuffix: return numberLit else: return _udl(numberLit)` and `_udl` builds an `ASTUserDefinedLiteral` iff `udl_identifier_re` matched | I | same control structure: an unsuffixed numeric literal with a trailing identifier becomes a UDL; otherwise it stays an ordinary numeric literal. |
| B4 | `else: return [76] + lit + [69]` (ordinary number id) | `return floatLit/intLit` (an `ASTNumberLiteral`) whose `get_id` is `L…E` | A-reference + R | the ordinary-literal id is `number_id_seq` (A5/§3.2), validated == real `ASTNumberLiteral.get_id` by G-AX. |

The discriminating content of the change is B3: the pre-patch code (the
`while self.current_char in 'uUlLfF'` loop) had **no UDL branch at all** — it
always returned an `ASTNumberLiteral`, leaving a trailing UDL identifier
unconsumed so the surrounding declaration failed to parse. `model_prepatch.py`
reproduces that (it always returns `[76]+lit+[69]`, the ordinary number id) and
**fails** the postcondition
`Implies(not suffixed and len(ident) > 0, ToSeq(Result()) == udl_id_seq(...))`,
which is exactly the spec sensing the change (G-DIFF). The F2P
`tests/test_domain_cpp.py::test_expressions` exercises this on the issue token
`6.62607015e-34q_J` (and the int/float/char/string × suffix UDL matrix).

## B'. The simpler-dialect parse decision — `_parse_literal` (`sphinx/domains/c.py`)

The gold patch makes a PARALLEL rewrite to the simpler dialect's
`DefinitionParser._parse_literal` (`sphinx/domains/c.py`), which has **no
user-defined literals**. The change there is exactly the suffix-handling: the
pre-patch maximal-run loop is replaced by a single recognised-suffix regex
match.

Gold hunk (C-domain):
```python
-        for regex in [float_literal_re, binary_literal_re, hex_literal_re,
+        pos = self.pos
+        if self.match(float_literal_re):
+            self.match(float_literal_suffix_re)
+            return ASTNumberLiteral(self.definition[pos:self.pos])
+        for regex in [binary_literal_re, hex_literal_re,
                       integer_literal_re, octal_literal_re]:
-            pos = self.pos
             if self.match(regex):
-                while self.current_char in 'uUlLfF':
-                    self.pos += 1
+                self.match(integers_literal_suffix_re)
                 return ASTNumberLiteral(self.definition[pos:self.pos])
```

`c_number_literal_id(lit, trail, valid)` models the produced numeric literal's
text/id, where `lit` is the matched numeric literal, `trail` is the maximal run
of suffix-alphabet characters (`uUlLfF`) following it (what the pre-patch loop
scanned), and `valid` is whether that run is a recognised numeric suffix (the
post-patch `*_literal_suffix_re` match).

| # | model.py impl op (`c_number_literal_id`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B'1 | `lit: List[int]` (matched numeric literal) | `self.definition[pos:self.pos]` before any suffix match, i.e. the literal-regex match | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| B'2 | `trail: List[int]` (maximal `uUlLfF` run after `lit`) | the characters the pre-patch loop scanned / the suffix-regex sees | R | a code-point run ↔ a `List[int]`. |
| B'3 | `valid: bool` | the truth of `self.match(float_literal_suffix_re)` / `self.match(integers_literal_suffix_re)` | R | a regex-match boolean ↔ a `bool` (mapping.md §2). A `\b`-terminated suffix regex matches the WHOLE maximal run or nothing (never a strict prefix), so `valid` ⇔ the matched suffix == the whole run; G-AX checks this against the real parser. |
| B'4 | `if valid: return [76] + lit + trail + [69]` | the suffix-regex `self.match` advances `self.pos` past the suffix, so `self.definition[pos:self.pos]` = `lit + suffix`; the literal's id is `number_id_seq` of that text | A-reference + I | the recognised suffix is folded into the literal text; the id is the trivial `L…E` framing of `lit+trail`, the shared `ASTNumberLiteral.get_id` (A5/§3.2). |
| B'5 | `else: return [76] + lit + [69]` | no suffix match ⇒ `self.pos` unchanged, `self.definition[pos:self.pos]` = `lit`; id is `number_id_seq(lit)` | A-reference + I | a non-recognised trailing run is left unconsumed; the literal text is just `lit`. |

The discriminating content of the C-domain change is B'5: the pre-patch
maximal-run loop (`while self.current_char in 'uUlLfF': self.pos += 1`) ALWAYS
folds the whole `trail` into the literal text, so for a non-recognised run (e.g.
a float `5.0` followed by `u`, or an integer `5` followed by `f`) it produced
`L5.0uE`/`L5fE` whereas the gold produces `L5.0E`/`L5E`. `model_prepatch.py`
reproduces that (its `c_number_literal_id` always returns `number_id_seq(lit +
trail)`) and **fails** the postcondition
`Implies(not valid, ToSeq(Result()) == number_id_seq(ToSeq(lit)))` — exactly the
spec sensing the change (G-DIFF). G-AX validates `c_number_literal_id` against the
real C-domain `DefinitionParser._parse_literal` on an 888-token (literal × trail)
matrix + 2000 fuzz, and asserts the pre-patch maximal-run behaviour provably
diverges on every non-recognised run (1902 such cases).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The three operations that genuinely *changed* —
the new user-defined-literal mangling (`get_id`), the C++ suffix-vs-identifier
parse decision, and the simpler-dialect suffix-vs-not parse decision — are
modelled **deeply** (the spelled-out concatenation `udl_id_seq` consumed in
`number_literal_id`, an **A-reference**; the branch B3, **I**; and the branch
B'4/B'5 in `c_number_literal_id`, **I** over the **A-reference** `number_id_seq`),
not hidden behind an axiom about a function under change. The
only consumed axiom, `ident_mangle` (**A-consumed**, A3), covers the UNCHANGED
identifier id-generator `ASTIdentifier.get_id`, whose length-prefixed form is
not worth re-deriving in Nagini (an int→decimal fold) and is checked by G-AX.
That axiom is contracted over a RESTRICTED domain (nonempty identifier, `!= std`)
because the real generator special-cases `std`→`St` (the length-prefixed claim
would over-claim there); the restriction is threaded through `udl_id_seq` and
`number_literal_id`'s precondition, and G-AX both validates the axiom on the
domain and asserts the excluded branches (`std`/`~`/`@`) genuinely deviate, so
the exclusion is load-bearing and the proof stays sound. The F2P UDL suffixes
(`_udl`/`q_J`/`uludl`/`fudl`) are all in-domain, so no tested behaviour is lost.
The other unchanged sub-callee `ASTNumberLiteral.get_id` is the trivial
`L…E` framing, modelled deeply (`number_id_seq`, **A-reference**, A5/B4) and
likewise checked by G-AX.

## D. The non-discriminating gold hunks (carried verbatim by patch.diff)

`patch.diff` also adds the suffix/UDL regexes and the `'udl'` description mode
(`sphinx/util/cfamily.py`, `sphinx/domains/cpp.py`), the `'udl'` branch of
`ASTIdentifier.describe_signature`, two TODO comments, and inlines
`key = symbol.get_lookup_key()`. These do not change the v2/v3/v4 id or the
`str()` of a parsed literal beyond what `number_literal_id` / `udl_id_seq` /
`c_number_literal_id` pin; they are part of the same fix and are present in the
verbatim gold so G-RESOLVE passes. (The parallel C-domain `_parse_literal`
rewrite is now MODELED — §B' — not carried as a non-discriminating hunk.)

## E. verify(model) ⇒ resolved

`number_literal_id` verifies only if its output, for an unsuffixed numeric
literal followed by an identifier, equals the exact UDL mangling
`clL_Zli<ident-id>E<L lit E>E` (A1–A6, B3) and, otherwise, the ordinary number
id `L lit E` (B4). `c_number_literal_id` verifies only if its output, for a
numeric literal with a recognised suffix run, equals `L<lit+trail>E` and,
otherwise, `L<lit>E` (B'4/B'5). By R (str ↔ List[int]; regex-match ↔ bool;
`.format` ↔ list `+`) the verified functions equal the real C++ `_parse_literal`
number path + `ASTUserDefinedLiteral.get_id` and the real C-domain
`_parse_literal` number path on the tested inputs; by G-AX the deep models
`udl_id_seq`/`number_id_seq` equal the real `ASTUserDefinedLiteral.get_id` /
`ASTNumberLiteral.get_id` (A-reference), the real `ASTIdentifier.get_id` meets
the `ident_mangle` axiom it stands in for (A-consumed), and `c_number_literal_id`
equals the real C-domain `_parse_literal` literal text/id (A-reference, with the
pre-patch maximal-run behaviour proven to diverge). Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
audited callees — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
