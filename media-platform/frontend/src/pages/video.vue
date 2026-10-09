<script setup>
import NavBar from '../components/NavBar.vue'
import MediaTool from '../components/MediaTool.vue'
</script>
<template>
  <NavBar active="video" />
  <main><h1>视频压缩与格式转换</h1>
    <MediaTool kind="video" accept="video/*,.mkv,.avi,.mov,.flv,.wmv" :formats="['mp4', 'webm', 'mkv', 'avi', 'mov', 'gif']" />
  </main>
</template>
