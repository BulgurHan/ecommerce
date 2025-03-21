from django.urls import path
from page.views import  ResultView

app_name = 'page'  

urlpatterns = [
    path('result/', ResultView.as_view(), name='result'),
]
