import logging

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from reviews.models import Contract
from reviews.serializers import ContractListSerializer, ContractSerializer
from reviews.services.brain import ContractBrain
from reviews.services.parsing import UnreadableFile, UnsupportedFileType, extract_text
from reviews.views.mixins import ContractOwnedMixin

logger = logging.getLogger(__name__)


class ContractListCreateView(APIView):
    def get(self, request):
        contracts = Contract.objects.filter(owner=request.user)
        return Response(ContractListSerializer(contracts, many=True).data)

    def post(self, request):
        upload = request.FILES.get("file")

        if upload:
            filename = upload.name
            raw_bytes = upload.read()
            try:
                text = extract_text(filename, raw_bytes)
            except (UnsupportedFileType, UnreadableFile) as exc:
                return Response({"detail": str(exc)}, status=400)
        else:
            text = (request.data.get("text") or "").strip()
            filename = request.data.get("filename", "pasted-contract.txt")
            if not text:
                return Response(
                    {"detail": "Provide either a 'file' upload or non-empty 'text' field."},
                    status=400,
                )

        if len(text) > settings.MAX_UPLOAD_CHARS:
            return Response(
                {
                    "detail": (
                        f"Contract text is too long ({len(text):,} characters, limit "
                        f"{settings.MAX_UPLOAD_CHARS:,}). Split it or contact the operator."
                    )
                },
                status=400,
            )

        contract = Contract.objects.create(owner=request.user, filename=filename, source_text=text)

        try:
            ContractBrain(contract).review()
        except Exception:
            logger.exception("Review failed for contract %s", contract.id)
            contract.status = Contract.Status.FAILED
            contract.error_message = (
                "Something went wrong while analyzing this contract. It has been saved -- "
                "contact the operator with this reference: "
                f"contract #{contract.id}."
            )
            contract.save(update_fields=["status", "error_message"])
            return Response(ContractSerializer(contract).data, status=502)

        contract.refresh_from_db()
        return Response(ContractSerializer(contract).data, status=201)


class ContractDetailView(ContractOwnedMixin, APIView):
    def get(self, request, pk):
        return Response(ContractSerializer(self.get_contract(request, pk)).data)

    def delete(self, request, pk):
        self.get_contract(request, pk).delete()
        return Response(status=204)
