from django.urls import path
from .views import VWHome, VWHostGroup, VWHost, VWItens, VWLayout, VWLayoutEdit, downloadReport, change_password
from report.report import CreateReport

urlpatterns = [
    path('', VWHome.as_view(), name = 'home'),
    path('hostgroup', VWHostGroup.as_view(), name = 'hostgroup'),
    path('host', VWHost.as_view(), name = 'host'),
    path('itens', VWItens.as_view(), name = 'itens'),
    path('layout', VWLayout.as_view(), name = 'layout'),
    path('layout/edit/<int:pk>', VWLayoutEdit.as_view(), name = 'layoutedit'),
    path('downloadreport/<int:pk>', downloadReport, name='downloadreport'),
    path('change-password/', change_password, name='change_password'),
]