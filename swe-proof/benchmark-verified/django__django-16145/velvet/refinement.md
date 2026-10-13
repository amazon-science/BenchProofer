# refinement.md — django__django-16145

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `formatHost` `do` block and the pure `displayAddress` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** / **A-reference** (axiomatized callee — none in
this bundle), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The display-address site — `Command.inner_run`

Gold hunk (`django/core/management/commands/runserver.py`):
```
+        if self._raw_ipv6:
+            addr = f"[{self.addr}]"
+        elif self.addr == "0":
+            addr = "0.0.0.0"
+        else:
+            addr = self.addr
...
-                "addr": "[%s]" % self.addr if self._raw_ipv6 else self.addr,
+                "addr": addr,
```

The fix introduces an `addr` local computed by a three-way ladder and feeds it
into the banner format dict in place of the old two-way inline conditional. The
modeled computation is exactly that ladder.

| # | Solution.lean impl op (`formatHost`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `bracketed : Bool` | `self._raw_ipv6` | R | Python `bool` ↔ Lean `Bool` (mapping.md §2). Read-only at the display site; not mutated (directive 5: not `mut`). |
| A2 | parameter `host : List Char` | `self.addr` | R | Python `str` ↔ `List Char` (mapping.md §2). Read-only at the display site. |
| A3 | `if bracketed then return ['['] ++ host ++ [']']` | `if self._raw_ipv6: addr = f"[{self.addr}]"` | R + I | the bracket-wrap branch: `f"[{...}]"` ↔ `['['] ++ host ++ [']']` (mapping.md §2). The control-flow branch is **I** (concrete `if`); the string-build is **R** (concat under the `str ↔ List Char` bijection). |
| A4 | `else if host = "0".toList then return "0.0.0.0".toList` | `elif self.addr == "0": addr = "0.0.0.0"` | R + I | the new behaviour of interest: the bare `"0"` shorthand expands to the dotted-quad `"0.0.0.0"`. Literal-equality test ↔ `host = ['0']`; literal result ↔ `"0.0.0.0".toList` (mapping.md §2). |
| A5 | `else return host` | `else: addr = self.addr` | R + I | any other non-bracketed host is shown verbatim — identity on the host content. |
| A6 | `out` returned (`List Char`) | `addr` placed in the banner dict, rendered via `%(addr)s` into the "Starting development server at …" line | R | the format dict substitution and `stdout.write` are content-preserving on `addr` (mapping.md §2); the F2P test asserts the rendered substring `http://0.0.0.0:8000/`, i.e. observes `addr` verbatim. |

Discriminating content of the change — a non-bracketed host equal to `"0"` →
`"0.0.0.0"` (rather than the verbatim `"0"`) — lives in
`displayAddress … = "0.0.0.0".toList` (model, step A4) ⇔ the `elif self.addr ==
"0": addr = "0.0.0.0"` branch (real). The pre-patch expression had no such
branch (host shown verbatim); `Solution_prepatch.lean` reproduces that and
**fails** the `(bracketed = false ∧ host = "0".toList) → out = "0.0.0.0".toList`
clause (and the exact-equality clause) — G-DIFF.

## B. No kind-A (axiomatized callee) steps

The modeled computation calls no repository or library function. It is built
only from language primitives (a boolean test, a string-equality test, percent /
f-string bracket wrapping, two string literals). There is therefore no consumed
axiom and no deep-model reference; the `axioms` region is empty and there is no
`axiom_check.py` (G-AX = skip). The surrounding `inner_run` machinery
(`get_version`, `settings`, `stdout.write`, the server `run`) is outside the
modeled region and untouched by the patch.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the
introduction of the `"0"` → `"0.0.0.0"` expansion in the display ladder — is
modeled **directly** (step A4, an R + I op spelled out in `displayAddress`), not
hidden behind any axiom. Nothing is left inexpressible.

## D. verify(Solution) ⇒ resolved

`formatHost` verifies only if its output equals the exact three-way display
ladder with the `"0"` → `"0.0.0.0"` expansion (A4) and the bracket / passthrough
branches (A3, A5). By R (`str ↔ List Char`, `bool ↔ Bool`, `f"[{…}]"` ↔ bracket
concat) the verified computation equals the patched `addr` ladder on every
`(self._raw_ipv6, self.addr)` pair; by A6 that `addr` is what the banner prints
verbatim, so the F2P test's asserted substring `http://0.0.0.0:8000/` follows
for input `addrport="0:8000"`. By G-CONF the R/I transliteration of
`displayAddress` agrees with `patch.diff`'s ladder on ≥10⁵ inputs. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). There are no axiom
trust points (no G-AX); the single trust point is refinement fidelity (this doc,
G-EQ + G-CONF).
