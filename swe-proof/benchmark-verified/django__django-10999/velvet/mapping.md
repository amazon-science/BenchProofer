# mapping.md — django__django-10999

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 36300ef336e3f130a0dadc1143163ff3d23dc843`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and
gives the provenance of the modeled behavior.

Repo file under change: `django/utils/dateparse.py`.

## 0. What the patch changes (and what it does NOT)

The gold patch edits **only the module-level compiled pattern**
`standard_duration_re` (`django/utils/dateparse.py:29-38`). The body of
`parse_duration` (`dateparse.py:124-149`) is **unchanged**. The behavioral
difference is therefore entirely in *how the pattern assigns named groups* on
the relevant inputs:

* pre-patch each numeric component carried its own optional `-?` (so a `-` could
  attach to any single component, and a leading `-` scaled only the first
  component);
* post-patch a single optional sign is captured **once at the front**
  (`(?P<sign>-?)`), the component patterns no longer admit `-`, and
  `parse_duration` multiplies the **whole** magnitude by that sign.

The operation that genuinely changed is the pattern's match semantics. Per
SPEC_GUIDE §0 directive 7, the changed op is **not** axiomatized; it is modeled
**deeply and concretely** (`step`/`decode`/`parseDuration`, the `pure` region)
and that deep model is validated against the real **post-patch** `parse_duration`
by **G-CONF** (which applies `patch.diff` first). It is NOT a G-AX obligation:
G-AX axiomatizes *unchanged* callees against the repo at `base_commit`, whereas
this is the function under change — so there is no `axiom_check.py` and G-AX
skips.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `parseDurationSeconds (text : List Char)` | `parse_duration(value)` — `django/utils/dateparse.py:124` | the modeled changed function (restricted to the patched format; see §2) |
| `parseDuration : List Char → Option Int` *(deep concrete model of the changed function)* | the composite "`standard_duration_re.match(value)` + the timedelta assembly of `parse_duration`", `dateparse.py:29-38` + `124-149` | pure spec: the signed total-seconds value of a sign-and-colon time string; deep model of the patched parse, validated `parseDuration == real post-patch parse_duration` by `conformance_check.py` (G-CONF, which applies patch.diff) |
| `step`, `decode`, `initPS`, `PS` | the named-group assignment of `standard_duration_re` together with the `days + sign * timedelta(...)` assembly | pure spec internals: a left-to-right scan realizing the same value |

There are **no `axiom`s** in this bundle and **no A-reference**: the changed
regex/assembly is the only non-trivial operation and it IS the function under
change, modeled deeply and concretely (an **I** op, refuted by G-CONF), never a
consumed axiom or a G-AX A-reference (which would axiomatize an *unchanged*
callee). `re.compile`/`re.match` themselves are CPython stdlib and are exercised
concretely by G-CONF. Consequently there is **no `axiom_check.py`** and G-AX
skips.

## 2. Modeled domain and type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `value : str` (the argument of `parse_duration`) | `List Char` | `s` (Python str) ↔ `s` as `List Char`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]` |
| a single character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; over the modeled alphabet (`0`–`9`, `:`, `-`) this is total and exact |
| `parse_duration(value)` result (`datetime.timedelta` or `None`) | `Option Int` (total seconds) | `None` ↔ `none`; a `timedelta` ↔ `some (round(td.total_seconds()))`. Over the modeled domain every result is an **integral** number of seconds (no `days`-word, no fractional `.microseconds`), so `Int` seconds is an exact carrier (verified by G-CONF). |

**Modeled input domain (the `require`s — BOTH machine-checked).**
`parseDurationSeconds` models `parse_duration` on **non-empty** strings drawn
from the alphabet `{'0'..'9', ':', '-'}` — i.e. the "`[D ]H:M:S`"-style *time
component without the optional leading `days` word or fractional seconds*.
This is the format the `standard_duration_re` branch governs and the one the
patch changes. Both halves of the domain restriction are stated as
machine-checked preconditions in the contract:

