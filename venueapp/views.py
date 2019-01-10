from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy

from django import forms
    
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from utils import user_is_initialized

class InitializedLoginMixin:
    @method_decorator(login_required)
    @method_decorator(user_is_initialized)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class IndexView(InitializedLoginMixin, TemplateView):
    verbose_name = "Venue Applications"
    help_text = "apply for space"
    
    template_name = "venueapp/index.html"

### Below has been copy pasted from the Django documentation as an example
## Then edited slightly to actually work
    
class ContactForm(forms.Form):
    name = forms.CharField()
    message = forms.CharField(widget=forms.Textarea)

    def send_email(self):
        # send email using the self.cleaned_data dictionary
        pass

class ContactView(InitializedLoginMixin, FormView):
    template_name = 'venueapp/form.html'
    form_class = ContactForm
    success_url = reverse_lazy("venueapp:public_index")

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.send_email()
        return super().form_valid(form)
