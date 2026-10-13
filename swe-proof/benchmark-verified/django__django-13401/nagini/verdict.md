# P2 adversarial audit — django__django-13401

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Attr:
@@ -51,7 +50,6 @@
     meaningful only when `owned` is true."""
 
     def __init__(self, rank: int, owned: bool, okey: PSeq[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.rank) and Acc(self.owned) and Acc(self.okey))  # type: ignore
         Ensures(self.rank == rank and self.owned == owned)  # type: ignore
         Ensures(self.okey is okey)  # type: ignore
@@ -130,7 +128,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -139,10 +136,7 @@
     Ensures(Result() == eq_ref(self_, other))
     # post-conditions-end
     # impl-start
-    return (
-        self_.rank == other.rank and
-        same_owner(self_, other)
-    )
+    return self_.rank == other.rank
     # impl-end
 
 
@@ -150,7 +144,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -175,7 +168,6 @@
 def attr_hash_key(self_: Attr) -> PSeq[int]:
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Attr:
@@ -51,7 +50,6 @@
     meaningful only when `owned` is true."""
 
     def __init__(self, rank: int, owned: bool, okey: PSeq[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.rank) and Acc(self.owned) and Acc(self.okey))  # type: ignore
         Ensures(self.rank == rank and self.owned == owned)  # type: ignore
         Ensures(self.okey is okey)  # type: ignore
@@ -130,7 +128,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -139,7 +136,7 @@
     Ensures(Result() == eq_ref(self_, other))
     # post-conditions-end
     # impl-start
-    return (
+    return same_owner(self_, other)
         self_.rank == other.rank and
         same_owner(self_, other)
     )
@@ -150,7 +147,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -175,7 +171,6 @@
 def attr_hash_key(self_: Attr) -> PSeq[int]:
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Attr:
@@ -51,7 +50,6 @@
     meaningful only when `owned` is true."""
 
     def __init__(self, rank: int, owned: bool, okey: PSeq[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.rank) and Acc(self.owned) and Acc(self.okey))  # type: ignore
         Ensures(self.rank == rank and self.owned == owned)  # type: ignore
         Ensures(self.okey is okey)  # type: ignore
@@ -130,7 +128,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -150,7 +147,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -166,7 +162,7 @@
     ):
         return self_.rank < other.rank
     elif self_.owned != other.owned:
-        return not self_.owned  # the owner-less attribute precedes
+        return self_.owned
     else:
         return lex_lt(self_.okey, other.okey)
     # impl-end
@@ -175,7 +171,6 @@
 def attr_hash_key(self_: Attr) -> PSeq[int]:
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Attr:
@@ -51,7 +50,6 @@
     meaningful only when `owned` is true."""
 
     def __init__(self, rank: int, owned: bool, okey: PSeq[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.rank) and Acc(self.owned) and Acc(self.okey))  # type: ignore
         Ensures(self.rank == rank and self.owned == owned)  # type: ignore
         Ensures(self.okey is okey)  # type: ignore
@@ -130,7 +128,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -150,7 +147,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -164,9 +160,9 @@
         self_.rank != other.rank or
         not self_.owned and not other.owned
     ):
-        return self_.rank < other.rank
+        return self_.rank <= other.rank
     elif self_.owned != other.owned:
-        return not self_.owned  # the owner-less attribute precedes
+        return not self_.owned
     else:
         return lex_lt(self_.okey, other.okey)
     # impl-end
@@ -175,7 +171,6 @@
 def attr_hash_key(self_: Attr) -> PSeq[int]:
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Attr:
@@ -51,7 +50,6 @@
     meaningful only when `owned` is true."""
 
     def __init__(self, rank: int, owned: bool, okey: PSeq[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.rank) and Acc(self.owned) and Acc(self.okey))  # type: ignore
         Ensures(self.rank == rank and self.owned == owned)  # type: ignore
         Ensures(self.okey is okey)  # type: ignore
@@ -130,7 +128,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -150,7 +147,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -175,7 +171,6 @@
 def attr_hash_key(self_: Attr) -> PSeq[int]:
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -184,7 +179,5 @@
     Ensures(Result() == hash_ref(self_))
     # post-conditions-end
     # impl-start
-    if self_.owned:
-        return PSeq(self_.rank, 1) + self_.okey
     return PSeq(self_.rank, 0)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Attr:
@@ -51,7 +50,6 @@
     meaningful only when `owned` is true."""
 
     def __init__(self, rank: int, owned: bool, okey: PSeq[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.rank) and Acc(self.owned) and Acc(self.okey))  # type: ignore
         Ensures(self.rank == rank and self.owned == owned)  # type: ignore
         Ensures(self.okey is okey)  # type: ignore
