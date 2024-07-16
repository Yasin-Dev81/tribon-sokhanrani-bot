from .start import register_start_handlers
from .home import register_home_handlers
from .user import register_user_handlers
from .teacher import register_teacher_handlers
from .admin import register_admin_handlers

from .admin import ActivePractice

__all__ = (
    register_start_handlers,
    register_home_handlers,
    register_user_handlers,
    register_teacher_handlers,
    register_admin_handlers,
    ActivePractice
)
