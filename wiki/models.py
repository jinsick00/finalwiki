from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django_summernote.fields import SummernoteTextFormField
import os

# Create your models here.

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


    def delete(self, *args, **kwargs):
        # 파일 경로를 저장하고 모델 인스턴스 삭제 후 파일 삭제
        file_path = self.file.path
        super().delete(*args, **kwargs)
        
        # 파일이 존재하면 파일 삭제
        if os.path.isfile(file_path):
            os.remove(file_path)


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
    file = models.FileField(upload_to='files/')  # 파일 업로드 필드

    def __str__(self):
        return self.file.name

