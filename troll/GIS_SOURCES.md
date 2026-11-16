# GIS_SOURCES - oficjalne, legalnie używalne źródła geodanych dla rekonstrukcji Norwegii 1:1

Data sondowania: **2026-11-16**. Środowisko: curl przez proxy HTTPS (bez ograniczeń sieciowych poza wymienionymi niżej).
Zakres: Norwegia kontynentalna + Svalbard + Jan Mayen.

## 0. Konwencje i legenda statusów

| Status | Znaczenie |
|---|---|
| **VERIFIED-BY-REQUEST (HTTP xxx)** | Endpoint faktycznie odpytany 2026-11-16; podano kod HTTP i co zwrócił |
| **DOCUMENTATION-ONLY** | Informacja z metadanych/dokumentacji lub wiedzy ogólnej, nie sprawdzona żądaniem |
| **UNREACHABLE** | Host zresetował połączenie / 502 z proxy po 3 próbach ("niedostępny z tego środowiska") |
| "not verified" | Nie udało się potwierdzić - nie zgadywać |

Metadane licencyjne i daty aktualizacji pochodzą z API katalogu Geonorge
(`https://kartkatalog.geonorge.no/api/getdata/{uuid}`, HTTP 200) - to jest **VERIFIED-BY-REQUEST jako treść metadanych**,
ale sama treść licencji (np. tekst CC BY 4.0) nie była czytana. Tam, gdzie metadane i inne źródło się różnią, jest to zaznaczone.

Częste CRS: EPSG:25833 (ETRS89 / UTM 33N), 25832 (UTM 32N), 25835 (UTM 35N), 25829 (UTM 29N, Jan Mayen),
4258 (ETRS89 geograficzny), 5973 (UTM33 + NN2000 wysokości), 3035 (LAEA).

---

## 1. Kartverket - Nasjonal høydemodell (hoydedata.no): DTM 1 m, DOM 1 m, DTM 10 m, LiDAR

### 1.1 WCS (Geonorge) - DTM

| Pole | Wartość |
|---|---|
| Dostawca | Kartverket (ProviderName w Capabilities: Kartverket, `hoydedata.no`) |
| Zbiór | NHM_DTM_25833 (Nasjonal høydemodell, Digital terrengmodell) |
| Zawartość | Teren (DTM), Float32 w metrach (wartości min/max 3.4E-38..3.4E+38 w DescribeCoverage) |
| Natywny CRS | **EPSG:25833** (kopie: `wcs.hoyde-dtm-nhm-25832`, `...-25835` - też HTTP 200) |
| Rozdzielczość | **1 m** (GeoTIFF z GetCoverage 1.0.0: `ModelPixelScale = 1,1`; offsetVector 1 m w DescribeCoverage) |
| Zasięg siatki (DescribeCoverage 2.0.1) | x: -100275..1150255, y: 6399725..8000275 (EPSG:25833) - czyli tylko kontynent, **bez Svalbardu** (próba na y=8 700 000: błąd/brak danych) |
| Coverage ID | `nhm_dtm_topo_25833` oraz `nhm_dtm_topo_25833_skyggerelieff` (cieniowanie, nie dane wysokościowe) |
| Format | `image/tiff` (GeoTIFF), `image/netcdf` (2.0.1 formatSupported) |
| URL | `https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833` |
| Metoda | WCS 1.0.0 / 1.1.x / 2.0.1 (ArcGIS Server za Geonorge) |
| Autoryzacja | **Nie** |
| Licencja | Capabilities: `Fees: free`, `AccessConstraints: None`; metadane WMS tego zbioru: "No conditions apply" ; zbiory powiązane (DTM1 Atom, DOM1) - CC BY 4.0 (metadane), a nagłówek Atom feed - NLOD 2.0 (patrz uwaga niżej) |
| Aktualność | Nie podana w Capabilities (not verified); Atom feed DTM1/DOM1: `updated 2025-09-02` |
| Status | **VERIFIED-BY-REQUEST** |

Wyniki prób (2026-11-16):

| Żądanie | Wynik |
|---|---|
| GetCapabilities 1.0.0 / 2.0.1 / bez wersji / 1.1.1 | HTTP 200 text/xml (4140 B / 6432 B) |
| DOM: `wcs.hoyde-dom-nhm-25833` Capabilities | HTTP 200; CoverageId `nhm_dom_topo_25833`, `nhm_dom_topo_25833_skyggerelieff` |
| DescribeCoverage 2.0.1 `nhm_dtm_topo_25833` | HTTP 200 |
| **GetCoverage 1.0.0** 500x500 px (BBOX 262000,6649000,262500,6649500) | HTTP 200 image/tiff, 1 049 839 B, float32, wartości 0.055..16.95 m |
| GetCoverage 1.0.0 2000x2000 px | HTTP 200, 16 780 399 B, 13.5 s (DOM: 13.5 s; DTM 2500x2500: 26.2 MB, 20.1 s) |
| GetCoverage 1.0.0 3000x3000 px (3 km x 3 km @1 m) | **HTTP 504 Gateway Timeout po 30 s** |
| GetCoverage 1.0.0 4000x4000 px | HTTP 504 |
| GetCoverage 1.0.0 8000x8000 px | błąd: "Request image size exceeds allowed limit" (limit rozmiaru obrazu; dokładny próg nie ustalony, leży między 2500 a 3000 px na stronę w praktyce przez timeout) |
| GetCoverage 1.0.0 100 km x 100 km z resamplingiem do 1000x1000 px (100 m/px) | HTTP 200, 4.2 MB, 4.7 s (serwer przelicza resampling) |
| **GetCoverage 2.0.1** (SUBSET=x(..),y(..), format image/tiff, różne warianty SUBSETTINGCRS) | **HTTP 400** (pusty ArcGIS "http.400") we wszystkich wariantach, które próbowałem - 2.0.1 GetCapabilities/DescribeCoverage działają, GetCoverage nie udało się uruchomić. **Używać WCS 1.0.0.** |
| `https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm1` i `wcs.hoyde-dtm10`, `wcs.hoyde-dom`, `wcs.dtm`... | HTTP 200 z "UKJENT APPLIKASJON" - **te nazwy usług nie istnieją** |
| `https://wms.geonorge.no/skwms1/wcs.hoyde-dom10_33` (z metadanych "Høyde DOM 10 WCS") | HTTP 200 z "UKJENT APPLIKASJON" - **adres z metadanych jest martwy** |
| `https://wms.geonorge.no/skwms1/wcs.hoyde-dtm10_33` | HTTP 500 |

Wniosek praktyczny: dla pełnej Norwegii przez WCS potrzeba kafelkowania po ok. 2000x2000 px (2 km x 2 km przy 1 m);
cały kraj (ok. 1.25 mln x 1.6 mln m bbox) to dziesiątki tysięcy żądań - **do masowego pobrania użyć plików (1.2)**, WCS tylko do
podglądu/łatek.

### 1.2 Pliki: DTM1 / DOM1 (Atom feed, kafle 15 km)

