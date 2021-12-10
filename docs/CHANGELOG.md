# Changelog

## 1.2.0

- moved to true type fonts for cross platform compatibility
- fixed major bug in `MeetingSet.value_set` that prevented some meeting types from not appearing. method now only takes one argument.
- fixed the `MeetingSet.by_id` method to return a dict
- writes PDF out only when rendering is complete instead of holding the file open for writing
- added a notes section at the end of the directory

## 1.1.1

- fixed bug with adict module that inserted `_default` and `_has_default` as items

## 1.1.0

- Removed dependency on `attrdict` package.
- Added support for all modern Python versions above 3.7
