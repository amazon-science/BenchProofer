# mapping.md — django__django-16899

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d3d173425fc0a1107836da5b4567f1c88253191b`, states the type
abstraction, and records why no callee is consumed as an axiom.

Repo file under change: `django/contrib/admin/checks.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `check_reference(label, value, cls, model_label, resolves)` | `BaseModelAdminChecks._check_readonly_fields_item(self, obj, field_name, label)` — `django/contrib/admin/checks.py:761` (the changed `checks.Error(...)` block at lines 772-784) | the modeled changed function: the per-reference validator that builds the diagnostic |
| `diagnostic_message(label, value, cls, model_label)` | the first argument of `checks.Error(...)` — the `%`-formatted template at `checks.py:774-780` (post-patch) | pure spec: the diagnostic message content |
| `seg_intro/seg_refers/seg_which_not/seg_or_attr/seg_end` | the fixed prose pieces of the template string (see §2) | pure spec: fixed prose markers between interpolation points |

### 1.1 The change (for the refinement audit, not referenced from the spec view)
The gold hunk replaces the message template and its `%`-argument tuple inside
the `except FieldDoesNotExist:` branch of `_check_readonly_fields_item`:

```
- "The value of '%s' is not a callable, an attribute of "
- "'%s', or an attribute of '%s'."
+ "The value of '%s' refers to '%s', which is not a callable, "
+ "an attribute of '%s', or an attribute of '%s'."
  % (
      label,
+     field_name,
      obj.__class__.__name__,
      obj.model._meta.label,
  )
```

i.e. a new `%s` is inserted right after the label slot, and the offending
`field_name` is added to the format tuple at the matching position.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `label` (`"readonly_fields[%d]" % index`, a `str`) | `label: List[int]` of code points | `s[k]` ↔ `label[k] == ord(s[k])`; `len`/`+` mirror `str` `len`/concat |
| `field_name` (the offending reference, a `str` here — the `callable(field_name)` branch returned earlier, so on the error path it is a non-callable, i.e. a string name) | `value: List[int]` of code points | as above |
| `obj.__class__.__name__` (a `str`) | `cls: List[int]` of code points | as above |
| `obj.model._meta.label` (a `str`) | `model_label: List[int]` of code points | as above |
| the `%`-formatted template `str` produced as `checks.Error`'s message | `PSeq[int]` (via `ToSeq`) built by `diagnostic_message` | `str` concatenation of literal pieces and `%s`-substitutions ↔ `PSeq` `+` of `seg_*` markers and the dynamic carriers |
| each FIXED prose piece of the template (`"The value of '"`, `"' refers to '"`, `"', which is not a callable, an attribute of '"`, `"', or an attribute of '"`, `"'."`) | a DISTINCT one-token marker `seg_intro/seg_refers/seg_which_not/seg_or_attr/seg_end` = `PSeq(1..5)` | each fixed-prose piece ↔ one constant marker token; the pieces never vary, so their internal characters are immaterial to the tested behaviour (the tests compare the rendered message, but the discriminating content is the PRESENCE and ORDER of the dynamic interpolations and the value). The marker bijection is fixed and 1:1; refinement.md tags this **R**. |
| the unchanged resolution checks `callable(field_name)`, `hasattr(obj, field_name)`, `hasattr(obj.model, field_name)`, `obj.model._meta.get_field(field_name)` raising `FieldDoesNotExist` | the boolean guard `resolves` | `resolves == True` ⟺ the reference is accepted by ANY of the four unchanged lookups (the four early-`return []` paths); `resolves == False` ⟺ all fail and the `except FieldDoesNotExist:` error branch is taken. These lookups are UNCHANGED by the patch. |
| `return []` (no error) vs `return [checks.Error(msg, ...)]` (one error) | `Result()` empty `List[int]` vs `Result()` = the message code-point list | empty result ⟺ no diagnostic; non-empty result ⟺ exactly one diagnostic whose content is the message. The message is always non-empty, so emptiness is an exact discriminator. The `checks.Error` wrapper's other fields (`obj=`, `id="admin.E035"`) are UNCHANGED and immaterial to this behaviour. |

`str` indexing/iteration is banned in Nagini, so every string is a `List[int]`;
the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Axioms / callees

**No `@ContractOnly` axiom is consumed.** The only behaviour under change is the
SHAPE of the message string, which is modelled DEEPLY as concrete code-point
sequence concatenation (`diagnostic_message` and the `check_reference` impl).
There is no library callee on the changed path that the proof depends on: `%`
string formatting and list construction are modelled directly.

The unchanged resolution lookups (`callable`, `hasattr`, `get_field`) are NOT
axiomatized with an Ensures-bearing contract — they are abstracted by the
boolean `resolves` (a free input), because the patch does not touch them and the
tested behaviour does not depend on HOW a reference resolves, only on WHAT the
message says when it does not. There is therefore nothing for G-AX to execute:
`axiom_check.py` instead validates the deep model (`diagnostic_message`) against
the REAL Python `%`-formatting of the post-patch template (an **A-reference**
check), confirming the marker-abstracted concatenation reproduces the real
message structure.

## 4. Flag dependencies
None. No floats; default Nagini encoding. No `--float-encoding`.
