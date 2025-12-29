// Popup Script - ติดต่อ Backend และส่งข้อมูลไป Content Script

const API_URL = "http://127.0.0.1:8000/api/get-video";

const fileIdInput = document.getElementById('fileId');
const uploadBtn = document.getElementById('uploadBtn');
const statusDiv = document.getElementById('status');

function showStatus(type, message) {
    statusDiv.className = 'status ' + type;
    statusDiv.textContent = message;
}

async function fetchAndUpload() {
    const fileId = fileIdInput.value.trim() || 'my_test_video_01';

    uploadBtn.disabled = true;
    showStatus('loading', '⏳ กำลังดึงวิดีโอจาก Server...');

    try {
        // 1. เรียก Backend API
        console.log("📨 Fetching video from localhost...");
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                type: "file_request",
                fileId: fileId
            })
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const envelope = await response.json();
        console.log("📦 Received envelope:", envelope);

        // 2. แกะซอง
        const message = envelope.messages[0];

        if (message.type === "video" && message.contentProvider.encoding === "base64") {
            showStatus('loading', '📤 กำลังส่งไฟล์ไป Shopee...');

            // 3. ส่งไป Content Script
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

            if (!tab.url.includes('seller.shopee.co.th')) {
                throw new Error('กรุณาเปิดหน้า Shopee Creator Center ก่อน');
            }

            chrome.tabs.sendMessage(tab.id, {
                action: "uploadVideo",
                base64Data: message.payload,
                fileName: `${message.packageId || 'video'}.mp4`
            }, (response) => {
                if (chrome.runtime.lastError) {
                    showStatus('error', '❌ ' + chrome.runtime.lastError.message);
                } else if (response && response.success) {
                    showStatus('success', '✅ อัพโหลดวิดีโอสำเร็จ! รอ Shopee ประมวลผล...');
                } else {
                    showStatus('error', '❌ ' + (response?.message || 'Unknown error'));
                }
                uploadBtn.disabled = false;
            });

        } else {
            throw new Error('Invalid message format from server');
        }

    } catch (error) {
        console.error("💥 Error:", error);
        showStatus('error', '❌ ' + error.message);
        uploadBtn.disabled = false;
    }
}

uploadBtn.addEventListener('click', fetchAndUpload);

// Enter key to submit
fileIdInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        fetchAndUpload();
    }
});

console.log("🔌 Popup script loaded!");
