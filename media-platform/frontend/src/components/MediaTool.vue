<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { createTask, getTask, downloadUrl, fmtSize } from '../api.js'

const props = defineProps({
  kind: String,
  accept: String,
  formats: Array,
})

const mode = ref('compress')
const file = ref(null)
const target = ref('')
const params = ref({ quality: 75, max_width: '', bitrate: 96, sample_rate: '', crf: 28, height: '' })
const task = ref(null)
const error = ref('')
const busy = ref(false)
let timer = null

const effectiveTarget = computed(() => target.value || props.formats[0])

function onFile(e) {
  file.value = e.target.files[0] || null
  task.value = null
  error.value = ''
}

async function submit() {
  if (!file.value) return (error.value = '请先选择文件')
  error.value = ''
  task.value = null
  busy.value = true
  const fd = new FormData()
  fd.append('file', file.value)
  fd.append('kind', props.kind)
  fd.append('action', mode.value)
  fd.append('target_format', effectiveTarget.value)
  const keys = { image: ['max_width'], audio: ['sample_rate'], video: ['height'] }[props.kind]
  const extra = [...keys]
  if (mode.value === 'compress') extra.push({ image: 'quality', audio: 'bitrate', video: 'crf' }[props.kind])
  for (const k of extra) if (params.value[k] !== '' && params.value[k] != null) fd.append(k, params.value[k])
  try {
    task.value = await createTask(fd)
    poll()
  } catch (e) {
    error.value = e.message
    busy.value = false
  }
}

function poll() {
  timer = setTimeout(async () => {
    try {
      task.value = await getTask(task.value.id)
      if (['done', 'failed'].includes(task.value.status)) {
        busy.value = false
        if (task.value.status === 'failed') error.value = task.value.error
        return
      }
    } catch (e) {
      error.value = e.message
      busy.value = false
      return
    }
    poll()
  }, 800)
}
onBeforeUnmount(() => clearTimeout(timer))
</script>

<template>
  <section class="card">
    <div class="tabs">
      <button :class="{ on: mode === 'compress' }" @click="mode = 'compress'">压缩</button>
      <button :class="{ on: mode === 'convert' }" @click="mode = 'convert'">格式转换</button>
    </div>

    <label class="row">选择文件
      <input type="file" :accept="accept" @change="onFile" data-test="file" />
    </label>

    <label class="row">目标格式
      <select v-model="target">
        <option v-for="f in formats" :key="f" :value="f">{{ f.toUpperCase() }}</option>
      </select>
    </label>

    <template v-if="kind === 'image'">
      <label v-if="mode === 'compress'" class="row">质量 (1-100): {{ params.quality }}
        <input type="range" min="1" max="100" v-model="params.quality" />
      </label>
      <label class="row">最大宽度 (px，可选)
        <input type="number" min="1" v-model="params.max_width" placeholder="不缩放" />
      </label>
    </template>

    <template v-if="kind === 'audio'">
      <label v-if="mode === 'compress'" class="row">比特率 (kbps)
        <select v-model="params.bitrate"><option v-for="b in [32, 64, 96, 128, 192, 256, 320]" :key="b" :value="b">{{ b }}</option></select>
      </label>
      <label class="row">采样率 (Hz，可选)
        <select v-model="params.sample_rate"><option value="">保持</option><option v-for="s in [8000, 22050, 44100, 48000]" :key="s" :value="s">{{ s }}</option></select>
      </label>
    </template>

    <template v-if="kind === 'video'">
      <label v-if="mode === 'compress'" class="row">CRF 质量 (0-51，越大压缩越多): {{ params.crf }}
        <input type="range" min="18" max="45" v-model="params.crf" />
      </label>
      <label class="row">输出高度
        <select v-model="params.height"><option value="">保持</option><option v-for="h in [240, 360, 480, 720, 1080]" :key="h" :value="h">{{ h }}p</option></select>
      </label>
    </template>

    <button class="primary" :disabled="busy" @click="submit">{{ busy ? '处理中…' : (mode === 'compress' ? '开始压缩' : '开始转换') }}</button>
    <p v-if="error" class="err">{{ error }}</p>

    <div v-if="task" class="result">
      <p>状态：<b :class="task.status">{{ { pending: '排队中', processing: '处理中', done: '完成', failed: '失败' }[task.status] }}</b></p>
      <template v-if="task.status === 'done'">
        <p>原始 {{ fmtSize(task.input_size) }} → 输出 {{ fmtSize(task.output_size) }}
          <span v-if="task.ratio != null">（{{ task.ratio >= 0 ? '减少' : '增加' }} {{ Math.abs(task.ratio * 100).toFixed(1) }}%）</span></p>
        <img v-if="kind === 'image'" :src="downloadUrl(task.id) + '?inline=1'" class="preview" />
        <audio v-if="kind === 'audio'" :src="downloadUrl(task.id) + '?inline=1'" controls />
        <video v-if="kind === 'video' && task.target_format !== 'gif'" :src="downloadUrl(task.id) + '?inline=1'" controls class="preview" />
        <p><a class="primary link" :href="downloadUrl(task.id)">下载结果</a></p>
      </template>
    </div>
  </section>
</template>
