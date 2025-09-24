"""
Bot handlers for the Telegram News Feed Bot.

This module contains all the command handlers and callback query handlers
for user interaction with the bot, including source management, subscriptions,
and administrative functions.
"""

from aiogram import Router, F, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from sqlalchemy import func
from typing import List

from models.database import Session, Source, User, Subscription
from services.scraper import ScraperService, ScraperError
from bot.keyboards import (
    main_menu_markup,
    sources_menu_markup,
    source_info_markup,
    confirm_source_deletion_markup,
    subscription_management_markup,
    help_markup,
    admin_markup
)
from config import config
from utils.logger import get_logger

logger = get_logger("handlers")
router = Router()


class AdminStates(StatesGroup):
    """States for admin operations."""
    waiting_for_source = State()


class UserStates(StatesGroup):
    """States for user operations."""
    browsing_sources = State()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Handle the /start command.
    
    Registers new users and displays the welcome message with main menu.
    """
    try:
        with Session() as session:
            user = session.query(User).filter(User.id == message.from_user.id).first()
            
            if not user:
                # Create new user
                user = User(
                    id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                    language_code=message.from_user.language_code or 'en'
                )
                session.add(user)
                session.commit()
                logger.info(f"New user registered: {user.id} (@{user.username})")
                
                welcome_text = (
                    "🎉 Welcome to the News Feed Bot!\n\n"
                    "I can help you stay updated with your favorite content sources:\n"
                    "• RSS feeds\n"
                    "• Websites\n"
                    "• Social media (with limitations)\n\n"
                    "Use the menu below to get started!"
                )
            else:
                # Update user info and last active time
                user.username = message.from_user.username
                user.first_name = message.from_user.first_name
                user.last_name = message.from_user.last_name
                user.last_active = datetime.utcnow()
                session.commit()
                
                welcome_text = (
                    f"👋 Welcome back, {user.first_name or user.username or 'User'}!\n\n"
                    "Ready to catch up on your news feeds?"
                )
        
        await message.answer(welcome_text, reply_markup=main_menu_markup())
        
    except Exception as e:
        logger.error(f"Error in start command for user {message.from_user.id}: {e}")
        await message.answer("❌ Sorry, something went wrong. Please try again later.")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle the /help command."""
    help_text = (
        "🔧 **News Feed Bot Help**\n\n"
        "**Available Commands:**\n"
        "/start - Start the bot and show main menu\n"
        "/help - Show this help message\n"
        "/menu - Show the main menu\n"
        "/sources - List all available sources\n"
        "/subscriptions - Manage your subscriptions\n\n"
        "**For Admins:**\n"
        "/add_source - Add a new content source\n"
        "/admin - Admin panel\n"
        "/stats - Bot statistics\n\n"
        "**Supported Source Types:**\n"
        "📰 RSS/Atom feeds\n"
        "🌐 Generic websites\n"
        "🐦 Twitter (via RSS alternatives)\n"
        "📺 YouTube channels\n"
        "🔴 Reddit subreddits\n\n"
        "**Note:** Facebook and Instagram require official API access."
    )
    
    await message.answer(help_text, parse_mode="Markdown", reply_markup=help_markup())


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Handle the /menu command."""
    await message.answer("📋 Main Menu:", reply_markup=main_menu_markup())


@router.message(Command("sources"))
async def cmd_sources(message: Message):
    """Handle the /sources command to list all sources."""
    await _show_sources_list(message)


@router.message(Command("subscriptions"))
async def cmd_subscriptions(message: Message):
    """Handle the /subscriptions command to show user's subscriptions."""
    await _show_user_subscriptions(message)


