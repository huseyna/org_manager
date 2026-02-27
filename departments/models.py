from django.db import models
from django.db.models import UniqueConstraint

class Department(models.Model):
    name = models.CharField(max_length=200)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            # Requirement: Unique name within the same parent
            UniqueConstraint(fields=['name', 'parent'], name='unique_name_per_parent'),
            # Handles root departments (where parent is null)
            UniqueConstraint(fields=['name'], condition=models.Q(parent__isnull=True), name='unique_root_name')
        ]

    def __str__(self) -> str:
        return self.name

class Employee(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='employees')
    full_name = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    hired_at = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['full_name','created_at']
    def __str__(self) -> str:
        return self.full_name
