# refinement.md — pallets__flask-5014

Operation correspondence between the Lean `implementation_construct` skeleton and
the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses
an axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

No axioms are declared or consumed: the validation is modeled deeply with
concrete Lean operations. Every row is **R** or **I**. (G-AX is therefore a skip
stub; the R/I legs are differential-tested by G-CONF.)

## What the gold patch changes

`patch.diff` inserts, into `Blueprint.__init__` (`src/flask/blueprints.py`),
BEFORE the pre-existing dot-character guard:

```python
        if not name:
            raise ValueError("'name' may not be empty.")
```

The OBSERVED behavior it changes is `Blueprint.__init__`'s control flow: an
empty name, which previously fell through to successful construction, now raises
`ValueError`. The Lean impl models that control flow with an early-return
emptiness guard placed before the dot guard.

## `implementation_construct` ↔ `Blueprint.__init__`

| Lean op | patch.diff / base counterpart | tag | note |
|---|---|---|---|
| `if name = "" then return Except.error BPError.emptyName` | `if not name: raise ValueError("'name' may not be empty.")` — ADDED by patch | R | Python falsiness of an empty `str` ↦ `name = ""`; `raise ValueError(…)` ↦ early `return Except.error BPError.emptyName`. This is the patched line. |
| `if name.contains '.' then return Except.error BPError.dottedName` | `if "." in name: raise ValueError("'name' may not contain a dot '.' character.")` | I/R | unchanged by patch; `"." in name` ↦ `name.contains '.'` (single-char membership); the raise ↦ early `return Except.error BPError.dottedName`. Carried so the spec frames the full validation. |
| `let st : BPState := { name := name }` | the object under construction (touched field only) | I | accumulator init for the success carrier |
| `return Except.ok st` | `self.name = name` then return from `__init__` | R | the constructed blueprint's touched field ↦ `Except.ok BPState`. `super().__init__(...)` and the other attribute assignments (`url_prefix`, `subdomain`, …) are unchanged by the patch and orthogonal to the name-validation observable, so they are abstracted out of the modeled state — not ops in the skeleton. |

The result carrier `Except BPError BPState` captures the precise observable the
F2P test `test_empty_name_not_allowed` asserts: `Blueprint("", __name__)` must
RAISE `ValueError` — i.e. land in the `Except.error BPError.emptyName` branch —
whereas at base_commit it constructed successfully.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: encodes the base_commit control flow (only the
  dot-character guard; no emptiness guard). The carried gold proof of
  `correct_construct` fails to close precisely on the empty-name case — the spec
  demands `Except.error BPError.emptyName` there, the buggy impl yields
  `Except.ok { name := "" }`. That is the exact FAIL_TO_PASS behavior
  (`test_empty_name_not_allowed`). A single prepatch suffices: the patch adds a
  single guard governing a single observable, and it is discriminated by the
  empty-name input.
