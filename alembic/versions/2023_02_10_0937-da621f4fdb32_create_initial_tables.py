"""create initial tables

Revision ID: da621f4fdb32
Revises: 
Create Date: 2023-02-10 09:37:47.483638

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "da621f4fdb32"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slack_id", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("github_username", sa.String(255), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), unique=True),
    )
    op.create_table(
        "channels",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slack_id", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("new_devs_are_reviewers", sa.Boolean, nullable=False),
    )
    op.create_table(
        "user_channel_configs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "channel_id", sa.Integer, sa.ForeignKey("channels.id"), nullable=False
        ),
        sa.Column("reviewer", sa.Boolean, nullable=False),
        sa.Column("notify_on_assignment", sa.Boolean, nullable=False),
    )
    op.create_table(
        "assigned_reviews",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "channel_id", sa.Integer, sa.ForeignKey("channels.id"), nullable=False
        ),
        sa.Column("pr_url", sa.String(1024), nullable=False),
        sa.Column("assigned_at", sa.DateTime, nullable=False),
        sa.Column("acknowleged_at", sa.DateTime, nullable=True),
        sa.Column("rerolled_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("assigned_reviews")
    op.drop_table("user_channel_configs")
    op.drop_table("channels")
    op.drop_table("users")
