<script setup lang="ts">
import axios from 'axios'

import { computed, ref, reactive, onMounted } from 'vue'
import { useVuelidate } from '@vuelidate/core'
import { required, maxLength, minLength } from '@vuelidate/validators'
import { Notyf } from 'notyf'

// Default confi for notyf
const notyf = new Notyf({
  duration: 4500,
  dismissible: true,
  position: {
    x: 'right',
    y: 'top'
  }
})

// Validation for user input string
const state = reactive({ userText: '' })
const rules = {
  userText: {
    minLengthValue: maxLength(1600),
    maxLengthValue: minLength(12),
    required,
    $autoDirty: true
  }
}
const v$ = useVuelidate(rules, state)

// Translated text for live representation
const liveTranslatedText = ref('')

// Common states for jobs: translation, extraction, creating choices
enum JobStatus {
  NotStarted = 'notStarted',
  Doing = 'doing',
  Done = 'done'
}

let transStatus = ref(JobStatus.NotStarted)
let extraStatus = ref(JobStatus.NotStarted)
let choicesStatus = ref(JobStatus.NotStarted)

// Indicates whether the translation has been started
const transHasStarted = computed(() => {
  return transStatus.value !== JobStatus.NotStarted
})

const anyInProgress = computed(() => {
  return transStatus.value === JobStatus.Doing || extraStatus.value == JobStatus.Doing
})

// The result of translation
const transResult = ref({
  origText: '',
  translatedText: ''
})

// The word sample object which has been extraed and saved to the voc book.
const wordSample = ref({
  word: '',
  word_normal: '',
  word_meaning: '',
  pronunciation: '',
  orig_text: '',
  translated_text: ''
})

// The word choices available for choosing
const wordChoices = ref([])

// Translate the user input text and extract word from it
function extractWord() {
  resetStatuses()

  // Validate input
  v$.value.$touch()
  if (v$.value.$error) {
    return false
  }

  transStatus.value = JobStatus.Doing

  // Create the SSE stream
  const source = new EventSource(
    window.API_ENDPOINT + '/api/translations/?user_text=' + encodeURIComponent(state.userText)
  )

  source.addEventListener('trans_partial', (event) => {
    const parsedData = JSON.parse(event.data)
    liveTranslatedText.value += parsedData.text
  })

  // Translation finished, set the text and start extracting
  source.addEventListener('translation', (event) => {
    const parsedData = JSON.parse(event.data)
    liveTranslatedText.value = parsedData.translated_text

    // Set global translated result
    transResult.value.origText = parsedData.text
    transResult.value.translatedText = parsedData.translated_text

    // Start to extract word
    extractWordSample(parsedData.text, parsedData.translated_text)
  })

  source.addEventListener('error', (event) => {
    if (event.data === undefined) {
      return
    }
    const parsedData = JSON.parse(event.data)
    notyf.error(parsedData.message)
  })

  source.onerror = function (event) {
    source.close()
    transStatus.value = JobStatus.Done
  }
}

// Extract one unknown word from the given english text
async function extractWordSample(origText: string, translatedText: string) {
  extraStatus.value = JobStatus.Doing

  let resp
  try {
    resp = await axios.post(window.API_ENDPOINT + '/api/word_samples/extractions/', {
      orig_text: origText,
      translated_text: translatedText
    })
  } catch (error) {
    const msg = error.resposne ? error.response.data.message : error.message
    notyf.error('Error requesting API: ' + msg)
    return
  }

  if (resp.data.word_sample === undefined) {
    notyf.error('Response is not valid JSON')
    return
  }

  // Update global state and notify user
  wordSample.value = resp.data.word_sample
  const msg = `<strong>${wordSample.value.word}</strong> was added to your vocabulary book (${resp.data.count} in total), well done! 🎉`
  extraStatus.value = JobStatus.Done
  notyf.success({ message: msg, dismissible: true, duration: 0 })
}

