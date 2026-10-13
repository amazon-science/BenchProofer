# mapping.md — astropy__astropy-14096

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 1a4462d72eb03f30dc83a879b1dd57aac8b2c18b`, states the type
abstraction, and gives the provenance of the axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `astropy/coordinates/sky_coordinate.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolve_missing(name, …)` | `SkyCoord.__getattr__(self, attr)` — `astropy/coordinates/sky_coordinate.py:869` (body lines 874-900) | the modeled changed function: the fallback attribute resolver, invoked by the interpreter only after ordinary attribute lookup has already failed for `attr` |
| `name` (`int`) | `attr` (`str`) — the requested attribute name | requested-name symbol id |
| `is_alias`, `alias_value` | `self._is_name(attr)` test (`:875`) and its `return self` (`:876`) | first domain resolution (frame-name alias) |
| `is_frame_attr`, `frame_attr_value` | `attr in frame_transform_graph.frame_attributes` test (`:881`) and the value it returns (`getattr(self.frame, attr)` `:883` / `getattr(self, "_"+attr, None)` `:885`) | second domain resolution (frame attribute) |
| `is_frame_passthrough`, `passthrough_value` | `not attr.startswith("_") and hasattr(self._sky_coord_frame, attr)` test (`:889`) and `getattr(self._sky_coord_frame, attr)` (`:890`) | third domain resolution (frame passthrough) |
| `is_transform`, `transform_value` | `frame_cls is not None and self.frame.is_transformable_to(frame_cls)` test (`:893-894`) and `self.transform_to(attr)` (`:895`) | fourth domain resolution (transform target) |
| `frame_attr_step(name, value)` *(axiom — A-consumed)* | the frame-attribute branch's value expression — `getattr(self.frame, attr)` (`:883`) / `getattr(self, "_" + attr, None)` (`:885`) | the PARTIAL step leg 2 performs; running a subclass descriptor here can itself raise, and the resolver then surfaces that failure |
| `frame_attr_step_succeeds(name)` *(axiom — A-consumed)* | whether that value expression completes rather than raising, for this `(self, attr)` | leg 2's own path selector |
| `passthrough_step(name, value)` *(axiom — A-consumed)* | `getattr(self._sky_coord_frame, attr)` (`:890`) | the PARTIAL step leg 3 performs |
| `passthrough_step_succeeds(name)` *(axiom — A-consumed)* | whether that `getattr` completes rather than raising | leg 3's own path selector |
| `transform_step(name, value)` *(axiom — A-consumed)* | `self.transform_to(attr)` (`:895`) | the PARTIAL step leg 4 performs; **measured** to raise for registered frame names the coordinate cannot be transformed to (`altaz`/`hadec` need an observer `location`, `teme` a `scale`, the Galactocentric/LSR/heliocentric families full 3D data) |
| `transform_step_succeeds(name)` *(axiom — A-consumed)* | whether `self.transform_to(attr)` returns rather than raising, for this `(self, attr)` | leg 4's own path selector |
| `residual_step(name)` *(axiom — A-consumed)* | `self.__getattribute__(attr)` — the object-mechanism call the changed leg evaluates (post-change `sky_coordinate.py:898`); `object.__getattribute__` is the CPython attribute-lookup machinery | the PARTIAL step leg 5 performs |
| `residual_step_subject(name)` *(axiom — A-consumed)* | the `name` carried by the `AttributeError` that step surfaces on its failing path — the genuinely-missing name reached inside the descriptor/property invoked for `attr`, in general distinct from `attr` | the subject the surfaced failure blames |
| `residual_step_succeeds(name)` *(axiom — A-consumed)* | whether that step RESOLVES `attr` (returns) rather than raising `AttributeError` | leg 5's own path selector |
| `residual_step_value(name)` *(axiom — A-consumed)* | the value that step returns when it resolves `attr` | the value leg 5's succeeding path yields |
| `*_step_performed(name)` *(abstract capabilities — one per partial leg, granted by that step's two paths)* | the fact that the surfaced outcome was produced BY that leg's own repo expression actually running — not fabricated by the resolver, and not borrowed from a different leg | the control-flow effect discriminator: unforgeable `@ContractOnly @Predicate`s with no body (directive-8); each one's SOLE producers are its own step's `Ensures` and `Exsures`, so an impl that echoes a pure oracle — or performs another leg's step — cannot discharge the clause |
| `AttributeAccessError(subject)` | the `AttributeError` raised on the failing path (its message names the blamed attribute) | user-defined stand-in (a builtin exception in an `Exsures` crashes the Nagini translator; §2) |

The pre-patch repo construct the change removes (for the refinement audit, not
referenced from the consumer spec view): the explicit
`raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attr}'")`
at `sky_coordinate.py:897-900`, whose subject is `attr` itself.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| attribute name `attr` (`str`) | `name` (`int`) — a stable symbol id, one per distinct name | distinct names ↔ distinct ids; the only observable the F2P test reads is WHICH name the surfaced error blames (`pytest.raises(AttributeError, match="random_attr")`), i.e. an *identity comparison* between names, which `int` equality models faithfully — never the characters (Nagini bans `str` indexing) |
| each domain-resolution test (a `bool`-valued guard over `self`, `attr`, and global frame state) | a `bool` parameter (`is_alias`, …) | the runtime truth value of that guard for the given call; their priority order is preserved exactly. The repo wraps all four in an outer `"_sky_coord_frame" in self.__dict__` test (`:874`); an object lacking that entry makes every guard False, which the model represents by all four flags False — the same no-resolution leg, so the outer guard needs no separate carrier (conformance_check.py feeds half-built objects explicitly) |
| the value each domain resolution would return (a coordinate / frame attribute / transformed frame) | a paired `int` parameter (`alias_value`, …) | an opaque value token; the test never inspects the returned value on the resolving paths, only that the right branch's value is produced |
| `AttributeError` (raised on the failing path) | `AttributeAccessError(subject)` + `Exsures` | a builtin-exception `Exsures` crashes the Nagini translator (SPEC_GUIDE §2); one user-defined exception carries the blamed-name symbol id. The test observes the blamed name, modelled by `subject` |

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 The five step axioms ↔ the repo expressions each leg evaluates (A-consumed)

