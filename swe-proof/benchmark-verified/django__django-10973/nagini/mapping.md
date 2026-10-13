# mapping.md — django__django-10973

Binds every `model.py` symbol to its repository counterpart at
`base_commit = ddb293685235fd09e932805771ae97f72e817181`, states the type
abstraction, and gives the provenance of the one A-reference (the removed
quoting helper the deep model is validated against).

Repo file under change: `django/db/backends/postgresql/client.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `password_env_value(passwd)` | the password-exposure logic of `DatabaseClient.runshell_db` — `django/db/backends/postgresql/client.py:19-68` (specifically the password handling at lines 37-58 pre-patch, lines 30-32/35 post-patch) | the modeled changed behaviour: the value handed to the child process for the password |
| `pgpass_quote(c)` *(deep model — A-reference; **model_prepatch.py only, elided impl region**)* | one `.replace` step of `_escape_pgpass` — `client.py:9-13` (`txt.replace('\\','\\\\').replace(':','\\:')`), per code point | reference helper for the legacy per-code-point file-fragment quoting (the helper the patch deletes); NOT in the consumer spec view |
| `pgpass_quote_seq(s)` *(deep model — A-reference; **model_prepatch.py only, elided impl region**)* | the whole-string `_escape_pgpass(txt)` — `client.py:9-13` | reference helper for the legacy quoting of a whole sequence; validated `== _escape_pgpass` by axiom_check.py (G-AX), NOT consumed as an axiom, NOT in the consumer spec view |

The pre-patch repo symbols the change removes (referenced for the refinement
audit / A-reference, not from the consumer spec view): the module-level helper
`_escape_pgpass` (`client.py:9-13`), the `NamedTemporaryFile`-based pgpass file
(`client.py:42-54`), and the `PGPASSFILE` environment plumbing
(`client.py:54,65-68`). The post-patch repo symbols that replace them: the
`subprocess_env = os.environ.copy()` copy and `subprocess_env['PGPASSWORD'] =
str(passwd)` assignment, run via `subprocess.run(args, check=True,
env=subprocess_env)`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `passwd` (a `str`, `conn_params['password']`) | `List[int]` of Unicode code points | `s[k]` ↔ `passwd[k] == ord(s[k])`; `len(s)` ↔ `len(passwd)`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `str(passwd)` coercion (`client.py:32` post-patch) | identity on the code-point list | `passwd` is already a `str` for all tested inputs; `str(str)` is the identity |
| "the value exposed to the child for the password": post-patch `subprocess_env['PGPASSWORD']` (set iff `passwd` truthy) | the returned `List[int]`, populated (`len > 0`) iff `len(passwd) > 0` | post-patch: the env var is present exactly when `passwd` is non-empty, and its value is `str(passwd)`; the model's `Result()` equals `passwd` verbatim and is non-empty iff `passwd` is non-empty |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

### Behaviour NOT re-modeled (identical between pre- and post-patch)
The `args` command-line list (`['psql', '-U', user, '-h', host, '-p',
str(port), dbname]`, gated on truthiness) and the SIGINT save/ignore/restore
dance are **unchanged** by the patch (byte-identical pre/post — see
refinement.md §B). They are unchanged plumbing, not the fix, so they are not
re-modeled; the changed behaviour is exactly the password-exposure value.

## 3. Callee provenance

### 3.1 `pgpass_quote_seq` deep model ↔ removed `_escape_pgpass` (A-reference)
The legacy quoting the new code must NOT apply is modeled **deeply** by the
`@Pure` fold `pgpass_quote_seq` (with `pgpass_quote`). To avoid leaking the
removed-mechanism diagnosis into the consumer-visible spec view (SPEC_GUIDE
directive 6), this reference fold is defined **only in `model_prepatch.py`**,
inside a module-level `# impl-start`/`# impl-end` region that is **elided from
the spec view** — it is never present in `model.py`'s consumer-visible regions
(the `pure` region is empty in both files), and it is **not a consumed axiom**.
The exact helper at base_commit (`client.py:9-13`):

```python
def _escape_pgpass(txt):
    """Escape a fragment of a PostgreSQL .pgpass file."""
    return txt.replace('\\', '\\\\').replace(':', '\\:')
```

is a per-code-point substitution: `\\`(92) → `\\\\`(92,92), `:`(58) → `\\:`(92,58),
every other code point identity. (Order matters in the real helper — backslash
first, then colon — but since the colon pass never introduces a backslash that
the already-finished backslash pass would double, and the backslash pass never
introduces a colon, the composite is exactly the per-code-point map above; G-AX
confirms `pgpass_quote_seq == _escape_pgpass` on boundary + fuzz.) This fold is
used only in `model_prepatch.py` (the pre-patch buggy skeleton); the post-patch
`model.py` exposes the password **verbatim**, so it does not apply the fold.

### 3.2 No consumed axiom
`model.py`'s proof consumes no `@ContractOnly`. The post-patch behaviour is a
verbatim copy of the password into the child environment — `str(passwd)` — which
is the identity on the code-point carrier and is spelled out directly in the
impl loop. The only stdlib call the patch *introduces* (`os.environ.copy()` /
`subprocess.run(..., env=...)`) does not transform the password value: the
tests observe `env.get('PGPASSWORD')`, which is exactly the value assigned. No
axiom about `subprocess`/`os` is needed (or shipped).

**Soundness check (G-AX):** `axiom_check.py` reproduces the removed
`_escape_pgpass` verbatim and asserts (a) the deep model `pgpass_quote_seq`
equals it on 15 boundary + 20000 fuzz inputs (the A-reference), and (b) the
post-patch exposed value equals the password verbatim on the same inputs (the
spec core), plus the colon/backslash witnesses where legacy quoting and
verbatim diverge — exactly the F2P behaviour change. Exit 0 iff sound. It
imports only the standard library.
