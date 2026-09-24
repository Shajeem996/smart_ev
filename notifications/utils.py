from .models import Notification

def send_notification(user, title, message, notification_type='SYSTEM', link=''):
    """
    Creates an in-app notification record for the specified user.
    """
    if not user:
        return None
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link
    )
