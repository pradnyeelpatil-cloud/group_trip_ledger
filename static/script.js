/* ============================================================
   GROUPTRIP LEDGER
   HOME PAGE JAVASCRIPT
   ============================================================ */


/* ============================================================
   DOM ELEMENTS
   ============================================================ */

const openCreateTripButton =
    document.getElementById("openCreateTrip");

const heroCreateTripButton =
    document.getElementById("heroCreateTrip");

const emptyCreateTripButton =
    document.getElementById("emptyCreateTrip");

const createTripModal =
    document.getElementById("createTripModal");

const closeModalButton =
    document.getElementById("closeModal");

const tripForm =
    document.getElementById("tripForm");

const tripNameInput =
    document.getElementById("tripName");

const startDateInput =
    document.getElementById("startDate");

const endDateInput =
    document.getElementById("endDate");

const membersContainer =
    document.getElementById("membersContainer");

const addMemberButton =
    document.getElementById("addMember");

const memberCounter =
    document.getElementById("memberCounter");

const tripsContainer =
    document.getElementById("tripsContainer");

const tripCount =
    document.getElementById("tripCount");

const createTripButton =
    document.getElementById("createTripButton");

const createTripButtonText =
    document.getElementById("createTripButtonText");


/* ============================================================
   APPLICATION STATE
   ============================================================ */

let isCreatingTrip = false;


/* ============================================================
   OPEN MODAL
   ============================================================ */

function openModal() {

    if (!createTripModal) {
        return;
    }

    createTripModal.classList.remove("hidden");

    document.body.style.overflow = "hidden";

    setTimeout(function () {

        if (tripNameInput) {
            tripNameInput.focus();
        }

    }, 150);
}


/* ============================================================
   CLOSE MODAL
   ============================================================ */

function closeModal() {

    if (!createTripModal) {
        return;
    }

    createTripModal.classList.add("hidden");

    document.body.style.overflow = "";

}


/* ============================================================
   MODAL BUTTONS
   ============================================================ */

if (openCreateTripButton) {

    openCreateTripButton.addEventListener(
        "click",
        openModal
    );

}


if (heroCreateTripButton) {

    heroCreateTripButton.addEventListener(
        "click",
        openModal
    );

}


if (emptyCreateTripButton) {

    emptyCreateTripButton.addEventListener(
        "click",
        openModal
    );

}


if (closeModalButton) {

    closeModalButton.addEventListener(
        "click",
        closeModal
    );

}


/* ============================================================
   CLICK OUTSIDE MODAL
   ============================================================ */

if (createTripModal) {

    createTripModal.addEventListener(
        "click",
        function (event) {

            if (
                event.target === createTripModal
            ) {

                closeModal();

            }

        }
    );

}


/* ============================================================
   ESC KEY
   ============================================================ */

document.addEventListener(
    "keydown",
    function (event) {

        if (
            event.key === "Escape" &&
            createTripModal &&
            !createTripModal.classList.contains("hidden")
        ) {

            closeModal();

        }

    }
);


/* ============================================================
   MEMBER COUNTER
   ============================================================ */

function updateMemberCounter() {

    if (
        !membersContainer ||
        !memberCounter
    ) {

        return;

    }


    const inputs =
        membersContainer.querySelectorAll(
            ".member-input"
        );


    let count = 0;


    inputs.forEach(function (input) {

        /*
         * Count member fields, not only
         * fields containing text.
         *
         * This matches the UI.
         */

        if (input) {

            count++;

        }

    });


    memberCounter.textContent =
        count === 1
            ? "1 member"
            : `${count} members`;

}


/* ============================================================
   RENUMBER MEMBERS
   ============================================================ */

function renumberMembers() {

    if (!membersContainer) {
        return;
    }


    const rows =
        membersContainer.querySelectorAll(
            ".member-input-row"
        );


    rows.forEach(
        function (row, index) {

            const number =
                row.querySelector(
                    ".input-number"
                );


            if (number) {

                number.textContent =
                    String(index + 1)
                        .padStart(2, "0");

            }

        }
    );

}


