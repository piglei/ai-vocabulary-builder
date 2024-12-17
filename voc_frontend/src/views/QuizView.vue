<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import axios from 'axios'
import LearnNav from '@/components/LearnNav.vue'
import { playWord } from '@/common/basic'
import { notyf } from '@/common/ui';


enum quizStatusEnum {
    NotStarted = 'notStarted',
    Doing = 'doing',
    Done = 'done'
}

const quizStatus = ref(quizStatusEnum.NotStarted)
const modeAvailable = ref(false)

const wordsNum = ref(5)
const quizWords = reactive([])

const currentQuizWord = ref(null)
const currentQuizChoices = ref([])
const currentQuizIndex = ref(null)

const showOrigText = ref(false);

// Get the mode available status from the server
async function getModeAvailableStatus() {
	try {
		const response = await axios.get(window.API_ENDPOINT + '/api/system_status')
        modeAvailable.value = response.data.quiz_mode_available
	} catch (error) {
        console.log(error)
	}
}

// Get the words from the server
async function getQuizWords(wordsNum) {
    try {
        // Send wordsNum to the server as GET params
        const response = await axios.get(window.API_ENDPOINT + '/api/quiz/words/', {
            params: { words_num: wordsNum.value }
        })
        const data = response.data
        return data
    } catch (error) {
        const msg = error.response ? error.response.data.message : error.message
        notyf.error('Failed to load settings, details: ' + msg)
        return null
    }
}

// Start a quiz
async function startQuiz() {
    const words = await getQuizWords(wordsNum)
    if (!words) {
        return
    }

    quizWords.length = 0
    quizWords.push(...words)
    currentQuizIndex.value = 1
    currentQuizWord.value = quizWords[0]
    prepareChoices()

    quizStatus.value = quizStatusEnum.Doing
}

// Check if the selected choice is correct, the index is the index of the choice
// in the choices array.
function checkAnswer(index) {
    const isCorrect = currentQuizChoices.value[index] === currentQuizWord.value.simple_definition;
    const selectedChoiceElement = document.querySelectorAll('.list-group-item')[index]

    if (!isCorrect) {
        // Add a class to the selected choice to indicate it's wrong
        selectedChoiceElement.classList.add('list-group-item-danger')
        selectedChoiceElement.classList.add('bounce')
        setTimeout(() => {
            selectedChoiceElement.classList.remove('bounce')
        }, 1000);
    } else {
        moveToNextWord()
    }
}

// Move to the next word in the quiz
function moveToNextWord() {
    if (currentQuizIndex.value >= quizWords.length) {
        quizStatus.value = quizStatusEnum.Done
        return
    }
    currentQuizIndex.value++;
    currentQuizWord.value = quizWords[currentQuizIndex.value - 1];
    prepareChoices()
}

// Prepare the choices, generate choices and reset the style and state if needed.
function prepareChoices() {
    currentQuizChoices.value = getQuizChoices();
    showOrigText.value = false;
    // Reset the choice colors
    document.querySelectorAll('.list-group-item').forEach(el => el.classList.remove('list-group-item-danger'))
}

// Get the choices for the current quiz word
function getQuizChoices() {
    const choices = [];
    const randomIndices = new Set();

    while (randomIndices.size < 3) {
        const randomIndex = Math.floor(Math.random() * quizWords.length);
        if (randomIndex !== currentQuizIndex.value - 1) {
            randomIndices.add(randomIndex);
        }
    }

    randomIndices.forEach(index => {
        choices.push(quizWords[index].simple_definition);
    });

    choices.push(currentQuizWord.value.simple_definition);

    // Shuffle the choices array
    for (let i = choices.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [choices[i], choices[j]] = [choices[j], choices[i]];
    }
    return choices;
}

onMounted(() => {
    getModeAvailableStatus()
})

function toggleOrigText() {
    showOrigText.value = !showOrigText.value;
}
</script>

<template>
    <div>
        <div class="row mt-4">
            <div class="col-12">
                <LearnNav activePanel="quiz" />
            </div>
        </div>
        <div class="row mt-2">
            <div class="cols-12">
                <div class="alert alert-info mt-2" role="alert">
                    Master words through quizzes!
                </div>
                
                <div class="d-flex align-items-center">
                    <button
                        type="button"
                        class="btn btn-primary"
                        id="start-quiz"
                        :class="{ 'disabled': !modeAvailable }"
                        @click="startQuiz"
                    >
                        <i class="bi bi-pencil"></i>
                        Start Quiz
                    </button>
                    <span class="ms-4">Use</span>
                    <select class="form-select ms-2" v-model="wordsNum" style="width: 100px;">
                        <option value="5">5</option>
                        <option value="10">10</option>
                        <option value="25">25</option>
                        <option value="50">50</option>
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

                <div id="quiz-word-card" v-if="quizStatus === quizStatusEnum.Doing">
                    <h4>
                        {{ currentQuizWord.word }}
						<i class="bi bi-volume-up ms-2" @click="playWord(currentQuizWord.word)" style="cursor: pointer;"></i>
                    </h4>
                    <div>{{ currentQuizWord.pronunciation }}</div>
                    <p class="mt-2 mb-1 word-orig-text" v-if="showOrigText">{{ currentQuizWord.orig_text }}</p>
                    <a class="mb-2" href="javascript:void(0)" @click="toggleOrigText">
                        {{ showOrigText ? 'hide example' : 'show example' }}
                    </a>
                    <div class="choices list-group">
                        <a 
                            href="javascript:void(0)"
                            v-for="choice, i of currentQuizChoices"
                            class="list-group-item list-group-item-action"
                            @click="checkAnswer(i)"
                            :key="i"
                        >
                            {{ choice }}
                        </a>
                    </div>
                    <div class="quiz-progress">
                        {{ currentQuizIndex }} / {{ quizWords.length }}
                    </div>
                </div>

                <div id="quiz-finished" v-if="quizStatus === quizStatusEnum.Done">
                    <i class="bi bi-trophy-fill celebration-icon"></i>
                    <h3>Congratulation!</h3>
                    <div>You've completed all the quizzes!</div>
                </div>
            </div>
        </div>
    </div>
</template>

<style lang="scss">
#quiz-word-card {
    background-color: #f4f4f4;
    padding: 16px 26px;
    font-size: 16px;
    line-height: 28px;

    .choices {
        margin-top: 14px;
    }

    .choices a {
        padding: 12px 8px;
        font-size: 16px;
    }
}
.bounce {
    animation: bounce 1s;
}

@keyframes bounce {
    0%, 20%, 50%, 80%, 100% {
        transform: translateY(0);
    }
    40% {
        transform: translateY(-30px);
    }
    60% {
        transform: translateY(-15px);
    }
}

#quiz-finished {
    text-align: center;

    .celebration-icon {
        font-size: 100px;
        color: gold;
        animation: pop-in 1s ease-out;
    }
}

@keyframes pop-in {
    0% {
        transform: scale(0);
        opacity: 0;
    }
    100% {
        transform: scale(1);
        opacity: 1;
    }
}

.quiz-progress {
    text-align: center;
    margin-top: 20px;
    font-size: 18px;
    font-weight: bold;
}
</style>
