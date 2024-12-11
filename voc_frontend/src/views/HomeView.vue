<script setup lang="ts">
import axios from 'axios'

import { computed, ref, reactive, onMounted, watch, nextTick } from 'vue'
import { useVuelidate } from '@vuelidate/core'
import { required, maxLength, minLength } from '@vuelidate/validators'
import { Notyf } from 'notyf'
import tippy from 'tippy.js';
import 'tippy.js/dist/tippy.css';

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
    minLengthValue: maxLength(800),
    maxLengthValue: minLength(12),
    required,
    $autoDirty: true
  }
}
const v$ = useVuelidate(rules, state)

// State variables start
//
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

// Indicates whether the translation has been started
const transHasStarted = computed(() => {
  return transStatus.value !== JobStatus.NotStarted
})

const anyInProgress = computed(() => {
  return transStatus.value === JobStatus.Doing || extraStatus.value == JobStatus.Doing
})

// The translation result
const transResult = ref({
  origText: '',
  translatedText: ''
})

// The word which manually selected by the user
const manuallySelectedWord = ref('')

// The word sample object which has been extracted and saved to the voc book.
const wordSample = ref({
  word: '',
  word_normal: '',
  word_meaning: '',
  pronunciation: '',
  orig_text: '',
  translated_text: ''
})

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

// Extract one word automatically from the given text
async function extractWordSample(origText: string, translatedText: string) {
  extraStatus.value = JobStatus.Doing

  let resp
  try {
    resp = await axios.post(window.API_ENDPOINT + '/api/word_samples/extractions/', {
      orig_text: origText,
      translated_text: translatedText
    })
  } catch (error) {
    const msg = error.response ? error.response.data.message : error.message
    extraStatus.value = JobStatus.NotStarted
    notyf.error('Error requesting API: ' + msg)
    return
  }

  if (resp.data.word_sample === undefined) {
    extraStatus.value = JobStatus.NotStarted
    notyf.error('Response is not valid JSON')
    return
  }

  // Update global state and notify user
  wordSample.value = resp.data.word_sample
  const msg = `<strong>${wordSample.value.word}</strong> added, well done! 🎉`
  extraStatus.value = JobStatus.Done
  notyf.success({ message: msg, dismissible: true })
}

// Remove current word sample form the vocabulary book
async function removeWord() {
  // Hide the extraction panel
  extraStatus.value = JobStatus.NotStarted

  // Remove the word sample first
  try {
    await axios.post(window.API_ENDPOINT + '/api/word_samples/deletion/', [wordSample.value.word])
  } catch (error) {
    // Ignore error when unable to delete
  }
  notyf.success(`<strong>${wordSample.value.word}</strong> removed. 🗑️`)
  wordSample.value.word = ''
}


// Save a word manually
async function saveWordManually() {
  if (wordSample.value.word !== '') {
    await removeWord()
  }

  extraStatus.value = JobStatus.Doing

  // Save the word manually
  let resp
  try {
    resp = await axios.post(window.API_ENDPOINT + '/api/word_samples/manually_save/', {
      orig_text: transResult.value.origText,
      translated_text: transResult.value.translatedText,
      word: manuallySelectedWord.value
    })
  } catch (error) {
    const msg = error.response ? error.response.data.message : error.message
    extraStatus.value = JobStatus.NotStarted
    notyf.error('Error requesting API: ' + msg)
    return
  }

  // Update global state and notify user
  wordSample.value = resp.data.word_sample
  const msg = `<strong>${wordSample.value.word}</strong> added, well done! 🎉`
  extraStatus.value = JobStatus.Done
  notyf.success({ message: msg, dismissible: true})
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

  liveTranslatedText.value = ''
  wordSample.value.word = ''
  forceShowTextArea.value = false
}

// If the text param was provided by URL, start the extracting process right away
onMounted(() => {
  const urlParams = new URLSearchParams(window.location.search)
  const textParam = urlParams.get('text')
  if (textParam) {
    state.userText = textParam
    extractWord()
  }
})

// Watch user input text and update URL when text changes
watch(() => state.userText, (newValue) => {
  const url = new URL(window.location.href)
  if (newValue) {
    url.searchParams.set('text', newValue)
  } else {
    url.searchParams.delete('text')
  }
  window.history.replaceState(null, '', url.toString())
})

// Below are some example sentences for user to try
// Generated by AI(of course!)
const exampleSentences = [
  "The new parking fines are positively draconian.",
  "She had a penchant for exotic foods.",
  "The weather today is quite unpredictable.",
  "He was known for his philanthropic efforts.",
  "The architecture of the building is stunning.",
  "Her eloquence in speech was admired by all.",
  "The book offers profound insights into human nature.",
  "He faced the challenge with unwavering determination.",
  "The festival was a vibrant celebration of culture.",
  "She navigated the complex situation with grace.",
  "The artist's work is a blend of modern and traditional styles.",
  "He has an innate ability to solve problems.",
  "The movie's plot was both intriguing and thought-provoking.",
  "She has a meticulous approach to her work.",
  "The landscape was dotted with picturesque cottages.",
  "He was an advocate for environmental conservation.",
  "The team's synergy was evident in their performance.",
  "She has a keen eye for detail.",
  "The lecture was both informative and engaging.",
  "He was a pioneer in his field."
]

// Set the input to a random example sentence
function setExampleText() {
  const randomIndex = Math.floor(Math.random() * exampleSentences.length)
  state.userText = exampleSentences[randomIndex]
}

// A flag value to show the text area for user input
const forceShowTextArea = ref(false)

