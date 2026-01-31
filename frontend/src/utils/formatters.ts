// Helper function to format decimal hours to h:mm format
export const formatHoursMinutes = (decimalHours: number | null | undefined): string => {
  if (decimalHours === null || decimalHours === undefined || isNaN(decimalHours)) return '--';
  const hours = Math.floor(decimalHours);
  const minutes = Math.round((decimalHours - hours) * 60);
  return `${hours}:${minutes.toString().padStart(2, '0')}`;
};

// Convert kg to lbs
export const kgToLbs = (kg: number | null | undefined): number | null => {
  if (kg === null || kg === undefined || isNaN(kg)) return null;
  return kg * 2.20462;
};

// Format body fat percentage (stored as decimal like 0.24, display as 24%)
export const formatBodyFatPercent = (decimal: number | null | undefined): string => {
  if (decimal === null || decimal === undefined || isNaN(decimal)) return '--';
  return (decimal * 100).toFixed(1);
};
