# GUI Components Package - Vue.js style
# Each component is a separate file

from .stats_card import StatsCard
from .order_table import OrderTable
from .client_table import ClientTable
from .dashboard_panel import DashboardPanel
from .settings_panel import SettingsPanel
from .products_panel import ProductsPanel
from .orders_panel import OrdersPanel
from .clients_panel import ClientsPanel

__all__ = [
    'StatsCard',
    'OrderTable', 
    'ClientTable',
    'DashboardPanel',
    'SettingsPanel',
    'ProductsPanel',
    'OrdersPanel',
    'ClientsPanel',
]
