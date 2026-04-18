// For future interactivity, smooth scroll (optional)
document.addEventListener("DOMContentLoaded", () => {
    const links = document.querySelectorAll(".sidebar a");
    const sidebar = document.querySelector(".sidebar");
    const sections = document.querySelectorAll(".page");

    // Active menu highlight on click & close sidebar
    links.forEach(link => {
        link.addEventListener("click", function () {
            links.forEach(l => l.classList.remove("active"));
            this.classList.add("active");

            // Close menu after click
            sidebar.classList.remove("active");
        });
    });

    // Highlight active link while scrolling
    const observer = new IntersectionObserver(
        entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const id = entry.target.id;
                    links.forEach(l => l.classList.remove("active"));
                    const activeLink = document.querySelector(`.sidebar a[href="#${id}"]`);
                    if(activeLink) activeLink.classList.add("active");
                }
            });
        },
        { threshold: 0.6 } // section 60% visible triggers active
    );

    sections.forEach(section => observer.observe(section));
});

// Toggle sidebar menu
function toggleMenu() {
    document.querySelector(".sidebar").classList.toggle("active");
}
