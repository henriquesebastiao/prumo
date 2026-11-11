"""Installed modules.

The order of this list is the default navigation and dashboard order for new users. Add a module
by importing its package and appending `<package>.module` here (see docs/novo-modulo.md).
Current order: finance, garage, reading, studies, habits.
"""

from prumo.core.modules import PrumoModule
from prumo.modules import finance, garage, habits, reading, studies

INSTALLED_MODULES: list[PrumoModule] = [
    finance.module,
    garage.module,
    reading.module,
    studies.module,
    habits.module,
]
