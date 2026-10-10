from groq import Groq
from config import GROQ_API_KEY                    ## Config.py daki tanımlı API'yı entegre ettik

client = Groq(api_key = GROQ_API_KEY)

def yapay_zeka_yaniti_al(soru):                         ## Kullanıcıdan gelen soruyu alır, Groq API'ye gönderir
    if not soru:
        raise ValueError("HATA: Soru alanı boş olamaz!")
    
    try:
        cevap = client.chat.completions.create(
            model = 'openai/gpt-oss-120b',              ## Kullanacağımız model
            messages=[
                {
                    'role': 'system',                   ## AI 'ın kişiliğini seçtik
                    'content': 'Sen MONO NUTRITION markasının profesyonel beslenme, fitness ve takviye ürünleri danışmanısın. Kısa ve net yanıtlar ver.'
                },
                {
                    'role': 'user',
                    'content': soru
                }
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        bot_mesaji = cevap.choices[0].message.content
        return bot_mesaji

    except Exception as hata:
        print(f'KRİTİK HATA (AI servisi): {hata}')
        return 'Üzgünüm, şu anda yapay zeka servisine bağlanırken bir sorun oluştu. Lütfen daha sonra tekrar deneyin. Anlayışınız için teşekkürler.'






