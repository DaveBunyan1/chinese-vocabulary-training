from chinese_learning.domain.category.category import Category, CategoryId

# Fixed UUIDs so the seed is deterministic across environments
HSK_1_ID = CategoryId("a1000000-0000-4000-8000-000000000001")
HSK_2_ID = CategoryId("a1000000-0000-4000-8000-000000000002")
HSK_3_ID = CategoryId("a1000000-0000-4000-8000-000000000003")
HSK_4_ID = CategoryId("a1000000-0000-4000-8000-000000000004")
HSK_5_ID = CategoryId("a1000000-0000-4000-8000-000000000005")
HSK_6_ID = CategoryId("a1000000-0000-4000-8000-000000000006")

TOPICS_ID = CategoryId("b1000000-0000-4000-8000-000000000001")
FOOD_ID = CategoryId("b1000000-0000-4000-8000-000000000002")
TRAVEL_ID = CategoryId("b1000000-0000-4000-8000-000000000003")
DAILY_LIFE_ID = CategoryId("b1000000-0000-4000-8000-000000000004")
EDUCATION_ID = CategoryId("b1000000-0000-4000-8000-000000000005")


BASIC_CATEGORIES: list[Category] = [
    # HSK levels (top-level)
    Category(id=HSK_1_ID, name="HSK 1", parent_id=None, sort_order=1),
    Category(id=HSK_2_ID, name="HSK 2", parent_id=None, sort_order=2),
    Category(id=HSK_3_ID, name="HSK 3", parent_id=None, sort_order=3),
    Category(id=HSK_4_ID, name="HSK 4", parent_id=None, sort_order=4),
    Category(id=HSK_5_ID, name="HSK 5", parent_id=None, sort_order=5),
    Category(id=HSK_6_ID, name="HSK 6", parent_id=None, sort_order=6),
    # Topic hierarchy
    Category(id=TOPICS_ID, name="Topics", parent_id=None, sort_order=10),
    Category(id=FOOD_ID, name="Food", parent_id=TOPICS_ID, sort_order=1),
    Category(id=TRAVEL_ID, name="Travel", parent_id=TOPICS_ID, sort_order=2),
    Category(id=DAILY_LIFE_ID, name="Daily Life", parent_id=TOPICS_ID, sort_order=3),
    Category(id=EDUCATION_ID, name="Education", parent_id=TOPICS_ID, sort_order=4),
]
