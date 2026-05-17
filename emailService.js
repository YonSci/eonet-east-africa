/**
 * emailService.js
 * Sends emails via EmailJS -- no backend or SMTP required.
 * All calls go directly from the browser to EmailJS servers.
 * Free tier: 200 emails/month.
 *
 * Docs: https://www.emailjs.com/docs/sdk/installation/
 */

const PUBLIC_KEY       = import.meta.env.VITE_EMAILJS_PUBLIC_KEY      || ''
const SERVICE_ID       = import.meta.env.VITE_EMAILJS_SERVICE_ID      || ''
const TEMPLATE_CONFIRM = import.meta.env.VITE_EMAILJS_TEMPLATE_CONFIRM || ''
const TEMPLATE_ALERT   = import.meta.env.VITE_EMAILJS_TEMPLATE_ALERT   || ''

export const EMAILJS_CONFIGURED =
  PUBLIC_KEY && SERVICE_ID &&
  TEMPLATE_CONFIRM && TEMPLATE_ALERT &&
  !PUBLIC_KEY.includes('YOUR_')

// Load EmailJS SDK lazily (only when needed)
let emailjsLoaded = false
async function loadEmailJS() {
  if (emailjsLoaded) return window.emailjs
  return new Promise((resolve, reject) => {
    if (window.emailjs) { emailjsLoaded = true; resolve(window.emailjs); return }
    const script    = document.createElement('script')
    script.src      = 'https://cdn.jsdelivr.net/npm/@emailjs/browser@4/dist/email.min.js'
    script.onload   = () => {
      window.emailjs.init({ publicKey: PUBLIC_KEY })
      emailjsLoaded = true
      resolve(window.emailjs)
    }
    script.onerror  = () => reject(new Error('Failed to load EmailJS SDK'))
    document.head.appendChild(script)
  })
}

/**
 * Send a subscription confirmation email.
 * Called when a user clicks "Save subscription".
 */
export async function sendConfirmationEmail({ email, categories, countries }) {
  if (!EMAILJS_CONFIGURED) {
    console.info('[EmailJS] Not configured -- skipping confirmation email')
    return { ok: false, reason: 'not_configured' }
  }
  const ejs = await loadEmailJS()
  const catLabels = categories.join(', ')
  const ctyLabels = countries.length > 0 ? countries.join(', ') : 'All countries'

  const params = {
    to_email:   email,
    to_name:    email.split('@')[0],
    categories: catLabels,
    countries:  ctyLabels,
  }

  try {
    const result = await ejs.send(SERVICE_ID, TEMPLATE_CONFIRM, params)
    console.info('[EmailJS] Confirmation sent to', email, result.status)
    return { ok: true }
  } catch (err) {
    console.error('[EmailJS] Confirmation failed:', err)
    return { ok: false, reason: err.text || String(err) }
  }
}

/**
 * Send an alert email for new events.
 * Called from EventWatcher when new events match a subscription.
 */
export async function sendAlertEmail({ email, newEvents, categories, countries }) {
  if (!EMAILJS_CONFIGURED) return { ok: false, reason: 'not_configured' }
  const ejs = await loadEmailJS()

  const eventList = newEvents
    .slice(0, 8)
    .map((ev) => {
      const date = (ev.latest_date || '').slice(0, 10)
      return '[' + ev.category + '] ' + ev.title + (date ? ' (' + date + ')' : '')
    })
    .join('
') + (newEvents.length > 8 ? '
...and ' + (newEvents.length - 8) + ' more' : '')

  const params = {
    to_email:    email,
    to_name:     email.split('@')[0],
    event_count: String(newEvents.length),
    event_list:  eventList,
    categories:  categories.join(', '),
    countries:   countries.length > 0 ? countries.join(', ') : 'All countries',
  }

  try {
    const result = await ejs.send(SERVICE_ID, TEMPLATE_ALERT, params)
    console.info('[EmailJS] Alert sent to', email, result.status)
    return { ok: true }
  } catch (err) {
    console.error('[EmailJS] Alert failed:', err)
    return { ok: false, reason: err.text || String(err) }
  }
}
