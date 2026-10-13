# mapping.md — psf__requests-5414

## Symbol binding (file:line @ base_commit 39d0fdd9096f7dceccbc8f82e1eda7dd64717a8e)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_validateHost` / `problem_spec_validateHost` | the host-label validation block inside `requests.models.PreparedRequest.prepare_url` | `requests/models.py:398-405` |
| `isAscii` (pure helper) | `requests._internal_utils.unicode_is_ascii` | `requests/_internal_utils.py:30-42` |
| `startsWithInvalid` (pure helper) | the `host.startswith((u'*', u'.'))` reserved-leading-character test | `requests/models.py:405` |
| `idnaEncode` (opaque callee) | `requests.models.PreparedRequest._get_idna_encoded_host` | `requests/models.py:350-358` |

The modeled fragment is the host-validation step of `prepare_url`. After the URL
is parsed and the empty-host case is rejected, the parsed `host` string is
validated and (for international names) encoded. This is the only behavior the
gold patch changes and the only behavior the FAIL_TO_PASS test
(`test_invalid_url[InvalidURL-http://.example.com]`) observes.

### What the modeled fragment does (base_commit)

```python
# host is the already-parsed, non-empty host string.
if not unicode_is_ascii(host):
    try:
        host = self._get_idna_encoded_host(host)   # IDNA-encode international name
    except UnicodeError:
        raise InvalidURL('URL has an invalid label.')
elif host.startswith(u'*'):                          # base_commit: only '*'
    raise InvalidURL('URL has an invalid label.')
# otherwise: host is accepted as-is
```

- `unicode_is_ascii(host)` returns `True` iff every code point of `host` encodes
  in ASCII, i.e. every code point is `< 128`.
- A host with any non-ASCII code point is routed through `_get_idna_encoded_host`,
  which returns the encoded host on success and raises `UnicodeError` on failure;
  `prepare_url` catches that and raises `InvalidURL`.
- A pure-ASCII host is accepted unchanged UNLESS it begins with a reserved
  leading character. At base_commit only `'*'` is rejected; an ASCII host
  beginning with `'.'` (an empty leading label, e.g. `.example.com`) passes this
  test and is accepted, which the issue reports as the wrong outcome.

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Python | Lean | bijection |
|---|---|---|
| `host : str` (per-code-point ops: `startswith`, ascii test) | `host : List Char` | element `i` ↔ code point `i`; total/sound indexing (SPEC_GUIDE §2). |
| outcome of the validation block | `Except Unit (List Char)` | `Except.error ()` ↔ `raise InvalidURL('URL has an invalid label.')`; `Except.ok h` ↔ the host string carried forward (the accepted ASCII host, or the IDNA-encoded host). The two distinct raise sites (IDNA failure, reserved leading char) raise the SAME `InvalidURL`, so both map to the single `Except.error ()`. |
| `unicode_is_ascii(host)` | `isAscii host : Bool` | `host.all (fun c => c.toNat < 128)` — `True` iff every code point `< 128`. |
| `host.startswith((u'*', u'.'))` (post-patch) | `startsWithInvalid host : Bool` | `true` iff `host`'s first code point is `'*'` or `'.'` (empty list ⇒ `false`). |
| `self._get_idna_encoded_host(host)` (+ caught `UnicodeError`) | `idnaEncode host : Except Unit (List Char)` | `Except.ok encoded` ↔ successful IDNA encoding; `Except.error ()` ↔ the raised `UnicodeError` (which `prepare_url` rethrows as `InvalidURL`). |

The validation block mutates `host`/raises; we model it as a pure function from
the parsed host to the validation outcome.

## Callee provenance + flag dependencies

- **`isAscii` — A-reference (deep model).** `unicode_is_ascii` is an UNCHANGED
  callee. It is modeled DEEPLY as `host.all (fun c => c.toNat < 128)`, exactly its
  observable contract (`.encode('ascii')` succeeds iff all code points `< 128`).
  Validated against the real callee by `axiom_check.py` (G-AX). No `_prop` axiom
  is consumed — the model IS the behavior.
- **`startsWithInvalid` — the changed decision, modeled deeply (R/I).** This is
  the operation the patch edits (`startswith(u'*')` → `startswith((u'*', u'.'))`).
  Modeled structurally over the host's first code point — NEVER axiomatized
  (SPEC_GUIDE §3). G-CONF differential-tests it.
- **`idnaEncode` — opaque, unchanged real callee (A-reference).**
  `_get_idna_encoded_host` is an UNCHANGED callee invoked only on non-ASCII
  hosts. Its internal IDNA algorithm is external (the `idna` package) and is NOT
  the behavior under spec, so it is declared `opaque` and used identically in
  both the spec and the implementation; the proof consumes NO property of it
  (the non-ASCII branch is discharged by case analysis on its return value). It
  therefore carries no `_prop` axiom and is excluded from the G-CONF differential
  (the non-ASCII leg is identical in both legs by construction).
- **Flag dependency.** The branch selector is `unicode_is_ascii(host)`; there are
  no other configuration flags. G-AX fuzzes ASCII and non-ASCII hosts.

## G-CONF fuzz seed

Pinned LCG seed: **5414** (see `conformance_check.py` `SEED`). Corpus: ASCII host
strings (the R/I leg), length 0–10, code points drawn from a mix of `'*'`, `'.'`,
ASCII letters/digits and other punctuation so the reserved-leading-character
decision is exercised in every position, over ≥1e5 fuzzed inputs, diffed against
an in-process replica of the post-patch validation outcome. The non-ASCII branch
delegates to the unchanged `_get_idna_encoded_host` callee (A-reference) and is
identical in both legs, so it is not part of the differential.
