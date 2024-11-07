from django import forms
from .models import TextModule, TextModuleFile
from django.core.exceptions import ValidationError
from django_summernote.widgets import SummernoteWidget

class TextModuleForm(forms.ModelForm):
    class Meta:
        model = TextModule
        fields = ['title', 'content', 'years', 'access_level']
        widgets = {
            'content': SummernoteWidget(),
        }

    def __init__(self, *args, hide_years=False, **kwargs):
        super(TextModuleForm, self).__init__(*args, **kwargs)
        if hide_years:
            self.fields.pop('years')

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get("title")
        years = cleaned_data.get("years")
        parent_module = self.instance.parent_module

        # 중복 검사 (현재 인스턴스를 제외)
        existing_query = TextModule.objects.filter(
            title=title,
            years=years,
            parent_module=parent_module
        ).exclude(id=self.instance.id)

        if existing_query.exists():
            if parent_module is None:
                self.add_error(None, "A module with this title and year already exists without a parent.")
            else:
                self.add_error(None, "A module with this title and year already exists under this parent.")
        
        return cleaned_data

    class TextModuleForm(forms.ModelForm):
        class Meta:
            model = TextModule
            fields = ['title', 'content', 'years', 'access_level']

    def __init__(self, *args, hide_years=False, **kwargs):
        super(TextModuleForm, self).__init__(*args, **kwargs)
        if hide_years:
            self.fields.pop('years')

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get("title")
        years = cleaned_data.get("years")
        parent_module = self.instance.parent_module  # 부모 모듈 설정 확인
        instance_id = self.instance.id  # 현재 인스턴스 ID 확인

        # 중복 검사 쿼리 (현재 인스턴스를 제외)
        existing_query = TextModule.objects.filter(
            title=title,
            years=years,
            parent_module=parent_module
        ).exclude(id=instance_id)

        # 디버깅 메시지
        print(f"[DEBUG] Title: {title}, Years: {years}, Parent Module: {parent_module}, Instance ID: {instance_id}")
        print(f"[DEBUG] Existing Query Count: {existing_query.count()}")  # 중복 검사의 결과 개수 확인

        # 중복 검사 조건
        if existing_query.exists():
            if parent_module is None:
                self.add_error(None, "A module with this title and year already exists without a parent.")
            else:
                self.add_error(None, "A module with this title and year already exists under this parent.")
        
        return cleaned_data

class TextModuleFileForm(forms.ModelForm):
    file = forms.FileField(required=False)

    class Meta:
        model = TextModuleFile
        fields = ['file']