# refinement.md — psf__requests-5414

Maps every operation in `implementation_validateHost` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `validateHost` (host-validation block of `prepare_url`)

Post-patch repo code (`patch.diff`, `requests/models.py:398-405`):
```python
if not unicode_is_ascii(host):
    try:
        host = self._get_idna_encoded_host(host)
    except UnicodeError:
        raise InvalidURL('URL has an invalid label.')
elif host.startswith((u'*', u'.')):
    raise InvalidURL('URL has an invalid label.')
# else: host accepted as-is
```

Lean impl (`implementation_validateHost`):
```lean
def implementation_validateHost (host : List Char) : Except Unit (List Char) :=
  Id.run do
    let mut h := host
    if !isAscii host then
      match idnaEncode host with
      | Except.ok enc => h := enc
      | Except.error () => return Except.error ()
    else if startsWithInvalid host then
      return Except.error ()
    return Except.ok h
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `host : List Char` | the parsed, non-empty `host : str` | **R** | per-code-point string ↔ `List Char`; element `i` ↔ code point `i` (mapping.md bijection; total/sound indexing, SPEC_GUIDE §2). |
| 2 | result `: Except Unit (List Char)` | raise `InvalidURL('URL has an invalid label.')` vs. carry `host` forward | **R** | `Except.error ()` ↔ the raised `InvalidURL` (both raise sites raise the identical message, so one error value); `Except.ok h` ↔ the host string used to build the netloc. |
| 3 | `if !isAscii host then …` | `if not unicode_is_ascii(host):` | **I** (deep model of unchanged callee) | branch selector. `isAscii host := host.all (c.toNat < 128)` models `unicode_is_ascii` exactly (`.encode('ascii')` succeeds iff all code points `< 128`). **A-reference** — validated == real callee by G-AX; no `_prop` axiom consumed. |
| 4 | `match idnaEncode host with \| ok enc => h := enc \| error () => return error ()` | `try: host = self._get_idna_encoded_host(host) except UnicodeError: raise InvalidURL(...)` | **A-reference** | `idnaEncode` is the UNCHANGED callee `_get_idna_encoded_host` (opaque; its IDNA internals are external and not the behavior under spec). On `ok` the encoded host is carried forward; on `error ()` (the caught `UnicodeError`) the host is rejected. The spec mirrors this leg verbatim (`result = idnaEncode host`), so the proof consumes no property of it. Excluded from the G-CONF differential (identical in both legs). |
| 5 | `else if startsWithInvalid host then return Except.error ()` | `elif host.startswith((u'*', u'.')): raise InvalidURL(...)` | **I** (deep model of the changed op) | **the fixed operation.** `startsWithInvalid host` is `true` iff the host's first code point is `'*'` or `'.'` (empty ⇒ `false`), exactly `host.startswith((u'*', u'.'))`. This is the line the patch edits (`startswith(u'*')` → `startswith((u'*', u'.'))`); modeled deeply, never axiomatized (SPEC_GUIDE §3). G-CONF differential-tests it. |
| 6 | `return Except.ok h` | fall through: `host` accepted, used to build netloc | **I** | the accepted-host path. For an ASCII host that is not reserved, `h = host`; for a non-ASCII host that encoded successfully, `h = enc`. |

The impl region contains **R/I + one A-reference** ops and NO consumed axiom, so
`conf_skip = false`: `conformance_check.py` differential-tests the R/I leg (the
ASCII validation decision) against an in-process replica of the patched
behavior. The non-ASCII leg (op 4) delegates to the unchanged real callee and is
identical in both legs by construction, so it is not part of the differential.

## Soundness check (verify ⟹ correct)

- `problem_spec_validateHost host result` pins the outcome EXACTLY for every
  host: in the ASCII case `result` is determined to be `error ()` iff the host
  begins with a reserved leading character and `ok host` otherwise; in the
  non-ASCII case `result = idnaEncode host` (full equality to the unchanged
  callee's outcome). Directive 5 (frame): no output component is left
  unconstrained — `result` is fully determined. Directive 8: the postcondition is
  grounded in the input host via the structural predicates `isAscii` /
  `startsWithInvalid`, not an opaque oracle; the only opaque term `idnaEncode`
  governs the unchanged branch the patch does not touch, and it appears
  identically on both sides so the result must be *produced by* the modeled
  decision.
- The prepatch impl tests only `host.startswith(u'*')` (op 5's selector becomes
  `c == '*'`). It violates the spec on the discriminating clause: an all-ASCII
  host beginning with `'.'` (e.g. `.example.com`), where `isAscii host = true`,
  `startsWithInvalid host = true`, so the spec requires `result = Except.error ()`
  but the prepatch returns `Except.ok host`. Its carried gold proof cannot close
  (G-DIFF/G-PANEL).
- This discriminating case is exactly the FAIL_TO_PASS test
  `test_invalid_url[InvalidURL-http://.example.com]`: a host `.example.com` that
  is pure ASCII and begins with a dot; the patched code raises `InvalidURL` while
  base_commit accepted it (the `idna` empty-label path that produced the reported
  `UnicodeError` is avoided because the host is ASCII and never reaches the IDNA
  encoder). The PASS_TO_PASS `http://*example.com` (leading `*`) remains rejected
  by both, confirming the `'*'` behavior is preserved.
- G-CONF confirms the R/I ASCII leg == an in-process replica of the patched
  `startswith((u'*', u'.'))` validation over hand-picked edge cases (leading `*`,
  leading `.`, empty host, ordinary hosts) plus ≥1e5 fuzzed ASCII hosts.
