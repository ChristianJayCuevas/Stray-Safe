<script setup>
import { Link } from '@inertiajs/vue3';
import ScrollToSection from '@/Components/WelcomeComponents/ScrollToSection.vue';
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

    // Set the corresponding radio button as checked
    const tab = document.getElementById(tabId);
    if (tab) {
        tab.checked = true;
    }
}
</script>
<template>

    <div class="background-website">
        <div class="custom-navbar">
            <a class="generic-container" href="#">
                <img src="/storage/images/FinalLogoStray.png" alt="Logo" class="logo-size" />
                <span class="custom-text">StraySafe</span>
            </a>
            <div class="tab-container">
                <input type="radio" name="tab" id="tab1" class="tab tab--1" />
                <label class="tab_label" for="tab1" @click="scrollToSection('#hero')">Home</label>

                <input type="radio" name="tab" id="tab2" class="tab tab--2" />
                <label class="tab_label" for="tab2" @click="scrollToSection('#features')">Features</label>

                <input type="radio" name="tab" id="tab3" class="tab tab--3" />
                <label class="tab_label" for="tab3" @click="scrollToSection('#highlights')">Highlights</label>

                <div class="indicator"></div>
            </div>

            <div class="generic-container">
                <Link href="/login"><q-btn label="Log in" padding="xs md" class="btn-color-login" rounded flat /></Link>
                <Link href="/register"><q-btn label="Sign Up" padding="xs md" class="btn-color-register" flat rounded />
                </Link>
            </div>
        </div>
        <div id="home" class="landing-wrapper overflow-hidden">
            <div id="hero">
                <div class="hero-text-container">
                    <h1 class="hero-text-heading">
                        Caring for strays and Securing streets
                    </h1>
                    <p class="hero-text-subheading">
                        Detecting strays, monitoring their locations and finding their homes.
                    </p>
                    <div class="mt-4">
                        <q-btn label="Get Started" push rounded class="btn-color-register" size="20px"></q-btn>
                    </div>
                </div>
                <div class="hero-container relative">
                    <div class="hero-image-container">
                        <img src="/storage/images/WebHero.png" alt="Hero Image" class="hero-image" />
                    </div>
                    <div class="custom-shape">
                        <svg viewBox="0 0 1440 400" xmlns="http://www.w3.org/2000/svg" class="wave"
                            preserveAspectRatio="none">
                            <path fill="#91D2CC" fill-opacity="0.2" d="M0,160L1440,64L1440,400L0,400Z"></path>
                        </svg>
                    </div>
                </div>
            </div>
            <div id="features">
    <div class="feature-grid spaced-grid">
        <div class="feature-heading">
            <div class="feature-title">Marvelous Features</div>
            <span class="feature-subtitle">Empowering smart city solutions</span>
        </div>

        <!-- Feature 1: Classifying Stray Animals -->
        <div class="feature-card">
            <div class="feature-card-inner">
                <div class="feature-card-content">
                    <div class="feature-icon-container">
                        <i class="fa-solid fa-dog text-4xl text-teal-700"></i>
                    </div>
                    <div class="feature-card-title">Classifying Stray Animals</div>
                    <span class="feature-card-description">Instantly identifies strays based on collar or leash detection.</span>
                </div>
            </div>
        </div>

        <!-- Feature 2: Real-Time Detection -->
        <div class="feature-card">
            <div class="feature-card-inner">
                <div class="feature-card-content">
                    <div class="feature-icon-container">
                        <i class="fa-solid fa-video text-4xl text-teal-700"></i>
                    </div>
                    <div class="feature-card-title">Real-Time Detection</div>
                    <span class="feature-card-description">Live CCTV feed for immediate stray identification.</span>
                </div>
            </div>
        </div>

        <!-- Feature 3: Location Pinning -->
        <div class="feature-card">
            <div class="feature-card-inner">
                <div class="feature-card-content">
                    <div class="feature-icon-container">
                        <i class="fa-solid fa-map-pin text-4xl text-teal-700"></i>
                    </div>
                    <div class="feature-card-title">Location Pinning</div>
                    <span class="feature-card-description">Maps stray locations for quick tracking and response.</span>
                </div>
            </div>
        </div>

        <!-- Feature 4: Notification System -->
        <div class="feature-card">
            <div class="feature-card-inner">
                <div class="feature-card-content">
                    <div class="feature-icon-container">
                        <i class="fa-solid fa-bell text-4xl text-teal-700"></i>
                    </div>
                    <div class="feature-card-title">Notification System</div>
                    <span class="feature-card-description">Alerts animal pound and pet owners instantly.</span>
                </div>
            </div>
        </div>

        <!-- Feature 5: Web and Mobile Application -->
        <div class="feature-card">
            <div class="feature-card-inner">
                <div class="feature-card-content">
                    <div class="feature-icon-container">
                        <i class="fa-solid fa-globe text-4xl text-teal-700"></i>
                        <i class="fa-solid fa-mobile-alt text-4xl text-teal-700"></i>
                    </div>
                    <div class="feature-card-title">Web & Mobile App</div>
                    <span class="feature-card-description">Monitor strays and register pets on any device.</span>
                </div>
            </div>
        </div>

        <!-- Feature 6: Feature Matching -->
        <div class="feature-card">
            <div class="feature-card-inner">
                <div class="feature-card-content">
                    <div class="feature-icon-container">
                        <i class="fa-solid fa-check-double text-4xl text-teal-700"></i>
                    </div>
                    <div class="feature-card-title">Feature Matching</div>
                    <span class="feature-card-description">Smart matching to identify registered pets swiftly.</span>
                </div>
            </div>
        </div>
    </div>
</div>




            <!-- Paste here -->
            <div id="highlights">
    <div class="text-center">
        <div class="highlight-title">Powerful Everywhere</div>
        <span class="highlight-subtitle">Web application and Mobile application</span>
    </div>

    <!-- First Section with Violet Box -->
    <div class="grid-container">
        <div class="grid-item">
            <img src="/storage/images/Mockup.png" class="w-11/12" alt="mockup mobile" />
        </div>

        <div class="grid-item-content">
            <div class="icon-container">
                <i class="material-icons text-4xl">devices</i>
            </div>
            <div class="text-large">Wide Compatibility</div>
            <span class="text-medium">Works seamlessly on both web and mobile platforms for maximum reach.</span>
        </div>
    </div>

    <!-- New Section with Yellow Box (Fixed and Aligned Text) -->
    <div class="grid-container">
        <div class="grid-item">
    <img src="/storage/images/userfriendly.png" class="w-11/12" alt="Pet and User Friendly Mockup" />
</div>
<div class="grid-item-content">
    <div class="icon-container">
        <i class="fa-solid fa-heart text-2xl text-red-600"></i>
    </div>
    <div class="text-large">Pet and User Friendly</div>
    <span class="text-medium">Designed for ease of use, making it simple for owners and effective for identifying lost pets.</span>
</div>

    </div>
</div>

            <div class="py-6 px-6 mx-0 mt-20 lg:mx-20">
                <div class="grid grid-cols-12 gap-4">
                    <!-- <div class="col-span-12 md:col-span-2">
                        <a class="generic-container" href="#">
                            <img src="/storage/images/FinalLogoStray.png" alt="Logo" class="logo-size" />
                            <span class="custom-text">StraySafe</span>
                        </a>
                    </div> -->

                    <div class="col-span-12 md:col-span-10">
                        <!-- <div class="grid grid-cols-12 gap-8 text-center md:text-left">
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
                        </div> -->
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
<style src="../../css/welcome.css"></style>


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