"""Catalog browsing: categories -> products (paginated) -> product detail."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import (
    CategoryCB,
    NavCB,
    ProductCB,
    ProductsPageCB,
    back_kb,
    categories_kb,
    product_detail_kb,
    products_kb,
)
from bot.services.api_client import AsyncAPIClient
from bot.texts import (
    BTN_CATALOG,
    CATEGORIES_TITLE,
    NO_CATEGORIES,
    NO_DESCRIPTION,
    NO_PRODUCTS,
    PRODUCT_DETAIL,
    PRODUCTS_TITLE,
)

router = Router(name="catalog")

_PRODUCTS_LABEL = "Products"


async def _show_categories(message: Message, api: AsyncAPIClient) -> None:
    categories = await api.get_categories()
    if not categories:
        await message.answer(NO_CATEGORIES)
        return
    await message.answer(CATEGORIES_TITLE, reply_markup=categories_kb(categories))


@router.message(F.text == BTN_CATALOG)
async def open_catalog(message: Message, api: AsyncAPIClient) -> None:
    await _show_categories(message, api)


@router.callback_query(NavCB.filter(F.to == "catalog"))
async def back_to_catalog(callback: CallbackQuery, api: AsyncAPIClient) -> None:
    categories = await api.get_categories()
    if isinstance(callback.message, Message):
        if categories:
            await callback.message.edit_text(
                CATEGORIES_TITLE, reply_markup=categories_kb(categories)
            )
        else:
            await callback.message.edit_text(NO_CATEGORIES)
    await callback.answer()


async def _render_products(
    callback: CallbackQuery, api: AsyncAPIClient, category_id: str, page: int
) -> None:
    page_data = await api.get_products(category_id=category_id, page=page)
    if not isinstance(callback.message, Message):
        return
    if not page_data["items"]:
        await callback.message.edit_text(
            NO_PRODUCTS, reply_markup=back_kb("catalog")
        )
        return
    text = PRODUCTS_TITLE.format(
        category=_PRODUCTS_LABEL,
        page=page_data["page"],
        pages=page_data["pages"],
    )
    await callback.message.edit_text(
        text, reply_markup=products_kb(page_data, category_id)
    )


@router.callback_query(CategoryCB.filter())
async def open_category(
    callback: CallbackQuery, callback_data: CategoryCB, api: AsyncAPIClient
) -> None:
    await _render_products(callback, api, callback_data.category_id, 1)
    await callback.answer()


@router.callback_query(ProductsPageCB.filter())
async def paginate_products(
    callback: CallbackQuery, callback_data: ProductsPageCB, api: AsyncAPIClient
) -> None:
    await _render_products(
        callback, api, callback_data.category_id, callback_data.page
    )
    await callback.answer()


@router.callback_query(ProductCB.filter())
async def open_product(
    callback: CallbackQuery, callback_data: ProductCB, api: AsyncAPIClient
) -> None:
    product = await api.get_product(callback_data.slug)
    text = PRODUCT_DETAIL.format(
        name=product["name"],
        description=product.get("description") or NO_DESCRIPTION,
        price=product["price"],
        currency=product["currency"],
        stock=product["stock"],
    )
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text, reply_markup=product_detail_kb(product)
        )
    await callback.answer()
