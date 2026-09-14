<?php
// deploy/seohost_thegame2026_art/public_html/api/index.php
// Lekki, bezobsługowy silnik REST API zgodny z docs/api/specyfikacja.md
// Działa natychmiast na każdym hostingu współdzielonym (PHP 7.4 / 8.x + SQLite)

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Accept');

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$dbPath = __DIR__ . '/../dane/sanatoria.db';
if (!file_exists($dbPath)) {
    http_response_code(500);
    echo json_encode(['blad' => 'Baza danych nie istnieje pod ścieżką ' . $dbPath], JSON_UNESCAPED_UNICODE);
    exit;
}

try {
    $db = new PDO('sqlite:' . $dbPath);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['blad' => 'Błąd połączenia z bazą SQLite: ' . $e->getMessage()], JSON_UNESCAPED_UNICODE);
    exit;
}

// Pobranie żądanego endpointu
$endpoint = isset($_GET['endpoint']) ? trim($_GET['endpoint'], '/') : '';
if (empty($endpoint)) {
    $uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
    $endpoint = preg_replace('#^.*?api/v1/#', '', $uri);
    $endpoint = trim($endpoint, '/');
}

// 1. Endpoint ZDROWIE / HEALTHZ
if ($endpoint === 'zdrowie' || $endpoint === 'healthz') {
    $count = (int)$db->query("SELECT COUNT(*) FROM oferty WHERE aktywna = 1")->fetchColumn();
    $lastImport = $db->query("SELECT zaimportowano_o FROM przebiegi_crawlerow ORDER BY id DESC LIMIT 1")->fetchColumn();
    echo json_encode([
        'status' => 'ok',
        'wersja_api' => '0.1.0',
        'wersja_kontraktu' => '0.1.0',
        'baza_ok' => true,
        'aktywne_oferty' => $count,
        'ostatni_import' => $lastImport ?: date('c'),
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

// 2. Endpoint SŁOWNIKI FILTRÓW
if ($endpoint === 'filtry') {
    $miejscowosci = $db->query("SELECT DISTINCT miejscowosc FROM oferty WHERE aktywna = 1 AND miejscowosc IS NOT NULL ORDER BY miejscowosc")->fetchAll(PDO::FETCH_COLUMN);
    $wojewodztwa = $db->query("SELECT DISTINCT wojewodztwo FROM oferty WHERE aktywna = 1 AND wojewodztwo IS NOT NULL ORDER BY wojewodztwo")->fetchAll(PDO::FETCH_COLUMN);
    $wyzywienie = $db->query("SELECT DISTINCT wyzywienie FROM oferty WHERE aktywna = 1 AND wyzywienie IS NOT NULL ORDER BY wyzywienie")->fetchAll(PDO::FETCH_COLUMN);
    $typyPokoju = $db->query("SELECT DISTINCT typ_pokoju FROM oferty WHERE aktywna = 1 AND typ_pokoju IS NOT NULL ORDER BY typ_pokoju")->fetchAll(PDO::FETCH_COLUMN);
    $jednostkiCeny = $db->query("SELECT DISTINCT jednostka_ceny FROM oferty WHERE aktywna = 1 AND jednostka_ceny IS NOT NULL ORDER BY jednostka_ceny")->fetchAll(PDO::FETCH_COLUMN);

    $stats = $db->query("SELECT MIN(CAST(cena AS NUMERIC)) AS min_c, MAX(CAST(cena AS NUMERIC)) AS max_c, MIN(liczba_dni) AS min_d, MAX(liczba_dni) AS max_d, COUNT(*) AS cnt FROM oferty WHERE aktywna = 1")->fetch();

    echo json_encode([
        'miejscowosci' => array_values($miejscowosci),
        'wojewodztwa' => array_values($wojewodztwa),
        'profile' => [],
        'wyzywienie' => array_values($wyzywienie),
        'typy_pokoju' => array_values($typyPokoju),
        'jednostki_ceny' => array_values($jednostkiCeny),
        'cena_min' => $stats['min_c'] !== null ? number_format((float)$stats['min_c'], 2, '.', '') : null,
        'cena_max' => $stats['max_c'] !== null ? number_format((float)$stats['max_c'], 2, '.', '') : null,
        'min_dni' => $stats['min_d'] !== null ? (int)$stats['min_d'] : null,
        'max_dni' => $stats['max_d'] !== null ? (int)$stats['max_d'] : null,
        'liczba_ofert_razem' => (int)$stats['cnt'],
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

// Pomocnicza funkcja mapowania wiersza SQLite na obiekt kontraktu Oferta
function mapujWierszNaOferte(array $r): array {
    $cenaWartosc = $r['cena'] !== null ? number_format((float)$r['cena'], 2, '.', '') : null;
    $kosztCalkowity = null;
    if ($r['jednostka_ceny'] === 'turnus_osoba' && $cenaWartosc !== null) {
        $kosztCalkowity = $cenaWartosc;
    } elseif ($r['jednostka_ceny'] === 'osobodoba' && $cenaWartosc !== null) {
        $dni = $r['liczba_dni'] ?? $r['liczba_nocy'];
        if ($dni !== null) {
            $kosztCalkowity = number_format(((float)$cenaWartosc) * (int)$dni, 2, '.', '');
        }
    }

    return [
        'id' => (int)$r['id'],
        'adapter' => $r['adapter'],
        'zrodlo_id' => $r['zrodlo_id'],
        'osrodek' => [
            'klucz' => $r['osrodek_klucz'],
            'nazwa' => $r['osrodek_nazwa'],
            'miejscowosc' => $r['miejscowosc'],
            'wojewodztwo' => $r['wojewodztwo'],
            'nip' => $r['nip'],
            'telefon' => $r['telefon'],
        ],
        'pakiet' => [
            'nazwa' => $r['nazwa_pakietu'],
            'liczba_dni' => $r['liczba_dni'] !== null ? (int)$r['liczba_dni'] : null,
            'liczba_nocy' => $r['liczba_nocy'] !== null ? (int)$r['liczba_nocy'] : null,
            'termin_od' => $r['termin_od'],
            'termin_do' => $r['termin_do'],
            'dostepny' => $r['dostepny'] !== null ? (bool)$r['dostepny'] : null,
        ],
        'cena' => [
            'wartosc' => $cenaWartosc,
            'waluta' => $r['waluta'] ?? 'PLN',
            'jednostka' => $r['jednostka_ceny'],
            'cena_od' => (bool)$r['cena_od'],
            'szacowany_koszt_calkowity' => $kosztCalkowity,
            'doplata_jedynka' => $r['doplata_jedynka'] !== null ? number_format((float)$r['doplata_jedynka'], 2, '.', '') : null,
            'oplata_klimatyczna_doba' => $r['oplata_klimatyczna_doba'] !== null ? number_format((float)$r['oplata_klimatyczna_doba'], 2, '.', '') : null,
        ],
        'standard' => [
            'wyzywienie' => $r['wyzywienie'],
            'typ_pokoju' => $r['typ_pokoju'],
            'liczba_zabiegow_dziennie' => $r['liczba_zabiegow_dziennie'] !== null ? (int)$r['liczba_zabiegow_dziennie'] : null,
            'zabiegi' => json_decode($r['zabiegi_json'] ?: '[]', true),
            'opieka_lekarska' => $r['opieka_lekarska'] !== null ? (bool)$r['opieka_lekarska'] : null,
        ],
        'profile' => json_decode($r['profile_json'] ?: '[]', true),
        'udogodnienia' => json_decode($r['udogodnienia_json'] ?: '{}', true),
        'linki' => [
            'url_rezerwacji' => $r['url_rezerwacji'],
            'url_zrodla' => $r['zrodlo_url'],
            'pobrano_o' => $r['pobrano_o'],
        ],
    ];
}

// 3. Endpoint SZCZEGÓŁY POJEDYNCZEJ OFERTY (/api/v1/oferty/{id})
if (preg_match('#^oferty/([0-9]+)$#', $endpoint, $m)) {
    $id = (int)$m[1];
    $stmt = $db->prepare("SELECT * FROM oferty WHERE id = ? AND aktywna = 1");
    $stmt->execute([$id]);
    $wiersz = $stmt->fetch();
    if (!$wiersz) {
        http_response_code(404);
        echo json_encode(['blad' => 'Nie znaleziono oferty'], JSON_UNESCAPED_UNICODE);
        exit;
    }
    echo json_encode(mapujWierszNaOferte($wiersz), JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

// 4. Endpoint LISTA OFERT (/api/v1/oferty)
if ($endpoint === 'oferty' || $endpoint === '') {
    $where = ["aktywna = 1"];
    $params = [];

    // Domyślnie ukrywaj przeszłe turnusy
    $pokazPrzeszle = filter_var($_GET['pokaz_przeszle'] ?? false, FILTER_VALIDATE_BOOLEAN);
    if (!$pokazPrzeszle) {
        $dzis = date('Y-m-d');
        $where[] = "(termin_do IS NULL OR termin_do >= ?)";
        $params[] = $dzis;
    }

    if (!empty($_GET['q'])) {
        $q = '%' . trim($_GET['q']) . '%';
        $where[] = "(osrodek_nazwa LIKE ? OR nazwa_pakietu LIKE ? OR miejscowosc LIKE ?)";
        $params[] = $q;
        $params[] = $q;
        $params[] = $q;
    }

    if (!empty($_GET['miejscowosc'])) {
        $where[] = "miejscowosc = ?";
        $params[] = trim($_GET['miejscowosc']);
    }
    if (!empty($_GET['wojewodztwo'])) {
        $where[] = "wojewodztwo = ?";
        $params[] = trim($_GET['wojewodztwo']);
    }
    if (!empty($_GET['wyzywienie'])) {
        $where[] = "wyzywienie = ?";
        $params[] = trim($_GET['wyzywienie']);
    }
    if (!empty($_GET['typ_pokoju'])) {
        $where[] = "typ_pokoju = ?";
        $params[] = trim($_GET['typ_pokoju']);
    }
    if (!empty($_GET['jednostka_ceny'])) {
        $where[] = "jednostka_ceny = ?";
        $params[] = trim($_GET['jednostka_ceny']);
    }
    if (isset($_GET['cena_min']) && is_numeric($_GET['cena_min'])) {
        $where[] = "CAST(cena AS NUMERIC) >= ?";
        $params[] = (float)$_GET['cena_min'];
    }
    if (isset($_GET['cena_max']) && is_numeric($_GET['cena_max'])) {
        $where[] = "CAST(cena AS NUMERIC) <= ?";
        $params[] = (float)$_GET['cena_max'];
    }
    if (isset($_GET['min_dni']) && is_numeric($_GET['min_dni'])) {
        $where[] = "liczba_dni >= ?";
        $params[] = (int)$_GET['min_dni'];
    }
    if (isset($_GET['max_dni']) && is_numeric($_GET['max_dni'])) {
        $where[] = "liczba_dni <= ?";
        $params[] = (int)$_GET['max_dni'];
    }
    if (!empty($_GET['termin_od'])) {
        $where[] = "(termin_od >= ? OR termin_od IS NULL)";
        $params[] = $_GET['termin_od'];
    }
    if (!empty($_GET['termin_do'])) {
        $where[] = "(termin_do <= ? OR termin_od IS NULL)";
        $params[] = $_GET['termin_do'];
    }
    if (filter_var($_GET['tylko_dostepne'] ?? false, FILTER_VALIDATE_BOOLEAN)) {
        $where[] = "dostepny = 1";
    }

    $sqlWhere = implode(" AND ", $where);

    // Zliczanie sumy wyników
    $countStmt = $db->prepare("SELECT COUNT(*) FROM oferty WHERE $sqlWhere");
    $countStmt->execute($params);
    $razem = (int)$countStmt->fetchColumn();

    // Sortowanie
    $sort = $_GET['sortuj'] ?? 'najnowsze';
    $orderMap = [
        'cena_asc' => 'CAST(cena AS NUMERIC) ASC, id ASC',
        'cena_desc' => 'CAST(cena AS NUMERIC) DESC, id DESC',
        'dni_asc' => 'liczba_dni ASC, id ASC',
        'dni_desc' => 'liczba_dni DESC, id DESC',
        'termin_od_asc' => 'termin_od ASC, id ASC',
        'najnowsze' => 'id DESC',
    ];
    $sqlOrder = $orderMap[$sort] ?? $orderMap['najnowsze'];

    // Paginacja
    $strona = max(1, (int)($_GET['strona'] ?? 1));
    $naStronie = max(1, min(100, (int)($_GET['na_stronie'] ?? 20)));
    $offset = ($strona - 1) * $naStronie;
    $stronRazem = max(1, (int)ceil($razem / $naStronie));

    $dataStmt = $db->prepare("SELECT * FROM oferty WHERE $sqlWhere ORDER BY $sqlOrder LIMIT ? OFFSET ?");
    $queryParams = array_merge($params, [$naStronie, $offset]);
    $dataStmt->execute($queryParams);
    $wiersze = $dataStmt->fetchAll();

    $elementy = array_map('mapujWierszNaOferte', $wiersze);

    echo json_encode([
        'elementy' => $elementy,
        'stronicowanie' => [
            'strona' => $strona,
            'na_stronie' => $naStronie,
            'razem' => $razem,
            'stron_razem' => $stronRazem,
        ],
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

http_response_code(404);
echo json_encode(['blad' => 'Nieznany endpoint: ' . $endpoint], JSON_UNESCAPED_UNICODE);
