export interface ExportOptions {
  filename?: string;
  format?: 'csv' | 'xlsx' | 'json';
  includeHeaders?: boolean;
  customFilename?: string;
}

export interface ExportableRow {
  [key: string]: any;
}

/**
 * Export data to various formats
 */
export function exportData(
  data: ExportableRow[],
  options: ExportOptions = {}
): void {
  const {
    filename = 'export',
    format = 'csv',
    includeHeaders = true,
    customFilename = '',
  } = options;
  
  const filenameWithExt = customFilename 
    ? customFilename 
    : `${filename}.${format}`;
  
  switch (format) {
    case 'csv':
      exportToCSV(data, filenameWithExt);
      break;
    case 'xlsx':
      exportToExcel(data, filenameWithExt);
      break;
    case 'json':
    default:
      exportToJSON(data, filenameWithExt);
      break;
  }
}

/**
 * Export to CSV format
 */
function exportToCSV(rows: ExportableRow[], filename: string): void {
  const headers = Object.keys(rows[0] || {});
  const csvContent = [
    headers.join(','),
    ...rows.map((row) => 
      headers.map(header => 
        `"${(row[header] ?? '').toString().replace(/"/g, '""')}"`
      ).join(',')
    )
  ].join('\\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  downloadFile(blob, filename);
}

/**
 * Export to Excel format (using existing JSON structure)
 */
function exportToExcel(rows: ExportableRow[], filename: string): void {
  // Using browser's native CSV download as fallback for Excel-compatible format
  exportToCSV(rows, filename);
}

/**
 * Export to JSON format
 */
function exportToJSON(rows: ExportableRow[], filename: string): void {
  const jsonContent = JSON.stringify(rows, null, 2);
  const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
  downloadFile(blob, filename);
}

/**
 * Trigger file download
 */
function downloadFile(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.setAttribute('target', '_self');
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Create download button element
 */
export function createExportButton(
  data: ExportableRow[],
  options: ExportOptions = {}, 
  className?: string
) {
  const handler = (e: React.MouseEvent) => {
    e.preventDefault();
    exportData(data, options);
  };

  const buttonId = `export-${options.filename || 'export'}-button`;
  const existingButton = document.getElementById(buttonId);

  if (existingButton) {
    existingButton.removeEventListener('click', () => {});
    existingButton.innerHTML = options.className 
      ? `${options.className} ${existingButton.innerHTML}`
      : existingButton.innerHTML;
  }

  const exportButton = document.createElement('button');
  exportButton.id = buttonId;
  exportButton.type = 'button';
  exportButton.addEventListener('click', handler);
  exportButton.textContent = 'Export';
  exportButton.setAttribute('aria-label', 'Export data');
  
  if (className) {
    exportButton.className = className;
  }

  return exportButton;
}