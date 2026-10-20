# Taste (Continuously Learned by [CommandCode][cmd])

[cmd]: https://commandcode.ai/

# Project Identity
- Business name is Atlas Fund Capital, domain is atlasfundcapital.com. Confidence: 0.85
- Business address: 444 Alaska Avenue Suite #BWM188, Torrance, CA 90503. Confidence: 0.85
- Atlas Fund Capital is a partner of LoanableUSA — use LoanableUSA's terms. Confidence: 0.80

# Tech Stack
- Use plain HTML, CSS, and JavaScript — no frameworks. Confidence: 0.85

# Design
- Use completely unique copywriting and content — do NOT copy text from loanableusa.com. Create original, human-level unique copy. Confidence: 0.85
- Design should look premium/luxury, like a billion-dollar financial company. Confidence: 0.80
- Blog detail pages need WordPress-level premium formatting: serif body font (Cormorant Garamond) at 1.15rem+, generous line-height (1.85-2.0), proper paragraph margins, styled blockquotes with gold left-border, dark-themed code blocks, and shadowed images. Confidence: 0.75
- Use clean and organized folder structure for the project. Confidence: 0.75
- Maximum funding amount offered is $20 million (not $50M). Confidence: 0.85

# Navigation
- Include loan products dropdown: line of credit, MCA loan, SBA loan, term loans, equipment financing, invoice factoring, business acquisition. Confidence: 0.80
- Exclude real estate loans dropdown and industries dropdown from navigation. Confidence: 0.80
- Include Resources nav tab but without dropdown subpages for now. Confidence: 0.75
- Include "Apply Now" and "Partner Login" CTA buttons in header. Confidence: 0.80

# Blog Editor
- Blog editor should allow creating new custom categories on the fly, not just selecting from predefined options. Confidence: 0.65

# Dashboard
- For admin CRUD operations (status change, edit, delete, add), update the DOM directly — do NOT use page reloads. All changes should reflect instantly inline. Confidence: 0.70
- Sidebar toggle must not cover logo or main content; when sidebar is open, main content area should resize/shift accordingly (not overlay). Confidence: 0.65

# Lead / Application Form
See [lead-/-application-form/taste.md](lead-/-application-form/taste.md)
- Acceptance of the Terms & Conditions and Privacy Policy must be its own separate, required checkbox — distinct from (and not merged into) the SMS/email opt-in checkboxes. Confidence: 0.75
# Tooling
- Use Python (not Node.js) for new tooling, infrastructure, or servers in this Django/Python project. Confidence: 0.70

# Admin Design
- All superadmin pages must use the same consistent design pattern — light theme with toggle sidebar, matching the blog list page's CSS and layout. Confidence: 0.60

# Images
- Use descriptive placeholder text and alt text that specify what type of image should be placed. Confidence: 0.80
- For AI-generated thumbnails, first generate a creative custom prompt with AI, then use that prompt to generate the thumbnail image. Confidence: 0.75
- AI-generated blog thumbnails may include text in the image — do not prohibit text in image prompts. Confidence: 0.65
- Use a high-quality image model (e.g., DALL·E 3 HD or equivalent) with detailed, vivid prompting for AI-generated thumbnails — low-quality outputs are unacceptable. Confidence: 0.70

# Analytics
- Capture HTTP referrer server-side for GA4 events — client-side document.referrer is unreliable and often stripped. Confidence: 0.75
- Superadmin leads table should include a referral source column showing the external referrer URL for organic leads, or the affiliate name/ID/email for referral leads. Confidence: 0.80
- Store original external referrer in a cookie on first visit so internal navigation doesn't overwrite it with self-referring URLs (e.g., atlasfundcapital.com). Confidence: 0.70
- Store the full external referrer URL in cookies — do not parse or extract just the hostname. Confidence: 0.70

# Footer
- Keep all footer items from LoanableUSA except: careers, real estate section, security item link, and success stories. Confidence: 0.80
- Use Atlas Fund Capital's business address (not LoanableUSA's) in the footer. Confidence: 0.85
