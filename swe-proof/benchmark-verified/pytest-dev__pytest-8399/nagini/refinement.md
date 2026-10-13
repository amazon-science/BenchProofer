# refinement.md — pytest-dev__pytest-8399

The operation-by-operation correspondence between `model.py`'s implementation
(the `generated_fixture_name` impl region, plus the deep `listed` /
`begins_private` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == the real callee/logic by
axiom_check.py / G-AX, NOT consumed), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The five name-construction sites (one modeled function, repeated hunk)

The gold patch is five identical hunks: each prepends `_` to a generated-fixture
name f-string. Base → fixed:

```
src/_pytest/python.py:531   -  name=f"xunit_setup_module_fixture_{self.obj.__name__}",
                            +  name=f"_xunit_setup_module_fixture_{self.obj.__name__}",
src/_pytest/python.py:560   -  name=f"xunit_setup_function_fixture_{self.obj.__name__}",
                            +  name=f"_xunit_setup_function_fixture_{self.obj.__name__}",
src/_pytest/python.py:812   -  name=f"xunit_setup_class_fixture_{self.obj.__qualname__}",
                            +  name=f"_xunit_setup_class_fixture_{self.obj.__qualname__}",
src/_pytest/python.py:841   -  name=f"xunit_setup_method_fixture_{self.obj.__qualname__}",
                            +  name=f"_xunit_setup_method_fixture_{self.obj.__qualname__}",
src/_pytest/unittest.py:147 -  name=f"unittest_{setup_name}_fixture_{obj.__qualname__}",
                            +  name=f"_unittest_{setup_name}_fixture_{obj.__qualname__}",
```

All five share the SAME edit (prepend the privacy marker to the name f-string)
and the SAME observable effect (the listing rule omits the result at default
verbosity). They collapse to one modeled function `generated_fixture_name`,
whose input `label` abstracts the descriptive name f-string at each site (the
`xunit_..._fixture_<name>` / `unittest_..._fixture_<qualname>` string) and whose
output is that label with `_` prepended.

| # | model.py impl op (`generated_fixture_name`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `label: List[int]`, non-empty, `label[0] != 95` | the descriptive name f-string `f"unittest_{setup_name}_fixture_{obj.__qualname__}"` (and the four xunit variants) | R | `str` ↔ `List[int]` code points (mapping.md §2). The f-strings begin with `u`/`x`, never `_`, and are non-empty (the listing rule indexes `argname[0]`) — exactly the model's preconditions. |
| A2 | `result = [PRIVACY_MARKER]` then append each `label[i]` — i.e. `[95] + label` | the textual prefix change `"unittest_..."` → `"_unittest_..."` (likewise `"xunit_..."` → `"_xunit_..."`) | I + R | prepending the literal `"_"` to the f-string IS prepending code point 95 to the list (`I` on the operation; `R` on the carrier). The post `ToSeq(Result()) == [95] ++ ToSeq(label)` is exactly "the new name is the old name with `_` in front". |
| A3 | the value returned (a `List[int]`) used by the listing rule via `listed` | the `name=` keyword consumed by `@pytest.fixture(...)`, which the `--fixtures` listing later filters | A-reference | the listing's visibility rule (`python.py:1511`/`:1429`) is **unchanged framework logic** modeled **deeply** as `listed`; there is no consumed axiom. The postconditions `not listed(Result(), 0)` and `listed(Result(), 1)` are discharged from `begins_private(Result())` (which holds because `Result()[0] == 95`). G-AX (axiom_check.py) validates `listed == ` both real rule expressions, and that prepending `_` to a real label flips the real filter shown→omitted at default verbosity. |

## B. Why the postcondition pins the fix (not an oracle)

The behaviour is pinned by **structural predicates on the actual input carrier**,
not an answer key:

* `len(Result()) == len(label) + 1` and `ToSeq(Result()).drop(1) == ToSeq(label)`
  force the result to be exactly the descriptive label with one extra leading
  code point — an impl cannot return a constant, a truncation, or an unrelated
  string. The label is carried through verbatim.
* `ToSeq(Result())[0] == 95` forces that extra leading code point to be the
  privacy marker `_` (not, say, a space or a different separator).
* `not listed(Result(), 0)` / `listed(Result(), 1)` tie the marker to its
  *witnessed structural consequence* under the unchanged listing rule: the
  generated fixture disappears from the default `--fixtures` listing yet
  reappears under `-v`. This is exactly the F2P observation.

`listed` reads its argument structurally (`name[0] == 95`); it is not an opaque
oracle, so a wrong impl cannot echo it.

* `Requires(MustTerminate(len(label) + 2))` makes the contract TOTAL: the real
  name construction is one f-string evaluation that always returns its value to
  the `@pytest.fixture(name=...)` decorator. Without the obligation, Nagini's
  partial-correctness semantics admits an impl that computes the correct
  `'_'`-prefixed name and then diverges before returning it (every `Ensures`
  holds vacuously) — such an impl never registers the fixture, hangs
  collection, and does NOT resolve the F2P. The obligation rejects it: any
  inserted unbounded loop leaks the caller's termination obligation.

## C. G-DIFF — the prepatch fails on the discriminating clause

`model_prepatch.py` keeps the spec byte-identical (axioms+pure+pre+post regions
diff-clean) and reverts the impl to the pre-patch behaviour: the generated name
is the descriptive label **with no leading marker** (`result == label`, mirroring
the base_commit f-strings `f"unittest_..."` without the `_`). It FAILS
verification on the postcondition

```
Postcondition might not hold. Assertion (len(Result()) == (len(label) + 1)) might not hold.
```

— the very clause that asserts the marker is prepended. (It equally violates
`ToSeq(Result())[0] == 95` and `not listed(Result(), 0)`: the un-prefixed label
begins with `u`/`x`, so the listing rule shows it at default verbosity — the
reported bug.) One failing prepatch suffices: all five gold hunks are the
identical edit with the identical observable effect, so they constitute one
independently-fixed behaviour.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The one operation that *changed* — the
generated fixture name gains a leading `_` — is modeled **deeply** (the spelled-
out prepend in `generated_fixture_name`), and the *unchanged* logic that gives
the marker its meaning (the listing's visibility rule) is the **A-reference**
`listed`, validated == the real rule by G-AX. There is **no consumed axiom** and
no stdlib callee: the only repo logic referenced beyond the edit is framework-
internal and unchanged.

## E. verify(model) ⇒ resolved

`generated_fixture_name` verifies only if its output is the descriptive label
with the privacy marker `_` prepended (A2/B), and only if that marker makes the
generated name omitted at default verbosity yet shown at verbose under the
unchanged listing rule (A3/B). By R (str ↔ List[int]) the verified construction
equals the gold f-strings' `"_" + <descriptive>` at all five sites; by G-AX the
deep model `listed` equals the real `--fixtures` visibility rule (A-reference),
so the generated fixtures vanish from the default listing — exactly what the F2P
test `test_fixtures_setup_setUpClass_issue8394` asserts (`result.ret == 0` and
`no_fnmatch_line("*no docstring available*")` under `--fixtures`, and the line
present under `--fixtures -v`). Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement and the audited
unchanged rule — and the gold patch resolves (G-RESOLVE). The single trust point
is refinement fidelity (this document, G-EQ) plus the G-AX-validated A-reference;
there is no consumed-axiom trust point.
