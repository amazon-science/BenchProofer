# mapping.md — django__django-16642

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = fbe850106b2e4b85f838219cb9e1df95fba6c164`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of the upstream callee whose outputs are the modeled inputs.

Repo file under change: `django/http/response.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveMediaType (guessed encoding : Option String)` | the media-type resolution slice inside `FileResponse.set_headers` — `django/http/response.py:606-619` (the `content_type = {…}.get(encoding, content_type)` lookup and the `content_type or "application/octet-stream"` fallback) | the modeled changed slice |
| `compressionMediaType (encoding : Option String)` | the `{ "bzip2": …, "gzip": …, "xz": … }` override dict literal — `django/http/response.py:611-615` (post-patch: `+ "br"`, `+ "compress"`) | pure spec: the compression-label → media-type table the patch extends |
| `resolvedMediaType (guessed encoding : Option String)` | the composite `{table}.get(encoding, content_type)` then `content_type or "application/octet-stream"` — `django/http/response.py:611-618` | pure spec: the full resolution (override wins, else guess, else generic) |

The modeled slice is the `if self._no_explicit_content_type: / if filename:`
branch of `set_headers` (the only branch the F2P test exercises): the file has a
name and no caller-supplied content type, so the response's Content-Type is
resolved purely from the name. The Content-Length / Content-Disposition logic
of `set_headers` is orthogonal and unchanged; it is not modeled.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a media-type string, e.g. `"text/html"` | `String` | identity on the byte content (ASCII media types) |
| the guessed media type — `content_type` from `mimetypes.guess_type`, possibly `None` | `Option String` (`guessed`) | `None` ↔ `none`; a present string `s` ↔ `some s` |
| the compression label — `encoding` from `mimetypes.guess_type`, possibly `None` | `Option String` (`encoding`) | `None` ↔ `none`; a present label `s` ↔ `some s` |
| Python `d.get(k, default)` on the override dict | `Option.orElse` over `compressionMediaType` | `compressionMediaType encoding` is the dict's `[encoding]` when present (a recognised label), else `none`; `.orElse (fun _ => guessed)` is the `, content_type` default |
| Python `x or "application/octet-stream"` | `Option.getD "application/octet-stream"` | the present/absent split: a present media type passes through; `None`/absent falls to the generic. (`x or d` and `getD` agree because every recognised/guessed media type is a non-empty truthy string, never `""`.) |

The `match encoding with | some "br" => … | _ => none` in `compressionMediaType`
is the Lean transliteration of dict membership `encoding in {…}`: the five string
keys are the recognised compression labels.

## 3. Callee provenance (the modeled inputs — no axioms)

**No `axiom` is declared and no callee contract is consumed.** The two inputs of
`resolveMediaType` — `guessed` and `encoding` — are exactly the pair returned by
the CPython standard-library **`mimetypes.guess_type(filename)`**
(`Lib/mimetypes.py`), called once at `django/http/response.py:608`:

```python
content_type, encoding = mimetypes.guess_type(filename)
```

`mimetypes.guess_type` is **unchanged** by the patch and is shared, untouched, by
every branch of the resolution; the patch only extends the *override table* that
post-processes its `encoding` result. Because the sniffer is upstream and
unchanged, its outputs are taken directly as the modeled function's **inputs**
(an input-provenance, not an axiomatized contract): there is nothing for the
proof to assume about it, hence no `axiom` and no `axiom_check.py`. G-CONF drives
the real `mimetypes.guess_type` over fuzzed file names to produce `(guessed,
encoding)`, then compares the R/I shadow of the resolution against the real
patched `FileResponse` Content-Type.

For reference, the labels `mimetypes.guess_type` emits in the eval image
(observed): `.br → "br"`, `.Z → "compress"`, `.gz/.tgz → "gzip"`,
`.bz2 → "bzip2"`, `.xz → "xz"`; the wrapped (uncompressed) type is the guess for
the stripped name (e.g. `archive.tar.br → ("application/x-tar", "br")`,
`page.html.Z → ("text/html", "compress")`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16642`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`compressionMediaType`/`resolvedMediaType` (R/I-tagged ops) to Python and drives
the unchanged `mimetypes.guess_type` (the input-provenance callee) over fuzzed
file names; the oracle is the patched `FileResponse(...).headers["Content-Type"]`.
