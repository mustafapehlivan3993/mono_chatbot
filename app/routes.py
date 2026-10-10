from flask import Blueprint, request, jsonify
from app.ai_service import yapay_zeka_yaniti_al

bp = Blueprint('main', __name__)                     ## Blueprint yapısı oluşturma      

@bp.route('/sohbet', methods=['POST'])               ## Kullanıcıdan gelen post isteğini karşılar, ai_service.py kısmına iletir
def sohbet_rotasi():
   
    try:
        
        veri = request.get_json()                    ## Gelen JSON verisini alış
        
        if not veri or 'soru' not in veri:           ## İstek boşsa uarı veer
            return jsonify({'hata': 'Geçersiz istek! Lütfen JSON formatında "soru" alanı gönderin.'}), 400
        
        soru = veri.get('soru')
        
        bot_yaniti = yapay_zeka_yaniti_al(soru)       ## Yapay zeka servisindne yanıtı alıyıoruz
        
        return jsonify({'cevap': bot_yaniti}), 200

    except ValueError as ve:                          ## Hatalı durumlar için save
        return jsonify({'hata': str(ve)}), 400

    except Exception as e:
        
        print(f"KRİTİK HATA (Routes): {e}")
        return jsonify({'hata': 'Sunucu tarafında beklenmeyen bir hata oluştu.'}), 500


    