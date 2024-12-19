<script setup lang="ts">
import 'bootstrap'
import axios from 'axios'

import { ref, onMounted, reactive } from 'vue'
import { notyf } from '@/common/ui';

const settings = reactive({
	model_provider: "",
	target_language: "",
	openai_config: {
		api_key: "",
		api_host: "",
		model: ""
	},
	gemini_config: {
		api_key: "",
		api_host: "",
		model: ""
	},
	anthropic_config: {
		api_key: "",
		api_host: "",
		model: ""
	}
})

// All available model options
const modelOptions = reactive({openai: [], gemini: []})
// All available target language options
const targetLanguageOptions = reactive([])

// The visibility of the API keys
// 
const showGeminiApiKey = ref(false);

const toggleGeminiApiKeyVisibility = () => {
	showGeminiApiKey.value = !showGeminiApiKey.value;
};

const showOpenAIApiKey = ref(false);

const toggleOpenAIApiKeyVisibility = () => {
	showOpenAIApiKey.value = !showOpenAIApiKey.value;
};

const showAnthropicApiKey = ref(false);

const toggleAnthropicApiKeyVisibility = () => {
	showAnthropicApiKey.value = !showAnthropicApiKey.value;
};


onMounted(() => {
	loadSettings()
})

// Load remote settings
async function loadSettings() {
	try {
		const response = await axios.get(window.API_ENDPOINT + '/api/settings')
		const data = response.data

		// Update the state
		Object.assign(settings, data.settings)
		Object.assign(modelOptions, data.model_options)
		targetLanguageOptions.length = 0
		targetLanguageOptions.push(...data.target_language_options)
	} catch (error) {
		const msg = error.response ? error.response.data.message : error.message
		notyf.error('Failed to load settings, details: ' + msg)
	}
}

// Submit the settings form
const handleSubmit = async (event: Event) => {
	event.preventDefault();
	
	try {
		await axios.post(window.API_ENDPOINT + '/api/settings', settings);
		notyf.success('Settings Updated.');
	} catch (error) {
		const msg = error.response ? error.response.data.message : error.message
		notyf.error('Failed, details: ' + msg);
	}
};

</script>

