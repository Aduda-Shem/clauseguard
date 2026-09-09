from django.shortcuts import get_object_or_404

from reviews.models import Contract


class ContractOwnedMixin:
    def get_contract(self, request, pk):
        return get_object_or_404(Contract, pk=pk, owner=request.user)
