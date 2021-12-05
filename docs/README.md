# 12 Step Recovery Meeting PDF Generator

This Python program can create meeting lists in PDF format for distribution on the web or print. In order to populate the meeting data, you must be connected to a site running the [12 Step Meeting List](https://wordpress.org/plugins/12-step-meeting-list/) WordPress plugin. This project was developed for the [Baltimore Intergroup Council of AA](https://baltimoreaa.org/)

The tool works by

- Downloading the JSON meeting data form the WP plugin
- Rendering the meeting list directory as HTML using [Jinja2](https://jinja.palletsprojects.com/) templates
- Converting the HTML into a PDF using the [WeasyPrint](https://weasyprint.org/) document factory

The CSS and HTML templates are extensible so you can customize the PDF output and make it fit your meeting format.

The app also contains a [Flask](https://flask.palletsprojects.com/) webapp that can render the live HTML and PDF content in your browser.
