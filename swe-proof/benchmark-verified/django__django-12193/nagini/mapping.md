# mapping.md — django__django-12193

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 3fb7c12158a2402f0f80824f6778112071235803`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/forms/widgets.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `prepare_attrs(value, attrs)` | `CheckboxInput.get_context(self, name, value, attrs)` — `django/forms/widgets.py:521` | the modeled changed function. The model captures the part of `get_context` the patch changes: the construction of the attribute mapping that is then handed to `super().get_context(name, value, attrs)`. Its `Result()` is that mapping (the one the shared rendering step receives). |
| `counts_as_selected(value)` | `self.check_test(value)`, default `boolean_check(v)` — `django/forms/widgets.py:503` | pure spec: the fixed selection predicate (`not (v is False or v is None or v == '')`). |
| `attr_selected()` | the dict key `'checked'` (`widgets.py:526` pre-patch / the `'checked': True` entry of the merge post-patch) | pure spec: the selection attribute-name token. |
| `val_false()/val_absent()/val_empty_text()` | the three "empty" value sentinels `False` / `None` / `''` that `boolean_check` rejects | pure spec: value codes for the not-selected sentinels. |
| `mapping_with(base, key, flag)` *(axiom — A-consumed)* | the dict-display merge `{**(attrs or {}), 'checked': True}` — `django/forms/widgets.py:525` (post-patch) | unchanged language primitive (`{**base, key: value}`) the new code composes to build a FRESH attribute mapping. |
| `mapping_copy(base)` *(axiom — A-consumed)* | the pass-through of `attrs` when `check_test` is false (`widgets.py:527`, `return super().get_context(name, value, attrs)`) modelled as the standard copy `{**base}` | unchanged language primitive; observationally equivalent pass-through of the caller's mapping contents (see §2). |

The pre-patch repo statements the change removes (for the refinement audit, not
referenced from the consumer spec view): `if attrs is None: attrs = {}` and the
in-place write `attrs['checked'] = True` (`widgets.py:524-526`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `attrs` dict (`{str: Any}`, here the rendered HTML attributes) | `Dict[int, bool]` from attribute-name token to flag | only key membership and per-key value are observed by the F2P/P2P tests (`attrs['checked'] is False`, `subwidget['attrs'] == {'checked': True}` / `{}`); integer-keyed identity is the faithful carrier. The `'checked'` key ↔ `attr_selected()`; the value `True` ↔ Python `True`. |
| `attrs is None` (caller passed no mapping) | the model takes a present `Dict`; the `attrs or {}` coalescing of the patch is the `None → {}` case | the F2P tests pass a present dict (`{'checked': False}`) and the empty dict (`{}`); the `None` case coalesces to an empty mapping, which the present-empty-`Dict` already covers behaviourally. Modeling `attrs` as a present (possibly empty) `Dict` is observationally faithful for the tested inputs. |
| `self.check_test(value)` (default `boolean_check`) | `counts_as_selected(value)` over an `int` value code | the predicate is `not (v is False or v is None or v == '')`; the three rejected sentinels map to `val_false()/val_absent()/val_empty_text()`, every other code counts as selected. Modeled deeply (not an oracle): the result must be produced by the selected/not-selected branch. |
| pass-through of `attrs` (false branch returns the same object to super) | a fresh copy `mapping_copy(attrs)` with identical contents | `super().get_context` reads only the CONTENTS of `attrs` (`build_attrs(self.attrs, attrs)` = `{**self.attrs, **attrs}`, `widgets.py:250`), never its object identity, so returning a fresh copy with the same keys/values is observationally identical to returning the same object. This keeps a uniform full-permission return and never weakens the no-mutation guarantee. |

`str` keys/values are not indexed (Nagini bans `str` indexing); the carrier is
`Dict[int, bool]` throughout.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `mapping_with` ↔ `{**base, key: flag}` (A-consumed)
**Callee:** the Python dict-display merge `{**(attrs or {}), 'checked': True}`,
an unchanged language primitive (PEP 448 dictionary unpacking; CPython
`BUILD_MAP` / `DICT_MERGE`). It always allocates a **new** dict, leaving `base`
unmutated, holding every key of `base` plus the named key (the named key's value
winning). The axiom encodes exactly the obligations the new `get_context` relies
on:

  * the result is a fresh object, `Result() is not base` (so the caller's
    mapping is never written — the heart of the fix);
  * the named key is present with the supplied flag;
  * every other key of `base` is carried through with its value;
  * no key outside `base ∪ {key}` appears.

This is the weakest contract sufficient for `prepare_attrs`'s postcondition. The
freshness clause (`Result() is not base`) is the load-bearing one: it is what
the pre-patch in-place mutation lacked.

### 3.2 `mapping_copy` ↔ `{**base}` (A-consumed)
**Callee:** the Python dict copy `{**base}` / `dict(base)`, an unchanged
language primitive. A fresh dict holding exactly `base`'s keys and values,
distinct from `base`. Used only to model the not-selected pass-through
(observationally a fresh, contents-identical mapping per §2). The axiom encodes:
fresh object distinct from `base`; same keys both directions; same value at each
key.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL Python operations
`{**base, key: flag}` and `{**base}` on boundary inputs (empty mapping; a
mapping already containing the `'checked'` key with `False` — exactly the F2P
`test_get_context_does_not_mutate_attrs` input; mappings with unrelated keys;
the selected/not-selected SplitArray scenario `[True, False]`) plus randomized
fuzzing, and asserts that (i) `base` is not mutated and is not the result
object, and (ii) every membership/value observation meets the axiom's `Ensures`.
It imports nothing repo-specific — the merge/copy are pure language primitives.
Exit 0 iff sound.
