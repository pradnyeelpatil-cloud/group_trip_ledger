import os
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, request, render_template, send_file
from dotenv import load_dotenv

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.units import mm


# ==========================================================
# 1. LOAD ENVIRONMENT
# ==========================================================

load_dotenv()


# ==========================================================
# 2. CREATE FLASK APPLICATION
# ==========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "development-secret-key"
)


# ==========================================================
# 3. DATABASE PATH
# ==========================================================

DATABASE = os.path.join(
    os.path.dirname(__file__),
    "database",
    "database.db"
)


# ==========================================================
# 4. DATABASE CONNECTION
# ==========================================================

def get_db():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ==========================================================
# 5. DATABASE INITIALIZATION
# ==========================================================

def init_database():

    # Make sure database directory exists
    database_directory = os.path.dirname(DATABASE)

    os.makedirs(
        database_directory,
        exist_ok=True
    )

    connection = get_db()

    connection.executescript("""

        CREATE TABLE IF NOT EXISTS trips (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            start_date TEXT,

            end_date TEXT,

            status TEXT DEFAULT 'active',

            ended_at TIMESTAMP,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        );


        CREATE TABLE IF NOT EXISTS members (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            trip_id INTEGER NOT NULL,

            name TEXT NOT NULL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (trip_id)
                REFERENCES trips(id)
                ON DELETE CASCADE
        );


        CREATE TABLE IF NOT EXISTS expenses (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            trip_id INTEGER NOT NULL,

            description TEXT NOT NULL,

            amount REAL NOT NULL,

            paid_by INTEGER NOT NULL,

            category TEXT DEFAULT 'Other',

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (trip_id)
                REFERENCES trips(id)
                ON DELETE CASCADE,

            FOREIGN KEY (paid_by)
                REFERENCES members(id)
        );


        CREATE TABLE IF NOT EXISTS expense_participants (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            expense_id INTEGER NOT NULL,

            member_id INTEGER NOT NULL,

            share_amount REAL NOT NULL,

            FOREIGN KEY (expense_id)
                REFERENCES expenses(id)
                ON DELETE CASCADE,

            FOREIGN KEY (member_id)
                REFERENCES members(id)
                ON DELETE CASCADE
        );

    """)

    # ------------------------------------------------------
    # DATABASE MIGRATION
    # ------------------------------------------------------

    columns = connection.execute(
        "PRAGMA table_info(trips)"
    ).fetchall()

    column_names = {
        column["name"]
        for column in columns
    }

    if "status" not in column_names:

        connection.execute("""
            ALTER TABLE trips
            ADD COLUMN status TEXT DEFAULT 'active'
        """)

    if "ended_at" not in column_names:

        connection.execute("""
            ALTER TABLE trips
            ADD COLUMN ended_at TIMESTAMP
        """)

    # Existing trips are active unless explicitly ended

    connection.execute("""
        UPDATE trips
        SET status = 'active'
        WHERE status IS NULL
    """)

    connection.commit()

    connection.close()


# ==========================================================
# 6. MONEY FORMATTER
# ==========================================================

def format_paise(paise):

    rupees = paise / 100

    return f"{rupees:,.2f}"


# ==========================================================
# 7. HOME PAGE
# ==========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ==========================================================
# 8. TRIP PAGE
# ==========================================================

@app.route("/trip/<int:trip_id>")
def trip_page(trip_id):

    return render_template(
        "trip.html",
        trip_id=trip_id
    )


# ==========================================================
# 9. HEALTH CHECK
# ==========================================================

@app.route("/api/health")
def health():

    return jsonify({

        "status": "success",

        "message":
            "GroupTrip Ledger backend is running"

    })


# ==========================================================
# 10. GET ALL TRIPS
# ==========================================================

@app.route(
    "/api/trips",
    methods=["GET"]
)
def get_trips():

    connection = get_db()

    try:

        trips = connection.execute("""
            SELECT *
            FROM trips
            ORDER BY created_at DESC
        """).fetchall()

        result = []

        for trip in trips:

            member_count = connection.execute("""
                SELECT COUNT(*) AS count
                FROM members
                WHERE trip_id = ?
            """, (
                trip["id"],
            )).fetchone()["count"]

            expense_count = connection.execute("""
                SELECT COUNT(*) AS count
                FROM expenses
                WHERE trip_id = ?
            """, (
                trip["id"],
            )).fetchone()["count"]

            result.append({

                "id":
                    trip["id"],

                "name":
                    trip["name"],

                "start_date":
                    trip["start_date"],

                "end_date":
                    trip["end_date"],

                "status":
                    trip["status"] or "active",

                "ended_at":
                    trip["ended_at"],

                "member_count":
                    member_count,

                "expense_count":
                    expense_count,

                "created_at":
                    trip["created_at"]

            })

        return jsonify(result)

    finally:

        connection.close()


