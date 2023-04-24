# Changelog

## 1.5.0

- Added meetings.Calendar for controling day of week cycle
- Breaking changes: MeetingSet.by_value now always returns two tuple list of
  items, not dictionary.

## 1.4.0

- added foldable column and table formats
- fixes for custom template dirs and css file locations
- new config options for passing YAML and data/asset directories via cli
- able to specify independent nonce and api urls
- default meeting codes from spec
- template config options
- PDF zoom option
- flask app updates and new config editing pages
- updated conference meeting attrs to handle nonzoom urls/ids

## 1.3.0

- using click groups for cli usage
- adding qrcode for cover
- added back cover w/ preamble and group description
- added `MeetingSet.value_set(filter_none)` kwarg
- added `latlon` and `is_conference` methods for `Meeting`
- lots of work to the PDF layout
- printing support

## 1.2.0

- moved to true type fonts for cross platform compatibility
- fixed major bug in `MeetingSet.value_set` that prevented some meeting types
  from not appearing. method now only takes one argument.
- fixed the `MeetingSet.by_id` method to return a dict
- writes PDF out only when rendering is complete instead of holding the file
  open for writing
- added a notes section at the end of the directory

## 1.1.1

- fixed bug with adict module that inserted `_default` and `_has_default` as
  items

## 1.1.0

- Removed dependency on `attrdict` package.
- Added support for all modern Python versions above 3.7
