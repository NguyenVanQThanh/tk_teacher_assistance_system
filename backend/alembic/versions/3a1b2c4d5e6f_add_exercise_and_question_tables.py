"""
File Name: 3a1b2c4d5e6f_add_exercise_and_question_tables.py
Description: Add exercise, question, and answer_option tables with soft delete status columns.
Created At: 2026-07-31 
Created By: Tam Khang
Updated At: 2026-07-31 
Updated By: Tam Khang

Revision ID: 3a1b2c4d5e6f
Revises: '2ecce316b47f'
Create Date: 2026-07-31
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '3a1b2c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '2ecce316b47f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create exercises table if not exists, or ensure status column exists
    op.create_table(
        'exercises',
        sa.Column('exercise_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.subject_id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('total_questions', sa.Integer(), server_default='0'),
        sa.Column('ai_metadata', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )

    # 2. Create questions table
    op.create_table(
        'questions',
        sa.Column('question_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('exercise_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('exercises.exercise_id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.document_id', ondelete='SET NULL'), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(length=20), server_default='MultipleChoice', nullable=False),
        sa.Column('difficulty', sa.String(length=20), nullable=True),
        sa.Column('correct_answer', sa.Text(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='0'),
        sa.Column('is_ai_generated', sa.Boolean(), server_default='false'),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )

    # 3. Create answer_options table
    op.create_table(
        'answer_options',
        sa.Column('option_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('questions.question_id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), server_default='false'),
        sa.Column('display_order', sa.Integer(), server_default='0')
    )


def downgrade() -> None:
    op.drop_table('answer_options')
    op.drop_table('questions')
    op.drop_table('exercises')
