# Using the tool

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