// Remove current word, show more word choices
async function undoShowChoices() {
  // Hide the extraction panel
  extraStatus.value = JobStatus.NotStarted

  // Remove the word sample first
  try {
    await axios.post(window.API_ENDPOINT + '/api/word_samples/deletion/', [wordSample.value.word])
  } catch (error) {
    // Ignore error when unable to delete
  }
  notyf.success(
    `<strong>${wordSample.value.word}</strong> has been removed from your vocabulary book. 🗑️`
  )

  choicesStatus.value = JobStatus.Doing

  // Extract a list of uncommon words for the user to choose from
  let resp
  try {
    resp = await axios.post(window.API_ENDPOINT + '/api/word_choices/extractions/', {
      orig_text: transResult.value.origText,
      translated_text: transResult.value.translatedText
    })
  } catch (error) {
    const msg = error.resposne ? error.response.data.message : error.message
    notyf.error('Error requesting API: ' + msg)
    return
  }

  wordChoices.value = resp.data.word_choices
  choicesStatus.value = JobStatus.Done
}

// Save selected words
async function saveChoices() {
  // Validate first
  const words = Array.from(document.querySelectorAll('input[name="word-choice"]:checked')).map(
    (checkbox) => checkbox.value
  )
  if (words.length === 0) {
    notyf.error('Please select at least 1 word')
    return
  }

  const checkedWordObjs = wordChoices.value.filter((wordObj) => words.includes(wordObj.word))

  let resp
  try {
    resp = await axios.post(window.API_ENDPOINT + '/api/word_choices/save/', {
      orig_text: transResult.value.origText,
      translated_text: transResult.value.translatedText,
      choices: checkedWordObjs
    })
  } catch (error) {
    const msg = error.resposne ? error.response.data.message : error.message
    notyf.error('Error requesting API: ' + msg)
    return
  }

  // Notify user
  const addedWrodsStr = resp.data.added_words.map((word) => word.word).join(', ')
  const msg = `<strong>${addedWrodsStr}</strong> was added to your vocabulary book (${resp.data.count} in total), well done! 🎉`
  extraStatus.value = JobStatus.NotStarted
  choicesStatus.value = JobStatus.NotStarted
  notyf.success({ message: msg, dismissible: true, duration: 2000 })
}

// Cancel the choices form
function cancelChoices() {
  extraStatus.value = JobStatus.NotStarted
  choicesStatus.value = JobStatus.NotStarted
}

// Reset all states
function reset() {
  resetStatuses()
  state.userText = ''
  v$.value.$reset()
}

function resetStatuses() {
  transStatus.value = JobStatus.NotStarted
  extraStatus.value = JobStatus.NotStarted
  choicesStatus.value = JobStatus.NotStarted

  liveTranslatedText.value = ''
  wordSample.value.word = ''
}
</script>

