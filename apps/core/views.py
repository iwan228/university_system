from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages


@login_required
def dashboard(request):
    """Главная страница — дашборд"""
    from apps.students.models import Student, AcademicDebt
    from apps.commissions.models import CommissionSheet

    total_debts = AcademicDebt.objects.count()

    context = {
        'total_students': Student.objects.count(),
        'total_debts': total_debts,
        'unique_debtors': AcademicDebt.objects.values('student').distinct().count(),
        'open_sheets': CommissionSheet.objects.filter(status='open').count(),
    }
    return render(request, 'core/dashboard.html', context)


def login_view(request):
    """Страница входа"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Неверные данные для входа.')
        else:
            messages.error(request, 'Неверные данные для входа.')
    else:
        form = AuthenticationForm()

    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('login')


def register_view(request):
    """Регистрация (для создания первого пользователя)"""
    from django.contrib.auth.models import User

    # Если пользователи уже есть — регистрация через эту страницу закрыта
    if User.objects.exists() and not request.user.is_authenticated:
        messages.warning(request, 'Регистрация закрыта. Обратитесь к администратору.')
        return redirect('login')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Учётная запись успешно создана!')
            return redirect('dashboard')
    else:
        form = UserCreationForm()

    return render(request, 'core/register.html', {'form': form})
