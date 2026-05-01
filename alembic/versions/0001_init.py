"""initial schema

Revision ID: 0001_init
Revises:
Create Date: 2026-05-01
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_match_id", sa.String(128), nullable=False),
        sa.Column("league", sa.String(128), nullable=False),
        sa.Column("home_team", sa.String(128), nullable=False),
        sa.Column("away_team", sa.String(128), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider_match_id", name="uq_provider_match_id"),
    )

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "SENT_TO_MODERATION",
                "APPROVED",
                "REJECTED",
                "PUBLISHED",
                "RESULT_CONFIRMED",
                name="predictionstatus",
            ),
            nullable=False,
        ),
        sa.Column("full_text", sa.Text(), nullable=False),
        sa.Column(
            "outcome",
            sa.Enum("HOME_WIN", "DRAW", "AWAY_WIN", name="matchoutcome"),
            nullable=False,
        ),
        sa.Column("total_line", sa.Float(), nullable=False),
        sa.Column("total_direction", sa.String(16), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("moderation_message_id", sa.Integer(), nullable=True),
        sa.Column("channel_message_id", sa.Integer(), nullable=True),
        sa.Column(
            "hit_miss",
            sa.Enum("HIT", "MISS", "PENDING", name="hitmiss"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("match_id", name="uq_prediction_match"),
    )

    op.create_table(
        "match_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("home_goals", sa.Integer(), nullable=False),
        sa.Column("away_goals", sa.Integer(), nullable=False),
        sa.Column("confirmed_by_admin", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("match_id", name="uq_result_match"),
    )


def downgrade() -> None:
    op.drop_table("match_results")
    op.drop_table("predictions")
    op.drop_table("matches")
