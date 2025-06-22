from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # 기업별 detail 페이지 (예시: /detail/성우하이텍/, /detail/데브시스터즈/)
    path('detail/<str:company_name>/', views.company_detail, name='company_detail'),

    # API: 예시로 크롤링된 주식정보 JSON 제공
    path('stock-info/', views.stock_info_api, name='stock_info'),
]
