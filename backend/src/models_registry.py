"""Central import point for every ORM model.

Importing this module guarantees that all models are registered on
``Base.metadata`` — required for Alembic autogenerate and for ``create_all``
in tests. Add new model modules here.
"""

from __future__ import annotations

from src.core.database import Base  # re-exported for convenience

# Import side-effects register each model on Base.metadata.
from src.modules.users.models import User  # noqa: F401
from src.modules.catalog.models import (  # noqa: F401
    Category,
    Product,
    ProductAttribute,
    ProductImage,
)
from src.modules.inventory.models import StockMovement  # noqa: F401
from src.modules.orders.models import Order, OrderItem  # noqa: F401
from src.modules.payments.models import Payment  # noqa: F401
from src.modules.shipping.models import Shipment, ShippingAddress  # noqa: F401
from src.modules.reviews.models import Review  # noqa: F401
from src.modules.notifications.models import Notification  # noqa: F401
from src.modules.vendors.models import Vendor  # noqa: F401  (defined always; wired conditionally)

__all__ = ["Base"]
