# Ekstrakcja piętra i informacji o windzie

## Raport z laboratorium 03 — modele i prompting

**Modele:** Gemma3:4b · Qwen3:4b · GPT-6 Luna

**Autorzy:** do uzupełnienia · **Grupa:** do uzupełnienia

**Data przygotowania raportu:** 22.10.2026. Daty poszczególnych pomiarów nie są zapisywane w CSV.

## Najważniejsze wyniki

GPT-6 Luna z czterema przykładami w prompcie uzyskała **100% exact match** przy średnim czasie **1,106 s**. Qwen3:4b osiągnął **100% już w zero-shot**, lecz potrzebował średnio **78,243 s**. Gemma3:4b wymagała wymuszenia JSON Schema, aby odpowiedzi przechodziły walidację; w tym wariancie uzyskała **70% exact match**.

Są to wyniki na **10 różnych notatkach testowych**. Nie stanowią dowodu takiej samej skuteczności na rzeczywistych notatkach kierowców. Raport obejmuje wszystkie dostępne pomiary trzech modeli, ale zakres eksperymentów jest nierówny.

## 1. Cel i zasady zadania

Celem było sprawdzenie, jak model językowy wyodrębnia z polskojęzycznej notatki kierowcy piętro docelowe dostawy oraz informację o obecności windy. Model powinien zwracać obiekt JSON z polami `floor` oraz `elevator`.

| Pole | Interpretacja |
| --- | --- |
| `floor` | Liczba całkowita, parter = 0; `null`, gdy piętra nie podano lub jest niejednoznaczne |
| `elevator` | `true`, gdy winda jest; `false`, gdy wyraźnie jej nie ma; `null`, gdy brak informacji |

Numer mieszkania i numer domofonu nie są piętrem. Zdanie „Winda nie działa” potwierdza obecność windy, dlatego oczekiwaną etykietą jest `true`. Zadanie dotyczy obecności, a nie sprawności urządzenia.

## 2. Środowisko i dane

| Parametr | Wartość |
| --- | --- |
| System i powłoka | Windows, PowerShell |
| Platforma | C#, .NET 10; SDK 10.0.402 |
| Procesor komputera lokalnego | Intel Core Ultra 9 185H |
| RAM dostępny systemowi | Około 31,4 GiB |
| Układ graficzny | Intel Arc Graphics; wykorzystanie akceleracji w pomiarach nie było rejestrowane |
| Modele lokalne | `gemma3:4b`, `qwen3:4b`, przez Ollamę |
| Wersja Ollamy podczas pomiarów | Nie została zarejestrowana |
| Model zdalny | `gpt-6-luna`, OpenAI Chat Completions API |
| Konfiguracja Luny | `reasoning_effort = none`; temperatura zgodna z danym eksperymentem |
| Zbiór testowy | `data/examples.csv`: 10 notatek z oczekiwanymi etykietami |
| Przykłady do promptów | `data/prompt-examples.csv`: 4 osobne notatki |
| Dodatkowe dane | `notes.csv` i `labeled-notes.csv` nie były używane w zapisanych eksperymentach |
| Źródło metryk | `results/results.csv` oraz logi w `reports/` |

Modele lokalne i model API pracowały w różnych środowiskach. Czas obejmuje wywołanie HTTP i odbiór wyniku; dla Ollamy może obejmować ładowanie modelu, a dla API także opóźnienia sieciowe i obsługę po stronie dostawcy. Nie rejestrowano tokenów ani kosztów, więc nie porównywano kosztu pieniężnego ani czystej szybkości generowania.

### Zakres wykonanych pomiarów

| Model | EXP-01 | EXP-02 | EXP-03 | EXP-04 |
| --- | --- | --- | --- | --- |
| Gemma3:4b | wykonano | wykonano | wykonano | wykonano |
| Qwen3:4b | wykonano | brak wyniku | brak wyniku | brak wyniku |
| GPT-6 Luna | wykonano | wykonano | wykonano | brak wyniku |

