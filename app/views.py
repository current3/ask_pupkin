import math

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from .forms import AnswerForm, AskForm, LoginForm, ProfileEditForm, SignupForm
from .models import Answer, Question, Tag


def paginate(objects, request, per_page=20):
    page_number = request.GET.get("page", 1)
    paginator = Paginator(objects, per_page)

    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    return page


def new_questions(request):
    qs = Question.objects.new()
    page = paginate(qs, request, per_page=20)
    return render(request, "index.html", {"questions": page})


def hot_questions(request):
    qs = Question.objects.hot()
    page = paginate(qs, request, per_page=20)
    return render(request, "index.html", {"questions": page})


def tag_questions(request, tag):
    tag_obj = get_object_or_404(Tag, name=tag)
    qs = tag_obj.questions.all()
    page = paginate(qs, request, per_page=20)
    return render(request, "index.html", {"questions": page, "tag": tag_obj})


def login_view(request):
    cont = request.GET.get("continue") if request.method == "GET" else request.POST.get("continue")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            login(request, form.user)
            return redirect(cont or "/")
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form, "continue": cont})

def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")
    else:
        form = SignupForm()

    return render(request, "signup.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required(login_url="/login/")
def profile_edit(request):
    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("/profile/edit/")
    else:
        form = ProfileEditForm(
            initial={
                "email": request.user.email,
                "nick": request.user.profile.nick,
            },
            user=request.user,
        )

    return render(request, "profile_edit.html", {"form": form})


@login_required(login_url="/login/")
def ask_view(request):
    if request.method == "POST":
        form = AskForm(request.POST)
        if form.is_valid():
            q = Question.objects.create(
                title=form.cleaned_data["title"],
                text=form.cleaned_data["text"],
                author=request.user.profile,
            )
            for t in form.cleaned_data["tags"]:
                tag, _ = Tag.objects.get_or_create(name=t)
                q.tags.add(tag)
            return redirect(reverse("question", kwargs={"id": q.id}))
    else:
        form = AskForm()

    return render(request, "ask.html", {"form": form})


PER_PAGE = 10

def question_view(request, id):
    question = get_object_or_404(Question, pk=id)

    answers_qs = Answer.objects.filter(question=question).order_by("id")
    paginator = Paginator(answers_qs, PER_PAGE)
    page_number = request.GET.get("page", 1)
    answers_page = paginator.get_page(page_number)

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"/login/?continue={request.path}")

        form = AnswerForm(request.POST)
        if form.is_valid():
            ans = Answer.objects.create(
                question=question,
                author=request.user.profile,
                text=form.cleaned_data["text"],
            )

            total = answers_qs.count() + 1
            new_page = math.ceil(total / PER_PAGE)
            return redirect(f"/question/{question.id}/?page={new_page}#answer-{ans.id}")
    else:
        form = AnswerForm()

    return render(request, "question.html", {
        "question": question,
        "answers": answers_page,
        "form": form,
    })