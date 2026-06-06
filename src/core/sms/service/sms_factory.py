from config import settings
from core.moolre.service.moolreservice import MoolreSMSService
from core.wirepick.service.wirepickservice import WirepickSMSService


def get_sms_service():
    """Return the configured SMS provider (Moolre or Wirepick)."""
    provider = (settings.SMS_PROVIDER or "moolre").lower()
    if provider == "wirepick":
        return WirepickSMSService()
    return MoolreSMSService()
