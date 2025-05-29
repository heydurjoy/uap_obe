from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Faculty
from programs.models import AllowedEmail

class UserRegistrationForm(UserCreationForm):
    # User fields
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )
    
    # Faculty profile fields
    name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )
    short_name = forms.CharField(
        max_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your short name (max 4 characters)'
        })
    )
    designation = forms.ChoiceField(
        choices=Faculty.DESIGNATION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    phone_number = forms.CharField(
        max_length=11,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number (optional)'
        })
    )
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Simplify password validation messages
        self.fields['password1'].help_text = 'Password must be at least 6 characters long.'
        self.fields['password2'].help_text = 'Enter the same password as before.'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            allowed_email = AllowedEmail.objects.get(email=email)
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("This email is already registered.")
            return email
        except AllowedEmail.DoesNotExist:
            raise forms.ValidationError("This email is not authorized to register.")
    
    def clean_short_name(self):
        short_name = self.cleaned_data.get('short_name')
        if len(short_name) > 4:
            raise forms.ValidationError("Short name must be at most 4 characters long.")
        return short_name.upper()
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create faculty profile
            allowed_email = AllowedEmail.objects.get(email=self.cleaned_data['email'])
            Faculty.objects.create(
                user=user,
                allowed_email=allowed_email,
                name=self.cleaned_data['name'],
                short_name=self.cleaned_data['short_name'],
                department=allowed_email.department,
                designation=self.cleaned_data['designation'],
                phone_number=self.cleaned_data.get('phone_number', '')
            )
        return user

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