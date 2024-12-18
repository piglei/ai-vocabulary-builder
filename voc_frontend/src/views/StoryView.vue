<script setup lang="ts">
import { JobStatus } from '@/common/basic';
import { computed, reactive, ref, onUpdated, nextTick, onMounted } from 'vue';
import tippy from 'tippy.js';
import LearnNav from '@/components/LearnNav.vue'
import { notyf } from '@/common/ui';
import axios from 'axios';

const writingStatus = ref(JobStatus.NotStarted)
const wordsNum = ref(6)
const story = ref('')
const words = reactive([])

const modeAvailable = ref(false);

// Get the mode available status from the server
async function getModeAvailableStatus() {
    try {
        const response = await axios.get(window.API_ENDPOINT + '/api/system_status')
        modeAvailable.value = response.data.story_mode_available
    } catch (error) {
        console.log(error)
    }
}

onMounted(() => {
    getModeAvailableStatus()
})

function writeStory() {
    writingStatus.value = JobStatus.Doing
    story.value = ''
    
    // Create the SSE stream
    const source = new EventSource(
    window.API_ENDPOINT + '/api/stories/?words_num=' + wordsNum.value
    )
    
    source.addEventListener('story_partial', (event) => {
        story.value = event.data
    })
    
    // Story is done
    source.addEventListener('story', (event) => {
        story.value = event.data
        writingStatus.value = JobStatus.Done
    })
    
    // Words used for this story received
    source.addEventListener('words', (event) => {
        const parsedData = JSON.parse(event.data)
        words.length = 0
        words.push(...parsedData)
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
        writingStatus.value = JobStatus.Done
    }
}

// Replace the special word markers with HTML tags.
const richStory = computed(() => {
    return story.value
        .replace(/\$(\w+)?\$/g, '<span class="word"><mark>$1</mark></span>')
        .replace(/\n/g, '<br>')
})


// Enable tippy instances for elements.
onUpdated(() => {
    nextTick(() => {
        tippy('i.word-card-info-icon[data-tippy-content]', {delay: 100})
    })
})
</script>

<template>
    <div>
        <div class="row mt-4">
            <div class="col-12">
                <LearnNav activePanel="story" />
            </div>
        </div>
        <div class="row mt-2">
            <div class="cols-12">
                <div class="alert alert-info mt-2" role="alert">
                    Read stories, master vocabulary!
                </div>
                
                <div class="d-flex align-items-center">
                    <button
                    type="button"
                    class="btn btn-primary"
                    id="write-story"
                    @click="writeStory"
                    :disabled="writingStatus === JobStatus.Doing || !modeAvailable"
                    >
                    <i class="bi bi-book"></i>
                    Write Me a Story
                </button>
                <span class="ms-4">Use</span>
                <select class="form-select ms-2" v-model="wordsNum" style="width: 100px;">
                    <option value="6">6</option>
                    <option value="12">12</option>
                    <option value="24">24</option>
                </select>
                <span class="ms-2">Words</span>
            </div>
        </div>
    </div>
    
    <div class="row">
        <div class="cols-12">
            <hr class="mt-3"/>
            <div v-if="!modeAvailable" class="alert alert-danger mt-2" role="alert">
                You don't have enough words yet. Gather some more and come back!
            </div>
            <div v-if="writingStatus !== JobStatus.NotStarted">
                <div id="story" v-html="richStory"></div>
                
                <h5 class="mt-3 mb-1">Words Used</h5>
                <div class="word-cards mt-2">
                    <div v-for="word of words" class="card border-info word-card" :key="word.word">
                        <div class="card-body">
                            <h5 class="card-title">
                                {{ word.word }}
                                <i class="bi bi-info-circle float-end word-card-info-icon" :data-tippy-content="word.orig_text + ' / ' + word.translated_text"></i>
                            </h5>
                            <p class="card-text text-secondary">{{ word.simple_definition }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
</template>

<style lang="scss">
#story {
    background-color: #f3f3f3;
    padding: 26px 16px;
    font-size: 16px;
    line-height: 28px;
    
    .word {
        font-weight: bold;
    }
}

.word-cards {
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

@media (min-width: 960px) {
    .word-cards {
        .word-card {
            width: calc(16.66% - 10px); // 6 cards in a row
        }
    }
}
</style>
