<template>
  <div class="form-control w-full">
    <label class="label">
      <span class="label-text-alt text-gray-400">Select CSV File</span>
    </label>
    <input 
      type="file" 
      accept=".csv"
      class="file-input file-input-bordered file-input-xs w-full max-w-xs bg-base-300" 
      @change="onFileChange"
    />
  </div>
</template>

<script setup>
import { defineEmits } from 'vue'

const emit = defineEmits(['file-loaded'])

const onFileChange = (e) => {
  const file = e.target.files[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    emit('file-loaded', e.target.result)
  }
  reader.readAsText(file)
}
</script>
