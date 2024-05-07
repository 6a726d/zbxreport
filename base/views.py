from django.db.models.query import QuerySet
from django.views.generic import TemplateView, ListView
from django.conf import settings
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import TBHostGroup, TBHost, TBItens, TBAPI, TBMiddleHost, TBMiddleItem, TBLayout, TBMiddleLayout
from django.contrib.auth.hashers import make_password
from api.zbx import ZbxAPI, ZbxHostGroup, ZbxHost, ZbxItens, ZbxHistory
from report.report import *
from django.http import FileResponse, Http404
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

@login_required
def change_password(request):
    if request.POST.get('action') == 'changepass':
        new_password = request.POST.get('newPassword')
        confirm_password = request.POST.get('confirmPassword')
        
        if new_password == confirm_password:
            request.user.set_password(new_password)
            request.user.save()
            print('change_password->')
            print('senha alterada campeao')
            print('<-change_password')
            update_session_auth_hash(request, request.user)
            print(new_password)
            print(confirm_password)
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('home')
        else:
            messages.error(request, 'As senhas não coincidem!')
            return redirect('home')

class VWHome(LoginRequiredMixin,TemplateView):
    login_url = reverse_lazy("login")
    template_name = 'vwhome/vwhome.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['tbapi'] = TBAPI.objects.get(apiusrid = self.request.user)
        except:
            pass
        context['grupos'] = TBHostGroup.objects.filter(gpusrid = self.request.user)
        context['layout'] = TBLayout.objects.filter(layoutusrid = self.request.user)
        return context

    def post(self, request, **kwargs):
        if self.request.POST.get('action') == 'save-api':
            self.apiurl = self.request.POST.get('apiurl')
            self.apiusr = self.request.POST.get('apiusr')
            self.apipass = self.request.POST.get('apipass')
            self._authApi(request)
            self._saveApi()
        if self.request.POST.get('report') == 'create-report':
            self.layout = self.request.POST.get('layout')
            self.hostgroup = self.request.POST.get('hostgroup')
            self.datefrom = self.request.POST.get('datefrom')
            self.dateto = self.request.POST.get('dateto')
            if not self._gethostfromgroup():
                messages.error(self.request, "Não existem hosts cadastrados neste grupo")
                return redirect('home') 
            self._getitemfromhost()
            self._getToken()
            self._getHistory(request)
            self._createGraph()
            self._createreport()
            self._createPDF(request)
            return redirect(reverse_lazy('downloadreport', args = [self.request.user.pk]))
        if self.request.POST.get('delete') == 'del-layout':
            self.layoutid = self.request.POST.get('layout_id')
            self._deleteLayout()
        return redirect(reverse_lazy('home'))
    
    def _authApi(self, request):
        self.token = ZbxAPI.get_zabbix_token(self.apiurl, self.apiusr, self.apipass, request)
        if not self.token:
            return
        messages.success(request, 'Login no Zabbix bem-sucedido!')
    
    def _saveApi(self):
        if not self.token:
            return
        self.apipass = make_password(self.apipass)
        try:
            tbapi = TBAPI.objects.get(apiusrid = self.request.user)
            tbapi.apiurl = self.apiurl
            tbapi.apiusr = self.apiusr
            tbapi.apipass = self.apipass
            tbapi.apitoken = self.token
            tbapi.save()
        except:
            TBAPI.objects.create(
                apiurl = self.apiurl,
                apiusr = self.apiusr,
                apipass = self.apipass,
                apiusrid = self.request.user,
                apitoken = self.token
            )

    def _deleteLayout(self):
        TBMiddleLayout.objects.filter(mdlid__pk = self.layoutid).delete()
        TBLayout.objects.get(pk = self.layoutid).delete()

    def _gethostfromgroup(self): 
        mdhost = TBMiddleHost.objects.filter(mdhhostgpid = self.hostgroup)
        self.hostlist = [TBHost.objects.get(pk = i.mdhhostid.pk) for i in mdhost]
        return bool(self.hostlist)

    def _getitemfromhost(self):
        self.mditem = TBMiddleItem.objects.filter(mdihostid__in = self.hostlist)
        layoutlist = [i.mdlitemname for i in TBMiddleLayout.objects.filter(mdlid__pk = self.layout)]
        self.mditem.filter(mdiitemname__in = layoutlist)
        self.zbxidlist = [i.mdiitemid for i in self.mditem]

    def _getToken(self):
        tbapi = TBAPI.objects.get(apiusrid = self.request.user)
        self._apitoken = tbapi.apitoken
        self._apiurl = tbapi.apiurl

    def _getHistory(self, request):
        self._history = ZbxHistory.get_item_history(self._apiurl, self._apitoken, self.zbxidlist, self.datefrom, self.dateto, request)
        self.data = [
            {'itemid': entry['itemid'], 'clock': entry['clock'], 'value': entry['value']}
            for entry in self._history
        ]

    def _createGraph(self):
        user_id = self.request.user.pk
        CreateReport.createGraph(self._history, self.layout, user_id)

    def _createreport(self):
        user_id = self.request.user.pk
        self._history = CreateReport.create_report(self.mditem, self.layout, self.hostgroup, self.datefrom, self.dateto, user_id)

    def _createPDF(self, request):
        user_id = self.request.user.pk
        CreateReport.gerarPDF(request, self._history)
        CreateReport.cleanGraphPNG(user_id)