* `require text ≠ []` — the empty string is the only `{digit,:,-}`-domain
  string on which `parse_duration` falls through to the postgres branch and
  returns `timedelta(0)`;
* `require ∀ c ∈ text, isDigit c ∨ c = ':' ∨ c = '-'` — pins the modeled
  alphabet in the contract itself, so inputs containing `.`/`,`/space (the
  fractional-seconds and days-word formats, handled by the **unchanged**
  `microseconds`/`days` groups) are out of the verified domain *by contract*,
  not merely by prose.

On this domain `standard_duration_re` is the sole matcher (the `iso8601` and
`postgres_interval` alternatives never match a `{digit,:,-}` string), so the
model equals the full `parse_duration`. The restriction is faithful because
all discriminating F2P inputs are non-empty `{digit,:,-}` strings and both
preconditions are stated honestly in the spec view.

The days-word prefix (`-4 15:30`, `-4 days -15:00:30`) and fractional seconds
(`-30.1`) are **out of the modeled domain**: they involve the unchanged `days`
and `microseconds` groups (handled identically before and after the patch) and
are validated end-to-end by G-RESOLVE on the real harness, not by the Lean
model. The discriminating F2P rows (`-15:30`, `-1:15:30`, `-00:01:01`,
`-01:01`, `-01:-01`) all lie inside the modeled domain.

## 3. Changed-op provenance (deep concrete model — checked by G-CONF)

### 3.1 `parseDuration` deep model ↔ real post-patch `parse_duration` (I, G-CONF)

The deep model encodes the post-patch named-group semantics directly:

* an optional **single leading** `-` sets the overall sign (a `-` anywhere else
  is invalid — matching that the patched component patterns no longer contain
  `-?`, and that `parse_duration` raises / fails to match otherwise);
* the colon-separated **non-empty** digit groups (at most three: `h`, `m`, `s`,
  right-aligned) are folded base-sixty into a magnitude;
* the overall sign multiplies the **entire** magnitude (`sign * timedelta(...)`
  in `parse_duration`);
* a trailing/empty group, a fourth group, or any non-`{digit,:,-}` character
  makes the string unparseable (`none`).

**Soundness check (G-CONF, not G-AX):** `conformance_check.py` runs the **real
post-patch** `django.utils.dateparse.parse_duration` — the harness applies
`patch.diff` (`apply_gold=True`) *before* the check — on the discriminating F2P
rows, the exhaustive `{0-9,:,-}` alphabet (length ≤ 5), plus randomized fuzz,
and asserts that the I-transliterated deep model `parseDuration` (= `shadow_parse`)
agrees with it on every input in the modeled domain (`None` matches `none`;
otherwise the model's signed seconds equals `round(td.total_seconds())`). Exit 0
iff sound. Validated locally pre-submission against the **patched** callee:
0 disagreements over 3.75M exhaustive (length ≤ 6) + 500k fuzz inputs.

*(Why not G-AX?* G-AX runs against the repo at `base_commit` with **no** patch
applied — the *pre-patch, buggy* `parse_duration`. A deep model of the **fix**
necessarily disagrees with the **bug** (e.g. `-1:30` → model/post-patch `-90`
vs. pre-patch `-30`). Axiomatizing the function-under-change is exactly what
SPEC_GUIDE §0 directive 7 forbids; its fidelity belongs to G-CONF, the gate that
applies the patch.)

### 3.2 Flag / configuration dependencies

None. `standard_duration_re` has no mode flags; the only configuration is which
of the three module patterns matches first, and over the `{digit,:,-}` alphabet
that is always `standard_duration_re` (verified exhaustively by G-CONF).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`10999`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `step`/`decode`/`parseDuration` (R/I-tagged ops) to Python and
compares against the real post-patch `parse_duration` (the G-RESOLVE oracle)
over the modeled `{digit,:,-}` domain.
