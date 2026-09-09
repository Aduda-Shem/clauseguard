from django.http import HttpResponse
from django.utils.text import get_valid_filename
from rest_framework.views import APIView

from reviews.models import Contract
from reviews.services.report_pdf import build_review_pdf
from reviews.views.mixins import ContractOwnedMixin


class ContractReportPDFView(ContractOwnedMixin, APIView):
    def get(self, request, pk):
        contract = self.get_contract(request, pk)
        if contract.status != Contract.Status.COMPLETE or not hasattr(contract, "review_result"):
            return HttpResponse(
                "This contract hasn't finished reviewing yet.", status=400, content_type="text/plain"
            )

        pdf_bytes = build_review_pdf(contract)
        stem = (contract.filename or f"contract-{contract.id}").rsplit(".", 1)[0]
        safe_stem = get_valid_filename(stem) or f"contract-{contract.id}"

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="ClauseGuard-{safe_stem}.pdf"'
        return response
