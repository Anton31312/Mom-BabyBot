"""
Формы для веб-приложения с поддержкой переводов.
"""

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .models import WeightRecord, BloodPressureRecord, FeedingSession


class WeightRecordForm(forms.ModelForm):
    """Форма для записи веса с переводами сообщений об ошибках."""
    
    class Meta:
        model = WeightRecord
        fields = ['weight', 'notes']
        labels = {
            'weight': _('Weight (kg)'),
            'notes': _('Notes'),
        }
        help_texts = {
            'weight': _('Enter your weight in kilograms'),
            'notes': _('Optional notes about the measurement'),
        }
        error_messages = {
            'weight': {
                'required': _('Weight is required.'),
                'invalid': _('Please enter a valid weight.'),
                'min_value': _('Weight must be greater than 0.'),
                'max_value': _('Weight cannot exceed 999.99 kg.'),
            },
        }
    
    def clean_weight(self):
        """Валидация веса с переводимыми сообщениями об ошибках."""
        weight = self.cleaned_data.get('weight')
        
        if weight is not None:
            # Проверка на положительное значение
            if weight <= 0:
                raise ValidationError(_('Weight must be a positive number.'))
            # Проверка максимального значения
            if weight > 999.99:
                raise ValidationError(_('Weight cannot exceed 999.99 kg.'))
        
        return weight


class BloodPressureRecordForm(forms.ModelForm):
    """Форма для записи артериального давления с переводами."""
    
    class Meta:
        model = BloodPressureRecord
        fields = ['systolic', 'diastolic', 'pulse', 'notes']
        labels = {
            'systolic': _('Systolic pressure'),
            'diastolic': _('Diastolic pressure'),
            'pulse': _('Pulse (bpm)'),
            'notes': _('Notes'),
        }
        help_texts = {
            'systolic': _('Upper blood pressure value'),
            'diastolic': _('Lower blood pressure value'),
            'pulse': _('Heart rate in beats per minute'),
            'notes': _('Optional notes about the measurement'),
        }
        error_messages = {
            'systolic': {
                'required': _('Systolic pressure is required.'),
                'invalid': _('Please enter a valid systolic pressure.'),
                'min_value': _('Systolic pressure must be at least 50.'),
                'max_value': _('Systolic pressure cannot exceed 300.'),
            },
            'diastolic': {
                'required': _('Diastolic pressure is required.'),
                'invalid': _('Please enter a valid diastolic pressure.'),
                'min_value': _('Diastolic pressure must be at least 30.'),
                'max_value': _('Diastolic pressure cannot exceed 200.'),
            },
            'pulse': {
                'invalid': _('Please enter a valid pulse rate.'),
                'min_value': _('Pulse must be at least 30 bpm.'),
                'max_value': _('Pulse cannot exceed 250 bpm.'),
            },
        }
    
    def clean(self):
        """Валидация формы с проверкой соотношения давлений."""
        cleaned_data = super().clean()
        systolic = cleaned_data.get('systolic')
        diastolic = cleaned_data.get('diastolic')
        
        if systolic and diastolic:
            if systolic <= diastolic:
                raise ValidationError(
                    _('Systolic pressure must be higher than diastolic pressure.')
                )
        
        return cleaned_data


class FeedingSessionForm(forms.ModelForm):
    """Форма для сессии кормления с переводами."""
    
    class Meta:
        model = FeedingSession
        fields = ['feeding_type', 'amount', 'notes']
        labels = {
            'feeding_type': _('Feeding type'),
            'amount': _('Amount (ml)'),
            'notes': _('Notes'),
        }
        help_texts = {
            'feeding_type': _('Select the type of feeding'),
            'amount': _('Amount in milliliters (for bottle feeding)'),
            'notes': _('Optional notes about the feeding session'),
        }
        error_messages = {
            'feeding_type': {
                'required': _('Please select a feeding type.'),
                'invalid_choice': _('Please select a valid feeding type.'),
            },
            'amount': {
                'invalid': _('Please enter a valid amount.'),
                'min_value': _('Amount must be greater than 0.'),
                'max_value': _('Amount cannot exceed 2000 ml.'),
            },
        }
    
    def clean_amount(self):
        """Валидация количества с переводимыми сообщениями."""
        amount = self.cleaned_data.get('amount')
        feeding_type = self.cleaned_data.get('feeding_type')
        
        if feeding_type == 'bottle' and not amount:
            raise ValidationError(
                _('Amount is required for bottle feeding.')
            )
        
        if amount is not None:
            if amount <= 0:
                raise ValidationError(_('Amount must be a positive number.'))
            if amount > 2000:
                raise ValidationError(_('Amount cannot exceed 2000 ml.'))
        
        return amount


class UserRegistrationForm(forms.ModelForm):
    """Форма регистрации пользователя с переводами."""
    
    password = forms.CharField(
        widget=forms.PasswordInput,
        label=_('Password'),
        help_text=_('Enter a secure password'),
        error_messages={
            'required': _('Password is required.'),
        }
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        label=_('Confirm password'),
        help_text=_('Enter the same password again'),
        error_messages={
            'required': _('Password confirmation is required.'),
        }
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'username': _('Username'),
            'email': _('Email address'),
            'first_name': _('First name'),
            'last_name': _('Last name'),
        }
        help_texts = {
            'username': _('Enter a unique username'),
            'email': _('Enter a valid email address'),
            'first_name': _('Your first name'),
            'last_name': _('Your last name'),
        }
        error_messages = {
            'username': {
                'required': _('Username is required.'),
                'unique': _('This username is already taken.'),
                'invalid': _('Username contains invalid characters.'),
            },
            'email': {
                'required': _('Email address is required.'),
                'invalid': _('Please enter a valid email address.'),
                'unique': _('This email address is already registered.'),
            },
            'first_name': {
                'required': _('First name is required.'),
            },
            'last_name': {
                'required': _('Last name is required.'),
            },
        }
    
    def clean_password_confirm(self):
        """Проверка совпадения паролей."""
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError(_('Passwords do not match.'))
        
        return password_confirm
    
    def clean_password(self):
        """Валидация пароля."""
        password = self.cleaned_data.get('password')
        
        if password:
            if len(password) < 8:
                raise ValidationError(_('Password must be at least 8 characters long.'))
            
            if password.isdigit():
                raise ValidationError(_('Password cannot be entirely numeric.'))
            
            if password.lower() in ['password', '12345678', 'qwerty']:
                raise ValidationError(_('Password is too common.'))
        
        return password


class ContactForm(forms.Form):
    """Форма обратной связи с переводами."""
    
    name = forms.CharField(
        max_length=100,
        label=_('Name'),
        help_text=_('Your full name'),
        error_messages={
            'required': _('Name is required.'),
            'max_length': _('Name cannot exceed 100 characters.'),
        }
    )
    
    email = forms.EmailField(
        label=_('Email address'),
        help_text=_('Your email address for response'),
        error_messages={
            'required': _('Email address is required.'),
            'invalid': _('Please enter a valid email address.'),
        }
    )
    
    subject = forms.CharField(
        max_length=200,
        label=_('Subject'),
        help_text=_('Brief description of your message'),
        error_messages={
            'required': _('Subject is required.'),
            'max_length': _('Subject cannot exceed 200 characters.'),
        }
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        label=_('Message'),
        help_text=_('Your message or question'),
        error_messages={
            'required': _('Message is required.'),
        }
    )
    
    def clean_message(self):
        """Валидация сообщения."""
        message = self.cleaned_data.get('message')
        
        if message and len(message) < 10:
            raise ValidationError(_('Message must be at least 10 characters long.'))
        
        return message