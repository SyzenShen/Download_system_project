"""
文件搜索和筛选API视图
支持全文搜索、Facets筛选、元数据查询等功能
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
    文件搜索API
    支持关键词搜索和多种筛选条件
    """
    try:
        # 获取搜索参数
        query = request.GET.get('q', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # 获取筛选参数 (Facets)
        document_type = request.GET.get('document_type', '')
        file_format = request.GET.get('file_format', '')
        organism = request.GET.get('organism', '')
        project = request.GET.get('project', '')
        experiment_type = request.GET.get('experiment_type', '')
        access_level = request.GET.get('access_level', '')
        
        # 排序参数
        sort_by = request.GET.get('sort_by', 'uploaded_at')
        sort_order = request.GET.get('sort_order', 'desc')
        
        # 基础查询：只返回当前用户的文件
        queryset = File.objects.filter(user=request.user)
        
        # 应用搜索条件
        if query:
            queryset = apply_search_query(queryset, query)
        
        # 应用筛选条件
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
        
        # 应用排序
        order_field = sort_by
        if sort_order == 'desc':
            order_field = f'-{sort_by}'
        queryset = queryset.order_by(order_field)
        
        # 分页
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # 序列化结果
        serializer = FileSerializer(page_obj.object_list, many=True)
        
        # 获取筛选统计信息
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
            {'error': f'搜索失败: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_facets(request):
    """
    获取筛选器数据 (Facets)
    返回各个筛选维度的可选值和计数
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
            {'error': f'获取筛选器数据失败: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_suggestions(request):
    """
    搜索建议API
    根据用户输入提供搜索建议
    """
    try:
        query = request.GET.get('q', '').strip()
        limit = int(request.GET.get('limit', 10))
        
        if not query or len(query) < 2:
            return Response({'suggestions': []})
        
        suggestions = []
        
        # 项目名建议
        projects = File.objects.filter(
            user=request.user,
            project__icontains=query
        ).values_list('project', flat=True).distinct()[:limit//2]
        
        for project in projects:
            suggestions.append({
                'type': 'project',
                'value': project,
                'label': f'项目: {project}'
            })
        
        # 物种建议
        organisms = File.objects.filter(
            user=request.user,
            organism__icontains=query
        ).values_list('organism', flat=True).distinct()[:limit//2]
        
        for organism in organisms:
            if organism:  # 过滤空值
                suggestions.append({
                    'type': 'organism',
                    'value': organism,
                    'label': f'物种: {organism}'
                })
        
        # 标题建议
        titles = File.objects.filter(
            user=request.user,
            title__icontains=query
        ).values_list('title', flat=True).distinct()[:limit//3]
        
        for title in titles:
            suggestions.append({
                'type': 'title',
                'value': title,
                'label': f'标题: {title[:50]}...' if len(title) > 50 else f'标题: {title}'
            })
        
        return Response({
            'suggestions': suggestions[:limit]
        })
        
    except Exception as e:
        return Response(
            {'error': f'获取搜索建议失败: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def file_preview(request, file_id):
    """
    文件预览API
    返回文件的预览内容
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
        
        # 根据文件格式生成预览内容
        if file_obj.file_format in ['txt', 'CSV', 'py']:
            preview_data['preview'] = get_text_preview(file_obj)
        elif file_obj.file_format in ['FASTA', 'FASTQ']:
            preview_data['preview'] = get_sequence_preview(file_obj)
        elif file_obj.file_format == 'PDF':
            preview_data['preview'] = get_pdf_preview(file_obj)
        else:
            preview_data['preview'] = {
                'type': 'metadata_only',
                'message': '此文件格式不支持预览，仅显示元数据信息'
            }
        
        return Response(preview_data)
        
    except File.DoesNotExist:
        return Response(
            {'error': '文件不存在或无权限访问'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'预览失败: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def apply_search_query(queryset, query: str):
    """
    应用搜索查询条件
    支持多种搜索模式
    """
    # 解析查询字符串，支持 field:value 格式
    field_queries = {}
    remaining_query = query
    
    # 提取字段查询 (如 project:MyLab)
    field_pattern = r'(\w+):([^\s]+)'
    matches = re.findall(field_pattern, query)
    
    for field, value in matches:
        field_queries[field] = value
        remaining_query = re.sub(f'{field}:{value}', '', remaining_query)
    
    # 清理剩余查询
    remaining_query = remaining_query.strip()
    
    # 应用字段查询
    if 'project' in field_queries:
        queryset = queryset.filter(project__icontains=field_queries['project'])
    if 'organism' in field_queries:
        queryset = queryset.filter(organism__icontains=field_queries['organism'])
    if 'type' in field_queries:
        queryset = queryset.filter(document_type__icontains=field_queries['type'])
    if 'format' in field_queries:
        queryset = queryset.filter(file_format__icontains=field_queries['format'])
    
    # 应用全文搜索
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
    """
    获取筛选器数据
    """
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
    
    # Organism facets (过滤空值)
    facets['organism'] = list(
        queryset.exclude(organism='')
        .values('organism')
        .annotate(count=Count('id'))
        .order_by('-count')[:20]  # 限制数量
    )
    
    # Project facets
    facets['project'] = list(
        queryset.values('project')
        .annotate(count=Count('id'))
        .order_by('-count')[:20]
    )
    
    # Experiment Type facets (过滤空值)
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
    """获取文本文件预览"""
    try:
        with open(file_obj.file.path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(2000)  # 读取前2000字符
            lines = content.split('\n')[:50]  # 前50行
            
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
            'message': f'无法预览文件: {str(e)}'
        }


def get_sequence_preview(file_obj) -> Dict[str, Any]:
    """获取序列文件预览 (FASTA/FASTQ)"""
    try:
        with open(file_obj.file.path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= 100:  # 只读前100行
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
            'message': f'无法预览序列文件: {str(e)}'
        }


def get_pdf_preview(file_obj) -> Dict[str, Any]:
    """获取PDF文件预览"""
    try:
        # 如果有提取的元数据，使用其中的文本预览
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
                'message': 'PDF文件预览需要安装额外的依赖包',
                'metadata': file_obj.extracted_metadata,
                'download_url': f'/api/files/{file_obj.id}/download/'
            }
    except Exception as e:
        return {
            'type': 'error',
            'message': f'无法预览PDF文件: {str(e)}'
        }