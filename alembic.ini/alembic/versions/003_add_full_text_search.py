"""Add full-text search support

Revision ID: 003_add_full_text_search
Revises: 002_add_indexes_and_constraints
Create Date: 2024-01-01 00:00:00.000000

"""

# pyright: reportAttributeAccessIssue=false
# pylint: disable=no-member

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_full_text_search'
down_revision: Union[str, None] = '002_add_indexes_and_constraints'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add full-text search support for PostgreSQL
    # Enable the pg_trgm extension for similarity search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    
    # Add search vectors for knowledge documents
    op.add_column('knowledge_documents', sa.Column('search_vector', sa.TEXT, nullable=True))
    
    # Create trigger to automatically update search_vector
    op.execute("""
        CREATE OR REPLACE FUNCTION knowledge_documents_search_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := 
                setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'B');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER knowledge_documents_search_trigger
        BEFORE INSERT OR UPDATE ON knowledge_documents
        FOR EACH ROW EXECUTE FUNCTION knowledge_documents_search_update();
    """)
    
    # Create GIN index for full-text search
    op.execute("""
        CREATE INDEX knowledge_documents_search_idx 
        ON knowledge_documents USING GIN (search_vector)
    """)


def downgrade() -> None:
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS knowledge_documents_search_idx")
    
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS knowledge_documents_search_trigger ON knowledge_documents")
    
    # Drop function
    op.execute("DROP FUNCTION IF EXISTS knowledge_documents_search_update()")
    
    # Drop column
    op.drop_column('knowledge_documents', 'search_vector')
    
    # Drop extension
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    