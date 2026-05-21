"""rename group table to groups

Revision ID: 35ef7fa5a2c5
Revises: 47960a18b35a
Create Date: 2026-05-21 08:38:09.656006

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '35ef7fa5a2c5'
down_revision = '47960a18b35a'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("group", "groups")

    with op.batch_alter_table("group_member", schema=None) as batch_op:
        batch_op.drop_constraint("group_member_ibfk_1", type_="foreignkey")
        batch_op.create_foreign_key(
            "group_member_ibfk_1",
            "groups",
            ["group_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade():
    with op.batch_alter_table("group_member", schema=None) as batch_op:
        batch_op.drop_constraint("group_member_ibfk_1", type_="foreignkey")
        batch_op.create_foreign_key(
            "group_member_ibfk_1",
            "group",
            ["group_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.rename_table("groups", "group")
