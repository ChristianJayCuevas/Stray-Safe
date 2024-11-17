
<script setup>
import { ref, computed, onMounted, defineEmits } from "vue";
import { Link, usePage, router } from "@inertiajs/vue3";
import { Head, useForm } from "@inertiajs/vue3";
import { useQuasar } from 'quasar';

//FilePond imports for multiple file upload
import vueFilePond from "vue-filepond";
import FilePondPluginImagePreview from "filepond-plugin-image-preview";
import 'filepond-plugin-image-preview/dist/filepond-plugin-image-preview.css';
import 'filepond/dist/filepond.min.css';

//Create an Instance of FilePond
const FilePond = vueFilePond(FilePondPluginImagePreview);

const { auth } = usePage().props;
const authUser = computed(() => auth.user || null);
console.log("auth.user:", auth.user);

const drawer = ref(false);
const miniState = ref(true);
const thepost = ref(false);
const leftDrawerOpen = ref(false);
const search = ref('');
const filteredResults = ref({ posts: [], users: [] });
const $q = useQuasar()

function submitLogout() {
    Inertia.post(route("logout"));
}

function toggleLeftDrawer() {
    leftDrawerOpen.value = !leftDrawerOpen.value;
}

// Perform search
const emit = defineEmits();

const updateSearch = () => {
    emit('search-updated', search.value);
};

const clearSearch = () => {
    search.value = '';
    emit('search-updated', search.value);
};
const uploader = ref(null);
const form = useForm({
    title: "",
    description: "",
    image_url: [],
});

const errorMessage = ref("");

function handleFilePondRevert(uniqueId, load, error){
    form.image_url = form.image_url.filter((image) => image !== uniqueId);
    router.delete('/revert/' + uniqueId);
    load();
}

function handleFilePondLoad(response){
    form.image_url.push(response); 
    return response;
}

