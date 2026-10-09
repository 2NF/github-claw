<script setup>
defineProps({ active: String })
const links = [
  ['index', '/index.html', '首页'],
  ['image', '/image.html', '图片'],
  ['audio', '/audio.html', '音频'],
  ['video', '/video.html', '视频'],
  ['history', '/history.html', '任务记录'],
]
</script>

<template>
  <header class="nav">
    <strong class="brand">🎞 多媒体处理平台</strong>
    <nav>
      <a v-for="[k, href, label] in links" :key="k" :href="href" :class="{ on: k === active }">{{ label }}</a>
    </nav>
  </header>
</template>