function toggleTextArea() {
  forceShowTextArea.value = !forceShowTextArea.value
}

// Tokenize the text into words and delimiters, so that user can select words manually.
function tokenizeText(text: string) {
  const tokens = []
  let currentToken = ''
  let currentType = ''

  for (let i = 0; i < text.length; i++) {
    const char = text[i]
    if (/[a-zA-Z-]/.test(char)) {
      if (currentType !== 'word') {
        if (currentToken) tokens.push({ type: currentType, value: currentToken })
        currentToken = char
        currentType = 'word'
      } else {
        currentToken += char
      }
    } else {
      if (currentType !== 'delimiter') {
        if (currentToken) tokens.push({ type: currentType, value: currentToken })
        currentToken = char
        currentType = 'delimiter'
      } else {
        currentToken += char
      }
    }
  }

  if (currentToken) tokens.push({ type: currentType, value: currentToken })
  return tokens
}

function saveManually(word: string) {
  manuallySelectedWord.value = word
  saveWordManually()
}

// Computed values start
//
const showTextArea = computed(() => {
  return transStatus.value === JobStatus.NotStarted || forceShowTextArea.value
})

// tokenizedText is the tokens which can be used for rendering the clickable text.
// Each token returned by this function has some special properties, such as "addedToVoc".
const tokenizedText = computed(() => {
  let tokens = tokenizeText(state.userText)
  let items = tokens.map(token => {
    let item = {"token": token, "addedToVoc": false}
    // When the word has been added to the vocabulary, mark it
    if (token.type === 'word' && token.value === wordSample.value.word) {
      item.addedToVoc = true
      return item
    }
    return item
  })
  return items
})

// Enable tippy instances for elements.

watch(tokenizedText, () => {
  nextTick(() => {
    tippy('.inputted-text-card span.word', {
      content: 'Select this word instead',
      delay: 300,
    })
  })
})

watch(showTextArea, () => {
  nextTick(() => {
    tippy('.icon-action', {delay: 300, placement: 'bottom'})
  })
})

</script>

<template>
  <div>
  <div class="row mt-4" v-if="showTextArea">
    <div class="col-12">
      <form>
        <div class="mb-3">
          <textarea
            id="input-text"
            autofocus
            class="form-control"
            style="height: 90px"
            placeholder="Text containing unknown word(s)."
            v-model="state.userText"
            :class="{ 'is-invalid': v$.userText.$error }"
          />
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
          <i class="bi bi-hammer"></i>
          Build Vocabulary
        </button>
        <div class="inprog-actions" v-if="transHasStarted">
          <button type="button" id="auto-extract" class="btn btn-link" @click="reset()">
            Reset
          </button>
        </div>
      </form>
    </div>
  </div>
  
  <div class="row mt-4" v-if="!showTextArea">
    <div class="col-12">
        <div class="card inputted-text-card">
          <div class="card-body">
            <template v-for="(t, index) in tokenizedText" :key="index">
              <span
                v-if="t.token.type === 'word' && t.addedToVoc"
                class="added-voc-word" 
              >
                {{ t.token.value }}
              </span>
              <span
                v-else-if="t.token.type === 'word'"
                @click="saveManually(t.token.value)"
                class="word"
                style="cursor: pointer"
              >
                {{ t.token.value }}
              </span>
              <span v-else>{{ t.token.value }}</span>
            </template>
          </div>
        </div>
        <i class="bi bi-pencil-square icon-action btn btn-light" data-tippy-content="Edit" @click="toggleTextArea"></i>
        <i class="bi bi-arrow-counterclockwise icon-action btn btn-light" data-tippy-content="Reset" @click="reset"></i>
    </div>
  </div>

  <div class="row mt-5">
    <div class="col-12" v-if="!transHasStarted">
      <div class="card tips-placeholder">
        <div class="card-body">
          <p>✨ Start building your vocabulary today with the power of AI! -- Tips: </p>
          <ul>
          <li>Input the text contains words you don't understand, click "Build" button.
            <a
              href="javascript:void(0)"
              id="set-example-text"
              @click="setExampleText"
            >
              [show me an example!]
            </a>
          </li>
          </ul>
        </div>
      </div>
    </div>

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
            @click="removeWord()"
          >
            Remove
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
    </div>
  </div>

  <footer class="footer mt-4 py-3 bg-light">
    <div class="container">
      <span class="text-muted">©2024 by <a href="https://www.piglei.com/" target="_blank">@piglei</a>.</span>
      <span class="text-muted float-end">
        <a href="https://github.com/piglei/ai-vocabulary-builder" target="_blank">
          <i class="bi bi-github"></i>
        </a>
      </span>
    </div>
  </footer>

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

.inprog-actions {
  display: inline-block;
}

.card-title-text {
  font-size: 16px;
  font-weight: 500;
  color: #666;
}


.inputted-text-card .card-body {
  line-height: 28px;
}
.inputted-text-card span.word:hover {
  color: #007bff;
  text-decoration: underline;
}
.inputted-text-card span.added-voc-word {
  font-weight: bold;
  text-decoration: underline;
}

.icon-action {
  cursor: pointer;
  margin-top: 12px;
  margin-right: 12px;
  display: inline-block;
  width: 50px;
  text-align: center;
}
.icon-action:hover {
  background-color: #f8f9fa;
  color: #007bff;
}

.footer {
  font-size: 14px;
}

.tips-placeholder {
  font-size: 14px;
}
.tips-placeholder p {
  margin: 4px 0;
}
.tips-placeholder ul {
  margin-bottom: 0;
}
</style>
