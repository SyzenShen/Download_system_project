import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ComplexPasswordValidator:
    """
    验证密码复杂度：
    - 至少8个字符
    - 包含大写字母
    - 包含小写字母
    - 包含数字
    """
    
    def __init__(self, min_length=8):
        self.min_length = min_length
    
    def validate(self, password, user=None):
        errors = []
        
        # 检查最小长度
        if len(password) < self.min_length:
            errors.append(_('密码至少需要 %(min_length)d 个字符。') % {'min_length': self.min_length})
        
        # 检查是否包含大写字母
        if not re.search(r'[A-Z]', password):
            errors.append(_('密码必须包含至少一个大写字母。'))
        
        # 检查是否包含小写字母
        if not re.search(r'[a-z]', password):
            errors.append(_('密码必须包含至少一个小写字母。'))
        
        # 检查是否包含数字
        if not re.search(r'\d', password):
            errors.append(_('密码必须包含至少一个数字。'))
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        return _(
            '您的密码必须满足以下要求：'
            '至少8个字符，包含大写字母、小写字母和数字。'
        )