# ==========================================================
# 11. CREATE TRIP
# ==========================================================

@app.route(
    "/api/trips",
    methods=["POST"]
)
def create_trip():

    data = request.get_json()

    if not data:

        return jsonify({
            "error":
                "No data received"
        }), 400

    name = str(
        data.get("name", "")
    ).strip()

    start_date = data.get(
        "start_date"
    )

    end_date = data.get(
        "end_date"
    )

    members = data.get(
        "members",
        []
    )

    if not name:

        return jsonify({
            "error":
                "Trip name is required"
        }), 400

    if not isinstance(members, list):

        return jsonify({
            "error":
                "Members must be a list"
        }), 400

    cleaned_members = []

    for member in members:

        member_name = str(
            member
        ).strip()

        if member_name:

            cleaned_members.append(
                member_name
            )

    if not cleaned_members:

        return jsonify({
            "error":
                "At least one member is required"
        }), 400

    connection = get_db()

    try:

        cursor = connection.execute("""
            INSERT INTO trips
            (
                name,
                start_date,
                end_date,
                status
            )
            VALUES (?, ?, ?, 'active')
        """, (
            name,
            start_date,
            end_date
        ))

        trip_id = cursor.lastrowid

        for member_name in cleaned_members:

            connection.execute("""
                INSERT INTO members
                (
                    trip_id,
                    name
                )
                VALUES (?, ?)
            """, (
                trip_id,
                member_name
            ))

        connection.commit()

        return jsonify({

            "message":
                "Trip created successfully",

            "trip_id":
                trip_id

        }), 201

    except Exception as error:

        connection.rollback()

        return jsonify({
            "error":
                str(error)
        }), 500

    finally:

        connection.close()


# ==========================================================
# 12. GET ONE TRIP
# ==========================================================

@app.route(
    "/api/trips/<int:trip_id>",
    methods=["GET"]
)
def get_trip(trip_id):

    connection = get_db()

    try:

        trip = connection.execute("""
            SELECT *
            FROM trips
            WHERE id = ?
        """, (
            trip_id,
        )).fetchone()

        if trip is None:

            return jsonify({
                "error":
                    "Trip not found"
            }), 404

        members = connection.execute("""
            SELECT *
            FROM members
            WHERE trip_id = ?
            ORDER BY id
        """, (
            trip_id,
        )).fetchall()

        return jsonify({

            "id":
                trip["id"],

            "name":
                trip["name"],

            "start_date":
                trip["start_date"],

            "end_date":
                trip["end_date"],

            "status":
                trip["status"] or "active",

            "ended_at":
                trip["ended_at"],

            "members": [

                {
                    "id":
                        member["id"],

                    "name":
                        member["name"]

                }

                for member in members

            ]

        })

    finally:

        connection.close()


# ==========================================================
# 13. GET EXPENSES
# ==========================================================

@app.route(
    "/api/trips/<int:trip_id>/expenses",
    methods=["GET"]
)
def get_expenses(trip_id):

    connection = get_db()

    try:

        expenses = connection.execute("""
            SELECT
                expenses.id,
                expenses.description,
                expenses.amount,
                expenses.category,
                expenses.created_at,
                members.name AS paid_by_name
            FROM expenses
            JOIN members
                ON expenses.paid_by = members.id
            WHERE expenses.trip_id = ?
            ORDER BY expenses.created_at DESC
        """, (
            trip_id,
        )).fetchall()

        result = []

        for expense in expenses:

            participants = connection.execute("""
                SELECT
                    expense_participants.member_id,
                    expense_participants.share_amount,
                    members.name
                FROM expense_participants
                JOIN members
                    ON expense_participants.member_id = members.id
                WHERE expense_participants.expense_id = ?
                ORDER BY expense_participants.id
            """, (
                expense["id"],
            )).fetchall()

            result.append({

                "id":
                    expense["id"],

                "description":
                    expense["description"],

                "amount":
                    expense["amount"],

                "category":
                    expense["category"],

                "paid_by":
                    expense["paid_by_name"],

                "created_at":
                    expense["created_at"],

                "participants": [

                    {
                        "id":
                            participant["member_id"],

                        "name":
                            participant["name"],

                        "share":
                            participant["share_amount"]

                    }

                    for participant in participants

                ]

            })

        return jsonify(result)

    finally:

        connection.close()


