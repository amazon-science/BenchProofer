# refinement.md — django__django-16145

The operation-by-operation correspondence between `model.py`'s implementation
(the `display_address` impl region and the deep `shown_address` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` — checked
with `git apply --check` — and is the real correctness oracle, G-RESOLVE).

## A. The address-derivation site — `inner_run` (`django/core/management/commands/runserver.py`)

Gold hunk (the inserted block + the dict-entry rewrite):
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

| # | model.py impl op (`display_address`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `addr: List[int]`, `raw_ipv6: bool` | `self.addr` (a `str`) and `self._raw_ipv6` (a `bool`), set in `handle` | R | `str` ↔ `List[int]` code points; `bool` identity (mapping.md §1-2). |
| A2 | `if raw_ipv6:` branch builds `PSeq(91) + addr + PSeq(93)` via the prefix-copy loop, then appends `]` | `if self._raw_ipv6: addr = f"[{self.addr}]"` | R + I | identical branch + bracket-wrap; `f"[{...}]"` ↔ `"[" + addr + "]"` on the code-point carrier (`[`=91, `]`=93). The verified loop copies `addr` element-for-element, so the result is exactly `[` + addr + `]`. |
| A3 | `elif ToSeq(addr) == wildcard_short():` returns `wildcard_dotted()` (`[48,46,48,46,48,46,48]`) | `elif self.addr == "0": addr = "0.0.0.0"` | R + I | identical branch; `self.addr == "0"` ↔ `ToSeq(addr) == wildcard_short()` (`"0"` ↔ `PSeq(48)`); `"0.0.0.0"` ↔ `wildcard_dotted()` character-for-character. **This is the operation the gold patch ADDS** (the pre-patch had no such branch). |
| A4 | `else:` branch copies `addr` verbatim via the prefix-copy loop | `else: addr = self.addr` | R + I | identity branch; the loop reproduces `addr` element-for-element. |
| A5 | `return result` | the local `addr` value is substituted into `%(addr)s` of the announcement format string and written to stdout | R | the model returns the same character content the patch binds to `"addr"`; the F2P test observes exactly this value rendered into the "Starting development server at http://%(addr)s:%(port)s/" line. The `%`-formatting and `stdout.write` do not alter the address content (mapping.md §1). |

The discriminating content of the change — the new `self.addr == "0"
→ "0.0.0.0"` expansion — lives in step A3 (`shown_address`'s middle branch,
`entity`-style). `model_prepatch.py` reproduces the pre-patch behaviour (only the
bracket-IPv6 case and the verbatim case; the wildcard `"0"` falls through the
verbatim path) and **fails** the postcondition
`ToSeq(Result()) == shown_address(ToSeq(addr), raw_ipv6)` on the input
`addr = "0"`, `raw_ipv6 = False` (the model copies `"0"` but the spec requires
`"0.0.0.0"`). This is exactly the spec sensing the change (G-DIFF). The F2P
`test_zero_ip_addr` (`addrport="0:8000"` → `self.addr == "0"`, `_raw_ipv6 ==
False`) observes precisely this case.

## B. No kind-3 (unexpressible-changed-op) steps; no axioms

Every step above is R or I. The one operation that genuinely *changed* — adding
the `"0" → "0.0.0.0"` wildcard expansion to the address-derivation — is a
primitive string comparison + literal, modeled **deeply** as the middle branch
of the `@Pure shown_address` over `PSeq[int]` and reproduced by the verified
`display_address` impl. There is **no consumed axiom** (no opaque library callee
is approximated) and **no A-reference deep model standing in for a library
callee**: the whole derivation is primitive Python string formatting,
comparison, and literals (`f"[{...}]"`, `== "0"`, `"0.0.0.0"`), each modeled
directly on the code-point carrier.

`axiom_check.py` therefore checks the only nontrivial soundness obligation that
remains — the R-refinement of mapping.md §2: that the modeled `shown_address`
over code points equals Python's native evaluation of the gold expression for 13
boundary addresses × 2 flags + 40 000 fuzz addresses (0 violations), and that
the pre-patch expression differs from the gold exactly on the wildcard `"0"`,
non-IPv6 input. It consumes no repo code (stdlib-only).

## C. verify(model) ⇒ resolved

`display_address` verifies only if its result equals
`shown_address(ToSeq(addr), raw_ipv6)` — i.e. the bracket-wrapped address when
`raw_ipv6`, the expanded `"0.0.0.0"` when the bound address is `"0"`, and the
bound address otherwise (A2-A4), in this priority order. By R (`str ↔
List[int]`, `bool` identity, `f"[{…}]"`/`%`-format/`stdout.write` content-
preserving) the verified result equals the local `addr` the gold patch binds to
`"addr"` and renders into the announcement line, for every `(self.addr,
self._raw_ipv6)` the command produces. In particular for `addrport="0:8000"`
(`self.addr == "0"`, `_raw_ipv6 == False`) the verified model and the gold patch
both yield `"0.0.0.0"`, while the pre-patch yields `"0"` and fails the F2P test.

Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to the string R-refinement — and the gold patch resolves (G-RESOLVE).
The only trust point is refinement fidelity (this document, G-EQ); there are no
axioms (so G-AX reduces to the exhaustive-by-boundary + fuzz string equality of
`axiom_check.py`).
