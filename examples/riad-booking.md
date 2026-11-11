# Riad Lotus booking site

A fictional brief for a small guesthouse in Marrakech. All names are invented.

## Background

- The owner currently takes bookings by phone and WhatsApp.
- About 12 rooms, high season is October to April.

## Public site

- Landing page with photo gallery and a short story about the riad
- Room pages with prices per night and a calendar showing availability
- Contact form that emails the owner
- Site available in English, French and Arabic

## Booking

- Guests pick dates and a room, then pay a 30% deposit online with Stripe
  - Refund the deposit if the owner cancels
- Confirmation email with the booking details
- Reminder email three days before arrival

## Owner area

- Owner login with password reset
- Admin screens to manage rooms, prices and blocked dates
- Monthly report of bookings and income, exportable as a spreadsheet
- Import existing bookings from the owner's Excel sheet

## Launch

- Deploy to a standard host with a custom domain and daily backups

## Out of scope

- Mobile app
- Channel manager sync with Booking.com
