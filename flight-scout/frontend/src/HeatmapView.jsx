import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Koordinaten der Städte (erweitern nach Bedarf)
const CITY_COORDS = {
  'London': [51.5074, -0.1278],
  'Paris': [48.8566, 2.3522],
  'Athen': [37.9838, 23.7275],
  'Barcelona': [41.3851, 2.1734],
  // ... mehr Städte
};

function getColor(price) {
  if (price < 30) return '#22c55e';      // grün
  if (price < 50) return '#84cc16';      // lime
  if (price < 70) return '#eab308';      // gelb
  if (price < 100) return '#f97316';     // orange
  return '#ef4444';                       // rot
}

export default function HeatmapView({ results }) {
  console.log('Heatmap results:', results);  // ← Diese Zeile hinzufügen
  return (
    <div className="glass" style={{ padding: '1rem', height: '600px' }}>
      <MapContainer center={[48.2, 16.3]} zoom={4} style={{ height: '100%', borderRadius: '16px' }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap'
        />
        {results.map((deal, i) => {
          const coords = CITY_COORDS[deal.city];
          if (!deal.latitude || !deal.longitude) return null;
          return (
            <CircleMarker
              key={i}
              center={[deal.latitude, deal.longitude]}
              radius={Math.max(8, 30 - deal.price / 5)}
              fillColor={getColor(deal.price)}
              fillOpacity={0.8}
              stroke={false}
            >
              <Popup>
                <strong>{deal.city}</strong><br />
                {deal.price}€ | {deal.origin}
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}