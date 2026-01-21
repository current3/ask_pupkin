import math

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db import models

from django.conf import settings
from django.template.loader import render_to_string

from .centrifugo import make_centrifugo_token, centrifugo_publish
from .forms import AnswerForm, AskForm, LoginForm, ProfileEditForm, SignupForm
from .models import Answer, Question, Tag, QuestionLike, AnswerLike

from django.db.models import Q

def search_suggest(request):
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    qs = Question.objects.all()

    qs = qs.filter(Q(title__icontains=q) | Q(text__icontains=q)).order_by("-rating")[:10]

    results = [{"id": obj.id, "title": obj.title} for obj in qs]
    return JsonResponse({"results": results})

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

    answers_qs = (
        Answer.objects.filter(question=question)
        .select_related("author", "author__user")
        .order_by("id")
    )

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

            html = render_to_string(
                "partials/answer_item.html",
                {"answer": ans},
                request=request,
            )
            centrifugo_publish(
                channel=f"question:{question.id}",
                data={"html": html, "answer_id": ans.id},
            )

            total = answers_qs.count() + 1 
            new_page = math.ceil(total / PER_PAGE)
            return redirect(f"/question/{question.id}/?page={new_page}#answer-{ans.id}")
    else:
        form = AnswerForm()

    user_id = request.user.profile.id if request.user.is_authenticated else 0

    return render(
        request,
        "question.html",
        {
            "question": question,
            "answers": answers_page,
            "form": form,

            "centrifugo_ws_url": settings.CENTRIFUGO_WS_URL,
            "centrifugo_token": make_centrifugo_token(user_id),
            "centrifugo_channel": f"question:{question.id}",
        },
    )


@require_POST
@login_required(login_url="/login/")
def ajax_question_vote(request):
    qid = request.POST.get("id")
    vtype = request.POST.get("type")

    if not qid:
        return JsonResponse({"error": "no_id"}, status=400)
    if vtype not in ("like", "dislike"):
        return JsonResponse({"error": "bad_type"}, status=400)

    question = get_object_or_404(Question, pk=qid)
    value = 1 if vtype == "like" else -1

    QuestionLike.objects.update_or_create(
        user=request.user.profile,
        question=question,
        defaults={"value": value},
    )

    rating = (
        QuestionLike.objects.filter(question=question)
        .aggregate(s=models.Sum("value"))["s"]
        or 0
    )

    question.rating = rating
    question.save(update_fields=["rating"])

    return JsonResponse({"rating": rating})


@require_POST
@login_required(login_url="/login/")
def ajax_answer_vote(request):
    aid = request.POST.get("id")
    vtype = request.POST.get("type")

    if not aid:
        return JsonResponse({"error": "no_id"}, status=400)
    if vtype not in ("like", "dislike"):
        return JsonResponse({"error": "bad_type"}, status=400)

    answer = get_object_or_404(Answer, pk=aid)
    value = 1 if vtype == "like" else -1

    AnswerLike.objects.update_or_create(
        user=request.user.profile,
        answer=answer,
        defaults={"value": value},
    )

    rating = (
        AnswerLike.objects.filter(answer=answer)
        .aggregate(s=models.Sum("value"))["s"]
        or 0
    )

    answer.rating = rating
    answer.save(update_fields=["rating"])

    return JsonResponse({"rating": rating})


@require_POST
@login_required(login_url="/login/")
def ajax_set_correct(request):
    qid = request.POST.get("question_id")
    aid = request.POST.get("answer_id")

    if not qid or not aid:
        return JsonResponse({"error": "bad_ids"}, status=400)

    question = get_object_or_404(Question, pk=qid)

    if question.author_id != request.user.profile.id:
        return JsonResponse({"error": "forbidden"}, status=403)

    answer = get_object_or_404(Answer, pk=aid, question=question)

    with transaction.atomic():
        if answer.is_correct:
            answer.is_correct = False
            answer.save(update_fields=["is_correct"])
            return JsonResponse({"ok": True, "answer_id": answer.id, "is_correct": False})

        Answer.objects.filter(question=question, is_correct=True).update(is_correct=False)
        answer.is_correct = True
        answer.save(update_fields=["is_correct"])

    return JsonResponse({"ok": True, "answer_id": answer.id, "is_correct": True})