const submit = () => {
    errorMessage.value = ""; // Clear any previous error messages

    // Print the form data for debugging purposes
    console.log("Form Data:", {
        title: form.title,
        description: form.description,
        image_url: form.image_url,
    });

    // Check if all required fields are filled
    if (!form.title || !form.description || !form.image_url) {
        errorMessage.value = "Image, Title and Description are required.";
        return;
    }

    form.post(route("post.uploadPost"), {
        onSuccess: () => {
            // Handle successful form submission
            console.log("Form submitted successfully!");
            localStorage.setItem('notification', 'successPost');
            window.location.reload();
        },
        onError: (errors) => {
            // Handle errors from the server
            console.error("Form submission error:", errors);
            errorMessage.value = "An error occurred while submitting the form.";
        },
    });
};
</script>
<template>
    <div class="bg-website">
    <q-layout view="hHh lpR fFf">
        <q-header
            elevated
            class="bg-navbar text-grey-8 q-py-xs z-10"
            height-hint="80"
        >
            <q-toolbar>
                <q-btn flat @click="drawer = !drawer" round dense icon="menu" />

                <Link :href="route('dashboard')">
                    <q-toolbar-title
                        v-if="$q.screen.gt.sm"
                        shrink
                        class="ml-5 row items-center no-wrap"
                    >
                        <button
                            class="btn btn-ghost flex items-center gap-2 text-2xl text-black"
                        >
                            <img
                                src='/storage/images/FinalLogoStray.png'
                                alt="Logo"
                                class="w-8 h-8"
                            />
                            StraySafe
                        </button>
                    </q-toolbar-title>
                </Link>

                <q-space />

                <!-- <q-input
                class="GPL__toolbar-input"
                dense
                standout="bg-primary"
                v-model="search"
                @input="updateSearch"
                placeholder="Search"
            >
                <template v-slot:prepend>
                    <q-icon v-if="search === ''" name="search" :style="{ color: siteSettings.icon_color }" />
                    <q-icon
                        v-else
                        name="clear"
                        class="cursor-pointer"
                        @click="clearSearch"
                        :style="{ color: siteSettings.icon_color }" 
                    />
                </template>
            </q-input> -->

                <q-btn
                    @click="thepost = true"
                    v-if="$q.screen.gt.xs && authUser"
                    flat
                    rounded
                    dense
                    no-wrap
                    color="black"
                    icon="add"
                    no-caps
                    class="q-ml-sm q-px-md"
                    
                >
                    Create
                </q-btn>
                <div class="q-gutter-sm row items-center no-wrap">
                    <!-- <Link v-if="authUser" >
                        <q-btn
                            round
                            dense
                            flat
                            color="text-grey-7"
                            icon="message"
                            class="mr-2"
                            :style="{ color: siteSettings.icon_color }" 
                        >
                            <q-tooltip>Message</q-tooltip>
                        </q-btn>
                    </Link> -->
                    <q-btn round dense flat color="grey-8" icon="notifications" >
                        <q-badge color="red" text-color="white" floating>
                            2
                        </q-badge>
                        <q-tooltip>Notifications</q-tooltip>
                    </q-btn>
                    <q-btn dense flat no-wrap v-if="authUser">
                        <q-avatar rounded size="35px">
                            <img
                                style="background: white; border-radius: 20px"
                                :src="authUser.profile_image_url
                                    ? `/storage/images/${authUser.profile_image_url}`
                                    : '/storage/images/TEMPPROFILE.png'"
                                alt="Profile Image"
                            />
                        </q-avatar>
                        <q-icon name="arrow_drop_down" size="19px"  />

                        <q-menu auto-close>
                            <q-list dense>
                                <q-item class="GL__menu-link-signed-in">
                                    <q-item-section>
                                        <div>
                                            Signed in as
                                            <strong>{{ authUser.name }}</strong>
                                        </div>
                                    </q-item-section>
                                </q-item>
                                <q-separator />
                                <q-separator />
                                <q-item clickable class="GL__menu-link">
                                    <q-item-section
                                        ><Link
                                            :href="route('profile.edit')"
                                            >Your profile</Link
                                        ></q-item-section
                                    >
                                </q-item>
                                <q-item clickable class="GL__menu-link">
                                      <q-item-section
                                        ><Link
                                            :href="route('profile.edit')"
                                            >Edit profile</Link
                                        ></q-item-section>
                                </q-item>

                                <q-item clickable class="GL__menu-link">
                                    <q-item-section
                                        ><Link
                                            :href="route('logout')"
                                            method="post"
                                            as="button"
                                            >Logout
                                        </Link></q-item-section
                                    >
                                </q-item>
                            </q-list>
                        </q-menu>
                    </q-btn>

                    <!-- Guest view -->
                    <div v-else>
                        <Link :href="route('login')">
                            <q-btn flat rounded dense no-wrap color="black">
                                Login
                            </q-btn>
                        </Link>
                        <Link :href="route('register')">
                            <q-btn flat rounded dense no-wrap color="black">
                                Register
                            </q-btn>
                        </Link>
                    </div>
                </div>
            </q-toolbar>
        </q-header>

        <q-drawer
            v-model="drawer"
            show-if-above
            :mini="miniState"
            @mouseover="miniState = false"
            @mouseout="miniState = true"
            mini-to-overlay
            :width="250"
            :breakpoint="500"
            bordered
            elevated
            color="primary"
        >
            <q-scroll-area class="fit" :horizontal-thumb-style="{ opacity: 0 }">
                <q-list padding>
                    <Link :href="route('dashboard')">
                        <q-item clickable class="GPL__drawer-item">
                            <q-item-section avatar>
                                <q-icon name="dashboard" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Dashboard</q-item-label>
                            </q-item-section>
                        </q-item>
                    </Link>

                    <Link :href="route('map')">
                        <q-item clickable class="GPL__drawer-item">
                            <q-item-section avatar>
                                <q-icon name="map" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Stray Map</q-item-label>
                            </q-item-section>
                        </q-item>
                    </Link>

                    <!-- <Link :href="route('mindfulcoloring')">
                        <q-item clickable class="GPL__drawer-item">
                            <q-item-section avatar>
                                <q-icon name="brush" :style="{ color: siteSettings.icon_color }" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Mindful Coloring</q-item-label>
                            </q-item-section>
                        </q-item>
                    </Link> -->

                    <Link >
                        <q-item clickable class="GPL__drawer-item">
                            <q-item-section avatar>
                                <q-icon name="crisis_alert" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Stray Alert</q-item-label>
                            </q-item-section>
                        </q-item>
                    </Link>
                    <Link :href="route('cctv.monitor')">
                        <q-item clickable class="GPL__drawer-item">
                            <q-item-section avatar>
                                <q-icon name="videocam" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Barangay CCTV</q-item-label>
                            </q-item-section>
                        </q-item>
                    </Link>
                    <q-separator class="q-my-md" />
                    <Link>
                        <q-item clickable class="GPL__drawer-item">
                            <q-item-section avatar>
                                <q-icon name="fa-solid fa-user"/>
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Profile Page</q-item-label>
                            </q-item-section>
                        </q-item>
                    </Link>

                    <Link >
                        <q-item clickable class="GPL__drawer-item">
                            <q-item-section avatar>
                                <q-icon name="fa-solid fa-gear" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Profile Settings</q-item-label>
                            </q-item-section>
                        </q-item>
                    </Link>

                    <!-- <q-separator v-if="isAdmin" class="q-my-md" /> -->

                    <!-- <Link v-if="isAdmin" :href="route('manage.users')">
                        <q-item clickable class="GPL__drawer-item">
                            <q-item-section avatar>
                                <q-icon name="fa-solid fa-user-pen"  />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Manage Users</q-item-label>
                            </q-item-section>
                        </q-item>
                    </Link> -->

                    
                    <!-- <Link v-if="isAdmin" >
                        <q-item clickable class="GPL__drawer-item">
                            <q-item-section avatar>
                                <q-icon name="fa-solid fa-pen-to-square"/>
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Manage Website</q-item-label>
                            </q-item-section>
                        </q-item>
                    </Link> -->

                    <!-- <q-separator v-if="isAdmin" class="q-my-md" /> -->
                </q-list>
            </q-scroll-area>
        </q-drawer>
        <q-dialog
        v-model="thepost"
        backdrop-filter="blur(4px) saturate(150%)"
        persistent
    >
        <div
            class="instagram-card-2 bg-white rounded-lg shadow-lg overflow-hidden max-w-half"
            style="width: 90vw; height: 70vh"
        >
            <div class="flex justify-start p-8 bg-gray-100">
                <h4 class="text-2xl font-bold">Create Post</h4>
            </div>

            <div
                class="flex flex-col gap-8 p-8 overflow-y-auto"
                style="height: calc(100% - 64px)"
            >
                <form @submit.prevent="submit">
                    <!-- File input for image upload -->
                    <file-pond 
                        name="image"
                        ref="pond"
                        class-name="my-pond"
                        label-idle="Drop files here or click to upload"
                        allow-multiple="true"
                        credits="false"
                        accepted-file-types="image/jpeg, image/png"
                        :server="{
                            url:'',
                            process: {
                                url:'/upload-image',
                                method: 'POST',
                                onload: handleFilePondLoad
                            },
                            revert: handleFilePondRevert,
                            headers:{
                                'X-CSRF-TOKEN': $page.props.csrf_token
                            }
            
                        }"
                    ></file-pond>

                    <!-- Title input -->
                    <div class="q-pa-md">
                        <q-input
                            v-model="form.title"
                            rounded
                            outlined
                            type="text"
                            label="Title"
                            class="w-full text-xl"
                        />
                    </div>

                    <!-- Description input -->
                    <div class="q-pa-md">
                        <q-input
                            v-model="form.description"
                            rounded
                            outlined
                            type="textarea"
                            label="Description"
                            class="w-full text-xl"
                        />
                    </div>

                    <!-- Error message display -->
                    <div
                        v-if="errorMessage"
                        class="q-pa-md text-red-500 text-lg"
                    >
                        {{ errorMessage }}
                    </div>

                    <!-- Submit button -->
                    <div class="q-pa-md flex justify-end gap-4">
                        <q-btn
                            color="positive"
                            label="Submit"
                            type="submit"
                            class="text-lg"
                        />
                        <q-btn
                            flat
                            color="negative"
                            label="Cancel"
                            v-close-popup
                            class="text-lg"
                        />
                    </div>
                </form>
            </div>
        </div>
    </q-dialog>
        <q-page-container>
            <slot :search="search"/>
        </q-page-container>
    </q-layout>
