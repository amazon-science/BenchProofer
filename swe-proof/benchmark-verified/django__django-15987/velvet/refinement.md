# refinement.md — django__django-15987

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `detectCollision` `do` block and the `matchesText` deep model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none in this bundle), or **I** (identical concrete
op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The membership site — `fixture_dirs` duplicate check (`loaddata.py:370`)

Gold hunk:
```
-            if app_dir in fixture_dirs:
+            if app_dir in [str(d) for d in fixture_dirs]:
                 raise ImproperlyConfigured(
                     "'%s' is a default fixture directory for the '%s' app ..."
```

| # | Solution.lean impl op (`detectCollision`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `target : List Char` | `app_dir` (`str`) — `os.path.join(app_config.path, "fixtures")` | R | `str ↔ List Char` (mapping.md §2). G-CONF bridges via `app_dir` produced by `os.path.join`. |
| A2 | parameter `entries : List Entry`, each `Entry.text = str(d)`, `Entry.wrapped = isinstance(d, Path)` | `fixture_dirs` (`settings.FIXTURE_DIRS`), elements `str` or `Path` | R | each element `d ↦ Entry.mk (str d).toList (wrapped?)` (mapping.md §2). The element-wise `str(d)` coercion the fix adds is the projection to `Entry.text` — an R-refinement, **not** an axiom. |
| A3 | result is `matchesText target entries`: the disjunction over `Entry.text == target`, computed by the backward `while` fold | `app_dir in [str(d) for d in fixture_dirs]` | I | the membership is modeled **directly**: `matchesText`/`Entry.text` and the verified loop ARE the text-only `in` test over the coerced sequence. The fold ops (`e.text == target`, `||`, the loop) are **I** (concrete, transliterated by G-CONF). No callee is axiomatized. |
| A4 | `out : Bool` returned | the `if … :` decides whether `raise ImproperlyConfigured(...)` fires | R | the boolean drives the raise; `test_..._as_pathlib` observes the raise iff the collision is detected. `mark_safe`/wrappers absent — pure boolean. |
| A5 | **total correctness** (`loom.semantics.termination "total"`, loop `decreasing i`) | the Python `in` membership over a finite list always terminates | I | the real comparison site is a bounded scan of `fixture_dirs`; the verified loop must *prove* termination (`decreasing i`), so a non-terminating impl (e.g. a loop that never decrements) cannot satisfy the contract — matching the real code, which cannot hang here. |

Discriminating content of the change — a configured entry held as a structured
path object (`Path`) must still register as a duplicate by its textual value —
lives in `matchesText` comparing on `Entry.text` (which equals `str(d)`)
regardless of `Entry.wrapped`. The pre-patch `app_dir in fixture_dirs` compares
the `str` `app_dir` to raw elements, and in Python `str == Path` is always
`False`, so a `Path` duplicate is missed. `Solution_prepatch.lean` reproduces
that (the skeleton matches only `wrapped = false` entries) and **fails**
`out = matchesText target entries` (G-DIFF): the unsolved goal is precisely the
`!wrapped && …` guard diverging from the text-only `matchesText`.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — extending the
membership comparison to canonical textual renderings via `str(d)` — is modeled
**directly** (the spelled-out fold `matchesText` over `Entry.text`, step A3, an
I; with the element-wise coercion captured as the R-projection of A2), not
hidden behind an axiom. There are **no consumed axioms** and **no deep-model
A-references**: the only callee, `str(d)`, is a pure language coercion folded
into the R-refinement and validated by G-CONF, so there is no soundness
obligation for G-AX (it skips: no `axiom_check.py`).

## C. verify(Solution) ⇒ resolved

`detectCollision` verifies only if its output equals the text-only membership
`matchesText target entries` (A3) — i.e. a collision is reported exactly when
some entry's canonical text equals `target`, independent of how the entry is
stored. By R (`str ↔ List Char`, `d ↦ Entry` carrying `text = str(d)`) the
verified test equals `app_dir in [str(d) for d in fixture_dirs]` on the inputs
the harness exercises (including `Path` entries — the case the F2P test
`test_fixture_dirs_with_default_fixture_path_as_pathlib` adds). By G-CONF the
R/I transliteration of the fold agrees with `patch.diff`'s behaviour on ≥10⁵
mixed `str`/`Path` inputs. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The sole trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there is no axiom-soundness trust point because the bundle consumes no
axioms.
