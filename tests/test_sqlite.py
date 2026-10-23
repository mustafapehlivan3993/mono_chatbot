import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from app import create_app


class SqliteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = {'TESTING': True, 'SQLITE_PATH': str(Path(self.tmp.name) / 'mono.db')}
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.data = dict(isim="O'Connor Test", telefon='05550000000', eposta='test@example.com',
                         mesaj='Ödev testidir. <script>literal</script>', kaynak='sohbet', istekId=str(uuid4()))

    def listing(self, client=None, suffix=''):
        with patch.dict('os.environ', {'ADMIN_API_KEY': 'sqlite-test-key'}):
            return (client or self.client).get('/api/leads'+suffix, headers={'Authorization': 'Bearer sqlite-test-key'})

    def test_real_write_reopen_and_idempotency(self):
        for _ in range(2):
            self.assertEqual(self.client.post('/api/leads', json=self.data).status_code, 200)
        other = create_app(self.config).test_client()
        rows = self.listing(other).json['leads']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['isim'], self.data['isim'])
        self.assertEqual(rows[0]['mesaj'], self.data['mesaj'])
        self.assertTrue(rows[0]['tarih'].endswith('Z'))
        self.assertEqual(self.client.post('/api/leads', json={**self.data, 'mesaj': 'Farklı'}).status_code, 409)
        self.assertEqual(self.listing().json['leads'][0]['mesaj'], self.data['mesaj'])

    def test_pagination_and_parallel_writes(self):
        def send(i):
            with self.app.test_client() as client:
                return client.post('/api/leads', json={**self.data, 'istekId': str(uuid4())}).status_code
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(list(pool.map(send, range(8))), [200]*8)
        first = self.listing(suffix='?limit=5').json
        last = self.listing(suffix='?limit=5&offset=5').json
        self.assertTrue(first['devam'])
        self.assertFalse(last['devam'])
        self.assertEqual(len(first['leads'])+len(last['leads']), 8)

    def test_missing_disk_file_recreates_empty_demo(self):
        self.client.post('/api/leads', json=self.data)
        Path(self.config['SQLITE_PATH']).unlink()
        self.assertEqual(self.listing().json['leads'], [])
