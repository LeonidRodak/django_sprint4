from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()


class Category(models.Model):

    title = models.CharField(
        max_length=256,
        # Читаемое название поле в админке, формах, сообщении об ошибках
        verbose_name='Заголовок'
    )

    description = models.TextField(
        verbose_name='Описание'
    )

    # Уникальный slug для URL (blog/category/puteshestviya/)
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text='Идентификатор страницы для URL; разрешены символы\
 латиницы, цифры, дефис и подчёркивание.'
    )

    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )

    class Meta:
        ordering = ['title']  # сортировка по полю title
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    # Определяет, как объект будет выглядеть при выводе
    def __str__(self):
        return self.title

    # Переопределение метода save()
    def save(self, *args, **kwargs):
        if not self.slug:
            # Если slug пустой, то генерируем автоматически
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)  # вызываем стандартный save из родительского класса


class Location(models.Model):

    name = models.CharField(
        max_length=256,
        verbose_name='Название места'
    )

    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name


class Post(models.Model):

    # Поле для хранения изображения
    image = models.ImageField(
        'Изображение',
        upload_to='posts/',  # путь сохранения media/posts/
        blank=True,  # можно оставить пустым
        null=True)  # значение может быть null

    title = models.CharField(
        max_length=256,
        verbose_name='Заголовок'
    )

    text = models.TextField(
        verbose_name='Текст'
    )

    pub_date = models.DateTimeField(
        auto_now_add=False,  # для создания отложенных постов
        verbose_name='Дата и время публикации',
        help_text='Если установить дату и время в будущем — можно делать\
 отложенные публикации.'
    )

    # Связь многоие к одному (автор)
    author = models.ForeignKey(
        User,  # получаем через get_user_model
        on_delete=models.CASCADE,  # при удалении пользователя удаляются все его посты
        related_name='posts',  # можно получить все посты пользователя через user.posts.all()
        verbose_name='Автор публикации'
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,  # если удалят, то будет null (не CASCADE)
        null=True,
        blank=True,
        related_name='posts',
        verbose_name='Местоположение'
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,  # в формах поле категории обязательно должно быть заполнено, но после удаления может быть null
        related_name='posts',
        verbose_name='Категория'
    )

    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'


class Comment(models.Model):

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,  # если удалить пост, то удаляются все комментарии
        related_name='comments',  # все комментарии связанные с постом
        verbose_name='Публикация'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария'
    )

    text = models.TextField('Текст комментария')
    created_at = models.DateTimeField('Дата и время', auto_now_add=True)

    class Meta:
        ordering = ['created_at']  # новые комментарии снизу
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'Комментарий от {self.author} к {self.post}'
