# mapping.md — django__django-16139

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d559cb02da30f74debbb1fc3a46de0df134d2d80`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance. There are **no axioms** in this bundle (the only changed
operation is modeled deeply), so there is no `axiom_check.py` and G-AX is
skipped.

Repo file under change: `django/contrib/auth/forms.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildRelativeLink (key : Nat)` | the `.format(...)` argument computed in `UserChangeForm.__init__` — `django/contrib/auth/forms.py:166` (`password.help_text = password.help_text.format(...)`) | the modeled changed function: it produces the relative URL substituted into the password field's help text |
| `relativeLink (key : Nat)` | the post-patch expression `f"../../{self.instance.pk}/password/"` — `django/contrib/auth/forms.py:166-167` (post-patch) | pure spec: the relative URL string as a function of the record's primary key |
| `key : Nat` | `self.instance.pk` — the bound record's primary key (an `AutoField`/`int` for the `User` model) | read-only input |

The pre-patch repo expression the change removes (refinement audit only, not in
the consumer spec view): the fixed string literal `"../password/"`
(`forms.py:166` pre-patch), which ascends one level and omits the key.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.instance.pk` (a non-negative `int` primary key) | `Nat` (`key`) | the `User` model's `pk` is an `AutoField` ⇒ a positive integer; `0`/large values fuzzed for completeness. `int n` ↔ `Nat n`. |
| `str(self.instance.pk)` (implicit in the f-string interpolation) | `toString key` (`List Char`) | Python `str(n)` for a non-negative `int` ↔ Lean `toString n` for the corresponding `Nat`: both render the decimal form with no leading zeros, no sign, no separators. Identical glyph sequence. |
| a Python `str` (the URL, and the literal segments) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; `"../../"`/`"/password/"` literals ↔ the matching `.toList` literals. |
| `str.format` placeholder substitution — `password.help_text.format(arg)` (`forms.py:166`) | identity (omitted) | `help_text` is a **fixed** template string (the `'…<a href="{}">this form</a>…'` literal, `forms.py:150-156`, UNCHANGED by the patch). The only `{}` placeholder is filled by `arg`; the patch changes **only** `arg`. So substituting into the constant template is an R-identity wrapper on `arg` — the observable change is exactly the relative URL `arg`, which is what `buildRelativeLink` returns. |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the produced value is a per-character URL string and the
sole input transformation is decimal rendering of the key.

## 3. Callee provenance

There are **no axiomatized callees**. The only operations are:
- decimal rendering of the key (`str(pk)`), modeled deeply as `toString` (an R
  refinement, §2 — checked by G-CONF, not an axiom);
- string concatenation of three segments (`++`, an I/R op — checked by G-CONF);
- `str.format` substitution into the constant `help_text` template, an
  R-identity wrapper (§2).

No real callee is over-claimed; nothing is left to a consumed axiom.
Consequently there is no `axiom_check.py` and `meta.json gates."G-AX".status =
"skip"`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16139`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `relativeLink` to Python (`"../../" + str(key) + "/password/"`)
and diffs it against `patch.diff`'s behaviour — the gold post-patch
format-argument expression `f"../../{pk}/password/"` — over ≥10⁵ fuzzed key
values (0, small, large, and boundary `int` magnitudes). There are no A-tagged
callees in the impl region, so the shadow is pure R/I.
