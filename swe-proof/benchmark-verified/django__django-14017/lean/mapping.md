# mapping.md — django__django-14017

## Symbol binding (file:line @ base_commit 466920f6d726eee90d5566e0a9948e92b33a122e)

- Modeled function: `Q._combine(self, other, conn)` —
  `django/db/models/query_utils.py:42-60` @ base_commit.
  - The changed line is the guard at line 43:
    pre-patch `if not isinstance(other, Q):` → post-patch
    `if not(isinstance(other, Q) or getattr(other, 'conditional', False) is True):`
  - The rest of the body (lines 45-60) is unchanged: empty-`other` short-circuit
    (`if not other: … return type(self)(*args, **kwargs)`), empty-`self`
    short-circuit (`elif not self: … return type(other)(...)`), and the general
    branch that builds a fresh node `obj` with `obj.connector = conn` and
    `obj.add(self, conn); obj.add(other, conn)`.

## Callee provenance + flag deps

- `getattr(other, 'conditional', False) is True` — reads the operand's
  `conditional` class/instance attribute. Provenance:
  - `Q.conditional = True` (`query_utils.py:37`).
  - `Combinable`-derived expressions expose `conditional` as a property; for
    `Exists` it is `isinstance(self.output_field, fields.BooleanField)`
    (`expressions.py:255-257`), and `Exists.output_field = BooleanField()`
    (`expressions.py:1152`) ⇒ `Exists().conditional is True`.
  - Plain expressions (`Expression`, `OrderBy`, `Value`) set
    `conditional = False` (`expressions.py:942-943, 1187`) ⇒ rejected, as before.
  - The default of `getattr(..., False)` ⇒ an object with no `conditional`
    attribute is rejected, as before.
  This attribute read is a pure observation, modeled DEEPLY as the boolean field
  `Operand.conditional`; it is NOT axiomatized (no opaque callee).
- `not other` / `not self` — `tree.Node.__bool__` returns `bool(self.children)`
  (`django/utils/tree.py:60-62`), i.e. "node has no children" = empty. Modeled as
  the boolean fields `Operand.empty` / `FilterNode.empty`.
- `obj.add(self, conn); obj.add(other, conn)` (`tree.Node.add`,
  `tree.py:74-122`) — builds the combined node. The fix does not touch the shape
  of the combined node; the modeled `MergeResult.merged conn` records that a
  fresh node joining both operands under `conn` is produced (the structural
  detail of `add`'s squashing is outside the fixed behavior and not modeled).

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self : Q` (a `tree.Node`) | `FilterNode` | `FilterNode.empty := (not bool(self)) == (len(self.children)==0)` |
| `other` operand | `Operand` | `isFilter := isinstance(other, Q)`; `boolValued := getattr(other,'conditional',False) is True` (EXACT `is True` — a truthy-but-not-`True` `conditional` such as `1` does NOT qualify); `empty := not bool(other)` (generic truthiness — the `not other` shortcut is NOT gated on `isinstance(other,Q)`, so a falsey accepted operand is empty too) |
| `conn` (`Q.AND` / `Q.OR`) | `Connector.and_` / `Connector.or_` | string `'AND'`↔`and_`, `'OR'`↔`or_` |
| `raise TypeError(other)` | `MergeResult.rejected` | guard fails |
| `return type(self)(*args,**kwargs)` (copy of self) | `MergeResult.keepLeft` | empty-`other` branch |
| `return type(other)(...)` (copy of other) | `MergeResult.keepRight` | empty-`self` branch |
| fresh `obj` w/ `obj.add(self,conn); obj.add(other,conn)` | `MergeResult.merged conn` | general branch |

## G-CONF fuzz seed

- Pinned seed: **14017** (see meta.json `verifier_pins.conf_seed`).
