<script lang="ts">
export default {
  name: 'SettingsView'
}
</script>

<script setup lang="ts">
import 'bootstrap'
import 'choices.js/public/assets/styles/choices.css'

import axios from 'axios'
import Choices from 'choices.js'

import { ref, onMounted, onBeforeUnmount, reactive, nextTick, type Ref } from 'vue'
import { notyf } from '@/common/ui'

type ModelProvider = 'openai' | 'gemini' | 'anthropic' | 'deepseek'

interface ModelConfig {
  api_key: string
  api_host: string
  model: string
}

interface Settings {
  model_provider: ModelProvider | ''
  target_language: string
  openai_config: ModelConfig
  gemini_config: ModelConfig
  anthropic_config: ModelConfig
  deepseek_config: ModelConfig
}

interface ModelChoice {
  value: string
  label: string
  selected?: boolean
  placeholder?: boolean
}

interface TargetLanguageOption {
  code: string
  name: string
}

interface ErrorWithMessage {
  message?: string
  response?: {
    data?: {
      message?: string
    }
  }
}

const settings = reactive<Settings>({
  model_provider: '',
  target_language: '',
  openai_config: {
    api_key: '',
    api_host: '',
    model: ''
  },
  gemini_config: {
    api_key: '',
    api_host: '',
    model: ''
  },
  anthropic_config: {
    api_key: '',
    api_host: '',
    model: ''
  },
  deepseek_config: {
    api_key: '',
    api_host: '',
    model: ''
  }
})

// All available model options
const modelOptions = reactive<Record<ModelProvider, string[]>>({
  openai: [],
  gemini: [],
  anthropic: [],
  deepseek: []
})
// All available target language options
const targetLanguageOptions = reactive<TargetLanguageOption[]>([])

const openaiModelSelect = ref<HTMLSelectElement | null>(null)
const geminiModelSelect = ref<HTMLSelectElement | null>(null)
const anthropicModelSelect = ref<HTMLSelectElement | null>(null)
const deepseekModelSelect = ref<HTMLSelectElement | null>(null)

const modelProviders: ModelProvider[] = ['openai', 'gemini', 'anthropic', 'deepseek']
const modelSelectRefs: Record<ModelProvider, Ref<HTMLSelectElement | null>> = {
  openai: openaiModelSelect,
  gemini: geminiModelSelect,
  anthropic: anthropicModelSelect,
  deepseek: deepseekModelSelect
}
const modelChoiceInstances = new Map<ModelProvider, Choices>()
const modelChoiceHandlers = new Map<ModelProvider, (event: Event) => void>()
const modelFetchInProgress = reactive<Record<ModelProvider, boolean>>({
  openai: false,
  gemini: false,
  anthropic: false,
  deepseek: false
})

// The visibility of the API keys
//
const showGeminiApiKey = ref(false)

const toggleGeminiApiKeyVisibility = () => {
  showGeminiApiKey.value = !showGeminiApiKey.value
}

const showOpenAIApiKey = ref(false)

const toggleOpenAIApiKeyVisibility = () => {
  showOpenAIApiKey.value = !showOpenAIApiKey.value
}

const showAnthropicApiKey = ref(false)

const toggleAnthropicApiKeyVisibility = () => {
  showAnthropicApiKey.value = !showAnthropicApiKey.value
}

const showDeepSeekApiKey = ref(false)

const toggleDeepSeekApiKeyVisibility = () => {
  showDeepSeekApiKey.value = !showDeepSeekApiKey.value
}

onMounted(() => {
  initModelChoices()
  loadSettings()
})

onBeforeUnmount(() => {
  destroyModelChoices()
})

function getModelConfig(provider: ModelProvider): ModelConfig {
  switch (provider) {
    case 'openai':
      return settings.openai_config
    case 'gemini':
      return settings.gemini_config
    case 'anthropic':
      return settings.anthropic_config
    case 'deepseek':
      return settings.deepseek_config
  }
}

