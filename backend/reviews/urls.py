from django.urls import path

from reviews import views

urlpatterns = [
    path("health/", views.HealthView.as_view()),
    path("contracts/", views.ContractListCreateView.as_view()),
    path("contracts/<int:pk>/", views.ContractDetailView.as_view()),
    path("contracts/<int:pk>/chat/", views.ContractChatView.as_view()),
    path("contracts/<int:pk>/report.pdf", views.ContractReportPDFView.as_view()),
    path("playbook/", views.PlaybookListView.as_view()),
]
