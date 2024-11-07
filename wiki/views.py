import os
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import TextModule, TextModuleFile
from django.shortcuts import get_object_or_404, redirect
from django.utils.text import slugify
from django.urls import reverse_lazy
from .forms import TextModuleForm, TextModuleFileForm
from django.http import HttpRequest
from django.db import IntegrityError
from django.db.models import Max
import markdown
from django.utils.safestring import mark_safe


# Create your views here.

class TextModuleListView(ListView):
    model = TextModule
    template_name = 'wiki/textmodule_list.html'
    context_object_name = 'module_list'

    def get_queryset(self):
        selected_year = self.kwargs.get('years')

        queryset = TextModule.objects.filter(parent_module__isnull=True)

        latest_modules = queryset.values('title').annotate(latest_year=Max('years'))
        filtered_queryset = queryset.filter(
            title__in=[item['title'] for item in latest_modules],
            years__in=[item['latest_year'] for item in latest_modules]
    )

        if selected_year:
            filtered_queryset = filtered_queryset.filter(years=selected_year)

        return filtered_queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_year'] = self.kwargs.get('years')
        context['years_list'] = TextModule.objects.values_list('years', flat=True).distinct()
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TextModule에 있는 고유한 연도 목록을 가져와 드롭다운에 사용
        context['years_list'] = TextModule.objects.values_list('years', flat=True).distinct()
        context['selected_year'] = self.kwargs.get('years')  # 선택된 연도
        return context
    
class TextModuleDetailView(DetailView):
    model = TextModule
    template_name = 'wiki/textmodule_detail.html'
    context_object_name = 'module_detail'

    def get_object(self, queryset=None):
        slug = self.kwargs.get('slug')
        years = self.kwargs.get('years')
        module = get_object_or_404(TextModule, slug=slug, years=years)
        return module

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_detail'].content = mark_safe(markdown.markdown(context['module_detail'].content, extensions=['markdown.extensions.extra']))
        context['current_module'] = self.object  # self.object가 current_module로 설정됨
        context['child_modules'] = self.object.child_modules.all()  # 자식 모듈
        context['file_list'] = self.object.files.all()  # 파일 리스트 추가
        

        # 상위 모듈들을 담는 리스트 생성
        parent_modules = []
        current_module = self.object
        while current_module.parent_module:
            current_module = current_module.parent_module
            parent_modules.insert(0, current_module)  # 최상위 부모부터 시작하도록 리스트에 추가

        context['parent_modules'] = parent_modules  # 상위 모듈 리스트 추가
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)  # 먼저 기본 폼을 저장
        # 파일을 추가로 저장하는 로직
        for file in self.request.FILES.getlist('file'):
            TextModuleFile.objects.create(module=self.object, file=file)
        return response
    
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()  # 현재 부모 모듈 객체를 가져옴
        child_form = TextModuleForm(request.POST, hide_years=True)
        file_form = TextModuleFileForm(request.POST, request.FILES)

        if child_form.is_valid():
            child_module = child_form.save(commit=False)
            child_module.parent_module = self.object  # 부모 모듈 설정
            child_module.years = self.object.years  # 부모의 years 값 상속
        
            try:
                child_module.save()
                # 다중 파일 처리
                for file in request.FILES.getlist('files'):
                    TextModuleFile.objects.create(module=child_module, file=file)

                return redirect('wiki:textmodule_detail', slug=child_module.slug, years=child_module.years)

            except IntegrityError:
                # 이미 존재하는 모듈일 때 오류 메시지 추가
                context = self.get_context_data()
                context['child_module_form'] = child_form
                context['file_form'] = file_form
                context['error_message'] = "A module with this title and year already exists."
                return self.render_to_response(context)

        # 폼 유효성 검사 실패 시 동일한 컨텍스트로 렌더링
        context = self.get_context_data()
        context['child_module_form'] = child_form
        context['file_form'] = file_form
        return self.render_to_response(context)
    
class TextModuleCreateView(CreateView):
    model = TextModule
    form_class = TextModuleForm
    template_name = 'wiki/textmodule_create.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # 부모 없는 경우 years 필드 포함
        kwargs['hide_years'] = False
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)  # 먼저 기본 폼을 저장
        # 파일을 추가로 저장하는 로직
        for file in self.request.FILES.getlist('file'):
            TextModuleFile.objects.create(module=self.object, file=file)
        return response

    def get_success_url(self):
        parent_module_id = self.kwargs.get('parent_module_id')
        if parent_module_id:
            parent_module = get_object_or_404(TextModule, id=parent_module_id)
            return reverse_lazy('wiki:textmodule_detail', kwargs={'slug': parent_module.slug, 'years': parent_module.years})
        return reverse_lazy('wiki:textmodule_list')
    
class TextModuleUpdateView(UpdateView):
    model = TextModule
    form_class = TextModuleForm
    template_name = 'wiki/textmodule_update.html'
    context_object_name = 'module_detail'

    def get_object(self, queryset=None):
        slug = self.kwargs.get('slug')
        years = self.kwargs.get('years')
        # slug와 years 조합으로 특정 모듈을 가져옴
        return get_object_or_404(TextModule, slug=slug, years=years)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['existing_files'] = TextModuleFile.objects.filter(module=self.object)  # 기존 파일 리스트
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        # 세션에 저장된 파일 ID들을 사용해 파일 삭제
        files_to_delete = self.request.session.get('files_to_delete', [])
        for file_id in files_to_delete:
            try:
                file = TextModuleFile.objects.get(id=file_id)
                file.delete()
            except TextModuleFile.DoesNotExist:
                continue
        # 세션 초기화
        self.request.session['files_to_delete'] = []

        # 새 파일 추가 (여러 파일 처리)
        new_files = self.request.FILES.getlist('new_files')
        for new_file in new_files:
            TextModuleFile.objects.create(
                module=self.object,
                file=new_file,
                file_name=new_file.name
            )

        return response

    def post(self, request, *args, **kwargs):
        # 삭제 요청된 파일 ID를 세션에 저장
        files_to_delete = request.POST.getlist('delete_files')
        request.session['files_to_delete'] = files_to_delete
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('wiki:textmodule_detail', kwargs={'slug': self.object.slug, 'years': self.object.years})
    

class TextModuleDeleteView(DeleteView):
    model = TextModule
    template_name = 'wiki/textmodule_confirm_delete.html'
    success_url = reverse_lazy('wiki:textmodule_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # "임시" 모듈 가져오기 또는 생성
        temp_module, created = TextModule.objects.get_or_create(
            title="임시",
            defaults={
                'content': '이 모듈은 자동으로 생성되었습니다.',
                'years': 9999,  # 필요한 경우 연도를 지정
                'access_level': 'all'  # 기본 접근 권한 설정
            }
        )

        # 현재 모듈의 자식 모듈이 있는 경우 "임시" 모듈로 재할당
        child_modules = self.object.child_modules.all()
        if child_modules.exists():
            child_modules.update(parent_module=temp_module)

        # 부모 모듈 삭제
        return super().delete(request, *args, **kwargs)