**The alias leg is the only TOTAL one.** `return self` (`:876`) cannot fail, so
leg 1 needs no selector and no capability, and the consumer pins it
unconditionally.

**The other four legs are PARTIAL, and that is the central fact this map
records.** The expression each leg evaluates can itself raise, and because each
leg is a `return` of that expression, the failure becomes `__getattr__`'s own
outcome. A spec pinning any of these legs as a total value equality would reject
a faithful implementation of the real function. Measured on the repo at
`base_commit` (and identically with the change applied — these legs are unchanged
by it):

| leg | expression | measured failing inputs |
|---|---|---|
| 2 frame attribute | `getattr(self, "_" + attr, None)` (`:885`) | a subclass descriptor named `_<frame_attr>` that raises: `__getattr__(obj, "equinox")` → `TypeError` |
| 3 frame passthrough | `getattr(self._sky_coord_frame, attr)` (`:890`) | (the GUARD is what raises here — see the bridge note below) |
| 4 transform target | `self.transform_to(attr)` (`:895`) | `altaz`, `hadec` → `AttributeError("'NoneType' object has no attribute 'to_geodetic'")` (no observer `location`); `teme` → `AttributeError(… 'scale')`; `lsr`/`lsrd`/`lsrk`/`galacticlsr`/`heliocentriceclipticiau76` → `TypeError` (insufficient position data); `galactocentric` → `ConvertError`; `hcrs`/`heliocentric*ecliptic` → `UnitsError`. Note these are NOT all `AttributeError`. |
| 5 residual | `self.__getattribute__(attr)` (`:898` with the change applied) | any name it cannot resolve → `AttributeError` blaming the name it found missing |

