# refinement.md — django__django-14376

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `selectOverride` `do` block and the deep `resolveWithPrecedence` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** / **A-reference** (axiomatized / deep-modeled callee — none
here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The database-name resolution — `settings_to_cmd_args_env` (`django/db/backends/mysql/client.py:11`)

Gold hunk:
```
- db = settings_dict['OPTIONS'].get('db', settings_dict['NAME'])
+ database = settings_dict['OPTIONS'].get(
+     'database',
+     settings_dict['OPTIONS'].get('db', settings_dict['NAME']),
+ )
  ...
- if db:
-     args += [db]
+ if database:
+     args += [database]
```

| # | Solution.lean impl op (`selectOverride`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `preferredOpt : Option String` | `OPTIONS.get('database', …)` — the preferred key | R | `dict.get` of a maybe-absent key ↔ `Option`; `key present ↔ some`, `absent ↔ none` (mapping.md §2). G-CONF bridges via the `settings_dict['OPTIONS']` dict. |
| A2 | param `secondaryOpt : Option String` | `OPTIONS.get('db', …)` — the deprecated/backward-compat key | R | as A1 (mapping.md §2). |
| A3 | param `baseValue : String` | `settings_dict['NAME']` — the always-present configured name | R | `str ↔ String` (mapping.md §2). |
| A4 | `let viaSecondary := secondaryOpt.getD baseValue` | the inner `OPTIONS.get('db', settings_dict['NAME'])` | I | `dict.get(k, d)` ↔ `Option.getD` on the present/absent carrier; same value selection. |
| A5 | `let out := preferredOpt.getD viaSecondary` | the outer `OPTIONS.get('database', <inner>)` | I | as A4; nests the inner result as the outer default ⇒ preferred-wins-over-secondary-wins-over-base precedence. |
| A6 | `return out` (`String`) | `database`, then `if database: args += [database]` | R | the resolved name is the trailing positional CLI arg; the `if database:`/rename is a local identifier rename, observationally identical to the pre-patch `if db:`/`args += [db]` on the F2P inputs (which always resolve a non-empty name — mapping.md §2 presence-vs-truthiness note). |

Discriminating content of the change — the *preferred* source must win when
present, which the one-level pre-patch fallback never consulted — lives in A5
(`preferredOpt.getD …`). The pre-patch `OPTIONS.get('db', NAME)` ignored the
preferred key entirely; `Solution_prepatch.lean` reproduces that
(`out := secondaryOpt.getD baseValue`, the preferred source never inspected) and
**fails** `out = resolveWithPrecedence preferredOpt secondaryOpt baseValue`
(G-DIFF) — exactly on inputs where `preferredOpt = some v` and the
secondary/base differ, which is what the new "non-deprecated keys preferred"
test exercises.

## B. The connection-kwarg rename — `get_connection_params` (`django/db/backends/mysql/base.py:203,205`)

Gold hunks rename `kwargs['db'] → kwargs['database']` and
`kwargs['passwd'] → kwargs['password']`. This is a pure key rename in a dict
passed to the third-party `Database.connect(**conn_params)` driver. It is
shipped in `patch.diff` (required for G-RESOLVE) but is **not** modeled and has
**no** `Solution_prepatch_<k>.lean`: no FAIL_TO_PASS or PASS_TO_PASS test
exercises `get_connection_params` (the tests call only
`settings_to_cmd_args_env`), so it is not an independently-observable fixed
behaviour (G-DIFF needs one failing prepatch per such behaviour; site A supplies
it). The rename carries no value-selection logic to refine. Tagged here only for
completeness of the diff↔model audit.

## C. No kind-3 (inexpressible-changed-op) steps

Every modeled step is R or I. The one operation that genuinely *changed* — the
widening of the value-resolution from a one-level to a precedence-ordered
two-level fallback — is modeled **deeply** (the spelled-out `resolveWithPrecedence
= preferredOpt.getD (secondaryOpt.getD baseValue)`, steps A4-A5, all **I**), not
hidden behind an axiom. There are **no consumed axioms** and **no A-reference
deep models of external callees**: the entire computation is over the three
candidate inputs.

## D. verify(Solution) ⇒ resolved

`selectOverride` verifies only if its output equals the precedence selection
`preferredOpt.getD (secondaryOpt.getD baseValue)` (A4-A5), i.e. preferred wins
over secondary wins over base, with presence (not truthiness) deciding. By R
(`dict.get`/maybe-absent-key ↔ `Option`, `str ↔ String`) the verified selection
equals the patched `OPTIONS.get('database', OPTIONS.get('db', NAME))` on the
tested inputs; by G-CONF the R/I transliteration of the nested `Option.getD`
agrees with `patch.diff`'s resolved database name on ≥10⁵ inputs. The base.py
rename (site B) is test-neutral and ships verbatim. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement —
and the gold patch resolves (G-RESOLVE). There are no axioms, so the only trust
point of plan §1.1 in play is refinement fidelity (this doc, G-EQ + G-CONF);
axiom soundness (G-AX) is vacuous (no axioms).
