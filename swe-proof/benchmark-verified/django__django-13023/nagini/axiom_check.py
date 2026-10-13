#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13023.

Executes the REAL canonical numeric constructor (`decimal.Decimal`, the stdlib
callee the coercion invokes) on representative inputs of every acceptance kind
and asserts that each observation matches the `construct_numeric` axiom encoded
in model.py:

    kind 2 — the constructor ACCEPTS the value and returns normally;
    kind 3 — the constructor rejects it as a malformed numeric literal
             (`decimal.InvalidOperation`);
    kind 4 — the constructor rejects it as a wrong-typed operand (`TypeError`);
    kind 5 — the constructor rejects it as an out-of-domain argument
             (`ValueError`);
    kind 6 — the constructor rejects it because a component of the value lies
             outside the internal range its representation can hold
             (`OverflowError`) — a rejection shape the coercion does NOT
             classify, so it propagates to the coercion's caller unchanged;
    kind 7 — the FLOATING branch's own rejection: the coercion routes a value to
             `create_decimal_from_float` on `isinstance(value, float)`, but that
             callee type-checks exactly and refuses a value which satisfies the
             test without being a real float (`TypeError`). Because line 1501 is
             outside the `try`, this too propagates unchanged.

The axiom's contract (model.py axioms region) is:
    Requires(kind in {2,3,4,5,6})
    Ensures(kind == 2)                              # returns normally iff kind 2
    Exsures(ConstructorMalformedError, kind == 3)   # InvalidOperation
    Exsures(ConstructorOperandError,   kind == 4)   # TypeError
    Exsures(ConstructorDomainError,    kind == 5)   # ValueError
    Exsures(ConstructorRangeError,     kind == 6)   # OverflowError

So soundness requires, for the REAL `decimal.Decimal(value)`:
    - kind-2 values construct without raising;
    - kind-3 values raise EXACTLY decimal.InvalidOperation;
    - kind-4 values raise EXACTLY TypeError;
    - kind-5 values raise EXACTLY ValueError;
    - kind-6 values raise EXACTLY OverflowError.

The mapping `value -> kind` is the field coercion's own classification: a value
is dispatched to the constructor only when it is neither None (kind 0) nor a
float (kind 1); its kind among {2,3,4,5,6} is then determined by how
`decimal.Decimal(value)` behaves. This check therefore also confirms the
exhaustiveness the axiom relies on: a constructor rejection is ALWAYS one of
InvalidOperation / TypeError / ValueError / OverflowError (never an undeclared
escape), and a broad cross-arm census confirms there is no FIFTH class.

Kind 6 is the fourth rejection class, and it is the one the coercion does NOT
convert. The C `_decimal` (libmpdec) accelerator — the implementation `import
decimal` binds, and therefore the one django calls — lowers the sign, each digit
and the exponent of the `(sign, digits, exponent)` coordinate form to C integers
and raises `OverflowError` when a component does not fit. Measured on both the
base and the gold-patched tree, `DecimalField.to_python((0,(1,),2**63))` raises
`OverflowError` identically, so a check asserting a three-way rejection space
would be asserting something false of the real callee.

Imports nothing repo-specific: `decimal` is the Python standard library — the
same module the coercion calls. Exit 0 iff every obligation holds.
"""
import decimal
import random
import sys


# decimal exception classes the axiom's three Exsures stand in for.
INVALID_OP = decimal.InvalidOperation


def real_kind(value):
    """Run the REAL decimal.Decimal(value) and report which acceptance kind it
    exhibits: 2 (accepted), 3 (InvalidOperation), 4 (TypeError), 5 (ValueError),
    or None for an undeclared/escaping rejection (which would be UNSOUND)."""
    try:
        decimal.Decimal(value)
        return 2
    except INVALID_OP:
        return 3
    except TypeError:
        return 4
    except OverflowError:
        # The FOURTH rejection class. Listed before ValueError only for clarity:
        # OverflowError's MRO is OverflowError -> ArithmeticError -> Exception, so
        # it is NOT a ValueError subclass and the order is immaterial.
        return 6
    except ValueError:
        return 5
    except Exception:
        return None  # an undeclared escape -> axiom is unsound


def check(value, expected_kind):
    observed = real_kind(value)
    assert observed is not None, (
        "construct_numeric axiom UNSOUND on %r: decimal.Decimal raised an "
        "exception class outside {InvalidOperation, TypeError, ValueError, "
        "OverflowError}; the coercion's four-way Exsures does not cover it"
        % (value,))
    assert observed == expected_kind, (
        "construct_numeric axiom UNSOUND on %r: expected acceptance kind %d, "
        "real decimal.Decimal exhibited kind %d"
        % (value, expected_kind, observed))


def main():
    # ---- kind 2: constructor ACCEPTS (returns normally) ----------------------
    accepted = [
        "3", "3.14", "0", "-1", "1e3", "2.0625", "+0.0", " 3.5 ", "  10\n",
        "1_000", "Infinity", "-Infinity", "1E+6", ".5", "5.",
        0, 1, -7, 2 ** 64, 10 ** 30,
        decimal.Decimal("1.5"),
    ]
    for v in accepted:
        check(v, 2)

    # ---- accepted_value axiom: accepted inputs yield a non-null Decimal token -
    # The `accepted_value(2)` accessor pins the kind-2 result to the
    # constructor's OWN returned value (model.py: Requires(kind == 2),
    # Ensures(Result() is not None)). Soundness: the REAL decimal.Decimal(value)
    # must return a non-null Decimal on every accepted value (it is the token the
    # coercion's accepted branch propagates, observed directly by P2P
    # test_to_python). The value is left abstract; only its non-null-ness is
    # claimed, so the axiom never over-claims.
    for v in accepted:
        produced = decimal.Decimal(v)  # real accepted-path callee return
        assert produced is not None, (
            "accepted_value axiom UNSOUND on %r: real decimal.Decimal returned "
            "None for an accepted value" % (v,))
        assert isinstance(produced, decimal.Decimal), (
            "accepted_value axiom UNSOUND on %r: real decimal.Decimal returned a "
            "non-Decimal %r" % (v, type(produced).__name__))

    # ---- kind 3: malformed numeric literal -> decimal.InvalidOperation -------
    malformed = [
        "abc", "non-numeric string", "1.2.3", "$5", "12,34", "", " ",
        "NaNx", "1 2", "0x10", "one", "--3", "1/2",
    ]
    for v in malformed:
        check(v, 3)

    # ---- kind 4: wrong-typed operand -> TypeError ----------------------------
    typeerr = [
        {}, set(), object(), complex(), b"non-numeric byte-string", b"123",
        {1: 2}, {"a"}, frozenset(), bytearray(b"x"), 3.5j, type,
        (lambda: 0),
    ]
    for v in typeerr:
        check(v, 4)

    # ---- kind 5: out-of-domain argument -> ValueError ------------------------
    valueerr = [
        (), [], (1, 2), [1, 2, 3], [0], (0,),
        # bad-shape coordinate forms whose components DO fit a C integer
        (2, (1,), 0), (-1, (1,), 0), ("0", (1,), 0), (0, "1", 0),
        (0, (10,), 0), (0, (-1,), 0), (0, (1,), "x"), (0, (1,), 1.5),
        (0, (1,), 0, 0), (0, None, 0), (0, ((1,),), 0),
    ]
    for v in valueerr:
        check(v, 5)

    # ---- kind 6: component outside the representable range -> OverflowError --
    # The FOURTH rejection class, and the one the coercion does NOT classify.
    # This is the SAME in-domain (sign, digits, exponent) coordinate family as
    # the ()/[]/(1,2) cases above — one step past the C ssize_t/long boundary at
    # which libmpdec can no longer lower a component to a C integer. Neither the
    # pre-patch nor the patched `to_python` converts it, so the model states it
    # as a raw-propagating leg rather than claiming a ValidationError.
    rangeerr = [
        (0, (1,), 2 ** 63), (0, (1,), -2 ** 63 - 1),
        (0, (1,), 10 ** 100), (0, (1,), -10 ** 100),
        (0, (10 ** 100,), 0), (10 ** 100, (1,), 0),
        (0, (1,), sys.maxsize + 1),
        [0, (1,), 2 ** 63], [0, (10 ** 100,), 0],
    ]
    for v in rangeerr:
        check(v, 6)

    # The BOUNDARY itself is kind 3, not kind 6: at exactly +/-(2**63-1) / -2**63
    # the exponent still fits a C ssize_t and libmpdec rejects it as an
    # InvalidOperation. Asserting both sides pins where the kind-3/kind-6 split
    # actually falls instead of only that kind 6 exists somewhere.
    for v in [(0, (1,), 2 ** 63 - 1), (0, (1,), -2 ** 63)]:
        check(v, 3)

    # ---- the EXACT F2P test_invalid_value inputs -----------------------------
    # ((), [], {}, set(), object(), complex(), 'non-numeric string',
    #  b'non-numeric byte-string') must ALL be rejections (kinds 3/4/5) so the
    # coercion uniformly surfaces a validation failure for each.
    f2p_invalid = [(), [], {}, set(), object(), complex(),
                   "non-numeric string", b"non-numeric byte-string"]
    for v in f2p_invalid:
        k = real_kind(v)
        assert k in (3, 4, 5), (
            "F2P invalid value %r must be a constructor rejection (kind 3/4/5), "
            "observed kind %r" % (v, k))

    # ---- randomized fuzz over each rejection family --------------------------
    rng = random.Random(13023)

    # fuzz kind-4 containers/objects (non-string, non-bytes are TypeError-prone)
    for _ in range(2000):
        choice = rng.randint(0, 4)
        if choice == 0:
            v = {rng.randint(0, 9): rng.randint(0, 9)}
        elif choice == 1:
            v = set(rng.randint(0, 9) for _ in range(rng.randint(1, 4)))
        elif choice == 2:
            v = complex(rng.random(), rng.random())
        elif choice == 3:
            v = object()
        else:
            v = bytes(rng.randint(0, 255) for _ in range(rng.randint(1, 6)))
        check(v, 4)

    # fuzz kind-5: non-empty / empty sequences (list/tuple) are ValueError
    for _ in range(2000):
        n = rng.randint(0, 5)
        seq = [rng.randint(0, 9) for _ in range(n)]
        check(list(seq), 5)
        check(tuple(seq), 5)

    # fuzz kind-6: coordinate forms driven PAST the C integer boundary in each of
    # the three component positions (exponent, a digit, the sign). The previous
    # kind-5 fuzzer above only ever generated small ints, which is exactly why it
    # never reached this boundary; this loop is what closes that blind spot.
    BIG_POS = [2 ** 63, 2 ** 63 + 1, 10 ** 100, 10 ** 400, sys.maxsize + 1]
    BIG_ANY = BIG_POS + [-2 ** 63 - 1, -2 ** 63 - 2, -10 ** 100]
    for _ in range(2000):
        where = rng.randint(0, 2)
        if where == 0:      # exponent too large in magnitude
            v = (rng.choice([0, 1]), (rng.randint(0, 9),), rng.choice(BIG_ANY))
        elif where == 1:    # a digit too large to lower to a C long
            v = (rng.choice([0, 1]), (rng.choice(BIG_POS),), rng.randint(-5, 5))
        else:               # sign too large to lower to a C long
            v = (rng.choice(BIG_POS), (rng.randint(0, 9),), rng.randint(-5, 5))
        check(v, 6)
        check(list(v), 6)

    # fuzz kind-3: random non-numeric strings are InvalidOperation
    junk = "abcXYZ$%@,/ \t!?one two"
    for _ in range(2000):
        n = rng.randint(1, 12)
        s = "".join(rng.choice(junk) for _ in range(n))
        try:
            decimal.Decimal(s)
            continue  # happened to be a valid literal (e.g. all-space) -> skip
        except INVALID_OP:
            check(s, 3)
        except (TypeError, ValueError):
            # a string can never be TypeError/ValueError from Decimal(); guard
            raise AssertionError(
                "string %r unexpectedly raised non-InvalidOperation" % (s,))

    # ---- EXHAUSTIVENESS: no FIFTH rejection class ----------------------------
    # The four-way Exsures is only sound if the real constructor's rejection space
    # has exactly these four classes. A broad cross-arm census (coordinate forms,
    # bad-length sequences, strings, ints, foreign types, with components on both
    # sides of the C boundary) must never make real_kind return its None sentinel.
    POOL_INT = [0, 1, -1, 2 ** 63, 2 ** 63 + 1, -2 ** 63 - 1, 10 ** 100,
                sys.maxsize, -sys.maxsize - 1]
    POOL_MISC = ["F", "n", "N", "x", "", None, 1.5, True, (1,), [1], "1", {},
                 set(), object(), b"1", complex(), memoryview(b"1"), range(2),
                 frozenset(), type, decimal.Decimal(1)]
    census = {}
    for _ in range(40000):
        a = rng.randint(0, 6)
        if a <= 2:
            v = (rng.choice(POOL_INT + POOL_MISC),
                 rng.choice([tuple(rng.choice(POOL_INT + POOL_MISC)
                                   for _ in range(rng.randint(0, 4)))] + POOL_MISC),
                 rng.choice(POOL_INT + POOL_MISC))
        elif a == 3:
            v = tuple(rng.choice(POOL_INT + POOL_MISC)
                      for _ in range(rng.randint(0, 6)))
        elif a == 4:
            v = [rng.choice(POOL_INT + POOL_MISC)
                 for _ in range(rng.randint(0, 6))]
        elif a == 5:
            v = "".join(rng.choice("0123456789eE+-._ NnaIifSs")
                        for _ in range(rng.randint(0, 20)))
        else:
            v = rng.choice(POOL_INT + POOL_MISC)
        k = real_kind(v)
        assert k is not None, (
            "construct_numeric axiom UNSOUND: a FIFTH rejection class escaped on "
            "%r (outside {InvalidOperation, TypeError, ValueError, OverflowError})"
            % (v,))
        census[k] = census.get(k, 0) + 1
    assert 6 in census, (
        "census INEFFECTIVE: never produced a kind-6 rejection, so it did not "
        "actually probe the boundary this check exists to cover")

    # ---- from_floating / convert_floating axioms -----------------------------
    # The floating branch's callee is `self.context.create_decimal_from_float`,
    # a callee DISTINCT from the general constructor and invoked at line 1501 —
    # ABOVE and OUTSIDE the `try` that begins at line 1502. The axiom pair claims
    # (a) it returns a constructed token WITHOUT raising for every value the
    # branch's test admits AND the conversion accepts (kind 1, value abstract),
    # and (b) it REFUSES as a wrong-typed operand a value that satisfies the
    # branch's isinstance test without being a real float (kind 7), whose
    # TypeError then escapes the coercion unconverted. (max_digits=4 mirrors the
    # F2P field; the precision only rounds the value, never raises.)
    ctx = decimal.Context(prec=4)

    class MyFloat(float):
        pass

    float_inputs = [0.0, -0.0, 1.0, -1.0, 2.4, 2.0625, 2.1875,
                    3.1415926535897, 1e308, -1e308, 1e-308, 1.5e-300,
                    float("inf"), float("-inf"), float("nan"),
                    sys.float_info.max, -sys.float_info.max,
                    sys.float_info.min, 5e-324,
                    MyFloat(1.5), MyFloat(float("inf")), MyFloat(0.0)]
    for fv in float_inputs:
        try:
            ctx.create_decimal_from_float(fv)  # real float-path callee
        except Exception as e:                  # noqa: BLE001
            raise AssertionError(
                "from_floating axiom UNSOUND: create_decimal_from_float(%r) "
                "raised %s; the axiom claims a normal return" % (fv, type(e).__name__))
    for _ in range(2000):
        fv = rng.uniform(-1e6, 1e6) * (10 ** rng.randint(-20, 20))
        try:
            ctx.create_decimal_from_float(fv)
        except Exception as e:                  # noqa: BLE001
            raise AssertionError(
                "from_floating axiom UNSOUND: create_decimal_from_float(%r) "
                "raised %s" % (fv, type(e).__name__))

    # ---- kind 7: the floating branch's OWN rejection -------------------------
    # `to_python` routes on `isinstance(value, float)`, but the C _decimal
    # `create_decimal_from_float` does an EXACT PyFloat/PyLong type check rather
    # than a duck-typed `__float__` call. A value that satisfies isinstance
    # WITHOUT being a real float is therefore refused with TypeError — and since
    # line 1501 sits outside the try, that TypeError escapes `to_python` raw.
    # This is the blind spot a genuine-floats-only probe cannot reach: 'every
    # genuine float converts' is true, but the branch's guard admits strictly
    # more than genuine floats.
    class _AttrSpoof:
        __class__ = float

    class _PropSpoof:
        @property
        def __class__(self):
            return float

    spoofers = [("attr __class__", _AttrSpoof()),
                ("property __class__", _PropSpoof())]
    try:
        from unittest.mock import MagicMock, Mock, NonCallableMock
        spoofers += [("MagicMock(spec=float)", MagicMock(spec=float)),
                     ("Mock(spec=float)", Mock(spec=float)),
                     ("NonCallableMock(spec=float)", NonCallableMock(spec=float))]
    except Exception:                            # noqa: BLE001
        pass
    try:
        from django.utils.functional import SimpleLazyObject
        for fac in (lambda: 1.5, lambda: float("inf"), lambda: float("nan"),
                    lambda: 0.0, lambda: -1e308):
            spoofers.append(("SimpleLazyObject(float)", SimpleLazyObject(fac)))
    except Exception:                            # noqa: BLE001
        pass

    n_spoof = 0
    for label, sv in spoofers:
        assert isinstance(sv, float) is True, (
            "kind-7 probe INEFFECTIVE: %s does not satisfy the coercion's "
            "floating-branch isinstance test, so it never reaches the "
            "conversion" % label)
        try:
            ctx.create_decimal_from_float(sv)
            raise AssertionError(
                "convert_floating axiom UNSOUND: create_decimal_from_float "
                "ACCEPTED %s, but the kind-7 leg claims it refuses this operand"
                % label)
        except TypeError:
            n_spoof += 1
        except AssertionError:
            raise
        except Exception as e:                   # noqa: BLE001
            raise AssertionError(
                "convert_floating axiom UNSOUND: create_decimal_from_float(%s) "
                "raised %s, not the wrong-typed-operand class the kind-7 leg "
                "declares" % (label, type(e).__name__))
    assert n_spoof > 0, (
        "kind-7 probe INEFFECTIVE: no floating-branch operand rejection was "
        "exercised, so the leg the coercion does not classify went unprobed")

    # ---- kind 8: the floating conversion's SECOND, distinct refusal ----------
    # The conversion accepts int as well as float operands, so an INT-payload
    # `__class__ = float` value passes its exact PyFloat/PyLong check (it is NOT
    # a kind-7 TypeError case) — and is then refused because its magnitude lies
    # outside the range the conversion's own context can represent, with a class
    # that is neither TypeError nor the constructor's OverflowError. The genuine
    # floats plus TypeError-spoofers probe above cannot reach this boundary:
    # genuine floats cap near 1e308, far inside the context's Emax.
    class _IntSpoof(int):
        __class__ = float

    n_range = 0
    for label, exp in (("int-payload 10**(Emax+1)", ctx.Emax + 1),
                       ("int-payload -10**(Emax+1)", ctx.Emax + 1),
                       ("int-payload 10**(Emax+7)", ctx.Emax + 7)):
        mag = 10 ** exp
        rv = _IntSpoof(-mag if label.startswith("int-payload -") else mag)
        assert isinstance(rv, float) is True, (
            "kind-8 probe INEFFECTIVE: %s does not satisfy the coercion's "
            "floating-branch isinstance test, so it never reaches the "
            "conversion" % label)
        try:
            ctx.create_decimal_from_float(rv)
            raise AssertionError(
                "convert_floating axiom UNSOUND: create_decimal_from_float "
                "ACCEPTED %s, but the kind-8 leg claims it refuses this "
                "magnitude" % label)
        except AssertionError:
            raise
        except TypeError as e:
            raise AssertionError(
                "kind-8/kind-7 boundary WRONG: %s was refused as a wrong-typed "
                "operand (%s), but the model routes it to the range-refusal leg"
                % (label, e))
        except Exception as e:                   # noqa: BLE001
            # The declared kind-8 class: distinct from TypeError (kind 7) and
            # from the constructor's OverflowError (kind 6).
            assert not isinstance(e, TypeError), label
            assert not isinstance(e, OverflowError), (
                "kind-8 leg WRONG: %s was refused with an OverflowError, which "
                "is the constructor's kind-6 class, not a distinct one" % label)
            n_range += 1
    assert n_range > 0, (
        "kind-8 probe INEFFECTIVE: no floating-branch range refusal was "
        "exercised, so the third unclassified leg went unprobed")

    # ...and the ACCEPTING side of that same boundary must still be kind 1, so
    # the kind-1/kind-8 split is pinned on both sides (an int-payload spoofer one
    # step INSIDE the context's Emax converts normally).
    _inside = _IntSpoof(10 ** ctx.Emax)
    assert isinstance(_inside, float) is True
    try:
        ctx.create_decimal_from_float(_inside)
    except Exception as e:                       # noqa: BLE001
        raise AssertionError(
            "kind-1/kind-8 boundary WRONG: an int-payload spoofer of magnitude "
            "10**Emax was refused with %s, but the model calls it kind 1"
            % type(e).__name__)

    # ---- value_kind axiom: the value in scope HAS a kind, inside 0..7 --------
    # `value_kind()` claims only `0 <= Result() <= 7`, i.e. mapping.md sec 2's
    # totality claim for the value->kind map: the single `value` the coercion was
    # handed lowers to some acceptance shape the model enumerates. Its role is to
    # tie each callee's tag to THAT shape, because the real callees take no tag
    # and are applied to the value in scope. Soundness here = lowering every
    # probe value this file already built and asserting each lands in range.
    def _kind_of(v):
        if v is None:
            return 0
        if isinstance(v, float):                 # the coercion's line-1500 test
            try:
                ctx.create_decimal_from_float(v)
                return 1
            except TypeError:
                return 7
            except Exception:                    # noqa: BLE001
                # the conversion accepted the operand TYPE but refused the
                # magnitude: a distinct class from both TypeError (7) and the
                # constructor's OverflowError (6)
                return 8
        try:
            decimal.Decimal(v)
            return 2
        except decimal.InvalidOperation:
            return 3
        except TypeError:
            return 4
        except ValueError:
            return 5
        except OverflowError:
            return 6

    vk_pool = (list(accepted) + list(malformed) + list(typeerr) + list(valueerr)
               + list(rangeerr) + list(f2p_invalid) + [None] + list(float_inputs)
               + [sv for _, sv in spoofers]
               # int-payload float-spoofers straddling the conversion context's
               # Emax: the kind-1/kind-8 boundary the other pools cannot reach.
               + [_IntSpoof(10 ** ctx.Emax), _IntSpoof(10 ** (ctx.Emax + 1)),
                  _IntSpoof(-(10 ** (ctx.Emax + 1))), _IntSpoof(0)])
    vk_seen = {}
    for v in vk_pool:
        k = _kind_of(v)
        assert k is not None and 0 <= k <= 8, (
            "value_kind axiom UNSOUND: value lowers to %r, outside the "
            "0..8 range the axiom's Ensures declares" % (k,))
        vk_seen[k] = vk_seen.get(k, 0) + 1
    assert set(vk_seen) == set(range(9)), (
        "value_kind probe INEFFECTIVE: the lowering never produced kinds %r, so "
        "the range claim went unprobed on them"
        % sorted(set(range(9)) - set(vk_seen)))

    print("G-AX OK: construct_numeric axiom sound against real decimal.Decimal "
          "on %d accepted + %d malformed + %d type-error + %d value-error + %d "
          "range-error boundary inputs, the 8 F2P invalid values, and 8000 fuzz "
          "inputs; every rejection is exactly one of "
          "{InvalidOperation, TypeError, ValueError, OverflowError}, and a "
          "40000-input cross-arm census found NO fifth class (kind histogram %r). "
          "accepted_value axiom sound: "
          "real decimal.Decimal returned a non-null Decimal on all %d accepted "
          "inputs. from_floating/convert_floating axioms sound: "
          "create_decimal_from_float returned normally on %d boundary + 2000 "
          "fuzz floats (incl. inf/-inf/nan and float subclasses), and refused "
          "all %d floating-branch operand spoofers (values satisfying the "
          "branch's isinstance test without being real floats) with EXACTLY the "
          "wrong-typed-operand class, which escapes the coercion unconverted "
          "because that call sits outside the try; and refused %d int-payload "
          "spoofers past the conversion context's Emax with a DISTINCT "
          "out-of-range class (neither TypeError nor the constructor's "
          "OverflowError), with the accepting side of that boundary "
          "(10**Emax) still converting normally. value_kind axiom sound: %d "
          "probe values lowered to a kind in 0..8 with every kind witnessed "
          "(histogram %r), so the tag every callee site is required to equal is "
          "always defined for the value in scope."
          % (len(accepted), len(malformed), len(typeerr), len(valueerr),
             len(rangeerr), sorted(census.items()),
             len(accepted), len(float_inputs), n_spoof, n_range,
             len(vk_pool), sorted(vk_seen.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
