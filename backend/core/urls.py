from . import views
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("", views.home, name="home"),
    path("chat/<int:id>", views.chat_details, name="chat-details"),
    path("search-users/", views.search_users, name="search-users"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register-user"),
    path("logout/", views.logout_view, name="logout"),
    path("send-invite/<int:id>", views.send_invite, name='send-invite'),
    path("send-message/<int:id>", views.send_message, name="send-message"),
    path("accept-request/<int:id>", views.accept_request, name='accept-request')

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)