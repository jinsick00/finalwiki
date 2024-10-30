from django import forms
from .models import TextModule, TextModuleFile

class TextModuleForm(forms.ModelForm):
    class Meta:
        model = TextModule
        fields = ['title', 'content', 'years']  # 기본 필드 포함

    def __init__(self, *args, hide_years=False, **kwargs):
        super(TextModuleForm, self).__init__(*args, **kwargs)
        if hide_years:
            self.fields.pop('years')

class TextModuleFileForm(forms.ModelForm):
    file = forms.FileField(required=False)  # 파일 필드를 선택 사항으로 변경

    class Meta:
        model = TextModuleFile
        fields = ['file']