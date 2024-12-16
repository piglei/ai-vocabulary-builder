<script setup lang="ts">
import axios from 'axios'

import { computed, ref, reactive, onMounted, watch, nextTick, onUpdated, onUnmounted } from 'vue'
import { useVuelidate } from '@vuelidate/core'
import { required, maxLength, minLength } from '@vuelidate/validators'
import tippy from 'tippy.js';
import { JobStatus, playWord } from '@/common/basic';
import { notyf } from '@/common/ui';
import { exampleSentences, tokenizeText } from '@/common/text';
import 'tippy.js/dist/tippy.css';

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

// Common states for jobs: translation, extraction
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
const transResult = reactive({
	origText: '',
	translatedText: ''
})

// The word sample object which has been extracted and saved to the voc book.
const wordSample = reactive({
	word: '',
	word_normal: '',
	pronunciation: '',
	orig_text: '',
	translated_text: '',

	structured_definitions: [],
	simple_definition: ''
})

// The word that AI picked from the text via extraction
const aiPickedExistedWord = ref('')
// All the words which have been added to the vocabulary book in current session
const addedWords = reactive([])
// Add the words which have been added to the vocabulary book in the past
const existingWords = reactive([])
// Add the words which have been marked as mastered
const masteredWords = reactive([])

// Whether the user is in the mode of adding extra word instead of replacing the current one
const addExtraMode = ref(false)

function toggleAddExtraMode() {
	addExtraMode.value = !addExtraMode.value
}

const systemStatus = reactive({
	model_settings_initialized: true,
	version: '',
	new_version: null,
})

