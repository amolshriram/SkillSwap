from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("inbox/", views.inbox, name="inbox"),
    path("inbox/<int:conversation_id>/", views.conversation_detail, name="conversation_detail"),
    path("profile/", views.profile, name="profile"),
    path("skills/add/", views.skill_add, name="skill_add"),
    path("skills/<int:skill_id>/edit/", views.skill_edit, name="skill_edit"),
    path("skills/<int:skill_id>/delete/", views.skill_delete, name="skill_delete"),
    path("users/", views.skill_listings, name="skill_listings"),
    path("swap/request/<int:receiver_id>/", views.swap_request_create, name="swap_request_create"),
    path("swap/<int:request_id>/accept/", views.swap_request_accept, name="swap_request_accept"),
    path("swap/<int:request_id>/reject/", views.swap_request_reject, name="swap_request_reject"),
]

