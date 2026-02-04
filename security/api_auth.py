"""
/* * Nom de l'application : ATM-RDC
 * Description : Source file: api_auth.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */
"""
from functools import wraps
from flask import request, jsonify, g, current_app
from models import ApiKey, db, AuditLog
from datetime import datetime
import redis
import time

# Initialize Redis connection (lazy)
redis_client = None

def get_redis_client():
    global redis_client
    if redis_client is None:
        redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        redis_client = redis.from_url(redis_url)
    return redis_client

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key_header = request.headers.get('X-API-KEY')

        if not api_key_header:
            return jsonify({'error': 'Missing API Key'}), 401

        # Check API Key in DB
        api_key = ApiKey.query.filter_by(key=api_key_header).first()

        if not api_key or api_key.status != 'active':
            return jsonify({'error': 'Invalid or inactive API Key'}), 403

        # Rate Limiting
        requests_count = 0
        try:
            r = get_redis_client()
            # Key format: rate_limit:{api_key_id}:{minute_timestamp}
            current_minute = int(time.time() / 60)
            redis_key = f"rate_limit:{api_key.id}:{current_minute}"

            # Increment and set expiry (60 seconds + buffer)
            requests_count = r.incr(redis_key)
            if requests_count == 1:
                r.expire(redis_key, 90)

            if requests_count > api_key.rate_limit:
                # Log rejection in AuditLog as well? Maybe not to spam DB, but good for visibility.
                # Let's skip heavy DB logging for rate limit hits to avoid DoS amplification.
                return jsonify({
                    'error': 'Too Many Requests',
                    'message': f'Rate limit of {api_key.rate_limit} requests/minute exceeded'
                }), 429

        except Exception as e:
            current_app.logger.error(f"Redis Rate Limit Error: {str(e)}")
            # Fail open (allow request) if Redis is down
            pass

        # Log Access (Audit)
        try:
            # We commit audit log immediately
            audit = AuditLog(
                user_id=None, # System action or link to api_key.created_by? kept null for external
                action='api_access',
                action_type='read',
                entity_type='api_key',
                entity_id=api_key.id,
                entity_name=api_key.name,
                ip_address=request.remote_addr,
                request_method=request.method,
                request_path=request.path,
                user_agent=request.user_agent.string[:500] if request.user_agent else None,
                status_code=200,
                created_at=datetime.utcnow(),
                changes=f"API Key Used: {api_key.key[:4]}..."
            )
            db.session.add(audit)

            # Update last used
            api_key.last_used_at = datetime.utcnow()

            db.session.commit()

        except Exception as e:
            current_app.logger.error(f"Audit Log Error: {str(e)}")
            db.session.rollback()

        # Store api_key in g for the route to use if needed
        g.api_key = api_key

        # Execute the function and ensure it's a response object
        response = current_app.make_response(f(*args, **kwargs))

        # Inject Rate Limit Headers
        # requests_count is initialized to 0, so if redis fails it stays 0 (unlimited appearance)
        # or we could omit headers if redis failed.
        # But if it succeeded, requests_count is set.
        if requests_count > 0:
            remaining = max(0, api_key.rate_limit - requests_count)
            response.headers['X-RateLimit-Limit'] = str(api_key.rate_limit)
            response.headers['X-RateLimit-Remaining'] = str(remaining)

        return response

    return decorated_function
