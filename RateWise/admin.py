from django.contrib import admin
from .models import Document, Rating


class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)


class RatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'score')
    search_fields = ('user__username',)


admin.site.register(Document, DocumentAdmin)
admin.site.register(Rating, RatingAdmin)
