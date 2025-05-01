import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from bot.handlers import setup_handlers
from utils.logger import setup_logger
from config import config

async def main():
    setup_logger()
    
    storage = RedisStorage.from_url("redis://localhost:6379/0")
    bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=storage)
    
    await setup_handlers(dp)
    
    from services.scheduler import start_scheduler
    asyncio.create_task(start_scheduler(bot))
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
