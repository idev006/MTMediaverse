<template>
  <table class="table table-xs table-pin-rows bg-base-100">
    <thead>
      <tr class="bg-base-200 text-gray-400">
        <th class="w-8">#</th>
        <th>Title</th>
        <th>Style</th>
        <th class="w-20">Status</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="song in songs" :key="song.id" :class="{ 'bg-base-300': song.status === 'Processing' }">
        <th>{{ song.id }}</th>
        <td class="max-w-[100px] truncate" :title="song.title">{{ song.title }}</td>
        <td class="max-w-[80px] truncate" :title="song.style">{{ song.style }}</td>
        <td>
           <span class="badge badge-xs" :class="statusClass(song.status)">{{ song.status }}</span>
        </td>
      </tr>
      <tr v-if="songs.length === 0">
         <td colspan="4" class="text-center text-gray-500 py-4">No data loaded</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { defineProps } from 'vue'

const props = defineProps({
  songs: { type: Array, required: true }
})

const statusClass = (status) => {
    switch(status) {
        case 'Pending': return 'badge-ghost'
        case 'Processing': return 'badge-info'
        case 'Generating': return 'badge-warning'
        case 'Completed': return 'badge-success'
        case 'Error': return 'badge-error'
        default: return 'badge-ghost'
    }
}
</script>
