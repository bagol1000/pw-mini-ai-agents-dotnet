"""Generuje raport z zapisanych wyników, bez wywoływania modeli ani API."""
from pathlib import Path
import csv
import html
import re

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
with (ROOT / "results/results.csv").open(encoding="utf-8-sig", newline="") as source:
    rows = list(csv.DictReader(source))


def latest(experiment, model, variant=None, temperature=None):
    matches = [r for r in rows if r["experiment"] == experiment and r["model"] == model
               and (variant is None or r["variant"] == variant)
               and (temperature is None or float(r["temperature"]) == temperature)]
    return matches[-1] if matches else None


def percent(value):
    return f"{float(value) * 100:.0f}%"


def time_s(value):
    return f"{float(value) / 1000:.3f}".replace(".", ",")


def metrics(r):
    if not r:
        return ["brak pomiaru"] * 5
    return [f'{r["valid_json"]}/{r["total"]}', percent(r["floor_accuracy"]),
            percent(r["elevator_accuracy"]), percent(r["exact_match"]), time_s(r["avg_ms"])]


def table(headers, records):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
                     + ["| " + " | ".join(map(str, record)) + " |" for record in records])


def stability(model):
    name = "exp-03-luna.txt" if model == "gpt-6-luna" else "exp-03.txt"
    path = REPORTS / name
    if not path.exists():
        return {}
    data = path.read_bytes()
    text = data.decode("utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")
    result = {}
    for block in text.split("Temperature: ")[1:]:
        temperature = float(block.splitlines()[0].strip().replace(",", "."))
        match = re.search(r"Powtarzalne notatki: (\d+/\d+)", block)
        result[temperature] = match.group(1) if match else "brak logu"
    return result


names = {"gemma3:4b": "Gemma3:4b", "qwen3:4b": "Qwen3:4b", "gpt-6-luna": "GPT-6 Luna"}
headers = ["Model", "Poprawny format", "Piętro", "Winda", "Exact match", "Czas [s]"]
comparison = table(headers, [[name] + metrics(latest("EXP-01", model)) for model, name in names.items()])
prompting = table(["Model", "Wariant"] + headers[1:],
                 [[names[model], variant] + metrics(latest("EXP-02", model, variant))
                  for model in ["gemma3:4b", "gpt-6-luna"]
                  for variant in ["zero-shot", "one-shot", "few-shot"]])
temperature_rows = []
for model in ["gemma3:4b", "gpt-6-luna"]:
    stable = stability(model)
    for temperature in [0, 0.5, 1]:
        r = latest("EXP-03", model, temperature=temperature)
        temperature_rows.append([names[model], str(temperature).replace(".", ",")] + metrics(r)
                                + [stable.get(temperature, "brak logu")])
temperatures = table(["Model", "T"] + headers[1:] + ["Powtarzalne notatki"], temperature_rows)
structured = table(["Model", "Wariant"] + headers[1:],
                   [[names[model], variant] + metrics(latest("EXP-04", model, variant))
                    for model in ["gemma3:4b", "gpt-6-luna"] for variant in ["prompt", "json-schema"]])
coverage = table(["Model", "EXP-01", "EXP-02", "EXP-03", "EXP-04"],
                 [[name] + ["wykonano" if latest(f"EXP-0{i}", model) else "brak wyniku"
                            for i in range(1, 5)] for model, name in names.items()])
total_calls = sum(int(r["total"]) for r in rows)
raw = table(["#", "EXP", "Model", "Wariant", "T", "N", "JSON", "Piętro", "Winda", "Exact", "Czas [s]"],
            [[i, r["experiment"], r["model"], r["variant"], r["temperature"], r["total"],
              r["valid_json"], percent(r["floor_accuracy"]), percent(r["elevator_accuracy"]),
              percent(r["exact_match"]), time_s(r["avg_ms"])] for i, r in enumerate(rows, 1)])

