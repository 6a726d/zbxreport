from django.contrib.auth.views import LoginView
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext as _

class VWLogin(LoginView):
    template_name = "vwlogin.html"

    def form_invalid(self, form):
        messages.error(self.request, _('Senha incorreta, tente novamente.'))
        return super().form_invalid(form)
    