W CSV zapisano **18 serii pomiarowych, łącznie 420 wywołań**. Pięć powtórzeń tej samej notatki w EXP-03 nie zwiększa liczby różnych przypadków testowych.

Dla Gemmy istnieją dwa wyniki EXP-01: 5032 ms oraz 4929 ms. W porównaniu głównym użyto ostatniego wyniku 4929 ms, pochodzącego z uruchomienia zapisanego razem z Qwenem. Obie serie pozostawiono w aneksie. Wyniki Luny pochodzą z osobnego uruchomienia.

## 3. EXP-00 — sposób oceny

| Metryka | Definicja |
| --- | --- |
| Poprawny format | Liczba odpowiedzi zaakceptowanych przez parser: obiekt JSON zawierający oba wymagane pola o właściwych typach |
| Floor accuracy | Liczba poprawnie rozpoznanych pięter / liczba wszystkich odpowiedzi |
| Elevator accuracy | Liczba poprawnych etykiet windy / liczba wszystkich odpowiedzi |
| Exact match | Liczba odpowiedzi z poprawnymi jednocześnie oboma polami / liczba wszystkich odpowiedzi |
| Średni czas | Łączny czas wywołań modelu / liczba wywołań |
| Powtarzalne notatki | Notatki, dla których pięć prób dało jeden identyczny zapis wyniku lub błędu parsowania |

Odpowiedzi odrzucone przez parser liczą się jako błędne we wszystkich metrykach poprawności. Zatem 0% dla Gemmy bez schematu oznacza niespełnienie kontraktu aplikacji; nie oznacza, że wszystkie wartości wewnątrz odpowiedzi były semantycznie błędne. Etykieta `null` jest pełnoprawnym oczekiwanym wynikiem.

## 4. EXP-01 — porównanie trzech modeli

Ten sam zbiór 10 notatek, prompt bez przykładów, temperatura 0, bez wymuszania JSON Schema.

| Model | Poprawny format | Piętro | Winda | Exact match | Czas [s] |
| --- | --- | --- | --- | --- | --- |
| Gemma3:4b | 0/10 | 0% | 0% | 0% | 4,929 |
| Qwen3:4b | 10/10 | 100% | 100% | 100% | 78,243 |
| GPT-6 Luna | 10/10 | 100% | 90% | 90% | 1,975 |

Qwen poprawnie rozpoznał obydwa pola we wszystkich 10 przypadkach i zwrócił odpowiedzi akceptowane przez parser. Luna poprawnie rozpoznała wszystkie piętra, lecz w NOTE-010 podała `elevator = null` zamiast `true`. Gemma zwracała JSON otoczony znacznikami Markdown, co powodowało odrzucanie odpowiedzi.

W tych pomiarach Qwen był około **39,6 razy wolniejszy od Luny** oraz **15,9 razy wolniejszy od Gemmy**. Są to porównania zmierzonych czasów całych wywołań w użytych środowiskach, a nie uniwersalny ranking wydajności modeli.

## 5. EXP-02 — wpływ przykładów w prompcie

Porównano zero-shot, one-shot z pierwszym przykładem („butle są na 1 piętrze”) oraz few-shot ze wszystkimi czterema przykładami. Przykłady w prompcie są inne niż notatki testowe. Temperatura wynosiła 0.

| Model | Wariant | Poprawny format | Piętro | Winda | Exact match | Czas [s] |
| --- | --- | --- | --- | --- | --- | --- |
| Gemma3:4b | zero-shot | 0/10 | 0% | 0% | 0% | 3,923 |
| Gemma3:4b | one-shot | 0/10 | 0% | 0% | 0% | 4,344 |
| Gemma3:4b | few-shot | 0/10 | 0% | 0% | 0% | 5,882 |
| GPT-6 Luna | zero-shot | 10/10 | 100% | 90% | 90% | 1,565 |
| GPT-6 Luna | one-shot | 10/10 | 100% | 90% | 90% | 1,214 |
| GPT-6 Luna | few-shot | 10/10 | 100% | 100% | 100% | 1,106 |

