# mapping.md — django__django-16145

## Symbol binding (file:line @ base_commit 93d4c9ea1de24eb391cb2b3561b6703fd46374df)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_displayAddr` / `problem_spec_displayAddr` / `correct_displayAddr` | the display-address local computed inside `Command.inner_run` and substituted for the `%(addr)s` field of the start-up banner | `django/core/management/commands/runserver.py:122-154` |

The modeled function is the pure sub-computation that turns the resolved bind
host (`self.addr`) and the raw-IPv6 flag (`self._raw_ipv6`) into the address
string shown in the banner line `Starting development server at
%(protocol)s://%(addr)s:%(port)s/`. It is the only behavior the patch changes,
and the only behavior the FAIL_TO_PASS test
(`test_zero_ip_addr (admin_scripts.tests.ManageRunserver)`) observes: with
`addrport="0:8000"` the banner must read
`http://0.0.0.0:8000/` rather than `http://0:8000/`.

### What the function does (base_commit)

At base_commit the displayed address is computed inline in the banner's
substitution dict:

```python
"addr": "[%s]" % self.addr if self._raw_ipv6 else self.addr,
```

i.e. a raw IPv6 literal is wrapped in square brackets, and every other host is
shown verbatim — including the shorthand host `"0"`, which is therefore printed
as `http://0:.../` (a host a browser such as Chrome will not follow).

The post-fix code lifts this into a local `addr` with an extra branch:

```python
if self._raw_ipv6:
    addr = f"[{self.addr}]"
elif self.addr == "0":
    addr = "0.0.0.0"
else:
    addr = self.addr
...
"addr": addr,
```

so the shorthand host `"0"` is now presented in its canonical dotted form
`"0.0.0.0"`. All other inputs map to the same display string as before.

### Input ↔ Python expression bijection

| Lean argument | Python source (`inner_run`) | notes |
|---|---|---|
| `rawIpv6 : Bool` | `self._raw_ipv6` | Bool; set in `handle()` — `True` exactly when the address parsed as a bracketed IPv6 literal (`[...]`) or when an empty/`--ipv6` default address was used |
| `addr : String` | `self.addr` | the resolved bind host (after `handle()` strips IPv6 brackets and applies defaults) |
| `result : String` | the value bound to the local `addr` / substituted for `%(addr)s` | the display host placed into the banner URL |

### Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `self.addr` / `addr` (a host `str`, value-level) | `String` | identity on the character sequence |
| `self._raw_ipv6` (`bool`) | `Bool` | `True`/`False` ↔ `true`/`false` |
| string equality `self.addr == "0"` | `addr = "0"` (`String` `DecidableEq`) | identity |
| `f"[{self.addr}]"` / `"[%s]" % self.addr` | `"[" ++ addr ++ "]"` | identity (bracket-wrap a value-level string) |
| literal `"0.0.0.0"` | `"0.0.0.0"` | identity |

The computation is value-level string formatting (whole-string equality and
concatenation), so `String` — not `List Char` — is the faithful model (SPEC_GUIDE
§2 cheatsheet: `str` value-level → Lean `String`).

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The modeled computation is a closed expression
  over the two inputs using only string equality, concatenation, and two literals;
  it calls no unchanged repo callee whose contract the proof must assume
  (SPEC_GUIDE §3 / §0.7). `axiom_check.py` is therefore a skip stub and G-AX
  skips.
- **Flag dependency.** `rawIpv6` (`self._raw_ipv6`) gates the first branch; it is
  an input of the modeled function, not a hidden callee configuration. The
  `elif self.addr == "0"` branch is reached only when `rawIpv6` is false, which
  the spec and conformance oracle both honor.
- **Upstream provenance of inputs.** `self.addr` and `self._raw_ipv6` are
  resolved earlier in `handle()` (address parsing / defaulting); that resolution
  is unchanged by the patch and is upstream of the modeled sub-computation, so it
  is treated as the (arbitrary) input to the modeled function. G-CONF fuzzes the
  full input cross-product including the boundary host `"0"`.

## G-CONF fuzz seed

Pinned LCG seed: **16145** (see `conformance_check.py` `SEED`). Corpus: `rawIpv6`
drawn from `{False, True}`; `addr` drawn from a boundary set
(`"0"`, `"0.0.0.0"`, `""`, `"::1"`, `"127.0.0.1"`, `"localhost"`, `"0.0"`, `"00"`,
`"10"`) plus randomly generated host-like strings. The full cross-product of the
boundary set with both flag values is enumerated as the edge set (it contains the
discriminating input `rawIpv6=False, addr="0"`); the fuzz loop then samples ≥1e5
random `(rawIpv6, addr)` pairs, diffed against an in-process replica of the
post-patch display-address computation (0 disagreements required).
