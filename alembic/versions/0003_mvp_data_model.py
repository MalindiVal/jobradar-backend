"""Modèle de données du cahier des charges MVP v0.1 (§3).

- sources -> job_sources, offers -> job_offers, search_profiles -> search_preferences
- job_offers : external_id (unique avec source_id), published_at, analysis_status,
  source_url renommé application_url
- nouvelles tables profiles, skills, profile_skills, job_analyses
- les compétences de search_profiles.skills sont reprises dans profiles / profile_skills
- notifications.user_id
"""
import re
from alembic import op
import sqlalchemy as sa

revision = "0003_mvp_data_model"
down_revision = "0002_spec_tables"
branch_labels = None
depends_on = None

def _normalize(name: str) -> str:
    return re.sub(r"\s+", " ", str(name)).strip()

def _rename_index(old: str, new: str, table: str, columns: list[str], unique: bool = False):
    op.drop_index(old, table_name=table)
    op.create_index(new, table, columns, unique=unique)

def upgrade():
    conn = op.get_bind()

    # --- job_sources -------------------------------------------------------------
    op.rename_table("sources", "job_sources")
    _rename_index("ix_sources_name", "ix_job_sources_name", "job_sources", ["name"], unique=True)

    # --- job_offers --------------------------------------------------------------
    op.rename_table("offers", "job_offers")
    for column in ("title", "deduplication_key", "status", "source_id"):
        _rename_index(f"ix_offers_{column}", f"ix_job_offers_{column}", "job_offers", [column])
    with op.batch_alter_table("job_offers") as batch:
        batch.alter_column("source_url", new_column_name="application_url", existing_type=sa.Text(),
                           existing_nullable=False)
        batch.add_column(sa.Column("external_id", sa.String(200), nullable=True))
        batch.add_column(sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("analysis_status", sa.String(30), nullable=False,
                                   server_default="pending_analysis"))
        batch.drop_constraint("uq_offer_deduplication_key", type_="unique")
        batch.create_unique_constraint("uq_job_offer_deduplication_key", ["deduplication_key"])
        batch.create_unique_constraint("uq_job_offer_source_external_id", ["source_id", "external_id"])
        batch.create_index("ix_job_offers_analysis_status", ["analysis_status"])

    # --- profils et compétences ----------------------------------------------------
    op.create_table("skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("normalized_name", sa.String(100), nullable=False))
    op.create_index("ix_skills_normalized_name", "skills", ["normalized_name"], unique=True)

    op.create_table("profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("headline", sa.String(200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"])

    op.create_table("profile_skills",
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("level", sa.String(30), nullable=True))
    op.create_index("ix_profile_skills_skill_id", "profile_skills", ["skill_id"])

    # --- search_preferences : reprise des compétences dans un profil ---------------
    op.rename_table("search_profiles", "search_preferences")
    _rename_index("ix_search_profiles_user_id", "ix_search_preferences_user_id", "search_preferences", ["user_id"])

    prefs = sa.table("search_preferences", sa.column("id", sa.Integer()), sa.column("user_id", sa.Integer()),
                     sa.column("skills", sa.JSON()))
    skill_ids: dict[str, int] = {}
    for _pref_id, user_id, skills in conn.execute(sa.select(prefs.c.id, prefs.c.user_id, prefs.c.skills)
                                                  .order_by(prefs.c.id)).all():
        profile_id = conn.execute(sa.text(
            "INSERT INTO profiles (user_id, headline, summary, created_at, updated_at) "
            "VALUES (:u, '', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) RETURNING id"), {"u": user_id}).scalar_one()
        linked = set()
        for raw in skills or []:
            name = _normalize(raw)[:100]
            key = name.lower()
            if not name or key in linked:
                continue
            if key not in skill_ids:
                skill_ids[key] = conn.execute(sa.text(
                    "INSERT INTO skills (name, normalized_name) VALUES (:n, :k) RETURNING id"),
                    {"n": name, "k": key}).scalar_one()
            conn.execute(sa.text("INSERT INTO profile_skills (profile_id, skill_id) VALUES (:p, :s)"),
                         {"p": profile_id, "s": skill_ids[key]})
            linked.add(key)

    with op.batch_alter_table("search_preferences") as batch:
        batch.drop_column("skills")

    # --- job_analyses --------------------------------------------------------------
    op.create_table("job_analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("offer_id", sa.Integer(), sa.ForeignKey("job_offers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("contract_match", sa.Boolean(), nullable=False),
        sa.Column("skills_match", sa.JSON(), nullable=False),
        sa.Column("missing_skills", sa.JSON(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("recommendation", sa.String(20), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("score_breakdown", sa.JSON(), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("raw_response", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_job_analyses_offer_id", "job_analyses", ["offer_id"])
    op.create_index("ix_job_analyses_profile_id", "job_analyses", ["profile_id"])

    # --- notifications -------------------------------------------------------------
    with op.batch_alter_table("notifications") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_notifications_user_id", "users", ["user_id"], ["id"], ondelete="SET NULL")
        batch.create_index("ix_notifications_user_id", ["user_id"])

def downgrade():
    conn = op.get_bind()

    with op.batch_alter_table("notifications") as batch:
        batch.drop_index("ix_notifications_user_id")
        batch.drop_constraint("fk_notifications_user_id", type_="foreignkey")
        batch.drop_column("user_id")

    op.drop_table("job_analyses")

    # Les compétences du premier profil redeviennent la liste JSON des critères de recherche.
    with op.batch_alter_table("search_preferences") as batch:
        batch.add_column(sa.Column("skills", sa.JSON(), nullable=True))
    first_profile = conn.execute(sa.text("SELECT id FROM profiles ORDER BY id LIMIT 1")).scalar()
    names = [] if first_profile is None else [row[0] for row in conn.execute(sa.text(
        "SELECT s.name FROM profile_skills ps JOIN skills s ON s.id = ps.skill_id "
        "WHERE ps.profile_id = :p ORDER BY ps.skill_id"), {"p": first_profile}).all()]
    prefs = sa.table("search_preferences", sa.column("skills", sa.JSON()))
    conn.execute(prefs.update().values(skills=names))
    with op.batch_alter_table("search_preferences") as batch:
        batch.alter_column("skills", existing_type=sa.JSON(), nullable=False)
    _rename_index("ix_search_preferences_user_id", "ix_search_profiles_user_id", "search_preferences", ["user_id"])
    op.rename_table("search_preferences", "search_profiles")

    op.drop_table("profile_skills")
    op.drop_table("profiles")
    op.drop_table("skills")

    with op.batch_alter_table("job_offers") as batch:
        batch.drop_index("ix_job_offers_analysis_status")
        batch.drop_constraint("uq_job_offer_source_external_id", type_="unique")
        batch.drop_constraint("uq_job_offer_deduplication_key", type_="unique")
        batch.create_unique_constraint("uq_offer_deduplication_key", ["deduplication_key"])
        batch.drop_column("analysis_status")
        batch.drop_column("published_at")
        batch.drop_column("external_id")
        batch.alter_column("application_url", new_column_name="source_url", existing_type=sa.Text(),
                           existing_nullable=False)
    for column in ("title", "deduplication_key", "status", "source_id"):
        _rename_index(f"ix_job_offers_{column}", f"ix_offers_{column}", "job_offers", [column])
    op.rename_table("job_offers", "offers")

    _rename_index("ix_job_sources_name", "ix_sources_name", "job_sources", ["name"], unique=True)
    op.rename_table("job_sources", "sources")