# ==========================================================
# 14. CREATE EXPENSE
# ==========================================================

@app.route(
    "/api/trips/<int:trip_id>/expenses",
    methods=["POST"]
)
def create_expense(trip_id):

    data = request.get_json()

    if not data:

        return jsonify({
            "error":
                "No data received"
        }), 400

    description = str(
        data.get(
            "description",
            ""
        )
    ).strip()

    category = str(
        data.get(
            "category",
            "Other"
        )
    ).strip()

    try:

        amount = float(
            data.get(
                "amount",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "error":
                "Amount must be a valid number"
        }), 400

    paid_by = data.get(
        "paid_by"
    )

    participants = data.get(
        "participants",
        []
    )

    if not description:

        return jsonify({
            "error":
                "Expense description is required"
        }), 400

    if amount <= 0:

        return jsonify({
            "error":
                "Amount must be greater than zero"
        }), 400

    try:

        paid_by = int(
            paid_by
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "error":
                "Please select who paid"
        }), 400

    if not isinstance(
        participants,
        list
    ):

        return jsonify({
            "error":
                "Invalid participants"
        }), 400

    try:

        participants = [

            int(member_id)

            for member_id
            in participants

        ]

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "error":
                "Invalid participant"
        }), 400

    # Remove duplicate participants

    participants = list(
        dict.fromkeys(
            participants
        )
    )

    if not participants:

        return jsonify({
            "error":
                "Select at least one participant"
        }), 400

    connection = get_db()

    try:

        # --------------------------------------------------
        # CHECK TRIP
        # --------------------------------------------------

        trip = connection.execute("""
            SELECT *
            FROM trips
            WHERE id = ?
        """, (
            trip_id,
        )).fetchone()

        if trip is None:

            return jsonify({
                "error":
                    "Trip not found"
            }), 404

        # --------------------------------------------------
        # DO NOT ALLOW EXPENSE AFTER TRIP ENDED
        # --------------------------------------------------

        if (
            trip["status"] or "active"
        ) == "ended":

            return jsonify({
                "error":
                    "This trip has already ended. New expenses cannot be added."
            }), 400

        # --------------------------------------------------
        # CHECK PAYER
        # --------------------------------------------------

        payer = connection.execute("""
            SELECT id
            FROM members
            WHERE id = ?
            AND trip_id = ?
        """, (
            paid_by,
            trip_id
        )).fetchone()

        if payer is None:

            return jsonify({
                "error":
                    "Selected payer is not part of this trip"
            }), 400

        # --------------------------------------------------
        # CHECK PARTICIPANTS
        # --------------------------------------------------

        placeholders = ",".join(
            ["?"] * len(participants)
        )

        valid_members = connection.execute(
            f"""
            SELECT id
            FROM members
            WHERE trip_id = ?
            AND id IN ({placeholders})
            """,
            [trip_id] + participants
        ).fetchall()

        if len(valid_members) != len(
            participants
        ):

            return jsonify({
                "error":
                    "One or more participants are invalid"
            }), 400

        # --------------------------------------------------
        # SAVE EXPENSE
        # --------------------------------------------------

        cursor = connection.execute("""
            INSERT INTO expenses
            (
                trip_id,
                description,
                amount,
                paid_by,
                category
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            trip_id,
            description,
            amount,
            paid_by,
            category
        ))

        expense_id = cursor.lastrowid

        # --------------------------------------------------
        # EXACT CENT SPLIT
        # --------------------------------------------------

        total_paise = int(
            round(
                amount * 100
            )
        )

        member_count = len(
            participants
        )

        base_paise = (
            total_paise //
            member_count
        )

        remainder = (
            total_paise %
            member_count
        )

        for index, member_id in enumerate(
            participants
        ):

            share_paise = base_paise

            if index < remainder:

                share_paise += 1

            share_amount = (
                share_paise / 100
            )

            connection.execute("""
                INSERT INTO expense_participants
                (
                    expense_id,
                    member_id,
                    share_amount
                )
                VALUES (?, ?, ?)
            """, (
                expense_id,
                member_id,
                share_amount
            ))

        connection.commit()

        return jsonify({

            "message":
                "Expense created successfully",

            "expense_id":
                expense_id

        }), 201

    except Exception as error:

        connection.rollback()

        return jsonify({
            "error":
                str(error)
        }), 500

    finally:

        connection.close()


# ==========================================================
# 15. CALCULATE SETTLEMENT
# ==========================================================
#
# IMPORTANT:
# There is ONLY ONE calculate_settlement() in this file.
#
# Positive balance:
#       Person should receive money.
#
# Negative balance:
#       Person needs to pay money.
#
# ==========================================================

def calculate_settlement(trip_id):

    connection = get_db()

    try:

        # --------------------------------------------------
        # GET MEMBERS
        # --------------------------------------------------

        members = connection.execute("""
            SELECT id, name
            FROM members
            WHERE trip_id = ?
            ORDER BY id
        """, (
            trip_id,
        )).fetchall()

        if not members:

            return None

        # --------------------------------------------------
        # CREATE LEDGER
        # --------------------------------------------------

        ledger = {

            member["id"]: {

                "id":
                    member["id"],

                "name":
                    member["name"],

                "paid_paise":
                    0,

                "share_paise":
                    0

            }

            for member in members

        }

        # --------------------------------------------------
        # GET EXPENSES
        # --------------------------------------------------

        expenses = connection.execute("""
            SELECT
                id,
                description,
                amount,
                paid_by,
                category,
                created_at
            FROM expenses
            WHERE trip_id = ?
            ORDER BY id ASC
        """, (
            trip_id,
        )).fetchall()

        expense_details = []

        category_totals = {}

        # --------------------------------------------------
        # PROCESS EXPENSES
        # --------------------------------------------------

        for expense in expenses:

            amount_paise = int(
                round(
                    float(
                        expense["amount"]
                    ) * 100
                )
            )

            payer_id = expense[
                "paid_by"
            ]

            # --------------------------------------------------
            # ADD PAYMENT TO PAYER
            # --------------------------------------------------

            if payer_id in ledger:

                ledger[
                    payer_id
                ]["paid_paise"] += amount_paise

            # --------------------------------------------------
            # GET PARTICIPANTS
            # --------------------------------------------------

            participants = connection.execute("""
                SELECT member_id
                FROM expense_participants
                WHERE expense_id = ?
                ORDER BY id
            """, (
                expense["id"],
            )).fetchall()

            participant_ids = [

                participant["member_id"]

                for participant
                in participants

                if participant["member_id"]
                in ledger

            ]

            # Remove duplicates

            participant_ids = list(
                dict.fromkeys(
                    participant_ids
                )
            )

            if not participant_ids:

                continue

            # --------------------------------------------------
            # EXACT SPLIT
            # --------------------------------------------------

            participant_count = len(
                participant_ids
            )

            base_paise = (
                amount_paise //
                participant_count
            )

            remainder = (
                amount_paise %
                participant_count
            )

            participant_details = []

            for index, member_id in enumerate(
                participant_ids
            ):

                share_paise = base_paise

                if index < remainder:

                    share_paise += 1

                ledger[
                    member_id
                ]["share_paise"] += share_paise

                participant_details.append({

                    "member_id":
                        member_id,

                    "name":
                        ledger[
                            member_id
                        ]["name"],

                    "share_paise":
                        share_paise

                })

            # --------------------------------------------------
            # CATEGORY TOTAL
            # --------------------------------------------------

            category = (
                expense["category"]
                or "Other"
            )

            category_totals[
                category
            ] = (
                category_totals.get(
                    category,
                    0
                )
                + amount_paise
            )

            # --------------------------------------------------
            # EXPENSE DETAILS
            # --------------------------------------------------

            paid_by_name = ledger.get(
                payer_id,
                {
                    "name":
                        "Unknown"
                }
            )["name"]

            expense_details.append({

                "id":
                    expense["id"],

                "description":
                    expense["description"],

                "amount_paise":
                    amount_paise,

                "category":
                    category,

                "paid_by":
                    paid_by_name,

                "participants":
                    participant_details,

                "created_at":
                    expense["created_at"]

            })

        # --------------------------------------------------
        # CALCULATE BALANCES
        # --------------------------------------------------

        balances = []

        for member in members:

            member_data = ledger[
                member["id"]
            ]

            paid = member_data[
                "paid_paise"
            ]

            share = member_data[
                "share_paise"
            ]

            # Positive = should receive
            # Negative = needs to pay

            balance = (
                paid - share
            )

            balances.append({

                "id":
                    member["id"],

                "name":
                    member["name"],

                "paid_paise":
                    paid,

                "share_paise":
                    share,

                "balance_paise":
                    balance

            })

        # --------------------------------------------------
        # CREDITORS
        # --------------------------------------------------

        creditors = [

            {

                "name":
                    member["name"],

                "remaining_paise":
                    member["balance_paise"]

            }

            for member in balances

            if member["balance_paise"] > 0

        ]

        # --------------------------------------------------
        # DEBTORS
        # --------------------------------------------------

        debtors = [

            {

                "name":
                    member["name"],

                "remaining_paise":
                    abs(
                        member["balance_paise"]
                    )

            }

            for member in balances

            if member["balance_paise"] < 0

        ]

        # --------------------------------------------------
        # GENERATE SETTLEMENT TRANSACTIONS
        # --------------------------------------------------

        settlements = []

        creditor_index = 0
        debtor_index = 0

        while (
            creditor_index < len(
                creditors
            )
            and
            debtor_index < len(
                debtors
            )
        ):

            creditor = creditors[
                creditor_index
            ]

            debtor = debtors[
                debtor_index
            ]

            payment = min(

                creditor[
                    "remaining_paise"
                ],

                debtor[
                    "remaining_paise"
                ]

            )

            if payment > 0:

                settlements.append({

                    "from":
                        debtor["name"],

                    "to":
                        creditor["name"],

                    "amount_paise":
                        payment

                })

            creditor[
                "remaining_paise"
            ] -= payment

            debtor[
                "remaining_paise"
            ] -= payment

            if creditor[
                "remaining_paise"
            ] == 0:

                creditor_index += 1

            if debtor[
                "remaining_paise"
            ] == 0:

                debtor_index += 1

        # --------------------------------------------------
        # TOTAL EXPENSE
        # --------------------------------------------------

        total_paise = sum(

            expense["amount_paise"]

            for expense
            in expense_details

        )

        # --------------------------------------------------
        # RETURN COMPLETE SETTLEMENT
        # --------------------------------------------------

        return {

            "trip_id":
                trip_id,

            "total_paise":
                total_paise,

            "total_amount":
                total_paise / 100,

            "expense_count":
                len(expense_details),

            "member_count":
                len(members),

            "members":
                balances,

            "expenses":
                expense_details,

            "category_totals":
                category_totals,

            "settlements":
                settlements

        }

    finally:

        connection.close()


# ==========================================================
# 16. GET CURRENT SETTLEMENT
# ==========================================================
#
# IMPORTANT:
# This route exists ONLY ONCE.
#
# GET:
# /api/trips/<trip_id>/settlement
#
# ==========================================================

@app.route(
    "/api/trips/<int:trip_id>/settlement",
    methods=["GET"]
)
def get_settlement(trip_id):

    connection = get_db()

    try:

        trip = connection.execute("""
            SELECT id, status
            FROM trips
            WHERE id = ?
        """, (
            trip_id,
        )).fetchone()

        if trip is None:

            return jsonify({
                "error":
                    "Trip not found"
            }), 404

    finally:

        connection.close()

    settlement = calculate_settlement(
        trip_id
    )

    return jsonify({

        "status":
            trip["status"] or "active",

        "settlement":
            settlement

    })


# ==========================================================
# 17. END TRIP
# ==========================================================
#
# IMPORTANT:
# This route exists ONLY ONCE.
#
# POST:
# /api/trips/<trip_id>/end
#
# ==========================================================

@app.route(
    "/api/trips/<int:trip_id>/end",
    methods=["POST"]
)
def end_trip(trip_id):

    connection = get_db()

    try:

        # --------------------------------------------------
        # FIND TRIP
        # --------------------------------------------------

        trip = connection.execute("""
            SELECT *
            FROM trips
            WHERE id = ?
        """, (
            trip_id,
        )).fetchone()

        if trip is None:

            return jsonify({
                "error":
                    "Trip not found"
            }), 404

        # --------------------------------------------------
        # ALREADY ENDED
        # --------------------------------------------------

        if (
            trip["status"] or "active"
        ) == "ended":

            settlement = calculate_settlement(
                trip_id
            )

            return jsonify({

                "message":
                    "Trip already ended",

                "status":
                    "ended",

                "ended_at":
                    trip["ended_at"],

                "settlement":
                    settlement

            })

        # --------------------------------------------------
        # CALCULATE SETTLEMENT BEFORE ENDING
        # --------------------------------------------------

        settlement = calculate_settlement(
            trip_id
        )

        # --------------------------------------------------
        # END TRIP
        # --------------------------------------------------

        ended_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        connection.execute("""
            UPDATE trips
            SET
                status = 'ended',
                ended_at = ?
            WHERE id = ?
        """, (
            ended_at,
            trip_id
        ))

        connection.commit()

        return jsonify({

            "message":
                "Trip ended successfully",

            "status":
                "ended",

            "ended_at":
                ended_at,

            "settlement":
                settlement

        })

    except Exception as error:

        connection.rollback()

        return jsonify({
            "error":
                str(error)
        }), 500

    finally:

        connection.close()


# ==========================================================
# 18. PDF REPORT
# ==========================================================

@app.route(
    "/api/trips/<int:trip_id>/report",
    methods=["GET"]
)
def download_report(trip_id):

    connection = get_db()

    try:

        trip = connection.execute("""
            SELECT *
            FROM trips
            WHERE id = ?
        """, (
            trip_id,
        )).fetchone()

    finally:

        connection.close()

    if trip is None:

        return jsonify({
            "error":
                "Trip not found"
        }), 404

    # ------------------------------------------------------
    # CALCULATE SETTLEMENT
    # ------------------------------------------------------

    settlement = calculate_settlement(
        trip_id
    )

    if settlement is None:

        return jsonify({
            "error":
                "Unable to calculate report"
        }), 500

    # ------------------------------------------------------
    # REPORT DIRECTORY
    # ------------------------------------------------------

    report_directory = os.path.join(
        os.path.dirname(__file__),
        "reports"
    )

    os.makedirs(
        report_directory,
        exist_ok=True
    )

    filename = (
        f"grouptrip_report_{trip_id}.pdf"
    )

    filepath = os.path.join(
        report_directory,
        filename
    )

    # ------------------------------------------------------
    # PDF DOCUMENT
    # ------------------------------------------------------

    document = SimpleDocTemplate(

        filepath,

        pagesize=A4,

        rightMargin=15 * mm,

        leftMargin=15 * mm,

        topMargin=15 * mm,

        bottomMargin=15 * mm

    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(

        "ReportTitle",

        parent=styles["Title"],

        fontSize=22,

        leading=28,

        alignment=TA_CENTER,

        spaceAfter=12

    )

    subtitle_style = ParagraphStyle(

        "ReportSubtitle",

        parent=styles["Normal"],

        fontSize=10,

        alignment=TA_CENTER,

        spaceAfter=10

    )

    heading_style = ParagraphStyle(

        "ReportHeading",

        parent=styles["Heading2"],

        fontSize=14,

        spaceBefore=14,

        spaceAfter=8

    )

    normal_style = ParagraphStyle(

        "ReportNormal",

        parent=styles["Normal"],

        fontSize=9,

        leading=13

    )

    footer_style = ParagraphStyle(

        "ReportFooter",

        parent=normal_style,

        alignment=TA_CENTER,

        fontSize=8

    )

    story = []

    # ======================================================
    # TITLE
    # ======================================================

    story.append(
        Paragraph(
            "GroupTrip Ledger",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Trip Expense & Settlement Report",
            subtitle_style
        )
    )

    story.append(
        Spacer(
            1,
            10
        )
    )

    # ======================================================
    # TRIP INFORMATION
    # ======================================================

    story.append(
        Paragraph(
            "Trip Information",
            heading_style
        )
    )

    trip_info = [

        [
            "Trip",
            trip["name"]
        ],

        [
            "Dates",
            f'{trip["start_date"] or "Not set"} → '
            f'{trip["end_date"] or "Not set"}'
        ],

        [
            "Status",
            trip["status"] or "active"
        ],

        [
            "Ended",
            trip["ended_at"] or "Not ended"
        ]

    ]

    table = Table(
        trip_info,
        colWidths=[
            35 * mm,
            135 * mm
        ]
    )

    table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.lightgrey
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            )

        ])
    )

    story.append(
        table
    )

    # ======================================================
    # SUMMARY
    # ======================================================

    story.append(
        Paragraph(
            "Trip Summary",
            heading_style
        )
    )

    summary_data = [

        [
            "Total Spent",
            "₹" + format_paise(
                settlement["total_paise"]
            )
        ],

        [
            "Members",
            str(
                settlement["member_count"]
            )
        ],

        [
            "Expenses",
            str(
                settlement["expense_count"]
            )
        ]

    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            70 * mm,
            100 * mm
        ]
    )

    summary_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.lightgrey
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            )

        ])
    )

    story.append(
        summary_table
    )

    # ======================================================
    # INDIVIDUAL CONTRIBUTIONS
    # ======================================================

    story.append(
        Paragraph(
            "Individual Contribution",
            heading_style
        )
    )

    member_rows = [

        [
            "Member",
            "Paid",
            "Share",
            "Balance"
        ]

    ]

    for member in settlement[
        "members"
    ]:

        balance = member[
            "balance_paise"
        ]

        if balance > 0:

            balance_text = (
                "+₹"
                + format_paise(
                    balance
                )
                + " Gets"
            )

        elif balance < 0:

            balance_text = (
                "-₹"
                + format_paise(
                    abs(balance)
                )
                + " Owes"
            )

        else:

            balance_text = (
                "₹0.00 Settled"
            )

        member_rows.append([

            member["name"],

            "₹" + format_paise(
                member["paid_paise"]
            ),

            "₹" + format_paise(
                member["share_paise"]
            ),

            balance_text

        ])

    member_table = Table(
        member_rows,
        colWidths=[
            45 * mm,
            40 * mm,
            40 * mm,
            45 * mm
        ]
    )

    member_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            )

        ])
    )

    story.append(
        member_table
    )

    # ======================================================
    # EXPENSE DETAILS
    # ======================================================

    story.append(
        Paragraph(
            "Expense Details",
            heading_style
        )
    )

    expense_rows = [

        [
            "Description",
            "Category",
            "Paid By",
            "Amount"
        ]

    ]

    for expense in settlement[
        "expenses"
    ]:

        expense_rows.append([

            expense["description"],

            expense["category"],

            expense["paid_by"],

            "₹" + format_paise(
                expense["amount_paise"]
            )

        ])

    expense_table = Table(
        expense_rows,
        colWidths=[
            60 * mm,
            35 * mm,
            40 * mm,
            35 * mm
        ]
    )

    expense_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            )

        ])
    )

    story.append(
        expense_table
    )

    # ======================================================
    # FINAL SETTLEMENT
    # ======================================================

    story.append(
        Paragraph(
            "Final Settlement",
            heading_style
        )
    )

    settlement_rows = [

        [
            "From",
            "To",
            "Amount"
        ]

    ]

    if settlement[
        "settlements"
    ]:

        for item in settlement[
            "settlements"
        ]:

            settlement_rows.append([

                item["from"],

                item["to"],

                "₹" + format_paise(
                    item["amount_paise"]
                )

            ])

    else:

        settlement_rows.append([

            "Everyone",

            "Everyone",

            "Fully Settled"

        ])

    settlement_table = Table(
        settlement_rows,
        colWidths=[
            60 * mm,
            60 * mm,
            50 * mm
        ]
    )

    settlement_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            )

        ])
    )

    story.append(
        settlement_table
    )

    # ======================================================
    # FOOTER
    # ======================================================

    story.append(
        Spacer(
            1,
            15
        )
    )

    story.append(
        Paragraph(
            "Generated by GroupTrip Ledger",
            footer_style
        )
    )

    # ======================================================
    # BUILD PDF
    # ======================================================

    document.build(
        story
    )

    return send_file(

        filepath,

        as_attachment=True,

        download_name=filename,

        mimetype="application/pdf"

    )


# ==========================================================
# 19. START APPLICATION
# ==========================================================

if __name__ == "__main__":

    init_database()

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )