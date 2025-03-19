from django.urls import path
from page.views import Payment, ResultView

app_name = 'page'  

urlpatterns = [
    path('payment/', Payment.as_view(), name='payment'),
    path('result/', ResultView.as_view(), name='result'),
]
