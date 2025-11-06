from rest_framework import serializers

from .models import MLTask


class MLTaskSerializer(serializers.ModelSerializer):
  class Meta:
    model = MLTask
    fields = '__all__'
