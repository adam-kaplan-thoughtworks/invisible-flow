import os
from datetime import datetime
from unittest import mock

from unittest.mock import call, patch
import pytest

from invisible_flow.constants import SCRAPE_URL
from invisible_flow.globals_factory import GlobalsFactory
from invisible_flow.storage import LocalStorage
from invisible_flow.transformers.copa_scrape_transformer import CopaScrapeTransformer

from tests.helpers.if_test_base import IFTestBase

response_code = 200


def mocked_requests_get(**kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code, content):
            self.json_data = json_data
            self.status_code = status_code
            self.content = content

        def json(self):
            return self.json_data
    if kwargs == {"url": SCRAPE_URL + ".csv"}:
        return MockResponse({"key1": "value1"}, response_code, b"bubbles")
    elif kwargs == {"url": SCRAPE_URL + ".json"}:
        return MockResponse({"key1": "value1"}, response_code, b"bubbles")
    elif kwargs == {"url": SCRAPE_URL + ".csv?$where=assignment=\"COPA\""}:
        return MockResponse({"key1": "value1"}, response_code, b"bubbles")
    elif kwargs == {"url": SCRAPE_URL + ".csv?$where=assignment!=\"COPA\""}:
        return MockResponse({"key1": "value1"}, response_code, b"bubbles")
    elif kwargs == {"url": SCRAPE_URL + ".csv?$select=log_no,complaint_date,beat&$where=assignment=\"COPA\""}:
        return MockResponse({"key1": "value1"}, response_code, b"bubbles")
    elif kwargs == {"url": SCRAPE_URL + ".csv?$select=log_no,assignment,case_type,current_status,current_category,"
                    "finding_code,police_shooting,race_of_complainants,sex_of_complainants,age_of_complainants,"
                    "race_of_involved_officers,sex_of_involved_officers,age_of_involved_officers,"
                    "years_on_force_of_officers,complaint_hour,complaint_day,complaint_month&"
                    "$where=assignment=\"COPA\""}:
        return MockResponse({"key1": "value1"}, response_code, b"bubbles")

    return MockResponse(None, 404, None)


@mock.patch('requests.get', side_effect=mocked_requests_get)
class TestCopaScrapeTransformer(IFTestBase):
    @pytest.fixture(
        autouse=True,
        params=[200, 404]
    )
    def default_fixture(self, request):
        global response_code
        response_code = request.param
        with patch('invisible_flow.app.StorageFactory.get_storage') as get_storage_mock:
            get_storage_mock.return_value = LocalStorage()
            self.transformer = CopaScrapeTransformer()

    def test_split_passes(self, get_mock):
        self.copa = False
        self.no_copa = False
        raw_data = self.transformer.split()
        assert not raw_data['copa'].find(b'BIA') > -1
        assert not raw_data['no_copa'].find(b'COPA') > -1

    def test_upload_to_gcs(self, get_mock):
        copa_split_csv = os.path.join(IFTestBase.resource_directory, 'copa_scraped_split.csv')
        no_copa_split_csv = os.path.join(IFTestBase.resource_directory, 'no_copa_scraped_split.csv')
        mock_converted_output = {"copa": open(copa_split_csv).read(), "no_copa": open(no_copa_split_csv).read()}
        with patch('invisible_flow.app.StorageFactory.get_storage') as get_storage_mock:
            with patch.object(LocalStorage, 'store_string') as mock:
                get_storage_mock.return_value = LocalStorage()
                self.transformer.upload_to_gcs(mock_converted_output)
        mock.assert_called()

    @patch('invisible_flow.app.GlobalsFactory.get_current_datetime_utc', lambda: datetime(2019, 3, 25, 5, 30, 50, 0))
    def test_transform(self, get_mock):
        with patch('invisible_flow.app.StorageFactory.get_storage') as get_storage_mock:
            with patch.object(LocalStorage, 'store_string') as store_string_mock:
                with patch('invisible_flow.api.CopaScrape.scrape_copa_ready_for_entity') as mock_scrape_entity:
                    with patch('invisible_flow.api.CopaScrape.scrape_copa_not_in_entity') as mock_scrape_misc:
                        with patch.object(CopaScrapeTransformer, 'save_scraped_data'):
                            with patch.object(CopaScrapeTransformer, 'upload_to_gcs'):
                                get_storage_mock.return_value = LocalStorage()
                                mock_scrape_entity.return_value = b'some content'
                                mock_scrape_misc.return_value = b'some content'
                                CopaScrapeTransformer().transform(None, None)
        self.current_date = GlobalsFactory.get_current_datetime_utc().isoformat(sep='_').replace(':', '-')
        calls = [
            call("copa.csv", b"some content", f'Scrape-{self.current_date}/transformed'),
            call("misc-data.csv", b"some content", f'Scrape-{self.current_date}/transformed')
        ]
        store_string_mock.assert_has_calls(calls)
