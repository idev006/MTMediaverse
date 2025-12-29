// background.js

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    // รับคำสั่งดาวน์โหลดจาก Content Script
    if (msg.type === 'DOWNLOAD_FILE') {
        
        // ใช้ API ของ Chrome โดยตรง (CSP ของ Suno ห้ามไม่ได้)
        chrome.downloads.download({
            url: msg.url,
            filename: `SunoMusic/${sanitizeFilename(msg.title)}.mp3`,
            conflictAction: 'uniquify',
            saveAs: false // false = โหลดเลยไม่ถาม, true = เด้งถามที่เก็บ
        }, (downloadId) => {
            if (chrome.runtime.lastError) {
                console.error("Download failed:", chrome.runtime.lastError);
            } else {
                console.log("Download started, ID:", downloadId);
            }
        });
    }
});

// ฟังก์ชันล้างชื่อไฟล์ให้ปลอดภัย
function sanitizeFilename(name) {
    return name.replace(/[^a-z0-9ก-๙\- ]/gi, '_').trim().substring(0, 100);
}