<script setup>
import { Head, Link, usePage } from '@inertiajs/vue3';
import NavLink from '@/Components/NavLink.vue';
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
    <div class="background-website dark:bg-surface-900">
        <div class="py-6 mx-0 md:mx-12 lg:mx-0 lg:px-10 flex items-center justify-between navbar-sticky">
            <a class="flex items-center" href="#">
                <img src="/storage/images/FinalLogoStray.png" alt="Logo" class="w-13 h-12 mr-2 mb-1" />
                <span
                    class="text-surface-900 dark:text-surface-0 font-medium text-2xl leading-normal mr-20">StraySafe</span>
            </a>

            <div class="tab-container">
                <input type="radio" name="tab" id="tab1" class="tab tab--1" />
                <label class="tab_label" for="tab1" @click.prevent="scrollToSection('#hero', 'tab1')">Home</label>
                <input type="radio" name="tab" id="tab2" class="tab tab--2" />
                <label class="tab_label" for="tab2"
                    @click.prevent="scrollToSection('#features', 'tab2')">Features</label>
                <div class="indicator"></div>
            </div>

            <div class="flex items-center">
                <Link href="/login"><q-btn label="Login" padding="xs lg" class="btn-color-2" rounded flat /></Link>
                <Link href="/register"><q-btn label="Register" padding="xs lg" class="btn-color" flat rounded /></Link>
            </div>

        </div>
        <div id="home" class="landing-wrapper overflow-hidden">
            <div id="hero" class="flex flex-col pt-6 px-6 lg:px-20 mt-6 overflow-hidden">
                <div class="mx-6 md:mx-20 mt-2 md:mt-6 text-center">
                    <h1 class="text-6xl font-bold text-gray-900 leading-tight">
                        Caring for strays and Securing streets
                    </h1>
                    <p class="font-normal text-2xl leading-normal md:mt-4 text-gray-700">
                        Detecting strays, monitoring their locations and finding their homes.
                    </p>
                    <div class="mt-4">
                        <q-btn label="Get Started" push rounded class="btn-color" size="20px"></q-btn>
                    </div>
                </div>
                <div class="hero-container relative">
                    <div class="flex justify-center md:justify-end" style="transform: translateY(90px);">
                        <img src="/storage/images/WebHero.png" alt="Hero Image"
                            class="w-70 h-70 md:w-auto relative z-10" />
                    </div>
                    <div class="custom-shape">
                        <svg viewBox="0 0 1440 400" xmlns="http://www.w3.org/2000/svg" class="wave"
                            preserveAspectRatio="none">
                            <path fill="#91D2CC" fill-opacity="0.2" d="M0,160L1440,64L1440,400L0,400Z"></path>
                        </svg>
                    </div>
                </div>
            </div>
            <div id="features" class="py-6 px-6 lg:px-20 mt-8 mx-0 lg:mx-20">
                <div class="grid grid-cols-12 gap-4 justify-center">
                    <div class="col-span-12 text-center mt-20 mb-6">
                        <div class="text-surface-900 dark:text-surface-0 font-normal mb-2 text-4xl">Marvelous Features
                        </div>
                        <span class="text-muted-color text-2xl">Useful in building smart cities</span>
                    </div>

                    <div class="col-span-12 md:col-span-12 lg:col-span-4 p-0 lg:pr-8 mt-6 lg:mt-0">
                        <div
                            style="height: 160px; padding: 2px; border-radius: 10px; background: linear-gradient(90deg, rgba(145, 210, 204, 0.2), rgba(160, 210, 250, 0.2)), linear-gradient(180deg, rgba(187, 199, 205, 0.2), rgba(145, 210, 204, 0.2))">
                            <div class="p-4 bg-surface-0 dark:bg-surface-900 h-full" style="border-radius: 8px">
                                <div class="flex items-center justify-center bg-teal-200 mb-4"
                                    style="width: 3.5rem; height: 3.5rem; border-radius: 10px">
                                    <i class="pi pi-fw pi-shopping-cart !text-2xl text-teal-700"></i>
                                </div>
                                <div class="mt-6 mb-1 text-surface-900 dark:text-surface-0 text-xl font-semibold">
                                    Classifying Stray Animals</div>
                                <span class="text-surface-600 dark:text-surface-200">It can classify stray animals in a
                                    footage.</span>
                            </div>
                        </div>
                    </div>

                    <div class="col-span-12 md:col-span-12 lg:col-span-4 p-0 lg:pr-8 mt-6 lg:mt-0">
                        <div
                            style="height: 160px; padding: 2px; border-radius: 10px; background: linear-gradient(90deg, rgba(145, 210, 204, 0.2), rgba(212, 162, 221, 0.2)), linear-gradient(180deg, rgba(251, 199, 145, 0.2), rgba(160, 210, 250, 0.2))">
                            <div class="p-4 bg-surface-0 dark:bg-surface-900 h-full" style="border-radius: 8px">
                                <div class="flex items-center justify-center bg-blue-200 mb-4"
                                    style="width: 3.5rem; height: 3.5rem; border-radius: 10px">
                                    <i class="pi pi-fw pi-globe !text-2xl text-blue-700"></i>
                                </div>
                                <div class="mt-6 mb-1 text-surface-900 dark:text-surface-0 text-xl font-semibold">
                                    Monitoring Locations</div>
                                <span class="text-surface-600 dark:text-surface-200">It can pin the location of a stray
                                    in the footage.</span>
                            </div>
                        </div>
                    </div>

                    <div class="col-span-12 md:col-span-12 lg:col-span-4 p-0 lg-4 mt-6 lg:mt-0">
                        <div
                            style="height: 160px; padding: 2px; border-radius: 10px; background: linear-gradient(90deg, rgba(160, 210, 250, 0.2), rgba(212, 162, 221, 0.2)), linear-gradient(180deg, rgba(246, 158, 188, 0.2), rgba(212, 162, 221, 0.2))">
                            <div class="p-4 bg-surface-0 dark:bg-surface-900 h-full" style="border-radius: 8px">
                                <div class="flex items-center justify-center bg-purple-200 mb-4"
                                    style="width: 3.5rem; height: 3.5rem; border-radius: 10px">
                                    <i class="pi pi-fw pi-eye !text-2xl text-purple-700"></i>
                                </div>
                                <div class="mt-6 mb-1 text-surface-900 dark:text-surface-0 text-xl font-semibold">
                                    Notifying Authorities & Citizens</div>
                                <span class="text-surface-600 dark:text-surface-200">It can notify authorities and
                                    citizens of a stray.</span>
                            </div>
                        </div>
                    </div>

                    <!-- <div class="col-span-12 mt-20 mb-20 p-2 md:p-20"
                        style="border-radius: 20px; background: linear-gradient(0deg, rgba(255, 255, 255, 0.6), rgba(255, 255, 255, 0.6)), radial-gradient(77.36% 256.97% at 77.36% 57.52%, #efe1af 0%, #c3dcfa 100%)">
                        <div class="flex flex-col justify-center items-center text-center px-4 py-4 md:py-0">
                            <div class="text-gray-900 mb-2 text-3xl font-semibold">Joséphine Miller</div>
                            <span class="text-gray-600 text-2xl">Peak Interactive</span>
                            <p class="text-gray-900 sm:line-height-2 md:line-height-4 text-2xl mt-6"
                                style="max-width: 800px">
                                “Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat
                                nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui
                                officia deserunt mollit anim id est laborum.”
                            </p>
                            <img src="/demo/images/landing/peak-logo.svg" class="mt-6" alt="Company logo" />
                        </div>
                    </div> -->
                </div>
            </div>
            <!-- Paste here -->
        </div>
    </div>
