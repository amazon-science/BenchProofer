# Adding a verification backend

A **backend** is one way of specifying and checking behavior. The shipped set
covers an imperative contract language verified by an SMT-backed tool, two
proof-assistant flavors (one where the obligations are discharged automatically
and one where an agent writes the proofs), and a natural-language requirements
format with no verifier at all. That spread is the point: the gate suite, the
construction loop, and the evaluation harness are written against an interface,
not against a prover.

This document says what that interface is and what a bundle in a new backend must
contain. Read [architecture.md](architecture.md) for what the gates are judging;
to point the pipeline at a different *dataset*, see
[adapting_a_benchmark.md](adapting_a_benchmark.md).

## 1. The interface

`src/swebench_unified/backends/base.py`:

```python
class Backend(ABC):
    name: str
    language: LanguageTables

    @abstractmethod
    def check(self, path: Path, timeout: int = 300) -> VerifyResult: ...

    def check_source(self, src: str, timeout: int = 300) -> VerifyResult:  # concrete
        ...

    @abstractmethod
    def conf_shadow(self, bundle_dir: Path) -> ShadowSpec | None: ...

    @abstractmethod
    def verifier_tool_name(self) -> str: ...

    def quickref(self) -> str:  # concrete: loads prompts/<name>/quickref.md
        ...
```

Register the class in `backends/registry.py`'s `BACKENDS` map. Instances are lazy
singletons, so constructing a backend must be cheap and must not touch a verifier.

The governing constraint, stated in the module and worth repeating: **gates only
ever call `check()`**. It is a deterministic, read-only judgment of the bundle as
committed. Any proof *search* belongs to construction, never to a gate, for the
reasons in [architecture.md](architecture.md) section 3. A per-backend `if` chain
appearing inside a gate is the signal that this interface needs another method,
not that the gate needs a special case.

### `check()`

Invoke your checker on one solution file and return a `VerifyResult`:
`success`, `wall_time_s`, `stdout`, `stderr`, `timed_out`, `returncode`.

Three requirements, each from a real failure mode:

* **Do not trust exit 0 alone if your tool does not deserve it.** One shipped
  backend's verifier exits 0 on some non-verifying outcomes, so its `check()`
  additionally requires a success marker in the output. `success` must mean
  verified, full stop, since every gate in the suite is built on it.
* **Enforce a hard wall clock inside the wrapper, and report a timeout
  distinctly.** A solver can run for hours on a pathological obligation. Surface
  `timed_out` so callers can record status `timeout` rather than `fail`. A timeout
  is "could not decide", not "the artifact is wrong", and conflating them
  manufactures evidence.
* **Kill the whole process group.** If your tool spawns solver children, reap them
  on both the normal and the timeout path. Orphaned solver processes accumulate
  under any parallelism and eventually take the host down.

By convention the actual invocation lives in a shell script under `scripts/`,
with the shared exit protocol `0` verified, `124` timed out, and optionally `3`
for a proof-carrying backend meaning "the file elaborated and only proof
obligations remain open". Exit 3 is what lets construction accept an intermediate
state before the proof phase without ever accepting it as a verdict. Reserve a
distinct code (the shipped scripts use 2) for "the verifier environment is
missing", so an infrastructure fault can never be read as a fact about a bundle.

If `check()` needs a per-bundle knob (one shipped backend takes a numeric-encoding
option recorded in `meta.json`), add it as a keyword argument and teach
`gates/_common.py`'s `check_bundle_file` / `check_bundle_source`. That is the
**gate layer's** single place: every gate that verifies goes through it, so no gate
module passes the knob itself. (The hygiene gate reads the recorded value, but only
to fail a bundle that declares a knob its solution cannot be using.)

It is not the *only* place, and a new knob is not done when that helper compiles.
The evaluation path has its own seam and does not go through `_common` at all:

* `eval/adapter.py` -- the `supports_float_encoding` flag on `EvalAdapter`, set per
  backend in `for_backend`, plus the adapter's own `check_source`, its
  `float_encoding(instance_id)` reader over `meta.json`, and the JSON schema of
  the verify tool the agent calls,
* `eval/dataset.py` -- copying the value out of `meta.json` onto the `EvalTask` and
  into the serialized task view,
* `eval/prompts.py` -- the knob travels with the spec block, so the agent sees the
  same value the bundle was verified under,
* `eval/agent.py` -- the verify tool's optional argument and what gets logged,
* `eval/grade.py` -- the verify grading call, and again in the checker tool the
  spec-quality judge is given,
* `eval/score.py` -- the consumer scorer's re-verification.

`adversary.py` (audit attacks) and `construct/audit_verdict.py` each pass it too.
`grep -rn "float_encoding" src/` is the honest enumeration; the guiding rule is
that any layer which re-verifies a bundle needs the same knob, because verifying
one under different options is not re-checking the same claim.

