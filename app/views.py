from django.shortcuts import render
from django.http import Http404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

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


fake_questions = [
    {
        "id": i,
        "title": f"Title {i}",
        "text": f"Text of question {i}",
        "tags": ["python", "django", "linux"][: (i % 3) + 1]
    }
    for i in range(1, 100)
]

fake_answers = [
    {
        "id": i,
        "text": f"Answer text {i}"
    }
    for i in range(1, 10)
]

def new_questions(request):
    page = paginate(fake_questions, request, per_page=20)
    return render(request, "index.html", {"questions": page})

def hot_questions(request):
    hot = list(reversed(fake_questions))
    page = paginate(hot, request, per_page=20)
    return render(request, "index.html", {"questions": page})

def tag_questions(request, tag):
    filtered = [q for q in fake_questions if tag in q["tags"]]
    if not filtered:
        raise Http404("Тег не найден")

    page = paginate(filtered, request, per_page=20)
    return render(request, "index.html", {"questions": page, "tag": tag})

def question(request, qid):
    q = next((q for q in fake_questions if q["id"] == qid), None)

    if q is None:
        raise Http404("Вопрос не найден")

    page = paginate(fake_answers, request, per_page=10)

    return render(request, "question.html", {
        "question": q,
        "answers": page
    })


def login_view(request):
    return render(request, "login.html")

def signup_view(request):
    return render(request, "signup.html")

def ask_view(request):
    return render(request, "ask.html")

def profile_view(request):
    return render(request, "profile.html")