<template>
	<div class="row mt-4">
		<div class="col-12">
			<h4 class="me-1" style="display: inline-block">Settings</h4>
			<hr class="mt-1" />
			<form @submit="handleSubmit">
			<h5>General</h5>
				 <!-- Target Language select -->
				<div class="mb-3">
					<label for="target_language" class="form-label">Target Language <span class="text-danger">*</span></label>
					<select name="target_language" class="form-select" id="target_language" v-model="settings.target_language">
						<option value="">-- Select --</option>
						<option v-for="o of targetLanguageOptions" :value="o.code" :key="o.code">{{ o.name }}</option>
					</select>
					<div class="form-text">
						All content and vocabulary you enter will be translated into this language.
					</div>
				</div>
			<h5 class="mt-4">AI Model</h5>
				<!-- Model Provider select -->
				<div class="mb-3">
					<label for="model_provider" class="form-label">Model Provider  <span class="text-danger">*</span></label>
					<select name="model_provider" class="form-select" id="model_provider" v-model="settings.model_provider">
						<option value="">-- Select --</option>
						<option value="openai">OpenAI API</option>
						<option value="gemini">Google Gemini</option>
						<option value="anthropic">Anthropic</option>
					</select>
				</div>
				
				<!-- The OpenAI configs -->
				<div v-if="settings.model_provider === 'openai'">
					<div class="mb-3">
						<label for="openai_api_key" class="form-label">API Key <span class="text-danger">*</span></label>
						<div class="input-group">
							<input :type="showOpenAIApiKey ? 'text' : 'password'" class="form-control" id="openai_api_key" name="openai_api_key" v-model="settings.openai_config.api_key" placeholder="">
							<button type="button" class="btn btn-outline-secondary" @click="toggleOpenAIApiKeyVisibility">{{ showOpenAIApiKey ? 'Hide' : 'Show' }}</button>
						</div>
					</div>
					<div class="mb-3">
						<label for="openai_api_host" class="form-label">API Host</label>
						<input class="form-control" id="openai_api_host" name="openai_api_host" v-model="settings.openai_config.api_host" placeholder="">
						<div class="form-text">
							Optional, the default value is <a href="https://api.openai.com/v1">https://api.openai.com/v1</a>
						</div>
					</div>
					<div class="mb-3">
						<label for="openai_model" class="form-label">Model  <span class="text-danger">*</span></label>
						<select name="openai_model" class="form-select" v-model="settings.openai_config.model">
							<option v-for="o of modelOptions.openai" :key="o" :value="o">{{ o }}</option>
						</select>
					</div>
				</div>
				
				<!-- The Gemini configs -->
				<div v-show="settings.model_provider === 'gemini'">
					<div class="mb-3">
						<label for="gemini_api_key" class="form-label">API Key <span class="text-danger">*</span></label>
						<div class="input-group">
							<input :type="showGeminiApiKey ? 'text' : 'password'" class="form-control" id="gemini_api_key" name="gemini_api_key" v-model="settings.gemini_config.api_key" placeholder="">
							<button type="button" class="btn btn-outline-secondary" @click="toggleGeminiApiKeyVisibility">{{ showGeminiApiKey ? 'Hide' : 'Show' }}</button>
						</div>
						<div class="form-text">
							<a href="https://aistudio.google.com/" target="_blank">Get API key in Google AI Studio</a>
						</div>
					</div>
					<div class="mb-3">
						<label for="gemini_api_host" class="form-label">API Host</label>
						<input class="form-control" id="gemini_api_host" name="gemini_api_host" v-model="settings.gemini_config.api_host" placeholder="">
						<div class="form-text">
							Optional, the default value is <a href="https://generativelanguage.googleapis.com">https://generativelanguage.googleapis.com</a>
						</div>
					</div>
					<div class="mb-3">
						<label for="gemini_model" class="form-label">Model  <span class="text-danger">*</span></label>
						<select name="gemini_model" class="form-select" v-model="settings.gemini_config.model">
							<option v-for="o of modelOptions.gemini" :key="o" :value="o">{{ o }}</option>
						</select>
					</div>
				</div>

				<!-- The Anthropic configs -->
				<div v-show="settings.model_provider === 'anthropic'">
					<div class="mb-3">
						<label for="anthropic_api_key" class="form-label">API Key <span class="text-danger">*</span></label>
						<div class="input-group">
							<input :type="showAnthropicApiKey ? 'text' : 'password'" class="form-control" id="anthropic_api_key" name="anthropic_api_key" v-model="settings.anthropic_config.api_key" placeholder="">
							<button type="button" class="btn btn-outline-secondary" @click="toggleAnthropicApiKeyVisibility">{{ showAnthropicApiKey ? 'Hide' : 'Show' }}</button>
						</div>
					</div>
					<div class="mb-3">
						<label for="anthropic_api_host" class="form-label">API Host</label>
						<input class="form-control" id="anthropic_api_host" name="anthropic_api_host" v-model="settings.anthropic_config.api_host" placeholder="">
						<div class="form-text">
							Optional, the default value is <a href="https://api.anthropic.com">https://api.anthropic.com</a>
						</div>
					</div>
					<div class="mb-3">
						<label for="anthropic_model" class="form-label">Model  <span class="text-danger">*</span></label>
						<select name="anthropic_model" class="form-select" v-model="settings.anthropic_config.model">
							<option v-for="o of modelOptions.anthropic" :key="o" :value="o">{{ o }}</option>
						</select>
					</div>
				</div>

				<button
				type="submit"
				class="btn btn-primary"
				>
				Save
			</button>
		</form>
		
	</div>
</div>
</template>

<style>
</style>
