import datetime

import pytest

from invisible_flow.copa.data_complainant import DataComplainant
from manage import db


class TestComplainant:

    @pytest.fixture(autouse=True)
    def get_db(self):
        db.session.query(DataComplainant).delete()
        db.session.commit()
        yield db
        db.session.close()

    def get_data_complainant(self):
        return DataComplainant(
            id=1,
            gender='M',
            race='race',
            age=30,
            birth_year=1990,
            allegation_id='allegation_id',
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )

    def test_create_data_complainant(self):
        try:
            self.get_data_complainant()
        except Exception:
            pytest.fail('this should not have thrown an exception')

    def test_adding_data_complainant_to_db_works(self, get_db):
        cr = self.get_data_complainant()
        get_db.session.add(cr)
        get_db.session.commit()
        assert len(DataComplainant.query.all()) == 1
        db.session.close()
