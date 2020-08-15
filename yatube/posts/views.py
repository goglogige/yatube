from django.views.decorators.cache import cache_page
from django.views.generic import CreateView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'group': group, 'page': page, 'paginator': paginator}
    )


class PostNew(CreateView):
    form_class = PostForm
    success_url = ""
    template_name = "new.html"


@login_required()
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'new.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('index')


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts_user.all()
    count = post_list.count()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    if request.user.is_anonymous:
        context = dict(author=author, page=page, paginator=paginator, count=count)
    else:
        user = request.user
        followers = Follow.objects.filter(author=author).count()
        subscriptions = Follow.objects.filter(user=author).count()
        if Follow.objects.filter(author=author, user=user).count() != 0:
            following = True
        else:
            following = False
        flag_user = True
        if author == user:
            flag_user = False
        context = dict(user=user, author=author, page=page, paginator=paginator, count=count,
                   subscriptions=subscriptions, followers=followers, following=following,
                   flag_user=flag_user)
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    user = request.user
    author = get_object_or_404(User, username=username)
    post_list = author.posts_user.all()
    items = post.comments.all()
    count = post_list.count()
    form = CommentForm(instance=None)
    followers = Follow.objects.filter(author=author).count()
    subscriptions = Follow.objects.filter(user=author).count()
    context = dict(user=user, post=post, author=author, count=count, items=items, form=form,
                   subscriptions=subscriptions, followers=followers)
    return render(request, 'post.html', context)


@login_required()
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'post.html', {'form': form})
    comment = form.save(commit=False)
    comment.post = post
    comment.author = request.user
    comment.save()
    return redirect('post', username=username, post_id=post_id)


@login_required()
def post_edit(request, username, post_id):
    """Функция редактирования созданного поста."""
    flag = True
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if post.author != request.user:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if not form.is_valid():
        return render(request, 'new.html', {'form': form, 'post': post, 'user': post.author, 'flag': flag})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('post', username=username, post_id=post_id)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'follow.html',
        {'page': page, 'paginator': paginator}
    )


@login_required
def profile_follow(request, username):
    follower = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    if author == follower:
        return redirect('profile', username=author.username)
    if follower.follower.filter(author=author).exists():
        return redirect('profile', username=author.username)
    follow = Follow.objects.create(user=follower, author=author)
    follow.save()
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follower = get_object_or_404(User, username=request.user.username)
    Follow.objects.filter(user=follower, author=author).delete()
    return redirect('profile', username=username)

