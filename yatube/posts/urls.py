from django.urls import path

from . import views

urlpatterns = [
    path("follow/", views.follow_index, name="follow_index"),
    path("<str:username>/unfollow/", views.profile_unfollow, name="profile_unfollow"),
    path("<str:username>/follow/", views.profile_follow, name="profile_follow"),
    path("", views.index, name="index"),
    path("group/<slug:slug>/", views.group_posts, name="group_posts"),
    path("new/", views.new_post, name="new_post"),
    path('<str:username>/', views.profile, name='profile'),
    # Просмотр записи
    path('<str:username>/<int:post_id>/', views.post_view, name='post'),
    path('<str:username>/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('<str:username>/<int:post_id>/edit/', views.post_edit, name='post_edit'),
]


