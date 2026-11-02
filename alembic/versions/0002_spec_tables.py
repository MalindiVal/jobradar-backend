"""Tables du cahier des charges : users, sources, offer_skills, applications, collection_logs.

Reprend les données existantes (sources et compétences des offres) et recalcule les clés
de déduplication à partir de l'URL canonique.
"""
from alembic import op
import sqlalchemy as sa
from app.services.dedup import dedup_key

revision = "0002_spec_tables"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()

    op.create_table("users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    with op.batch_alter_table("search_profiles") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_search_profiles_user_id", "users", ["user_id"], ["id"], ondelete="CASCADE")
        batch.create_index("ix_search_profiles_user_id", ["user_id"])

    # sources : une ligne par valeur distincte de offers.source
    op.create_table("sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_sources_name", "sources", ["name"], unique=True)
    op.add_column("offers", sa.Column("source_id", sa.Integer(), nullable=True))
    source_ids = {}
    for (raw,) in conn.execute(sa.text("SELECT DISTINCT source FROM offers")).all():
        name = (raw or "manual").strip().lower() or "manual"
        if name not in source_ids:
            source_ids[name] = conn.execute(sa.text(
                "INSERT INTO sources (name, label, base_url, is_enabled, created_at) "
                "VALUES (:n, :l, '', true, CURRENT_TIMESTAMP) RETURNING id"), {"n": name, "l": name.capitalize()}).scalar_one()
        conn.execute(sa.text("UPDATE offers SET source_id = :sid WHERE source = :raw"),
                     {"sid": source_ids[name], "raw": raw})

    # offer_skills : éclate la colonne JSON offers.skills
    op.create_table("offer_skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("offer_id", sa.Integer(), sa.ForeignKey("offers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.UniqueConstraint("offer_id", "name", name="uq_offer_skill"))
    op.create_index("ix_offer_skills_offer_id", "offer_skills", ["offer_id"])
    op.create_index("ix_offer_skills_name", "offer_skills", ["name"])
    offers = sa.table("offers", sa.column("id", sa.Integer()), sa.column("skills", sa.JSON()))
    skills_table = sa.table("offer_skills", sa.column("offer_id", sa.Integer()), sa.column("name", sa.String()))
    rows = []
    for offer_id, skills in conn.execute(sa.select(offers.c.id, offers.c.skills)).all():
        seen = set()
        for skill in skills or []:
            skill = str(skill).strip()[:100]
            if skill and skill.lower() not in seen:
                seen.add(skill.lower()); rows.append({"offer_id": offer_id, "name": skill})
    if rows:
        op.bulk_insert(skills_table, rows)

    with op.batch_alter_table("offers") as batch:
        batch.alter_column("source_id", existing_type=sa.Integer(), nullable=False)
        batch.create_foreign_key("fk_offers_source_id", "sources", ["source_id"], ["id"])
        batch.create_index("ix_offers_source_id", ["source_id"])
        batch.drop_index("ix_offers_source")
        batch.drop_column("source")
        batch.drop_column("skills")

    # Recalcul des clés de déduplication ; en cas de collision on garde l'ancienne clé.
    full = sa.table("offers", sa.column("id", sa.Integer()), sa.column("title", sa.String()),
                    sa.column("company", sa.String()), sa.column("location", sa.String()),
                    sa.column("source_url", sa.Text()), sa.column("deduplication_key", sa.String()))
    existing = conn.execute(sa.select(full).order_by(full.c.id)).mappings().all()
    taken = {row["deduplication_key"] for row in existing}
    for row in existing:
        new_key = dedup_key(dict(row))
        if new_key != row["deduplication_key"] and new_key not in taken:
            conn.execute(full.update().where(full.c.id == row["id"]).values(deduplication_key=new_key))
            taken.discard(row["deduplication_key"]); taken.add(new_key)

    op.rename_table("collection_runs", "collection_logs")

    conn.execute(sa.text("DELETE FROM notifications WHERE offer_id NOT IN (SELECT id FROM offers)"))
    with op.batch_alter_table("notifications") as batch:
        batch.create_foreign_key("fk_notifications_offer_id", "offers", ["offer_id"], ["id"], ondelete="CASCADE")

    op.create_table("applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("offer_id", sa.Integer(), sa.ForeignKey("offers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_applications_offer_id", "applications", ["offer_id"], unique=True)
    op.create_index("ix_applications_user_id", "applications", ["user_id"])
    op.create_index("ix_applications_status", "applications", ["status"])

def downgrade():
    conn = op.get_bind()
    op.drop_table("applications")
    with op.batch_alter_table("notifications") as batch:
        batch.drop_constraint("fk_notifications_offer_id", type_="foreignkey")
    op.rename_table("collection_logs", "collection_runs")

    with op.batch_alter_table("offers") as batch:
        batch.add_column(sa.Column("source", sa.String(80), nullable=True))
        batch.add_column(sa.Column("skills", sa.JSON(), nullable=True))
    conn.execute(sa.text("UPDATE offers SET source = (SELECT name FROM sources WHERE sources.id = offers.source_id)"))
    offers = sa.table("offers", sa.column("id", sa.Integer()), sa.column("skills", sa.JSON()))
    skills = {}
    for offer_id, name in conn.execute(sa.text("SELECT offer_id, name FROM offer_skills ORDER BY id")).all():
        skills.setdefault(offer_id, []).append(name)
    for (offer_id,) in conn.execute(sa.text("SELECT id FROM offers")).all():
        conn.execute(offers.update().where(offers.c.id == offer_id).values(skills=skills.get(offer_id, [])))
    with op.batch_alter_table("offers") as batch:
        batch.alter_column("source", existing_type=sa.String(80), nullable=False)
        batch.alter_column("skills", existing_type=sa.JSON(), nullable=False)
        batch.create_index("ix_offers_source", ["source"])
        batch.drop_index("ix_offers_source_id")
        batch.drop_constraint("fk_offers_source_id", type_="foreignkey")
        batch.drop_column("source_id")
    op.drop_table("offer_skills")
    op.drop_table("sources")

    with op.batch_alter_table("search_profiles") as batch:
        batch.drop_index("ix_search_profiles_user_id")
        batch.drop_constraint("fk_search_profiles_user_id", type_="foreignkey")
        batch.drop_column("user_id")
    op.drop_table("users")
