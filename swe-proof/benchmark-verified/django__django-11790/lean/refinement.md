# refinement.md — operation correspondence (django__django-11790)

Maps every op in `implementation_authUsernameField` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The post-patch Python block is:
```python
username_max_length = self.username_field.max_length or 254
self.fields['username'].max_length = username_max_length
self.fields['username'].widget.attrs['maxlength'] = username_max_length
```

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let umax := usernameMaxLength configuredMax` | `username_max_length = self.username_field.max_length or 254` | R | `max_length or 254` ↔ `usernameMaxLength : Option Nat → Nat`: falsy (`None`/`0`) → 254, positive int → itself. Python truthiness on int bijects to the `none`/`some 0`/`some (n+1)` split (mapping.md). |
| 2 | `let mut field := { maxLength := 0, attrs := initAttrs }` | the existing bound `self.fields['username']` with its widget attrs | I | initial field carrier; `maxLength := 0` is a placeholder overwritten in op 3; `attrs := initAttrs` is the field widget's current integer-valued attribute map |
| 3 | `field := { field with maxLength := umax }` | `self.fields['username'].max_length = username_max_length` | I | field `max_length` assignment |
| 4 | `field := { field with attrs := setAttr field.attrs "maxlength" umax }` | `self.fields['username'].widget.attrs['maxlength'] = username_max_length` | I | dict key assignment ↔ `setAttr` (overwrite-or-insert on the assoc list) |
| 5 | `return field` | (block falls through; the configured form field is the effect) | I | concrete return of the configured carrier |

No A-consumed and no A-reference rows: every op is R or I, fully concrete; no
UNCHANGED callee property is assumed and nothing is axiomatized. No
changed-inexpressible op.

The discriminating op is row 4: the widget `maxlength` attribute assignment.
The prepatch impl omits it (stops after row 3, leaving `attrs = initAttrs`), so
its `correct_authUsernameField` cannot close the second conjunct of the frozen
`problem_spec` (`result.attrs = setAttr initAttrs "maxlength"
(usernameMaxLength configuredMax)`): `initAttrs ≠ setAttr initAttrs …` in
general. That is the G-DIFF signal. Note the spec pins the WHOLE attribute map to
the concrete `setAttr` update (not merely its `maxlength` lookup), so even an
impl that omits the update but starts from an `initAttrs` that already carries
the right `maxlength` is excluded — the frame is grounded in the input.

G-CONF runs a real fuzz (impl region is R/I, not all-A-tagged): the Python shadow
of the impl is differential-tested against an independent reconstruction of the
post-patch block over ≥10^5 fuzzed `(max_length, init_attrs)` inputs.
