<script setup>
import NavBar from '../components/NavBar.vue'
import MediaTool from '../components/MediaTool.vue'
</script>
<template>
  <NavBar active="image" />
  <main><h1>图片压缩与格式转换</h1>
    <MediaTool kind="image" accept="image/*,.webp,.bmp,.tiff" :formats="['jpg', 'png', 'webp', 'bmp', 'gif']" />
  </main>
</template>
