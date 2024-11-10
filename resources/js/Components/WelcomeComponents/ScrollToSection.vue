<script setup>
import { ref } from 'vue';

const props = defineProps({
    sectionId: {
        type: String,
        required: true,
    },
    tabId: {
        type: String,
        required: true,
    },
});

function scrollToSection(sectionId, tabId) {
    const targetElement = document.querySelector(sectionId);
    const targetPosition = targetElement.getBoundingClientRect().top + window.scrollY;
    const startPosition = window.scrollY;
    const distance = targetPosition - startPosition;
    const duration = 800;
    let start = null;

    function step(timestamp) {
        if (!start) start = timestamp;
        const progress = timestamp - start;
        const percentage = Math.min(progress / duration, 1);
        const ease = easeInOutQuad(percentage);

        window.scrollTo(0, startPosition + distance * ease);

        if (progress < duration) {
            window.requestAnimationFrame(step);
        }
    }

    function easeInOutQuad(t) {
        return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    }

    window.requestAnimationFrame(step);

    const tab = document.getElementById(tabId);
    tab.checked = true;
}
</script>
<template>
    <button @click="scrollToSection(sectionId, tabId)">
        <slot></slot>
    </button>
</template>