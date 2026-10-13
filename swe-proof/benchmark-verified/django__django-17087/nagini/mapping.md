# mapping.md — django__django-17087

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 4a72da71001f154ea60906a2f74898d32b7322a7`, states the type
abstraction, and gives the provenance of each deep-model reference (callee
source + the exact behaviour the deep model is validated against).

Repo file under change: `django/db/migrations/serializer.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_class_member_reference(module, class_simple_name, class_qualified_name, method_name)` | `FunctionTypeSerializer.serialize(self)` — `django/db/migrations/serializer.py:165` (the class-bound-method branch, body lines 166-173) | the modeled changed function (the serializer path for a callable bound to a class object) |
| `member_path(module, class_qualified_name, method_name)` *(deep model — A-reference)* | the post-patch return string `"%s.%s.%s" % (module, klass.__qualname__, self.value.__name__)` (`serializer.py:171` post-patch) | pure spec: the rendered fragment, keyed by the owning class's fully-qualified name |
| `import_line(module)` *(deep model — A-reference)* | the lone import `"import %s" % module` of the import set `{"import %s" % module}` (`serializer.py:171-173`) | pure spec: the one accompanying import statement |

The four `render_class_member_reference` parameters bind to the data the real method
reads, inside the branch taken when the value is a callable bound to a class
object:

| model.py parameter | real source (`FunctionTypeSerializer.serialize`, class-bound-method branch) |
|---|---|
| `module` | `module = klass.__module__`, where `klass = self.value.__self__` (`serializer.py:169-170`) |
| `class_simple_name` | `klass.__name__` — the owning class's SIMPLE leaf name (the pre-patch code wrongly used it on line 171) |
| `class_qualified_name` | `klass.__qualname__` — the owning class's FULLY-QUALIFIED name within the module (the dotted chain of every enclosing class). The post-patch return keys the rendering by this (line 171). |
| `method_name` | `self.value.__name__` — the bound callable's own attribute name on the owning class (used unchanged in both pre- and post-patch as the third `%s`) |

The branch guard at `serializer.py:166-168`
(`getattr(self.value, "__self__", None) and isinstance(self.value.__self__, type)`)
is control-flow context unaffected by the change; it selects exactly the
class-bound-method case the modeled function covers. The "further error
checking" tail (`serializer.py:174-189`, the lambda / no-module / `<locals>`
guards) is a different, unchanged branch never reached for the tested
class-bound methods, so it is outside the modeled function (an `I` context
boundary, refinement.md §A1).

The pre-patch repo expression the change removes (for the refinement audit, not
referenced from the consumer spec view): the return
`"%s.%s.%s" % (module, klass.__name__, self.value.__name__), {"import %s" % module}`
(`serializer.py:171`), which used the SIMPLE leaf name `klass.__name__` where the
post-patch uses `klass.__qualname__`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`module`, `klass.__name__`, `klass.__qualname__`, `self.value.__name__`, and the rendered fragment) | `List[int]` of Unicode code points | `s[k]` ↔ `cps[k] == ord(s[k])`; `len(s)` ↔ `len(cps)`; `str` concatenation / `%`-splice of whole strings ↔ list `+`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`len`/`[i]` mirror `str` `+`/`len`/index |
| the method's return value, a 2-tuple `(string, imports)` | `Tuple[List[int], List[int]]` — `(fragment, import_line)` | the `string` first element refines as the `str`↔`List[int]` row above. The `imports` set is a one-element set `{"import %s" % module}`, modeled as its single member rendered to code points (`Result()[1]`). The set wrapper is the identity on its one element for the F2P comparison (`assertSerializedResultEqual` compares `(string, {'import migrations.test_writer'})` exactly). |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

### 2.1 `class_simple_name` vs `class_qualified_name` — the carrier of the change
For a class declared at module top level, CPython sets
`__qualname__ == __name__` (no enclosing scope). For a class declared INSIDE an
enclosing class, `__qualname__` is `EnclosingChain.leaf` — strictly the simple
name with a non-empty dotted prefix of every enclosing class — while `__name__`
is the bare leaf. (Empirically confirmed at base_commit's interpreter:
`Outer.Inner.__name__ == "Inner"`, `Outer.Inner.__qualname__ == "Outer.Inner"`;
for a classmethod `Outer.Inner.method`, `method.__self__ is Outer.Inner`, so the
real code reads `klass.__qualname__ == "Outer.Inner"` and `method.__name__ ==
"method"`, rendering `module.Outer.Inner.method`.) The model carries the owning
class's two names as independent `List[int]` inputs because they genuinely differ
exactly in the nested case the issue is about; the spec keys the rendering on
`class_qualified_name`, which is the behaviour the F2P
`test_serialize_nested_class_method` demands.

## 3. Deep-model references (kind-A-reference — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom**. The whole rendering is the
function under change, so it is modelled **deeply** (spelled out in the `pure`
region and the verified impl), and its equality to the real post-patch
serializer output is validated out-of-band by `axiom_check.py` (G-AX). Two
A-references:

### 3.1 `member_path` ↔ the post-patch format string (A-reference)
**Callee:** the gold-patch expression
`"%s.%s.%s" % (module, klass.__qualname__, self.value.__name__)`
(`serializer.py:171` post-patch). This is exactly
`module ++ "." ++ class_qualified_name ++ "." ++ method_name`, which is what
`member_path` encodes (`module + PSeq(46) + class_qualified_name + PSeq(46) +
method_name`). G-AX reconstructs the real post-patch formatting from real
class-bound methods and asserts `member_path` reproduces the string code point
for code point, over: classmethods owned by top-level classes (where
`__qualname__ == __name__`), classmethods owned by classes nested inside
enclosing classes (where they differ — the central case, including a nested
`enum.Enum` subclass mirroring the `NestedChoices` TextChoices F2P shape), and
20 000 synthesised class-bound methods whose owning class's
`__module__`/`__qualname__`/`__name__` span both nested and top-level shapes.

### 3.2 `import_line` ↔ the import (A-reference)
**Callee:** the import set `{"import %s" % module}` — a singleton. `import_line`
encodes its single element as `"import " ++ module`
(`PSeq(105,109,112,111,114,116,32) + module`). The change does not touch the
import set; G-AX asserts the real import set has exactly one element equal to
`import_line(module)`.

**Soundness check (G-AX):** `axiom_check.py` reconstructs the gold-patch
post-patch formatting
(`"%s.%s.%s" % (module, klass.__qualname__, value.__name__)` and
`{"import %s" % module}`, where `klass = value.__self__`) and runs it on real
class-bound methods, asserting `member_path`/`import_line` reproduce the real
string and import code point for code point over explicit nested / top-level /
nested-enum classmethods (incl. the F2P `NestedChoices.method` shape) + 20 000
fuzz class-bound methods. It imports only the standard library (`builtins`,
`enum`, `random`, `string`, `types`); nothing repo-specific. Exit 0 iff sound.

## 4. F2P coverage note

The single FAIL_TO_PASS test exercises this changed function via
`MigrationWriter.serialize → serializer_factory → FunctionTypeSerializer`: the
value `WriterTests.NestedChoices.method` is a `types.MethodType` bound to the
class `WriterTests.NestedChoices`, so `serializer_factory` routes it (via the
`(FunctionType, BuiltinFunctionType, MethodType)` registry row,
`serializer.py:349-353`) to `FunctionTypeSerializer`. Because
`self.value.__self__` is the class `NestedChoices` (a `type`), the
class-bound-method branch (`serializer.py:166-173`) is taken.

* `test_serialize_nested_class_method` serializes `WriterTests.NestedChoices.method`
  — a classmethod owned by a class nested inside the test case class — and
  asserts the rendering is
  `"migrations.test_writer.WriterTests.NestedChoices.method"` (the full
  qualified chain of the owning class) with `{'import migrations.test_writer'}`.
  Pre-patch produced `"migrations.test_writer.NestedChoices.method"` (the owning
  class's bare leaf name) — the bug. Here `module ==
  "migrations.test_writer"`, `klass.__qualname__ == "WriterTests.NestedChoices"`,
  `klass.__name__ == "NestedChoices"`, `self.value.__name__ == "method"`.

G-RESOLVE (gold patch verbatim) is the authority on the exact harness verdict for
the listed test plus the full PASS_TO_PASS set (which includes the unchanged
top-level / `<locals>` / lambda paths of `FunctionTypeSerializer`, all unaffected
because for a top-level class `__qualname__ == __name__`).
