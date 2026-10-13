# mapping.md — sphinx-doc__sphinx-8721

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 82ef497a8c88f0f6e50d84520e7276bfbf65025d`, states the type
abstraction, and gives the provenance of each deep-model reference (the builtin
it is validated against by G-AX).

Repo file under change: `sphinx/ext/viewcode.py`.

The gold patch installs two early-return guards in `collect_pages`: a
single-file (`name == "singlehtml"`) guard and an electronic-book
(`name.startswith("epub") and not viewcode_enable_epub`) guard. Only the
electronic-book guard is described in the public `problem_statement` ("module
pages should not be created for epub by default") and only it is exercised by
any FAIL_TO_PASS / PASS_TO_PASS test. The model therefore specifies exactly the
tested electronic-book behaviour; the single-file co-change is carried verbatim
by `patch.diff` (the correctness oracle) but is not part of the modeled,
consumer-visible behavioural contract.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `module_source_pages(name, enable_epub, modules)` | `collect_pages(app)` — `sphinx/ext/viewcode.py:181` | the modeled changed function: the `html-collect-pages` handler that yields the highlighted module-source pages |
| `begins_with(name, lit)` | `app.builder.name.startswith("epub")` — `sphinx/ext/viewcode.py:187` (post-patch) | begins-with test gating electronic-book targets |
| `prefix_eq(s, lit)` *(deep model — A-reference)* | `str.startswith` (CPython builtin), as used at the `.startswith("epub")` site | pure spec: literal begins-with; validated `prefix_eq == str.startswith` by axiom_check.py (G-AX), NOT a consumed axiom |
| `suppressed(name, enable_epub)` | the electronic-book gate `name.startswith("epub") and not viewcode_enable_epub` — `sphinx/ext/viewcode.py:187-188` (post-patch) | pure spec: the electronic-book page-suppression predicate the patch installs (the tested discriminator) |
| `lit_epub()` | the string literal `"epub"` | pure spec: the gate literal as a code-point sequence |
| parameter `enable_epub` | `env.config.viewcode_enable_epub` — config value, default `False` (`sphinx/ext/viewcode.py:281`, `app.add_config_value('viewcode_enable_epub', False, False)`) | the electronic-book preference read by the epub gate |
| parameter `modules` | `env._viewcode_modules` entries with truthy `entry` — the per-module source records iterated at `sphinx/ext/viewcode.py:190-194` | the recorded module entries, one element per page that would be produced |
| `Result()` (a `List[int]`) | the sequence of `(pagename, context, 'page.html')` tuples the generator `yield`s | the produced module-source page set |

The pre-patch repo behaviour (for the refinement audit, not referenced from the
consumer spec view): `collect_pages` had no electronic-book (nor single-file)
gate; the body fell straight through from the `_viewcode_modules` guard
(`viewcode.py:183-184`) into the per-module page-emission loop
(`viewcode.py:190-247`), so module pages were yielded for every output target.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `app.builder.name` (a `str`) | `name: List[int]` of Unicode code points | `name[k] == ord(builder_name[k])`; `len(name) == len(builder_name)`; an empty name ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str`/sequence ops |
| `env.config.viewcode_enable_epub` (a `bool`) | `enable_epub: bool` | identity |
| the generator's yielded page set | `modules: List[int]` (page carriers) → `Result(): List[int]` | each yielded page ↔ one element; emitting a page for module *k* ↔ appending `modules[k]`; yielding nothing ↔ the empty list. The tested behaviour is **which / how many** module pages are produced (a page file exists iff a page is yielded), so a per-page integer carrier is faithful for the F2P/P2P observation (`(outdir / '_modules/.../mod1.xhtml').exists()`). The page *content* and the trailing index page are unchanged by the patch and irrelevant to the gate; they are abstracted away. |

`str` indexing/iteration is banned in Nagini, so builder names are carried as
`List[int]`; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model references (kind-A reference — checked by G-AX / axiom_check.py)

There are **no consumed axioms**. The electronic-book string decision the gate
performs is modelled deeply and validated against the real builtin:

### 3.1 `prefix_eq` deep model ↔ `str.startswith` (A-reference)
**Callee:** CPython `str.startswith(prefix)` (the `.startswith("epub")` at the
epub gate). `prefix_eq(s, lit)` is the literal begins-with test: the first
`len(lit)` code points of `s` equal `lit`, and `False` when `s` is shorter than
`lit`. This matches single-argument `str.startswith` (no `start`/`end`
arguments are passed at the call site, so the default whole-string-anchored
behaviour applies). G-AX asserts
`prefix_eq(cps(name), cps("epub")) == name.startswith("epub")` over boundary +
50 000 fuzz builder names. Docs:
https://docs.python.org/3/library/stdtypes.html#str.startswith.

### 3.2 `suppressed` composite ↔ the installed electronic-book gate (A-reference)
The composite predicate
`suppressed(name, enable_epub) = prefix_eq(name,"epub") and not enable_epub`
is validated == the real electronic-book gate
`name.startswith("epub") and not viewcode_enable_epub`
by axiom_check.py over boundary + fuzz, exit 0 iff sound. `viewcode_enable_epub`
defaults to `False` (`viewcode.py:281`), which is why an electronic-book target
suppresses module pages by default — the behaviour the F2P test observes.
