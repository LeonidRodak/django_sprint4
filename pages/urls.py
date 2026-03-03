from django.urls import path
from .views import AboutView, RulesView

app_name = 'pages'  # namespace

urlpatterns = [
    path('about/', AboutView.as_view(), name='about'),
    path('rules/', RulesView.as_view(), name='rules'),
]
