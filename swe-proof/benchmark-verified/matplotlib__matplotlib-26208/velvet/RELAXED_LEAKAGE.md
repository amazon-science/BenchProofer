# RELAXED_LEAKAGE — matplotlib__matplotlib-26208

Disposition: **KEEP with relaxed leakage**. In this unified repo the policy
lives in the binding spec-construction rules, `prompts/velvet/spec_guide.md`
directive 6 ("**Exception — relaxed-leakage:** for a proven `problem_statement
↔ gold` mismatch where a faithful spec MUST name the discriminator, keep the
instance with the leak allowed (`meta.json gates.G-LEAK.status = 'relaxed'`)");
the G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`)
via `meta.json relaxed_leakage: true` + this in-bundle file. (References below
to `RELAXED_LEAKAGE.md` are to the former source-repo-only policy doc,
which does not exist in this repo — see `prompts/README.md` on dangling
source-repo refs; the acceptance conditions quoted from it are the same ones
spec_guide.md directive 6 encodes.)

## The problem_statement ↔ gold mismatch

The public `problem_statement` reports one behavior — a **symptom** — and nothing
else:

> "dataLims get replaced by inf for charts with twinx if ax1 is a stackplot" …
> "the data limits (dataLims) of the first axis (ax1) get changed to ±inf when
> plotting a stackplot on the second axis (ax2)" … "To not change ax1 dataLims".

The entire public issue is about the **dataLim → ±inf** symptom. It never
mentions units, unit converters, conversion settings, category/string handling,
or any notion of one axis *inheriting* a setting from another.

The gold patch — and the sole FAIL_TO_PASS test `test_twin_units[x]` /
`test_twin_units[y]` — pins a completely different, narrower behavior: that a
newly created twin axis **inherits the shared axis's `units`**:

```python
# gold (lib/matplotlib/axes/_base.py)
ax2.xaxis.units = self.xaxis.units      # in twinx()
ax2.yaxis.units = self.yaxis.units      # in twiny()
```

```python
# test_twin_units (the only F2P)
ax1.plot(a, b)                                   # a, b are string lists
assert getattr(ax1, axis_name).units is not None
ax2 = getattr(ax1, twin_func)()
assert getattr(ax2, axis_name).units is not None
assert getattr(ax2, axis_name).units is getattr(ax1, axis_name).units
```

The tested behavior is **units inheritance / object identity** of the shared
axis's converter — the dataLim symptom is never asserted by the test.

### Mechanical verification (run against `instance.json`)

| token | in `problem_statement` | in `hints_text` |
|---|---|---|
| `units` | **no** | no |
| `unit` | **no** | yes ("unit machinery", "unit handling code") |
| `converter` / `convert` | **no** | no |
| `inherit` | **no** | no |
| `xaxis` / `yaxis` | **no** | no |
| `category` / `categorical` | **no** | no |
| `dataLim` / `inf` / `stackplot` / `twinx` | yes | — |

The discriminating vocabulary of the gold/tested behavior — units, the unit
converter, inheritance of a per-axis setting — is **absent from
`problem_statement`** and surfaces only in `hints_text`:

> "This is an edge case in the unit handling code, PR incoming."
> "do not use the unit machinery (due to using strings to get catarogicals)"

## Why faithful + non-leaking is impossible

A **faithful** spec must pin units inheritance, because `test_twin_units` (the
sole FAIL_TO_PASS, and therefore the only thing `resolved` depends on) asserts
exactly: after a quantity is plotted along the shared coordinate so the source
axis carries a present converter, the companion axis (a) carries a present
converter and (b) carries the *same* converter object. A spec that pinned only
the publicly-described behavior (the dataLim → ±inf symptom) would say nothing
about `units` at all, and would admit a wrong implementation that verifies yet
fails `test_twin_units` — i.e. it would violate G-EQ / verify⟹correct.

But units inheritance and its tested observables (`units is not None`,
`ax2.<axis>.units is ax1.<axis>.units`) are derivable only from `hints_text` /
the gold / the hidden `test_patch`, never from the public issue. Therefore any
faithful spec necessarily pins a *behavior* the public task text does not
contain — the leak is in the **behavior itself**, not in narration that could be
removed. No `problem_statement`-derivable reformulation models the gold fix
(the public symptom — dataLim → inf — is a downstream consequence the test never
checks, and reconstructing "the companion must inherit the converter" from
"dataLims become inf" is not possible from the public text). This is the precise
condition `RELAXED_LEAKAGE.md` accepts.

## Requirements check (RELAXED_LEAKAGE.md)

1. **Core is sound.** G-VERIFY pass (1.5s); G-DIFF fail — `Solution_prepatch_1`
   / `Solution_prepatch_2` reproduce the pre-patch absent default
   (companion axis keeps its freshly-initialised `None`) and fail on exactly the
   discriminating clause `out = source` at each independently-tested site;
   G-MUT 2/2; G-EQ target tight (the postconditions are grounded structural
   facts about the actual input `source` — `out = source`, `isPresent out =
   isPresent source` — no ungrounded oracle, directive 8); G-AX vacuous (no
   axioms, no A-reference); G-CONF runs (all-R/I impl, `conf_skip = false`) and
   agrees with the real patched `twinx`/`twiny` over the input space; and
   **G-RESOLVE**: `patch.diff` == gold verbatim, harness resolves.
2. **The leak is genuinely unavoidable**, established above: the units /
   converter / inheritance discriminator is demonstrably absent from
   `problem_statement` and present only in `hints_text` / gold / `test_patch`.
3. **Documented in-bundle** (this file); `meta.json gates.G-LEAK.status =
   "relaxed"` points here. The mechanical lexical G-LEAK screen still **passes**
   (the spec view writes "conversion setting" / "display-conversion setting",
   names no patched path/symbol/`units`/`xaxis`/`twinx`, and describes only the
   abstract carry-over behavior) — the leak is semantic, as the policy expects.

## Scope of what is disclosed

The spec view discloses: when a new companion view is created that shares one
coordinate with a source view, the companion's axis for that shared coordinate
carries over the source axis's display-conversion setting (the same object when
present, absent otherwise). That carry-over behavior is the relaxed disclosure —
it is the tested behavior, absent from the public dataLim-symptom issue. Nothing
about the patched file (`lib/matplotlib/axes/_base.py`), the `twinx`/`twiny`
symbols, the `xaxis.units` / `yaxis.units` attributes, the unit-converter
machinery, or the category/string plumbing is named in the spec view.
