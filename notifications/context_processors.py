from .models import Notification

def notification_badge(request):
    """
    Context processor providing unread notifications count and recent notifications list to all templates.
    """
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        recent_notifications = Notification.objects.filter(user=request.user)[:5]
        return {
            'unread_notifications_count': unread_count,
            'recent_navbar_notifications': recent_notifications
        }
    return {
        'unread_notifications_count': 0,
        'recent_navbar_notifications': []
    }
