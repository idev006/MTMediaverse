"""
Global Store - จัดการ State กลางของ Application

คล้าย Vuex/Pinia ใน Vue.js
- Centralized state
- Getters
- Mutations (actions)
- Subscriptions for reactive updates

Usage:
    from app.gui.store import get_store
    
    store = get_store()
    
    # Read state
    products = store.state.products
    
    # Update state
    store.commit('set_products', [p1, p2, p3])
    
    # Subscribe to changes
    store.subscribe('products', lambda val: print(f'Products changed: {val}'))
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
import threading

from PySide6.QtCore import QObject, Signal


@dataclass
class AppState:
    """Application state container."""
    
    # Stats
    product_count: int = 0
    clip_count: int = 0
    order_count: int = 0
    client_count: int = 0
    
    # Data lists
    products: List[Dict] = field(default_factory=list)
    orders: List[Dict] = field(default_factory=list)
    clients: List[Dict] = field(default_factory=list)
    
    # Current selections
    selected_product_id: Optional[int] = None
    selected_order_id: Optional[int] = None
    selected_client_code: Optional[str] = None
    
    # UI state
    current_tab: str = "dashboard"
    is_loading: bool = False
    last_refresh: Optional[datetime] = None
    
    # API status
    api_connected: bool = False
    api_url: str = "http://localhost:8000"


class Store(QObject):
    """
    Global Store - Centralized State Management
    
    Features:
    - Reactive state updates via Qt Signals
    - Thread-safe mutations
    - Subscription system
    """
    
    # Qt Signals for reactive updates
    state_changed = Signal(str, object)  # (key, value)
    
    _instance: Optional['Store'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'Store':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        super().__init__()
        self._state = AppState()
        self._subscribers: Dict[str, List[Callable]] = {}
        self._initialized = True
    
    # ========================================================================
    # State Access
    # ========================================================================
    
    @property
    def state(self) -> AppState:
        """Get current state (read-only access)."""
        return self._state
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a state value by key."""
        return getattr(self._state, key, default)
    
    # ========================================================================
    # Mutations
    # ========================================================================
    
    def commit(self, key: str, value: Any) -> None:
        """
        Commit a state change.
        Thread-safe and triggers reactive updates.
        """
        with self._lock:
            if hasattr(self._state, key):
                setattr(self._state, key, value)
                self._notify(key, value)
    
    def _notify(self, key: str, value: Any) -> None:
        """Notify subscribers of state change."""
        # Emit Qt Signal
        self.state_changed.emit(key, value)
        
        # Call subscribers
        if key in self._subscribers:
            for callback in self._subscribers[key]:
                try:
                    callback(value)
                except Exception as e:
                    print(f"Store subscriber error: {e}")
        
        # Notify wildcard subscribers
        if '*' in self._subscribers:
            for callback in self._subscribers['*']:
                try:
                    callback(key, value)
                except Exception as e:
                    print(f"Store subscriber error: {e}")
    
    # ========================================================================
    # Subscriptions
    # ========================================================================
    
    def subscribe(self, key: str, callback: Callable) -> Callable:
        """
        Subscribe to state changes.
        
        Args:
            key: State key to watch, or '*' for all changes
            callback: Function(value) or Function(key, value) for '*'
        
        Returns:
            Unsubscribe function
        """
        if key not in self._subscribers:
            self._subscribers[key] = []
        
        self._subscribers[key].append(callback)
        
        # Return unsubscribe function
        def unsubscribe():
            if key in self._subscribers and callback in self._subscribers[key]:
                self._subscribers[key].remove(callback)
        
        return unsubscribe
    
    def unsubscribe_all(self, key: str) -> None:
        """Unsubscribe all callbacks for a key."""
        if key in self._subscribers:
            self._subscribers[key].clear()
    
    # ========================================================================
    # Actions (Complex mutations)
    # ========================================================================
    
    def refresh_stats(self) -> None:
        """Refresh all stats from database."""
        from app.core.database import get_db, Product, MediaAsset, Order, ClientAccount
        
        db = get_db()
        session = db.get_session()
        
        try:
            self.commit('product_count', session.query(Product).count())
            self.commit('clip_count', session.query(MediaAsset).count())
            self.commit('order_count', session.query(Order).count())
            self.commit('client_count', session.query(ClientAccount).filter(
                ClientAccount.is_active == 1
            ).count())
            self.commit('last_refresh', datetime.now())
        finally:
            session.close()
    
    def load_orders(self, limit: int = 50) -> None:
        """Load orders from database."""
        from app.core.database import get_db, Order
        
        db = get_db()
        session = db.get_session()
        
        try:
            orders = session.query(Order).order_by(Order.id.desc()).limit(limit).all()
            order_list = []
            for order in orders:
                order_list.append({
                    'id': order.id,
                    'client_code': order.client.client_code if order.client else 'Unknown',
                    'platform': order.target_platform,
                    'status': order.status,
                    'item_count': len(order.items),
                    'done_count': sum(1 for i in order.items if i.status == 'done'),
                })
            self.commit('orders', order_list)
        finally:
            session.close()
    
    def load_clients(self) -> None:
        """Load clients from database."""
        from app.core.database import get_db, ClientAccount
        
        db = get_db()
        session = db.get_session()
        
        try:
            clients = session.query(ClientAccount).all()
            client_list = []
            for client in clients:
                client_list.append({
                    'id': client.id,
                    'client_code': client.client_code,
                    'platform': client.platform,
                    'is_active': bool(client.is_active),
                    'last_seen': client.last_seen.isoformat() if client.last_seen else None,
                })
            self.commit('clients', client_list)
        finally:
            session.close()
    
    def set_loading(self, loading: bool) -> None:
        """Set loading state."""
        self.commit('is_loading', loading)
    
    def select_order(self, order_id: Optional[int]) -> None:
        """Select an order."""
        self.commit('selected_order_id', order_id)
    
    def select_client(self, client_code: Optional[str]) -> None:
        """Select a client."""
        self.commit('selected_client_code', client_code)
    
    # ========================================================================
    # Getters (Computed properties)
    # ========================================================================
    
    def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        """Get order by ID from cached list."""
        orders = self._state.orders
        for order in orders:
            if order['id'] == order_id:
                return order
        return None
    
    def get_client_by_code(self, client_code: str) -> Optional[Dict]:
        """Get client by code from cached list."""
        clients = self._state.clients
        for client in clients:
            if client['client_code'] == client_code:
                return client
        return None
    
    def get_online_clients(self) -> List[Dict]:
        """Get list of online clients."""
        return [c for c in self._state.clients if c.get('is_active')]
    
    # ========================================================================
    # Utils
    # ========================================================================
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance."""
        cls._instance = None


def get_store() -> Store:
    """Get the global Store instance."""
    return Store()
