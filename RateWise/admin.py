from django.contrib import admin
from .models import Document


class Admin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)


admin.site.register(Document, Admin)
