# refinement.md — django__django-11532

Maps every operation in `implementation_hostName` to its `patch.diff`
counterpart in `django/core/mail/utils.py::CachedDnsName.get_fqdn` (the modeled
representative — see mapping.md). Tags: **R** type-refinement, **A-consumed**
proof uses a callee axiom, **A-reference** deep-modeled changed op validated ==
real callee, **I** identical concrete op.

## Patch (post-patch `get_fqdn`)
```python
def get_fqdn(self):
    if not hasattr(self, '_fqdn'):
        self._fqdn = punycode(socket.getfqdn())   # punycode(d) = d.encode('idna').decode('ascii')
    return self._fqdn
```

## Operation correspondence

`get_fqdn` is a method, so the modeled op sequence is a state transition on the
receiver: the impl threads a `NameHolder` (the receiver's modeled `_fqdn` state
— mapping.md) and returns the pair (state afterwards, value returned). Every
line of the four-line patched body has a modeled counterpart, INCLUDING the
`hasattr` guard and the assignment, because both are observable (mapping.md,
"Why `_fqdn`'s presence is modeled").

| # | Lean op (`implementation_hostName`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut holder := st` | the receiver `self` on entry, whose modeled state is whether `_fqdn` is present and what it holds | R | `NameHolder ↔ the `_fqdn` state`: `slot = none ↔ hasattr(self,'_fqdn')` false, `slot = some n ↔ self._fqdn == n`. The OS-reported host name enters separately as `reportedName ↔ socket.getfqdn()` (`str ↔ String`). |
| 2 | `if holder.slot = none then` | `if not hasattr(self, '_fqdn'):` | I | the same guard on the same observable. Emptiness is tested as `slot = none`, i.e. attribute ABSENCE, matching `hasattr` and not truthiness — a stored empty name is `some ""` and does not re-settle. |
| 3 | `holder := { holder with slot := some (aceEncode reportedName) }` | `self._fqdn = punycode(socket.getfqdn())` — i.e. `socket.getfqdn().encode('idna').decode('ascii')` | R | the introduced `punycode(...)` call IS the fix, and the ASSIGNMENT is the modeled state write. `aceEncode : String → String ↔ str.encode('idna').decode('ascii')`, the unchanged stdlib IDNA/ACE codec (mapping.md callee provenance). The single behavioral edit: the host name is now run through the ASCII-compatible encoder before being stored as the metadata name. |
| 4 | `let served := holder.slot.getD (aceEncode reportedName)`; `return (holder, served)` | `return self._fqdn` | I | serve the name the slot now holds. The `getD` default is unreachable — after op 3 the slot is occupied on both arms — so the encoder is invoked exactly once, on the settle path, exactly as the real callee invokes it once inside the guard. The returned pair exposes the receiver's state afterwards alongside the value, which is what makes op 3's write checkable. |

