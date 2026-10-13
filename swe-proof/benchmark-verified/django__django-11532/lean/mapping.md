# mapping.md — django__django-11532

## Symbol binding (file:line @ base_commit a5308514fb4bc5086c9a16a8a24a945eeebb073c)

Modeled function: `hostName` (Lean) ↔ `CachedDnsName.get_fqdn`
(`django/core/mail/utils.py:14-17` @ base_commit).

This is the site the `problem_statement` points at: the locally-reported host
name (`socket.getfqdn()`) is cached and later stamped into mail metadata
(the `Message-ID` header, via `make_msgid(domain=DNS_NAME)` in
`django/core/mail/message.py`). The crash in the issue occurs because that
cached name is non-ASCII and cannot be emitted in a non-unicode header
encoding. The fix Punycode-encodes the name at the point it is cached:

```python
# post-patch get_fqdn (utils.py)
def get_fqdn(self):
    if not hasattr(self, '_fqdn'):
        self._fqdn = punycode(socket.getfqdn())
    return self._fqdn
```

where the introduced helper is

```python
# django/utils/encoding.py (post-patch)
def punycode(domain):
    """Return the Punycode of the given domain if it's non-ASCII."""
    return domain.encode('idna').decode('ascii')
```

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

The modeled surface is a STATE TRANSITION, not a pure function: `get_fqdn` is a
method on a `CachedDnsName` instance whose whole relevant state is the single
attribute `_fqdn`, and the call both reads and writes it. `NameHolder` is that
instance's modeled state, and `implementation_hostName` maps the state before the
call to the pair (state after the call, value returned).

| Lean | Python | note |
|---|---|---|
| `st : NameHolder` | the `CachedDnsName` instance before the call | its whole modeled state is the one storage slot below |
| `st.slot = none` | the instance has NO `_fqdn` attribute (`hasattr(self,'_fqdn')` is false) | the unsettled state; `DNS_NAME` is in this state at import and returns to it whenever a caller does `delattr(DNS_NAME,'_fqdn')` |
| `st.slot = some n` | `self._fqdn == n` (attribute present, holding `n`) | the settled state. Presence, not truthiness: a stored empty name is `some ""`, which `hasattr` reports as present |
| `reportedName : String` | the host name `socket.getfqdn()` reports (`str`) | the OS-reported local name; arbitrary unicode |
| `result.1 : NameHolder` | the instance's slot state AFTER the call | `result.1.slot = some n` ⟺ `_fqdn` is present afterwards and holds `n` |
| `result.2 : String` | the value `get_fqdn()` returns (`str`) | the name used for mail metadata |
| `aceEncode : String → String` | `domain.encode('idna').decode('ascii')` (the body of `punycode`), **on the codec's own domain only** — see the domain restriction below | unchanged stdlib IDNA/ACE codec — see callee provenance |

Bridge: a Lean `String` corresponds to the Python `str` of identical
code points. `aceEncode` corresponds to running the IDNA/ACE encoder
(`str.encode('idna').decode('ascii')`); `implementation_hostName st reportedName`
corresponds to invoking `get_fqdn` on an instance whose `_fqdn` state is `st`,
with the `socket.getfqdn()` result substituted as `reportedName`, and reading
BOTH observables afterwards — the instance's `_fqdn` state and the returned
value.

### Why `_fqdn`'s presence is modeled and not elided as a caching detail

The `if not hasattr(self, '_fqdn')` wrapper is NOT an internal shortcut with no
observable effect. `DNS_NAME` is a module-level singleton that callers hold
directly, and the attribute is part of its interface in both directions:

- the FAIL_TO_PASS test `test_non_ascii_dns_non_unicode_email`
  (`tests/mail/tests.py`) begins by clearing it — `del DNS_NAME._fqdn` — so that
  its `socket.getfqdn` mock takes effect. That statement REQUIRES the attribute
  to be present, i.e. it requires the preceding call to have left a name
  stored. An implementation that returns the correct Punycode name but never
  assigns `self._fqdn` makes this `del` raise `AttributeError`, and the test
  errors before reaching its assertion;
- symmetrically, whether the attribute is present decides whether a later call
  consults `socket.getfqdn()` again, which is the entire point of the class.

