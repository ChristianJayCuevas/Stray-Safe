<script setup>
import axios from "axios";
import { ref, computed, defineProps, defineEmits, watch, toRef, onMounted } from "vue";
import { Head, Link, usePage, useForm, router } from "@inertiajs/vue3";
import HeartButton from "@/Components/HeartButton.vue";
import moment from "moment";

const errorMessage = ref("");
const successMessage = ref("");
const props = defineProps({
    post: Object,
    comments: Object,
});
const userId = ref(null);
const postImages = computed(() => props.post.postImages);

const { auth } = usePage().props;
const roles = auth.user?.roles.map((role) => role.name) || [];
const isAdmin = computed(() => {
    const adminRoles = ["super_admin"];
    return roles.some((role) => adminRoles.includes(role));
});
const isOwner = computed(() => auth.user?.id === props.post.user.id);
const canEditOrDelete = computed(() => isAdmin.value || isOwner.value);
console.log("post", props.post);
const form = useForm({
    post_id: props.post.id,
    comment: "",
});

const form2 = useForm({
    id: props.post.id,
    title: props.post.title,
    description: props.post.description,
    image_url: props.post.image_url,
});

const submit = () => {
    errorMessage.value = "";
    successMessage.value = "";

    // Validate that the comment is not null or empty
    if (!form.comment || form.comment.trim() === "") {
        errorMessage.value = "Comment cannot be empty.";
        return;
    }

    form.post(route("createComment"), {
        preserveScroll: true,
        onSuccess: () => {
            // Handle successful form submission
            console.log("Form submitted successfully!");
            successMessage.value = "Comment submitted successfully!";
            form.comment = "";
        },
        onError: (errors) => {
            // Handle errors from the server
            console.error("Form submission error:", errors);
            errorMessage.value = "An error occurred while submitting the form.";
        },
    });
};

const thepost = ref(false);
const imageUrl = ref(
    props.post.image_url ? `/storage/${props.post.image_url}` : null
);

const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
        form2.image_url = file; // Set the file in form2
        const reader = new FileReader();
        reader.onload = (e) => {
            imageUrl.value = e.target.result; // Set the preview URL
        };
        reader.readAsDataURL(file);
    } else {
        form2.image_url = null;
        imageUrl.value = `/storage/${props.post.image_url}`; // Fallback to existing image URL
    }
};

const submit2 = () => {
    // Ensure form2.image_url is correctly set before submission
    form2.image_url = imageUrl.value.includes("data:image")
        ? imageUrl.value
        : form2.image_url;

    form2.patch(route("updatePost", form2.id), {
        preserveScroll: true,
        onSuccess: () => {
            console.log("Form submitted successfully!");
            window.location.reload();
        },
        onError: (errors) => {
            console.error("Form submission error:", errors);
            errorMessage.value = "An error occurred while submitting the form.";
        },
    });
};

const destroy = async (id) => {
    if (confirm("Are you sure you want to delete this post?")) {
        axios
            .delete(`/post-delete/${id}`)
            .then(() => {
                console.log("Post deleted successfully!");
                localStorage.setItem("notification", "successDelete");
                window.location.reload(); // Refresh the page to reflect changes
            })
            .catch((error) => {
                console.error("Error deleting post:", error);
                errorMessage.value =
                    "An error occurred while deleting the post.";
            });
    }
};

const formattedDate = computed(() => {
    return moment(props.post.created_at).fromNow();
});
const card = ref(false);

const maxComments = 5;
const showAll = ref(false);

const displayedComments = computed(() => {
    return showAll.value
        ? props.comments
        : props.comments.slice(0, maxComments);
});

const toggleComments = () => {
    showAll.value = !showAll.value;
};

const post = ref(props.post);

