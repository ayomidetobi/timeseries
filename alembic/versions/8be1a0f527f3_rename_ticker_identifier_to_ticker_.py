"""rename_ticker_identifier_to_ticker_source

Revision ID: 8be1a0f527f3
Revises: b5e74380d5ca
Create Date: 2025-12-11 18:12:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "8be1a0f527f3"
down_revision = "b5e74380d5ca"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename table
    op.rename_table("ticker_identifier_lookup", "ticker_source_lookup")

    # Rename columns in ticker_source_lookup table
    op.alter_column(
        "ticker_source_lookup",
        "ticker_identifier_id",
        new_column_name="ticker_source_id",
    )
    op.alter_column(
        "ticker_source_lookup",
        "ticker_identifier_name",
        new_column_name="ticker_source_name",
    )
    op.alter_column(
        "ticker_source_lookup",
        "ticker_identifier_code",
        new_column_name="ticker_source_code",
    )

    # Rename indexes
    op.drop_index("ix_ticker_identifier_lookup_name", table_name="ticker_source_lookup")
    op.drop_index("ix_ticker_identifier_lookup_code", table_name="ticker_source_lookup")
    op.drop_index("uq_ticker_identifier_lookup_name", table_name="ticker_source_lookup")
    op.create_index(
        "ix_ticker_source_lookup_name",
        "ticker_source_lookup",
        ["ticker_source_name"],
        unique=False,
    )
    op.create_index(
        "ix_ticker_source_lookup_code",
        "ticker_source_lookup",
        ["ticker_source_code"],
        unique=False,
    )
    op.create_index(
        "uq_ticker_source_lookup_name",
        "ticker_source_lookup",
        ["ticker_source_name"],
        unique=True,
    )

    # Rename column in meta_series table
    op.alter_column(
        "meta_series", "ticker_identifier_id", new_column_name="ticker_source_id"
    )

    # Rename index in meta_series
    op.drop_index("ix_meta_series_ticker_identifier", table_name="meta_series")
    op.create_index(
        "ix_meta_series_ticker_source",
        "meta_series",
        ["ticker_source_id"],
        unique=False,
    )

    # Rename foreign key constraint
    op.drop_constraint(
        "fk_meta_series_ticker_identifier", "meta_series", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_meta_series_ticker_source",
        "meta_series",
        "ticker_source_lookup",
        ["ticker_source_id"],
        ["ticker_source_id"],
    )


def downgrade() -> None:
    # Rename foreign key constraint back
    op.drop_constraint(
        "fk_meta_series_ticker_source", "meta_series", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_meta_series_ticker_identifier",
        "meta_series",
        "ticker_identifier_lookup",
        ["ticker_identifier_id"],
        ["ticker_identifier_id"],
    )

    # Rename index in meta_series back
    op.drop_index("ix_meta_series_ticker_source", table_name="meta_series")
    op.create_index(
        "ix_meta_series_ticker_identifier",
        "meta_series",
        ["ticker_identifier_id"],
        unique=False,
    )

    # Rename column in meta_series back
    op.alter_column(
        "meta_series", "ticker_source_id", new_column_name="ticker_identifier_id"
    )

    # Rename indexes back
    op.drop_index("uq_ticker_source_lookup_name", table_name="ticker_source_lookup")
    op.drop_index("ix_ticker_source_lookup_code", table_name="ticker_source_lookup")
    op.drop_index("ix_ticker_source_lookup_name", table_name="ticker_source_lookup")
    op.create_index(
        "uq_ticker_identifier_lookup_name",
        "ticker_source_lookup",
        ["ticker_identifier_name"],
        unique=True,
    )
    op.create_index(
        "ix_ticker_identifier_lookup_code",
        "ticker_source_lookup",
        ["ticker_identifier_code"],
        unique=False,
    )
    op.create_index(
        "ix_ticker_identifier_lookup_name",
        "ticker_source_lookup",
        ["ticker_identifier_name"],
        unique=False,
    )

    # Rename columns in ticker_source_lookup table back
    op.alter_column(
        "ticker_source_lookup",
        "ticker_source_code",
        new_column_name="ticker_identifier_code",
    )
    op.alter_column(
        "ticker_source_lookup",
        "ticker_source_name",
        new_column_name="ticker_identifier_name",
    )
    op.alter_column(
        "ticker_source_lookup",
        "ticker_source_id",
        new_column_name="ticker_identifier_id",
    )

    # Rename table back
    op.rename_table("ticker_source_lookup", "ticker_identifier_lookup")
