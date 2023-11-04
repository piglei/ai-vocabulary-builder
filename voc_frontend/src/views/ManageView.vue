<script setup lang="ts">
import 'bootstrap'
import axios from 'axios'

import { Notyf } from 'notyf'
import { ref, onMounted, onUpdated } from 'vue'
import { DateTime } from 'luxon'

const notyf = new Notyf({
  duration: 4500,
  dismissible: true,
  position: {
    x: 'right',
    y: 'top'
  }
})

const words = ref([])
const count = ref(0)

onMounted(() => {
  getWords()
})

onUpdated(() => {
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
  const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
})

// Get word samples
async function getWords() {
  let resp
  try {
    resp = await axios.get(window.API_ENDPOINT + '/api/word_samples/')
  } catch (error) {
    const msg = error.resposne ? error.response.data.message : error.message
    notyf.error('Error requesting API: ' + msg)
    return
  }

  words.value = resp.data.words
  words.value.forEach((w) => {
    w.dateAdded = DateTime.fromSeconds(w.ts_date_added)
  })
  count.value = resp.data.count
}

// Remove a word
// TODO: Add confirmation
async function removeWord(word) {
  try {
    await axios.post(window.API_ENDPOINT + '/api/word_samples/deletion/', [word])
  } catch (error) {
    const msg = error.resposne ? error.response.data.message : error.message
    notyf.error('Error requesting API: ' + msg)
    return
  }

  // Remove it from local memory
  words.value = words.value.filter((obj) => obj.ws.word !== word)
  count.value = words.value.length
  notyf.success(`<strong>${word}</strong> has been removed.`)
}

</script>

<template>
  <div class="row mt-4">
    <div class="col-12">
      <h6 class="me-1" style="display: inline-block">Words</h6>
      <span class="badge text-bg-secondary">{{ count }}</span>
      <table class="table table-striped words-list mt-3" v-if="words.length > 0">
        <colgroup>
          <col span="1" style="width: 120px" />
          <col span="1" />
          <col span="1" />
          <col span="1" style="width: 120px" />
          <col span="1" style="width: 80px" />
        </colgroup>

        <thead>
          <tr>
            <th scope="col">Word</th>
            <th scope="col">Definition</th>
            <th scope="col">Example sentence / Translation</th>
            <th scope="col">Date Added</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="word of words" :key="word.ws.word">
            <td>
              <div class="word mb-1">{{ word.ws.word }}</div>
              <div class="pronun text-secondary">{{ word.ws.pronunciation }}</div>
            </td>
            <td>{{ word.ws.word_meaning }}</td>
            <td>
              {{ word.ws.orig_text }} /
              <span class="text-secondary">{{ word.ws.translated_text }}</span>
            </td>
            <td>
              <span data-bs-toggle="tooltip" :title="word.dateAdded.toISO()">
                {{ word.dateAdded.toRelativeCalendar() }}
              </span>
            </td>
            <td>
              <a class="word-action" href="javascript:void(0)" @click="removeWord(word.ws.word)">remove</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style>
.words-list {
  font-size: 13px;
}
.words-list .word {
  font-size: 15px;
  font-weight: 500;
}
.words-list .proun {
  font-size: 13px;
}
</style>
