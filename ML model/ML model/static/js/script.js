// =====================
// PIE CHART
// =====================

const pieCanvas = document.getElementById("pieChart");

if (pieCanvas) {

    new Chart(pieCanvas, {

        type: "pie",

        data: {

            labels: [
                "Placed",
                "Not Placed"
            ],

            datasets: [{

                data: [28732, 21268],

                backgroundColor: [
                    "#10b981",
                    "#ef4444"
                ],

                borderWidth: 1

            }]

        },

        options: {

            responsive: true,

            plugins: {

                legend: {
                    position: "bottom"
                }

            }

        }

    });

}


// =====================
// BAR CHART
// =====================

const barCanvas = document.getElementById("barChart");

if (barCanvas) {

    new Chart(barCanvas, {

        type: "bar",

        data: {

            labels: [
                "3 LPA",
                "5 LPA",
                "7 LPA",
                "10 LPA",
                "15 LPA"
            ],

            datasets: [{

                label: "Students",

                data: [
                    5000,
                    12000,
                    18000,
                    9000,
                    6000
                ],

                backgroundColor: [
                    "#2563eb",
                    "#10b981",
                    "#8b5cf6",
                    "#f59e0b",
                    "#ef4444"
                ]

            }]

        },

        options: {

            responsive: true,

            scales: {

                y: {

                    beginAtZero: true

                }

            }

        }

    });

}