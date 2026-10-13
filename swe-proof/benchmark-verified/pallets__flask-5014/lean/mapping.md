# mapping.md — pallets__flask-5014

Cold construction. Spec derived solely from `problem_statement`, the gold
`patch`, and the repo source at `base_commit`
(`7ee9ceb71e868944a46e1ff00b506772a53a4f1d`). No pre-existing solution consulted.

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_construct` / `problem_spec_construct` / `correct_construct` | `Blueprint.__init__` name-validation + name storage | `src/flask/blueprints.py:172-206` |
| `BPError.emptyName` | `raise ValueError("'name' may not be empty.")` | added by gold patch @ `:193-194` (does NOT exist at base_commit) |
| `BPError.dottedName` | `raise ValueError("'name' may not contain a dot '.' character.")` | `src/flask/blueprints.py:193-194` (base) |
| `BPState.name` | `self.name = name` | `src/flask/blueprints.py:196` |

## The observable behavior

`Blueprint.__init__` is the single function whose behavior the gold patch
changes. At `base_commit`:

```python
def __init__(self, name, import_name, ...):
    super().__init__(import_name=import_name, ...)   # base-class init (untouched)

    if "." in name:
        raise ValueError("'name' may not contain a dot '.' character.")

    self.name = name
    self.url_prefix = url_prefix
    ...
```

The gold patch inserts, BEFORE the dot check:

```python
    if not name:
        raise ValueError("'name' may not be empty.")
```

The directly observable consequence (asserted by the F2P test
`test_empty_name_not_allowed`): constructing a blueprint with an empty name
**raises `ValueError`**. Before the patch an empty name was accepted (it passed
the dot check, since `"" `contains no dot, and was stored as `self.name`); after
the patch it raises. The problem statement: "Require a non-empty name for
Blueprints … It would be helpful if a `ValueError` was raised when trying to do
that."

The `super().__init__(import_name=import_name, ...)` call and the subsequent
attribute assignments (`url_prefix`, `subdomain`, `deferred_functions`,
`url_values_defaults`, `cli_group`, `_blueprints`) are unchanged by the patch
and orthogonal to the name-validation observable. They are abstracted away — the
modeled state carries only the touched field `name`.

## Lean ↔ Python type bijection

| Python | Lean | bijection |
|---|---|---|
| `name: str` argument | `name : String` | identity (value-level string) |
| `not name` (empty test) | `name = ""` | Python truthiness of `str`: empty string is falsy ⇔ `name == ""` |
| `"." in name` (substring/char membership) | `name.contains '.'` | `'.'` occurs in `name`; `str.__contains__` for a single char ⇔ char membership |
| `self.name = name` (successful construction) | `Except.ok { name := name }` | the constructed blueprint's touched field |
| `raise ValueError("'name' may not be empty.")` | `Except.error BPError.emptyName` | the empty-name failure |
| `raise ValueError("'name' may not contain a dot '.' character.")` | `Except.error BPError.dottedName` | the dotted-name failure |

The two `ValueError`s are distinguished into two `BPError` constructors so the
spec pins WHICH failure occurs for WHICH name, and so the empty-name ordering
(empty checked before dot) is observable. Their precedence matches the patched
source: the empty check runs first, so `""` (which contains no dot anyway) maps
to `emptyName`, never `dottedName`.

## Callee provenance / flag deps

- No UNCHANGED callee needs an axiom. The name-validation + field storage is
  modeled DEEPLY with concrete Lean operations (an emptiness test
  `name = ""`, a dot-membership test `name.contains '.'`, an early `return`
  raise, and a field assignment). → `axioms` region is EMPTY; `axiom_check.py`
  is a skip stub.
- `super().__init__` (base-class storage of `import_name`/folders/`root_path`)
  is NOT modeled: it is unchanged by the patch and does not affect the
  name-validation observable. It is neither a consumed axiom nor a reference
  callee — it is abstracted out of the state entirely.
- No flag dependency: both raises are unconditional guards on the name value.

## G-CONF fuzz seed

Pinned seed: **20240612**. `conformance_check.py` enumerates a boundary matrix
of names (empty, dotted, plain, dotted+empty-edge, leading/trailing dot,
whitespace) against the REAL patched `flask.Blueprint` in-container — observing
whether `Blueprint(name, __name__)` raises `ValueError` (and which message) or
constructs (and that `bp.name == name`) — plus ≥10⁵ randomized name draws over
an alphabet including `'.'` and the empty string.
