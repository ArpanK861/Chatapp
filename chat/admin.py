from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'room', 'message_content', 'delivered', 'timestamp')
    list_filter = ('room', 'delivered', 'timestamp', 'sender')
    search_fields = ('text', 'sender__username', 'room')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    @admin.display(description="Message Content")
    def message_content(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text