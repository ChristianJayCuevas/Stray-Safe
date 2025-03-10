<script setup>
import { Link } from '@inertiajs/vue3';
import { ref, computed, onMounted, onUnmounted, onBeforeUnmount, watch } from "vue";

const selectedTab = ref("tab1"); // Default selected tab
const mobileMenuOpen = ref(false); // State for mobile menu

onMounted(() => {
    selectedTab.value = "tab1"; // Ensures 'Home' is selected initially
});
const isScrolled = ref(false);

const indicatorStyle = computed(() => {
    let position = 2; // Default position for tab1
    if (selectedTab.value === "tab2") position = 110 + 2;
    if (selectedTab.value === "tab3") position = 110 * 2 + 2;
    if (selectedTab.value === "tab4") position = 110 * 3 + 2;
    return { left: `${position}px` };
});

function scrollToSection(sectionId, tabId) {
    const targetElement = document.querySelector(sectionId);
    if (!targetElement) return;

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

    // Update selected tab in Vue state
    selectedTab.value = tabId;
    // Close mobile menu after selection
    mobileMenuOpen.value = false;
}

const toggleMobileMenu = () => {
    mobileMenuOpen.value = !mobileMenuOpen.value;
};

const handleScroll = () => {
    isScrolled.value = window.scrollY > 50; // Change navbar when scrolled past 50px
};

const cardElements = ref([]);

