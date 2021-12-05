# Configuration

## YAML Configuration File

You must create a configuration YAML file that contains the values used to render the PDF.
Then pass the config file as the `--config` parameter to the 12step commands.
You can use the `12step-init` command to interactively setup your configuration values.

```
12step-init my.config.yaml
```

In the repo there is also a `example.config.yml` you can use as a reference to get the program up and running using the Baltimore AA meeting data.

## Environment Variables

There are a few environment variables you can set to control the behavior of the 12step commands

### `PDF12STEP_CONFIG`

Set this to the filename of your YAML configuration file.
If not set, then pass it using the `--config` parameter to the 12step commands.

### `PDF12STEP_DATA_DIR`

Set this to the path where the tool should download all of the JSON meeting data.
Defaults to `$PWD/data`
