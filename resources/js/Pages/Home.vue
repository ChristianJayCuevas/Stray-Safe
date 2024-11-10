<script setup>
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import Card from '@/Components/Card.vue';
import Pagination from '@/Components/Pagination.vue';
import SearchFilter from '@/Components/HomeComponents/SearchFilter.vue'; 
import { usePage } from '@inertiajs/vue3';
import { ref} from 'vue';

const { props } = usePage();
const posts = ref(props.posts);
const comments = ref(props.comments);
const search = ref('');

const filteredPosts = ref(posts.value.data);

const updateSearch = (newSearch) => {
    search.value = newSearch;
};

const updateFilteredPosts = (newFilteredPosts) => {
    filteredPosts.value = newFilteredPosts;
};
</script>

<template>
    <AuthenticatedLayout>
        <template #header>
            <h2 class="header">Home</h2>
        </template>
        <div class="dashboard-container">
            <div class="main-content">
                <template v-if="filteredPosts.length > 0">
                    <template v-for="post in filteredPosts" :key="post.id">
                        <Card :post="post" :comments="comments[post.id] || []" />
                    </template>
                    <Pagination :pagination="posts" />
                </template>
                <template v-else>
                    <div class="text-subtitle-center">No posts available.</div>
                </template>
            </div>
            <div class="right-column">
                <SearchFilter
                    :posts="posts"
                    :search="search"
                    @update:search="updateSearch"
                    @filteredPostsUpdated="updateFilteredPosts"
                />
            </div>
        </div>
    </AuthenticatedLayout>
</template>

<style src="../../css/home.css" lang="css"></style>
<style src="../../css/text.css" lang="css"></style>
