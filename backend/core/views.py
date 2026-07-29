from datetime import timedelta
import base64
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import User, Chat
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
import json

# Create your views here.
@login_required
def home(request):
    friends = get_friends(request.user)
    chat_list = []
    for friend in friends:
        chat = get_or_create_chat(request.user, friend)
        last_message = chat.messages.order_by("-created_at").first()
        if last_message:
            if last_message.image:
                last_message_text = "new snap"
            else:
                last_message_text = last_message.text
        else:
            last_message_text = ""
        chat_list.append((friend, chat, last_message_text))

    chat_list.sort(key=lambda x:x[1].last_message, reverse=True)
    return render(request, "pages/chat.html", {"friendList":chat_list})

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
    chat = get_or_create_chat(request.user, friend)

    if are_friends(request.user, friend):
        messages = Messages.objects.filter(Q(sender=request.user , receiver=friend) | Q(sender=friend, receiver=request.user)).order_by("created_at")
        messages = list(messages)
        recieved_msg = Messages.objects.filter(receiver=request.user, sender=friend)
        if chat.mode == Chat.Mode.ON_CLOSE:
            recieved_msg.delete()
        if chat.mode == Chat.Mode.AFTER_24HR:
            msg = recieved_msg.filter(created_at__gte=timezone.now() - timedelta(days=1))
            msg.delete()

        update_streak(request.user, friend)
        return render(request, "pages/chat-details.html", {"messages":messages, "friend": friend, "chat":chat})
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
        chat = get_or_create_chat(request.user, friend)
        Messages.objects.create(
            sender=request.user,
            receiver=friend,
            text=text,
            image=image,
            chat=chat
        )
        chat.last_message = timezone.now()
        chat.save(update_fields=["last_message"])
        update_streak(request.user, friend)
        return redirect("chat-details", id=friend.id)
    return redirect("home")

def are_friends(user1, user2):
    exist = FriendRequest.objects.filter(Q(to_user=user1, from_user=user2) | Q(to_user=user2, from_user=user1)).filter(status=FriendRequest.StatusChoice.ACCEPTED).exists()
    if exist:
        return True
    else:
        return False

def get_friends(user):
    friendList = FriendRequest.objects.filter(Q(to_user=user) | Q(from_user=user)).filter(status=FriendRequest.StatusChoice.ACCEPTED)
    friends = []
    for f in friendList:
        if f.to_user == user:
            friends.append(f.from_user)
        else:
            friends.append(f.to_user)
    return friends


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


def get_or_create_chat(user1, user2):
    if user1.id > user2.id:
        user1, user2 = user2, user1
    chat , _ = Chat.objects.get_or_create(user1=user1, user2=user2)
    return chat

def camera(request):
    friends =  get_friends(request.user)
    return render(request, "pages/camera.html", {"friends": friends})


def is_user_sended_snap(chat, user):
    return (
        chat.messages.filter(
            sender=user,
            created_at__date=timezone.localtime().date(),
        ).exclude(image="").exclude(image__isnull=True).exists()
    )



def update_streak(user1, user2):
    chat = get_or_create_chat(user1, user2)

    user1_sent = is_user_sended_snap(chat, user1)
    user2_sent = is_user_sended_snap(chat, user2)

    # print(user1_sent, user2_sent)
    
    if user1_sent and user2_sent:
        now = timezone.now().date()
        # print(now, chat.last_streak_at.date())
        difference = now - chat.last_streak_at.date() 
        # print(difference)
        if difference.days == 1:
            chat.streak += 1
        elif difference.days == 0:
            return
        else:
            chat.streak = 0
        print(chat.streak)
        chat.last_streak_at = timezone.now()
        chat.save(update_fields=["streak", "last_streak_at"])

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def send_snap_multiple(request):
    friend_ids_json = request.POST.get("friend_ids")
    image_data_url = request.POST.get("image_data")
    
    if not friend_ids_json or not image_data_url:
        return redirect("home")
        
    try:
        friend_ids = json.loads(friend_ids_json)
    except Exception:
        return redirect("home")
        
    if ';base64,' in image_data_url:
        format, imgstr = image_data_url.split(';base64,') 
        print(format)
        extention = format.split('/')[-1]
        print(extention)
        data = ContentFile(base64.b64decode(imgstr), name=f'snap_{timezone.now()}.{extention}')
    else:
        return redirect("home")
    
    for fid in friend_ids:
        friend = get_object_or_404(get_user_model(), pk=fid)
        if are_friends(request.user, friend):
            chat = get_or_create_chat(request.user, friend)
            Messages.objects.create(
                sender=request.user,
                receiver=friend,
                text="",
                image=data,
                chat=chat
            )
            chat.last_message = timezone.now()
            chat.save(update_fields=["last_message"])
            update_streak(request.user, friend)
            
    return redirect("home")