### `LanguageTables`

```python
LanguageTables(
    flavor,               # dispatch key for the lexing-sensitive machinery
    solution_filename,    # e.g. "model.py", "Solution.lean"
    comment_line,         # the line-comment token used by marker regions
    region_names,         # legal marker region names
    import_allowlist,     # roots the solution may import
    banned_tokens,        # tokens that fake verification
)
```

This one value is what makes the rest of the pipeline generic. Consumers:

* **markers** parses `<comment> <name>-start` / `-end` pairs and computes the spec
  view, the spec signature, `same_spec`, and the region hashes,
* **mutation** generates first-order mutants inside the impl region only,
* **leakage** lexes the spec view to screen it against the problem statement,
* **variant admissibility** and the **witness** machinery check that a
  spec-strength variant differs only where it is allowed to,
* **hygiene** enforces the allowlist, the banned tokens, and per-backend
  structural requirements.

`flavor` is a dispatch key, not a language name: two shipped backends share one
flavor because they are lexed identically and differ only in their region tables,
their allowlists, and their hygiene rules. Reuse an existing flavor when your
language lexes like it.

Introducing a new flavor means adding a branch at each dispatch point below. None
of them defaults: each **raises `ValueError` naming your flavor**, so what you owe
arrives as an error you cannot miss rather than as a silent wrong answer. Two of
them, `variant_scope` and `gates/hygiene`, also name the extension point and what
defaulting would have cost; the rest raise a shorter message, usually a bare
`unknown language flavor '<yours>'`, so read the traceback for the module rather
than expecting the message to tell you. This list is the map, not the checklist:

| dispatch point | what it refuses to guess |
|---|---|
| `markers.parse_regions`, `markers.spec_view` | how your source delimits marker regions and what the spec view elides |
| `mutation.generate_mutants` | which edits inside the impl region are behavioural |
| `leakage.screen` (its formal-flavor path) | how to lex the spec view into identifiers and comments |
| `variant_scope.unsound_evasions` | how a rival could discharge an obligation without proving it |
| `variant_scope._decl_names`, `_axiom_names` | your declaration and axiom syntax; a flavor with no such construct is listed in `_FLAVORS_WITHOUT_DECLARATIONS`, which makes the empty answer deliberate rather than accidental |
| `gates/hygiene.run` | which structural linter your source needs, and (separately) a backend with no `_REQUIRED_REGIONS` entry |
| `pbt_witness.witness_file` | lean-flavored only, by construction |

> **Caveat -- two of these can fail *green* once the port is under way, and they are
> the two to extend first: `variant_scope.unsound_evasions` and
> `gates/hygiene.run`.** The raise protects a flavor that is still entirely
> unknown. Both have a second state, part-way through a port, in which the guard no
> longer fires and the check still is not checking anything about your language.
>
> `unsound_evasions` reports problems as a list whose **emptiness means
> ADMISSIBLE**, and its dispatch guard is nothing but membership of
> `_KNOWN_FLAVORS`. Its own error message invites you to list a flavor with no
> declaration form in `_FLAVORS_WITHOUT_DECLARATIONS` / `_KNOWN_FLAVORS`, which is
> the right answer for a language that genuinely has no such construct -- and the
> wrong place to stop, because the obligation-preservation rules in the body are
> guarded by `if t.flavor == "lean"` and the `@ContractOnly` rule by
> `if t.flavor == "python"`. A newly listed flavor is therefore left with the
> generic assumption-token delta alone (`sorry`, `sorryAx`, `admit`,
> `native_decide`, `Assume`, `Refute`). A rival that simply drops your language's
> obligation comes back as `[]` -- reported sound, by a screen holding no rule that
> could have caught it, and both callers then draw a conclusion about the
> *specification*: a falsification battery reads it as "too strong", an audit as
> "admits a wrong implementation". Add your obligation rule in the same change that
> adds your flavor to those tuples, or add it to neither and keep the raise.
>
> `gates/hygiene.run` dispatches to a per-flavor linter with no fall-through,
> because borrowing another flavor's linter would apply its comment syntax,
> divergence tokens and axiom screen to source that says nothing about them.
> Writing `_run_<flavor>()` is only half the extension point, because
> `_REQUIRED_REGIONS` is keyed by **backend** rather than by flavor: if your linter
> checks marker regions the way the Lean one does, a second backend on your flavor
> with no entry there raises from that lookup instead -- deliberately, since
> defaulting to the empty tuple would pass a bundle that declares no spec region at
> all.

One deliberate default remains: `variant_scope._strip_comments` treats any
non-lean flavor as `#`-commented. It is reached only for a flavor
`unsound_evasions` has already accepted, and it feeds nothing but the
assumption-token delta. Extend it anyway if your language comments differently:
a `sorry` merely *discussed* in a comment the stripper does not recognise is
counted as a use, which retires an admissible rival and records a weakness search
that never ran.