</div>
</template>

<style lang="sass">
.GPL

  &__toolbar
    height: 64px

  &__toolbar-input
    width: 35%

  &__drawer-item
    line-height: 24px
    border-radius: 0 24px 24px 0

    .q-item__section--avatar
      padding-left: 10px
      .q-icon
        color: #5f6368

    .q-item__label:not(.q-item__label--caption)
      color: #3c4043
      letter-spacing: .01785714em
      font-size: .875rem
      font-weight: 500
      line-height: 1.25rem

    &--storage
      border-radius: 0
      margin-right: 0
      padding-top: 24px
      padding-bottom: 24px

  &__side-btn
    &__label
      font-size: 12px
      line-height: 24px
      letter-spacing: .01785714em
      font-weight: 500

  @media (min-width: 1024px)
    &__page-container
      padding-left: 94px
</style>

<style scoped>
.bg-website{
    background-color: #F8F3EC;
}
.text-brand {
    color: #a2aa33 !important;
}
.bg-navbar {
    background: white !important;
}

.bg-buttons {
    background: #efd6d5 !important;
}

.bg-base-200 {
    background-color: #f5f5f5;
}

.file-input {
    width: 100%;
    max-width: 500px;
}

.max-w-full {
    max-width: 90%;
}

.max-w-half {
    max-width: 50%;
}


.shadow-lg {
    box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
}

.p-10 {
    padding: 2.5rem;
}

.p-8 {
    padding: 2rem;
}

.instagram-card-2 {
    width: 90vh;
    border: 1px solid #ddd;
    border-radius: 10px;
    box-shadow: 12px 17px 51px rgba(0, 0, 0, 0.22);
    margin: 0 auto;
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
}
</style>
