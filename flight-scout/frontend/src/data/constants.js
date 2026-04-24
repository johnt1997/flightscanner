// Statische App-Konstanten – getrennt vom UI-Code für bessere Übersicht.

export const AIRPORTS = {
  vie: { name: 'Wien', cc: 'at', color: '#dc2626' },
  bts: { name: 'Bratislava', cc: 'sk', color: '#2563eb' },
  bud: { name: 'Budapest', cc: 'hu', color: '#16a34a' },
  zur: { name: 'Zürich', cc: 'ch', color: '#f60e5d' },
};

export const COUNTRY_CC = {
  'Italien': 'it', 'Spanien': 'es', 'Vereinigtes Königreich': 'gb', 'Irland': 'ie',
  'Frankreich': 'fr', 'Niederlande': 'nl', 'Belgien': 'be', 'Dänemark': 'dk',
  'Schweden': 'se', 'Lettland': 'lv', 'Litauen': 'lt', 'Norwegen': 'no',
  'Finnland': 'fi', 'Griechenland': 'gr', 'Türkei': 'tr', 'Albanien': 'al',
  'Serbien': 'rs', 'Rumänien': 'ro', 'Bulgarien': 'bg', 'Kroatien': 'hr',
  'Bosnien und Herzegowina': 'ba', 'Montenegro': 'me', 'Nordmazedonien': 'mk',
  'Slowakei': 'sk', 'Slowenien': 'si', 'Tschechische Republik': 'cz',
  'Polen': 'pl', 'Portugal': 'pt', 'Marokko': 'ma', 'Ägypten': 'eg',
  'Island': 'is', 'Georgien': 'ge', 'Malta': 'mt', 'Österreich': 'at', 'Ungarn': 'hu',
  'Deutschland': 'de', 'Schweiz': 'ch', 'Zypern': 'cy',
};

const COUNTRY_SHORT = {
  'Vereinigtes Königreich': 'UK', 'Bosnien und Herzegowina': 'Bosnien',
  'Tschechische Republik': 'Tschechien', 'Nordmazedonien': 'N. Mazedonien',
};
export const shortCountry = (name) => COUNTRY_SHORT[name] || name;

export const WEEKDAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

export const CITY_DB = {
  'Italien': ['Mailand', 'Rom', 'Bologna', 'Venedig', 'Neapel', 'Catania', 'Palermo', 'Bari', 'Pisa', 'Turin', 'Lamezia Terme', 'Trapani'],
  'Spanien': ['Barcelona', 'Madrid', 'Malaga', 'Palma de Mallorca'],
  'Vereinigtes Königreich': ['London', 'Edinburgh', 'Manchester', 'Liverpool', 'Newcastle upon Tyne'],
  'Irland': ['Dublin'],
  'Frankreich': ['Paris'],
  'Niederlande': ['Amsterdam'],
  'Belgien': ['Brüssel'],
  'Dänemark': ['Kopenhagen'],
  'Schweden': ['Stockholm'],
  'Lettland': ['Riga'],
  'Litauen': ['Vilnius'],
  'Norwegen': ['Oslo'],
  'Finnland': ['Helsinki'],
  'Griechenland': ['Athen', 'Thessaloniki'],
  'Türkei': ['Istanbul', 'Antalya'],
  'Albanien': ['Tirana'],
  'Serbien': ['Belgrad'],
  'Rumänien': ['Bukarest'],
  'Bulgarien': ['Sofia'],
  'Kroatien': ['Zagreb', 'Split', 'Dubrovnik'],
  'Bosnien und Herzegowina': ['Sarajevo'],
  'Montenegro': ['Podgorica'],
  'Nordmazedonien': ['Skopje'],
  'Slowakei': ['Košice'],
  'Slowenien': ['Ljubljana'],
  'Tschechische Republik': ['Prag'],
  'Polen': ['Warschau', 'Krakau', 'Danzig', 'Breslau', 'Kattowitz'],
  'Portugal': ['Lissabon'],
  'Marokko': ['Marrakesch'],
  'Ägypten': ['Kairo'],
  'Island': ['Reykjavik'],
  'Georgien': ['Kutaissi'],
  'Malta': ['Malta'],
};

export const ALL_CITIES = Object.entries(CITY_DB).flatMap(([country, cities]) =>
  cities.map(city => ({ city, country }))
);

// Länder die im Blacklist-Picker auftauchen
export const COUNTRIES = [
  'Griechenland', 'Türkei', 'Albanien', 'Montenegro',
  'Serbien', 'Nordmazedonien', 'Bosnien und Herzegowina',
  'Rumänien', 'Vereinigtes Königreich',
  'Irland', 'Niederlande', 'Belgien', 'Dänemark', 'Schweden',
  'Norwegen', 'Marokko', 'Frankreich',
  'Malta', 'Zypern', 'Spanien', 'Portugal',
  'Italien', 'Bulgarien', 'Schweiz', 'Polen', 'Lettland', 'Deutschland',
];

// Preset = vordefinierte Wochentag/Dauer-Kombinationen für die Suche
export const PRESETS = {
  weekend:     { weekday: 4, durations: [2], label: 'Wochenende',  sub: 'Fr → So' },
  longWeekend: { weekday: 4, durations: [3], label: 'Verlängert',  sub: 'Fr → Mo' },
  midweek:     { weekday: 1, durations: [2], label: 'Wochenmitte', sub: 'Di → Do' },
  weekly:      { weekday: 0, durations: [7], label: 'Wochentrip',  sub: 'Mo → Mo' },
};
export const PRESET_KEYS = ['weekend', 'longWeekend', 'midweek', 'weekly'];
