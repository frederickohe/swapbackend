
 SOFTWARE REQUIREMENTS SPECIFICATION (SRD)
 Swap Pro – Barter Exchange Platform with Credit & Prepaid Commitment

Version: 1.0
Date: 2026-05-25
Status: Final


 1. Introduction

 1.1 Purpose
This document defines all functional and non-functional requirements for Swap Pro, a mobile application enabling users to exchange goods and services without fiat currency. The platform uses a credit system for value differences and a prepaid mutual transaction fee model to eliminate no-shows and build trust.

 1.2 Scope
Swap Pro includes:
- User management (profiles, authentication, credit wallet)
- Listing management with wishlist
- Search & filter
- Swap request workflow with prepaid fees
- Credit system for positive value differences
- Price difference settlement (cash or credit)
- Google Maps routing to swap hubs
- In-app notifications
- Admin dashboard (metrics, upcoming swaps per hub)
- Paystack integration (fees, refunds, cash differences)
- No‑show forfeiture mechanism

 1.3 Definitions
| Term | Definition |
|------|------------|
| Credit Wallet | Non‑withdrawable balance used for cash adjustments. |
| Transaction Fee | Fee paid to Swap Pro (e.g., 5% of higher item value), this fee is paid before request (initiator) or before approval (owner). |
| No‑show | User fails to appear at hub during scheduled meeting slot. |
| Price Difference | Cash or credit amount when item values are unequal. |



 2. Overall Description

 2.1 User Personas
| Role | Description |
|------|-------------|
| Regular User | Lists items, searches, sends/receives swap requests, pays transaction fees, attends hub meetings, uses credit. |
| Admin | Views dashboard metrics, sees upcoming swaps per hub location, manually resolves disputes. |

 2.2 Assumptions
- Users have smartphones with GPS and internet.
- Paystack supports payments, refunds, and webhooks in all operating regions.
- Swap Pro officials are present at hubs during operating hours.
- Credit has no cash value and cannot be withdrawn.

 2.3 Dependencies
- Google Maps API (location & routing)
- Paystack API (payments, refunds, webhooks)
- Push notification service (FCM / APNs)

---

 3. Functional Requirements

 3.1 User Management
| ID | Requirement |
|----|-------------|
| FR‑01 | Register with email/phone and password. |
| FR‑02 | Login, password reset, account deletion. |
| FR‑03 | Profile shows: active listings, swap history, pending requests, credit wallet balance. |

 3.2 Credit Wallet