const handleLikeToggle = async (event) => {
    event.preventDefault();

    // Optimistically update the UI
    post.value.liked = !post.value.liked;
    post.value.likes_count += post.value.liked ? 1 : -1;

    try {
        const response = await axios.post(`/post/${post.value.id}/like`, {
            post_id: post.value.id,
        });

        // Check response to ensure successful toggle
        if (!response.data.success) {
            throw new Error("Failed to toggle like");
        }
    } catch (error) {
        // Revert the optimistic update
        post.value.liked = !post.value.liked;
        post.value.likes_count += post.value.liked ? -1 : 1;
        console.error("Error toggling like:", error);
    }
};

const currentIndex = ref(0);
const nextImage = () => {
    if (postImages.value.length > 1) {
        currentIndex.value = (currentIndex.value + 1) % postImages.value.length;
    }
};
const prevImage = () => {
    if (postImages.value.length > 1) {
        currentIndex.value =
            (currentIndex.value - 1 + postImages.value.length) %
            postImages.value.length;
    }
};
const currentImage = computed(
    () => postImages.value[currentIndex.value]?.post_image_path
);
const showArrows = computed(() => postImages.value.length > 1);
const beforeEnter = (el) => {
    el.style.opacity = 0;
    el.style.transform = "scale(0.95)";
};

const enter = (el, done) => {
    el.offsetHeight; // Trigger reflow
    el.style.transition = "opacity 0.5s ease, transform 0.5s ease";
    el.style.opacity = 1;
    el.style.transform = "scale(1)";
    done();
};

const leave = (el, done) => {
    el.style.transition = "opacity 0.5s ease, transform 0.5s ease";
    el.style.opacity = 0;
    el.style.transform = "scale(0.95)";
    done();
};

