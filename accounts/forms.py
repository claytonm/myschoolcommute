from django.contrib.auth.models import User, Group
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.gis import admin
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import AuthenticationForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Fieldset, ButtonHolder, Submit

from models import Profile
from survey.models import District, School

class InitModelForm(forms.ModelForm):
    """
    Subclass of `forms.ModelForm` that makes sure the initial values
    are present in the form data, so you don't have to send all old values
    for the form to actually validate.
    """
    def merge_from_initial(self):
        filt = lambda v: v not in self.data.keys()
        for field in filter(filt, getattr(self.Meta, 'fields', ())):
            self.data[field] = self.initial.get(field, None)

# I put this on all required fields, because it's easier to pick up
# on them with CSS or JavaScript if they have a class of "required"
# in the HTML. Your mileage may vary. If/when Django ticket #3515
# lands in trunk, this will no longer be necessary.
attrs_dict = {'class': 'required', 'style': 'font-weight: bold;'}


class LoginForm(AuthenticationForm, forms.Form):
    class Meta:
        layout = (
            Fieldset("Please Login", "username", "password", ),
        )

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.add_input(Submit('submit', 'Log in'))


class RegistrationForm(forms.Form):
    """
    Form for registering a new user account.

    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.

    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.

    """
    username = forms.RegexField(regex=r'^\w+$',
                                max_length=30,
                                widget=forms.TextInput(attrs=attrs_dict),
                                label=_("Username"),
                                error_messages={ 'invalid': _("This value must contain only letters, numbers and underscores.") })

    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Password (again)"))

    first_name = forms.CharField(max_length=30, label=_("First name"), required=True)
    last_name = forms.CharField(max_length=30, label=_("Last name"), required=True)

    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_("Email address"))

    group = forms.ModelChoiceField(
        queryset=Group.objects.all(), help_text="Which admin group are you in?"
        #Hide group selection, comment out below to re-enable
        , initial= Group.objects.get(name="District Officials")
        , widget= forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.form_tag = False
        #self.helper.add_input(Submit('submit', 'Create the account'))

    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.

        """
        try:
            user = User.objects.get(username__iexact=self.cleaned_data['username'])
        except User.DoesNotExist:
            return self.cleaned_data['username']
        raise forms.ValidationError(_("A user with that username already exists."))

    def clean_email(self):
        """
        Validate that the supplied email address is unique for the
        site.
        """

        if User.objects.filter(email__iexact=self.cleaned_data['email']).count():
            raise forms.ValidationError(_(u'This email address is already in use. Please supply a different email address.'))
        return self.cleaned_data['email']

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.

        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields didn't match."))
        return self.cleaned_data

    def save(self, commit=True):
        u = User.objects.create_user(username=self.cleaned_data['username'],
                                     email=self.cleaned_data['email'],
                                     password=self.cleaned_data['password1'])
        u.first_name = self.cleaned_data['first_name']
        u.last_name = self.cleaned_data['last_name']
        u.is_active = False

        group = self.cleaned_data['group']

        if commit:
            u.save()
            u.groups.add(group)
        else:
            old_save_m2m = u.save_m2m
            def save_m2m():
                old_save_m2m()
                u.groups.add(group)
            u.save_m2m = save_m2m
        return u


class UserForm(InitModelForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        editor = kwargs.pop('editor', None)
        super(UserForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.form_tag = False

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', )


class ProfileForm(InitModelForm):
    school = forms.ModelChoiceField(
        required=False,
        queryset=School.objects.all().defer('shed_05', 'shed_10', 'shed_15', 'shed_20')
    )
    def __init__(self, *args, **kwargs):
        editor = kwargs.pop('editor', None)
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.form_tag = False
        if editor:
            if not editor.is_superuser or editor.groups.filter(name="MassRIDES Staff").count() == 0:
                self.fields['district'].widget.attrs['readonly'] = 'readonly'

    class Meta:
        model = Profile
        exclude = ('user',)
