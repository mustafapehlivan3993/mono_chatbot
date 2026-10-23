import os
import unittest
from unittest.mock import patch
from app import create_app


class LeadTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app({'TESTING': True}).test_client()
        self.data = dict(isim=' MONO Test ', eposta='test@example.com',
                         telefon='05550000000', mesaj='Entegrasyon testi',
                         istekId='684b38da-7da3-4f13-aa56-fc5ef80c336d')

    def test_valid_lead_aliases(self):
        with patch('app.database.save_lead', return_value=self.data['istekId']) as save:
            for path in ['/api/lead', '/api/leads']:
                response = self.client.post(path, json=self.data)
                self.assertTrue(response.json['basari'])
                self.assertEqual(save.call_args.args[0]['isim'], 'MONO Test')

    def test_validation_before_storage(self):
        with patch('app.database.save_lead') as save:
            for key, value in [('isim', []), ('eposta', 'x'), ('telefon', 'abc1234567'),
                               ('mesaj', ''), ('istekId', 32), ('kaynak', {})]:
                response = self.client.post('/api/leads', json={**self.data, key: value})
                self.assertEqual(response.status_code, 400, key)
            save.assert_not_called()

    def test_no_false_success(self):
        with patch('app.database.save_lead', side_effect=RuntimeError('private')):
            response = self.client.post('/api/leads', json=self.data)
            self.assertEqual(response.status_code, 503)
            self.assertFalse(response.json['basari'])
            self.assertNotIn('private', response.get_data(as_text=True))

    def test_conflicting_id(self):
        with patch('app.database.save_lead', side_effect=ValueError()):
            self.assertEqual(self.client.post('/api/leads', json=self.data).status_code, 409)

    def test_list_authorization(self):
        with patch.dict(os.environ, {'ADMIN_API_KEY': 'test-only-key'}):
            with patch('app.database.list_leads', return_value=([], False)) as listing:
                for auth in ['', 'Bearer wrong', 'Bearer şifre']:
                    response = self.client.get('/api/leads', headers={'Authorization': auth})
                    self.assertEqual(response.status_code, 401)
                listing.assert_not_called()
                response = self.client.get('/api/leads', headers={'Authorization': 'Bearer test-only-key'})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json['leads'], [])
                self.assertEqual(self.client.get('/api/leads?limit=1000', headers={'Authorization': 'Bearer test-only-key'}).status_code, 400)

    def test_missing_db_and_admin_fail_closed(self):
        with patch.dict(os.environ, {'ADMIN_API_KEY': '', 'DATABASE_URL': ''}):
            self.assertEqual(self.client.get('/api/leads').status_code, 503)
            self.assertEqual(self.client.post('/api/leads', json=self.data).status_code, 503)

    def test_lead_preflight(self):
        response = self.client.options('/api/leads', headers={
            'Origin': 'https://mustafapehlivan22.wixstudio.com',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'https://mustafapehlivan22.wixstudio.com')
