from rest_framework import serializers
from .models import File, Folder
from django.conf import settings


class FileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_path = serializers.SerializerMethodField()
    parent_folder_name = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ('id', 'file', 'file_url', 'file_name', 'file_path', 'original_filename', 
                 'upload_method', 'uploaded_at', 'file_size', 'parent_folder', 'parent_folder_name')
        read_only_fields = ('id', 'uploaded_at', 'file_size', 'file_url', 'file_name', 'file_path', 'parent_folder_name')

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

    def get_file_name(self, obj):
        if obj.file:
            return obj.file.name.split('/')[-1]
        return obj.original_filename

    def get_file_path(self, obj):
        return obj.get_path()

    def get_parent_folder_name(self, obj):
        return obj.parent_folder.name if obj.parent_folder else None

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('file', 'upload_method', 'parent_folder')

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


class FolderSerializer(serializers.ModelSerializer):
    folder_path = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    subfolders_count = serializers.SerializerMethodField()
    files_count = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = ('id', 'name', 'parent', 'parent_name', 'folder_path', 
                 'created_at', 'updated_at', 'subfolders_count', 'files_count')
        read_only_fields = ('id', 'created_at', 'updated_at', 'folder_path', 
                           'parent_name', 'subfolders_count', 'files_count')

    def get_folder_path(self, obj):
        return obj.get_path()

    def get_parent_name(self, obj):
        return obj.parent.name if obj.parent else None

    def get_subfolders_count(self, obj):
        return obj.subfolders.count()

    def get_files_count(self, obj):
        return obj.files.count()

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class FolderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ('name', 'parent')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)