"""All user-facing strings and label constants.

Handlers import from here so there are no hardcoded strings buried in logic.
Plain ASCII keys, emoji allowed in values (Telegram renders UTF-8).
"""

from __future__ import annotations

# --- Reply menu buttons -----------------------------------------------------
BTN_CATALOG = "🛍 Catalog"
BTN_CART = "🛒 Cart"
BTN_ORDERS = "📦 Orders"
BTN_SUPPORT = "💬 Support"

# --- Inline button labels ---------------------------------------------------
BTN_ADD_TO_CART = "➕ Add to cart"
BTN_VIEW_CART = "🛒 View cart"
BTN_REMOVE = "❌ Remove"
BTN_CLEAR_CART = "🗑 Clear cart"
BTN_CHECKOUT = "✅ Checkout"
BTN_CONTINUE_SHOPPING = "⬅️ Continue shopping"
BTN_BACK = "⬅️ Back"
BTN_PREV = "◀️"
BTN_NEXT = "▶️"

# --- Payment methods --------------------------------------------------------
PAYMENT_METHODS: dict[str, str] = {
    "click": "💳 Click",
    "payme": "💳 Payme",
    "cash": "💵 Cash on delivery",
}

# --- Greetings / menus ------------------------------------------------------
WELCOME = (
    "👋 <b>Welcome to the shop!</b>\n\n"
    "Browse the catalog, manage your cart and place orders right here.\n"
    "Use the menu below to get started."
)
MAIN_MENU_PROMPT = "Choose an option:"

# --- Catalog ----------------------------------------------------------------
CATEGORIES_TITLE = "🛍 <b>Categories</b>\nPick a category:"
NO_CATEGORIES = "No categories available yet."
PRODUCTS_TITLE = "🛍 <b>{category}</b>\nPage {page} of {pages}:"
NO_PRODUCTS = "No products in this category yet."
PRODUCT_DETAIL = (
    "<b>{name}</b>\n\n"
    "{description}\n\n"
    "💰 Price: <b>{price} {currency}</b>\n"
    "📦 In stock: {stock}"
)
NO_DESCRIPTION = "No description."
PRODUCT_NOT_FOUND = "Product not found."

# --- Cart -------------------------------------------------------------------
CART_TITLE = "🛒 <b>Your cart</b>"
CART_EMPTY = "🛒 Your cart is empty.\nBrowse the catalog to add items."
CART_LINE = "• <b>{name}</b> — {quantity} × {unit_price} = {line_total} {currency}"
CART_TOTAL = "\n<b>Total: {subtotal} {currency}</b> ({total_items} item(s))"
CART_ITEM_ADDED = "✅ Added to cart."
CART_ITEM_REMOVED = "❌ Removed from cart."
CART_CLEARED = "🗑 Cart cleared."

# --- Checkout ---------------------------------------------------------------
CHECKOUT_ASK_ADDRESS = (
    "🏠 <b>Checkout</b>\n\nPlease send your <b>delivery address</b> "
    "(street, building, city)."
)
CHECKOUT_ASK_PHONE = "📞 Now send your <b>contact phone number</b>."
CHECKOUT_ASK_PAYMENT = "💳 Choose a <b>payment method</b>:"
CHECKOUT_INVALID_ADDRESS = "Please send a valid address (at least 5 characters)."
CHECKOUT_INVALID_PHONE = "Please send a valid phone number."
CHECKOUT_EMPTY_CART = "Your cart is empty — add items before checking out."
ORDER_CREATED = (
    "🎉 <b>Order placed!</b>\n\n"
    "Order <code>{order_id}</code>\n"
    "Status: {status}\n"
    "Total: <b>{total} {currency}</b>\n"
    "Payment: {payment}\n\n"
    "Thank you for your purchase!"
)

# --- Orders -----------------------------------------------------------------
ORDERS_TITLE = "📦 <b>Your orders</b>"
NO_ORDERS = "You have no orders yet."
ORDER_BUTTON = "{emoji} {short_id} — {total} {currency}"
ORDER_DETAIL = (
    "📦 <b>Order {short_id}</b>\n\n"
    "Status: {emoji} <b>{status}</b>\n"
    "Total: <b>{total} {currency}</b>\n"
    "Placed: {created_at}\n\n"
    "<b>Items:</b>\n{items}"
)
ORDER_ITEM_LINE = "• {name} — {quantity} × {unit_price}"

STATUS_EMOJI: dict[str, str] = {
    "pending": "🕓",
    "confirmed": "✅",
    "paid": "💰",
    "processing": "⚙️",
    "shipped": "🚚",
    "delivered": "📬",
    "cancelled": "❌",
    "refunded": "↩️",
}

# --- Support ----------------------------------------------------------------
SUPPORT_PROMPT = (
    "💬 <b>Support</b>\n\nSend your message and our team will get back to you."
)
SUPPORT_SENT = "✅ Your message has been sent to support. Thank you!"
SUPPORT_NOT_CONFIGURED = "Support is not available right now. Please try later."
SUPPORT_FORWARD_HEADER = (
    "💬 <b>Support request</b>\n"
    "From: {user} (id <code>{user_id}</code>)\n\n{text}"
)

# --- Errors -----------------------------------------------------------------
SERVICE_UNAVAILABLE = "⚠️ Service temporarily unavailable. Please try again later."
GENERIC_ERROR = "⚠️ Something went wrong. Please try again."
THROTTLED = "⏳ You're going too fast. Please slow down a little."
