# refinement.md — django__django-16145

Maps every operation in `implementation_displayAddr` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `displayAddr` (the banner display-address computation in `inner_run`)

Post-patch repo code (`patch.diff`):
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

Lean impl (`implementation_displayAddr`): an `Id.run do` skeleton with the same
three-way branch (raw-IPv6 → bracket-wrap; shorthand `"0"` → `"0.0.0.0"`;
otherwise verbatim), early-returning the display string from each branch.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `rawIpv6 : Bool` argument | `self._raw_ipv6` | **R** | a Python `bool` modeled as Lean `Bool` (identity on the value; mapping.md bijection). Resolved upstream in `handle()`, unchanged by the patch — treated as the modeled function's input. |
| 2 | `addr : String` argument | `self.addr` | **R** | a Python host `str` (value-level) modeled as Lean `String` (identity on the character sequence; SPEC_GUIDE §2 cheatsheet). |
| 3 | `if rawIpv6 then return "[" ++ addr ++ "]"` | `if self._raw_ipv6: addr = f"[{self.addr}]"` | **I** | identical branch: bracket-wrap the host. `"[" ++ addr ++ "]"` ↔ `f"[{self.addr}]"` is identity string concatenation. |
| 4 | `else if addr = "0" then return "0.0.0.0"` | `elif self.addr == "0": addr = "0.0.0.0"` | **I** (the changed op, deeply modeled) | **the fixed operation.** The patch adds this `elif` branch; the Lean impl adds the matching `else if addr = "0"` returning the literal `"0.0.0.0"`. The prepatch impl omits this branch (falling through to verbatim), matching base_commit. Modeled directly (no axiom). |
| 5 | `else return addr` | `else: addr = self.addr` | **I** | identical: the host is shown verbatim. |
| 6 | `Id.run do … return …` (early returns) | the `addr` local subsequently substituted for `"addr": addr` in the banner dict | **R** | the patch lifts the value into a local and substitutes it for the `%(addr)s` banner field; we model the function as returning that display string directly (mapping.md). The surrounding banner formatting (`protocol`, `port`, the format template) is unchanged by the patch and not part of the modeled decision. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch display-address computation.

## Soundness check (verify ⟹ correct)

- `problem_spec_displayAddr` pins the result in ALL THREE input cases (directive 5
  — frame: no case is left unconstrained; directive 8 — every case's result is
  grounded structurally in the inputs via concatenation / equality / literals, no
  ungrounded oracle). A verifying impl must therefore reproduce exactly this
  three-way behavior.
- The discriminating clause is the second conjunct
  `rawIpv6 = false → addr = "0" → result = "0.0.0.0"`. The prepatch impl returns
  `addr` (`"0"`) unchanged in this case, so the carried gold proof's reduction
  yields `pure "0" = "0.0.0.0"`, which is not definitionally true — the proof
  fails to typecheck (G-DIFF/G-PANEL). On every other input the prepatch and
  patched impls agree.
- This is exactly what the FAIL_TO_PASS test
  `test_zero_ip_addr (admin_scripts.tests.ManageRunserver)` exercises: with
  `addrport="0:8000"` (so `self.addr == "0"`, `self._raw_ipv6 == False`) the
  banner must read `http://0.0.0.0:8000/`, i.e. the display host is `"0.0.0.0"`,
  not `"0"`.
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  display-address computation over the boundary cross-product (including
  `rawIpv6=False, addr="0"`) plus ≥1e5 fuzzed `(rawIpv6, addr)` pairs.
