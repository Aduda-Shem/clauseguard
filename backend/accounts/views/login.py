from knox.views import LoginView as KnoxLoginView
from rest_framework.permissions import AllowAny

from accounts.serializers import LoginSerializer


class LoginView(KnoxLoginView):
    permission_classes = (AllowAny,)
    authentication_classes = []

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user = serializer.validated_data["user"]
        return super().post(request, format=None)
