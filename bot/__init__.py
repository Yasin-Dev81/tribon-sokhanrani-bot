from .start import register_start_handlers
from .home import register_home_handlers
from .user import register_user_handlers
from .teacher import register_teacher_handlers
from .admin import register_admin_handlers
from .report import register_report_handlers
from .utils import register_utils_handlers
from .system import register_system_handlers


__all__ = (
    register_start_handlers,
    register_home_handlers,
    register_user_handlers,
    register_teacher_handlers,
    register_admin_handlers,
    register_report_handlers,
    register_utils_handlers,
    register_system_handlers,
)
