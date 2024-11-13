from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django_summernote.fields import SummernoteTextFormField
import os
from django.dispatch import receiver
from django.db.models.signals import post_delete

# Create your models here.

def upload_to_module_directory(instance, filename):
    # 연도 및 모듈 제목을 경로에 포함하여 저장
    module_title = instance.module.title.replace(" ", "_")  # 공백을 밑줄로 변경
    years = instance.module.years
    return f'files/{years}/{module_title}/{filename}'

class TextModule(models.Model):
    ACCESS_CHOICES = [
        ('all', '모두 열람 가능'),
        ('staff', 'Staff 및 Superuser 전용'),
        ('superuser', 'Superuser 전용'),
    ]
    
    title = models.CharField(max_length=200)  # 제목
    content = models.TextField()  # 내용
    years = models.PositiveIntegerField()  # 연도 필드
    parent_module = models.ForeignKey(
        'self', null=True, blank=True, related_name='child_modules', on_delete=models.CASCADE
    )
    slug = models.SlugField()  # URL-friendly 문자열

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['parent_module', 'title', 'years'], name='unique_parent_title_years')
        ]
    
    
    # 접근 권한 필드 추가
    access_level = models.CharField(max_length=10, choices=ACCESS_CHOICES, default='all')

    def save(self, *args, **kwargs):
        # 부모 모듈과 상관없이 title만을 기반으로 slug 설정
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)

        super(TextModule, self).save(*args, **kwargs)


    


    def __str__(self):
        return self.title
    

    

class TextModuleFile(models.Model):
    # TextModule과 다대일 관계 설정
    file_name = models.CharField(max_length=200)
    FILE_TYPE_CHOICES = [
    ('form', '서식'),
    ('guideline', '지침')
    ]
    module = models.ForeignKey(TextModule, related_name='files', on_delete=models.CASCADE)
    file = models.FileField(upload_to=upload_to_module_directory)  # 파일 업로드 필드

    # 붙임파일 폴더경로 안보이게 하기(템플릿에서 사용)
    def get_filename(self):
        return os.path.basename(self.file.name)
    
    def __str__(self):
        return self.file.name

# 모델 인스턴스 삭제 시 실제 파일도 삭제
@receiver(post_delete, sender=TextModuleFile)
def delete_file_on_model_delete(sender, instance, **kwargs):
    if instance.file:
        file_path = instance.file.path
        if os.path.isfile(file_path):
            os.remove(file_path)