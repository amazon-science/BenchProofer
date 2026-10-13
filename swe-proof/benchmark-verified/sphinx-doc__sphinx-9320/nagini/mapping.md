# mapping.md — sphinx-doc__sphinx-9320

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e05cef574b8f23ab1b57f57e7da6dee509a4e230`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sphinx/cmd/quickstart.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validate_path_allowing_empty(x)` | `is_path_or_empty(x)` — added by the patch in `sphinx/cmd/quickstart.py` (between `is_path` at line 91 and `allow_empty` at line 98) | the modeled NEW validator: empty response accepted as-is, otherwise delegate to the strict validator |
| `validate_strict(x)` | `is_path(x)` — `sphinx/cmd/quickstart.py:91-95` (`path.expanduser` line 92, `path.isdir` guard line 93, `raise ValidationError` line 94) | the UNCHANGED strict path validator the new one delegates to for non-empty responses |
| `abort_on_empty_reprompt(x)` | the re-prompt `while` loop body in `ask_user` — `sphinx/cmd/quickstart.py:218-228`: `d['path'] = do_prompt(..., '', <validator>)` (line 225-226) followed by `if not d['path']: sys.exit(1)` (line 227-228) | the consuming decision: the operation aborts (exits) exactly when the validated re-prompt response is empty |
| `expand_home(x)` *(axiom — A-consumed)* | `os.path.expanduser` — Python stdlib `Lib/posixpath.py` / `Lib/ntpath.py` (imported `from os import path` at line 17; called at line 92) | unchanged filesystem callee inside the strict validator |
| `expand_home_value(x)` *(axiom — A-consumed)* | the SAME `os.path.expanduser` call at line 92, in the value-producing form (its `Ensures` ties it to `expand_home`) | the rebind `x = path.expanduser(x)` at line 92, whose result is what line 95 returns; a `PSeq` cannot be materialized as a `List` inside an impl, so the spec-side pure function needs this value-side face |
| `path_is_dir(x)` *(axiom — A-consumed)* | `os.path.isdir` — Python stdlib `Lib/genericpath.py` (imported `from os import path` at line 17; called at line 93) | unchanged filesystem callee inside the strict validator |
| `ValidationRejected` exception | `ValidationError` — `sphinx/cmd/quickstart.py:87-88` (raised at line 94; caught by `do_prompt`'s `except ValidationError` at line 153) | the initializer's own validation-error signal, modeled as a user exception (builtin-exception `Exsures` crashes the translator) |
| `is_empty(x)` | the falsy-test `if not d['path']` (line 227) / the `if x == ''` guard the patch adds to `is_path_or_empty` | pure spec: an empty (just-Enter) response |

The gold patch (`sphinx/cmd/quickstart.py`):
- adds `is_path_or_empty(x)`: `if x == '': return x` else `return is_path(x)`;
- changes the re-prompt validator argument at the `do_prompt(...)` call (line 226)
  from `is_path` to `is_path_or_empty`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the response `x`, the validator return, `d['path']`) | `List[int]` of Unicode code points | `s[k]` ↔ `x[k] == ord(s[k])`; `len(s)` ↔ `len(x)`; an empty `str` `''` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `len`/equality mirror `str` `len`/`==` |
