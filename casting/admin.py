from django.contrib import admin
from django import forms
from django.utils import timezone
from django.utils.html import format_html
from django.contrib import messages
from django.conf import settings
from datetime import timedelta

from collections import defaultdict

from emailtracker.tools import render_for_user

from .models import *

def send_confirmation(modeladmin, request, qs):
    actors = defaultdict(list)
    for i in qs.filter(response__isnull=False):
        actors[i.actor].append(i)
    emails = 0
    for actor, signed in actors.items():
        if not actor.login_token:
            actor.new_token()
        render_for_user(actor, "casting/email/signed.html",
                        "signed", context={ "signed": signed },
                        subject="Signing Confirmation",
                        tags=["casting", "signing_confirmation", "admin"])
        emails += 1
    messages.success(request, "Sent {} email{}.".format(
        emails, "s" if emails != 1 else ""))
send_confirmation.short_description = ("Send confirmation emails for "
                                       "selected signatures")

def clear_response(modeladmin, request, qs):
    qs.update(response=None, tech_req=None)
    messages.success(request, "Cleared {} signatures.".format(qs.count()))
clear_response.short_description = "Clear selected responses and tech reqs"

@admin.register(Signing)
class SigningAdmin(admin.ModelAdmin):
    list_display = ('show', 'character', 'order_title', 'actor', 'response',
                    'tech_req', 'signed_time')
    list_display_links = ('response',)
    list_filter = ('character__show__show__year',
                   'character__show__show__season',
                   'response', 'timed_out')
    search_fields = ('actor__first_name', 'actor__last_name',
                     'character__name')
    actions = [send_confirmation] + ([clear_response] if settings.DEBUG else [])

    fieldsets = (
        ("Role", {
            "fields": ("show", "character", "order_title")
        }),
        ("Signature", {
            "fields": ("actor", "response", 'tech_req', 'signed_time'),
        }),
    )
    readonly_fields = ("show", "character", "order_title", "actor",
                       "signed_time")

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


CASTING_RELEASE_TIME_LOCKS = ("publish_callbacks", "publish_first_round_casts",
                              "publish_casts")
CASTING_RELEASE_LOCK_TIME = timedelta(minutes=10)
def is_locked(dt):
    return dt and (dt - CASTING_RELEASE_LOCK_TIME < timezone.now())

class CastingReleaseForm(forms.ModelForm):
    def clean_publish_callbacks(self):
        if (is_locked(self.instance.publish_callbacks) or
            self.instance.stage > 0):
            raise forms.ValidationError(
                "Cannot change callback publishing time, it is too soon or "
                "has already passed.")
        return self.cleaned_data["publish_callbacks"]

    def clean_publish_first_round_casts(self):
        if (is_locked(self.instance.publish_first_round_casts) or
            self.instance.stage > 1):
            raise forms.ValidationError(
                "Cannot change first-round cast list publishing time, it is "
                "too soon or has already passed.")
        return self.cleaned_data["publish_first_round_casts"]

    def clean_publish_casts(self):
        if (is_locked(self.instance.publish_casts) or
            self.instance.stage > 2):
            raise forms.ValidationError(
                "Cannot change cast list publishing time, it is "
                "too soon or has already passed.")
        return self.cleaned_data["publish_casts"]

    def clean_signing_option_field(self):
        if is_locked(self.instance.publish_casts) or self.instance.stage > 2:
            raise forms.ValidationError("Cannot change signing options after "
                                        "casts have been published.")

    def clean_signing_opens(self):
        self.clean_signing_option_field()
        return self.cleaned_data["signing_opens"]

    def clean_second_signing_opens(self):
        self.clean_signing_option_field()
        return self.cleaned_data["second_signing_opens"]

    def clean_second_signing_warning(self):
        self.clean_signing_option_field()
        return self.cleaned_data["second_signing_warning"]

