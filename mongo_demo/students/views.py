
import json

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder

from bson import ObjectId
from bson.errors import InvalidId

from .models import Student

FIELDS = ["name", "email", "course", "age"]


def to_dict(s):
    return {
        "id": str(s.pk),
        **{f: getattr(s, f) for f in FIELDS}
    }


def read_json(request):
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


@csrf_exempt
def student_list(request):

    if request.method == "GET":
        students = Student.objects.all()
        return JsonResponse(
            [to_dict(s) for s in students],
            safe=False,
            encoder=DjangoJSONEncoder
        )

    if request.method == "POST":
        data = read_json(request)

        if not isinstance(data, dict):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        data = {k: v for k, v in data.items() if k in FIELDS}

        try:
            student = Student.objects.create(**data)
            return JsonResponse(to_dict(student), status=201)
        except (TypeError, ValidationError) as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse(
        {"error": "Method not allowed"},
        status=405
    )


@csrf_exempt
def student_detail(request, pk):

    if not ObjectId.is_valid(pk):
        return JsonResponse({"error": "Invalid student ID"}, status=400)

    try:
        student = Student.objects.get(pk=ObjectId(pk))
    except (Student.DoesNotExist, ValidationError):
        return JsonResponse({"error": "Student not found"}, status=404)

    if request.method == "GET":
        return JsonResponse(to_dict(student))

    if request.method == "PUT":
        data = read_json(request)

        if not isinstance(data, dict):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        for key, value in data.items():
            if key in FIELDS:
                setattr(student, key, value)

        try:
            student.full_clean()
            student.save()
            return JsonResponse(to_dict(student))
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)

    if request.method == "DELETE":
        student.delete()
        return JsonResponse({"deleted": True})

    return JsonResponse(
        {"error": "Method not allowed"},
        status=405
    )