W Gemmie przykłady nie usunęły problemu formatu, przez co walidacja nadal odrzucała wszystkie odpowiedzi. Nie można na tej podstawie rozstrzygnąć wpływu przykładów na samą trafność wyodrębnionych wartości.

Luna osiągnęła 90% exact match w zero-shot i one-shot, a 100% w few-shot. Różnica dotyczyła NOTE-010: zero-shot zwrócił `null`, one-shot `false`, a few-shot poprawne `true`. Żaden z czterech przykładów nie opisywał bezpośrednio awarii windy, dlatego obserwacja wskazuje na wpływ całego kontekstu przykładów, a nie skopiowanie identycznego przypadku.

W tym uruchomieniu wariant few-shot był także najszybszy. Bez powtarzanych serii i danych o tokenach nie można jednak uznać, że dłuższy prompt z zasady skraca czas odpowiedzi. Dla Qwena EXP-02 nie wykonano.

## 6. EXP-03 — temperatura i powtarzalność

Zastosowano prompt zero-shot, temperatury 0, 0,5 i 1 oraz pięć powtórzeń każdej z 10 notatek. Każdy wiersz obejmuje 50 odpowiedzi.

| Model | T | Poprawny format | Piętro | Winda | Exact match | Czas [s] | Powtarzalne notatki |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma3:4b | 0 | 0/50 | 0% | 0% | 0% | 2,585 | 10/10 |
| Gemma3:4b | 0,5 | 0/50 | 0% | 0% | 0% | 2,682 | 10/10 |
| Gemma3:4b | 1 | 0/50 | 0% | 0% | 0% | 2,772 | 10/10 |
| GPT-6 Luna | 0 | 50/50 | 100% | 90% | 90% | 1,305 | 9/10 |
| GPT-6 Luna | 0,5 | 50/50 | 100% | 92% | 92% | 1,137 | 9/10 |
| GPT-6 Luna | 1 | 50/50 | 100% | 92% | 92% | 1,231 | 9/10 |

Gemma uzyskała pozornie idealną powtarzalność 10/10, ponieważ program porównywał komunikaty „Niepoprawny JSON”. Nie jest to dowód identyczności surowych odpowiedzi ani poprawnego rozpoznawania danych.

Luna miała 9/10 powtarzalnych notatek przy każdej temperaturze. Zmieniał się wyłącznie wynik NOTE-010. Przy temperaturze 0 wystąpiły cztery odpowiedzi `false` i jedna `null`; przy 0,5 trzy `false`, jedna `null` i jedna `true`; przy 1 trzy `null`, jedna `false` i jedna `true`. Pozostałe dziewięć notatek było poprawnych we wszystkich próbach.

Wzrost exact match z 90% do 92% oznacza tylko jedną dodatkową poprawną odpowiedź na 50 prób. Nie stanowi podstawy do stwierdzenia, że wyższa temperatura poprawia jakość. Temperatura 0 również nie zapewniła pełnej deterministyczności. Dla ekstrakcji danych punktem wyjścia pozostaje niska temperatura, jasna definicja etykiet i walidacja. Dla Qwena EXP-03 nie wykonano.

## 7. EXP-04 — prompt a JSON Schema

Porównano opis formatu wyłącznie w prompcie z natywnym wymuszaniem schematu; temperatura 0.

| Model | Wariant | Poprawny format | Piętro | Winda | Exact match | Czas [s] |
| --- | --- | --- | --- | --- | --- | --- |
| Gemma3:4b | prompt | 0/10 | 0% | 0% | 0% | 5,002 |
| Gemma3:4b | json-schema | 10/10 | 80% | 80% | 70% | 4,576 |
| GPT-6 Luna | prompt | brak pomiaru | brak pomiaru | brak pomiaru | brak pomiaru | brak pomiaru |
| GPT-6 Luna | json-schema | brak pomiaru | brak pomiaru | brak pomiaru | brak pomiaru | brak pomiaru |

