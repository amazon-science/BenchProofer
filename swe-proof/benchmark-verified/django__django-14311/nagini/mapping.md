# mapping.md — django__django-14311

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 5a8e8f80bb82a867eab7e4d9d099f21d0a976d22`, states the type
abstraction, and gives the provenance of the one kind-A item (an opaque
A-reference callee — the deep model is validated against the real `str`
selector by G-AX; the proof consumes no contract from it).

Repo file under change: `django/utils/autoreload.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_module_name(name, parent)` | the `-m` module-name selection inside `get_child_arguments()` — `django/utils/autoreload.py:226-228` (changed hunk) | the modeled changed behaviour: which module name is reproduced for the relaunch command |
| `marks_entry(name)` *(opaque A-reference callee)* | the unchanged classification `spec.name == '__main__' or spec.name.endswith('.__main__')` (post-patch `autoreload.py:226`); concrete callees `str.__eq__` / `str.endswith` | fully opaque `@Pure @ContractOnly` boundary classifier (no contract consumed): whether the qualified name denotes a package executed through its entry file. The deep model is validated == this real classifier by G-AX (§3.1). |
| `module_arg(name, parent)` *(deep model — grounded over inputs)* | the post-patch selection `name = spec.parent if (sentinel and spec.parent) else spec.name` (`autoreload.py:225-231`) | pure spec (built on `marks_entry`): the module-name argument used after `-m` |

The pre-patch repo behaviour the change corrects (for the refinement audit, not
referenced from the consumer spec view): `get_child_arguments` unconditionally
used `__main__.__spec__.parent` for the `-m` argument whenever it was truthy
(`autoreload.py:226-227`):

```python
if getattr(__main__, '__spec__', None) is not None and __main__.__spec__.parent:
    args += ['-m', __main__.__spec__.parent]
```

so a directly-named module `pkg.sub.tool` (whose `__spec__.parent` is `pkg.sub`)
was wrongly relaunched as `-m pkg.sub`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`__main__.__spec__.name`, `.parent`, and the produced `-m` argument) | `List[int]` of Unicode code points | `s[k]` ↔ `name[k] == ord(s[k])`; `len(s)` ↔ `len(name)`; `str` `==` ↔ list/`PSeq` `==`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `+`/`take`/`drop`/`len`/`[i]`/`==` mirror `str` `+`/slice/`len`/index/`==` |
| the entry-file classification `spec.name == '__main__' or spec.name.endswith('.__main__')` (`autoreload.py:226`) | `marks_entry(name: PSeq[int]) -> bool` (`@Pure @ContractOnly`, opaque A-reference) | the unchanged boundary classification, modelled fully opaquely (no contract consumed); the concrete `str` selector is validated == it (and the resulting `module_arg`) by G-AX (§3.1) |
| truthiness of `spec.parent` (`and __main__.__spec__.parent`, `and spec.parent`) | `len(parent) > 0` | a `str` is falsy iff empty; `parent` is always a `str` here, so truthy ⇔ non-empty ⇔ `len > 0` |
| `args += ['-m', name]` (wrapping the selected module name) | identity on the selected module name (`select_module_name`'s result) | the F2P/P2P tests compare the produced argument list; the `-m` prefix and `sys.argv[1:]` tail are unchanged by this patch and observationally constant, so the modeled behaviour is exactly *which name* follows `-m`. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `marks_entry` opaque callee ↔ real `str` classifier (A-reference); `module_arg` selection
**Callee:** Python `str.__eq__` and `str.endswith` — the concrete operations
the gold patch performs to classify the launched unit:

```python
if getattr(__main__, '__spec__', None) is not None:
    spec = __main__.__spec__
    if (spec.name == '__main__' or spec.name.endswith('.__main__')) and spec.parent:
        name = spec.parent
    else:
        name = spec.name
    args += ['-m', name]
```

The unchanged classification (`spec.name == '__main__' or
spec.name.endswith('.__main__')`) is modelled as the **opaque A-reference**
`@Pure @ContractOnly` callee `marks_entry(name)` — it carries **no contract**
(`pass` body), so the proof consumes none of its behaviour and treats it as an
uninterpreted pure function. (It is not an A-consumed axiom; an earlier
`Ensures(Implies(len(name)==0, not Result()))` was empirically dead — the proof
verified identically without it — and has been removed.)

The changed *selection* (`module_arg`) is modelled deeply over the input
carriers, on top of `marks_entry`. `axiom_check.py` (G-AX) discharges the
**A-reference** obligation against the REAL `str` operations:

* **selection faithfulness (deep model == real callee):** the real classifier +
  selection `name == '__main__' or name.endswith('.__main__')` /
  `parent if sentinel and parent else name` match `module_arg`'s code-point
  semantics, code-point-for-code-point,

on:

* 16 boundary qualified names — including the F2P name
  `utils_tests.test_module.main_module` (a directly-named module → selects the
  name), the P2P package names `utils_tests.test_module.__main__` and
  `django.__main__` (→ select the parent), the empty name, the bare sentinels
  `__main__` / `.__main__`, sentinel-in-the-middle `pkg.__main__.sub`
  (NOT a match), and the corner cases the upstream review called out
  (`foo.my__main__`, `my__main__`, `x__main__` — names containing but not
  *dotted-ending* in `__main__`, which the real classifier correctly rejects)
  × 6 parent values;
* 40 000 randomized fuzz inputs (identifier-segment dotted names with
  `__main__` as a frequent final segment, plus character-level fuzz over
  `. _ m a i n` and astral code points to stress the suffix comparison).

It asserts agreement on every input; exit 0 iff sound. It imports only the
standard library — `str` operations are the very operations the gold patch
calls; nothing repo-specific.

**Flag dependency:** none. `str.endswith` and `str.__eq__` take no relevant
keyword arguments here; the comparison is the plain single-suffix form.
