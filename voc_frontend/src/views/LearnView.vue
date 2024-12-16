<script setup lang="ts">
import 'bootstrap'
import axios from 'axios'

import { ref, onMounted, onUpdated, nextTick } from 'vue'
import { DateTime } from 'luxon'
import tippy from 'tippy.js';
import LearnNav from '@/components/LearnNav.vue'
import { playWord } from '@/common/basic'
import { notyf } from '@/common/ui';


const words = ref([])
const count = ref(0)

onMounted(() => {
	getWords()
})

onUpdated(() => {
	nextTick(() => {
		tippy('span[data-tippy-content]', {delay: 100})
	})
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
		await axios.post(window.API_ENDPOINT + '/api/word_samples/deletion/', {words: [word]})
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

// Method to handle export
function exportWords() {
	window.open(window.API_ENDPOINT + '/api/word_samples/export/', '_blank')
}

</script>

<template>
	<div>
		<div class="row mt-4">
				<div class="col-12">
						<LearnNav activePanel="words" />                
				</div>
		</div>
		<div class="row">
			<div class="col-12">
				<div>
					<div class="alert alert-info mt-3 mb-1">
						<span>You've added <strong>{{ count }}</strong> words so far, keep going!</span>
					</div>
					<div class="d-flex justify-content-end mt-3 mb-2">
						<button class="btn btn-sm btn-primary" @click="exportWords">Export (.csv)</button>
					</div>
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
									<div class="word mb-1">
										{{ word.ws.word }}
										<i class="bi bi-volume-up ms-2" @click="playWord(word.ws.word)" style="cursor: pointer;"></i>
									</div>
									<div class="pronun text-secondary">{{ word.ws.pronunciation }}</div>
								</td>
								<td>{{ word.ws.word_meaning }}</td>
								<td>
									{{ word.ws.orig_text }} /
									<span class="text-secondary">{{ word.ws.translated_text }}</span>
								</td>
								<td>
									<span :data-tippy-content="word.dateAdded.toISO()">
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
				<div></div>
			</div>
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