Choose `region_names` to reflect what your language actually separates. The
required-region check is per backend: one shipped backend requires pre-conditions,
post-conditions, and impl; another requires only impl because its obligations live
in a different construct; the proof-carrying one requires post-conditions, impl,
and proof.

`banned_tokens` is the anti-fakery surface and is the most important table to get
right. List every construct that discharges an obligation without proving
anything, every escape from the checked fragment, and every facility that can
assume a postcondition. Identifiers are matched on word boundaries and
operator-like tokens by substring. Note the deliberate asymmetry between two
shipped backends: one bans a choice principle that the other allows, because in the
latter the standard mathematical library legitimately depends on it and it is
instead tracked by an explicit standard-axioms check. Ban what your fragment cannot
tolerate, and where a construct is unavoidable, track it explicitly rather than
pretending it is absent.

### `conf_shadow()`

Return a `ShadowSpec(provenance, script)` locating the executable shadow the
differential conformance gate runs inside the instance container, or `None`, which
makes the gate record an explicit skip with a reason and **never** a silent pass.

`provenance` is the trust label and it matters more than the mechanics:

* `"direct"` when the specification language *is* the repository's language, so
  the shadow is the impl region with contracts stripped, run as is. There is no
  transliteration gap.
* `"transliterated"` when it is not, so the shadow is an agent-written port of the
  formal implementation. This is the least-trustworthy link in the whole chain, and
  the gate records the label so a consumer can weight the result accordingly.

A natural-language backend has no formal implementation to shadow and correctly
returns `None`.

### `verifier_tool_name()`

The name the evaluation agent sees for its checking tool. Be honest here. The
natural-language backend returns a lint tool name, and every surface that renders
its result labels it as a lint rather than a verification, because "verified" must
not be claimable by well-formedness.

## 2. What a bundle must contain

`gates/base.py`'s `Bundle` resolves these by convention. Everything below is
keyed off `solution_filename`, so a new backend gets the naming for free.

| artifact | required | judged by |
|---|---|---|
| `<solution>` | yes | verification, hygiene, mutation, leakage |
| `<stem>_prepatch*<ext>` | yes | the discriminating-power gate: identical spec, buggy implementation, must fail verification |
| `<stem>_gold<ext>` | optional | the gold gate (absent means the shipped solution is the gold-faithful one) |
| `refinement.md` | for formal backends | the operation-by-operation map from the formal implementation to the reference patch |
| `mapping.md` | for formal backends | the formal-symbol to repository-symbol binding, plus any pinned probe seed |
| `axiom_check.py` | when the bundle has axioms | the axiom-soundness gate, in container |
| `conformance_check.py` | when a shadow exists | the differential conformance gate, in container |
| `properties.py` | optional | the adversarial spec-strength battery |
| `pbt_result.json` | optional | no gate; that battery's per-case outcomes, as recorded by whoever ran it, rendered by the review site |
| `meta.json` | yes | every recorded verdict, plus modeling metadata |
| `result.json` | when `construct` built the bundle | no gate; the terminal construction status, which resume and `green_check --only-ok` key off |
| `verdict.md` | when audited | the inspectable audit record |
| `RELAXED_LEAKAGE.md` | when a leak was reviewed and accepted | the leakage gate, which honors it as `relaxed` |
| `BLOCKED.md` | when blocked | the terminal principled block |

The immutable inputs, `instance.json` and `patch.diff`, live one level up at the
instance root and are shared by every backend, so the formalizations of one row
cannot drift onto different inputs.

Add your backend to the integrity gate's per-backend allowlist, and to its
exclusion table if some common artifact can never apply to you. The allowlist is
not bureaucracy: it is an additions-only discipline that says a file a gate cannot
read has no business existing in a released bundle, so a dead artifact that *looks*
load-bearing fails the gate instead of misleading a reader. The natural-language
backend, for instance, excludes the axiom, conformance, and battery artifacts,
because the gates that would read them are explicit skips for it.

## 3. Prompts

Create `prompts/<backend>/` with at least:

| prompt | used by |
|---|---|
| `construct_system.md`, `worker.md` | the construction agent |
| `spec_guide.md` | the binding specification rules your worker references |
| `quickref.md` | the evaluation agent's tool reference |
| `eval_mode_*.md` | the per-mode task prompts for the modes you support |
| `audit_eq.md`, `audit_panel_1.md`, `audit_<role>_task.md` | the audit roles |
| `judge_*_system.md` | the judged evaluation criteria |

Anything genuinely language-neutral goes in `prompts/shared/` and is found by
fallback. Two roles of the audit panel (faithfulness and leakage) are shared
already, because neither has an executable oracle and neither depends on the
specification language.

