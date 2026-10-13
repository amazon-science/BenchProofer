# mapping.md — django__django-12125

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 89d41cba392b759732ba9f1db4ff29ed47da6a56`, states the type
abstraction, and gives the provenance of each deep-model reference (callee
source + the exact behaviour the deep model is validated against).

Repo file under change: `django/db/migrations/serializer.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `serialize_type(module, simple_name, qualified_name, module_is_builtin)` | `TypeSerializer.serialize(self)` — `django/db/migrations/serializer.py:259` (body lines 260-272) | the modeled changed function (the class-object serializer) |
| `dotted_path(module, qualified_name)` *(deep model — A-reference)* | the post-patch non-built-in return string `"%s.%s" % (module, self.value.__qualname__)` (`serializer.py:272` post-patch) | pure spec: the non-built-in rendering, keyed by the fully-qualified name |
| `import_line(module)` *(deep model — A-reference)* | the lone import `"import %s" % module` of the non-built-in import set `{"import %s" % module}` (`serializer.py:272`) | pure spec: the one accompanying import statement |

The four `serialize_type` parameters bind to the data the real method reads
from `self.value` (the class object being serialized) and its module:

| model.py parameter | real source (`TypeSerializer.serialize`) |
|---|---|
| `module` | `self.value.__module__` (`serializer.py:268`) |
| `simple_name` | `self.value.__name__` — the class's SIMPLE leaf name (used in the built-in branch, line 270; the pre-patch code wrongly used it in the non-built-in branch, line 272) |
| `qualified_name` | `self.value.__qualname__` — the class's FULLY-QUALIFIED name within the module (the dotted chain of every enclosing class). The post-patch non-built-in branch keys the rendering by this (line 272). |
| `module_is_builtin` | the boolean `module == builtins.__name__` (`serializer.py:269`) — true exactly for the built-in namespace |

The pre-patch repo expression the change removes (for the refinement audit, not
referenced from the consumer spec view): the non-built-in return
`"%s.%s" % (module, self.value.__name__), {"import %s" % module}`
(`serializer.py:272`), which used the SIMPLE leaf name `self.value.__name__`
where the post-patch uses `self.value.__qualname__`.

The two special-case rows (`models.Model`, `type(None)`) at `serializer.py:260-265`
and the `hasattr(self.value, "__module__")` guard at line 267 are control-flow
context unaffected by the change; every value the F2P/P2P tests route through
`TypeSerializer` has a `__module__`, so the modeled function takes the module
text and the built-in flag directly (the guard is an `I` step, see
refinement.md §A1).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`module`, `self.value.__name__`, `self.value.__qualname__`, and the rendered fragment) | `List[int]` of Unicode code points | `s[k]` ↔ `cps[k] == ord(s[k])`; `len(s)` ↔ `len(cps)`; `str` concatenation / `%`-splice of whole strings ↔ list `+`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`len`/`[i]` mirror `str` `+`/`len`/index |
| the boolean `module == builtins.__name__` | `module_is_builtin: bool` | identical Python `bool`; selects the branch (`I`) |
| the method's return value, a 2-tuple `(string, imports)` | `Tuple[List[int], List[int]]` — `(fragment, import_line)` | the `string` first element refines as the `str`↔`List[int]` row above. The `imports` set is **either** empty (built-in branch — `set()`, modeled as the empty list, `len(Result()[1]) == 0`) **or** a one-element set `{"import %s" % module}` (modeled as its single member rendered to code points, `Result()[1]`). The set wrapper is the identity on its (≤1) elements for the F2P comparison (`assertSerializedResultEqual` compares `(string, {'import module'})` exactly). |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

### 2.1 `simple_name` vs `qualified_name` — the carrier of the change
For a class declared at module top level, CPython sets `__qualname__ == __name__`
(no enclosing scope). For a class declared INSIDE an enclosing class,
`__qualname__` is `EnclosingChain.leaf` — strictly the simple name with a
non-empty dotted prefix of every enclosing class — while `__name__` is the bare
leaf. (Empirically: `Outer.Inner.__name__ == "Inner"`,
`Outer.Inner.__qualname__ == "Outer.Inner"`.) The model carries the two as
independent `List[int]` inputs because they genuinely differ exactly in the
nested case the issue is about; the spec keys the non-built-in rendering on
`qualified_name`, which is the behaviour the F2P `test_serialize_nested_class`
demands.