</script>
<template>
    <div class="instagram-card max-w-3xl" @click="card = true">
        <div class="flex items-center justify-between p-4">
            <div class="flex items-center gap-2">
                <q-avatar size="40px">
                    <img style="background: white; border-radius: 20px" :src="post.user.profile_image_url
                            ? `/storage/images/${post.user.profile_image_url}`
                            : '/storage/images/TEMPPROFILE.png'
                        " alt="Profile Image" />
                </q-avatar>
                <div>
                    <a @click.stop class="font-medium text-lg hover:underline">{{ post.user.name }}</a>
                    <br />
                    <span class="text-xs text-gray-500">{{
                        formattedDate
                        }}</span>
                </div>
            </div>

            <q-btn-dropdown dropdown-icon="fa-solid fa-ellipsis-h" @click.stop flat round >
                <q-list style="min-width: 150px">
                    <!-- <q-item
                        clickable
                        v-close-popup
                        @click="onItemClick('Save Post')"
                    >
                        <q-item-section>
                            <div class="flex items-center">
                                <q-icon name="fa-solid fa-box-archive" />
                                <q-item-label class="ml-2"
                                    >Save Post</q-item-label
                                >
                            </div>
                        </q-item-section>
                    </q-item> -->
                        <q-item clickable v-close-popup @click="thepost = true">
                            <q-item-section>
                                <div class="flex items-center">
                                    <q-icon name="fa-solid fa-pencil-alt" />
                                    <q-item-label class="ml-2" color="warning">Edit Post</q-item-label>
                                </div>
                            </q-item-section>
                        </q-item>

                        <q-item clickable v-close-popup @click="destroy(post.id)">
                            <q-item-section>
                                <div class="flex items-center">
                                    <q-icon name="fa-solid fa-trash-alt" />
                                    <q-item-label class="ml-2">Delete Post</q-item-label>
                                </div>
                            </q-item-section>
                        </q-item>
                 
                </q-list>
            </q-btn-dropdown>
        </div>
        <q-separator />

        <!-- Image container with fixed aspect ratio -->
        <div class="carousel-container" @click.stop v-if="postImages.length > 0">
            <!-- Conditionally rendered prev button -->
            <button v-if="showArrows" class="carousel-control prev" @click="prevImage">
                ❮
            </button>
            <div class="carousel-images">
                <transition name="fade" @before-enter="beforeEnter" @enter="enter" @leave="leave">
                    <img :key="currentImage" :src="`/storage/images/${currentImage}`" alt="Post Image"
                        class="carousel-image" />
                </transition>
            </div>
            <!-- Conditionally rendered next button -->
            <button v-if="showArrows" class="carousel-control next" @click="nextImage">
                ❯
            </button>
        </div>
        <!-- Actions and details -->
        <div class="flex flex-row p-4 justify-between items-center">
            <div class="flex gap-4">
                <Link @click.stop :href="`/post/${post.id}/like`" method="post" as="button" type="button"
                    preserve-scroll class="flex items-center text-blue-500 hover:text-blue-700">
                <HeartButton class="w-4 h-4" :name="post.liked ? 'heart' : 'heart-outline'" @click="handleLikeToggle" />
                <span class="ml-2 text-black" style="font-weight: bold">{{
                    post.likes_count
                }}</span>
                </Link>
                <div class="flex items-center text-gray-500 hover:text-gray-700">
                    <q-btn flat round icon="comment" color="gray" />
                    <span class="mr-1" style="color: black">Comment</span>
                </div>
            </div>
        </div>
        <q-separator />
        <div class="flex flex-col p-4 ml-3">
            <h6 class="text-3xl font-bold mb-2">{{ post.title }}</h6>
            <p class="text-lg font-light mb-4">{{ post.description }}</p>
        </div>
        <form @submit.prevent="submit">
            <div class="flex items-center p-4 border-t" @click.stop>
                <q-input filled placeholder="Add a comment..." class="flex-grow" v-model="form.comment" />
                <q-btn rounded flat label="Post" icon="fa-solid fa-paper-plane" type="submit" />
            </div>
            <div v-if="errorMessage" class="q-pa-md text-red-500">
                {{ errorMessage }}
            </div>
            <div v-if="successMessage" class="q-pa-md text-green-500">
                {{ successMessage }}
            </div>
        </form>
    </div>

    <q-dialog v-model="card" backdrop-filter="blur(4px) saturate(150%)">
        <q-card class="instagram-dialog my-card row no-wrap">
            <!-- Left side: Image (3/4) -->
            <div v-if="postImages.length > 0" class="carousel-container" style="background: black" @click.stop>
                <!-- Conditionally rendered prev button -->
                <button v-if="showArrows" class="carousel-control prev" @click="prevImage">
                    ❮
                </button>
                <div class="carousel-images">
                    <transition name="fade" @before-enter="beforeEnter" @enter="enter" @leave="leave">
                        <div class="carousel-image-wrapper">
                            <img v-if="currentImage" :key="currentImage" :src="`/storage/images/${currentImage}`"
                                alt="Post Image" class="carousel-image" />
                        </div>
                    </transition>
                </div>
                <!-- Conditionally rendered next button -->
                <button v-if="showArrows" class="carousel-control next" @click="nextImage">
                    ❯
                </button>
            </div>

            <!-- Right side: Post details (1/4) -->
            <div class="col-3 flex flex-col post-details">
                <!-- User details -->
                <div class="flex items-center p-4 border-b">
                    <q-avatar size="42px">
                        <img style="
                            background: white;
                            border-radius: 50%;
                            width: 42px;
                            height: 42px;
                        " :src="post.user.profile_image_url
                                ? `/storage/images/${post.user.profile_image_url}`
                                : '/storage/images/TEMPPROFILE.png'
                            " alt="Profile Image" />
                    </q-avatar>
                    <div class="ml-3">
                        <span class="font-medium text-sm">{{ post.user.name }}</span><br />
                        <span class="text-xs text-gray-500">{{ formattedDate }}</span>
                    </div>
                    <template v-if="post.user.id !== $page.props.auth.user.id">

                    </template>
                </div>

                <!-- Post content -->
                <div class="flex-grow p-4 overflow-auto comments-section">
                    <h2 class="text-xl font-bold text-black mb-2">{{ post.title }}</h2>
                    <div class="text-caption text-black mb-2">{{ post.description }}</div>
                    <q-separator class="mb-4" />
                    <div class="instagram-comments">
                        <template v-if="comments && comments.length">
                            <div v-for="(comment, index) in displayedComments" :key="comment.id"
                                class="comment-item mt-2 mb-1">
                                <div class="comment-content">
                                    <p class="font-semibold text-black mr-2">{{ comment.user.name }}:</p>
                                    <p class="text-gray-700">{{ comment.comments }}</p>
                                </div>
                            </div>
                            <template v-if="comments.length > maxComments">
                                <button @click="toggleComments" class="text-blue-500 mt-2">
                                    {{ showAll ? "See Less..." : "See More..." }}
                                </button>
                            </template>
                        </template>
                        <template v-else>
                            <p class="text-gray-500">No comments yet.</p>
                        </template>
                    </div>
                </div>

                <!-- Actions -->
                <div class="flex items-center p-4 border-t actions-section">
                    <Link @click.stop :href="`/post/${post.id}/like`" method="post" as="button" type="button"
                        preserve-scroll class="flex items-center text-blue-500 hover:text-blue-700">
                    <HeartButton class="w-4 h-4" :name="post.liked ? 'heart' : 'heart-outline'"
                        @click="handleLikeToggle" />
                    <span class="ml-2 text-black" style="font-weight: bold">{{ post.likes_count }}</span>
                    </Link>
                </div>

                <!-- Add a comment -->
                <form @submit.prevent="submit">
                    <div class="flex items-center p-4 border-t" @click.stop>
                        <q-input filled placeholder="Add a comment..." class="flex-grow" v-model="form.comment" />
                        <q-btn rounded flat label="Post" icon="fa-solid fa-paper-plane" type="submit" />
                    </div>
                    <div v-if="errorMessage" class="q-pa-md text-red-500">
                        {{ errorMessage }}
                    </div>
                    <div v-if="successMessage" class="q-pa-md text-green-500">
                        {{ successMessage }}
                    </div>
                </form>
            </div>
        </q-card>
    </q-dialog>
    <q-dialog v-model="thepost" backdrop-filter="blur(4px) saturate(150%)" persistent>
        <div class="instagram-card bg-white rounded-lg shadow-lg overflow-hidden"
            style="max-width: 90vw; max-height: 90vh; width: 80vw; height: 80vh">
            <div class="flex justify-start p-8 bg-gray-100">
                <h4 class="text-2xl font-bold">Update Post</h4>
            </div>

            <div class="flex flex-col gap-8 p-8 overflow-y-auto" style="height: calc(100% - 64px)">
                <form @submit.prevent="submit2">
                    <!-- File input for image upload -->
                    <input type="file" class="ml-5 bg-base-200 file-input file-input-bordered w-half mb-8"
                        @change="handleFileUpload" accept="image/*" />

                    <div v-if="imageUrl" class="q-pa-md">
                        <img :src="imageUrl" class="rounded-lg max-w-full mx-auto" alt="Uploaded Image"
                            style="max-height: 300px" />
                    </div>

                    <!-- Title input -->
                    <div class="q-pa-md">
                        <q-input v-model="form2.title" rounded outlined type="text" label="Title"
                            class="w-full text-lg" />
                    </div>

                    <!-- Description input -->
                    <div class="q-pa-md">
                        <q-input v-model="form2.description" rounded outlined type="textarea" label="Description"
                            class="w-full text-lg" />
                    </div>

                    <!-- Error message display -->
                    <div v-if="errorMessage" class="q-pa-md text-red-500 text-lg">
                        {{ errorMessage }}
                    </div>

                    <!-- Submit button -->
                    <div class="q-pa-md flex justify-end gap-4">
                        <q-btn color="positive" label="Submit" type="submit" v-close-popup class="text-lg" />
                        <q-btn flat color="negative" label="Cancel" v-close-popup class="text-lg" />
                    </div>
                </form>
            </div>
        </div>
    </q-dialog>
