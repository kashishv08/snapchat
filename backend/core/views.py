from django.dispatch import receiver
from .models import User
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import FriendRequest, Messages
from django.shortcuts import render,redirect
from .forms import LoginForm, RegisterForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, logout
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings

# Create your views here.
@login_required
def home(request):
    friendList = FriendRequest.objects.filter(Q(to_user=request.user) | Q(from_user=request.user)).filter(status=FriendRequest.StatusChoice.ACCEPTED)
    friends = []
    for f in friendList:
        if f.to_user == request.user:
            friends.append(f.from_user)
        else:
            friends.append(f.to_user)
    print(friendList)
    return render(request, "pages/chat.html", {"friendList":friends})

@require_http_methods(["POST"])
@login_required
def send_invite(request,id):
    if id == request.user.id:
        return redirect("search-users")
    to_user = get_object_or_404(get_user_model(), pk=id)
    if request.method == 'POST':
        friend = FriendRequest.objects.filter(Q(from_user=request.user, to_user=to_user) | Q(from_user=to_user, to_user=request.user) ).exists()
        if friend:
            return redirect("search-users")
        FriendRequest.objects.create(from_user=request.user, to_user=to_user, status=FriendRequest.StatusChoice.PENDING)
        return redirect("search-users")

@login_required
@require_http_methods(["GET", "POST"])
def chat_details(request, id):
    friend = get_object_or_404(get_user_model(), pk=id)

    if are_friends(request.user, friend):
        messages = Messages.objects.filter(Q(sender=request.user , receiver=friend) | Q(sender=friend, receiver=request.user)).order_by("created_at")

        messages = list(messages)

        recieved_msg = Messages.objects.filter(receiver=request.user)
        recieved_msg.delete()
        return render(request, "pages/chat-details.html", {"messages":messages, "friend": friend})
    return redirect("home")

@login_required
def search_users(request):
    friend_requests = FriendRequest.objects.filter(Q(to_user=request.user) | Q(from_user=request.user))

    user_ids = set()
    for f in friend_requests:
        user_ids.add(f.from_user_id)
        user_ids.add(f.to_user_id)

    if request.user.id in user_ids:
        user_ids.remove(request.user.id)

    pending_friend_requests = friend_requests.exclude(status=FriendRequest.StatusChoice.ACCEPTED)
    not_added_user = User.objects.exclude(id__in=user_ids).exclude(id=request.user.id)
    return render(request, "pages/search.html", {"pending_friend_requests":pending_friend_requests, "not_added_user":not_added_user})

@login_required
@require_http_methods(["POST"])
def send_message(request, id):
    friend = get_object_or_404(get_user_model(), pk=id)
    text = request.POST.get("message")
    image = request.FILES.get("image")
    if are_friends(request.user, friend):
        Messages.objects.create(
            sender=request.user,
            receiver=friend,
            text=text,
            image=image
        )
        return redirect("chat-details", id=friend.id)
    return redirect("home")


def are_friends(user1, user2):
    exist = FriendRequest.objects.filter(Q(to_user=user1, from_user=user2) | Q(to_user=user2, from_user=user1)).filter(status=FriendRequest.StatusChoice.ACCEPTED).exists()
    if exist:
        return True
    else:
        return False

@require_http_methods(["POST", "GET"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    form =  LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        print(form.get_user())
        login(request, form.get_user())
        return redirect("home")
    else:
        print("form not valid")
    return render(request, "accounts/auth.html", { "form":form ,"is_login": True})

@require_http_methods(["POST", "GET"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("home")
    return render(request, "accounts/auth.html", {"form":form})

def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
# @csrf_exempt
@require_http_methods(["POST"])
def accept_request(request, id):
    from_request = get_object_or_404(get_user_model(), pk=id)
    try:
        friend_request = FriendRequest.objects.get(to_user=request.user, from_user=from_request, status=FriendRequest.StatusChoice.PENDING)
        friend_request.status = FriendRequest.StatusChoice.ACCEPTED
        friend_request.save()
    except FriendRequest.DoesNotExist:
        messages.error(request, "No pending friend request found.")
    return redirect("home")
    
def map_view(request):
    return render(request, "pages/map.html", {"REVERSE_GEO_API_KEY" : settings.REVERSE_GEO_API_KEY})

