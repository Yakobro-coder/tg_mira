from sqlalchemy import Column, Integer, Table
from sqlalchemy.orm import declarative_base
Base = declarative_base()

from db_foo.db_connect import get_metadata
metadata = get_metadata()

from enum import Enum


class Admin(Enum):
    ADMIN = 253345770, 378592965, 2083337355


class Users(Base):
    __table__ = Table('bot_mira_users', metadata,
                      Column("id", Integer, primary_key=True),
                      autoload=True)

    def __json__(self):
        return dict(
            id=self.id,
            telegram_id=self.telegram_id,
            crm_id=self.crm_id,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email
        )
