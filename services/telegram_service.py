"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: telegram_service.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
import os
import logging
import json
import random
from datetime import datetime
from threading import Thread

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from models import db, TelegramSubscriber, SystemConfig
from services.notification_service import NotificationService
from services.translation_service import t
from utils.system_gate import SystemGate

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Bot
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False) if TELEGRAM_TOKEN else None

class TelegramService:
    @staticmethod
    def is_enabled():
        return bot is not None

    @staticmethod
    def test_connection():
        if not bot:
            return False, "Bot not initialized"
        try:
            info = bot.get_me()
            return True, f"Connected as @{info.username}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_admin_subscribers():
        """Get all approved subscribers who are also admins (if we linked them users)"""
        # For now, we notify all approved subscribers or specific roles.
        # The prompt implies a general list of subscribers with preferences.
        return TelegramSubscriber.query.filter_by(status='APPROVED').all()

    @staticmethod
    def send_message(chat_id, text, parse_mode='Markdown'):
        if not TelegramService.is_enabled():
            logger.warning("Telegram Bot Token not configured. Cannot send message.")
            return False

        # Check system status
        if not SystemGate.is_active():
            return False

        try:
            # Security Check: Verify status before sending every single message
            subscriber = TelegramSubscriber.query.filter_by(telegram_chat_id=str(chat_id)).first()
            if not subscriber or subscriber.status != 'APPROVED':
                logger.warning(f"Security blocked message to {chat_id}: User not APPROVED.")
                return False

            bot.send_message(chat_id, text, parse_mode=parse_mode)
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
            return False

    @staticmethod
    def notify_entry(flight):
        """
        Notify subscribers about aircraft entry.
        """
        subscribers = TelegramSubscriber.query.filter_by(status='APPROVED').all()

        # Format Message
        callsign = flight.callsign
        origin = flight.departure_icao or "N/A"
        dest = flight.arrival_icao or "N/A"

        msg = (
            f"{t('notifications.entry_title', 'fr')}\n"
            f"{t('notifications.entry_flight', 'fr')}: `{callsign}`\n"
            f"{t('notifications.entry_route', 'fr')}: {origin} ➡️ {dest}\n"
            f"{t('notifications.entry_type', 'fr')}: {flight.flight_type.upper() if flight.flight_type else 'N/A'}"
        )

        for sub in subscribers:
            prefs = sub.preferences or {}
            if prefs.get('notify_entry', True):
                TelegramService.send_message(sub.telegram_chat_id, msg)

    @staticmethod
    def notify_exit(overflight):
        """
        Notify subscribers about aircraft exit (Exit + Summary).
        """
        subscribers = TelegramSubscriber.query.filter_by(status='APPROVED').all()

        # Format Message
        flight = overflight.flight
        callsign = flight.callsign if flight else "Inconnu"

        dist = f"{overflight.distance_km:.1f}km" if overflight.distance_km else "N/A"
        dur = f"{int(overflight.duration_minutes)}min" if overflight.duration_minutes else "N/A"
        alt = f"FL{int(overflight.exit_alt/100)}" if overflight.exit_alt else "N/A"

        msg = (
            f"{t('notifications.exit_title', 'fr')}\n"
            f"{t('notifications.entry_flight', 'fr')}: `{callsign}`\n"
            f"{t('notifications.exit_dist', 'fr')}: {dist} | {t('notifications.exit_dur', 'fr')}: {dur}\n"
            f"{t('notifications.exit_alt', 'fr')}: {alt}"
        )

        for sub in subscribers:
            prefs = sub.preferences or {}
            if prefs.get('notify_exit', True):
                TelegramService.send_message(sub.telegram_chat_id, msg)

    @staticmethod
    def notify_billing(invoice):
        """
        Notify subscribers about generated billing.
        """
        subscribers = TelegramSubscriber.query.filter_by(status='APPROVED').all()

        amount = f"{invoice.total_amount:.2f} {invoice.currency}"
        airline = invoice.airline.name if invoice.airline else "Inconnu"

        msg = (
            f"{t('notifications.billing_title', 'fr')}\n"
            f"{t('notifications.billing_ref', 'fr')}: `{invoice.invoice_number}`\n"
            f"{t('notifications.billing_client', 'fr')}: {airline}\n"
            f"{t('notifications.billing_amount', 'fr')}: *{amount}*\n"
            f"{t('notifications.billing_type', 'fr')}: {invoice.invoice_type}"
        )

        for sub in subscribers:
            prefs = sub.preferences or {}
            if prefs.get('notify_billing', True):
                TelegramService.send_message(sub.telegram_chat_id, msg)

    @staticmethod
    def notify_alert(title, message, severity="INFO"):
        """
        Notify subscribers about alerts/emergencies.
        """
        subscribers = TelegramSubscriber.query.filter_by(status='APPROVED').all()

        icon = "🚨" if severity in ['CRITICAL', 'HIGH'] else "⚠️"

        # Use template but replace icon if needed, or construct manually if template includes icon
        # Template: 🚨 *ALERTE: {title}*
        title_text = t('notifications.alert_title_fmt', 'fr').format(title=title)
        if icon != "🚨":
             title_text = title_text.replace("🚨", icon)

        msg = (
            f"{title_text}\n"
            f"{message}"
        )

        for sub in subscribers:
            prefs = sub.preferences or {}
            if prefs.get('notify_alerts', True):
                TelegramService.send_message(sub.telegram_chat_id, msg)


# ==============================================================================
# BOT HANDLERS
# ==============================================================================

