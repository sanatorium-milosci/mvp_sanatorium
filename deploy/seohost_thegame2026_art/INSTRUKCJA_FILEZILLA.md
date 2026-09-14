# Instrukcja wdrożenia na seohost.pl przez SFTP / FileZilla
**Domena**: `thegame2026.art`  
**Katalog źródłowy do wdrożenia**: `deploy/seohost_thegame2026_art/public_html/`

---

## 1. Co zawiera paczka wdrożeniowa?

Paczka w katalogu `deploy/seohost_thegame2026_art/public_html/` jest w 100% gotowa do działania na hostingu współdzielonym seohost.pl bez konieczności instalowania czegokolwiek na serwerze:
- **Frontend SPA (React 19 + TypeScript + Vite)**: skompilowane zoptymalizowane pliki HTML/CSS/JS (`index.html`, `assets/`, `favicon.svg`).
- **Natywne REST API (`api/index.php`)**: lekki silnik obsługujący pełny kontrakt API (`/api/v1/oferty`, `/api/v1/filtry`, `/healthz`), łączący się z bazą SQLite.
- **Baza danych (`dane/sanatoria.db`)**: baza SQLite zasilona 206 rzeczywistymi ofertami ośrodków (Ciechocinek, Kudowa-Zdrój).
- **Konfiguracja serwera (`.htaccess`)**:
  - Automatyczne przekierowanie na bezpieczne połączenie `HTTPS`
  - Przepisywanie ścieżek dla routingu React SPA (odświeżanie podstron działa poprawnie)
  - Przekierowanie `/api/v1/*` oraz `/healthz` do skryptu API
  - Blokada bezpośredniego pobierania pliku bazy danych (`dane/.htaccess`)
  - Kompresja GZIP/Deflate i nagłówki bezpieczeństwa

---

## 2. Krok po kroku: Połączenie przez FileZilla

1. **Uruchom program FileZilla**.
2. W górnym pasku szybkiego łączenia (lub w *Plik -> Menedżer stron*) wpisz dane dostępowe z maila powitalnego od seohost.pl:
   - **Serwer (Host)**: `thegame2026.art` (lub adres serwera z panelu, np. `s123.seohost.pl` albo adres IP)
   - **Protokół**: `SFTP - SSH File Transfer Protocol` (port `22`)  
     *(Jeśli Twoje konto nie ma włączonego SFTP/SSH, wybierz `FTP` z jawnym TLS na porcie `21`)*
   - **Użytkownik**: Twoja nazwa użytkownika w DirectAdmin
   - **Hasło**: Twoje hasło do konta hostingowego
   - **Port**: `22` (dla SFTP) lub `21` (dla FTP)
3. Kliknij **Szybkie łączenie** (lub *Połącz*).
4. Jeśli pojawi się okno z pytaniem o akceptację klucza hosta SSL/SSH, zaznacz *„Zawsze ufaj temu hostowi”* i kliknij **OK**.

---

## 3. Przesłanie plików na serwer

1. **Prawy panel (Serwer zdalny)**:
   - Przejdź do katalogu domeny:
     `/domains/thegame2026.art/public_html/`  
     *(W niektórych kontach główna domena ma ścieżkę bezpośrednio w `/public_html/`)*.
   - Jeśli w katalogu `public_html` znajdują się domyślne pliki powitalne seohost (np. `index.html` z logo seohost), usuń je lub zmień ich nazwę.

2. **Lewy panel (Twój komputer lokalny)**:
   - Wejdź do katalogu projektu:
     `deploy/seohost_thegame2026_art/public_html/`

3. **Przesłanie plików**:
   - Zaznacz **WSZYSTKIE** elementy w tym folderze:
     - `.htaccess` *(upewnij się w FileZilla w menu „Serwer”, że włączona jest opcja „Wymuś pokazywanie ukrytych plików”)*
     - `index.html`
     - `favicon.svg`
     - folder `assets/`
     - folder `api/`
     - folder `dane/`
   - Kliknij prawym przyciskiem myszy i wybierz **Wyślij** (lub po prostu przeciągnij je z lewego panelu do prawego).
   - Poczekaj na zakończenie transferu (kolejka plików w dolnym panelu powinna być pusta, a zakładka *„Nieudane transfery”* mieć licznik 0).

---

## 4. Włączenie certyfikatu SSL (HTTPS) w panelu seohost.pl

Aby strona działała pod bezpiecznym adresem `https://thegame2026.art`:
1. Zaloguj się do panelu **DirectAdmin** w seohost.pl.
2. Wybierz domenę `thegame2026.art`.
3. Przejdź do zakładki **Certyfikaty SSL** (SSL Certificates).
4. Zaznacz opcję: **Darmowy certyfikat od Let's Encrypt**.
5. Zaznacz pozycje:
   - `thegame2026.art`
   - `www.thegame2026.art`
6. Kliknij **Zapisz** / **Zainstaluj**. Certyfikat wygeneruje się w około 1–2 minuty.

---

## 5. Test i weryfikacja wdrożenia

Po przesłaniu plików sprawdź w przeglądarce:

1. **Strona główna**:
   Otwórz: `https://thegame2026.art`
   - Powinna załadować się aplikacja wyszukiwarki z nagłówkiem „Wyszukiwarka pobytów sanatoryjnych”.
   - Powinny pojawić się oferty sanatoriów z cenami, terminami i udogodnieniami.
   - Sprawdź działanie filtrów: miejscowość (np. *Ciechocinek*), jednostka ceny, suwaki cenowe i sortowanie.

2. **Test API i bazy danych**:
   - `https://thegame2026.art/healthz`  
     -> Powinno zwrócić JSON: `{"status":"ok","aktywne_oferty":208,...}`
   - `https://thegame2026.art/api/v1/oferty?na_stronie=5`  
     -> Powinno zwrócić listę ofert w formacie JSON
   - `https://thegame2026.art/api/v1/filtry`  
     -> Powinno zwrócić metadane filtrów i zakresy cenowe

3. **Test bezpieczeństwa**:
   - `https://thegame2026.art/dane/sanatoria.db`  
     -> Przeglądarka powinna zwrócić błąd **403 Forbidden** (plik bazy jest chroniony przed bezpośrednim pobraniem).
