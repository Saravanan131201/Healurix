from django import template
from django.utils.timezone import now
import datetime

register = template.Library()

@register.filter
def is_active_now(last_seen):
    if not last_seen:
        return False
    return abs((now() - last_seen).total_seconds()) < 10 
    

@register.filter
def format_last_seen(last_seen_time):
    if not last_seen_time:
        return "Unavailable"

    current_time = now()
    delta = current_time - last_seen_time

    if delta.total_seconds() < 60:
        return "just now"
    elif delta.total_seconds() < 3600:
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif delta.total_seconds() < 86400 and last_seen_time.date() == current_time.date():
        hours = int(delta.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif (current_time.date() - last_seen_time.date()).days == 1:
        return f"Yesterday at {last_seen_time.strftime('%I:%M %p')}"
    else:
        return last_seen_time.strftime('%d %b %Y at %I:%M %p')  
    