Dla Gemmy schemat zwiększył odsetek odpowiedzi akceptowanych przez parser z 0% do 100%. Nie usunął jednak błędów znaczeniowych: poprawne były 8/10 pięter, 8/10 etykiet windy i 7/10 całych odpowiedzi.

**W dostarczonych plikach brakuje wyników EXP-04 Luny oraz wszystkich pomiarów EXP-04 Qwena.** Nie przypisano im żadnych wartości ani nie uruchamiano dodatkowych zapytań. Wynik few-shot Luny z EXP-02 nie zastępuje pomiaru JSON Schema.

## 8. Analiza najtrudniejszych przypadków

| Notatka | Oczekiwany wynik | Zaobserwowany problem |
| --- | --- | --- |
| NOTE-006: „Mieszkanie 15, domofon 15” | `floor = null`, `elevator = null` | Gemma z JSON Schema podała piętro 15: pomyliła numer mieszkania z piętrem |
| NOTE-009: „Drugie lub trzecie piętro” | `floor = null`, `elevator = null` | Gemma z JSON Schema podała `elevator = false`, mimo braku informacji o windzie |
| NOTE-010: „Winda nie działa, dostawa na 5p” | `floor = 5`, `elevator = true` | Gemma z JSON Schema podała `floor = null`, `elevator = false`; Luna bez kilku przykładów myliła obecność ze sprawnością windy |

W NOTE-010 błędy dotyczą interpretacji domenowej: awaria urządzenia potwierdza jego istnienie. Kolejnym eksperymentem mogłoby być dopisanie tej reguły wprost do promptu i sprawdzenie jej na nowych notatkach, zamiast dalszego dopasowywania rozwiązania wyłącznie do znanych 10 przykładów.

## 9. Rekomendacja i ograniczenia

Na podstawie dostępnych pomiarów najbardziej obiecującym wariantem do dalszych prac jest **GPT-6 Luna, few-shot, temperatura 0**, który osiągnął 10/10 poprawnych odpowiedzi przy średnim czasie 1,106 s. Wariant ten wymaga potwierdzenia na większym, niezależnym zbiorze. Połączenie few-shot z JSON Schema jest propozycją do sprawdzenia, a nie przetestowanym wynikiem tego raportu.

Jeżeli wymagane jest przetwarzanie lokalne, Qwen3:4b jest lepszym punktem wyjścia niż Gemma w badanej konfiguracji: osiągnął 100% exact match bez przykładów, ale z wysokim opóźnieniem. Trzeba jeszcze zbadać rozgrzany model, wpływ konfiguracji wykonania i pozostałe eksperymenty.

Ograniczenia badania:

- Tylko 10 różnych notatek; pojedynczy błąd zmienia wynik serii dziesięciu prób o 10 punktów procentowych.
- Zbiór był wielokrotnie oglądany; brak niezależnego zbioru końcowego i oszacowania niepewności.
- Nierówny zakres badań trzech modeli, w szczególności brak EXP-02–04 Qwena oraz EXP-04 Luny.
- Brak ujednoliconej rozgrzewki, pomiaru tokenów, kosztów, rozrzutu czasów i rejestracji użycia GPU.
- Powtarzalność błędów parsera w Gemmie nie mierzy powtarzalności treści odpowiedzi.
- Wczesne logi Gemmy mają uszkodzone polskie znaki na wyjściu konsoli; w analizie użyto oryginalnych treści z danych i identyfikatorów notatek. Nie ma dowodu, że problem dotyczył wejścia modelu.

## 10. Odtwarzalność i źródła

