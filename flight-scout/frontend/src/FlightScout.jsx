import { useState, useEffect } from 'react';
import HeatmapView from './HeatmapView';
const API_URL = 'http://localhost:8000';

const AIRPORTS = {
  vie: { name: 'Wien', emoji: '🇦🇹', color: '#dc2626' },
  bts: { name: 'Bratislava', emoji: '🇸🇰', color: '#2563eb' },
  bud: { name: 'Budapest', emoji: 'BD', color: '#16a34a' },
};

const WEEKDAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

const COUNTRIES = [
  'Griechenland', 'Türkei', 'Albanien', 'Montenegro',
  'Serbien', 'Nordmazedonien', 'Bosnien und Herzegowina',
  'Rumänien', 'Vereinigtes Königreich',
  'Irland', 'Niederlande', 'Belgien', 'Dänemark', 'Schweden',
  'Norwegen', 'Marokko', 'Frankreich',
  'Malta', 'Zypern', 'Spanien', 'Portugal'
];

export default function FlightScout() {
  // Form State
  const [selectedAirports, setSelectedAirports] = useState(['vie']);
  const [startDate, setStartDate] = useState('2026-03-20');
  const [endDate, setEndDate] = useState('2026-04-30');
  const [startWeekday, setStartWeekday] = useState(4); // Freitag
  const [duration, setDuration] = useState(2); // Fr-So
  const [adults, setAdults] = useState(1);
  const [maxPrice, setMaxPrice] = useState(70);
  const [minDepartureHour, setMinDepartureHour] = useState(14);
  const [whitelistCountries, setWhitelistCountries] = useState([]);
  const [activeTab, setActiveTab] = useState('search'); // 'search' | 'heatmap'
  // Job State
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  
  // UI State
  const [showCountryPicker, setShowCountryPicker] = useState(false);

  // Poll for job status
  useEffect(() => {
    if (!jobId || jobStatus?.status === 'completed' || jobStatus?.status === 'failed') {
      return;
    }
    
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/status/${jobId}`);
        const data = await res.json();
        setJobStatus(data);
        
        if (data.status === 'completed') {
          setResults(data.results || []);
          setIsSearching(false);
        } else if (data.status === 'failed') {
          setIsSearching(false);
        }
      } catch (e) {
        console.error('Status poll error:', e);
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [jobId, jobStatus?.status]);

  const toggleAirport = (code) => {
    setSelectedAirports(prev => 
      prev.includes(code) 
        ? prev.filter(a => a !== code)
        : [...prev, code]
    );
  };

  const toggleCountry = (country) => {
    setWhitelistCountries(prev =>
      prev.includes(country)
        ? prev.filter(c => c !== country)
        : [...prev, country]
    );
  };

  const startSearch = async () => {
    if (selectedAirports.length === 0) {
      alert('Bitte mindestens einen Flughafen auswählen!');
      return;
    }
    
    setIsSearching(true);
    setResults([]);
    setJobStatus(null);
    
    try {
      const res = await fetch(`${API_URL}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          airports: selectedAirports,
          start_date: startDate,
          end_date: endDate,
          start_weekday: startWeekday,
          duration: duration,
          adults: adults,
          max_price: maxPrice,
          min_departure_hour: minDepartureHour,
          whitelist_countries: whitelistCountries,
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

  const downloadPdf = () => {
    if (jobId) {
      window.open(`${API_URL}/download/${jobId}`, '_blank');
    }
  };

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('de-AT', { day: '2-digit', month: '2-digit' });
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
      fontFamily: "'Outfit', sans-serif",
      color: '#f8fafc',
      padding: '2rem',
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');
        
        * { box-sizing: border-box; }
        
        .glass {
          background: rgba(255, 255, 255, 0.03);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 24px;
        }
        
        .btn-primary {
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          border: none;
          padding: 1rem 2rem;
          border-radius: 16px;
          color: white;
          font-weight: 600;
          font-size: 1.1rem;
          cursor: pointer;
          transition: all 0.3s ease;
          box-shadow: 0 4px 24px rgba(99, 102, 241, 0.4);
        }
        
        .btn-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 32px rgba(99, 102, 241, 0.5);
        }
        
        .btn-primary:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          transform: none;
        }
        
        .chip {
          padding: 0.75rem 1.25rem;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s ease;
          border: 2px solid transparent;
          font-weight: 500;
        }
        
        .chip:hover {
          transform: scale(1.02);
        }
        
        .chip.selected {
          border-color: #6366f1;
          box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
        }
        
        .input-field {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 0.875rem 1rem;
          color: #f8fafc;
          font-size: 1rem;
          width: 100%;
          transition: all 0.2s ease;
        }
        
        .input-field:focus {
          outline: none;
          border-color: #6366f1;
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }
        
        .result-card {
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.06);
          border-radius: 16px;
          padding: 1.25rem;
          transition: all 0.3s ease;
        }
        
        .result-card:hover {
          background: rgba(255, 255, 255, 0.05);
          border-color: rgba(99, 102, 241, 0.3);
          transform: translateX(4px);
        }
        
        .price-tag {
          font-family: 'Space Mono', monospace;
          font-size: 1.5rem;
          font-weight: 700;
          color: #22c55e;
        }
        
        .progress-bar {
          height: 6px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 3px;
          overflow: hidden;
        }
        
        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #6366f1, #8b5cf6);
          border-radius: 3px;
          transition: width 0.5s ease;
        }
        
        .glow-text {
          text-shadow: 0 0 40px rgba(99, 102, 241, 0.5);
        }
        
        .country-chip {
          padding: 0.5rem 0.875rem;
          border-radius: 8px;
          font-size: 0.875rem;
          cursor: pointer;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          transition: all 0.2s ease;
        }
        
        .country-chip.selected {
          background: rgba(99, 102, 241, 0.2);
          border-color: #6366f1;
        }
        
        .country-chip:hover {
          background: rgba(255, 255, 255, 0.1);
        }
        
        .weekday-btn {
          width: 44px;
          height: 44px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          font-weight: 600;
          font-size: 0.875rem;
          background: rgba(255, 255, 255, 0.05);
          border: 2px solid transparent;
          transition: all 0.2s ease;
        }
        
        .weekday-btn:hover {
          background: rgba(255, 255, 255, 0.1);
        }
        
        .weekday-btn.start {
          background: #6366f1;
          border-color: #6366f1;
        }
        
        .weekday-btn.in-range {
          background: rgba(99, 102, 241, 0.3);
        }
        
        .weekday-btn.end {
          background: #8b5cf6;
          border-color: #8b5cf6;
        }
      `}</style>
      
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h1 style={{
            fontSize: '3.5rem',
            fontWeight: 700,
            margin: 0,
            letterSpacing: '-0.02em',
          }} className="glow-text">
            ✈️ Flight Scout
          </h1>
          <p style={{
            fontSize: '1.25rem',
            color: '#94a3b8',
            marginTop: '0.5rem',
          }}>
            Finde die günstigsten Wochenend-Flüge
          </p>
        </div>
        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>

<button onClick={() => setActiveTab('search')} className={activeTab === 'search' ? 'btn-primary' : 'chip'}>🔍 Suche</button>
<button onClick={() => setActiveTab('heatmap')} className={activeTab === 'heatmap' ? 'btn-primary' : 'chip'}>🗺️ Heatmap</button>
      </div>
      {activeTab === 'search' && (
        <>
        <div className="glass" style={{ padding: '2rem', marginBottom: '2rem' }}>
          {/* Airports */}
          <div style={{ marginBottom: '2rem' }}>
            <label style={{ display: 'block', marginBottom: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>
              Abflughäfen
            </label>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              {Object.entries(AIRPORTS).map(([code, airport]) => (
                <div
                  key={code}
                  className={`chip ${selectedAirports.includes(code) ? 'selected' : ''}`}
                  style={{
                    background: selectedAirports.includes(code)
                      ? `${airport.color}22`
                      : 'rgba(255, 255, 255, 0.05)',
                  }}
                  onClick={() => toggleAirport(code)}
                >
                  <span style={{ marginRight: '0.5rem' }}>{airport.emoji}</span>
                  {airport.name}
                  <span style={{ 
                    marginLeft: '0.5rem',
                    opacity: 0.6,
                    fontFamily: 'Space Mono, monospace',
                    fontSize: '0.875rem',
                  }}>
                    {code.toUpperCase()}
                  </span>
                </div>
              ))}
            </div>
          </div>
          
          {/* Date Range */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: '#94a3b8' }}>
                Von
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="input-field"
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: '#94a3b8' }}>
                Bis
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="input-field"
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: '#94a3b8' }}>
                Personen
              </label>
              <input
                type="number"
                min="1"
                max="9"
                value={adults}
                onChange={(e) => setAdults(parseInt(e.target.value) || 1)}
                className="input-field"
              />
            </div>
          </div>
          
          {/* Trip Days Selector */}
          <div style={{ marginBottom: '2rem' }}>
            <label style={{ display: 'block', marginBottom: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>
              Reisezeitraum: {WEEKDAYS[startWeekday]} bis {WEEKDAYS[(startWeekday + duration) % 7]}
              <span style={{ opacity: 0.6, marginLeft: '0.5rem' }}>({duration} Nächte)</span>
            </label>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              {WEEKDAYS.map((day, i) => {
                const endDay = (startWeekday + duration) % 7;
                const isStart = i === startWeekday;
                const isEnd = i === endDay;
                const isInRange = duration > 0 && (
                  (startWeekday <= endDay && i > startWeekday && i < endDay) ||
                  (startWeekday > endDay && (i > startWeekday || i < endDay))
                );
                
                return (
                  <div
                    key={day}
                    className={`weekday-btn ${isStart ? 'start' : ''} ${isEnd ? 'end' : ''} ${isInRange ? 'in-range' : ''}`}
                    onClick={() => {
                      if (isStart) return;
                      // Calculate duration
                      let newDuration = i - startWeekday;
                      if (newDuration <= 0) newDuration += 7;
                      setDuration(newDuration);
                    }}
                    onContextMenu={(e) => {
                      e.preventDefault();
                      setStartWeekday(i);
                    }}
                    title={isStart ? 'Starttag (Rechtsklick zum Ändern)' : 'Klick = Endtag setzen'}
                  >
                    {day}
                  </div>
                );
              })}
            </div>
            <p style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.5rem' }}>
              💡 Rechtsklick = Starttag ändern, Linksklick = Endtag setzen
            </p>
          </div>
          
          {/* Price & Time */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: '#94a3b8' }}>
                Max. Preis pro Person
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type="number"
                  min="20"
                  max="500"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(parseInt(e.target.value) || 70)}
                  className="input-field"
                  style={{ paddingRight: '3rem' }}
                />
                <span style={{
                  position: 'absolute',
                  right: '1rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: '#64748b',
                  fontFamily: 'Space Mono, monospace',
                }}>€</span>
              </div>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: '#94a3b8' }}>
                Früheste Abflugzeit
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type="number"
                  min="0"
                  max="23"
                  value={minDepartureHour}
                  onChange={(e) => setMinDepartureHour(parseInt(e.target.value) || 0)}
                  className="input-field"
                  style={{ paddingRight: '4rem' }}
                />
                <span style={{
                  position: 'absolute',
                  right: '1rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: '#64748b',
                }}>:00 Uhr</span>
              </div>
            </div>
          </div>
          
          {/* Country Whitelist */}
          <div style={{ marginBottom: '2rem' }}>
            <div 
              style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '0.75rem',
                cursor: 'pointer',
              }}
              onClick={() => setShowCountryPicker(!showCountryPicker)}
            >
              <label style={{ fontWeight: 600, color: '#94a3b8' }}>
                Länder-Whitelist 
                {whitelistCountries.length > 0 && (
                  <span style={{ 
                    marginLeft: '0.5rem',
                    background: '#6366f1',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '6px',
                    fontSize: '0.75rem',
                  }}>
                    {whitelistCountries.length} ausgewählt
                  </span>
                )}
              </label>
              <span style={{ color: '#64748b' }}>{showCountryPicker ? '▲' : '▼'}</span>
            </div>
            
            {showCountryPicker && (
              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '0.5rem',
                padding: '1rem',
                background: 'rgba(0, 0, 0, 0.2)',
                borderRadius: '12px',
              }}>
                {COUNTRIES.map(country => (
                  <div
                    key={country}
                    className={`country-chip ${whitelistCountries.includes(country) ? 'selected' : ''}`}
                    onClick={() => toggleCountry(country)}
                  >
                    {country}
                  </div>
                ))}
              </div>
            )}
            
            {whitelistCountries.length === 0 && (
              <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>
                Keine Einschränkung – alle Länder werden durchsucht
              </p>
            )}
          </div>
          
          {/* Search Button */}
          <button
            className="btn-primary"
            onClick={startSearch}
            disabled={isSearching || selectedAirports.length === 0}
            style={{ width: '100%' }}
          >
            {isSearching ? (
              <>
                <span style={{ marginRight: '0.5rem' }}>🔍</span>
                Suche läuft...
              </>
            ) : (
              <>
                <span style={{ marginRight: '0.5rem' }}>🚀</span>
                Flüge suchen
              </>
            )}
          </button>
        </div>
        
        {/* Progress Bar */}
        {isSearching && jobStatus && (
          <div className="glass" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              <span>{jobStatus.message}</span>
              <span style={{ fontFamily: 'Space Mono, monospace' }}>{jobStatus.progress}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${jobStatus.progress}%` }} />
            </div>
          </div>
        )}
        
        {/* Results */}
        {results.length > 0 && (
          <div className="glass" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.5rem' }}>
                🎯 {results.length} Deals gefunden
              </h2>
              <button
                onClick={downloadPdf}
                style={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  padding: '0.75rem 1.25rem',
                  borderRadius: '12px',
                  color: 'white',
                  cursor: 'pointer',
                  fontWeight: 500,
                }}
              >
                📄 PDF Download
              </button>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {results.slice(0, 20).map((deal, i) => (
                <a
                  key={i}
                  href={deal.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="result-card"
                  style={{ textDecoration: 'none', color: 'inherit', display: 'block' }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <span style={{
                        width: '32px',
                        height: '32px',
                        background: 'rgba(99, 102, 241, 0.2)',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        fontSize: '0.875rem',
                      }}>
                        {i + 1}
                      </span>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '1.1rem' }}>
                          {deal.city}
                          <span style={{ opacity: 0.5, marginLeft: '0.5rem', fontWeight: 400 }}>
                            {deal.country}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>
                          {formatDate(deal.departure_date)} – {formatDate(deal.return_date)}
                          {deal.flight_time && deal.flight_time !== '??:??' && (
                            <span style={{ marginLeft: '0.75rem' }}>✈️ {deal.flight_time}</span>
                          )}
                          <span style={{ marginLeft: '0.75rem', opacity: 0.6 }}>
                            ab {deal.origin}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="price-tag">
                      {deal.price.toFixed(0)}€
                    </div>
                  </div>
                </a>
              ))}
            </div>
            
            {results.length > 20 && (
              <p style={{ textAlign: 'center', marginTop: '1.5rem', color: '#64748b' }}>
                ... und {results.length - 20} weitere Deals im PDF
              </p>
            )}
          </div>
        )}
        
        {/* Empty State */}
        {jobStatus?.status === 'completed' && results.length === 0 && (
          <div className="glass" style={{ padding: '3rem', textAlign: 'center' }}>
            <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>😢</div>
            <h3 style={{ margin: 0, marginBottom: '0.5rem' }}>Keine Deals gefunden</h3>
            <p style={{ color: '#94a3b8', margin: 0 }}>
              Versuche einen höheren Maximalpreis oder frühere Abflugzeiten
            </p>
           </div>
        )}
        </>
      )}
{activeTab === 'heatmap' && (
  <HeatmapView results={results} />
)}

        
        
        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: '3rem', color: '#64748b', fontSize: '0.875rem' }}>
          Flight Scout • Powered by Python & React
        </div>
      </div>
    </div>
  );
}
