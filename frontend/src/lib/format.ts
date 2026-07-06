/** Utility di formattazione condivise (date/orari in italiano). */

/** Formatta una data ISO come "gg/mm/aaaa". */
export function formatData(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

/** Formatta un timestamp ISO come "gg/mm/aaaa, hh:mm". */
export function formatDataOra(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
