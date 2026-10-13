# mapping.md — symbol binding & type bijection (django__django-16139)

## Modeled function
- **Lean** `implementation_passwordHelpText : List Char → Nat → List Char`
- **Python** `django.contrib.auth.forms.UserChangeForm.__init__`
  — `django/contrib/auth/forms.py:158-170 @ d559cb02da`
  (the statement `password.help_text = password.help_text.format(<url>)`).

The function under spec is the per-instance computation of the password field's
help-text string. The help text is a template carrying a single `{}` placeholder
inside an anchor tag; `__init__` substitutes a relative URL into that
placeholder. The observable behavior demanded by the F2P test is the VALUE of
the substituted URL: it is built from the record's own primary key as
`../../<pk>/password/` (three path components grounded in the primary key),
rather than a fixed single-component relative path.

Only the `password` branch is modeled — the `user_permissions` branch below it is
untouched by the change and irrelevant to the modeled behavior.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `str` help-text template (input) | `List Char` | per-code-point string; total/sound indexing |
| `str` help-text result (output) | `List Char` | same character carrier |
| `self.instance.pk` (positive AutoField int) | `Nat` | `str(pk)` for a non-negative int == `toString (pk : Nat)`: decimal digits, no separators |
| `"{}"` placeholder | `'{' :: '}'` | the single positional field of the template |
| `str.format(url)` (positional, one field) | `formatFirst template url` | replace the first `{}` occurrence with `url`, leave the remainder verbatim |

`self.instance.pk` is the record's OWN primary key (an integer for the default
User model); the route by which admin is reached (`to_field`) does not change
`pk`, so modeling `pk : Nat` is faithful.

## Callee provenance
- `str.format` (one positional argument, template with a single `{}` and no other
  brace) is an UNCHANGED callee. It is modeled DEEPLY as `formatFirst`
  (an **A-reference**, refinement.md row 3) — validated character-for-character
  against the real `str.format` by G-AX — NOT axiomatized.
- The relative-URL argument is the CHANGED expression; it is reconstructed
  identically as `mkUrl pk = "../../" ++ toString pk ++ "/password/"`
  (I / R, refinement.md rows 1–2). It is not a callee.
- No UNCHANGED callee is consumed as a proof axiom; the axioms region is empty.

## Flag dependency
None. `str.format` is called with a single positional argument; G-AX fuzzes
templates carrying exactly one `{}` and no other `{`/`}` (the real template's
shape) and arbitrary brace-free replacement strings.

## G-CONF fuzz seed
Pinned seed: **16139**. ≥10^5 fuzzed (template, pk) pairs: templates carry one
`{}` with random surrounding text (no other braces); `pk` ranges over small and
large non-negative integers including boundary values.