<template>
  <div class="row mt-4">
    <div class="col-12">
      <form>
        <div class="mb-3">
          <textarea
            id="input-text"
            autofocus
            class="form-control"
            style="height: 140px"
            placeholder="Text containing unknown word(s), e.g. The new parking fines are positively draconian."
            v-model="state.userText"
            :class="{ 'is-invalid': v$.userText.$error }"
          />
          <div class="form-text">
            <i class="bi bi-info-circle-fill"></i>
            One sentence at a time, don't paste huge amounts of text at once.
          </div>
          <div class="invalid-feedback">
            <template v-for="error of v$.userText.$errors" :key="error.$uid">
              {{ error.$message }}
            </template>
          </div>
        </div>
        <button
          type="button"
          class="btn btn-primary"
          :class="{ disabled: anyInProgress }"
          @click="extractWord()"
        >
          Translate & Extract Word
        </button>
        <div class="inprog-actions ms-2" v-if="transHasStarted">
          <button type="button" id="auto-extract" class="btn btn-link" @click="reset()">
            Reset
          </button>
        </div>
      </form>
    </div>
  </div>

  <div class="row mt-5">
    <div class="col-7" v-if="transHasStarted">
      <div class="card trans-ret">
        <div class="card-header" v-if="transStatus === JobStatus.Doing">
          <div class="spinner-border spinner-border-my-sm" role="status">
            <span class="sr-only"></span>
          </div>
          &nbsp;
          <span class="card-title-text">Translation in Progress...</span>
        </div>
        <div class="card-header" v-if="transStatus === JobStatus.Done">
          <i class="bi bi-pencil"></i>
          &nbsp;
          <span class="card-title-text">Translation Result</span>
        </div>

        <div class="card-body">
          <div class="card-text">{{ liveTranslatedText }}</div>
        </div>
      </div>
    </div>

    <div class="col-5">
      <div class="card extraction-card shadow-sm" v-if="extraStatus === JobStatus.Doing">
        <div class="card-header">
          <div class="spinner-border spinner-border-my-sm" role="status">
            <span class="sr-only"></span>
          </div>
          &nbsp;
          <span class="card-title-text">Extracting...</span>
        </div>
        <div class="card-body">
          <div class="card-text placeholder-glow">
            <span class="placeholder col-12 placeholder-lg"></span>
            <span class="placeholder col-12 placeholder-sm"></span>
            <span class="placeholder col-12 placeholder-sm"></span>
          </div>
        </div>
      </div>

      <div class="card extraction-card shadow-sm" v-if="extraStatus === JobStatus.Done">
        <div class="card-header">
          <i class="bi bi-bookmark-plus"></i>
          &nbsp;
          <span class="card-title-text">Word</span>

          <a
            href="javascript:void(0)"
            class="float-end"
            style="font-size: 13px; margin-top: 2px"
            @click="undoShowChoices()"
          >
            Undo & Pick Other
          </a>
        </div>
        <div class="card-body">
          <div class="card-text">
            <h5>{{ wordSample.word }}</h5>
            <p><strong>Pron：</strong> {{ wordSample.pronunciation }}</p>
            <p><strong>Mean：</strong> {{ wordSample.word_meaning }}</p>
          </div>
        </div>
      </div>

      <div class="card choices-card shadow-sm" v-if="choicesStatus === JobStatus.Doing">
        <div class="card-header">
          <div class="spinner-border spinner-border-my-sm" role="status">
            <span class="sr-only"></span>
          </div>
          &nbsp;
          <span class="card-title-text">Creating choices...</span>
        </div>
        <div class="card-body">
          <div class="card-text placeholder-glow">
            <span class="placeholder col-12 placeholder-sm"></span>
            <span class="placeholder col-12 placeholder-sm"></span>
            <span class="placeholder col-12 placeholder-sm"></span>
            <span class="placeholder col-12 placeholder-sm"></span>
          </div>
        </div>
      </div>

      <div class="card choices-card shadow-sm" v-if="choicesStatus === JobStatus.Done">
        <div class="card-header">
          <i class="bi bi-bookmark-plus"></i>
          &nbsp;
          <strong>Word Choices</strong>
        </div>
        <div class="card-body">
          <div class="card-text">
            <div class="list-group">
              <label
                class="list-group-item d-flex gap-2"
                v-for="choice of wordChoices"
                :key="choice.word"
              >
                <input
                  class="form-check-input flex-shrink-0"
                  type="checkbox"
                  name="word-choice"
                  :value="choice.word"
                />
                <span>
                  {{ choice.word }}
                  <small class="d-block text-body-secondary">
                    {{ choice.word_meaning }}
                  </small>
                </span>
              </label>
            </div>

            <div class="mt-2">
              <button
                type="button"
                id="save-choices"
                class="btn btn-sm btn-primary"
                @click="saveChoices()"
              >
                Save
              </button>
              <button type="button" class="btn btn-sm btn-link" @click="cancelChoices()">
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


<style scoped>
.trans-ret .card-text {
  height: 140px;
  overflow-y: auto;
}

.spinner-border-my-sm {
  color: #666;
  width: 14px;
  height: 14px;
}

.extraction-card .card-text {
  height: 140px;
  overflow-y: auto;
}
.extraction-card .card-text p {
  margin-bottom: 0;
  font-size: 13px;
}

.choices-card {
  min-height: 140px;
}

.inprog-actions {
  display: inline-block;
}

.card-title-text {
  font-weight: 500;
  color: #666;
}
</style>
