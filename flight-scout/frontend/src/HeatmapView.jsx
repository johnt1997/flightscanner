import { useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const ORIGIN_AIRPORTS = {
  'Wien':       { coords: [48.1103, 16.5697], color: '#dc2626', code: 'VIE' },
  'Bratislava': { coords: [48.1702, 17.2127], color: '#2563eb', code: 'BTS' },
  'Budapest':   { coords: [47.4380, 19.2556], color: '#16a34a', code: 'BUD' },
};

function getPriceColor(price) {
  if (price < 30) return '#22c55e';
  if (price < 50) return '#84cc16';
  if (price < 70) return '#eab308';
  if (price < 100) return '#f97316';
  return '#ef4444';
}

function Legend({ origins }) {
  const map = useMap();
  return (
    <div style={{
      position: 'absolute', top: '10px', right: '10px', zIndex: 1000,
      background: 'rgba(15, 23, 42, 0.9)', backdropFilter: 'blur(8px)',
      borderRadius: '12px', padding: '12px 16px',
      border: '1px solid rgba(255,255,255,0.1)',
      color: '#f8fafc', fontSize: '0.8rem',
      pointerEvents: 'auto', minWidth: '140px',
    }}>
      <div style={{ fontWeight: 700, marginBottom: '8px', fontSize: '0.85rem' }}>Abflughaefen</div>
      {origins.map(name => {
        const ap = ORIGIN_AIRPORTS[name];
        if (!ap) return null;
        return (
          <div key={name} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: ap.color, border: '2px solid white', flexShrink: 0 }} />
            <span>{ap.code} {name}</span>
          </div>
        );
      })}
      <div style={{ borderTop: '1px solid rgba(255,255,255,0.15)', marginTop: '8px', paddingTop: '8px', fontWeight: 700, fontSize: '0.85rem' }}>Preise</div>
      {[
        { label: '< 30€', color: '#22c55e' },
        { label: '30-49€', color: '#84cc16' },
        { label: '50-69€', color: '#eab308' },
        { label: '70€+', color: '#f97316' },
      ].map(item => (
        <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: item.color, flexShrink: 0 }} />
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  );
}

export default function HeatmapView({ results }) {
  // Group deals by destination city, keep cheapest per city per origin
  const { cityDeals, activeOrigins } = useMemo(() => {
    const cities = {};
    const origins = new Set();

    results.forEach(deal => {
      if (deal.latitude == null || deal.longitude == null) return;
      if (deal.latitude === 0 && deal.longitude === 0) return;
      const origin = deal.origin || 'Wien';
      origins.add(origin);

      const key = `${deal.city}__${origin}`;
      if (!cities[key] || deal.price < cities[key].price) {
        cities[key] = { ...deal, origin };
      }
    });

    return { cityDeals: Object.values(cities), activeOrigins: [...origins] };
  }, [results]);

  return (
    <div className="glass" style={{ padding: '1rem', height: '600px', position: 'relative' }}>
      <MapContainer center={[46.5, 14]} zoom={4} style={{ height: '100%', borderRadius: '16px' }}>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; OpenStreetMap &copy; CARTO'
        />

        <Legend origins={activeOrigins} />

        {/* Lines from origin to destination */}
        {cityDeals.map((deal, i) => {
          const originAirport = ORIGIN_AIRPORTS[deal.origin];
          if (!originAirport) return null;
          return (
            <Polyline
              key={`line-${i}`}
              positions={[originAirport.coords, [deal.latitude, deal.longitude]]}
              pathOptions={{
                color: originAirport.color,
                weight: 1.5,
                opacity: 0.35,
                dashArray: '4 6',
              }}
            >
              <Popup>
                <strong>{originAirport.code} &rarr; {deal.city}</strong><br />
                {deal.price.toFixed(0)}€
                {deal.flight_time && deal.flight_time !== '??:??' && <><br />Hin: {deal.flight_time}</>}
                {deal.return_flight_time && deal.return_flight_time !== '??:??' && <> | Rueck: {deal.return_flight_time}</>}
              </Popup>
            </Polyline>
          );
        })}

        {/* Origin airport markers */}
        {activeOrigins.map(name => {
          const ap = ORIGIN_AIRPORTS[name];
          if (!ap) return null;
          return (
            <CircleMarker
              key={`origin-${name}`}
              center={ap.coords}
              radius={10}
              fillColor={ap.color}
              fillOpacity={1}
              color="white"
              weight={3}
            >
              <Popup><strong>{ap.code} - {name}</strong></Popup>
            </CircleMarker>
          );
        })}

        {/* Destination markers */}
        {cityDeals.map((deal, i) => {
          const originAirport = ORIGIN_AIRPORTS[deal.origin];
          return (
            <CircleMarker
              key={`dest-${i}`}
              center={[deal.latitude, deal.longitude]}
              radius={Math.max(6, 22 - deal.price / 5)}
              fillColor={getPriceColor(deal.price)}
              fillOpacity={0.85}
              color={originAirport ? originAirport.color : '#fff'}
              weight={2}
              opacity={0.6}
            >
              <Popup>
                <strong>{deal.city}</strong> ({deal.country})<br />
                <span style={{ fontSize: '1.1em', fontWeight: 700 }}>{deal.price.toFixed(0)}€</span> ab {deal.origin}<br />
                {deal.departure_date} &rarr; {deal.return_date}
                {deal.flight_time && deal.flight_time !== '??:??' && <><br />Hin: {deal.flight_time}</>}
                {deal.return_flight_time && deal.return_flight_time !== '??:??' && <> | Rueck: {deal.return_flight_time}</>}
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