| Pole | Wartość |
|---|---|
| Dostawca | Kartverket |
| Zbiory | "DTM 1 Høydedata" i "DOM 1 Høydedata" |
| Zawartość | GeoTIFF float32, kafle 15 km x 15 km; Atom feed DTM1: **2033 wpisów** (kafli) |
| CRS | EPSG:25833 w tym kaflu (kategoria w feedzie: `ETRS89 / UTM zone 33N`); inne kafle mogą mieć inne strefy (not verified dla wszystkich) |
| Rozdzielczość | 1 m |
| Pokrycie | Norwegia kontynentalna (metadane: "Norge fastland"); zakres Atom `georss:polygon` 57.85-71.31 N, 4.28-31.35 E. **Bez Svalbardu i Jan Mayen** |
| URL indeksu | `https://nedlasting.geonorge.no/geonorge/ATOM/hoydedata/Hoydedata_ServiceFeed.atom` |
| URL DTM1 | `https://nedlasting.geonorge.no/geonorge/ATOM/hoydedata/datasett/DTM1.atom` |
| URL DOM1 | `https://nedlasting.geonorge.no/geonorge/ATOM/hoydedata/datasett/DOM1.atom` |
| URL kafla (przykład) | `https://nedlasting.geonorge.no/hoydedata/DTM1/33-107-122.tif` |
| Metoda | Plik (HTTP GET, INSPIRE Atom) |
| Autoryzacja | **Nie** |
| Rozmiar kafla | Przykładowy kafel 33-107-122: `content-length: 1 182 467 120` B (**ok. 1.18 GB**), `accept-ranges: bytes` (wspiera Range, ale to nie jest potwierdzony COG), last-modified 2025-09-02. Łączny rozmiar kraju: **not verified** (mnożenie 2033 x do 1.2 GB daje górne oszacowanie rzędu kilku TB) |
| Licencja | Nagłówek Atom feed: **NLOD 2.0** (`https://data.norge.no/nlod/en/2.0`); metadane Geonorge "DTM1 Atom feed-tjeneste" i "Høyde DOM1": **CC BY 4.0**. **Rozbieżność** - traktować jako NLOD 2.0 / CC BY 4.0 (oba wymagają atrybucji; stosować bardziej rygorystyczny wymóg, czyli podać obie nazwy) |
| Aktualność | Feed `updated 2025-09-02`; metadane DOM1: 2021-01-25 (data metadanych) |
| Status | **VERIFIED-BY-REQUEST** (feed HTTP 200 4667 B; DTM1.atom HTTP 200 5.4 MB; HEAD kafla HTTP 200) |

Uwaga: stary dataset "DTM 10 Terrengmodell (UTM33) - Historisk" (uuid `dddbb667-1303-4ac5-8640-7ec04c0e3918`) ma metadane:
**dane z 2013**, status "Må oppdateres", CC BY 4.0, 254 komórki (np. `6400-1`), format DEM, siatka 10 m, "na stronie zagranicznej dane niepewne".
Aktualne DTM10 jest wg metadanych dostępne z hoydedata.no (**not verified** - strona `https://hoydedata.no/LaserInnsyn2/` zwraca HTTP 200,
ale to aplikacja JS bez API sprawdzonego tutaj). **Zalecenie:** DTM10/DTM50 liczyć lokalnie z DTM1 (resampling), nie polegać na pliku historycznym.

### 1.3 API punktowe wysokości

| Pole | Wartość |
|---|---|
| URL | `https://ws.geonorge.no/hoydedata/v1/punkt?nord=6649000&ost=262000&koordsys=25833` |
| Wynik | `{"koordsys":25833,"punkter":[{"datakilde":"dtm1","terreng":"BymessigBebyggelse","x":262000.0,"y":6649000.0,"z":4.55}]}` |
| `.../v1/datakilder` | `dtm1`, `dom1`, `dybdekurver`, `hoydekurver`, `innsjohoyde`, ... |
| Autoryzacja | Nie |
| Status | **VERIFIED-BY-REQUEST (HTTP 200)**. Dla punktu poza zasięgiem (y=8 700 000) zwraca `z: null`. Limity zapytań: not verified |
| Uwaga | `https://api.kartverket.no/hoydedata/v1/punkt` zwraca HTTP 404 (inny prefiks niż stedsnavn) |

### 1.4 Chmury punktów LiDAR

| Pole | Wartość |
|---|---|
| Zbiór | "Høydedata - laser" (uuid `f297e948-8a34-4e6c-9740-54b3a657f8d5`) |
| Zawartość | Chmury punktów z ALS, format **LAZ**, per projekt, klasyfikacja wg FKB-Laser |
| URL | `https://hoydedata.no/LaserInnsyn2/` (HTTP 200, aplikacja webowa) |
| Licencja | Metadane: "No conditions apply to access and use" (INSPIRE), dane otwarte |
| Metoda | Pobieranie przez aplikację webową (bez zweryfikowanego API), not verified czy jest masowe API |
| Autoryzacja | Metadane mówią "Åpne data"; czy pobieranie wymaga konta - **not verified** |
| Status | Metadane **VERIFIED-BY-REQUEST (HTTP 200)**, samo pobranie LAZ **not verified** |

---

## 2. Geonorge - API pobierania (nedlasting) i katalog (kartkatalog)

| Endpoint | Wynik 2026-11-16 |
|---|---|
| `https://kartkatalog.geonorge.no/api/search?text=...&limit=N` | HTTP 200 JSON, pola `Uuid`, `Title`, `Organization`, `DistributionProtocol`, `AccessConstraint`... |
| `https://kartkatalog.geonorge.no/api/getdata/{uuid}` | HTTP 200 JSON (metadane, Constraints, DateUpdated, BoundingBox, ReferenceSystems) |
| `https://nedlasting.geonorge.no/api/capabilities/{uuid}` | HTTP 200 JSON (`supportsProjectionSelection`, `supportsAreaSelection`, `supportsPolygonSelection`, `supportsDownloadBundling`) |
| `https://nedlasting.geonorge.no/api/codelists/projection/{uuid}`, `.../format/{uuid}`, `.../area/{uuid}` | HTTP 200 JSON |
| `https://nedlasting.geonorge.no/api/capabilities` (bez uuid) | HTTP 302 -> strona HTML dokumentacji |

Autoryzacja: **nie** dla listowania i dla zbiorów otwartych. Samo zamówienie pobrania (POST `/api/order`) **nie było testowane**
(not verified), żeby nie generować zamówień. Pobieranie zbiorów "Norge digitalt begrenset" wymaga logowania/umowy.

Wszystkie poniżej: dostawca = Kartverket, chyba że napisano inaczej; "Hele landet" = dostępne zamówienie krajowe (`landsdekkende`), poza tym fylkesvis (15) i kommunevis (357).

