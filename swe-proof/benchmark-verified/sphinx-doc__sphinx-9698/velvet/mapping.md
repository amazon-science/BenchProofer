# mapping.md — sphinx-doc__sphinx-9698

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f050a7775dfc9000f55d023d36d925a8d02ccfa8`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance.

Repo file under change: `sphinx/domains/python.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `indexEntryText (name modname : List Char) (addModuleNames : Bool) (kind : MethodKind)` | `PyMethod.get_index_text(self, modname, name_cls)` — `sphinx/domains/python.py:784` (changed branch at `:799`) | the modeled changed function: builds the index-entry label for a documented member |
| `indexText` *(pure)* | the full body of `get_index_text` (`python.py:785–804`) | pure spec of the label the function computes |
| `rsplitDot` *(pure)* | `name.rsplit('.', 1)` + the `try/except ValueError` (`python.py:786,790`) | split a qualified name at its last `.`; `none` ⇔ the `ValueError` (no separator) branch |
| `shownOwner` *(pure)* | `if modname and self.env.config.add_module_names: clsname = '.'.join([modname, clsname])` (`python.py:787–788`) | the owner shown in the label, module-prefixed when configured |
| `MethodKind` *(pure)* | the resolved option among `'classmethod' / 'property' / 'staticmethod' / (else)` in `self.options` (`python.py:796–804`) | the category the member is classified under |

**No axiomatized callees.** Every operation in `get_index_text` is a concrete
string computation (`rsplit`, `'.'.join`, `%`-format with literal templates).
Nothing is delegated to an *unchanged* callee whose contract the proof would
consume, so there is no `axiom` and no A-reference. The `_(...)` gettext wrapper
is the identity translation under the test harness's no-catalog default (see §3);
it alters no character content the F2P test observes and is modeled as identity.

The four category flags are mutually exclusive **as consumed here**: the real
`if/elif` chain (`python.py:796–803`) applies a fixed precedence
`classmethod > property > staticmethod > (plain method)`, selecting exactly one
template. `MethodKind` carries that single resolved category; the precedence
itself is unchanged by the patch and is not re-modeled (mapping.md is the audit
record that one flag is the faithful input — G-CONF sets exactly one flag).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `name` / `modname` / the returned label (`str`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat / `%`-fill ↔ `List` `++`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `self.env.config.add_module_names` (`bool`) | `Bool` (`addModuleNames`) | `True` ↔ `true`, `False` ↔ `false` |
| the resolved category in `self.options` | `MethodKind` | `'classmethod'`↔`classMethod`, `'property'`↔`propertyKind`, `'staticmethod'`↔`staticMethod`, none-of-these ↔ `instanceMethod` |
| `name.rsplit('.', 1)` → 2-list / `ValueError` | `rsplitDot : List Char → Option (List Char × List Char)` | a 2-element split (separator present) ↔ `some (owner, member)`; the `ValueError` (no `.`) ↔ `none`. Splits at the **rightmost** `.`: `'A.B.C'` ↔ `some ("A.B", "C")`, `'.bar'` ↔ `some ("", "bar")`, `'Class.'` ↔ `some ("Class", "")`, `'bar'` ↔ `none`. |
| `_('...') ` gettext wrapper (`python.py:797…`) | identity (omitted) | under no message catalog `_` is the identity translation; it changes no character content the F2P `test_pymethod_options` observes. Identity on `List Char`. |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the operation is a per-character string build.

## 3. Callee provenance (kind-A) — none

There are **no** kind-A callees: no `axiom`, no `:|`-stub, no A-reference. The
`get_index_text` body computes the label purely from its inputs. Consequently
there is **no `axiom_check.py`** and G-AX is `skip` (mapping.md is the audit
record that no callee contract is consumed — consistent with the no-axiom
exemplars `django__django-11138`, `django__django-11400`).

`_(...)`: `sphinx.locale._` is `get_translation('sphinx')`; with no installed
catalog (the unit-test default — `test_pymethod_options` builds a bare app) it
returns its argument unchanged, so `_('%s (%s property)') % (m, c)` is exactly
the `%`-substituted literal. The oracle in `conformance_check.py` invokes the
*real* function, so any catalog effect would be captured oracle-side; running it
under the same no-catalog default keeps the differential test about the format
template — the only thing the patch changes.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`9698`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `rsplitDot` / `shownOwner` / `indexText` (all R/I-tagged ops) to
Python; there are no A-tagged callees to leave real. The oracle is the patched
`PyMethod.get_index_text` run at base_commit with a minimal fake env.
