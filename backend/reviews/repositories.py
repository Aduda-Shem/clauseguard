from reviews.models import PlaybookRule


class PlaybookRepository:
    @staticmethod
    def get_active_rules():
        return list(PlaybookRule.objects.filter(active=True).order_by("order"))