PUBLISHING_HELP = """
The callback and cast lists will become visible on the site after the inputted
dates and times. Additionally, actors will be emailed when these times pass.
<p class="text-white bg-danger rounded p-1 mt-1">
    DANGER: These times cannot be changed after they have passed,
    or less than ten minutes before they occur. Setting them incorrectly can
    accidentally send many emails.
<span class="text-warning">
    Please wait to set them if you are unsure, and double-check when editing
    this section.
</span>
</p>
""".strip().replace("\n", " ")
SIGNING_HELP = """
Actors will be able to sign after the first time and date. At the second
time and date, second-round-cast actors will be emailed again, and given
the option to sign regardless of first-round actors.
<p class="text-white bg-warning rounded p-1 mt-1">
    WARNING: Once casts have been published, these cannot be changed. As such,
    these times are locked along with the cast list publishing setting.
</p>
""".strip().replace("\n", " ")

@admin.register(CastingReleaseMeta)
class CastingReleaseAdmin(admin.ModelAdmin):
    form = CastingReleaseForm
    fieldsets = (
        ("", {
            "fields": (("season", "year",),),
        }),
        ("Casting Release Status", {
            "fields": ("associated_with", "stage", "prevent_advancement",
                       "disable_signing")
        }),
        ("List Publishing", {
            "fields": ("publish_callbacks", "publish_first_round_casts",
                       "publish_casts"),
            "description": PUBLISHING_HELP
        }),
        ("Signing Options", {
            "fields": ("signing_opens", "second_signing_opens",
                       "second_signing_warning"),
            "description": SIGNING_HELP
        })
    )
    readonly_fields = ("associated_with",)
    list_display = ('__str__', 'stage', 'publish_callbacks',
                    'publish_first_round_casts', 'publish_casts',
                    'signing_opens', 'second_signing_opens',
                    'second_signing_warning')

    def get_readonly_fields(self, request, obj):
        readonly = list(self.readonly_fields)
        if not request.user.has_perm("casting.update_castingreleasemeta_stage"):
            readonly.append("stage")
        if not obj:
            return readonly
        if obj.stage > 2 or (
                not obj.tracker.has_changed("publish_casts") and
                is_locked(obj.publish_casts)):
            for i in ("signing_opens", "second_signing_opens",
                      "second_signing_warning"):
                if not obj.tracker.has_changed(i):
                    readonly.append(i)
        for i, attr in enumerate(CASTING_RELEASE_TIME_LOCKS):
            if obj.stage > i:
                readonly.append(attr)
            elif (not obj.tracker.has_changed(attr)) and is_locked(
                    getattr(obj, attr)):
                readonly.append(attr)
        return readonly

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
        n = obj.castingmeta_set.count()
        if n > 0:
            show = obj.association
            if n > 1:
                season = ""
                for i in obj.castingmeta_set.prefetch_related("show").all():
                    if season and i.show.seasonstr() != season:
                        return "({} associated with multiple seasons)".format(
                            obj._meta.verbose_name)
                    else:
                        season = i.show.seasonstr()
                return season
            else:
                return show.title
        else:
            if obj.id:
                return "(Unassociated {})".format(obj._meta.verbose_name)
            else:
                return "(New {})".format(obj._meta.verbose_name)

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
    list_display = ('show', 'release_meta', 'casting_release_stage',
                    'callbacks_submitted', 'first_cast_submitted',
                    'cast_submitted')
    search_fields = ('show__title',)
    list_filter = ('show__season', 'show__year', 'callbacks_submitted',
                   'first_cast_submitted', 'cast_submitted')
    autocomplete_fields = ('show', 'tech_req_pool',)
    fieldsets = (
        ("", {
            "fields": ('show', 'release_meta',)
        }),
        ("Technical Requirement", {
            "fields": ('tech_req_pool', ('num_tech_reqers', 'exempt_year')),
            "description": "Set the shows this show will contribute tech reqers to."
        }),
        ("Information", {
            "fields": ('contact_email_link',)
        }),
        ("Submitted Lists", {
            "fields": (('callbacks_submitted', 'first_cast_submitted',
                        'cast_submitted'),),
            "description": """<p class="text-white bg-danger rounded p-1 mt-1">
            When this page is saved, the values of these checkboxes will
            overwrite any submissions PDSMs may have made.</p>"""
        })
    )
    readonly_fields = ('contact_email_link',)

    inlines = [
        AuditionSlotAdmin,
        #CallbackSlotAdmin,
    ]

    def get_readonly_fields(self, request, obj):
        fields = list(self.readonly_fields)
        if not request.user.has_perm("casting.modify_submission_status"):
            fields += ['callbacks_submitted', 'first_cast_submitted',
                       'cast_submitted']
        if obj:
            return ["show"] + fields
        else:
            return fields

    def contact_email_link(self, obj):
        return format_html('<a href="mailto:{0}">{0}</a>', obj.contact_email)
    contact_email_link.short_description = "Staff-set Show Contact Email"

    def auditioners(self, obj):
        return obj.audition_set.filter(sign_in_complete=True).count()

    def audition_avg_display(self, obj):
        return ("{} mins".format(obj.audition_avg) if obj.audition_avg
                is not None else None)
    audition_avg_display.short_description = "Avg Aud Len"

    def season(self, obj):
        return obj.show.seasonstr()

    def casting_release_stage(self, instance):
        return instance.release_meta.get_stage_display()

