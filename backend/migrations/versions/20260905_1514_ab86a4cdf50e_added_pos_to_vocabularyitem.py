"""Added pos to VocabularyItem

Revision ID: ab86a4cdf50e
Revises: c7b0dbb4e34c
Create Date: 2026-09-05 15:14:09.740850

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab86a4cdf50e'
down_revision: Union[str, Sequence[str], None] = 'c7b0dbb4e34c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "vocabulary_items",
        sa.Column(
            "pos",
            sa.String(length=50),
            server_default="",
            nullable=False,
        ),
    )
    op.create_unique_constraint(
        "uq_vocab_text_pos",
        "vocabulary_items",
        ["text", "pos"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_vocab_text_pos", "vocabulary_items", type_="unique")
    op.drop_column("vocabulary_items", "pos")
