from __future__ import annotations

import asyncio

from bot import setup_bot
from config import load_settings
from config import setup_logging
from dispatcher import setup_dispatcher


async def main() -> None:
    logger = setup_logging()
    settings = load_settings()

    bot = await setup_bot(logger, settings)
    await setup_dispatcher(bot)


if __name__ == '__main__':
    asyncio.run(main())
