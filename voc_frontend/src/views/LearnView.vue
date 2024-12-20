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
		tippy('.word-extra-info span[data-tippy-content]', {delay: 100})
		
		// Initialize tippy for confirmation
		tippy('.action-panel a.mark-mastered', {
			content: '<div class="mb-1">Marking a word as "Mastered" will prevent it from appearing again when building vocabularies.</div><br><button class="btn btn-sm btn-danger confirm-btn">Confirm</button>',
			trigger: 'click',
			interactive: true,
			allowHTML: true,
			appendTo: document.body,
			onShow(instance) {
				const confirmButton = instance.popper.querySelector('.confirm-btn');
				if (confirmButton) {
					confirmButton.onclick = () => {
						const word = instance.reference.getAttribute('data-word');
						removeWord(word, true);
						instance.hide();
					};
				}
			}
		});
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
async function removeWord(word, markMastered) {
	try {
		await axios.post(window.API_ENDPOINT + '/api/word_samples/deletion/', {
			mark_mastered: markMastered,	
			words: [word]}
		)
	} catch (error) {
		const msg = error.resposne ? error.response.data.message : error.message
		notyf.error('Error requesting API: ' + msg)
		return
	}
	
	// Remove it from local memory
	words.value = words.value.filter((obj) => obj.ws.word !== word)
	count.value = words.value.length
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
							<col span="1" style="width: 140px" />
							<col span="1" />
							<col span="1" />
							<col span="1" style="width: 100px" />
						</colgroup>
						
						<tbody>
							<tr v-for="word of words" :key="word.ws.word" class="word-row">
								<td>
									<div class="word mb-1">
										{{ word.ws.word }}
										<i class="bi bi-volume-up ms-2" @click="playWord(word.ws.word)" style="cursor: pointer;"></i>
									</div>
									<div class="pronun text-secondary">{{ word.ws.pronunciation }}</div>
								</td>
								<td>
									<p class="definition" v-for="def of word.ws.structured_definitions">
										<span v-if="def.part_of_speech" class="part-of-speech text-secondary">[{{ def.part_of_speech }}]</span>
										{{ def.definition }}
									</p>
								</td>
								<td>
									<p class="mb-2">{{ word.ws.orig_text }}</p>
									<p class="text-secondary mt-1 mb-1">{{ word.ws.translated_text }}</p>
									<p class="word-extra-info text-secondary mt-2">
										<i class="bi bi-calendar"></i>
										<span class="ms-2" :data-tippy-content="word.dateAdded.toISO()">Added {{ word.dateAdded.toRelativeCalendar() }}</span>
									</p>
								</td>
								<td>
									<div class="action-panel">
										<a class="me-2 mark-mastered" title='Mark as "mastered"' :data-word="word.ws.word">
											<i class="bi bi-check-circle"></i>
										</a>
										<div class="dropdown">
											<a href="javascript:void(0)" class="dropdown-toggle no-caret" data-bs-toggle="dropdown" aria-expanded="false">
												<i class="bi bi-three-dots"></i>
											</a>
											<ul class="dropdown-menu">
												<li>
													<a class="dropdown-item" href="javascript:void(0)" @click="removeWord(word.ws.word, false)">
														<i class="bi bi-trash"></i> Remove
													</a>
												</li>
											</ul>
										</div>
									</div>
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

<style lang="scss">
.words-list {
	font-size: 14px;
	.word {
		font-size: 18px;
		font-weight: 500;
	}
	.proun {
		font-size: 13px;
	}
	p.definition {
		margin-bottom: 2px;
	}
	.word-extra-info {
		font-size: 13px;
		margin-bottom: 0;
	}
	td {
		padding-top: 13px;
		padding-bottom: 13px;
	}
	td:first-child {
		padding-left: 24px;
	}
	td:last-child {
		padding-right: 24px;
	}

	.dropdown {
		display: inline-block;
		.dropdown-item {
			font-size: 14px;
			color: #007bff;
		}
	}
}
.action-panel {
	font-size: 18px;
	text-align: right;
	i {
		cursor: pointer;
	}
}
.no-caret::after {
	display: none;
}
</style>
