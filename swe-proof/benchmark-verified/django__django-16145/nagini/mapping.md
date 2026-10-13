# mapping.md — django__django-16145

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 93d4c9ea1de24eb391cb2b3561b6703fd46374df`, states the type
abstraction, and records callee provenance.

Repo file under change:
`django/core/management/commands/runserver.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `display_address(addr, raw_ipv6)` | the value bound to the `"addr"` key of the format-context dict in `Command.inner_run(self, *args, **options)` — `django/core/management/commands/runserver.py:150` (the expression `"[%s]" % self.addr if self._raw_ipv6 else self.addr`, replaced by the new local `addr` computed at the inserted block, post-patch lines 132-138) | the modeled changed behaviour: the address string shown in the "Starting development server at …" announcement |

The modeled function isolates exactly the address-derivation logic the patch
introduces. The two inputs it reads are instance attributes set earlier, in
`Command.handle` (same file):

| model.py parameter | repo expression (file:line @ base_commit) |
|---|---|
| `addr` (the bound address) | `self.addr` — assigned in `handle` at `runserver.py:89` (`""`), `98` (regex group), `103` (IPv6 strip), `109` (default). For `addrport="0:8000"` the `naiveip_re` FQDN group matches `"0"`, so `self.addr == "0"`. |
| `raw_ipv6` (bracketed-IPv6 flag) | `self._raw_ipv6` — `runserver.py:87` (`False`), `105` (`True` when the matched address was a `[...]` IPv6 literal), `110` (mirrors `use_ipv6` for the default). |

The announcement string is emitted by `self.stdout.write(... % { ... "addr":
... })` at `runserver.py:140-154`; the F2P test
`test_zero_ip_addr (admin_scripts.tests.ManageRunserver)` asserts the rendered
line `"Starting development server at http://0.0.0.0:8000/"` for
`addrport="0:8000"`, i.e. it observes precisely the value this function returns
substituted into `%(addr)s`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.addr` (a `str`), and the produced display `str` | `List[int]` of Unicode code points | `s[k]` ↔ `addr[k] == ord(s[k])`; `len(s)` ↔ `len(addr)`; `str` concatenation ↔ list `+`; empty `str` ↔ `[]`. Specification carried over `PSeq[int]` via `ToSeq`. |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `+`/`take`/`len`/`==` mirror `str` `+`/slice/`len`/`==`. |
| `self._raw_ipv6` (a `bool`) | `raw_ipv6: bool` parameter | identity on the Python `bool`. |
| the literal `"0"` (the wildcard short form) | `PSeq(48)` (`wildcard_short()`) — code point of `'0'` is U+0030 = 48 | the `self.addr == "0"` comparison ↔ `ToSeq(addr) == wildcard_short()`. |
| the literal `"0.0.0.0"` | `PSeq(48,46,48,46,48,46,48)` (`wildcard_dotted()`) — `'.'` is U+002E = 46 | character-for-character. |
| the f-string `f"[{self.addr}]"` / `"[%s]" % self.addr` | `PSeq(91) + addr + PSeq(93)` — `'['` is U+005B = 91, `']'` is U+005D = 93 | bracket-wrap on the code-point carrier. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout. No float, collection, or object modeling is needed.

## 3. Callee provenance

**No consumed axioms (kind A-consumed) and no deep-model references that stand
in for a library callee (A-reference).** The modeled expression calls no
library/utility function: it is `f"[{...}]"` / `"%s"` string formatting,
a `==` literal comparison, and a string literal — all primitive Python string
operations, modeled directly on the `List[int]` carrier. The two inputs
(`self.addr`, `self._raw_ipv6`) are plain attribute reads of values fixed
earlier in `handle`, modeled as the identity on their carriers (§2).

Consequently `axiom_check.py` has no axiom `Ensures` to fuzz against a real
callee. It instead validates the R-refinement of §2: that the modeled
`shown_address` over code points equals Python's own evaluation of the gold
`patch.diff` expression
(`f"[{addr}]"` if raw_ipv6 / `"0.0.0.0"` if `addr == "0"` / `addr`) over 13
boundary addresses × 2 flags + 40 000 randomized fuzz addresses (0 violations),
and confirms the pre-patch expression (no wildcard expansion) differs from the
gold exactly on the wildcard `"0"`, non-IPv6 input — the discriminating case the
F2P test exercises.
