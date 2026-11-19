import asyncio
import json
from collections import defaultdict


class OrderEventBroker:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[tuple[asyncio.AbstractEventLoop, asyncio.Queue]]] = (
            defaultdict(set)
        )

    def subscribe(self, order_id: str) -> tuple[asyncio.AbstractEventLoop, asyncio.Queue]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[order_id].add((loop, queue))
        return loop, queue

    def unsubscribe(
        self,
        order_id: str,
        subscriber: tuple[asyncio.AbstractEventLoop, asyncio.Queue],
    ) -> None:
        subscribers = self._subscribers[order_id]
        subscribers.discard(subscriber)
        if not subscribers:
            self._subscribers.pop(order_id, None)

    def publish(self, order_id: str, status: str) -> None:
        payload = json.dumps({"order_id": order_id, "status": status}, ensure_ascii=False)
        for loop, queue in list(self._subscribers.get(order_id, set())):
            loop.call_soon_threadsafe(queue.put_nowait, payload)


order_events = OrderEventBroker()
