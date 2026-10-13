# refinement.md — pytest-dev__pytest-7205

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`renderParameterDisplay` `do` block, plus the deep `quotedRepr`/`bracket` models)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The display site — `_show_fixture_action` (`src/_pytest/setuponly.py:69`)

Gold hunk:
```
- tw.write("[{}]".format(fixturedef.cached_param))          # implicit str(cached_param)
+ tw.write("[{}]".format(saferepr(fixturedef.cached_param, maxsize=42)))
```
(plus the import `from _pytest._io.saferepr import saferepr` at `setuponly.py:2`.)

| # | Solution.lean impl op (`renderParameterDisplay`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `param : ParamValue` (`textVal s` / `bytesVal s`) | `fixturedef.cached_param` (a text value or a byte-string value) | R | `str` ↔ `textVal` over `List Char`, printable-ASCII `bytes` ↔ `bytesVal` over `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)` / byte ↔ `Char.ofNat b`. |
| A2 | `let r := quotedRepr param` — text surrounded by apostrophes; bytes additionally carrying the `b` prefix | `saferepr(fixturedef.cached_param, maxsize=42)` | A-reference + I | the changed display op is modeled **deeply**: `quotedRepr` (pure region) spells out the size-limited safe representation on the `simpleParam` domain, per payload shape. No consumed `saferepr` axiom. The construction ops (`'\'' :: (s ++ ['\''])`, `'b' :: '\'' :: (s ++ ['\''])`) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `saferepr(·, maxsize=42)` on `simpleParam` is the **A-reference** G-AX validates on both shapes. mapping.md §3.1. |
| A3 | `return bracket r` — wrap `r` in `[` … `]` | `"[{}]".format(...)` | I | the square-bracket wrapping is unchanged between pre- and post-patch; `bracket` (`'[' :: t ++ [']']`) is the literal `"[{}]".format(t)` (mapping.md §2). G-CONF transliterates it directly. |

Precondition `require simpleParam param` (mapping.md §3.1) names exactly the
domain on which the deep model `quotedRepr` is the *exact* value of the real
`saferepr(·, maxsize=42)`: text ≤ 40 code points or bytes ≤ 39 bytes, printable
ASCII, no apostrophe or backslash. Every F2P parameter/id value — including the
BytesWarning test's `b'Hello World'` — lies in this domain.

Discriminating content of the change — the parameter value is now displayed
through the **safe representation** (apostrophe-wrapped, `b`-prefixed on a
byte-string) rather than through its plain textual form — lives in
`quotedRepr` (model, with the apostrophes/prefix) ⇔
`saferepr(param, maxsize=42)` (real, which reprs the value). The pre-patch took
the **plain textual form** (`"[{}]".format` ⇒ implicit `str(param)`, no
apostrophes, and a `-bb` `BytesWarning` on a bytes value);
`Solution_prepatch.lean` reproduces that (`let r := <the payload's bare
content>`) and **fails** every `ensures` clause on the missing apostrophes /
missing `b` prefix (G-DIFF).

## B. The BytesWarning observation (`test_show_fixture_action_with_bytes`)

The same single edit also fixes the `-bb` BytesWarning, and this observation is
now INSIDE the modeled domain: a printable-ASCII `bytes` value is
`ParamValue.bytesVal`, and the spec pins its rendered token to
`[b'…']` — the output only `saferepr`/`repr` produces. The pre-patch
`"[{}]".format(cached_param)` takes an implicit `str()` of the value, which on a
`bytes` parameter raises `BytesWarning` under `-bb` (no token at all — the
F2P test observes `result.ret == 0` post-patch vs an error pre-patch); the
post-patch `saferepr` calls `repr` (never `str`) so no warning fires. This is
the SAME op as site A (one replaced expression); `Solution_prepatch.lean`'s
bytes leg (bare content, no `b'…'`) fails the `bytesVal` ensures clause, and
axiom_check.py witnesses the real `-bb` behaviour on both sides (mapping.md
§3.1). The F2P `fnmatch_lines` *content* assertions all live within the
`textVal` leg of `simpleParam`.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
parameter value's rendering — is modeled **deeply** (the spelled-out
`quotedRepr` on both payload shapes, step A2, an A-reference + I), not hidden
behind an axiom about the function under change: there is no consumed
`saferepr` axiom. There are no consumed axioms at all (mapping.md §3.2).

## D. verify(Solution) ⇒ resolved

`renderParameterDisplay` verifies only if its output equals the bracketed safe
representation of the parameter on BOTH payload shapes (A2 + A3): the per-shape
`ensures` clauses force `[ '…' ]` on a text value and `[ b'…' ]` on a
byte-string, not the bare `[ … ]` (and not a text-style token on a bytes
value). By R (`str`/`bytes` ↔ `ParamValue`, the `"[{}]".format`/`str()`
identities) the verified renderer equals
`"[{}]".format(saferepr(param, maxsize=42))` on the tested `simpleParam`
inputs; by G-AX the deep model `quotedRepr` equals the real
`saferepr(·, maxsize=42)` over the whole `simpleParam` domain on both shapes
(A-reference), and no BytesWarning fires where the pre-patch's `str()` did; by
G-CONF the I transliteration of the token construction agrees with
`patch.diff`'s behaviour on ≥10⁵ inputs across both shapes. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited callee — and the gold patch resolves (G-RESOLVE).
The single trust point is the A-reference soundness (G-AX) plus refinement
fidelity (this doc, G-EQ + G-CONF).
