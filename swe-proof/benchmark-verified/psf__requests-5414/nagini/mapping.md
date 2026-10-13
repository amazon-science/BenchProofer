# mapping.md — psf__requests-5414

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 39d0fdd9096f7dceccbc8f82e1eda7dd64717a8e`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `requests/models.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `screen_host(host, host_is_ascii, encodable)` | the host-validation slice of `PreparedRequest.prepare_url(self, url, params)` — `requests/models.py:360`; specifically the `if not unicode_is_ascii(host): … elif host.startswith(u'*'): raise InvalidURL(...)` block at `requests/models.py:401-407` | the modeled changed function (the leading-code-point screen the patch extends) |
| `is_invalid_leading(c)` | the membership test `host.startswith(u'*')` (pre-patch) / `host.startswith((u'*', u'.'))` (post-patch) — `requests/models.py:406` | pure spec: a single leading code point cannot begin a valid label iff it is `*`(42) or `.`(46) |
| `host_is_ascii` (bool param) | `unicode_is_ascii(host)` — `requests/_internal_utils.py:30`, called at `requests/models.py:401` | the UNCHANGED ASCII predicate's verdict, abstracted to one bit (selects the screen branch vs. the IDNA branch) |
| `encode_label(encodable)` *(axiom — A-consumed)* | `PreparedRequest._get_idna_encoded_host(host)` (which calls `idna.encode(host, uts46=True)`) — `requests/models.py:350-358`, called at `requests/models.py:403`; its `UnicodeError` is caught at `:404` and re-raised as `InvalidURL` at `:405` | the UNCHANGED internationalised-label encoder the non-ASCII branch defers to; the patch does not touch it |
| `InvalidLocator` (exception) | `requests.exceptions.InvalidURL` — raised at `requests/models.py:405` and `:407` with message `'URL has an invalid label.'` | the rejection both branches signal |

The change is a single one-line hunk inside the `elif` branch of the host
screen: `host.startswith(u'*')` → `host.startswith((u'*', u'.'))`. Everything
around it — the `if not unicode_is_ascii(host)` IDNA branch and its
`UnicodeError → InvalidURL` handling, and the netloc reconstruction below — is
byte-for-byte unchanged.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `host` (a `str`) | `List[int]` of Unicode code points | `host[k]` ↔ `ord(host[k])`; `len(host)` ↔ `len(host)`; the empty `str` ↔ `[]`. The slice is reached only after `if not host: raise InvalidURL(...)` (`requests/models.py:394-395`), so `host` is non-empty here — modelled by the precondition `len(host) > 0`. |
| `host.startswith(u'*')` / `host.startswith((u'*', u'.'))` | `is_invalid_leading(host[0])` (post) / `host[0] == 42` (pre) | `str.startswith(prefix)` for the single-character prefixes `'*'`(U+002A=42) and `'.'`(U+002E=46) is exactly "the first code point equals 42 (or 46)" — each prefix is one character, so `startswith` reduces to a first-code-point comparison. `startswith((a, b))` is the disjunction. |
| `unicode_is_ascii(host)` is truthy | the boolean `host_is_ascii` | `unicode_is_ascii` returns `True` iff `host.encode('ascii')` succeeds (`requests/_internal_utils.py:37-42`); abstracted to the single bit that selects the branch. It is UNCHANGED by the patch and inspected only to choose the branch, so its verdict is the sole observable. |
| `self._get_idna_encoded_host(host)` returns normally / raises `UnicodeError` | `encode_label(encodable)` returns normally / raises `InvalidLocator` | the IDNA encoder's only observable on this slice is whether the label is encodable: it returns the encoded host (normal) iff encodable, else raises `UnicodeError` (`requests/models.py:356-357`) which the slice immediately re-raises as `InvalidURL`. Abstracted by the boolean `encodable`; the rejection both forms collapse to `InvalidLocator`. |
| `raise InvalidURL('URL has an invalid label.')` | `raise InvalidLocator()` | user-defined exception stands in for the builtin-carrying `InvalidURL` (a builtin exception in an `Exsures` crashes the Nagini translator); only the raised/not-raised control flow is observed. The message string is not behaviour the F2P/P2P tests inspect (`pytest.raises(InvalidURL)` checks only the type). |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`;
the leading-code-point test is the comparison on `host[0]`.

**Termination:** the real host slice is bounded, straight-line code that always
answers (returns normally or raises `InvalidURL('URL has an invalid label.')`)
before `prepare_url` proceeds to netloc reconstruction, and
`_get_idna_encoded_host` is a bounded call that always answers (total over
{return str, raise UnicodeError} on the reachable non-ASCII domain — G-AX).
This total-correctness fact is carried as `Requires(MustTerminate(2))` on
`screen_host` and `Requires(MustTerminate(1))` on the `encode_label` axiom
(Nagini's default is partial correctness, under which a diverging
implementation would satisfy the contract vacuously).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `encode_label` ↔ `_get_idna_encoded_host` / `idna.encode(uts46=True)` (A-consumed)

**Callee:** `PreparedRequest._get_idna_encoded_host`, a static method that calls
`idna.encode(host, uts46=True).decode('utf-8')` and converts `idna.IDNAError`
into a bare `UnicodeError` (`requests/models.py:350-358`). In `prepare_url` the
call is wrapped in `try/except UnicodeError: raise InvalidURL('URL has an
invalid label.')` (`:402-405`). None of this is touched by the patch (the hunk
edits only the sibling `elif` branch).