</template>

<style scoped>
.instagram-card {
    border: 1px solid #ddd;
    border-radius: 10px;
    box-shadow: 12px 17px 51px rgba(0, 0, 0, 0.22);
    /* margin: 0 auto; */
    /* margin-left: auto;
    margin-right: 20px; */
    margin-bottom: 20px;
    backdrop-filter: blur(6px);
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.5s;
    user-select: none;
    font-weight: bolder;
    color: black;
    background: white;
    font-family: "Poppins", sans-serif;
    overflow: hidden;
}

.aspect-ratio-container {
    position: relative;
    width: 100%;
    padding-top: 56.25%;
    /* 16:9 aspect ratio */
    background-color: black;
    /* Black filler */
}

.aspect-ratio-img {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
}

.instagram-card:hover {
    border: 1px solid black;
}

.instagram-card-header,
.instagram-card-footer {
    display: flex;
    align-items: center;
    padding: 10px;
}

.instagram-card-user-image {
    border-radius: 50%;
    width: 42px;
    height: 42px;
    margin-right: 10px;
}

.instagram-card-user-name {
    color: #333;
    text-decoration: none;
    font-weight: bold;
}

.instagram-card-image img {
    width: 100%;
    height: auto;
    display: block;
}

.instagram-card-content {
    padding: 10px;
}

