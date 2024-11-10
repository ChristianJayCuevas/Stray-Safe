<script setup>
import { ref, computed, watch } from 'vue';

// Props to be passed from the parent component
const props = defineProps({
    posts: Object,
    search: String,
});

const emit = defineEmits(['update:search', 'filteredPostsUpdated']);

const search = ref(props.search || '');

// Watch for changes in the search value and emit events
watch(search, (newSearch) => {
    emit('update:search', newSearch);
    emit('filteredPostsUpdated', filterPosts());
});

const filterPosts = () => {
    if (!search.value.trim()) {
        return props.posts.data;
    }
    const searchTerm = search.value.toLowerCase();
    return props.posts.data.filter(post => {
        // Use optional chaining and default values
        const title = (post.title || '').toLowerCase();
        const content = (post.description || '').toLowerCase();
        const username = (post.user.username || '').toLowerCase();
        return title.includes(searchTerm) || content.includes(searchTerm) || username.includes(searchTerm);
    });
};

const clearSearch = () => {
    search.value = '';
};
</script>

<template>
    <q-card class="search-card">
        <q-card-section>
            <h3 class="text-title-small mb-3">Search</h3>
            <q-input
                class="search-input focus:outline-none focus:shadow-none"
                v-model="search"
                label="Search"
            >
                <template v-slot:prepend>
                    <q-icon v-if="search === ''" name="search" />
                    <q-icon
                        v-else
                        name="clear"
                        class="cursor-pointer"
                        @click="clearSearch"
                    />
                </template>
            </q-input>
        </q-card-section>
    </q-card>
</template>
