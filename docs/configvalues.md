```yaml
# Site URL where 12 Step WP Plugin is installed
site_url: https://baltimoreaa.org/
# URL to gather nonce param which is required for certain versions of the plugin
nonce_url: https://baltimoreaa.org/meetings
# URL to POST to in order to get meeting TSML JSON data
api_url: https://baltimoreaa.org/wordpress/wp-admin/admin-ajax.php

# Page size of the output PDF.
# If not doing Letter, prepare to use custom template_dirs and stylesheets
size: Letter #  5.5in 8.5in

# Background css color of the cover
color: "#ff697b"

# Background css color of page headers
header_color: "#ff697b"

# Page number text color for header on all pages. Background color is header_color above
page_number_color: "black"

# URL to add to QR code image. Scanning the code takes you to this URL
qrcode_url: https://baltimoreaa.org/meetings/

# Metadata info about who makes this PDF
# Also included on the cover
author: Baltimore Intergroup Council
description: Baltimore Area A.A. Group meeting Directory
address: 8635 Loch Raven Boulevard, Suite 4 • Baltimore, Maryland 21286
phone: 410-663-1922
fax: 410-663-7465
email: intergroup@baltimoreaa.org
website: www.baltimoreaa.org

# Sections to use on the PDF. If they are removed they will not show
# See the templates/includes/sections for details of each
sections:
  - contact
  - codes
  - misc
  # - regions
  - index
  - list
  - readings
  - notes

# Template directories.
# Create your own directory and add it here to override default emplates
# template_dirs:
#     - my/custom/templates

# Static asset directories.
# A directory where static files will be rendered
# Other static files here will be available for the HTML to render
asset_dir: ./assets

# CSS stylesheets to add when rendering PDF
# Add your own to modify styles
# stylesheets:
#     - my/path/to/custom.css

# Show links or not when rendering
show_links: true

# Codes to filter out from displaying
# Removes them from PDF entirely
filtercodes:
    - TC # Temporarily closed

# Set this to display only these attendance_options in the PDF
# Normal options are in_person, inactive, online, andhybrid
# Used to only print hybrid/in_person for print PDF
# attendance_options:
#     - in_person
#     - hybrid
#     - online
#     - inactive

# Number of notes pages to add to the end of the PDF
# Helpful to padd the total pages to a fixed amount
notes_pages: 4

# Maps a system code to a new code to display in the directory
codemap:
    B: BB
    BE: BEG
    S: SPAN
    ST: STEP
    TR: TRAD
    X: H

# System meeting codes and their descriptions.
# Do not modify the keys on this mapping, this is from the plugin
# Feel free to change descriptions or add your own
meetingcodes:
    11: 11th Step Meditation
    12x12: 12 Steps & 12 Traditions
    A: Agnostic/Secular
    B: Big Book
    BE: Beginner/Newcomer
    C: Closed Meeting for Alcoholics Only
    CAN: Candlelight
    CF: Child-Friendly
    CPTS: Concepts
    D: Discussion
    DB: Digital Basket
    HYB: Hybrid
    LGBTQ: LGBTQ
    LIT: Literature
    M: Men's
    MED: Meditation
    NB: Non-Binary
    O: Open
    ONL: Online
    OUT: Outdoor Meeting
    POC: People of Color
    S: Spanish Speaking
    SEN: Seniors
    SP: Speaker
    ST: Step Meeting
    T: Transgender
    TC: Temporarily Closed
    TR: Tradition Study
    W: Women's
    X: Handicap Access
    Y: Young People's

# Locztions by zipcode with their neighborhood name
# Used in the PDF to define sections for each day
zipcodes:
    20705: College Park
    20707: Laurel
    20715: Bowie
    20723: Laurel
    20794: Jessup
    20910: Silver Spring
    21014: Bel Air, Forest Hill
    21023: Butler
    21029: Clarksville
    21030: Cockeysville, Hunt Valley
    21031: Cockeysville, Hunt Valley
    21032: Crownsville
```
