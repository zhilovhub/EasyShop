"""added on_cascade

Revision ID: a0143883fa19
Revises: 
Create Date: 2024-02-12 08:23:14.144289

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a0143883fa19'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('fsm')
    op.drop_table('users')
    op.alter_column('products', 'price',
               existing_type=sa.BIGINT(),
               type_=sa.Float(),
               existing_nullable=False)
    op.drop_constraint('products_bot_token_fkey', 'products', type_='foreignkey')
    op.create_foreign_key(None, 'products', 'bots', ['bot_token'], ['bot_token'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'products', type_='foreignkey')
    op.create_foreign_key('products_bot_token_fkey', 'products', 'bots', ['bot_token'], ['bot_token'])
    op.alter_column('products', 'price',
               existing_type=sa.Float(),
               type_=sa.BIGINT(),
               existing_nullable=False)
    op.create_table('users',
    sa.Column('user_id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('status', sa.VARCHAR(length=55), autoincrement=False, nullable=False),
    sa.Column('registered_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('locale', sa.VARCHAR(length=10), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('user_id', name='users_pkey')
    )
    op.create_table('fsm',
    sa.Column('id', sa.VARCHAR(length=70), autoincrement=False, nullable=False),
    sa.Column('state', sa.VARCHAR(length=55), autoincrement=False, nullable=True),
    sa.Column('data', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='fsm_pkey')
    )
    # ### end Alembic commands ###