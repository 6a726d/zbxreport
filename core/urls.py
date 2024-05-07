from django.urls import path, include

urlpatterns = [
    path('', include('base.urls')),
    path('login', include('login.urls')),
]
