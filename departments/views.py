from typing import Any, Dict

from django.db.models import QuerySet, Prefetch
from rest_framework import viewsets, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db import transaction
from .models import Department
from .serializers import DepartmentSerializer, EmployeeSerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self) -> QuerySet[Department]:
        qs = super().get_queryset().prefetch_related('children')

        include = self.request.query_params.get('include_employees', 'true').lower() == 'true'
        if include:
            qs = qs.prefetch_related('employees')

        return qs

    @extend_schema(
        parameters=[
            OpenApiParameter("depth", type=int, description="Tree depth (max 5)", default=1),
            OpenApiParameter("include_employees", type=bool, description="Include employee list", default=True),
        ]
    )
    def retrieve(self, request, *args, **kwargs) -> Response:
        """
        GET /departments/{id}
        Returns department details, employees, and sub-tree up to specified depth.
        """
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=EmployeeSerializer,
        responses={201: EmployeeSerializer},
        description="Create an employee directly inside this department."
    )
    @action(detail=True, methods=['post'], url_path='employees')
    def employees(self, request, pk=None):

        department = self.get_object()
        serializer = EmployeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(department=department)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[
            OpenApiParameter("mode", type=str, enum=['cascade', 'reassign'], default='cascade'),
            OpenApiParameter("reassign_to_department_id", type=int, required=False),
        ]
    )
    def destroy(self, request:Request, *args : Any, **kwargs: Any) -> Response:

        instance = self.get_object()
        mode = request.query_params.get('mode', 'cascade')

        with transaction.atomic():
            if mode == 'reassign':
                target_id = request.query_params.get('reassign_to_department_id')
                if not target_id:
                    return Response(
                        {"error": "reassign_to_department_id is required for reassign mode"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if str(target_id) == str(instance.id):
                    return Response(
                        {"error": "reassign_to_department_id targets same department"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Ensure target department exists
                target_dept = get_object_or_404(Department, pk=target_id)
                instance.employees.all().update(department=target_dept)
                instance.children.all().update(parent=instance.parent)

            instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_context(self) -> Dict[str, Any]:
        context = super().get_serializer_context()
        context["current_lvl"] = 0
        return context
