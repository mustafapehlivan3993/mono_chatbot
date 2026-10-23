import unittest
from unittest.mock import patch

from app import create_app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app({'TESTING': True}).test_client()

    def test_cors_preflight(self):
        for origin in ['https://mustafapehlivan22.wixstudio.com',
                       'https://mustafapehlivan22-mononutrition.editor.wix.com']:
            response = self.client.options('/sohbet', headers={
                'Origin': origin, 'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'content-type'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['Access-Control-Allow-Origin'], origin)
            self.assertIn('content-type', response.headers['Access-Control-Allow-Headers'].lower())

    def test_unapproved_origin(self):
        response = self.client.options('/sohbet', headers={
            'Origin': 'https://example.com', 'Access-Control-Request-Method': 'POST'})
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)

    def test_invalid_questions(self):
        for payload in [[], {}, {'soru': 123}, {'soru': '  '}, {'soru': 'x' * 4001}]:
            self.assertEqual(self.client.post('/sohbet', json=payload).status_code, 400)
        self.assertEqual(self.client.post('/sohbet', data='{', content_type='application/json').status_code, 400)

    def test_service_success_and_failure(self):
        import sys
        import types
        fake = types.ModuleType('app.services.ai_service')
        fake.yapay_zeka_yaniti_al = lambda soru: 'Test yanıtı'
        with patch.dict(sys.modules, {'app.services.ai_service': fake}):
            response = self.client.post('/sohbet', json={'soru': 'Merhaba'})
            self.assertEqual(response.json, {'cevap': 'Test yanıtı'})
            def unavailable(soru):
                raise RuntimeError('private provider details')
            fake.yapay_zeka_yaniti_al = unavailable
            response = self.client.post('/sohbet', json={'soru': 'Merhaba'})
            self.assertEqual(response.status_code, 502)
            self.assertNotIn('private', response.get_data(as_text=True))

    def test_size_limit(self):
        self.assertEqual(self.client.post('/sohbet', json={'soru': 'x' * 40000}).status_code, 413)


if __name__ == '__main__':
    unittest.main()
