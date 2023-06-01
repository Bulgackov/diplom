import sqlalchemy as sq
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DSN

# схема БД
metadata = MetaData()
Base = declarative_base()


class Viewed(Base):
    __tablename__ = 'viewed'

    id = sq.Column(sq.Integer, primary_key=True)  # id записи в таблице
    profile_id = sq.Column(sq.Integer, nullable=False)  # id пользователя
    account_id = sq.Column(sq.Integer, unique=True)  # id владельца отправляемых фото

    def __str__(self):
        return (f'ID записи: {self.id}|'
                f' ID клиента: {self.profile_id}|'
                f' ID владельца фото: {self.account_id}\n ')


def create_tables(mover):
    Base.metadata.create_all(mover)


# добавление записи в бд
def add_to_table(session, profile_id, account_id):
    to_bd = Viewed(profile_id=profile_id, account_id=account_id)
    session.add(to_bd)
    session.commit()
    print(to_bd.profile_id)


# извлечение записей из БД
def extract_from_db(session, account_id):
    from_db = session.query(Viewed).filter(Viewed.account_id == account_id).all()
    if not from_db:
        result = 0
    else:
        for s in from_db:
            print(s)
        result = 1
    return result


if __name__ == '__main__':
    engine = sq.create_engine(DSN)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Base.metadata.drop_all(engine)

    create_tables(engine)
    # add_to_table(session, profile_id=119258287, account_id=130334067)
    from_bd = extract_from_db(session, 130334067)
    print(from_bd)
    q = session.query(Viewed).all()
    for c in q:
        print(c)

    session.close()
