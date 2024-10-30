import os
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from .models import TextModule, TextModuleFile
from django.shortcuts import get_object_or_404, redirect
from django.utils.text import slugify
from django.urls import reverse_lazy
from .forms import TextModuleForm, TextModuleFileForm
from django.http import HttpRequest
from django.db import IntegrityError

# Create your views here.

class TextModuleListView(ListView):
    model = TextModule
    template_name = 'wiki/textmodule_list.html'
    context_object_name = 'module_list'

    def get_queryset(self):
        # URL에서 'years' 파라미터를 받아 필터링
        years = self.kwargs.get('years')
        if years:
            return TextModule.objects.filter(years=years, parent_module__isnull=True)
        return TextModule.objects.filter(parent_module__isnull=True)  # 전체 목록 (기본값)

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
        context['child_module_form'] = TextModuleForm(hide_years=True)
        context['file_form'] = TextModuleFileForm()
        context['child_modules'] = self.object.child_modules.all()  # 바로 아래 자식 모듈들

        # 부모 모듈 리스트 가져오기
        parent_modules = []
        current_module = self.object
        while current_module.parent_module:
            parent_modules.insert(0, current_module.parent_module)  # 최상위 부모가 먼저 오도록 앞에 추가
            current_module = current_module.parent_module

        context['parent_modules'] = parent_modules
        context['file_list'] = TextModuleFile.objects.filter(module=self.object)
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