from flask import Blueprint, current_app, request, jsonify

bp = Blueprint('main', __name__)


@bp.get('/')
def anasayfa():
    return 'Mono Nutrition Chatbot Çalışıyor'


@bp.get('/health')
def health():
    return jsonify(durum='ok', depolama='sqlite-gecici')


@bp.post('/sohbet')
def sohbet_rotasi():
    veri = request.get_json(silent=True)
    if not isinstance(veri, dict):
        return jsonify(hata='JSON nesnesi gönderin.'), 400
    soru = veri.get('soru')
    if not isinstance(soru, str) or not soru.strip() or len(soru) > 4000:
        return jsonify(hata='Soru 1–4000 karakter arasında olmalıdır.'), 400
    try:
        from app.services.ai_service import yapay_zeka_yaniti_al
        cevap = yapay_zeka_yaniti_al(soru.strip())
        return jsonify(cevap=cevap)
    except Exception:
        current_app.logger.error('Sohbet servisi yanıt veremedi.')
        return jsonify(hata='Asistan şu anda yanıt veremiyor. Lütfen tekrar deneyin.'), 502


@bp.post('/api/lead')
@bp.post('/api/leads')
def lead_kaydet():
    import re
    from uuid import UUID, uuid4
    from app import database

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(basari=False, hata='JSON nesnesi gönderin.'), 400
    clean = {}
    for key, maximum in [('isim', 150), ('eposta', 254), ('telefon', 40), ('mesaj', 5000)]:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            return jsonify(basari=False, hata=f'{key} zorunludur, en fazla {maximum} karakter olabilir.'), 400
        clean[key] = value.strip()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', clean['eposta']):
        return jsonify(basari=False, hata='Geçerli bir e-posta girin.'), 400
    if not re.fullmatch(r'\+?[0-9 ()\-\.]+', clean['telefon']) or not 7 <= len(re.sub(r'\D', '', clean['telefon'])) <= 15:
        return jsonify(basari=False, hata='Geçerli bir telefon girin.'), 400
    clean['kaynak'] = data.get('kaynak', 'form')
    if clean['kaynak'] not in ('form', 'sohbet'):
        return jsonify(basari=False, hata='Geçersiz kayıt kaynağı.'), 400
    try:
        clean['id'] = str(UUID(data['istekId'])) if 'istekId' in data else str(uuid4())
    except (ValueError, TypeError, AttributeError):
        return jsonify(basari=False, hata='istekId geçerli bir UUID olmalıdır.'), 400
    try:
        lead_id = database.save_lead(clean)
        return jsonify(basari=True, durum='basarili', id=lead_id, mesaj='Talebiniz kaydedildi.'), 200
    except ValueError:
        return jsonify(basari=False, hata='İstek kimliği başka bir kayıtla çakışıyor.'), 409
    except Exception:
        current_app.logger.error('Lead veritabanına yazılamadı.')
        return jsonify(basari=False, hata='Talep kaydedilemedi. Lütfen tekrar deneyin.'), 503


@bp.get('/api/leads')
def lead_listele():
    import hmac
    import os
    from app import database

    import hashlib
    from pathlib import Path
    token = os.environ.get('ADMIN_API_KEY', '')
    expected = (hashlib.sha256(token.encode()).hexdigest() if token else
                Path(__file__).with_name('panel-key.sha256').read_text().strip())
    supplied = request.headers.get('Authorization', '')
    provided = supplied[7:] if supplied.startswith('Bearer ') else ''
    if not provided or not hmac.compare_digest(hashlib.sha256(provided.encode()).hexdigest(), expected):
        return jsonify(basari=False, hata='Yetkisiz erişim.'), 401
    try:
        limit = int(request.args.get('limit', '100'))
        offset = int(request.args.get('offset', '0'))
        if not 1 <= limit <= 100 or offset < 0:
            raise ValueError()
    except ValueError:
        return jsonify(basari=False, hata='Geçersiz sayfalama.'), 400
    try:
        rows, more = database.list_leads(limit, offset)
        return jsonify(basari=True, leads=rows, devam=more)
    except Exception:
        current_app.logger.error('Lead listesi alınamadı.')
        return jsonify(basari=False, hata='Kayıtlar alınamadı.'), 503
