from rest_framework.response import Response
from rest_framework.views import APIView

from reviews.models import ChatMessage, Contract
from reviews.serializers import ChatMessageSerializer
from reviews.services.brain import ContractBrain
from reviews.views.mixins import ContractOwnedMixin

MAX_QUESTION_CHARS = 2000


class ContractChatView(ContractOwnedMixin, APIView):
    def get(self, request, pk):
        contract = self.get_contract(request, pk)
        messages = ChatMessage.objects.filter(contract=contract)
        return Response(ChatMessageSerializer(messages, many=True).data)

    def post(self, request, pk):
        contract = self.get_contract(request, pk)
        if contract.status != Contract.Status.COMPLETE:
            return Response({"detail": "This contract hasn't finished reviewing yet."}, status=400)

        question = (request.data.get("question") or "").strip()
        if not question:
            return Response({"detail": "Provide a non-empty 'question'."}, status=400)
        if len(question) > MAX_QUESTION_CHARS:
            return Response(
                {"detail": f"Question is too long (limit {MAX_QUESTION_CHARS} characters)."}, status=400
            )

        user_message, assistant_message = ContractBrain(contract).ask(question)
        return Response(
            {
                "user_message": ChatMessageSerializer(user_message).data,
                "assistant_message": ChatMessageSerializer(assistant_message).data,
            },
            status=201,
        )
