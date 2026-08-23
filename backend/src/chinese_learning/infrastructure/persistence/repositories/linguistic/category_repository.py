from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.category.category import Category, CategoryId, CategoryType
from chinese_learning.infrastructure.persistence.mappers.linguistic_mappers import (
    category_to_domain,
)
from chinese_learning.infrastructure.persistence.models import CategoryModel
from chinese_learning.infrastructure.persistence.repositories.repo_utils import (
    logger,
    record_repo_metric,
)


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, category_id: CategoryId) -> Category | None:
        record_repo_metric("get", entity="category")
        stmt = select(CategoryModel).where(CategoryModel.id == str(category_id.value))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return category_to_domain(model) if model else None

    async def save(self, category: Category) -> None:
        record_repo_metric("save", entity="category")
        await self.save_many([category])

    async def save_many(self, categories: Sequence[Category]) -> None:
        if not categories:
            return

        record_repo_metric("save_many", entity="category")
        values = [
            {
                "id": str(c.id.value),
                "name": c.name,
                "type": c.type.value,
                "parent_id": str(c.parent_id.value) if c.parent_id else None,
                "sort_order": c.sort_order,
                "hsk_level": c.hsk_level,
            }
            for c in categories
        ]

        stmt = pg_insert(CategoryModel).values(values)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": stmt.excluded.name,
                "type": stmt.excluded.type,
                "parent_id": stmt.excluded.parent_id,
                "sort_order": stmt.excluded.sort_order,
                "hsk_level": stmt.excluded.hsk_level,
            },
        )
        await self.session.execute(upsert_stmt)

        logger.info("category.saved_many", count=len(categories))

    async def get_children(self, parent_id: CategoryId | None) -> list[Category]:
        record_repo_metric("get_children", entity="category")
        if parent_id is None:
            stmt = (
                select(CategoryModel)
                .where(CategoryModel.parent_id.is_(None))
                .order_by(CategoryModel.sort_order)
            )
        else:
            stmt = (
                select(CategoryModel)
                .where(CategoryModel.parent_id == str(parent_id.value))
                .order_by(CategoryModel.sort_order)
            )
        result = await self.session.execute(stmt)
        return [category_to_domain(m) for m in result.scalars().all()]

    async def get_all(self) -> list[Category]:
        record_repo_metric("get_all", entity="category")
        stmt = select(CategoryModel).order_by(
            CategoryModel.sort_order, CategoryModel.name
        )
        result = await self.session.execute(stmt)
        return [category_to_domain(m) for m in result.scalars().all()]

    async def exists(self, category_id: CategoryId) -> bool:
        record_repo_metric("exists", entity="category")
        stmt = select(func.count(1)).where(CategoryModel.id == str(category_id.value))
        result = await self.session.execute(stmt)
        return bool(result.scalar_one())

    async def get_hsk_categories(self) -> Sequence[Category]:
        record_repo_metric("get_hsk_categories", entity="category")
        stmt = (
            select(CategoryModel)
            .where(CategoryModel.type == CategoryType.HSK.value)
            .order_by(CategoryModel.hsk_level)
        )
        result = await self.session.execute(stmt)
        return [category_to_domain(m) for m in result.scalars().all()]

    async def get_uncategorised(self) -> Category:
        record_repo_metric("get_uncategorised", entity="category")
        stmt = select(CategoryModel).where(
            CategoryModel.type == CategoryType.SYSTEM.value,
            CategoryModel.name == "Uncategorised",
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise RuntimeError(
                "System category 'Uncategorised' is missing – run seed data"
            )
        return category_to_domain(row)

    async def list_by_type(self, category_type: CategoryType) -> Sequence[Category]:
        record_repo_metric("list_by_type", entity="category")
        stmt = (
            select(CategoryModel)
            .where(CategoryModel.type == category_type.value)
            .order_by(CategoryModel.sort_order, CategoryModel.name)
        )
        result = await self.session.execute(stmt)
        return [category_to_domain(m) for m in result.scalars().all()]

    async def delete(self, category_id: CategoryId) -> None:
        record_repo_metric("delete", entity="category")
        stmt = select(CategoryModel).where(CategoryModel.id == category_id.value)
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj:
            await self.session.delete(obj)
            logger.info("category.deleted", category_id=category_id.value)