@@ -130,7 +128,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -150,7 +147,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -175,7 +171,6 @@
 def attr_hash_key(self_: Attr) -> PSeq[int]:
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -185,6 +180,8 @@
     # post-conditions-end
     # impl-start
     if self_.owned:
+        return PSeq(self_.rank, 0) + self_.okey
+    return PSeq(self_.rank, 0)
         return PSeq(self_.rank, 1) + self_.okey
     return PSeq(self_.rank, 0)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Attr:
@@ -51,7 +50,6 @@
     meaningful only when `owned` is true."""
 
     def __init__(self, rank: int, owned: bool, okey: PSeq[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.rank) and Acc(self.owned) and Acc(self.okey))  # type: ignore
         Ensures(self.rank == rank and self.owned == owned)  # type: ignore
         Ensures(self.okey is okey)  # type: ignore
@@ -130,7 +128,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -150,7 +147,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -164,9 +160,9 @@
         self_.rank != other.rank or
         not self_.owned and not other.owned
     ):
-        return self_.rank < other.rank
+        return other.rank < self_.rank
     elif self_.owned != other.owned:
-        return not self_.owned  # the owner-less attribute precedes
+        return not self_.owned
     else:
         return lex_lt(self_.okey, other.okey)
     # impl-end
@@ -175,7 +171,6 @@
 def attr_hash_key(self_: Attr) -> PSeq[int]:
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Attr:
@@ -51,7 +50,6 @@
     meaningful only when `owned` is true."""
 
     def __init__(self, rank: int, owned: bool, okey: PSeq[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.rank) and Acc(self.owned) and Acc(self.okey))  # type: ignore
         Ensures(self.rank == rank and self.owned == owned)  # type: ignore
         Ensures(self.okey is okey)  # type: ignore
@@ -130,7 +128,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -139,10 +136,7 @@
     Ensures(Result() == eq_ref(self_, other))
     # post-conditions-end
     # impl-start
-    return (
-        self_.rank == other.rank and
-        same_owner(self_, other)
-    )
+    return eq_ref(self_, other)
     # impl-end
 
 
@@ -150,7 +144,6 @@
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
     Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -160,22 +153,13 @@
     Ensures(Result() == lt_ref(self_, other))
     # post-conditions-end
     # impl-start
-    if (
-        self_.rank != other.rank or
-        not self_.owned and not other.owned
-    ):
-        return self_.rank < other.rank
-    elif self_.owned != other.owned:
-        return not self_.owned  # the owner-less attribute precedes
-    else:
-        return lex_lt(self_.okey, other.okey)
+    return lt_ref(self_, other)
     # impl-end
 
 
 def attr_hash_key(self_: Attr) -> PSeq[int]:
     # pre-conditions-start
     Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
@@ -184,7 +168,5 @@
     Ensures(Result() == hash_ref(self_))
     # post-conditions-end
     # impl-start
-    if self_.owned:
-        return PSeq(self_.rank, 1) + self_.okey
-    return PSeq(self_.rank, 0)
+    return hash_ref(self_)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13401.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A schema attribute carries an integer creation rank and, optionally, an
  owning-container identity (a label/name pair). Three relational operations are
  specified over two such attributes:

  (1) EQUALITY. Two attributes are equal exactly when they share the same
      creation rank AND have the same owning-container identity. "Same identity"
      means: both lack an owner, or both have an owner with an identical
      (label, name) pair. Consequently two attributes that share a creation rank
      but belong to DIFFERENT owning containers are NOT equal — and one that has
      an owner is never equal to one that lacks an owner.

  (2) STRICT ORDER (a total order refining equality, used so the attributes may
      be kept sorted). The order is taken first by creation rank, for backward
      compatibility: whenever the two ranks differ, OR neither attribute has an
      owner, the smaller-ranked one precedes. Only when the ranks are equal and
      ownership is involved does the owner break the tie: an attribute that
      lacks an owner precedes one that has an owner; and when both have an owner
      with the same rank, they are ordered by the lexicographic order of their
      (label, name) identity pair.

  (3) HASH KEY. The value an attribute contributes to a hash is determined by
      its FULL identity — its creation rank together with its owning-container
      identity (the (label, name) pair, or their absence) — not by the creation
      rank alone. Hence two attributes that differ in owning container (even at
      the same creation rank) contribute distinct hash keys, so a hashed
      collection keeps them distinct rather than collapsing them.

