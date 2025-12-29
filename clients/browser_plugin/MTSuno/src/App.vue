<template>
  <div class="card w-96 bg-base-100 shadow-xl border border-gray-700" :class="{ 'opacity-20 hover:opacity-100 transition-opacity': isCollapsed }">
    <div class="card-body p-4">
      <!-- Header -->
      <div class="flex justify-between items-center mb-2">
        <h2 class="card-title text-sm font-bold text-primary">
          🎵 MTSuno <span v-if="version" class="text-xs text-gray-500">v{{ version }}</span>
        </h2>
        <div class="flex gap-2">
          <button class="btn btn-xs btn-circle btn-ghost" @click="toggleCollapse">
            {{ isCollapsed ? '+' : '-' }}
          </button>
        </div>
      </div>

      <!-- Main Content (Hidden if collapsed) -->
      <div v-show="!isCollapsed" class="flex flex-col gap-3">
        
        <!-- File Upload -->
        <FileUpload @file-loaded="handleFileLoaded" />

        <!-- Progress / Stats -->
        <div v-if="songs.length > 0" class="stats stats-vertical lg:stats-horizontal shadow bg-base-200">
          <div class="stat p-2">
            <div class="stat-title text-xs">Total</div>
            <div class="stat-value text-lg">{{ songs.length }}</div>
          </div>
          <div class="stat p-2">
            <div class="stat-title text-xs">Done</div>
            <div class="stat-value text-lg text-success">{{ completedCount }}</div>
          </div>
        </div>

        <!-- Start Button -->
        <button 
          class="btn btn-primary btn-sm w-full" 
          :disabled="songs.length === 0 || isRunning"
          @click="startAutomation"
        >
          <span v-if="isRunning" class="loading loading-spinner loading-xs"></span>
          {{ isRunning ? 'Running...' : 'Start Automation' }}
        </button>

        <!-- Song Table -->
        <div class="overflow-x-auto max-h-60 rounded-lg border border-base-300">
          <SongTable :songs="songs" />
        </div>

        <!-- Logs (Optional/Debug) -->
        <div class="collapse collapse-arrow bg-base-200 border border-base-300 rounded-box">
          <input type="checkbox" /> 
          <div class="collapse-title text-xs font-medium min-h-0 py-2">
            Show Logs
          </div>
          <div class="collapse-content text-xs font-mono max-h-32 overflow-y-auto">
             <div v-for="(log, i) in logs" :key="i" class="border-b border-gray-700 pb-1 mb-1">
               {{ log }}
             </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import FileUpload from './components/FileUpload.vue'
import SongTable from './components/SongTable.vue'
import { useAutomation } from './viewModels/useAutomation'

// Injected Globals
const stub = inject('$stub')

// State
const isCollapsed = ref(false)
const version = ref('1.0')

// ViewModel
const { 
  songs, 
  logs, 
  isRunning, 
  completedCount, 
  processCsvData, 
  startJob 
} = useAutomation()

// Methods
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

const handleFileLoaded = (csvText) => {
  processCsvData(csvText)
}

const startAutomation = async () => {
  await startJob()
}

onMounted(async () => { 
  console.log('App Mounted')
  if(stub) {
      const health = await stub.healthCheck()
      console.log('Backend Health:', health)
  }
})

</script>

<style scoped>
/* Scoped styles if needed, mostly Tailwind */
</style>