@admin.register(AuditionCastingMeta)
class AuditionMetaAdmin(MetaAdmin):
    list_display = ('show', 'release_meta',
                    'casting_release_stage',
                    'auditioners', 'audition_avg_display', 'active_slot')
    list_filter = ('show__season', 'show__year', 'slot__day',
                   'slot__space__building')

    def active_slot(self, obj):
        slot = Slot.objects.active_slot(obj)
        return slot.space if slot else None

@admin.register(TechReqCastingMeta)
class TechReqMetaAdmin(MetaAdmin):
    list_display = ('show', 'contributes_to', 'contributors',
                    'tech_reqer_numbers', 'tech_reqers')
    list_filter = ('show__season', 'show__year',
                   'show__space__building')

    def contributes_to(self, obj):
        return (", ".join([str(i) for i in obj.tech_req_pool.all()])
                if obj.tech_req_pool else None)

    def contributors(self, obj):
        return ((", ".join([str(i) for i in obj.tech_req_contributors]) or None)
                if obj.tech_req_contributors else None)

    def tech_reqer_numbers(self, obj):
        return "{} / {}".format(obj.tech_reqer_count, obj.num_tech_reqers)
    tech_reqer_numbers.short_description = "Has / Max"

    def tech_reqers(self, obj):
        return (", ".join([str(i.actor) for i in obj.tech_reqers])
                if obj.tech_reqers else None)


def mark_as_done(modeladmin, request, qs):
    qs = qs.filter(status=Audition.STATUSES[1][0])
    for audition in qs:
        audition.status = Audition.STATUSES[2][0]
        audition.done_time = timezone.now()
        audition.save()
    messages.success(request, "Marked {} auditions as done.".format(qs.count()))
mark_as_done.short_description = "Mark selected auditions as done"

@admin.register(Audition)
class AuditionAdmin(admin.ModelAdmin):
    autocomplete_fields = ('actor', 'show')
    list_filter = ('show__show__year', 'show__show__season')
    search_fields = ('actor__email', 'actor__first_name', 'actor__last_name',
                     'show__show__title')
    list_display = ('actor', 'show', 'sign_in_complete', 'status')
    readonly_fields = ('busy', 'done_time', 'called_time', 'status',
                       'audition_length', 'tech_interest',
                       'actorseasonmeta')
    actions = (mark_as_done,)

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request):
        return False

    list_filter = ('show__show__year', 'show__show__season',
                   'show__show__space__building',
                   'added_for_signing', 'hidden_for_signing')
    search_fields = ('name', 'show__show__title')
    list_display = ('name', 'show', 'allowed_signers',
                    'allow_multiple_signatures')
    list_editable = ('allow_multiple_signatures',)
    readonly_fields = ('name',)
    fields = ('name', 'callback_description', 'cast_description',
              'allowed_signers',)