@router.message(Command("add_source"))
async def cmd_add_source(message: Message, state: FSMContext):
    """
    Handle the /add_source command (admin only).
    
    Initiates the process of adding a new content source.
    """
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("❌ Only administrators can add sources.")
        return
    
    await state.set_state(AdminStates.waiting_for_source)
    await message.answer(
        "🔗 **Add New Source**\n\n"
        "Please send the source URL. I support:\n\n"
        "📰 **RSS/Atom feeds**\n"
        "🌐 **Websites** (I'll try to extract articles)\n"
        "🐦 **Twitter profiles** (via RSS alternatives)\n"
        "📺 **YouTube channels**\n"
        "🔴 **Reddit subreddits**\n\n"
        "**Examples:**\n"
        "• `https://feeds.feedburner.com/TechCrunch`\n"
        "• `https://www.reddit.com/r/technology`\n"
        "• `https://www.youtube.com/channel/UCBJycsmduvYEL83R_U4JriQ`\n\n"
        "Send /cancel to abort.",
        parse_mode="Markdown"
    )


@router.message(F.text, AdminStates.waiting_for_source)
async def process_new_source(message: Message, state: FSMContext):
    """
    Process the URL for a new source.
    
    Validates the URL, detects the source type, and adds it to the database.
    """
    if message.text.lower() == '/cancel':
        await state.clear()
        await message.answer("➰ Source addition cancelled.")
        return
    
    url = message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        await message.answer(
            "❌ Invalid URL. Please provide a complete URL starting with http:// or https://\n"
            "Send /cancel to abort."
        )
        return
    
    try:
        # Show processing message
        processing_msg = await message.answer("🔍 Analyzing source... This may take a moment.")
        
        # Detect source type and validate
        async with ScraperService() as scraper:
            source_type = await scraper.detect_source_type(url)
            
            # Try to scrape a sample to validate
            sample_items = await scraper.scrape_source(url, source_type)
        
        with Session() as session:
            # Check if source already exists
            existing_source = session.query(Source).filter(Source.url == url).first()
            if existing_source:
                await processing_msg.edit_text("❌ This source is already configured!")
                await state.clear()
                return
            
            # Create new source
            source = Source(
                url=url,
                type=source_type,
                added_by=message.from_user.id,
                title=f"{source_type.upper()} Source"
            )
            session.add(source)
            session.commit()
            
            # Get the source ID for the response
            source_id = source.id
        
        await state.clear()
        
        # Success message
        success_text = (
            f"✅ **Source Added Successfully!**\n\n"
            f"🔗 **URL:** {url}\n"
            f"📱 **Type:** {source_type.upper()}\n"
            f"📊 **Sample Items:** {len(sample_items)} found\n\n"
            f"The source is now active and will be checked regularly for updates."
        )
        
        await processing_msg.edit_text(success_text, parse_mode="Markdown")
        logger.info(f"Admin {message.from_user.id} added source: {url} (type: {source_type})")
        
    except ScraperError as e:
        await processing_msg.edit_text(f"❌ Error adding source: {str(e)}")
        logger.error(f"Scraper error while adding source {url}: {e}")
    except Exception as e:
        await processing_msg.edit_text(f"❌ Unexpected error: {str(e)}")
        logger.error(f"Error adding source {url}: {e}")


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Handle the /admin command (admin only)."""
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("❌ Access denied. This command is for administrators only.")
        return
    
    await message.answer("🔧 **Admin Panel**", parse_mode="Markdown", reply_markup=admin_markup())


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Handle the /stats command to show bot statistics."""
    try:
        with Session() as session:
            # Gather statistics
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.is_active == True).count()
            total_sources = session.query(Source).count()
            active_sources = session.query(Source).filter(Source.is_active == True).count()
            total_subscriptions = session.query(Subscription).count()
            active_subscriptions = session.query(Subscription).filter(Subscription.is_active == True).count()
            
            # Source type breakdown
            source_types = session.query(Source.type, func.count(Source.id)).group_by(Source.type).all()
            
        stats_text = (
            f"📊 **Bot Statistics**\n\n"
            f"👥 **Users:** {active_users}/{total_users} active\n"
            f"📰 **Sources:** {active_sources}/{total_sources} active\n"
            f"🔔 **Subscriptions:** {active_subscriptions}/{total_subscriptions} active\n\n"
            f"**Source Types:**\n"
        )
        
        for source_type, count in source_types:
            emoji = {"rss": "📰", "twitter": "🐦", "facebook": "📘", "instagram": "📸", "website": "🌐", "youtube": "📺", "reddit": "🔴"}.get(source_type, "📄")
            stats_text += f"{emoji} {source_type.upper()}: {count}\n"
        
        await message.answer(stats_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error generating stats: {e}")
        await message.answer("❌ Error generating statistics.")


# Callback query handlers
@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Handle main menu callback."""
    await callback.message.edit_text(
        "📋 Main Menu:",
        reply_markup=main_menu_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "list_sources")
async def callback_list_sources(callback: CallbackQuery):
    """Handle list sources callback."""
    await _show_sources_list(callback.message, edit=True)
    await callback.answer()


@router.callback_query(F.data == "my_subscriptions")
async def callback_my_subscriptions(callback: CallbackQuery):
    """Handle my subscriptions callback."""
    await _show_user_subscriptions(callback.message, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("source_info_"))
async def callback_source_info(callback: CallbackQuery):
    """Handle source info callback."""
    try:
        source_id = int(callback.data.split("_")[-1])
        
        with Session() as session:
            source = session.query(Source).filter(Source.id == source_id).first()
            if not source:
                await callback.answer("❌ Source not found!")
                return
            
            # Check if user is subscribed
            subscription = session.query(Subscription).filter(
                Subscription.user_id == callback.from_user.id,
                Subscription.source_id == source_id
            ).first()
            
            is_subscribed = subscription is not None and subscription.is_active
            
            # Check if user is admin for delete button
            is_admin = callback.from_user.id in config.ADMIN_IDS
            
        source_text = (
            f"📰 **Source Information**\n\n"
            f"🔗 **URL:** {source.url}\n"
            f"📱 **Type:** {source.type.upper()}\n"
            f"✅ **Status:** {'Active' if source.is_active else 'Inactive'}\n"
            f"📊 **Checks:** {source.check_count}\n"
            f"❌ **Errors:** {source.error_count}\n\n"
        )
        
        if source.last_checked:
            source_text += f"🕐 **Last Checked:** {source.last_checked.strftime('%Y-%m-%d %H:%M UTC')}\n"
        
        if source.last_updated:
            source_text += f"🆕 **Last Updated:** {source.last_updated.strftime('%Y-%m-%d %H:%M UTC')}\n"
        
        keyboard = source_info_markup(source_id, is_subscribed)
        
        # Remove delete button for non-admins
        if not is_admin and len(keyboard.inline_keyboard) > 1:
            keyboard.inline_keyboard.pop(1)  # Remove delete button
        
        await callback.message.edit_text(source_text, parse_mode="Markdown", reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing source info: {e}")
        await callback.answer("❌ Error loading source information.")


@router.callback_query(F.data.startswith("subscribe_"))
async def callback_subscribe(callback: CallbackQuery):
    """Handle subscribe callback."""
    try:
        source_id = int(callback.data.split("_")[-1])
        
        with Session() as session:
            # Check if source exists
            source = session.query(Source).filter(Source.id == source_id).first()
            if not source:
                await callback.answer("❌ Source not found!")
                return
            
            # Check for existing subscription
            existing = session.query(Subscription).filter(
                Subscription.user_id == callback.from_user.id,
                Subscription.source_id == source_id
            ).first()
            
            if existing:
                if existing.is_active:
                    await callback.answer("ℹ️ You're already subscribed to this source!")
                    return
                else:
                    # Reactivate subscription
                    existing.is_active = True
                    existing.notification_enabled = True
            else:
                # Create new subscription
                subscription = Subscription(
                    user_id=callback.from_user.id,
                    source_id=source_id
                )
                session.add(subscription)
            
            session.commit()
        
        await callback.answer("✅ Successfully subscribed!")
        
        # Refresh the source info display
        await callback_source_info(callback)
        
    except Exception as e:
        logger.error(f"Error subscribing to source: {e}")
        await callback.answer("❌ Error subscribing to source.")


@router.callback_query(F.data.startswith("unsubscribe_"))
async def callback_unsubscribe(callback: CallbackQuery):
    """Handle unsubscribe callback."""
    try:
        source_id = int(callback.data.split("_")[-1])
        
        with Session() as session:
            subscription = session.query(Subscription).filter(
                Subscription.user_id == callback.from_user.id,
                Subscription.source_id == source_id
            ).first()
            
            if not subscription:
                await callback.answer("ℹ️ You're not subscribed to this source!")
                return
            
            subscription.is_active = False
            session.commit()
        
        await callback.answer("✅ Successfully unsubscribed!")
        
        # Refresh the source info display
        await callback_source_info(callback)
        
    except Exception as e:
        logger.error(f"Error unsubscribing from source: {e}")
        await callback.answer("❌ Error unsubscribing from source.")


@router.callback_query(F.data.startswith("delete_source_"))
async def callback_delete_source(callback: CallbackQuery):
    """Handle delete source callback (admin only)."""
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("❌ Access denied!")
        return
    
    source_id = int(callback.data.split("_")[-1])
    
    await callback.message.edit_reply_markup(
        reply_markup=confirm_source_deletion_markup(source_id)
    )
    await callback.answer("⚠️ Confirm deletion")


@router.callback_query(F.data.startswith("confirm_delete_"))
async def callback_confirm_delete(callback: CallbackQuery):
    """Handle confirm delete callback (admin only)."""
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("❌ Access denied!")
        return
    
    try:
        source_id = int(callback.data.split("_")[-1])
        
        with Session() as session:
            source = session.query(Source).filter(Source.id == source_id).first()
            if source:
                # Delete all subscriptions first
                session.query(Subscription).filter(Subscription.source_id == source_id).delete()
                # Delete the source
                session.delete(source)
                session.commit()
                
                await callback.message.edit_text("✅ Source deleted successfully!")
                logger.info(f"Admin {callback.from_user.id} deleted source: {source.url}")
            else:
                await callback.message.edit_text("❌ Source not found!")
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error deleting source: {e}")
        await callback.message.edit_text("❌ Error deleting source!")
        await callback.answer()


# Helper functions
async def _show_sources_list(message: Message, edit: bool = False):
    """Show the list of all sources."""
    try:
        with Session() as session:
            sources = session.query(Source).filter(Source.is_active == True).all()
        
        if not sources:
            text = "📋 **Available Sources**\n\nNo sources configured yet."
            keyboard = main_menu_markup()
        else:
            text = f"📋 **Available Sources** ({len(sources)})\n\nSelect a source to view details and subscribe:"
            keyboard = sources_menu_markup(sources)
        
        if edit:
            await message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"Error showing sources list: {e}")
        error_text = "❌ Error loading sources list."
        if edit:
            await message.edit_text(error_text)
        else:
            await message.answer(error_text)


async def _show_user_subscriptions(message: Message, edit: bool = False):
    """Show the user's subscriptions."""
    try:
        with Session() as session:
            subscriptions = session.query(Subscription).join(Source).filter(
                Subscription.user_id == message.from_user.id,
                Subscription.is_active == True,
                Source.is_active == True
            ).all()
            
            user_sources = [sub.source for sub in subscriptions]
        
        if not user_sources:
            text = (
                "🔔 **Your Subscriptions**\n\n"
                "You're not subscribed to any sources yet.\n"
                "Browse available sources to get started!"
            )
        else:
            text = f"🔔 **Your Subscriptions** ({len(user_sources)})\n\nYou're subscribed to:"
        
        keyboard = subscription_management_markup(user_sources)
        
        if edit:
            await message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"Error showing user subscriptions: {e}")
        error_text = "❌ Error loading your subscriptions."
        if edit:
            await message.edit_text(error_text)
        else:
            await message.answer(error_text)


def setup_handlers(dp: Dispatcher) -> None:
    """
    Set up all handlers with the dispatcher.
    
    Args:
        dp: Aiogram dispatcher instance
    """
    dp.include_router(router)
    logger.info("Handlers registered successfully")
