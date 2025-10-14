from rest_framework import serializers
from .models import File
from django.conf import settings


class FileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ('id', 'file', 'file_url', 'file_name', 'original_filename', 
                 'upload_method', 'uploaded_at', 'file_size')
        read_only_fields = ('id', 'uploaded_at', 'file_size', 'file_url', 'file_name')

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

    def get_file_name(self, obj):
        if obj.file:
            return obj.file.name.split('/')[-1]
        return obj.original_filename

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('file', 'upload_method')

    def validate_file(self, file):
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE_BYTES', None)
        if max_size is not None and file.size > max_size:
            raise serializers.ValidationError(
                f'文件过大，最大允许 {int(max_size / (1024 * 1024 * 1024))}GB'
            )
        return file

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        if validated_data.get('file'):
            validated_data['original_filename'] = validated_data['file'].name
        return super().create(validated_data)