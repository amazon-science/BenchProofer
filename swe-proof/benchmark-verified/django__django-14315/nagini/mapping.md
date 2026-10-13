# mapping.md — django__django-14315

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 187118203197801c6cb72dc8b06b714b23b6dd3d`, states the type
abstraction, and gives the provenance of the one axiom.

Repo files under change:
`django/db/backends/base/client.py`, `django/db/backends/postgresql/client.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `effective_environment(env, base)` | `BaseDatabaseClient.runshell` body — `django/db/backends/base/client.py:22` (changed line 23-26: `args, env = ...` / `if env: env = {**os.environ, **env}` / `subprocess.run(args, env=env, ...)`) | modeled changed function (site 1): the environment value computed and handed to the launched subprocess |
| `normalized_environment(env)` | `DatabaseClient.settings_to_cmd_args_env` return — `django/db/backends/postgresql/client.py:54` (changed line: `return args, env`) | modeled changed function (site 2): the environment the backend reports for a command (the `env` element of the returned tuple) |
| `env_merge(base, overlay)` *(axiom — A-consumed)* | the dictionary-unpacking merge `{**os.environ, **env}` — `django/db/backends/base/client.py:25` (UNCHANGED across the patch) | unchanged standard mapping merge the changed `runshell` invokes |
| `base` (param) | `os.environ` — the current process environment (`os` imported at `base/client.py:1`) | the process environment merged into for a non-empty command mapping |
| `env` (param) | the `env` returned by `settings_to_cmd_args_env` (a `dict`, possibly empty, or — for the base class — never reached) | the per-command environment mapping |

The pre-patch repo expressions the change replaces (for the refinement audit,
not referenced from the consumer spec view):
- `base/client.py:24-25`: `if env:` / `env = {**os.environ, **env}` (so an
  empty `env` stayed an empty `dict` and was handed to `subprocess.run`) →
  `env = {**os.environ, **env} if env else None`.
- `postgresql/client.py:54`: `return args, env` (returned the built `env` dict,
  which is `{}` when no variable is set) → `return args, (env or None)`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an environment `dict` (str→str: variable name → value) | `Dict[int, int]` (name token → value token) | a key `k` is present in the model dict iff the named variable is set; the tested behaviour observes only membership, per-key value, and emptiness, so opaque `int` identity is the faithful carrier |
| `os.environ` (the `os._Environ` mapping) | `base: Dict[int, int]` | observed only via the `{**os.environ, **env}` merge; modeled as an ordinary mapping (`os.environ` behaves as a `dict` for `**`-unpacking) |
| `None` (the value handed to `subprocess.run(env=None)`, meaning "inherit `os.environ`") | the `None` case of `Optional[Dict[int, int]]` | `subprocess.run(env=None)` ⟺ the child inherits the parent environment; an empty `dict` would instead give the child an empty environment. The model's `None` is exactly this distinguished value. |
| `dict` truthiness `if env:` / `env or None` | `env is not None and len(env) > 0` | a `dict` is truthy iff non-empty; `Optional` adds the `None` case. The model spells the truthiness test out as `env is None` / `len(env) == 0`. |

`str` keys/values are never indexed (Nagini bans `str` indexing); the mapping
is carried as `Dict[int, int]` throughout, which is sound because no test
observes the textual content of a key/value through these two sites — only
presence, per-key value, and emptiness/None.

**Termination (total correctness).** Both real sites are bounded straight-line
code — a truthiness decision plus at most one bounded mapping-unpacking merge —
that always delivers its value. This is carried as
`Requires(MustTerminate(2))` on both modeled functions (Nagini is a
partial-correctness verifier by default, so without the obligation a diverging
implementation would satisfy every value postcondition vacuously). The
`env_merge` callee carries the strictly smaller `MustTerminate(1)` — it stands
for a single bounded mapping-unpacking step, and the smaller measure (1 < 2)
lets a contracted caller invoke it without leaking its own obligation.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `env_merge` ↔ `{**os.environ, **env}` (A-consumed)
**Callee:** the standard dictionary-unpacking merge `{**base, **overlay}`
(CPython mapping unpacking, PEP 448), used at `base/client.py:25` and UNCHANGED
by the patch (the patch only changes *when* it runs and what the alternative
is). The axiom encodes the weakest semantics the proof needs:

  * the result is a fresh non-empty mapping (when an input is non-empty) and is
    not `None`;
  * every key of `overlay` is present with `overlay`'s value (`overlay` wins on
    a shared key — later unpack overrides earlier);
  * every key of `base` not in `overlay` keeps `base`'s value;
  * the result holds no key outside `base ∪ overlay`;
  * `base` and `overlay` are not mutated (lengths preserved — `{**a, **b}`
    builds a new dict).

This is the standard `{**a, **b}` semantics; docs:
https://docs.python.org/3/reference/expressions.html#dictionary-displays
(PEP 448 dictionary unpacking). **Soundness check (G-AX):** `axiom_check.py`
runs the real `{**base, **overlay}` on boundary pairs (empty/empty, disjoint,
shared-key override, identical) plus 20 000 randomized pairs and asserts every
`env_merge` Ensures clause; it also confirms the inputs are unmodified.

### 3.2 The changed selection — deep models (A-reference, NOT axioms)
The two operations that genuinely **change** are modeled DEEPLY (spelled out in
the impl regions), not behind a consumed axiom:

  * `normalized_environment(env)` mirrors `env or None`
    (`postgresql/client.py:54` post-patch): empty mapping → `None`, else the
    same mapping.
  * `effective_environment(env, base)` mirrors
    `{**os.environ, **env} if env else None` (`base/client.py:25` post-patch):
    `None`/empty command mapping → `None` (subprocess inherits `os.environ`),
    else the merge.

These are validated **== the real Python expressions** out-of-band by
`axiom_check.py` (G-AX) — `(env or None)` and
`({**base, **env} if env else None)` — on boundary inputs (including the F2P
`env ∈ {None, {}} → None` case) plus 20 000 fuzz inputs. They are
A-**reference** checks, not consumed axioms (there is no `@ContractOnly` for the
selection logic). `axiom_check.py` imports only the standard library.
