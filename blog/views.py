
# Create your views here.
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Post, Category, Comment
from django.contrib.auth import login, get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .forms import CommentForm, PostForm


User = get_user_model()


@login_required
def delete_post(request, post_id):
    """Удаление публикации (только автор)"""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/delete.html', {'item': post})


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария (только автор)"""
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/delete.html', {'item': comment})


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария (только автор)"""
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment_form.html', {
        'form': form,
        'post_id': post_id,
        'is_edit': True
    })


@login_required
def add_comment(request, post_id):
    """Добавление комментария"""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def create_post(request):
    """Создание новой публикации"""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    """Редактирование публикации (только автор)"""
    post = get_object_or_404(Post, pk=post_id)
    # Проверка прав: только автор может редактировать
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post.id)
    return render(request, 'blog/create.html', {'form': form, 'is_edit': True})


def index(request):
    """Главная страница — пагинация 10 постов"""
    # 1. Формируем QuerySet с фильтрами
    posts = Post.objects.select_related('category', 'location').filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True
    ).annotate(  # <-- Добавляем аннотацию
        comment_count=Count('comments')
    ).order_by('-pub_date')  # Сортировка: новые сверху
    # 2. Создаём пагинатор: 10 постов на страницу
    paginator = Paginator(posts, 10)
    # 3. Получаем номер страницы из URL (?page=2)
    page_number = request.GET.get('page')
    # 4. Получаем объекты для текущей страницы
    page_obj = paginator.get_page(page_number)
    # 5. Передаём page_obj в контекст (именно page_obj!)
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def category_posts(request, category_slug):
    """Страница категории — пагинация 10 постов"""
    # 1. Получаем категорию (проверяем, что она опубликована)
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    # 2. Формируем QuerySet постов этой категории
    posts = Post.objects.select_related('category', 'location').filter(
        category=category,
        pub_date__lte=timezone.now(),
        is_published=True
    ).order_by('-pub_date')
    # 3. Пагинация
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # 4. Контекст: category + page_obj
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'blog/category.html', context)


def profile(request, username):
    """Страница профиля пользователя"""
    # 1. Получаем пользователя, чей профиль просматриваем
    profile_user = get_object_or_404(User, username=username)
    # 2. Формируем базовый QuerySet постов автора
    posts = Post.objects.select_related('category', 'location').filter(
        author=profile_user
    )
    # 3.Проверка прав доступа
    if request.user == profile_user:
        # Если это сам автор — показываем ВСЕ его посты
        # (включая черновики, отложенные и снятые с публикации)
        pass  # Фильтры не применяем
    else:
        # Если это другой пользователь — показываем только опубликованные
        posts = posts.filter(
            pub_date__lte=timezone.now(),      # Дата не в будущем
            is_published=True,                 # Пост опубликован
            category__is_published=True        # Категория опубликована
        )
    posts = posts.annotate(  # <-- Добавляем аннотацию
        comment_count=Count('comments')
        # 4. Сортировка: новые посты сверху
    ).order_by('-pub_date')
    # 5. Пагинация (10 постов на страницу)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # 6. Контекст для шаблона
    context = {
        'profile_user': profile_user,
        'page_obj': page_obj,
        'is_owner': request.user == profile_user,  # Флаг для шаблона
    }
    return render(request, 'blog/profile.html', context)


def signup(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматический вход после регистрации
            return redirect('blog:index')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registration_form.html',
                  {'form': form})


def post_detail(request, id):
    """Страница отдельной публикации"""
    post = get_object_or_404(
        Post.objects.select_related('category', 'location', 'author'),
        pk=id,
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True
    )
    comments = post.comments.select_related('author').all()
    context = {
        'post': post,
        'comments': comments,
        'form': CommentForm(),  # Пустая форма для нового комментария
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    """Страница категории"""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True  # Если категория скрыта — 404
    )

    posts = Post.objects.select_related('category', 'location').filter(
        category=category,
        pub_date__lte=timezone.now(),
        is_published=True
    ).annotate(  # <-- Добавляем аннотацию
        comment_count=Count('comments')
    ).order_by('-pub_date')
    context = {'category': category, 'post_list': posts}
    return render(request, 'blog/category.html', context)
