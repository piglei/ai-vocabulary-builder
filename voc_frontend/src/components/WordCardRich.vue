<template>
	<div :class="['word-card-rich card shadow-sm', borderClass]">
		<div class="card-body">
			<div class="card-text">
                <a
                    href="javascript:void(0)"
                    class="float-end"
                    style="font-size: 13px; margin-top: 2px"
                    @click="removeWordFunc(wordSample.word)"
                >
                    Remove
                </a>

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
				<p class="definition" v-for="def of wordSample.structured_definitions" :key="def.definition">
					<span v-if="def.part_of_speech" class="part-of-speech text-secondary">[{{ def.part_of_speech }}]</span>
					{{ def.definition }}
				</p>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue';
import { playWord } from '@/common/basic';

const props = defineProps({
	wordSample: {
		type: Object,
		required: true
	},
	borderClass: {
		type: String,
		default: ''
	},
	removeWordFunc: {
		type: Function,
		required: true
	}
});
</script>

<style scoped lang="scss">
.word-card-rich {
	width: calc(33% - 10px);
	box-sizing: border-box;
	margin-bottom: 10px;

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
</style>
