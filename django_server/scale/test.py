from django.http import HttpResponse
import os

def test_rest(request):
    param = request.GET.get("param")
    response = "your parameter is %s" % param
    return HttpResponse(response, content_type="text/plain")
