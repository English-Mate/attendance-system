from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Attendance, Department


class UserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)
    employee_id = forms.CharField(max_length=50, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'department', 'employee_id', 'password1', 'password2']


class AttendanceForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.filter(is_active_record=True))

    class Meta:
        model = Attendance
        fields = ['user', 'date', 'check_in', 'check_out', 'status', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'check_in': forms.TimeInput(attrs={'type': 'time'}),
            'check_out': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