Strings (the label and name of an owner) are modelled as `List[int]` of code
points (Nagini bans `str` indexing); the (label, name) identity pair is carried
as a single `PSeq[int]` key (label, a separator below every identifier code
point, then name), and identity-pair comparison is the lexicographic order on
that key. The hash KEY is modelled deeply (the operation under specification is
which identity flows into the hash, not the hashing itself).

Markers (machine-parsed) delimit the spec / proof / impl regions; provenance
binding to the repository is in mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *


class Attr:
    """A schema attribute abstracted by its integer creation rank `rank`, a flag
    `owned` recording whether it has an owning container, and `okey`, the owner
    identity (label, name) flattened into one code-point sequence. `okey` is
    meaningful only when `owned` is true."""

    def __init__(self, rank: int, owned: bool, okey: PSeq[int]) -> None:
        Ensures(Acc(self.rank) and Acc(self.owned) and Acc(self.okey))  # type: ignore
        Ensures(self.rank == rank and self.owned == owned)  # type: ignore
        Ensures(self.okey is okey)  # type: ignore
        self.rank = rank  # type: ignore
        self.owned = owned  # type: ignore
        self.okey = okey  # type: ignore


# axioms-start
# (No axiomatized callees: equality, the order, and the hash KEY are modelled
# deeply over the attributes' own fields. The unchanged hashing of a key is an
# A-reference validated out-of-band by axiom_check.py / G-AX, not a consumed
# axiom of this proof.)
# axioms-end


# pure-start
@Pure
def lex_lt(x: PSeq[int], y: PSeq[int]) -> bool:
    """Lexicographic strict less-than on two code-point sequences (the order
    Python uses to compare the (label, name) identity pairs). Front-recursive so
    one unfold is available per element."""
    if len(x) == 0:
        return len(y) > 0
    if len(y) == 0:
        return False
    if x[0] != y[0]:
        return x[0] < y[0]
    return lex_lt(x.drop(1), y.drop(1))


@Pure
def same_owner(a: 'Attr', b: 'Attr') -> bool:
    """Two attributes have the same owning-container identity iff both lack an
    owner, or both have an owner with an identical (label, name) key."""
    Requires(Acc(a.owned, 1 / 8) and Acc(a.okey, 1 / 8))  # type: ignore
    Requires(Acc(b.owned, 1 / 8) and Acc(b.okey, 1 / 8))  # type: ignore
    return a.owned == b.owned and (not a.owned or a.okey == b.okey)  # type: ignore


@Pure
def eq_ref(a: 'Attr', b: 'Attr') -> bool:
    """Reference equality: same creation rank AND same owning-container identity."""
    Requires(Acc(a.rank, 1 / 8) and Acc(a.owned, 1 / 8) and Acc(a.okey, 1 / 8))  # type: ignore
    Requires(Acc(b.rank, 1 / 8) and Acc(b.owned, 1 / 8) and Acc(b.okey, 1 / 8))  # type: ignore
    return a.rank == b.rank and same_owner(a, b)  # type: ignore


@Pure
def lt_ref(a: 'Attr', b: 'Attr') -> bool:
    """Reference strict order: by creation rank first; only equal-rank owned
    attributes are tie-broken (no-owner before owner, then by identity key)."""
    Requires(Acc(a.rank, 1 / 8) and Acc(a.owned, 1 / 8) and Acc(a.okey, 1 / 8))  # type: ignore
    Requires(Acc(b.rank, 1 / 8) and Acc(b.owned, 1 / 8) and Acc(b.okey, 1 / 8))  # type: ignore
    if a.rank != b.rank or (not a.owned and not b.owned):  # type: ignore
        return a.rank < b.rank  # type: ignore
    if a.owned != b.owned:  # type: ignore
        return not a.owned  # type: ignore
    return lex_lt(a.okey, b.okey)  # type: ignore


