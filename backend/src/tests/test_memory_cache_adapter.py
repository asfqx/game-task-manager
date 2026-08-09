import asyncio
import unittest

from app.adapters.cache.adapters.memory_adapter import MemoryCacheAdapter


class MemoryCacheAdapterTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_stores_reads_and_deletes_values(self) -> None:
        cache = MemoryCacheAdapter()

        self.assertFalse(await cache.exists("task:1"))
        self.assertIsNone(await cache.get("task:1"))

        await cache.set("task:1", {"status": "IN_WORK"})

        self.assertTrue(await cache.exists("task:1"))
        self.assertEqual(await cache.get("task:1"), {"status": "IN_WORK"})

        await cache.delete("task:1")

        self.assertFalse(await cache.exists("task:1"))
        self.assertIsNone(await cache.get("task:1"))

    async def test_publishes_json_to_active_subscribers(self) -> None:
        cache = MemoryCacheAdapter()
        subscription = cache.subscribe("notifications")
        next_message = asyncio.create_task(anext(subscription))

        await asyncio.sleep(0)

        subscriber_count = await cache.publish(
            "notifications",
            {"task_uuid": "task-1", "xp": 50},
        )

        self.assertEqual(subscriber_count, 1)
        self.assertEqual(
            await next_message,
            '{"task_uuid": "task-1", "xp": 50}',
        )

        await subscription.aclose()

    async def test_publishes_text_without_subscribers(self) -> None:
        cache = MemoryCacheAdapter()

        subscriber_count = await cache.publish("notifications", "task updated")

        self.assertEqual(subscriber_count, 0)

    async def test_publishes_to_each_subscriber_and_cleans_closed_channels(self) -> None:
        cache = MemoryCacheAdapter()
        first_subscription = cache.subscribe("notifications")
        second_subscription = cache.subscribe("notifications")
        first_message = asyncio.create_task(anext(first_subscription))
        second_message = asyncio.create_task(anext(second_subscription))

        await asyncio.sleep(0)

        subscriber_count = await cache.publish("notifications", "task updated")

        self.assertEqual(subscriber_count, 2)
        self.assertEqual(await first_message, "task updated")
        self.assertEqual(await second_message, "task updated")

        await first_subscription.aclose()
        await second_subscription.aclose()

        self.assertNotIn("notifications", cache._channels)

    async def test_subscription_yields_none_on_timeout(self) -> None:
        cache = MemoryCacheAdapter()
        subscription = cache.subscribe("notifications", timeout=0.001)

        self.assertIsNone(await anext(subscription))

        await subscription.aclose()


if __name__ == "__main__":
    unittest.main()