Wyniki pochodzą wyłącznie z lokalnych plików; podczas przygotowania raportu nie wykonywano nowych wywołań modeli. Tabele są generowane z CSV, a powtarzalność odczytywana z logów. Do tabel eksperymentów wybierany jest ostatni zapis dla danej konfiguracji.

- `../results/results.csv` — metryki wszystkich zapisanych serii.
- `exp-01-powtorka.txt`, `exp-01-luna.txt` — porównanie modeli.
- `exp-02.txt`, `exp-02-luna.txt` — warianty promptów i odpowiedzi.
- `exp-03.txt`, `exp-03-luna.txt` — powtórzenia oraz stabilność.
- `exp-04.txt` — porównanie formatu Gemmy.
- `../data/examples.csv`, `../data/prompt-examples.csv` — dane i etykiety.
- `../src/ModelLab/Extraction.cs`, `Metrics.cs`, `OllamaClient.cs` oraz `../src/Experiments/` — implementacja.

Plik `generate_report.py` odtwarza Markdown i HTML bez połączeń z API. Po dopisaniu kolejnych pomiarów należy zaktualizować także opisowe wnioski i zakres badania; sam skrypt automatycznie przelicza tabele, ale tekst analizy dokumentuje obecny stan eksperymentów.

## Aneks — wszystkie zapisane serie

| # | EXP | Model | Wariant | T | N | JSON | Piętro | Winda | Exact | Czas [s] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | EXP-01 | gemma3:4b | zero-shot | 0 | 10 | 0 | 0% | 0% | 0% | 5,032 |
| 2 | EXP-02 | gemma3:4b | zero-shot | 0 | 10 | 0 | 0% | 0% | 0% | 3,923 |
| 3 | EXP-02 | gemma3:4b | one-shot | 0 | 10 | 0 | 0% | 0% | 0% | 4,344 |
| 4 | EXP-02 | gemma3:4b | few-shot | 0 | 10 | 0 | 0% | 0% | 0% | 5,882 |
| 5 | EXP-03 | gemma3:4b | x5 | 0 | 50 | 0 | 0% | 0% | 0% | 2,585 |
| 6 | EXP-03 | gemma3:4b | x5 | 0.5 | 50 | 0 | 0% | 0% | 0% | 2,682 |
| 7 | EXP-03 | gemma3:4b | x5 | 1 | 50 | 0 | 0% | 0% | 0% | 2,772 |
| 8 | EXP-04 | gemma3:4b | prompt | 0 | 10 | 0 | 0% | 0% | 0% | 5,002 |
| 9 | EXP-04 | gemma3:4b | json-schema | 0 | 10 | 10 | 80% | 80% | 70% | 4,576 |
| 10 | EXP-01 | gemma3:4b | zero-shot | 0 | 10 | 0 | 0% | 0% | 0% | 4,929 |
| 11 | EXP-01 | qwen3:4b | zero-shot | 0 | 10 | 10 | 100% | 100% | 100% | 78,243 |
| 12 | EXP-01 | gpt-6-luna | zero-shot | 0 | 10 | 10 | 100% | 90% | 90% | 1,975 |
| 13 | EXP-02 | gpt-6-luna | zero-shot | 0 | 10 | 10 | 100% | 90% | 90% | 1,565 |
| 14 | EXP-02 | gpt-6-luna | one-shot | 0 | 10 | 10 | 100% | 90% | 90% | 1,214 |
| 15 | EXP-02 | gpt-6-luna | few-shot | 0 | 10 | 10 | 100% | 100% | 100% | 1,106 |
| 16 | EXP-03 | gpt-6-luna | x5 | 0 | 50 | 50 | 100% | 90% | 90% | 1,305 |
| 17 | EXP-03 | gpt-6-luna | x5 | 0.5 | 50 | 50 | 100% | 92% | 92% | 1,137 |
| 18 | EXP-03 | gpt-6-luna | x5 | 1 | 50 | 50 | 100% | 92% | 92% | 1,231 |