onMounted(() => {
    window.addEventListener("scroll", handleScroll);

    // 3D Card Effect
    const cards = document.querySelectorAll('.feature-card, .grid-item');

    cards.forEach(card => {
        card.addEventListener('mousemove', handleMouseMove);
        card.addEventListener('mouseleave', handleMouseLeave);
        cardElements.value.push({
            element: card,
            moveHandler: handleMouseMove,
            leaveHandler: handleMouseLeave
        });
    });

    function handleMouseMove(e) {
        const card = this;
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Calculate rotation based on mouse position
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        // Calculate rotation angle (max 15 degrees)
        const rotateY = ((x - centerX) / centerX) * 15;
        const rotateX = -((y - centerY) / centerY) * 15;

        // Apply the transform with a slight delay for smoother effect
        requestAnimationFrame(() => {
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`;
        });

        // Add shine effect based on mouse position
        const shine = card.querySelector('.card-shine') || createShineElement(card);
        const shineX = (x / rect.width) * 100;
        const shineY = (y / rect.height) * 100;
        shine.style.background = `radial-gradient(circle at ${shineX}% ${shineY}%, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) 80%)`;
    }

    function handleMouseLeave() {
        const card = this;
        // Reset transform on mouse leave with smooth transition
        requestAnimationFrame(() => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
        });

        // Remove or hide shine effect
        const shine = card.querySelector('.card-shine');
        if (shine) {
            shine.style.background = 'none';
        }
    }

    function createShineElement(card) {
        const shine = document.createElement('div');
        shine.classList.add('card-shine');
        shine.style.position = 'absolute';
        shine.style.top = '0';
        shine.style.left = '0';
        shine.style.width = '100%';
        shine.style.height = '100%';
        shine.style.pointerEvents = 'none';
        shine.style.zIndex = '10';
        shine.style.borderRadius = 'inherit';
        card.appendChild(shine);
        return shine;
    }
});

onUnmounted(() => {
    window.removeEventListener("scroll", handleScroll);

    // Clean up event listeners
    cardElements.value.forEach(item => {
        item.element.removeEventListener('mousemove', item.moveHandler);
        item.element.removeEventListener('mouseleave', item.leaveHandler);

        // Remove shine elements
        const shine = item.element.querySelector('.card-shine');
        if (shine) {
            shine.remove();
        }
    });
});

const currentTeamIndex = ref(0);
const teamMembers = ref([
    {
        name: "Jane Doe",
        title: "Lead Developer",
        bio: "AI specialist with expertise in computer vision and machine learning models for animal recognition.",
        image: "/storage/images/team-member-1.jpg", // Replace with actual image path
        linkedin: "https://linkedin.com/",
        github: "https://github.com/"
    },
    {
        name: "John Smith",
        title: "UX/UI Designer",
        bio: "Creating intuitive interfaces for both web and mobile applications focused on animal welfare.",
        image: "/storage/images/team-member-2.jpg", // Replace with actual image path
        linkedin: "https://linkedin.com/",
        github: "https://github.com/"
    },
    {
        name: "Emily Johnson",
        title: "Project Manager",
        bio: "Coordinating between tech and animal welfare organizations to ensure maximum impact.",
        image: "/storage/images/team-member-3.jpg", // Replace with actual image path
        linkedin: "https://linkedin.com/"
    },
    {
        name: "Michael Chen",
        title: "Backend Developer",
        bio: "Building robust systems for real-time data processing and notification delivery.",
        image: "/storage/images/team-member-4.jpg", // Replace with actual image path
        linkedin: "https://linkedin.com/",
        github: "https://github.com/"
    },
    {
        name: "Sarah Williams",
        title: "Animal Behavior Specialist",
        bio: "Ensuring our technology considers animal welfare and behavior in all aspects.",
        image: "/storage/images/team-member-5.jpg", // Replace with actual image path
        linkedin: "https://linkedin.com/"
    }
]);

// Refs
const teamCarousel = ref(null);

// Set initial index to the middle of the carousel
// If you want to start with a different member, adjust this value
const initialTeamIndex = Math.floor(teamMembers.value.length / 2);
currentTeamIndex.value = initialTeamIndex;

// Lifecycle hooks
onMounted(() => {
    window.addEventListener('scroll', handleScroll);
    
    // Initialize the carousel with the center card active
    updateActiveCard();
    
    // Need to trigger initial scroll to center the active card
    // Small delay to ensure DOM is fully rendered
    setTimeout(() => {
        scrollTeamCarousel();
    }, 100);
    
    // Check for screen size and adjust if necessary
    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
});

onBeforeUnmount(() => {
    window.removeEventListener('scroll', handleScroll);
    window.removeEventListener('resize', checkScreenSize);
});

// Watch for changes in currentTeamIndex
watch(currentTeamIndex, () => {
    scrollTeamCarousel();
    updateActiveCard();
});

const nextTeamMember = () => {
    currentTeamIndex.value = (currentTeamIndex.value + 1) % (teamMembers.value.length + 1); // +1 for the duplicate
};

const prevTeamMember = () => {
    currentTeamIndex.value = (currentTeamIndex.value - 1 + (teamMembers.value.length + 1)) % (teamMembers.value.length + 1);
};

const goToTeamMember = (index) => {
    currentTeamIndex.value = index;
};

const scrollTeamCarousel = () => {
    if (teamCarousel.value) {
        const cards = teamCarousel.value.querySelectorAll('.team-card');
        if (!cards.length) return;
        
        const cardWidth = cards[0].offsetWidth;
        const gap = 20; // Same as defined in CSS
        
        // Calculate center position
        const containerWidth = teamCarousel.value.clientWidth;
        const carouselCenter = containerWidth / 2;
        const cardCenter = cardWidth / 2;
        
        // Calculate scroll position to center the current card
        let scrollPosition = currentTeamIndex.value * (cardWidth + gap);
        
        // Adjust for centering if we're not using CSS padding for initial centering
        // scrollPosition = scrollPosition - (carouselCenter - cardCenter);
        
        teamCarousel.value.scrollTo({
            left: scrollPosition,
            behavior: 'smooth'
        });
    }
};

const updateActiveCard = () => {
    if (teamCarousel.value) {
        const cards = teamCarousel.value.querySelectorAll('.team-card');
        cards.forEach((card, index) => {
            if (index === currentTeamIndex.value) {
                card.classList.add('active');
            } else {
                card.classList.remove('active');
            }
        });
    }
};

const checkScreenSize = () => {
    // Adjust scrolling behavior based on screen size
    if (window.innerWidth <= 768) {
        // For mobile, ensure we have proper snapping
        if (teamCarousel.value) {
            teamCarousel.value.style.scrollSnapType = 'x mandatory';
        }
    }
    
    // Force update active card after resize
    scrollTeamCarousel();
    setTimeout(updateActiveCard, 300); // Small delay to ensure scroll has completed
};
</script>
<template>
    <div class="background-website">
        <div :class="['custom-navbar', { 'glassmorphism': isScrolled, 'ellipse-shape': isScrolled }]">
            <a class="generic-container" href="#">
                <img src="/storage/images/NEWLOGO.png" alt="Logo" class="logo-size" />
                <span class="custom-text font-poppins">Stray<span class="custom-color">Safe</span></span>
            </a>

            <div class="tab-container">
                <input type="radio" name="tab" id="tab1" class="tab tab--1" v-model="selectedTab" value="tab1" />
                <label :class="{ active: selectedTab === 'tab1' }" class="tab_label font-poppins" for="tab1"
                    @click="scrollToSection('#hero', 'tab1')">Home</label>

                <input type="radio" name="tab" id="tab2" class="tab tab--2" v-model="selectedTab" value="tab2" />
                <label :class="{ active: selectedTab === 'tab2' }" class="tab_label font-poppins" for="tab2"
                    @click="scrollToSection('#features', 'tab2')">Features</label>

                <input type="radio" name="tab" id="tab3" class="tab tab--3" v-model="selectedTab" value="tab3" />
                <label :class="{ active: selectedTab === 'tab3' }" class="tab_label font-poppins" for="tab3"
                    @click="scrollToSection('#highlights', 'tab3')">Demo</label>

                <input type="radio" name="tab" id="tab4" class="tab tab--4" v-model="selectedTab" value="tab4" />
                <label :class="{ active: selectedTab === 'tab4' }" class="tab_label font-poppins" for="tab4"
                    @click="scrollToSection('#highlights', 'tab4')">About Us</label>

                <div class="indicator" :style="indicatorStyle"></div>
            </div>

            <div class="generic-container2">
                <Link href="/login">
                <button class="auth-btn btn-login">Log in</button>
                </Link>
                <Link href="/register">
                <button class="auth-btn btn-signup">Sign Up</button>
                </Link>
            </div>
        </div>

        <!-- Mobile Navigation -->
        <button class="mobile-nav-button" @click="toggleMobileMenu">
            <i class="fa-solid fa-paw"></i>
        </button>

        <div class="mobile-nav-menu" :class="{ 'active': mobileMenuOpen }">
            <div :class="['mobile-nav-item', { 'active': selectedTab === 'tab1' }]"
                @click="scrollToSection('#hero', 'tab1')">
                <i class="fa-solid fa-home mr-2"></i> Home
            </div>
            <div :class="['mobile-nav-item', { 'active': selectedTab === 'tab2' }]"
                @click="scrollToSection('#features', 'tab2')">
                <i class="fa-solid fa-list-check mr-2"></i> Features
            </div>
            <div :class="['mobile-nav-item', { 'active': selectedTab === 'tab3' }]"
                @click="scrollToSection('#highlights', 'tab3')">
                <i class="fa-solid fa-play mr-2"></i> Demo
            </div>
            <div :class="['mobile-nav-item', { 'active': selectedTab === 'tab4' }]"
                @click="scrollToSection('#highlights', 'tab4')">
                <i class="fa-solid fa-info-circle mr-2"></i> About Us
            </div>
            <div class="mobile-nav-divider"></div>
            <Link href="/login" class="mobile-nav-item mobile-nav-auth">
            <i class="fa-solid fa-sign-in-alt mr-2"></i> Log in
            </Link>
            <Link href="/register" class="mobile-nav-item mobile-nav-auth">
            <i class="fa-solid fa-user-plus mr-2"></i> Sign Up
            </Link>
        </div>

        <div class="landing-wrapper flex justify-center">
            <div id="hero" class="hero-card flex justify-center">
                <div class="hero-container">
                    <img src="/storage/images/HERO.png">
                </div>
                <div class="hero-content">
                    <div class="hero-text-container">
                        <p class="font-abril hero-text">Care for Strays,<br> Secure Streets</p>
                        <p class="font-poppins hero-normal">
                            Monitoring strays, Securing streets - <br>
                            Using technology to create safer, more<br> compassionate communities.
                        </p>
                    </div>
                    <div class="hero-button font-poppins">
                        <button>Get Started <img class="ml-7 mb-1" src="/storage/images/PAW.png"></button>
                    </div>
                </div>

            </div>
            <div id="features">
                <div class="feature-grid">
                    <div class="feature-heading">
                        <div class="feature-title font-poppins text-bold">Marvelous Features</div>
                        <span class="feature-subtitle font-poppins">Empowering smart city solutions</span>
                    </div>

                    <div class="feature-cards-container">
                        <div class="feature-card relative overflow-hidden">
                            <!-- Custom Semi-Circle -->
                            <div class="custom-semi-circle">
                                <span class="ml-7 text-4xl font-bold">01</span>
                            </div>

                            <div class="feature-card-inner">
                                <div class="feature-card-content">
                                    <div class="feature-icon-container">
                                        <i class="fa-solid fa-shield-dog ml-4 text-9xl text-[#1f3623]"></i>
                                    </div>
                                    <div class="feature-card-title font-poppins">Classifying Stray Animals</div>
                                    <span class="feature-card-description">Instantly identifies strays based on collar
                                        or
                                        leash detection.</span>
                                </div>
                            </div>
                        </div>


                        <div class="feature-card relative overflow-hidden">
                            <!-- Custom Semi-Circle -->
                            <div class="custom-semi-circle">
                                <span class="ml-7 text-4xl font-bold">02</span>
                            </div>

                            <div class="feature-card-inner">
                                <div class="feature-card-content">
                                    <div class="feature-icon-container">
                                        <i class="fa-solid fa-video ml-4 text-9xl text-[#1f3623]"></i>
                                    </div>
                                    <div class="feature-card-title font-poppins">Real-Time Detection</div>
                                    <span class="feature-card-description">Live CCTV feed for immediate stray
                                        identification.</span>
                                </div>
                            </div>
                        </div>

                        <div class="feature-card relative overflow-hidden">
                            <!-- Custom Semi-Circle -->
                            <div class="custom-semi-circle">
                                <span class="ml-7 text-4xl font-bold">03</span>
                            </div>

                            <div class="feature-card-inner">
                                <div class="feature-card-content">
                                    <div class="feature-icon-container">
                                        <i class="fa-solid fa-map-pin ml-4 text-9xl text-[#1f3623]"></i>
                                    </div>
                                    <div class="feature-card-title font-poppins">Location Pinning</div>
                                    <span class="feature-card-description">Maps stray locations for quick tracking and
                                        response.</span>
                                </div>
                            </div>
                        </div>

                        <div class="feature-card relative overflow-hidden">
                            <!-- Custom Semi-Circle -->
                            <div class="custom-semi-circle">
                                <span class="ml-7 text-4xl font-bold">04</span>
                            </div>

                            <div class="feature-card-inner">
                                <div class="feature-card-content">
                                    <div class="feature-icon-container">
                                        <i class="fa-solid fa-bell ml-4 text-9xl text-[#1f3623]"></i>
                                    </div>
                                    <div class="feature-card-title font-poppins">Notification System</div>
                                    <span class="feature-card-description">Alerts animal pound and pet owners
                                        instantly.</span>
                                </div>
                            </div>
                        </div>
                        <!-- Feature 4: Notification System -->
                        <div class="feature-card relative overflow-hidden">
                            <!-- Custom Semi-Circle -->
                            <div class="custom-semi-circle">
                                <span class="ml-7 text-4xl font-bold">05</span>
                            </div>

                            <div class="feature-card-inner">
                                <div class="feature-card-content">
                                    <div class="feature-icon-container">
                                        <i class="fa-solid fa-mobile-alt ml-4 text-9xl text-[#1f3623]"></i>
                                    </div>
                                    <div class="feature-card-title font-poppins">Web & Mobile App</div>
                                    <span class="feature-card-description">Monitor strays and register pets on any
                                        device.</span>
                                </div>
                            </div>
                        </div>

                        <div class="feature-card relative overflow-hidden">
                            <!-- Custom Semi-Circle -->
                            <div class="custom-semi-circle">
                                <span class="ml-7 text-4xl font-bold">06</span>
                            </div>

                            <div class="feature-card-inner">
                                <div class="feature-card-content">
                                    <div class="feature-icon-container">
                                        <i class="fa-solid fa-check-double ml-4 text-9xl text-[#1f3623]"></i>
                                    </div>
                                    <div class="feature-card-title font-poppins">Feature Matching</div>
                                    <span class="feature-card-description">Smart matching to identify registered pets
                                        swiftly.</span>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>
            </div>
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
                        <span class="text-medium">Works seamlessly on both web and mobile platforms for maximum
                            reach.</span>
                    </div>
                </div>

                <!-- New Section with Yellow Box (Fixed and Aligned Text) -->
                <div class="grid-container">
                    <div class="grid-item">
                        <img src="/storage/images/userfriendly.png" class="w-11/12"
                            alt="Pet and User Friendly Mockup" />
                    </div>
                    <div class="grid-item-content">
                        <div class="icon-container">
                            <i class="fa-solid fa-heart text-2xl text-red-600"></i>
                        </div>
                        <div class="text-large">Pet and User Friendly</div>
                        <span class="text-medium">Designed for ease of use, making it simple for owners and effective
                            for identifying lost pets.</span>
                    </div>

                </div>
            </div>

            <div id="demo">
                <div class="demo-section">
                    <div class="section-heading">
                        <div class="section-title font-poppins">See StraySafe in Action</div>
                        <span class="section-subtitle font-poppins">Watch how our technology helps stray animals and
                            communities</span>
                    </div>

                    <div class="video-grid">
                        <div class="video-card">
                            <div class="video-container">
                                <!-- Replace with your actual video embed code -->
                                <div class="video-placeholder">
                                    <div class="play-button">
                                        <i class="fa-solid fa-play"></i>
                                    </div>
                                    <span>Detection Demo</span>
                                </div>
                            </div>
                            <div class="video-description">
                                <h3 class="video-title font-poppins">Real-time Stray Detection</h3>
                                <p class="video-text">See how our AI identifies stray animals in real-time through CCTV
                                    cameras.</p>
                            </div>
                        </div>

                        <div class="video-card">
                            <div class="video-container">
                                <!-- Replace with your actual video embed code -->
                                <div class="video-placeholder">
                                    <div class="play-button">
                                        <i class="fa-solid fa-play"></i>
                                    </div>
                                    <span>Mobile App Demo</span>
                                </div>
                            </div>
                            <div class="video-description">
                                <h3 class="video-title font-poppins">Mobile App Features</h3>
                                <p class="video-text">Tour of our mobile application for pet registration and stray
                                    reporting.</p>
                            </div>
                        </div>

                        <div class="video-card">
                            <div class="video-container">
                                <!-- Replace with your actual video embed code -->
                                <div class="video-placeholder">
                                    <div class="play-button">
                                        <i class="fa-solid fa-play"></i>
                                    </div>
                                    <span>Feature Matching Demo</span>
                                </div>
                            </div>
                            <div class="video-description">
                                <h3 class="video-title font-poppins">Pet Identification System</h3>
                                <p class="video-text">Demonstration of how our feature matching reunites lost pets with
                                    owners.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- About Us Section -->
            <div id="about">
    <div class="about-section">
        <div class="section-heading">
            <div class="section-title font-poppins">Meet Our Team</div>
            <span class="section-subtitle font-poppins">The minds behind StraySafe</span>
        </div>

        <div class="team-carousel-container">
            <button class="carousel-control prev-btn" @click="prevTeamMember">
                <i class="fa-solid fa-chevron-left"></i>
            </button>

            <div class="team-carousel" ref="teamCarousel">
                <div 
                    v-for="(member, index) in teamMembers" 
                    :key="index"
                    :class="['team-card', { active: currentTeamIndex === index }]"
                >
                    <div class="member-image">
                        <img :src="member.image" :alt="member.name" />
                    </div>
                    <div class="member-info">
                        <h3 class="member-name font-poppins">{{ member.name }}</h3>
                        <p class="member-title">{{ member.title }}</p>
                        <p class="member-bio">{{ member.bio }}</p>
                        <div class="member-social">
                            <a :href="member.linkedin" target="_blank" class="social-link">
                                <i class="fa-brands fa-linkedin"></i>
                            </a>
                            <a 
                                v-if="member.github" 
                                :href="member.github" 
                                target="_blank" 
                                class="social-link"
                            >
                                <i class="fa-brands fa-github"></i>
                            </a>
                        </div>
                    </div>
                </div>
                <!-- Duplicate the first card -->
                <div class="team-card" v-if="teamMembers.length > 0">
                    <div class="member-image">
                        <img :src="teamMembers[0].image" :alt="teamMembers[0].name" />
                    </div>
                    <div class="member-info">
                        <h3 class="member-name font-poppins">{{ teamMembers[0].name }}</h3>
                        <p class="member-title">{{ teamMembers[0].title }}</p>
                        <p class="member-bio">{{ teamMembers[0].bio }}</p>
                        <div class="member-social">
                            <a :href="teamMembers[0].linkedin" target="_blank" class="social-link">
                                <i class="fa-brands fa-linkedin"></i>
                            </a>
                            <a 
                                v-if="teamMembers[0].github" 
                                :href="teamMembers[0].github" 
                                target="_blank" 
                                class="social-link"
                            >
                                <i class="fa-brands fa-github"></i>
                            </a>
                        </div>
                    </div>
                </div>
            </div>

            <button class="carousel-control next-btn" @click="nextTeamMember">
                <i class="fa-solid fa-chevron-right"></i>
            </button>
        </div>

        <div class="carousel-dots">
            <span 
                v-for="(member, index) in teamMembers" 
                :key="index"
                :class="['carousel-dot', { active: currentTeamIndex === index }]"
                @click="goToTeamMember(index)"
            ></span>
        </div>
    </div>
</div>
            <div class="footer-container" style="background-color: rgba(79, 102, 66, 0.1);">
                <div class="footer-content">
                    <div class="footer-section logo-section">
                        <div class="footer-logo">
                            <img src="/storage/images/NEWLOGO.png" alt="StraySafe Logo" class="footer-logo-img" />
                            <span class="footer-logo-text font-poppins">Stray<span
                                    class="custom-color">Safe</span></span>
                        </div>
                        <p class="footer-tagline">Care for Strays, Secure Streets</p>
                        <p class="footer-description">A smart city solution for stray animal management and pet
                            identification</p>
                    </div>

                    <div class="footer-section links-section">
                        <h3 class="footer-heading font-poppins">Quick Links</h3>
                        <ul class="footer-links">
                            <li><a href="#hero">Home</a></li>
                            <li><a href="#features">Features</a></li>
                            <li><a href="#highlights">Demo</a></li>
                            <li><a href="#about">About Us</a></li>
                        </ul>
                    </div>

                    <div class="footer-section contact-section">
                        <h3 class="footer-heading font-poppins">Contact</h3>
                        <ul class="footer-contact-info">
                            <li><i class="fa-solid fa-envelope"></i> straysafeteam3@gmail.com</li>
                            <li><i class="fa-solid fa-location-dot"></i> College of Computer Engineering</li>
                            <li>Technological Institute of the Philippines, Quezon City</li>
                        </ul>
                    </div>

                    <div class="footer-section thesis-section">
                        <h3 class="footer-heading font-poppins">Thesis Project</h3>
                        <p>This application was developed as a requirement for the degree of:</p>
                        <p class="thesis-degree">Bachelor of Science in Computer Engineering</p>
                        <p class="thesis-term">Academic Year 2024-2025</p>
                        <div class="thesis-advisors">
                            <p><strong>PD Adviser:</strong> Engr. Roman Richard </p>
                        </div>
                    </div>
                </div>

                <div class="footer-bottom">
                    <div class="social-links">
                        <a href="#" class="social-icon"><i class="fa-brands fa-github"></i></a>
                        <a href="#" class="social-icon"><i class="fa-brands fa-linkedin"></i></a>
                        <a href="#" class="social-icon"><i class="fa-solid fa-envelope"></i></a>
                    </div>
                    <div class="copyright">
                        <p>&copy; 2025 StraySafe | All Rights Reserved</p>
                        <p class="thesis-disclaimer">This project is for academic purposes only</p>
                    </div>
                </div>
            </div>

        </div>
    </div>
</template>
<style src="../../css/welcome2.css"></style>