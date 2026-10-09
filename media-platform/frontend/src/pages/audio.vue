<script setup>
import NavBar from '../components/NavBar.vue'
import MediaTool from '../components/MediaTool.vue'
</script>
<template>
  <NavBar active="audio" />
  <main><h1>音频压缩与格式转换</h1>
    <MediaTool kind="audio" accept="audio/*,.mp3,.wav,.aac,.ogg,.flac,.m4a" :formats="['mp3', 'wav', 'aac', 'ogg', 'flac', 'm4a']" />
  </main>
</template>
