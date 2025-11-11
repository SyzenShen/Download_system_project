"""
Search and filtering API views for files.
Supports full-text search, facets, and metadata-driven queries.
"""

from django.db.models import Q, Count
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.db.models import Case, When, Value, CharField
import re
from typing import Dict, List, Any

from .models import File
from .serializers import FileSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_files(request):
    """
    Search API that supports keyword queries plus multiple filters
    """
    try:
        # Query parameters
        query = request.GET.get('q', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # Facet filters
        document_type = request.GET.get('document_type', '')
        file_format = request.GET.get('file_format', '')
        organism = request.GET.get('organism', '')
        project = request.GET.get('project', '')
        experiment_type = request.GET.get('experiment_type', '')
        access_level = request.GET.get('access_level', '')
        
        # Sorting parameters
        sort_by = request.GET.get('sort_by', 'uploaded_at')
        sort_order = request.GET.get('sort_order', 'desc')
        
        # Base queryset: only the current user's files
        queryset = File.objects.filter(user=request.user)
        
        # Apply search query
        if query:
            queryset = apply_search_query(queryset, query)
        
        # Apply filters
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        if file_format:
            queryset = queryset.filter(file_format=file_format)
        if organism:
            queryset = queryset.filter(organism__icontains=organism)
        if project:
            queryset = queryset.filter(project__icontains=project)
        if experiment_type:
            queryset = queryset.filter(experiment_type=experiment_type)
        if access_level:
            queryset = queryset.filter(access_level=access_level)
        
        # Apply sorting
        order_field = sort_by
        if sort_order == 'desc':
            order_field = f'-{sort_by}'
        queryset = queryset.order_by(order_field)
        
        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize results
        serializer = FileSerializer(page_obj.object_list, many=True)
        
        # Compute facet stats
        facets = get_facets_data(File.objects.filter(user=request.user))
        
        return Response({
            'results': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
            'facets': facets,
            'query_info': {
                'query': query,
                'filters_applied': {
                    'document_type': document_type,
                    'file_format': file_format,
                    'organism': organism,
                    'project': project,
                    'experiment_type': experiment_type,
                    'access_level': access_level,
                }
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'Search failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_facets(request):
    """
    Return available facet values and counts for the current user
    """
    try:
        queryset = File.objects.filter(user=request.user)
        facets = get_facets_data(queryset)
        
        return Response({
            'facets': facets,
            'total_files': queryset.count()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch facets: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_suggestions(request):
    """
    Suggest search helpers based on the partial query
    """
    try:
        query = request.GET.get('q', '').strip()
        limit = int(request.GET.get('limit', 10))
        
        if not query or len(query) < 2:
            return Response({'suggestions': []})
        
        suggestions = []
        
        # Project suggestions
        projects = File.objects.filter(
            user=request.user,
            project__icontains=query
        ).values_list('project', flat=True).distinct()[:limit//2]
        
        for project in projects:
            suggestions.append({
                'type': 'project',
                'value': project,
                'label': f'Project: {project}'
            })
        
        # Organism suggestions
        organisms = File.objects.filter(
            user=request.user,
            organism__icontains=query
        ).values_list('organism', flat=True).distinct()[:limit//2]
        
        for organism in organisms:
            if organism:  # Skip empty values
                suggestions.append({
                    'type': 'organism',
                    'value': organism,
                    'label': f'Organism: {organism}'
                })
        
        # Title suggestions
        titles = File.objects.filter(
            user=request.user,
            title__icontains=query
        ).values_list('title', flat=True).distinct()[:limit//3]
        
        for title in titles:
            suggestions.append({
                'type': 'title',
                'value': title,
                'label': f'Title: {title[:50]}...' if len(title) > 50 else f'Title: {title}'
            })
        
        return Response({
            'suggestions': suggestions[:limit]
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch search suggestions: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def file_preview(request, file_id):
    """
    Return a preview payload for the requested file
    """
    try:
        file_obj = File.objects.get(id=file_id, user=request.user)
        
        preview_data = {
            'id': file_obj.id,
            'title': file_obj.title,
            'filename': file_obj.original_filename,
            'file_format': file_obj.file_format,
            'file_size': file_obj.file_size,
            'uploaded_at': file_obj.uploaded_at,
            'metadata': file_obj.extracted_metadata,
        }
        
        # Build preview content per file format
        if file_obj.file_format in ['txt', 'CSV', 'py']:
            preview_data['preview'] = get_text_preview(file_obj)
        elif file_obj.file_format in ['FASTA', 'FASTQ']:
            preview_data['preview'] = get_sequence_preview(file_obj)
        elif file_obj.file_format == 'PDF':
            preview_data['preview'] = get_pdf_preview(file_obj)
        else:
            preview_data['preview'] = {
                'type': 'metadata_only',
                'message': 'Preview is not supported for this format; metadata will be shown instead.'
            }
        
        return Response(preview_data)
        
    except File.DoesNotExist:
        return Response(
            {'error': 'File does not exist or cannot be accessed'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Preview failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def apply_search_query(queryset, query: str):
    """
    Apply search filters supporting several modes
    """
    # Parse the query string, supporting field:value syntax
    field_queries = {}
    remaining_query = query
    
    # Extract field-specific queries (e.g., project:MyLab)
    field_pattern = r'(\w+):([^\s]+)'
    matches = re.findall(field_pattern, query)
    
    for field, value in matches:
        field_queries[field] = value
        remaining_query = re.sub(f'{field}:{value}', '', remaining_query)
    
    # Clean up the remaining query
    remaining_query = remaining_query.strip()
    
    # Apply field-specific filters
    if 'project' in field_queries:
        queryset = queryset.filter(project__icontains=field_queries['project'])
    if 'organism' in field_queries:
        queryset = queryset.filter(organism__icontains=field_queries['organism'])
    if 'type' in field_queries:
        queryset = queryset.filter(document_type__icontains=field_queries['type'])
    if 'format' in field_queries:
        queryset = queryset.filter(file_format__icontains=field_queries['format'])
    
    # Apply full-text search for the remaining tokens
    if remaining_query:
        search_q = Q()
        for term in remaining_query.split():
            term_q = (
                Q(search_vector__icontains=term) |
                Q(title__icontains=term) |
                Q(description__icontains=term) |
                Q(tags__icontains=term) |
                Q(project__icontains=term) |
                Q(organism__icontains=term) |
                Q(original_filename__icontains=term)
            )
            search_q &= term_q
        
        queryset = queryset.filter(search_q)
    
    return queryset


def get_facets_data(queryset) -> Dict[str, List[Dict[str, Any]]]:
    """Assemble facet counts for the supplied queryset"""
    facets = {}
    
    # Document Type facets
    facets['document_type'] = list(
        queryset.values('document_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # File Format facets
    facets['file_format'] = list(
        queryset.values('file_format')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # Organism facets (skip blank values)
    facets['organism'] = list(
        queryset.exclude(organism='')
        .values('organism')
        .annotate(count=Count('id'))
        .order_by('-count')[:20]  # Limit results
    )
    
    # Project facets
    facets['project'] = list(
        queryset.values('project')
        .annotate(count=Count('id'))
        .order_by('-count')[:20]
    )
    
    # Experiment type facets (skip blank values)
    facets['experiment_type'] = list(
        queryset.exclude(experiment_type='')
        .values('experiment_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # Access Level facets
    facets['access_level'] = list(
        queryset.values('access_level')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    return facets


def get_text_preview(file_obj) -> Dict[str, Any]:
    """Return a preview for plain-text files"""
    try:
        with open(file_obj.file.path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(2000)  # Read the first 2,000 characters
            lines = content.split('\n')[:50]  # Only show the first 50 lines
            
        return {
            'type': 'text',
            'content': '\n'.join(lines),
            'total_chars': len(content),
            'preview_chars': min(2000, len(content)),
            'total_lines': len(lines),
        }
    except Exception as e:
        return {
            'type': 'error',
            'message': f'Unable to preview file: {str(e)}'
        }


def get_sequence_preview(file_obj) -> Dict[str, Any]:
    """Return a preview of sequence files (FASTA/FASTQ)"""
    try:
        with open(file_obj.file.path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= 100:  # Read at most 100 lines
                    break
                lines.append(line.rstrip())
        
        return {
            'type': 'sequence',
            'content': '\n'.join(lines),
            'total_lines_preview': len(lines),
            'format': file_obj.file_format,
        }
    except Exception as e:
        return {
            'type': 'error',
            'message': f'Unable to preview sequence file: {str(e)}'
        }


def get_pdf_preview(file_obj) -> Dict[str, Any]:
    """Return a preview payload for PDFs"""
    try:
        # Use extracted text preview when available
        if file_obj.extracted_metadata and 'text_preview' in file_obj.extracted_metadata:
            return {
                'type': 'pdf_text',
                'content': file_obj.extracted_metadata['text_preview'],
                'page_count': file_obj.extracted_metadata.get('page_count', 'Unknown'),
                'source': 'extracted_metadata'
            }
        else:
            return {
                'type': 'pdf_info',
                'message': 'PDF preview requires optional dependencies to be installed.',
                'metadata': file_obj.extracted_metadata,
                'download_url': f'/api/files/{file_obj.id}/download/'
            }
    except Exception as e:
        return {
            'type': 'error',
            'message': f'Unable to preview PDF file: {str(e)}'
        }