// Get the system status
async function getSystemStatus() {
	try {
		const response = await axios.get(window.API_ENDPOINT + '/api/system_status')
		const data = response.data
		Object.assign(systemStatus, data)
	} catch (error) {
		const msg = error.response ? error.response.data.message : error.message
		notyf.error('Failed to load system status, details: ' + msg)
	}
}

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
		liveTranslatedText.value += parsedData.translated_text
	})

	// Translation finished, set the text and start extracting
	source.addEventListener('translation', (event) => {
		const parsedData = JSON.parse(event.data)
		liveTranslatedText.value = parsedData.translated_text

		// Set global translated result
		transResult.origText = parsedData.text
		transResult.translatedText = parsedData.translated_text

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

    // Also get all known words from the text
    getKnownWords(state.userText)
}

// Get all known words from the text.
async function getKnownWords(text: string) {
    let resp
    try {
		resp = await axios.post(window.API_ENDPOINT + '/api/known_words/find_by_text/', {text: text})
		existingWords.length = 0
        existingWords.push(...resp.data.existing_words)
		masteredWords.length = 0
        masteredWords.push(...resp.data.mastered_words)
	} catch (error) {
        // Ignore error when unable to get known words
        console.log(error)
	}
}

// Extract the word automatically from the given text
async function extractWordSample(origText: string, translatedText: string) {
	extraStatus.value = JobStatus.Doing

	let resp
	try {
		resp = await axios.post(window.API_ENDPOINT + '/api/word_samples/extractions/', {
			orig_text: origText,
			translated_text: translatedText
		})

		aiPickedExistedWord.value = ''
	} catch (error) {
        if (!error.response) {
		    notyf.error('Error requesting API: ' + error.message)
		    extraStatus.value = JobStatus.NotStarted
            return
        }
        let data = error.response.data
        if (data.code === 'WORD_ALREADY_EXISTS') {
            aiPickedExistedWord.value = data.data
            extraStatus.value = JobStatus.NotStarted
            return
        }

		extraStatus.value = JobStatus.NotStarted
		notyf.error('Error requesting API: ' + data.message)
		return
	}

	if (resp.data.word_sample === undefined) {
		extraStatus.value = JobStatus.NotStarted
		notyf.error('Response is not valid JSON')
		return
	}

	// Update global state and notify user
	Object.assign(wordSample, resp.data.word_sample)
	const msg = `<strong>${wordSample.word}</strong> added, well done! 🎉`
	extraStatus.value = JobStatus.Done
	notyf.success({ message: msg, dismissible: true })
}

// Remove current word sample form the vocabulary book
async function removeWord() {
	// Remove the word sample first
	try {
		await axios.post(window.API_ENDPOINT + '/api/word_samples/deletion/', {
			mark_mastered: true,
			words: [wordSample.word]
		})

        // Fade out the card
        const card = document.querySelector('.extraction-card')
        if (card) {
            card.classList.add('removing')
            setTimeout(() => {
                wordSample.word = ''
				if (extraStatus.value === JobStatus.Done) {
					extraStatus.value = JobStatus.NotStarted
				}
            }, 500)
        } else {
            wordSample.word = ''
			if (extraStatus.value === JobStatus.Done) {
				extraStatus.value = JobStatus.NotStarted
			}
        }

		// Also get known words again because "mastered" words may change
		getKnownWords(state.userText)
	} catch (error) {
		// Ignore error when unable to delete
	}
}


// Save a word manually
async function saveWordManually(word: string, removeCurrent = false) {
	if (removeCurrent && wordSample.word !== '') {
		await removeWord()
	}

	extraStatus.value = JobStatus.Doing
	aiPickedExistedWord.value = ''

	// Save the word manually
	let resp
	try {
		resp = await axios.post(window.API_ENDPOINT + '/api/word_samples/manually_save/', {
			orig_text: transResult.origText,
			translated_text: transResult.translatedText,
			word: word
		})
	} catch (error) {
		const msg = error.response ? error.response.data.message : error.message
		extraStatus.value = JobStatus.NotStarted
		notyf.error('Error requesting API: ' + msg)
		return
	}

	// Update global state and notify user
	Object.assign(wordSample, resp.data.word_sample)

	const msg = `<strong>${wordSample.word}</strong> added, well done! 🎉`
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
	wordSample.word = ''
    aiPickedExistedWord.value = ''
    addedWords.splice(0, addedWords.length)
    existingWords.splice(0, existingWords.length)

	forceShowTextArea.value = false
}

// Add event listener for enter key press on the textarea
function handleKeyPress(event: KeyboardEvent) {
	if (event.key === 'Enter') {
		extractWord();
	}
}

// If the text param was provided by URL, start the extracting process right away
onMounted(() => {
	// Get system status
	getSystemStatus()

	const urlParams = new URLSearchParams(window.location.search)
	const textParam = urlParams.get('text')
	if (textParam) {
		state.userText = textParam
		extractWord()
	}
	const textarea = document.getElementById('input-text');
	if (textarea) {
		textarea.addEventListener('keypress', handleKeyPress);
	}
});

onUnmounted(() => {
	const textarea = document.getElementById('input-text');
	if (textarea) {
		textarea.removeEventListener('keypress', handleKeyPress);
	}
});

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

function saveManually(word: string) {
	saveWordManually(word, true)
}

// Add an extra word to the vocabulary book
function addExtraWord(word: string) {
	// Push current word sample to the addedWords list
	if (wordSample.word) {
		addedWords.push({
			word: wordSample.word,
			simple_definition: wordSample.simple_definition
		})
	}
	saveWordManually(word, false)
}

// Check if the word has been added to the vocabulary already
function wordIsAddedToVoc(word: string): boolean {
	if (wordSample.word.toLowerCase() === word.toLowerCase()) {
		return true;
	}
	return addedWords.some(addedWord => addedWord.word.toLowerCase() === word.toLowerCase());
}

// Check if the word has been marked as mastered
function wordIsMastered(word: string): boolean {
	return masteredWords.some(w => w.toLowerCase() === word.toLowerCase());
}

// Get the known word object if the word is known
function getExistingObj(word: string) {
    return existingWords.find(w => w.word.toLowerCase() === word.toLowerCase()) || null
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
		let item = {
			"token": token,
			"addedToVoc": false,
			"existingObj": null,
			"isMastered": false,
		}
        if (token.type !== 'word') {
		    return item
        }
		// When the word has been added to the vocabulary, mark it
		if (wordIsAddedToVoc(token.value)) {
			item.addedToVoc = true
			return item
		}
        let obj = getExistingObj(token.value)
        if (obj !== null) {
            item.existingObj = obj
            return item
        }
		if (wordIsMastered(token.value)) {
			item.isMastered = true
			return item
		}
		return item
	})
	return items
})

