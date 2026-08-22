"""Initial database schema for Sentinel AI Phase 9.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-22 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index('ix_organizations_id', 'organizations', ['id'], unique=False)
    op.create_index('ix_organizations_slug', 'organizations', ['slug'], unique=True)

    # 3. organization_members table
    op.create_table(
        'organization_members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.Enum('ORGANIZATION_ADMIN', 'ANALYST', 'VIEWER', name='organizationrole'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_org_user_membership')
    )
    op.create_index('ix_organization_members_id', 'organization_members', ['id'], unique=False)
    op.create_index('ix_organization_members_org_id', 'organization_members', ['organization_id'], unique=False)
    op.create_index('ix_organization_members_user_id', 'organization_members', ['user_id'], unique=False)
    op.create_index('ix_org_member_org_user', 'organization_members', ['organization_id', 'user_id'], unique=False)

    # 4. clients table
    op.create_table(
        'clients',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('client_code', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'ARCHIVED', name='clientstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'client_code', name='uq_org_client_code')
    )
    op.create_index('ix_clients_id', 'clients', ['id'], unique=False)
    op.create_index('ix_clients_organization_id', 'clients', ['organization_id'], unique=False)
    op.create_index('ix_client_org_code', 'clients', ['organization_id', 'client_code'], unique=False)
    op.create_index('ix_client_org_status', 'clients', ['organization_id', 'status'], unique=False)

    # 5. datasets table
    op.create_table(
        'datasets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('client_id', sa.String(length=36), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=False),
        sa.Column('column_count', sa.Integer(), nullable=False),
        sa.Column('target_column', sa.String(length=64), nullable=True),
        sa.Column('validation_status', sa.Enum('VALID', 'WARNINGS', 'INVALID', name='datasetvalidationstatus'), nullable=False),
        sa.Column('validation_summary', sa.JSON(), nullable=True),
        sa.Column('processing_status', sa.Enum('PENDING', 'ANALYZED', 'FAILED', name='datasetprocessingstatus'), nullable=False),
        sa.Column('uploaded_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_datasets_id', 'datasets', ['id'], unique=False)
    op.create_index('ix_dataset_org_client', 'datasets', ['organization_id', 'client_id'], unique=False)

    # 6. analyses table
    op.create_table(
        'analyses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('client_id', sa.String(length=36), nullable=False),
        sa.Column('dataset_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('optimal_threshold', sa.Float(), nullable=False),
        sa.Column('execution_time_seconds', sa.Float(), nullable=False),
        sa.Column('status', sa.Enum('COMPLETED', 'FAILED', 'PROCESSING', name='analysisstatus'), nullable=False),
        sa.Column('validation_metrics', sa.JSON(), nullable=False),
        sa.Column('test_metrics', sa.JSON(), nullable=True),
        sa.Column('fraud_statistics', sa.JSON(), nullable=False),
        sa.Column('risk_statistics', sa.JSON(), nullable=False),
        sa.Column('category_breakdown', sa.JSON(), nullable=False),
        sa.Column('empirical_findings', sa.JSON(), nullable=False),
        sa.Column('recommendations', sa.JSON(), nullable=False),
        sa.Column('global_feature_importance', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analyses_id', 'analyses', ['id'], unique=False)
    op.create_index('ix_analysis_org_client', 'analyses', ['organization_id', 'client_id'], unique=False)
    op.create_index('ix_analysis_created', 'analyses', ['created_at'], unique=False)

    # 7. transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('client_id', sa.String(length=36), nullable=False),
        sa.Column('analysis_id', sa.String(length=36), nullable=False),
        sa.Column('transaction_num', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.String(length=64), nullable=True),
        sa.Column('merchant', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=50), nullable=True),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('long', sa.Float(), nullable=True),
        sa.Column('merch_lat', sa.Float(), nullable=True),
        sa.Column('merch_long', sa.Float(), nullable=True),
        sa.Column('is_fraud_pred', sa.Integer(), nullable=False),
        sa.Column('actual_fraud_label', sa.Integer(), nullable=True),
        sa.Column('fraud_probability', sa.Float(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_band', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transactions_id', 'transactions', ['id'], unique=False)
    op.create_index('ix_tx_analysis_risk_score', 'transactions', ['analysis_id', 'risk_score'], unique=False)
    op.create_index('ix_tx_analysis_risk_band', 'transactions', ['analysis_id', 'risk_band'], unique=False)
    op.create_index('ix_tx_analysis_amount', 'transactions', ['analysis_id', 'amount'], unique=False)
    op.create_index('ix_tx_analysis_fraud', 'transactions', ['analysis_id', 'is_fraud_pred'], unique=False)
    op.create_index('ix_tx_org_client_analysis', 'transactions', ['organization_id', 'client_id', 'analysis_id'], unique=False)

    # 8. reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('client_id', sa.String(length=36), nullable=True),
        sa.Column('analysis_id', sa.String(length=36), nullable=True),
        sa.Column('report_type', sa.Enum('ORGANIZATION', 'CLIENT', 'ANALYSIS', name='reporttype'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('generated_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['generated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reports_id', 'reports', ['id'], unique=False)
    op.create_index('ix_report_org_type', 'reports', ['organization_id', 'report_type'], unique=False)

    # 9. audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'], unique=False)
    op.create_index('ix_audit_org_action', 'audit_logs', ['organization_id', 'action'], unique=False)
    op.create_index('ix_audit_org_created', 'audit_logs', ['organization_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('reports')
    op.drop_table('transactions')
    op.drop_table('analyses')
    op.drop_table('datasets')
    op.drop_table('clients')
    op.drop_table('organization_members')
    op.drop_table('organizations')
    op.drop_table('users')
