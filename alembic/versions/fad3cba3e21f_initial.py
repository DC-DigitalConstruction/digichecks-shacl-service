"""initial

Revision ID: fad3cba3e21f
Revises: 
Create Date: 2024-10-30 13:15:49.335130

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fad3cba3e21f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS core')

    op.create_table('companies',
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        schema='core'
    )
    op.create_index(op.f('ix_core_companies_id'), 'companies', ['id'], unique=True, schema='core')
    op.create_index(op.f('ix_core_companies_name'), 'companies', ['name'], unique=False, schema='core')

    op.create_table('applications',
        sa.Column('client_id', sa.UUID(), nullable=False),
        sa.Column('hashed_client_secret', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('super_user', 'company_admin', 'company_user', name='applicationrole'), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['core.companies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id'),
        sa.UniqueConstraint('uuid'),
        schema='core'
    )
    op.create_index(op.f('ix_core_applications_company_id'), 'applications', ['company_id'], unique=False, schema='core')
    op.create_index(op.f('ix_core_applications_id'), 'applications', ['id'], unique=True, schema='core')

    op.execute('CREATE SCHEMA IF NOT EXISTS compliance')

    op.create_table('connectors',
        sa.Column('connector_name', sa.String(), nullable=False),
        sa.Column('token_endpoint', sa.String(), nullable=True),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['core.companies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        schema='compliance'
    )
    op.create_index(op.f('ix_compliance_connectors_company_id'), 'connectors', ['company_id'], unique=False, schema='compliance')
    op.create_index(op.f('ix_compliance_connectors_id'), 'connectors', ['id'], unique=True, schema='compliance')

    op.create_table('checks',
        sa.Column('check_name', sa.String(), nullable=False),
        sa.Column('rule_source', sa.Enum('digichecks_hosted', 'api', name='rulesource'), nullable=False),
        sa.Column('rule', sa.String(), nullable=True),
        sa.Column('connector_id', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['core.companies.id'], ),
        sa.ForeignKeyConstraint(['connector_id'], ['compliance.connectors.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        schema='compliance'
    )
    op.create_index(op.f('ix_compliance_checks_check_name'), 'checks', ['check_name'], unique=False, schema='compliance')
    op.create_index(op.f('ix_compliance_checks_company_id'), 'checks', ['company_id'], unique=False, schema='compliance')
    op.create_index(op.f('ix_compliance_checks_id'), 'checks', ['id'], unique=True, schema='compliance')


def downgrade() -> None:
    op.drop_index(op.f('ix_compliance_checks_id'), table_name='checks', schema='compliance')
    op.drop_index(op.f('ix_compliance_checks_company_id'), table_name='checks', schema='compliance')
    op.drop_index(op.f('ix_compliance_checks_check_name'), table_name='checks', schema='compliance')
    op.drop_table('checks', schema='compliance')

    op.drop_index(op.f('ix_compliance_connectors_id'), table_name='connectors', schema='compliance')
    op.drop_index(op.f('ix_compliance_connectors_company_id'), table_name='connectors', schema='compliance')
    op.drop_table('connectors', schema='compliance')

    op.execute('DROP SCHEMA compliance')

    op.drop_index(op.f('ix_core_companies_name'), table_name='companies', schema='core')

    op.drop_index(op.f('ix_core_applications_id'), table_name='applications', schema='core')
    op.drop_index(op.f('ix_core_applications_company_id'), table_name='applications', schema='core')
    op.drop_table('applications', schema='core')

    op.drop_index(op.f('ix_core_companies_id'), table_name='companies', schema='core')
    op.drop_table('companies', schema='core')

    op.execute('DROP SCHEMA core')
