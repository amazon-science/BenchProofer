# refinement.md — operation correspondence (django__django-17087)

Maps every op in `implementation_classMethodRef` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The post-patch Python (this branch of `FunctionTypeSerializer.serialize`) is:

```python
klass = self.value.__self__
module = klass.__module__
return "%s.%s.%s" % (module, klass.__qualname__, self.value.__name__), {
    "import %s" % module
}
```

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let module := m.module` | `module = klass.__module__` | I | attribute read of the defining module, bound to `module` (str ↔ List Char, R-trivial) |
| 2 | `m.ownerQualname` used as the class label | `klass.__qualname__` | I | the post-patch label is the class's fully-qualified name; modeled as the `ownerQualname` field |
| 3 | `module ++ "." ++ ownerQualname ++ "." ++ methodName` | `"%s.%s.%s" % (module, klass.__qualname__, self.value.__name__)` | A-reference | the `%`-format dotted join modeled deeply as char-list concatenation; validated == real `"%s.%s.%s" % (...)` by G-CONF/G-AX |
| 4 | `imports := [importFor module]` | `{"import %s" % module}` | A-reference | the one-element import set modeled deeply as a singleton list of `"import " ++ module`; validated == real `{"import %s" % module}` by G-CONF/G-AX |
| 5 | `return { text, imports }` | `return <str>, <set>` | I | tuple/return of the two assembled components |

No A-consumed rows: the proof discharges the dotted join and import directly via
the deeply-modeled concatenation; no UNCHANGED callee property is assumed. No
changed-inexpressible op — the only changed token (`__name__` → `__qualname__`)
is captured by selecting the `ownerQualname` field instead of `ownerName`.

The discriminating clause is row 2: the class label. The prepatch impl assembles
the path from `m.ownerName` (the bare innermost name), so for a nested-class input
(`ownerQualname` strictly longer than `ownerName`) its `text` differs from the
spec's required `... ++ ownerQualname ++ ...`, and `correct_classMethodRef` cannot
close its first conjunct against the frozen `problem_spec_classMethodRef`. That is
the G-DIFF signal.
