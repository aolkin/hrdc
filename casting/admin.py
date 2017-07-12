from django.contrib import admin

from .models import *

@admin.register(Signing)
class SigningAdmin(admin.ModelAdmin):
    list_display = ('show', 'character', 'actor', 'response')
    list_editable = ('response',)
    list_display_links = None
    search_fields = ('actor', 'show', 'character')
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        del actions['delete_selected']
        return actions
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_add_permission(self, request, obj=None):
        return False

PUBLISHING_HELP = """
The callback and cast lists will become visible on the site after the inputted
dates and times. Additionally, actors will be emailed when these times pass.
""".strip().replace("\n", " ")
SIGNING_HELP = """
Actors will be able to sign after the first time and date. At the second
time and date, second-round-cast actors will be emailed again, and given
the option to sign regardless of first-round actors.
""".strip().replace("\n", " ")
    
@admin.register(CastingReleaseMeta)
class CastingReleaseAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": ("associated_with",)
        }),
        ("List Publishing", {
            "fields": ("publish_callbacks", "publish_casts"),
            "description": PUBLISHING_HELP
        }),
        ("Signing Options", {
            "fields": ("signing_opens", "second_signing_opens"),
            "description": SIGNING_HELP
        })
    )
    readonly_fields = ("associated_with",)
    list_display = ('__str__', 'publish_callbacks', 'publish_casts',
                    'signing_opens', 'second_signing_opens')

    def get_actions(self, request):
        return { "delete_unnassociated": (
            CastingReleaseAdmin.delete_unnassociated,
            "delete_unnassociated", "Delete unnassociated settings") }
    
    def delete_unnassociated(self, request, queryset):
        qs = queryset.filter(castingmeta__isnull=True)
        n = qs.count()
        qs.delete()
        self.message_user(request, "%s settings object(s) deleted." % n)

    def associated_with(self, obj):
        return str(obj)
    
    def has_delete_permission(self, request, obj=None):
        if obj:
            return not obj.association
        else:
            return super().has_delete_permission(request)

class SlotAdmin(admin.StackedInline):
    model = Slot
    fields = (('space', 'day'), ('start', 'end'))
    ordering = ('day', 'start')

    class Media:
        css = {
            'all': ('casting/django_admin.css',)
        }

    def get_queryset(self, request):
        return super().get_queryset(request).filter(type=self.type)
    
    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            n = obj.slot_set.filter(type=self.type).count()
            return max(self.extra - n, 0)
        else:
            return self.extra
    
class AuditionSlotAdmin(SlotAdmin):
    type = Slot.TYPES[0][0]
    extra = 3
    verbose_name = "Audition Slot"

class CallbackSlotAdmin(SlotAdmin):
    type = Slot.TYPES[1][0]
    extra = 1
    verbose_name = "Callback Slot"

@admin.register(CastingMeta)
class MetaAdmin(admin.ModelAdmin):
    list_display = ('show', 'season', 'release_meta', 'contact_email')
    list_editable = ("release_meta",)
    exclude = ('callback_description', 'cast_list_description',
               'contact_email')
    search_fields = ('show__title',)
    list_filter = ('show__season', 'show__year', 'release_meta', 'slot__day')

    inlines = [
        AuditionSlotAdmin,
        CallbackSlotAdmin,
    ]
    
    def season(self, obj):
        return obj.show.seasonstr()