</template>
<style scoped>
.hero-container {
    position: relative;
    width: 100%;
    margin-bottom: 40px;
    /* Adjust as needed */
}

.custom-shape {
    position: relative;
    width: 100vw;
    left: 50%;
    right: 50%;
    margin-left: -50vw;
    margin-right: -50vw;
    overflow: hidden;
    line-height: 0;
    margin-top: -80px;
}

.wave {
    position: relative;
    display: block;
    width: 100%;
    height: clamp(200px, 30vw, 400px);
    /* Increased height */
}

/* Responsive adjustments */
@media (max-width: 767px) {
    .wave {
        height: clamp(150px, 25vw, 300px);
    }
}

@media (min-width: 768px) and (max-width: 1024px) {
    .wave {
        height: clamp(175px, 28vw, 350px);
    }
}

.btn-color-2 {
    background-color: transparent;
    color: black;
}

.btn-color {
    background-color: #38a3a5;
    color: white;
}

.transparent-button {
    display: inline-block;
    padding: 8px 16px;
    /* Adjust for desired size */
    border: 2px solid rgba(255, 255, 255, 0.5);
    /* Light, semi-transparent border */
    background-color: transparent;
    /* Transparent background */
    color: black;
    /* Text color (adjust as needed) */
    border-radius: 25px;
    /* Rounded corners */
    font-size: 16px;
    /* Adjust font size as needed */
    text-align: center;
    cursor: pointer;
    transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}

