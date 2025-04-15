from django import forms
from .models import RegistroUsoLaboratorio

class RegistroUsoLaboratorioForm(forms.ModelForm):
    class Meta:
        model = RegistroUsoLaboratorio
        fields = '__all__'
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }
