from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import TextModuleListView, TextModuleDetailView, TextModuleCreateView, TextModuleUpdateView

app_name = 'wiki'

urlpatterns = [
    # ListView URL 패턴
    path('', TextModuleListView.as_view(), name='textmodule_list'),
    path('create/', TextModuleCreateView.as_view(), name='textmodule_create'),  # 부모 없는 모듈 생성
    path('year/<int:years>/', TextModuleListView.as_view(), name='textmodule_list_filtered'),  # 기본 페이지를 ListView로 설정
    path('<path:slug>/<int:years>/', TextModuleDetailView.as_view(), name='textmodule_detail'),
    path('<path:slug>/<int:years>/edit/', TextModuleUpdateView.as_view(), name='textmodule_edit'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)