.transparent-button:hover {
    background-color: rgba(255, 255, 255, 0.1);
    /* Light hover effect */
    color: #ffffff;
    /* Ensure text remains visible */
    border-color: rgba(255, 255, 255, 0.8);
    /* Slightly more opaque border on hover */
}

.navbar-sticky {
    position: -webkit-sticky;
    /* For Safari */
    position: sticky;
    top: 0;
    z-index: 1000;
    background-color: #F8F3EC;
}

.background-website {
    background-color: #F8F3EC;
}

.hero-section {
    background: linear-gradient(0deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.2)),
        radial-gradient(77.36% 256.97% at 77.36% 57.52%, rgb(238, 239, 175) 0%, rgb(195, 227, 250) 100%);
    clip-path: ellipse(150% 87% at 93% 13%);
}

.feature-box {
    height: 160px;
    padding: 2px;
    border-radius: 10px;
}

.feature-box-1 {
    background: linear-gradient(90deg, rgba(145, 210, 204, 0.2), rgba(160, 210, 250, 0.2)),
        linear-gradient(180deg, rgba(187, 199, 205, 0.2), rgba(145, 210, 204, 0.2));
}

.feature-box-2 {
    background: linear-gradient(90deg, rgba(145, 210, 204, 0.2), rgba(212, 162, 221, 0.2)),
        linear-gradient(180deg, rgba(251, 199, 145, 0.2), rgba(160, 210, 250, 0.2));
}

.feature-box-3 {
    background: linear-gradient(90deg, rgba(160, 210, 250, 0.2), rgba(212, 162, 221, 0.2)),
        linear-gradient(180deg, rgba(246, 158, 188, 0.2), rgba(212, 162, 221, 0.2));
}

.feature-content {
    padding: 1rem;
    background-color: var(--surface-0);
    height: 100%;
    border-radius: 8px;
}

.dark .feature-content {
    background-color: var(--surface-900);
}

.icon-container {
    width: 3.5rem;
    height: 3.5rem;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1rem;
}

