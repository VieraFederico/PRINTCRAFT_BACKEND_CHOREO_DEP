# backend/api/views/generalImports.py

# Django imports
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.conf import settings

# Django REST Framework imports
from rest_framework import status, generics 
from rest_framework.response import Response 
from rest_framework.views import APIView 
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes

from django.contrib.auth.models import User


# Other common imports
from datetime import datetime