def downloadReport(request, pk):
    filename = f"{pk}.pdf"  # Supondo que o nome do arquivo seja baseado no pk
    file_path = os.path.join(settings.MEDIA_ROOT, 'report', filename)
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'), as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    else:
        messages.error(request, "O arquivo PDF não foi encontrado.")
    

class VWHostGroup(LoginRequiredMixin,ListView):
    login_url = reverse_lazy("login")
    template_name = 'vwhostgroup/vwhostgroup.html'
    model = TBHostGroup
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().filter(gpusrid = self.request.user).order_by('gpzbxid')
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(gpname__icontains = search)
        return queryset
    
    def post(self, request, **kwargs):
        if self.request.POST.get('action') == 'save-hostgroup':
            self._getToken()
            self._getHostGroups(request)
            self._saveHostGroups()
        return redirect(reverse_lazy('hostgroup'))
    
    def _getToken(self):
        tbapi = TBAPI.objects.get(apiusrid = self.request.user)
        self._apitoken = tbapi.apitoken
        self._apiurl = tbapi.apiurl

    def _getHostGroups(self, request):
        self._hostgroups = ZbxHostGroup.get_host_groups(self._apiurl, self._apitoken, request)

    def _saveHostGroups(self):
        for i in self._hostgroups:
            group_exists = TBHostGroup.objects.filter(gpzbxid=i['groupid'], gpusrid=self.request.user).exists()

            # Se não existir, procede com a criação e salvamento
            if not group_exists:
                tbhostgroup = TBHostGroup(
                    gpzbxid=i['groupid'],
                    gpname=i['name'],
                    gpusrid=self.request.user
                )
                try:
                    tbhostgroup.save()
                except Exception as e:
                   pass 


class VWHost(LoginRequiredMixin,ListView):
    login_url = reverse_lazy("login")
    template_name = 'vwhost/vwhost.html'
    model = TBHost

    def get_queryset(self):
        queryset = super().get_queryset().filter(hostusrid = self.request.user)
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(hostname__icontains = search)
        return queryset
    
    def post(self, request, **kwargs):
        if self.request.POST.get('action') == 'save-hosts':
            self._getToken()
            self._getHosts(request)
            self._saveHosts()
            self._saveMdHost()
        return redirect(reverse_lazy('host'))
    
    def _getToken(self):
        tbapi = TBAPI.objects.get(apiusrid = self.request.user)
        self._apitoken = tbapi.apitoken
        self._apiurl = tbapi.apiurl
        
    def _getHosts(self, request):
        self._hosts = ZbxHost.get_hosts(self._apiurl, self._apitoken, request)

    def _saveHosts(self):
        for i in self._hosts:
            host_exists = TBHost.objects.filter(hostzbxid=i['hostid'], hostusrid=self.request.user).exists()

            if not host_exists:
                try:
                    tbhost = TBHost(
                        hostzbxid=i['hostid'],
                        hostname=i['name'],
                        hostusrid=self.request.user
                    )
                    tbhost.save()
                except Exception as e:
                    pass 

    def _saveMdHost(self):
        for host in self._hosts:
            for group in host['groups']:
                try:
                    host_instance = TBHost.objects.get(hostzbxid = host['hostid'], hostusrid = self.request.user)
                    group_instance = TBHostGroup.objects.get(gpzbxid = group['groupid'], gpusrid = self.request.user)

                    host_exists = TBMiddleHost.objects.filter(
                        mdhhostid=host_instance,
                        mdhhostgpid=group_instance,
                    ).exists()

                    if not host_exists:
                        tbmdhhost = TBMiddleHost(
                            mdhhostid=host_instance,
                            mdhhostgpid=group_instance,
                        )
                        tbmdhhost.save()
                except Exception as e:
                    pass