Its only observable on the model's domain (a non-ASCII host — the only path on
which `encode_label` stands in for it) is whether the label is encodable:

  * it **returns the encoded host** (normal completion), so `prepare_url`
    proceeds, exactly when `idna.encode(host, uts46=True)` succeeds — the
    `encodable` case;
  * it **raises `UnicodeError`**, which `prepare_url` re-raises as `InvalidURL`,
    exactly when `idna.encode` raises `idna.IDNAError` — the not-`encodable`
    case.

This is the WEAKEST contract the screen's proof needs: the screen never inspects
the encoded value, it only sequences the ASCII-vs-IDNA branch decision. The
axiom is therefore `Ensures(encodable is True)` /
`Exsures(InvalidLocator, encodable is False)`, NOT any claim about which
concrete hosts encode (that would over-claim against `idna`'s exact behaviour).

**Soundness check (G-AX):** `axiom_check.py` runs the real
`PreparedRequest._get_idna_encoded_host` on a boundary oracle of non-ASCII hosts
(repository test inputs that must encode, e.g. `ジェーピーニック.jp`, `straße.de`,
`Königsgäßchen.de`, `☃.net`) plus randomized non-ASCII fuzz, asserting for each
that the call is total over `{encodable → returns a str, not-encodable → raises
UnicodeError}` — i.e. it never produces any other out-of-band signal. The check
is restricted to non-ASCII hosts, which is exactly the domain on which
`encode_label` abstracts the real callee. Exit 0 iff sound.

**Flag dependency:** `idna.encode(host, uts46=True)`. The `uts46=True` flag is
fixed in `_get_idna_encoded_host` and is part of the abstracted callee's
identity; the axiom is sound only under that flag (recorded here per the
SPEC_GUIDE flag-dependency rule). `axiom_check.py` calls the real
`_get_idna_encoded_host`, so it exercises exactly this flag configuration.

### 3.2 `host_is_ascii` ↔ `unicode_is_ascii(host)` (R, not an axiom)

`unicode_is_ascii` (`requests/_internal_utils.py:30-42`) returns `True` iff
`host.encode('ascii')` succeeds. It is UNCHANGED by the patch and its verdict is
abstracted to the boolean parameter `host_is_ascii` (a pure branch selector),
not modelled as a `@ContractOnly` axiom: the proof reasons over the abstract bit
directly, so it is an R-refinement of the predicate's verdict, not a consumed
axiom. Its behaviour is therefore not a trust point. (Recorded here for the
G-EQ/refinement audit.)