| `x == ''` (the new empty guard) | `len(x) == 0` / `is_empty(ToSeq(x))` | empty `str` ⇔ zero-length code-point sequence |
| `path.expanduser(x)` (line 92) | `expand_home(ToSeq(x))` axiom (specification side) / `expand_home_value(x)` (value side, tied to it by its Ensures) | str → str pure function; only the empty-case fact is relied on. Line 92 is a REBIND (`x = path.expanduser(x)`), so the name returned at line 95 denotes the EXPANDED path, not the argument as passed |
| `path.isdir(...)` (line 93) | `path_is_dir(...)` axiom | str → bool pure predicate; only the empty-case fact is relied on |
| `raise ValidationError(...)` (line 94) | `raise ValidationRejected()` + `Exsures(ValidationRejected, ...)` | the validation-error control-flow signal |
| `do_prompt(..., '', validator)` returning then `if not d['path']: sys.exit(1)` | `abort_on_empty_reprompt` returning `True` (abort) iff the validated value is empty | `do_prompt` returns the value the validator accepted (its `try: x = validator(x) ... break` loop, lines 151-156); the abort is `not d['path']`. Modeled as: validator-accepts-empty ⇒ abort. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`. Only the
LENGTH of the response (empty vs non-empty) is behaviourally relevant to the
fix, so the model never indexes the sequence.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

Both axioms are **A-consumed**: the proof of `validate_strict` (hence of the
re-prompt validator and the abort decision) consumes their `Ensures`. They are
the unchanged filesystem callees the strict validator calls; the patch does NOT
touch them.

### 3.1 `expand_home` ↔ `os.path.expanduser` (A-consumed)
**Callee:** CPython `os.path.expanduser(path)` (`Lib/posixpath.py::expanduser`,
`Lib/ntpath.py::expanduser`). It replaces a leading `~` or `~user` with the
user's home directory and otherwise returns the argument unchanged. Docs:
https://docs.python.org/3/library/os.path.html#os.path.expanduser.

**Weakest relied-on fact:** `expanduser('')` returns `''` — the empty path has
no leading `~`, so it is returned unchanged. Modeled:
`Implies(len(x) == 0, len(Result()) == 0)`. The proof needs only that expanding
an empty response leaves it empty, so the `path_is_dir` guard below sees the
empty path.

The callee is axiomatized twice over this one fact, because line 92 both feeds
the directory guard and determines the returned value: `expand_home` (`@Pure`,
`PSeq[int] -> PSeq[int]`) carries it on the specification side, and
`expand_home_value` (`List[int] -> List[int]`) is the value-producing face an
implementation can hold, tied to the pure one by
`Ensures(ToSeq(Result()) == expand_home(ToSeq(x)))`. Both resolve to the same
real callee in the G-CONF shadow, so neither adds an assumed fact beyond the
`Implies` above — the tie is a definition, not a new axiom.

### 3.2 `path_is_dir` ↔ `os.path.isdir` (A-consumed)
**Callee:** CPython `os.path.isdir(path)` (`Lib/genericpath.py::isdir`):
`os.stat(path)` then `stat.S_ISDIR`, returning `False` (never raising) when the
path does not exist or cannot be stat-ed. Docs:
https://docs.python.org/3/library/os.path.html#os.path.isdir.

**Weakest relied-on fact:** `isdir('')` is `False` — the empty path is not an
existing directory (the empty string is not a valid path; `os.stat('')` fails
and `isdir` swallows it to `False`). Modeled:
`Implies(len(x) == 0, Result() == False)`. This is exactly the fact that makes
the strict validator REJECT an empty response (`not path.isdir(...)` ⇒ raise),
which is why pre-patch the empty re-prompt looped on a validation error instead
of aborting.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`os.path.expanduser` and `os.path.isdir`, asserts `expanduser('') == ''` and
`isdir('') is False`, exhibits the strict-validator guard firing on the empty
response, and fuzzes 20 000 + 12 boundary inputs to confirm both callees are
total (never raise) on prompt-shaped strings — so the empty-only axiom is the
honest weakest contract. It imports only the standard-library `os` / `os.path`
(the very module the patched code imports via `from os import path`). Exit 0
iff sound.

## G-CONF (differential conformance)

`conformance_check.py` diffs the SHADOW — the three `# impl-start` /
`# impl-end` regions of `model.py` copied **verbatim** with only the contract
calls removed (the script re-extracts both regions and they are byte-identical)
— against the ORACLE, the **real patched repo functions, called** (not
transliterated):

| shadow (model.py impl region) | oracle (real, called) |
|---|---|
| `validate_strict` | `quickstart.is_path` (`sphinx/cmd/quickstart.py:91-95`) |
| `validate_path_allowing_empty` | `quickstart.is_path_or_empty` (added by the gold patch between `:95` and `:98`) |
| `abort_on_empty_reprompt` | the real `ask_user` re-prompt loop (`:218-228`), driven in-process |
| `expand_home` *(@ContractOnly)* | `quickstart.path.expanduser` — the REAL callee |
| `expand_home_value` *(@ContractOnly)* | the SAME `quickstart.path.expanduser` (value-producing face) |
| `path_is_dir` *(@ContractOnly)* | `quickstart.path.isdir` — the REAL callee |