@Pure
def hash_ref(a: 'Attr') -> PSeq[int]:
    """Reference hash KEY: the full identity that flows into the hash — the
    creation rank, an ownership flag, then (when owned) the identity key. Two
    attributes contribute the same hash key iff this whole sequence agrees, so
    attributes differing in owner contribute distinct keys."""
    Requires(Acc(a.rank, 1 / 8) and Acc(a.owned, 1 / 8) and Acc(a.okey, 1 / 8))  # type: ignore
    if a.owned:  # type: ignore
        return PSeq(a.rank, 1) + a.okey  # type: ignore
    return PSeq(a.rank, 0)  # type: ignore
# pure-end


def attr_eq(self_: Attr, other: Attr) -> bool:
    # pre-conditions-start
    Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    Ensures(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
    # Equal iff same creation rank AND same owning-container identity.
    Ensures(Result() == eq_ref(self_, other))
    # post-conditions-end
    # impl-start
    return (
        self_.rank == other.rank and
        same_owner(self_, other)
    )
    # impl-end


def attr_lt(self_: Attr, other: Attr) -> bool:
    # pre-conditions-start
    Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    Ensures(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
    # Order by creation rank first; equal-rank owned attributes tie-break by
    # ownership then by lexicographic identity key.
    Ensures(Result() == lt_ref(self_, other))
    # post-conditions-end
    # impl-start
    if (
        self_.rank != other.rank or
        not self_.owned and not other.owned
    ):
        return self_.rank < other.rank
    elif self_.owned != other.owned:
        return not self_.owned  # the owner-less attribute precedes
    else:
        return lex_lt(self_.okey, other.okey)
    # impl-end


def attr_hash_key(self_: Attr) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    # The hash key is the full identity: creation rank, ownership, and (when
    # owned) the identity key. So it depends on the owner, not the rank alone.
    Ensures(Result() == hash_ref(self_))
    # post-conditions-end
    # impl-start
    if self_.owned:
        return PSeq(self_.rank, 1) + self_.okey
    return PSeq(self_.rank, 0)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: attr_eq/attr_lt/attr_hash_key each fully pin Result() to a deep reference (eq_ref/lt_ref/hash_ref) that lives in the FROZEN pure region; therefore any verifying impl is behaviorally identical to the reference. refinement.md legs are all R / A-reference / I — NO A-consumed, NO kind-3 (bundle consumes no @ContractOnly axioms). A-legs audited: A3 same_owner<->getattr(model)-equality (model modeled by (app_label,model_name) pair); B3 lex_lt on flattened okey (NUL sep=0 below all identifier code points) <-> native tuple compare; C1/C2 hash_ref key + builtin hash distinct-on-equal-rank (soundness note correctly restricts to equal-rank to dodge hash(-1)==hash(-2)). axiom_check.py exit 0 (F2P + 13225 boundary + 40000 fuzz pairs).

ATTACKS (cmd: python -m swebench_unified.adversary weakness nagini django__django-13401 <path>), run concurrently in batches of 3:
 atk_1 eq drop same_owner (=prepatch_eq §D witness): exit 2 rejected
 atk_2 eq drop rank keep same_owner: exit 2 rejected
 atk_3 lt tie-break flipped (owner precedes): exit 2 rejected
 atk_4 lt <= in rank branch (boundary): exit 2 rejected
 atk_5 hash drop owner from key (=prepatch_hash §D witness): exit 2 rejected
 atk_6 hash owned-tag 0 collides w/ ownerless: exit 2 rejected
 atk_7 lt reversed rank comparison: exit 2 rejected
 atk_8 ECHO return eq_ref/lt_ref/hash_ref (behaviorally correct): exit 0 CANDIDATE (12.2s).

CANDIDATE RESOLVE (protocol step 2): atk_8 returns the references verbatim => its faithful refined patch = gold post-patch decisions = patch.diff. run_resolve('django__django-13401', faithful_patch) executed via swebench_unified.harness: RESOLVED=True COMPLETED=True NOTE=resolved ATTEMPTS=1 FLAKY=False. F2P 'Field instances from abstract models are not equal.' PASS; all 32 PASS_TO_PASS PASS; no failures. The sole verifying candidate RESOLVES.

Positive control: model.py verifies (nagini_verify.sh exit 0, 11.78s). Prepatch reproduced: atk_1 (eq) and atk_5 (hash) reproduce §D prepatch bugs and are both rejected by the spec.

VERDICT: SOUND — 7 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded/collision) all rejected by verification; the one verifying candidate's materialized faithful patch resolves under the official harness. No verify⇏correct gap found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13401.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A schema attribute carries an integer creation rank and, optionally, an
  owning-container identity (a label/name pair). Three relational operations are
  specified over two such attributes:

  (1) EQUALITY. Two attributes are equal exactly when they share the same
      creation rank AND have the same owning-container identity. "Same identity"
      means: both lack an owner, or both have an owner with an identical
      (label, name) pair. Consequently two attributes that share a creation rank
      but belong to DIFFERENT owning containers are NOT equal — and one that has
      an owner is never equal to one that lacks an owner.

  (2) STRICT ORDER (a total order refining equality, used so the attributes may
      be kept sorted). The order is taken first by creation rank, for backward
      compatibility: whenever the two ranks differ, OR neither attribute has an
      owner, the smaller-ranked one precedes. Only when the ranks are equal and
      ownership is involved does the owner break the tie: an attribute that
      lacks an owner precedes one that has an owner; and when both have an owner
      with the same rank, they are ordered by the lexicographic order of their
      (label, name) identity pair.

  (3) HASH KEY. The value an attribute contributes to a hash is determined by
      its FULL identity — its creation rank together with its owning-container
      identity (the (label, name) pair, or their absence) — not by the creation
      rank alone. Hence two attributes that differ in owning container (even at
      the same creation rank) contribute distinct hash keys, so a hashed
      collection keeps them distinct rather than collapsing them.

Strings (the label and name of an owner) are modelled as `List[int]` of code
points (Nagini bans `str` indexing); the (label, name) identity pair is carried
as a single `PSeq[int]` key (label, a separator below every identifier code
point, then name), and identity-pair comparison is the lexicographic order on
that key. The hash KEY is modelled deeply (the operation under specification is
which identity flows into the hash, not the hashing itself).

Markers (machine-parsed) delimit the spec / proof / impl regions; provenance
binding to the repository is in mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *


class Attr:
    """A schema attribute abstracted by its integer creation rank `rank`, a flag
    `owned` recording whether it has an owning container, and `okey`, the owner
    identity (label, name) flattened into one code-point sequence. `okey` is
    meaningful only when `owned` is true."""

    def __init__(self, rank: int, owned: bool, okey: PSeq[int]) -> None:
        Ensures(Acc(self.rank) and Acc(self.owned) and Acc(self.okey))  # type: ignore
        Ensures(self.rank == rank and self.owned == owned)  # type: ignore
        Ensures(self.okey is okey)  # type: ignore
        self.rank = rank  # type: ignore
        self.owned = owned  # type: ignore
        self.okey = okey  # type: ignore


# axioms-start
# (No axiomatized callees: equality, the order, and the hash KEY are modelled
# deeply over the attributes' own fields. The unchanged hashing of a key is an
# A-reference validated out-of-band by axiom_check.py / G-AX, not a consumed
# axiom of this proof.)
# axioms-end


# pure-start
@Pure
def lex_lt(x: PSeq[int], y: PSeq[int]) -> bool:
    """Lexicographic strict less-than on two code-point sequences (the order
    Python uses to compare the (label, name) identity pairs). Front-recursive so
    one unfold is available per element."""
    if len(x) == 0:
        return len(y) > 0
    if len(y) == 0:
        return False
    if x[0] != y[0]:
        return x[0] < y[0]
    return lex_lt(x.drop(1), y.drop(1))


@Pure
def same_owner(a: 'Attr', b: 'Attr') -> bool:
    """Two attributes have the same owning-container identity iff both lack an
    owner, or both have an owner with an identical (label, name) key."""
    Requires(Acc(a.owned, 1 / 8) and Acc(a.okey, 1 / 8))  # type: ignore
    Requires(Acc(b.owned, 1 / 8) and Acc(b.okey, 1 / 8))  # type: ignore
    return a.owned == b.owned and (not a.owned or a.okey == b.okey)  # type: ignore


@Pure
def eq_ref(a: 'Attr', b: 'Attr') -> bool:
    """Reference equality: same creation rank AND same owning-container identity."""
    Requires(Acc(a.rank, 1 / 8) and Acc(a.owned, 1 / 8) and Acc(a.okey, 1 / 8))  # type: ignore
    Requires(Acc(b.rank, 1 / 8) and Acc(b.owned, 1 / 8) and Acc(b.okey, 1 / 8))  # type: ignore
    return a.rank == b.rank and same_owner(a, b)  # type: ignore


@Pure
def lt_ref(a: 'Attr', b: 'Attr') -> bool:
    """Reference strict order: by creation rank first; only equal-rank owned
    attributes are tie-broken (no-owner before owner, then by identity key)."""
    Requires(Acc(a.rank, 1 / 8) and Acc(a.owned, 1 / 8) and Acc(a.okey, 1 / 8))  # type: ignore
    Requires(Acc(b.rank, 1 / 8) and Acc(b.owned, 1 / 8) and Acc(b.okey, 1 / 8))  # type: ignore
    if a.rank != b.rank or (not a.owned and not b.owned):  # type: ignore
        return a.rank < b.rank  # type: ignore
    if a.owned != b.owned:  # type: ignore
        return not a.owned  # type: ignore
    return lex_lt(a.okey, b.okey)  # type: ignore


@Pure
def hash_ref(a: 'Attr') -> PSeq[int]:
    """Reference hash KEY: the full identity that flows into the hash — the
    creation rank, an ownership flag, then (when owned) the identity key. Two
    attributes contribute the same hash key iff this whole sequence agrees, so
    attributes differing in owner contribute distinct keys."""
    Requires(Acc(a.rank, 1 / 8) and Acc(a.owned, 1 / 8) and Acc(a.okey, 1 / 8))  # type: ignore
    if a.owned:  # type: ignore
        return PSeq(a.rank, 1) + a.okey  # type: ignore
    return PSeq(a.rank, 0)  # type: ignore
# pure-end


def attr_eq(self_: Attr, other: Attr) -> bool:
    # pre-conditions-start
    Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    Ensures(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
    # Equal iff same creation rank AND same owning-container identity.
    Ensures(Result() == eq_ref(self_, other))
    # post-conditions-end
    # impl-start
    return (
        self_.rank == other.rank and
        same_owner(self_, other)
    )
    # impl-end


def attr_lt(self_: Attr, other: Attr) -> bool:
    # pre-conditions-start
    Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    Ensures(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
    # Order by creation rank first; equal-rank owned attributes tie-break by
    # ownership then by lexicographic identity key.
    Ensures(Result() == lt_ref(self_, other))
    # post-conditions-end
    # impl-start
    if (
        self_.rank != other.rank or
        not self_.owned and not other.owned
    ):
        return self_.rank < other.rank
    elif self_.owned != other.owned:
        return not self_.owned  # the owner-less attribute precedes
    else:
        return lex_lt(self_.okey, other.okey)
    # impl-end


def attr_hash_key(self_: Attr) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    # The hash key is the full identity: creation rank, ownership, and (when
    # owned) the identity key. So it depends on the owner, not the rank alone.
    Ensures(Result() == hash_ref(self_))
    # post-conditions-end
    # impl-start
    if self_.owned:
        return PSeq(self_.rank, 1) + self_.okey
    return PSeq(self_.rank, 0)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: attr_eq/attr_lt/attr_hash_key each fully pin Result() to a deep reference (eq_ref/lt_ref/hash_ref) that lives in the FROZEN pure region; therefore any verifying impl is behaviorally identical to the reference. refinement.md legs are all R / A-reference / I — NO A-consumed, NO kind-3 (bundle consumes no @ContractOnly axioms). A-legs audited: A3 same_owner<->getattr(model)-equality (model modeled by (app_label,model_name) pair); B3 lex_lt on flattened okey (NUL sep=0 below all identifier code points) <-> native tuple compare; C1/C2 hash_ref key + builtin hash distinct-on-equal-rank (soundness note correctly restricts to equal-rank to dodge hash(-1)==hash(-2)). axiom_check.py exit 0 (F2P + 13225 boundary + 40000 fuzz pairs).

ATTACKS (cmd: python -m swebench_unified.adversary weakness nagini django__django-13401 <path>), run concurrently in batches of 3:
 atk_1 eq drop same_owner (=prepatch_eq §D witness): exit 2 rejected
 atk_2 eq drop rank keep same_owner: exit 2 rejected
 atk_3 lt tie-break flipped (owner precedes): exit 2 rejected
 atk_4 lt <= in rank branch (boundary): exit 2 rejected
 atk_5 hash drop owner from key (=prepatch_hash §D witness): exit 2 rejected
 atk_6 hash owned-tag 0 collides w/ ownerless: exit 2 rejected
 atk_7 lt reversed rank comparison: exit 2 rejected
 atk_8 ECHO return eq_ref/lt_ref/hash_ref (behaviorally correct): exit 0 CANDIDATE (12.2s).

CANDIDATE RESOLVE (protocol step 2): atk_8 returns the references verbatim => its faithful refined patch = gold post-patch decisions = patch.diff. run_resolve('django__django-13401', faithful_patch) executed via swebench_unified.harness: RESOLVED=True COMPLETED=True NOTE=resolved ATTEMPTS=1 FLAKY=False. F2P 'Field instances from abstract models are not equal.' PASS; all 32 PASS_TO_PASS PASS; no failures. The sole verifying candidate RESOLVES.

Positive control: model.py verifies (nagini_verify.sh exit 0, 11.78s). Prepatch reproduced: atk_1 (eq) and atk_5 (hash) reproduce §D prepatch bugs and are both rejected by the spec.

VERDICT: SOUND — 7 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded/collision) all rejected by verification; the one verifying candidate's materialized faithful patch resolves under the official harness. No verify⇏correct gap found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-13401 (nagini). Spec models the three post-patch Field methods (__eq__, __lt__, __hash__ key) via deep references eq_ref/lt_ref/hash_ref; each impl postcondition pins Result() to its reference. No @ContractOnly axioms consumed.

Empirical validation against the REAL gold-patched repo (worktree at base_commit 453967477e, gold patch applied verbatim):
- conformance_check.py: 0 disagreements over 114,884 pairs (14,884 boundary incl. regression scenario + 100k fuzz, seed 13401), exercising eq, order both ways, and both hash keys.
- Independent adversarial probe over 168,100 pairs targeting the abstraction edges most likely to over-strengthen the spec: shared prefixes across the NUL separator, empty label/name, code point just above NUL (\x01), mixed bare/owned at equal and unequal ranks. 0 divergences for both eq_ref and lt_ref vs real Field.__eq__/__lt__.
- Hash/dedup: regression scenario (rank 0, three distinct model names) reproduces exactly (unequal, ordered by model name, hashes distinct); model keys distinct. Spec correctly scopes the builtin-hash injectivity claim to equal-rank pairs, acknowledging the CPython -1/-2 quirk affects only distinct ranks (irrelevant to the fix).

Abstraction (model class <-> (app_label, model_name) pair) is sound within the modeled domain: Django enforces one model per pair, and both __lt__ (tuple tie-break) and __hash__ (key) already observe the model through that pair. NUL separator (0, below every identifier code point) preserves native tuple order under lex_lt. No input found where the modeled functions disagree with the real callees. The spec is faithful, not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen on the spec_view) PASSES: no diff markers, no gold-patch line reproduced (impl regions elided as '... # implementation elided'), no patched file/module path, no patched symbol echoed, no bug/fix narration. Only distinctive patched symbol is 'clone' (context header) — absent from spec view.

Semantic judgment: the public problem_statement already discloses essentially the whole edit — it names creation_counter-only equality as the root cause and explicitly directs 'adjust __eq__ so that if the field.model is different, they will compare unequal. Similarly ... __hash__ and __lt__', plus 'order first by self.creation_counter ... backward compatibility'. So all three modified operations, the model-identity discriminator, and the creation_counter-first ordering nuance are public.

The spec view uses fully abstracted vocabulary (Attr/rank/owned/okey, attr_eq/attr_lt/attr_hash_key) and never names Field, creation_counter, model, app_label, model_name, _meta, __eq__/__lt__/__hash__, or the patched path django/db/models/fields/__init__.py. The behavioral prose (equality = rank AND owner identity; order by rank first then owner tie-break; hash key = full identity keeps distinct owners apart) is a 1:1 restatement of behaviors the problem_statement itself prescribes. Modeling owner identity as a lexicographic (label,name) pair is a faithful abstraction the spec must supply to be usable and does not localize the edit to repo symbols. The only repo tokens present are the standard instance-id in the title and the generic words 'fields'/'django' — neither reveals localization beyond the public task. Nothing in the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
