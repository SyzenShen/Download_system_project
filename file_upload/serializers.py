from rest_framework import serializers
from .models import File, Folder
from django.conf import settings


class FileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_path = serializers.SerializerMethodField()
    parent_folder_name = serializers.SerializerMethodField()
    tags_list = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ('id', 'file', 'file_url', 'file_name', 'file_path', 'original_filename', 
                 'upload_method', 'uploaded_at', 'file_size', 'parent_folder', 'parent_folder_name',
                 # 新增元数据字段
                 'title', 'project', 'uploader', 'file_format', 'document_type', 'access_level',
                 'organism', 'experiment_type', 'tags', 'tags_list', 'description', 'checksum', 
                 'qc_status', 'extracted_metadata')
        read_only_fields = ('id', 'uploaded_at', 'file_size', 'file_url', 'file_name', 'file_path', 
                           'parent_folder_name', 'checksum', 'extracted_metadata', 'tags_list')

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
    
    def get_tags_list(self, obj):
        """将标签字符串转换为列表"""
        if obj.tags:
            return [tag.strip() for tag in obj.tags.split(',') if tag.strip()]
        return []

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class FileUploadSerializer(serializers.ModelSerializer):
    # 重新定义字段以允许空白值
    title = serializers.CharField(allow_blank=True, required=False)
    project = serializers.CharField(allow_blank=True, required=False)
    file_format = serializers.CharField(allow_blank=True, required=False)
    document_type = serializers.CharField(allow_blank=True, required=False)
    access_level = serializers.CharField(allow_blank=True, required=False)
    
    class Meta:
        model = File
        fields = ('file', 'upload_method', 'parent_folder', 
                 # 必填元数据字段
                 'title', 'project', 'file_format', 'document_type', 'access_level',
                 # 可选元数据字段
                 'organism', 'experiment_type', 'tags', 'description')

    def validate_file(self, file):
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE_BYTES', None)
        if max_size is not None and file.size > max_size:
            raise serializers.ValidationError(
                f'文件过大，最大允许 {int(max_size / (1024 * 1024 * 1024))}GB'
            )
        return file
    
    def validate_title(self, value):
        """验证标题字段，空字符串时提供默认值"""
        if not value or value.strip() == '':
            return '未命名文件'
        return value
    
    def validate_project(self, value):
        """验证项目字段，空字符串时提供默认值"""
        if not value or value.strip() == '':
            return '默认项目'
        return value
    
    def validate_file_format(self, value):
        """验证文件格式字段，空字符串时提供默认值"""
        if not value or value.strip() == '':
            return 'other'
        return value
    
    def validate_document_type(self, value):
        """验证文档类型字段，空字符串时提供默认值"""
        if not value or value.strip() == '':
            return 'Dataset'
        return value
    
    def validate_access_level(self, value):
        """验证访问级别字段，空字符串时提供默认值"""
        if not value or value.strip() == '':
            return 'Internal'
        return value
    
    def validate(self, data):
        """验证必填字段并提供默认值"""
        # 为必填字段提供默认值，避免空字符串导致验证失败
        if not data.get('title'):
            data['title'] = data.get('file').name if data.get('file') else '未命名文件'
        
        if not data.get('project'):
            data['project'] = '默认项目'
            
        if not data.get('file_format'):
            # 从文件扩展名推断格式
            if data.get('file'):
                filename = data['file'].name
                ext = filename.split('.')[-1].lower() if '.' in filename else ''
                # 映射常见扩展名到格式
                format_mapping = {
                    'txt': 'TXT', 'csv': 'CSV', 'json': 'JSON', 'xml': 'XML',
                    'pdf': 'PDF', 'doc': 'DOC', 'docx': 'DOCX', 'xls': 'XLS', 'xlsx': 'XLSX',
                    'jpg': 'JPG', 'jpeg': 'JPG', 'png': 'PNG', 'gif': 'GIF',
                    'mp4': 'MP4', 'avi': 'AVI', 'mov': 'MOV',
                    'zip': 'ZIP', 'tar': 'TAR', 'gz': 'GZ'
                }
                data['file_format'] = format_mapping.get(ext, 'OTHER')
            else:
                data['file_format'] = 'OTHER'
            
        if not data.get('document_type'):
            data['document_type'] = 'Dataset'
            
        if not data.get('access_level'):
            data['access_level'] = 'Internal'
            
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        if validated_data.get('file'):
            validated_data['original_filename'] = validated_data['file'].name
        
        # 创建文件对象
        file_obj = super().create(validated_data)
        
        # 异步提取元数据
        self._extract_metadata_async(file_obj)
        
        return file_obj
    
    def _extract_metadata_async(self, file_obj):
        """异步提取文件元数据"""
        try:
            from .metadata_extractor import extract_file_metadata
            
            if file_obj.file and file_obj.file_format:
                metadata = extract_file_metadata(file_obj.file.path, file_obj.file_format)
                if metadata:
                    file_obj.extracted_metadata = metadata
                    
                    # 如果没有手动填写物种信息，尝试从提取的元数据中获取
                    if not file_obj.organism and 'detected_organism' in metadata:
                        file_obj.organism = metadata['detected_organism']
                    
                    # 更新描述信息
                    if not file_obj.description and 'detected_keywords' in metadata:
                        keywords = metadata['detected_keywords']
                        if keywords:
                            file_obj.description = f"检测到的关键词: {', '.join(keywords[:5])}"
                    
                    file_obj.save()
        except Exception as e:
            # 记录错误但不影响文件上传
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"元数据提取失败 {file_obj.id}: {e}")


class FolderSerializer(serializers.ModelSerializer):
    folder_path = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    subfolders_count = serializers.SerializerMethodField()
    files_count = serializers.SerializerMethodField()
    folder_size = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = ('id', 'name', 'parent', 'parent_name', 'folder_path', 
                 'created_at', 'updated_at', 'subfolders_count', 'files_count', 'folder_size')
        read_only_fields = ('id', 'created_at', 'updated_at', 'folder_path', 
                           'parent_name', 'subfolders_count', 'files_count', 'folder_size')

    def get_folder_path(self, obj):
        return obj.get_path()

    def get_parent_name(self, obj):
        return obj.parent.name if obj.parent else None

    def get_subfolders_count(self, obj):
        return obj.subfolders.count()

    def get_files_count(self, obj):
        return obj.files.count()

    def get_folder_size(self, obj):
        """计算文件夹总大小（包括子文件夹）"""
        def calculate_folder_size(folder):
            # 计算当前文件夹中所有文件的大小
            files_size = sum(file.file_size or 0 for file in folder.files.all())
            
            # 递归计算子文件夹的大小
            subfolders_size = sum(calculate_folder_size(subfolder) for subfolder in folder.subfolders.all())
            
            return files_size + subfolders_size
        
        return calculate_folder_size(obj)

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