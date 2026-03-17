from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Post, Category, Comment
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, DetailView, UpdateView
from django.views.generic import DeleteView, ListView
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import ProfileEditForm, CommentForm, PostForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count


class RegisterView(CreateView):
    # Стандартная форма Django для создания пользователя (логин+пароль+подтверждение пароля)
    form_class = UserCreationForm
    # Какой шаблон показывать при GET-запросе (пустая форма)
    template_name = 'registration/registration_form.html'
    # Куда направить после регистрации
    success_url = reverse_lazy('login')


class ProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    slug_field = 'username'  # по какому полю искать
    slug_url_kwarg = 'username'  # название параметра в URL
    context_object_name = 'profile'  # имя объекта в шаблоне

    def get_context_data(self, **kwargs):
        # Передает стандартный контекст (profile, view, object)
        context = super().get_context_data(**kwargs)
        user = self.object  # получаем пользователя

        posts = Post.objects.filter(author=user)  # берем все посты пользователя
        posts = posts.annotate(comment_count=Count('comments'))  # добавляем счетчик комментариев
        posts = posts.order_by('-pub_date')  # сортировка постов (новые сверху)

        # Если не мой профиль, то показывать только опубликованные посты
        if self.request.user != user:
            posts = posts.filter(
                is_published=True,
                pub_date__lte=timezone.now()  # уже наступило время публикации
            )

        paginator = Paginator(posts, 10)  # 10 постов на странице профиля
        page_number = self.request.GET.get('page')  # получаем номер страницы из GET-параметра ?page=...
        context['page_obj'] = paginator.get_page(page_number)  # получаем объект текущей страницы (или первую, или 404 при неверном номере) и добавляем в контекст
        return context


class ProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = ProfileEditForm
    template_name = 'blog/user.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def test_func(self):
        # Возвращаем True - можно редактировать, False — 403
        return self.get_object() == self.request.user

    def get_success_url(self):
        # После сохранения возвращаемся в профиль этого же пользователя
        return reverse(
            'blog:profile', kwargs={'username': self.object.username}
        )


class IndexListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'  # в шаблоне будет for post in post_list
    paginate_by = 10  # пагинатор

    # Определяет какие именно записи показывать
    def get_queryset(self):
        return Post.objects.select_related(
            'category', 'location', 'author'  # заранее подгружаем связанные объекты
        ).filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        ).annotate(
            comment_count=Count('comments')  # добавляем счетчик комментариев
        ).order_by('-pub_date')  # новые сверху


# Детальная страница одного поста
def post_detail(request, post_id):
    # Получаем пост по id или 404 (найди где id равен тому, что в URL)
    post = get_object_or_404(
        Post.objects.select_related('category', 'location', 'author'),
        id=post_id  # id = тому, что берется из URL из строки в urls.py
    )
    # Проверка прав доступа
    if not (request.user == post.author
            or (post.is_published
                and post.pub_date <= timezone.now()
                and post.category.is_published)):
        from django.http import Http404
        raise Http404("Пост не найден или не доступен")

    comments = post.comments.select_related('author').all()  # все комментарии к посту + авторы 
    form = CommentForm() if request.user.is_authenticated else None  # форма добавления комментария, только если залогинен

    # Словарь контекста, который будет передан в шаблон
    context = {
        'post': post,
        'comments': comments,
        'form': form,  # форма комментария
    }
    return render(request, 'blog/detail.html', context)


class CategoryPostsView(ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'post_list'
    paginate_by = 10  # пагинатор

    # Находим категорию
    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return Post.objects.select_related(
            'category', 'location', 'author'
        ).filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category=self.category
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Передаём объект категории в шаблон (чтобы вывести название категории, описание и т.д.)
        context['category'] = self.category
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        # Автоматически ставим автор = текущий пользователь
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        # После создания переходим в профиль автора
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'  # параметр в URL называется post_id

    def test_func(self):
        # Только автор может редактировать
        return self.get_object().author == self.request.user

    def get_success_url(self):
        # После редактирования переходим в детали поста
        return reverse('blog:post_detail', kwargs={'post_id': self.object.pk})

    def handle_no_permission(self):
        # Если не автор - не 403, а просто перенаправляем на просмотр
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'  # параметр в URL называется post_id

    def test_func(self):
        # Только автор может удалить
        return self.get_object().author == self.request.user

    def get_success_url(self):

        return reverse(
            # После удаления переходим в свой профиль
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


@login_required  # только для авторизованных
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None) 
    if form.is_valid():  # если нет ошибок
        comment = form.save(commit=False)  # не сохраняем сразу в базу
        comment.post = post  # приязываем к конкретному посту
        comment.author = request.user  # устанавливаем автора
        comment.save()
    # Возвращаемся на страницу поста
    return redirect('blog:post_detail', post_id=post.pk)


class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'  # параметр в URL называется comment_id

    def test_func(self):
        # Только автор может изменить
        return self.get_object().author == self.request.user

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.pk}  # возврат на страницу поста
        )


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'  # параметр в URL называется comment_id

    def test_func(self):
        # Только автор может удалить комментарий
        return self.get_object().author == self.request.user

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.pk}  # возврат на страницу поста
        )


def index(request):
    """Функция-прокси для обратной совместимости с тестами."""
    view = IndexListView.as_view()
    return view(request)


def category_posts(request, category_slug):
    """Функция-прокси для обратной совместимости с тестами."""
    view = CategoryPostsView.as_view()
    return view(request, category_slug=category_slug)
