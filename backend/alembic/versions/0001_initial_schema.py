"""Create the initial CommunicateIQ schema.

Revision ID: 0001_initial_schema
"""
from alembic import op
from app.database import Base
from app import models  # register all model tables

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)

def downgrade():
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=True)