So both the presence of `_fqdn` and the value it holds are directly observable
by the official test suite, and `problem_spec_hostName` constrains both
components of `result` accordingly (clause 1, OCCUPANCY). A value-only reading
of this surface — one whose `result` is just a `String` — cannot express the
`del`-ability the test depends on, and admits the "return the right name, store
nothing" implementation as correct.

## Callee provenance + flag deps

- `aceEncode` (opaque) ↔ `str.encode('idna').decode('ascii')`: the Python
  standard-library IDNA codec (`encodings.idna`), an UNCHANGED callee. The patch
  does not modify it; it only (a) names it `punycode` and (b) starts calling it
  on the host name inside `get_fqdn`. There is no flag dependency: the encoder is
  applied unconditionally to the host name in the post-patch code (the `punycode`
  helper itself contains no ASCII fast-path branch — the conditional in its
  docstring is descriptive of the IDNA codec's own behavior, which already leaves
  pure-ASCII labels unchanged).
- No `axiom aceEncode_prop` is consumed by the proof: `problem_spec_hostName`
  pins the settled name to `aceEncode reportedName` and the impl stores and
  serves exactly `aceEncode reportedName`, so `correct_hostName` closes by case
  analysis on the slot with `simp` on each arm — no property of the encoder is
  assumed or needed (measured: `#print axioms correct_hostName` reports
  `[propext, Quot.sound]`, both standard, and no bundle-local axiom). The opaque
  is declared only so the encoder can appear in the executable impl. Hence G-AX
  has nothing to validate (skip stub).
- Because the encoder is opaque, it is a term the proofs may quantify over but
  cannot compute with: no proof in this bundle can conclude `aceEncode s = s`
  for an ASCII `s`, nor `aceEncode s ≠ aceEncode t` for `s ≠ t`. The G-PBT
  refutation witnesses therefore CONDITION on the encoder (`aceEncode <input> ≠
  <the rival's answer>`) instead of computing it; see properties.py.

### DOMAIN RESTRICTION on `aceEncode` (binding on any refinement)

`aceEncode` has the Lean type `String → String`, i.e. it is TOTAL in the model.
Its Python counterpart is NOT total: `str.encode('idna')` raises
`UnicodeError` for a name it rejects — notably any name with a label longer than
63 characters (`UnicodeError: label too long`) and any name with an empty label.
Measured, for every host name `h` in the fuzz corpus,
`punycode(h + 'a' * 70)` raises.

The bijection above is therefore asserted ON THE CODEC'S DOMAIN ONLY: the Lean
term `aceEncode t` corresponds to the Python expression `punycode(t)` exactly
when `t` is a name the codec accepts, and corresponds to NOTHING otherwise. Two
consequences, both binding:

1. `conformance_check.py` treats an input the real codec rejects as outside the
   modeled domain and requires the shadow and the real callee to raise on
   exactly the same inputs (it compares error classes). That is what makes the
   restriction mechanically enforced rather than merely asserted here.
2. A candidate implementation is a REFINEMENT of a Lean variant only if every
   `aceEncode t` it evaluates is applied to a name the codec accepts. An
   implementation that invokes the codec on a fabricated argument outside that
   domain — e.g. `punycode(reported + 'a' * 70)`, even where its answer is
   immediately discarded (`[:0]`) — is NOT a faithful refinement of a Lean term
   built from the total `aceEncode`, because in Lean that term denotes a string
   and in Python that call raises before the method can return. Such a candidate
   does not exhibit the Lean variant's behavior at all: it raises on every
   input, and the failure is visible far outside the modeled surface (measured:
   FAIL_TO_PASS 1/1 fails and 90/148 PASS_TO_PASS fail, because every test that
   builds a message reaches `DNS_NAME.get_fqdn()` for its `Message-ID`).

Recorded because the totality of the modeled carrier is the one place where this
bundle's model is weaker than the code it models, and a reader comparing a Lean
variant against a Python diff has to know which side the domain restriction lives
on. A model that closed the gap structurally — `opaque aceEncode : String →
Option String`, with the modeled outcome an `Option (NameHolder × String)` whose
`none` is the raised rejection, and a PROPAGATION clause pinning the failing arm
— was drafted and measured against this same rival family; see the note at the
end of refinement.md.

## G-CONF fuzz seed (pinned)

`seed = 11532` (used by `conformance_check.py`; see that file).
