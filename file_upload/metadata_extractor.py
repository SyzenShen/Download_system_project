"""
File metadata extraction utilities for BioFileManager.
Each extractor focuses on low-cost parsing of common bioinformatics formats.
"""

import re
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Metadata extractor that understands several bioinformatics formats"""
    
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
        Extract structured metadata for the provided file.

        Args:
            file_path: absolute path to the file on disk
            file_format: normalized file format string (FASTA/FASTQ/VCF/etc.)

        Returns:
            dict containing extracted metadata fields
        """
        try:
            extractor = self.extractors.get(file_format)
            if extractor:
                return extractor(file_path)
            else:
                return self._extract_basic_metadata(file_path)
        except Exception as e:
            logger.error(f"Failed to extract metadata from {file_path}: {e}")
            return {}
    
    def _extract_basic_metadata(self, file_path: str) -> Dict[str, Any]:
        """Return generic file stats when no specialized extractor exists"""
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
        """Extract metadata from FASTA files"""
        metadata = {}
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read headers from the first few sequences
                headers = []
                sequence_count = 0
                total_length = 0
                
                current_seq_length = 0
                for line_num, line in enumerate(f):
                    if line_num > 1000:  # Cap how many lines we inspect
                        break
                        
                    line = line.strip()
                    if line.startswith('>'):
                        if current_seq_length > 0:
                            total_length += current_seq_length
                            current_seq_length = 0
                        
                        headers.append(line[1:])  # Drop the leading '>'
                        sequence_count += 1
                        
                        if sequence_count > 10:  # Only analyze the first 10 sequences
                            break
                elif line and not line.startswith('>'):
                    current_seq_length += len(line)
            
                # Account for the final sequence
                if current_seq_length > 0:
                    total_length += current_seq_length
            
                metadata.update({
                    'sequence_count': sequence_count,
                    'average_length': total_length // sequence_count if sequence_count > 0 else 0,
                    'sample_headers': headers[:5],  # Keep a sample of the first five headers
                })
                
                # Attempt to infer the organism from headers
                organism = self._extract_organism_from_headers(headers)
                if organism:
                    metadata['detected_organism'] = organism
                    
        except Exception as e:
            logger.error(f"FASTA metadata extraction failed: {e}")
        
        return metadata
    
    def _extract_fastq_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from FASTQ files"""
        metadata = {}
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                read_count = 0
                total_length = 0
                quality_scores = []
                headers = []
                
                lines = []
                for line_num, line in enumerate(f):
                    if line_num > 4000:  # Limit to roughly the first 1,000 reads
                        break
                    
                    lines.append(line.strip())
                    
                    # Every 4 lines correspond to a read
                    if len(lines) == 4:
                        header, sequence, plus, quality = lines
                        if header.startswith('@') and plus.startswith('+'):
                            read_count += 1
                            total_length += len(sequence)
                            headers.append(header[1:])  # Drop '@'
                            
                            # Track basic quality metrics
                            if quality:
                                avg_qual = sum(ord(c) - 33 for c in quality) / len(quality)
                                quality_scores.append(avg_qual)
                        
                        lines = []
                        
                        if read_count >= 1000:  # Only analyze the first 1,000 reads
                            break
                
                metadata.update({
                    'read_count': read_count,
                    'average_read_length': total_length // read_count if read_count > 0 else 0,
                    'average_quality': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                    'sample_headers': headers[:5],
                })
                
                # Try to detect the sequencing platform
                platform = self._detect_sequencing_platform(headers)
                if platform:
                    metadata['sequencing_platform'] = platform
                    
        except Exception as e:
            logger.error(f"FASTQ metadata extraction failed: {e}")
        
        return metadata
    
    def _extract_vcf_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from VCF files"""
        metadata = {}
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                header_lines = []
                variant_count = 0
                sample_names = []
                
                for line_num, line in enumerate(f):
                    if line_num > 1000:  # Cap how much of the file we scan
                        break
                    
                    line = line.strip()
                    if line.startswith('##'):
                        header_lines.append(line)
                    elif line.startswith('#CHROM'):
                        # Parse sample names
                        columns = line.split('\t')
                        if len(columns) > 9:
                            sample_names = columns[9:]
                    elif line and not line.startswith('#'):
                        variant_count += 1
                        if variant_count >= 100:  # Count only the first 100 variants
                            break
                
                metadata.update({
                    'variant_count_sample': variant_count,
                    'sample_count': len(sample_names),
                    'sample_names': sample_names[:10],  # Keep the first 10 sample names
                    'header_info': self._parse_vcf_headers(header_lines),
                })
                
        except Exception as e:
            logger.error(f"VCF metadata extraction failed: {e}")
        
        return metadata
    
    def _extract_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract simple metadata from PDF files"""
        metadata = {}
        try:
            # Try to use pypdf to pull textual content when available
            try:
                from pypdf import PdfReader
                
                reader = PdfReader(file_path)
                metadata['page_count'] = len(reader.pages)
                
                # Capture the first two pages of text
                text_content = ""
                for i in range(min(2, len(reader.pages))):
                    page_text = reader.pages[i].extract_text() or ""
                    text_content += page_text
                
                if text_content:
                    metadata['text_preview'] = text_content[:1000]  # First 1000 characters
                    
                    # Attempt to extract keywords
                    keywords = self._extract_keywords_from_text(text_content)
                    if keywords:
                        metadata['detected_keywords'] = keywords
                
                # Extract PDF metadata
                if reader.metadata:
                    pdf_info = {}
                    for key, value in reader.metadata.items():
                        if value:
                            pdf_info[key.replace('/', '')] = str(value)
                    metadata['pdf_info'] = pdf_info
                    
            except ImportError:
                logger.warning("pypdf is not installed; skipping PDF text extraction")
                
        except Exception as e:
            logger.error(f"PDF metadata extraction failed: {e}")
        
        return metadata
    
    def _extract_csv_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from CSV-like files"""
        metadata = {}
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read the first few lines to infer structure
                lines = []
                for i, line in enumerate(f):
                    if i >= 10:  # Inspect at most 10 lines
                        break
                    lines.append(line.strip())
                
                if lines:
                    # Detect the delimiter
                    first_line = lines[0]
                    separators = [',', '\t', ';', '|']
                    separator = ','
                    max_cols = 0
                    
                    for sep in separators:
                        cols = len(first_line.split(sep))
                        if cols > max_cols:
                            max_cols = cols
                            separator = sep
                    
                    # Parse column names
                    columns = first_line.split(separator)
                    metadata.update({
                        'column_count': len(columns),
                        'separator': separator,
                        'columns': columns[:20],  # Keep up to 20 column names
                        'sample_rows': len(lines) - 1,
                    })
                    
        except Exception as e:
            logger.error(f"CSV metadata extraction failed: {e}")
        
        return metadata
    
    def _extract_text_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract simple stats from plain-text files"""
        metadata = {}
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(5000)  # Read the first 5,000 characters
                
                lines = content.split('\n')
                words = content.split()
                
                metadata.update({
                    'line_count': len(lines),
                    'word_count': len(words),
                    'char_count': len(content),
                    'preview': content[:500],  # Preview the first 500 characters
                })
                
                # Attempt to detect common keywords
                keywords = self._extract_keywords_from_text(content)
                if keywords:
                    metadata['detected_keywords'] = keywords
                    
        except Exception as e:
            logger.error(f"Text metadata extraction failed: {e}")
        
        return metadata
    
    def _extract_organism_from_headers(self, headers: list) -> Optional[str]:
        """Extract organism information from FASTA/FASTQ headers"""
        organism_patterns = [
            r'Homo sapiens',
            r'Mus musculus',
            r'Drosophila melanogaster',
            r'Caenorhabditis elegans',
            r'Saccharomyces cerevisiae',
            r'Escherichia coli',
            r'Arabidopsis thaliana',
        ]
        
        for header in headers[:10]:  # Only inspect the first few headers
            for pattern in organism_patterns:
                if re.search(pattern, header, re.IGNORECASE):
                    return pattern
        
        return None
    
    def _detect_sequencing_platform(self, headers: list) -> Optional[str]:
        """Detect the sequencing platform from FASTQ headers"""
        platform_patterns = {
            'Illumina': [r'@.*:.*:.*:.*:', r'HWI-', r'HWUSI-', r'M[0-9]+:', r'HiSeq', r'MiSeq', r'NextSeq'],
            'PacBio': [r'@m[0-9]+', r'PacBio'],
            'Oxford Nanopore': [r'@.*_ch[0-9]+_read[0-9]+', r'MinION', r'GridION'],
            'Ion Torrent': [r'@.*_[0-9]+_[0-9]+', r'IonTorrent'],
        }
        
        for header in headers[:5]:  # Only inspect the first five headers
            for platform, patterns in platform_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, header, re.IGNORECASE):
                        return platform
        
        return None
    
    def _parse_vcf_headers(self, header_lines: list) -> Dict[str, Any]:
        """Parse high-level VCF header information"""
        info = {}
        for line in header_lines[:20]:  # Process at most 20 header lines
            if '=' in line:
                if line.startswith('##fileformat='):
                    info['file_format'] = line.split('=', 1)[1]
                elif line.startswith('##reference='):
                    info['reference'] = line.split('=', 1)[1]
                elif line.startswith('##source='):
                    info['source'] = line.split('=', 1)[1]
        
        return info
    
    def _extract_keywords_from_text(self, text: str) -> list:
        """Extract a small set of bio-medical keywords from text"""
        # Common life-science keywords we scan for
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
        
        return found_keywords[:10]  # Return at most 10 keywords


# Convenience helper
def extract_file_metadata(file_path: str, file_format: str) -> Dict[str, Any]:
    """
    Extract metadata for a file given its normalized format.
    """
    extractor = MetadataExtractor()
    return extractor.extract_metadata(file_path, file_format)