/* ============================================================
   ADD MEMBER
   ============================================================ */

if (addMemberButton) {

    addMemberButton.addEventListener(
        "click",
        function () {

            if (!membersContainer) {
                return;
            }


            const rows =
                membersContainer.querySelectorAll(
                    ".member-input-row"
                );


            const newIndex =
                rows.length + 1;


            const row =
                document.createElement("div");


            row.className =
                "member-input-row";


            row.innerHTML = `

                <div class="input-number">
                    ${String(newIndex).padStart(2, "0")}
                </div>

                <input
                    type="text"
                    class="member-input"
                    placeholder="Member name"
                    maxlength="60"
                >

            `;


            membersContainer.appendChild(row);


            updateMemberCounter();


            const newInput =
                row.querySelector(
                    ".member-input"
                );


            if (newInput) {

                newInput.focus();

            }

        }
    );

}


/* ============================================================
   REMOVE / LIMIT EMPTY DUPLICATES
   ============================================================ */

function getMemberNames() {

    if (!membersContainer) {

        return [];

    }


    const inputs =
        membersContainer.querySelectorAll(
            ".member-input"
        );


    const names = [];


    inputs.forEach(function (input) {

        const name =
            input.value.trim();


        if (name) {

            names.push(name);

        }

    });


    return names;

}


/* ============================================================
   ESCAPE HTML
   ============================================================ */

function escapeHtml(value) {

    const div =
        document.createElement("div");


    div.textContent =
        value == null
            ? ""
            : String(value);


    return div.innerHTML;

}


/* ============================================================
   FORMAT DATE
   ============================================================ */

function formatDate(dateString) {

    if (!dateString) {

        return "Date not set";

    }


    const date =
        new Date(
            dateString + "T00:00:00"
        );


    if (Number.isNaN(date.getTime())) {

        return dateString;

    }


    return date.toLocaleDateString(
        "en-IN",
        {
            day: "2-digit",
            month: "short",
            year: "numeric"
        }
    );

}


/* ============================================================
   UPDATE TRIP COUNT
   ============================================================ */

function updateTripCount(count) {

    if (!tripCount) {
        return;
    }


    tripCount.textContent =
        count === 1
            ? "1 trip"
            : `${count} trips`;

}


/* ============================================================
   SHOW LOADING
   ============================================================ */

function showLoading() {

    if (!tripsContainer) {
        return;
    }


    tripsContainer.innerHTML = `

        <div class="loading-state">

            <div>

                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>

            </div>

            <p>
                Loading your journeys...
            </p>

        </div>

    `;

}


/* ============================================================
   SHOW EMPTY STATE
   ============================================================ */

function showEmptyState() {

    if (!tripsContainer) {
        return;
    }


    tripsContainer.innerHTML = `

        <div class="empty-state">

            <div class="empty-illustration">

                <div class="empty-ring"></div>

                <div class="empty-plane">
                    ✈
                </div>

            </div>


            <div class="empty-content">

                <div class="empty-label">
                    READY FOR TAKEOFF?
                </div>


                <h3>
                    Your journey starts here
                </h3>


                <p>
                    Create your first trip,
                    invite your crew and let
                    GroupTrip Ledger handle
                    the expenses.
                </p>


                <button
                    id="dynamicEmptyCreateTrip"
                    class="primary-button"
                    type="button"
                >

                    <span>
                        +
                    </span>

                    Create Your First Trip

                </button>

            </div>

        </div>

    `;


    const button =
        document.getElementById(
            "dynamicEmptyCreateTrip"
        );


    if (button) {

        button.addEventListener(
            "click",
            openModal
        );

    }

}


/* ============================================================
   CREATE REAL TRIP CARD
   ============================================================ */

