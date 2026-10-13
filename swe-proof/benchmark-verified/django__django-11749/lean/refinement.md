# refinement.md — django__django-11749

Maps every operation of `implementation_requiredOptionArgs` to its `patch.diff`
counterpart. Tags: **R** type refinement, **A-consumed** consumed axiom,
**A-reference** deep-model callee (G-AX), **I** identical concrete op.

| # | Lean impl op | patch.diff / source op | tag | note |
|---|---|---|---|---|
| 1 | `let mut parseArgs := parseArgsPrefix` | `parse_args = [str(a) for a in args]` (the prefix already built before the patched region) | R | the positional prefix is opaque to this fix; modeled as a `List String` carried unchanged. Frame-pinned (directive 5): the spec states `result = parseArgsPrefix ++ …`. |
| 2 | `for opt in actions do` | `for opt in parser_actions` (the comprehension iterates the flattened action list) | I | same iteration order over the same action list. |
| 3 | `destInOptions optionKeys opt` | `opt.dest in options` | R | `optionKeys` models the KEYS of the caller's `**options` — the raw keyword names, before the `opt_mapping` renaming. Membership is tested against that key set, NOT against the value table (see row 9): the source tests one dict and subscripts another. |
| 4 | `opt.req` | `opt.required` | I | the individually-required flag. |
| 5 | `inRequiredGroup groups opt` | `opt in mutually_exclusive_required_options`, where that set = `{opt for group in parser._mutually_exclusive_groups for opt in group._group_actions if group.required}` | R | the pre-computed required-group set is modeled inline as a membership test over the groups; identity (`opt in set`) ↦ structural `==` on `ParserAction` whose `id` field carries object identity. This is the CHANGED op, modeled deeply (NOT axiomatized). |
| 6 | `&&` / `||` combination of (3),(4),(5) | `opt.dest in options and (opt.required or opt in mutually_exclusive_required_options)` | I | identical boolean structure to the patched predicate. |
| 7 | `parseArgs := parseArgs ++ [← renderArg? argOptions opt]` (guarded append inside the `Option` `do`-block) | the list-comprehension element `'{}={}'.format(min(opt.option_strings), arg_options[opt.dest])` accumulated into `parse_args` | I | append-in-order realizes the comprehension; the loop+guard is the skeleton of `[... for opt in ... if ...]`. The `←` propagates the element's partiality to the whole result, matching the comprehension: if one element's `min(...)` raises OR its `arg_options[...]` subscript raises, the comprehension produces no list. |
| 8 | `leastFlag? opt.optionStrings : Option String` | `min(opt.option_strings)` | I | lexicographic minimum of the flag strings, with the SAME domain: `min` raises `ValueError` on an empty sequence, so it has no value on an action declaring no flag, and `leastFlag? [] = none`. A flagless action is a positional, and a required positional whose `dest` was supplied by keyword is selected, so this point is reachable — modeled, not excluded. |
| 9 | `argOptions.lookup opt.dest : Option String`, then `flag ++ "=" ++ value` | `arg_options[opt.dest]` interpolated via `'{}={}'.format(...)` | I | `"<flag>=<value>"` rendering, over a lookup with the SAME domain as the subscript: `arg_options` is the caller's `**options` REKEYED through `opt_mapping` (`{opt_mapping.get(key, key): value ...}`), so a `dest` that appears among the caller's keys need NOT appear in `arg_options`, and the subscript then raises `KeyError`. Hence `Option`, not a totalizing default. Measured at the patched commit with a required group holding `--x` (dest `shop`) and `--shop` (dest `shop_id`), called as `call_command(cmd, shop='foo')`: `options={'shop':'foo'}`, `arg_options={'shop_id':'foo'}`, selection picks dest `shop`, and the subscript raises `KeyError: 'shop'` at `django/core/management/__init__.py:141`. Reachable only post-patch (the pre-patch predicate never selected that action), so it is modeled, not excluded. |

No row is A-consumed or A-reference: the changed op (5) is modeled deeply and
`min`/formatting are concrete. Hence there is no consumed axiom, `axiom_check.py`
is a skip stub, and `conf_skip = false` (the impl region is all R/I, so G-CONF
runs a real differential test).

The result carrier is `Option (List String)` rather than `List String` because of
rows 8 AND 9: BOTH operations in the comprehension element are partial in the
source, and the comprehension inherits both, so a total carrier would have forced
the model to invent a value at inputs where the source returns none. Both the
postcondition and the differential state the partiality explicitly rather than
totalizing it, and neither side of `conformance_check.py` guards either operation
— the shadow reaches `None` by mirroring `renderAll`, the oracle by evaluating the
real unguarded `min(...)` and the real unguarded `arg_options[...]` subscript and
catching the raise. `conformance_check.py` draws the key set and the value table
independently, counts the two undefined branches separately, and fails if either
goes unexercised.

Rows 3 and 9 consult DIFFERENT inputs, which is why the model carries two binders.
Fusing them into one dict would model a function the repo does not compute: the
membership test reads the caller's raw keyword names and the value read goes to the
rekeyed table.

The single independently-observable fixed behavior is: an action that is not
individually required but belongs to a required mutually-exclusive group, whose
`dest` was supplied via kwargs, is now forwarded to the parser. The prepatch impl
drops the `|| inRequiredGroup groups opt` disjunct — exactly the bug — so it omits
that action and fails the spec (G-DIFF).