| ID | Requirement |
|----|-------------|
| FR‑04 | Every user has a credit wallet. Credit cannot be withdrawn as cash. |
| FR‑05 | Credit are gained from: negative difference transactions (when you swap a high value property for a less value property, once agreed, the negative difference is given to you as credit |
| FR‑06 | Credit can be used to settle positive difference on your future swaps. |
| FR‑07 | Users see credit transaction history (earned, spent). |

 3.3 Listings
| ID | Requirement |
|----|-------------|
| FR‑08 | Create listing with: title, description, category, condition, up to 5 images, estimated value (in local currency). |
| FR‑09 | Each listing includes a wishlist (items/services desired in return). |
| FR‑10 | Edit or delete own listings. |
| FR‑11 | Listings expire after 30 days unless renewed. |

 3.4 Search & Filters
| ID | Requirement |
|----|-------------|
| FR‑12 | Search by keyword, category, location radius, value range. |
| FR‑13 | Search results highlight if wishlist matches searcher’s offered item. |

 3.5 Swap Request, Credit Calculation & Prepaid Fee (Initiator)
| ID | Requirement |
|----|-------------|
| FR‑14 | User selects a listing → chooses their own listing to swap with. |
| FR‑15 | System compares declared values. |
| FR‑16 | If initiator’s value > owner’s value: Difference added as credit to initiator’s wallet. No cash owed. |
| FR‑17 | If initiator’s value < owner’s value: Initiator must pay difference in cash (or use credit) at hub. |
| FR‑18 | Before sending request: Initiator pays full transaction fee (e.g., 5% of higher item value) via Paystack. Fee held by Swap Pro. |
| FR‑19 | Request is sent only after fee payment confirmed. |

 3.6 Owner Approval & Prepaid Fee
| ID | Requirement |
|----|-------------|
| FR‑20 | Owner receives notification + swap details (initiator’s item, difference, cash adjustment). |
| FR‑21 | Owner can approve or reject swap request. |
| FR‑22 | To approve: Owner must pay their transaction fee via Paystack. |
| FR‑23 | After owner pays fee → swap status = “pending hub meeting”. |
| FR‑24 | If owner rejects → initiator’s fee refunded (minus 1% processing fee). |
| FR‑25 | If owner ignores for 72 hours → request expires → initiator refunded (minus 1%). |

 3.7 Swap Hub Location & Routing
| ID | Requirement |
|----|-------------|
| FR‑26 | After mutual fee payment, system selects nearest Swap Pro hub (midpoint or user choice). |
| FR‑27 | App displays hub address + “Open in Google Maps” button. |
| FR‑28 | Both users see scheduled meeting time (admin‑configurable slots). |

 3.8 No‑Show & Forfeiture
| ID | Requirement |
|----|-------------|
| FR‑29 | Hub official marks attendance digitally for each user. |
| FR‑30 | If both attend → swap completes → both fees kept by Swap Pro. |
| FR‑31 | If one user no‑shows → they decide to take a percentage of the transaction fee as compensation or as in app credit to the attending user. |
| FR‑32 | No‑show user receives a strike; after 3 strikes, account restricted. |
| FR‑33 | If both no‑show → both fees forfeited to Swap Pro. |

 3.9 Price Difference Settlement at Hub
| ID | Requirement |
|----|-------------|
| FR‑34 | If initiator owes cash difference (initiator’s value < owner’s value), payment made at hub via their preferred means, cash, bank transfere or they can opt to be deducted from credit for other party. |
| FR‑35 | If initiator uses credit, balance is reduced. |
| FR‑36 | Official verifies difference payment before marking swap complete. |

 3.10 Notifications
| ID | Requirement |
|----|-------------|
| FR‑37 | Push notifications for: swap request received, owner approval/rejection, hub meeting reminder (1 hour before), no‑show penalty. |
| FR‑38 | In‑app notification center with read/unread. |

 3.11 Admin Dashboard
| ID | Requirement |
|----|-------------|
| FR‑39 | View metrics: total users, active listings, completed swaps, total fees collected, credit issued. |
| FR‑40 | See upcoming swaps per hub location (date, time, items, user names, fee payment status). |
| FR‑41 | Mark swaps as “completed”, “dispute”, or “no‑show” manually. |
| FR‑42 | Override credit adjustments in exceptional cases. |

---

 4. Non‑Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | Search results < 2 sec. Push notifications < 10 sec. |
| Security | Passwords hashed (bcrypt). HTTPS only. Paystack PCI compliance. |
| Availability | 99.5% uptime for core services. |
| Usability | Mobile‑first. Minimum touch target 44x44pt. |
| Platform | iOS 13+ and Android 8+ (React Native / Flutter). |
| Scalability | Indexed DB. Support 100k active users initially. |

---

 5. Complete User Flow (Final)

| Step | Actor | Action |
|------|-------|--------|
| 1 | User A | Lists property + wishlist. |
| 2 | User B | Searches → finds listing. |
| 3 | User B | Selects swap → system compares values. If B’s item > A’s → credit added to B. If B’s item < A’s → B owes cash at hub. |
| 4 | User B | Pays transaction fee (via Paystack) → request sent. |
| 5 | User A | Receives notification. |
| 6 | User A | To approve: pays their transaction fee. |
| 7 | System | If A rejects → B refunded (minus 1%). If A approves → swap scheduled. |
| 8 | Both | Routed to nearest swap hub (Google Maps). |
| 9 | Both | Meet Swap Pro official. |
| 10 | Official | Marks attendance. |
| 11 | Both | If difference owed → B pays (cash/credit). |
| 12 | Both | Sign transfer forms. |
| 13 | System | Swap marked complete. Both fees kept. |
| 14 | (No‑show case) | Attending user gets no‑show’s fee as cash or credit. |

---

 6. Admin Flow

| Step | Action |
|------|--------|
| 1 | Admin logs into dashboard. |
| 2 | Views metrics (users, listings, swaps, fees, credit issued). |
| 3 | Filters upcoming swaps by hub location. |
| 4 | Sees details: swap ID, users, items, meeting time, fee payment status. |
| 5 | Manually resolves disputes or marks no‑shows. |
6 Flags swap as completed
7 Transfer credit from one user to another if requested

---

 7. Data Entities (Conceptual)

| Entity | Fields |
|--------|--------|
| User | id, name, email, phone, password_hash, role, credit_balance, strikes |

|Admins| id, name, email, phone, password_hash, role, |
| Listing | id, user_id, title, description, category, value, wishlist (JSON), status, created_at |
| Swap Request | id, initiator_id, owner_id, initiator_listing_id, owner_listing_id, initiator_fee_paid, owner_fee_paid, difference_value, positive_difference, negative_difference, status |
| Swap | id, swap_request_id, hub_id, status |
| Hub | id, name, address, lat, lng, operating_hours |
| Transaction | id, swap_id, user_id, amount, type (fee / difference / refund), paystack_reference, status |
| CreditTransaction | id, user_id, swap_id, amount, reason (difference / forfeit / spent) |

---

 8. External Interfaces

| Interface | Purpose |
|-----------|---------|
| Google Maps SDK | Location selection, routing to hub |
| Paystack SDK | Payments, refunds, webhooks for fee confirmation |
| FCM / APNs | Push notifications |

---

 9. Constraints (Final)

|  | Constraint | Explanation |
|---|------------|-------------|
| 1 | Refund conditions | Refund (minus 1% processing) only on owner rejection or request expiry. |
| 2 | Hub official verification | Attendance must be marked digitally before swap completion. |
| 3 | Credit non‑transferable | Credit cannot be sent user to user or converted to cash. |

---

 10. Assumptions & Risks

| Type | Item |
|------|------|
| Assumption | Paystack supports instant refunds via API. |
| Assumption | Users accept that credit has no cash value. |

---

 11. Appendices

 A. Fee & Refund Rules Summary
| Scenario | Result |
|----------|--------|
| Initiator pays fee, owner rejects | Initiator refunded minus 1% |
| Initiator pays fee, owner ignores 72h | Initiator refunded minus 1% |
| Both pay fees, both attend | Both fees kept by Swap Pro |
| Both pay fees, one no‑shows | Attending user gets absent user’s fee as cash or credit |
| Both pay fees, both no‑show | Both fees kept by Swap Pro |

 B. Credit Earning & Spending
| Action | Credit Change |
|--------|---------------|
| Initiator’s value > owner’s value | +difference to initiator |
| No‑show’s fee transferred | +fee amount to attending user |
| Pay cash difference with credit | –difference amount |


