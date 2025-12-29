import { ref, computed } from 'vue'
import { CsvService } from '../services/CsvService'
import { AutomationService } from '../services/AutomationService'

export function useAutomation() {
    const songs = ref([])
    const logs = ref([])
    const isRunning = ref(false)
    const automationService = new AutomationService()

    const completedCount = computed(() => songs.value.filter(s => s.status === 'Completed').length)

    const addLog = (msg) => {
        const entry = `[${new Date().toLocaleTimeString()}] ${msg}`
        logs.value.push(entry)
        console.log('[VM]', msg)
    }

    const processCsvData = (text) => {
        try {
            const data = CsvService.parse(text)
            songs.value = data.map((row, index) => ({
                id: index + 1,
                title: row['descr'] || row['title'] || 'Untitled',
                style: row['style'] || '',
                lyrics: row['lyrics'] || '',
                status: 'Pending', // Pending, Processing, Generating, Completed, Error
                msg: ''
            }))
            addLog(`Parsed ${songs.value.length} songs from CSV`)
        } catch (e) {
            addLog(`Error parsing CSV: ${e.message}`)
        }
    }

    const startJob = async () => {
        if (isRunning.value) return
        if (songs.value.length === 0) return

        isRunning.value = true
        addLog('Starting Automation Job...')

        for (const song of songs.value) {
            // Check Stop Flag? (TODO)

            song.status = 'Processing'
            // Scroll to row? (In component)

            try {
                addLog(`Processing: ${song.title}`)

                // 1. Fill Inputs
                await automationService.fillForm(song.title, song.style, song.lyrics)

                // 2. Click Create
                await automationService.clickCreate()

                song.status = 'Generating'

                // 3. Wait for Generation (Top 2 items)
                await automationService.waitForGeneration()

                // 4. Extract & Send (TODO: Call BackendStub)
                song.status = 'Completed'
                song.msg = 'Saved'

            } catch (e) {
                console.error(e)
                song.status = 'Error'
                song.msg = e.message
                addLog(`Error processing ${song.id}: ${e.message}`)
            }

            // Wait a bit
            await new Promise(r => setTimeout(r, 2000))
        }

        isRunning.value = false
        addLog('Job Finished')
    }

    return {
        songs,
        logs,
        isRunning,
        completedCount,
        processCsvData,
        startJob
    }
}
