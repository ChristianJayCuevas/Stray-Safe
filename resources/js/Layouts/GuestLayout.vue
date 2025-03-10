<template>
    <div class="flex min-h-screen items-center justify-center background-website px-4 sm:px-6 md:px-8 lg:px-10 pt-6 sm:pt-0 dark:bg-gray-900">
        <div class="flex flex-col md:flex-row w-full max-w-6xl h-auto md:h-[700px] rounded-2xl shadow-2xl overflow-hidden dark:bg-gray-800">
            <!-- Left side: Slot with its own container -->
            <div class="flex flex-col justify-center items-center w-full md:w-[35%] p-6 md:p-10 bg-white shadow-xl rounded-t-2xl md:rounded-t-none md:rounded-l-2xl dark:bg-gray-700">
                <div class="w-full">
                    <div class="mb-6 md:mb-8 flex justify-center items-center">
                        <img src="/storage/images/NEWLOGO.png" alt="Logo" class="w-10 h-10 mr-2" />
                        <span class="custom-text font-poppins">Stray<span class="custom-color">Safe</span></span>
                    </div>
                    <slot />
                </div>
            </div>

            <!-- Right side: Image with overlay -->
            <div class="md:block md:w-[65%] relative h-full">
                <div class="absolute inset-0 bg-gradient-to-r from-[#4f6642]/40 to-[#38a3a5]/30 z-10"></div>
                <img 
                    v-if="page === 'register'" 
                    src="/storage/images/PersonRegistering2.png" 
                    alt="Person Registering" 
                    class="object-cover w-full h-full" 
                />
                <img 
                    v-if="page === 'login'" 
                    src="/storage/images/PersonLearning.png" 
                    alt="Person Learning" 
                    class="object-cover w-full h-full" 
                />
                <div class="absolute bottom-10 left-10 right-10 text-white z-20">
                    <h2 class="text-2xl md:text-3xl font-bold mb-2">Welcome to StraySafe</h2>
                    <p class="text-base md:text-lg">Using technology to create safer, more compassionate communities</p>
                </div>
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
    background-color: #F5F5DC;
}
.custom-text {
    color: var(--surface-900); 
    font-weight: 700; 
    font-size: 1.5rem; 
    line-height: 2rem;
}
.custom-color{
    color: #4f6642;
}
</style>
