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
from datetime import datetime
from threading import Thread

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from models import db, TelegramSubscriber
from services.notification_service import NotificationService

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
            f"🛬 *Entrée Espace Aérien*\n"
            f"Vol: `{callsign}`\n"
            f"Trajet: {origin} ➡️ {dest}\n"
            f"Type: {flight.flight_type.upper() if flight.flight_type else 'N/A'}"
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
            f"🛫 *Sortie de Zone*\n"
            f"Vol: `{callsign}`\n"
            f"Dist: {dist} | Durée: {dur}\n"
            f"Exit Alt: {alt}"
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
            f"💰 *Facture Générée*\n"
            f"Ref: `{invoice.invoice_number}`\n"
            f"Client: {airline}\n"
            f"Montant: *{amount}*\n"
            f"Type: {invoice.invoice_type}"
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

        msg = (
            f"{icon} *ALERTE: {title}*\n"
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
                subscriber = TelegramSubscriber(
                    telegram_chat_id=chat_id,
                    username=username,
                    first_name=first_name,
                    status='PENDING'
                )
                db.session.add(subscriber)
                db.session.commit()

                bot.reply_to(message, "🔒 Demande d'accès envoyée à l'administrateur. Veuillez patienter.")

                # Notify Internal Admins
                NotificationService.notify_admins(
                    type='security',
                    title="Nouvelle demande Telegram",
                    message=f"Utilisateur {username} ({first_name}) demande l'accès au Bot.",
                    link="/admin/users" # Assuming an admin page exists or will exist
                )

            elif subscriber.status == 'PENDING':
                bot.reply_to(message, "⏳ Votre demande est toujours en attente de validation.")

            elif subscriber.status == 'APPROVED':
                bot.reply_to(message, f"✅ Bienvenue, {first_name}!\n\nUtilisez /settings pour configurer vos notifications.")

            elif subscriber.status in ['REJECTED', 'REVOKED']:
                bot.reply_to(message, "⛔ Accès refusé.")

    @bot.message_handler(commands=['settings'])
    def handle_settings(message):
        chat_id = str(message.chat.id)

        with app_context_provider():
            subscriber = TelegramSubscriber.query.filter_by(telegram_chat_id=chat_id).first()

            if not subscriber or subscriber.status != 'APPROVED':
                bot.reply_to(message, "⛔ Non autorisé.")
                return

            # Build Inline Keyboard
            markup = InlineKeyboardMarkup()
            prefs = subscriber.preferences or {}

            # Map keys to labels
            options = [
                ('notify_entry', '🛬 Entrées Zone'),
                ('notify_exit', '🛫 Sorties Zone'),
                ('notify_alerts', '🚨 Alertes/Urgences'),
                ('notify_billing', '💰 Facturation'),
                ('notify_daily_report', '📊 Rapport 24h')
            ]

            for key, label in options:
                is_active = prefs.get(key, False)
                status_icon = "✅" if is_active else "❌"
                # Callback data: toggle:key
                markup.add(InlineKeyboardButton(f"{label} {status_icon}", callback_data=f"toggle:{key}"))

            bot.send_message(chat_id, "⚙️ *Paramètres de Notification*\nCliquez pour activer/désactiver :", reply_markup=markup, parse_mode='Markdown')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('toggle:'))
    def callback_query(call):
        chat_id = str(call.message.chat.id)
        key = call.data.split(':')[1]

        with app_context_provider():
            subscriber = TelegramSubscriber.query.filter_by(telegram_chat_id=chat_id).first()

            if not subscriber or subscriber.status != 'APPROVED':
                bot.answer_callback_query(call.id, "Non autorisé")
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
                ('notify_entry', '🛬 Entrées Zone'),
                ('notify_exit', '🛫 Sorties Zone'),
                ('notify_alerts', '🚨 Alertes/Urgences'),
                ('notify_billing', '💰 Facturation'),
                ('notify_daily_report', '📊 Rapport 24h')
            ]

            for k, label in options:
                is_active = new_prefs.get(k, False)
                status_icon = "✅" if is_active else "❌"
                markup.add(InlineKeyboardButton(f"{label} {status_icon}", callback_data=f"toggle:{k}"))

            bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)
            bot.answer_callback_query(call.id, f"Mis à jour : {key}")

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
