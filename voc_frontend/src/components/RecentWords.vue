<script lang="ts">
import axios from 'axios'
import { nextTick, onMounted, reactive } from 'vue'
import tippy from 'tippy.js'

export default {
    props: {},
    setup() {
        const words = reactive([])

        async function getRecentWords() {
            // Get the recent words from the server
            try {
                const response = await axios.get(window.API_ENDPOINT + '/api/word_samples/recent')
                words.length = 0
                words.push(...response.data.words)

                nextTick(() => {
                    tippy('.recent-word-cards i.word-card-info-icon[data-tippy-content]', {delay: 100})
                })
            } catch (error) {
                console.log(error)
            }
        }

        onMounted(() => {
            getRecentWords()
        })

        return {
            words
        }
    }
}
</script>

<template>
    <div class="recent-word-cards mt-2 mb-2">
        <div v-for="word of words" class="card border-info mb-3 word-card" :key="word.word">
            <div class="card-body">
                <h5 class="card-title">
                    {{ word.word }}
                    <i class="bi bi-info-circle float-end word-card-info-icon" :data-tippy-content="word.orig_text + ' / ' + word.translated_text"></i>
                </h5>
                <p class="card-text text-secondary">{{ word.simple_definition }}</p>
            </div>
        </div>
    </div>
</template>

<style scoped lang="scss">
.recent-word-cards {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;

    .word-card {
        width: calc(25% - 10px);
        box-sizing: border-box;
        margin-bottom: 10px;
        
        h5 {
            font-size: 18px;
            font-weight: normal;
        }
        .card-text {
            font-size: 13px;
        }
        
        i {
            font-size: 12px;
            cursor: pointer;
        }
    }
}
</style>