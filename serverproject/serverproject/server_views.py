from django.http import HttpResponse

def home():
    return HttpResponse("Hello, Django!")