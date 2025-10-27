from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    """自定义用户管理器，使用邮箱创建用户"""
    
    def create_user(self, email, password=None, **extra_fields):
        """创建普通用户"""
        if not email:
            raise ValueError('邮箱地址是必需的')
        email = self.normalize_email(email)
        # 使用邮箱作为用户名
        extra_fields.setdefault('username', email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """创建超级用户"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置 is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置 is_superuser=True')
            
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """自定义用户模型，使用邮箱作为用户名"""
    email = models.EmailField(unique=True, verbose_name='邮箱地址')
    
    # 使用自定义用户管理器
    objects = CustomUserManager()
    
    # 使用邮箱作为用户名字段
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # 创建超级用户时需要的额外字段
    
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
    
    def __str__(self):
        return self.email