The `@ContractOnly` axioms have no body to copy, so the shadow calls the real
callees through the patched module's own `path` binding: the axioms are
exercised, not assumed. The re-prompt loop is driven because the gold patch's
SECOND hunk (the validator argument at `:226`) is observable only through it —
`os.path.isfile` reports an existing `conf.py` exactly once (the lever the F2P
test `test_exits_when_existing_confpy` pulls), `term_input` returns the
generated response, `path.isdir` stays real, and `d['path']` is preseeded so the
first prompt reached IS the re-prompt.

**Seed:** `SEED = 9320` (module constant). **Inputs:** 100 066 = 66 boundary
(the empty F2P response first, tilde forms, real existing directories,
whitespace, NUL, surrogate and astral code points) + 100 000 seeded fuzz. The
script exits 2 if any impl branch went unexercised; the recorded run took all
three (empty-accept 14 868, non-empty-accept 15 774, reject 66 943).

**Bridge additions** (beyond §2's `str` ↔ `List[int]` code-point bijection):
- `do_prompt` **strips** the response before calling the validator
  (`x = term_input(prompt).strip()`, `:109`) and refinement.md C1 abstracts
  `do_prompt` to "the value its validator accepts", so on the abort leg the
  model's `x` denotes the VALIDATOR'S ARGUMENT: the real loop is driven with the
  raw response and the shadow runs on `raw.strip()`. (`default` at `:226` is
  `''`, falsy, so the `:110-111` default substitution never fires.)
- `os.path.expanduser` is **not total**: on a `~`-prefixed response containing a
  NUL byte or a lone surrogate it raises `ValueError` / `UnicodeEncodeError` out
  of `pwd.getpwnam`, which `do_prompt`'s `except ValidationError` does not
  catch. Recorded as a third outcome class on BOTH sides (the shadow reaches the
  same real callee), so those inputs stay in the domain instead of being routed
  around. Note for G-AX: the `@Pure @ContractOnly expand_home` axiom is declared
  total over `Requires(True)` while the real callee can raise — an
  axiom-totality observation, not a shadow/oracle disagreement.

### Recorded verdict: **pass** — all five legs clean

Per-leg result over the 100 066 inputs:

| leg | compared | result |
|---|---|---|
| `strict_routing` | accept / reject / error | 100 066 — **clean** |
| `lenient_routing` | accept / reject / error | 100 066 — **clean** |
| `abort` | abort / continue / rejected | 100 066 — **clean** |
| `strict_value` | the accepted return value | 100 066 — **clean** |
| `lenient_value` | the accepted return value | 100 066 — **clean** |

**History (the value-leg divergence this run closed).** An earlier revision of
this bundle recorded `fail` on the two value legs (15 774 / 30 642
disagreements), with witnesses:

```
input='~'      shadow = ('ok', '~')       oracle = ('ok', '/root')
input='~/'     shadow = ('ok', '~/')      oracle = ('ok', '/root/')
input='~root'  shadow = ('ok', '~root')   oracle = ('ok', '/root')
```

The cause was a mis-read of the callee: the real `is_path` REBINDS its argument
before returning it — `x = path.expanduser(x)` (`:92`) then `return x` (`:95`) —
so an acceptance yields the home-EXPANDED path. The model returned `list(x)`,
the response as typed, and its postcondition `Ensures(ToSeq(Result()) ==
ToSeq(x))` pinned exactly that wrong value; refinement.md B4 had justified it as
"accepted response returned unchanged", overlooking the `:92` rebind. The model
was therefore unfaithful on the return value for every `~`-prefixed
existing-directory response, and a faithful port of the patched `is_path` would
have FAILED to verify.

The repair realigned the model to the callee rather than dropping the claim: the
normal-return clause is now `ToSeq(Result()) == expand_home(ToSeq(x))` in
`validate_strict`, threaded through `validate_path_allowing_empty` (whose empty
branch is unaffected because `expanduser('') == ''`, the fact the `expand_home`
axiom already carries and G-AX already checks). The impl mirrors the rebind via
`expand_home_value`, the value-producing face of the same callee. Both value legs
now agree on all 100 066 inputs, including every tilde form, and the reject lane
that pins the wrong value is `weak-strict-returns-unresolved` in properties.py.

**Materiality.** The divergence never reached the F2P test: `expanduser('') ==
''`, so the empty response returned `''` on both sides and the abort decision
depends only on `len == 0`. G-RESOLVE was unaffected throughout. The refinement
leg was nonetheless false as documented, which is precisely what G-CONF exists
to report — and what it now confirms is fixed.
