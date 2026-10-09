<script setup>
import { ref, onMounted } from 'vue'
import NavBar from '../components/NavBar.vue'
import { getStats, getFormats, fmtSize } from '../api.js'

const stats = ref([])
const ffmpeg = ref(true)
const names = { image: '图片', audio: '音频', video: '视频' }
onMounted(async () => {
  stats.value = await getStats().catch(() => [])
  ffmpeg.value = (await getFormats().catch(() => ({ ffmpeg: true }))).ffmpeg
})
</script>
<template>
  <NavBar active="index" />
  <main>
    <h1>多媒体处理平台</h1>
    <p v-if="!ffmpeg" class="err">未检测到 FFmpeg，音频/视频功能不可用。</p>
    <div class="grid">
      <a class="card tile" href="/image.html"><h2>🖼 图片</h2><p>JPG/PNG/WebP/BMP/GIF 压缩、缩放、转换</p></a>
      <a class="card tile" href="/audio.html"><h2>🎵 音频</h2><p>MP3/WAV/AAC/OGG/FLAC/M4A 压缩与转换</p></a>
      <a class="card tile" href="/video.html"><h2>🎬 视频</h2><p>MP4/WebM/MKV/AVI/MOV/GIF 压缩与转换</p></a>
    </div>
    <h2>累计统计</h2>
    <table v-if="stats.length"><thead><tr><th>类型</th><th>任务数</th><th>成功</th><th>失败</th><th>处理前</th><th>处理后</th></tr></thead>
      <tbody><tr v-for="s in stats" :key="s.kind"><td>{{ names[s.kind] }}</td><td>{{ s.n }}</td><td>{{ s.done }}</td><td>{{ s.failed }}</td><td>{{ fmtSize(s.in_size) }}</td><td>{{ fmtSize(s.out_size) }}</td></tr></tbody></table>
    <p v-else>暂无任务。</p>
  </main>
</template>
