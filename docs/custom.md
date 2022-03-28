# Customizing the PDFs

There are a few ways to add your own style to the PDFs the tool generates.
The customizations are designed to be simple enough that anyone with basic HTML/CSS knowledge can customize the directories to fit their needs.

## Config

There are several config values that can be modified to customize the structure of the PDF generated. See the {ref}`config`

## CSS

You can use custom CSS to override the style and layout of the PDFs.
You can override the default CSS by pointing your config to new CSS files using the `stylesheets` config variable. To see the default CSS see the `pdf12step/templates/assets/css/style.css` file

## Templates

You can override the default templates by customizing the blocks or the entire template itself. You can set the `template_dirs` config value to a directory with you own templates. To learn more about the templating language, Jinja2, you can see the [Template Designer Documentation](https://jinja.palletsprojects.com/en/3.1.x/templates/)
