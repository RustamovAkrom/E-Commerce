export type Money = number | string;
export type UserRole = "customer" | "vendor" | "operator" | "courier" | "admin" | "superadmin";
export type OrderStatus = "pending" | "confirmed" | "paid" | "processing" | "shipped" | "delivered" | "cancelled" | "refunded";
export type PaymentStatus = "pending" | "processing" | "paid" | "failed" | "refunded";
export type PaymentProvider = "click" | "payme" | "stripe";
export type ShippingMethod = "standard" | "express" | "pickup";
export type ShipmentStatus = "pending" | "label_created" | "in_transit" | "delivered" | "returned" | "cancelled";

export interface ApiErrorBody { error?: string; message?: string; details?: Record<string, unknown> }
export interface MessageResponse { message: string }
export interface Page<T> { items: T[]; total: number; page: number; size: number; pages: number }
export interface PaginationQuery { page?: number; size?: number }

export interface User { id: string; email: string; full_name: string | null; phone: string | null; role: UserRole; is_active: boolean; is_verified: boolean; created_at: string }
export interface LoginRequest { email: string; password: string }
export interface RegisterRequest { email: string; password: string; full_name?: string | null; phone?: string | null }
export interface TokenPair { access_token: string; refresh_token: string; token_type: string; expires_in: number }
export interface AuthResult { user: User; tokens: TokenPair }
export interface UserUpdateRequest { full_name?: string | null; phone?: string | null }
export interface PasswordChangeRequest { current_password: string; new_password: string }
export interface UserAdminUpdateRequest { role?: UserRole; is_active?: boolean; is_verified?: boolean }

export interface Category { id: string; name: string; slug: string; description: string | null; parent_id: string | null; sort_order: number; is_active: boolean }
export interface CategoryCreate { name: string; slug: string; description?: string | null; parent_id?: string | null; sort_order?: number; is_active?: boolean }
export interface CategoryUpdate { name?: string; description?: string | null; parent_id?: string | null; sort_order?: number; is_active?: boolean }

export interface ProductImage { id: string; url: string; is_primary: boolean; sort_order: number }
export interface ProductAttribute { id: string; key: string; value: string }
export interface Product { id: string; vendor_id: string | null; category_id: string; name: string; slug: string; description: string | null; sku: string | null; price: Money; currency: string; stock: number; is_active: boolean; created_at: string }
export interface ProductDetail extends Product { images: ProductImage[]; attributes: ProductAttribute[] }
export interface ProductWrite { category_id: string; vendor_id?: string | null; name: string; slug: string; description?: string | null; sku?: string | null; price: number; currency?: string; stock?: number; is_active?: boolean; attributes?: Array<{ key: string; value: string }> }
export type ProductUpdate = Partial<Omit<ProductWrite, "vendor_id" | "currency" | "attributes">>;
export interface ProductQuery extends PaginationQuery { search?: string; category_id?: string; vendor_id?: string; min_price?: number; max_price?: number; in_stock?: boolean; is_active?: boolean; sort?: "created_at" | "-created_at" | "price" | "-price" | "name" | "-name" }

export interface CartItem { product_id: string; name: string; slug: string; unit_price: Money; currency: string; quantity: number; line_total: Money; available_stock: number }
export interface Cart { items: CartItem[]; total_items: number; subtotal: Money; currency: string }
export interface CartItemRequest { product_id: string; quantity: number }

export interface ShippingAddressInput { full_name: string; phone: string; address: string; city: string; country: string; postal_code?: string | null }
export interface Address extends ShippingAddressInput { id: string; user_id: string; label: string | null; is_default: boolean; created_at: string }
export interface AddressCreate extends ShippingAddressInput { label?: string | null; is_default?: boolean }
export type AddressUpdate = Partial<AddressCreate>;
export interface OrderItem { id: string; product_id: string; product_name: string; quantity: number; unit_price: Money }
export interface Order { id: string; user_id: string; status: OrderStatus; total_amount: Money; currency: string; shipping_address: ShippingAddressInput; note: string | null; created_at: string }
export interface OrderDetail extends Order { items: OrderItem[] }
export interface OrderCreate { shipping_address: ShippingAddressInput; note?: string | null }
export interface OrderStatusUpdate { status: OrderStatus }

export interface PaymentInitRequest { order_id: string; provider: PaymentProvider; return_url?: string | null }
export interface PaymentInitResponse { payment_id: string; provider: PaymentProvider; status: PaymentStatus; amount: Money; currency: string; checkout_url: string | null; params: Record<string, unknown> }

export interface DashboardStats { total_users: number; total_products: number; active_products: number; total_orders: number; total_revenue: Money; pending_orders: number; low_stock_products: number }
export interface OrderStatusBreakdown { status: OrderStatus; count: number }
export interface RevenuePoint { date: string; order_count: number; revenue: Money }
export interface SalesOverview { period_days: number; total_revenue: Money; order_count: number; points: RevenuePoint[] }

export interface Courier { id: string; user_id: string; phone: string | null; zone: string | null; is_active: boolean }
export interface CourierCreate { user_id: string; phone?: string | null; zone?: string | null }
export interface CourierUpdate { phone?: string | null; zone?: string | null; is_active?: boolean }
export interface DeliveryAssignment { id: string; order_id: string; courier_id: string | null; courier_name: string | null; status: string; created_at: string }

export interface VendorPublic { id: string; name: string; slug: string; description: string | null; is_active: boolean; created_at: string }
export interface VendorResponse extends VendorPublic { user_id: string; status: string; commission_rate: number }
export interface VendorApplyRequest { business_name: string; description?: string | null }
export interface VendorUpdateRequest { business_name?: string; description?: string | null; commission_rate?: number }
export interface VendorAdminUpdateRequest { status?: string; is_active?: boolean }

export interface Review { id: string; product_id: string; user_id: string; rating: number; title: string | null; comment: string | null; is_approved: boolean; created_at: string }
export interface ReviewCreate { rating: number; title?: string | null; comment?: string | null }
export interface ReviewUpdate { rating?: number; title?: string | null; comment?: string | null }
export interface ReviewModerate { is_approved: boolean }
export interface ProductRatingSummary { product_id: string; average_rating: number; review_count: number }
