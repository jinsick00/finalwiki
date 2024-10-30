from django.contrib import admin
from .models import TextModule, TextModuleFile
# Register your models here.


class TextModuleFileInline(admin.TabularInline):
    model = TextModuleFile
    extra = 1  # 새 파일 추가를 위해 빈 필드 1개 추가

@admin.register(TextModule)
class TextModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'years', 'access_level', 'parent_module')  # 목록에 표시할 필드
    search_fields = ('title', 'content')  # 검색 가능 필드
    list_filter = ('years', 'access_level')  # 필터링 옵션
    prepopulated_fields = {'slug': ('title',)}  # 슬러그를 제목을 기반으로 자동 생성
    inlines = [TextModuleFileInline]  # 파일을 인라인으로 추가