| Zbiór (uuid) | Zawartość | Skala / rozdz. | CRS | Format | Licencja (z metadanych) | Aktualizacja | Pokrycie |
|---|---|---|---|---|---|---|---|
| **N50 Kartdata** `ea192681-d039-42ec-b1bc-f3ce04c189ac` | Pełna topografia 1:50 000 (wody, tereny, budynki, drogi, koleje...), 1:25 000-1:100 000 | 50 000 | 25832, 25833, 25835 | FGDB, GML, PostGIS, SOSI | **CC BY 4.0**, "Åpne data" | DateUpdated 2026-11-14, aktualizowany tygodniowo | "Norge fastland", bbox 2-33 E, 57-72 N. **Bez Svalbardu** |
| **N250 Kartdata** `442cae64-b447-478d-b384-545bc1d9ab48` | Generalizacja N50 | 250 000 | 25832/33/35 | FGDB, GML, PostGIS, SOSI | CC BY 4.0 | 2026-11-14 | Norge fastland |
| **N1000 Kartdata** `aee42bb6-d0e9-4d70-86fe-6ea76c381055` | Generalizacja 1:1 000 000 (status w metadanych: "Arkivert") | 1 000 000 | 25832/33/35, 3035, 4258 | FGDB, GML, PostGIS, SOSI | CC BY 4.0 | 2026-11-14 | Norge fastland |
| **Administrative enheter - kommuner** `041f1e6e-bdbc-4091-b48f-8a5990f3cc5b` (fylker: `6093c8a8-fa80-11e6-bc64-92361f002671`) | Granice gmin/województw, numery, nazwy norw./saami/kvenske | 1:5000 wg metadanych | 25832/33/35, 3035, 4258 | FGDB, GeoJSON, GML, PostGIS | CC BY 4.0 | DateUpdated 2026-07-30 | Norge fastland (Svalbard/Jan Mayen jako osobne dane: not verified) |
| **Administrative enheter WFS** `wfs.administrative_enheter` | typy: `app:Fylke`, `app:Kommune`, `app:Grense` | - | - | WFS 2.0 | - | - | HTTP 200 (30 287 B) |
| **Stedsnavn** `30caed2f-454e-44be-b5cc-26bb5c0110ca` | Nazwy geograficzne (SSR), współrzędne punktu, typ obiektu, język, status | 1:50 000 | 25832/33/35, 3035, 4258 | FGDB, GML, PostGIS, SOSI | CC BY 4.0 | DateUpdated 2026-11-13 | "Norge", "fastland", "Norske havområder" |
| **Stedsnavn - API** `https://ws.geonorge.no/stedsnavn/v1/navn?sok=...` | wyszukiwanie nazw (np. Galdhøpiggen: `navneobjekttype: Fjell`, lat 61.63644 lon 8.31248) | - | WGS84 / `koordsys` | JSON | jak wyżej (CC BY 4.0) | na żywo | HTTP 200. Alias `https://api.kartverket.no/stedsnavn/v1/navn` też HTTP 200 |
| **Kommuneinfo** `https://ws.geonorge.no/kommuneinfo/v1/kommuner` | lista 357 gmin (nr, nazwa) | - | - | JSON | not verified (prawdopodobnie jak Admin. enheter) | na żywo | HTTP 200 |
| **Matrikkelen - Bygningspunkt** `24d7e9d1-87f6-45a0-b38e-3447f8d7f9a1` | Punkt reprezentatywny budynku, typ budynku, numer, status | 1:1000 | 25832/33/35, 3035, 4258 | FGDB, GML, PostGIS, SOSI | CC BY 4.0 | 2026-11-16 | Norge fastland |
| **FKB-Bygning** `8b4304ea-4fb0-479c-a24d-fa225e2c6e97` | Poligony budynków 3D (dachy, kalenice) 1:500 | 500 | 5972/5973/5975 (UTM + NN2000) | FGDB, GML, SOSI | **"Norge digitalt begrenset" - Norge digitalt-lisens**: *"Nedlasting av data begrenset til Norge digitalt avtaleparter"* | 2026-11-15 | Norge. **DANE OGRANICZONE - nie do użycia w grze bez umowy Norge digitalt** |
| Inne FKB (FKB-Vann `595e47d9...`, FKB-AR5 `166382b4...`, FKB-Lufthavn `23dfcc33...`, FKB-Arealbruk `87b31015...`) | - | - | - | - | "norway digital restricted" (kartkatalog) | - | **OGRANICZONE** |
| **Sjøkart - Dybdedata** `2751aacf-5472-4850-a208-3532a51c529a` | patrz sekcja 12 | | | | | | |

Status całej sekcji: **VERIFIED-BY-REQUEST (HTTP 200)** dla katalogu, capabilities, codelists. Faktyczne pobranie plików N50 itd.
nie było wykonywane (not verified).

---

## 3. NVE (hydrologia, jeziora, lodowce)

**Uwaga o hostach:** `nve.geodataonline.no` jest **UNREACHABLE z tego środowiska** (3x proxy 502 "CONNECT tunnel failed").
`gis3.nve.no/map/rest/services` zwraca HTTP 200 ale z pustą listą usług. Aktualne działające: **`https://kart.nve.no/enterprise/rest/services`**
(HTTP 200, 7742 B, ok. 70 usług MapServer/FeatureServer).

| Zbiór | URL | Zawartość | Layers (zweryfikowane) | CRS | Rozmiar | Licencja | Status |
|---|---|---|---|---|---|---|---|
| **ELVIS - Elvenett** | `https://kart.nve.no/enterprise/rest/services/Elvenett1/MapServer` (i `/FeatureServer`) | Sieć rzeczna: osie rzek, strahler, nazwy, vassdragsnr | 0 oversikt, 1 hovedelv, 2 elvenett (polilinie; pola m.in. `elveordenstrahler`, `lengde_m`, `elvenavn`, `datafangstdato`, `oppdateringsdato`) | **25833** | layer 2: **1 954 539 obiektów** (`returnCountOnly`), `minScale 100000`, `maxRecordCount 2000`, tylko Query, JSON | Metadane Geonorge `3f95a194-0968-4457-a500-912958de3d39`: **NLOD 1.0** (`http://data.norge.no/nlod/no/1.0`), skala 50 000 | **VERIFIED-BY-REQUEST (HTTP 200)** |
| **Innsjødatabase** | `https://kart.nve.no/enterprise/rest/services/Innsjodatabase2/MapServer` | Jeziora (poligony): `vatnlnr`, nazwa, wysokość n.p.m., powierzchnia km2, nr magazynu. Opis usługi: ok. **243 000 jezior**, unikalny numer dla > 2500 m2 | 1 DybdePunkt, 2 DybdeKurve, 3 Innsjo_ved_dybdemaling, 4 Dybdekart, 5 Innsjodatabase, 6 KommunefordeltInnsjo | 25833 | layer 5: **267 194 obiektów** (count 2026-11-16), `maxRecordCount 2000` | Metadane `823b8639-9a49-41bf-8571-3608435eb149`: **NLOD 1.0**, skala 20 000, aktualizacja roczna, DateUpdated 2019-01-01 | **VERIFIED-BY-REQUEST (HTTP 200)** |
| **Lodowce (Breatlas / "Bre")** | `https://kart.nve.no/enterprise/rest/services/Bre2/MapServer` | Lodowce Norwegii kontynentalnej: poligony, grubość lodu, prędkość, pomiary bilansu masy | 9 Breflate (poligony; 6 743 obiekty; pola `brenavn`, `areal_km2`, `bretype`, `minhoyde_moh`, `makshoyde_moh`...), 16 Breflate_Historisk, 15 Bre, 17 Breregion, 3 Istykkelse, 4 Brehastighet, 13 Bresjo itd. | 25833 | `maxRecordCount 2000` | Metadane "Breer i Norge" `ef3e36ad-6914-432e-a0e0-4ff8e091a423`: "no restrictions"; dokładna nazwa licencji - **not verified** (prawdopodobnie NLOD, nie sprawdzono) | **VERIFIED-BY-REQUEST (HTTP 200)** |
| seNorgeGrid_png (ImageServer) | `https://kart.nve.no/enterprise/rest/services/seNorgeGrid_png/ImageServer` | siatka klimatyczna jako obraz | not verified | - | - | not verified | tylko na liście usług (HTTP 200 listy) |

Wymagana atrybucja (NLOD): wskazać źródło "NVE" i licencję (patrz sekcja "Obowiązki licencyjne").
Autoryzacja: **nie**. Przykład zapytania poprawnego: `.../Innsjodatabase2/MapServer/5/query?where=1%3D1&returnCountOnly=true&f=json` (HTTP 200).
Paginacja: `resultOffset`/`resultRecordCount`, max 2000 na stronę (z metadanych usługi `maxRecordCount`; tylko format JSON, brak GeoJSON/pbf w `supportedQueryFormats`).

---

## 4. NIBIO - AR5, AR50, SR16, CORINE