class VWItens(LoginRequiredMixin,ListView):
    login_url = reverse_lazy("login")
    template_name = 'vwitens/vwitens.html'
    model = TBItens
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().filter(itemusrid = self.request.user)
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(itemname__icontains = search)

        return queryset

    def post(self, request, **kwargs):
        if self.request.POST.get('action') == 'save-itens':
            self._getToken()
            self._getItens(request)
            self._saveItens()
            self._getItensHost(request)
            self._saveMdItens()
        if self.request.POST.get('action') == 'save-dsc':
            self.itemdsc = self.request.POST.get('itemdsc')
            self.itemid = self.request.POST.get('itemid')
            self._saveitemdsc()
        return redirect(reverse_lazy('itens'))
    
    def _saveitemdsc(self):
        tbitem = TBItens.objects.get(pk = self.itemid)
        tbitem.itemdscreport = self.itemdsc
        tbitem.save()
    
    def _getToken(self):
        tbapi = TBAPI.objects.get(apiusrid = self.request.user)
        self._apitoken = tbapi.apitoken
        self._apiurl = tbapi.apiurl
        
    def _getItens(self, request):
        self._itens = ZbxItens.get_itens(self._apiurl, self._apitoken, request)

    def _saveItens(self):
        for i in self._itens:
            itens_exists = TBItens.objects.filter(itemname = i['name'], itemusrid = self.request.user).exists()

            if not itens_exists:
                try:
                    tbitens = TBItens(
                        itemname = i['name'],
                        itemusrid = self.request.user
                    )
                    tbitens.save()
                except Exception as e:
                    pass 

    def _getItensHost(self, request):
        self._itenshost = ZbxItens.get_itens_hosts(self._apiurl, self._apitoken, request)

    def _saveMdItens(self):
        for i in self._itenshost:
            itenshost_exists = TBMiddleItem.objects.filter(mdiitemid = i['itemid'], mdiusrid = self.request.user).exists()
            item_instance = TBItens.objects.get(itemname = i['name'], itemusrid = self.request.user)

            if not itenshost_exists:
                try:
                    tbmditens = TBMiddleItem(
                        mdiitemid = i['itemid'],
                        mdiitemname = item_instance,
                        mdihostid = TBHost.objects.get(hostzbxid = i['hostid'], hostusrid = self.request.user),
                        mdiusrid = self.request.user
                    )
                    tbmditens.save()
                except Exception as e:
                    pass


class VWLayout(LoginRequiredMixin,TemplateView):
    login_url = reverse_lazy("login")
    template_name = 'vwlayout/vwlayout.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['itens'] = TBItens.objects.filter(itemusrid = self.request.user)
        return context
    
    def post(self, request, **kwargs):
        if self.request.POST.get('action') == 'save-layout':
            self.layoutname = self.request.POST.get('layoutname')
            self.layoutemp = self.request.POST.get('layoutemp')
            self.layoutdsc = self.request.POST.get('layoutdsc')
            self.itemValues = self.request.POST.getlist('selectedItems[]')
            self.layoutlogo = self.request.FILES.get('layoutlogo')
            if self.layoutlogo:
                self._saveLogo()
            self._saveLayout(request)
        return redirect(reverse_lazy('home'))

    def _saveLogo(self):
        user_id = self.request.user.pk
        original_extension = os.path.splitext(self.layoutlogo.name)[1]
        file_name = f"{user_id}{original_extension}"
        file_path = os.path.join(settings.MEDIA_ROOT, 'logo', file_name)
        with default_storage.open(file_path, 'wb+') as destination:
            for chunk in self.layoutlogo.chunks():
                destination.write(chunk)
    
    def _saveLayout(self, request):
        tblayout = TBLayout(
            layoutname = self.layoutname,
            layoutemp = self.layoutemp,
            layoutdsc = self.layoutdsc,
            layoutusrid = self.request.user
        )
        tblayout.save()
        for i in self.itemValues:
            item = TBItens.objects.get(pk = i, itemusrid=self.request.user)
            TBMiddleLayout.objects.create(
                mdlid = tblayout,
                mdlitemname = item
            )
        messages.success(request, 'Layout salvo!')

class VWLayoutEdit(LoginRequiredMixin,TemplateView):
    login_url = reverse_lazy("login")
    template_name = 'vwlayout/vwlayoutedit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['itens'] = TBItens.objects.all()
        layout = TBLayout.objects.get(pk = context['pk'])
        context['tblayout'] = layout
        context['tbmiddlelayout'] = TBMiddleLayout.objects.filter(mdlid=layout)
        return context
    
    def post(self, request, **kwargs):
        if self.request.POST.get('action') == 'save-layout':
            self.layoutname = self.request.POST.get('layoutname')
            self.layoutemp = self.request.POST.get('layoutemp')
            self.layoutdsc = self.request.POST.get('layoutdsc')
            self.layoutpk = self.request.POST.get('id')
            self.itemValues = self.request.POST.getlist('selectedItems[]')
            print(self.itemValues)
            self.layoutlogo = self.request.FILES.get('layoutlogo')
            if self.layoutlogo:
                self._saveLogo()
            self._saveLayout(request)
        return redirect(reverse_lazy('home'))
    
    def _saveLogo(self):
        user_id = self.request.user.pk
        original_extension = os.path.splitext(self.layoutlogo.name)[1]
        file_name = f"{user_id}{original_extension}"
        file_path = os.path.join(settings.MEDIA_ROOT, 'logo', file_name)
        with default_storage.open(file_path, 'wb+') as destination:
            for chunk in self.layoutlogo.chunks():
                destination.write(chunk)

    def _saveLayout(self, request):
        tblayout = TBLayout.objects.get(pk = self.layoutpk)
        tblayout.layoutname = self.layoutname
        tblayout.layoutemp = self.layoutemp
        tblayout.layoutdsc = self.layoutdsc
        tblayout.save()
        tbmdlayout = TBMiddleLayout.objects.filter(mdlid = tblayout)
        tbmdlayout.delete()
        for i in self.itemValues:
            item = TBItens.objects.get(pk = i, itemusrid=self.request.user)
            TBMiddleLayout.objects.create(
                mdlid = tblayout,
                mdlitemname = item
            )
        messages.success(request, 'Layout salvo!')
