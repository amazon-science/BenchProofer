# mapping.md — astropy__astropy-14096

## Symbol binding (file:line @ base_commit)

Modeled function: `SkyCoord.__getattr__`
- File: `astropy/coordinates/sky_coordinate.py`
- Function `def __getattr__(self, attr):` at line 867 @ base_commit.
- Gold-patch edit: lines 894–898 of the hunk — the final "Fail" path. Before:
  `raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attr}'")`.
  After: `return self.__getattribute__(attr)`.

## Lean ↔ Python type bijection

| Lean | Python |
|---|---|
| `CoordObj` (opaque) | the `SkyCoord` (or subclass) instance `self` |
| `attr : String` | the requested attribute name `attr : str` |
| `AttrValue` (opaque) | an arbitrary resolved Python attribute value |
| `AttrError { missing, kind }` | the Python exception that escapes the attribute access; `kind` = `type(e).__name__`, `missing` = the attribute name quoted in the message (the `match=` group the F2P test asserts on) for an `AttributeError`, and `""` for kinds that name no attribute. `kind` defaults to `"AttributeError"` so a bare `{ missing := m }` denotes an attribute-lookup failure naming `m`. |
| `Except AttrError AttrValue` | "returns a value" (`Except.ok`) vs "propagates an exception" (`Except.error`) — the two observable outcomes of an attribute access |
| `handledCase self attr : Option (Except AttrError AttrValue)` | aggregate of the domain-specific resolution branches inside `__getattr__` guarded by `"_sky_coord_frame" in self.__dict__` (frame-alias `_is_name`; `frame_transform_graph.frame_attributes`; delegation to `self._sky_coord_frame`; `lookup_name` + `transform_to`). `some (Except.ok v)` iff one of those branches `return`s a value `v`; `some (Except.error e)` iff the branch that applies is entered but evaluating it RAISES `e`, which escapes `__getattr__` without the fail path ever being reached; `none` iff no branch applies and control reaches the final fail path. |

Why the resolution aggregate is three-valued and not `Option AttrValue`: the
branches are not guards, they are evaluated expressions, and the transform-target
branch `return self.transform_to(attr)` can raise. Measured on the worktree at
base_commit with `patch.diff` applied, on
`SkyCoord("00h42m30s", "+41d12m00s", frame="icrs")`:

| requested name | guard trace | outcome |
|---|---|---|
| `altaz` | `lookup_name` → `AltAz`, `is_transformable_to` → `True` | raises `AttributeError: 'NoneType' object has no attribute 'to_geodetic'` (`AltAz.location` defaults to `None`; `erfa_astrom.apco`) |
| `lsr` | same branch | raises `TypeError` (insufficient position information) |
| `galactocentric` | same branch | raises `ConvertError` (needs a 3D coordinate) |
| `hcrs` | same branch | raises `UnitsError` (no length units) |

In every one of the four the traceback contains `return self.transform_to(attr)`
and does NOT contain `return self.__getattribute__(attr)`, so the fallback line is
provably not reached and the outcome is neither "resolved a value" nor "fell
through". That is why the aggregate's codomain carries the branch's own
`Except` outcome, and why `AttrError` carries a `kind`: three of the four
exceptions are not `AttributeError` at all.
| `ordinaryLookup self attr : Except AttrError AttrValue` | `self.__getattribute__(attr)` — Python's ordinary attribute-access protocol for the same name: `Except.ok v` if it produces a value, `Except.error { missing := m }` if it raises `AttributeError`, where `m` is the name that protocol reports (which need NOT equal `attr` — e.g. a property getter that internally touches a genuinely-missing name reports THAT name). |

## Callee provenance + flag deps

- `handledCase` — A-reference. Aggregates the UNCHANGED resolution branches of
  `__getattr__` (lines 873–895), INCLUDING their exceptional exits: the value of
  the branch that applies, or the exception evaluating it raises. Guard flag: all
  branches sit under `if "_sky_coord_frame" in self.__dict__`; when that key is
  absent the guard block is skipped entirely and `handledCase = none`. Not changed
  by the patch — the four measured raising names above behave identically before
  and after it, because the branch returns or raises before the fail path in both
  versions, and the patch rewrites only the fail path (lines 894–898).
- `ordinaryLookup` — A-reference. Models the UNCHANGED Python ordinary
  attribute-access protocol `object.__getattribute__` as re-invoked by the fix
  (`self.__getattribute__(attr)`). The patch SELECTS this callee on the fallback
  path; it does not modify the callee. Its error-name behavior (reporting the
  genuinely-missing inner name, not the requested one) is the property the issue
  hinges on, and is intrinsic to CPython's protocol — exercised by G-AX.

## Proof obligations

`correct_resolveAttr` is closed by pure case analysis on `handledCase self attr`
(`some`/`none`); it consumes NO property axiom about either callee. Both `_prop`
slots are therefore empty (the proof agent should not need the axiom-propose loop).
`#print axioms correct_resolveAttr` reports `[propext]` — a standard axiom, via
`Option.some_inj`; no `sorryAx`.

## G-CONF fuzz seed

Pinned seed: `20240629`. (Impl region is all-A-tagged → G-CONF is a skip stub;
seed recorded for reproducibility of the stub's manifest.)
