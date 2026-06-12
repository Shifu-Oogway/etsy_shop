"""Initial schema — all eleven tables in ONE migration.

Lessons baked in:
- no GENERATED ALWAYS AS STORED computed columns (unsupported in our setup)
- every column defined exactly once (duplicates across migrations broke before)
- pgvector extension created before the embeddings table
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

product_type = sa.Enum("pdf_planner", "excel_template", "notion_template", name="producttype")
product_status = sa.Enum("draft", "generated", "qa_passed", "qa_failed", "published",
                         "archived", name="productstatus")
listing_status = sa.Enum("pending", "active", "inactive", "failed", name="listingstatus")
experiment_status = sa.Enum("running", "completed", "aborted", name="experimentstatus")
task_status = sa.Enum("queued", "running", "success", "failure", name="taskstatus")


def _ts():
    return (
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "products",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("product_type", product_type, nullable=False),
        sa.Column("status", product_status, nullable=False, server_default="draft"),
        sa.Column("niche", sa.String(120), nullable=False, server_default=""),
        sa.Column("price", sa.Float, nullable=False, server_default="4.99"),
        sa.Column("file_path", sa.String(512), nullable=False, server_default=""),
        sa.Column("spec", sa.JSON, nullable=False, server_default="{}"),
        *_ts(),
    )
    op.create_index("ix_products_status", "products", ["status"])
    op.create_index("ix_products_niche", "products", ["niche"])

    op.create_table(
        "listings",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.BigInteger,
                  sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("etsy_listing_id", sa.String(64), nullable=False, server_default=""),
        sa.Column("status", listing_status, nullable=False, server_default="pending"),
        sa.Column("title", sa.String(140), nullable=False),
        sa.Column("tags", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("price", sa.Float, nullable=False, server_default="4.99"),
        sa.Column("url", sa.String(512), nullable=False, server_default=""),
        *_ts(),
    )
    op.create_index("ix_listings_product_id", "listings", ["product_id"])
    op.create_index("ix_listings_etsy_listing_id", "listings", ["etsy_listing_id"])

    op.create_table(
        "trends",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("keyword", sa.String(160), nullable=False),
        sa.Column("niche", sa.String(120), nullable=False, server_default=""),
        sa.Column("score", sa.Float, nullable=False, server_default="0"),
        sa.Column("source", sa.String(64), nullable=False, server_default="ollama"),
        sa.Column("details", sa.JSON, nullable=False, server_default="{}"),
        *_ts(),
    )
    op.create_index("ix_trends_keyword", "trends", ["keyword"])
    op.create_index("ix_trends_niche", "trends", ["niche"])

    op.create_table(
        "seo_metadata",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.BigInteger,
                  sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("optimized_title", sa.String(140), nullable=False, server_default=""),
        sa.Column("optimized_description", sa.Text, nullable=False, server_default=""),
        sa.Column("tags", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("keywords", sa.JSON, nullable=False, server_default="[]"),
        *_ts(),
    )
    op.create_index("ix_seo_metadata_product_id", "seo_metadata", ["product_id"])

    op.create_table(
        "qa_reports",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.BigInteger,
                  sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("passed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("score", sa.Float, nullable=False, server_default="0"),
        sa.Column("checks", sa.JSON, nullable=False, server_default="{}"),
        *_ts(),
    )
    op.create_index("ix_qa_reports_product_id", "qa_reports", ["product_id"])

    op.create_table(
        "sales",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("listing_id", sa.BigInteger,
                  sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("etsy_receipt_id", sa.String(64), nullable=False, server_default=""),
        sa.Column("amount", sa.Float, nullable=False, server_default="0"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("buyer_country", sa.String(64), nullable=False, server_default=""),
        *_ts(),
    )
    op.create_index("ix_sales_listing_id", "sales", ["listing_id"])

    op.create_table(
        "experiments",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("hypothesis", sa.Text, nullable=False, server_default=""),
        sa.Column("status", experiment_status, nullable=False, server_default="running"),
        sa.Column("variants", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("results", sa.JSON, nullable=False, server_default="{}"),
        *_ts(),
    )

    op.create_table(
        "task_runs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("task_name", sa.String(160), nullable=False),
        sa.Column("celery_id", sa.String(64), nullable=False, server_default=""),
        sa.Column("status", task_status, nullable=False, server_default="queued"),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("error", sa.Text, nullable=False, server_default=""),
        *_ts(),
    )
    op.create_index("ix_task_runs_task_name", "task_runs", ["task_name"])
    op.create_index("ix_task_runs_celery_id", "task_runs", ["celery_id"])

    op.create_table(
        "embeddings",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("ref_type", sa.String(40), nullable=False),
        sa.Column("ref_id", sa.BigInteger, nullable=False),
        sa.Column("model", sa.String(80), nullable=False, server_default="nomic-embed-text"),
        sa.Column("vector", sa.JSON, nullable=True),  # altered to VECTOR below
        sa.Column("meta", sa.JSON, nullable=False, server_default="{}"),
        *_ts(),
    )
    op.execute("ALTER TABLE embeddings ALTER COLUMN vector TYPE vector(768) "
               "USING NULL")
    op.create_index("ix_embeddings_ref_type", "embeddings", ["ref_type"])
    op.create_index("ix_embeddings_ref_id", "embeddings", ["ref_id"])

    op.create_table(
        "schedules",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(160), nullable=False, unique=True),
        sa.Column("cron", sa.String(64), nullable=False, server_default="0 6 * * *"),
        sa.Column("task_name", sa.String(160), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        *_ts(),
    )

    op.create_table(
        "event_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("level", sa.String(16), nullable=False, server_default="INFO"),
        sa.Column("source", sa.String(120), nullable=False, server_default=""),
        sa.Column("message", sa.Text, nullable=False, server_default=""),
        sa.Column("context", sa.JSON, nullable=False, server_default="{}"),
        *_ts(),
    )
    op.create_index("ix_event_logs_level", "event_logs", ["level"])
    op.create_index("ix_event_logs_source", "event_logs", ["source"])


def downgrade() -> None:
    for table in ("event_logs", "schedules", "embeddings", "task_runs", "experiments",
                  "sales", "qa_reports", "seo_metadata", "trends", "listings", "products"):
        op.drop_table(table)
    for enum in (task_status, experiment_status, listing_status, product_status, product_type):
        enum.drop(op.get_bind(), checkfirst=True)
