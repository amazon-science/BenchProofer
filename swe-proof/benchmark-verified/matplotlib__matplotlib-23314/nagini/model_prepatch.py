"""Twin-artifact model for matplotlib__matplotlib-23314.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A renderable container exposes a boolean visibility flag and a body of
  drawable content. Its render entry point, given an output sink that
  accumulates the work it is asked to perform, must honour the visibility
  flag the same way every other renderable container does:

    (1) when the container is flagged not-visible, the render entry point
        performs NO drawing work whatsoever — the sink is left exactly as it
        was on entry (no content is emitted to it); and

    (2) when the container is flagged visible, the render entry point performs
        its full body of work — the sink receives the container's entire
        drawable content.

So the amount of work delivered to the sink is the container's content when it
is visible and zero when it is not; visibility gates the whole render pass.

The output sink is modelled as a minimal mutable object carrying only the
touched field — a running tally of work it has received (``work``). The
container is modelled as a minimal object carrying only the two fields the
behaviour reads — its visibility flag (``visible``) and the size of its
drawable body (``content``, a non-negative quantity), both read-only here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Sink:
    def __init__(self) -> None:
        Ensures(Acc(self.work) and self.work == 0)  # type: ignore
        self.work = 0  # type: int


class Container:
    def __init__(self, visible: bool, content: int) -> None:
        Requires(content >= 0)
        Ensures(Acc(self.visible, 1 / 2) and self.visible == visible)  # type: ignore
        Ensures(Acc(self.content, 1 / 2) and self.content == content)  # type: ignore
        Ensures(self.content >= 0)  # type: ignore
        self.visible = visible    # type: bool
        self.content = content    # type: int


# axioms-start
# (no unchanged callee needs axiomatizing: the rendering body is abstracted as
#  the single quantity `self.content` and the whole pass is modeled deeply.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def render(self: Container, sink: Sink) -> None:
    # pre-conditions-start
    Requires(Acc(self.visible, 1 / 2))
    Requires(Acc(self.content, 1 / 2))
    Requires(self.content >= 0)
    Requires(Acc(sink.work))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # read-only container fields are returned at the same fractional permission
    # and are unchanged by the render pass.
    Ensures(Acc(self.visible, 1 / 2) and self.visible == Old(self.visible))
    Ensures(Acc(self.content, 1 / 2) and self.content == Old(self.content))
    Ensures(Acc(sink.work))
    # (1) not-visible => no work is delivered to the sink (left as on entry).
    Ensures(Implies(not self.visible, sink.work == Old(sink.work)))
    # (2) visible => the sink receives the container's entire drawable content.
    Ensures(Implies(self.visible, sink.work == Old(sink.work) + self.content))
    # post-conditions-end
    # impl-start
    sink.work = sink.work + self.content
    return
    # impl-end
