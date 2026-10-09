<script setup>
import { ref, onMounted } from 'vue'
import NavBar from '../components/NavBar.vue'
import { listTasks, deleteTask, downloadUrl, fmtSize } from '../api.js'

const tasks = ref([])
const kind = ref('')
const err = ref('')
const names = { image: '图片', audio: '音频', video: '视频' }
const acts = { compress: '压缩', convert: '转换' }
async function load() {
  try { tasks.value = await listTasks(kind.value) } catch (e) { err.value = e.message }
}
async function remove(id) {
  if (!confirm('确定删除该任务及文件？')) return
  await deleteTask(id)
  load()
}
onMounted(load)
</script>
<template>
  <NavBar active="history" />
  <main>
    <h1>任务记录</h1>
    <select v-model="kind" @change="load"><option value="">全部</option><option v-for="(n, k) in names" :key="k" :value="k">{{ n }}</option></select>
    <button @click="load">刷新</button>
    <p v-if="err" class="err">{{ err }}</p>
    <table>
      <thead><tr><th>文件</th><th>类型</th><th>操作</th><th>格式</th><th>大小</th><th>状态</th><th>时间</th><th></th></tr></thead>
      <tbody>
        <tr v-for="t in tasks" :key="t.id">
          <td>{{ t.original_name }}</td><td>{{ names[t.kind] }}</td><td>{{ acts[t.action] }}</td><td>{{ t.target_format }}</td>
          <td>{{ fmtSize(t.input_size) }} → {{ fmtSize(t.output_size) }}</td>
          <td :title="t.error">{{ t.status }}</td><td>{{ t.created_at.slice(0, 19).replace('T', ' ') }}</td>
          <td><a v-if="t.status === 'done'" :href="downloadUrl(t.id)">下载</a> <a href="#" @click.prevent="remove(t.id)">删除</a></td>
        </tr>
      </tbody>
    </table>
    <p v-if="!tasks.length">暂无记录。</p>
  </main>
</template>
