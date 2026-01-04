"""webapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from webapp import views

urlpatterns = [
    # 原始管理后台
    # path('admin/', admin.site.urls),
    # 里面留空，代表首页
    path('', views.start),
    # 返回首页
    path('home/', views.start, name="start"),
    # 搜索跳转
    path('get_ans/', views.get_ans, name="get_ans"),
    # 输入错误
    path('error/', views.get_ans, name="error"),
    # 输入正确
    path('user_class/', views.get_ans, name="user_class"),
]