| Zbiór | Zawartość | Rozdz./skala | CRS | Dostęp | Licencja | Aktualizacja | Status |
|---|---|---|---|---|---|---|---|
| **AR50** (Arealressurskart 50) `4bc2d1e0-f693-4bf2-820d-c11830d849a3` | Pokrycie/użytkowanie terenu (artype, jakość lasu `Bonitet`, itd.), Norge | 1:20 000-1:100 000 | 4258, 25832, 25833, 25835 | Plik: FGDB/GDB/GML/SOSI przez `https://kartkatalog.nibio.no/api/capabilities/{uuid}` (osobny nedlasting NIBIO; capabilities dla SR16 raster: HTTP 200, `supportsPolygonSelection: false`); WMS `https://wms.nibio.no/cgi-bin/ar50_2?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities` (HTTP 200, warstwa `AR50_2`, `Bonitet`, `Bonitet11kl`); WFS `https://wfs.nibio.no/cgi-bin/ar50_2?Service=WFS&Request=GetCapabilities` (HTTP 200, feature type `ms:AR50`) | **NLOD 1.0**; WMS Capabilities: `Fees: no conditions apply`, `AccessConstraints: none` | DateUpdated 2026-03-16, nieregularnie | **VERIFIED-BY-REQUEST** (WMS/WFS HTTP 200) |
| **AR5 (FKB-AR5)** `166382b4-82d6-4ea9-a68e-6fd0c87bf788` | Szczegółowe użytkowanie ziemi 1:5000 | 5 000 | - | Pobieranie: **OGRANICZONE** (Norge digitalt). Otwarty jest tylko widok WMS: `https://wms.nibio.no/cgi-bin/ar5forvaltning2?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities` (HTTP 200) | WMS "no restrictions"; dane źródłowe - Norge digitalt | - | WMS **VERIFIED**; pobranie wektorów AR5 **niedostępne publicznie** (wg metadanych katalogu) |
| **SR16 - Skogressurskart 16x16 m** raster `5de45872-f534-4e97-840e-3cfd8db04398`, wektor `27206b9e-4830-4f71-810d-d04c0dc32b59` | Zasoby leśne: gatunek (`SRRTRESLAG`), wysokość (`SRRHOYDEM`, `SRRHOYDEO`), bonitet (`SRRBONITET`), objętość (`SRRVOLMB`/`SRRVOLUB`), biomasa (`SRRBMU`/`SRRBMO`), status (`SR16_STATUS`) | **16 m** piksel; skala od 1:5 000 do 1:50 000 | raster: 25832, 25833, 25835; wektor +4258 | Pliki: raster GeoTIFF, wektor FGDB/GML/SOSI/GDB, **fylkesvis**, przez `https://kartkatalog.nibio.no/api/capabilities/{uuid}`; WMS `https://wms.nibio.no/cgi-bin/sr16?VERSION=1.3.0&SERVICE=WMS&REQUEST=GetCapabilities` (HTTP 200, 58 938 B, warstwa grupowa `skogressurs_sr16`, MaxWidth/MaxHeight 5120, CRS m.in. EPSG:25833, 4326, 900913) | **NLOD 1.0** ("Ingen begrensninger på bruk er oppgitt"); WMS: `Fees: no conditions apply` | raster DateUpdated 2026-08-31, wektor 2026-11-03; status "Under arbeid" | **VERIFIED-BY-REQUEST** (WMS, capabilities); pobranie fylkesvis plików **not verified** |
| **CORINE Land Cover (Norge)** `1e03cfca-dd04-45b6-8c79-75f175b5b8ae` | Pokrycie terenu CLC | 1:100 000 | 4258, 25832/33/35 | Shape, GML (`kartkatalog.nibio.no`); WMS `https://wms.nibio.no/cgi-bin/clc?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities`, WFS `.../clc2012` | NLOD 1.0 (metadane NIBIO) | DateUpdated 2026-08-13 | metadane **VERIFIED**, WMS/WFS nie sondowane (not verified) |

Uwaga: SR16 obejmuje las produktywny (Norwegia kontynentalna); wartości wysokości drzew to klasyfikacje/średnie z lidaru, nie obiekty pojedyncze.
Svalbard/Jan Mayen: poza zakresem (bbox 2-33 E, 57-72 N).

---

## 5. Statens vegvesen - NVDB (drogi, tunele, mosty, promy)

| Pole | Wartość |
|---|---|
| Dostawca | Statens vegvesen (NVDB) |
| API | NVDB Les API v4: `https://nvdbapiles.atlas.vegvesen.no` |
| Wymagana autoryzacja | **Brak klucza/konta**, ale **obowiązkowy nagłówek `X-Client`** (identyfikator klienta); bez niego HTTP 400 "X-Client må være satt når du kaller Les API" (VERIFIED). Starszy host `nvdbapiles-v3` wymaga ponadto `User-Agent` (błąd 4017) |
| Przykłady (z `X-Client: geodata-research-probe`) | `/vegobjekttyper?inkluder=minimum` HTTP 200 (550 994 B); `/vegnett/api/v4/veglenkesekvenser/segmentert?antall=1` HTTP 200; `/vegobjekter/api/v4/vegobjekter/60?antall=1&inkluder=metadata` HTTP 200 |
| Typy obiektów (id) | **60 Bru** (mosty; statystyka: 29 388 szt., 2 059 227 m łącznie), **581 Tunnel** (1 291 szt.), **67 Tunnelløp** (1 561 szt., 5 961 803 m), 69 Tunnelportal, **770 Ferjesamband** (promy), 64 Ferjekai, 41 Ferjeoppstillingsplass, **105 Fartsgrense** (952 933 szt.), 45 Bomstasjon, 39 Rasteplass, 602 (311 693 szt., nazwa not verified) |
| Parametr CRS | `srid`: dozwolone **EPSG_5972, EPSG_5973, EPSG_5975, EPSG_4326, UTM_32, UTM_33, UTM_35, WGS_84** (np. `srid=4326`; **`srid=25833` odrzucone HTTP 400** - trzeba `UTM_33`) |
| Metoda | REST JSON, paginacja kursorowa (`metadata.neste.start`), filtry `kommune`, `vegsystemreferanse`, `antall` |
| Alternatywa plikowa | Geonorge "NVDB Vegnett" `ad17eb84-b6b7-4fd1-99d9-b1b920421705` (SOSI, EPSG:5973, CC BY 4.0, tygodniowo, DateUpdated 2026-11-12) oraz "NVDB Vegnett Pluss" `97e6a869-8dd4-4379-bf39-f7d7dbf94863` (GML/SOSI, miesięcznie, 2026-11-13); WMS `vegnett2` |
| Licencja | Zbiory Geonorge: **CC BY 4.0**. Licencja samego Les API: nie odczytana (**not verified**; strona główna API HTTP 200 nie została przeanalizowana pod kątem licencji) |
| Limity zapytań | not verified (dokumentacja wspomina śledzenie requestów przez X-Client) |
| Status | **VERIFIED-BY-REQUEST** (API) |

---

## 6. Bane NOR / Kartverket - sieć kolejowa

| Pole | Wartość |
|---|---|
| Dostawca | Bane NOR SF (publikacja przez Geonorge) |
| Zbiór | "Jernbane - Banenettverk" `c3da3591-cded-4584-a4b1-bc61b7d1f4f2` |
| Zawartość | Sieć torów (polilinie), węzły stacji, kilometraż, przerwy |
| WFS | `https://wfs.geonorge.no/skwms1/wfs.banenettverk?request=GetCapabilities&service=WFS` - HTTP 200 (29 997 B); typy: **`app:Banelenke`, `app:Stasjonsnode`, `app:Kilometerpunkt`, `app:Banekjedebrudd`** |
| WMS | `https://wms.geonorge.no/skwms1/wms.banenettverk?request=GetCapabilities&service=WMS` - HTTP 200 (16 829 B) |
| Pliki | Geonorge nedlasting: FGDB, GML, PostGIS, SOSI; CRS 25832, 25833, 3035, 4258 |
| Skala | 1:100 000 |
| Pokrycie | Norwegia kontynentalna ("Norges fastland") |
| Licencja | **NLOD 1.0** (`http://data.norge.no/nlod/no/1.0`) |
| Aktualność | DateUpdated 2025-03-06, aktualizacja roczna, status "Kontinuerlig oppdatert" |
| Autoryzacja | Nie |
| Status | **VERIFIED-BY-REQUEST** (WFS/WMS HTTP 200); pliki not verified |

