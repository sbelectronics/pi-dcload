from django.shortcuts import render
from django.template import RequestContext, loader
import json

from dcload_control import glo_dcload

# Create your views here.

from django.http import HttpResponse


def index(request):
    template = loader.get_template('dcload_ui/index.html')
    context = RequestContext(request, {});
    return HttpResponse(template.render(context))


def setDesiredMa(request):
    value = request.GET.get("value",  "0")
    value = float(value)
    glo_dcload.set_new_desired_ma(value)

    return HttpResponse("okey dokey")


def setPower(request):
    # not implemented

    return HttpResponse("okey dokey")


def getStatus(request):
    result = {"actual_ma": glo_dcload.actual_ma,
              "actual_volts": glo_dcload.actual_volts,
              "actual_watts": glo_dcload.actual_watts,
              "actual_temp": glo_dcload.temperature,
              "desired_ma": glo_dcload.desired_ma,
              "new_desired_ma": glo_dcload.new_desired_ma,
              "power": True}

    return HttpResponse(json.dumps(result), content_type='application/javascript')
