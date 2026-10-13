# refinement.md — django__django-15851

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `buildShellArgs` `do` block plus the pure `builtArgs`/`dbnameToken` models)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized/deep-modeled callee — none here), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The argument-vector assembly — `settings_to_cmd_args_env()`

Gold hunk (`django/db/backends/postgresql/client.py:35–37`):
```
+        args.extend(parameters)
         if dbname:
             args += [dbname]
-        args.extend(parameters)
```
i.e. the `args.extend(parameters)` step is moved to run **before** the
`if dbname: args += [dbname]` block, so the extra parameters precede the
database name and the database name is last.

| # | Solution.lean impl op (`buildShellArgs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `leading : List String` (`let mut args := leading`) | the `args` list as built up through `args = [cls.executable_name]` and the `-U/-h/-p` option-flag blocks (`client.py:11,29–34`), unchanged by the patch | R + I | `list[str] ↔ List String` (mapping.md §2); this segment is built by unchanged code and read here as the starting vector. G-CONF reconstructs it from the real `settings_dict`. |
| A2 | `args := args ++ parameters` | `args.extend(parameters)` (gold line 35, **moved up**) | R + I | `list.extend` ↔ `++` (mapping.md §2). The extend now runs before the dbname token — the heart of the fix. |
| A3 | `args := args ++ dbnameToken dbname` | `if dbname: args += [dbname]` (`client.py:35–36`) | R + I | the optional token: `if dbname: args += [dbname]` ↔ `dbnameToken dbname = dbname.toList` (`some ↦ [s]`, `none ↦ []`) under the `str?`↔`Option String` bijection (mapping.md §2). Now runs after the parameters, so the database name is last. |
| A4 | `return args` | `return args, (env or None)` — the `args` (first) component | R | the F2P test observes the first element of the returned tuple (the argument vector). `env` is unchanged by the patch and not modeled. |

Discriminating content of the change — the **order**: extra `parameters` precede
the database-name token, which is last — lives in `builtArgs leading dbname
parameters = leading ++ parameters ++ dbnameToken dbname`. The pre-patch code
appended the parameters AFTER the dbname token; `Solution_prepatch.lean`
reproduces that (`args ++ dbnameToken dbname ++ parameters`) and **fails**
`args = builtArgs …` precisely on `dbname.toList ++ parameters = parameters ++
dbname.toList` (G-DIFF), the order the F2P `test_parameters` distinguishes
(`["psql", "dbname", "--help"]` → `["psql", "--help", "dbname"]`).

## B. No second site
The patch touches one function and one behaviour; there is one prepatch.

## C. No axioms; no kind-3 (inexpressible-changed-op) steps

Every step is R or I; there are **no A** steps. The changed operation — the
order in which the parameters and the database-name token extend the vector — is
modeled **directly and concretely** (list `++`, `Option.toList`), not behind an
axiom. No unchanged callee's contract is consumed and nothing foreign is
deep-modeled, so the `axioms` region is empty and there are no deep-model
references. G-AX is skipped (mapping.md §3). No operation is left inexpressible.

## D. verify(Solution) ⇒ resolved

`buildShellArgs` verifies only if its output equals `leading ++ parameters ++
dbnameToken dbname` (A2+A3): the extra parameters before the database-name
token, the database name last. By R (`list[str] ↔ List String`, `str?` ↔
`Option String`, `extend`/`+= [dbname]` ↔ `++`/`Option.toList`) the verified
assembly equals the patched `settings_to_cmd_args_env`'s `args` component on the
tested inputs; by G-CONF the R/I transliteration agrees with `patch.diff`'s
behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). There are no axioms, so the only trust point is refinement fidelity
(this doc, G-EQ + G-CONF).
