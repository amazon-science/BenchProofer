# mapping.md — django__django-14608

## Modeled function

| Lean | Python | file:line @ base_commit `7f33c1e22d` |
|---|---|---|
| `implementation_nonFormErrors` / `problem_spec_nonFormErrors` / `correct_nonFormErrors` | the production of a form-set's non-form error collection in `BaseFormSet.full_clean` | `django/forms/formsets.py:330-383` (sites: `:336` initial construction, `:353` management-error append, `:383` validation-error reconstruction) |

The modeled function abstracts `full_clean`'s production of `self._non_form_errors`:
the collection is constructed, possibly appended to (management bookkeeping error),
and possibly replaced wholesale (cross-collection validation error). The output is
the resulting error collection — the value `non_form_errors()` returns and that
templates render via its CSS class.

## Type bijection (Lean ↔ Python) — used by G-CONF + G-AX

| Python | Lean | notes |
|---|---|---|
| `ErrorList` instance | `structure ErrorList` with `messages : List String`, `cssClass : String` | only the two touched/observable fields: the carried messages and the rendered CSS class (`self.error_class`) |
| `self.error_class(initlist, error_class=c)` constructor | `mkErrorList initlist (some c)` | `ErrorList.__init__`: `error_class is None → 'errorlist'`; else `'errorlist {}'.format(c)` (`django/forms/utils.py:84-90`) |
| `self.error_class()` (no extra class) | `mkErrorList [] none` | base CSS class `'errorlist'` |
| `el.append(msg)` | `ErrorList.append el msg` | `UserList.append`: pushes one message, CSS class unchanged |
| `self.is_bound` | `isBound : Bool` | whether the form-set has bound data; `full_clean` returns early when false |
| `self.management_form.is_valid()` | `mgmtValid : Bool` | management bookkeeping validity; when false, a management error message is appended |
| the management `ValidationError` message | `mgmtError : String` | the single message appended at the management-error site |
| `ValidationError` raised by max/min/clean, surfaced as `e.error_list` | `raised : Option (List String)` | `none` = no cross-collection error; `some errs` = the raised messages that replace the collection |
| CSS class string `'errorlist nonform'` | `"errorlist nonform"` | the post-patch rendered class for the non-form collection |

## Callee provenance / flag deps

- `self.error_class` is the form-set's `ErrorList` class (`forms/utils.py:80`,
  unchanged by the patch). Its constructor's class-string behavior
  (`None → 'errorlist'`, `c → 'errorlist {}'.format(c)`) is modeled DEEPLY as
  `mkErrorList` (no opaque callee, no consumed `_prop` axiom). G-AX validates
  `mkErrorList` == the real `ErrorList` constructor's `error_class` field over
  fuzzed inputs.
- `ErrorList.append`/`UserList.append` only push a message; the CSS class is set
  once at construction and is invariant under append — pinned in `ErrorList.append`.
- No flag dependency: the patch unconditionally passes `error_class='nonform'` at
  both construction sites.

## Production-path note

`full_clean` may both append a management error AND then raise+replace on
max/min/clean validation; in that path the wholesale reconstruction at `:383`
discards the appended message (matches Python: `self._non_form_errors` is
reassigned). `expectedMessages` models this precedence: `raised = some errs`
yields exactly `errs` regardless of `mgmtValid`. The CSS class is `errorlist
nonform` on every path.

## G-CONF fuzz seed

`conf_seed = 14608` (pinned; see conformance_check.py and meta.json).
