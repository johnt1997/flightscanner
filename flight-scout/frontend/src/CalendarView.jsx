import { useState } from 'react';

const API_URL = 'http://localhost:8000';

const DAY_NAMES = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
const MONTH_NAMES = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];

function getPriceColor(price, maxPrice) {
  if (price === null) return 'rgba(255,255,255,0.03)';
  const ratio = price / maxPrice;
  if (ratio < 0.3) return '#22c55e';
  if (ratio < 0.5) return '#84cc16';
  if (ratio < 0.7) return '#eab308';
  if (ratio < 0.85) return '#f97316';
  return '#ef4444';
}

export default function CalendarView({ airports, maxPrice, duration, adults, blacklistCountries }) {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth()); // 0-indexed
  const [calendarData, setCalendarData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ message: '', percent: 0 });
  const [selectedDay, setSelectedDay] = useState(null);

  const monthStr = `${year}-${String(month + 1).padStart(2, '0')}`;

  const prevMonth = () => {
    if (month === 0) { setMonth(11); setYear(y => y - 1); }
    else setMonth(m => m - 1);
    setCalendarData(null);
    setSelectedDay(null);
  };

  const nextMonth = () => {
    if (month === 11) { setMonth(0); setYear(y => y + 1); }
    else setMonth(m => m + 1);
    setCalendarData(null);
    setSelectedDay(null);
  };

  const loadCalendar = async () => {
    if (airports.length === 0) return;
    setLoading(true);
    setCalendarData(null);
    setSelectedDay(null);

    try {
      const res = await fetch(`${API_URL}/calendar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          airports,
          month: monthStr,
          duration,
          adults,
          max_price: maxPrice,
          blacklist_countries: blacklistCountries,
        }),
      });
      const data = await res.json();
      const jobId = data.job_id;

      // Poll for completion
      const poll = setInterval(async () => {
        try {
          const statusRes = await fetch(`${API_URL}/status/${jobId}`);
          const statusData = await statusRes.json();
          setProgress({ message: statusData.message, percent: statusData.progress });

          if (statusData.status === 'completed') {
            clearInterval(poll);
            setCalendarData(statusData.results || []);
            setLoading(false);
          } else if (statusData.status === 'failed') {
            clearInterval(poll);
            setLoading(false);
            alert('Kalender-Suche fehlgeschlagen: ' + statusData.message);
          }
        } catch (e) {
          console.error('Poll error:', e);
        }
      }, 2000);
    } catch (e) {
      console.error('Calendar error:', e);
      setLoading(false);
      alert('Verbindung fehlgeschlagen!');
    }
  };

  // Build calendar grid
  const buildGrid = () => {
    if (!calendarData) return null;

    const firstDay = new Date(year, month, 1);
    // JS: 0=Sun, convert to Mon=0
    let startWeekday = firstDay.getDay() - 1;
    if (startWeekday < 0) startWeekday = 6;

    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const dataMap = {};
    calendarData.forEach(d => {
      const dayNum = parseInt(d.date.split('-')[2]);
      dataMap[dayNum] = d;
    });

    const cells = [];
    // Empty cells before first day
    for (let i = 0; i < startWeekday; i++) {
      cells.push(<div key={`empty-${i}`} style={{ minHeight: '80px' }} />);
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const data = dataMap[day];
      const price = data?.min_price;
      const count = data?.deals_count || 0;
      const bgColor = getPriceColor(price, maxPrice);
      const hasData = price !== null && price !== undefined;

      cells.push(
        <div
          key={day}
          onClick={() => hasData && setSelectedDay(data)}
          style={{
            minHeight: '80px',
            background: hasData ? `${bgColor}22` : 'rgba(255,255,255,0.02)',
            border: selectedDay?.date === data?.date ? '2px solid #6366f1' : '1px solid rgba(255,255,255,0.06)',
            borderRadius: '12px',
            padding: '0.5rem',
            cursor: hasData ? 'pointer' : 'default',
            transition: 'all 0.2s ease',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ fontSize: '0.875rem', opacity: 0.7 }}>{day}</div>
          {hasData && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontFamily: 'Space Mono, monospace', fontWeight: 700, fontSize: '1.1rem', color: bgColor }}>
                {Math.round(price)}€
              </div>
              <div style={{ fontSize: '0.7rem', opacity: 0.5 }}>{count} Deals</div>
            </div>
          )}
        </div>
      );
    }

    return cells;
  };

  return (
    <div>
      {/* Month Navigation */}
      <div className="glass" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <button onClick={prevMonth} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'white', padding: '0.5rem 1rem', borderRadius: '8px', cursor: 'pointer', fontSize: '1.2rem' }}>
            ◀
          </button>
          <div style={{ textAlign: 'center' }}>
            <h2 style={{ margin: 0, fontSize: '1.5rem' }}>
              {MONTH_NAMES[month]} {year}
            </h2>
            <div style={{ fontSize: '0.8rem', opacity: 0.5, marginTop: '0.25rem' }}>
              {duration} {duration === 1 ? 'Nacht' : 'Nächte'} · max {maxPrice}€
            </div>
          </div>
          <button onClick={nextMonth} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'white', padding: '0.5rem 1rem', borderRadius: '8px', cursor: 'pointer', fontSize: '1.2rem' }}>
            ▶
          </button>
        </div>

        <button
          className="btn-primary"
          onClick={loadCalendar}
          disabled={loading || airports.length === 0}
          style={{ width: '100%' }}
        >
          {loading ? `Lade... ${progress.percent}% – ${progress.message}` : 'Kalender laden'}
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="glass" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <span>{progress.message}</span>
            <span style={{ fontFamily: 'Space Mono, monospace' }}>{progress.percent}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress.percent}%` }} />
          </div>
        </div>
      )}

      {/* Calendar Grid */}
      {calendarData && (
        <div className="glass" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
          {/* Day headers */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '0.5rem', marginBottom: '0.5rem' }}>
            {DAY_NAMES.map(d => (
              <div key={d} style={{ textAlign: 'center', fontWeight: 600, color: '#94a3b8', fontSize: '0.875rem', padding: '0.5rem 0' }}>
                {d}
              </div>
            ))}
          </div>

          {/* Day cells */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '0.5rem' }}>
            {buildGrid()}
          </div>

          {/* Legend */}
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '1rem', fontSize: '0.75rem', color: '#94a3b8' }}>
            <span><span style={{ color: '#22c55e' }}>●</span> Günstig</span>
            <span><span style={{ color: '#eab308' }}>●</span> Mittel</span>
            <span><span style={{ color: '#ef4444' }}>●</span> Teuer</span>
          </div>
        </div>
      )}

      {/* Selected Day Details */}
      {selectedDay && selectedDay.deals && selectedDay.deals.length > 0 && (
        <div className="glass" style={{ padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 1rem 0' }}>
            Deals am {new Date(selectedDay.date).toLocaleDateString('de-AT', { day: '2-digit', month: '2-digit', year: 'numeric' })}
            <span style={{ fontWeight: 400, fontSize: '0.875rem', opacity: 0.6, marginLeft: '0.75rem' }}>
              ({duration} {duration === 1 ? 'Nacht' : 'Nächte'})
            </span>
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {selectedDay.deals.map((deal, i) => (
              <a
                key={i}
                href={deal.url}
                target="_blank"
                rel="noopener noreferrer"
                className="result-card"
                style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', textDecoration: 'none', color: 'inherit', cursor: 'pointer' }}
              >
                <div>
                  <span style={{ fontWeight: 600 }}>{deal.country}</span>
                  <span style={{ marginLeft: '0.75rem', fontSize: '0.875rem', color: '#94a3b8' }}>ab {deal.origin}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ fontFamily: 'Space Mono, monospace', fontWeight: 700, color: '#22c55e' }}>
                    {Math.round(deal.price)}€
                  </span>
                  <span style={{ fontSize: '0.75rem', opacity: 0.5 }}>↗</span>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
