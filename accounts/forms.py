from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Faculty
from programs.models import AllowedEmail

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Simplify password validation messages
        self.fields['password1'].help_text = 'Password must be at least 6 characters long.'
        self.fields['password2'].help_text = 'Enter the same password as before.'
        
        # Add Bootstrap classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not AllowedEmail.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is not authorized to register.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

class FacultyProfileForm(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ('name', 'short_name', 'department', 'designation', 'phone_number')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class UserLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'})) 