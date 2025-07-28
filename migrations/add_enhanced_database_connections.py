"""
Migration script to add enhanced database connection features.
Adds new columns for connection status tracking and metadata.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'enhanced_db_connections'
down_revision = 'previous_revision'  # Replace with actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    """Add enhanced database connection columns."""
    
    # Add new columns to database_connections table
    op.add_column('database_connections', 
                  sa.Column('last_tested', sa.DateTime(timezone=True), nullable=True))
    
    op.add_column('database_connections', 
                  sa.Column('test_status', sa.String(50), nullable=True))
    
    op.add_column('database_connections', 
                  sa.Column('test_message', sa.Text(), nullable=True))
    
    op.add_column('database_connections', 
                  sa.Column('response_time_ms', sa.Integer(), nullable=True))
    
    op.add_column('database_connections', 
                  sa.Column('created_by', sa.String(255), nullable=True))
    
    op.add_column('database_connections', 
                  sa.Column('description', sa.Text(), nullable=True))
    
    # Update existing records with default values
    op.execute("""
        UPDATE database_connections 
        SET test_status = 'NotTested', 
            created_by = 'migration_script'
        WHERE test_status IS NULL
    """)
    
    # Add index for better query performance
    op.create_index('idx_database_connections_test_status', 
                    'database_connections', ['test_status'])
    
    op.create_index('idx_database_connections_last_tested', 
                    'database_connections', ['last_tested'])


def downgrade():
    """Remove enhanced database connection columns."""
    
    # Drop indexes
    op.drop_index('idx_database_connections_last_tested', 
                  table_name='database_connections')
    
    op.drop_index('idx_database_connections_test_status', 
                  table_name='database_connections')
    
    # Drop columns
    op.drop_column('database_connections', 'description')
    op.drop_column('database_connections', 'created_by')
    op.drop_column('database_connections', 'response_time_ms')
    op.drop_column('database_connections', 'test_message')
    op.drop_column('database_connections', 'test_status')
    op.drop_column('database_connections', 'last_tested')
