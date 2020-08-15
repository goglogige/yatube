from typing import Tuple

from django.contrib import admin

from posts.models import Post, Group, Comment


class PostAdmin(admin.ModelAdmin):
    list_display: Tuple[int, str, str, str] = (
        "pk",
        "text",
        "pub_date",
        "author",
        "image",
    )
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"


class GroupAdmin(admin.ModelAdmin):
    list_display: Tuple[int, str, str, str] = (
        "pk",
        "title",
        "slug",
        "description"
    )
    list_filter = ("slug",)
    empty_value_display = "-пусто-"


class CommentAdmin(admin.ModelAdmin):
    list_display: Tuple[int, str, str, str] = (
        "pk",
        "text",
        "created",
        "author",
        "post",
    )
    search_fields = ("text",)
    list_filter = ("created",)
    empty_value_display = "-пусто-"


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)

