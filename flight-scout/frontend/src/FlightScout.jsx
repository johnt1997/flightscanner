import { useState, useEffect, useMemo } from 'react';
import HeatmapView from './HeatmapView';
import CalendarView from './CalendarView';
const API_URL = '';

const AIRPORTS = {
  vie: { name: 'Wien', emoji: '🇦🇹', color: '#dc2626' },
  bts: { name: 'Bratislava', emoji: '🇸🇰', color: '#2563eb' },
  bud: { name: 'Budapest', emoji: 'BD', color: '#16a34a' },
};

const WEEKDAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

const CITY_DB = {
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

const ALL_CITIES = Object.entries(CITY_DB).flatMap(([country, cities]) =>
  cities.map(city => ({ city, country }))
);

const COUNTRIES = [
  'Griechenland', 'Türkei', 'Albanien', 'Montenegro',
  'Serbien', 'Nordmazedonien', 'Bosnien und Herzegowina',
  'Rumänien', 'Vereinigtes Königreich',
  'Irland', 'Niederlande', 'Belgien', 'Dänemark', 'Schweden',
  'Norwegen', 'Marokko', 'Frankreich',
  'Malta', 'Zypern', 'Spanien', 'Portugal',
  'Italien', 'Bulgarien', 'Schweiz', 'Polen', 'Lettland', 'Deutschland'
];

export default function FlightScout() {
  // Theme
  const [theme, setTheme] = useState(() => localStorage.getItem('flight_scout_theme') || 'dark');

  // Form State
  const [selectedAirports, setSelectedAirports] = useState(['vie']);
  const [startDate, setStartDate] = useState(() => {
    const now = new Date();
    const daysToFri = (5 - now.getDay() + 7) % 7 || 7;
    const nextFri = new Date(now.getTime() + daysToFri * 86400000);
    return nextFri.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => {
    const now = new Date();
    const last = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    return last.toISOString().split('T')[0];
  });
  const [startWeekday, setStartWeekday] = useState(4);
  const [durations, setDurations] = useState([2]);
  const [adults, setAdults] = useState(1);
  const [maxPrice, setMaxPrice] = useState(70);
  const [minDepartureHour, setMinDepartureHour] = useState(14);
  const [maxReturnHour, setMaxReturnHour] = useState(23);
  const [blacklistCountries, setBlacklistCountries] = useState([]);
  const [searchMode, setSearchMode] = useState('everywhere'); // 'everywhere' | 'cities'
  const [selectedCities, setSelectedCities] = useState([]);
  const [cityFilter, setCityFilter] = useState('');
  const [activeTab, setActiveTab] = useState('search');

  // Job State
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  // UI State
  const [showCountryPicker, setShowCountryPicker] = useState(false);
  const [expandedCity, setExpandedCity] = useState(null);
  const [expandedAlts, setExpandedAlts] = useState(new Set());

  // Favorites (localStorage)
  const [favorites, setFavorites] = useState(() => {
    const saved = localStorage.getItem('flight_scout_favorites');
    return saved ? JSON.parse(saved) : [];
  });

  // Auth State
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('flight_scout_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState('login');
  const [authUsername, setAuthUsername] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState('');

  // Archive State
  const [savedDeals, setSavedDeals] = useState([]);
  const [savingDealIndex, setSavingDealIndex] = useState(null);

  // Alert State
  const [alerts, setAlerts] = useState([]);
  const [alertCity, setAlertCity] = useState('');
  const [alertMaxPrice, setAlertMaxPrice] = useState(50);
  const [alertChatId, setAlertChatId] = useState('');

  // Share toast
  const [showShareToast, setShowShareToast] = useState(false);

  // New deal toast queue
  const [dealToasts, setDealToasts] = useState([]);
  const [seenCities, setSeenCities] = useState(new Set());

  // Theme colors
  const t = theme === 'dark' ? {
    bg: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
    text: '#f8fafc',
    textMuted: '#94a3b8',
    textDim: '#64748b',
    glass: 'rgba(255, 255, 255, 0.03)',
    glassBorder: 'rgba(255, 255, 255, 0.08)',
    inputBg: 'rgba(255, 255, 255, 0.05)',
    inputBorder: 'rgba(255, 255, 255, 0.1)',
    cardBg: 'rgba(255, 255, 255, 0.02)',
    cardBorder: 'rgba(255, 255, 255, 0.06)',
    cardHover: 'rgba(255, 255, 255, 0.05)',
    modalBg: '#1e293b',
    pickerBg: 'rgba(0, 0, 0, 0.2)',
    chipBg: 'rgba(255, 255, 255, 0.05)',
  } : {
    bg: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #f8fafc 100%)',
    text: '#0f172a',
    textMuted: '#475569',
    textDim: '#94a3b8',
    glass: 'rgba(255, 255, 255, 0.7)',
    glassBorder: 'rgba(0, 0, 0, 0.08)',
    inputBg: 'rgba(255, 255, 255, 0.8)',
    inputBorder: 'rgba(0, 0, 0, 0.12)',
    cardBg: 'rgba(255, 255, 255, 0.6)',
    cardBorder: 'rgba(0, 0, 0, 0.06)',
    cardHover: 'rgba(255, 255, 255, 0.9)',
    modalBg: '#ffffff',
    pickerBg: 'rgba(0, 0, 0, 0.04)',
    chipBg: 'rgba(0, 0, 0, 0.04)',
  };

  const COUNTRY_FACTS = {
    'Italien': ['Italien hat 58 UNESCO-Welterbestätten - mehr als jedes andere Land!', 'In Italien gibt es über 350 Pasta-Sorten!', 'Die Universität Bologna ist die älteste der Welt (1088).'],
    'Spanien': ['Spanien hat die drittmeisten UNESCO-Welterbestätten weltweit!', 'La Tomatina: jährlich werden 150.000 Tomaten geworfen!', 'Spanien produziert 44% des weltweiten Olivenöls.'],
    'Griechenland': ['Griechenland hat über 6.000 Inseln!', 'Die griechische Sprache wird seit 3.400 Jahren geschrieben.', 'Griechenland hat mehr archäologische Museen als jedes andere Land.'],
    'Türkei': ['Istanbul liegt auf zwei Kontinenten gleichzeitig!', 'Der Weihnachtsmann (Nikolaus) stammt aus der heutigen Türkei.', 'Die Türkei hat über 80.000 Moscheen.'],
    'Frankreich': ['Frankreich ist das meistbesuchte Land der Welt!', 'In Frankreich gibt es über 400 Käsesorten.', 'Der Eiffelturm wächst im Sommer um 15cm.'],
    'Kroatien': ['Kings Landing aus Game of Thrones wurde in Dubrovnik gedreht!', 'Kroatien hat über 1.200 Inseln.', 'Die Krawatte wurde in Kroatien erfunden!'],
    'Portugal': ['Portugal ist das älteste Land Europas mit gleichen Grenzen seit 1139!', 'Lissabon ist älter als Rom.', 'Portugal hat 850km Küste.'],
    'Vereinigtes Königreich': ['London hat über 170 Museen!', 'Big Ben ist eigentlich der Name der Glocke, nicht des Turms.', 'Die Briten trinken täglich 165 Mio. Tassen Tee.'],
    'Irland': ['Irland hat keine Schlangen!', 'Die irische Harfe ist das einzige Musikinstrument als Nationalsymbol.', 'Halloween stammt aus Irland.'],
    'Niederlande': ['Die Niederlande haben mehr Fahrräder als Einwohner!', 'Amsterdam steht auf 11 Mio. Holzpfählen.', 'Orangen heißen auf Niederländisch "sinaasappel" (Chinas Apfel).'],
    'Albanien': ['Albanien hat mehr Bunker als McDonalds - über 170.000!', 'Die albanische Flagge ist die einzige mit einem doppelköpfigen Adler.', 'Albanien hat einige der letzten wilden Strände Europas.'],
    'Montenegro': ['Montenegros Bucht von Kotor ist der südlichste Fjord Europas!', 'Das Land hat nur 620.000 Einwohner.', 'Der Name bedeutet "Schwarzer Berg".'],
    'Serbien': ['Belgrad ist eine der ältesten Städte Europas!', 'Serbien ist der größte Himbeer-Exporteur der Welt.', 'Nikola Tesla wurde in Serbien geboren.'],
    'Bulgarien': ['Bulgarien ist das älteste Land Europas, das seinen Namen nie geändert hat!', 'Joghurt heißt dort "kiselo mlyako".', 'In Bulgarien nickt man für Nein und schüttelt für Ja.'],
    'Rumänien': ['Rumäniens Parlamentspalast ist das zweitgrößte Gebäude der Welt!', 'Transsilvanien ist die Heimat von Dracula.', 'Rumänien hat das schnellste Internet Europas.'],
    'Marokko': ['Marokkos Uni in Fès ist die älteste noch bestehende der Welt!', 'Marokko hat sowohl Atlantik- als auch Mittelmeerküste.', 'Tagine ist gleichzeitig das Gericht und der Kochtopf.'],
    'Ungarn': ['Budapest hat das größte Thermalbad Europas!', 'Der Rubik-Würfel wurde in Ungarn erfunden.', 'Ungarn hat über 1.000 Thermalquellen.'],
    'Tschechien': ['Prag hat mehr als 100 Kirchtürme!', 'Tschechien hat den höchsten Bierkonsum pro Kopf weltweit.', 'Das Wort "Roboter" kommt aus dem Tschechischen.'],
    'Polen': ['Polen hat 17 UNESCO-Welterbestätten!', 'Krakaus Marktplatz ist der größte mittelalterliche Platz Europas.', 'Marie Curie wurde in Warschau geboren.'],
    'Dänemark': ['Dänemark hat über 7.000 km Küste!', 'LEGO wurde in Dänemark erfunden.', 'Kopenhagen wurde 5x zur lebenswertesten Stadt gewählt.'],
    'Schweden': ['In Schweden gibt es ein Eishotel, das jedes Jahr neu gebaut wird!', 'Schweden hat über 200.000 Inseln.', 'IKEA, Spotify und Minecraft kommen aus Schweden.'],
    'Norwegen': ['Norwegens Küste ist 25.000 km lang - mit allen Fjorden!', 'Im Sommer geht die Sonne im Norden nie unter.', 'Norwegen hat den längsten Straßentunnel der Welt (24,5km).'],
    'Island': ['Island hat keine Armee!', 'Das Althing ist das älteste Parlament der Welt (930 n.Chr.).', 'In Island gibt es mehr Schafe als Menschen.'],
    'Ägypten': ['Die Pyramiden von Gizeh sind das letzte erhaltene Weltwunder der Antike!', 'Der Nil ist 6.650 km lang.', 'Kleopatra lebte zeitlich näher am iPhone als am Pyramidenbau.'],
    'Malta': ['Malta hat die ältesten freistehenden Gebäude der Welt!', 'Malta ist kleiner als München.', 'Maltesisch ist die einzige semitische Sprache mit lateinischer Schrift.'],
    'Zypern': ['Zypern hat 340 Sonnentage im Jahr!', 'Aphrodite soll an Zyperns Küste geboren worden sein.', 'Halloumi-Käse kommt aus Zypern.'],
    'Bosnien und Herzegowina': ['Sarajevo war die erste Stadt Europas mit einer Straßenbahn!', 'Bosnien hat die letzte Urwald-Region Europas.', 'Der Balkan-Kaffee in Bosnien ist UNESCO Kulturerbe.'],
    'Nordmazedonien': ['Ohrid-See ist einer der ältesten Seen der Welt!', 'Mutter Teresa wurde in Skopje geboren.', 'Das Land hat über 50 natürliche Seen.'],
    'Slowenien': ['Über 60% Sloweniens ist mit Wald bedeckt!', 'Ljubljana wurde 2016 zur grünsten Hauptstadt Europas gewählt.', 'Slowenien hat nur 46km Küste.'],
    'Belgien': ['Belgien produziert 220.000 Tonnen Schokolade pro Jahr!', 'Pommes Frites wurden in Belgien erfunden, nicht in Frankreich.', 'Brüssel hat die meisten Diplomaten pro km² weltweit.'],
    'Finnland': ['Finnland hat über 180.000 Seen!', 'Finnen haben mehr Saunen als Autos.', 'Finnland ist das glücklichste Land der Welt (UN-Ranking).'],
  };

  const getCountryFact = (country) => {
    const facts = COUNTRY_FACTS[country];
    if (!facts) return null;
    return facts[Math.floor(Math.random() * facts.length)];
  };

  // Persist theme
  useEffect(() => { localStorage.setItem('flight_scout_theme', theme); }, [theme]);
  useEffect(() => { localStorage.setItem('flight_scout_favorites', JSON.stringify(favorites)); }, [favorites]);

  // Smart sync: startDate -> endDate (same month end), startWeekday, duration
  useEffect(() => {
    if (!startDate) return;
    const d = new Date(startDate + 'T00:00:00');
    if (isNaN(d.getTime())) return;

    // Sync weekday: JS getDay() = 0=Sun, convert to 0=Mon
    const jsDay = d.getDay();
    const weekday = jsDay === 0 ? 6 : jsDay - 1; // 0=Mo, 1=Di, ..., 6=So
    setStartWeekday(weekday);

    // Sync endDate to end of same month
    const lastDay = new Date(d.getFullYear(), d.getMonth() + 1, 0);
    const endStr = lastDay.toISOString().split('T')[0];
    setEndDate(endStr);

    // Sync duration: distance to Sunday (typical weekend return)
    // Mo=0->So=6 nights, Di=1->5, Mi=2->4, Do=3->3, Fr=4->2, Sa=5->1, So=6->7(skip)
    const nightsToSunday = weekday <= 5 ? (6 - weekday) : 1;
    setDurations([nightsToSunday]);
  }, [startDate]);
  useEffect(() => {
    if (user) localStorage.setItem('flight_scout_user', JSON.stringify(user));
    else localStorage.removeItem('flight_scout_user');
  }, [user]);

  useEffect(() => {
    if (user && activeTab === 'archive') { loadSavedDeals(); loadAlerts(); }
  }, [user, activeTab]);

  const authHeaders = () => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${user?.token}`,
  });

  // --- Auth ---
  const handleAuth = async () => {
    setAuthError('');
    const endpoint = authMode === 'login' ? '/login' : '/register';
    try {
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: authUsername, password: authPassword }),
      });
      const data = await res.json();
      if (!res.ok) { setAuthError(data.detail || 'Fehler'); return; }
      setUser({ username: data.username, token: data.token });
      setShowAuth(false);
      setAuthUsername('');
      setAuthPassword('');
    } catch (e) { setAuthError('Verbindung fehlgeschlagen'); }
  };

  const logout = () => { setUser(null); setSavedDeals([]); setAlerts([]); };

  // --- Saved Deals ---
  const loadSavedDeals = async () => {
    try {
      const res = await fetch(`${API_URL}/deals`, { headers: authHeaders() });
      const data = await res.json();
      if (res.ok) setSavedDeals(data.deals || []);
    } catch (e) { console.error('Load deals error:', e); }
  };

  const saveDeal = async (deal, key) => {
    if (!user) { setShowAuth(true); return; }
    setSavingDealIndex(key);
    try {
      await fetch(`${API_URL}/deals/save`, { method: 'POST', headers: authHeaders(), body: JSON.stringify(deal) });
      setTimeout(() => setSavingDealIndex(null), 1000);
    } catch (e) { console.error('Save deal error:', e); setSavingDealIndex(null); }
  };

  const deleteSavedDeal = async (dealId) => {
    try {
      await fetch(`${API_URL}/deals/${dealId}`, { method: 'DELETE', headers: authHeaders() });
      setSavedDeals(prev => prev.filter(d => d.id !== dealId));
    } catch (e) { console.error('Delete deal error:', e); }
  };

  // --- Alerts ---
  const loadAlerts = async () => {
    try {
      const res = await fetch(`${API_URL}/alerts`, { headers: authHeaders() });
      const data = await res.json();
      if (res.ok) setAlerts(data.alerts || []);
    } catch (e) { console.error('Load alerts error:', e); }
  };

  const createAlert = async () => {
    if (!alertCity || !alertChatId) return;
    try {
      await fetch(`${API_URL}/alerts`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ destination_city: alertCity, max_price: alertMaxPrice, telegram_chat_id: alertChatId }),
      });
      setAlertCity('');
      loadAlerts();
    } catch (e) { console.error('Create alert error:', e); }
  };

  const deleteAlert = async (alertId) => {
    try {
      await fetch(`${API_URL}/alerts/${alertId}`, { method: 'DELETE', headers: authHeaders() });
      setAlerts(prev => prev.filter(a => a.id !== alertId));
    } catch (e) { console.error('Delete alert error:', e); }
  };

  // --- Favorites ---
  const toggleFavorite = (city) => {
    setFavorites(prev => prev.includes(city) ? prev.filter(c => c !== city) : [...prev, city]);
  };

  // --- Share ---
  const shareDeal = (deal) => {
    const text = [
      `✈️ Flight Scout Deal`,
      `━━━━━━━━━━━━━━━━`,
      `🏙  ${deal.city}, ${deal.country}`,
      `💰 ${deal.price.toFixed(0)}€ pro Person`,
      `📅 ${formatDate(deal.departure_date)} – ${formatDate(deal.return_date)}`,
      deal.flight_time && deal.flight_time !== '??:??' ? `🕐 Hin ${deal.flight_time}${deal.return_flight_time && deal.return_flight_time !== '??:??' ? ` / Rück ${deal.return_flight_time}` : ''}` : '',
      `🛫 Ab ${deal.origin}`,
      deal.early_departure ? `☀️ Frühflug` : '',
      deal.is_direct ? `⚡ Direktflug` : '',
      `━━━━━━━━━━━━━━━━`,
      deal.url,
    ].filter(Boolean).join('\n');

    navigator.clipboard.writeText(text).then(() => {
      setShowShareToast(true);
      setTimeout(() => setShowShareToast(false), 2000);
    });
  };

  // --- Grouped Results ---
  const groupedResults = useMemo(() => {
    if (!results.length) return [];
    const groups = {};
    results.forEach(deal => {
      const key = deal.city;
      if (!groups[key]) {
        groups[key] = {
          city: deal.city,
          country: deal.country,
          cheapest: deal.price,
          deals: [],
          isFavorite: favorites.includes(deal.city),
        };
      }
      groups[key].deals.push(deal);
      if (deal.price < groups[key].cheapest) groups[key].cheapest = deal.price;
    });

    const arr = Object.values(groups);
    // Sort: favorites first, then by cheapest price
    arr.sort((a, b) => {
      if (a.isFavorite && !b.isFavorite) return -1;
      if (!a.isFavorite && b.isFavorite) return 1;
      return a.cheapest - b.cheapest;
    });
    // Sort deals within each group by price
    arr.forEach(g => g.deals.sort((a, b) => a.price - b.price));
    return arr;
  }, [results, favorites]);

  // Poll for job status with live streaming
  useEffect(() => {
    if (!jobId || jobStatus?.status === 'completed' || jobStatus?.status === 'failed' || jobStatus?.status === 'cancelled') return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/status/${jobId}`);
        const data = await res.json();
        setJobStatus(data);

        // Live-update results during search
        if (data.status === 'running' && data.partial_results?.length) {
          setResults(data.partial_results);
        }

        // New deal toast
        if (data.new_deals?.length) {
          const newCities = new Set();
          data.new_deals.forEach(d => {
            if (!seenCities.has(d.city)) {
              newCities.add(d.city);
            }
          });

          if (newCities.size > 0) {
            setSeenCities(prev => {
              const updated = new Set(prev);
              newCities.forEach(c => updated.add(c));
              return updated;
            });

            // Show toast for each new city
            newCities.forEach(city => {
              const deal = data.new_deals.find(d => d.city === city);
              if (deal) {
                const fact = getCountryFact(deal.country);
                const toastId = Date.now() + Math.random();
                setDealToasts(prev => [...prev, { id: toastId, city: deal.city, country: deal.country, price: deal.price, fact }]);
                setTimeout(() => setDealToasts(prev => prev.filter(t => t.id !== toastId)), 5000);
              }
            });
          }
        }

        if (data.status === 'completed' || data.status === 'cancelled') {
          setResults(data.results || []);
          setIsSearching(false);
        } else if (data.status === 'failed') {
          setIsSearching(false);
        }
      } catch (e) { console.error('Status poll error:', e); }
    }, 1500);
    return () => clearInterval(interval);
  }, [jobId, jobStatus?.status, seenCities]);

  const toggleAirport = (code) => {
    setSelectedAirports(prev => prev.includes(code) ? prev.filter(a => a !== code) : [...prev, code]);
  };

  const toggleCountry = (country) => {
    setBlacklistCountries(prev => prev.includes(country) ? prev.filter(c => c !== country) : [...prev, country]);
  };

  const toggleCity = (city) => {
    setSelectedCities(prev => prev.includes(city) ? prev.filter(c => c !== city) : [...prev, city]);
  };

  const selectCountryCities = (country) => {
    const countryCities = CITY_DB[country] || [];
    const allSelected = countryCities.every(c => selectedCities.includes(c));
    if (allSelected) {
      setSelectedCities(prev => prev.filter(c => !countryCities.includes(c)));
    } else {
      setSelectedCities(prev => [...new Set([...prev, ...countryCities])]);
    }
  };

  const toggleDuration = (dur) => {
    setDurations(prev => {
      if (prev.includes(dur)) {
        if (prev.length === 1) return prev; // must keep at least one
        return prev.filter(d => d !== dur);
      }
      return [...prev, dur].sort((a, b) => a - b);
    });
  };

  const stopSearch = async () => {
    if (!jobId) return;
    try {
      await fetch(`${API_URL}/stop/${jobId}`, { method: 'POST' });
    } catch (e) { console.error('Stop error:', e); }
  };

  const startSearch = async () => {
    if (selectedAirports.length === 0) { alert('Bitte mindestens einen Flughafen auswählen!'); return; }
    if (searchMode === 'cities' && selectedCities.length === 0) { alert('Bitte mindestens eine Stadt auswählen!'); return; }
    setIsSearching(true);
    setResults([]);
    setJobStatus(null);
    setExpandedCity(null);
    setSeenCities(new Set());
    setDealToasts([]);
    try {
      const res = await fetch(`${API_URL}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          airports: selectedAirports, start_date: startDate, end_date: endDate,
          start_weekday: startWeekday, durations, adults, max_price: maxPrice,
          min_departure_hour: minDepartureHour, max_return_hour: maxReturnHour,
          blacklist_countries: blacklistCountries,
          search_mode: searchMode,
          selected_cities: searchMode === 'cities' ? selectedCities : [],
        }),
      });
      const data = await res.json();
      setJobId(data.job_id);
      setJobStatus(data);
    } catch (e) {
      console.error('Search error:', e);
      setIsSearching(false);
      alert('Verbindung zum Backend fehlgeschlagen!');
    }
  };

  const downloadPdf = () => { if (jobId) window.open(`${API_URL}/download/${jobId}`, '_blank'); };

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('de-AT', { day: '2-digit', month: '2-digit' });
  };

  const formatDateFull = (dateStr) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('de-AT', { weekday: 'short', day: '2-digit', month: '2-digit' });
  };

  function getPriceColor(price) {
    if (price < 30) return '#22c55e';
    if (price < 50) return '#84cc16';
    if (price < 70) return '#eab308';
    return '#f97316';
  }

  return (
    <div style={{ minHeight: '100vh', background: t.bg, fontFamily: "'Outfit', sans-serif", color: t.text, padding: '2rem', transition: 'all 0.3s ease' }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');
        * { box-sizing: border-box; }
        html, body { overflow-x: hidden; }
        .glass { background: ${t.glass}; backdrop-filter: blur(20px); border: 1px solid ${t.glassBorder}; border-radius: 24px; }
        .btn-primary { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); border: none; padding: 1rem 2rem; border-radius: 16px; color: white; font-weight: 600; font-size: 1.1rem; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 24px rgba(99, 102, 241, 0.4); }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(99, 102, 241, 0.5); }
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .chip { padding: 0.75rem 1.25rem; border-radius: 12px; cursor: pointer; transition: all 0.2s ease; border: 2px solid transparent; font-weight: 500; background: ${t.chipBg}; color: ${t.text}; }
        .chip:hover { transform: scale(1.02); }
        .chip.selected { border-color: #6366f1; box-shadow: 0 0 20px rgba(99, 102, 241, 0.3); }
        .input-field { background: ${t.inputBg}; border: 1px solid ${t.inputBorder}; border-radius: 12px; padding: 0.875rem 1rem; color: ${t.text}; font-size: 1rem; width: 100%; transition: all 0.2s ease; }
        .input-field:focus { outline: none; border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2); }
        .result-card { background: ${t.cardBg}; border: 1px solid ${t.cardBorder}; border-radius: 16px; padding: 1.25rem; transition: all 0.3s ease; }
        .result-card:hover { background: ${t.cardHover}; border-color: rgba(99, 102, 241, 0.3); }
        .price-tag { font-family: 'Space Mono', monospace; font-size: 1.5rem; font-weight: 700; color: #22c55e; }
        .progress-bar { height: 6px; background: ${t.inputBg}; border-radius: 3px; overflow: hidden; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #6366f1, #8b5cf6); border-radius: 3px; transition: width 0.5s ease; }
        .glow-text { text-shadow: 0 0 40px rgba(99, 102, 241, 0.5); }
        .country-chip { padding: 0.5rem 0.875rem; border-radius: 8px; font-size: 0.875rem; cursor: pointer; background: ${t.chipBg}; border: 1px solid ${t.inputBorder}; transition: all 0.2s ease; color: ${t.text}; }
        .country-chip.selected { background: rgba(99, 102, 241, 0.2); border-color: #6366f1; }
        .country-chip:hover { background: ${t.cardHover}; }
        .weekday-btn { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-weight: 600; font-size: 0.875rem; background: ${t.chipBg}; border: 2px solid transparent; transition: all 0.2s ease; color: ${t.text}; }
        .weekday-btn:hover { background: ${t.cardHover}; }
        .weekday-btn.start { background: #6366f1; border-color: #6366f1; color: white; }
        .weekday-btn.in-range { background: rgba(99, 102, 241, 0.3); }
        .weekday-btn.end { background: #8b5cf6; border-color: #8b5cf6; color: white; }
        .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; }
        .modal-content { background: ${t.modalBg}; border: 1px solid ${t.glassBorder}; border-radius: 24px; padding: 2rem; width: 400px; max-width: 90vw; color: ${t.text}; }
        .save-btn, .share-btn { background: none; border: 1px solid ${t.inputBorder}; border-radius: 8px; padding: 0.4rem 0.6rem; cursor: pointer; color: ${t.textMuted}; transition: all 0.2s ease; font-size: 1rem; }
        .save-btn:hover, .share-btn:hover { background: rgba(99, 102, 241, 0.2); border-color: #6366f1; color: #6366f1; }
        .save-btn.saved { color: #6366f1; border-color: #6366f1; }
        .delete-btn { background: none; border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 0.4rem 0.6rem; cursor: pointer; color: #ef4444; transition: all 0.2s ease; font-size: 0.875rem; }
        .delete-btn:hover { background: rgba(239, 68, 68, 0.15); }
        .tab-btn { padding: 0.75rem 1.25rem; border-radius: 12px; cursor: pointer; transition: all 0.2s ease; border: none; font-weight: 500; font-size: 1rem; color: ${t.text}; }
        .dur-chip { padding: 0.5rem 0.875rem; border-radius: 10px; cursor: pointer; font-weight: 600; font-size: 0.875rem; border: 2px solid transparent; transition: all 0.2s ease; background: ${t.chipBg}; color: ${t.text}; }
        .dur-chip.selected { background: rgba(99, 102, 241, 0.2); border-color: #6366f1; }
        .city-group { border-radius: 20px; overflow: hidden; transition: all 0.3s ease; }
        .city-header { display: grid; grid-template-columns: auto 1fr auto auto; align-items: center; padding: 1rem 1.25rem; cursor: pointer; transition: all 0.2s ease; gap: 0 0.75rem; }
        .city-header:hover { background: ${t.cardHover}; }
        .fav-star { cursor: pointer; font-size: 1.2rem; transition: all 0.2s ease; padding: 0.25rem; }
        .fav-star:hover { transform: scale(1.3); }
        .deal-row { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 1.25rem; border-top: 1px solid ${t.cardBorder}; transition: all 0.2s ease; gap: 0.5rem; }
        .deal-row:hover { background: ${t.cardHover}; }
        .toast { position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%); background: #22c55e; color: white; padding: 0.75rem 1.5rem; border-radius: 12px; font-weight: 600; z-index: 9999; animation: fadeInUp 0.3s ease; }
        @keyframes fadeInUp { from { opacity: 0; transform: translateX(-50%) translateY(10px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }
        @keyframes dealSlideIn { from { opacity: 0; transform: translateX(120%); } to { opacity: 1; transform: translateX(0); } }
        @keyframes dealSlideOut { from { opacity: 1; transform: translateX(0); } to { opacity: 0; transform: translateX(120%); } }
        .deal-toast { animation: dealSlideIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1); }
        .deal-toast.exiting { animation: dealSlideOut 0.4s ease-in forwards; }
        @keyframes progressPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        .progress-fill { animation: progressPulse 2s ease-in-out infinite; }
        .date-pill { padding: 0.35rem 0.7rem; border-radius: 8px; font-size: 0.8rem; font-weight: 500; cursor: pointer; transition: all 0.15s ease; white-space: nowrap; }
        .date-pill:hover { transform: scale(1.05); }
        .save-btn, .share-btn { flex-shrink: 0; min-width: 36px; min-height: 36px; display: inline-flex; align-items: center; justify-content: center; }
        @media (max-width: 640px) {
          .header-controls { position: static !important; justify-content: center !important; margin-top: 0.75rem; flex-wrap: wrap; }
          .header-title { font-size: 2rem !important; }
          .header-subtitle { font-size: 0.95rem !important; }
          .main-container { padding: 0.75rem !important; }
          .deal-row { padding: 0.6rem 0.75rem !important; }
          .city-header { padding: 0.75rem 0.75rem !important; }
          .btn-primary { padding: 0.75rem 1.25rem !important; font-size: 1rem !important; }
          .tab-btn { padding: 0.5rem 0.875rem !important; font-size: 0.875rem !important; }
          .date-pill { font-size: 0.7rem !important; padding: 0.25rem 0.5rem !important; }
        }
      `}</style>

      <div className="main-container" style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem', position: 'relative' }}>
          <h1 className="glow-text header-title" style={{ fontSize: '3.5rem', fontWeight: 700, margin: 0, letterSpacing: '-0.02em' }}>Flight Scout</h1>
          <p className="header-subtitle" style={{ fontSize: '1.25rem', color: t.textMuted, marginTop: '0.5rem' }}>Finde die günstigsten Wochenend-Flüge</p>
          <div className="header-controls" style={{ position: 'absolute', right: 0, top: 0, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button onClick={() => setTheme(th => th === 'dark' ? 'light' : 'dark')} style={{ background: t.chipBg, border: `1px solid ${t.inputBorder}`, borderRadius: '8px', padding: '0.4rem 0.6rem', cursor: 'pointer', color: t.textMuted, fontSize: '1rem' }} title={theme === 'dark' ? 'Light Mode' : 'Dark Mode'}>
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
            {user ? (
              <>
                <span style={{ color: t.textMuted, fontSize: '0.875rem' }}>{user.username}</span>
                <button onClick={logout} style={{ background: t.chipBg, border: `1px solid ${t.inputBorder}`, borderRadius: '8px', padding: '0.4rem 0.75rem', color: t.textMuted, cursor: 'pointer', fontSize: '0.875rem' }}>Abmelden</button>
              </>
            ) : (
              <button onClick={() => setShowAuth(true)} style={{ background: 'rgba(99,102,241,0.2)', border: '1px solid rgba(99,102,241,0.4)', borderRadius: '8px', padding: '0.4rem 0.75rem', color: '#a5b4fc', cursor: 'pointer', fontSize: '0.875rem' }}>Anmelden</button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
          {[['search', 'Suche'], ['heatmap', 'Heatmap'], ['calendar', 'Kalender'], ['archive', 'Archiv']].map(([key, label]) => (
            <button key={key} onClick={() => { if (key === 'archive' && !user) { setShowAuth(true); return; } setActiveTab(key); }}
              className="tab-btn" style={{ background: activeTab === key ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : t.chipBg, color: activeTab === key ? 'white' : t.text }}>
              {label}
            </button>
          ))}
        </div>

        {/* === SEARCH TAB === */}
        {activeTab === 'search' && (
          <>
          <div className="glass" style={{ padding: '2rem', marginBottom: '2rem' }}>
            {/* Airports */}
            <div style={{ marginBottom: '2rem' }}>
              <label style={{ display: 'block', marginBottom: '0.75rem', fontWeight: 600, color: t.textMuted }}>Abflughäfen</label>
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                {Object.entries(AIRPORTS).map(([code, airport]) => (
                  <div key={code} className={`chip ${selectedAirports.includes(code) ? 'selected' : ''}`}
                    style={{ background: selectedAirports.includes(code) ? `${airport.color}22` : t.chipBg }}
                    onClick={() => toggleAirport(code)}>
                    <span style={{ marginRight: '0.5rem' }}>{airport.emoji}</span>
                    {airport.name}
                    <span style={{ marginLeft: '0.5rem', opacity: 0.6, fontFamily: 'Space Mono, monospace', fontSize: '0.875rem' }}>{code.toUpperCase()}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Search Mode Toggle */}
            <div style={{ marginBottom: '2rem' }}>
              <label style={{ display: 'block', marginBottom: '0.75rem', fontWeight: 600, color: t.textMuted }}>Suchmodus</label>
              <div style={{ display: 'flex', gap: '0', borderRadius: '14px', overflow: 'hidden', border: `1px solid ${t.inputBorder}`, width: 'fit-content' }}>
                <button onClick={() => setSearchMode('everywhere')}
                  style={{
                    padding: '0.75rem 1.5rem', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: '0.95rem',
                    background: searchMode === 'everywhere' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : t.chipBg,
                    color: searchMode === 'everywhere' ? 'white' : t.text, transition: 'all 0.2s ease',
                  }}>
                  Überall
                </button>
                <button onClick={() => setSearchMode('cities')}
                  style={{
                    padding: '0.75rem 1.5rem', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: '0.95rem',
                    borderLeft: `1px solid ${t.inputBorder}`,
                    background: searchMode === 'cities' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : t.chipBg,
                    color: searchMode === 'cities' ? 'white' : t.text, transition: 'all 0.2s ease',
                  }}>
                  Gezielte Städte
                  {searchMode === 'cities' && selectedCities.length > 0 && (
                    <span style={{ marginLeft: '0.5rem', background: 'rgba(255,255,255,0.25)', padding: '0.15rem 0.5rem', borderRadius: '6px', fontSize: '0.8rem' }}>
                      {selectedCities.length}
                    </span>
                  )}
                </button>
              </div>
              <p style={{ fontSize: '0.85rem', color: t.textDim, margin: '0.5rem 0 0 0' }}>
                {searchMode === 'everywhere'
                  ? 'Durchsucht alle Destinationen weltweit nach günstigen Deals'
                  : 'Sucht gezielt nach bestimmten Städten – schneller & exakter'}
              </p>
            </div>

            {/* City Picker (nur im City-Modus) */}
            {searchMode === 'cities' && (
              <div style={{ marginBottom: '2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <label style={{ fontWeight: 600, color: t.textMuted }}>
                    Städte auswählen
                    {selectedCities.length > 0 && (
                      <span style={{ marginLeft: '0.5rem', background: '#6366f1', padding: '0.25rem 0.5rem', borderRadius: '6px', fontSize: '0.75rem', color: 'white' }}>
                        {selectedCities.length} ausgewählt
                      </span>
                    )}
                  </label>
                  {selectedCities.length > 0 && (
                    <button onClick={() => setSelectedCities([])}
                      style={{ background: 'none', border: `1px solid ${t.inputBorder}`, borderRadius: '8px', padding: '0.3rem 0.6rem', color: t.textMuted, cursor: 'pointer', fontSize: '0.8rem' }}>
                      Alle abwählen
                    </button>
                  )}
                </div>

                {/* Search filter */}
                <input
                  type="text" value={cityFilter} onChange={(e) => setCityFilter(e.target.value)}
                  placeholder="Stadt suchen..." className="input-field"
                  style={{ marginBottom: '0.75rem', maxWidth: '300px' }}
                />

                {/* Selected cities pills */}
                {selectedCities.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.75rem' }}>
                    {selectedCities.map(city => (
                      <span key={city} onClick={() => toggleCity(city)}
                        style={{ padding: '0.35rem 0.75rem', borderRadius: '20px', fontSize: '0.8rem', fontWeight: 600,
                          background: 'rgba(99, 102, 241, 0.2)', border: '1px solid rgba(99, 102, 241, 0.4)',
                          color: '#a5b4fc', cursor: 'pointer', transition: 'all 0.15s ease' }}>
                        {city} ×
                      </span>
                    ))}
                  </div>
                )}

                {/* Cities grouped by country */}
                <div style={{ background: t.pickerBg, borderRadius: '12px', padding: '1rem', maxHeight: '350px', overflowY: 'auto' }}>
                  {Object.entries(CITY_DB)
                    .filter(([country, cities]) => {
                      if (!cityFilter) return true;
                      const f = cityFilter.toLowerCase();
                      return country.toLowerCase().includes(f) || cities.some(c => c.toLowerCase().includes(f));
                    })
                    .map(([country, cities]) => {
                      const filteredCities = cityFilter
                        ? cities.filter(c => c.toLowerCase().includes(cityFilter.toLowerCase()) || country.toLowerCase().includes(cityFilter.toLowerCase()))
                        : cities;
                      if (filteredCities.length === 0) return null;
                      const allSelected = filteredCities.every(c => selectedCities.includes(c));
                      return (
                        <div key={country} style={{ marginBottom: '0.75rem' }}>
                          <div onClick={() => selectCountryCities(country)}
                            style={{ fontSize: '0.8rem', fontWeight: 700, color: allSelected ? '#6366f1' : t.textMuted, marginBottom: '0.35rem', cursor: 'pointer', transition: 'color 0.2s' }}>
                            {country}
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                            {filteredCities.map(city => (
                              <div key={city} className={`country-chip ${selectedCities.includes(city) ? 'selected' : ''}`}
                                onClick={() => toggleCity(city)}
                                style={{ fontSize: '0.8rem', padding: '0.35rem 0.7rem' }}>
                                {city}
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
            )}

            {/* Date Range + Persons */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: t.textMuted }}>Von</label>
                <input type="date" value={startDate} min={new Date().toISOString().split('T')[0]} onChange={(e) => setStartDate(e.target.value)} className="input-field" />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: t.textMuted }}>Bis</label>
                <input type="date" value={endDate} min={startDate || new Date().toISOString().split('T')[0]} onChange={(e) => setEndDate(e.target.value)} className="input-field" />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: t.textMuted }}>Personen</label>
                <input type="number" min="1" max="9" value={adults} onChange={(e) => setAdults(parseInt(e.target.value) || 1)} className="input-field" />
              </div>
            </div>

            {/* Weekday Selector */}
            <div style={{ marginBottom: '2rem' }}>
              <label style={{ display: 'block', marginBottom: '0.75rem', fontWeight: 600, color: t.textMuted }}>
                Starttag: {WEEKDAYS[startWeekday]} {durations.length === 1 && <span style={{ fontWeight: 400, color: t.textDim }}>→ {WEEKDAYS[(startWeekday + durations[0]) % 7]}</span>}
              </label>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                {WEEKDAYS.map((day, i) => (
                  <div key={day} className={`weekday-btn ${i === startWeekday ? 'start' : ''}`}
                    onClick={() => {
                      setStartWeekday(i);
                      const nightsToSunday = i <= 5 ? (6 - i) : 1;
                      setDurations([nightsToSunday]);
                    }}>{day}</div>
                ))}
              </div>
            </div>

            {/* Duration Multi-Select */}
            <div style={{ marginBottom: '2rem' }}>
              <label style={{ display: 'block', marginBottom: '0.75rem', fontWeight: 600, color: t.textMuted }}>
                Reisedauer (Nächte) – mehrere auswählbar
              </label>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {[1, 2, 3, 4, 5, 6, 7].map(n => (
                  <div key={n} className={`dur-chip ${durations.includes(n) ? 'selected' : ''}`}
                    onClick={() => toggleDuration(n)}>
                    {n} {n === 1 ? 'Nacht' : 'Nächte'}
                  </div>
                ))}
              </div>
            </div>

            {/* Price & Time */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: t.textMuted }}>Max. Preis pro Person</label>
                <div style={{ position: 'relative' }}>
                  <input type="number" min="20" max="500" value={maxPrice} onChange={(e) => setMaxPrice(parseInt(e.target.value) || 70)} className="input-field" style={{ paddingRight: '3rem' }} />
                  <span style={{ position: 'absolute', right: '1rem', top: '50%', transform: 'translateY(-50%)', color: t.textDim, fontFamily: 'Space Mono, monospace' }}>€</span>
                </div>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: t.textMuted }}>Frühester Hinflug</label>
                <div style={{ position: 'relative' }}>
                  <input type="number" min="0" max="23" value={minDepartureHour} onChange={(e) => setMinDepartureHour(parseInt(e.target.value) || 0)} className="input-field" style={{ paddingRight: '4rem' }} />
                  <span style={{ position: 'absolute', right: '1rem', top: '50%', transform: 'translateY(-50%)', color: t.textDim }}>:00 Uhr</span>
                </div>
              </div>
            </div>

            {/* Blacklist (nur bei Everywhere-Modus) */}
            {searchMode === 'everywhere' && (
            <div style={{ marginBottom: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', cursor: 'pointer' }} onClick={() => setShowCountryPicker(!showCountryPicker)}>
                <label style={{ fontWeight: 600, color: t.textMuted }}>
                  Länder-Blacklist
                  {blacklistCountries.length > 0 && (
                    <span style={{ marginLeft: '0.5rem', background: '#6366f1', padding: '0.25rem 0.5rem', borderRadius: '6px', fontSize: '0.75rem', color: 'white' }}>
                      {blacklistCountries.length} ausgeschlossen
                    </span>
                  )}
                </label>
                <span style={{ color: t.textDim }}>{showCountryPicker ? '▲' : '▼'}</span>
              </div>
              {showCountryPicker && (
                <div style={{ background: t.pickerBg, borderRadius: '12px', padding: '1rem' }}>
                  <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                    <button onClick={() => setBlacklistCountries([...COUNTRIES])}
                      style={{ background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: '8px', padding: '0.35rem 0.75rem', color: '#818cf8', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>
                      Alle auswählen
                    </button>
                    <button onClick={() => setBlacklistCountries([])}
                      style={{ background: t.chipBg, border: `1px solid ${t.inputBorder}`, borderRadius: '8px', padding: '0.35rem 0.75rem', color: t.textMuted, cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>
                      Alle abwählen
                    </button>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {COUNTRIES.map(country => (
                      <div key={country} className={`country-chip ${blacklistCountries.includes(country) ? 'selected' : ''}`} onClick={() => toggleCountry(country)}>{country}</div>
                    ))}
                  </div>
                </div>
              )}
              {blacklistCountries.length === 0 && (
                <p style={{ fontSize: '0.875rem', color: t.textDim, margin: 0 }}>Keine Länder ausgeschlossen – alle werden durchsucht</p>
              )}
            </div>
            )}

            {/* Search Button */}
            <button className="btn-primary" onClick={startSearch} disabled={isSearching || selectedAirports.length === 0 || (searchMode === 'cities' && selectedCities.length === 0)} style={{ width: '100%' }}>
              {isSearching ? 'Suche läuft...' : searchMode === 'cities' ? `${selectedCities.length} Städte suchen` : 'Flüge suchen'}
            </button>
          </div>

          {/* Progress */}
          {isSearching && jobStatus && (
            <div className="glass" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ marginBottom: '0.5rem' }}>
                    <div style={{ fontSize: '0.95rem', lineHeight: 1.4, marginBottom: '0.25rem' }}>{jobStatus.message}</div>
                    <div style={{ fontFamily: 'Space Mono, monospace', fontWeight: 700, fontSize: '0.85rem', color: t.textMuted }}>{jobStatus.progress}%</div>
                  </div>
                  <div className="progress-bar"><div className="progress-fill" style={{ width: `${jobStatus.progress}%` }} /></div>
                  {(jobStatus.destinations_found > 0 || jobStatus.deals_found > 0) && (
                    <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.75rem', fontSize: '0.9rem' }}>
                      <span style={{ color: '#6366f1', fontWeight: 600 }}>{jobStatus.destinations_found} Ziele</span>
                      <span style={{ color: '#22c55e', fontWeight: 600 }}>{jobStatus.deals_found} Deals</span>
                    </div>
                  )}
                </div>
                <button onClick={stopSearch}
                  style={{ marginLeft: '1.5rem', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', borderRadius: '12px', padding: '0.75rem 1.25rem', color: '#ef4444', cursor: 'pointer', fontWeight: 600, fontSize: '0.9rem', transition: 'all 0.2s ease', whiteSpace: 'nowrap' }}
                  onMouseOver={e => e.target.style.background = 'rgba(239, 68, 68, 0.25)'}
                  onMouseOut={e => e.target.style.background = 'rgba(239, 68, 68, 0.15)'}>
                  Stopp
                </button>
              </div>
            </div>
          )}

          {/* === GROUPED RESULTS === */}
          {groupedResults.length > 0 && (
            <div className="glass" style={{ padding: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ margin: 0, fontSize: '1.5rem' }}>
                  {groupedResults.length} Ziele, {results.length} Deals
                  {isSearching && <span style={{ fontSize: '0.9rem', color: t.textMuted, fontWeight: 400, marginLeft: '0.75rem' }}>live...</span>}
                </h2>
                {!isSearching && (
                  <button onClick={downloadPdf} style={{ background: t.chipBg, border: `1px solid ${t.inputBorder}`, padding: '0.75rem 1.25rem', borderRadius: '12px', color: t.text, cursor: 'pointer', fontWeight: 500 }}>
                    PDF Download
                  </button>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {groupedResults.map((group) => {
                  const isExpanded = expandedCity === group.city;
                  return (
                    <div key={group.city} className="city-group" style={{ background: t.cardBg, border: `1px solid ${group.isFavorite ? 'rgba(234, 179, 8, 0.3)' : t.cardBorder}`, borderRadius: '20px' }}>
                      {/* City Header */}
                      <div className="city-header" onClick={() => setExpandedCity(isExpanded ? null : group.city)}>
                        {/* Spalte 1: Stern */}
                        <span className="fav-star" onClick={(e) => { e.stopPropagation(); toggleFavorite(group.city); }}>
                          {group.isFavorite ? '⭐' : '☆'}
                        </span>
                        {/* Spalte 2: Stadt + Date Pills (nimmt allen freien Platz) */}
                        <div style={{ overflow: 'hidden' }}>
                          <div style={{ fontWeight: 700, fontSize: 'clamp(0.95rem, 3.5vw, 1.15rem)', lineHeight: 1.3 }}>
                            {group.city}{' '}
                            <span style={{ opacity: 0.5, fontWeight: 400, fontSize: '0.85em' }}>{group.country}</span>
                          </div>
                          <div style={{ display: 'flex', gap: '0.3rem', marginTop: '0.35rem', flexWrap: 'wrap' }}>
                            {group.deals.slice(0, 6).map((deal, i) => (
                              <span key={i} className="date-pill" style={{ background: `${getPriceColor(deal.price)}22`, color: getPriceColor(deal.price), border: `1px solid ${deal.early_departure ? '#f59e0b' : getPriceColor(deal.price)}44` }}>
                                {deal.early_departure && '☀ '}{formatDate(deal.departure_date)} {deal.price.toFixed(0)}€
                              </span>
                            ))}
                            {group.deals.length > 6 && (
                              <span className="date-pill" style={{ background: t.chipBg, color: t.textMuted }}>+{group.deals.length - 6}</span>
                            )}
                          </div>
                        </div>
                        {/* Spalte 3: Preis */}
                        <div style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                          <div style={{ fontFamily: 'Space Mono, monospace', fontWeight: 700, fontSize: 'clamp(1.1rem, 4vw, 1.4rem)', color: getPriceColor(group.cheapest) }}>
                            {group.cheapest.toFixed(0)}€
                          </div>
                          <div style={{ fontSize: '0.7rem', color: t.textDim }}>{group.deals.length} {group.deals.length === 1 ? 'Termin' : 'Termine'}</div>
                        </div>
                        {/* Spalte 4: Arrow */}
                        <span style={{ color: t.textDim, fontSize: '1rem', transition: 'transform 0.2s', transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }}>▼</span>
                      </div>

                      {/* Expanded Deals */}
                      {isExpanded && (
                        <div>
                          {group.deals.map((deal, i) => {
                            const altKey = `${group.city}-${i}`;
                            const alts = deal.alternatives || [];
                            const altsOpen = expandedAlts.has(altKey);
                            return (
                              <div key={i}>
                                <div className="deal-row">
                                  <a href={deal.url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: 'inherit', flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    <span style={{ fontFamily: 'Space Mono, monospace', fontSize: '0.85rem', fontWeight: 600, color: getPriceColor(deal.price), minWidth: '42px' }}>
                                      {deal.price.toFixed(0)}€
                                    </span>
                                    <span style={{ color: t.textMuted, fontSize: '0.85rem', whiteSpace: 'nowrap' }}>
                                      {formatDateFull(deal.departure_date)} – {formatDateFull(deal.return_date)}
                                    </span>
                                    {deal.flight_time && deal.flight_time !== '??:??' && (
                                      <span style={{ color: deal.early_departure ? '#f59e0b' : t.textDim, fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                                        {deal.early_departure && '☀ '}{deal.flight_time}
                                        {deal.return_flight_time && deal.return_flight_time !== '??:??' && ` / ${deal.return_flight_time}`}
                                      </span>
                                    )}
                                    <span style={{ color: t.textDim, fontSize: '0.8rem' }}>ab {deal.origin}</span>
                                    {deal.early_departure && <span style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b', padding: '0.1rem 0.4rem', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 600 }}>Früh</span>}
                                    {deal.is_direct && <span style={{ background: 'rgba(34,197,94,0.15)', color: '#22c55e', padding: '0.1rem 0.4rem', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 600 }}>Direkt</span>}
                                  </a>
                                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexShrink: 0 }}>
                                    {alts.length > 0 && (
                                      <span onClick={() => setExpandedAlts(prev => {
                                          const next = new Set(prev);
                                          next.has(altKey) ? next.delete(altKey) : next.add(altKey);
                                          return next;
                                        })}
                                        style={{ fontSize: '0.75rem', color: '#6366f1', cursor: 'pointer', whiteSpace: 'nowrap', padding: '0.25rem 0.5rem', borderRadius: '6px', background: 'rgba(99,102,241,0.1)', transition: 'all 0.15s ease' }}>
                                        {altsOpen ? '▾' : '▸'} +{alts.length}
                                      </span>
                                    )}
                                    <button className="share-btn" onClick={() => shareDeal(deal)} title="Teilen">↗</button>
                                    <button className={`save-btn ${savingDealIndex === altKey ? 'saved' : ''}`}
                                      onClick={() => saveDeal(deal, altKey)} title="Speichern">
                                      {savingDealIndex === altKey ? '✓' : '♡'}
                                    </button>
                                  </div>
                                </div>
                                {/* Alternativen */}
                                {altsOpen && alts.map((alt, j) => (
                                  <div key={j} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.5rem 1.5rem 0.5rem 3.5rem', borderTop: `1px dashed ${t.cardBorder}`, fontSize: '0.85rem', color: t.textMuted }}>
                                    <span style={{ fontFamily: 'Space Mono, monospace', fontWeight: 600, color: getPriceColor(alt.price), minWidth: '50px' }}>
                                      {alt.price.toFixed(0)}€
                                    </span>
                                    <span>
                                      {alt.early_departure && '☀ '}{alt.time}{alt.return_time && ` / ${alt.return_time}`}
                                    </span>
                                    {alt.return_arrival && (
                                      <span style={{ color: t.textDim, fontSize: '0.8rem' }}>
                                        Ank. {alt.return_arrival}
                                      </span>
                                    )}
                                  </div>
                                ))}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Empty State */}
          {jobStatus?.status === 'completed' && results.length === 0 && (
            <div className="glass" style={{ padding: '3rem', textAlign: 'center' }}>
              <h3 style={{ margin: 0, marginBottom: '0.5rem' }}>Keine Deals gefunden</h3>
              <p style={{ color: t.textMuted, margin: 0 }}>Versuche einen höheren Maximalpreis oder frühere Abflugzeiten</p>
            </div>
          )}
          </>
        )}

        {/* === HEATMAP TAB === */}
        {activeTab === 'heatmap' && <HeatmapView results={results} />}

        {/* === CALENDAR TAB === */}
        <div style={{ display: activeTab === 'calendar' ? 'block' : 'none' }}>
          <CalendarView airports={selectedAirports} maxPrice={maxPrice} duration={durations[0] || 2} adults={adults} blacklistCountries={blacklistCountries} />
        </div>

        {/* === ARCHIVE TAB === */}
        {activeTab === 'archive' && user && (
          <div>
            <div className="glass" style={{ padding: '2rem', marginBottom: '2rem' }}>
              <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.5rem' }}>Gespeicherte Deals</h2>
              {savedDeals.length === 0 ? (
                <p style={{ color: t.textMuted }}>Noch keine Deals gespeichert. Suche Flüge und klicke auf das Herz-Symbol.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {savedDeals.map((deal) => (
                    <div key={deal.id} className="result-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <a href={deal.url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: 'inherit', flex: 1 }}>
                        <div style={{ fontWeight: 600 }}>{deal.city} <span style={{ opacity: 0.5, fontWeight: 400 }}>{deal.country}</span></div>
                        <div style={{ fontSize: '0.875rem', color: t.textMuted }}>{deal.departure_date && formatDate(deal.departure_date)} – {deal.return_date && formatDate(deal.return_date)} <span style={{ opacity: 0.6 }}>ab {deal.origin}</span></div>
                      </a>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <span className="price-tag" style={{ fontSize: '1.25rem' }}>{deal.price.toFixed(0)}€</span>
                        <button className="delete-btn" onClick={() => deleteSavedDeal(deal.id)}>Löschen</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="glass" style={{ padding: '2rem' }}>
              <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.5rem' }}>Preis-Alerts (Telegram)</h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: t.textMuted, fontSize: '0.875rem' }}>Stadt</label>
                  <input type="text" value={alertCity} onChange={(e) => setAlertCity(e.target.value)} placeholder="z.B. London" className="input-field" />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: t.textMuted, fontSize: '0.875rem' }}>Max. Preis (€)</label>
                  <input type="number" value={alertMaxPrice} onChange={(e) => setAlertMaxPrice(parseInt(e.target.value) || 50)} className="input-field" />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: t.textMuted, fontSize: '0.875rem' }}>Telegram Chat ID</label>
                  <input type="text" value={alertChatId} onChange={(e) => setAlertChatId(e.target.value)} placeholder="z.B. 123456789" className="input-field" />
                </div>
              </div>
              <button className="btn-primary" onClick={createAlert} disabled={!alertCity || !alertChatId} style={{ width: '100%', padding: '0.75rem', fontSize: '1rem' }}>Alert erstellen</button>

              {alerts.length > 0 && (
                <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {alerts.map((alert) => (
                    <div key={alert.id} className="result-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <span style={{ fontWeight: 600 }}>{alert.destination_city}</span>
                        <span style={{ marginLeft: '0.75rem', color: '#22c55e', fontFamily: 'Space Mono, monospace' }}>≤ {alert.max_price}€</span>
                        <span style={{ marginLeft: '0.75rem', color: t.textMuted, fontSize: '0.875rem' }}>Chat: {alert.telegram_chat_id}</span>
                      </div>
                      <button className="delete-btn" onClick={() => deleteAlert(alert.id)}>Löschen</button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: '3rem', color: t.textDim, fontSize: '0.875rem' }}>Flight Scout</div>
      </div>

      {/* Auth Modal */}
      {showAuth && (
        <div className="modal-overlay" onClick={() => setShowAuth(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ margin: '0 0 1.5rem 0', textAlign: 'center' }}>{authMode === 'login' ? 'Anmelden' : 'Registrieren'}</h2>
            {authError && (
              <div style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', padding: '0.75rem', marginBottom: '1rem', color: '#ef4444', fontSize: '0.875rem' }}>{authError}</div>
            )}
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: t.textMuted, fontSize: '0.875rem' }}>Benutzername</label>
              <input type="text" value={authUsername} onChange={(e) => setAuthUsername(e.target.value)} className="input-field" onKeyDown={(e) => e.key === 'Enter' && handleAuth()} />
            </div>
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: t.textMuted, fontSize: '0.875rem' }}>Passwort</label>
              <input type="password" value={authPassword} onChange={(e) => setAuthPassword(e.target.value)} className="input-field" onKeyDown={(e) => e.key === 'Enter' && handleAuth()} />
            </div>
            <button className="btn-primary" onClick={handleAuth} style={{ width: '100%', marginBottom: '1rem' }}>{authMode === 'login' ? 'Anmelden' : 'Registrieren'}</button>
            <p style={{ textAlign: 'center', color: t.textMuted, fontSize: '0.875rem', margin: 0 }}>
              {authMode === 'login' ? (
                <>Noch kein Konto? <span onClick={() => { setAuthMode('register'); setAuthError(''); }} style={{ color: '#6366f1', cursor: 'pointer' }}>Registrieren</span></>
              ) : (
                <>Bereits ein Konto? <span onClick={() => { setAuthMode('login'); setAuthError(''); }} style={{ color: '#6366f1', cursor: 'pointer' }}>Anmelden</span></>
              )}
            </p>
          </div>
        </div>
      )}

      {/* Share Toast */}
      {showShareToast && <div className="toast">In Zwischenablage kopiert!</div>}

      {/* New Deal Toasts */}
      <div style={{ position: 'fixed', top: '1.5rem', right: '1.5rem', zIndex: 9999, display: 'flex', flexDirection: 'column', gap: '0.75rem', maxWidth: '380px' }}>
        {dealToasts.slice(-3).map((toast) => (
          <div key={toast.id} className="deal-toast"
            style={{
              background: theme === 'dark' ? 'rgba(30, 41, 59, 0.95)' : 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(20px)',
              border: `1px solid ${getPriceColor(toast.price)}44`,
              borderLeft: `4px solid ${getPriceColor(toast.price)}`,
              borderRadius: '16px',
              padding: '1rem 1.25rem',
              boxShadow: `0 8px 32px rgba(0,0,0,0.3), 0 0 20px ${getPriceColor(toast.price)}22`,
            }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: toast.fact ? '0.5rem' : 0 }}>
              <span style={{ fontSize: '1.5rem' }}>&#9992;</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: t.text }}>
                  {toast.city}
                  <span style={{ opacity: 0.5, fontWeight: 400, marginLeft: '0.5rem' }}>{toast.country}</span>
                </div>
                <div style={{ fontFamily: 'Space Mono, monospace', fontWeight: 700, color: getPriceColor(toast.price), fontSize: '1.1rem' }}>
                  ab {toast.price.toFixed(0)}€
                </div>
              </div>
            </div>
            {toast.fact && (
              <div style={{ fontSize: '0.8rem', color: t.textMuted, lineHeight: 1.4, borderTop: `1px solid ${t.glassBorder}`, paddingTop: '0.5rem', fontStyle: 'italic' }}>
                {toast.fact}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