---

## 7. Lotniska i porty

| Zbiór | Dostawca | Zawartość | Dostęp | Licencja | Status |
|---|---|---|---|---|---|
| **Lufthavn-punkt Avinor** `22485273-dc0c-4484-a8be-357105d65689` | Avinor | Punkty lotnisk Avinor | Geonorge nedlasting: FGDB, GML, PostGIS, SOSI; CRS 25832/33/35, 3035 | Metadane: "No conditions apply to access and use" (otwarte). Skala 1:20 000, DateUpdated 2025-09-03 | metadane **VERIFIED (HTTP 200)** |
| Støysoner Avinors lufthavner `1489f7f8-40c8-4dc4-83b6-bcf277b56506` | Avinor | strefy hałasu | j.w. | "no restrictions" (metadane katalogu) | tylko listing |
| FKB-Lufthavn `23dfcc33-fb04-4898-aa88-68b49c4bfea7` | Geovekst | szczegółowe obiekty lotniskowe | - | **Norge digitalt begrenset** | OGRANICZONE |
| Avinor Flydata `https://flydata.avinor.no/airportNames.asp` | Avinor | dane lotów (nie geometria) | HTTP | not verified | HTTP 200, ale odpowiedź to strona HTML "Flight data"; nie nadaje się jako źródło geometrii |
| **Havnedata** `e46767e4-c6d9-49a6-93e8-716da0922fd7` | Kartverket | porty (skala 1:5000, UTM+NN2000) | Geonorge nedlasting | **Norge digitalt begrenset** | OGRANICZONE; DateUpdated 2026-11-13 |
| ISPS Havneanlegg `dc9b4d63-8597-4971-92a4-9f665abc3e21` | Kystverket | obiekty portowe ISPS | `https://kystinfo.no/` (HTTP 200, portal HTML) | "no restrictions" (katalog), nazwa licencji not verified | metadane **VERIFIED**, API not verified |
| Porty z OSM | OSM | `harbour`, `ferry_terminal`, `aerodrome` | patrz sekcja 9 | ODbL | patrz sekcja 9 |

Zalecenie: lotniska/porty w grze budować z N50 (budynki/obiekty) + Avinor punkty + OSM; ruch lotniczy nie jest potrzebny.

---

## 8. MET Norway - Frost API, THREDDS, licencja

| Zasób | Wynik 2026-11-16 | Szczegóły |
|---|---|---|
| **Frost API** `https://frost.met.no/sources/v0.jsonld`, `.../observations/v0.jsonld` | **HTTP 401 "Missing authentication token"** | **Wymaga client-id** (rejestracja darmowa, HTTP Basic z client-id jako użytkownik) - **autoryzacja: TAK**. Ścieżki typu `/api/v0/...` dają HTTP 404 (błędny prefix). Odpowiedź zawiera `"license": "https://creativecommons.org/licenses/by/3.0/no/"` |
| `https://frost.met.no/index.html` | HTTP 200 | strona dokumentacji |
| **THREDDS** `https://thredds.met.no/thredds/catalog.html` | HTTP 200 | brak autoryzacji |
| seNorge_2018 `https://thredds.met.no/thredds/catalog/senorge/seNorge_2018/catalog.xml` | HTTP 200; podkatalogi `Archive/`, `Latest/`, `aggregated_products/`, `indices/`, `return_levels/` | usługi: `dapService`, `httpService`, `wms` |
| seNorge2018 NetCDF DAS/DDS `.../senorge/seNorge_2018/Archive/seNorge2018_2025.nc.das` | HTTP 200 | siatka **X=1195, Y=1550**, projekcja UTM zone 33 (`transverse_mercator`), `geospatial_lat 57.8-72.1`, `lon -1.3..32.5`, tytuł "seNorge_2018 version 23.09", CF-1.6, instytucja MET Norway; rozdzielczość komórki 1 km (**wynika z X*Y w ramach UTM33, krok jawnie nie odczytany** - not verified) |
| MEPS `.../catalog/meps25epsfull/catalog.xml` | **HTTP 404** | ta ścieżka katalogu nie istnieje; dokładna ścieżka MEPS - **not verified** |
| Locationforecast `https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=60&lon=10` | HTTP 200 JSON | wymaga identyfikującego `User-Agent` (dokumentacja MET: bez tego 403 - strona License/FAQ to potwierdza tekstem) |

Licencja (`https://api.met.no/doc/License`, HTTP 200, cytat): *"Unless specified otherwise, all data and products are licensed under the Norwegian Licence for Open Government Data (NLOD) 2.0 and Creative Commons 4.0 BY International licences. Credit should be given to The Norwegian Meteorological Institute, shortened MET Norway, as the source of data. Some suggestions: «Data from MET Norway», «Based on data from MET Norway»."*
Plik seNorge (atrybut `license`) wskazuje: `https://www.met.no/en/free-meteorological-data/Licensing-and-crediting`.
Uwaga: Frost API w odpowiedzi podaje CC BY 3.0 NO - niezgodność z NLOD 2.0 / CC BY 4.0 z dokumentacji; zachować najostrożniej: atrybucja "MET Norway" działa dla wszystkich.
Status: **VERIFIED-BY-REQUEST** (THREDDS, api.met.no, Frost=401).

---

## 9. OpenStreetMap

| Pole | Wartość |
|---|---|
| Plik Norwegii | `https://download.geofabrik.de/europe/norway-latest.osm.pbf` (HTTPS **UNREACHABLE** - connection reset po 3 próbach; **HTTP działa**) |
| Działający adres | `http://download.geofabrik.de/europe/norway-latest.osm.pbf` -> HTTP 307 -> `https://download.geofabrik.de/europe/norway-261115.osm.pbf` |
| Rozmiar | `norway-261115.osm.pbf`: **1 379 030 578 B (ok. 1.38 GB)**, last-modified 2026-11-16 02:24:45 GMT (HEAD po HTTP, HTTP 200). (HEAD `https://download.openstreetmap.fr/extracts/europe/norway.osm.pbf` -> HTTP 200, 1 432 721 846 B, last-modified 2026-11-15) |
| MD5 | `f1c88019ebecdf959ac6a55c20568768  norway-latest.osm.pbf` (HTTP 200) |
| Replikacja | `http://download.geofabrik.de/europe/norway-updates/state.txt`: sequenceNumber 4972, timestamp 2026-11-15T21:22:28Z |
| Zawartość | pełne dane OSM Norwegii; wg strony Geofabrik "norway" obejmuje m.in. Svalbard i Jan Mayen (**czy włączone - not verified**; sprawdzić po pobraniu przez bbox) |
| Overpass | `https://overpass-api.de/api/status` **UNREACHABLE** (reset po HTTPS, 503 po HTTP); mirror `https://maps.mail.ru/osm/tools/overpass/api/status` HTTP 200 (nieoficjalny, nie używać produkcyjnie); `overpass.kumi.systems` HTTP 301 (po HTTP) |
| CRS | EPSG:4326 |
| Autoryzacja | Nie |
| Licencja | **ODbL 1.0** (`https://opendatacommons.org/licenses/odbl/1-0/`) + wymóg wspólnej "CC BY-SA" dla dokumentacji kartograficznej. Status: **DOCUMENTATION-ONLY** (nie pobierano tekstu licencji w tej sesji) |
| Wymagana atrybucja | "© OpenStreetMap contributors" + link do `https://www.openstreetmap.org/copyright` |
| Obowiązki ODbL (DOCUMENTATION-ONLY) | atrybucja; **share-alike**: jeśli publikujesz zmodyfikowaną bazę danych (derivative database), musi być na ODbL; "produced work" (np. wyrenderowana mapa/gra) - wystarczy atrybucja; jeśli gra dystrybuuje dane OSM w zmodyfikowanej formie bazodanowej - obowiązek udostępnienia tej bazy. Zalecenie: oddzielić pliki z danymi OSM w repo (osobny zbiór danych/katalog) od kodu gry |
| Status | plik/MD5/state: **VERIFIED-BY-REQUEST (HTTP 200)**; Overpass: **UNREACHABLE** |