report = f"""# Ekstrakcja piętra i informacji o windzie

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

{coverage}

W CSV zapisano **{len(rows)} serii pomiarowych, łącznie {total_calls} wywołań**. Pięć powtórzeń tej samej notatki w EXP-03 nie zwiększa liczby różnych przypadków testowych.

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

{comparison}

Qwen poprawnie rozpoznał obydwa pola we wszystkich 10 przypadkach i zwrócił odpowiedzi akceptowane przez parser. Luna poprawnie rozpoznała wszystkie piętra, lecz w NOTE-010 podała `elevator = null` zamiast `true`. Gemma zwracała JSON otoczony znacznikami Markdown, co powodowało odrzucanie odpowiedzi.

W tych pomiarach Qwen był około **39,6 razy wolniejszy od Luny** oraz **15,9 razy wolniejszy od Gemmy**. Są to porównania zmierzonych czasów całych wywołań w użytych środowiskach, a nie uniwersalny ranking wydajności modeli.

## 5. EXP-02 — wpływ przykładów w prompcie

Porównano zero-shot, one-shot z pierwszym przykładem („butle są na 1 piętrze”) oraz few-shot ze wszystkimi czterema przykładami. Przykłady w prompcie są inne niż notatki testowe. Temperatura wynosiła 0.

{prompting}

W Gemmie przykłady nie usunęły problemu formatu, przez co walidacja nadal odrzucała wszystkie odpowiedzi. Nie można na tej podstawie rozstrzygnąć wpływu przykładów na samą trafność wyodrębnionych wartości.

Luna osiągnęła 90% exact match w zero-shot i one-shot, a 100% w few-shot. Różnica dotyczyła NOTE-010: zero-shot zwrócił `null`, one-shot `false`, a few-shot poprawne `true`. Żaden z czterech przykładów nie opisywał bezpośrednio awarii windy, dlatego obserwacja wskazuje na wpływ całego kontekstu przykładów, a nie skopiowanie identycznego przypadku.

W tym uruchomieniu wariant few-shot był także najszybszy. Bez powtarzanych serii i danych o tokenach nie można jednak uznać, że dłuższy prompt z zasady skraca czas odpowiedzi. Dla Qwena EXP-02 nie wykonano.

## 6. EXP-03 — temperatura i powtarzalność

Zastosowano prompt zero-shot, temperatury 0, 0,5 i 1 oraz pięć powtórzeń każdej z 10 notatek. Każdy wiersz obejmuje 50 odpowiedzi.

{temperatures}

Gemma uzyskała pozornie idealną powtarzalność 10/10, ponieważ program porównywał komunikaty „Niepoprawny JSON”. Nie jest to dowód identyczności surowych odpowiedzi ani poprawnego rozpoznawania danych.

Luna miała 9/10 powtarzalnych notatek przy każdej temperaturze. Zmieniał się wyłącznie wynik NOTE-010. Przy temperaturze 0 wystąpiły cztery odpowiedzi `false` i jedna `null`; przy 0,5 trzy `false`, jedna `null` i jedna `true`; przy 1 trzy `null`, jedna `false` i jedna `true`. Pozostałe dziewięć notatek było poprawnych we wszystkich próbach.

Wzrost exact match z 90% do 92% oznacza tylko jedną dodatkową poprawną odpowiedź na 50 prób. Nie stanowi podstawy do stwierdzenia, że wyższa temperatura poprawia jakość. Temperatura 0 również nie zapewniła pełnej deterministyczności. Dla ekstrakcji danych punktem wyjścia pozostaje niska temperatura, jasna definicja etykiet i walidacja. Dla Qwena EXP-03 nie wykonano.

## 7. EXP-04 — prompt a JSON Schema

Porównano opis formatu wyłącznie w prompcie z natywnym wymuszaniem schematu; temperatura 0.

{structured}

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

{raw}
"""


def inline(text):
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)


