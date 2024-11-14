from django.contrib import admin
from .models import Thread, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0


class ThreadAdmin(admin.ModelAdmin):
    inlines = [MessageInline]
    list_display = ["id", "title", "created", "modified"]
    search_fields = ["title"]

    class Meta:
        model = Thread


class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "thread", "role", "text", "created", "modified"]
    search_fields = ["text"]

    class Meta:
        model = Message


admin.site.register(Thread, ThreadAdmin)
admin.site.register(Message, MessageAdmin)

