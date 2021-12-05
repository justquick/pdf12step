# 12 Step Recovery Meeting PDF Generator

This Python program can create meeting lists in PDF format for distribution on the web or print. In order to populate the meeting data, you must be connected to a site running the [12 Step Meeting List](https://wordpress.org/plugins/12-step-meeting-list/) WordPress plugin. This project was developed for the [Baltimore Intergroup Council of AA](https://baltimoreaa.org/)

The tool works by

- Downloading the JSON meeting data form the WP plugin
- Rendering the meeting list directory as HTML using [Jinja2](https://jinja.palletsprojects.com/) templates
- Converting the HTML into a PDF using the [WeasyPrint](https://weasyprint.org/) document factory

The CSS and HTML templates are extensible so you can customize the PDF output and make it fit your meeting format.

The app also contains a [Flask](https://flask.palletsprojects.com/) webapp that can render the live HTML and PDF content in your browser.

## Install

### Pip

Run python to install dependencies and setup package from pypi

```
pip install pdf12step
```


### Development

Install package and manage dependencies with [Pipenv](https://docs.pipenv.org/) for development

```
pipenv install --dev
```

## Configuration

You must create a configuration YAML file that contains the values used to render the PDF.
Then pass the config file as the `--config` parameter to the 12step commands.
You can use the `12step-init` command to interactively setup your configuration values.

```
12step-init my.config.yaml
```

In the repo there is also a `example.config.yml` you can use as a reference to get the program up and running using the Baltimore AA meeting data.


## Downloading Data

Run the `12step-download` script to fetch data from a WordPress site with the 12 Step Meeting plugin installed. For example using the [Baltimore Intergroup ](https://baltimoreaa.org/) site.

```
12step-download --config my.config.yaml -u https://baltimoreaa.org -v
```

The data will now be stored in JSON files in the project root.

## Making Documents

### Commmand Line

Run the `12step-pdf` script to generate the PDF

```
12step-pdf --config my.config.yaml -v
```

The PDF will be generated in the project directory in the format `<month> <year> Directory.pdf` with the current date.

### From the Web App

Run the Flask server to start the local web app running.

```
12step-flask
```

The app will now be available on [http://localhost:5000](http://localhost:5000)

If you change any config or code, you will have to restart the service as live reload doesnt pick up on changes and most of the code is cached.

Please never use this webapp in production. It takes a long time and a lot of resources to render PDFs which makes it bad for app deployment. Instead, run the `12step-pdf` command on a regular interval (cron) to write the PDF file to a location your site can serve (eg wp-content)

#### HTML

The fastest way to test out the document is using the HTML formatter. It will not have the page cover, page header or some styles but it's a good quick sanity check.

[http://localhost:5000/meetings.html](http://localhost:5000/meetings.html)

#### PDF

The live PDF version takes a while to generate but is available at

[http://localhost:5000/meetings.pdf](http://localhost:5000/meetings.pdf)
