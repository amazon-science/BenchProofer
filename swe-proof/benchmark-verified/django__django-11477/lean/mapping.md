# mapping.md — django__django-11477

## Symbol binding (file:line @ base_commit e28671187903e6aca2428374fdd504fca3032aee)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_capture` / `problem_spec_capture` | `django.urls.resolvers.RegexPattern.match` | `django/urls/resolvers.py:150-159` |
| `ScanOutcome` (pure helper) | the successful `re.Match` object `match = self.regex.search(path)` plus `self` | `django/urls/resolvers.py:151` |
| `carriesValue` (pure helper) | the per-group test `v is not None` in the changed dict comprehension | `django/urls/resolvers.py:156` (the changed line) |

The modeled function is `RegexPattern.match`. It is the only function whose
behavior changes and the one observed (transitively, via `resolve`/`reverse`/
`translate_url`) by the FAIL_TO_PASS tests.

### What the function does (base_commit)

```python
def match(self, path):
    match = self.regex.search(path)
    if match:
        # If there are any named groups, use those as kwargs, ignoring
        # non-named groups. Otherwise, pass all non-named arguments as
        # positional arguments.
        kwargs = match.groupdict()                  # <-- the changed line
        args = () if kwargs else match.groups()
        return path[match.end():], args, kwargs
    return None
```

The function searches the compiled pattern against `path`. On no match it returns
`None`. On a match it builds:
1. `kwargs` — the named-group dictionary `match.groupdict()`. In Python a named
   group that did NOT participate in the match (an OPTIONAL named group that the
   input did not exercise) maps to the value `None` in `groupdict()`.
2. `args` — the empty tuple when `kwargs` is truthy (non-empty), otherwise the
   full positional-group tuple `match.groups()`.
3. the leftover path `path[match.end():]`, alongside `args` and `kwargs`.

The defect: an absent optional NAMED group is recorded in `kwargs` with the value
`None`. Downstream, `reverse()`/`_reverse_with_prefix` runs `force_text()` over
the kwargs and turns that `None` into the literal string `'None'`, corrupting the
rebuilt URL (`translate_url` then 404s). Two further consequences flow from
`kwargs` being non-empty even when every named value is absent: `args` is forced
empty (positional groups suppressed) when really there were no usable named
captures.

The post-fix line filters out the `None` values:
```python
kwargs = {k: v for k, v in match.groupdict().items() if v is not None}
```
so an absent optional named group contributes NO `kwargs` entry. When that
leaves `kwargs` empty (every named group was optional and absent), `args` then
correctly falls back to `match.groups()` (the positional captures).

### `ScanOutcome` field ↔ Python expression bijection

| `ScanOutcome` field | Python meaning | notes |
|---|---|---|
| `consumed` | `match.end()` — the index one past the matched prefix | the leftover path is `path[match.end():]`, modeled as `path.drop consumed`. |
| `namedCaptures` | `match.groupdict()` as an ordered list of `(name, value-or-None)` | each named group in declaration order; value is `some v` when the group participated, `none` when it is an absent optional group (Python `None`). |
| `positionalCaptures` | `match.groups()` as a list of `value-or-None` | the positional (non-named) captures; modeled as `List (Option V)` — only its identity/length/contents matter, never inspected element-wise here. |

The whole input is `(path : List Char, outcome : Option (ScanOutcome V))`:

| Lean input | Python meaning |
|---|---|
| `path` | the `path` argument (`str`), modeled per-character as `List Char`. |
| `outcome` | the result of `self.regex.search(path)`: `none ↔ match is None` (the `if match:` test is false → return `None`); `some sc ↔` a successful match carrying `end()`, `groupdict()`, `groups()`. |

`carriesValue (name, v)` models the `v is not None` test in the post-fix
comprehension: `v.isSome` is true exactly when the named group participated.

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `path` (`str`) | `List Char` | per-code-point; `path[match.end():]` ↔ `path.drop consumed`. |
| `self.regex.search(path)` result | `Option (ScanOutcome V)` | `None ↔ none`; a match ↔ `some` of its `end`/`groupdict`/`groups`. |
| `match.groupdict()` (`dict[str, str|None]`, insertion = declaration order) | `List (Nat × Option V)` | ordered association list; group names distinct ⇒ lossless; `None` value ↔ `none`, a captured string ↔ `some v`. |
| `match.groups()` (`tuple[str|None, ...]`) | `List (Option V)` | positional captures in order; `None` ↔ `none`. |
| the returned `(newpath, args, kwargs)` (or `None`) | `Option (List Char × List (Option V) × List (Nat × Option V))` | `None ↔ none`; the 3-tuple ↔ `some (leftover, positional, named)`. The Python `kwargs` dict ↔ the `named` association list; `args` tuple ↔ the `positional` list. |

Group names are distinct (a regex cannot declare two groups with the same name),
so the `groupdict()` dict ↔ ordered `(name, value)` list bijection is exact, with
declaration order as the deterministic ordering.

The captured-text VALUE is modeled by a type variable `V`: the function never
inspects a captured string, it only decides presence (`is not None`) and carries
the value through. Using `Option V` keeps the `None`/present distinction — the
sole observable the fix turns on — while abstracting the irrelevant text content.

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — discarding the
  named captures whose value is `None`, and the consequent `args` fallback — is
  modeled DEEPLY as `namedCaptures.filter carriesValue` and the
  `if named.isEmpty then positionalCaptures else []` decision (SPEC_GUIDE §3: a
  deeply-modeled changed decision is never axiomatized).
- **`self.regex.search` is not modeled as an opaque callee whose contract the
  proof consumes.** Its outcome is supplied as input data (`ScanOutcome`): the
  modeled logic only reshapes that data (filter named, choose positional, slice
  path). No property of the regex engine is needed by the proof, so there is no
  `opaque`/`axiom` and `axiom_check.py` is a skip stub (G-AX skips).
- **`match.end()` / `match.groupdict()` / `match.groups()`** are the three
  observables carried as `consumed` / `namedCaptures` / `positionalCaptures`.
  `groupdict()` placing `None` for an absent optional group is the precise
  pre-condition the fix addresses; modeled by `none` values in `namedCaptures`.
- No flag dependency.

## G-CONF fuzz seed

Pinned LCG seed: **11477** (see `conformance_check.py` `SEED`). Corpus: randomized
scan outcomes — `consumed` in `0..len(path)`; `namedCaptures` a list (length 0–6)
of `(name, value-or-None)` with names drawn from `0..7` and value `None` with
~40% probability (so the absent-named-group case bites); `positionalCaptures` a
list (length 0–4) of value-or-None; crossed with `outcome ∈ {None} ∪ {a built
outcome}` and varied `path` lengths — diffed against an in-process replica of the
post-patch `RegexPattern.match` body (`{k:v for k,v in groupdict().items() if v
is not None}`, `args = () if kwargs else groups()`, leftover `path[end:]`), over
≥1e5 fuzzed inputs. Hand-picked edge cases pin the discriminating absent-optional
-named-group clause (a named group present with value `None`).
