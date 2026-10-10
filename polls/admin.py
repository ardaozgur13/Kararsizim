from django.contrib import admin
from .models import Poll, Option


class OptionInline(admin.TabularInline):
    model = Option
    extra = 2
    min_num = 2
    max_num = 5


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ("question", "author", "created_at")
    search_fields = ("question", "author__username")
    list_filter = ("created_at",)
    inlines = [OptionInline]


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ("text", "poll", "position")