---

## 10. Norsk Polarinstitutt - Svalbard i Jan Mayen

| Zbiór | Zawartość | Rozdz./skala | CRS | Format / dostęp | Licencja | Aktualność | Status |
|---|---|---|---|---|---|---|---|
| **Svalbard DTM 5** `010bfb4a-65aa-4d30-aba9-7d090a432df7` | DEM Svalbardu | **5 m** | 25833, 25835 | GeoTIFF, "cellevis" (32 komórki w area codelist), `mapSelectionLayer: dtm-svalbard`; `https://nedlasting.geonorge.no/api/capabilities/010bfb4a-...` HTTP 200 | **CC BY 4.0**, "Åpne data" | DateUpdated 2023-11-08 | **VERIFIED (HTTP 200)** metadane+capabilities |
| **Svalbard DTM 20** `9d118d31-182c-495b-b7be-d819cc7444b1` | DEM | 20 m | 25833 | GeoTIFF, zamówienie dla "Svalbard" (kod 2100) | CC BY 4.0 | 2023-11-08 | VERIFIED |
| **Svalbard DTM 50** `3a83e0a7-113e-4850-8fed-1646838acb02` | DEM | 50 m | 25833 | GeoTIFF | CC BY 4.0 | 2023-11-08 | VERIFIED |
| **Jan Mayen DTM 5** `731a0602-d262-483d-aaa6-474cef68e82a` | DEM Jan Mayen | 5 m | **25829** (UTM 29N) | GeoTIFF, jednostka "Jan Mayen" (kod 2211); bbox -9.08..-7.93 E, 70.83..71.16 N | CC BY 4.0 | 2024-10-29 | VERIFIED |
| **S100 Kartdata** `bd6050e8-7182-459b-9989-66c4ecbae874` | Topografia Svalbardu (wektor) | 1:100 000 | 25833 | SOSI (jedyny format w metadanych!) | CC BY 4.0 | 2023-11-08 | VERIFIED (metadane) |
| S250 / S1000 Kartdata `4bccbc7b-...` / `335e3bc0-...` | j.w. | 1:250 000 / 1:1 000 000 | 25833 | SOSI | CC BY 4.0 | S250: "Må oppdateres" | VERIFIED (metadane) |
| **S0 Stedsnavn (Svalbard)** `46660b69-b4e4-4c1c-a1c5-204b7ed02187` | oficjalne nazwy Svalbardu | - | 25833 | SOSI | CC BY 4.0 | 2023-11-08 | VERIFIED |
| **Nazwy: API Norsk Polarinstitutt** `https://api.npolar.no/placename/?q=Longyearbyen&limit=1&format=json` | rekordy z `title`, `area` (Svalbard / Jan Mayen), `type`, `terrain`, opis, pochodzenie nazwy | - | - | JSON | not verified (dataset NPI; zwykle CC BY 4.0) | na żywo | **HTTP 200** (także `q=Beerenberg` -> area "Jan Mayen") |
| **Mapy bazowe NPI (kafle)** `https://geodata.npolar.no/arcgis/rest/services/Basisdata` | HTTP 200; usługi: `NP_Basiskart_Svalbard_WMTS_25833`, `..._32633`, `..._3857`, `NP_Basiskart_Svalbard_WMS`, `NP_Basiskart_JanMayen_WMTS_25829`, `..._25833`, `..._3857`, `NP_Basiskart_JanMayen_WMS`, `NP_Ortofoto_Svalbard_WMTS_25833`, `NP_Satellitt_*`, `FKB_Svalbard_WMTS_*` | kafle | 25833/32633/3857/25829 | WMTS/WMS (ArcGIS) | metadane katalogu "no restrictions"; nazwa licencji **not verified** | - | WMTS Capabilities Svalbard HTTP 200 (11 267 B), Jan Mayen HTTP 200 (18 956 B) |
| Aplikacje | `https://toposvalbard.npolar.no` (HTTP 200), `https://svalbardkartet.npolar.no`, `https://topojanmayen.npolar.no/` | podgląd | | | | | tylko do podglądu |

Uwaga o układach współrzędnych: Svalbard w EPSG:25833 (UTM 33N) leży ekstremalnie daleko od południka osiowego 15E dla wschodu - NPI stosuje
25833/32633, a dla Jan Mayen **25829 (UTM 29N)**. Gra musi mieć wspólny układ światowy (np. własny azymutalny/ECEF) i konwersje per-region.
Brak API "S0 Terrengmodell" pod taką nazwą: zbiory DEM nazywają się **Svalbard DTM 5/20/50** (zweryfikowano w katalogu).
NHM WCS (sekcja 1.1) **nie obejmuje** Svalbardu ani Jan Mayen (y max 8 000 275 w EPSG:25833).

---

## 11. Copernicus DEM GLO-30 (globalny fallback)

| Pole | Wartość |
|---|---|
| Dostawca | Copernicus / ESA; hosting: AWS Open Data |
| Zbiór | Copernicus DEM GLO-30 Public (DSM - powierzchnia, **zawiera budynki, roślinność**) |
| Bucket | `https://copernicus-dem-30m.s3.amazonaws.com/` (HTTP 200 listing 286 457 B, publiczny, bez autoryzacji); `s3://copernicus-dem-30m` |
| Rozdzielczość | 30 m (1 arcsec); odstęp w długości geograficznej rośnie z szerokością: dla 70-80 N szerokość kafla 1200 px (3x), dla 60-70 N 1800 px (2x) (wg readme) |
| CRS | EPSG:4326 (WGS84) - **not verified w nagłówku GeoTIFF** (readme mówi "tiles 1x1 degree grid") |
| Format | Cloud Optimized GeoTIFF, kafle 1x1 stopień, DEFLATE, przykład `Copernicus_DSM_COG_10_N60_00_E010_00_DEM/Copernicus_DSM_COG_10_N60_00_E010_00_DEM.tif` HTTP 200, 21 547 276 B |
| Indeks | `https://copernicus-dem-30m.s3.amazonaws.com/tileList.txt` (HTTP 200, 1.1 MB) |
| Pokrycie | Norwegia: kafle dla Svalbardu istnieją (np. `N78_00_E010_00` zawiera AUXFILES: ACM, EDM, FLM, HEM); Jan Mayen: kafle `N71_00_W009_00`, `N71_00_W008_00`, `N71_00_W007_00`, `N71_00_W010_00` są na liście (VERIFIED); liczba kafli w tileList dla N70-N81 E: 820. Oceany bez kafli (wartość 0) |
| Wysokości | Wysokości względem EGM2008 (wg ogólnej wiedzy o CDEM; w readme nie czytano) - **not verified** |
| Licencja | Readme w bucketcie **nie zawiera tekstu licencji** (HTTP 404 dla `license.pdf`). Znana licencja Copernicus DEM: "Licence for the use of the Copernicus DEM" - użycie bezpłatne, komercyjne dozwolone, wymagana atrybucja - **DOCUMENTATION-ONLY / not verified w tej sesji** |
| Atrybucja (wg wytycznych Copernicus; not verified) | "Produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved." |
| Status | **VERIFIED-BY-REQUEST (HTTP 200)** dla pliku i indeksu; licencja DOCUMENTATION-ONLY |

