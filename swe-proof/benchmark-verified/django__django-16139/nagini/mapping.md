# mapping.md — django__django-16139

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d559cb02da30f74debbb1fc3a46de0df134d2d80`, states the type
abstraction, and gives the provenance of the deep-model reference (the unchanged
resolver `resolve` is validated against).

Repo file under change: `django/contrib/auth/forms.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_action_reference(prefix, token, current_action, pk, secondary_action)` | the body of `UserChangeForm.__init__` — `django/contrib/auth/forms.py:162` — specifically the relative-URL it builds for the password field's help-text link (`django/contrib/auth/forms.py:164-166`) | the modeled changed function: it constructs the relative reference embedded in the read-only password field's help text |
| `resolve(base_dir, rel)` *(deep model — A-reference)* | `urllib.parse.urljoin` — CPython stdlib `Lib/urllib/parse.py` (the resolver the FAIL_TO_PASS test `test_link_to_password_reset_in_helptext_via_to_field` applies to the built reference) | pure spec: hierarchical relative-reference resolution; the deep model of the unchanged resolver, validated `resolve == urllib.parse.urljoin` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `DOTDOT()` | the `..` path step in a relative URL | pure spec: the up-one-level sentinel (`-1`) |

The pre-patch repo expression the change replaces (for the refinement audit, not
referenced from the consumer spec view): the literal relative reference
`"../password/"` at `django/contrib/auth/forms.py:166`, replaced by
`f"../../{self.instance.pk}/password/"`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a URL path (e.g. `/admin/auth/user/<id>/change/`) | `List[int]` / `PSeq[int]` of opaque path-segment ids | each non-empty path segment ↔ one int id; distinct segments ↔ distinct ids; the trailing-slash "directory" path ↔ its segment list |
| the `..` step in a relative reference | the sentinel `DOTDOT() == -1` | the only negative segment id; ordinary segments are `>= 0` |
| the access identifier in the change URL (`<pk>` or a `to_field` value such as a username/uuid) | the int `token` | `token` is an arbitrary segment id; the spec quantifies over ALL `token`, so it distinguishes "keyed by token" from "keyed by pk" |
| the object's primary key (`self.instance.pk`) | the int `pk` | a segment id, independent of `token` |
| the current / secondary action page name (`change`, `password`) | `current_action`, `secondary_action` | segment ids |
| the fixed leading path shared by both URLs (e.g. `/admin/<app>/<model>`) | `prefix: List[int]` | the leading segment list, read-only (fractional permission) |
| `help_text.format(rel)` substituting `{}` with the relative reference, and the `<a href="...">` markup | omitted (identity on the link target) | `str.format` only inserts `rel` into the `href`; the F2P test extracts exactly that `href` and resolves it. The modeled object is the relative reference `rel` itself — the only thing the patch changes. |
| `f"../../{self.instance.pk}/password/"` (post-patch) | `result == [DOTDOT(), DOTDOT(), pk, secondary_action]` | two `..` steps, then the pk segment, then the password-action segment |

`str` indexing/iteration is banned in Nagini, and the link markup is unchanged
boilerplate; the carrier is the list of path-segment ids, and the specification
is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

### `resolve` deep model ↔ `urllib.parse.urljoin`
**Callee:** CPython `urllib.parse.urljoin(base, url)` — resolves a (possibly
relative) reference against a base URL per RFC 3986. The relative-reference
resolution the bundle relies on (pop one accumulated path segment per `..`
step; append any other segment) is modeled **deeply** by the `@Pure`
front-recursive fold `resolve` in the `pure` region; there is **no `urljoin`
axiom** the proof consumes. The deep model is validated equal to the real
resolver out of band by axiom_check.py (G-AX).

Behaviour on the bundle's domain (the change URL is a trailing-slash directory
path `/admin/<app>/<model>/<token>/change/`, and the references pop at most two
levels — `current_action` then `token` — never above the shared prefix, so the
RFC 3986 root-over-pop corner is never reached):

```
urljoin("/admin/auth/user/<token>/change/", "../password/")
    == "/admin/auth/user/<token>/password/"          # pre-patch: TOKEN-keyed
urljoin("/admin/auth/user/<token>/change/", "../../<pk>/password/")
    == "/admin/auth/user/<pk>/password/"             # post-patch: PK-keyed
```

The directory-segment list of the base is `[admin, app, model, token, change]`;
one `..` pops `change`, a second pops `token`, then `pk` and `password` are
appended — giving `[admin, app, model, pk, password]`, the password-change page
keyed by the **primary key**, independent of the access `token`. This is
exactly what the FAIL_TO_PASS test asserts via
`urllib.parse.urljoin(admin_user_change_url, matches.group(1)) == pw_change_url`
where `admin_user_change_url` is reached through a `to_field` value (the
username) and `pw_change_url` is keyed by `user.pk`.

**Domain note (declared, sound):** `resolve` models `urljoin` on references
that do not pop above the root. The change URLs always have depth ≥ 5 and the
references pop ≤ 2 levels, so this domain always holds; the model.py
precondition (non-negative ordinary segments, the base built as
`prefix + [token] + [current_action]`) keeps the base populated through both
pops. RFC 3986's distinct over-pop behaviour (urljoin emits a non-absolute
remainder) is outside this domain and never occurs in the bundle;
axiom_check.py restricts validation to the non-over-popping domain accordingly.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`urllib.parse.urljoin` on boundary base/relative shapes (incl. the exact
change-URL shape and the two references the bug is about) plus 20 000 randomized
fuzz inputs, asserting `resolve == urljoin` on the declared domain. It also runs
5 000 end-to-end token/pk witnesses confirming the post-patch reference lands on
the pk-keyed password page for every access token while the pre-patch reference
does so only when `token == pk`. It imports only the standard-library
`urllib.parse` (the very module the F2P test uses); nothing repo-specific.
Docs: https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urljoin.
