# refinement.md — astropy__astropy-14096

Each operation of `implementation_resolveAttr` mapped to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op).

| # | Lean impl op | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `if let some r := handledCase self attr then return r` | the UNCHANGED resolution branches of `__getattr__` (lines 873–895: `_is_name`, `frame_attributes`, embedded-frame delegation, `lookup_name`/`transform_to`), each ending in `return …` | A-reference | not touched by the patch; aggregated as `handledCase`. Its outcome is three-valued because the branches are evaluated expressions, not guards: resolves-to-`v`, RAISES (the transform-target branch, measured on four names), or falls-through. Surfacing it verbatim — `return r` — is what makes the raised exception escape `__getattr__` unchanged, as it does in the real function. Validated against the real branches by G-AX. |
| 2 | `return ordinaryLookup self attr` | the PATCHED fail path: `return self.__getattribute__(attr)` (replacing the fabricated `raise AttributeError(...'{attr}'...)`) | A-reference | THE fix. The new behavior is "defer to the ordinary attribute-access protocol," modeled as `ordinaryLookup self attr` and propagated verbatim (value or genuine error). The error-naming property — that the propagated error reports the genuinely-missing name, not the requested `attr` — is the discriminator; validated against the real protocol by G-AX. |

Control flow: `Id.run do` with an early `return` on the branch that applies and a
tail `return` on the fallback — a line-for-line skeleton of the real
`__getattr__` epilogue (guarded branches that `return` a value or raise, the
raise being carried by the `Except.error` half of the surfaced outcome, then a
single fallback `return`).

No **R** or **I** rows ⇒ the impl region is all-A-tagged ⇒ `conf_skip = true`
(G-CONF skip stub). No **A-consumed** rows ⇒ no consumed callee axiom; G-AX
validates the two A-reference callees' modeled behavior against the real ones.

## Prepatch discriminator

`Solution_prepatch.lean` keeps op 1 verbatim (the branches, and their raised
exceptions, are untouched by the patch) and replaces op 2 with
`return Except.error { missing := attr }` (the pre-fix fabricated error, whose
default `kind` is the attribute-lookup class). On the `handledCase = none` branch the spec
demands `result = ordinaryLookup self attr`; the buggy impl yields
`Except.error { missing := attr }`, which is not equal to the ordinary-lookup
outcome whenever the genuine error reports a different name (the exact F2P
scenario: requested `prop`, genuinely-missing `random_attr`). Hence the carried
gold proof cannot close — G-DIFF satisfied.
