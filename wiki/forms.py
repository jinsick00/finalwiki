from django import forms
from .models import TextModule, TextModuleFile
from django.core.exceptions import ValidationError

class TextModuleForm(forms.ModelForm):
    class Meta:
        model = TextModule
        fields = ['title', 'content', 'years', 'access_level']  # access_level 필드 추가

    def __init__(self, *args, hide_years=False, **kwargs):
        super(TextModuleForm, self).__init__(*args, **kwargs)
        if hide_years:
            self.fields.pop('years')

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get("title")
        years = cleaned_data.get("years")
        parent_module = self.instance.parent_module

        # 부모가 없는 경우 title과 years 조합이 고유해야 함
        if parent_module is None and TextModule.objects.filter(title=title, years=years, parent_module__isnull=True).exists():
            
            self.add_error(None, "A module with this title and year already exists without a parent.")
        
        # 부모가 있는 경우 parent_module, title, years 조합이 고유해야 함
        elif parent_module and TextModule.objects.filter(title=title, years=years, parent_module=parent_module).exists():
            
            self.add_error(None, "A module with this title and year already exists under this parent.")
        
        return cleaned_data

class TextModuleFileForm(forms.ModelForm):
    file = forms.FileField(required=False)

    class Meta:
        model = TextModuleFile
        fields = ['file']