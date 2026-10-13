# refinement.md — django__django-15851

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_argv` impl region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — none here), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The argument-vector assembly — `settings_to_cmd_args_env()` (`django/db/backends/postgresql/client.py:11`)

The function builds an ordered argument list `args`. The gold patch changes the
order in which two trailing segments are appended; nothing else in the function
is touched. Gold hunk:

```
         if port:
             args += ["-p", str(port)]
+        args.extend(parameters)
         if dbname:
             args += [dbname]
-        args.extend(parameters)
```

So post-patch the assembly order is:

```
args = [psql] (+ optional -U/-h/-p segments)   # the flag prefix, unchanged
args.extend(parameters)                         # extra args appended NEXT
if dbname: args += [dbname]                      # database name LAST
```

The model abstracts the unchanged flag prefix (program name plus the
`-U/-h/-p` segments built above the hunk) into a single read-only input
`prefix`, the extra arguments into the read-only input `parameters`, and the
optional database-name token into `(has_dbname, dbname)`. The behaviour under
change is purely the ordering of these three segments in the result vector.

| # | model.py impl op (`build_argv`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `prefix: List[int]` | the `args` list as it stands at the `+args.extend(parameters)` line — `[cls.executable_name]` plus the `-U user`, `-h host`, `-p str(port)` segments built by the four `if` blocks above the hunk | R | each command-line token is an opaque string; modelled as one `int` token identity. `List[int]` ↔ `list[str]` element-wise (mapping.md §2). The flag prefix is unchanged by the patch, so it is summarised as a read-only opaque sequence rather than re-derived. |
| A2 | `parameters: List[int]` | the `parameters` argument | R | same token bijection; the caller-supplied extras, passed through verbatim and in order. |
| A3 | `(has_dbname, dbname)` | `dbname = settings_dict.get("NAME")` (with the `if not dbname and not service: dbname = "postgres"` default applied earlier) and the `if dbname:` guard | R | the database name is at-most-one trailing token; the `if dbname:` truth value ↔ `has_dbname`, the token ↔ `dbname`. |
| A4 | first loop: `result = prefix` (append every `prefix[i]` in order) | the prefix already sitting in `args` before the hunk | R / I | copying the unchanged prefix into the result, element-wise in order. Concrete list append; the carrier is `List[int]` (R). |
| A5 | second loop: append every `parameters[j]` in order → `result == prefix ++ parameters` | `args.extend(parameters)` (the `+` line, now BEFORE the dbname block) | I | `list.extend` appends each element in order — exactly the second loop. The element type is the only refinement (R for the carrier); the operation is identical. |
| A6 | `if has_dbname: result.append(dbname)` → `result == prefix ++ parameters ++ [dbname]` | `if dbname: args += [dbname]` (now AFTER the extend) | I | append the single trailing database-name token under the same guard. |

The unchanged `env` dictionary (the function returns `(args, env)`; the `env`
half is built by the `if passwd: …` block below the hunk and is **not touched**
by the patch) is omitted from the model — it is observationally identical
between pre- and post-patch and is not part of the behaviour under change
(mapping.md §2). The F2P test `test_parameters` asserts on the args list order;
the P2P tests that include an env assert the same env in both pre- and
post-patch states.

## B. The discriminating change

The single behavioural change is the **relative order** of the `parameters`
segment and the `dbname` token. Post-patch: `parameters` precede `dbname`
(extras are options, processed by the client; the database name terminates the
option list). Pre-patch: `dbname` preceded `parameters`, so the extras followed
the database name and were silently ignored by the client.

This is pinned by the postcondition

```
Ensures(Implies(has_dbname,
                ToSeq(Result()) == ToSeq(prefix) + ToSeq(parameters) + PSeq(dbname)))
```

`model_prepatch.py` reproduces the pre-patch ordering (`result.append(dbname)`
BEFORE the parameters loop, yielding `prefix ++ [dbname] ++ parameters`) and
**fails** exactly this postcondition — the spec sensing the change (G-DIFF).
The no-dbname postcondition (`Result == prefix ++ parameters`) is unchanged by
the ordering bug and holds in both, matching the P2P cases with no `NAME`
(`test_service`).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The changed operation — the segment ordering in a
list — is concrete list construction, expressed directly with `list.append` and
`PSeq` concatenation in the postcondition; nothing is hidden behind an axiom and
no library callee participates in the change. There are therefore **no axioms**
(neither A-consumed nor A-reference) and no `axiom_check.py`.

## D. verify(model) ⇒ resolved

`build_argv` verifies only if its output equals `prefix ++ parameters ++
[dbname]` when a database name is in effect (A5+A6, clause B) and `prefix ++
parameters` otherwise. By R (string token ↔ `int` identity; `list.extend` /
`list +=` ↔ the append loops; the omitted, unchanged `env`) the verified vector
equals the post-patch `args` of `settings_to_cmd_args_env` on the tested inputs.
The gold patch produces exactly this ordering and resolves (G-RESOLVE). The
only trust point is refinement fidelity (this document, G-EQ); there is no axiom
soundness obligation because the bundle consumes no axiom.
