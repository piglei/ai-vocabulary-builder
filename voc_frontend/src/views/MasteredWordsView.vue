<script setup lang="ts">
import axios from 'axios'

import { reactive, onMounted } from 'vue';
import LearnNav from '@/components/LearnNav.vue'
import { notyf } from '@/common/ui';

const masteredWords = reactive([])

// Get mastered words from the server
async function getMasteredWords() {
	try {
		const response = await axios.get(window.API_ENDPOINT + '/api/mastered_words/')
		const data = response.data

        masteredWords.length = 0
        masteredWords.push(...data.words)
	} catch (error) {
		const msg = error.response ? error.response.data.message : error.message
		notyf.error('Failed to load mastered words, detail: ' + msg)
	}
}

// Delete a mastered word
async function deleteMasteredWord(word) {
    try {
        await axios.post(window.API_ENDPOINT + '/api/mastered_words/deletion/', { words: [word]})

        // Remove the word from the masteredWords list.
        const index = masteredWords.indexOf(word)
        if (index > -1) {
            masteredWords.splice(index, 1)
        }
    } catch (error) {
        const msg = error.response ? error.response.data.message : error.message
        notyf.error('Failed to delete mastered word, detail: ' + msg)
    }
}

onMounted(() => {
    getMasteredWords()
})

</script>

<template>
    <div>
        <div class="row mt-4">
            <div class="col-12">
                <LearnNav activePanel="more" />                
            </div>
        </div>
        <div class="row mt-2">
            <div class="cols-12">
                <div class="alert alert-info mt-2" role="alert">
                    Words marked as "mastered" will not appear when building the vocabulary. When an AI-selected word is manually removed, it is flagged as "mastered."
                </div>
            </div>
        </div>
    
        <div class="row mt-2">
            <div class="cols-12">
                <hr class="mt-3"/>

                <div class="text-secondary" v-if="masteredWords.length === 0">No mastered words.</div>

                <div class="word-cards mt-4">
                    <div v-for="word of masteredWords" class="card border-secondary-subtle mb-3 word-card" :key="word">
                        <div class="card-body d-flex">
                            {{ word }}
                            <i class="bi bi-trash recycle-icon text-primary" @click="deleteMasteredWord(word)"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style lang="scss">
.word-cards {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.word-card {
    position: relative;
    width: calc(16.6% - 6px);
    box-sizing: border-box;
    margin-bottom: 10px;
    font-size: 14px;
    word-break: break-word;
}
.recycle-icon {
    position: absolute;
    top: 8px;
    right: 8px;
    display: none;
    cursor: pointer;
}
.word-card:hover .recycle-icon {
    display: inline;
}
</style>