.testimonial-section {
    border-radius: 20px;
    background: linear-gradient(0deg, rgba(255, 255, 255, 0.6), rgba(255, 255, 255, 0.6)),
        radial-gradient(77.36% 256.97% at 77.36% 57.52%, #efe1af 0%, #c3dcfa 100%);
}

.feature-highlight {
    border-radius: 8px;
}

.highlight-icon {
    width: 4.2rem;
    height: 4.2rem;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.component-title {
    width: 100%;
    position: absolute;
    z-index: 999;
    top: 30px;
    left: 0;
    padding: 0;
    margin: 0;
    font-size: 1rem;
    font-weight: 700;
    color: transparent;
    text-align: center;
}

.tab-container {
    position: relative;

    display: flex;
    flex-direction: row;
    align-items: flex-start;

    padding: 2px;

    background-color: transparent;
    border-radius: 9px;
}

.indicator {
    content: "";
    width: 130px;
    height: 28px;
    background: #38a3a5;
    position: absolute;
    top: 2px;
    left: 2px;
    z-index: 9;
    border: 0.5px solid rgba(0, 0, 0, 0.04);
    box-shadow: 0px 3px 8px rgba(0, 0, 0, 0.12), 0px 3px 1px rgba(0, 0, 0, 0.04);
    border-radius: 7px;
    transition: all 0.2s ease-out;
}

.tab {
    width: 130px;
    height: 28px;
    position: absolute;
    z-index: 99;
    outline: none;
    opacity: 0;
}

.tab_label {
    width: 130px;
    height: 28px;
    color: black;
    position: relative;
    z-index: 999;

    display: flex;
    align-items: center;
    justify-content: center;

    border: 0;

    font-size: 0.75rem;
    opacity: 0.6;

    cursor: pointer;
}

.tab--1:checked~.indicator {
    left: 2px;
}

.tab--2:checked~.indicator {
    left: calc(130px + 2px);
}

.tab--3:checked~.indicator {
    left: calc(130px * 2 + 2px);
}

.tab--4:checked~.indicator {
    left: calc(130px * 3 + 2px);
}
</style>

<!-- Paste it to the top
 <div id="highlights" class="py-6 px-6 lg:px-20 mx-0 my-12 lg:mx-20">
                <div class="text-center">
                    <div class="text-surface-900 dark:text-surface-0 font-normal mb-2 text-4xl">Powerful Everywhere
                    </div>
                    <span class="text-muted-color text-2xl">Amet consectetur adipiscing elit...</span>
                </div>

                <div class="grid grid-cols-12 gap-4 mt-20 pb-2 md:pb-20">
                    <div class="flex justify-center col-span-12 lg:col-span-6 bg-purple-100 p-0 order-1 lg:order-none"
                        style="border-radius: 8px">
                        <img src="/demo/images/landing/mockup.svg" class="w-11/12" alt="mockup mobile" />
                    </div>

                    <div
                        class="col-span-12 lg:col-span-6 my-auto flex flex-col lg:items-end text-center lg:text-right gap-4">
                        <div class="flex items-center justify-center bg-purple-200 self-center lg:self-end"
                            style="width: 4.2rem; height: 4.2rem; border-radius: 10px">
                            <i class="pi pi-fw pi-mobile !text-4xl text-purple-700"></i>
                        </div>
                        <div class="leading-none text-surface-900 dark:text-surface-0 text-3xl font-normal">Congue
                            Quisque Egestas</div>
                        <span class="text-surface-700 dark:text-surface-100 text-2xl leading-normal ml-0 md:ml-2"
                            style="max-width: 650px">Lectus arcu bibendum at varius vel pharetra vel turpis nunc. Eget
                            aliquet nibh praesent tristique magna sit amet purus gravida. Sit amet mattis vulputate enim
                            nulla aliquet.</span>
                    </div>
                </div>

                <div class="grid grid-cols-12 gap-4 my-20 pt-2 md:pt-20">
                    <div
                        class="col-span-12 lg:col-span-6 my-auto flex flex-col text-center lg:text-left lg:items-start gap-4">
                        <div class="flex items-center justify-center bg-yellow-200 self-center lg:self-start"
                            style="width: 4.2rem; height: 4.2rem; border-radius: 10px">
                            <i class="pi pi-fw pi-desktop !text-3xl text-yellow-700"></i>
                        </div>
                        <div class="leading-none text-surface-900 dark:text-surface-0 text-3xl font-normal">Celerisque
                            Eu Ultrices</div>
                        <span class="text-surface-700 dark:text-surface-100 text-2xl leading-normal mr-0 md:mr-2"
                            style="max-width: 650px">Adipiscing commodo elit at imperdiet dui. Viverra nibh cras
                            pulvinar mattis nunc sed blandit libero. Suspendisse in est ante in. Mauris pharetra et
                            ultrices neque ornare aenean euismod elementum nisi.</span>
                    </div>

                    <div class="flex justify-end order-1 sm:order-2 col-span-12 lg:col-span-6 bg-yellow-100 p-0"
                        style="border-radius: 8px">
                        <img src="/demo/images/landing/mockup-desktop.svg" class="w-11/12" alt="mockup" />
                    </div>
                </div>
            </div>
<div class="py-6 px-6 mx-0 mt-20 lg:mx-20">
    <div class="grid grid-cols-12 gap-4">
        <div class="col-span-12 md:col-span-2">
            <a href="#home" v-smooth-scroll
                class="flex flex-wrap items-center justify-center md:justify-start md:mb-0 mb-4 cursor-pointer">
                <h4 class="font-medium text-3xl text-surface-900 dark:text-surface-0">StraySafe</h4>
            </a>
        </div>

        <div class="col-span-12 md:col-span-10">
            <div class="grid grid-cols-12 gap-8 text-center md:text-left">
                <div class="col-span-12 md:col-span-3">
                    <h4
                        class="font-medium text-2xl leading-normal mb-4 text-surface-900 dark:text-surface-0">
                        Company</h4>
                    <a
                        class="leading-normal text-xl block cursor-pointer mb-2 text-surface-700 dark:text-surface-100">About
                        Us</a>
                    <a
                        class="leading-normal text-xl block cursor-pointer mb-2 text-surface-700 dark:text-surface-100">News</a>
                    <a
                        class="leading-normal text-xl block cursor-pointer mb-2 text-surface-700 dark:text-surface-100">Investor
                        Relations</a>
                    <a
                        class="leading-normal text-xl block cursor-pointer mb-2 text-surface-700 dark:text-surface-100">Careers</a>
                    <a
                        class="leading-normal text-xl block cursor-pointer text-surface-700 dark:text-surface-100">Media
                        Kit</a>
                </div>

                <div class="col-span-12 md:col-span-3">
                    <h4
                        class="font-medium text-2xl leading-normal mb-4 text-surface-900 dark:text-surface-0">
                        Resources</h4>
                    <a
                        class="leading-normal text-xl block cursor-pointer mb-2 text-surface-700 dark:text-surface-100">Get
                        Started</a>
                    <a
                        class="leading-normal text-xl block cursor-pointer mb-2 text-surface-700 dark:text-surface-100">Learn</a>
                    <a
                        class="leading-normal text-xl block cursor-pointer text-surface-700 dark:text-surface-100">Case
                        Studies</a>
                </div>

                <div class="col-span-12 md:col-span-3">
                    <h4
                        class="font-medium text-2xl leading-normal mb-4 text-surface-900 dark:text-surface-0">
                        Community</h4>
                    <a
                        class="leading-normal text-xl block cursor-pointer mb-2 text-surface-700 dark:text-surface-100">Discord</a>
                    <a
                        class="leading-normal text-xl block cursor-pointer mb-2 text-surface-700 dark:text-surface-100">Events<img
                            src="/demo/images/landing/new-badge.svg" class="ml-2" /></a>
                    <a
                        class="leading-normal text-xl block cursor-pointer mb-2 text-surface-700 dark:text-surface-100">FAQ</a>
                    <a
                        class="leading-normal text-xl block cursor-pointer text-surface-700 dark:text-surface-100">Blog</a>
                </div>

                <div class="col-span-12 md:col-span-3">
                    <h4
                        class="font-medium text-2xl leading-normal mb-4 text-surface-900 dark:text-surface-0">
                        Legal</h4>
                    <a
                        class="leading-normal text-xl block cursor-pointer mb-2 text-surface-700 dark:text-surface-100">Brand
                        Policy</a>
                    <a
                        class="leading-normal text-xl block cursor-pointer mb-2 text-surface-700 dark:text-surface-100">Privacy
                        Policy</a>
                    <a
                        class="leading-normal text-xl block cursor-pointer text-surface-700 dark:text-surface-100">Terms
                        of Service</a>
                </div>
            </div>
        </div>
    </div>
</div> -->