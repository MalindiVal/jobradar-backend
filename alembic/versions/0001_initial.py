from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("search_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("locations", sa.JSON(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("duration_months", sa.Integer(), nullable=False),
        sa.Column("contract_type", sa.String(100), nullable=False))
    op.create_table("offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("company", sa.String(200), nullable=False),
        sa.Column("location", sa.String(200), nullable=False),
        sa.Column("contract_type", sa.String(100), nullable=False),
        sa.Column("duration_months", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(80), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("deduplication_key", sa.String(64), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("match_explanation", sa.Text(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("is_favorite", sa.Boolean(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("deduplication_key", name="uq_offer_deduplication_key"))
    op.create_index("ix_offers_title", "offers", ["title"])
    op.create_index("ix_offers_source", "offers", ["source"])
    op.create_index("ix_offers_deduplication_key", "offers", ["deduplication_key"])
    op.create_index("ix_offers_status", "offers", ["status"])
    op.create_table("collection_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("found_count", sa.Integer(), nullable=False),
        sa.Column("new_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table("notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("recipient", sa.String(320), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_notifications_offer_id", "notifications", ["offer_id"])

def downgrade():
    op.drop_table("notifications")
    op.drop_table("collection_runs")
    op.drop_index("ix_offers_status", table_name="offers")
    op.drop_index("ix_offers_deduplication_key", table_name="offers")
    op.drop_index("ix_offers_source", table_name="offers")
    op.drop_index("ix_offers_title", table_name="offers")
    op.drop_table("offers")
    op.drop_table("search_profiles")
