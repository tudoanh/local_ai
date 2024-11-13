from django.contrib import admin

from rag.models import Knowledge, UploadFile


class UploadFileAdmin(admin.ModelAdmin):
    list_display = ("id", "file", "created", "modified")


class KnowledgeAdmin(admin.ModelAdmin):
    list_display = ("id", "file", "content", "created", "modified")


admin.site.register(UploadFile, UploadFileAdmin)
admin.site.register(Knowledge, KnowledgeAdmin)
