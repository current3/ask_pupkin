from datetime import timedelta

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count, Sum

from app.models import Tag, Question, Answer, Profile


class Command(BaseCommand):
    help = "Fill cache for popular tags and best members"

    def handle(self, *args, **options):
        now = timezone.now()

        since_3m = now - timedelta(days=90)

        popular_tags = (
            Tag.objects
            .filter(questions__created_at__gte=since_3m)
            .annotate(q_cnt=Count("questions"))
            .order_by("-q_cnt", "name")[:10]
        )
        cache.set("popular_tags", list(popular_tags))

        since_1w = now - timedelta(days=7)

        q_scores = (
            Question.objects
            .filter(created_at__gte=since_1w)
            .values("author_id")
            .annotate(score=Sum("rating"))
        )
        q_map = {row["author_id"]: (row["score"] or 0) for row in q_scores}

        a_scores = (
            Answer.objects
            .filter(created_at__gte=since_1w)
            .values("author_id")
            .annotate(score=Sum("rating"))
        )
        a_map = {row["author_id"]: (row["score"] or 0) for row in a_scores}

        author_ids = set(q_map.keys()) | set(a_map.keys())
        totals = []
        for aid in author_ids:
            totals.append((aid, q_map.get(aid, 0) + a_map.get(aid, 0)))

        totals.sort(key=lambda x: x[1], reverse=True)
        top_ids = [aid for aid, _ in totals[:10]]

        best_members = list(Profile.objects.filter(id__in=top_ids))
        best_members.sort(key=lambda p: top_ids.index(p.id) if p.id in top_ids else 999)

        cache.set("best_members", best_members)

        self.stdout.write(self.style.SUCCESS("Cache filled: popular_tags, best_members"))