function getErrorMessage(error: unknown): string {
  const err = error as ErrorWithMessage

  return err.response?.data?.message ?? err.message ?? 'Unknown error'
}

// Build the list consumed by Choices.js. The currently saved/custom model is
// prepended when it is not in the fetched model list, so loading settings never
// drops a valid user-entered value.
function buildModelChoices(provider: ModelProvider): ModelChoice[] {
  const selectedModel = getModelConfig(provider).model
  const models = [...modelOptions[provider]]

  if (selectedModel !== '' && !models.includes(selectedModel)) {
    models.unshift(selectedModel)
  }

  return [
    {
      value: '',
      label: 'Enter or select a model',
      selected: selectedModel === '',
      placeholder: true
    },
    ...models.map((model) => ({
      value: model,
      label: model,
      selected: model === selectedModel
    }))
  ]
}

// Full-page sync used after loadSettings(): remote settings update the reactive
// state first, then Choices gets rebuilt from that state for every provider.
function syncModelChoices(): void {
  modelProviders.forEach((provider) => {
    const choices = modelChoiceInstances.get(provider)

    if (!choices) {
      return
    }

    choices.setChoices(buildModelChoices(provider), 'value', 'label', true, true, true)
  })
}

// Targeted sync used after fetchModels(): only the provider whose remote model
// list changed needs its Choices options rebuilt.
function syncProviderModelChoices(provider: ModelProvider): void {
  const choices = modelChoiceInstances.get(provider)

  if (!choices) {
    return
  }

  choices.setChoices(buildModelChoices(provider), 'value', 'label', true, true, true)
}

// Fetch button flow:
// 1. Read the current unsaved API key/host from the active provider config.
// 2. Ask the backend to call the provider's models API to avoid browser CORS issues.
// 3. Store the returned ids in modelOptions, then refresh that provider's Choices list.
async function fetchModels(provider: ModelProvider): Promise<void> {
  const config = getModelConfig(provider)

  if (!config.api_key) {
    notyf.error('Please enter API Key before fetching models.')
    return
  }

  modelFetchInProgress[provider] = true

  try {
    const response = await axios.post(window.API_ENDPOINT + '/api/settings/model-options', {
      provider,
      api_key: config.api_key,
      api_host: config.api_host
    })
    const models = response.data.models ?? []

    if (models.length === 0) {
      throw new Error('No models were returned by the provider.')
    }

    modelOptions[provider] = models
    syncProviderModelChoices(provider)
    notyf.success(`Fetched ${models.length} models.`)
  } catch (error) {
    const msg = getErrorMessage(error)
    notyf.error('Failed to fetch models, details: ' + msg)
  } finally {
    modelFetchInProgress[provider] = false
  }
}

// Choices owns the visible model controls. Its change event writes back into
// settings so the existing Save flow can submit the same settings object.
function initModelChoices(): void {
  modelProviders.forEach((provider) => {
    const element = modelSelectRefs[provider].value

    if (!element || modelChoiceInstances.has(provider)) {
      return
    }

    const handler = (event: Event) => {
      getModelConfig(provider).model = (event.target as HTMLSelectElement).value
    }

    element.addEventListener('change', handler)
    modelChoiceHandlers.set(provider, handler)

    modelChoiceInstances.set(
      provider,
      new Choices(element, {
        addChoices: true,
        allowHTML: false,
        allowHtmlUserInput: false,
        duplicateItemsAllowed: false,
        itemSelectText: '',
        noResultsText: 'No models found. Press Enter to use this value.',
        placeholder: true,
        searchEnabled: true,
        shouldSort: false
      })
    )
  })
}

// Choices attaches DOM/event state outside Vue's reactivity, so clean it up
// explicitly when this view is unmounted.
function destroyModelChoices(): void {
  modelProviders.forEach((provider) => {
    const element = modelSelectRefs[provider].value
    const handler = modelChoiceHandlers.get(provider)
    const choices = modelChoiceInstances.get(provider)

    if (element && handler) {
      element.removeEventListener('change', handler)
    }

    choices?.destroy()
  })

  modelChoiceHandlers.clear()
  modelChoiceInstances.clear()
}

