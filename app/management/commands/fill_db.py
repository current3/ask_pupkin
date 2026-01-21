import random
from faker import Faker

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from app.models import Profile, Tag, Question, Answer, QuestionLike, AnswerLike

fake = Faker()


class Command(BaseCommand):
    help = "Fill database with test data: python manage.py fill_db <ratio>"

    def add_arguments(self, parser):
        parser.add_argument("ratio", type=int)

    @transaction.atomic
    def handle(self, *args, **options):
        ratio = options["ratio"]

        users_n = ratio
        tags_n = ratio
        questions_n = ratio * 10
        answers_n = ratio * 100
        likes_n = ratio * 200

        self.stdout.write(self.style.WARNING(f"Fill DB started. ratio={ratio}"))

        # 1) Users + Profiles
        self.stdout.write("Creating users...")
        users = []
        for i in range(users_n):
            username = f"user_{i}_{fake.user_name()}"
            users.append(User(username=username))
        User.objects.bulk_create(users, batch_size=5000)

        created_users = list(User.objects.order_by("-id")[:users_n])

        profiles = [Profile(user=u, nickname=u.username) for u in created_users]
        Profile.objects.bulk_create(profiles, batch_size=5000)

        profiles = list(Profile.objects.order_by("-id")[:users_n])
        self.stdout.write(self.style.SUCCESS(f"Created users: {len(created_users)}, profiles: {len(profiles)}"))

        # 2) Tags
        self.stdout.write("Creating tags...")
        tags = [Tag(name=f"tag_{i}_{fake.word()}") for i in range(tags_n)]
        Tag.objects.bulk_create(tags, batch_size=5000, ignore_conflicts=True)

        tags = list(Tag.objects.all()[:max(1, tags_n)])
        self.stdout.write(self.style.SUCCESS(f"Tags total now: {Tag.objects.count()}"))

        # 3) Questions
        self.stdout.write("Creating questions...")
        questions = []
        for i in range(questions_n):
            author = random.choice(profiles)
            questions.append(Question(
                title=fake.sentence(nb_words=6),
                text=fake.paragraph(nb_sentences=3),
                author=author,
                rating=random.randint(-5, 50),
            ))
        Question.objects.bulk_create(questions, batch_size=5000)

        questions = list(Question.objects.order_by("-id")[:questions_n])
        self.stdout.write(self.style.SUCCESS(f"Created questions: {len(questions)}"))

        # 3.1) Add tags to questions
        # ManyToMany нельзя через bulk_create, делаем через промежуточную таблицу
        self.stdout.write("Linking tags to questions...")
        through = Question.tags.through
        links = []
        for q in questions:
            # 1-3 тега на вопрос
            for t in random.sample(tags, k=min(len(tags), random.randint(1, 3))):
                links.append(through(question_id=q.id, tag_id=t.id))
        through.objects.bulk_create(links, batch_size=10000, ignore_conflicts=True)

        # 4) Answers
        self.stdout.write("Creating answers...")
        answers = []
        for i in range(answers_n):
            answers.append(Answer(
                question=random.choice(questions),
                author=random.choice(profiles),
                text=fake.paragraph(nb_sentences=2),
                rating=random.randint(-5, 30),
                is_correct=False,
            ))
        Answer.objects.bulk_create(answers, batch_size=10000)

        answers = list(Answer.objects.order_by("-id")[:answers_n])
        self.stdout.write(self.style.SUCCESS(f"Created answers: {len(answers)}"))

        # 5) Likes (QuestionLike / AnswerLike)
        self.stdout.write("Creating likes...")
        q_likes = []
        a_likes = []

        for i in range(likes_n):
            p = random.choice(profiles)
            val = random.choice([-1, 1])

            if random.random() < 0.5:
                q = random.choice(questions)
                q_likes.append(QuestionLike(user=p, question=q, value=val))
            else:
                a = random.choice(answers)
                a_likes.append(AnswerLike(user=p, answer=a, value=val))

        QuestionLike.objects.bulk_create(q_likes, batch_size=20000, ignore_conflicts=True)
        AnswerLike.objects.bulk_create(a_likes, batch_size=20000, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS("Fill DB finished успешно ✅"))