So each partial leg is axiomatised with its own two-path contract keyed to its own
`*_step_succeeds(name)` selector, and each grants its own
`*_step_performed(name)` capability. The selectors are the step's own facts, not
choices the resolver makes; the capabilities are bodyless `@ContractOnly
@Predicate`s (directive-8 control-flow grounding) whose sole producers are that
step's two paths, so an impl can neither fabricate a leg's outcome by echoing a
pure oracle nor pass one leg's work off as another's.

**A note on the passthrough leg's GUARD (a type-bridge edge, not a model gap).**
The guard `hasattr(self._sky_coord_frame, attr)` (`:889`) swallows only
`AttributeError`, so for velocity/differential names on a coordinate without
velocity data the guard ITSELF raises out of `__getattr__` — measured:
`radial_velocity`, `proper_motion`, `velocity` → `ValueError`; `pm_dec`,
`pm_ra_cosdec`, `sphericalcoslat` → `TypeError`. The model takes the guards as
boolean INPUTS (§2), so for such an input no boolean exists to supply and there is
no corresponding model input at all. `conformance_check.py` probes these names
explicitly and reports them as outside-the-bridge (12 inputs) rather than
silently dropping them, so the coverage claim stays honest.

**Why leg 5's subject matters (the regression scenario, gh-8340):** when `attr`
names a computed accessor (a `property`/descriptor) on a subclass,
`__getattribute__` runs that accessor; if the accessor body reads a *different*,
genuinely-absent attribute `inner`, the `AttributeError` that propagates blames
`inner`, not `attr`. So `residual_step_subject(attr) == inner ≠ attr`. For the
F2P case `attr = "prop"` (a property whose body does `return self.random_attr`),
`residual_step_subject("prop") == "random_attr"`. When `attr` names nothing at
all, the explicit `self.__getattribute__(attr)` call does NOT re-enter
`__getattr__` — the interpreter's implicit fallback is triggered by
attribute-access syntax, not by a direct `__getattribute__` call — so the
`AttributeError` comes straight back out and the blamed subject is that name
itself; the axiom's "function of name" still holds
(`residual_step_subject(name) == name` in that degenerate case).

**Leg 5's succeeding path is reachable and is real behaviour, not a modelling
artifact.** Many names that fail all four guards are nonetheless resolved by the
residual step: plain class attributes on a subclass, instance-`__dict__` entries,
bound methods, and dunders. Measured on the reference with the change applied:
all four guards False, `__getattr__(obj, "CLASS_CONST")` returns `12345`, and
`__getattr__(obj, "_sky_coord_frame")` returns the frame object — while
`__getattr__(obj, "prop")` raises `AttributeError('… no attribute
'random_attr'')`. This is why the consumer's leg-5 returning path is CONDITIONAL
on the selector rather than forbidden.

**Soundness check (G-AX):** `axiom_check.py` runs INSIDE the instance image (real
`astropy`), constructs `SkyCoord` subclasses with a property `p` whose body reads
a missing inner attribute `q`, and for many distinct `(p, q)` name pairs
(boundary + fuzz) asserts that `obj.__getattribute__(p)` raises `AttributeError`
whose message blames `q` and NOT `p` — i.e. `residual_step_subject(p) == q ≠ p`,
exactly leg 5's `Exsures`. It also confirms determinism, the degenerate "plain
missing name blames itself" case, and — the direction that keeps the axiom honest
— that for names the step RESOLVES (class attributes, instance-dict entries,
bound methods, dunders) `__getattribute__` returns normally and deterministically,
and that the resolve/fail selector is exclusive and stable. An axiom asserting the
step never returns would fail this last group. The check is valid on the repo
without the change applied because `__getattribute__` is unchanged by it. Exit 0
iff every observation meets the axiom.

The check imports only `astropy.coordinates` (the package under test, resolved
from `/testbed`) and the standard library — nothing scaffolded.
