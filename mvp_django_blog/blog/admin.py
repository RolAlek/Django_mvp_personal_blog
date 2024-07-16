from django.contrib import admin

from .models import Category, Location, Post


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'text',
        'is_published',
        'pub_date',
        'created_at',
        'category',
        'location'
    )
    list_editable = (
        'is_published',
        'category',
        'location'
    )

    search_fields = ('title',)
    list_filter = ('category', 'location')
    list_display_links = ('title',)
    empty_value_display = 'Не задано'


class PostInline(admin.TabularInline):
    model = Post
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    inlines = (PostInline, )
    list_display = ('title', )


class LocationAdmin(admin.ModelAdmin):
    inlines = (PostInline, )
    list_display = ('name', )


admin.site.register(Category, CategoryAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Post, PostAdmin)
