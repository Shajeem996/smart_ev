# Smart EV Charging Slot Booking & Queue Scheduler
**A Web-Based Intelligent EV Charging Slot Reservation, Virtual Queue Management & Session Tracking System**
*Master of Computer Applications (MCA) Project*

---

## ⚡ Project Overview

The **Smart EV Charging Slot Booking & Queue Scheduler** is a web application designed to solve key challenges in electric vehicle (EV) charging infrastructure: charger unavailability, uncertain waiting times, schedule conflicts, and uncoordinated station operations.

The system connects EV owners, charging station operators, and a central system administrator through a unified platform featuring distinct role-based workflows, an interactive map, QR-code arrival verification, interval conflict prevention, and an event-driven priority waiting queue.

---

## 👥 User Roles & Responsibilities

The system enforces three distinct user roles with strict backend permission isolation:

### 1. EV User (Customer-Facing Portal)
* **Registration & Auth:** Self-service registration and secure login.
* **Vehicle Management:** Add and manage EV vehicles (e.g. Tata Nexon EV, Hyundai Ioniq 5) with battery capacity and connector types (CCS-2, Type 2, CHAdeMO, GB/T).
* **Live Interactive Map:** Browse charging stations on an interactive Leaflet/OpenStreetMap interface with real-time availability markers.
* **Slot Booking:** Select station, point, date, and time slot. Strict interval scheduling prevents double-bookings.
* **Unique Booking & QR Code:** Receive an instant unique Booking ID (`EVB-XXXXXX`) and cryptographically signed QR code.
* **Smart Waiting Queue:** When a station's slots are occupied, users can join the priority waiting queue and receive real-time notifications when a bay becomes available.
* **Notifications:** In-app alert dropdown for bookings, queue promotions, and charging updates.

### 2. Station Operator (Assigned-Station Operations)
* **Creation:** Operators are provisioned exclusively by the System Admin (no self-registration).
* **Station Isolation:** Operators are strictly restricted to their single assigned charging hub. Backend security prevents unauthorized cross-station access.
* **Live Bay Monitoring:** View real-time status of each charging point (`AVAILABLE`, `RESERVED`, `CHARGING`, `FINISHING`, `OUT_OF_SERVICE`).
* **QR Verification:** Scan or enter user QR codes to verify reservation details, time-window validity, and connector compatibility upon arrival.
* **Charging Simulation:** Start charging sessions (`RESERVED` → `CHARGING`), monitor duration, and complete charging (`CHARGING` → `FINISHING` → `AVAILABLE`).
* **Auto-Queue Trigger:** Ending a charging session automatically recalculates station queue positions and alerts the next eligible driver.
* **Station Analytics:** View station-specific energy delivery (kWh), throughput metrics, and Chart.js utilization charts.

### 3. System Administrator (System-Wide Management)
* **Strict Single-Admin Rule:** The application strictly enforces exactly ONE active System Admin account at the database and application level.
* **User & Operator Management:** Activate/deactivate EV user accounts; create and assign station operators.
* **Station & Bay Management:** Full CRUD operations for charging stations (geo-coordinates, operating hours, amenities) and charging points (power rating, connector standard).
* **System-Wide Monitoring:** Central dashboard tracking all bookings, live sessions, waiting queues, and station utilization.
* **System Reports:** Analytical reports and Chart.js graphs displaying system throughput and energy delivered.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | Python 3.11+, Django 5.x |
| **API Architecture** | Django REST Framework (DRF) JSON endpoints |
| **Database** | MySQL (with seamless local SQLite fallback) |
| **Frontend UI** | HTML5, Vanilla CSS3 (Custom design system), Bootstrap 5 |
| **Interactive Maps** | Leaflet.js, OpenStreetMap |
| **Data Visualization** | Chart.js 4.x |
| **QR Code Engine** | `qrcode` Python library, Pillow (PIL) |
| **Icons & Fonts** | Bootstrap Icons, Google Fonts (Inter) |

---

## 🧠 Core Algorithms & Technical Concepts (MCA Viva Topics)

### 1. Interval Scheduling & Conflict Prevention
To guarantee that two drivers cannot book the same physical charging connector for overlapping time intervals, the system implements interval overlap validation:
$$\text{Conflict exists if: } (\text{Start}_A < \text{End}_B) \land (\text{End}_A > \text{Start}_B)$$
Implemented in `Booking.check_conflict()` and enforced on Django form validation before writing to the database.

### 2. Event-Driven Priority Waiting Queue
When all slots at a station are reserved, EV users can enter the queue. The queue ordering is determined by:
* **Priority Level** (emergency or normal)
* **FIFO Timestamp** (`created_at`)
* **Connector Compatibility** (matches driver's vehicle connector)

When an active session completes or a reservation is cancelled, `process_station_queue()` immediately identifies the next eligible waiting driver, transitions their status to `NOTIFIED`, and sends an in-app notification with a direct claim link.

### 3. Software-Based Charging Lifecycle Simulation
The system models realistic hardware state transitions without physical IoT dependencies:
$$\text{AVAILABLE} \xrightarrow{\text{Book Slot}} \text{RESERVED} \xrightarrow{\text{Operator QR Scan}} \text{CHARGING} \xrightarrow{\text{End Session}} \text{FINISHING} \rightarrow \text{AVAILABLE}$$
Energy delivered ($E$) is modeled using point power rating ($P$) and duration ($t$):
$$E = P \times t \times \eta \quad (\eta \approx 92\% \text{ charger efficiency})$$

---

## 🚀 Quick Setup & Installation

### 1. Clone or Open Project
```bash
cd smart_ev
```

### 2. Create and Activate Virtual Environment (Recommended)
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
The system automatically connects to MySQL if running on `localhost:3306` with database `ev_charging_db`. If MySQL is not running, it automatically and gracefully uses SQLite (`db.sqlite3`) for local development without any manual configuration required.

Run database migrations:
```bash
python manage.py migrate
```

### 5. Load Demo Seed Data
A built-in management command seeds the database with stations, charging points, operators, vehicles, bookings, sessions, and the single System Admin:
```bash
python manage.py seed_data
```

### 6. Run the Development Server
```bash
python manage.py runserver
```
Open your browser and navigate to: `http://127.0.0.1:8000/`

---

## 🔑 Demo Login Credentials

| Role | Username | Password | Notes |
|---|---|---|---|
| **System Admin** | `admin` | `Admin@123` | Full system control |
| **Station Operator 1** | `operator1` | `Operator@123` | Assigned to *EcoCharge Metro Hub* |
| **Station Operator 2** | `operator2` | `Operator@123` | Assigned to *GreenCharge Station* |
| **EV User 1** | `user1` | `User@123` | Owns Tata Nexon & Hyundai Ioniq 5 |
| **EV User 2** | `user2` | `User@123` | Owns MG ZS EV (queued demo user) |

*You can also register a new EV User account anytime from the registration page.*

---

## 🧪 Running Automated Tests

The project includes an automated test suite covering authentication, single-admin enforcement, interval conflicts, QR generation, operator isolation, charging lifecycles, and queue promotion:

```bash
python manage.py test
```
All 19 test cases run and pass with 100% success.

---

## 🔮 Future Enhancements
* OCPP (Open Charge Point Protocol) 1.6/2.0 integration for physical IoT hardware.
* Dynamic electricity tariff pricing based on grid load peak hours.
* AI/ML-driven demand prediction and optimal slot recommendation.
* Payment gateway integration (UPI, Credit/Debit cards).
* Mobile application interface using Progressive Web App (PWA) standards.