## 3. Deep-model references (kind-A-reference — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom**. The whole rendering is the
function under change, so it is modelled **deeply** (spelled out in the `pure`
region and the verified impl), and its equality to the real post-patch
serializer output is validated out-of-band by `axiom_check.py` (G-AX). Two
A-references:

### 3.1 `dotted_path` ↔ the post-patch non-built-in format string (A-reference)
**Callee:** the gold-patch expression `"%s.%s" % (module, self.value.__qualname__)`
(`serializer.py:272` post-patch). This is exactly
`module ++ "." ++ qualified_name`, which is what `dotted_path` encodes
(`module + PSeq(46) + qualified_name`). G-AX reconstructs the real post-patch
`TypeSerializer.serialize` formatting and asserts `dotted_path` reproduces the
string code point for code point, over real class objects: top-level classes
(where `__qualname__ == __name__`), classes nested inside enclosing classes
(where they differ — the central case, including a nested `enum.IntEnum` and a
nested `enum.Enum` mirroring the `NestedEnum`/`NestedChoices` F2P shapes), and
20 000 synthesised classes whose `__module__`/`__qualname__`/`__name__` span
both nested and top-level shapes.

### 3.2 `import_line` ↔ the post-patch import (A-reference)
**Callee:** the post-patch non-built-in import set `{"import %s" % module}` — a
singleton. `import_line` encodes its single element as `"import " ++ module`
(`PSeq(105,109,112,111,114,116,32) + module`). The change does not touch the
import set; G-AX asserts the real post-patch import set has exactly one element
equal to `import_line(module)`.

### 3.3 The built-in branch (modeled, validated identity)
When `module == builtins.__name__` the real code returns `self.value.__name__,
set()` (`serializer.py:269-270`) — the bare simple name and no import. The model
returns `(simple_name, [])` with `len(Result()[1]) == 0`. This branch is
**unchanged** by the patch (built-in types are never nested in user code, so
`__qualname__ == __name__` there); it is included for skeleton faithfulness and
G-AX confirms `real_serialize_type` reproduces it for `int/str/list/dict/...`.

**Soundness check (G-AX):** `axiom_check.py` reconstructs the gold-patch
post-patch formatting (`"%s.%s" % (module, value.__qualname__)` and
`{"import %s" % module}`, plus the built-in `value.__name__, set()`) and runs it
on real class objects, asserting `dotted_path`/`import_line` reproduce the real
string and import code point for code point over explicit nested/top-level/enum/
built-in classes (incl. the F2P nested-enum shapes) + 20 000 fuzz classes. It
imports only the standard library (`builtins`, `enum`, `random`, `string`,
`types`); nothing repo-specific. Exit 0 iff sound.

## 4. F2P coverage note

Both FAIL_TO_PASS tests exercise this single changed function via
`MigrationWriter.serialize → serializer_factory → TypeSerializer` (the value is
a `type`, so `serializer_factory` returns `TypeSerializer`, line 328-329):

* `test_serialize_nested_class` (the direct case) serializes `WriterTests.NestedEnum`
  and `WriterTests.NestedChoices` — classes nested inside the test case class —
  and asserts the rendering is
  `"migrations.test_writer.WriterTests.NestedEnum"` (the full qualified chain)
  with `{'import migrations.test_writer'}`. Pre-patch produced
  `"migrations.test_writer.NestedEnum"` (the bare leaf name) — the bug.
* `test_serialize_numbers` appears in FAIL_TO_PASS as a side effect of the
  test_patch refactor, not because it exercises a second behaviour: the
  test_patch moves the helper class `DeconstructibleInstances` from a local
  scope inside `test_deconstruct_class_arguments` to module top level (so the
  newly-added `test_deconstruct_class_arguments` assertion can serialize it by a
  reachable path). `Money` (the value `test_serialize_numbers` serializes) is a
  module-top-level `decimal.Decimal` subclass routed through
  `DeconstructableSerializer` via its own `deconstruct()`, NOT through
  `TypeSerializer`; the qualname edit does not change its output. The single
  behavioural change under specification is the one `test_serialize_nested_class`
  pins directly: a non-built-in class is rendered with its fully-qualified name,
  not its bare leaf name. G-RESOLVE (gold patch verbatim) is the authority on
  the exact harness verdict for both listed tests.
