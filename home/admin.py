from django.contrib import admin
from ckeditor.widgets import CKEditorWidget
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import *
from django.http import HttpResponse
import xlwt

# Register your models here.


class RegistrationExportResource(resources.ModelResource):
    event_title = fields.Field(attribute='event__title', column_name='Event Title')
    student_name = fields.Field(attribute='student__name', column_name='Student Name')
    student_college = fields.Field(attribute='student__college', column_name='Student College')
    student_email = fields.Field(attribute='student__email__email', column_name='Student Email')
    student_phone = fields.Field(attribute='student__ph_no', column_name='Contact')
    student_dept = fields.Field(attribute='student__dept', column_name='Department')
    student_year = fields.Field(attribute='student__year', column_name='Year')
    # Include more fields as needed

    class Meta:
        model = Registration
        fields = ('event_title', 'student_name', 'student_college', 'student_dept', 'student_year', 'student_phone', 'is_paid', 'registered_at', 'is_reported')


def export_selected_to_excel(modeladmin, request, queryset):
    resource = RegistrationExportResource()
    dataset = resource.export(queryset)

    response = HttpResponse(dataset.xls, content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Event_Registration.xls"'
    return response

export_selected_to_excel.short_description = "Export selected data to Excel"




class CustomUserAdmin(admin.ModelAdmin):
    list_filter = ['email']
    list_display = ['email']
    search_fields = ['email']

    class Meta:
        model = CustomUser

admin.site.register(CustomUser, CustomUserAdmin)



class StudentsAdmin(admin.ModelAdmin):
    list_filter = ['name', 'college']
    list_display = ['name', 'college', 'dept', 'ph_no']
    search_fields = ['name', 'college', 'dept', 'ph_no']

    class Meta:
        model = Students

admin.site.register(Students, StudentsAdmin)



class EventsAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget},
    }
    list_filter = ['title', 'category']
    list_display = ['title', 'category', 'date', 'event_time', 'cordinator']
    search_fields = ['title', 'category', 'date', 'event_time', 'cordinator']

    class Meta:
        model = Events

admin.site.register(Events, EventsAdmin)



class FacultyInchargeAdmin(admin.ModelAdmin):
    list_filter = ['fac_name']
    list_display = ['fac_name', 'event_incharge']
    search_fields = ['fac_name', 'event_incharge']

    class Meta:
        model = FacultyIncharge

admin.site.register(FacultyIncharge, FacultyInchargeAdmin)



class RegistrationAdmin(admin.ModelAdmin):
    list_filter = ['event', 'student', 'is_paid']
    list_display = ['event', 'student', 'registered_at', 'is_paid', 'is_reported']
    search_fields = ['event__title', 'student__name']

    actions = [export_selected_to_excel]  # Add the custom action

    class Meta:
        model = Registration

admin.site.register(Registration, RegistrationAdmin)



class TeamsAdmin(admin.ModelAdmin):
    list_filter = ['team_lead', 'team_member', 'event']
    list_display = ['team_lead', 'event']
    search_fields = ['team_lead__name', 'team_member__name', 'event__title']

    class Meta:
        model = Teams

admin.site.register(Teams, TeamsAdmin)



class PaymentAdmin(admin.ModelAdmin):
    list_filter = ['student', 'event', 'status', 'order_id', 'datetime']
    list_display = ['student', 'event', 'status', 'order_id', 'datetime']
    search_fields = ['student', 'event', 'status', 'datetime']

    class Meta:
        model = Payment

admin.site.register(Payment, PaymentAdmin)