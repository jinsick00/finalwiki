from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegisterForm

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # 회원가입 후 자동 로그인
            return redirect('index')  # 회원가입 후 리다이렉트할 페이지
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})