# GUI Components Package - Vue.js style
# Each component is a separate file

from .stats_card import StatsCard
from .order_table import OrderTable
from .client_table import ClientTable
from .dashboard_panel import DashboardPanel
from .settings_panel import SettingsPanel

__all__ = [
    'StatsCard',
    'OrderTable', 
    'ClientTable',
    'DashboardPanel',
    'SettingsPanel',
]