Every op is R or I; **no A row** is *consumed*: `aceEncode` is declared `opaque`
purely so the unchanged codec can appear in the executable impl, and the proof
closes by case analysis on the slot (`simp` on each arm) without assuming any
property of the encoder. No `axiom aceEncode_prop` is declared, so there is no
A-consumed and no A-reference. Therefore `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

### Why the state is modeled rather than abstracted away
A value-only model of this surface (`hostName : String → String`) is refuted by
the official test: `test_non_ascii_dns_non_unicode_email` opens with
`del DNS_NAME._fqdn`, which requires the attribute to be PRESENT, so an
implementation that returns `punycode(socket.getfqdn())` without assigning
`self._fqdn` returns the exactly-correct value on the whole domain and still
fails the FAIL_TO_PASS test with `AttributeError`. Op 3's write is therefore a
behavioral obligation, not a caching detail, and clause 1 (OCCUPANCY) of
`problem_spec_hostName` is what carries it. The corresponding rival is
`weak-drop-occupancy` in properties.py.

## R/I legs ⇒ G-CONF
The impl is R/I (no A-tagged op), so `conformance_check.py` mechanically
differential-tests the impl shadow (`aceEncode` realized as the real
`str.encode('idna').decode('ascii')`) against `patch.diff` behavior — i.e. the
patched `get_fqdn` invoked on a `CachedDnsName` put into the fuzzed slot state,
with `socket.getfqdn()` mocked to the fuzzed name — over ≥10^5 fuzzed inputs.
BOTH modeled observables are compared: the instance's `_fqdn` state after the
call (against `result.1.slot`) and the returned value (against `result.2`), so
op 3's state write is checked against the real callee and not only op 4's value.
Both slot shapes are driven for every fuzzed name, so the settle path (op 3) and
the reuse path (guard false) are each exercised. `conf_skip = false`.

## Prepatch = the real bug
`Solution_prepatch.lean` omits the encoder in op #3: it settles the slot with the
reported host name verbatim (`slot := some reportedName`, and correspondingly
`getD reportedName` in op #4). Ops #1, #2 and the state write itself are
unchanged, so the twin differs from gold in exactly the one behavioral edit the
patch makes. That is precisely the pre-patch `get_fqdn`
(`self._fqdn = socket.getfqdn()`), the real bug from the issue: a non-ASCII
reported name is stored and served verbatim and crashes when serialized into a
non-unicode mail header. It cannot satisfy clause 3 (SETTLING) of
`problem_spec_hostName` — which demands the settled name be
`aceEncode reportedName` — for any `reportedName` whose ACE form differs from
itself (every non-ASCII name), so its `correct_hostName` is unclosable ⇒ G-DIFF
fails verification as required. Note the twin DOES satisfy clauses 1 and 2
(it occupies the slot and serves the stored name on reuse), which is what makes
it a minimal single-edit counterpart rather than a differently-broken program.

## Sibling sites (NOT separately modeled — behavior-preserving refactors)
`patch.diff` also touches four other call sites. These are NOT independent
behavioral fixes: they replace the inline idiom
`x.encode('idna').decode('ascii')` with a call to the newly-extracted
`punycode(x)` helper, whose body IS that same idiom. The observable behavior of
each site is unchanged:

- `django/utils/encoding.py`: *adds* the `punycode` helper (the extracted idiom).
- `django/core/mail/message.py::sanitize_address`: `domain.encode('idna').decode('ascii')` → `punycode(domain)` (inside the same `try/except UnicodeEncodeError`).
- `django/core/validators.py` (URLValidator, EmailValidator): `netloc/domain_part.encode('idna').decode('ascii')` → `punycode(...)`.
- `django/utils/html.py` (`urlize`, `is_email_simple`): `netloc/domain.encode('idna').decode('ascii')` → `punycode(...)`.

Only `get_fqdn` changes behavior (it previously did NOT encode at all), and only
that site is exercised by the FAIL_TO_PASS test
(`test_non_ascii_dns_non_unicode_email`, which mocks `socket.getfqdn` to a
non-ASCII name and asserts the resulting `Message-ID` contains the Punycode
`@xn--p8s937b>`). `patch.diff` (gold verbatim) applies all five edits so the
official harness resolves.

## Note: the carrier's totality, and a measured stronger model

The one place this model is weaker than the code it models is the TOTALITY of
`aceEncode`. In Lean it is `opaque aceEncode : String → String`; the real codec
is partial and raises `UnicodeError` on a name it rejects (mapping.md, "DOMAIN
RESTRICTION"). A pure total carrier cannot express a discarded computation, so a
Lean variant may evaluate `aceEncode t` for a fabricated `t`, discard the answer,
stay extensionally equal to gold, and verify — while a Python transcription that
actually calls `punycode(t)` raises. mapping.md records why such a transcription
is not a faithful refinement (the Lean term denotes a string; the Python call
raises before returning), which is where that family is ruled out today.

A model that closes the gap STRUCTURALLY rather than by that argument was drafted
and measured:

- `opaque aceEncode : String → Option String` — `none` is the codec's rejection;
- the modeled outcome becomes `Option (NameHolder × String)`, whose `none` is the
  request failing because the encoding it had to perform was rejected;
- three exhaustive clauses, each pinning the outcome outright: REUSE (occupied
  slot ⇒ succeed, serve the stored name, holder unchanged), SETTLING (unoccupied
  slot and the encoder accepts ⇒ succeed, serve the encoding, slot left holding
  exactly it), PROPAGATION (unoccupied slot and the encoder rejects ⇒ fail, and
  settle nothing).

Measured on that draft (`scripts/lean_verify.sh`, `#print axioms`): gold verifies
with `[propext, Quot.sound]` and the determinism theorem needs no axioms; nine
rivals are refuted, including BOTH shapes of the fabricated-argument family (one
propagating the rejection of `reportedName ++ 70×"a"` from the settling arm, one
from the reuse arm) and a new `absorb-rejection` rival that serves the raw name
instead of failing; and four correct reshapes verify, including one that
evaluates the encoder on that same fabricated argument and DISCARDS the answer.

That last pair is the point of the design: the partial carrier splits the family
in two and each half lands correctly. An implementation that PROPAGATES the
fabricated argument's rejection — which is what the crashing Python actually does
— is refuted by SETTLING. An implementation that DISCARDS it verifies, and its
faithful Python is then necessarily a guarded call (`try: punycode(padded)
except UnicodeError: pass`), which does not crash and does resolve. So
verify ⇒ correct holds on both halves by construction rather than by an argument
about which transcriptions count as faithful.

NOT LANDED here: the change rewrites the axioms, post-conditions, impl and proof
regions, so it voids the recorded G-EQ/G-PANEL audit (their digests cover
Solution.lean and properties.py) and requires the full battery and a fresh audit
to be re-derived against the new shape. It is recorded so the next repair round
starts from a measured design rather than re-deriving it.
