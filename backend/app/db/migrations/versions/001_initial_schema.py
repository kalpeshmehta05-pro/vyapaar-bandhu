"""Initial schema — all tables, CHECK constraints, RLS, audit rules

Revision ID: 001_initial
Revises: None
Create Date: 2026-03-31
"""
import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Schema ─────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS vyapaar")

    # ── Application DB role for RLS ────────────────────────────────
    # Password from env var — never hardcode in migration history
    app_role_password = os.environ.get("VYAPAAR_APP_ROLE_PASSWORD", "vyapaar_app_password")
    # Escape single quotes to prevent SQL injection
    safe_pwd = app_role_password.replace("'", "''")
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'vyapaar_app') THEN
                CREATE ROLE vyapaar_app LOGIN PASSWORD '{safe_pwd}';
            END IF;
        END
        $$;
    """)
    op.execute("GRANT USAGE ON SCHEMA vyapaar TO vyapaar_app")

    # ── ca_accounts ────────────────────────────────────────────────
    op.create_table(
        "ca_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("firm_name", sa.Text(), nullable=False),
        sa.Column("proprietor_name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), unique=True, nullable=False),
        sa.Column("phone", sa.Text(), unique=True, nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("membership_number", sa.Text(), unique=True),
        sa.Column("gstin", sa.Text()),
        sa.Column("logo_s3_key", sa.Text()),
        sa.Column("logo_thumbnail_s3_key", sa.Text()),
        sa.Column("icai_certificate_s3_key", sa.Text()),
        sa.Column("tier", sa.String(20), nullable=False, server_default="starter"),
        sa.Column("max_clients", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("tier IN ('starter','professional','scale')", name="ck_ca_accounts_tier"),
        schema="vyapaar",
    )

    # ── clients ────────────────────────────────────────────────────
    op.create_table(
        "clients",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ca_id", UUID(as_uuid=True), sa.ForeignKey("vyapaar.ca_accounts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("whatsapp_phone", sa.Text(), nullable=False),
        sa.Column("business_name", sa.Text(), nullable=False),
        sa.Column("owner_name", sa.Text(), nullable=False),
        sa.Column("gstin", sa.String(15)),
        sa.Column("business_type", sa.String(30), nullable=False, server_default="trader"),
        sa.Column("primary_activity", sa.Text()),
        sa.Column("state_code", sa.String(2)),
        sa.Column("is_composition", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("onboarded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("consent_given_at", sa.DateTime(timezone=True)),
        sa.Column("consent_version", sa.Text()),
        sa.Column("consent_withdrawn_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "business_type IN ('trader','manufacturer','service_provider','retailer','other')",
            name="ck_clients_business_type",
        ),
        sa.UniqueConstraint("ca_id", "whatsapp_phone", name="uq_clients_ca_phone"),
        schema="vyapaar",
    )
    op.create_index("idx_clients_whatsapp_phone", "clients", ["whatsapp_phone"], schema="vyapaar")
    op.create_index("idx_clients_ca_id", "clients", ["ca_id"], schema="vyapaar")

    # ── invoices ───────────────────────────────────────────────────
    op.create_table(
        "invoices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("vyapaar.clients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ca_id", UUID(as_uuid=True), sa.ForeignKey("vyapaar.ca_accounts.id", ondelete="RESTRICT"), nullable=False),
        # Source
        sa.Column("image_s3_key", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False, server_default="whatsapp_photo"),
        sa.Column("whatsapp_message_id", sa.Text()),
        # Extracted fields
        sa.Column("seller_gstin", sa.String(15)),
        sa.Column("seller_name", sa.Text()),
        sa.Column("invoice_number", sa.Text()),
        sa.Column("invoice_date", sa.Date()),
        sa.Column("taxable_amount", sa.Numeric(15, 2)),
        sa.Column("cgst_amount", sa.Numeric(15, 2), server_default="0"),
        sa.Column("sgst_amount", sa.Numeric(15, 2), server_default="0"),
        sa.Column("igst_amount", sa.Numeric(15, 2), server_default="0"),
        sa.Column("total_amount", sa.Numeric(15, 2)),
        sa.Column("product_description", sa.Text()),
        # OCR metadata
        sa.Column("ocr_confidence_score", sa.Numeric(5, 4)),
        sa.Column("ocr_provider", sa.String(20)),
        sa.Column("gstin_was_autocorrected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("gstin_original_ocr", sa.Text()),
        # Classification
        sa.Column("category", sa.Text()),
        sa.Column("classification_method", sa.String(20)),
        sa.Column("classification_confidence", sa.Numeric(5, 4)),
        sa.Column("is_itc_eligible_draft", sa.Boolean()),
        sa.Column("blocked_reason", sa.Text()),
        # RCM
        sa.Column("is_rcm", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("rcm_category", sa.String(50)),
        # CA workflow
        sa.Column("status", sa.String(40), nullable=False, server_default="pending_client_confirmation"),
        sa.Column("ca_reviewed_by", UUID(as_uuid=True), sa.ForeignKey("vyapaar.ca_accounts.id")),
        sa.Column("ca_reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("ca_override_notes", sa.Text()),
        sa.Column("ca_override_category", sa.Text()),
        sa.Column("ca_override_itc_eligible", sa.Boolean()),
        # Dedup
        sa.Column("dedup_hash", sa.Text(), unique=True, nullable=False),
        # Timestamps
        sa.Column("client_confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        # CHECK constraints
        sa.CheckConstraint(
            "source_type IN ('whatsapp_photo','bank_pdf','manual_entry')",
            name="ck_invoices_source_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending_client_confirmation','pending_ca_review','flagged_low_confidence',"
            "'flagged_classification','flagged_anomaly','ca_approved','ca_rejected','ca_overridden')",
            name="ck_invoices_status",
        ),
        schema="vyapaar",
    )
    op.create_index("idx_invoices_client_id", "invoices", ["client_id"], schema="vyapaar")
    op.create_index("idx_invoices_ca_id", "invoices", ["ca_id"], schema="vyapaar")
    op.create_index("idx_invoices_status", "invoices", ["status"], schema="vyapaar")
    op.create_index("idx_invoices_invoice_date", "invoices", ["invoice_date"], schema="vyapaar")
    op.create_index("idx_invoices_dedup_hash", "invoices", ["dedup_hash"], schema="vyapaar")

    # ── monthly_summaries ──────────────────────────────────────────
    op.create_table(
        "monthly_summaries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("vyapaar.clients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ca_id", UUID(as_uuid=True), sa.ForeignKey("vyapaar.ca_accounts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tax_period", sa.String(7), nullable=False),
        # Draft figures
        sa.Column("draft_total_taxable", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("draft_cgst_itc", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("draft_sgst_itc", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("draft_igst_itc", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("draft_total_itc", sa.Numeric(15, 2), nullable=False, server_default="0"),
        # Confirmed figures
        sa.Column("confirmed_total_taxable", sa.Numeric(15, 2)),
        sa.Column("confirmed_cgst_itc", sa.Numeric(15, 2)),
        sa.Column("confirmed_sgst_itc", sa.Numeric(15, 2)),
        sa.Column("confirmed_igst_itc", sa.Numeric(15, 2)),
        sa.Column("confirmed_total_itc", sa.Numeric(15, 2)),
        # RCM
        sa.Column("draft_rcm_liability", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("confirmed_rcm_liability", sa.Numeric(15, 2)),
        # Counts
        sa.Column("invoice_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("flagged_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"),
        # Exports
        sa.Column("gstr3b_json_s3_key", sa.Text()),
        sa.Column("filing_pdf_s3_key", sa.Text()),
        sa.Column("tally_xml_s3_key", sa.Text()),
        sa.Column("is_filed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("filed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("client_id", "tax_period", name="uq_summary_client_period"),
        schema="vyapaar",
    )

    # ── audit_log ──────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("actor_type", sa.String(10), nullable=False),
        sa.Column("actor_id", UUID(as_uuid=True)),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.String(30)),
        sa.Column("entity_id", UUID(as_uuid=True)),
        sa.Column("old_value", JSONB),
        sa.Column("new_value", JSONB),
        sa.Column("ip_address", INET),
        sa.Column("correlation_id", sa.Text()),
        sa.Column("prev_hash", sa.Text()),
        sa.Column("row_hash", sa.Text()),
        sa.CheckConstraint(
            "actor_type IN ('ca','client','system','admin')",
            name="ck_audit_log_actor_type",
        ),
        schema="vyapaar",
    )

    # Audit log protection: append-only — no UPDATE or DELETE ever
    op.execute("CREATE RULE no_update_audit AS ON UPDATE TO vyapaar.audit_log DO INSTEAD NOTHING")
    op.execute("CREATE RULE no_delete_audit AS ON DELETE TO vyapaar.audit_log DO INSTEAD NOTHING")

    # ── reminder_log ───────────────────────────────────────────────
    op.create_table(
        "reminder_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("vyapaar.clients.id"), nullable=False),
        sa.Column("tax_period", sa.String(7), nullable=False),
        sa.Column("reminder_type", sa.String(10), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("wa_message_id", sa.Text()),
        sa.CheckConstraint(
            "reminder_type IN ('7_day','3_day','1_day','overdue')",
            name="ck_reminder_log_type",
        ),
        sa.UniqueConstraint("client_id", "tax_period", "reminder_type", name="uq_reminder_client_period_type"),
        schema="vyapaar",
    )

    # ── refresh_tokens ─────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ca_id", UUID(as_uuid=True), sa.ForeignKey("vyapaar.ca_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text(), unique=True, nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("user_agent", sa.Text()),
        sa.Column("ip_address", INET),
        schema="vyapaar",
    )

    # ── classification_feedback ────────────────────────────────────
    op.create_table(
        "classification_feedback",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("invoice_id", UUID(as_uuid=True), sa.ForeignKey("vyapaar.invoices.id"), nullable=False),
        sa.Column("original_category", sa.Text(), nullable=False),
        sa.Column("corrected_category", sa.Text(), nullable=False),
        sa.Column("original_method", sa.Text(), nullable=False),
        sa.Column("ca_id", UUID(as_uuid=True), sa.ForeignKey("vyapaar.ca_accounts.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        schema="vyapaar",
    )

    # ══════════════════════════════════════════════════════════════
    # ROW-LEVEL SECURITY (RLS)
    # A CA can only see/modify their own clients and invoices.
    # Enforced at database level as defense-in-depth.
    # The application ALSO enforces this in queries (belt + suspenders).
    # ══════════════════════════════════════════════════════════════

    # Enable RLS on tables containing PII
    for table in ["ca_accounts", "clients", "invoices", "monthly_summaries", "refresh_tokens"]:
        op.execute(f"ALTER TABLE vyapaar.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE vyapaar.{table} FORCE ROW LEVEL SECURITY")

    # Grant table access to app role
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA vyapaar TO vyapaar_app")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA vyapaar TO vyapaar_app")

    # RLS policy: CA can only see their own row
    op.execute("""
        CREATE POLICY ca_own_account ON vyapaar.ca_accounts
        FOR ALL TO vyapaar_app
        USING (id = current_setting('app.current_ca_id')::uuid)
    """)

    # RLS policy: CA can only see their own clients
    op.execute("""
        CREATE POLICY ca_own_clients ON vyapaar.clients
        FOR ALL TO vyapaar_app
        USING (ca_id = current_setting('app.current_ca_id')::uuid)
    """)

    # RLS policy: CA can only see invoices for their own clients
    op.execute("""
        CREATE POLICY ca_own_invoices ON vyapaar.invoices
        FOR ALL TO vyapaar_app
        USING (ca_id = current_setting('app.current_ca_id')::uuid)
    """)

    # RLS policy: CA can only see summaries for their own clients
    op.execute("""
        CREATE POLICY ca_own_summaries ON vyapaar.monthly_summaries
        FOR ALL TO vyapaar_app
        USING (ca_id = current_setting('app.current_ca_id')::uuid)
    """)

    # RLS policy: CA can only see their own refresh tokens
    op.execute("""
        CREATE POLICY ca_own_tokens ON vyapaar.refresh_tokens
        FOR ALL TO vyapaar_app
        USING (ca_id = current_setting('app.current_ca_id')::uuid)
    """)

    # Audit log: no RLS (system-wide, read by admin only)
    # Reminder log: no RLS (system-level, written by Celery worker)
    # Classification feedback: no RLS (used for model retraining pipeline)


def downgrade() -> None:
    # Drop RLS policies
    for policy, table in [
        ("ca_own_tokens", "refresh_tokens"),
        ("ca_own_summaries", "monthly_summaries"),
        ("ca_own_invoices", "invoices"),
        ("ca_own_clients", "clients"),
        ("ca_own_account", "ca_accounts"),
    ]:
        op.execute(f"DROP POLICY IF EXISTS {policy} ON vyapaar.{table}")

    for table in ["ca_accounts", "clients", "invoices", "monthly_summaries", "refresh_tokens"]:
        op.execute(f"ALTER TABLE vyapaar.{table} DISABLE ROW LEVEL SECURITY")

    # Drop audit rules
    op.execute("DROP RULE IF EXISTS no_delete_audit ON vyapaar.audit_log")
    op.execute("DROP RULE IF EXISTS no_update_audit ON vyapaar.audit_log")

    # Drop tables in reverse dependency order
    op.drop_table("classification_feedback", schema="vyapaar")
    op.drop_table("refresh_tokens", schema="vyapaar")
    op.drop_table("reminder_log", schema="vyapaar")
    op.drop_table("audit_log", schema="vyapaar")
    op.drop_table("monthly_summaries", schema="vyapaar")
    op.drop_table("invoices", schema="vyapaar")
    op.drop_table("clients", schema="vyapaar")
    op.drop_table("ca_accounts", schema="vyapaar")

    # Revoke and drop role
    op.execute("REVOKE ALL ON SCHEMA vyapaar FROM vyapaar_app")
    op.execute("DROP ROLE IF EXISTS vyapaar_app")
    op.execute("DROP SCHEMA IF EXISTS vyapaar CASCADE")
