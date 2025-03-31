from django.apps import AppConfig
import redis
from django.db.models.signals import post_migrate
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def initialize_system(sender, **kwargs):
    """Initialize system after migrations complete."""
    try:
        # Initialize Redis
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.flushdb()
        logger.info("Redis database cleared on startup!")

        # Initialize Database
        from .models import UserStock, LimitOrder, UserProfile, Transaction
        UserStock.objects.all().delete()
        print("UserStock table cleared")
        LimitOrder.objects.all().delete()
        print("LimitOrder table cleared")
        Transaction.objects.all().delete()
        print("Transaction table cleared")
        UserProfile.objects.all().update(balance=10000.00)
        print("UserProfile table cleared")
        
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Initialization error: {e}")

class MainappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mainapp'

    def ready(self):
        """Connect initialization signal without immediate DB access."""
        from django.db.utils import OperationalError
        try:
            post_migrate.connect(initialize_system, sender=self)
        except OperationalError:
            logger.info("Database not ready yet - skipping initial connection")