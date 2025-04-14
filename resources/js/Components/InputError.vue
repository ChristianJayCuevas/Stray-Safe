<script setup>
defineProps({
    message: {
        type: String,
    },
});
</script>

<template>
    <div v-show="message">
        <p v-if="message" class="error-message text-sm text-red-600 dark:text-red-400">
            {{ message }}
        </p>
    </div>
</template>