Uwaga: GLO-30 to DSM, nie DTM - nie nadaje się do rzeźby terenu pod lasem/budynkami; tylko fallback dla Svalbardu/Jan Mayen, gdy DTM NPI niedostępny
(NPI DTM 5 m jest lepszy, a otwarty).

---

## 12. Batymetria (fiordy, morze)

| Zbiór | Dostawca | Zawartość | Rozdz. | CRS | Dostęp | Licencja | Status |
|---|---|---|---|---|---|---|---|
| **Sjøkart - Dybdedata** `2751aacf-5472-4850-a208-3532a51c529a` | Kartverket (Sjøkartverket) | Wektorowe punkty głębokości, izobaty, linia brzegowa ("kystkontur"), skały; odniesienie **sjøkartnull (EPSG 9672)**; linia brzegowa wg średniego przypływu | gęstość punktów **50 m** (wg abstraktu) | 25832/33/35, 4258 | Geonorge nedlasting (FGDB, GML, PostGIS, SOSI), WMS `https://wms.geonorge.no/skwms1/wms.dybdedata2?service=WMS&request=GetCapabilities` (HTTP 200, 34 204 B), WFS `https://wfs.geonorge.no/skwms1/wfs.dybdedata?service=WFS&request=GetCapabilities` (HTTP 200, 69 158 B) | **CC BY 4.0**. UseLimitations: *"Dataene er ikke godkjent for navigasjon. De er ikke egnet for nøyaktige masseberegninger."* WMS Capabilities: `AccessConstraints: Copyright Statens kartverk 2007`, `Fees: Norge digital` (stare pola, rozbieżne z metadanymi) | DateUpdated 2026-11-10, tygodniowo; zakres bbox 2-33 E, 55-81 N, **w tym Svalbard i Bjørnøya** | **VERIFIED-BY-REQUEST** |
| **Dybdedata - terrengmodeller 5 m** `13b707ad-a379-4bf0-a707-da237d646f44` | Kartverket / MAREANO | Modele dna morskiego 5 m (tylko obszary zmierzone w programie MAREANO: Møre og Romsdal, Trøndelag, Nordland, Troms, Finnmark, Barentshavet) | 5 m | 25833, 4326 | Geonorge nedlasting: ENH, NED, TIFF, XYZ, "cellevis" | CC BY 4.0, UseLimitations: brak | 2026-10-16, status "Må oppdateres" | metadane VERIFIED |
| **EMODnet Bathymetry** `https://ows.emodnet-bathymetry.eu/wcs?service=WCS&request=GetCapabilities&version=2.0.1` | EMODnet | Średnia głębokość DTM Europy (m.in. fiordy, szelf) | ok. 1/16 arcmin (**not verified**; w Capabilities nie odczytano) | **not verified** (zwykle EPSG:4326) | WCS 2.0.1: coverage `emodnet__mean`, `emodnet__mean_2016`, `..._2018`, `..._2020`, `..._2022`, `emodnet__mean_atlas_land`, `..._multicolour`, `..._rainbowcolour`; WMS HTTP 200 (kompresja gzip) | Capabilities: `Fees: NONE`, `AccessConstraints: NONE`; Warunki EMODnet - not verified (zwykle CC BY 4.0) | WCS Capabilities **VERIFIED (HTTP 200, 15 688 B)** |

**Ograniczenia norweskie (ważne):** abstrakt Dybdedata jawnie mówi, że zbiór jest **"ugradert"** (nieobjęty klasyfikacją) i że rozdzielczość punktów (50 m)
jest zgodna z *"graderingsregimet og gjeldende lovverk om skjermingsverdig informasjon"* - tj. gęstsze dane głębokości są objęte reżimem klasyfikacji/ochrony
i nie są publicznie dostępne. **Nie** próbować uzyskać gęstszych danych niż 50 m; dla fiordów używać Dybdedata (50 m + izobaty 2-250 m, krzywe co 1 m tylko w niektórych portach)
lub terrengmodeller 5 m MAREANO (tam, gdzie istnieją). Dane nie są dla żeglugi.
Dokładne przepisy (nazwa ustawy/rozporządzenia) - **not verified**.

---

## 13. Ortofoto - Norge i bilder (TYLKO REFERENCJA)

| Pole | Wartość |
|---|---|
| Dostawca | Norge i bilder (Kartverket, Geovekst, kommuner, Statens vegvesen) |
| Zbiór | "Norge i bilder WMS-Ortofoto" `dcee8bf4-fdf3-4433-a91b-209c7d9b0b0f`, "WMS-Prosjekt", "WMS-Mosaikk" |
| URL | `https://wms.geonorge.no/skwms1/wms.nib?service=WMS&request=GetCapabilities` |
| Wynik sondy | **HTTP 200 z ServiceException: "Bruker kan ikke autentiseres ... tjenesteid: wms.nib ikke godkjent av autorisasjons tjener"** - czyli wymaga autoryzacji/białej listy IP (**auth: TAK**, niedostępne tu) |
| Licencja | **Norge digitalt begrenset - Norge digitalt-lisens** (`https://www.kartverket.no/geodataarbeid/norge-digitalt/partsinformasjon/avtaler-og-vilkar/norge-digitalt-lisens`) |
| Użycie w grze | **Nie używać do tekstur**; tylko jako wizualna referencja ręczna (lokalnie, nie w repo, nie w buildzie). Licencja ogranicza do stron umowy Norge digitalt |
| Status | **VERIFIED-BY-REQUEST (HTTP 200, odmowa autoryzacji)**; licencja z metadanych Geonorge |

Alternatywy otwarte (do tekstur/satelity): NPI `NP_Ortofoto_Svalbard_WMTS_25833`, `NP_Satellitt_Svalbard_WMTS_25833`, `NP_Satellitt_JanMayen_WMTS_25829`
(usługi istnieją, HTTP 200 na liście; licencja kafli - not verified).

---

## 14. Pokrycie terenu - alternatywy

| Zbiór | Dostawca | Rozdz. | Dostęp | Licencja | Status |
|---|---|---|---|---|---|
| **ESA WorldCover 10 m, v200 (2021)** | ESA | 10 m, globalnie, 11 klas, kafle 3x3 stopnie | S3 `https://esa-worldcover.s3.eu-central-1.amazonaws.com/` (HTTP 200, listing); prefiksy `v100/`, `v200/`; przykład `v200/2021/map/ESA_WorldCover_10m_2021_v200_N60E009_Map.tif` HTTP 200, 82 806 697 B; kafle Svalbardu istnieją (`..._N78E009_Map.tif`, `..._N78E012_Map.tif`, `..._N78E015_Map.tif`) | **CC BY 4.0** (DOCUMENTATION-ONLY - w tej sesji nie czytano pliku licencji) | **VERIFIED-BY-REQUEST** |
| **CORINE (Norge, NIBIO)** | NIBIO / EEA | 100 m (CLC), 1:100 000 | patrz sekcja 4 | NLOD 1.0 | metadane VERIFIED |
| CORINE (EEA) | EEA | - | `https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine?f=pjson` HTTP 200 (usługi `Corine/CHA1990_2000_WM`, ...) | Copernicus Land: bezpłatna, atrybucja - **DOCUMENTATION-ONLY** | lista usług VERIFIED |
| **AR50 (NIBIO)** | NIBIO | 1:20 000-1:100 000 | patrz sekcja 4 | NLOD 1.0 | VERIFIED |

