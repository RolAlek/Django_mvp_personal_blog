from datetime import datetime
from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.forms.models import BaseModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DetailView, DeleteView, ListView, UpdateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count

from blog.models import Post, Category, Comment
from blog.forms import CommentForm, PostForms, ProfileEditForm


COMMENT_CONST = 'comments'
COMMENT_ID_CONST = 'comment_id'
CUT_SLUG = 'category_slug'
DETAIL_URL = 'blog:post_detail'
GET_PAGE_CONST = 'page'
OBJECTS_PER_PAGE = 10
PAGE_OBJ_CONST = 'page_obj'
PROFILE_HTML = 'blog/profile.html'
POST_ID_CONST = 'post_id'
TABLES_LIST = (
    'category',
    'author',
    'location',
)
USERNAME_SLUG = 'username'


User = get_user_model()


class ProfileMixin:
    model = User
    slug_field = USERNAME_SLUG
    slug_url_kwarg = USERNAME_SLUG


class PostMixin:
    model = Post
    pk_url_kwarg = POST_ID_CONST


class PostCreateMixin:
    form_class = PostForms
    template_name = 'blog/create.html'


class PostEditMixin:

    def dispatch(
            self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        instance = get_object_or_404(Post, id=kwargs.get(POST_ID_CONST))
        if instance.author != request.user:
            return redirect(
                DETAIL_URL,
                post_id=self.kwargs.get(POST_ID_CONST)
            )
        return super().dispatch(request, *args, **kwargs)


class CommentMixin:
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'


class CommentEditMixin:
    pk_url_kwarg = COMMENT_ID_CONST

    def dispatch(
            self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        instance = get_object_or_404(Comment, id=kwargs.get(COMMENT_ID_CONST))
        if instance.author != request.user:
            return redirect(
                DETAIL_URL,
                post_id=self.kwargs.get(POST_ID_CONST)
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse(
            DETAIL_URL, kwargs={POST_ID_CONST: self.object.posts_id}
        )


class HomePage(ListView):
    model = Post
    queryset = Post.objects.select_related(*TABLES_LIST).annotate(
        comment_count=Count(COMMENT_CONST)
    ).filter(
        pub_date__lte=datetime.now(),
        is_published=True,
        category__is_published=True
    )
    template_name = 'blog/index.html'
    paginate_by = OBJECTS_PER_PAGE
    ordering = ('-pub_date', 'title',)


class ProfileView(ProfileMixin, DetailView):
    template_name = PROFILE_HTML
    context_object_name = 'profile'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        posts = None
        if self.request.user.is_authenticated:
            posts = Post.objects.select_related(*TABLES_LIST).annotate(
                comment_count=Count(COMMENT_CONST)
            ).filter(
                author=get_object_or_404(User, username=self.object.username),
            )
        else:
            posts = Post.objects.all().annotate(
                comment_count=Count(COMMENT_CONST)
            ).filter(
                author=get_object_or_404(User, username=self.object.username),
                is_published=True,
                pub_date__lte=datetime.now()
            )
        paginatror = Paginator(posts, OBJECTS_PER_PAGE)
        page_number = self.request.GET.get(GET_PAGE_CONST)
        context[PAGE_OBJ_CONST] = paginatror.get_page(page_number)
        return context


class ProfileEditView(ProfileMixin, LoginRequiredMixin, UpdateView):
    form_class = ProfileEditForm
    template_name = 'blog/user.html'

    def get_success_url(self) -> str:
        return reverse(
            'blog:profile', kwargs={USERNAME_SLUG: self.object.username}
        )


class PostDetailView(PostMixin, DetailView):
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context[COMMENT_CONST] = (
            self.object.comments.all()
        )
        return context


class PostCreatView(
    PostMixin, PostCreateMixin, LoginRequiredMixin, CreateView
):

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            'blog:profile', kwargs={USERNAME_SLUG: self.request.user}
        )


class PostEditView(
    PostMixin, PostEditMixin, PostCreateMixin, LoginRequiredMixin, UpdateView
):
    pass


class PostDeleteView(
    PostMixin, PostEditMixin, PostCreateMixin, LoginRequiredMixin, DeleteView
):
    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        instance = get_object_or_404(Post, id=self.object.id)
        form = PostForms(instance=instance)
        context['form'] = form
        return context


class CommentCreateView(CommentMixin, LoginRequiredMixin, CreateView):
    posts = None

    def dispatch(
            self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        self.posts = get_object_or_404(Post, id=kwargs.get(POST_ID_CONST))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.author = self.request.user
        form.instance.posts = self.posts
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            DETAIL_URL,
            kwargs={POST_ID_CONST: self.posts.id}
        )


class EditComment(
    CommentMixin, CommentEditMixin, LoginRequiredMixin, UpdateView
):
    pass


class CommentDeleteView(
    CommentMixin, CommentEditMixin, LoginRequiredMixin, DeleteView
):
    pass


class CategoryListView(DetailView):
    model = Category
    queryset = Category.objects.filter(is_published=True)
    template_name = 'blog/category.html'
    slug_field = 'slug'
    slug_url_kwarg = CUT_SLUG
    context_object_name = 'category'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        posts = Post.objects.select_related(*TABLES_LIST).annotate(
            comment_count=Count(COMMENT_CONST)
        ).filter(
            category__slug=self.kwargs.get(CUT_SLUG),
            is_published=True,
            pub_date__lte=datetime.now()
        )
        paginator = Paginator(posts, OBJECTS_PER_PAGE)
        page_number = self.request.GET.get(GET_PAGE_CONST)
        page_obj = paginator.get_page(page_number)
        context[PAGE_OBJ_CONST] = page_obj
        return context
