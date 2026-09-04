"""add OIDC identity to user

Revision ID: 8d41b3f0a6c2
Revises: 35ef7fa5a2c5
Create Date: 2026-09-04 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "8d41b3f0a6c2"
down_revision = "35ef7fa5a2c5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("identity_issuer", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("identity_subject", sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint(
            "uq_user_identity_issuer_subject",
            ["identity_issuer", "identity_subject"],
        )


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_constraint("uq_user_identity_issuer_subject", type_="unique")
        batch_op.drop_column("identity_subject")
        batch_op.drop_column("identity_issuer")