// Load remote settings
async function loadSettings() {
  try {
    const response = await axios.get(window.API_ENDPOINT + '/api/settings')
    const data = response.data

    // Update the state
    Object.assign(settings, data.settings)
    targetLanguageOptions.length = 0
    targetLanguageOptions.push(...data.target_language_options)
    await nextTick()
    syncModelChoices()
  } catch (error) {
    const msg = getErrorMessage(error)
    notyf.error('Failed to load settings, details: ' + msg)
  }
}

// Submit the settings form
const handleSubmit = async (event: Event) => {
  event.preventDefault()

  try {
    await axios.post(window.API_ENDPOINT + '/api/settings', settings)
    notyf.success('Settings Updated.')
  } catch (error) {
    const msg = getErrorMessage(error)
    notyf.error('Failed, details: ' + msg)
  }
}
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
          <label for="target_language" class="form-label"
            >Target Language <span class="text-danger">*</span></label
          >
          <select
            name="target_language"
            class="form-select"
            id="target_language"
            v-model="settings.target_language"
          >
            <option value="">-- Select --</option>
            <option v-for="o of targetLanguageOptions" :value="o.code" :key="o.code">
              {{ o.name }}
            </option>
          </select>
          <div class="form-text">
            All content and vocabulary you enter will be translated into this language.
          </div>
        </div>
        <h5 class="mt-4">AI Model</h5>
        <!-- Model Provider select -->
        <div class="mb-3">
          <label for="model_provider" class="form-label"
            >Model Provider <span class="text-danger">*</span></label
          >
          <select
            name="model_provider"
            class="form-select"
            id="model_provider"
            v-model="settings.model_provider"
          >
            <option value="">-- Select --</option>
            <option value="openai">OpenAI API</option>
            <option value="gemini">Google Gemini</option>
            <option value="anthropic">Anthropic</option>
            <option value="deepseek">DeepSeek</option>
          </select>
        </div>

        <!-- The OpenAI configs -->
        <div v-show="settings.model_provider === 'openai'">
          <div class="mb-3">
            <label for="openai_api_key" class="form-label"
              >API Key <span class="text-danger">*</span></label
            >
            <div class="input-group">
              <input
                :type="showOpenAIApiKey ? 'text' : 'password'"
                class="form-control"
                id="openai_api_key"
                name="openai_api_key"
                v-model="settings.openai_config.api_key"
                placeholder=""
              />
              <button
                type="button"
                class="btn btn-outline-secondary"
                @click="toggleOpenAIApiKeyVisibility"
              >
                {{ showOpenAIApiKey ? 'Hide' : 'Show' }}
              </button>
            </div>
          </div>
          <div class="mb-3">
            <label for="openai_api_host" class="form-label">API Host</label>
            <input
              class="form-control"
              id="openai_api_host"
              name="openai_api_host"
              v-model="settings.openai_config.api_host"
              placeholder=""
            />
            <div class="form-text">
              Optional, the default value is
              <a href="https://api.openai.com/v1">https://api.openai.com/v1</a>
            </div>
          </div>
          <div class="mb-3">
            <div class="d-flex align-items-center justify-content-between gap-2">
              <label for="openai_model" class="form-label"
                >Model <span class="text-danger">*</span></label
              >
              <button
                type="button"
                class="btn btn-sm btn-outline-secondary model-fetch-button"
                :disabled="modelFetchInProgress.openai"
                @click="fetchModels('openai')"
              >
                <span
                  v-if="modelFetchInProgress.openai"
                  class="spinner-border spinner-border-sm"
                  aria-hidden="true"
                ></span>
                <i v-else class="bi bi-arrow-clockwise" aria-hidden="true"></i>
                <span class="visually-hidden">Fetch OpenAI models</span>
              </button>
            </div>
            <select
              ref="openaiModelSelect"
              class="form-select model-choice-select"
              id="openai_model"
              name="openai_model"
              aria-label="OpenAI model"
            ></select>
          </div>
        </div>

        <!-- The Gemini configs -->
        <div v-show="settings.model_provider === 'gemini'">
          <div class="mb-3">
            <label for="gemini_api_key" class="form-label"
              >API Key <span class="text-danger">*</span></label
            >
            <div class="input-group">
              <input
                :type="showGeminiApiKey ? 'text' : 'password'"
                class="form-control"
                id="gemini_api_key"
                name="gemini_api_key"
                v-model="settings.gemini_config.api_key"
                placeholder=""
              />
              <button
                type="button"
                class="btn btn-outline-secondary"
                @click="toggleGeminiApiKeyVisibility"
              >
                {{ showGeminiApiKey ? 'Hide' : 'Show' }}
              </button>
            </div>
            <div class="form-text">
              <a href="https://aistudio.google.com/" target="_blank"
                >Get API key in Google AI Studio</a
              >
            </div>
          </div>
          <div class="mb-3">
            <label for="gemini_api_host" class="form-label">API Host</label>
            <input
              class="form-control"
              id="gemini_api_host"
              name="gemini_api_host"
              v-model="settings.gemini_config.api_host"
              placeholder=""
            />
            <div class="form-text">
              Optional, the default value is
              <a href="https://generativelanguage.googleapis.com"
                >https://generativelanguage.googleapis.com</a
              >
            </div>
          </div>
          <div class="mb-3">
            <div class="d-flex align-items-center justify-content-between gap-2">
              <label for="gemini_model" class="form-label"
                >Model <span class="text-danger">*</span></label
              >
              <button
                type="button"
                class="btn btn-sm btn-outline-secondary model-fetch-button"
                :disabled="modelFetchInProgress.gemini"
                @click="fetchModels('gemini')"
              >
                <span
                  v-if="modelFetchInProgress.gemini"
                  class="spinner-border spinner-border-sm"
                  aria-hidden="true"
                ></span>
                <i v-else class="bi bi-arrow-clockwise" aria-hidden="true"></i>
                <span class="visually-hidden">Fetch Gemini models</span>
              </button>
            </div>
            <select
              ref="geminiModelSelect"
              class="form-select model-choice-select"
              id="gemini_model"
              name="gemini_model"
              aria-label="Gemini model"
            ></select>
          </div>
        </div>

        <!-- The Anthropic configs -->
        <div v-show="settings.model_provider === 'anthropic'">
          <div class="mb-3">
            <label for="anthropic_api_key" class="form-label"
              >API Key <span class="text-danger">*</span></label
            >
            <div class="input-group">
              <input
                :type="showAnthropicApiKey ? 'text' : 'password'"
                class="form-control"
                id="anthropic_api_key"
                name="anthropic_api_key"
                v-model="settings.anthropic_config.api_key"
                placeholder=""
              />
              <button
                type="button"
                class="btn btn-outline-secondary"
                @click="toggleAnthropicApiKeyVisibility"
              >
                {{ showAnthropicApiKey ? 'Hide' : 'Show' }}
              </button>
            </div>
          </div>
          <div class="mb-3">
            <label for="anthropic_api_host" class="form-label">API Host</label>
            <input
              class="form-control"
              id="anthropic_api_host"
              name="anthropic_api_host"
              v-model="settings.anthropic_config.api_host"
              placeholder=""
            />
            <div class="form-text">
              Optional, the default value is
              <a href="https://api.anthropic.com">https://api.anthropic.com</a>
            </div>
          </div>
          <div class="mb-3">
            <div class="d-flex align-items-center justify-content-between gap-2">
              <label for="anthropic_model" class="form-label"
                >Model <span class="text-danger">*</span></label
              >
              <button
                type="button"
                class="btn btn-sm btn-outline-secondary model-fetch-button"
                :disabled="modelFetchInProgress.anthropic"
                @click="fetchModels('anthropic')"
              >
                <span
                  v-if="modelFetchInProgress.anthropic"
                  class="spinner-border spinner-border-sm"
                  aria-hidden="true"
                ></span>
                <i v-else class="bi bi-arrow-clockwise" aria-hidden="true"></i>
                <span class="visually-hidden">Fetch Anthropic models</span>
              </button>
            </div>
            <select
              ref="anthropicModelSelect"
              class="form-select model-choice-select"
              id="anthropic_model"
              name="anthropic_model"
              aria-label="Anthropic model"
            ></select>
          </div>
        </div>

        <!-- The DeepSeek configs -->
        <div v-show="settings.model_provider === 'deepseek'">
          <div class="mb-3">
            <label for="deepseek_api_key" class="form-label"
              >API Key <span class="text-danger">*</span></label
            >
            <div class="input-group">
              <input
                :type="showDeepSeekApiKey ? 'text' : 'password'"
                class="form-control"
                id="deepseek_api_key"
                name="deepseek_api_key"
                v-model="settings.deepseek_config.api_key"
                placeholder=""
              />
              <button
                type="button"
                class="btn btn-outline-secondary"
                @click="toggleDeepSeekApiKeyVisibility"
              >
                {{ showDeepSeekApiKey ? 'Hide' : 'Show' }}
              </button>
            </div>
            <div class="form-text">
              <a href="https://platform.deepseek.com/" target="_blank"
                >Get API key in DeepSeek Platform</a
              >
            </div>
          </div>
          <div class="mb-3">
            <label for="deepseek_api_host" class="form-label">API Host</label>
            <input
              class="form-control"
              id="deepseek_api_host"
              name="deepseek_api_host"
              v-model="settings.deepseek_config.api_host"
              placeholder=""
            />
            <div class="form-text">
              Optional, the default value is
              <a href="https://api.deepseek.com">https://api.deepseek.com</a>
            </div>
          </div>
          <div class="mb-3">
            <div class="d-flex align-items-center justify-content-between gap-2">
              <label for="deepseek_model" class="form-label"
                >Model <span class="text-danger">*</span></label
              >
              <button
                type="button"
                class="btn btn-sm btn-outline-secondary model-fetch-button"
                :disabled="modelFetchInProgress.deepseek"
                @click="fetchModels('deepseek')"
              >
                <span
                  v-if="modelFetchInProgress.deepseek"
                  class="spinner-border spinner-border-sm"
                  aria-hidden="true"
                ></span>
                <i v-else class="bi bi-arrow-clockwise" aria-hidden="true"></i>
                <span class="visually-hidden">Fetch DeepSeek models</span>
              </button>
            </div>
            <select
              ref="deepseekModelSelect"
              class="form-select model-choice-select"
              id="deepseek_model"
              name="deepseek_model"
              aria-label="DeepSeek model"
            ></select>
          </div>
        </div>

        <button type="submit" class="btn btn-primary">Save</button>
      </form>
    </div>
  </div>
</template>

<style>
.model-choice-select + .choices {
  margin-bottom: 0;
}

.model-choice-select + .choices .choices__inner {
  background-color: #fff;
  border: 1px solid #ced4da;
  border-radius: 0.375rem;
  min-height: calc(1.5em + 0.75rem + 2px);
  padding: 0.375rem 0.75rem;
}

.model-choice-select + .choices.is-focused .choices__inner,
.model-choice-select + .choices.is-open .choices__inner {
  border-color: #86b7fe;
  box-shadow: 0 0 0 0.25rem rgb(13 110 253 / 25%);
}

.model-choice-select + .choices .choices__list--single {
  padding: 0;
}

.model-choice-select + .choices .choices__input {
  background-color: #fff;
  margin-bottom: 0;
  padding: 0;
}

.model-fetch-button {
  align-items: center;
  display: inline-flex;
  height: 2rem;
  justify-content: center;
  margin-bottom: 0.5rem;
  width: 2rem;
}
</style>
