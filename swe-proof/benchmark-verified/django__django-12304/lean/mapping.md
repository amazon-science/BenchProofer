# mapping.md — django__django-12304

## Symbol binding (file:line @ base_commit 4c1b401e82)

Modeled function: the metaclass constructor that builds an enumerated-choices
class, `ChoicesMeta.__new__` (`django/db/models/enums.py:11-34` @ base_commit).
The gold patch adds a single line at `:34` (post-patch) — after the per-member
value/label processing and the installation of the `label` property — that sets
a class-level attribute marking the produced class as one the template engine
must NOT invoke when it is encountered as a resolved value.

Lean modeled function name: `buildChoicesClass` (neutral — it names the
*behavior* "build the choices class", and the modeled attribute uses the
attribute name that appears verbatim in the public `problem_statement`).

### Why the attribute matters (the consumer, unchanged)
The behavioral consumer is the template variable resolver
`Variable._resolve_lookup` (`django/template/base.py:816-881` @ base_commit).
For each resolved lookup value `current`, lines 851-866 do:

```python
if callable(current):
    if getattr(current, 'do_not_call_in_templates', False):
        pass                       # leave the value as-is, do NOT call it
    elif getattr(current, 'alters_data', False):
        current = ...string_if_invalid
    else:
        current = current()        # call with no args  <-- crashes for an enum class
```

An enumeration class is *callable* (calling it does value-lookup and REQUIRES a
`value` argument), so absent the flag the resolver hits the `else` arm and calls
`current()` with no args → `TypeError` → the variable fails to resolve. Setting
`do_not_call_in_templates = True` selects the first arm (`pass`), so the class is
left intact and subsequent member/attribute lookups (`.DIAMOND`, `.label`,
`.value`) resolve normally. This is exactly the FAIL_TO_PASS `test_templates`
shape (`{{ Suit.DIAMOND.label }}|{{ Suit.DIAMOND.value }}` → `Diamond|1`).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `buildChoicesClass` (modeled constructor) | `ChoicesMeta.__new__`, `enums.py:11-34` |
| `memberValues` | the per-member `(value, label)` entries computed in the `__new__` loop (`enums.py:12-27`) and recorded as `cls._value2label_map_ = dict(zip(cls._value2member_map_, labels))` (`enums.py:29`) |
| `result.value2label` | `cls._value2label_map_` — the produced class's value→label map (unchanged by this patch; frame-pinned) |
| `result.doNotCallInTemplates` | `cls.do_not_call_in_templates` — the attribute the patch adds at `enums.py:34` (post) |
| `templateWouldCall c d a` | the `_resolve_lookup` call decision `callable(current) and not do_not_call_in_templates and not alters_data` (`base.py:851-856`) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| an enum member's stored `(value, label)` — `value : int`, `label : str` | `(Int × String)` |
| `cls._value2label_map_` (value→label, ordered by member definition) | `value2label : List (Int × String)` |
| `cls.do_not_call_in_templates : bool` (default-absent ⇒ `getattr(..., False)`) | `doNotCallInTemplates : Bool` |
| the resolver's "is this value callable?" — always True for an enum class | the `isCallable` argument to `templateWouldCall`, fixed `true` for the class |
| `getattr(current, 'alters_data', False)` — False for an enum class | the `altersData` argument, fixed `false` for the class |
| `_resolve_lookup` calls `current()` | `templateWouldCall true result.doNotCallInTemplates false = true` |

`Int` is used for the member value because the reported case (`IntegerChoices`,
`Suit.DIAMOND = 1`) is integer-valued; only equality / pass-through of the value
is observed, so the choice does not affect the modeled decision.

## Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom. The member `(value, label)`
  entries enter as plain DATA (`memberValues`); the value→label map is the
  identity carrier `value2label = memberValues` (the `dict(zip(...))` gather is
  pre-existing, unchanged code, not touched by this patch). The added attribute
  is a literal `true`. The resolver decision `templateWouldCall` is modeled
  deeply as the exact boolean `c && !d && !a` from `base.py:851-856`.
- Flag dependency: the produced class is ALWAYS marked (the patch sets the
  attribute unconditionally for every Choices class), so `doNotCallInTemplates`
  is `true` for every input. An enum class is always `callable` and never
  `alters_data`, so the resolver's call decision depends only on the added flag.

## G-LEAK
The discriminator vocabulary — `do_not_call_in_templates`, "templates",
"callable", "called with no arguments" — appears VERBATIM in the public
`problem_statement` ("Django Templates always call callables with no arguments";
"declare do_not_call_in_templates = True"). The spec view therefore names the
behavior in public terms with no relaxation. The modeled-function identifier
`buildChoicesClass` shares no patched def/class name (`ChoicesMeta`, `__new__`)
as a substring.

## Pinned G-CONF fuzz seed
`12304`.
