from rest_framework.response import Response
from rest_framework.views import APIView

from reviews.repositories import PlaybookRepository
from reviews.serializers import PlaybookRuleSerializer


class PlaybookListView(APIView):
    def get(self, request):
        rules = PlaybookRepository.get_active_rules()
        return Response(PlaybookRuleSerializer(rules, many=True).data)