// Enable tippy instances for elements.
onUpdated(() => {
    nextTick(() => {
        tippy('.inputted-text-card span[data-tippy-content]', {delay: 300})
        tippy('.icon-action[data-tippy-content]', {delay: 300, placement: 'bottom'})
        tippy('.extraction-card span.normal-form[data-tippy-content]', {delay: 300, placement: 'bottom'})
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
						placeholder="Text containing new vocabulary."
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
					:class="{ disabled: anyInProgress || !systemStatus.model_settings_initialized }"
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
						<div class="mb-1">
							<span data-tippy-content="Choose from the words below." class="badge text-bg-primary">Select Manually</span>
						</div>
						<template v-for="(t, index) in tokenizedText" :key="index">
							<span v-if="t.token.type === 'delimiter'">
                                {{ t.token.value }}
                            </span>
                            <template v-else>
                                <span
                                    v-if="t.addedToVoc"
                                    class="added-voc-word" 
                                >
                                    {{ t.token.value }}
                                </span>
                                <span
                                    v-else-if="t.existingObj !== null"
                                    class="text-secondary existing-word" 
                                    data-tippy-content="This word is already in your vocabulary book."
                                    data-tippy-delay="1000"
                                >
                                    {{ t.token.value }}({{ t.existingObj.simple_definition }})
                                </span>
                                <span
                                    v-else-if="t.isMastered"
                                    class="text-secondary" 
                                    data-tippy-content='This word was previously marked as "mastered".'
                                    data-tippy-delay="1000"
                                >
                                    {{ t.token.value }}
                                </span>
                                <span
                                    v-else-if="addExtraMode"
                                    @click="addExtraWord(t.token.value)"
                                    class="word"
                                    data-tippy-content="📝 Add one MORE word"
                                    style="cursor: pointer"
                                >
                                    {{ t.token.value }}
                                </span>
                                <span
                                    v-else-if="!addExtraMode"
                                    @click="saveManually(t.token.value)"
                                    class="word"
                                    data-tippy-content="Select this word instead"
                                    style="cursor: pointer"
                                >
                                    {{ t.token.value }}
                                </span>
							</template>
						</template>
					</div>
				</div>
				<i class="bi bi-pencil-square icon-action btn btn-light" data-tippy-content="Edit" @click="toggleTextArea"></i>
				<i :class="['bi bi-file-plus icon-action btn', { 'btn-light': !addExtraMode, 'btn-primary': addExtraMode }]" data-tippy-content="Add an extra word" @click="toggleAddExtraMode"></i>
				<i class="bi bi-arrow-counterclockwise icon-action btn btn-light" data-tippy-content="Reset" @click="reset"></i>
		</div>
	</div>

	<div class="row mt-5">
		<div class="col-12" v-if="!transHasStarted">
			<div v-if="!systemStatus.model_settings_initialized" class="alert alert-danger mt-2" role="alert">
				<i class="bi bi-wrench-adjustable-circle"></i>
				The model settings has not been initialized. Please <router-link to="/app/settings">configure</router-link> it first.
			</div>

			<div class="card tips-placeholder">
				<div class="card-body">
					<p>✨ Harness the power of AI to build your personalized vocabulary list! -- Tips: </p>
					<ul>
					<li>Click the "Build" button after entering a sentence containing new words.
						<a
							href="javascript:void(0)"
							id="set-example-text"
							@click="setExampleText"
						>
							[example text]
						</a>
					</li>
					</ul>

					<div class="version-info" v-if="systemStatus.version">
						Version: {{ systemStatus.version }}
						<a 
							class="text-primary"
							v-if="systemStatus.new_version"
							href="https://github.com/piglei/ai-vocabulary-builder"
							target="_blank">
							&lt;⬆️ Upgrade to {{ systemStatus.new_version  }}&gt;
					    </a>
					</div>
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
					<span class="card-title-text">
						<i class="bi bi-robot"></i>
						Extracting...
					</span>
				</div>
				<div class="card-body">
					<div class="card-text placeholder-glow">
						<span class="placeholder col-12 placeholder-lg"></span>
						<span class="placeholder col-12 placeholder-sm"></span>
						<span class="placeholder col-12 placeholder-sm"></span>
					</div>
				</div>
			</div>

			<div class="card shadow-sm" v-if="aiPickedExistedWord">
				<div class="card-header">⚠️ Oops!</div>
				<div class="card-body">
                    <div class="card-text text-secondary">
                        <p>
                            AI picked <strong>"{{ aiPickedExistedWord }}"</strong>, but
                            it's already in your vocabulary book.
                        </p>
                        <p>
                            ⏫ Try select the word from above. ⏫
                        </p>
					</div>
				</div>
			</div>

			<div class="card extraction-card shadow-sm border-primary" v-if="extraStatus === JobStatus.Done">
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
						<h5>{{ wordSample.word }}
							<span
								:data-tippy-content='`The base form of "${wordSample.word}" is "${wordSample.word_normal}"`'
								v-if="wordSample.word !== wordSample.word_normal"
								class="normal-form text-secondary">
								({{ wordSample.word_normal }})
							</span>
						</h5>
						<p class="pron">
							{{ wordSample.pronunciation }}
							<i class="bi bi-volume-up ms-2" @click="playWord(wordSample.word)" style="cursor: pointer;"></i>
						</p>
						<p class="definition" v-for="def of wordSample.structured_definitions">
							<span v-if="def.part_of_speech" class="part-of-speech text-secondary">[{{ def.part_of_speech }}]</span>
							{{ def.definition }}
						</p>
					</div>
				</div>
			</div>

			<div v-for="word of addedWords" class="card shadow-sm mt-1" :key="word.word">
				<div class="card-header text-truncate">
					<i class="bi bi-bookmarks"></i>
					&nbsp;
					<span class="card-title-text">{{ word.word }}({{ word.simple_definition }})</span>
				</div>
			</div>
		</div>
	</div>

	</div>
</template>


<style type="texst/scss" scoped>
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

	.pron {
		font-size: 14px;
	}

	.definition {
		font-size: 14px;
		margin-bottom: 2px;
	}

	h5 span {
		font-weight: normal;
		font-size: 14px;
	}
}
.extraction-card.removing {
    animation: moveUpFadeOut 0.5s forwards;
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

	span.word {
		text-decoration: underline dotted;
		text-decoration-color: #d4d4d4;
	}

	span.word:hover {
		color: #007bff;
		text-decoration: underline;
	}

	span.added-voc-word {
		font-weight: bold;
		text-decoration: underline;
	}

	span.existing-word {
		margin: 0 6px;
		font-style: italic;
	}
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
	font-size: 16px;

	p {
		margin: 4px 0;
	}

	ul {
		margin-bottom: 0;
	}

	.version-info {
		margin-top: 2em;
		font-size: 13px;
		color: #999;
	}
}

.card-header.text-truncate {
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

@keyframes moveUpFadeOut {
    0% {
        opacity: 1;
        transform: translateY(0);
    }
    50% {
        opacity: 0.5;
        transform: translateY(-10px);
    }
    100% {
        opacity: 0;
        transform: translateY(-20px);
    }
}
</style>
