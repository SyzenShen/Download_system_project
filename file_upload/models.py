from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import os
import uuid

User = get_user_model()

# Create your models here.
# Define user directory path


def generate_session_id():
    """Generate a unique session identifier"""
    return uuid.uuid4().hex


def user_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid.uuid4().hex[:10], ext)
    return os.path.join("files", str(instance.user.id), filename)


class Folder(models.Model):
    """Folder model with hierarchical relationships"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=255, verbose_name="Folder name")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        # Ensure a user cannot create duplicate folder names at the same level
        unique_together = ['user', 'parent', 'name']

    def clean(self):
        """Prevent a folder from becoming its own ancestor"""
        if self.parent:
            current = self.parent
            while current:
                if current == self:
                    raise ValidationError("A folder cannot be its own descendant")
                current = current.parent

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_path(self):
        """Return the full path for the folder"""
        path_parts = []
        current = self
        while current:
            path_parts.append(current.name)
            current = current.parent
        return '/'.join(reversed(path_parts))

    def get_all_subfolders(self):
        """Recursively fetch all descendant folders"""
        subfolders = list(self.subfolders.all())
        for subfolder in self.subfolders.all():
            subfolders.extend(subfolder.get_all_subfolders())
        return subfolders

    def __str__(self):
        return f"{self.get_path()} - {self.user.username}"


class File(models.Model):
    # Document type choices
    DOCUMENT_TYPE_CHOICES = [
        ('Paper', 'Paper'),
        ('Protocol', 'Protocol'),
        ('Dataset', 'Dataset'),
        ('Code', 'Code'),
    ]
    
    # File format choices
    FILE_FORMAT_CHOICES = [
        # Bioinformatics formats
        ('FASTQ', 'FASTQ'),
        ('FASTA', 'FASTA'),
        ('VCF', 'VCF'),
        ('BAM', 'BAM'),
        ('SAM', 'SAM'),
        ('BED', 'BED'),
        ('GTF', 'GTF'),
        ('GFF', 'GFF'),
        
        # Document formats
        ('PDF', 'PDF'),
        ('DOC', 'Word Document'),
        ('DOCX', 'Word Document'),
        ('PPT', 'PowerPoint'),
        ('PPTX', 'PowerPoint'),
        ('RTF', 'Rich Text Format'),
        
        # Data formats
        ('CSV', 'CSV'),
        ('TSV', 'TSV'),
        ('XLS', 'Excel'),
        ('XLSX', 'Excel'),
        ('JSON', 'JSON'),
        ('XML', 'XML'),
        ('YAML', 'YAML'),
        ('SQL', 'SQL'),
        
        # Code formats
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
        
        # Text formats
        ('txt', 'Text'),
        ('md', 'Markdown'),
        ('log', 'Log File'),
        ('conf', 'Configuration'),
        ('ini', 'INI File'),
        ('cfg', 'Config File'),
        
        # Image formats
        ('jpg', 'JPEG Image'),
        ('jpeg', 'JPEG Image'),
        ('png', 'PNG Image'),
        ('gif', 'GIF Image'),
        ('bmp', 'BMP Image'),
        ('tiff', 'TIFF Image'),
        ('svg', 'SVG Image'),
        ('webp', 'WebP Image'),
        ('ico', 'Icon'),
        
        # Audio formats
        ('mp3', 'MP3 Audio'),
        ('wav', 'WAV Audio'),
        ('flac', 'FLAC Audio'),
        ('aac', 'AAC Audio'),
        ('ogg', 'OGG Audio'),
        ('m4a', 'M4A Audio'),
        
        # Video formats
        ('mp4', 'MP4 Video'),
        ('avi', 'AVI Video'),
        ('mov', 'MOV Video'),
        ('wmv', 'WMV Video'),
        ('flv', 'FLV Video'),
        ('mkv', 'MKV Video'),
        ('webm', 'WebM Video'),
        ('m4v', 'M4V Video'),
        
        # Archive formats
        ('zip', 'ZIP Archive'),
        ('rar', 'RAR Archive'),
        ('7z', '7-Zip Archive'),
        ('tar', 'TAR Archive'),
        ('gz', 'GZIP Archive'),
        ('bz2', 'BZIP2 Archive'),
        ('xz', 'XZ Archive'),
        
        # Other formats
        ('other', 'Other'),
    ]
    
    # Experiment type choices
    EXPERIMENT_TYPE_CHOICES = [
        ('RNA-seq', 'RNA-seq'),
        ('WGS', 'Whole Genome Sequencing'),
        ('scRNA-seq', 'Single Cell RNA-seq'),
        ('MS', 'Mass Spectrometry'),
        ('ChIP-seq', 'ChIP-seq'),
        ('ATAC-seq', 'ATAC-seq'),
        ('other', 'Other'),
    ]
    
    # Access level choices
    ACCESS_LEVEL_CHOICES = [
        ('Public', 'Public'),
        ('Internal', 'Internal'),
        ('Restricted', 'Restricted'),
    ]
    
    # QC status choices
    QC_STATUS_CHOICES = [
        ('unknown', 'Unknown'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]

    # Core fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to=user_directory_path, null=True)
    upload_method = models.CharField(max_length=50, verbose_name="Upload Method")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(default=0)
    original_filename = models.CharField(max_length=255, blank=True)
    parent_folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True, related_name='files')
    
    # Metadata fields (required)
    title = models.CharField(max_length=500, default="", verbose_name="File title", help_text="Descriptive name")
    project = models.CharField(max_length=200, default="", verbose_name="Project", help_text="Project or study code")
    uploader = models.CharField(max_length=100, default="", verbose_name="Uploader", help_text="Person who uploaded the file")
    file_format = models.CharField(max_length=20, choices=FILE_FORMAT_CHOICES, default='other', verbose_name="File format")
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='Dataset', verbose_name="Document type")
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVEL_CHOICES, default='Internal', verbose_name="Access level")
    
    # Optional or auto-filled metadata
    organism = models.CharField(max_length=200, blank=True, verbose_name="Organism", help_text="e.g., Homo sapiens")
    experiment_type = models.CharField(max_length=50, choices=EXPERIMENT_TYPE_CHOICES, blank=True, verbose_name="Assay type")
    tags = models.TextField(blank=True, verbose_name="Tags", help_text="Comma-separated tags")
    description = models.TextField(blank=True, verbose_name="Description", help_text="Detailed notes")
    checksum = models.CharField(max_length=64, blank=True, verbose_name="Checksum", help_text="MD5 hash")
    qc_status = models.CharField(max_length=20, choices=QC_STATUS_CHOICES, default='unknown', verbose_name="QC status")
    
    # Automatically extracted metadata
    extracted_metadata = models.JSONField(default=dict, blank=True, verbose_name="Extracted metadata", help_text="Auto-generated insights")
    
    # Full-text search field (tsvector in PostgreSQL; plain text in SQLite)
    search_vector = models.TextField(blank=True, verbose_name="Search vector", help_text="Materialized text for search")

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            if not self.original_filename:
                self.original_filename = self.file.name
            
            # Auto-detect file format
            if not self.file_format or self.file_format == 'other':
                self.file_format = self._detect_file_format()
            
            # Calculate checksum
            if not self.checksum:
                self.checksum = self._calculate_checksum()
        
        # Populate uploader name if missing
        if not self.uploader and self.user:
            self.uploader = self.user.get_full_name() or self.user.username
        
        # Refresh the search vector
        self._update_search_vector()
        
        super().save(*args, **kwargs)
    
    def _detect_file_format(self):
        """Infer the file format from the extension"""
        if not self.original_filename:
            return 'other'
        
        ext = self.original_filename.lower().split('.')[-1]
        format_mapping = {
            # Bioinformatics formats
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
            
            # Document formats
            'pdf': 'PDF',
            'doc': 'DOC',
            'docx': 'DOCX',
            'ppt': 'PPT',
            'pptx': 'PPTX',
            'rtf': 'RTF',
            
            # Data formats
            'csv': 'CSV',
            'tsv': 'TSV',
            'xls': 'XLS',
            'xlsx': 'XLSX',
            'json': 'JSON',
            'xml': 'XML',
            'yaml': 'YAML',
            'yml': 'YAML',
            'sql': 'SQL',
            
            # Code formats
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
            
            # Text formats
            'txt': 'txt',
            'md': 'md',
            'markdown': 'md',
            'log': 'log',
            'conf': 'conf',
            'config': 'conf',
            'ini': 'ini',
            'cfg': 'cfg',
            
            # Image formats
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
            
            # Audio formats
            'mp3': 'mp3',
            'wav': 'wav',
            'flac': 'flac',
            'aac': 'aac',
            'ogg': 'ogg',
            'm4a': 'm4a',
            
            # Video formats
            'mp4': 'mp4',
            'avi': 'avi',
            'mov': 'mov',
            'wmv': 'wmv',
            'flv': 'flv',
            'mkv': 'mkv',
            'webm': 'webm',
            'm4v': 'm4v',
            
            # Archive formats
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
        """Calculate the file MD5 checksum"""
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
        """Refresh the search vector used for full-text queries"""
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
        """Return the full filesystem path of the file"""
        if self.parent_folder:
            return f"{self.parent_folder.get_path()}/{self.original_filename}"
        return self.original_filename

    def __str__(self):
        return f"{self.get_path()} - {self.user.username}"

    class Meta:
        ordering = ['-uploaded_at']
        # Do not allow duplicate file names within the same folder for a user
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
    chunk_size = models.IntegerField(default=2 * 1024 * 1024)  # 2 MB default chunks
    uploaded_size = models.BigIntegerField(default=0)
    temp_path = models.CharField(max_length=512)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    parent_folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True, related_name='upload_sessions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.session_id} ({self.original_filename}) - {self.status}"
