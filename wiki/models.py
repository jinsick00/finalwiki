from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

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
        # 중복 검증
        if self.parent_module is None:
            # 부모가 없는 경우 title과 years 조합이 고유해야 함
            if TextModule.objects.filter(title=self.title, years=self.years, parent_module__isnull=True).exists():
                raise ValidationError("A module with this title and year already exists without a parent.")
        else:
            # 부모가 있는 경우 parent_module, title, years 조합이 고유해야 함
            if TextModule.objects.filter(title=self.title, years=self.years, parent_module=self.parent_module).exists():
                raise ValidationError("A module with this title and year already exists under this parent.")

        # 슬러그 설정
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True)
            parent = self.parent_module
            slug_parts = [base_slug]

            while parent:
                slug_parts.insert(0, slugify(parent.title, allow_unicode=True))
                parent = parent.parent_module

            self.slug = "-".join(slug_parts)

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
    file = models.FileField(upload_to='files/')  # 파일 업로드 필드

    def __str__(self):
        return self.file.name