def register_bot_handlers(app_context_provider):
    """
    Register bot command handlers.
    app_context_provider: function that returns app.app_context()
    """
    if not bot:
        return

    @bot.message_handler(func=lambda message: not SystemGate.is_active())
    def handle_system_offline(message):
         bot.reply_to(message, "⚠️ Le système ATM-RDC est actuellement éteint pour maintenance/sécurité.")

    @bot.message_handler(commands=['start'])
    def handle_start(message):
        chat_id = str(message.chat.id)
        username = message.from_user.username
        first_name = message.from_user.first_name

        # We need application context to access DB
        with app_context_provider():
            subscriber = TelegramSubscriber.query.filter_by(telegram_chat_id=chat_id).first()

            if not subscriber:
                # Create PENDING request
                otp_code = f"{random.randint(0, 999999):06d}"
                subscriber = TelegramSubscriber(
                    telegram_chat_id=chat_id,
                    username=username,
                    first_name=first_name,
                    status='PENDING',
                    verification_code=otp_code,
                    code_generated_at=datetime.utcnow()
                )
                db.session.add(subscriber)
                db.session.commit()

                # Respond with OTP
                otp_fmt = f"{otp_code[:3]} {otp_code[3:]}"
                msg = t('notifications.pending_msg', 'fr').format(code_formatted=otp_fmt)
                bot.reply_to(message, msg, parse_mode='Markdown')

                # Notify Internal Admins
                NotificationService.notify_admins(
                    type='security',
                    title=t('notifications.new_request_title', 'fr'),
                    message=t('notifications.new_request_msg', 'fr').format(username=username, first_name=first_name),
                    link="/admin/telegram"
                )

            elif subscriber.status == 'PENDING':
                # If code exists, resend it, otherwise generate new one
                if not subscriber.verification_code:
                    otp_code = f"{random.randint(0, 999999):06d}"
                    subscriber.verification_code = otp_code
                    subscriber.code_generated_at = datetime.utcnow()
                    db.session.commit()
                else:
                    otp_code = subscriber.verification_code

                otp_fmt = f"{otp_code[:3]} {otp_code[3:]}"
                msg = t('notifications.pending_msg', 'fr').format(code_formatted=otp_fmt)
                bot.reply_to(message, msg, parse_mode='Markdown')

            elif subscriber.status == 'APPROVED':
                msg = t('notifications.welcome_msg', 'fr').format(name=first_name)
                bot.reply_to(message, msg)

            elif subscriber.status in ['REJECTED', 'REVOKED']:
                bot.reply_to(message, t('notifications.access_denied', 'fr'))

    @bot.message_handler(commands=['settings'])
    def handle_settings(message):
        chat_id = str(message.chat.id)

        with app_context_provider():
            subscriber = TelegramSubscriber.query.filter_by(telegram_chat_id=chat_id).first()

            if not subscriber or subscriber.status != 'APPROVED':
                bot.reply_to(message, t('notifications.not_authorized', 'fr'))
                return

            # Build Inline Keyboard
            markup = InlineKeyboardMarkup()
            prefs = subscriber.preferences or {}

            # Map keys to labels
            options = [
                ('notify_entry', t('notifications.setting_entry', 'fr')),
                ('notify_exit', t('notifications.setting_exit', 'fr')),
                ('notify_alerts', t('notifications.setting_alerts', 'fr')),
                ('notify_billing', t('notifications.setting_billing', 'fr')),
                ('notify_daily_report', t('notifications.setting_daily', 'fr'))
            ]

            for key, label in options:
                is_active = prefs.get(key, False)
                status_icon = "✅" if is_active else "❌"
                # Callback data: toggle:key
                markup.add(InlineKeyboardButton(f"{label} {status_icon}", callback_data=f"toggle:{key}"))

            bot.send_message(chat_id, t('notifications.settings_title', 'fr'), reply_markup=markup, parse_mode='Markdown')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('toggle:'))
    def callback_query(call):
        chat_id = str(call.message.chat.id)
        key = call.data.split(':')[1]

        with app_context_provider():
            subscriber = TelegramSubscriber.query.filter_by(telegram_chat_id=chat_id).first()

            if not subscriber or subscriber.status != 'APPROVED':
                bot.answer_callback_query(call.id, t('notifications.not_authorized', 'fr'))
                return

            # Update Preference
            # Need to copy dict, modify, and re-assign to trigger SQLAlchemy detection if needed
            new_prefs = dict(subscriber.preferences)
            current_val = new_prefs.get(key, False)
            new_prefs[key] = not current_val
            subscriber.preferences = new_prefs

            db.session.commit() # Save to DB

            # Refresh Keyboard
            markup = InlineKeyboardMarkup()
            options = [
                ('notify_entry', t('notifications.setting_entry', 'fr')),
                ('notify_exit', t('notifications.setting_exit', 'fr')),
                ('notify_alerts', t('notifications.setting_alerts', 'fr')),
                ('notify_billing', t('notifications.setting_billing', 'fr')),
                ('notify_daily_report', t('notifications.setting_daily', 'fr'))
            ]

            for k, label in options:
                is_active = new_prefs.get(k, False)
                status_icon = "✅" if is_active else "❌"
                markup.add(InlineKeyboardButton(f"{label} {status_icon}", callback_data=f"toggle:{k}"))

            bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)
            bot.answer_callback_query(call.id, t('notifications.updated_key', 'fr').format(key=key))

def start_polling(app_context_provider):
    """
    Start the bot polling loop (Blocking).
    """
    if not bot:
        logger.error("Bot token not found. Skipping polling.")
        return

    logger.info("Starting Telegram Bot Polling...")
    register_bot_handlers(app_context_provider)
    bot.infinity_polling()
