(config)=
# Configuration

## YAML Configuration File

You must create a configuration YAML file that contains the values used to render the PDF.
Then pass the config file as the `--config` parameter to the 12step commands.
You can use the `12step init` command to interactively setup your configuration values.

```
12step init -o my.config.yaml
```

## Example



Here is a full example of the YAML configuration file for Baltimore AA intergroup.
See comments below for each setting and its purpose.
You can copy this config from and modify it to fit your sites' needs.
You can find this file in the repo at `sites/baltimoreaa.org/config.yml`

```{include} configvalues.md
```

## Environment Variables

There are a few environment variables you can set to control the behavior of the 12step commands

### `PDF12STEP_CONFIG`

Set this to the filename of your YAML configuration file.
If not set, then pass it using the `--config` parameter to the 12step commands.

### `PDF12STEP_DATA_DIR`

Set this to the path where the tool should download all of the JSON meeting data.
Defaults to `$PWD/data`