---

## Rekomendowane źródło na warstwę świata

| Warstwa | Rekomendacja | Zapas / uwagi |
|---|---|---|
| **Wysokość (kontynent)** | Kartverket **DTM1** kafle 15 km z Atom feed (EPSG:25833, 1 m); WCS 1.0.0 tylko dla łatek <= 2000x2000 px | DOM1 (powierzchnia) do wysokości drzew/budynków; **nie** polegać na historycznym DTM10 (2013) |
| **Linia brzegowa** | N50 Kartdata (`ea192681-...`) warstwy wody/lądu; dopasować do `Dybdedata` (kystkontur MHW) | Svalbard: S100 Kartdata (SOSI); Jan Mayen: NPI Basiskart/Jan Mayen DTM |
| **Jeziora** | NVE Innsjødatabase (`Innsjodatabase2` layer 5; 267 194 obiektów) | N50 wody jako uzupełnienie |
| **Rzeki** | NVE ELVIS (`Elvenett1` layer 2; 1 954 539 odcinków; strahler) | N50 (`Elv`), OSM `waterway` |
| **Pokrycie terenu** | AR50 (NIBIO) lub ESA WorldCover 10 m (jeden spójny raster dla całego kraju + Svalbard) | CORINE 100 m za gruby |
| **Typ lasu / drzewa** | NIBIO SR16 (16 m; gatunek, wysokość, bonitet) przez pliki fylkesvis lub WMS | tylko kontynent |
| **Drogi (mosty, tunele, promy)** | NVDB Les API (Bru=60, Tunnel=581, Ferjesamband=770, Fartsgrense=105) lub plik "NVDB Vegnett Pluss" | OSM `highway` jako uzupełnienie (Svalbard) |
| **Kolej** | Bane NOR Banenettverk (WFS/pliki, NLOD) | OSM `railway` |
| **Budynki** | Matrikkelen Bygningspunkt (CC BY 4.0, punkty + typ) + kontury z N50 (budynki) lub **OSM building** (poligony); **FKB-Bygning niedostępne** (Norge digitalt) | wysokości budynków z DOM1 - DTM1 |
| **Osady** | N50 (tekst/obszary zabudowy) + SSR `Stedsnavn`; Matrikkelen | OSM `place` |
| **Nazwy miejsc** | Stedsnavn (SSR) + API `ws.geonorge.no/stedsnavn/v1`; Svalbard/Jan Mayen: `api.npolar.no/placename` i S0 Stedsnavn | |
| **Klimat** | seNorge_2018 (THREDDS, NetCDF, 1195x1550 w UTM33) | Frost (wymaga client-id) dla stacji; MEPS - ścieżka not verified |
| **Svalbard** | NPI Svalbard DTM 5 (CC BY 4.0, EPSG:25833/25835), S100 Kartdata, S0 Stedsnavn, Dybdedata (batymetria) | Fallback: Copernicus GLO-30 (DSM!) |
| **Jan Mayen** | NPI Jan Mayen DTM 5 (**EPSG:25829**), NPI Basiskart Jan Mayen WMTS, `api.npolar.no/placename` (area Jan Mayen) | Fallback: GLO-30 kafle N71 W010..W007 |
| **Batymetria** | Sjøkart Dybdedata (50 m, CC BY 4.0) + MAREANO 5 m (tam gdzie jest) | EMODnet jako grubszy fallback |

---

## Obowiązki licencyjne - linie atrybucji, które gra musi pokazać

Ogólnie: wszystkie warstwy "Åpne data" Geonorge/NPI/Kartverket są na **CC BY 4.0** (metadane), NVE/NIBIO/Bane NOR na **NLOD 1.0**
(`http://data.norge.no/nlod/no/1.0`; kanał Atom Kartverket DTM1/DOM1 podaje NLOD 2.0 - `https://data.norge.no/nlod/en/2.0`), MET na **NLOD 2.0 i CC BY 4.0**,
OSM na **ODbL**. Brak ograniczeń komercyjnych w żadnej z zweryfikowanych licencji, ale **wymagana atrybucja** i (CC BY/NLOD) wskazanie licencji.
Poniższe teksty są propozycją (nie narzucone przez dostawców dosłownie, o ile nie zaznaczono cytatu).

Ekran "Credits / Dane":

```
Elevation, N50, administrative boundaries, place names, buildings, bathymetry:
  Contains data from Kartverket (Norwegian Mapping Authority), licensed under CC BY 4.0 / NLOD 2.0.
Lakes, rivers, glaciers: Contains data from NVE (Norwegian Water Resources and Energy Directorate), licensed under NLOD.
Land cover, forest resources: Contains data from NIBIO (Norwegian Institute of Bioeconomy Research), licensed under NLOD.
Roads, bridges, tunnels, ferries: Contains data from Statens vegvesen (NVDB), licensed under CC BY 4.0 / NLOD (check API terms).
Railways: Contains data from Bane NOR, licensed under NLOD.
Airports: Contains data from Avinor.
Svalbard and Jan Mayen: Contains data from the Norwegian Polar Institute (Norsk Polarinstitutt), licensed under CC BY 4.0.
Climate: Data from MET Norway, licensed under NLOD 2.0 / CC BY 4.0.
Map data (roads, buildings, POI, where used): (c) OpenStreetMap contributors, licensed under ODbL.
  https://www.openstreetmap.org/copyright
Global elevation fallback (if used): Produced using Copernicus WorldDEM-30 (c) DLR e.V. 2010-2014 and (c) Airbus Defence
  and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved. (not verified wording)
ESA WorldCover (if used): (c) ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium.
  (not verified wording)
```

| Licencja | Co musi zrobić gra |
|---|---|
| **CC BY 4.0** (`https://creativecommons.org/licenses/by/4.0/`) | podać autora/źródło, link do licencji, wskazać zmiany ("modified"), nie sugerować poparcia |
| **NLOD** (`http://data.norge.no/nlod/no/1.0`, `https://data.norge.no/nlod/en/2.0`) | podać źródło (nazwa instytucji), link do licencji, nie sugerować, że dostawca popiera aplikację; dane można modyfikować i używać komercyjnie |
| **ODbL 1.0** (OSM) | atrybucja "© OpenStreetMap contributors"; share-alike dla zmodyfikowanej BAZY (nie dla samej gry/"produced work" - DOCUMENTATION-ONLY, skonsultować prawnika przed wydaniem) |
| **Norge digitalt begrenset** (FKB-*, Havnedata, Norge i bilder) | **NIE używać bez umowy**; nie wchodzą do projektu |
| Copernicus / ESA WorldCover | atrybucja wg wytycznych dostawcy (not verified w tej sesji) |

Uwagi końcowe / otwarte kwestie do ręcznej weryfikacji:
1. Rozbieżność licencji DTM1/DOM1 (Atom: NLOD 2.0 vs metadane: CC BY 4.0) - pokazać obie.
2. Licencja Les API NVDB i szczegóły limitów - not verified.
3. Dokładne przepisy dot. gęstych danych batymetrycznych - not verified.
4. Całkowity rozmiar DTM1 dla Norwegii - not verified (kafel testowy 1.18 GB, 2033 kafli).
5. Overpass i HTTPS Geofabrik są **UNREACHABLE** z tego środowiska (używać HTTP/mirror do testów, w produkcji HTTPS z innej sieci).
