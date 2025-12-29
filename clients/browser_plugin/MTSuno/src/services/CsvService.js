export class CsvService {
    static parse(text) {
        const rows = [];
        let currentRow = [];
        let currentVal = '';
        let inQuotes = false;

        for (let i = 0; i < text.length; i++) {
            const char = text[i];
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                currentRow.push(currentVal.trim());
                currentVal = '';
            } else if (char === '\n' && !inQuotes) {
                currentRow.push(currentVal.trim());
                rows.push(currentRow);
                currentRow = [];
                currentVal = '';
            } else {
                currentVal += char;
            }
        }
        if (currentVal) currentRow.push(currentVal.trim());
        if (currentRow.length > 0) rows.push(currentRow);

        if (rows.length < 2) return [];

        // Headers
        const headers = rows[0].map(h => h.toLowerCase().replace(/['"]/g, ''));
        const data = [];

        for (let i = 1; i < rows.length; i++) {
            const rowData = rows[i];
            if (rowData.length === headers.length) {
                const obj = {};
                headers.forEach((h, idx) => obj[h] = rowData[idx].replace(/^"|"$/g, ''));
                data.push(obj);
            }
        }
        return data;
    }
}