def render_markdown(text):
    lines = text.splitlines()
    output = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith("#"):
            match = re.match(r"^(#{1,6}) (.*)", line)
            level = len(match.group(1))
            output.append(f"<h{level}>{inline(match.group(2))}</h{level}>")
            index += 1
        elif line.startswith("| "):
            block = []
            while index < len(lines) and lines[index].startswith("| "):
                block.append(lines[index])
                index += 1
            def cells(row):
                return [c.strip() for c in row.strip().strip("|").split("|")]
            head = "".join(f"<th>{inline(c)}</th>" for c in cells(block[0]))
            body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells(row)) + "</tr>" for row in block[2:])
            output.append(f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
        elif line.startswith("- "):
            items = []
            while index < len(lines) and lines[index].startswith("- "):
                items.append("<li>" + inline(lines[index][2:]) + "</li>")
                index += 1
            output.append("<ul>" + "".join(items) + "</ul>")
        else:
            paragraph = [line]
            index += 1
            while index < len(lines) and lines[index].strip() and not lines[index].startswith(("#", "| ", "- ")):
                paragraph.append(lines[index])
                index += 1
            output.append("<p>" + inline(" ".join(paragraph)) + "</p>")
    return "\n".join(output)


style = """
:root{color-scheme:light;--ink:#17263b;--muted:#596b80;--accent:#136c79;--line:#dce5ec}
*{box-sizing:border-box}body{margin:0;background:#edf2f6;color:var(--ink);font:15px/1.7 'Segoe UI',Arial,sans-serif}
.toolbar{max-width:1140px;margin:24px auto 12px;display:flex;justify-content:space-between;align-items:center;color:var(--muted);padding:0 16px;font-size:13px}
button{background:var(--accent);color:white;border:0;border-radius:8px;padding:11px 18px;font:inherit;cursor:pointer}
main{max-width:1140px;margin:0 auto 48px;background:white;padding:64px 70px;border:1px solid var(--line);border-radius:16px;box-shadow:0 12px 45px #17263b0a}
.eyebrow{text-transform:uppercase;letter-spacing:2.5px;font-size:12px;font-weight:700;color:var(--accent);margin-bottom:18px}
h1{font-size:43px;line-height:1.15;letter-spacing:-1.5px;margin:0 0 18px;max-width:850px}
h2{font-size:23px;line-height:1.35;letter-spacing:-.4px;margin:42px 0 16px;padding-top:22px;border-top:1px solid var(--line);break-after:avoid}
h1+h2{border:0;padding:0;margin-top:0;color:var(--muted);font-size:20px;font-weight:400}
h3{font-size:17px;margin:28px 0 12px;break-after:avoid}p{margin:12px 0}strong{font-weight:650}code{font:12px/1.5 Consolas,monospace;background:#f0f4f7;padding:2px 5px;border-radius:4px;overflow-wrap:anywhere}
.table-wrap{overflow-x:auto;margin:18px 0 24px;border:1px solid var(--line);border-radius:9px}table{width:100%;border-collapse:collapse;font-size:12px;line-height:1.5;font-variant-numeric:tabular-nums}
th{background:#172f43;color:white;font-weight:600;text-align:left;padding:12px 10px}td{padding:10px;border-bottom:1px solid var(--line);vertical-align:top}tbody tr:nth-child(even){background:#f5f8fa}tbody tr:last-child td{border:0}
ul{padding-left:22px}li{margin:7px 0}footer{margin-top:42px;border-top:1px solid var(--line);padding-top:18px;color:var(--muted);font-size:12px}
@media(max-width:800px){main{padding:28px 20px;border-radius:0}h1{font-size:32px}.toolbar{margin-top:12px}}
@page{size:A4;margin:16mm 12mm}
@media print{body{background:white;font-size:10pt;line-height:1.5}.toolbar{display:none}main{max-width:none;margin:0;padding:0;border:0;border-radius:0;box-shadow:none}h1{font-size:29pt}h2{font-size:16pt;margin-top:24px}h3{font-size:12pt}table{font-size:8pt}th,td{padding:6px}thead{display:table-header-group}tr{break-inside:avoid}.table-wrap{overflow:visible;border-radius:0}code{font-size:8pt}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""
document = f'''<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Laboratorium 03 — porównanie trzech modeli</title><style>{style}</style></head>
<body><div class="toolbar"><span>Raport laboratoryjny · .NET / AI · 22.10.2026</span><button onclick="window.print()">Drukuj / zapisz PDF</button></div>
<main><div class="eyebrow">Modele i prompting / Laboratorium 03</div>{render_markdown(report)}
<footer>Raport wygenerowany z zapisanych pomiarów. Wszystkie czasy dotyczą całych wywołań w badanym środowisku.</footer></main></body></html>'''
(REPORTS / "raport.md").write_text(report, encoding="utf-8")
(REPORTS / "raport.html").write_text(document, encoding="utf-8")
print(f"Wygenerowano raport.md i raport.html: {len(rows)} serii, {total_calls} wywołań.")
