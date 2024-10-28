<template>
    <AuthenticatedLayout>
        <template #header>
            <h2 class="font-semibold text-xl text-gray-800 leading-tight">Home</h2>
        </template>
        <div class="dashboard-container py-12">
            <!-- Main content -->
            <div class="main-content flex-1">

                <template v-if="filteredPosts.length > 0">
                    <template v-for="post in filteredPosts" :key="post.id">
                        <Card :post="post" :comments="comments[post.id] || []"/>
                    </template>
                    <Pagination :pagination="posts" />
                </template>
                <template v-else>
                    <div class="text-center text-gray-500">No posts available.</div>
                </template>
            </div>
            <div class="right-column">
                <q-card class="search-card">
                    <q-card-section>
                        <h3 class="text-lg font-semibold mb-3">Search</h3>
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
            </div>
        </div>
    </AuthenticatedLayout>
</template>
<script setup>
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import Card from '@/Components/Card.vue';
import Pagination from '@/Components/Pagination.vue';
import { usePage } from '@inertiajs/vue3';
import { ref, computed } from 'vue';

const { props } = usePage();
const posts = ref(props.posts);
const authUser = ref(props.auth.user || {});
const search = ref('');

defineProps({
    posts: Object,
    comments: Object,
    isFollowing: Boolean,
    search: String,
});

const filteredPosts = computed(() => {
    if (!search.value.trim()) {
        return posts.value.data;
    }
    const searchTerm = search.value.toLowerCase();
    return posts.value.data.filter(post => {
        // Use optional chaining and default values
        const title = (post.title || '').toLowerCase();
        const content = (post.description || '').toLowerCase();
        const username = (post.user.username || '').toLowerCase();
        return title.includes(searchTerm) || content.includes(searchTerm) || username.includes(searchTerm);
    });
});

const clearSearch = () => {
    search.value = '';
};
</script>
<style scoped>
.dashboard-container {
    display: flex;
    justify-content: center;
    gap: 50px; /* Space between the main content and right column */
    padding: 50px 20px; /* Add padding to the container */
}

.main-content {
    flex: 1;
    max-width: 700px; /* Adjust based on your desired width for the Card content */
}

.right-column {
    width: 400px;
    flex-shrink: 0; /* Prevent the right column from shrinking */
}

/* Media query to stack the right column on top of the main content on small screens */
@media (max-width: 1024px) {
    .dashboard-container {
        flex-direction: column; /* Stack the columns vertically */
        padding: 50px 20px; /* Ensure padding remains on smaller screens */
        gap: 20px; /* Adjust the gap between the stacked elements */
    }

    .main-content {
        max-width: 100%; /* Allow the main content to take full width */
        margin: 0 auto; /* Center the main content */
    }

    .right-column {
        width: 100%; /* Allow the right column to take full width */
        order: -1; /* Move the right column above the main content */
    }
}

.search-card {
    margin-bottom: 20px;
    border: 1px solid #ddd;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    padding: 15px;
    background-color: #ffffff;
}

.search-input {
    width: 100%;
}

.search-input .q-field--focused .q-field__control {
    outline: none; /* Remove the blue outline */
    box-shadow: none; /* Remove any additional focus shadow */
}

.search-input input:focus {
    outline: none;
    box-shadow: none;
}

.user-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}

.q-card-section {
    padding: 0;
}

.user-details {
    display: flex;
    flex-direction: column;
    text-align: left;
    margin-left: 10px;
    flex-grow: 1;
}

.user-name {
    font-size: 0.875rem;
    font-weight: 600;
}

.user-email {
    font-size: 0.75rem;
    color: #6b7280;
}

.user-name:hover {
    text-decoration: underline;
}

.no-focus .q-field__native:focus {
    outline: none !important;
    box-shadow: none !important;
    border-color: transparent !important;
}
</style>