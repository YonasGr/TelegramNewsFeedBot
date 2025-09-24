"""
Inline keyboard markups for the Telegram News Feed Bot.

This module contains all the inline keyboard configurations used throughout
the bot for user interaction and navigation.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional
from models.database import Source


def main_menu_markup() -> InlineKeyboardMarkup:
    """
    Create the main menu inline keyboard markup.
    
    Returns:
        InlineKeyboardMarkup with main menu options
    """
    keyboard = [
        [
            InlineKeyboardButton(text="📋 View Sources", callback_data="list_sources"),
            InlineKeyboardButton(text="📊 My Subscriptions", callback_data="my_subscriptions")
        ],
        [
            InlineKeyboardButton(text="🔍 Browse Available Sources", callback_data="browse_sources"),
        ],
        [
            InlineKeyboardButton(text="❓ Help", callback_data="help"),
            InlineKeyboardButton(text="📈 Bot Stats", callback_data="stats")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def sources_menu_markup(sources: List[Source]) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for managing sources.
    
    Args:
        sources: List of Source objects to display
    
    Returns:
        InlineKeyboardMarkup with source management options
    """
    keyboard = []
    
    # Add buttons for each source (max 10 to avoid message limits)
    for source in sources[:10]:
        source_type_emoji = {
            "rss": "📰",
            "twitter": "🐦",
            "facebook": "📘",
            "instagram": "📸",
            "website": "🌐"
        }.get(source.type, "📄")
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{source_type_emoji} {source.type.upper()}: {source.url[:30]}...",
                callback_data=f"source_info_{source.id}"
            )
        ])
    
    # Add navigation buttons
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def source_info_markup(source_id: int, is_subscribed: bool = False) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for source information and actions.
    
    Args:
        source_id: ID of the source
        is_subscribed: Whether the user is subscribed to this source
    
    Returns:
        InlineKeyboardMarkup with source action options
    """
    keyboard = []
    
    # Subscribe/Unsubscribe button
    if is_subscribed:
        keyboard.append([
            InlineKeyboardButton(
                text="🔕 Unsubscribe",
                callback_data=f"unsubscribe_{source_id}"
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                text="🔔 Subscribe",
                callback_data=f"subscribe_{source_id}"
            )
        ])
    
    # Admin-only delete button (will be shown conditionally)
    keyboard.append([
        InlineKeyboardButton(
            text="🗑️ Delete Source",
            callback_data=f"delete_source_{source_id}"
        )
    ])
    
    # Navigation buttons
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Back to Sources", callback_data="list_sources"),
        InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def confirm_source_deletion_markup(source_id: int) -> InlineKeyboardMarkup:
    """
    Create a confirmation keyboard for source deletion.
    
    Args:
        source_id: ID of the source to delete
    
    Returns:
        InlineKeyboardMarkup with confirmation options
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text="✅ Yes, Delete",
                callback_data=f"confirm_delete_{source_id}"
            ),
            InlineKeyboardButton(
                text="❌ Cancel",
                callback_data=f"source_info_{source_id}"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def subscription_management_markup(user_subscriptions: List[Source]) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for managing user subscriptions.
    
    Args:
        user_subscriptions: List of sources the user is subscribed to
    
    Returns:
        InlineKeyboardMarkup with subscription management options
    """
    keyboard = []
    
    if not user_subscriptions:
        keyboard.append([
            InlineKeyboardButton(
                text="🔍 Browse Available Sources",
                callback_data="browse_sources"
            )
        ])
    else:
        # Add buttons for each subscription (max 10)
        for source in user_subscriptions[:10]:
            source_type_emoji = {
                "rss": "📰",
                "twitter": "🐦",
                "facebook": "📘",
                "instagram": "📸",
                "website": "🌐"
            }.get(source.type, "📄")
            
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{source_type_emoji} {source.url[:35]}...",
                    callback_data=f"subscription_info_{source.id}"
                )
            ])
    
    # Navigation
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def help_markup() -> InlineKeyboardMarkup:
    """
    Create the help menu inline keyboard markup.
    
    Returns:
        InlineKeyboardMarkup with help options
    """
    keyboard = [
        [
            InlineKeyboardButton(text="🔧 Setup Guide", callback_data="help_setup"),
            InlineKeyboardButton(text="🎛️ Commands", callback_data="help_commands")
        ],
        [
            InlineKeyboardButton(text="📱 Supported Sources", callback_data="help_sources"),
            InlineKeyboardButton(text="❓ FAQ", callback_data="help_faq")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="main_menu")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def admin_markup() -> InlineKeyboardMarkup:
    """
    Create the admin panel inline keyboard markup.
    
    Returns:
        InlineKeyboardMarkup with admin options
    """
    keyboard = [
        [
            InlineKeyboardButton(text="➕ Add Source", callback_data="admin_add_source"),
            InlineKeyboardButton(text="📊 Bot Statistics", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton(text="👥 User Management", callback_data="admin_users"),
            InlineKeyboardButton(text="🔄 Force Update", callback_data="admin_force_update")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="main_menu")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)