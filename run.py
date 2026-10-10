from app import create_app

app = create_app()                        ## Fabrikamızı çalıştırıp Flask uygulamamızı üretiyoruz

if __name__ == '__main__':               
    
    app.run(debug=True)                   ## # Sunucuyu yerel bilgisayarımızda canlıya alıyoruz


    