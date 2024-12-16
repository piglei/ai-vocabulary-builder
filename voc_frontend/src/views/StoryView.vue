<script setup lang="ts">
import { JobStatus } from '@/common/basic';
import { computed, reactive, ref, onUpdated, nextTick } from 'vue';
import tippy from 'tippy.js';
import LearnNav from '@/components/LearnNav.vue'
import { notyf } from '@/common/ui';

const writingStatus = ref(JobStatus.NotStarted)
const wordsNum = ref(6)
const story = ref('')
const words = reactive([])


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
    return story.value.replace(/\$(\w+)?\$/g, '<span class="word"><mark>$1</mark></span>')
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
                        :disabled="writingStatus === JobStatus.Doing"
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
    
        <div class="row mt-2" v-if="writingStatus !== JobStatus.NotStarted">
        
            <div class="cols-12">
                <hr class="mt-3"/>
                <div id="story" v-html="richStory"></div>
            
                <div class="word-cards mt-4">
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
            </div>
        </div>
    </div>
</template>

<style type="text/scss">
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
}
.word-card {
    width: calc(25% - 10px);
    box-sizing: border-box;
    margin-bottom: 10px;

    .card-text {
        font-size: 13px;
    }

    i {
        font-size: 12px;
        cursor: pointer;
    }
}
</style>
