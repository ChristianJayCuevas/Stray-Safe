<template>
    <div class="flex min-h-screen items-center justify-center background-website pt-6 sm:pt-0 dark:bg-gray-900">
        <div class="flex w-full max-w-6xl bg-white rounded-lg shadow-xl overflow-hidden dark:bg-gray-800">
            <!-- Left side: Slot with its own container -->
            <div class="flex flex-col ml-10 my-10 justify-center items-center w-full max-w-md p-10 bg-white shadow-xl rounded-xl dark:bg-gray-700">
                <div class="w-full">
                    <slot />
                </div>
            </div>

            <!-- Right side: Image -->
            <div class="sm:block w-1/2">
                <img 
                    v-if="page === 'register'" 
                    src="/storage/images/PersonRegistering2.png" 
                    alt="Person Registering" 
                    class="object-cover h-full w-full rounded-r-lg ml-10" 
                />
                <img 
                    v-if="page === 'login'" 
                    src="/storage/images/PersonLearning.png" 
                    alt="Default Image" 
                    class="object-cover h-full w-full rounded-r-lg ml-10" 
                />
            </div>
        </div>
    </div>
</template>
<script setup>
const props = defineProps({
    page: {
        type: String,
        default: ''
    }
});
</script>


<style scoped>
.background-website{
    background-color: #F8F3EC;
}
</style>
