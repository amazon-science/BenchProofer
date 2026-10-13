# mapping.md — pallets__flask-5014

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7ee9ceb71e868944a46e1ff00b506772a53a4f1d`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `src/flask/blueprints.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validate_name(name, import_name)` | `Blueprint.__init__(self, name, import_name, ...)` — `src/flask/blueprints.py:172` (the name-validation control flow, body lines 185–194) | the modeled changed function: the constructor's name-validation prologue |
| `init_base(import_name)` *(axiom — A-consumed)* | `Scaffold.__init__(self, import_name, ...)` invoked via `super().__init__(...)` — `src/flask/scaffold.py:76`, called from `blueprints.py:185` | unchanged base initialiser the constructor delegates to before validating the name |
| `base_init_can_complete(import_name)` *(axiom — A-reference)* | "the unchanged base init is able to complete as a unit on this `import_name`" — `super().__init__` → `Scaffold.__init__` → `get_root_path` → `pkgutil.get_loader` returning a path (`scaffold.py:76`/`helpers.py:562`) | pure ATTAINABILITY witness over `import_name`, handed out only by the base call's normal exit; carried by every exit of `validate_name` that ran the name guards |
| `base_init_can_fail(import_name)` *(axiom — A-reference)* | "the unchanged base init is able to fail as a unit on this `import_name`, before any name check" — the same chain raising (`ImportError`/`RuntimeError`/`AttributeError`) | pure ATTAINABILITY witness over `import_name`, handed out only by the base call's failure exit; it is **not** the negation of `base_init_can_complete` (§3.2), and demanding it is what stops a name rejection being routed through the base-init channel |
| `contains_dot(s)` | the `"." in name` membership test — `src/flask/blueprints.py:193` | pure spec: does the name contain the dot code point U+002E |
| `NameValidationError` | the `ValueError` raised at `blueprints.py:191` (post-patch empty check) and `blueprints.py:194` (dot check) | user-defined exception modelling the validation failure |
| `BaseInitError` | the `ImportError`/`RuntimeError` the unchanged base init can raise via `super().__init__` → `Scaffold.__init__` → `get_root_path` → `pkgutil.get_loader` (`helpers.py:562`) on an unresolvable `import_name` | user-defined exception modelling the base-init failure-as-a-unit before name validation |

The repo line the patch ADDS (for the refinement audit; not referenced from the
consumer spec view): a guard `if not name: raise ValueError("'name' may not be
empty.")` inserted between `super().__init__(...)` (`blueprints.py:185`) and the
pre-existing `if "." in name:` dot check (`blueprints.py:193`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `name: str` (the blueprint name argument) | `List[int]` of Unicode code points | `name[k]` ↔ `ord(real_name[k])`; `len(name)` ↔ `len(real_name)`; an empty `str` (`""`) ↔ the empty list `[]` (`len == 0`) |
| `name` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(name)` materialises the list; `PSeq` `len`/`[i]`/`drop` mirror `str` `len`/index/suffix-slice |
| `import_name: str` (passed straight to the base initialiser) | `List[int]` of code points | same code-point bijection; only its presence/permission matters here, never its contents |
| `not name` (Python truthiness of a `str`) | `len(name) == 0` | a `str` is falsy **iff** it is the empty string; for the `str` carrier the only falsy value is `""`, i.e. zero code points. (mapping note: `name` is always a `str` at this call — the F2P/P2P tests pass `str` literals.) |
| `"." in name` (substring/membership on `str`) | `contains_dot(ToSeq(name))` — `46 ∈ name` | `"." in name` for the single-character needle `"."` is exactly "the code point 46 occurs in `name`"; the front-recursive fold `contains_dot` decides that membership. |
| `raise ValueError(msg)` | `raise NameValidationError()` + `Exsures(NameValidationError, …)` | a builtin-exception `Exsures` crashes the Nagini translator (probe `p_exsures.py`), so the single `ValueError` raised by both guards is modelled by one user-defined exception class (probe `p_exsures2.py` verifies this pattern). The harness/test only observes *that a `ValueError` is raised*, not its message or subtype. |
| base-init failure: `super().__init__(...)` → `get_root_path` → `pkgutil.get_loader` raises `ImportError`/`RuntimeError`/`AttributeError` on a relative/unresolvable/path-less `import_name` | `BaseInitError` + `Exsures(BaseInitError, … and base_init_can_fail(ToSeq(import_name)))` on both `init_base` and `validate_name` | same translator constraint as above — the builtin `ImportError`/`RuntimeError`/`AttributeError` is modelled by one user-defined exception class. **The model's exception classes are keyed to the STEP that failed, not to the Python type:** `BaseInitError` = "the base step failed as a unit before any name check". That is measurable because the base step never raises `ValueError` — over ~4050 `import_name` shapes with an accepted name (empty/space/dotted/relative/non-ASCII/absent/builtin/300-char + 4000 fuzz) the only failure types observed were `ImportError` (2569), `RuntimeError` (2, e.g. `sys`, `builtins`) and `AttributeError` (2, `typing.io`, `typing.re`); zero `ValueError`. So a `ValueError` from the prologue is unambiguously a name-guard rejection. |
| the two exit channels cannot be swapped: `ValueError` (name reject) fires only *after* `super().__init__` returns; `ImportError`/`RuntimeError` (base-init) fires *instead of* reaching the name checks | `Exsures(NameValidationError, … base_init_can_complete(import_name) and (len==0 or dot))` vs `Exsures(BaseInitError, … base_init_can_fail(import_name))` | the name guards in `Blueprint.__init__` run strictly *after* `super().__init__(...)` returns, so a `ValueError` (NameValidationError) can only arise where the base step COMPLETED and therefore carries the success witness; the base-init channel demands the FAILURE witness, which only a base call that actually failed hands out. The discrimination is by **provenance of the witness**, not by the two witnesses excluding each other — they do not (§3.2), because the real outcome for one `import_name` is not a function of `import_name`. Faithful to the real control flow and required by the `pytest.raises(ValueError)` F2P/P2P. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `init_base` ↔ `Scaffold.__init__` (A-consumed)
**Callee:** `Scaffold.__init__` (`src/flask/scaffold.py:76`), invoked by
`Blueprint.__init__` as `super().__init__(import_name=import_name, ...)` at
`src/flask/blueprints.py:185`, BEFORE any name validation. It is **unchanged by
the patch** (the gold diff touches only `blueprints.py`).

Reading its body (`scaffold.py:76`–end) STEP BY STEP: (S1) `self.import_name =
import_name` (`scaffold.py:86`); (S2) the `static_folder` / `static_url_path`
property setters; (S3) `self.template_folder`; (S4) **`if root_path is None:
root_path = get_root_path(self.import_name)`** (`scaffold.py:96–97`); (S5)
`self.root_path = root_path`; (S6) `self.cli = AppGroup()`; (S7) the empty
registries (`view_functions`, `error_handler_spec`, the deferred/url maps). Only
S4 can fail, and it is the only step that consults anything outside its
arguments. Its callee `get_root_path(import_name)` (`helpers.py:562`) has six
legs, and the CONSULTED TABLE is `sys.modules` (plus `sys.path`/the filesystem
through `pkgutil`):

  * **B1** `mod = sys.modules.get(import_name)`; if it has a non-`None`
    `__file__`, return its directory (`helpers.py:572–575`) — completes;
  * **B2** `loader = pkgutil.get_loader(import_name)` (`helpers.py:578`) — RAISES
    `ImportError` for a relative/unresolvable dotted name (`"."`,
    `"no.such.package"`) and `AttributeError` for `"typing.io"`/`"typing.re"`;
  * **B3/B4** `loader is None or import_name == "__main__"` → `os.getcwd()`
    (`helpers.py:583–584`) — completes (this is the leg an *absent* top-level
    name takes);
  * **B5** `loader.get_filename(import_name)` (`helpers.py:586–587`) — completes;
  * **B6** otherwise `__import__(import_name)`, then
    `sys.modules[import_name].__file__` (`helpers.py:590–592`) — **this leg
    WRITES the consulted table**, and if `__file__` is `None` (a namespace
    package, or `sys`/`builtins`) it RAISES `RuntimeError` (`helpers.py:597–599`).

Every failing leg (B2, B6) fails as a unit *before* any name check, so all of
them fold into the model's single `BaseInitError` channel; every completing leg
(B1, B3/B4, B5, and S4 skipped entirely when `root_path` is supplied) folds into
the normal-completion channel. Crucially:

  * it never inspects, validates, or raises on the blueprint **`name`**
    argument — `name` is not even a parameter of `Scaffold.__init__`; but
  * it is **NOT unconditionally terminating.** When `root_path is None` (the
    default at the `Blueprint.__init__` call site, `blueprints.py:185`) it runs
    `root_path = get_root_path(self.import_name)` (`scaffold.py`, the
    `if root_path is None:` block). `get_root_path` (`helpers.py:562`) calls
    `pkgutil.get_loader(import_name)`, which **raises** (e.g. `ImportError`) on
    a relative/unresolvable dotted `import_name` such as `"."`, `".."`,
    `"no.such.package"`, and `get_root_path` itself can raise `RuntimeError`
    for a namespace package with no file path. So on some `import_name` the
    real base initialiser **fails as a unit** — *before* any name check runs.

Hence for the *name-validation* behaviour under spec, `Scaffold.__init__` is an
opaque callee that is independent of `name`, touches no state this
specification observes, and either completes or fails as a unit before any name
check. The axiom is therefore the **weakest sound** contract (SPEC_GUIDE
directive 7 — never stronger than the real callee): it requires only fractional
permission on `import_name` (`Acc(list_pred(import_name), 1/2)`) and gives TWO
posts — `Ensures(Acc(...) and base_init_can_complete(ToSeq(import_name)))` for
normal completion **and** `Exsures(BaseInitError, Acc(...) and
base_init_can_fail(ToSeq(import_name)))` for the failure-as-a-unit path. Each
post hands out its OWN witness (§3.2) and neither witness is the negation of the
other, so the contract does not decide which exit the real callee takes on a
given `import_name` — it cannot, because the real callee does not decide that
from `import_name` either (§3.2). This is the **weakest sound** contract over the
*value* side that still removes the channel ambiguity the un-pinned (value-free)
Exsures permitted: a name rejection cannot be discharged through the
BaseInitError post, because the reject decision runs only after `init_base`
returned, and the only witness in scope there is the SUCCESS one — the failure
witness is obtainable exclusively from a base call that actually failed. It does NOT
over-claim unconditional normal termination (the earlier Ensures-only axiom did,
which was strictly *stronger* than the real callee — the textbook unsound
over-approximation the G-AX gate exists to catch; the panel's minimal
counterexamples were `"."`, `".."`, `"no.such.package"`). It says nothing about
`name`, so it cannot mask or pre-empt the name check; on failure it propagates,
which `validate_name` re-raises via `Exsures(BaseInitError, …
base_init_can_fail(import_name))` — faithful to
the real constructor aborting before name validation. (Note: the F2P/P2P tests
all pass the resolvable `__name__` as `import_name`, so the raise path is never
hit by the oracle and the gold patch resolves — this over-claim was latent, not
test-observable; it is corrected here so the axiom is sound on its full
`Requires` domain.)

**Why A-consumed (not A-reference):** the proof *consumes* this axiom's posts —
the call `init_base(import_name)` either returns normally (giving back the
`import_name` permission for the subsequent guards and the normal postconditions)
or raises `BaseInitError`, which `validate_name` propagates under its own
`Exsures(BaseInitError, …)`. Both posts are genuinely consumed: removing
`validate_name`'s `Exsures(BaseInitError, …)` while `init_base` may raise makes
the proof FAIL ("method only raises exceptions of type NameValidationError"),
confirming the weaker axiom is load-bearing. The proof does not spell out
`Scaffold.__init__` deeply; it relies on the contract.

**Soundness check (G-AX):** `axiom_check.py` (imports only `flask` + stdlib;
runs in the instance container) checks two split obligations and exits 0 iff
both hold:

  * **(A) the `init_base` axiom** — it fuzzes the AXIOM'S OWN argument: an
    arbitrary `import_name` (the panel CEs `"."`, `".."`, `"no.such.package"`,
    relatives, plus 2000 dotted fuzz names) while holding the blueprint `name`
    at a fixed *accepted* value, and runs the real base init (real
    `super().__init__` → `Scaffold.__init__` → `get_root_path`). It observes
    that the real callee **returns** on resolvable `import_name` (the `Ensures`
    post) and **raises** (`ImportError`) on unresolvable dotted `import_name`
    (the `Exsures(BaseInitError)` post); both are permitted outcomes of the
    weakened axiom, and the checker asserts the raise path is actually
    reachable. This exercises the input domain the *previous* checker missed —
    it fuzzed only the validation `name` while always passing the resolvable
    `__name__` as `import_name`, so it never touched the axiom's real claim. A
    probe that forces the OLD `Ensures`-only claim (base init "must always
    return") FAILS here with `ImportError("Relative module name '.' not
    supported")` on `import_name="."`, so this checker would have caught the
    original over-claim.
  * **(B) the empty/dot validation decision** — empty names and dotted names
    raise `ValueError`; non-empty dot-free names construct successfully, over
    boundary + 20000 fuzz names with a resolvable `import_name`. The empty-name
    rejection is a POST-patch behaviour, so it is asserted against whichever
    tree is mounted (the checker DETECTS the tree: post-patch rejects `""`,
    `base_commit` accepts `""`), making the checker correct whether or not the
    orchestrator applies the gold patch.

### 3.2 `base_init_can_complete` / `base_init_can_fail` ↔ the base init's two attainable outcomes (A-reference)
**Referent:** the two outcomes of running the unchanged base initialiser on this
`import_name` — `super().__init__` → `Scaffold.__init__` → (`root_path is None` at
the call site, `scaffold.py:96`) `get_root_path(import_name)` — namely completing
as a unit (legs B1/B3/B4/B5 of §3.1) and failing as a unit before any name check
(legs B2/B6).

**Why these are two INDEPENDENT witnesses and not one predicate.** The outcome is
**not a function of `import_name`**. It is a function of `import_name` *together
with* (a) the ambient module table `sys.modules`, which leg B6 itself WRITES via
`__import__` (`helpers.py:590`), and (b) the `root_path` argument of the modeled
constructor (`Blueprint.__init__(..., root_path=None)` →
`Scaffold.__init__(..., root_path=...)`), which skips S4 entirely when supplied.
Neither is carried by this specification. Measured on the patched tree in the
instance container, with the blueprint name held at an accepted value:

| `import_name` | perturbation | outcome |
|---|---|---|
| `"zzns5014"` (a namespace package on `sys.path`) | before `import zzns5014` | completes (leg B3/B4 → `os.getcwd()`) |
| `"zzns5014"` | after `import zzns5014` | fails, `RuntimeError` (leg B6, `__file__` is `None`) |
| `"no.such.pkg5014"` | `root_path=None` | fails, `ImportError` (leg B2) |
| `"no.such.pkg5014"` | `root_path="/tmp"` | completes (S4 skipped) |

So a single predicate `p(import_name)` deciding the channel would be UNFAITHFUL:
for `"zzns5014"` and for `"no.such.pkg5014"` the real callee takes BOTH channels.
Instead each exit of `init_base` hands out its own `@Pure @ContractOnly`
attainability witness — `base_init_can_complete` on the normal exit,
`base_init_can_fail` on the failure exit — and **nothing in the spec says the two
exclude each other**; both may hold for one `import_name`, exactly as measured.
Both witnesses are stated over the base callee's own argument only, which is sound
because the base init never reads the blueprint `name` (it is not even a parameter
of `Scaffold.__init__`).

**Why they are needed (the channel pin).** Without them, `validate_name`'s
`Exsures(BaseInitError, …)` was value-free, so an implementation that raised
`BaseInitError` *on the name-reject set* (after `init_base` had already returned)
type-checked against it — a control-flow effect invisible to the value side. Its
faithful real patch (raise `ImportError`/`RuntimeError` on an empty/dotted name)
would FAIL the `pytest.raises(ValueError)` F2P `test_empty_name_not_allowed` and
P2P `test_dotted_name_not_allowed` — a verify-not-resolve break. The witnesses
close that channel by PROVENANCE rather than by exclusion: the name guards run
only after `init_base` RETURNED, so the reject exits carry
`base_init_can_complete`, while the `BaseInitError` exit demands
`base_init_can_fail`, a fact only a base call that actually failed produces. A
synthesized `BaseInitError` on the reject set therefore cannot be discharged —
and, unlike the exclusion argument, this reasoning never asserts anything false
about the real callee.

**Why A-reference (not A-consumed):** neither witness is ever *called* in the
impl; they appear only inside the contracts (the posts of `init_base` and
`validate_name`). Their faithfulness — each is attainable on the real callee, both
are silent about the blueprint `name`, and they are genuinely INDEPENDENT — is
validated against the real callee by G-AX / `axiom_check.py` and the PBT axiom
lane: `ax-init-base-sound` witnesses each channel on the real base init, asserts
name-silence, and asserts the independence by exhibiting `import_name`s on which
the real base init does BOTH (via the `root_path` route and via the ambient module
table); `ax-init-base-name-indep` confirms the name-silence on a resolvable
`import_name`.
