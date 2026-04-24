// Open-Meteo Wetter-Helper.

export function getWeatherIcon(code) {
  if (code <= 1) return '☀️';
  if (code <= 3) return '⛅';
  if (code <= 48) return '☁️';
  if (code <= 67) return '🌧️';
  if (code <= 77) return '❄️';
  if (code <= 82) return '🌧️';
  if (code <= 86) return '❄️';
  return '⛈️';
}

export function getWeatherLabel(code) {
  if (code <= 0) return 'Klar';
  if (code <= 1) return 'Überwiegend klar';
  if (code <= 2) return 'Teilweise bewölkt';
  if (code <= 3) return 'Bewölkt';
  if (code <= 48) return 'Nebelig';
  if (code <= 55) return 'Nieselregen';
  if (code <= 67) return 'Regen';
  if (code <= 77) return 'Schnee';
  if (code <= 82) return 'Regenschauer';
  if (code <= 86) return 'Schneeschauer';
  return 'Gewitter';
}

export const weatherCacheKey = (lat, lon, startDate) =>
  `${lat.toFixed(1)}_${lon.toFixed(1)}_${startDate}`;

// Fetcht Wetter-Forecast und liefert {code, temp} oder -1 bei Fehler.
export async function fetchWeatherData(lat, lon, startDate, endDate) {
  try {
    const res = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&daily=weathercode,temperature_2m_max&start_date=${startDate}&end_date=${endDate}&timezone=auto`
    );
    const data = await res.json();
    const codes = data?.daily?.weathercode || [];
    const temps = data?.daily?.temperature_2m_max || [];
    const worst = codes.length ? Math.max(...codes) : null;
    const avgTemp = temps.length ? Math.round(temps.reduce((a, b) => a + b, 0) / temps.length) : null;
    return { code: worst, temp: avgTemp };
  } catch {
    return -1;
  }
}
