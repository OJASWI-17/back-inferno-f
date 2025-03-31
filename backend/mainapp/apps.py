from django.apps import AppConfig
import redis
from django.db.models.signals import post_migrate
import logging
from django.conf import settings
from django.db import connection
import time

logger = logging.getLogger(__name__)

def safe_redis_flush():
    """Safe Redis flushing with timeout and retries"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            redis_client = redis.from_url(
                settings.REDIS_URL,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            redis_client.ping()  # Test connection
            redis_client.flushdb()
            logger.info("Redis cleared successfully")
            return True
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed (attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                logger.error("Max Redis connection attempts reached")
                return False
            time.sleep(2)
        except Exception as e:
            logger.error(f"Redis flush error: {e}")
            return False

def initialize_system(sender, **kwargs):
    """Initialize system after migrations complete."""
    if not safe_redis_flush():
        logger.error("Skipping DB initialization due to Redis failure")
        return

    try:
        # Initialize Database
        from .models import UserStock, LimitOrder, UserProfile, Transaction
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM mainapp_userprofile LIMIT 1")
        
        UserStock.objects.all().delete()
        logger.info("UserStock table cleared")
        LimitOrder.objects.all().delete()
        logger.info("LimitOrder table cleared")
        Transaction.objects.all().delete()
        logger.info("Transaction table cleared")
        UserProfile.objects.all().update(balance=10000.00)
        logger.info("UserProfile balances reset")
        
    except Exception as e:
        logger.error(f"DB initialization error: {e}")

class MainappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mainapp'
    _initialized = False

    def ready(self):
        """Safe initialization with multiple guards"""
        if self._initialized:
            return
            
        try:
            # Check if tables exist without triggering ORM
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'mainapp_userprofile'
                    )
                """)
                exists = cursor.fetchone()[0]
                
            if exists:
                post_migrate.connect(initialize_system, sender=self, weak=False)
                self._initialized = True
                
        except Exception as e:
            logger.error(f"Ready check failed: {e} (will retry)")