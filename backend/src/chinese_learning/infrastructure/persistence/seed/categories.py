from chinese_learning.domain.category.category import Category, CategoryId, CategoryType

# Fixed UUIDs so the seed is deterministic across environments
HSK_1_ID = CategoryId("a1000000-0000-4000-8000-000000000001")
HSK_2_ID = CategoryId("a1000000-0000-4000-8000-000000000002")
HSK_3_ID = CategoryId("a1000000-0000-4000-8000-000000000003")
HSK_4_ID = CategoryId("a1000000-0000-4000-8000-000000000004")
HSK_5_ID = CategoryId("a1000000-0000-4000-8000-000000000005")
HSK_6_ID = CategoryId("a1000000-0000-4000-8000-000000000006")
HSK_7_9_ID = CategoryId("a1000000-0000-4000-8000-000000000007")

UNCATEGORISED_ID = CategoryId("c1000000-0000-4000-8000-000000000001")

TOPICS_ID = CategoryId("b1000000-0000-4000-8000-000000000001")
FOOD_ID = CategoryId("b1000000-0000-4000-8000-000000000002")
TRAVEL_ID = CategoryId("b1000000-0000-4000-8000-000000000003")
DAILY_LIFE_ID = CategoryId("b1000000-0000-4000-8000-000000000004")
EDUCATION_ID = CategoryId("b1000000-0000-4000-8000-000000000005")


BASIC_CATEGORIES: list[Category] = [
    # ------------------------------------------------------------------
    # HSK levels (system-managed)
    # hsk_level 7 represents the combined HSK 7-9 band
    # ------------------------------------------------------------------
    Category(
        id=HSK_1_ID,
        name="HSK 1",
        type=CategoryType.HSK,
        parent_id=None,
        sort_order=1,
        hsk_level=1,
    ),
    Category(
        id=HSK_2_ID,
        name="HSK 2",
        type=CategoryType.HSK,
        parent_id=None,
        sort_order=2,
        hsk_level=2,
    ),
    Category(
        id=HSK_3_ID,
        name="HSK 3",
        type=CategoryType.HSK,
        parent_id=None,
        sort_order=3,
        hsk_level=3,
    ),
    Category(
        id=HSK_4_ID,
        name="HSK 4",
        type=CategoryType.HSK,
        parent_id=None,
        sort_order=4,
        hsk_level=4,
    ),
    Category(
        id=HSK_5_ID,
        name="HSK 5",
        type=CategoryType.HSK,
        parent_id=None,
        sort_order=5,
        hsk_level=5,
    ),
    Category(
        id=HSK_6_ID,
        name="HSK 6",
        type=CategoryType.HSK,
        parent_id=None,
        sort_order=6,
        hsk_level=6,
    ),
    Category(
        id=HSK_7_9_ID,
        name="HSK 7-9",
        type=CategoryType.HSK,
        parent_id=None,
        sort_order=7,
        hsk_level=7,
    ),
    # ------------------------------------------------------------------
    # System fallback
    # ------------------------------------------------------------------
    Category(
        id=UNCATEGORISED_ID,
        name="Uncategorised",
        type=CategoryType.SYSTEM,
        parent_id=None,
        sort_order=999,
        hsk_level=None,
    ),
    # ------------------------------------------------------------------
    # Topic hierarchy (user-facing)
    # ------------------------------------------------------------------
    Category(
        id=TOPICS_ID,
        name="Topics",
        type=CategoryType.TOPIC,
        parent_id=None,
        sort_order=10,
        hsk_level=None,
    ),
    Category(
        id=FOOD_ID,
        name="Food",
        type=CategoryType.TOPIC,
        parent_id=TOPICS_ID,
        sort_order=1,
        hsk_level=None,
    ),
    Category(
        id=TRAVEL_ID,
        name="Travel",
        type=CategoryType.TOPIC,
        parent_id=TOPICS_ID,
        sort_order=2,
        hsk_level=None,
    ),
    Category(
        id=DAILY_LIFE_ID,
        name="Daily Life",
        type=CategoryType.TOPIC,
        parent_id=TOPICS_ID,
        sort_order=3,
        hsk_level=None,
    ),
    Category(
        id=EDUCATION_ID,
        name="Education",
        type=CategoryType.TOPIC,
        parent_id=TOPICS_ID,
        sort_order=4,
        hsk_level=None,
    ),
]
