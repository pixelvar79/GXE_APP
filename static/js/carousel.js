// let scrollInterval;

// function startScroll(direction) {
//     const carousel = document.querySelector('.tabs');
//     const scrollAmount = 320; // Adjust the scroll speed as needed
//     scrollInterval = setInterval(() => {
//         carousel.scrollBy({
//             top: direction * scrollAmount,
//             behavior: 'smooth'
//         });
//     }, 120); // Adjust the interval as needed
// }

// function stopScroll() {
//     clearInterval(scrollInterval);
// }

let scrollInterval;

function startScroll(direction) {
    const carousel = document.querySelector('.tabs');
    const scrollAmount = 10; // Adjust the scroll speed as needed
    scrollInterval = setInterval(() => {
        carousel.scrollBy({
            top: direction * scrollAmount,
            behavior: 'smooth'
        });
    }, 50); // Adjust the interval as needed
}

function stopScroll() {
    clearInterval(scrollInterval);
}

document.querySelector('.top-scroll-area').addEventListener('mouseover', () => startScroll(-1));
document.querySelector('.top-scroll-area').addEventListener('mouseout', stopScroll);
document.querySelector('.bottom-scroll-area').addEventListener('mouseover', () => startScroll(1));
document.querySelector('.bottom-scroll-area').addEventListener('mouseout', stopScroll);