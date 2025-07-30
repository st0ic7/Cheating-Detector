from django.contrib import admin
from .models import Alert

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('message', 'timestamp')
    list_filter = ('timestamp',)
    ordering = ('-timestamp',)
