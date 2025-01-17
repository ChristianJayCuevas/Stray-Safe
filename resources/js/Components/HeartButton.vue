<template>
  <div class="heart-container">
    <transition name="fade" mode="out-in">
      <q-btn
        v-if="name === 'heart'"
        :key="'filled'"
        round
        flat
        icon="favorite"
        class="text-red-500"
        color="red"
        @click="toggleLike"
      />
      <q-btn
        v-else
        :key="'outlined'"
        flat
        round
        icon="favorite_border"
        class="text-gray-500"
        color="grey"
        @click="toggleLike"
      />
    </transition>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';

const props = defineProps({
  name: {
    type: String,
    required: true,
    validator: value => ['heart', 'heart-outline'].includes(value)
  }
});

const emit = defineEmits(['toggle-like']);

function toggleLike() {
  emit('toggle-like');
}
</script>

<style scoped>
.heart-container {
  display: inline-flex; /* Ensure items are inline */
  margin-bottom: 27px;
  margin-right: 13px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.1s ease;
  transform: scale(1.1);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 1;
}  
</style>  