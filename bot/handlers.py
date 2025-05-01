from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from models.database import Session, Source, User
from services.scraper import ScraperService
from bot.keyboards import (
    main_menu_markup,
    sources_menu_markup,
    confirm_source_deletion_markup
)
from models.schemas import SourceCreate
from config import config

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    with Session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        if not user:
            user = User(id=message.from_user.id, username=message.from_user.username)
            session.add(user)
            session.commit()
    
    await message.answer(
        "📰 Welcome to Feed Aggregator Bot!\n\n"
        "I can monitor websites and social media for new content and deliver it to you.",
        reply_markup=main_menu_markup()
    )

@router.message(Command("add_source"))
async def add_source(message: Message, state: FSMContext):
    if message.from_user.id not in config.ADMIN_IDS:
        return await message.answer("❌ Only admins can add sources.")
    
    await state.set_state("waiting_for_source")
    await message.answer(
        "🔗 Please send the source URL (RSS feed or supported social media profile):\n\n"
        "Supported platforms:\n"
        "- Twitter/X (profile URLs)\n"
        "- Facebook (page URLs)\n"
        "- Instagram (profile URLs)\n"
        "- Any website with RSS feed"
    )

@router.message(F.text, state="waiting_for_source"))
async def process_source(message: Message, state: FSMContext):
    url = message.text.strip()
    
    try:
        scraper = ScraperService()
        source_type = await scraper.detect_source_type(url)
        
        with Session() as session:
            source = Source(
                url=url,
                type=source_type,
                added_by=message.from_user.id
            )
            session.add(source)
            session.commit()
        
        await state.clear()
        await message.answer(f"✅ Source added successfully!\nType: {source_type}")
    except Exception as e:
        await message.answer(f"❌ Error adding source: {str(e)}")

@router.message(Command("list_sources"))
async def list_sources(message: Message):
    with Session() as session:
        sources = session.query(Source).all()
        
    if not sources:
        return await message.answer("No sources configured yet.")
    
    response = ["📋 Configured Sources:"]
    for source in sources:
        response.append(f"\n- {source.type.upper()}: {source.url}")
    
    await message.answer("\n".join(response), reply_markup=sources_menu_markup(sources))

@router.callback_query(F.data.startswith("delete_source_"))
async def delete_source(callback: CallbackQuery):
    source_id = int(callback.data.split("_")[-1])
    
    with Session() as session:
        source = session.query(Source).filter(Source.id == source_id).first()
        if not source:
            return await callback.answer("Source not found!")
        
        await callback.message.edit_reply_markup(
            reply_markup=confirm_source_deletion_markup(source_id)
        )
        await callback.answer()

@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete(callback: CallbackQuery):
    source_id = int(callback.data.split("_")[-1])
    
    with Session() as session:
        source = session.query(Source).filter(Source.id == source_id).first()
        if source:
            session.delete(source)
            session.commit()
            await callback.message.edit_text("✅ Source deleted successfully!")
        else:
            await callback.message.edit_text("❌ Source not found!")
    
    await callback.answer()

def setup_handlers(dp: Dispatcher):
    dp.include_router(router)