function createTripCard(trip) {

    const card =
        document.createElement("div");


    card.className =
        "trip-card";


    card.setAttribute(
        "data-trip-id",
        trip.id
    );


    const name =
        escapeHtml(
            trip.name || "Unnamed Trip"
        );


    const start =
        formatDate(
            trip.start_date
        );


    const end =
        formatDate(
            trip.end_date
        );


    const members =
        Number(
            trip.member_count || 0
        );


    card.innerHTML = `

        <div class="trip-card-left">

            <div class="trip-icon">
                ✈
            </div>


            <div class="trip-info">

                <h3>
                    ${name}
                </h3>


                <p>
                    ${start} → ${end}
                </p>

            </div>

        </div>


        <div class="trip-card-right">

            <span class="trip-members">

                👥 ${members}
                ${members === 1 ? "member" : "members"}

            </span>


            <span class="trip-status">
                Active
            </span>


            <span class="trip-arrow">
                →
            </span>

        </div>

    `;


    card.addEventListener(
        "click",
        function () {

            window.location.href =
                `/trip/${trip.id}`;

        }
    );


    return card;

}


/* ============================================================
   RENDER TRIPS
   ============================================================ */

function renderTrips(trips) {

    if (!tripsContainer) {
        return;
    }


    if (
        !Array.isArray(trips) ||
        trips.length === 0
    ) {

        updateTripCount(0);

        showEmptyState();

        return;

    }


    tripsContainer.innerHTML = "";


    trips.forEach(
        function (trip) {

            const card =
                createTripCard(trip);


            tripsContainer.appendChild(card);

        }
    );


    updateTripCount(
        trips.length
    );

}


/* ============================================================
   LOAD TRIPS FROM SQLITE
   ============================================================ */

async function loadTrips() {

    showLoading();


    try {

        const response =
            await fetch(
                "/api/trips",
                {
                    method: "GET",
                    headers: {
                        "Accept": "application/json"
                    },
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );

        }


        const trips =
            await response.json();


        renderTrips(trips);


    }
    catch (error) {

        console.error(
            "Unable to load trips:",
            error
        );


        if (tripsContainer) {

            tripsContainer.innerHTML = `

                <div class="empty-state">

                    <div class="empty-illustration">

                        <div class="empty-ring"></div>

                        <div class="empty-plane">
                            ⚠
                        </div>

                    </div>


                    <div class="empty-content">

                        <div class="empty-label">
                            CONNECTION ERROR
                        </div>


                        <h3>
                            Unable to load trips
                        </h3>


                        <p>
                            Make sure the Flask server
                            is running and try again.
                        </p>


                        <button
                            id="retryTrips"
                            class="primary-button"
                            type="button"
                        >
                            Try Again
                        </button>

                    </div>

                </div>

            `;


            const retryButton =
                document.getElementById(
                    "retryTrips"
                );


            if (retryButton) {

                retryButton.addEventListener(
                    "click",
                    loadTrips
                );

            }

        }

    }

}


/* ============================================================
   DATE VALIDATION
   ============================================================ */

function validateDates() {

    const start =
        startDateInput
            ? startDateInput.value
            : "";


    const end =
        endDateInput
            ? endDateInput.value
            : "";


    if (
        start &&
        end &&
        end < start
    ) {

        alert(
            "End date cannot be before start date."
        );


        return false;

    }


    return true;

}


/* ============================================================
   RESET FORM
   ============================================================ */

function resetTripForm() {

    if (tripForm) {

        tripForm.reset();

    }


    if (!membersContainer) {

        return;

    }


    /*
     * Always return to exactly two fields.
     */

    membersContainer.innerHTML = `

        <div class="member-input-row">

            <div class="input-number">
                01
            </div>

            <input
                type="text"
                class="member-input"
                placeholder="Member name"
                maxlength="60"
                required
            >

        </div>


        <div class="member-input-row">

            <div class="input-number">
                02
            </div>

            <input
                type="text"
                class="member-input"
                placeholder="Member name"
                maxlength="60"
            >

        </div>

    `;


    updateMemberCounter();

}


