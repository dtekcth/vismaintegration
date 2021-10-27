# DBus fakturor i Visma
Detta script eller integration tar information från DBus formulären och lägger automatiskt till faktura utkast i visma.

# Setup 
Ladda ner hela detta repot

Se till att fixa configurationen i `config.toml` (använd exempel filen för information om vad som behövs)

client_ID och client_secret hittas i sektionskassören lösenordsfil. Token genereras efter första körningen (och behöver genereras om varje timme)

### Visma IDn
Dessa idn får man tag på genom att logga in på visma som vanligt och kolla på vilken route under antingen /internal/articles/{id} eller liknande. Detta fungerar både för artiklarna och för kostnadsstället

### Sheets
Körjournalen och drivers (Kontakt uppgifter) laddas ner och uppdateras från DBus drive.
Glöm inte uppdatera meter_indication_base med lägsta mätar ställningen som är med i körjournalen

### other 
Om du får ett fel med browser. uppdatera denna till en webbläsare du har installerad.

# Användning
För att allting ska fungera korrekt behöver du verifiera dig mot Visma. Detta kommer göras om `--authenicate` flaggan används vid körning. Då öppnas webbläsaren och du får logga in med dina vanliga visma uppgifter, Sedan kommer du till en Unable to connect. Ta då den långa strängen med bokstäver som du hittar mellan `code=` och `&` i URLn och klistra in i terminalen. Efter det ska du vara autentiserad och kan därmed skicka och ta emot information från VismaAPIet.

Kontrollera sedan ordentligt att informationen som programmet ger i terminalen stämmer för varje förare och körning. Om något inte stämmer måste DU ändra det i .csv filerna (google sheetsen) och sedan köra skriptet igen. 

I vissa situationer kommer det inte finnas kunder inlagda i Visma då behöver du göra detta manuellt. Enklast görs det genom att klicka 'Ny Kund' och sedan söka efter personen med deras personnummer (glöm inte fylla i e-postaddress efter). När du gjort det med alla kunder som saknas kör skriptet igen och kolla så allt stämmer. 

