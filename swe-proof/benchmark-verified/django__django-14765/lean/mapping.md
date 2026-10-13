# mapping.md — symbol binding & type bijection (django__django-14765)

## Modeled function
- **Lean** `implementation_initRealApps : RealAppsArg → Except Unit (List String)`
- **Python** the `real_apps` initialization inside `ProjectState.__init__`
  (`django/db/migrations/state.py:91-100 @ 4e8121e`). The function under spec is
  `ProjectState.__init__`; the only output component this triple models is the
  computed `self.real_apps` value (the other attributes set by the constructor —
  `self.models`, `self.is_delayed`, `self.relations` — are untouched by the
  change and are out of scope, see frame note below).

The observable behavior is the rule that derives `self.real_apps` from the
`real_apps` argument:
- argument `None` (absent)  → the empty set;
- argument that **is** a set → that same set, taken as-is;
- argument that is **not** a set (some other iterable) → an `AssertionError`
  is raised (no value is produced).

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `real_apps=None` | `RealAppsArg.absent` | the missing/None argument |
| a `set` of app labels `{"a","b"}` | `RealAppsArg.isSet [..]` | the elements carried in a `List String`; set identity is preserved (output is the same object) so order/dedup are irrelevant — compared as sets in G-CONF |
| a non-set iterable `["a","b"]`/`("a",)` | `RealAppsArg.nonSet [..]` | any value whose runtime type is not `set` |
| app label (a `str`) | `String` | one element |
| produced `self.real_apps` (a `set`) | `Except.ok (List String)` | the set's elements |
| `AssertionError` raised | `Except.error ()` | the constructor aborts; no value produced |

`RealAppsArg.elems` projects the carried element list (`[]` for `absent`). The
Python set is modeled by its element list because the changed code returns the
**same** object unchanged on the set branch (pure identity), so no set algebra
is exercised by the modeled op; G-CONF compares the `ok` element lists as sets.

### Frame note (SPEC_GUIDE §0.5)
`ProjectState.__init__` also assigns `self.models`, `self.is_delayed = False`,
`self.relations = None`. None of these are altered by the change and none depend
on `real_apps`, so they are outside the modeled output component. The modeled
output is exactly the `self.real_apps` value (or the raised error). There is no
other result component to pin.

## Callee provenance
- `isinstance(real_apps, set)` and `set()`/`set(real_apps)` are Python builtins.
  The set-vs-non-set distinction is modeled **structurally** by the
  `RealAppsArg` constructor tag (`isSet` vs `nonSet`), not axiomatized — there is
  no UNCHANGED repo callee to consume. The axioms region is therefore empty and
  G-AX is a skip stub.
- No flag dependency.

## G-CONF fuzz seed
Pinned seed: **14765**. ≥10^5 fuzzed inputs over the three argument kinds
(absent / set / non-set iterable) with random small `str` element multisets that
oversample empties and duplicates.