/* ============================================================
   SET CREATE BUTTON LOADING
   ============================================================ */

function setCreateButtonLoading(loading) {

    if (
        !createTripButton ||
        !createTripButtonText
    ) {

        return;

    }


    if (loading) {

        createTripButton.disabled = true;

        createTripButtonText.textContent =
            "Creating...";

        isCreatingTrip = true;

    }
    else {

        createTripButton.disabled = false;

        createTripButtonText.textContent =
            "Create Trip";

        isCreatingTrip = false;

    }

}


/* ============================================================
   CREATE REAL TRIP
   ============================================================ */

if (tripForm) {

    tripForm.addEventListener(
        "submit",
        async function (event) {

            /*
             * VERY IMPORTANT:
             *
             * This prevents the browser from
             * submitting twice or reloading.
             */

            event.preventDefault();


            /*
             * Prevent double-click /
             * double submission.
             */

            if (isCreatingTrip) {

                return;

            }


            const name =
                tripNameInput
                    ? tripNameInput.value.trim()
                    : "";


            if (!name) {

                alert(
                    "Please enter a trip name."
                );

                return;

            }


            if (!validateDates()) {

                return;

            }


            const members =
                getMemberNames();


            if (members.length === 0) {

                alert(
                    "Please add at least one member."
                );

                return;

            }


            /*
             * Prevent duplicate member names
             * inside the same trip.
             */

            const normalized =
                members.map(
                    function (member) {

                        return member
                            .toLowerCase();

                    }
                );


            const hasDuplicate =
                new Set(normalized).size
                !== normalized.length;


            if (hasDuplicate) {

                alert(
                    "Please use different names for each member."
                );

                return;

            }


            /*
             * Prepare REAL API data.
             */

            const payload = {

                name: name,

                start_date:
                    startDateInput
                        ? startDateInput.value || null
                        : null,

                end_date:
                    endDateInput
                        ? endDateInput.value || null
                        : null,

                members: members

            };


            setCreateButtonLoading(true);


            try {

                /*
                 * REAL Flask request.
                 *
                 * This goes to:
                 *
                 * POST /api/trips
                 */

                const response =
                    await fetch(
                        "/api/trips",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json",

                                "Accept":
                                    "application/json"
                            },

                            body:
                                JSON.stringify(
                                    payload
                                )
                        }
                    );


                /*
                 * Safely read JSON.
                 */

                let result = null;


                try {

                    result =
                        await response.json();

                }
                catch (jsonError) {

                    result = null;

                }


                if (!response.ok) {

                    throw new Error(
                        result &&
                        result.error
                            ? result.error
                            : "Unable to create trip."
                    );

                }


                /*
                 * Flask should return:
                 *
                 * {
                 *   message: "...",
                 *   trip_id: 1
                 * }
                 */

                if (
                    !result ||
                    !result.trip_id
                ) {

                    throw new Error(
                        "Trip was not created correctly."
                    );

                }


                /*
                 * Close modal.
                 */

                closeModal();


                /*
                 * Reset form.
                 */

                resetTripForm();


                /*
                 * Reload directly from SQLite.
                 *
                 * This is important:
                 *
                 * We DO NOT create a fake card.
                 */

                await loadTrips();


                /*
                 * Small confirmation.
                 */

                console.log(
                    "Trip created successfully:",
                    result.trip_id
                );


            }
            catch (error) {

                console.error(
                    "Create trip error:",
                    error
                );


                alert(
                    error.message ||
                    "Something went wrong while creating the trip."
                );

            }
            finally {

                setCreateButtonLoading(false);

            }

        }
    );

}


/* ============================================================
   INITIALIZE MEMBER COUNTER
   ============================================================ */

updateMemberCounter();


/* ============================================================
   LOAD REAL TRIPS WHEN PAGE OPENS
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        loadTrips();

    }
);