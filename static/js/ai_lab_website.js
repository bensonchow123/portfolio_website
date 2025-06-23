tailwind.config = {
    theme: {
        extend: {
            colors: {
                primary: {
                    light: '#7C3AED',
                    DEFAULT: '#5D5CDE',
                    dark: '#4338CA'
                },
                secondary: {
                    light: '#06B6D4',
                    DEFAULT: '#0EA5E9',
                    dark: '#0369A1'
                },
                accent: {
                    light: '#F59E0B',
                    DEFAULT: '#F97316',
                    dark: '#EA580C'
                }
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif']
            }
        }
    }
};

// Dark mode detection
if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.classList.add('dark');
}
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
    if (event.matches) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
});

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    const closeMenu = document.getElementById('close-menu');
    
    menuToggle.addEventListener('click', function() {
        mobileMenu.classList.remove('hidden');
        mobileMenu.classList.add('flex');
    });
    
    closeMenu.addEventListener('click', function() {
        mobileMenu.classList.add('hidden');
        mobileMenu.classList.remove('flex');
    });
});

// Form submission handlers
document.addEventListener('DOMContentLoaded', function() {
    // Contact form
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // Add animation to button to show processing
            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Sending...';
            submitBtn.disabled = true;
            
            // Simulate form submission
            setTimeout(function() {
                // Reset form
                contactForm.reset();
                
                // Show success message
                submitBtn.innerHTML = '<i class="fas fa-check mr-2"></i> Message Sent!';
                submitBtn.classList.add('bg-green-500');
                submitBtn.classList.remove('bg-primary', 'hover:bg-primary-dark');
                
                // Reset button after delay
                setTimeout(function() {
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('bg-green-500');
                    submitBtn.classList.add('bg-primary', 'hover:bg-primary-dark');
                }, 3000);
            }, 1500);
        });
    }
    
    // Newsletter form
    const newsletterForm = document.getElementById('newsletterForm');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // Add animation to button to show processing
            const submitBtn = newsletterForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Subscribing...';
            submitBtn.disabled = true;
            
            // Simulate form submission
            setTimeout(function() {
                // Reset form
                newsletterForm.reset();
                
                // Show success message
                submitBtn.innerHTML = '<i class="fas fa-check mr-2"></i> Subscribed!';
                submitBtn.classList.add('bg-green-500');
                submitBtn.classList.remove('bg-primary', 'hover:bg-primary-dark');
                
                // Reset button after delay
                setTimeout(function() {
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('bg-green-500');
                    submitBtn.classList.add('bg-primary', 'hover:bg-primary-dark');
                }, 3000);
            }, 1500);
        });
    }
    
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            // Close mobile menu if open
            const mobileMenu = document.getElementById('mobile-menu');
            if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                mobileMenu.classList.add('hidden');
                mobileMenu.classList.remove('flex');
            }
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80, // Adjust for header height
                    behavior: 'smooth'
                });
            }
        });
    });
});
