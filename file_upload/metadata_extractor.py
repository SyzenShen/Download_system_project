"""
文件元数据提取工具
支持从不同格式的文件中自动提取元数据信息
"""

import re
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """文件元数据提取器"""
    
    def __init__(self):
        self.extractors = {
            'FASTA': self._extract_fasta_metadata,
            'FASTQ': self._extract_fastq_metadata,
            'VCF': self._extract_vcf_metadata,
            'PDF': self._extract_pdf_metadata,
            'CSV': self._extract_csv_metadata,
            'txt': self._extract_text_metadata,
        }
    
    def extract_metadata(self, file_path: str, file_format: str) -> Dict[str, Any]:
        """
        从文件中提取元数据
        
        Args:
            file_path: 文件路径
            file_format: 文件格式
            
        Returns:
            提取的元数据字典
        """
        try:
            extractor = self.extractors.get(file_format)
            if extractor:
                return extractor(file_path)
            else:
                return self._extract_basic_metadata(file_path)
        except Exception as e:
            logger.error(f"提取元数据失败 {file_path}: {e}")
            return {}
    
    def _extract_basic_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取基本文件信息"""
        try:
            path = Path(file_path)
            return {
                'file_size': path.stat().st_size,
                'file_extension': path.suffix.lower(),
                'extracted_at': 'basic_info'
            }
        except Exception:
            return {}
    
    def _extract_fasta_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取FASTA文件元数据"""
        metadata = {}
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 读取前几个序列的header
                headers = []
                sequence_count = 0
                total_length = 0
                
                current_seq_length = 0
                for line_num, line in enumerate(f):
                    if line_num > 1000:  # 限制读取行数
                        break
                        
                    line = line.strip()
                    if line.startswith('>'):
                        if current_seq_length > 0:
                            total_length += current_seq_length
                            current_seq_length = 0
                        
                        headers.append(line[1:])  # 去掉 '>'
                        sequence_count += 1
                        
                        if sequence_count > 10:  # 只分析前10个序列
                            break
                    elif line and not line.startswith('>'):
                        current_seq_length += len(line)
                
                # 添加最后一个序列的长度
                if current_seq_length > 0:
                    total_length += current_seq_length
                
                metadata.update({
                    'sequence_count': sequence_count,
                    'average_length': total_length // sequence_count if sequence_count > 0 else 0,
                    'sample_headers': headers[:5],  # 保存前5个header作为样本
                })
                
                # 尝试从header中提取物种信息
                organism = self._extract_organism_from_headers(headers)
                if organism:
                    metadata['detected_organism'] = organism
                    
        except Exception as e:
            logger.error(f"FASTA元数据提取失败: {e}")
        
        return metadata
    
    def _extract_fastq_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取FASTQ文件元数据"""
        metadata = {}
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                read_count = 0
                total_length = 0
                quality_scores = []
                headers = []
                
                lines = []
                for line_num, line in enumerate(f):
                    if line_num > 4000:  # 限制读取行数（约1000个reads）
                        break
                    
                    lines.append(line.strip())
                    
                    # 每4行为一个read
                    if len(lines) == 4:
                        header, sequence, plus, quality = lines
                        if header.startswith('@') and plus.startswith('+'):
                            read_count += 1
                            total_length += len(sequence)
                            headers.append(header[1:])  # 去掉 '@'
                            
                            # 计算质量分数统计
                            if quality:
                                avg_qual = sum(ord(c) - 33 for c in quality) / len(quality)
                                quality_scores.append(avg_qual)
                        
                        lines = []
                        
                        if read_count >= 1000:  # 分析前1000个reads
                            break
                
                metadata.update({
                    'read_count': read_count,
                    'average_read_length': total_length // read_count if read_count > 0 else 0,
                    'average_quality': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                    'sample_headers': headers[:5],
                })
                
                # 尝试检测测序平台
                platform = self._detect_sequencing_platform(headers)
                if platform:
                    metadata['sequencing_platform'] = platform
                    
        except Exception as e:
            logger.error(f"FASTQ元数据提取失败: {e}")
        
        return metadata
    
    def _extract_vcf_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取VCF文件元数据"""
        metadata = {}
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                header_lines = []
                variant_count = 0
                sample_names = []
                
                for line_num, line in enumerate(f):
                    if line_num > 1000:  # 限制读取行数
                        break
                    
                    line = line.strip()
                    if line.startswith('##'):
                        header_lines.append(line)
                    elif line.startswith('#CHROM'):
                        # 解析样本名称
                        columns = line.split('\t')
                        if len(columns) > 9:
                            sample_names = columns[9:]
                    elif line and not line.startswith('#'):
                        variant_count += 1
                        if variant_count >= 100:  # 只计数前100个变异
                            break
                
                metadata.update({
                    'variant_count_sample': variant_count,
                    'sample_count': len(sample_names),
                    'sample_names': sample_names[:10],  # 保存前10个样本名
                    'header_info': self._parse_vcf_headers(header_lines),
                })
                
        except Exception as e:
            logger.error(f"VCF元数据提取失败: {e}")
        
        return metadata
    
    def _extract_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取PDF文件元数据"""
        metadata = {}
        try:
            # 尝试使用pypdf提取文本（如果可用）
            try:
                from pypdf import PdfReader
                
                reader = PdfReader(file_path)
                metadata['page_count'] = len(reader.pages)
                
                # 提取前两页的文本
                text_content = ""
                for i in range(min(2, len(reader.pages))):
                    page_text = reader.pages[i].extract_text() or ""
                    text_content += page_text
                
                if text_content:
                    metadata['text_preview'] = text_content[:1000]  # 前1000字符
                    
                    # 尝试提取关键信息
                    keywords = self._extract_keywords_from_text(text_content)
                    if keywords:
                        metadata['detected_keywords'] = keywords
                
                # 提取PDF元信息
                if reader.metadata:
                    pdf_info = {}
                    for key, value in reader.metadata.items():
                        if value:
                            pdf_info[key.replace('/', '')] = str(value)
                    metadata['pdf_info'] = pdf_info
                    
            except ImportError:
                logger.warning("pypdf未安装，跳过PDF文本提取")
                
        except Exception as e:
            logger.error(f"PDF元数据提取失败: {e}")
        
        return metadata
    
    def _extract_csv_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取CSV文件元数据"""
        metadata = {}
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 读取前几行分析结构
                lines = []
                for i, line in enumerate(f):
                    if i >= 10:  # 只读前10行
                        break
                    lines.append(line.strip())
                
                if lines:
                    # 检测分隔符
                    first_line = lines[0]
                    separators = [',', '\t', ';', '|']
                    separator = ','
                    max_cols = 0
                    
                    for sep in separators:
                        cols = len(first_line.split(sep))
                        if cols > max_cols:
                            max_cols = cols
                            separator = sep
                    
                    # 解析列名
                    columns = first_line.split(separator)
                    metadata.update({
                        'column_count': len(columns),
                        'separator': separator,
                        'columns': columns[:20],  # 保存前20列名
                        'sample_rows': len(lines) - 1,
                    })
                    
        except Exception as e:
            logger.error(f"CSV元数据提取失败: {e}")
        
        return metadata
    
    def _extract_text_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取文本文件元数据"""
        metadata = {}
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(5000)  # 读取前5000字符
                
                lines = content.split('\n')
                words = content.split()
                
                metadata.update({
                    'line_count': len(lines),
                    'word_count': len(words),
                    'char_count': len(content),
                    'preview': content[:500],  # 前500字符预览
                })
                
                # 尝试提取关键词
                keywords = self._extract_keywords_from_text(content)
                if keywords:
                    metadata['detected_keywords'] = keywords
                    
        except Exception as e:
            logger.error(f"文本元数据提取失败: {e}")
        
        return metadata
    
    def _extract_organism_from_headers(self, headers: list) -> Optional[str]:
        """从FASTA/FASTQ headers中提取物种信息"""
        organism_patterns = [
            r'Homo sapiens',
            r'Mus musculus',
            r'Drosophila melanogaster',
            r'Caenorhabditis elegans',
            r'Saccharomyces cerevisiae',
            r'Escherichia coli',
            r'Arabidopsis thaliana',
        ]
        
        for header in headers[:10]:  # 检查前10个header
            for pattern in organism_patterns:
                if re.search(pattern, header, re.IGNORECASE):
                    return pattern
        
        return None
    
    def _detect_sequencing_platform(self, headers: list) -> Optional[str]:
        """检测测序平台"""
        platform_patterns = {
            'Illumina': [r'@.*:.*:.*:.*:', r'HWI-', r'HWUSI-', r'M[0-9]+:', r'HiSeq', r'MiSeq', r'NextSeq'],
            'PacBio': [r'@m[0-9]+', r'PacBio'],
            'Oxford Nanopore': [r'@.*_ch[0-9]+_read[0-9]+', r'MinION', r'GridION'],
            'Ion Torrent': [r'@.*_[0-9]+_[0-9]+', r'IonTorrent'],
        }
        
        for header in headers[:5]:  # 检查前5个header
            for platform, patterns in platform_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, header, re.IGNORECASE):
                        return platform
        
        return None
    
    def _parse_vcf_headers(self, header_lines: list) -> Dict[str, Any]:
        """解析VCF header信息"""
        info = {}
        for line in header_lines[:20]:  # 只解析前20行header
            if '=' in line:
                if line.startswith('##fileformat='):
                    info['file_format'] = line.split('=', 1)[1]
                elif line.startswith('##reference='):
                    info['reference'] = line.split('=', 1)[1]
                elif line.startswith('##source='):
                    info['source'] = line.split('=', 1)[1]
        
        return info
    
    def _extract_keywords_from_text(self, text: str) -> list:
        """从文本中提取关键词"""
        # 生物医学相关关键词
        bio_keywords = [
            'RNA-seq', 'DNA-seq', 'ChIP-seq', 'ATAC-seq', 'scRNA-seq',
            'genome', 'transcriptome', 'proteome', 'metabolome',
            'GWAS', 'SNP', 'variant', 'mutation', 'expression',
            'protein', 'gene', 'chromosome', 'sequencing',
            'cancer', 'tumor', 'disease', 'treatment', 'therapy',
            'cell', 'tissue', 'organ', 'development', 'differentiation',
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in bio_keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords[:10]  # 返回前10个关键词


# 使用示例函数
def extract_file_metadata(file_path: str, file_format: str) -> Dict[str, Any]:
    """
    提取文件元数据的便捷函数
    
    Args:
        file_path: 文件路径
        file_format: 文件格式
        
    Returns:
        提取的元数据字典
    """
    extractor = MetadataExtractor()
    return extractor.extract_metadata(file_path, file_format)