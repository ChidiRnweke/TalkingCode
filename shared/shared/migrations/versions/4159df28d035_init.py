"""init

Revision ID: 4159df28d035
Revises: 
Create Date: 2024-06-04 19:36:00.284135

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = '4159df28d035'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('github_languages',
    sa.Column('language', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('language')
    )
    op.create_table('github_repositories',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('user', sa.String(length=255), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('url', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('name', 'user')
    )
    op.create_table('github_files',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('content_url', sa.String(length=255), nullable=False),
    sa.Column('last_modified', sa.DateTime(), nullable=False),
    sa.Column('repository_name', sa.String(length=255), nullable=False),
    sa.Column('repository_user', sa.String(length=255), nullable=False),
    sa.Column('file_extension', sa.String(length=255), nullable=False),
    sa.Column('path_in_repo', sa.String(length=255), nullable=False),
    sa.Column('latest_version', sa.Boolean(), nullable=False),
    sa.Column('is_embedded', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['repository_name', 'repository_user'], ['github_repositories.name', 'github_repositories.user'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('languages_repository_bridge',
    sa.Column('language_name', sa.String(length=255), nullable=True),
    sa.Column('repository_name', sa.String(length=255), nullable=True),
    sa.Column('repository_user', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['language_name'], ['github_languages.language'], ),
    sa.ForeignKeyConstraint(['repository_name', 'repository_user'], ['github_repositories.name', 'github_repositories.user'], )
    )
    op.create_table('embedded_documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.Vector(dim=3072), nullable=False),
    sa.Column('input_token_count', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['github_files.id'], ),
    sa.ForeignKeyConstraint(['document_id'], ['github_files.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('embedded_documents')
    op.drop_table('languages_repository_bridge')
    op.drop_table('github_files')
    op.drop_table('github_repositories')
    op.drop_table('github_languages')
    # ### end Alembic commands ###
