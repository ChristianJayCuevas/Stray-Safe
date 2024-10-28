<template>
  <nav class="flex items-center justify-center mt-8">
    <ul class="flex items-center space-x-40">
      <!-- Previous page link -->
      <li>
        <a v-if="links.prev" :href="links.prev" class="px-3 py-1 bg-gray-200 rounded-md hover:bg-gray-300">
          &lt; Previous
        </a>
        <span v-else class="px-3 py-1 bg-gray-200 rounded-md opacity-50 cursor-not-allowed">
          &lt; Previous
        </span>
      </li>

      <!-- Next page link -->
      <li>
        <a v-if="links.next" :href="links.next" class="px-3 py-1 bg-gray-200 rounded-md hover:bg-gray-300">
          Next &gt;
        </a>
        <span v-else class="px-3 py-1 bg-gray-200 rounded-md opacity-50 cursor-not-allowed">
          Next &gt;
        </span>
      </li>
    </ul>
  </nav>
</template>

<script setup>
import { defineProps, computed } from 'vue';

const props = defineProps({
  pagination: {
    type: Object,
    required: true
  }
});

const links = computed(() => ({
  prev: props.pagination.links.prev || null,
  next: props.pagination.links.next || null
}));

const data = props.pagination.data || [];
</script>