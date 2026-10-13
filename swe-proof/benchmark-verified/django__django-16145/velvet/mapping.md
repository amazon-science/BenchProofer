# mapping.md — django__django-16145

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 93d4c9ea1de24eb391cb2b3561b6703fd46374df`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance and flag dependencies.

Repo file under change: `django/core/management/commands/runserver.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `formatHost (bracketed : Bool) (host : List Char)` | the display-address computation in `Command.inner_run` — `django/core/management/commands/runserver.py:122` (banner-building block; post-patch the `addr` local at lines 132-137, consumed at line 154) | the modeled changed computation: the host string printed in the startup banner |
| `displayAddress (bracketed host)` | the post-patch `addr` ladder (`runserver.py:132-137`) | pure spec: the display form of the host |
| `bracketed : Bool` | `self._raw_ipv6` (`runserver.py:87,105,110`; read at the display site) | read-only flag: host was parsed as a bracketed IPv6 literal |
| `host : List Char` | `self.addr` (`runserver.py:89,98,103,109`; read at the display site) | read-only host string, already stripped of any IPv6 brackets |

The pre-patch repo expression the change replaces (refinement audit only, not in
the consumer spec view): the inline conditional
`"[%s]" % self.addr if self._raw_ipv6 else self.addr` (`runserver.py:150`,
pre-patch), which has no "0" → "0.0.0.0" expansion.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.addr` (Python `str`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]`; the literal `"0"` ↔ `"0".toList = ['0']`; `"0.0.0.0"` ↔ `"0.0.0.0".toList` |
| `self._raw_ipv6` (Python `bool`) | `Bool` | `True` ↔ `true`, `False` ↔ `false` |
| `"[%s]" % self.addr` (bracket wrap) | `['['] ++ host ++ [']']` | percent-format with a single `%s` of `self.addr` is literal prefix `[` + the host content + literal suffix `]` |
| `self.addr == "0"` (literal equality) | `host = "0".toList` | Python `str.__eq__` against the one-character literal ↔ Lean `List Char` equality against `['0']` |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the operation is a string value computation (equality,
literal substitution, concatenation).

## 3. Callee provenance — none (no kind-A)

`formatHost`/`displayAddress` model a self-contained computation built only from
language primitives — a boolean test on `self._raw_ipv6`, a string-equality test
`self.addr == "0"`, percent-format bracket wrapping, and the string literals
`"0"` / `"0.0.0.0"`. The block calls **no** repository or library function, so
there is **no callee to axiomatize and no deep-model reference**: the `axioms`
region is empty and there is no `axiom_check.py` (G-AX = skip).

The surrounding `inner_run` machinery (`self.get_version()`, `settings`,
`self.stdout.write`, the server `run(...)`) is **outside** the modeled region —
the patch does not touch it and `formatHost` does not depend on it. It is not a
callee of the modeled computation.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16145`** so the
consumer-side verdict (§11.3) is reproducible. The shadow it builds
transliterates `displayAddress` (pure R/I ops) to Python; the oracle is the
patched `addr` ladder transliterated verbatim from `patch.diff`
(`runserver.py:132-137`).

### Why the oracle is the patched source ladder, not a live `inner_run`

The display computation lives inside
`Command.inner_run(self, *args, **options)`. Reaching it for real binds a socket
and starts a blocking development server (the `run(...)` call a few lines later
never returns), and requires a fully-initialised command with `stdout`,
`settings`, and a parsed `addrport`. The F2P test
`ManageRunserver.test_zero_ip_addr` itself mocks `runserver.run` and
`check_migrations` precisely so the only observable is the banner string. So,
per the worker prompt, the G-CONF **oracle** is the patched ladder transliterated
verbatim:

```python
if self._raw_ipv6:
    addr = f"[{self.addr}]"
elif self.addr == "0":
    addr = "0.0.0.0"
else:
    addr = self.addr
```

The **shadow** is `displayAddress` transliterated. G-CONF differential-tests
shadow vs oracle over the boundary inputs (both `bracketed` values × the "0"
shorthand, bracketed hosts, ordinary hosts) plus ≥10⁵ seeded fuzz `(bool, str)`
pairs. Exit 0 iff zero disagreements.