.instagram-card-icon {
    color: #333;
    text-decoration: none;
    margin-right: 10px;
    cursor: pointer;
}

.instagram-card-icon.instagram-bookmark {
    margin-left: auto;
}

.instagram-card-content-user,
.hashtag {
    color: #003569;
    text-decoration: none;
    font-weight: bold;
}

.instagram-card-input {
    border: none;
    flex: 1;
    padding: 10px;
    margin-right: 10px;
    border-radius: 10px;
}

.instagram-card-footer .fa-ellipsis-h {
    cursor: pointer;
}

.instagram-dialog {
    max-width: 90vw;
    max-height: 90vh;
}

.image-container {
    overflow: hidden;
}

.instagram-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.post-details {
    display: flex;
    flex-direction: column;
    max-height: 100%;
}

.comments-section {
    overflow-y: auto;
}

.instagram-comments {
    max-height: 35vh;
    overflow-y: auto;
}

.my-card {
    display: flex;
    flex-direction: row;
    padding: 0;
    width: 85vw;
    height: 80vh;
}

.q-card-section {
    padding: 0;
}

.q-separator {
    margin: 0;
}

.instagram-actions svg {
    width: 24px;
    height: 24px;
}

.comment-content {
    display: flex;
    flex-direction: row;
    /* Ensures items are aligned horizontally */
}

.carousel-container {
    position: relative;
    width: 100%;
    height: 100%;
}

.carousel-images {
    position: relative;
    width: 100%;
    height: 100%;
    overflow: hidden;
}

.carousel-image-wrapper {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.carousel-image {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    /* Maintains aspect ratio and fits within the container */
}


.carousel-control {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    background-color: rgba(0, 0, 0, 0.5);
    color: white;
    border: none;
    padding: 10px;
    cursor: pointer;
    z-index: 1000;
    font-size: 24px;
    /* Adjust size of the arrows */
}

.prev {
    left: 10px;
}

.next {
    right: 10px;
}

/* Transition effects for carousel */
.carousel-enter-active,
.carousel-leave-active {
    transition: opacity 0.5s ease, transform 0.5s ease;
}

.carousel-enter,
.carousel-leave-to {
    opacity: 0;
    transform: scale(0.95);
    /* Optional: Scale down during the transition */
}

/* Optional: Add additional scale effect for entering */
.carousel-enter {
    opacity: 0;
    transform: scale(1.05);
    /* Optional: Scale up during the transition */
}
</style>
