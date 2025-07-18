from django.shortcuts import render, redirect


def index(request):
    if not request.user.is_authenticated:
        return redirect("login")
    context={}
    return render(request, "chat/index.html", context)


def room(request, room_name):
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "chat/room.html", {"room_name": room_name})
