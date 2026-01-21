from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from .models import Question, Tag


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


def question(request, qid):
    q = get_object_or_404(Question, pk=qid)
    answers = q.answers.all()
    page = paginate(answers, request, per_page=10)

    return render(request, "question.html", {
        "question": q,
        "answers": page
    })
