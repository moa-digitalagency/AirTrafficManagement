"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: system_gate.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
import os
import redis
import logging
from models import db, SystemConfig, AuditLog

logger = logging.getLogger(__name__)

class SystemGate:
    """
    Centralized gatekeeper for System Global Switch.
    Uses Redis for caching to prevent DB overload.
    """

    _redis_client = None
    REDIS_KEY = 'system:active'

    @classmethod
    def get_redis(cls):
        if cls._redis_client is None:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            try:
                cls._redis_client = redis.from_url(redis_url)
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                return None
        return cls._redis_client

    @classmethod
    def is_active(cls):
        """
        Check if the system is active.
        1. Check Redis.
        2. If missing, check DB.
        3. Cache in Redis.
        """
        r = cls.get_redis()

        # 1. Check Redis
        if r:
            try:
                val = r.get(cls.REDIS_KEY)
                if val is not None:
                    # Redis stores bytes
                    return val.decode('utf-8') == '1'
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")

        # 2. Check DB
        try:
            # Need app context if running outside requests (should be handled by caller usually, but let's be safe)
            # If we are in celery, we might need to be careful.
            # Assuming db.session works (scoped session).

            # Note: DB queries might fail if not in app context.
            # Caller responsability usually.

            config = SystemConfig.query.filter_by(key='system_active').first()

            # Default to False (Safety) if not found, as per requirement
            is_active = False
            if config:
                val = config.get_typed_value()
                if val is not None:
                    is_active = val

            # 3. Cache in Redis
            if r:
                try:
                    r.set(cls.REDIS_KEY, '1' if is_active else '0')
                except Exception as e:
                    logger.warning(f"Redis set failed: {e}")

            return is_active

        except Exception as e:
            logger.error(f"DB Check failed for SystemGate: {e}")
            # Fail closed (False) for safety
            return False

    @classmethod
    def set_active(cls, active: bool, user_id: int = None, ip_address: str = None):
        """
        Toggle system status.
        Updates DB and Redis.
        """
        try:
            # Update DB
            config = SystemConfig.query.filter_by(key='system_active').first()
            if not config:
                config = SystemConfig(key='system_active', value_type='bool', category='system', description='État global du système')
                db.session.add(config)

            old_value = config.get_typed_value()
            config.value = str(active).lower()
            config.updated_by = user_id

            # Audit Log
            if user_id:
                log = AuditLog(
                    user_id=user_id,
                    action='toggle_system_master_switch',
                    entity_type='SystemConfig',
                    entity_id=config.id if config.id else 0,
                    changes=f"Changed system_active from {old_value} to {active}",
                    ip_address=ip_address,
                    severity='critical'
                )
                db.session.add(log)

            db.session.commit()

            # Update Redis
            r = cls.get_redis()
            if r:
                try:
                    r.set(cls.REDIS_KEY, '1' if active else '0')
                except Exception as e:
                    logger.warning(f"Redis set failed after DB update: {e}")

            return True, "Status updated"
        except Exception as e:
            logger.error(f"Failed to set system status: {e}")
            db.session.rollback()
            return False, str(e)
