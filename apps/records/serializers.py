"""
Financial Record Serializers

FinancialRecordSerializer   — full read/write for Admin
FinancialRecordReadSerializer — safe read-only for Analyst/Viewer
"""

from rest_framework import serializers
from .models import FinancialRecord


class FinancialRecordSerializer(serializers.ModelSerializer):
    """
    Full serializer used for creating and updating records.
    `created_by` is set automatically from request.user.
    """
    created_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = FinancialRecord
        fields = [
            'id', 'amount', 'type', 'category', 'date', 'notes',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_by_name', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        return obj.created_by.full_name if obj.created_by else None

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be a positive number.")
        return value

    def validate_type(self, value):
        valid = [t.value for t in FinancialRecord.TransactionType]
        if value not in valid:
            raise serializers.ValidationError(f"Type must be one of: {', '.join(valid)}.")
        return value

    def validate_category(self, value):
        valid = [c.value for c in FinancialRecord.Category]
        if value not in valid:
            raise serializers.ValidationError(
                f"Invalid category. Choose from: {', '.join(valid)}."
            )
        return value

    def create(self, validated_data):
        # Attach the requesting user as the owner
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class FinancialRecordReadSerializer(serializers.ModelSerializer):
    """Lightweight read-only view exposed to Viewer/Analyst roles."""
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model  = FinancialRecord
        fields = [
            'id', 'amount', 'type', 'category', 'date', 'notes',
            'created_by_name', 'created_at',
        ]

    def get_created_by_name(self, obj):
        return obj.created_by.full_name if obj.created_by else None
