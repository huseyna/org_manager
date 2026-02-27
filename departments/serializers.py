from .models import Department, Employee
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(trim_whitespace=True, min_length=1, max_length=200)
    position = serializers.CharField(trim_whitespace=True, min_length=1, max_length=200)

    class Meta:
        model = Employee
        fields = ['id', 'full_name', 'position', 'hired_at', 'created_at']


class DepartmentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(trim_whitespace=True, min_length=1, max_length=200)
    parent_id = serializers.PrimaryKeyRelatedField(
        source='parent', queryset=Department.objects.all(), required=False, allow_null=True,default=None
    )

    employees = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'parent_id', 'created_at', 'employees', 'children']
        validators = []

    def validate(self, data):
        name = data.get('name', self.instance.name if self.instance else None)
        parent = data.get('parent', self.instance.parent if self.instance else None)
        instance = self.instance

        queryset = Department.objects.filter(name=name, parent=parent)
        if instance:
            queryset = queryset.exclude(pk=instance.pk)

        if queryset.exists():
            raise ValidationError({
                "name": f"A department named '{name}' already exists under this parent."
            })
        if instance and parent:
            if instance.pk == parent.pk:
                raise ValidationError({"parent_id": "A department cannot be its own parent."})

            curr = parent
            while curr is not None:
                if curr.pk == instance.pk:
                    raise ValidationError({"parent_id": "Cycle detected: cannot move department into its own subtree."})
                curr = curr.parent

        return data

    def get_employees(self, obj: Department):
        request = self.context.get('request')
        include = request.query_params.get('include_employees', 'true').lower() == 'true' if request else True
        if not include:
            return None

        employees = obj.employees.all()
        return EmployeeSerializer(employees, many=True).data

    def get_children(self, obj):
        request = self.context.get('request')
        depth = int(request.query_params.get('depth', 1)) if request else 1
        depth = min(depth, 5)

        current_lvl = self.context.get('current_lvl', 0)
        if current_lvl >= depth:
            return []

        # Recurse with incremented level
        serializer = DepartmentSerializer(
            obj.children.all(),
            many=True,
            context={**self.context, 'current_lvl': current_lvl + 1}
        )
        return serializer.data
