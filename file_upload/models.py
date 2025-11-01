from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import os
import uuid

User = get_user_model()

# Create your models here.
# Define user directory path


def generate_session_id():
    """生成唯一的会话ID"""
    return uuid.uuid4().hex


def user_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid.uuid4().hex[:10], ext)
    return os.path.join("files", str(instance.user.id), filename)


class Folder(models.Model):
    """文件夹模型，支持层级结构"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=255, verbose_name="文件夹名称")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        # 确保同一用户在同一父目录下不能有重名文件夹
        unique_together = ['user', 'parent', 'name']

    def clean(self):
        """验证文件夹不能成为自己的子文件夹（防止循环引用）"""
        if self.parent:
            current = self.parent
            while current:
                if current == self:
                    raise ValidationError("文件夹不能成为自己的子文件夹")
                current = current.parent

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_path(self):
        """获取文件夹的完整路径"""
        path_parts = []
        current = self
        while current:
            path_parts.append(current.name)
            current = current.parent
        return '/'.join(reversed(path_parts))

    def get_all_subfolders(self):
        """递归获取所有子文件夹"""
        subfolders = list(self.subfolders.all())
        for subfolder in self.subfolders.all():
            subfolders.extend(subfolder.get_all_subfolders())
        return subfolders

    def __str__(self):
        return f"{self.get_path()} - {self.user.username}"


class File(models.Model):
    # 文档类型选择
    DOCUMENT_TYPE_CHOICES = [
        ('Paper', 'Paper'),
        ('Protocol', 'Protocol'),
        ('Dataset', 'Dataset'),
        ('Code', 'Code'),
    ]
    
    # 文件格式选择
    FILE_FORMAT_CHOICES = [
        # 生物信息学格式
        ('FASTQ', 'FASTQ'),
        ('FASTA', 'FASTA'),
        ('VCF', 'VCF'),
        ('BAM', 'BAM'),
        ('SAM', 'SAM'),
        ('BED', 'BED'),
        ('GTF', 'GTF'),
        ('GFF', 'GFF'),
        
        # 文档格式
        ('PDF', 'PDF'),
        ('DOC', 'Word Document'),
        ('DOCX', 'Word Document'),
        ('PPT', 'PowerPoint'),
        ('PPTX', 'PowerPoint'),
        ('RTF', 'Rich Text Format'),
        
        # 数据格式
        ('CSV', 'CSV'),
        ('TSV', 'TSV'),
        ('XLS', 'Excel'),
        ('XLSX', 'Excel'),
        ('JSON', 'JSON'),
        ('XML', 'XML'),
        ('YAML', 'YAML'),
        ('SQL', 'SQL'),
        
        # 代码格式
        ('py', 'Python'),
        ('ipynb', 'Jupyter Notebook'),
        ('R', 'R Script'),
        ('Rmd', 'R Markdown'),
        ('js', 'JavaScript'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('c', 'C'),
        ('sh', 'Shell Script'),
        ('pl', 'Perl'),
        ('php', 'PHP'),
        ('rb', 'Ruby'),
        ('go', 'Go'),
        ('rs', 'Rust'),
        ('swift', 'Swift'),
        ('kt', 'Kotlin'),
        ('scala', 'Scala'),
        
        # 文本格式
        ('txt', 'Text'),
        ('md', 'Markdown'),
        ('log', 'Log File'),
        ('conf', 'Configuration'),
        ('ini', 'INI File'),
        ('cfg', 'Config File'),
        
        # 图像格式
        ('jpg', 'JPEG Image'),
        ('jpeg', 'JPEG Image'),
        ('png', 'PNG Image'),
        ('gif', 'GIF Image'),
        ('bmp', 'BMP Image'),
        ('tiff', 'TIFF Image'),
        ('svg', 'SVG Image'),
        ('webp', 'WebP Image'),
        ('ico', 'Icon'),
        
        # 音频格式
        ('mp3', 'MP3 Audio'),
        ('wav', 'WAV Audio'),
        ('flac', 'FLAC Audio'),
        ('aac', 'AAC Audio'),
        ('ogg', 'OGG Audio'),
        ('m4a', 'M4A Audio'),
        
        # 视频格式
        ('mp4', 'MP4 Video'),
        ('avi', 'AVI Video'),
        ('mov', 'MOV Video'),
        ('wmv', 'WMV Video'),
        ('flv', 'FLV Video'),
        ('mkv', 'MKV Video'),
        ('webm', 'WebM Video'),
        ('m4v', 'M4V Video'),
        
        # 压缩格式
        ('zip', 'ZIP Archive'),
        ('rar', 'RAR Archive'),
        ('7z', '7-Zip Archive'),
        ('tar', 'TAR Archive'),
        ('gz', 'GZIP Archive'),
        ('bz2', 'BZIP2 Archive'),
        ('xz', 'XZ Archive'),
        
        # 其他格式
        ('other', 'Other'),
    ]
    
    # 实验类型选择
    EXPERIMENT_TYPE_CHOICES = [
        ('RNA-seq', 'RNA-seq'),
        ('WGS', 'Whole Genome Sequencing'),
        ('scRNA-seq', 'Single Cell RNA-seq'),
        ('MS', 'Mass Spectrometry'),
        ('ChIP-seq', 'ChIP-seq'),
        ('ATAC-seq', 'ATAC-seq'),
        ('other', 'Other'),
    ]
    
    # 访问级别选择
    ACCESS_LEVEL_CHOICES = [
        ('Public', 'Public'),
        ('Internal', 'Internal'),
        ('Restricted', 'Restricted'),
    ]
    
    # QC状态选择
    QC_STATUS_CHOICES = [
        ('unknown', 'Unknown'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]

    # 原有字段
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to=user_directory_path, null=True)
    upload_method = models.CharField(max_length=50, verbose_name="Upload Method")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(default=0)
    original_filename = models.CharField(max_length=255, blank=True)
    parent_folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True, related_name='files')
    
    # 新增元数据字段 - 必填字段
    title = models.CharField(max_length=500, default="", verbose_name="文件标题", help_text="文件的描述性标题")
    project = models.CharField(max_length=200, default="", verbose_name="项目名称", help_text="项目名或课题号")
    uploader = models.CharField(max_length=100, default="", verbose_name="上传者", help_text="上传者姓名")
    file_format = models.CharField(max_length=20, choices=FILE_FORMAT_CHOICES, default='other', verbose_name="文件格式")
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='Dataset', verbose_name="文档类型")
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVEL_CHOICES, default='Internal', verbose_name="访问级别")
    
    # 新增元数据字段 - 可选/自动填充字段
    organism = models.CharField(max_length=200, blank=True, verbose_name="物种", help_text="如 Homo sapiens")
    experiment_type = models.CharField(max_length=50, choices=EXPERIMENT_TYPE_CHOICES, blank=True, verbose_name="实验类型")
    tags = models.TextField(blank=True, verbose_name="标签", help_text="用逗号分隔的标签")
    description = models.TextField(blank=True, verbose_name="描述", help_text="文件详细描述")
    checksum = models.CharField(max_length=64, blank=True, verbose_name="校验和", help_text="文件MD5校验和")
    qc_status = models.CharField(max_length=20, choices=QC_STATUS_CHOICES, default='unknown', verbose_name="质控状态")
    
    # 自动提取的元数据
    extracted_metadata = models.JSONField(default=dict, blank=True, verbose_name="提取的元数据", help_text="从文件自动提取的元数据")
    
    # 全文搜索字段（PostgreSQL tsvector，如果使用SQLite则为普通文本）
    search_vector = models.TextField(blank=True, verbose_name="搜索向量", help_text="用于全文搜索的文本")

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            if not self.original_filename:
                self.original_filename = self.file.name
            
            # 自动推断文件格式
            if not self.file_format or self.file_format == 'other':
                self.file_format = self._detect_file_format()
            
            # 计算文件校验和
            if not self.checksum:
                self.checksum = self._calculate_checksum()
        
        # 自动填充上传者
        if not self.uploader and self.user:
            self.uploader = self.user.get_full_name() or self.user.username
        
        # 更新搜索向量
        self._update_search_vector()
        
        super().save(*args, **kwargs)
    
    def _detect_file_format(self):
        """根据文件扩展名自动检测文件格式"""
        if not self.original_filename:
            return 'other'
        
        ext = self.original_filename.lower().split('.')[-1]
        format_mapping = {
            # 生物信息学格式
            'fastq': 'FASTQ',
            'fq': 'FASTQ',
            'fasta': 'FASTA',
            'fa': 'FASTA',
            'vcf': 'VCF',
            'bam': 'BAM',
            'sam': 'SAM',
            'bed': 'BED',
            'gtf': 'GTF',
            'gff': 'GFF',
            
            # 文档格式
            'pdf': 'PDF',
            'doc': 'DOC',
            'docx': 'DOCX',
            'ppt': 'PPT',
            'pptx': 'PPTX',
            'rtf': 'RTF',
            
            # 数据格式
            'csv': 'CSV',
            'tsv': 'TSV',
            'xls': 'XLS',
            'xlsx': 'XLSX',
            'json': 'JSON',
            'xml': 'XML',
            'yaml': 'YAML',
            'yml': 'YAML',
            'sql': 'SQL',
            
            # 代码格式
            'py': 'py',
            'ipynb': 'ipynb',
            'r': 'R',
            'rmd': 'Rmd',
            'js': 'js',
            'html': 'html',
            'htm': 'html',
            'css': 'css',
            'java': 'java',
            'cpp': 'cpp',
            'cxx': 'cpp',
            'cc': 'cpp',
            'c': 'c',
            'h': 'c',
            'hpp': 'cpp',
            'sh': 'sh',
            'bash': 'sh',
            'zsh': 'sh',
            'pl': 'pl',
            'php': 'php',
            'rb': 'rb',
            'go': 'go',
            'rs': 'rs',
            'swift': 'swift',
            'kt': 'kt',
            'scala': 'scala',
            
            # 文本格式
            'txt': 'txt',
            'md': 'md',
            'markdown': 'md',
            'log': 'log',
            'conf': 'conf',
            'config': 'conf',
            'ini': 'ini',
            'cfg': 'cfg',
            
            # 图像格式
            'jpg': 'jpg',
            'jpeg': 'jpeg',
            'png': 'png',
            'gif': 'gif',
            'bmp': 'bmp',
            'tiff': 'tiff',
            'tif': 'tiff',
            'svg': 'svg',
            'webp': 'webp',
            'ico': 'ico',
            
            # 音频格式
            'mp3': 'mp3',
            'wav': 'wav',
            'flac': 'flac',
            'aac': 'aac',
            'ogg': 'ogg',
            'm4a': 'm4a',
            
            # 视频格式
            'mp4': 'mp4',
            'avi': 'avi',
            'mov': 'mov',
            'wmv': 'wmv',
            'flv': 'flv',
            'mkv': 'mkv',
            'webm': 'webm',
            'm4v': 'm4v',
            
            # 压缩格式
            'zip': 'zip',
            'rar': 'rar',
            '7z': '7z',
            'tar': 'tar',
            'gz': 'gz',
            'bz2': 'bz2',
            'xz': 'xz',
        }
        return format_mapping.get(ext, 'other')
    
    def _calculate_checksum(self):
        """计算文件MD5校验和"""
        import hashlib
        if not self.file:
            return ''
        
        try:
            hash_md5 = hashlib.md5()
            for chunk in self.file.chunks():
                hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ''
    
    def _update_search_vector(self):
        """更新搜索向量，用于全文搜索"""
        search_content = ' '.join(filter(None, [
            self.title or '',
            self.description or '',
            self.tags or '',
            self.project or '',
            self.organism or '',
            self.original_filename or '',
            self.uploader or '',
        ]))
        self.search_vector = search_content.lower()

    def get_path(self):
        """获取文件的完整路径"""
        if self.parent_folder:
            return f"{self.parent_folder.get_path()}/{self.original_filename}"
        return self.original_filename

    def __str__(self):
        return f"{self.get_path()} - {self.user.username}"

    class Meta:
        ordering = ['-uploaded_at']
        # 确保同一用户在同一文件夹下不能有重名文件
        unique_together = ['user', 'parent_folder', 'original_filename']


class UploadSession(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    )

    session_id = models.CharField(max_length=64, unique=True, default=generate_session_id)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upload_sessions')
    original_filename = models.CharField(max_length=255)
    total_size = models.BigIntegerField(default=0)
    chunk_size = models.IntegerField(default=2 * 1024 * 1024)  # 2MB 默认分片
    uploaded_size = models.BigIntegerField(default=0)
    temp_path = models.CharField(max_length=512)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    parent_folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True, related_name='upload_sessions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.session_id} ({self.original_filename}) - {self.status}"