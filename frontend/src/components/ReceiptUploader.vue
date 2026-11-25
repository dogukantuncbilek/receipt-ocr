<script setup>
import { computed, ref } from 'vue'

const file = ref(null)
const preview = ref(null)
const processedImage = ref(null)
const showProcessed = ref(false)
const results = ref([])
const selected = ref(0)
const fields = ref({})
const busy = ref(false)
const error = ref('')

const selectedText = computed(() => results.value[selected.value]?.text ?? '')

function onFile(event) {
  const chosen = event.target.files[0]
  error.value = ''
  results.value = []
  fields.value = {}
  processedImage.value = null
  if (!chosen) {
    file.value = null
    preview.value = null
    return
  }
  if (!chosen.type.startsWith('image/')) {
    error.value = 'Choose an image file.'
    return
  }
  if (chosen.size > 10 * 1024 * 1024) {
    error.value = 'Image must be smaller than 10 MB.'
    return
  }
  file.value = chosen
  preview.value = URL.createObjectURL(chosen)
}

async function run() {
  if (!file.value || busy.value) return
  busy.value = true
  error.value = ''
  const body = new FormData()
  body.append('file', file.value)
  try {
    const response = await fetch(`/api/ocr?debug=${showProcessed.value}`, { method: 'POST', body })
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}))
      throw new Error(detail.detail || `HTTP ${response.status}`)
    }
    const data = await response.json()
    results.value = data.results
    fields.value = data.fields
    processedImage.value = data.processed_image ?? null
    selected.value = 0
    if (results.value.length === 0) error.value = 'No engine produced text. Try a sharper, flatter photo.'
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="layout">
    <section class="panel preview">
      <img v-if="preview" :src="preview" alt="uploaded receipt" />
      <img v-if="processedImage" :src="processedImage" alt="preprocessed receipt" />
      <p v-if="!preview" class="placeholder">Upload a receipt photo (JPG or PNG) to start.</p>
    </section>

    <section class="panel">
      <div class="controls">
        <label class="file-label">
          <input type="file" accept="image/*" @change="onFile" />
          Choose image
        </label>
        <button :disabled="!file || busy" @click="run">{{ busy ? 'Reading…' : 'Run OCR' }}</button>
        <label class="inline"><input v-model="showProcessed" type="checkbox" /> show preprocessed image</label>
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <template v-if="results.length">
        <select v-model="selected">
          <option v-for="(r, i) in results" :key="r.engine" :value="i">
            {{ r.engine }} · {{ r.confidence }}% confidence
          </option>
        </select>
        <textarea readonly :value="selectedText"></textarea>

        <table v-if="Object.keys(fields).length">
          <tbody>
            <tr v-for="(value, key) in fields" :key="key">
              <td class="key">{{ key }}</td>
              <td><input type="text" :value="value" @input="fields[key] = $event.target.value" /></td>
            </tr>
          </tbody>
        </table>
      </template>
    </section>
  </div>
</template>