The worker prompt is where the per-file bundle contract is spelled out to the
agent: which artifacts to write, that the pre-patch twin's specification must be
byte-identical to the solution's, that the marker regions are mandatory, that the
probe scripts must be self-contained and deterministic with a recorded seed, and
two rules that are not negotiable: **never weaken a contract to make a gate pass**,
and if the instance cannot be specified inside the language's fragment, write a
principled `BLOCKED.md` instead. The prompt should also tell the agent not to run
the container gates itself, since those are the driver's job and running them from
inside an agent wastes the host's scarcest resource.

## 4. The evaluation seam

`eval/adapter.py`'s `EvalAdapter` is the single place where per-backend evaluation
differences live, and its docstring states the rule: a per-backend `if` chain
anywhere else under `eval/` should be moved here. Add a branch to `for_backend`
supplying the agent-facing tool name, the judge-facing checker name (empty when you
have no verifier, in which case callers must guard on it), the solution filename,
the markdown fence language, the evaluation-side import allowlist (which may extend
the construction allowlist where a solver legitimately imports more), the banned
tokens, candidate paths for recovering a model when an agent exits without
submitting, and the anti-fakery rules.

The anti-fakery hook is what makes "verifies" mean something in an evaluation, and
it is deliberately minimal: it rejects an unparseable artifact, imports outside the
allowlist, verification-faking tokens, and a missing or vacuous obligation. It is
*not* a spec-strength check. Judging whether a constructed specification actually
pins the required behavior is the equivalence judge's and the spec audit's job, and
folding that into a mechanical lint would make it look decidable when it is not.

Register your tool name in the list the trajectory audit and metrics scan, or a
solver's verifier calls will be invisible to the anti-cheat review.

## 5. Backends without a verifier

A backend need not have a prover. The shipped natural-language backend shows the
full shape, and it is worth studying before writing a partial one, because the
pipeline stays honest about it end to end rather than pretending:

* it is absent from `applies_to` on the seven verifier-backed gates, so the runner
  records explicit stamped skips and nothing in the gate layer ever calls its
  `check()`,
* its `check()` is a structural lint and every surface labels it as such,
* `conf_shadow()` returns `None`,
* the spec view is the identity (there are no regions to elide) so `same_spec`
  degrades to normalized whole-file equality,
* its hygiene gate requires that the bundle record which repository sources the
  author consulted, which is the closest available analog of an import allowlist,
* the mechanized audit roles are routed to a different derivation: instead of
  "does this variant verify", the substrate is executable probes run in the
  instance image, where a probe failing on the patched tree is a violation
  candidate, an alternative patch satisfying every probe yet not resolving is a
  too-weak finding, and a positive control must fail at base and hold when patched,
* it is scored on resolution plus an adversarial audit, in unaudited and audited
  mode pairs, and the mode that requires a verifying witness is rejected for it
  before any work starts.

The general lesson: when a capability is absent, wire the absence explicitly at
every layer. Do not let a gate pass by default, do not let a lint be called
verification, and reject invalid mode combinations up front rather than producing a
number that cannot mean anything.

## 6. Checklist

1. `LanguageTables`, reusing an existing `flavor` if your language lexes like it.
2. The wrapper script with the exit protocol, plus `check()` on top of it.
3. `conf_shadow()` with an honest provenance label, or `None`.
4. `verifier_tool_name()`.
5. Register in `BACKENDS`.
6. Add the backend to each gate's `applies_to` **only** where the gate can really
   judge it; leave it out elsewhere so the runner records explicit skips.
7. Extend the integrity gate's allowlist and, if applicable, its exclusion table.
8. Extend the hygiene gate's required-region table and any structural rules.
9. Add the `EvalAdapter` branch and register the tool name for trajectory audit.
10. Write `prompts/<backend>/`.
11. Give the review site the backend's *presentation*. Its column list, and the
    `FORMAL_BACKENDS` / `EXTRA_BACKENDS` split that decides where the chooser
    draws it, both come from the registry already; what is hand-written in
    `viz/backend/settings.py` is `BACKEND_LABELS` and `_BACKEND_MODEL` (solution
    filename, pre-patch stem, extension, fence language). That last lookup falls
    back to the first backend's filenames on an unknown key, so a backend missing
    from it renders empty panes instead of failing loudly.
12. Nothing to do for the general entry points: `--backend` choices are derived
    from `BACKENDS`, from `GATED_BACKENDS`, or from the gate's own `applies_to`,
    and `tests/test_backend_vocabulary.py` fails if one restates a registry set
    instead. Check only the narrower-scope drivers, whose choice lists are their
    own declared scope (the PBT port lane accepts the two backends it knows how
    to port to), and reject the combinations the backend cannot support at
    argument-parse time.
13. `python -m pytest tests/`, then construct one cell with `--skip-docker`, then
    one full cell with the audit enabled.
