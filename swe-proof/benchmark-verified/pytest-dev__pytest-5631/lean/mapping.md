# mapping.md — symbol binding & type bijection (pytest-dev__pytest-5631)

## Modeled function
- **Lean** `implementation_num_mock_patch_args : List Patching → Option Nat`
- **Python** `_pytest.compat.num_mock_patch_args(function)` —
  `src/_pytest/compat.py:62-73 @ cb828ebe70` (post-patch counts, via identity,
  the decorations that consume a positional argument).

The function inspects a test function's list of mock-patch decorations
(`function.patchings`) and returns how many of them "use up" a mandatory
positional argument. A decoration uses up an argument when it does **not** bind a
named attribute (`attribute_name` is falsy) **and** its replacement value
(`p.new`) is one of the recognised sentinel "default" objects (the marker that
means "auto-create a mock for this argument"). The recognised sentinels are the
`DEFAULT` objects of the `mock` and `unittest.mock` modules, when present.

The post-patch function determines sentinel-ness by **identity** (`p.new is
sentinel`), which is always total. It always returns an integer; it never aborts
on the value of `p.new`.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `function.patchings` (list of decoration objects) | `List Patching` | one element per `@patch(...)` decoration, base-of-list order |
| `bool(p.attribute_name)` truthy | `Patching.attributeName = true` | decoration binds a named attribute → does not consume an argument |
| `p.new is mock_sentinel or p.new is ut_mock_sentinel` | `Patching.isSentinel = true` | replacement is a recognised sentinel default (identity match) |
| `p.new` compares for equality with an ordinary boolean truth value | `Patching.eqWellDefined = true` | `false` for array-like / numpy-like values whose `__eq__` returns a non-boolean (ambiguous truth value) |
| count returned (an `int`) | `some n` | function always returns a value |
| `ValueError` raised mid-count (ambiguous truth value of an equality) | `none` | the pre-patch failure mode; post-patch never produces this |
| `not function.patchings` (empty / missing) | `patchings = []` short-circuit to `some 0` | early return 0 |

`eqWellDefined` is a *latent* attribute of `p.new`: it is irrelevant to the
post-patch behavior (which uses identity) but governs whether the pre-patch
equality-membership test aborts. It is carried in the abstraction so the prepatch
skeleton can express its abort, and so G-CONF can fuzz numpy-like replacements.

## Callee provenance
- The sentinel-recognition predicate (`p.new is mock_sentinel or p.new is
  ut_mock_sentinel`, combined with `not p.attribute_name`) is the operation the
  change introduces; it is modeled DEEPLY as `isCounted` / the `for` loop (an
  **A-reference**, validated by G-AX against the real post-patch classifier run
  over constructed decoration objects, including numpy-like replacements). NOT
  axiomatized.
- `sys.modules.get("mock")` / `sys.modules.get("unittest.mock")` and
  `getattr(..., "DEFAULT", object())` are environment lookups that resolve the
  sentinel objects; their result is abstracted into `isSentinel` (whether
  `p.new` is identity-equal to an active sentinel). No UNCHANGED callee is
  consumed as a proof axiom; the axioms region is empty.

## Flag dependency
The sentinel set depends on which mock modules are imported (`mock`,
`unittest.mock`). Post-patch this only changes WHICH objects count as sentinels,
never whether the function raises — `getattr(..., "DEFAULT", object())` supplies
a fresh unique object when a module is absent, so identity simply fails to match.
G-AX exercises both modules-present and modules-absent configurations.

## Modeled configuration and faithfulness of the abstraction
The modeled configuration is **at least one mock module present** (`any(mock_modules)`
truthy). This is the only configuration in which the function does sentinel work,
and it is the only reachable one in practice: `function.patchings` is set by the
`@patch` decorator, which lives in those modules, so a function can only have a
non-empty `.patchings` if a mock module was imported. The pre-patch
`else: return len(patchings)` branch (no mock module → count every decoration) is
therefore effectively dead and is not modeled; the F2P scenario imports
`unittest.mock`, so `any(mock_modules)` holds.

Two facts justify the `(attributeName, isSentinel, eqWellDefined)` abstraction:

1. **The count is invariant across the change when no exception occurs.** The
   sentinel objects' equality is plain identity (`object.__eq__`), so for any
   replacement whose equality is well-defined, `p.new in sentinels` (`==`-based,
   pre-patch) and `p.new is s1 or p.new is s2` (identity-based, post-patch) agree.
   Hence `isSentinel` (= identity match against an active sentinel) yields the
   correct count for BOTH pre- and post-patch whenever the computation completes.
   The sole observable change is the elimination of the raise — captured by the
   `Option Nat` result (`none` ≙ raise).

2. **The raise condition is pair-blind and attribute-gated.** `p.new in sentinels`
   raises iff some comparison `p.new == s` produces a non-boolean truth value —
   which, for an array-like `p.new`, occurs for ANY sentinel `s`, independent of
   which sentinel and independent of whether it would have matched. Because `and`
   short-circuits on `not p.attribute_name`, attribute-bound decorations never
   reach the comparison. So a single `eqWellDefined` bit, consulted only on the
   non-attribute branch (as in the prepatch skeleton), faithfully reproduces the
   real raise condition under the modeled (mock-present) configuration.

## G-CONF fuzz seed
Pinned seed: **5631**. ≥10^5 fuzzed decoration lists over a mix of
attribute-bound / positional decorations whose replacements are sentinels,
ordinary objects, and numpy-like array values (ambiguous equality).
